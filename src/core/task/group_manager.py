"""
优化后的任务组管理器
专门负责任务组管理，确保任务组连续性
"""

import threading
from typing import Dict, List, Optional
from collections import defaultdict
import logging

from .task import Task


logger = logging.getLogger(__name__)


class OptimizedGroupManager:
    """优化后的任务组管理器"""

    def __init__(self):
        # 任务组映射：file_id -> [task_ids]
        self.task_groups: Dict[str, List[str]] = defaultdict(list)

        # 任务到组的映射：task_id -> file_id
        self.task_to_group: Dict[str, str] = {}

        # 组状态映射：file_id -> status
        self.group_status: Dict[str, str] = {}

        # 组统计信息
        self.group_stats: Dict[str, Dict[str, int]] = defaultdict(
            lambda: {
                "total": 0,
                "pending": 0,
                "running": 0,
                "completed": 0,
                "failed": 0,
            }
        )

        # 线程锁
        self.lock = threading.Lock()

    def add_task_to_group(self, task: Task) -> bool:
        """
        将任务添加到组

        Args:
            task: 任务对象

        Returns:
            是否成功
        """
        if not task.file_id:
            logger.warning(f"任务 {task.id} 没有文件ID，无法添加到组")
            return False

        with self.lock:
            # 添加到任务组
            if task.id not in self.task_groups[task.file_id]:
                self.task_groups[task.file_id].append(task.id)

            # 建立任务到组的映射
            self.task_to_group[task.id] = task.file_id

            # 更新统计
            self.group_stats[task.file_id]["total"] += 1
            self.group_stats[task.file_id]["pending"] += 1

            logger.debug(f"任务 {task.id} 添加到组 {task.file_id}")
            return True

    def remove_task_from_group(self, task_id: str) -> bool:
        """
        从组中移除任务

        Args:
            task_id: 任务ID

        Returns:
            是否成功
        """
        with self.lock:
            if task_id not in self.task_to_group:
                return False

            file_id = self.task_to_group[task_id]

            # 从任务组中移除
            if task_id in self.task_groups[file_id]:
                self.task_groups[file_id].remove(task_id)

            # 从映射中移除
            del self.task_to_group[task_id]

            # 更新统计
            if file_id in self.group_stats:
                stats = self.group_stats[file_id]
                stats["total"] = max(0, stats["total"] - 1)
                stats["pending"] = max(0, stats["pending"] - 1)

            logger.debug(f"任务 {task_id} 从组 {file_id} 中移除")
            return True

    def get_tasks_in_group(self, file_id: str) -> List[str]:
        """
        获取组中的所有任务ID

        Args:
            file_id: 文件ID

        Returns:
            任务ID列表
        """
        with self.lock:
            return self.task_groups.get(file_id, []).copy()

    def get_group_status(self, file_id: str) -> str:
        """
        获取组状态

        Args:
            file_id: 文件ID

        Returns:
            组状态
        """
        with self.lock:
            return self.group_status.get(file_id, "unknown")

    def update_task_status_in_group(
        self, task_id: str, old_status: str, new_status: str
    ) -> None:
        """
        更新组中任务的状态

        Args:
            task_id: 任务ID
            old_status: 旧状态
            new_status: 新状态
        """
        with self.lock:
            if task_id not in self.task_to_group:
                return

            file_id = self.task_to_group[task_id]
            stats = self.group_stats[file_id]

            # 更新旧状态统计
            if old_status in stats:
                stats[old_status] = max(0, stats[old_status] - 1)

            # 更新新状态统计
            if new_status in stats:
                stats[new_status] += 1
            elif new_status == "cancelled":
                stats["failed"] += 1  # 取消的任务也算失败

            # 更新组状态
            self._update_group_status(file_id)

    def _update_group_status(self, file_id: str) -> None:
        """更新组的整体状态"""
        stats = self.group_stats[file_id]

        if stats["total"] == 0:
            self.group_status[file_id] = "empty"
        elif stats["failed"] > 0:
            self.group_status[file_id] = "failed"
        elif stats["completed"] == stats["total"]:
            self.group_status[file_id] = "completed"
        elif stats["running"] > 0:
            self.group_status[file_id] = "running"
        elif stats["pending"] > 0:
            self.group_status[file_id] = "pending"
        else:
            self.group_status[file_id] = "processing"

    def get_group_statistics(self, file_id: str) -> Optional[Dict[str, int]]:
        """
        获取组统计信息

        Args:
            file_id: 文件ID

        Returns:
            统计信息或None
        """
        with self.lock:
            if file_id not in self.group_stats:
                return None
            return self.group_stats[file_id].copy()

    def get_all_groups(self) -> List[str]:
        """
        获取所有组ID

        Returns:
            组ID列表
        """
        with self.lock:
            return list(self.task_groups.keys())

    def is_group_complete(self, file_id: str) -> bool:
        """
        检查组是否完成

        Args:
            file_id: 文件ID

        Returns:
            是否完成
        """
        with self.lock:
            stats = self.group_stats.get(file_id, {})
            return (
                stats.get("completed", 0) == stats.get("total", 0)
                and stats.get("total", 0) > 0
            )

    def is_group_running(self, file_id: str) -> bool:
        """
        检查组是否正在运行

        Args:
            file_id: 文件ID

        Returns:
            是否正在运行
        """
        with self.lock:
            return self.group_status.get(file_id, "unknown") == "running"

    def get_running_groups(self) -> List[str]:
        """
        获取正在运行的组

        Returns:
            正在运行的组列表
        """
        with self.lock:
            return [
                gid for gid, status in self.group_status.items() if status == "running"
            ]

    def get_pipeline_tasks_in_group(self, file_id: str) -> List[str]:
        """
        获取组中的流水线任务

        Args:
            file_id: 文件ID

        Returns:
            流水线任务ID列表
        """
        with self.lock:
            all_task_ids = self.task_groups.get(file_id, [])
            # 这里需要访问任务对象来确定是否为流水线任务
            # 在实际实现中，可能需要与任务监控器集成
            return all_task_ids  # 简化实现

    def clear_group(self, file_id: str) -> None:
        """
        清空组

        Args:
            file_id: 文件ID
        """
        with self.lock:
            if file_id in self.task_groups:
                # 移除所有任务的组映射
                for task_id in self.task_groups[file_id]:
                    if task_id in self.task_to_group:
                        del self.task_to_group[task_id]

                # 清空组和统计
                del self.task_groups[file_id]
                if file_id in self.group_stats:
                    del self.group_stats[file_id]
                if file_id in self.group_status:
                    del self.group_status[file_id]

                logger.info(f"组 {file_id} 已清空")

    def get_groups_with_status(self, status: str) -> List[str]:
        """
        获取指定状态的组

        Args:
            status: 状态

        Returns:
            组ID列表
        """
        with self.lock:
            return [
                gid
                for gid, group_status in self.group_status.items()
                if group_status == status
            ]
