"""
嵌入引擎 - 使用Infinity Python-native模式统一管理AI模型，生成媒体内容向量
符合design.md中关于michaelfeil/infinity集成的要求
"""
import numpy as np
from typing import Dict, Any, List, Union
import logging
import os

logger = logging.getLogger(__name__)

try:
    from infinity_emb import AsyncEngineArray, EngineArgs
    INFINITY_AVAILABLE = True
except ImportError:
    INFINITY_AVAILABLE = False
    logger.warning("Infinity未安装，将使用模拟向量生成")


class EmbeddingEngine:
    """嵌入引擎 - 符合design.md中关于Python-native模式集成的要求"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化嵌入引擎
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 模型映射 - 根据内容类型选择对应的模型
        self.model_mapping = {
            'image': 'clip',
            'text': 'clip',
            'audio_music': 'clap',
            'audio_speech': 'whisper'
        }
        
        # 模型健康状态
        self.model_health = {
            'clip': False,
            'clap': False,
            'whisper': False
        }
        
        # 初始化Infinity引擎数组
        self.engine_array = None
        self._init_infinity_engine()
    
    def _init_infinity_engine(self):
        """初始化Infinity引擎 - 使用本地模型，不进行网络下载"""
        try:
            from infinity_emb import AsyncEngineArray, EngineArgs
            
            # 从配置中获取模型设置
            models_config = self.config.get('models', {})
            models_storage = self.config.get('models_storage', {})
            
            # 设置环境变量，强制使用离线模式
            os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'
            os.environ['TRANSFORMERS_OFFLINE'] = '1'  # 强制离线模式
            os.environ['HF_HUB_OFFLINE'] = '1'
            
            # 如果配置中指定了模型缓存目录，设置环境变量
            if models_storage.get('models_dir'):
                os.environ['TRANSFORMERS_CACHE'] = models_storage.get('models_dir')
                os.environ['HF_HOME'] = models_storage.get('models_dir')
            
            # 初始化成功的模型列表
            successful_models = []
            
            # 动态加载配置中指定的模型
            model_loaders = {
                'clip': {
                    'config_key': 'clip',
                    'default_path': './data/models/clip',
                    'default_batch_size': 16
                },
                'clap': {
                    'config_key': 'clap', 
                    'default_path': './data/models/clap',
                    'default_batch_size': 8
                },
                'whisper': {
                    'config_key': 'whisper',
                    'default_path': './data/models/whisper',
                    'default_batch_size': 4
                }
            }
            
            for model_name, loader in model_loaders.items():
                model_config = models_config.get(loader['config_key'], {})
                
                # 如果配置中明确指定了该模型，或者配置不为空，则尝试加载
                if model_config or loader['config_key'] in models_config:
                    model_path = model_config.get('local_path', model_config.get('model_name', loader['default_path']))
                    
                    # 确保使用绝对路径
                    if not os.path.isabs(model_path):
                        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                        # 移除开头的./或../，避免重复路径
                        if model_path.startswith('./'):
                            model_path = model_path[2:]
                        elif model_path.startswith('../'):
                            model_path = model_path[3:]
                        model_path = os.path.join(project_root, model_path)
                    
                    try:
                        # 检查本地模型是否存在
                        if os.path.exists(model_path):
                            # 特殊处理CLAP模型的safetensors文件问题
                            if model_name == 'clap':
                                safetensors_path = os.path.join(model_path, 'model.safetensors')
                                if os.path.exists(safetensors_path):
                                    # 检查safetensors文件是否可用
                                    try:
                                        import safetensors
                                        with open(safetensors_path, 'rb') as f:
                                            safetensors.torch.load_file(f)
                                        self.logger.info(f"CLAP模型使用safetensors格式")
                                    except Exception:
                                        # safetensors文件有问题，使用pytorch格式
                                        self.logger.warning(f"CLAP模型safetensors文件有问题，使用pytorch格式")
                                        # 确保pytorch_model.bin存在
                                        if not os.path.exists(os.path.join(model_path, 'pytorch_model.bin')):
                                            raise FileNotFoundError("CLAP模型pytorch_model.bin文件不存在")
                            
                            engine_args = EngineArgs(
                                model_name_or_path=model_path,
                                device=model_config.get('device', 'cpu'),
                                model_warmup=True,
                                batch_size=model_config.get('batch_size', loader['default_batch_size']),
                                dtype='float32'
                            )
                            
                            successful_models.append(engine_args)
                            self.model_health[model_name] = True
                            self.logger.info(f"本地{model_name.upper()}模型 {model_path} 初始化成功")
                        else:
                            self.logger.warning(f"本地{model_name.upper()}模型路径不存在: {model_path}")
                            raise FileNotFoundError(f"{model_name.upper()}模型路径不存在: {model_path}")
                        
                    except Exception as e:
                        self.logger.error(f"本地{model_name.upper()}模型初始化失败: {e}")
                        # 不尝试从网络下载，直接标记为失败
            
            # 如果有成功加载的模型，创建引擎数组
            if successful_models:
                try:
                    # 使用AsyncEngineArray.from_args的正确方式
                    self.engine_array = AsyncEngineArray.from_args(successful_models)
                    self.logger.info(f"Infinity引擎初始化完成，成功加载 {len(successful_models)} 个本地模型")
                except Exception as e:
                    self.logger.error(f"创建引擎数组失败: {e}")
                    self.engine_array = None
                    raise RuntimeError(f"创建引擎数组失败: {e}")
            else:
                self.logger.error("没有成功加载任何本地模型")
                raise RuntimeError("无法加载本地模型，请检查模型文件是否存在且路径配置正确")
                
        except Exception as e:
            self.logger.error(f"初始化Infinity引擎失败: {e}")
            raise RuntimeError(f"初始化嵌入引擎失败: {e}")
    
    async def embed_content(self, content: Union[str, np.ndarray, List[np.ndarray]], 
                           content_type: str) -> np.ndarray:
        """
        统一的内容向量化接口 - 改进版本，支持批处理和更好的错误处理
        
        Args:
            content: 内容数据(文本字符串、图片数据或音频数据)
            content_type: 内容类型 ('image', 'text', 'audio_music', 'audio_speech')
            
        Returns:
            向量表示 (512维)
        """
        if self.engine_array is not None:
            try:
                model = self._get_model_for_content_type(content_type)
                if not model:
                    raise ValueError(f"不支持的内容类型: {content_type}")
                
                # 检查模型健康状态
                if not self.model_health.get(model, False):
                    raise RuntimeError(f"模型 {model} 不可用")
                
                self.logger.debug(f"使用{model.upper()}模型生成向量: 内容类型={content_type}")
                
                # 预处理内容数据
                processed_content = self._preprocess_content(content, content_type)
                
                # 调用Infinity生成向量 - 使用具体的模型引擎和上下文管理器
                if model == 'clip':
                    # 找到CLIP引擎
                    clip_engine = None
                    for engine in self.engine_array:
                        # 检查引擎类型是否支持图像/文本嵌入
                        if hasattr(engine, 'embed') or hasattr(engine, 'image_embed'):
                            clip_engine = engine
                            break
                    
                    if clip_engine is None:
                        raise RuntimeError("未找到CLIP模型引擎")
                    
                    # 根据内容类型选择嵌入方法
                    if content_type in ['image', 'visual']:
                        # 对于图像内容，使用image_embed
                        if isinstance(processed_content, (list, tuple)):
                            result = await clip_engine.image_embed(processed_content)
                        else:
                            result = await clip_engine.image_embed([processed_content])
                    else:  # 文本类型
                        if isinstance(processed_content, (list, tuple)):
                            result = await clip_engine.embed(processed_content)
                        else:
                            result = await clip_engine.embed([processed_content])
                            
                    # 提取向量数据
                    if isinstance(result, tuple) and len(result) >= 1:
                        embeddings = result[0]
                    else:
                        embeddings = result
                        
                elif model == 'clap':
                    # 找到CLAP引擎
                    clap_engine = None
                    for engine in self.engine_array:
                        if hasattr(engine, 'audio_embed'):
                            clap_engine = engine
                            break
                    
                    if clap_engine is None:
                        raise RuntimeError("未找到CLAP模型引擎")
                    
                    # 对于音频内容
                    if isinstance(processed_content, (list, tuple)):
                        result = await clap_engine.audio_embed(processed_content)
                    else:
                        result = await clap_engine.audio_embed([processed_content])
                        
                    # 提取向量数据
                    if isinstance(result, tuple) and len(result) >= 1:
                        embeddings = result[0]
                    else:
                        embeddings = result
                        
                elif model == 'whisper':
                    # 找到Whisper引擎
                    whisper_engine = None
                    for engine in self.engine_array:
                        if hasattr(engine, 'transcribe'):
                            whisper_engine = engine
                            break
                    
                    if whisper_engine is None:
                        raise RuntimeError("未找到Whisper模型引擎")
                    
                    # 对于语音转录
                    if isinstance(processed_content, (list, tuple)):
                        result = await whisper_engine.transcribe(processed_content)
                    else:
                        result = await whisper_engine.transcribe([processed_content])
                        
                    # 提取向量数据
                    if isinstance(result, tuple) and len(result) >= 1:
                        embeddings = result[0]
                    else:
                        embeddings = result
                else:
                    raise RuntimeError(f"不支持的模型类型: {model}")
                
                # 提取向量 - 处理不同的返回格式
                if isinstance(embeddings, list) and len(embeddings) > 0:
                    # 如果是列表，取第一个元素
                    vector = embeddings[0]
                elif hasattr(embeddings, 'shape') and len(embeddings.shape) > 0:
                    # 如果是numpy数组，取第一个元素
                    vector = embeddings[0]
                else:
                    # 其他情况，直接使用
                    vector = embeddings
                
                # 确保返回的是numpy数组
                if not isinstance(vector, np.ndarray):
                    vector = np.array(vector)
                
                # 后处理向量
                processed_embeddings = self._postprocess_embeddings(vector, content_type)
                
                self.logger.debug(f"向量生成完成: 形状={processed_embeddings.shape}")
                return processed_embeddings
                
            except Exception as e:
                self.logger.error(f"使用Infinity生成向量失败: {e}")
                raise RuntimeError(f"向量生成失败: {e}")
        else:
            raise RuntimeError("嵌入引擎未正确初始化")
    
    def _preprocess_content(self, content: Union[str, np.ndarray, List[np.ndarray]], 
                             content_type: str) -> Union[str, np.ndarray, List[np.ndarray]]:
        """
        预处理内容数据
        
        Args:
            content: 原始内容
            content_type: 内容类型
            
        Returns:
            预处理后的内容
        """
        try:
            if content_type == 'text':
                # 文本预处理
                if isinstance(content, str):
                    # 清理文本，移除多余空白
                    content = content.strip()
                    if len(content) == 0:
                        content = "empty text"  # 避免空文本
                    return content
                else:
                    return str(content)
                    
            elif content_type == 'image':
                # 图片预处理
                if isinstance(content, np.ndarray):
                    # 确保图片格式正确
                    if content.dtype != np.float32:
                        content = content.astype(np.float32)
                    
                    # 归一化到0-1范围
                    if content.max() > 1.0:
                        content = content / 255.0
                    
                    # 确保是RGB格式
                    if len(content.shape) == 2:  # 灰度图
                        content = np.stack([content] * 3, axis=-1)
                    elif len(content.shape) == 3 and content.shape[2] == 4:  # RGBA
                        content = content[:, :, :3]
                    
                    return content
                else:
                    return content
                    
            elif content_type in ['audio_music', 'audio_speech']:
                # 音频预处理
                if isinstance(content, np.ndarray):
                    # 确保音频数据格式正确
                    if content.dtype != np.float32:
                        content = content.astype(np.float32)
                    
                    # 归一化音频
                    max_val = np.abs(content).max()
                    if max_val > 0:
                        content = content / max_val
                    
                    return content
                else:
                    return content
                    
            else:
                return content
                
        except Exception as e:
            self.logger.warning(f"内容预处理失败: {e}，使用原始内容")
            return content
    
    def _postprocess_embeddings(self, embeddings, content_type: str) -> np.ndarray:
        """
        后处理生成的向量
        
        Args:
            embeddings: 原始向量(可能是列表、numpy数组等)
            content_type: 内容类型
            
        Returns:
            处理后的向量
        """
        try:
            # 确保是numpy数组
            if not isinstance(embeddings, np.ndarray):
                embeddings = np.array(embeddings)
            
            # 确保向量是float32类型
            if embeddings.dtype != np.float32:
                embeddings = embeddings.astype(np.float32)
            
            # 确保向量被归一化(L2归一化)
            if len(embeddings.shape) == 1:
                # 单个向量
                norm = np.linalg.norm(embeddings)
                if norm > 0:
                    embeddings = embeddings / norm
            else:
                # 多个向量
                norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
                norms[norms == 0] = 1  # 避免除零
                embeddings = embeddings / norms
            
            return embeddings
            
        except Exception as e:
            self.logger.warning(f"向量后处理失败: {e}，使用原始向量")
            return embeddings
    
    def _mock_embed_content(self, content: Union[str, np.ndarray, List[np.ndarray]], 
                           content_type: str) -> np.ndarray:
        """
        模拟向量生成(用于测试或Infinity不可用时)
        
        Args:
            content: 内容数据
            content_type: 内容类型
            
        Returns:
            模拟向量 (512维)
        """
        logger.warning(f"使用模拟向量生成: 内容类型={content_type}")
        
        # 生成512维的随机向量(模拟)
        mock_vector = np.random.rand(512).astype(np.float32)
        
        # 标准化向量(L2归一化)
        mock_vector = mock_vector / np.linalg.norm(mock_vector)
        
        return mock_vector
    
    async def embed_image(self, images: Union[np.ndarray, List[np.ndarray], str, List[str]]) -> np.ndarray:
        """
        图片向量化

        Args:
            images: 图片数据 (单张图片、图片列表、图片路径或路径列表)

        Returns:
            图片向量
        """
        # 如果传入的是文件路径，转换为numpy数组
        if isinstance(images, str):
            # 单个路径
            from PIL import Image
            img = Image.open(images).convert('RGB')
            images = np.array(img).astype(np.float32) / 255.0
        elif isinstance(images, list) and len(images) > 0 and isinstance(images[0], str):
            # 路径列表
            from PIL import Image
            processed = []
            for path in images:
                img = Image.open(path).convert('RGB')
                processed.append(np.array(img).astype(np.float32) / 255.0)
            images = processed
        
        if self.engine_array is not None:
            try:
                # 查找CLIP模型用于图像向量化
                clip_engine = None
                for engine in self.engine_array:
                    if hasattr(engine, 'image_embed'):
                        clip_engine = engine
                        break
                
                if clip_engine is None:
                    raise RuntimeError("未找到支持图像嵌入的模型引擎")
                
                async with clip_engine:
                    if isinstance(images, list):
                        embeddings, usage = await clip_engine.image_embed(images)
                        return np.array(embeddings[0])
                    else:
                        embeddings, usage = await clip_engine.image_embed([images])
                        return np.array(embeddings[0])
            except Exception as e:
                self.logger.error(f"图像向量化失败: {e}")
                raise
        else:
            self.logger.error("嵌入引擎未正确初始化")
            raise RuntimeError("嵌入引擎未正确初始化")
    
    async def embed_text(self, text: str) -> np.ndarray:
        """
        文本向量化
        
        Args:
            text: 文本字符串
            
        Returns:
            文本向量
        """
        if self.engine_array is not None:
            try:
                # 查找支持文本嵌入的模型
                clip_engine = None
                for engine in self.engine_array:
                    if hasattr(engine, 'embed'):
                        clip_engine = engine
                        break
                
                if clip_engine is None:
                    raise RuntimeError("未找到支持文本嵌入的模型引擎")
                
                async with clip_engine:
                    embeddings, usage = await clip_engine.embed([text])
                    return np.array(embeddings[0])
            except Exception as e:
                self.logger.error(f"文本向量化失败: {e}")
                raise
        else:
            self.logger.error("嵌入引擎未正确初始化")
            raise RuntimeError("嵌入引擎未正确初始化")
    
    async def embed_audio_music(self, audio: np.ndarray) -> np.ndarray:
        """
        音乐音频向量化
        
        Args:
            audio: 音频数据
            
        Returns:
            音频向量
        """
        return await self.embed_content(audio, 'audio_music')
    
    async def embed_audio_speech(self, audio: np.ndarray) -> np.ndarray:
        """
        语音音频向量化
        
        Args:
            audio: 音频数据
            
        Returns:
            音频向量
        """
        return await self.embed_content(audio, 'audio_speech')
    
    async def transcribe_audio(self, audio: np.ndarray) -> str:
        """
        使用Whisper模型将音频转换为文本
        
        Args:
            audio: 音频数据
            
        Returns:
            转录文本
        """
        if self.engine_array is not None:
            try:
                # 检查Whisper模型是否可用
                if not self.model_health.get('whisper', False):
                    raise RuntimeError("Whisper模型不可用")
                
                # 查找Whisper引擎
                whisper_engine = None
                for engine in self.engine_array:
                    if hasattr(engine, 'transcribe'):
                        whisper_engine = engine
                        break
                
                if whisper_engine is None:
                    raise RuntimeError("未找到Whisper模型引擎")
                
                # 使用Whisper引擎进行转录
                async with whisper_engine:
                    transcription_result = await whisper_engine.transcribe([audio])
                
                # 提取转录文本
                if hasattr(transcription_result, 'segments'):
                    # 如果返回的是包含segments的对象
                    text_result = ' '.join([segment.text for segment in transcription_result.segments])
                    return text_result.strip()
                elif hasattr(transcription_result, 'text'):
                    return transcription_result.text
                elif isinstance(transcription_result, dict) and 'text' in transcription_result:
                    return transcription_result['text']
                elif isinstance(transcription_result, list) and len(transcription_result) > 0:
                    # 如果返回的是列表，取第一个元素
                    first_item = transcription_result[0]
                    if hasattr(first_item, 'text'):
                        return first_item.text
                    else:
                        return str(first_item)
                else:
                    # 如果返回的是字符串或其他格式
                    return str(transcription_result)
                    
            except Exception as e:
                self.logger.error(f"使用Whisper进行语音转文本失败: {e}")
                raise RuntimeError(f"语音转文本失败: {e}")
        else:
            raise RuntimeError("嵌入引擎未正确初始化")

    async def transcribe_speech(self, audio: np.ndarray) -> str:
        """
        使用Whisper模型将语音转换为文本（兼容方法）
        
        Args:
            audio: 音频数据
            
        Returns:
            转录文本
        """
        return await self.transcribe_audio(audio)
    
    def get_model_status(self) -> Dict[str, bool]:
        """
        获取模型状态
        
        Returns:
            模型健康状态字典
        """
        return self.model_health.copy()
    
    def is_model_available(self, model_name: str) -> bool:
        """
        检查指定模型是否可用
        
        Args:
            model_name: 模型名称 ('clip', 'clap', 'whisper')
            
        Returns:
            模型是否可用
        """
        return self.model_health.get(model_name, False)
    
    def _get_model_for_content_type(self, content_type: str) -> str:
        """
        根据内容类型获取对应的模型名称
        
        Args:
            content_type: 内容类型 ('image', 'text', 'audio_music', 'audio_speech')
            
        Returns:
            模型名称 ('clip', 'clap', 'whisper')
        """
        # 如果配置中只包含CLIP模型，则所有内容类型都使用CLIP
        configured_models = self.config.get('models', {})
        if 'clip' in configured_models and len(configured_models) == 1:
            # 只配置了CLIP模型，所有类型都使用CLIP
            return 'clip'
        
        # 否则使用默认的模型映射
        return self.model_mapping.get(content_type, 'clip')
    
    async def batch_embed_text(self, texts: List[str]) -> List[np.ndarray]:
        """
        批量文本向量化
        
        Args:
            texts: 文本列表
            
        Returns:
            向量列表
        """
        if not texts:
            return []
        
        # 如果支持批处理，使用批处理
        if self.engine_array is not None:
            try:
                # 使用支持文本嵌入的模型
                clip_engine = None
                for engine in self.engine_array:
                    if hasattr(engine, 'embed'):
                        clip_engine = engine
                        break
                
                if clip_engine is None:
                    raise RuntimeError("未找到支持文本嵌入的模型引擎")
                
                async with clip_engine:
                    embeddings, usage = await clip_engine.embed(texts)
                    
                    # 转换为numpy数组列表
                    return [np.array(embedding) for embedding in embeddings]
                    
            except Exception as e:
                self.logger.error(f"批量文本向量化失败: {e}")
        
        # 回退到逐个处理
        return [await self.embed_text(text) for text in texts]
    
    async def batch_embed_image(self, images: List[np.ndarray]) -> List[np.ndarray]:
        """
        批量图片向量化
        
        Args:
            images: 图片列表
            
        Returns:
            向量列表
        """
        if not images:
            return []
        
        # 如果支持批处理，使用批处理
        if self.engine_array is not None:
            try:
                # 使用支持图像嵌入的模型
                clip_engine = None
                for engine in self.engine_array:
                    if hasattr(engine, 'image_embed'):
                        clip_engine = engine
                        break
                
                if clip_engine is None:
                    raise RuntimeError("未找到支持图像嵌入的模型引擎")
                
                async with clip_engine:
                    embeddings, usage = await clip_engine.image_embed(images)
                    
                    # 转换为numpy数组列表
                    return [np.array(embedding) for embedding in embeddings]
                    
            except Exception as e:
                self.logger.error(f"批量图片向量化失败: {e}")
        
        # 回退到逐个处理
        result = []
        for image in images:
            try:
                result.append(await self.embed_image(image))
            except Exception as e:
                self.logger.error(f"单个图片向量化失败: {e}")
                # 添加零向量作为占位符
                result.append(np.zeros(512, dtype=np.float32))
        return result


# 全局嵌入引擎实例
_embedding_engine = None


def get_embedding_engine(config: Dict[str, Any] = None) -> EmbeddingEngine:
    """
    获取全局嵌入引擎实例
    
    Args:
        config: 配置字典，首次调用时需要提供
        
    Returns:
        嵌入引擎实例
    """
    global _embedding_engine
    if _embedding_engine is None:
        if config is None:
            raise ValueError("首次调用get_embedding_engine时必须提供config参数")
        _embedding_engine = EmbeddingEngine(config)
    return _embedding_engine


# 示例使用
if __name__ == "__main__":
    import asyncio
    
    # 配置示例
    config = {
        'features': {
            'enable_clip': True,
            'enable_clap': True,
            'enable_whisper': True
        },
        'models': {
            'clip_model': 'openai/clip-vit-base-patch32',
            'clap_model': 'laion/clap-htsat-fused',
            'whisper_model': 'openai/whisper-base'
        },
        'device': 'cpu'
    }
    
    # 创建引擎实例
    async def main():
        engine = get_embedding_engine(config)
        
        # 模拟图片向量化
        # image_data = np.random.rand(224, 224, 3).astype(np.float32)
        # image_vector = await engine.embed_image(image_data)
        # print(f"图片向量形状: {image_vector.shape}")
        
        # 模拟文本向量化
        # text_vector = await engine.embed_text("这是一段测试文本")
        # print(f"文本向量形状: {text_vector.shape}")
        
        # 模拟音频向量化
        # audio_data = np.random.rand(16000).astype(np.float32)  # 1秒音频数据
        # music_vector = await engine.embed_audio_music(audio_data)
        # speech_vector = await engine.embed_audio_speech(audio_data)
        # print(f"音乐向量形状: {music_vector.shape}")
        # print(f"语音向量形状: {speech_vector.shape}")
    
    # 运行异步主函数
    # asyncio.run(main())