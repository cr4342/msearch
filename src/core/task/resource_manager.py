"""
优化后的资源管理器
专门负责资源管理，简化OOM处理为两级
"""

import psutil
import threading
import time
from typing import Dict, Any, Optional
import logging


logger = logging.getLogger(__name__)


class OptimizedResourceManager:
    """优化后的资源管理器 - 简化OOM处理"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化资源管理器
        
        Args:
            config: 配置字典
        """
        # 简化的OOM阈值配置（两级）
        self.memory_warning_threshold = config.get('memory_warning_threshold', 80.0)  # 警告级
        self.memory_pause_threshold = config.get('memory_pause_threshold', 95.0)      # 暂停级
        
        # GPU内存阈值
        self.gpu_memory_warning_threshold = config.get('gpu_memory_warning_threshold', 80.0)
        self.gpu_memory_pause_threshold = config.get('gpu_memory_pause_threshold', 95.0)
        
        # 当前状态
        self.current_state = 'normal'  # normal, warning, pause
        self.last_state_change = time.time()
        
        # 资源历史
        self.resource_history = []
        self.max_history_size = 10
        
        # 线程控制
        self.is_monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()
        
        logger.info(f"资源管理器初始化完成: "
                   f"内存警告阈值={self.memory_warning_threshold}%, "
                   f"内存暂停阈值={self.memory_pause_threshold}%")
    
    def start_monitoring(self) -> None:
        """启动资源监控"""
        if not self.is_monitoring:
            self.is_monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            logger.info("资源监控已启动")
    
    def stop_monitoring(self) -> None:
        """停止资源监控"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
        logger.info("资源监控已停止")
    
    def check_resource_usage(self) -> str:
        """
        检查资源使用情况，返回当前状态
        
        Returns:
            当前资源状态 ('normal', 'warning', 'pause')
        """
        with self.lock:
            # 获取内存使用率
            memory_usage = psutil.virtual_memory().percent
            
            # 获取GPU内存使用率（如果可用）
            gpu_memory_usage = self._get_gpu_memory_usage()
            
            # 确定当前状态
            current_state = 'normal'
            
            # 检查内存使用
            if memory_usage >= self.memory_pause_threshold or \
               (gpu_memory_usage and gpu_memory_usage >= self.gpu_memory_pause_threshold):
                current_state = 'pause'
            elif memory_usage >= self.memory_warning_threshold or \
                 (gpu_memory_usage and gpu_memory_usage >= self.gpu_memory_warning_threshold):
                current_state = 'warning'
            
            # 记录资源历史
            self._record_resource_usage(memory_usage, gpu_memory_usage, current_state)
            
            # 如果状态发生变化，记录日志
            if current_state != self.current_state:
                self.current_state = current_state
                self.last_state_change = time.time()
                
                if current_state == 'warning':
                    logger.warning(f"资源警告: 内存使用率 {memory_usage:.1f}% "
                                 f"(阈值 {self.memory_warning_threshold}%)")
                elif current_state == 'pause':
                    logger.error(f"资源暂停: 内存使用率 {memory_usage:.1f}% "
                               f"(阈值 {self.memory_pause_threshold}%)")
                else:
                    logger.info(f"资源状态恢复正常: 内存使用率 {memory_usage:.1f}%")
            
            return self.current_state
    
    def _get_gpu_memory_usage(self) -> Optional[float]:
        """
        获取GPU内存使用率
        
        Returns:
            GPU内存使用率百分比或None（如果不可用）
        """
        try:
            import torch
            if torch.cuda.is_available():
                device = torch.cuda.current_device()
                total_memory = torch.cuda.get_device_properties(device).total_memory
                allocated_memory = torch.cuda.memory_allocated(device)
                
                if total_memory > 0:
                    return (allocated_memory / total_memory) * 100
        except ImportError:
            # 如果torch不可用，跳过GPU监控
            pass
        except Exception as e:
            logger.debug(f"获取GPU内存使用率失败: {e}")
        
        return None
    
    def _record_resource_usage(self, memory_usage: float, gpu_memory_usage: Optional[float], state: str) -> None:
        """记录资源使用情况到历史"""
        record = {
            'timestamp': time.time(),
            'memory_percent': memory_usage,
            'gpu_memory_percent': gpu_memory_usage,
            'state': state
        }
        
        self.resource_history.append(record)
        
        # 限制历史记录大小
        if len(self.resource_history) > self.max_history_size:
            self.resource_history.pop(0)
    
    def _monitor_loop(self) -> None:
        """监控循环"""
        logger.info("资源监控循环启动")
        
        while self.is_monitoring:
            try:
                # 检查资源使用
                self.check_resource_usage()
                
                # 每5秒检查一次
                time.sleep(5.0)
                
            except Exception as e:
                logger.error(f"资源监控循环错误: {e}")
                time.sleep(5.0)
    
    def get_current_state(self) -> str:
        """
        获取当前资源状态
        
        Returns:
            当前资源状态
        """
        with self.lock:
            return self.current_state
    
    def get_resource_usage(self) -> Dict[str, Any]:
        """
        获取当前资源使用情况
        
        Returns:
            资源使用情况字典
        """
        memory = psutil.virtual_memory()
        gpu_memory_usage = self._get_gpu_memory_usage()
        
        return {
            'memory_percent': memory.percent,
            'memory_available_gb': memory.available / (1024**3),
            'memory_total_gb': memory.total / (1024**3),
            'gpu_memory_percent': gpu_memory_usage,
            'current_state': self.current_state,
            'state_change_time': self.last_state_change
        }
    
    def get_resource_history(self) -> list:
        """
        获取资源使用历史
        
        Returns:
            资源使用历史列表
        """
        with self.lock:
            return self.resource_history.copy()
    
    def should_pause_tasks(self) -> bool:
        """
        是否应该暂停任务
        
        Returns:
            是否应该暂停任务
        """
        return self.check_resource_usage() == 'pause'
    
    def should_reduce_priority(self) -> bool:
        """
        是否应该降低非核心任务优先级
        
        Returns:
            是否应该降低优先级
        """
        return self.check_resource_usage() in ['warning', 'pause']
    
    def get_memory_pressure(self) -> float:
        """
        获取内存压力指数（0.0-1.0）
        
        Returns:
            内存压力指数
        """
        memory_usage = psutil.virtual_memory().percent
        gpu_memory_usage = self._get_gpu_memory_usage() or 0
        
        # 使用最大压力作为指标
        pressure = max(memory_usage, gpu_memory_usage) / 100.0
        return min(1.0, pressure)  # 限制在0-1范围内
    
    def get_recommendations(self) -> Dict[str, Any]:
        """
        获取资源优化建议
        
        Returns:
            优化建议字典
        """
        with self.lock:
            current_state = self.current_state
            recommendations = {
                'state': current_state,
                'actions': []
            }
            
            if current_state == 'pause':
                recommendations['actions'].append('暂停所有非关键任务')
                recommendations['actions'].append('释放缓存内存')
                recommendations['actions'].append('考虑增加物理内存')
            elif current_state == 'warning':
                recommendations['actions'].append('降低非核心任务优先级')
                recommendations['actions'].append('减少并发任务数')
                recommendations['actions'].append('监控内存使用趋势')
            else:
                recommendations['actions'].append('资源使用正常')
                recommendations['actions'].append('可按正常优先级执行任务')
            
            return recommendations
    
    def cleanup(self) -> None:
        """清理资源"""
        self.stop_monitoring()
        logger.info("资源管理器清理完成")