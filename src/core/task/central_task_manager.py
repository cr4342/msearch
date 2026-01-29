"""
中央任务管理器

统一协调所有任务管理功能，解决职责边界模糊问题。
严格遵循依赖注入原则，所有依赖通过构造函数参数传递。
"""

import uuid
import threading
import time
from typing import Any, Dict, List, Optional, Callable
from pathlib import Path
from datetime import datetime
import logging

from src.interfaces.task_interface import (
    TaskManagerInterface,
    TaskSchedulerInterface,
    TaskExecutorInterface,
    TaskMonitorInterface,
    TaskGroupManagerInterface
)

from .task import Task


logger = logging.getLogger(__name__)


class CentralTaskManager(TaskManagerInterface):
    """
    中央任务管理器：统一协调所有任务管理功能
    
    职责：
    - 任务生命周期管理（创建、执行、取消）
    - 组件协调和集成（orchestrator 角色）
    - 对外提供统一的任务管理接口
    - 调度循环控制
    
    明确边界：
    - ✅ 负责任务的创建、取消、状态查询
    - ✅ 协调各组件完成调度流程
    - ✅ 维护调度循环，触发任务调度
    - ❌ 不直接计算优先级（委托给TaskScheduler）
    - ❌ 不直接执行任务（委托给TaskExecutor）
    - ❌ 不直接管理任务组锁（委托给TaskGroupManager）
    """
    
    def __init__(
        self,
        config: Dict[str, Any],
        task_scheduler: TaskSchedulerInterface,
        task_executor: TaskExecutorInterface,
        task_monitor: TaskMonitorInterface,
        task_group_manager: TaskGroupManagerInterface,
        device: str = 'cpu'
    ):
        """
        初始化中央任务管理器
        
        Args:
            config: 配置字典
            task_scheduler: 任务调度器
            task_executor: 任务执行器
            task_monitor: 任务监控器
            task_group_manager: 任务组管理器
            device: 设备类型（cuda/cpu）
        """
        self.config = config
        self.device = device
        
        # 任务配置
        self.task_config = config.get('task_manager', {})
        
        # 依赖注入：通过构造函数参数接收组件
        self.task_scheduler = task_scheduler
        self.task_executor = task_executor
        self.task_monitor = task_monitor
        self.group_manager = task_group_manager
        
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
            'cancelled_tasks': 0,
            'retried_tasks': 0
        }
        
        logger.info("中央任务管理器初始化完成（依赖注入模式）")
    
    def create_task(
        self,
        task_type: str,
        task_data: Dict[str, Any],
        priority: int = 5,
        file_id: Optional[str] = None,
        file_path: Optional[str] = None,
        depends_on: Optional[List[str]] = None,
        group_id: Optional[str] = None
    ) -> str:
        """
        创建任务
        
        Args:
            task_type: 任务类型
            task_data: 任务数据
            priority: 优先级
            file_id: 关联的文件ID
            file_path: 关联的文件路径
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
        optimized_priority = self.task_scheduler.calculate_priority(task)
        task.priority = optimized_priority
        
        # 添加到任务组
        if file_id:
            self.group_manager.add_task_to_group_sync(file_id, task)
        
        # 添加到调度器队列
        self.task_scheduler.enqueue_task(task)
        
        # 添加到监控器
        self.task_monitor.add_task(task)
        
        # 更新统计
        with self.lock:
            self.stats['total_tasks'] += 1
        
        logger.info(f"任务创建成功: {task_id}, 类型: {task_type}, 优先级: {optimized_priority}")
        
        return task_id
    
    def cancel_task(self, task_id: str) -> bool:
        """
        取消任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否成功取消
        """
        try:
            # 更新任务状态
            self.task_monitor.update_task_status(task_id, 'cancelled')
            
            # 更新统计
            with self.lock:
                self.stats['cancelled_tasks'] += 1
            
            logger.info(f"任务已取消: {task_id}")
            return True
        except Exception as e:
            logger.error(f"取消任务失败 {task_id}: {e}")
            return False
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务状态字典
        """
        return self.task_monitor.get_task(task_id)
    
    def get_all_tasks(
        self,
        status: Optional[str] = None,
        task_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取所有任务
        
        Args:
            status: 状态过滤
            task_type: 任务类型过滤
            
        Returns:
            任务列表
        """
        tasks_dict = self.task_monitor.get_all_tasks(status=status)
        # 将Task对象转换为字典列表
        return [task.to_dict() for task in tasks_dict.values()]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            统计信息字典
        """
        with self.lock:
            stats = self.stats.copy()
        
        # 添加各组件的统计
        stats['scheduler'] = {
            'queue_size': self.task_scheduler.get_queue_size()
        }
        
        return stats
    
    def start(self) -> None:
        """启动任务管理器"""
        if self.is_running:
            logger.warning("任务管理器已经在运行")
            return
        
        self.is_running = True
        
        # 启动工作线程
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        
        logger.info("中央任务管理器已启动")
    
    def stop(self) -> None:
        """停止任务管理器"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # 等待工作线程结束
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=5.0)
        
        logger.info("中央任务管理器已停止")
    
    def _worker_loop(self) -> None:
        """工作线程主循环"""
        logger.info("任务调度工作线程已启动")
        
        import asyncio
        
        while self.is_running:
            try:
                # 从调度器获取任务（同步调用异步方法）
                task = asyncio.run(self.task_scheduler.dequeue_task())
                
                if task:
                    # 执行任务
                    self._execute_task(task)
                else:
                    # 没有任务，短暂休眠
                    time.sleep(0.1)
                    
            except Exception as e:
                logger.error(f"工作线程出错: {e}")
                time.sleep(1)
    
    def _execute_task(self, task: Task) -> None:
        """
        执行任务
        
        Args:
            task: 任务对象
        """
        try:
            logger.debug(f"执行任务: {task.id}, 类型: {task.task_type}")
            
            # 更新任务状态
            self.task_monitor.update_task_status(task.id, 'running')
            
            # 委托给执行器
            success = self.task_executor.execute_task(task)
            
            if success:
                self.task_monitor.update_task_status(task.id, 'completed', progress=1.0)
                with self.lock:
                    self.stats['completed_tasks'] += 1
            else:
                self.task_monitor.update_task_status(task.id, 'failed')
                with self.lock:
                    self.stats['failed_tasks'] += 1
                    
        except Exception as e:
            logger.error(f"执行任务失败 {task.id}: {e}")
            self.task_monitor.update_task_status(task.id, 'failed')
            with self.lock:
                self.stats['failed_tasks'] += 1
    
    def register_task_handler(self, task_type: str, handler: Callable) -> bool:
        """
        注册任务处理器
        
        Args:
            task_type: 任务类型
            handler: 处理函数
            
        Returns:
            是否注册成功
        """
        self.task_handlers[task_type] = handler
        return self.task_executor.register_handler(task_type, handler)
