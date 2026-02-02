"""
流水线锁管理器
确保同一文件的核心任务连续执行
"""

import threading
import time
from typing import Dict, Optional, List
from datetime import datetime
import logging

from .task import Task


logger = logging.getLogger(__name__)


class PipelineLockManager:
    """流水线锁管理器 - 确保同一文件的核心任务连续执行"""

    def __init__(self):
        # 流水线锁：file_id -> lock_info
        self.pipeline_locks: Dict[str, Dict[str, any]] = {}

        # 文件任务队列：file_id -> [task_ids]，存储等待流水线锁的任务
        self.waiting_queues: Dict[str, List[str]] = {}

        # 线程锁
        self.lock = threading.Lock()

        # 锁超时时间（秒）
        self.lock_timeout = 300  # 5分钟

    def acquire_pipeline_lock(self, task: Task) -> bool:
        """
        获取流水线锁

        Args:
            task: 任务对象

        Returns:
            是否成功获取锁
        """
        with self.lock:
            if not task.file_id:
                # 没有文件ID的任务不需要流水线锁
                return True

            if not self._is_pipeline_task(task.task_type):
                # 非流水线任务不需要锁
                return True

            # 检查是否已有流水线锁
            if task.file_id in self.pipeline_locks:
                current_lock = self.pipeline_locks[task.file_id]

                # 检查锁是否已过期
                if self._is_lock_expired(current_lock):
                    logger.warning(f"流水线锁已过期，释放文件 {task.file_id} 的锁")
                    del self.pipeline_locks[task.file_id]
                else:
                    # 有其他任务持有流水线锁，将当前任务加入等待队列
                    if task.file_id not in self.waiting_queues:
                        self.waiting_queues[task.file_id] = []

                    if task.id not in self.waiting_queues[task.file_id]:
                        self.waiting_queues[task.file_id].append(task.id)
                        logger.debug(
                            f"任务 {task.id} 加入文件 {task.file_id} 的流水线等待队列"
                        )

                    return False  # 无法获取锁

            # 创建新的流水线锁
            self.pipeline_locks[task.file_id] = {
                "holder": task.id,
                "holder_type": task.task_type,
                "start_time": time.time(),
                "acquired_at": datetime.now(),
            }

            logger.debug(f"任务 {task.id} 获取文件 {task.file_id} 的流水线锁")
            return True

    def release_pipeline_lock(self, task: Task) -> None:
        """
        释放流水线锁

        Args:
            task: 任务对象
        """
        with self.lock:
            if not task.file_id or task.file_id not in self.pipeline_locks:
                return

            current_lock = self.pipeline_locks[task.file_id]

            # 只有锁的持有者才能释放锁
            if current_lock["holder"] == task.id:
                # 检查是否还有同文件的流水线任务在等待队列中
                has_waiting_pipeline_tasks = self._has_pipeline_tasks_in_queue(
                    task.file_id
                )

                if has_waiting_pipeline_tasks:
                    # 有等待的流水线任务，不立即释放锁，让等待的任务获取
                    logger.debug(f"文件 {task.file_id} 有等待的流水线任务，保留锁")
                else:
                    # 没有等待的流水线任务，释放锁
                    del self.pipeline_locks[task.file_id]
                    logger.debug(f"任务 {task.id} 释放文件 {task.file_id} 的流水线锁")

                # 从等待队列中移除已完成的任务
                if task.file_id in self.waiting_queues:
                    if task.id in self.waiting_queues[task.file_id]:
                        self.waiting_queues[task.file_id].remove(task.id)

    def _is_pipeline_task(self, task_type: str) -> bool:
        """检查任务类型是否属于流水线任务"""
        pipeline_tasks = [
            "file_preprocessing",
            "image_preprocess",
            "video_preprocess",
            "audio_preprocess",
            "file_embed_image",
            "file_embed_video",
            "file_embed_audio",
            "video_slice",
            "audio_segment",
        ]
        return task_type in pipeline_tasks

    def _has_pipeline_tasks_in_queue(self, file_id: str) -> bool:
        """检查指定文件是否有流水线任务在等待队列中"""
        if file_id not in self.waiting_queues:
            return False

        waiting_tasks = self.waiting_queues[file_id]
        for task_id in waiting_tasks:
            task = self._get_task_by_id(task_id)
            if task and self._is_pipeline_task(task.task_type):
                return True

        return False

    def _is_lock_expired(self, lock_info: Dict[str, any]) -> bool:
        """检查锁是否已过期"""
        elapsed_time = time.time() - lock_info["start_time"]
        return elapsed_time > self.lock_timeout

    def _get_task_by_id(self, task_id: str) -> Optional[Task]:
        """
        根据ID获取任务（这个方法需要与任务监控器集成）
        在实际实现中，这应该通过依赖注入获取任务监控器实例
        """
        # 这里只是一个简化实现，实际应用中需要与任务监控器集成
        return None

    def get_lock_info(self, file_id: str) -> Optional[Dict[str, any]]:
        """
        获取锁信息

        Args:
            file_id: 文件ID

        Returns:
            锁信息或None
        """
        with self.lock:
            return self.pipeline_locks.get(file_id)

    def is_file_locked(self, file_id: str) -> bool:
        """
        检查文件是否被流水线锁锁定

        Args:
            file_id: 文件ID

        Returns:
            是否被锁定
        """
        with self.lock:
            return file_id in self.pipeline_locks

    def get_waiting_tasks_count(self, file_id: str) -> int:
        """
        获取等待流水线锁的任务数量

        Args:
            file_id: 文件ID

        Returns:
            等待任务数量
        """
        with self.lock:
            if file_id in self.waiting_queues:
                return len(self.waiting_queues[file_id])
            return 0

    def get_all_locked_files(self) -> List[str]:
        """
        获取所有被锁定的文件ID

        Returns:
            文件ID列表
        """
        with self.lock:
            return list(self.pipeline_locks.keys())

    def force_release_lock(self, file_id: str) -> bool:
        """
        强制释放锁（通常只在异常情况下使用）

        Args:
            file_id: 文件ID

        Returns:
            是否成功
        """
        with self.lock:
            if file_id in self.pipeline_locks:
                del self.pipeline_locks[file_id]
                # 清空等待队列
                if file_id in self.waiting_queues:
                    self.waiting_queues[file_id].clear()
                logger.warning(f"强制释放文件 {file_id} 的流水线锁")
                return True
            return False

    def cleanup_expired_locks(self) -> int:
        """
        清理过期的锁

        Returns:
            清理的锁数量
        """
        with self.lock:
            expired_locks = []
            for file_id, lock_info in self.pipeline_locks.items():
                if self._is_lock_expired(lock_info):
                    expired_locks.append(file_id)

            for file_id in expired_locks:
                del self.pipeline_locks[file_id]
                if file_id in self.waiting_queues:
                    self.waiting_queues[file_id].clear()

            if expired_locks:
                logger.warning(
                    f"清理了 {len(expired_locks)} 个过期的流水线锁: {expired_locks}"
                )

            return len(expired_locks)

    def get_statistics(self) -> Dict[str, any]:
        """
        获取统计信息

        Returns:
            统计信息字典
        """
        with self.lock:
            return {
                "active_locks": len(self.pipeline_locks),
                "locked_files": list(self.pipeline_locks.keys()),
                "waiting_queues_count": len(self.waiting_queues),
                "waiting_tasks_total": sum(
                    len(q) for q in self.waiting_queues.values()
                ),
            }
