import psutil
import asyncio
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ResourceUsage:
    """资源使用情况"""
    cpu_percent: float  # CPU使用率（0-100）
    memory_percent: float  # 内存使用率（0-100）
    memory_used_gb: float  # 已用内存（GB）
    memory_total_gb: float  # 总内存（GB）
    gpu_percent: Optional[float] = None  # GPU使用率（0-100）
    gpu_memory_percent: Optional[float] = None  # GPU显存使用率（0-100）
    
    def is_over_threshold(self, cpu_threshold: float = 90, 
                        memory_threshold: float = 90) -> bool:
        """检查是否超过阈值"""
        return (self.cpu_percent > cpu_threshold or 
                self.memory_percent > memory_threshold)


class ResourceMonitor:
    """
    资源监控器
    
    负责实时监控系统资源使用情况，并触发相应的资源控制策略。
    """
    
    # 资源阈值配置
    CPU_WARNING_THRESHOLD = 80  # CPU警告阈值（%）
    CPU_PAUSE_THRESHOLD = 90  # CPU暂停阈值（%）
    
    MEMORY_WARNING_THRESHOLD = 80  # 内存警告阈值（%）
    MEMORY_PAUSE_THRESHOLD = 90  # 内存暂停阈值（%）
    
    GPU_WARNING_THRESHOLD = 80  # GPU警告阈值（%）
    GPU_PAUSE_THRESHOLD = 90  # GPU暂停阈值（%）
    
    def __init__(self, check_interval: float = 1.0):
        """
        初始化资源监控器
        
        Args:
            check_interval: 资源检查间隔（秒）
        """
        self.check_interval = check_interval
        self._is_running = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
        
        # 资源使用历史（用于趋势分析）
        self._history: list = []
        self._history_max_size = 60  # 保留60个历史记录（约1分钟）
        
        # 回调函数
        self._on_warning: Optional[callable] = None
        self._on_pause: Optional[callable] = None
        self._on_resume: Optional[callable] = None
        
        # 状态标志
        self._is_paused = False
        self._last_warning_time = 0
        
    def set_callbacks(self, on_warning: callable = None,
                     on_pause: callable = None,
                     on_resume: callable = None):
        """
        设置回调函数
        
        Args:
            on_warning: 警告回调（资源超过80%时调用）
            on_pause: 暂停回调（资源超过90%时调用）
            on_resume: 恢复回调（资源低于85%时调用）
        """
        self._on_warning = on_warning
        self._on_pause = on_pause
        self._on_resume = on_resume
    
    def get_resource_usage(self) -> ResourceUsage:
        """
        获取当前资源使用情况
        
        Returns:
            ResourceUsage对象
        """
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        # 内存使用情况
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used_gb = memory.used / (1024 ** 3)
        memory_total_gb = memory.total / (1024 ** 3)
        
        # GPU使用情况（可选）
        gpu_percent = None
        gpu_memory_percent = None
        
        try:
            import torch
            if torch.cuda.is_available():
                gpu_percent = torch.cuda.utilization()
                gpu_memory = torch.cuda.memory_allocated() / torch.cuda.max_memory_allocated()
                gpu_memory_percent = gpu_memory * 100
        except Exception as e:
            logger.debug(f"GPU监控不可用: {e}")
        
        return ResourceUsage(
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_used_gb=memory_used_gb,
            memory_total_gb=memory_total_gb,
            gpu_percent=gpu_percent,
            gpu_memory_percent=gpu_memory_percent
        )
    
    async def _monitor_loop(self):
        """资源监控循环"""
        while self._is_running:
            try:
                # 获取当前资源使用情况
                usage = self.get_resource_usage()
                
                # 记录历史
                self._history.append(usage)
                if len(self._history) > self._history_max_size:
                    self._history.pop(0)
                
                # 检查资源阈值
                await self._check_thresholds(usage)
                
                # 等待检查间隔
                await asyncio.sleep(self.check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"资源监控循环错误: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def _check_thresholds(self, usage: ResourceUsage):
        """
        检查资源阈值并触发相应动作
        
        Args:
            usage: 当前资源使用情况
        """
        current_time = asyncio.get_event_loop().time()
        
        # CPU检查
        if usage.cpu_percent > self.CPU_PAUSE_THRESHOLD:
            if not self._is_paused:
                logger.warning(
                    f"CPU使用率超限: {usage.cpu_percent:.1f}% > {self.CPU_PAUSE_THRESHOLD}%"
                )
                self._is_paused = True
                if self._on_pause:
                    await self._on_pause('cpu', usage.cpu_percent)
        
        # 内存检查
        if usage.memory_percent > self.MEMORY_PAUSE_THRESHOLD:
            if not self._is_paused:
                logger.warning(
                    f"内存使用率超限: {usage.memory_percent:.1f}% > {self.MEMORY_PAUSE_THRESHOLD}%"
                )
                self._is_paused = True
                if self._on_pause:
                    await self._on_pause('memory', usage.memory_percent)
        
        # 恢复条件
        if self._is_paused:
            if (usage.cpu_percent < self.CPU_WARNING_THRESHOLD - 5 and
                usage.memory_percent < self.MEMORY_WARNING_THRESHOLD - 5):
                logger.info(
                    f"资源已恢复: CPU={usage.cpu_percent:.1f}%, "
                    f"Memory={usage.memory_percent:.1f}%"
                )
                self._is_paused = False
                if self._on_resume:
                    await self._on_resume()
        
        # 警告（80%阈值）
        if (usage.cpu_percent > self.CPU_WARNING_THRESHOLD or
            usage.memory_percent > self.MEMORY_WARNING_THRESHOLD):
            if (current_time - self._last_warning_time) > 10:  # 每10秒只警告一次
                logger.warning(
                    f"资源使用率警告: CPU={usage.cpu_percent:.1f}%, "
                    f"Memory={usage.memory_percent:.1f}%"
                )
                self._last_warning_time = current_time
                if self._on_warning:
                    await self._on_warning(usage)
    
    def is_paused(self) -> bool:
        """
        检查是否因资源超限而暂停
        
        Returns:
            是否暂停
        """
        return self._is_paused
    
    def get_resource_trend(self) -> Dict[str, Any]:
        """
        获取资源使用趋势
        
        Returns:
            趋势数据字典
        """
        if len(self._history) < 2:
            return {'trend': 'stable', 'change_rate': 0}
        
        # 计算CPU趋势
        cpu_trend = (
            self._history[-1].cpu_percent - 
            self._history[0].cpu_percent
        ) / len(self._history)
        
        # 计算内存趋势
        memory_trend = (
            self._history[-1].memory_percent - 
            self._history[0].memory_percent
        ) / len(self._history)
        
        return {
            'cpu_trend': cpu_trend,
            'memory_trend': memory_trend,
            'trend': 'increasing' if cpu_trend > 0 or memory_trend > 0 else 'decreasing'
        }
    
    async def start(self):
        """启动资源监控"""
        if self._is_running:
            logger.warning("资源监控已在运行中")
            return
        
        self._is_running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("资源监控已启动")
    
    async def stop(self):
        """停止资源监控"""
        self._is_running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("资源监控已停止")
