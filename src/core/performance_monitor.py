"""
性能监控器
实时监控系统性能指标和组件健康状态
"""

import asyncio
import logging
import psutil
import time
from collections import defaultdict, deque
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

from src.core.config_manager import get_config_manager


@dataclass
class PerformanceMetrics:
    """性能指标数据类"""
    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_total_mb: float
    disk_usage_percent: float
    disk_free_gb: float
    gpu_memory_used_mb: Optional[float] = None
    gpu_memory_total_mb: Optional[float] = None
    gpu_utilization_percent: Optional[float] = None


@dataclass
class ComponentMetrics:
    """组件指标数据类"""
    name: str
    execution_count: int
    total_time: float
    average_time: float
    min_time: float
    max_time: float
    error_count: int
    success_rate: float
    last_execution: Optional[float] = None


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, config_manager=None):
        self.config_manager = config_manager or get_config_manager()
        self.logger = logging.getLogger(__name__)
        
        # 配置参数
        self.monitoring_interval = self.config_manager.get(
            "performance.monitoring_interval", 5
        )
        self.max_history_size = self.config_manager.get(
            "performance.max_history_size", 1000
        )
        
        # 性能数据存储
        self.system_metrics_history: deque = deque(maxlen=self.max_history_size)
        self.component_metrics: Dict[str, ComponentMetrics] = {}
        self.component_performance_history: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=100)
        )
        
        # 运行状态
        self.is_monitoring = False
        self.monitoring_task: Optional[asyncio.Task] = None
        
        # 告警阈值
        self.cpu_threshold = self.config_manager.get(
            "performance.alerts.cpu_threshold", 80.0
        )
        self.memory_threshold = self.config_manager.get(
            "performance.alerts.memory_threshold", 85.0
        )
        self.disk_threshold = self.config_manager.get(
            "performance.alerts.disk_threshold", 90.0
        )
        
        # 告警状态
        self.active_alerts: Dict[str, bool] = {}
        
        self.logger.info("性能监控器初始化完成")
    
    async def start(self):
        """启动性能监控"""
        self.logger.info("启动性能监控器")
        self.is_monitoring = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
    
    async def stop(self):
        """停止性能监控"""
        self.logger.info("停止性能监控器")
        self.is_monitoring = False
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
    
    async def _monitoring_loop(self):
        """监控循环"""
        while self.is_monitoring:
            try:
                # 收集系统指标
                metrics = await self._collect_system_metrics()
                self.system_metrics_history.append(metrics)
                
                # 检查告警
                self._check_alerts(metrics)
                
                # 等待下次监控
                await asyncio.sleep(self.monitoring_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"性能监控异常: {e}")
                await asyncio.sleep(self.monitoring_interval)
    
    async def _collect_system_metrics(self) -> PerformanceMetrics:
        """收集系统性能指标"""
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # 内存使用情况
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used_mb = memory.used / (1024 * 1024)
        memory_total_mb = memory.total / (1024 * 1024)
        
        # 磁盘使用情况
        disk = psutil.disk_usage('/')
        disk_usage_percent = disk.percent
        disk_free_gb = disk.free / (1024 * 1024 * 1024)
        
        # GPU指标（如果可用）
        gpu_metrics = await self._collect_gpu_metrics()
        
        return PerformanceMetrics(
            timestamp=time.time(),
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_used_mb=memory_used_mb,
            memory_total_mb=memory_total_mb,
            disk_usage_percent=disk_usage_percent,
            disk_free_gb=disk_free_gb,
            **gpu_metrics
        )
    
    async def _collect_gpu_metrics(self) -> Dict[str, float]:
        """收集GPU指标"""
        try:
            import GPUtil
            
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]  # 使用第一个GPU
                return {
                    'gpu_memory_used_mb': gpu.memoryUsed,
                    'gpu_memory_total_mb': gpu.memoryTotal,
                    'gpu_utilization_percent': gpu.load * 100
                }
            else:
                return {
                    'gpu_memory_used_mb': None,
                    'gpu_memory_total_mb': None,
                    'gpu_utilization_percent': None
                }
        except ImportError:
            # GPUtil未安装
            return {
                'gpu_memory_used_mb': None,
                'gpu_memory_total_mb': None,
                'gpu_utilization_percent': None
            }
        except Exception as e:
            self.logger.warning(f"GPU指标收集失败: {e}")
            return {
                'gpu_memory_used_mb': None,
                'gpu_memory_total_mb': None,
                'gpu_utilization_percent': None
            }
    
    def _check_alerts(self, metrics: PerformanceMetrics):
        """检查告警条件"""
        current_time = time.time()
        
        # CPU告警
        if metrics.cpu_percent > self.cpu_threshold:
            self._trigger_alert('high_cpu', f"CPU使用率过高: {metrics.cpu_percent:.1f}%")
        else:
            self._clear_alert('high_cpu')
        
        # 内存告警
        if metrics.memory_percent > self.memory_threshold:
            self._trigger_alert('high_memory', f"内存使用率过高: {metrics.memory_percent:.1f}%")
        else:
            self._clear_alert('high_memory')
        
        # 磁盘告警
        if metrics.disk_usage_percent > self.disk_threshold:
            self._trigger_alert('high_disk', f"磁盘使用率过高: {metrics.disk_usage_percent:.1f}%")
        else:
            self._clear_alert('high_disk')
    
    def _trigger_alert(self, alert_type: str, message: str):
        """触发告警"""
        if not self.active_alerts.get(alert_type, False):
            self.active_alerts[alert_type] = True
            self.logger.warning(f"性能告警 [{alert_type}]: {message}")
    
    def _clear_alert(self, alert_type: str):
        """清除告警"""
        if self.active_alerts.get(alert_type, False):
            self.active_alerts[alert_type] = False
            self.logger.info(f"性能告警清除 [{alert_type}]: 指标恢复正常")
    
    def record_component_performance(self, component_name: str, execution_time: float, success: bool = True, error: Optional[str] = None):
        """记录组件性能指标"""
        current_time = time.time()
        
        if component_name not in self.component_metrics:
            self.component_metrics[component_name] = ComponentMetrics(
                name=component_name,
                execution_count=0,
                total_time=0.0,
                average_time=0.0,
                min_time=float('inf'),
                max_time=0.0,
                error_count=0,
                success_rate=1.0,
                last_execution=None
            )
        
        metrics = self.component_metrics[component_name]
        
        # 更新统计信息
        metrics.execution_count += 1
        metrics.total_time += execution_time
        metrics.average_time = metrics.total_time / metrics.execution_count
        metrics.min_time = min(metrics.min_time, execution_time)
        metrics.max_time = max(metrics.max_time, execution_time)
        metrics.last_execution = current_time
        
        if not success:
            metrics.error_count += 1
        
        # 计算成功率
        metrics.success_rate = (metrics.execution_count - metrics.error_count) / metrics.execution_count
        
        # 记录到历史数据
        self.component_performance_history[component_name].append({
            'timestamp': current_time,
            'execution_time': execution_time,
            'success': success,
            'error': error
        })
        
        # 记录性能日志
        if not success:
            self.logger.warning(f"组件执行失败 [{component_name}]: {error} (耗时: {execution_time:.3f}s)")
        else:
            self.logger.debug(f"组件执行成功 [{component_name}]: 耗时 {execution_time:.3f}s")
    
    def get_current_metrics(self) -> Optional[PerformanceMetrics]:
        """获取当前性能指标"""
        if self.system_metrics_history:
            return self.system_metrics_history[-1]
        return None
    
    def get_component_metrics(self, component_name: Optional[str] = None) -> Dict[str, Any]:
        """获取组件性能指标"""
        if component_name:
            if component_name in self.component_metrics:
                return asdict(self.component_metrics[component_name])
            return {}
        else:
            return {name: asdict(metrics) for name, metrics in self.component_metrics.items()}
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        current_metrics = self.get_current_metrics()
        
        if not current_metrics:
            return {
                'status': 'no_data',
                'message': '暂无性能数据'
            }
        
        # 计算平均值（最近10次记录）
        recent_metrics = list(self.system_metrics_history)[-10:]
        if recent_metrics:
            avg_cpu = sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics)
            avg_memory = sum(m.memory_percent for m in recent_metrics) / len(recent_metrics)
            avg_disk = sum(m.disk_usage_percent for m in recent_metrics) / len(recent_metrics)
        else:
            avg_cpu = avg_memory = avg_disk = 0
        
        # 活跃告警
        active_alerts = [alert_type for alert_type, active in self.active_alerts.items() if active]
        
        return {
            'timestamp': current_metrics.timestamp,
            'system': {
                'cpu_percent': current_metrics.cpu_percent,
                'memory_percent': current_metrics.memory_percent,
                'disk_usage_percent': current_metrics.disk_usage_percent,
                'gpu_utilization': current_metrics.gpu_utilization_percent,
            },
            'averages': {
                'cpu_percent': avg_cpu,
                'memory_percent': avg_memory,
                'disk_usage_percent': avg_disk,
            },
            'components': self.get_component_metrics(),
            'active_alerts': active_alerts,
            'monitoring_duration': time.time() - (self.system_metrics_history[0].timestamp if self.system_metrics_history else time.time())
        }
    
    def get_performance_report(self) -> Dict[str, Any]:
        """生成性能报告"""
        summary = self.get_performance_summary()
        
        # 添加详细统计信息
        report = {
            'summary': summary,
            'component_details': {},
            'recommendations': []
        }
        
        # 组件详细信息
        for component_name, metrics in self.component_metrics.items():
            history = list(self.component_performance_history[component_name])
            
            if history:
                execution_times = [h['execution_time'] for h in history]
                error_rate = sum(1 for h in history if not h['success']) / len(history)
                
                report['component_details'][component_name] = {
                    'total_executions': metrics.execution_count,
                    'success_rate': metrics.success_rate,
                    'error_rate': error_rate,
                    'average_execution_time': metrics.average_time,
                    'min_execution_time': metrics.min_time,
                    'max_execution_time': metrics.max_time,
                    'last_execution': metrics.last_execution
                }
        
        # 生成优化建议
        report['recommendations'] = self._generate_recommendations(summary)
        
        return report
    
    def _generate_recommendations(self, summary: Dict[str, Any]) -> List[str]:
        """生成性能优化建议"""
        recommendations = []
        
        system = summary.get('system', {})
        components = summary.get('components', {})
        
        # 系统资源建议
        if system.get('cpu_percent', 0) > 70:
            recommendations.append("CPU使用率较高，建议检查高CPU消耗的组件")
        
        if system.get('memory_percent', 0) > 80:
            recommendations.append("内存使用率较高，建议增加批处理大小或优化内存使用")
        
        if system.get('disk_usage_percent', 0) > 85:
            recommendations.append("磁盘使用率较高，建议清理临时文件或扩展存储空间")
        
        # 组件性能建议
        for component_name, metrics in components.items():
            if metrics.get('success_rate', 1.0) < 0.95:
                recommendations.append(f"组件 {component_name} 成功率较低 ({metrics['success_rate']:.1%})，需要检查错误原因")
            
            if metrics.get('average_execution_time', 0) > 5.0:
                recommendations.append(f"组件 {component_name} 平均执行时间较长 ({metrics['average_execution_time']:.1f}s)，建议进行性能优化")
        
        if not recommendations:
            recommendations.append("系统性能良好，暂无优化建议")
        
        return recommendations


class PerformanceMonitorDecorator:
    """性能监控装饰器"""
    
    def __init__(self, monitor: PerformanceMonitor):
        self.monitor = monitor
    
    def __call__(self, component_name: str = None):
        """装饰器"""
        def decorator(func):
            component = component_name or func.__name__
            
            if asyncio.iscoroutinefunction(func):
                @wraps(func)
                async def async_wrapper(*args, **kwargs):
                    start_time = time.time()
                    try:
                        result = await func(*args, **kwargs)
                        execution_time = time.time() - start_time
                        self.monitor.record_component_performance(component, execution_time, True)
                        return result
                    except Exception as e:
                        execution_time = time.time() - start_time
                        self.monitor.record_component_performance(component, execution_time, False, str(e))
                        raise
                return async_wrapper
            else:
                @wraps(func)
                def sync_wrapper(*args, **kwargs):
                    start_time = time.time()
                    try:
                        result = func(*args, **kwargs)
                        execution_time = time.time() - start_time
                        self.monitor.record_component_performance(component, execution_time, True)
                        return result
                    except Exception as e:
                        execution_time = time.time() - start_time
                        self.monitor.record_component_performance(component, execution_time, False, str(e))
                        raise
                return sync_wrapper
        return decorator