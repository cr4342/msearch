"""
任务组管理器

职责：
- 文件级任务组管理（为每个文件创建和管理任务组）
- 任务组进度跟踪（监控同一文件的所有任务进度）
- 任务流水线锁管理（保障同一文件的核心任务连续执行）
- 文件级优先级管理（确保文件级优先级的正确应用）

明确边界：
- ✅ 负责管理文件与任务的映射关系
- ✅ 管理任务流水线锁的获取和释放
- ✅ 跟踪任务组进度
- ❌ 不执行任务
- ❌ 不计算优先级
- ❌ 不管理资源
- ❌ 不直接调度任务（提供锁状态供调度器查询）
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum

from .task import Task
from .task_types import TaskType, TaskStatus


logger = logging.getLogger(__name__)


@dataclass
class PipelineLock:
    """任务流水线锁"""
    owner_file: str
    owner_task: str
    acquired_at: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "owner_file": self.owner_file,
            "owner_task": self.owner_task,
            "acquired_at": self.acquired_at,
            "duration": time.time() - self.acquired_at
        }


@dataclass
class TaskGroup:
    """任务组"""
    file_id: str
    file_path: str
    tasks: Dict[str, Task] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    
    def add_task(self, task: Task):
        """添加任务到组"""
        self.tasks[task.id] = task
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务"""
        return self.tasks.get(task_id)
    
    def get_all_tasks(self) -> List[Task]:
        """获取所有任务"""
        return list(self.tasks.values())
    
    def get_pending_tasks(self) -> List[Task]:
        """获取待处理任务"""
        return [t for t in self.tasks.values() if t.status == TaskStatus.PENDING]
    
    def get_running_tasks(self) -> List[Task]:
        """获取运行中任务"""
        return [t for t in self.tasks.values() if t.status == TaskStatus.RUNNING]
    
    def get_completed_tasks(self) -> List[Task]:
        """获取已完成任务"""
        return [t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED]
    
    def get_failed_tasks(self) -> List[Task]:
        """获取失败任务"""
        return [t for t in self.tasks.values() if t.status == TaskStatus.FAILED]
    
    def get_core_tasks(self) -> List[Task]:
        """获取核心任务"""
        core_types = {
            TaskType.IMAGE_PREPROCESS,
            TaskType.VIDEO_PREPROCESS,
            TaskType.AUDIO_PREPROCESS,
            TaskType.VIDEO_SLICE,
            TaskType.FILE_EMBED_IMAGE,
            TaskType.FILE_EMBED_VIDEO,
            TaskType.FILE_EMBED_AUDIO
        }
        return [t for t in self.tasks.values() if t.type in core_types]
    
    def get_pending_core_tasks(self) -> List[Task]:
        """获取待处理的核心任务"""
        return [t for t in self.get_core_tasks() if t.status == TaskStatus.PENDING]
    
    def has_pending_core_tasks(self) -> bool:
        """检查是否有待处理的核心任务"""
        return len(self.get_pending_core_tasks()) > 0
    
    def get_progress(self) -> float:
        """获取任务组进度"""
        if not self.tasks:
            return 0.0
        
        completed = len(self.get_completed_tasks())
        total = len(self.tasks)
        
        return completed / total if total > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_id": self.file_id,
            "file_path": self.file_path,
            "created_at": self.created_at,
            "task_count": len(self.tasks),
            "pending_count": len(self.get_pending_tasks()),
            "running_count": len(self.get_running_tasks()),
            "completed_count": len(self.get_completed_tasks()),
            "failed_count": len(self.get_failed_tasks()),
            "progress": self.get_progress(),
            "has_pending_core_tasks": self.has_pending_core_tasks()
        }


class TaskGroupManager:
    """
    任务组管理器
    
    负责管理文件级任务组和任务流水线锁
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # 任务组存储
        self.task_groups: Dict[str, TaskGroup] = {}
        
        # 流水线锁存储
        self.pipeline_locks: Dict[str, PipelineLock] = {}
        
        # 锁
        self._lock = asyncio.Lock()
        
        # 运行状态
        self.is_running = False
        
        logger.info("TaskGroupManager initialized")
    
    async def start(self):
        """启动任务组管理器"""
        self.is_running = True
        logger.info("TaskGroupManager started")
    
    async def stop(self):
        """停止任务组管理器"""
        self.is_running = False
        
        # 释放所有锁
        async with self._lock:
            self.pipeline_locks.clear()
        
        logger.info("TaskGroupManager stopped")
    
    async def create_group(self, file_id: str, file_path: str) -> TaskGroup:
        """
        创建任务组
        
        Args:
            file_id: 文件ID
            file_path: 文件路径
        
        Returns:
            创建的任务组
        """
        async with self._lock:
            if file_id in self.task_groups:
                return self.task_groups[file_id]
            
            group = TaskGroup(file_id=file_id, file_path=file_path)
            self.task_groups[file_id] = group
            
            logger.debug(f"Task group created: {file_id}")
            return group
    
    async def add_task_to_group(self, file_id: str, task: Task) -> bool:
        """
        添加任务到任务组
        
        Args:
            file_id: 文件ID
            task: 要添加的任务
        
        Returns:
            是否成功添加
        """
        async with self._lock:
            if file_id not in self.task_groups:
                # 自动创建任务组
                self.task_groups[file_id] = TaskGroup(
                    file_id=file_id,
                    file_path=task.file_path
                )
            
            group = self.task_groups[file_id]
            group.add_task(task)
            
            logger.debug(f"Task {task.id} added to group {file_id}")
            return True
    
    async def get_group(self, file_id: str) -> Optional[TaskGroup]:
        """获取任务组"""
        async with self._lock:
            return self.task_groups.get(file_id)
    
    async def get_all_groups(self) -> List[TaskGroup]:
        """获取所有任务组"""
        async with self._lock:
            return list(self.task_groups.values())
    
    async def update_group_progress(self, file_id: str):
        """更新任务组进度"""
        async with self._lock:
            group = self.task_groups.get(file_id)
            if group:
                progress = group.get_progress()
                logger.debug(f"Group {file_id} progress updated: {progress:.2%}")
    
    # ==================== 任务流水线锁机制 ====================
    
    def is_pipeline_locked(self, file_id: str) -> bool:
        """
        检查文件的任务流水线是否被锁定
        
        Args:
            file_id: 文件ID
        
        Returns:
            是否被锁定
        """
        return file_id in self.pipeline_locks
    
    def get_pipeline_lock_owner(self, file_id: str) -> Optional[str]:
        """
        获取流水线锁的拥有者任务ID
        
        Args:
            file_id: 文件ID
        
        Returns:
            拥有者任务ID，如果没有锁则返回None
        """
        lock = self.pipeline_locks.get(file_id)
        return lock.owner_task if lock else None
    
    def acquire_pipeline_lock(self, file_id: str, task_id: str) -> bool:
        """
        获取任务流水线锁
        
        策略：
        - 如果锁不存在，创建锁并获取
        - 如果锁存在且是同文件的核心任务，允许执行（不阻塞）
        - 如果锁存在且是其他文件的任务，阻塞等待
        
        Args:
            file_id: 文件ID
            task_id: 任务ID
        
        Returns:
            是否成功获取锁
        """
        if file_id not in self.pipeline_locks:
            # 创建新锁
            self.pipeline_locks[file_id] = PipelineLock(
                owner_file=file_id,
                owner_task=task_id,
                acquired_at=time.time()
            )
            logger.debug(f"Pipeline lock acquired: {file_id} by {task_id}")
            return True
        
        lock = self.pipeline_locks[file_id]
        if lock.owner_file == file_id:
            # 同文件的核心任务，允许执行
            logger.debug(f"Pipeline lock already held by same file: {file_id}")
            return True
        
        # 其他文件的任务，需要等待
        logger.debug(f"Pipeline lock held by different file: {lock.owner_file}")
        return False
    
    def release_pipeline_lock(self, file_id: str, task_id: str) -> bool:
        """
        释放任务流水线锁
        
        策略：
        - 只有锁的拥有者可以释放锁
        - 释放时检查是否还有未完成的同文件核心任务
        - 如果没有，才真正释放锁
        
        Args:
            file_id: 文件ID
            task_id: 任务ID
        
        Returns:
            是否成功释放锁
        """
        if file_id not in self.pipeline_locks:
            return False
        
        lock = self.pipeline_locks[file_id]
        if lock.owner_task != task_id:
            logger.warning(f"Cannot release lock: {file_id} not owned by {task_id}")
            return False
        
        # 检查是否还有未完成的同文件核心任务
        group = self.task_groups.get(file_id)
        if group and group.has_pending_core_tasks():
            # 还有核心任务未完成，不释放锁
            logger.debug(f"Not releasing lock: pending core tasks exist for {file_id}")
            return False
        
        # 释放锁
        del self.pipeline_locks[file_id]
        logger.debug(f"Pipeline lock released: {file_id} by {task_id}")
        return True
    
    def has_pending_core_tasks(self, file_id: str) -> bool:
        """
        检查文件是否还有待处理的核心任务
        
        Args:
            file_id: 文件ID
        
        Returns:
            是否有待处理的核心任务
        """
        group = self.task_groups.get(file_id)
        if not group:
            return False
        
        return group.has_pending_core_tasks()
    
    def get_lock_status(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        获取锁状态
        
        Args:
            file_id: 文件ID
        
        Returns:
            锁状态信息
        """
        lock = self.pipeline_locks.get(file_id)
        if lock:
            return {
                "locked": True,
                "lock_info": lock.to_dict()
            }
        return {"locked": False}
    
    # ==================== 统计和查询 ====================
    
    async def get_statistics(self) -> Dict[str, Any]:
        """获取任务组统计信息"""
        async with self._lock:
            total_groups = len(self.task_groups)
            total_tasks = sum(len(g.tasks) for g in self.task_groups.values())
            pending_tasks = sum(len(g.get_pending_tasks()) for g in self.task_groups.values())
            running_tasks = sum(len(g.get_running_tasks()) for g in self.task_groups.values())
            completed_tasks = sum(len(g.get_completed_tasks()) for g in self.task_groups.values())
            failed_tasks = sum(len(g.get_failed_tasks()) for g in self.task_groups.values())
            
            return {
                "total_groups": total_groups,
                "total_tasks": total_tasks,
                "pending_tasks": pending_tasks,
                "running_tasks": running_tasks,
                "completed_tasks": completed_tasks,
                "failed_tasks": failed_tasks,
                "locked_files": len(self.pipeline_locks),
                "average_progress": sum(g.get_progress() for g in self.task_groups.values()) / total_groups if total_groups > 0 else 0.0
            }
    
    async def get_group_details(self, file_id: str) -> Optional[Dict[str, Any]]:
        """获取任务组详细信息"""
        async with self._lock:
            group = self.task_groups.get(file_id)
            if not group:
                return None
            
            lock_status = self.get_lock_status(file_id)
            
            return {
                "group": group.to_dict(),
                "lock_status": lock_status,
                "tasks": [t.to_dict() for t in group.get_all_tasks()]
            }
