"""
任务管理器（重构版）
负责任务生命周期管理、任务调度、任务状态跟踪
使用新的组件实现职责分离
"""

import uuid
import threading
from typing import Any, Dict, List, Optional, Callable
from pathlib import Path
import logging
from datetime import datetime

from .task import Task
from .task_queue import TaskQueue
from .task_executor import OptimizedTaskExecutor
from .priority_calculator import PriorityCalculator
from .task_group_manager import TaskGroupManager
from .resource_manager import OptimizedResourceManager
from .task_monitor import OptimizedTaskMonitor
from .concurrency_manager import OptimizedConcurrencyManager, ConcurrencyConfig

logger = logging.getLogger(__name__)


class TaskManager:
    """任务管理器（重构版）：负责任务生命周期管理、任务调度、任务状态跟踪"""
    
    def __init__(self, config: Dict[str, Any], device: str = 'cpu'):
        """
        初始化任务管理器
        
        Args:
            config: 配置字典
            device: 设备类型（cuda/cpu），从配置文件读取
        """
        self.config = config
        self.device = device
        
        # 任务配置
        self.task_config = config.get('task_manager', {})
        
        # 创建组件
        self.task_queue = TaskQueue()
        self.task_executor = OptimizedTaskExecutor()
        # 使用简化的2级OOM处理的资源管理器
        self.resource_manager = OptimizedResourceManager({
            'memory_warning_threshold': 85.0,
            'memory_pause_threshold': 95.0,
            'gpu_memory_warning_threshold': 85.0,
            'gpu_memory_pause_threshold': 95.0
        })
        self.task_monitor = OptimizedTaskMonitor()
        self.group_manager = TaskGroupManager(self.task_config)
        self.priority_calculator = PriorityCalculator()
        
        # 并发管理器
        concurrency_config = ConcurrencyConfig(
            concurrency_mode=self.task_config.get('concurrency_mode', 'dynamic'),
            min_concurrent=self.task_config.get('min_concurrent_tasks', 1),
            max_concurrent=self.task_config.get('max_concurrent_tasks', 8),
            base_concurrent_tasks=self.task_config.get('base_concurrent_tasks', 4),
            target_cpu_percent=self.task_config.get('dynamic_concurrency_target_cpu', 70.0),
            target_memory_percent=self.task_config.get('dynamic_concurrency_target_memory', 70.0),
            target_gpu_memory_percent=self.task_config.get('dynamic_concurrency_target_gpu', 80.0),
            adjustment_interval=self.task_config.get('dynamic_concurrency_interval', 5.0),
            adjustment_step=self.task_config.get('dynamic_concurrency_step', 1)
        )
        self.concurrency_manager = OptimizedConcurrencyManager(concurrency_config, device)
        
        # 任务处理器
        self.task_handlers: Dict[str, Callable] = {}
        
        # 线程控制
        self.is_running = False
        self.worker_thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()
        
        logger.info("任务管理器（重构版）初始化完成")
    
    def initialize(self) -> bool:
        """
        初始化任务管理器
        
        Returns:
            是否成功
        """
        try:
            # 初始化并发管理器
            if not self.concurrency_manager.initialize():
                logger.warning("并发管理器启动失败")
                return False
            
            # 启动资源管理器监控
            self.resource_manager.start_monitoring()
            
            # 启动工作线程
            self.is_running = True
            self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
            self.worker_thread.start()
            
            logger.info("任务管理器启动成功")
            return True
        except Exception as e:
            logger.error(f"任务管理器初始化失败: {e}")
            return False
    
    def shutdown(self) -> None:
        """关闭任务管理器"""
        logger.info("正在关闭任务管理器...")
        
        self.is_running = False
        
        # 等待工作线程结束
        if self.worker_thread:
            self.worker_thread.join(timeout=5.0)
        
        # 关闭资源管理器
        self.resource_manager.stop_monitoring()
        self.resource_manager.cleanup()
        
        # 关闭并发管理器
        self.concurrency_manager.shutdown()
        
        logger.info("任务管理器已关闭")
    
    def create_task(
        self,
        task_type: str,
        task_data: Dict[str, Any],
        priority: int = 5,
        file_id: Optional[str] = None,
        depends_on: Optional[List[str]] = None
    ) -> str:
        """
        创建任务
        
        Args:
            task_type: 任务类型
            task_data: 任务数据
            priority: 优先级
            file_id: 文件ID
            depends_on: 依赖的任务ID列表
        
        Returns:
            任务ID
        """
        with self.lock:
            # 创建任务
            task = Task(
                task_type=task_type,
                task_data=task_data,
                priority=priority,
                file_id=file_id,
                depends_on=depends_on
            )
            
            # 计算最终优先级（包含等待时间补偿和流水线连续性奖励）
            final_priority = self.priority_calculator.calculate_priority(
                task, 
                file_info={'file_id': file_id} if file_id else None,
                file_priority=priority
            )
            
            # 添加到队列
            self.task_queue.add_task(task)
            
            # 添加到监控器
            self.task_monitor.add_task(task)
            
            logger.info(f"任务创建成功: {task.id}, 类型: {task_type}, 优先级: {final_priority}")
            return task.id
    
    def register_handler(self, task_type: str, handler: Callable) -> None:
        """
        注册任务处理器
        
        Args:
            task_type: 任务类型
            handler: 处理函数
        """
        self.task_handlers[task_type] = handler
        self.task_executor.register_handler(task_type, handler)
        logger.info(f"任务处理器注册成功: {task_type}")
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
        
        Returns:
            任务状态字典
        """
        return self.task_monitor.get_task(task_id)
    
    def get_task_progress(self, task_id: str) -> Optional[float]:
        """
        获取任务进度
        
        Args:
            task_id: 任务ID
        
        Returns:
            任务进度（0.0-1.0）
        """
        task = self.task_monitor.get_task(task_id)
        if task:
            return getattr(task, 'progress', 0.0)
        return None

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务信息

        Args:
            task_id: 任务ID

        Returns:
            任务信息字典，不存在则返回None
        """
        return self.task_monitor.get_task(task_id)

    def update_task_status(self, task_id: str, status: str, **kwargs) -> bool:
        """
        更新任务状态

        Args:
            task_id: 任务ID
            status: 新状态
            kwargs: 其他更新参数（如progress、result等）

        Returns:
            是否成功
        """
        task = self.task_monitor.get_task(task_id)
        if task:
            task.status = status
            for key, value in kwargs.items():
                setattr(task, key, value)
            self.task_monitor.update_task(task)
            return True
        return False

    def update_task_priority(self, task_id: str, priority: int) -> bool:
        """
        更新任务优先级

        Args:
            task_id: 任务ID
            priority: 新优先级

        Returns:
            是否成功
        """
        task = self.task_monitor.get_task(task_id)
        if task:
            task.priority = priority
            # 重新计算调度优先级
            new_priority = self.priority_calculator.calculate_priority(task)
            self.task_queue.update_task_priority(task_id, new_priority)
            logger.info(f"任务 {task_id} 优先级已更新为 {priority}")
            return True
        return False

    def check_dependencies(self, task_id: str) -> bool:
        """
        检查任务依赖是否满足

        Args:
            task_id: 任务ID

        Returns:
            依赖是否满足
        """
        task = self.task_monitor.get_task(task_id)
        if not task:
            return False

        for dep_id in task.depends_on:
            dep_task = self.task_monitor.get_task(dep_id)
            if not dep_task or dep_task.status != 'completed':
                return False
        return True

    def get_dependent_tasks(self, task_id: str) -> List[str]:
        """
        获取依赖指定任务的任务列表

        Args:
            task_id: 任务ID

        Returns:
            依赖该任务的任务ID列表
        """
        dependents = []
        for task in self.task_monitor.get_all_tasks().values():
            if task_id in task.depends_on:
                dependents.append(task.id)
        return dependents

    def get_task_stats(self) -> Dict[str, Any]:
        """
        获取任务统计信息

        Returns:
            统计信息字典
        """
        return self.task_monitor.get_statistics()
    
    def cancel_task(self, task_id: str) -> bool:
        """
        取消任务
        
        Args:
            task_id: 任务ID
        
        Returns:
            是否成功
        """
        with self.lock:
            # 从队列中移除
            success = self.task_queue.remove_task(task_id)
            
            if success:
                # 更新监控器
                task = self.task_monitor.get_task(task_id)
                if task:
                    task.status = 'cancelled'
                    self.task_monitor.update_task(task)
                logger.info(f"任务取消成功: {task_id}")
            else:
                logger.warning(f"任务取消失败: {task_id}")
            
            return success
    
    def cancel_all_tasks(self, cancel_running: bool = False) -> Dict[str, Any]:
        """
        取消所有任务
        
        Args:
            cancel_running: 是否取消正在运行的任务
        
        Returns:
            取消结果统计
        """
        with self.lock:
            cancelled_count = 0
            failed_count = 0
            
            # 获取所有待处理的任务
            all_tasks = self.task_monitor.get_all_tasks()
            
            for task in all_tasks.values():
                # 如果任务不是运行中，或者允许取消运行中的任务
                if task.status != 'running' or cancel_running:
                    success = self.task_queue.remove_task(task.id)
                    if success:
                        task.status = 'cancelled'
                        self.task_monitor.update_task(task)
                        cancelled_count += 1
                    else:
                        failed_count += 1
            
            logger.info(f"批量取消任务完成: 成功{cancelled_count}个, 失败{failed_count}个")
            
            return {
                'cancelled': cancelled_count,
                'failed': failed_count,
                'total': cancelled_count + failed_count
            }
    
    def cancel_tasks_by_type(self, task_type: str, cancel_running: bool = False) -> Dict[str, Any]:
        """
        按类型取消任务
        
        Args:
            task_type: 任务类型
            cancel_running: 是否取消正在运行的任务
        
        Returns:
            取消结果统计
        """
        with self.lock:
            cancelled_count = 0
            failed_count = 0
            
            # 获取指定类型的全部任务
            all_tasks = self.task_monitor.get_all_tasks()
            
            for task in all_tasks.values():
                if task.task_type == task_type:
                    # 如果任务不是运行中，或者允许取消运行中的任务
                    if task.status != 'running' or cancel_running:
                        success = self.task_queue.remove_task(task.id)
                        if success:
                            task.status = 'cancelled'
                            self.task_monitor.update_task(task)
                            cancelled_count += 1
                        else:
                            failed_count += 1
            
            logger.info(f"批量取消{task_type}任务完成: 成功{cancelled_count}个, 失败{failed_count}个")
            
            return {
                'cancelled': cancelled_count,
                'failed': failed_count,
                'total': cancelled_count + failed_count,
                'task_type': task_type
            }
    
    def get_all_tasks(self, status: str = None, task_type: str = None) -> List[Dict[str, Any]]:
        """
        获取所有任务
        
        Args:
            status: 状态过滤（pending/running/completed/failed）
            task_type: 任务类型过滤
        
        Returns:
            任务列表
        """
        tasks_dict = self.task_monitor.get_all_tasks(status=status, task_type=task_type)
        # 将Task对象转换为字典列表
        return [task.to_dict() for task in tasks_dict.values()]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            统计信息字典
        """
        return {
            'task_stats': self.task_monitor.get_statistics(),
            'resource_usage': self.resource_manager.get_resource_usage(),
            'concurrency': self.concurrency_manager.current_concurrent,
            'queue_size': self.task_queue.size()
        }
    
    def _worker_loop(self) -> None:
        """工作线程循环"""
        logger.info("工作线程启动")
        
        while self.is_running:
            try:
                # 检查是否可以执行新任务
                if not self._can_execute_task():
                    import time
                    time.sleep(0.1)
                    continue
                
                # 从队列获取下一个任务
                task = self.task_queue.get_next_task()
                if not task:
                    import time
                    time.sleep(0.1)
                    continue
                
                # 检查任务依赖
                if not self._check_dependencies(task):
                    # 依赖未满足，重新入队
                    self.task_queue.add_task(task)
                    import time
                    time.sleep(0.1)
                    continue
                
                # 检查任务流水线锁（如果任务属于文件）
                if task.file_id:
                    # 尝试获取任务流水线锁
                    if not self.group_manager.acquire_pipeline_lock(task):
                        # 无法获取锁，重新入队
                        self.task_queue.add_task(task)
                        import time
                        time.sleep(0.1)
                        continue
                
                try:
                    # 执行任务
                    self._execute_task(task)
                finally:
                    # 释放任务流水线锁（如果有）
                    if task.file_id:
                        self.group_manager.release_pipeline_lock(task)
                
            except Exception as e:
                logger.error(f"工作线程错误: {e}")
                import time
                time.sleep(1.0)
        
        logger.info("工作线程结束")
    
    def _can_execute_task(self) -> bool:
        """
        检查是否可以执行新任务
        
        Returns:
            是否可以执行
        """
        # 检查并发限制
        current_concurrent = self.concurrency_manager.current_concurrent
        max_concurrent = self.concurrency_manager.config.max_concurrent
        
        if current_concurrent >= max_concurrent:
            return False
        
        # 检查资源使用情况（使用简化的2级OOM处理）
        if self.resource_manager.should_pause_tasks():
            return False
        
        return True
    
    def _check_dependencies(self, task: Task) -> bool:
        """
        检查任务依赖
        
        Args:
            task: 任务
        
        Returns:
            依赖是否满足
        """
        for dep_id in task.depends_on:
            dep_task = self.task_monitor.get_task(dep_id)
            if not dep_task or dep_task.status != 'completed':
                return False
        
        return True
    
    def _execute_task(self, task: Task) -> None:
        """
        执行任务
        
        Args:
            task: 任务
        """
        try:
            # 增加并发计数
            self.concurrency_manager.increment_concurrent()
            
            # 执行任务
            success = self.task_executor.execute_task(task)
            
            if success:
                task.status = 'completed'
            else:
                task.status = 'failed'
            
            # 更新任务监控器
            self.task_monitor.update_task(task)
            
            logger.info(f"任务执行{'成功' if success else '失败'}: {task.id}")
            
        except Exception as e:
            # 更新任务状态
            task.status = 'failed'
            task.error = str(e)
            self.task_monitor.update_task(task)
            
            logger.error(f"任务执行失败: {task.id}, 错误: {e}")
            
        finally:
            # 减少并发计数
            self.concurrency_manager.decrement_concurrent()