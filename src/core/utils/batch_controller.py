import asyncio
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class BatchConfig:
    """批处理配置"""
    min_batch_size: int = 1
    max_batch_size: int = 32
    initial_batch_size: int = 16
    current_batch_size: int = 16
    
    # 调整参数
    increase_threshold: float = 0.7  # CPU < 70%时增加批处理大小
    decrease_threshold: float = 0.85  # CPU > 85%时降低批处理大小
    adjustment_step: int = 2  # 每次调整的步长
    adjustment_cooldown: float = 5.0  # 调整冷却时间（秒）


class BatchSizeController:
    """
    批处理大小控制器
    
    根据资源使用情况动态调整批处理大小，确保系统稳定性。
    """
    
    def __init__(self, config: Optional[BatchConfig] = None):
        """
        初始化批处理大小控制器
        
        Args:
            config: 批处理配置
        """
        self.config = config or BatchConfig()
        self._current_batch_size = self.config.initial_batch_size
        self._last_adjustment_time = 0
        self._adjustment_count = 0
        self._lock = asyncio.Lock()
    
    @property
    def current_batch_size(self) -> int:
        """获取当前批处理大小"""
        return self._current_batch_size
    
    async def adjust_batch_size(self, cpu_percent: float, memory_percent: float) -> int:
        """
        根据资源使用情况调整批处理大小
        
        Args:
            cpu_percent: 当前CPU使用率
            memory_percent: 当前内存使用率
            
        Returns:
            调整后的批处理大小
        """
        async with self._lock:
            current_time = asyncio.get_event_loop().time()
            
            # 检查冷却时间
            if (current_time - self._last_adjustment_time) < self.config.adjustment_cooldown:
                return self._current_batch_size
            
            # 增加批处理大小（资源充足）
            if (cpu_percent < self.config.increase_threshold * 100 and
                memory_percent < self.config.increase_threshold * 100 and
                self._current_batch_size < self.config.max_batch_size):
                new_batch_size = min(
                    self._current_batch_size + self.config.adjustment_step,
                    self.config.max_batch_size
                )
                if new_batch_size != self._current_batch_size:
                    logger.info(
                        f"增加批处理大小: {self._current_batch_size} -> {new_batch_size} "
                        f"(CPU={cpu_percent:.1f}%, Memory={memory_percent:.1f}%)"
                    )
                    self._current_batch_size = new_batch_size
                    self._last_adjustment_time = current_time
                    self._adjustment_count += 1
            
            # 降低批处理大小（资源紧张）
            elif (cpu_percent > self.config.decrease_threshold * 100 or
                  memory_percent > self.config.decrease_threshold * 100) and
                 self._current_batch_size > self.config.min_batch_size:
                new_batch_size = max(
                    self._current_batch_size - self.config.adjustment_step,
                    self.config.min_batch_size
                )
                if new_batch_size != self._current_batch_size:
                    logger.warning(
                        f"降低批处理大小: {self._current_batch_size} -> {new_batch_size} "
                        f"(CPU={cpu_percent:.1f}%, Memory={memory_percent:.1f}%)"
                    )
                    self._current_batch_size = new_batch_size
                    self._last_adjustment_time = current_time
                    self._adjustment_count += 1
            
            return self._current_batch_size
    
    def reset(self):
        """重置批处理大小为初始值"""
        self._current_batch_size = self.config.initial_batch_size
        self._last_adjustment_time = 0
        self._adjustment_count = 0
        logger.info(f"批处理大小已重置为: {self._current_batch_size}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取批处理调整统计信息"""
        return {
            'current_batch_size': self._current_batch_size,
            'adjustment_count': self._adjustment_count,
            'min_batch_size': self.config.min_batch_size,
            'max_batch_size': self.config.max_batch_size
        }
