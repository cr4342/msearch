"""
任务管理器
负责任务队列管理、调度和状态跟踪
"""

import uuid
import json
import time
import threading
from typing import Any, Dict, List, Optional, Callable
from pathlib import Path
import logging
from datetime import datetime
from queue import PriorityQueue

logger = logging.getLogger(__name__)


class Task:
    """任务数据类"""
    
    def __init__(
        self,
        task_type: str,
        task_data: Dict[str, Any],
        priority: int = 5,
        max_retries: int = 3,
        depends_on: Optional[List[str]] = None
    ):
        """
        初始化任务
        
        Args:
            task_type: 任务类型
            task_data: 任务数据
            priority: 优先级（0-10，越小越优先）
            max_retries: 最大重试次数
            depends_on: 依赖的任务ID列表
        """
        self.id = str(uuid.uuid4())
        self.task_type = task_type
        self.task_data = task_data
        self.priority = priority
        self.status = 'pending'
        self.created_at = time.time()
        self.updated_at = time.time()
        self.started_at: Optional[float] = None
        self.completed_at: Optional[float] = None
        self.retry_count = 0
        self.max_retries = max_retries
        self.result: Optional[Any] = None
        self.error: Optional[str] = None
        self.progress = 0.0
        self.depends_on = depends_on or []
        self.blocking_for: List[str] = []
    
    def __lt__(self, other: 'Task') -> bool:
        """任务优先级比较（用于优先队列）"""
        return self.priority < other.priority
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'task_type': self.task_type,
            'task_data': self.task_data,
            'priority': self.priority,
            'status': self.status,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'result': self.result,
            'error': self.error,
            'progress': self.progress,
            'depends_on': self.depends_on,
            'blocking_for': self.blocking_for
        }


class TaskManager:
    """任务管理器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化任务管理器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.task_config = config.get('task_manager', {})
        
        # 任务队列
        self.task_queue: PriorityQueue = PriorityQueue()
        self.running_tasks: Dict[str, Task] = {}
        self.pending_tasks: Dict[str, Task] = {}
        self.completed_tasks: Dict[str, Task] = {}
        self.failed_tasks: Dict[str, Task] = {}
        
        # 并发控制
        self.max_concurrent_tasks = self.task_config.get('max_concurrent_tasks', 4)
        self.max_concurrent_by_type = self.task_config.get('max_concurrent_by_type', {
            'file_scan': 1,
            'file_embed': 2,
            'video_slice': 2,
            'audio_segment': 2
        })
        
        # 任务处理器
        self.task_handlers: Dict[str, Callable] = {}
        self.task_listeners: Dict[str, List[Callable]] = {}
        
        # 锁
        self.queue_lock = threading.Lock()
        self.tasks_lock = threading.Lock()
        
        # 持久化
        self.enable_persistence = self.task_config.get('enable_persistence', True)
        self.persistence_file = Path(self.task_config.get('persistence_file', 'data/tasks/task_queue.json'))
        self.persistence_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 线程控制
        self.is_running = False
        self.worker_thread: Optional[threading.Thread] = None
        
        logger.info("任务管理器初始化完成")
    
    def initialize(self) -> bool:
        """
        初始化任务管理器
        
        Returns:
            是否成功
        """
        try:
            # 加载持久化的任务
            if self.enable_persistence and self.persistence_file.exists():
                self._load_persistent_tasks()
            
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
        self.is_running = False
        
        if self.worker_thread:
            self.worker_thread.join(timeout=5.0)
        
        # 保存任务状态
        if self.enable_persistence:
            self._save_persistent_tasks()
        
        logger.info("任务管理器已关闭")
    
    def create_task(
        self,
        task_type: str,
        task_data: Dict[str, Any],
        priority: int = 5,
        max_retries: int = 3,
        depends_on: Optional[List[str]] = None
    ) -> str:
        """
        创建任务
        
        Args:
            task_type: 任务类型
            task_data: 任务数据
            priority: 优先级
            max_retries: 最大重试次数
            depends_on: 依赖的任务ID列表
        
        Returns:
            任务ID
        """
        task = Task(task_type, task_data, priority, max_retries, depends_on)
        
        with self.queue_lock:
            self.pending_tasks[task.id] = task
            self.task_queue.put(task)
        
        self._notify_listeners('task_created', task)
        logger.info(f"任务创建: {task.id}, 类型: {task_type}, 优先级: {priority}")
        
        return task.id
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务
        
        Args:
            task_id: 任务ID
        
        Returns:
            任务数据字典
        """
        with self.tasks_lock:
            task = self._get_task_by_id(task_id)
            if task:
                return task.to_dict()
            return None
    
    def _get_task_by_id(self, task_id: str) -> Optional[Task]:
        """根据ID获取任务对象"""
        for task_dict in [self.pending_tasks, self.running_tasks, self.completed_tasks, self.failed_tasks]:
            if task_id in task_dict:
                return task_dict[task_id]
        return None
    
    def update_task_status(
        self,
        task_id: str,
        status: str,
        result: Optional[Any] = None,
        error: Optional[str] = None,
        progress: float = 0.0
    ) -> bool:
        """
        更新任务状态
        
        Args:
            task_id: 任务ID
            status: 新状态
            result: 任务结果
            error: 错误信息
            progress: 任务进度
        
        Returns:
            是否成功
        """
        try:
            with self.tasks_lock:
                task = self._get_task_by_id(task_id)
                if not task:
                    return False
                
                # 更新状态
                old_status = task.status
                task.status = status
                task.updated_at = time.time()
                
                if status == 'running' and old_status != 'running':
                    task.started_at = time.time()
                elif status == 'completed':
                    task.completed_at = time.time()
                    task.progress = 1.0
                elif status == 'failed':
                    task.error = error
                
                if result is not None:
                    task.result = result
                
                if error is not None:
                    task.error = error
                
                if progress > 0:
                    task.progress = progress
                
                # 更新任务字典
                if task_id in self.pending_tasks:
                    if status == 'running':
                        self.running_tasks[task_id] = self.pending_tasks.pop(task_id)
                    elif status == 'completed':
                        self.completed_tasks[task_id] = self.pending_tasks.pop(task_id)
                    elif status == 'failed':
                        self.failed_tasks[task_id] = self.pending_tasks.pop(task_id)
                elif task_id in self.running_tasks:
                    if status == 'completed':
                        self.completed_tasks[task_id] = self.running_tasks.pop(task_id)
                    elif status == 'failed':
                        self.failed_tasks[task_id] = self.running_tasks.pop(task_id)
                
                self._notify_listeners('task_updated', task)
            
            return True
        except Exception as e:
            logger.error(f"更新任务状态失败: {task_id}, {e}")
            return False
    
    def get_pending_tasks(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取待处理任务
        
        Args:
            limit: 返回数量限制
        
        Returns:
            任务列表
        """
        with self.tasks_lock:
            tasks = list(self.pending_tasks.values())
            tasks.sort(key=lambda t: t.priority)
            return [task.to_dict() for task in tasks[:limit]]
    
    def get_running_tasks(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取运行中任务
        
        Args:
            limit: 返回数量限制
        
        Returns:
            任务列表
        """
        with self.tasks_lock:
            tasks = list(self.running_tasks.values())
            return [task.to_dict() for task in tasks[:limit]]
    
    def get_completed_tasks(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取已完成任务
        
        Args:
            limit: 返回数量限制
        
        Returns:
            任务列表
        """
        with self.tasks_lock:
            tasks = list(self.completed_tasks.values())
            tasks.sort(key=lambda t: t.completed_at, reverse=True)
            return [task.to_dict() for task in tasks[:limit]]
    
    def get_failed_tasks(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取失败任务
        
        Args:
            limit: 返回数量限制
        
        Returns:
            任务列表
        """
        with self.tasks_lock:
            tasks = list(self.failed_tasks.values())
            tasks.sort(key=lambda t: t.created_at, reverse=True)
            return [task.to_dict() for task in tasks[:limit]]
    
    def cancel_task(self, task_id: str) -> bool:
        """
        取消任务
        
        Args:
            task_id: 任务ID
        
        Returns:
            是否成功
        """
        try:
            with self.tasks_lock:
                task = self._get_task_by_id(task_id)
                if not task:
                    return False
                
                if task.status == 'running':
                    # 运行中的任务不能直接取消，需要通过其他机制
                    return False
                
                # 从待处理队列中移除
                if task_id in self.pending_tasks:
                    del self.pending_tasks[task_id]
                    task.status = 'cancelled'
                    self.failed_tasks[task_id] = task
                
                self._notify_listeners('task_cancelled', task)
                logger.info(f"任务取消: {task_id}")
                return True
        
        except Exception as e:
            logger.error(f"取消任务失败: {task_id}, {e}")
            return False
    
    def pause_task(self, task_id: str) -> bool:
        """
        暂停任务
        
        Args:
            task_id: 任务ID
        
        Returns:
            是否成功
        """
        # TODO: 实现任务暂停逻辑
        return False
    
    def resume_task(self, task_id: str) -> bool:
        """
        恢复任务
        
        Args:
            task_id: 任务ID
        
        Returns:
            是否成功
        """
        # TODO: 实现任务恢复逻辑
        return False
    
    def get_task_stats(self) -> Dict[str, Any]:
        """
        获取任务统计信息
        
        Returns:
            统计信息字典
        """
        with self.tasks_lock:
            return {
                'pending_count': len(self.pending_tasks),
                'running_count': len(self.running_tasks),
                'completed_count': len(self.completed_tasks),
                'failed_count': len(self.failed_tasks),
                'total_count': len(self.pending_tasks) + len(self.running_tasks) + len(self.completed_tasks) + len(self.failed_tasks)
            }
    
    def add_task_listener(self, event_type: str, callback: Callable) -> None:
        """
        添加任务监听器
        
        Args:
            event_type: 事件类型
            callback: 回调函数
        """
        if event_type not in self.task_listeners:
            self.task_listeners[event_type] = []
        self.task_listeners[event_type].append(callback)
    
    def remove_task_listener(self, event_type: str, callback: Callable) -> None:
        """
        移除任务监听器
        
        Args:
            event_type: 事件类型
            callback: 回调函数
        """
        if event_type in self.task_listeners and callback in self.task_listeners[event_type]:
            self.task_listeners[event_type].remove(callback)
    
    def register_task_handler(self, task_type: str, handler: Callable) -> None:
        """
        注册任务处理器
        
        Args:
            task_type: 任务类型
            handler: 处理函数
        """
        self.task_handlers[task_type] = handler
        logger.info(f"注册任务处理器: {task_type}")
    
    def _worker_loop(self) -> None:
        """工作线程循环"""
        logger.info("任务工作线程启动")
        
        while self.is_running:
            try:
                # 检查并发限制
                if len(self.running_tasks) >= self.max_concurrent_tasks:
                    time.sleep(0.1)
                    continue
                
                # 获取下一个任务
                with self.queue_lock:
                    if self.task_queue.empty():
                        time.sleep(0.1)
                        continue
                    
                    task = self.task_queue.get()
                
                # 检查依赖
                if not self._check_dependencies(task):
                    # 依赖未满足，放回队列
                    with self.queue_lock:
                        self.task_queue.put(task)
                    time.sleep(0.5)
                    continue
                
                # 检查类型并发限制
                if not self._check_type_concurrency(task):
                    with self.queue_lock:
                        self.task_queue.put(task)
                    time.sleep(0.5)
                    continue
                
                # 执行任务
                self._execute_task(task)
            
            except Exception as e:
                logger.error(f"工作线程错误: {e}")
                time.sleep(1.0)
        
        logger.info("任务工作线程停止")
    
    def _execute_task(self, task: Task) -> None:
        """执行任务"""
        task_id = task.id
        task_type = task.task_type
        
        try:
            # 更新状态为运行中
            self.update_task_status(task_id, 'running')
            
            # 获取任务处理器
            handler = self.task_handlers.get(task_type)
            if not handler:
                raise ValueError(f"未注册的任务处理器: {task_type}")
            
            # 执行任务
            result = handler(task)
            
            # 更新状态为完成
            self.update_task_status(task_id, 'completed', result=result)
            logger.info(f"任务完成: {task_id}")
        
        except Exception as e:
            logger.error(f"任务执行失败: {task_id}, {e}")
            
            # 检查是否需要重试
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.status = 'pending'
                
                # 放回队列
                with self.queue_lock:
                    self.task_queue.put(task)
                
                logger.info(f"任务重试: {task_id}, 重试次数: {task.retry_count}")
            else:
                # 标记为失败
                self.update_task_status(
                    task_id,
                    'failed',
                    error=str(e)
                )
                logger.error(f"任务失败: {task_id}")
    
    def _check_dependencies(self, task: Task) -> bool:
        """
        检查任务依赖
        
        Args:
            task: 任务对象
        
        Returns:
            依赖是否满足
        """
        if not task.depends_on:
            return True
        
        for dep_id in task.depends_on:
            dep_task = self._get_task_by_id(dep_id)
            if not dep_task or dep_task.status != 'completed':
                return False
        
        return True
    
    def _check_type_concurrency(self, task: Task) -> bool:
        """
        检查类型并发限制
        
        Args:
            task: 任务对象
        
        Returns:
            是否可以执行
        """
        task_type = task.task_type
        max_concurrent = self.max_concurrent_by_type.get(task_type, 2)
        
        current_count = sum(
            1 for t in self.running_tasks.values()
            if t.task_type == task_type
        )
        
        return current_count < max_concurrent
    
    def _notify_listeners(self, event_type: str, task: Task) -> None:
        """
        通知监听器
        
        Args:
            event_type: 事件类型
            task: 任务对象
        """
        if event_type in self.task_listeners:
            for callback in self.task_listeners[event_type]:
                try:
                    callback(task)
                except Exception as e:
                    logger.error(f"监听器回调失败: {event_type}, {e}")
    
    def _save_persistent_tasks(self) -> None:
        """保存任务到持久化文件"""
        try:
            tasks_to_save = []
            
            # 保存待处理和运行中的任务
            for task in list(self.pending_tasks.values()) + list(self.running_tasks.values()):
                tasks_to_save.append(task.to_dict())
            
            with open(self.persistence_file, 'w', encoding='utf-8') as f:
                json.dump(tasks_to_save, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"任务持久化保存: {len(tasks_to_save)}个任务")
        
        except Exception as e:
            logger.error(f"保存持久化任务失败: {e}")
    
    def _load_persistent_tasks(self) -> None:
        """从持久化文件加载任务"""
        try:
            with open(self.persistence_file, 'r', encoding='utf-8') as f:
                tasks_data = json.load(f)
            
            for task_data in tasks_data:
                task = Task(
                    task_type=task_data['task_type'],
                    task_data=task_data['task_data'],
                    priority=task_data['priority'],
                    max_retries=task_data['max_retries'],
                    depends_on=task_data.get('depends_on', [])
                )
                
                # 恢复任务状态
                task.status = task_data['status']
                task.created_at = task_data['created_at']
                task.updated_at = task_data['updated_at']
                task.started_at = task_data.get('started_at')
                task.completed_at = task_data.get('completed_at')
                task.retry_count = task_data.get('retry_count', 0)
                task.result = task_data.get('result')
                task.error = task_data.get('error')
                task.progress = task_data.get('progress', 0.0)
                
                # 根据状态放入对应的字典
                if task.status == 'pending':
                    self.pending_tasks[task.id] = task
                    self.task_queue.put(task)
                elif task.status == 'running':
                    self.running_tasks[task.id] = task
                elif task.status == 'completed':
                    self.completed_tasks[task.id] = task
                elif task.status == 'failed':
                    self.failed_tasks[task.id] = task
            
            logger.info(f"任务持久化加载: {len(tasks_data)}个任务")
        
        except Exception as e:
            logger.error(f"加载持久化任务失败: {e}")


def create_task_manager(config: Dict[str, Any]) -> TaskManager:
    """
    创建任务管理器实例
    
    Args:
        config: 配置字典
    
    Returns:
        TaskManager实例
    """
    task_manager = TaskManager(config)
    return task_manager