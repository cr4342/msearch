"""
中央任务管理器
统一协调所有任务管理功能，解决职责边界模糊问题
"""

import uuid
import threading
import time
from typing import Any, Dict, List, Optional, Callable
from pathlib import Path
from datetime import datetime
import logging

from .task import Task
from .task_queue import TaskQueue
from .task_executor import OptimizedTaskExecutor
from .priority_calculator import PriorityCalculator
from .task_group_manager import TaskGroupManager
from .resource_manager import OptimizedResourceManager
from .task_monitor import OptimizedTaskMonitor
from .pipeline_lock_manager import PipelineLockManager
from .concurrency_manager import ConcurrencyConfig, OptimizedConcurrencyManager


logger = logging.getLogger(__name__)


class CentralTaskManager:
    """中央任务管理器：统一协调所有任务管理功能"""
    
    def __init__(self, config: Dict[str, Any], device: str = 'cpu'):
        """
        初始化中央任务管理器
        
        Args:
            config: 配置字典
            device: 设备类型（cuda/cpu），从配置文件读取
        """
        self.config = config
        self.device = device
        
        # 任务配置
        self.task_config = config.get('task_manager', {})
        
        # 创建专业化组件
        self.task_queue = TaskQueue()
        self.task_executor = OptimizedTaskExecutor()
        self.priority_calculator = PriorityCalculator()
        self.group_manager = TaskGroupManager(self.task_config)
        self.resource_manager = OptimizedResourceManager(self.task_config)
        self.task_monitor = OptimizedTaskMonitor()
        self.pipeline_lock_manager = PipelineLockManager()
        
        # 并发管理器（优化版）
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
        
        # 统计信息
        self.stats = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'running_tasks': 0
        }
        
        logger.info("中央任务管理器初始化完成")
    
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
            
            # 启动工作线程
            self.is_running = True
            self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
            self.worker_thread.start()
            
            logger.info("中央任务管理器启动成功")
            return True
        except Exception as e:
            logger.error(f"中央任务管理器初始化失败: {e}")
            return False
    
    def shutdown(self) -> None:
        """关闭任务管理器"""
        logger.info("正在关闭中央任务管理器...")
        
        self.is_running = False
        
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=5.0)
        
        # 关闭各组件
        self.concurrency_manager.shutdown()
        
        logger.info("中央任务管理器已关闭")
    
    def register_handler(self, task_type: str, handler: Callable) -> None:
        """
        注册任务处理器
        
        Args:
            task_type: 任务类型
            handler: 处理函数
        """
        self.task_handlers[task_type] = handler
        self.task_executor.register_handler(task_type, handler)
        logger.info(f"注册任务处理器: {task_type}")
    
    def create_task(self, task_type: str, task_data: Dict[str, Any], 
                   priority: int = 5, file_id: str = None, 
                   file_path: str = None, depends_on: List[str] = None,
                   group_id: str = None) -> str:
        """
        创建任务
        
        Args:
            task_type: 任务类型
            task_data: 任务数据
            priority: 优先级
            file_id: 文件ID
            file_path: 文件路径
            depends_on: 依赖的任务ID列表
            group_id: 任务组ID
        
        Returns:
            任务ID
        """
        task_id = str(uuid.uuid4())
        
        # 创建任务对象
        task = Task(
            id=task_id,
            task_type=task_type,
            task_data=task_data,
            priority=priority,
            file_id=file_id,
            file_path=file_path,
            depends_on=depends_on or [],
            group_id=group_id
        )
        
        # 计算优化后的优先级
        optimized_priority = self.priority_calculator.calculate_priority(
            task, 
            wait_time_compensation=True,
            pipeline_continuity=True
        )
        task.priority = optimized_priority
        
        # 添加到任务组
        if file_id:
            self.group_manager.add_task_to_group(task)
        
        # 检查依赖是否满足
        if not self._check_dependencies_satisfied(task):
            task.status = 'waiting_dependencies'
            logger.debug(f"任务 {task_id} 等待依赖完成")
        else:
            # 获取流水线锁（如果是核心任务）
            if self._is_pipeline_task(task_type):
                if not self.pipeline_lock_manager.acquire_pipeline_lock(task):
                    task.status = 'waiting_pipeline'
                    logger.debug(f"任务 {task_id} 等待流水线锁")
                else:
                    task.status = 'pending'
            else:
                task.status = 'pending'
        
        # 添加到队列和监控器
        self.task_queue.add_task(task)
        self.task_monitor.add_task(task)
        
        # 更新统计
        self.stats['total_tasks'] += 1
        
        logger.info(f"创建任务 {task_id} (类型: {task_type}, 优先级: {optimized_priority})")
        return task_id
    
    def _check_dependencies_satisfied(self, task: Task) -> bool:
        """检查任务依赖是否满足"""
        for dep_id in task.depends_on:
            dep_task = self.task_monitor.get_task(dep_id)
            if not dep_task or dep_task.status != 'completed':
                return False
        return True
    
    def _is_pipeline_task(self, task_type: str) -> bool:
        """检查是否为核心流水线任务"""
        pipeline_tasks = [
            'file_preprocessing', 
            'image_preprocess',
            'video_preprocess', 
            'audio_preprocess',
            'file_embed_image', 
            'file_embed_video', 
            'file_embed_audio'
        ]
        return task_type in pipeline_tasks
    
    def _worker_loop(self) -> None:
        """工作线程主循环"""
        logger.info("任务管理器工作线程启动")
        
        while self.is_running:
            try:
                # 检查资源状态
                resource_state = self.resource_manager.check_resource_usage()
                
                if resource_state == 'pause':
                    # 资源紧张，暂停非关键任务
                    time.sleep(2.0)
                    continue
                elif resource_state == 'warning':
                    # 资源警告，降低非核心任务优先级
                    pass
                
                # 获取可执行的任务
                ready_task = self._get_ready_task()
                
                if ready_task:
                    # 检查并发限制
                    current_running = self.task_monitor.get_running_count()
                    max_concurrent = self.concurrency_manager.get_target_concurrent()
                    
                    if current_running < max_concurrent:
                        # 执行任务
                        self._execute_task(ready_task)
                    else:
                        # 达到并发限制，稍后重试
                        time.sleep(0.1)
                else:
                    # 没有可执行的任务，稍后重试
                    time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"工作线程错误: {e}")
                time.sleep(1.0)
    
    def _get_ready_task(self) -> Optional[Task]:
        """获取下一个可执行的任务"""
        # 从队列中获取任务
        task = self.task_queue.get_next_task()
        
        if not task:
            return None
        
        # 检查依赖
        if not self._check_dependencies_satisfied(task):
            # 依赖未满足，放回队列等待
            self.task_queue.add_task(task)
            return None
        
        # 检查流水线锁
        if self._is_pipeline_task(task.task_type):
            if not self.pipeline_lock_manager.acquire_pipeline_lock(task):
                # 无法获取流水线锁，放回队列等待
                self.task_queue.add_task(task)
                return None
        
        # 更新任务状态
        task.status = 'running'
        task.started_at = datetime.now()
        self.task_monitor.update_task(task)
        
        return task
    
    def _execute_task(self, task: Task) -> None:
        """执行任务"""
        # 更新统计
        with self.lock:
            self.stats['running_tasks'] += 1
        
        try:
            # 执行任务
            success = self.task_executor.execute_task(task)
            
            # 更新任务状态
            if success:
                task.status = 'completed'
                task.completed_at = datetime.now()
                self.stats['completed_tasks'] += 1
            else:
                task.status = 'failed'
                self.stats['failed_tasks'] += 1
            
            task.updated_at = datetime.now()
            
            # 释放流水线锁
            if self._is_pipeline_task(task.task_type):
                self.pipeline_lock_manager.release_pipeline_lock(task)
            
            # 更新监控器
            self.task_monitor.update_task(task)
            
            # 处理任务完成后的逻辑
            self._on_task_completed(task)
            
            logger.info(f"任务 {task.id} 执行{'成功' if success else '失败'}")
            
        except Exception as e:
            logger.error(f"执行任务 {task.id} 时发生错误: {e}")
            task.status = 'failed'
            task.error = str(e)
            task.updated_at = datetime.now()
            self.task_monitor.update_task(task)
            self.stats['failed_tasks'] += 1
        
        finally:
            # 更新统计
            with self.lock:
                self.stats['running_tasks'] -= 1
    
    def _on_task_completed(self, task: Task) -> None:
        """任务完成后的处理"""
        # 检查是否有依赖此任务的其他任务
        dependent_tasks = self.task_monitor.get_tasks_dependent_on(task.id)
        
        for dep_task_id in dependent_tasks:
            dep_task = self.task_monitor.get_task(dep_task_id)
            if dep_task and dep_task.status == 'waiting_dependencies':
                # 依赖已完成，更新任务状态
                dep_task.status = 'pending'
                self.task_queue.add_task(dep_task)
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        return self.task_monitor.get_task(task_id)
    
    def get_all_tasks(self, status: str = None, task_type: str = None) -> List[Dict[str, Any]]:
        """获取所有任务"""
        return self.task_monitor.get_all_tasks(status, task_type)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = self.stats.copy()
        stats.update({
            'queue_size': self.task_queue.size(),
            'running_count': self.task_monitor.get_running_count(),
            'resource_state': self.resource_manager.check_resource_usage()
        })
        return stats
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        task = self.task_monitor.get_task(task_id)
        if not task:
            return False
        
        if task.status in ['completed', 'failed']:
            return False  # 已完成的任务无法取消
        
        # 从队列中移除
        self.task_queue.remove_task(task_id)
        
        # 更新状态
        task.status = 'cancelled'
        task.updated_at = datetime.now()
        self.task_monitor.update_task(task)
        
        # 释放流水线锁
        if self._is_pipeline_task(task.task_type):
            self.pipeline_lock_manager.release_pipeline_lock(task)
        
        logger.info(f"任务 {task_id} 已取消")
        return True
    
    def get_task_dependency_graph(self, group_id: str = None) -> Dict[str, Any]:
        """获取任务依赖图"""
        return self.task_monitor.generate_dependency_graph(group_id)