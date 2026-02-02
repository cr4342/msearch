"""
优化后的任务监控器
专门负责任务状态监控，避免与TaskManager的循环依赖
"""

import threading
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from .task import Task

logger = logging.getLogger(__name__)


class OptimizedTaskMonitor:
    """
    优化后的任务监控器

    职责：
    - 任务状态跟踪（记录任务的生命周期状态变化）
    - 任务进度监控（监控任务执行进度）
    - 任务历史记录（维护任务执行历史）
    - 任务查询接口（提供任务信息查询功能）
    """

    def __init__(self):
        # 任务存储
        self.tasks: Dict[str, Task] = {}

        # 线程锁
        self.lock = threading.Lock()

        # 任务统计
        self.stats = {
            "total_created": 0,
            "total_completed": 0,
            "total_failed": 0,
            "total_cancelled": 0,
            "running_count": 0,
        }

        # 事件回调
        self.event_callbacks: Dict[str, List[callable]] = {
            "task_created": [],
            "task_started": [],
            "task_completed": [],
            "task_failed": [],
            "task_cancelled": [],
        }

        logger.info("优化后的任务监控器初始化完成")

    def add_task(self, task: Task) -> None:
        """
        添加任务到监控器

        Args:
            task: 任务对象
        """
        with self.lock:
            self.tasks[task.id] = task
            self.stats["total_created"] += 1

            # 触发任务创建事件
            self._trigger_event("task_created", task)

    def get_task(self, task_id: str) -> Optional[Task]:
        """
        获取任务

        Args:
            task_id: 任务ID

        Returns:
            任务对象或None
        """
        with self.lock:
            return self.tasks.get(task_id)

    def update_task(self, task: Task) -> bool:
        """
        更新任务

        Args:
            task: 任务对象

        Returns:
            是否成功
        """
        with self.lock:
            if task.id in self.tasks:
                # 更新统计
                old_status = self.tasks[task.id].status
                new_status = task.status

                # 状态变更统计
                if old_status != new_status:
                    if new_status == "completed":
                        self.stats["total_completed"] += 1
                    elif new_status == "failed":
                        self.stats["total_failed"] += 1
                    elif new_status == "cancelled":
                        self.stats["total_cancelled"] += 1

                    # 触发相应事件
                    if new_status == "running":
                        self.stats["running_count"] += 1
                        self._trigger_event("task_started", task)
                    elif old_status == "running" and new_status in [
                        "completed",
                        "failed",
                        "cancelled",
                    ]:
                        self.stats["running_count"] -= 1

                    if new_status == "completed":
                        self._trigger_event("task_completed", task)
                    elif new_status == "failed":
                        self._trigger_event("task_failed", task)
                    elif new_status == "cancelled":
                        self._trigger_event("task_cancelled", task)

                # 更新任务
                self.tasks[task.id] = task
                return True
            return False

    def get_all_tasks(
        self, status: str = None, task_type: str = None
    ) -> Dict[str, Task]:
        """
        获取所有任务

        Args:
            status: 状态过滤
            task_type: 任务类型过滤

        Returns:
            任务字典
        """
        with self.lock:
            result = {}
            for task_id, task in self.tasks.items():
                # 状态过滤
                if status and task.status != status:
                    continue
                # 类型过滤
                if task_type and task.task_type != task_type:
                    continue
                result[task_id] = task
            return result

    def get_tasks_by_status(self, status: str) -> List[Task]:
        """
        按状态获取任务

        Args:
            status: 状态

        Returns:
            任务列表
        """
        with self.lock:
            return [task for task in self.tasks.values() if task.status == status]

    def get_running_tasks(self) -> List[Task]:
        """
        获取运行中的任务

        Returns:
            运行中的任务列表
        """
        return self.get_tasks_by_status("running")

    def get_pending_tasks(self) -> List[Task]:
        """
        获取待处理的任务

        Returns:
            待处理的任务列表
        """
        return self.get_tasks_by_status("pending")

    def get_completed_tasks(self) -> List[Task]:
        """
        获取已完成的任务

        Returns:
            已完成的任务列表
        """
        return self.get_tasks_by_status("completed")

    def get_failed_tasks(self) -> List[Task]:
        """
        获取失败的任务

        Returns:
            失败的任务列表
        """
        return self.get_tasks_by_status("failed")

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息

        Returns:
            统计信息字典
        """
        with self.lock:
            stats = self.stats.copy()
            stats.update(
                {
                    "total_tasks": len(self.tasks),
                    "pending_count": len(self.get_pending_tasks()),
                    "running_count": len(self.get_running_tasks()),
                    "completed_count": len(self.get_completed_tasks()),
                    "failed_count": len(self.get_failed_tasks()),
                }
            )
            return stats

    def clear_completed_tasks(self) -> int:
        """
        清除已完成的任务

        Returns:
            清除的任务数量
        """
        with self.lock:
            completed_tasks = self.get_completed_tasks()
            removed_count = 0

            for task in completed_tasks:
                if task.id in self.tasks:
                    del self.tasks[task.id]
                    removed_count += 1

            return removed_count

    def clear_failed_tasks(self) -> int:
        """
        清除失败的任务

        Returns:
            清除的任务数量
        """
        with self.lock:
            failed_tasks = self.get_failed_tasks()
            removed_count = 0

            for task in failed_tasks:
                if task.id in self.tasks:
                    del self.tasks[task.id]
                    removed_count += 1

            return removed_count

    def clear_old_tasks(self, hours: int = 24) -> int:
        """
        清除指定时间前的任务

        Args:
            hours: 小时数

        Returns:
            清除的任务数量
        """
        with self.lock:
            cutoff_time = time.time() - (hours * 3600)
            removed_count = 0

            for task_id, task in list(self.tasks.items()):
                # 只清除已完成或失败的任务
                if task.status in ["completed", "failed", "cancelled"]:
                    task_time = getattr(
                        task, "completed_at", getattr(task, "updated_at", None)
                    )
                    if task_time:
                        task_timestamp = (
                            task_time.timestamp()
                            if hasattr(task_time, "timestamp")
                            else task_time
                        )
                        if task_timestamp < cutoff_time:
                            del self.tasks[task_id]
                            removed_count += 1
                    else:
                        # 如果没有时间戳，使用创建时间
                        created_time = getattr(task, "created_at", time.time())
                        if created_time < cutoff_time:
                            del self.tasks[task_id]
                            removed_count += 1

            return removed_count

    def add_event_callback(self, event_type: str, callback: callable) -> None:
        """
        添加事件回调

        Args:
            event_type: 事件类型
            callback: 回调函数
        """
        if event_type in self.event_callbacks:
            self.event_callbacks[event_type].append(callback)
        else:
            logger.warning(f"未知的事件类型: {event_type}")

    def remove_event_callback(self, event_type: str, callback: callable) -> bool:
        """
        移除事件回调

        Args:
            event_type: 事件类型
            callback: 回调函数

        Returns:
            是否成功
        """
        if event_type in self.event_callbacks:
            if callback in self.event_callbacks[event_type]:
                self.event_callbacks[event_type].remove(callback)
                return True
        return False

    def _trigger_event(self, event_type: str, task: Task) -> None:
        """
        触发事件

        Args:
            event_type: 事件类型
            task: 任务对象
        """
        if event_type in self.event_callbacks:
            for callback in self.event_callbacks[event_type]:
                try:
                    callback(task)
                except Exception as e:
                    logger.error(f"事件回调执行失败: {e}")

    def get_task_history(self, task_id: str) -> List[Dict[str, Any]]:
        """
        获取任务历史（如果实现的话）

        Args:
            task_id: 任务ID

        Returns:
            任务历史列表
        """
        # 简化实现：返回当前任务状态
        task = self.get_task(task_id)
        if task:
            return [task.to_dict()]  # 假设有to_dict方法
        return []

    def search_tasks(self, query: str) -> List[Task]:
        """
        搜索任务

        Args:
            query: 查询字符串

        Returns:
            匹配的任务列表
        """
        with self.lock:
            results = []

            for task in self.tasks.values():
                # 搜索任务ID、类型、错误信息等
                if (
                    query.lower() in task.id.lower()
                    or query.lower() in task.task_type.lower()
                    or (task.error and query.lower() in task.error.lower())
                ):
                    results.append(task)

            return results

    def get_tasks_by_file(self, file_id: str) -> List[Task]:
        """
        按文件ID获取任务

        Args:
            file_id: 文件ID

        Returns:
            任务列表
        """
        with self.lock:
            return [task for task in self.tasks.values() if task.file_id == file_id]

    def get_task_count_by_status(self) -> Dict[str, int]:
        """
        获取各状态的任务数量

        Returns:
            状态任务数量字典
        """
        with self.lock:
            counts = {}
            for task in self.tasks.values():
                status = task.status
                counts[status] = counts.get(status, 0) + 1
            return counts
