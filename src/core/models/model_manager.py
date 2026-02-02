#!/usr/bin/env python3
"""
统一模型管理器

基于 Infinity 框架实现多模型的统一管理、配置驱动的模型加载、热切换等功能。

参考文档：
- INFINITY_MODEL_MANAGEMENT_GUIDE.md: Infinity多模型管理完整指南
"""

from typing import Dict, Optional, List, Union, Any
from dataclasses import dataclass
from pathlib import Path
import asyncio
import logging
import os
import tempfile

logger = logging.getLogger(__name__)


@dataclass
class ModelConfig:
    """模型配置数据类"""

    name: str
    engine: str = "torch"
    device: str = "cuda"
    dtype: str = "float16"
    embedding_dim: int = 512
    trust_remote_code: bool = False
    pooling_method: str = "mean"
    compile: bool = False
    batch_size: int = 16
    local_path: Optional[str] = None

    def __post_init__(self):
        """验证配置"""
        self._validate()

    def _validate(self):
        """验证配置的合法性"""
        # 验证引擎类型
        valid_engines = ["torch", "ctranslate2", "optimum", "neuron", "debugengine"]
        if self.engine not in valid_engines:
            raise ValueError(
                f"不支持的引擎类型: {self.engine}。"
                f"支持的引擎: {', '.join(valid_engines)}"
            )

        # 验证设备类型
        valid_devices = ["cuda", "cpu", "mps"]
        if not any(device in self.device.lower() for device in valid_devices):
            logger.warning(
                f"设备类型 {self.device} 可能不支持。"
                f"建议使用: {', '.join(valid_devices)}"
            )

        # 验证数据类型
        valid_dtypes = ["float16", "bfloat16", "float32", "float64"]
        if self.dtype not in valid_dtypes:
            raise ValueError(
                f"不支持的数据类型: {self.dtype}。"
                f"支持的类型: {', '.join(valid_dtypes)}"
            )

        # 验证向量维度
        if self.embedding_dim <= 0:
            raise ValueError("向量维度必须大于0")

        # 验证批处理大小
        if self.batch_size <= 0:
            raise ValueError("批处理大小必须大于0")


class ModelManager:
    """
    统一模型管理器

    负责管理所有模型的加载、卸载、切换等操作。
    支持配置驱动的模型管理和热切换功能。
    """

    # Infinity 客户端类型（延迟导入）
    _AsyncEmbeddingEngine = None
    _EngineArgs = None

    def __init__(self):
        self._models: Dict[str, "AsyncEmbeddingEngine"] = {}
        self._configs: Dict[str, ModelConfig] = {}
        self._lock = asyncio.Lock()
        self._initialized = False

    @staticmethod
    def load_configs_from_yaml(models_config: Dict[str, Any]) -> Dict[str, ModelConfig]:
        """
        从config.yml格式的配置加载模型配置

        Args:
            models_config: config.yml中的models配置字典

        Returns:
            模型配置字典，key为model_id，value为ModelConfig对象
        """
        configs = {}
        available_models = models_config.get("available_models", {})
        active_models = models_config.get("active_models", [])

        # 只加载活跃的模型
        for model_id in active_models:
            if model_id not in available_models:
                logger.warning(f"活跃模型 {model_id} 不在可用模型列表中，跳过")
                continue

            model_data = available_models[model_id]
            config = ModelConfig(
                name=model_data.get("model_name", model_id),
                engine=model_data.get("engine", "torch"),
                device=model_data.get("device", "cpu"),
                dtype=model_data.get("dtype", "float32"),
                embedding_dim=model_data.get("embedding_dim", 512),
                trust_remote_code=model_data.get("trust_remote_code", False),
                pooling_method=model_data.get("pooling_method", "mean"),
                compile=model_data.get("compile", False),
                batch_size=model_data.get("batch_size", 16),
                local_path=model_data.get("local_path"),
            )
            configs[model_id] = config
            logger.info(f"加载模型配置: {model_id} -> {config.name}")

        return configs

    def _ensure_imports(self):
        """延迟导入 Infinity 模块"""
        if self._AsyncEmbeddingEngine is None:
            try:
                from infinity_emb import AsyncEmbeddingEngine, EngineArgs

                self._AsyncEmbeddingEngine = AsyncEmbeddingEngine
                self._EngineArgs = EngineArgs
            except ImportError as e:
                raise RuntimeError(
                    "无法导入 infinity_emb 模块。"
                    "请安装: pip install infinity-emb[all]"
                ) from e

    async def initialize(self, configs: Dict[str, ModelConfig]):
        """
        初始化模型管理器

        Args:
            configs: 模型配置字典，key为模型类型，value为ModelConfig对象
        """
        if self._initialized:
            logger.warning("模型管理器已初始化，跳过重复初始化")
            return

        self._ensure_imports()

        logger.info(f"正在初始化模型管理器，将加载 {len(configs)} 个模型...")

        # 加载所有模型
        for model_type, config in configs.items():
            try:
                await self.register_model(model_type, config)
                logger.info(f"模型 {model_type} 加载成功: {config.name}")
            except Exception as e:
                logger.error(f"模型 {model_type} 加载失败: {e}")
                raise

        self._initialized = True
        logger.info(f"模型管理器初始化完成，已加载 {len(self._models)} 个模型")

    async def register_model(
        self, model_type: str, config: ModelConfig
    ) -> "AsyncEmbeddingEngine":
        """
        注册并加载模型

        Args:
            model_type: 模型类型（如 'text', 'image', 'audio'）
            config: 模型配置

        Returns:
            Infinity 客户端实例

        Raises:
            ValueError: 如果模型配置无效
            RuntimeError: 如果模型加载失败
        """
        async with self._lock:
            # 如果模型已存在，直接返回
            if model_type in self._models:
                logger.info(f"模型 {model_type} 已加载，跳过重复加载")
                return self._models[model_type]

            logger.info(f"正在加载模型: {config.name} (type={model_type})")

            self._ensure_imports()

            # 确定模型路径
            model_path = config.local_path or config.name

            # 检查本地模型是否存在
            if model_path and not os.path.isabs(model_path):
                # 尝试相对于项目根目录
                project_root = os.environ.get("PROJECT_ROOT", os.getcwd())
                absolute_path = os.path.join(project_root, model_path)
                if os.path.exists(absolute_path):
                    logger.info(f"本地模型存在: {absolute_path}")
                    model_path = absolute_path
                else:
                    logger.info(f"使用HuggingFace模型: {model_path}")

            logger.info(f"使用模型路径: {model_path}")

            # 所有模型都通过Infinity统一调用
            try:
                return await self._load_model(model_type, config, model_path)
            except Exception as e:
                logger.error(f"使用Infinity加载模型失败: {e}")
                raise RuntimeError(f"模型加载失败: {e}") from e

    async def get_model(self, model_type: str) -> "AsyncEmbeddingEngine":
        """
        获取已加载的模型

        Args:
            model_type: 模型类型

        Returns:
            Infinity 客户端实例

        Raises:
            ValueError: 如果模型未加载
        """
        if model_type not in self._models:
            raise ValueError(
                f"未找到模型: {model_type}。已加载的模型: {list(self._models.keys())}"
            )
        return self._models[model_type]

    async def get_config(self, model_type: str) -> ModelConfig:
        """
        获取模型配置

        Args:
            model_type: 模型类型

        Returns:
            模型配置对象

        Raises:
            ValueError: 如果模型未加载
        """
        if model_type not in self._configs:
            raise ValueError(f"未找到模型配置: {model_type}")
        return self._configs[model_type]

    async def _load_model(self, model_type: str, config: ModelConfig, model_path: str):
        """
        使用Infinity统一加载所有模型

        Args:
            model_type: 模型类型
            config: 模型配置
            model_path: 模型路径

        Returns:
            Infinity客户端对象
        """
        try:
            # 创建引擎参数
            engine_args = self._EngineArgs(
                model_name_or_path=model_path,
                engine=config.engine,
                device=config.device,
                dtype=config.dtype,
                trust_remote_code=config.trust_remote_code,
                compile=config.compile,
                embedding_dtype="float32",
                pooling_method=config.pooling_method,
                batch_size=config.batch_size,
            )

            # 创建并启动 Infinity 客户端
            client = self._AsyncEmbeddingEngine.from_args(engine_args)
            await client.astart()

            # 存储模型和配置
            self._models[model_type] = client
            self._configs[model_type] = config

            logger.info(f"✓ 模型加载成功: {config.name} (type={model_type})")
            return client

        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            import traceback

            logger.error(f"详细错误: {traceback.format_exc()}")
            raise RuntimeError(f"模型加载失败: {e}") from e

    async def unload_model(self, model_type: str):
        """
        卸载模型

        Args:
            model_type: 模型类型
        """
        async with self._lock:
            if model_type in self._models:
                client = self._models[model_type]
                config = self._configs[model_type]

                try:
                    await client.astop()
                    logger.info(f"模型已卸载: {model_type} ({config.name})")
                except Exception as e:
                    logger.error(f"卸载模型失败: {e}")

                del self._models[model_type]
                del self._configs[model_type]

    async def switch_model(self, model_type: str, new_config: ModelConfig) -> bool:
        """
        热切换模型

        加载新模型并验证成功后，切换到新模型，支持快速回滚。

        Args:
            model_type: 模型类型
            new_config: 新的模型配置

        Returns:
            是否切换成功
        """
        temp_model_type = f"{model_type}_temp"

        try:
            logger.info(f"正在热切换模型 {model_type} 到 {new_config.name}...")

            # 1. 加载新模型到临时位置
            logger.info(f"步骤1: 加载新模型到临时位置 {temp_model_type}")
            new_client = await self.register_model(temp_model_type, new_config)

            # 2. 验证新模型
            logger.info("步骤2: 验证新模型可用性")
            try:
                # 简单的验证：执行一次向量化
                test_result = await new_client.embed(["test"], input_type="text")
                if test_result and len(test_result) > 0:
                    logger.info("新模型验证成功")
                else:
                    raise ValueError("新模型验证失败：返回空结果")
            except Exception as e:
                raise RuntimeError(f"新模型验证失败: {e}") from e

            # 3. 卸载旧模型（如果存在）
            if model_type in self._models:
                logger.info("步骤3: 卸载旧模型")
                await self.unload_model(model_type)

            # 4. 重命名临时模型
            logger.info("步骤4: 切换到新模型")
            self._models[model_type] = new_client
            self._configs[model_type] = new_config

            # 5. 清理临时模型
            if temp_model_type in self._models:
                del self._models[temp_model_type]
            if temp_model_type in self._configs:
                del self._configs[temp_model_type]

            logger.info(f"模型切换成功: {model_type} -> {new_config.name}")
            return True

        except Exception as e:
            logger.error(f"模型切换失败: {e}")

            # 清理临时模型
            if temp_model_type in self._models:
                await self.unload_model(temp_model_type)

            logger.info("模型切换已回滚，继续使用旧模型")
            return False

    async def shutdown(self):
        """
        关闭所有模型
        """
        async with self._lock:
            logger.info("正在关闭所有模型...")

            for model_type, client in list(self._models.items()):
                try:
                    await client.astop()
                    logger.info(f"模型已关闭: {model_type}")
                except Exception as e:
                    logger.error(f"关闭模型失败: {model_type}, 错误: {e}")

            self._models.clear()
            self._configs.clear()
            self._initialized = False

            logger.info("所有模型已关闭")

    def get_loaded_models(self) -> List[str]:
        """
        获取已加载的模型列表

        Returns:
            已加载的模型类型列表
        """
        return list(self._models.keys())

    def is_initialized(self) -> bool:
        """
        检查模型管理器是否已初始化

        Returns:
            是否已初始化
        """
        return self._initialized


class EmbeddingService:
    """
    统一向量化服务

    提供统一的向量化接口，支持文本、图像、音频等多种类型的向量化。
    """

    def __init__(self, model_manager: ModelManager):
        self._model_manager = model_manager

    async def embed(
        self, model_type: str, inputs: Union[str, List[str]], input_type: str = "text"
    ) -> List[List[float]]:
        """
        统一向量化接口

        Args:
            model_type: 模型类型
            inputs: 输入数据，可以是字符串或字符串列表
            input_type: 输入类型（'text', 'image', 'audio'）

        Returns:
            向量列表，每个向量是一个 float 列表
        """
        client = await self._model_manager.get_model(model_type)

        # 确保输入是列表
        if isinstance(inputs, str):
            inputs = [inputs]

        # 过滤空输入
        inputs = [
            input_data for input_data in inputs if input_data and input_data.strip()
        ]

        if not inputs:
            return []

        # 使用 Infinity 进行向量化
        try:
            if input_type == "text":
                embeddings, _ = await client.embed(inputs)
            elif input_type == "image":
                # 处理图像输入：Infinity框架的image_embed需要图像数据
                # 读取本地图像文件为字节数据
                valid_images = []
                for image_path in inputs:
                    image_path = image_path.strip()
                    if os.path.exists(image_path):
                        # 读取图像文件为字节数据
                        try:
                            with open(image_path, "rb") as f:
                                image_bytes = f.read()
                            valid_images.append(image_bytes)
                            logger.debug(f"图像处理成功: {image_path}")
                        except Exception as e:
                            raise RuntimeError(f"读取图像文件失败: {image_path} - {e}")
                    else:
                        raise FileNotFoundError(f"图像文件不存在: {image_path}")

                if not valid_images:
                    raise ValueError("没有有效的图像文件")

                embeddings, _ = await client.image_embed(images=valid_images)
            elif input_type == "audio":
                # 使用AudioPreprocessor预处理音频（按照设计文档要求）
                # 预处理包括：采样率转换（48kHz）、单声道转换、WAV格式
                from src.services.media.audio_preprocessor import AudioPreprocessor

                audio_preprocessor = AudioPreprocessor()

                audio_data = []
                for audio_path in inputs:
                    audio_path = audio_path.strip()
                    if os.path.exists(audio_path):
                        # 使用AudioPreprocessor获取预处理后的音频bytes
                        audio_bytes = audio_preprocessor.get_preprocessed_audio_bytes(
                            audio_path
                        )
                        if audio_bytes:
                            audio_data.append(audio_bytes)
                            logger.debug(f"音频预处理成功: {audio_path}")
                        else:
                            raise RuntimeError(f"音频预处理失败: {audio_path}")
                    else:
                        raise FileNotFoundError(f"音频文件不存在: {audio_path}")

                embeddings, _ = await client.audio_embed(audios=audio_data)
            elif input_type == "video":
                # 使用VideoPreprocessor预处理视频（按照设计文档要求）
                # 预处理包括：视频分段、抽帧、转换为PIL Image
                from src.services.media.video_preprocessor import VideoPreprocessor

                video_preprocessor = VideoPreprocessor()

                video_frames = []
                for video_path in inputs:
                    video_path = video_path.strip()
                    if os.path.exists(video_path):
                        # 使用VideoPreprocessor获取视频帧
                        frames = video_preprocessor.get_video_frames(
                            video_path, max_frames=3
                        )
                        if frames:
                            video_frames.extend(frames)
                            logger.debug(
                                f"视频帧提取成功: {video_path}, {len(frames)}帧"
                            )
                        else:
                            raise RuntimeError(f"视频帧提取失败: {video_path}")
                    else:
                        raise FileNotFoundError(f"视频文件不存在: {video_path}")

                if not video_frames:
                    raise RuntimeError("未能提取任何视频帧")

                # 使用image_embed处理视频帧
                embeddings, _ = await client.image_embed(images=video_frames)
            else:
                raise ValueError(f"不支持的输入类型: {input_type}")

            # 如果返回的是list，直接返回
            if isinstance(embeddings, list) and all(
                isinstance(e, list) for e in embeddings
            ):
                return embeddings
            # 如果返回的是tensor，转换为list
            return [embedding.tolist() for embedding in embeddings]
        except Exception as e:
            logger.error(f"向量化失败: {e}")
            raise RuntimeError(f"向量化失败: {e}") from e

    async def embed_text(
        self, texts: Union[str, List[str]], model_type: str
    ) -> List[List[float]]:
        """
        文本向量化

        Args:
            texts: 文本数据
            model_type: 模型类型

        Returns:
            向量列表
        """
        return await self.embed(model_type, texts, input_type="text")

    async def embed_image(
        self, images: Union[str, List[str]], model_type: str
    ) -> List[List[float]]:
        """
        图像向量化

        Args:
            images: 图像文件路径列表
            model_type: 模型类型

        Returns:
            向量列表
        """
        return await self.embed(model_type, images, input_type="image")

    async def embed_audio(
        self, audios: Union[str, List[str]], model_type: str
    ) -> List[List[float]]:
        """
        音频向量化

        Args:
            audios: 音频文件路径列表
            model_type: 模型类型

        Returns:
            向量列表
        """
        return await self.embed(model_type, audios, input_type="audio")

    async def embed_video(
        self, videos: Union[str, List[str]], model_type: str
    ) -> List[List[float]]:
        """
        视频向量化

        Args:
            videos: 视频文件路径列表
            model_type: 模型类型

        Returns:
            向量列表
        """
        return await self.embed(model_type, videos, input_type="video")


def setup_offline_mode(model_cache_dir: str):
    """
    设置完全离线模式

    设置所有必要的环境变量，确保系统在完全离线模式下运行，不会尝试连接HuggingFace。

    Args:
        model_cache_dir: 模型缓存目录
    """
    logger.info(f"设置完全离线模式，模型缓存目录: {model_cache_dir}")

    Path(model_cache_dir).mkdir(parents=True, exist_ok=True)

    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["HF_DATASETS_OFFLINE"] = "1"
    os.environ["HF_HUB_OFFLINE"] = "1"

    os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
    os.environ["TRANSFORMERS_VERBOSITY"] = "error"
    os.environ["HF_HUB_DISABLE_IMPORT_ERROR"] = "1"

    os.environ["HF_HOME"] = model_cache_dir
    os.environ["HUGGINGFACE_HUB_CACHE"] = model_cache_dir

    os.environ["INFINITY_LOCAL_MODE"] = "1"
    os.environ["INFINITY_ANONYMOUS_USAGE_STATS"] = "0"

    os.environ["NO_PROXY"] = "*"
    os.environ["no_proxy"] = "*"

    logger.info("完全离线模式环境变量已设置")


# 全局模型管理器实例
_model_manager: Optional[ModelManager] = None
_embedding_service: Optional[EmbeddingService] = None


def get_model_manager() -> ModelManager:
    """
    获取全局模型管理器实例

    Returns:
        模型管理器实例

    Raises:
        RuntimeError: 如果模型管理器未初始化
    """
    global _model_manager
    if _model_manager is None:
        raise RuntimeError("模型管理器未初始化。请先调用 initialize_model_manager()")
    return _model_manager


def get_embedding_service() -> EmbeddingService:
    """
    获取全局向量化服务实例

    Returns:
        向量化服务实例

    Raises:
        RuntimeError: 如果向量化服务未初始化
    """
    global _embedding_service
    if _embedding_service is None:
        raise RuntimeError("向量化服务未初始化。请先调用 initialize_model_manager()")
    return _embedding_service


async def initialize_model_manager(
    configs: Dict[str, ModelConfig], model_cache_dir: Optional[str] = None
):
    """
    初始化全局模型管理器

    Args:
        configs: 模型配置字典
        model_cache_dir: 模型缓存目录，用于离线模式
    """
    global _model_manager, _embedding_service

    # 设置离线模式
    if model_cache_dir:
        setup_offline_mode(model_cache_dir)

    # 创建模型管理器
    _model_manager = ModelManager()
    await _model_manager.initialize(configs)

    # 创建向量化服务
    _embedding_service = EmbeddingService(_model_manager)

    logger.info("全局模型管理器初始化完成")


async def shutdown_model_manager():
    """
    关闭全局模型管理器
    """
    global _model_manager, _embedding_service

    if _model_manager:
        await _model_manager.shutdown()
        _model_manager = None

    if _embedding_service:
        _embedding_service = None

    logger.info("全局模型管理器已关闭")


if __name__ == "__main__":
    # 示例：使用模型管理器
    import asyncio

    async def example():
        """示例：使用模型管理器"""
        configs = {
            "image_model": ModelConfig(
                name="OFA-Sys/chinese-clip-vit-base-patch16",
                engine="torch",
                device="cpu",
                dtype="float32",
                embedding_dim=512,
                trust_remote_code=False,
                local_path="data/models/chinese-clip-vit-base-patch16",
            )
        }

        await initialize_model_manager(configs)

        service = get_embedding_service()
        embeddings = await service.embed_text(
            ["这是一个测试", "另一个测试"], "image_model"
        )
        print(f"向量化结果: {len(embeddings)} 个向量，每个维度: {len(embeddings[0])}")

        await shutdown_model_manager()

    asyncio.run(example())
