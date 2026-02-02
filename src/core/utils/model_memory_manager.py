import asyncio
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ModelMemoryManager:
    """
    模型内存管理器

    负责管理模型的加载、卸载和缓存，优化内存使用。
    """

    def __init__(
        self, max_models_in_memory: int = 3, inactive_timeout: int = 300
    ):  # 5分钟不活跃超时
        """
        初始化模型内存管理器

        Args:
            max_models_in_memory: 内存中最大模型数量
            inactive_timeout: 不活跃模型超时时间（秒）
        """
        self.max_models_in_memory = max_models_in_memory
        self.inactive_timeout = inactive_timeout

        # 模型状态
        self._model_states: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

        # 清理任务
        self._cleanup_task: Optional[asyncio.Task] = None
        self._is_running = False

    async def track_model(self, model_type: str, model_size_gb: float):
        """
        跟踪已加载的模型

        Args:
            model_type: 模型类型
            model_size_gb: 模型大小（GB）
        """
        async with self._lock:
            self._model_states[model_type] = {
                "size_gb": model_size_gb,
                "last_used": datetime.now(),
                "usage_count": 0,
                "is_loaded": True,
            }

        logger.info(f"模型已跟踪: {model_type} ({model_size_gb:.2f}GB)")

    async def mark_model_used(self, model_type: str):
        """
        标记模型已使用

        Args:
            model_type: 模型类型
        """
        if model_type in self._model_states:
            self._model_states[model_type]["last_used"] = datetime.now()
            self._model_states[model_type]["usage_count"] += 1

    async def get_unload_candidates(self) -> List[str]:
        """
        获取可卸载的候选模型

        Returns:
            可卸载的模型类型列表
        """
        async with self._lock:
            # 1. 找出不活跃的模型（超过超时时间）
            inactive_models = []
            now = datetime.now()

            for model_type, state in self._model_states.items():
                if state["is_loaded"]:
                    inactive_time = (now - state["last_used"]).total_seconds()
                    if inactive_time > self.inactive_timeout:
                        inactive_models.append(model_type)

            # 2. 如果没有不活跃模型，按使用频率排序
            if (
                not inactive_models
                and len(self._model_states) > self.max_models_in_memory
            ):
                # 按使用频率排序，优先卸载使用最少的
                sorted_models = sorted(
                    self._model_states.items(), key=lambda x: x[1]["usage_count"]
                )
                for model_type, _ in sorted_models:
                    if self._model_states[model_type]["is_loaded"]:
                        inactive_models.append(model_type)
                        if (
                            len(inactive_models)
                            >= len(self._model_states) - self.max_models_in_memory
                        ):
                            break

            return inactive_models

    async def unload_model(self, model_type: str) -> bool:
        """
        卸载指定模型

        Args:
            model_type: 模型类型

        Returns:
            是否成功卸载
        """
        async with self._lock:
            if model_type in self._model_states:
                self._model_states[model_type]["is_loaded"] = False
                logger.info(f"模型已卸载: {model_type}")
                return True
            return False

    async def cleanup_inactive_models(self):
        """清理不活跃模型"""
        candidates = await self.get_unload_candidates()

        for model_type in candidates:
            await self.unload_model(model_type)

        if candidates:
            logger.info(f"已卸载 {len(candidates)} 个不活跃模型")

    async def start_cleanup_task(self):
        """启动定期清理任务"""
        if self._is_running:
            logger.warning("清理任务已在运行中")
            return

        self._is_running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("模型清理任务已启动")

    async def _cleanup_loop(self):
        """清理循环"""
        while self._is_running:
            try:
                await self.cleanup_inactive_models()
                await asyncio.sleep(60)  # 每分钟清理一次
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"清理循环错误: {e}")
                await asyncio.sleep(60)

    async def stop_cleanup_task(self):
        """停止清理任务"""
        self._is_running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        logger.info("模型清理任务已停止")

    def get_memory_stats(self) -> Dict[str, Any]:
        """获取内存使用统计"""
        total_size = 0
        loaded_count = 0

        for state in self._model_states.values():
            if state["is_loaded"]:
                total_size += state["size_gb"]
                loaded_count += 1

        return {
            "total_models": len(self._model_states),
            "loaded_models": loaded_count,
            "total_memory_gb": round(total_size, 2),
            "max_models": self.max_models_in_memory,
        }
