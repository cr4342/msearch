"""
任务队列管理器
专门负责任务队列管理，不涉及优先级计算或执行逻辑
"""

import heapq
import threading
from typing import Dict, List, Optional
from datetime import datetime

from .task import Task


class TaskQueue:
    """任务队列管理器"""
    
    def __init__(self):
        # 优先级队列：使用堆实现
        self.priority_queue = []
        # 任务索引：快速查找任务
        self.task_index: Dict[str, Task] = {}
        # 线程锁
        self.lock = threading.Lock()
        # 统计信息
        self.stats = {
            'total_added': 0,
            'total_removed': 0
        }
    
    def add_task(self, task: Task) -> None:
        """
        添加任务到队列
        
        Args:
            task: 任务对象
        """
        with self.lock:
            # 如果任务已存在，先移除
            if task.id in self.task_index:
                self._remove_task_internal(task.id)
            
            # 添加到索引
            self.task_index[task.id] = task
            
            # 添加到优先级队列（使用负优先级实现最大堆）
            heapq.heappush(self.priority_queue, (-task.priority, task.created_at or datetime.now(), task.id))
            
            self.stats['total_added'] += 1
    
    def get_next_task(self) -> Optional[Task]:
        """
        获取下一个任务
        
        Returns:
            任务对象或None
        """
        with self.lock:
            if not self.priority_queue:
                return None
            
            # 获取优先级最高的任务
            priority, created_at, task_id = heapq.heappop(self.priority_queue)
            
            # 检查任务是否还存在于索引中
            if task_id not in self.task_index:
                # 任务可能已被移除，继续尝试下一个
                return self.get_next_task()
            
            task = self.task_index[task_id]
            
            # 检查任务状态
            if task.status not in ['pending', 'waiting_pipeline']:
                # 任务状态不正确，移除并继续
                del self.task_index[task_id]
                return self.get_next_task()
            
            # 从索引中移除（任务已被取出）
            del self.task_index[task_id]
            
            return task
    
    def remove_task(self, task_id: str) -> bool:
        """
        从队列中移除任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否成功
        """
        with self.lock:
            return self._remove_task_internal(task_id)
    
    def _remove_task_internal(self, task_id: str) -> bool:
        """内部移除任务方法"""
        if task_id in self.task_index:
            del self.task_index[task_id]
            self.stats['total_removed'] += 1
            return True
        return False
    
    def peek_next_task(self) -> Optional[Task]:
        """
        预览下一个任务（不移除）
        
        Returns:
            任务对象或None
        """
        with self.lock:
            # 创建副本以避免修改原队列
            temp_queue = self.priority_queue.copy()
            
            while temp_queue:
                priority, created_at, task_id = heapq.heappop(temp_queue)
                
                if task_id in self.task_index:
                    task = self.task_index[task_id]
                    if task.status in ['pending', 'waiting_pipeline']:
                        return task
            
            return None
    
    def size(self) -> int:
        """
        获取队列大小
        
        Returns:
            队列中任务数量
        """
        with self.lock:
            return len(self.task_index)
    
    def is_empty(self) -> bool:
        """
        检查队列是否为空
        
        Returns:
            是否为空
        """
        return self.size() == 0
    
    def get_all_tasks(self) -> List[Task]:
        """
        获取队列中的所有任务
        
        Returns:
            任务列表
        """
        with self.lock:
            return list(self.task_index.values())
    
    def clear(self) -> None:
        """清空队列"""
        with self.lock:
            self.priority_queue.clear()
            self.task_index.clear()
    
    def update_task_priority(self, task_id: str, new_priority: int) -> bool:
        """
        更新任务优先级
        
        Args:
            task_id: 任务ID
            new_priority: 新优先级
            
        Returns:
            是否成功
        """
        with self.lock:
            if task_id not in self.task_index:
                return False
            
            task = self.task_index[task_id]
            task.priority = new_priority
            
            # 从队列中移除并重新添加
            self._remove_task_internal(task_id)
            self.add_task(task)
            
            return True
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """
        获取指定任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务对象或None
        """
        with self.lock:
            return self.task_index.get(task_id)
    
    def get_stats(self) -> Dict[str, int]:
        """
        获取统计信息
        
        Returns:
            统计信息字典
        """
        with self.lock:
            stats = self.stats.copy()
            stats['queue_size'] = len(self.task_index)
            return stats