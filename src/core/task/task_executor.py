"""
优化后的任务执行器
专门负责任务执行，不与TaskManager产生循环依赖
"""

import logging
import time
from typing import Dict, Any, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from datetime import datetime

from .task import Task

logger = logging.getLogger(__name__)


class OptimizedTaskExecutor:
    """
    优化后的任务执行器
    
    职责：
    - 任务执行（调用具体的任务处理器）
    - 错误处理和重试（处理执行过程中的异常）
    - 进度更新（跟踪任务执行进度）
    - 任务状态管理（更新任务的运行状态）
    """
    
    def __init__(self):
        # 任务处理器映射
        self.task_handlers: Dict[str, Callable] = {}
        
        # 线程池
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # 任务执行统计
        self.execution_stats = {
            'total_executed': 0,
            'total_failed': 0,
            'total_retried': 0
        }
        
        # 重试配置
        self.max_retries = 3
        self.retry_delay = 5  # 秒
        
        logger.info("优化后的任务执行器初始化完成")
    
    def register_handler(self, task_type: str, handler: Callable) -> None:
        """
        注册任务处理器
        
        Args:
            task_type: 任务类型
            handler: 处理函数
        """
        self.task_handlers[task_type] = handler
        logger.info(f"任务处理器注册成功: {task_type}")
    
    def execute_task(self, task: Task) -> bool:
        """
        执行任务
        
        Args:
            task: 任务对象
            
        Returns:
            是否执行成功
        """
        try:
            # 更新任务状态为运行中
            task.status = 'running'
            task.started_at = datetime.now()
            
            # 获取任务处理器
            handler = self.task_handlers.get(task.task_type)
            if not handler:
                logger.error(f"未找到任务处理器: {task.task_type}")
                task.status = 'failed'
                task.error = f"未找到任务处理器: {task.task_type}"
                return False
            
            # 执行任务
            result = handler(task.task_data)
            
            # 更新任务结果
            task.result = result
            task.status = 'completed'
            task.completed_at = datetime.now()
            
            logger.info(f"任务执行成功: {task.id}")
            self.execution_stats['total_executed'] += 1
            
            return True
            
        except Exception as e:
            logger.error(f"任务执行失败: {task.id}, 错误: {e}")
            
            # 更新任务状态
            task.status = 'failed'
            task.error = str(e)
            task.completed_at = datetime.now()
            
            self.execution_stats['total_failed'] += 1
            
            return False
    
    def execute_task_with_retry(self, task: Task) -> bool:
        """
        执行任务（带重试机制）
        
        Args:
            task: 任务对象
            
        Returns:
            是否执行成功
        """
        for attempt in range(self.max_retries + 1):
            try:
                success = self.execute_task(task)
                
                if success:
                    return True
                elif attempt < self.max_retries:
                    # 重试前等待
                    logger.info(f"任务执行失败，准备重试 ({attempt + 1}/{self.max_retries}): {task.id}")
                    time.sleep(self.retry_delay)
                    self.execution_stats['total_retried'] += 1
                    continue
                else:
                    logger.error(f"任务执行失败，已达到最大重试次数: {task.id}")
                    return False
                    
            except Exception as e:
                logger.error(f"任务执行异常: {task.id}, 错误: {e}")
                if attempt < self.max_retries:
                    logger.info(f"准备重试 ({attempt + 1}/{self.max_retries}): {task.id}")
                    time.sleep(self.retry_delay)
                    continue
                else:
                    logger.error(f"任务执行失败，已达到最大重试次数: {task.id}")
                    return False
        
        return False
    
    def execute_batch_tasks(self, tasks: list[Task], max_concurrent: int = 4) -> Dict[str, Any]:
        """
        批量执行任务
        
        Args:
            tasks: 任务列表
            max_concurrent: 最大并发数
            
        Returns:
            执行结果统计
        """
        results = {
            'completed': 0,
            'failed': 0,
            'total': len(tasks)
        }
        
        with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            # 提交任务
            future_to_task = {
                executor.submit(self.execute_task_with_retry, task): task 
                for task in tasks
            }
            
            # 等待完成
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    success = future.result()
                    if success:
                        results['completed'] += 1
                    else:
                        results['failed'] += 1
                except Exception as e:
                    logger.error(f"批量执行任务异常: {task.id}, 错误: {e}")
                    results['failed'] += 1
        
        return results
    
    def shutdown(self) -> None:
        """关闭执行器"""
        if self.executor:
            self.executor.shutdown(wait=True)
        logger.info("任务执行器已关闭")
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """
        获取执行统计信息
        
        Returns:
            统计信息字典
        """
        return self.execution_stats.copy()
    
    def reset_stats(self) -> None:
        """重置统计信息"""
        self.execution_stats = {
            'total_executed': 0,
            'total_failed': 0,
            'total_retried': 0
        }
    
    def get_handler(self, task_type: str) -> Optional[Callable]:
        """
        获取任务处理器
        
        Args:
            task_type: 任务类型
            
        Returns:
            任务处理器或None
        """
        return self.task_handlers.get(task_type)
    
    def remove_handler(self, task_type: str) -> bool:
        """
        移除任务处理器
        
        Args:
            task_type: 任务类型
            
        Returns:
            是否成功
        """
        if task_type in self.task_handlers:
            del self.task_handlers[task_type]
            logger.info(f"任务处理器已移除: {task_type}")
            return True
        return False