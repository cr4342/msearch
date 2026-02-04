"""
向量化引擎 - 统一使用Infinity调用模型
负责AI模型的加载、初始化和推理

本模块使用统一模型管理器（ModelManager）管理所有模型，实现配置驱动的模型加载和热切换。

参考文档：
- INFINITY_MODEL_MANAGEMENT_GUIDE.md: Infinity多模型管理完整指南
- model_manager.py: 统一模型管理器实现
"""

import os
import sys
from pathlib import Path

# 设置环境变量以支持完全离线模式
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"

# 禁用HuggingFace遥测
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ["HF_HUB_DISABLE_EXPERIMENTAL_WARNING"] = "1"

# 禁用网络请求
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"

# 设置统一模型缓存目录
hf_home = os.environ.get("HF_HOME", "data/models/huggingface_cache")
os.makedirs(hf_home, exist_ok=True)
os.environ["HF_HOME"] = hf_home
os.environ["HUGGINGFACE_HUB_CACHE"] = hf_home

# 禁用Infinity的遥测
os.environ["INFINITY_ANONYMOUS_USAGE_STATS"] = "0"

import numpy as np
import torch
from typing import Any, Dict, List, Optional, Union
import logging
from PIL import Image
import asyncio
import base64
import io
import time
import psutil
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager

from src.core.models.model_manager import (
    ModelManager,
    ModelConfig,
    EmbeddingService,
    initialize_model_manager,
    get_embedding_service,
    get_model_manager,
)

logger = logging.getLogger(__name__)


# ============================================================================
# 性能优化模块：内存管理、GPU管理和性能监控
# ============================================================================


@dataclass
class PerformanceMetrics:
    """性能指标"""

    operation: str
    duration_ms: float
    timestamp: float = field(default_factory=time.time)
    memory_used_mb: float = 0.0
    success: bool = True
    error_message: str = ""


class MemoryManager:
    """内存管理器 - 限制内存使用，自动管理内存"""

    def __init__(self, max_memory_mb: int = 4096):
        self.max_memory_mb = max_memory_mb
        self.process = psutil.Process()

    def get_memory_usage(self) -> float:
        """获取当前内存使用（MB）"""
        return self.process.memory_info().rss / (1024 * 1024)

    def get_memory_percent(self) -> float:
        """获取内存使用百分比"""
        return self.process.memory_percent()

    def check_memory_limit(self) -> bool:
        """检查是否超过内存限制"""
        return self.get_memory_usage() < self.max_memory_mb

    def is_memory_critical(self) -> bool:
        """是否内存紧张（超过90%限制）"""
        return self.get_memory_usage() >= self.max_memory_mb * 0.9

    def get_memory_status(self) -> Dict[str, Any]:
        """获取内存状态"""
        usage = self.get_memory_usage()
        return {
            "used_mb": usage,
            "limit_mb": self.max_memory_mb,
            "percent": (usage / self.max_memory_mb) * 100,
            "critical": self.is_memory_critical(),
            "ok": self.check_memory_limit(),
        }


class GPUMemoryManager:
    """GPU内存管理器 - 监控和管理GPU内存"""

    @staticmethod
    def is_available() -> bool:
        """检查GPU是否可用"""
        try:
            import torch

            return torch.cuda.is_available()
        except ImportError:
            return False

    @staticmethod
    def get_memory_info(device: int = 0) -> Optional[Dict[str, float]]:
        """获取GPU内存信息"""
        if not GPUMemoryManager.is_available():
            return None

        try:
            import torch

            torch.cuda.synchronize(device)

            total_memory = torch.cuda.get_device_properties(device).total_memory
            allocated = torch.cuda.memory_allocated(device)
            reserved = torch.cuda.memory_reserved(device)

            return {
                "allocated_gb": allocated / (1024**3),
                "cached_gb": reserved / (1024**3),
                "total_gb": total_memory / (1024**3),
                "free_gb": (total_memory - allocated) / (1024**3),
                "utilization_percent": (allocated / total_memory) * 100,
            }
        except Exception as e:
            logger.warning(f"获取GPU内存信息失败: {e}")
            return None

    @staticmethod
    def clear_cache(device: int = 0):
        """清理GPU缓存"""
        if GPUMemoryManager.is_available():
            try:
                import torch

                torch.cuda.empty_cache()
            except Exception as e:
                logger.warning(f"清理GPU缓存失败: {e}")

    @staticmethod
    def is_memory_sufficient(required_gb: float, device: int = 0) -> bool:
        """检查GPU内存是否充足"""
        info = GPUMemoryManager.get_memory_info(device)
        if info is None:
            return False
        return info["free_gb"] > required_gb


class DeviceManager:
    """设备管理器 - 从配置文件读取设备配置，支持CPU/GPU"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._current_device = self._read_device_from_config()

    def _read_device_from_config(self) -> str:
        """从配置文件中读取device参数（配置驱动原则）"""
        models_config = self.config.get("models", {})
        available_models = models_config.get("available_models", {})

        # 获取第一个活跃模型的device配置
        active_models = models_config.get("active_models", [])
        if active_models:
            first_model_id = active_models[0]
            model_config = available_models.get(first_model_id, {})
            device = model_config.get("device", "cpu")
            logger.info(f"从配置文件读取设备: {device} (模型: {first_model_id})")
            return device

        # 默认使用CPU
        logger.info("未配置活跃模型，使用CPU模式")
        return "cpu"

    def get_optimal_device(self, required_memory_gb: float = 2.0) -> str:
        """获取最优设备（直接从配置读取，不进行运行时检测）"""
        return self._current_device

    def get_device(self) -> str:
        """获取当前设备"""
        return self._current_device


class PerformanceMonitor:
    """性能监控器 - 收集和统计性能指标"""

    def __init__(self):
        self.metrics: List[PerformanceMetrics] = []
        self.memory_manager = MemoryManager()

    @contextmanager
    def measure(self, operation: str):
        """测量操作耗时"""
        start_time = time.time()
        memory_before = self.memory_manager.get_memory_usage()

        success = False
        error_msg = ""

        try:
            yield
            success = True
            error_msg = ""
        except Exception as e:
            success = False
            error_msg = str(e)
            raise
        finally:
            duration = (time.time() - start_time) * 1000
            memory_after = self.memory_manager.get_memory_usage()

            self.metrics.append(
                PerformanceMetrics(
                    operation=operation,
                    duration_ms=duration,
                    memory_used_mb=memory_after - memory_before,
                    success=success,
                    error_message=error_msg,
                )
            )

    def get_stats(self, operation: str = None) -> Dict[str, Any]:
        """获取性能统计"""
        if operation:
            ops = [m for m in self.metrics if m.operation == operation]
        else:
            ops = self.metrics

        if not ops:
            return {"count": 0}

        durations = [m.duration_ms for m in ops]
        successful = [m for m in ops if m.success]

        return {
            "count": len(ops),
            "avg_ms": sum(durations) / len(durations),
            "min_ms": min(durations),
            "max_ms": max(durations),
            "success_rate": len(successful) / len(ops) * 100 if ops else 0,
        }

    def get_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        return {
            "total_operations": len(self.metrics),
            "memory_status": self.memory_manager.get_memory_status(),
            "operation_stats": self.get_stats(),
        }


class BatchOptimizer:
    """批处理器 - 根据内存动态调整批处理大小"""

    def __init__(self, config: Dict[str, Any], base_batch_size: int = 8):
        self.config = config
        self.base_batch_size = base_batch_size
        self.current_batch_size = base_batch_size
        self.memory_manager = MemoryManager()

    def get_optimal_batch_size(self) -> int:
        """获取最优批处理大小"""
        status = self.memory_manager.get_memory_status()
        memory_percent = status["percent"]

        if memory_percent > 80:
            self.current_batch_size = max(1, int(self.base_batch_size * 0.5))
        elif memory_percent > 60:
            self.current_batch_size = max(2, int(self.base_batch_size * 0.75))
        elif memory_percent < 40:
            self.current_batch_size = min(16, int(self.base_batch_size * 1.25))
        else:
            self.current_batch_size = self.base_batch_size

        return self.current_batch_size


class EmbeddingEngine:
    """向量化引擎 - 统一使用Infinity调用模型（性能优化版）

    本类使用统一模型管理器（ModelManager）管理所有模型，实现配置驱动的模型加载和热切换。

    主要特性：
    - 配置驱动的模型管理
    - 支持多模型同时加载
    - 统一的向量化接口
    - 完整的离线模式支持
    - 性能优化：懒加载、内存管理、GPU管理
    """

    def __init__(self, config: Dict[str, Any]):
        """
        初始化向量化引擎（性能优化版 - 懒加载 + 后台加载）

        Args:
            config: 配置字典
        """
        self.config = config

        # 获取模型配置
        self.models_config = config.get("models", {})
        self.infinity_config = self.models_config.get("infinity_config", {})

        # 离线模式配置
        self.offline_enabled = self.infinity_config.get("enable_offline_mode", True)

        # 模型管理器（使用统一模型管理器）
        self._model_manager: Optional[ModelManager] = None
        self._embedding_service: Optional[EmbeddingService] = None

        # 模型配置对象字典
        self._model_configs: Dict[str, ModelConfig] = {}

        # 全局事件循环（优化：避免重复创建）
        self._event_loop = None

        # ================================================================
        # 性能优化：懒加载机制
        # ================================================================
        self._models_loaded = False  # 模型是否已加载
        self._load_in_progress = False  # 是否正在加载
        self._load_future = None  # 后台加载任务

        # 后台线程加载器
        self._executor = ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="model_loader"
        )

        # 性能监控
        self._perf_monitor = PerformanceMonitor()
        self._memory_manager = MemoryManager(
            max_memory_mb=config.get("system", {}).get("max_memory_mb", 4096)
        )

        # 设备管理器
        self._device_manager = DeviceManager(config)

        # 批处理优化器
        batch_size = (
            self.models_config.get("available_models", {})
            .get(self._get_default_model_id(), {})
            .get("batch_size", 8)
        )
        self._batch_optimizer = BatchOptimizer(config, base_batch_size=batch_size)

        # 模型最后使用时间（用于自动卸载）
        self._model_last_used: Dict[str, float] = {}
        self._auto_unload_enabled = self.models_config.get("auto_unload_enabled", False)
        self._unload_after_seconds = self.models_config.get("unload_after_seconds", 300)

        # 初始化模型配置（从配置文件读取）
        self._init_model_configs()

        logger.info(
            f"向量化引擎初始化完成，配置驱动模式，模型数量: {len(self._model_configs)}"
        )
        logger.info(f"性能优化已启用：懒加载={True}, 后台加载={True}, 内存管理={True}")

    def _init_model_configs(self):
        """初始化模型配置对象（完全配置驱动）"""
        # 使用ModelManager的静态方法从config.yml格式加载配置
        self._model_configs = ModelManager.load_configs_from_yaml(self.models_config)

        # 设置默认模型类型
        self._default_image_model = "chinese_clip_base"
        self._default_text_model = "chinese_clip_base"  # 文本搜索使用相同的CLIP模型
        self._default_audio_model = "audio_model"

        # 设置默认模型
        active_models = self.models_config.get("active_models", [])
        if active_models:
            # 第一个活跃模型作为默认图像/视频/文本模型
            self._default_image_model = active_models[0]
            self._default_text_model = active_models[0]  # 文本使用相同的模型
            # 查找音频模型
            for model_id in active_models:
                model_config = self.models_config.get("available_models", {}).get(
                    model_id, {}
                )
                if (
                    "audio" in model_id.lower()
                    or "clap" in model_config.get("model_name", "").lower()
                ):
                    self._default_audio_model = model_id
                    break

        logger.info(f"模型配置加载完成，模型数量: {len(self._model_configs)}")
        logger.info(f"默认图像/视频模型: {self._default_image_model}")
        logger.info(f"默认文本模型: {self._default_text_model}")
        logger.info(f"默认音频模型: {self._default_audio_model}")

    def _get_default_model_id(self) -> str:
        """获取默认模型ID"""
        active_models = self.models_config.get("active_models", [])
        if active_models:
            return active_models[0]
        return "chinese_clip_base"

    # ================================================================
    # 性能优化：懒加载机制
    # ================================================================

    async def _ensure_models_loaded(self):
        """确保模型已加载（懒加载机制）"""
        if self._models_loaded:
            return

        if self._load_in_progress:
            # 等待正在进行的加载完成
            while self._load_in_progress:
                await asyncio.sleep(0.1)
            return

        await self._load_models()

    async def _load_models(self):
        """加载模型（同步，在后台线程执行）"""
        self._load_in_progress = True
        try:
            logger.info("开始加载模型...")

            # 同步加载模型
            self._model_manager = ModelManager()
            await self._model_manager.initialize(self._model_configs)
            self._embedding_service = EmbeddingService(self._model_manager)

            self._models_loaded = True
            logger.info("模型加载完成")

        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            raise
        finally:
            self._load_in_progress = False

    def start_background_load(self):
        """后台开始加载模型（不阻塞）"""
        if self._models_loaded or self._load_in_progress:
            return

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        def sync_load():
            """同步加载"""
            try:
                loop.run_until_complete(self._load_models())
            except Exception as e:
                logger.error(f"后台模型加载失败: {e}")
            finally:
                loop.close()

        # 在后台线程执行
        self._executor.submit(sync_load)
        logger.info("后台模型加载已启动")

    async def wait_for_loading(self, timeout: float = 30.0) -> bool:
        """等待模型加载完成

        Args:
            timeout: 超时时间（秒）

        Returns:
            是否加载成功
        """
        start_time = time.time()

        while self._load_in_progress:
            if time.time() - start_time > timeout:
                logger.warning("模型加载超时")
                return False
            await asyncio.sleep(0.1)

        return self._models_loaded

    def is_loaded(self) -> bool:
        """检查模型是否已加载"""
        return self._models_loaded

    def is_loading(self) -> bool:
        """检查模型是否正在加载"""
        return self._load_in_progress

    # ================================================================
    # 性能优化：自动卸载机制
    # ================================================================

    def _mark_model_used(self, model_id: str):
        """标记模型已被使用"""
        self._model_last_used[model_id] = time.time()

    def _check_and_unload_idle_models(self):
        """检查并卸载空闲模型"""
        if not self._auto_unload_enabled:
            return

        current_time = time.time()
        models_to_unload = []

        for model_id, last_used in self._model_last_used.items():
            idle_time = current_time - last_used

            if idle_time > self._unload_after_seconds:
                models_to_unload.append(model_id)

        for model_id in models_to_unload:
            logger.info(f"自动卸载空闲模型: {model_id}")
            if self._model_manager:
                # 移除模型引用
                self._model_last_used.pop(model_id, None)

    # ================================================================
    # 性能优化：内存管理
    # ================================================================

    def get_memory_status(self) -> Dict[str, Any]:
        """获取内存状态"""
        return self._memory_manager.get_memory_status()

    def check_memory_and_adapt(self) -> bool:
        """检查内存并调整策略

        Returns:
            是否需要降低处理强度
        """
        status = self._memory_manager.get_memory_status()

        if status["critical"]:
            logger.warning(f"内存使用率: {status['percent']:.1f}%，建议降低处理强度")
            # 清理GPU缓存
            GPUMemoryManager.clear_cache()
            return True

        return False

    # ================================================================
    # 性能优化：性能监控
    # ================================================================

    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        return self._perf_monitor.get_summary()

    @contextmanager
    def monitor_operation(self, operation: str):
        """监控操作性能"""
        with self._perf_monitor.measure(operation):
            yield

    # ================================================================
    # 性能优化：批处理优化
    # ================================================================

    def get_optimal_batch_size(self) -> int:
        """获取最优批处理大小"""
        return self._batch_optimizer.get_optimal_batch_size()

    async def _get_event_loop(self) -> asyncio.AbstractEventLoop:
        """
        获取当前事件循环（避免创建新的事件循环）

        Returns:
            当前事件循环实例
        """
        # 使用当前的事件循环，避免创建新的事件循环
        try:
            return asyncio.get_running_loop()
        except RuntimeError:
            # 如果没有运行中的事件循环（例如在同步上下文中），创建一个新的事件循环
            if self._event_loop is None or self._event_loop.is_closed():
                self._event_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._event_loop)
            return self._event_loop

    async def _get_model_client(self, model_type: str = None):
        """
        获取模型客户端（使用统一模型管理器，基于Infinity框架）

        Args:
            model_type: 模型类型，默认为图片模型

        Returns:
            模型客户端实例
        """
        if model_type is None:
            model_type = self._default_text_model  # 使用文本模型进行文本向量化

        if self._model_manager is None:
            try:
                logger.info("初始化统一模型管理器...")

                # 创建模型管理器
                self._model_manager = ModelManager()

                # 初始化模型管理器（加载所有配置的模型）
                await self._model_manager.initialize(self._model_configs)

                # 创建向量化服务
                self._embedding_service = EmbeddingService(self._model_manager)

                logger.info("统一模型管理器初始化完成")
                logger.info(f"已加载的模型: {self._model_manager.get_loaded_models()}")
            except Exception as e:
                logger.error(f"初始化模型管理器失败: {e}")
                import traceback

                logger.error(f"详细错误: {traceback.format_exc()}")
                raise RuntimeError(f"初始化模型管理器失败: {e}") from e

        # 获取指定类型的模型
        if model_type not in self._model_manager.get_loaded_models():
            raise ValueError(
                f"未找到模型: {model_type}。已加载的模型: {self._model_manager.get_loaded_models()}"
            )

        return await self._model_manager.get_model(model_type)

    async def _ensure_embedding_service(self):
        """
        确保向量化服务已初始化

        Raises:
            RuntimeError: 如果初始化失败
        """
        if self._embedding_service is None:
            await self._get_model_client()

        if self._embedding_service is None:
            raise RuntimeError("向量化服务初始化失败")

    def _validate_model_integrity(self, model_path: str) -> bool:
        """
        验证模型完整性

        Args:
            model_path: 模型路径

        Returns:
            模型是否完整
        """
        required_files = ["config.json", "tokenizer.json", "tokenizer_config.json"]

        # 检查主要文件是否存在
        for file in required_files:
            file_path = os.path.join(model_path, file)
            if not os.path.exists(file_path):
                logger.error(f"模型文件缺失: {file_path}")
                return False

        # 检查模型权重文件（包括adapter_model.safetensors）
        weight_files = [
            "pytorch_model.bin",
            "model.safetensors",
            "adapter_model.safetensors",
        ]
        has_weight_file = any(
            os.path.exists(os.path.join(model_path, wf)) for wf in weight_files
        )

        if not has_weight_file:
            logger.error(f"模型权重文件缺失: {model_path}")
            return False

        logger.info(f"模型完整性验证通过: {model_path}")
        return True

    async def initialize(self) -> bool:
        """
        初始化向量化引擎（异步，懒加载模式）

        注意：此方法只执行必要的初始化，模型实际加载延迟到首次使用时

        Returns:
            是否成功
        """
        try:
            logger.info("向量化引擎初始化（懒加载模式）")
            logger.info("模型将在首次使用时自动加载")

            # 检查内存状态
            memory_status = self.get_memory_status()
            logger.info(
                f"内存状态: 使用 {memory_status['used_mb']:.1f}MB / 限制 {memory_status['limit_mb']}MB"
            )

            # 检查GPU状态
            if GPUMemoryManager.is_available():
                gpu_info = GPUMemoryManager.get_memory_info()
                if gpu_info:
                    logger.info(
                        f"GPU状态: 已用 {gpu_info['allocated_gb']:.2f}GB / 总计 {gpu_info['total_gb']:.2f}GB"
                    )

            return True
        except Exception as e:
            logger.error(f"向量化引擎初始化失败: {e}")
            import traceback

            logger.error(f"详细错误: {traceback.format_exc()}")
            return False

    async def preload_models(self) -> bool:
        """
        预加载所有模型（可选，用于需要立即使用模型的场景）

        Returns:
            是否成功
        """
        try:
            await self._load_models()
            logger.info("模型预加载完成")
            return True
        except Exception as e:
            logger.error(f"模型预加载失败: {e}")
            return False

    async def shutdown(self) -> None:
        """关闭向量化引擎（异步）"""
        try:
            # 关闭统一模型管理器
            if self._model_manager:
                await self._model_manager.shutdown()
                self._model_manager = None
                self._embedding_service = None
                logger.info("统一模型管理器已关闭")

            # 关闭事件循环
            if self._event_loop and not self._event_loop.is_closed():
                self._event_loop.close()
                self._event_loop = None
                logger.info("事件循环已关闭")

            logger.info("向量化引擎已关闭")
        except Exception as e:
            logger.error(f"关闭向量化引擎失败: {e}")

        async def embed_text(self, text: str, model_type: str = None) -> List[float]:
            """

            文本向量化（使用统一的EmbeddingService，基于Infinity框架）



            支持的模型：OFA-Sys/chinese-clip-vit-* 系列



            Args:

                text: 文本内容

                model_type: 模型类型，默认为图片模型



            Returns:

                向量嵌入



            Raises:

                ValueError: 文本为空

                RuntimeError: 模型未初始化

            """

            if not text or not text.strip():

                raise ValueError("文本内容不能为空")

            if model_type is None:

                model_type = self._default_image_model

            with self.monitor_operation(f"embed_text_{model_type}"):

                try:

                    # 懒加载：确保模型已加载

                    await self._ensure_models_loaded()

                    # 标记模型使用时间

                    self._mark_model_used(model_type)

                    # 检查内存状态

                    self.check_memory_and_adapt()

                    # 使用统一的EmbeddingService

                    embedding = await self._embedding_service.embed_text(
                        [text], model_type
                    )

                    result = embedding[0]

                    logger.debug(f"文本向量化成功: {text[:50]}..., 模型: {model_type}")

                    return result

                except ValueError as e:

                    logger.error(f"文本向量化参数错误: {e}")

                    raise

                except Exception as e:

                    logger.error(f"文本向量化失败: {e}")

                    raise RuntimeError(f"文本向量化失败: {e}") from e

    async def embed_texts(
        self, texts: List[str], model_type: str = None
    ) -> List[List[float]]:
        """
        批量文本向量化（使用统一的EmbeddingService，基于Infinity框架）

        支持的模型：OFA-Sys/chinese-clip-vit-* 系列

        Args:
            texts: 文本内容列表
            model_type: 模型类型，默认为图片模型

        Returns:
            向量嵌入列表

        Raises:
            ValueError: 文本列表为空
            RuntimeError: 模型未初始化
        """
        if not texts:
            raise ValueError("文本列表不能为空")

        if model_type is None:
            model_type = self._default_image_model

        with self.monitor_operation(f"embed_texts_{model_type}"):
            try:
                # 懒加载：确保模型已加载
                await self._ensure_models_loaded()

                # 标记模型使用时间
                self._mark_model_used(model_type)

                # 动态调整批处理大小
                optimal_batch_size = self.get_optimal_batch_size()

                # 分批处理
                all_embeddings = []
                for i in range(0, len(texts), optimal_batch_size):
                    batch = texts[i : i + optimal_batch_size]

                    # 检查内存状态
                    self.check_memory_and_adapt()

                    embedding = await self._embedding_service.embed_text(
                        batch, model_type
                    )
                    all_embeddings.extend(embedding)

                logger.debug(
                    f"批量文本向量化成功: {len(texts)}个文本, 模型: {model_type}"
                )
                return all_embeddings
            except ValueError as e:
                logger.error(f"批量文本向量化参数错误: {e}")
                raise
            except Exception as e:
                logger.error(f"批量文本向量化失败: {e}")
                raise RuntimeError(f"批量文本向量化失败: {e}") from e

    async def embed_image(self, image_path: str, model_type: str = None) -> List[float]:
        """
        图像向量化（使用统一的EmbeddingService，基于Infinity框架）

        支持的模型：OFA-Sys/chinese-clip-vit-* 系列

        Args:
            image_path: 图像文件路径
            model_type: 模型类型，默认为图片模型

        Returns:
            向量嵌入

        Raises:
            FileNotFoundError: 图像文件不存在
            ValueError: 图像格式不支持
            RuntimeError: 模型未初始化
        """
        embeddings = await self.embed_images([image_path], model_type)
        return embeddings[0]

    async def embed_images(
        self, image_paths: Union[str, List[str]], model_type: str = None
    ) -> List[List[float]]:
        """
        批量图像向量化（使用统一的EmbeddingService，基于Infinity框架）

        支持的模型：OFA-Sys/chinese-clip-vit-* 系列

        Args:
            image_paths: 图像文件路径或路径列表
            model_type: 模型类型，默认为图片模型

        Returns:
            向量嵌入列表

        Raises:
            FileNotFoundError: 图像文件不存在
            ValueError: 图像格式不支持
            RuntimeError: 模型未初始化
        """
        if isinstance(image_paths, str):
            image_paths = [image_paths]

        if not image_paths:
            raise ValueError("图像路径列表不能为空")

        if model_type is None:
            model_type = self._default_image_model

        with self.monitor_operation(f"embed_images_{model_type}"):
            try:
                # 验证图像文件存在
                for image_path in image_paths:
                    if not os.path.exists(image_path):
                        raise FileNotFoundError(f"图像文件不存在: {image_path}")

                # 懒加载：确保模型已加载
                await self._ensure_models_loaded()

                # 标记模型使用时间
                self._mark_model_used(model_type)

                # 使用EmbeddingService统一向量化接口（按照设计文档要求）
                # 预处理在ImagePreprocessor中完成，这里直接传递文件路径
                embeddings = await self._embedding_service.embed(
                    model_type, image_paths, input_type="image"
                )

                logger.debug(
                    f"批量图像向量化成功: {len(image_paths)}个图像, 模型: {model_type}"
                )
                return embeddings
            except FileNotFoundError as e:
                logger.error(f"图像文件不存在: {e}")
                raise
            except ValueError as e:
                logger.error(f"图像向量化参数错误: {e}")
                raise
            except Exception as e:
                logger.error(f"图像向量化失败: {e}")
                import traceback

                logger.error(f"详细错误: {traceback.format_exc()}")
                raise RuntimeError(f"图像向量化失败: {e}") from e

    async def embed_video_segment(
        self,
        video_path: str,
        start_time: float = 0.0,
        end_time: Optional[float] = None,
        aggregation: str = "mean",
    ) -> List[float]:
        """
        视频片段向量化（使用统一的EmbeddingService，基于Infinity框架）

        注意：视频预处理（分段、抽帧）应该在VideoPreprocessor中完成
        这里假设输入视频已经过预处理，直接调用model_manager进行向量化

        Args:
            video_path: 视频文件路径
            start_time: 开始时间（秒）
            end_time: 结束时间（秒）
            aggregation: 特征聚合策略（mean/max/weighted）

        Returns:
            向量嵌入

        Raises:
            FileNotFoundError: 视频文件不存在
            ValueError: 无效的视频片段时长
            RuntimeError: 模型未初始化
        """
        with self.monitor_operation(f"embed_video_segment"):
            try:
                if not os.path.exists(video_path):
                    raise FileNotFoundError(f"视频文件不存在: {video_path}")

                # 懒加载：确保模型已加载
                await self._ensure_models_loaded()

                # 标记模型使用时间
                self._mark_model_used(self._default_image_model)

                # 检查内存状态
                self.check_memory_and_adapt()

                # 使用统一的EmbeddingService进行视频向量化
                # model_manager的embed方法会使用VideoPreprocessor进行预处理
                embedding = await self._embedding_service.embed(
                    self._default_image_model, [video_path], input_type="video"
                )
                result = embedding[0]

                logger.debug(
                    f"视频片段向量化成功: {video_path} ({start_time}s-{end_time}s)"
                )
                return result
            except FileNotFoundError as e:
                logger.error(f"视频文件不存在: {e}")
                raise
            except ValueError as e:
                logger.error(f"视频向量化参数错误: {e}")
                raise
            except RuntimeError as e:
                logger.error(f"视频片段向量化失败: {e}")
                raise

    async def embed_video(self, video_path: str) -> List[float]:
        """
        视频向量化（使用统一的EmbeddingService，基于Infinity框架）

        支持的模型：OFA-Sys/chinese-clip-vit-* 系列

        Args:
            video_path: 视频文件路径

        Returns:
            向量嵌入

        Raises:
            FileNotFoundError: 视频文件不存在
            RuntimeError: 模型未初始化
        """
        with self.monitor_operation("embed_video"):
            try:
                if not os.path.exists(video_path):
                    raise FileNotFoundError(f"视频文件不存在: {video_path}")

                # 直接调用embed_video_segment，由它调用model_manager进行预处理和向量化
                return await self.embed_video_segment(video_path, 0.0, 5.0)
            except FileNotFoundError as e:
                logger.error(f"视频文件不存在: {e}")
                raise
            except Exception as e:
                logger.error(f"视频向量化失败: {e}")
                raise RuntimeError(f"视频向量化失败: {e}") from e

    async def embed_audio(
        self,
        audio_path: str,
        model_type: str = None,
        is_text_query: bool = False,
    ) -> List[float]:
        """
        音频向量化（使用统一的EmbeddingService，基于Infinity框架）

        支持两种模式：
        1. 音频文件向量化（默认）：将音频文件转换为向量
        2. 文本查询跨模态检索：使用CLAP模型将文本查询转换为音频向量空间

        Args:
            audio_path: 音频文件路径 或 文本查询
            model_type: 模型类型，默认为音频模型
            is_text_query: 是否为文本查询（用于跨模态检索）

        Returns:
            向量嵌入

        Raises:
            FileNotFoundError: 音频文件不存在
            ValueError: 音频格式不支持
            RuntimeError: 模型未初始化
        """
        if model_type is None:
            model_type = self._default_audio_model

        with self.monitor_operation(f"embed_audio_{model_type}"):
            try:
                if not is_text_query and not os.path.exists(audio_path):
                    raise FileNotFoundError(f"音频文件不存在: {audio_path}")

                await self._ensure_models_loaded()

                self._mark_model_used(model_type)

                self.check_memory_and_adapt()

                if is_text_query:
                    embeddings = await self._embedding_service.embed(
                        model_type, [audio_path], input_type="text"
                    )
                else:
                    embeddings = await self._embedding_service.embed(
                        model_type, [audio_path], input_type="audio"
                    )
                result = embeddings[0]

                mode = "text_query" if is_text_query else "audio_file"
                logger.debug(f"音频向量化成功: {mode}, 模型: {model_type}")
                return result
            except FileNotFoundError as e:
                logger.error(f"音频文件不存在: {e}")
                raise
            except ValueError as e:
                logger.error(f"音频向量化参数错误: {e}")
                raise
            except RuntimeError as e:
                logger.error(f"音频向量化失败: {e}")
                raise
            except Exception as e:
                logger.error(f"音频向量化失败: {e}")
                raise RuntimeError(f"音频向量化失败: {e}") from e

    def get_embedding_dim(self, model_type: str = None) -> int:
        """
        获取嵌入维度（基于Infinity框架）

        Args:
            model_type: 模型类型，默认为图片模型

        Returns:
            嵌入维度
        """
        if model_type is None:
            model_type = self._default_image_model

        if model_type in self._model_configs:
            return self._model_configs[model_type].embedding_dim
        else:
            return 512

    async def embed_text(self, text: str, model_type: str = None) -> List[float]:
        """
        文本向量化（使用统一的EmbeddingService，基于Infinity框架）

        支持的模型：OFA-Sys/chinese-clip-vit-* 系列

        Args:
            text: 文本内容
            model_type: 模型类型，默认为图片模型

        Returns:
            向量嵌入

        Raises:
            ValueError: 文本为空
            RuntimeError: 模型未初始化
        """
        if not text or not text.strip():
            raise ValueError("文本内容不能为空")

        if model_type is None:
            model_type = self._default_text_model  # 使用文本模型进行文本向量化

        with self.monitor_operation(f"embed_text_{model_type}"):
            try:
                # 懒加载：确保模型已加载
                await self._ensure_models_loaded()

                # 标记模型使用时间
                self._mark_model_used(model_type)

                # 检查内存状态
                self.check_memory_and_adapt()

                # 使用统一的EmbeddingService
                embedding = await self._embedding_service.embed_text([text], model_type)
                result = embedding[0]

                logger.debug(f"文本向量化成功: {text[:50]}..., 模型: {model_type}")
                return result
            except ValueError as e:
                logger.error(f"文本向量化参数错误: {e}")
                raise
            except Exception as e:
                logger.error(f"文本向量化失败: {e}")
                raise RuntimeError(f"文本向量化失败: {e}") from e

    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息（基于Infinity框架）

        Returns:
            模型信息字典
        """
        model_info = {}
        for model_type, model_config in self._model_configs.items():
            model_info[model_type] = {
                "model_name": model_config.name,
                "engine": model_config.engine,
                "device": model_config.device,
                "embedding_dim": model_config.embedding_dim,
                "batch_size": model_config.batch_size,
                "dtype": model_config.dtype,
            }

        model_info["total_models"] = len(self._model_configs)
        model_info["model_types"] = list(self._model_configs.keys())

        return model_info
