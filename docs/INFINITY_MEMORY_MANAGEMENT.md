# Infinity 内存管理与资源控制设计文档

## 1. 资源控制目标

为避免系统因CPU和内存占满而卡死，Infinity模型管理框架必须实现严格的资源控制策略：

- **CPU使用率上限**：90%
- **内存使用率上限**：90%
- **GPU显存使用率上限**：90%
- **系统预留资源**：10% CPU + 10% 内存（用于系统稳定性）

## 2. 资源监控架构

### 2.1 资源监控模块设计

```
┌─────────────────────────────────────────────────────────────────┐
│                    ResourceMonitor                              │
│                   （资源监控器）                                │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │  CPU Monitor    │  │  Memory Monitor │  │  GPU Monitor    │  │
│  │  （CPU监控）    │  │  （内存监控）   │  │  （GPU监控）    │  │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘  │
│           │                     │                    │           │
│           └─────────────────────┴────────────────────┘           │
│                              │                                  │
│                              ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │      Resource Threshold Manager                          │   │
│  │      （资源阈值管理器）                                   │   │
│  │  - CPU: 90% max                                         │   │
│  │  - Memory: 90% max                                     │   │
│  │  - GPU: 90% max                                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │      Resource Action Handler                            │   │
│  │      （资源动作处理器）                                  │   │
│  │  - 80%: 警告日志                                        │   │
│  │  - 85%: 降低批处理大小                                  │   │
│  │  - 90%: 暂停推理任务                                    │   │
│  │  - 95%: 卸载不活跃模型                                  │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ModelManager                                 │
│                   （模型管理器）                                │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 资源监控实现

```python
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
```

## 3. 批处理大小动态调整

### 3.1 批处理大小自适应算法

```python
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
```

## 4. 模型内存管理

### 4.1 模型卸载与缓存策略

```python
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
    
    def __init__(self, max_models_in_memory: int = 3,
                 inactive_timeout: int = 300):  # 5分钟不活跃超时
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
                'size_gb': model_size_gb,
                'last_used': datetime.now(),
                'usage_count': 0,
                'is_loaded': True
            }
        
        logger.info(f"模型已跟踪: {model_type} ({model_size_gb:.2f}GB)")
    
    async def mark_model_used(self, model_type: str):
        """
        标记模型已使用
        
        Args:
            model_type: 模型类型
        """
        if model_type in self._model_states:
            self._model_states[model_type]['last_used'] = datetime.now()
            self._model_states[model_type]['usage_count'] += 1
    
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
                if state['is_loaded']:
                    inactive_time = (now - state['last_used']).total_seconds()
                    if inactive_time > self.inactive_timeout:
                        inactive_models.append(model_type)
            
            # 2. 如果没有不活跃模型，按使用频率排序
            if not inactive_models and len(self._model_states) > self.max_models_in_memory:
                # 按使用频率排序，优先卸载使用最少的
                sorted_models = sorted(
                    self._model_states.items(),
                    key=lambda x: x[1]['usage_count']
                )
                for model_type, _ in sorted_models:
                    if self._model_states[model_type]['is_loaded']:
                        inactive_models.append(model_type)
                        if len(inactive_models) >= len(self._model_states) - self.max_models_in_memory:
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
                self._model_states[model_type]['is_loaded'] = False
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
            if state['is_loaded']:
                total_size += state['size_gb']
                loaded_count += 1
        
        return {
            'total_models': len(self._model_states),
            'loaded_models': loaded_count,
            'total_memory_gb': round(total_size, 2),
            'max_models': self.max_models_in_memory
        }
```

## 5. 资源控制集成

### 5.1 ModelManager集成资源控制

```python
import asyncio
import logging
from typing import List, Optional
from .resource_monitor import ResourceMonitor
from .batch_controller import BatchSizeController
from .model_memory_manager import ModelMemoryManager

logger = logging.getLogger(__name__)


class ResourceControlledModelManager:
    """
    带资源控制的模型管理器
    
    集成资源监控、批处理控制和模型内存管理，确保系统稳定运行。
    """
    
    def __init__(self):
        """初始化资源控制模型管理器"""
        self.resource_monitor = ResourceMonitor()
        self.batch_controller = BatchSizeController()
        self.model_memory_manager = ModelMemoryManager()
        
        # 初始化回调
        self.resource_monitor.set_callbacks(
            on_warning=self._on_resource_warning,
            on_pause=self._on_resource_pause,
            on_resume=self._on_resource_resume
        )
        
        self._is_initialized = False
    
    async def initialize(self):
        """初始化资源控制"""
        if self._is_initialized:
            return
        
        await self.resource_monitor.start()
        await self.model_memory_manager.start_cleanup_task()
        self._is_initialized = True
        logger.info("资源控制模型管理器已初始化")
    
    async def shutdown(self):
        """关闭资源控制"""
        await self.resource_monitor.stop()
        await self.model_memory_manager.stop_cleanup_task()
        self._is_initialized = False
        logger.info("资源控制模型管理器已关闭")
    
    async def _on_resource_warning(self, usage):
        """资源警告回调"""
        # 降低批处理大小
        await self.batch_controller.adjust_batch_size(
            usage.cpu_percent, usage.memory_percent
        )
    
    async def _on_resource_pause(self, resource_type, value):
        """资源暂停回调"""
        logger.warning(f"资源暂停: {resource_type} = {value:.1f}%")
    
    async def _on_resource_resume(self):
        """资源恢复回调"""
        logger.info("资源已恢复，继续处理")
    
    async def _wait_for_resource_available(self):
        """等待资源可用"""
        while self.resource_monitor.is_paused():
            await asyncio.sleep(0.5)
    
    async def embed_with_resource_control(self, model_type: str,
                                        inputs: List[str],
                                        input_type: str = "text") -> List[List[float]]:
        """
        在资源控制下执行向量化
        
        Args:
            model_type: 模型类型
            inputs: 输入数据
            input_type: 输入类型
            
        Returns:
            向量化结果
        """
        # 检查资源状态
        if self.resource_monitor.is_paused():
            # 等待资源恢复
            await self._wait_for_resource_available()
        
        # 获取当前批处理大小
        batch_size = self.batch_controller.current_batch_size
        
        # 动态调整批处理大小
        usage = self.resource_monitor.get_resource_usage()
        await self.batch_controller.adjust_batch_size(
            usage.cpu_percent, usage.memory_percent
        )
        
        # 标记模型使用
        await self.model_memory_manager.mark_model_used(model_type)
        
        # 分批处理
        results = []
        for i in range(0, len(inputs), batch_size):
            batch = inputs[i:i+batch_size]
            
            # 再次检查资源
            if self.resource_monitor.is_paused():
                await self._wait_for_resource_available()
            
            # 执行向量化
            batch_results = await self._embed_batch(model_type, batch, input_type)
            results.extend(batch_results)
        
        return results
    
    async def _embed_batch(self, model_type: str, batch: List[str],
                          input_type: str) -> List[List[float]]:
        """
        执行批量向量化
        
        Args:
            model_type: 模型类型
            batch: 批处理数据
            input_type: 输入类型
            
        Returns:
            向量化结果
        """
        # 实际向量化逻辑（由子类实现）
        raise NotImplementedError("_embed_batch must be implemented by subclass")
    
    def get_resource_stats(self) -> dict:
        """
        获取资源统计信息
        
        Returns:
            资源统计字典
        """
        return {
            'resource_usage': self.resource_monitor.get_resource_usage(),
            'batch_stats': self.batch_controller.get_stats(),
            'memory_stats': self.model_memory_manager.get_memory_stats(),
            'resource_trend': self.resource_monitor.get_resource_trend()
        }
```

## 6. 使用示例

### 6.1 基本使用

```python
import asyncio
from resource_controlled_model_manager import ResourceControlledModelManager


class MyModelManager(ResourceControlledModelManager):
    """自定义模型管理器"""
    
    async def _embed_batch(self, model_type: str, batch: List[str],
                          input_type: str) -> List[List[float]]:
        """实现批量向量化"""
        # 这里替换为实际的向量化逻辑
        # 例如调用Infinity的embedding服务
        results = []
        for text in batch:
            # 实际向量化操作
            vector = [0.1] * 512  # 示例向量
            results.append(vector)
        return results


async def main():
    # 创建模型管理器
    manager = MyModelManager()
    await manager.initialize()
    
    try:
        # 处理数据
        inputs = ["这是一个测试文本"] * 100
        embeddings = await manager.embed_with_resource_control(
            'chinese_clip_base', inputs, 'text'
        )
        
        print(f"生成了 {len(embeddings)} 个向量")
        
        # 获取资源统计
        stats = manager.get_resource_stats()
        print("资源统计:", stats)
        
    finally:
        await manager.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
```

## 7. 配置建议

### 7.1 资源阈值配置

根据服务器配置调整阈值：

```yaml
# 资源监控配置
resource_monitor:
  check_interval: 1.0  # 检查间隔（秒）
  cpu_warning_threshold: 80  # CPU警告阈值（%）
  cpu_pause_threshold: 90  # CPU暂停阈值（%）
  memory_warning_threshold: 80  # 内存警告阈值（%）
  memory_pause_threshold: 90  # 内存暂停阈值（%）

# 批处理配置
batch_controller:
  min_batch_size: 1
  max_batch_size: 32
  initial_batch_size: 16
  increase_threshold: 0.7  # 资源充足阈值
  decrease_threshold: 0.85  # 资源紧张阈值
  adjustment_step: 2
  adjustment_cooldown: 5.0

# 模型内存配置
model_memory_manager:
  max_models_in_memory: 3
  inactive_timeout: 300  # 5分钟
```

### 7.2 不同服务器配置建议

| 服务器配置 | CPU阈值 | 内存阈值 | 最大批处理 | 最大模型数 |
|-----------|--------|--------|----------|----------|
| 低配（2核4GB） | 85% | 85% | 8 | 1 |
| 中配（4核8GB） | 90% | 90% | 16 | 2 |
| 高配（8核16GB+） | 90% | 90% | 32 | 3 |
| GPU服务器 | 90% | 90% | 64 | 4 |

## 8. 监控与调优

### 8.1 监控指标

建议监控以下指标：

- CPU使用率（目标：<90%）
- 内存使用率（目标：<90%）
- 批处理大小变化
- 模型加载/卸载频率
- 向量化延迟

### 8.2 调优策略

1. **如果CPU经常超限**：
   - 降低初始批处理大小
   - 增加检查间隔
   - 调整降低阈值到80%

2. **如果内存经常超限**：
   - 减少最大模型数
   - 降低不活跃超时时间
   - 优先卸载大模型

3. **如果系统频繁暂停**：
   - 增加恢复阈值的缓冲（如从85%降到80%）
   - 优化模型加载策略
   - 考虑增加硬件资源

## 9. 故障排查

### 9.1 常见问题

**Q: 系统经常因CPU占满而卡死**

A: 检查以下几点：
1. 确认资源监控器已启动
2. 检查批处理大小是否过大
3. 确认回调函数已正确注册
4. 查看日志中的资源警告信息

**Q: 模型被频繁卸载**

A: 可能原因：
1. 不活跃超时时间设置过短
2. 内存阈值设置过低
3. 最大模型数设置过小

**Q: 资源恢复后处理不继续**

A: 检查恢复条件是否正确：
1. 确保恢复阈值低于警告阈值
2. 确认回调函数已实现
3. 检查是否有死锁或阻塞

## 10. 总结

通过实现资源监控器、批处理大小控制器和模型内存管理器，可以有效防止系统因CPU和内存占满而卡死。核心策略包括：

1. **实时监控**：每秒检查资源使用情况
2. **分级处理**：80%警告、85%降批处理、90%暂停、95%卸载模型
3. **动态调整**：根据资源情况自动调整批处理大小
4. **智能卸载**：优先卸载不活跃和使用频率低的模型
5. **自动恢复**：资源充足时自动恢复处理

这些机制确保了系统在高负载情况下的稳定性，同时最大化资源利用率。
