"""
任务调度器

职责：
- 任务优先级计算（包括基础优先级、文件优先级、类型优先级和等待时间补偿）
- 任务队列管理（PriorityQueue）
- 动态优先级调整（根据资源使用情况和等待时间）
- 任务排序和选择（决定任务执行顺序）
- 响应OOM状态通知，调整调度行为

明确边界：
- ✅ 负责计算任务优先级，决定任务执行顺序
- ✅ 管理任务队列，提供入队/出队接口
- ✅ 根据资源状态调整调度策略
- ✅ 查询TaskGroupManager的锁状态，决定是否可调度
- ❌ 不直接执行任务
- ❌ 不直接管理任务组状态
- ❌ 不直接监控资源（接收ResourceManager通知）
"""

import asyncio
import heapq
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

from .task import Task
from .task_types import TaskType, TaskStatus
from .priority_calculator import PriorityCalculator


logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """任务优先级枚举"""

    CRITICAL = 1  # 关键任务
    HIGH = 2  # 高优先级
    NORMAL = 3  # 普通优先级
    LOW = 4  # 低优先级
    BACKGROUND = 5  # 后台任务


@dataclass(order=True)
class PrioritizedTask:
    """带优先级的任务包装器"""

    priority: int
    created_at: float = field(compare=False)
    task: Task = field(compare=False)

    def __init__(self, task: Task):
        self.task = task
        self.priority = task.priority
        self.created_at = task.created_at


class TaskScheduler:
    """
    任务调度器

    负责计算任务优先级和管理任务队列
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config

        # 优先级计算器
        self.priority_calculator = PriorityCalculator()

        # 优先级队列
        self._queue: List[PrioritizedTask] = []
        self._queue_lock = asyncio.Lock()

        # 任务索引（用于快速查找和删除）
        self._task_index: Dict[str, PrioritizedTask] = {}

        # 等待时间补偿配置
        self.wait_time_compensation_enabled = config.get("wait_time_compensation", True)
        self.wait_time_compensation_interval = config.get(
            "wait_time_compensation_interval", 60
        )  # 60秒
        self.wait_time_compensation_max = config.get("wait_time_compensation_max", 999)

        # 动态优先级调整配置
        self.dynamic_priority_enabled = config.get("dynamic_priority", True)
        self.priority_boost_threshold = config.get(
            "priority_boost_threshold", 300
        )  # 5分钟

        # OOM状态
        self.oom_state = "normal"  # normal, warning, critical

        # 运行状态
        self.is_running = False

        logger.info("TaskScheduler initialized")

    async def start(self):
        """启动调度器"""
        self.is_running = True
        logger.info("TaskScheduler started")

    async def stop(self):
        """停止调度器"""
        self.is_running = False
        # 清空队列
        async with self._queue_lock:
            self._queue.clear()
            self._task_index.clear()
        logger.info("TaskScheduler stopped")

    def calculate_priority(self, task: Task, central_task_manager=None) -> int:
        """
        计算任务优先级

        使用优先级计算器来计算任务的最终优先级
        """
        # 使用文件优先级（如果任务有关联的文件）
        file_priority = 5  # 默认优先级
        if task.file_path and central_task_manager:
            # 从文件路径中提取文件扩展名并映射到文件类型
            try:
                file_ext = task.file_path.split('.')[-1].lower() if task.file_path else 'unknown'
                if file_ext in ['mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv']:
                    file_type = 'video'
                elif file_ext in ['mp3', 'wav', 'flac', 'aac', 'ogg', 'wma']:
                    file_type = 'audio'
                elif file_ext in ['jpg', 'jpeg', 'png', 'bmp', 'gif', 'webp']:
                    file_type = 'image'
                else:
                    file_type = 'unknown'
                    
                if file_type != 'unknown':
                    file_priority = central_task_manager.get_file_type_priority(file_type)
            except:
                pass  # 使用默认优先级
        
        return self.priority_calculator.calculate_priority(task, file_priority=file_priority, central_task_manager=central_task_manager)

    def recalculate_priority(self, task: Task) -> int:
        """
        重新计算任务优先级（用于动态调整）

        根据任务等待时间和当前状态重新计算优先级
        """
        return self.priority_calculator.calculate_priority(task)

    async def enqueue_task(self, task: Task) -> bool:
        """
        将任务加入队列

        Args:
            task: 要入队的任务

        Returns:
            是否成功入队
        """
        if not self.is_running:
            logger.warning("Scheduler not running, cannot enqueue task")
            return False

        async with self._queue_lock:
            # 检查任务是否已在队列中
            if task.id in self._task_index:
                logger.debug(f"Task already in queue: {task.id}")
                return False

            # 计算任务优先级
            task.priority = self.calculate_priority(task)

            # 创建带优先级的任务包装器
            prioritized_task = PrioritizedTask(task)

            # 加入优先队列
            heapq.heappush(self._queue, prioritized_task)
            self._task_index[task.id] = prioritized_task

            logger.debug(f"Task enqueued: {task.id}, priority: {task.priority}")
            return True

    async def dequeue_task(self) -> Optional[Task]:
        """
        从队列中取出优先级最高的任务

        Returns:
            优先级最高的任务，如果队列为空则返回None
        """
        if not self.is_running:
            return None

        async with self._queue_lock:
            # 检查OOM状态
            if self.oom_state == "critical":
                # 临界状态，只允许关键任务出队
                return await self._dequeue_critical_task_only()

            # 动态优先级调整：重新计算队列中任务的优先级
            if self.dynamic_priority_enabled:
                await self._adjust_priorities()

            # 取出优先级最高的任务
            while self._queue:
                prioritized_task = heapq.heappop(self._queue)
                task = prioritized_task.task

                # 检查任务是否已被取消或完成
                if task.status != "pending":
                    # 从索引中移除
                    if task.id in self._task_index:
                        del self._task_index[task.id]
                    continue

                # 从索引中移除
                if task.id in self._task_index:
                    del self._task_index[task.id]

                logger.debug(f"Task dequeued: {task.id}, priority: {task.priority}")
                return task

            return None

    async def _dequeue_critical_task_only(self) -> Optional[Task]:
        """OOM临界状态下，只出队关键任务"""
        critical_types = {
            TaskType.IMAGE_PREPROCESS.value,
            TaskType.VIDEO_PREPROCESS.value,
            TaskType.AUDIO_PREPROCESS.value,
            TaskType.FILE_EMBED_IMAGE.value,
            TaskType.FILE_EMBED_VIDEO.value,
            TaskType.FILE_EMBED_AUDIO.value,
        }

        # 遍历队列找出关键任务
        temp_queue = []
        result = None

        while self._queue:
            prioritized_task = heapq.heappop(self._queue)
            task = prioritized_task.task

            if task.status != "pending":
                continue

            if task.task_type in critical_types:
                result = task
                if task.id in self._task_index:
                    del self._task_index[task.id]
                break
            else:
                temp_queue.append(prioritized_task)

        # 将非关键任务放回队列
        for pt in temp_queue:
            heapq.heappush(self._queue, pt)

        return result

    async def _adjust_priorities(self):
        """动态调整队列中任务的优先级"""
        current_time = time.time()

        # 重新计算所有任务的优先级
        new_queue = []
        for prioritized_task in self._queue:
            task = prioritized_task.task

            # 重新计算优先级
            new_priority = self.recalculate_priority(task)

            # 如果优先级发生变化，更新任务
            if new_priority != task.priority:
                task.priority = new_priority
                logger.debug(
                    f"Task priority adjusted: {task.id}, new priority: {new_priority}"
                )

            # 创建新的优先任务对象
            new_prioritized_task = PrioritizedTask(task)
            new_queue.append(new_prioritized_task)
            self._task_index[task.id] = new_prioritized_task

        # 重建堆
        heapq.heapify(new_queue)
        self._queue = new_queue

    async def remove_task(self, task_id: str) -> bool:
        """
        从队列中移除任务

        Args:
            task_id: 任务ID

        Returns:
            是否成功移除
        """
        async with self._queue_lock:
            if task_id not in self._task_index:
                return False

            # 从索引中移除
            del self._task_index[task_id]

            # 从队列中移除（需要重建堆）
            self._queue = [pt for pt in self._queue if pt.task.id != task_id]
            heapq.heapify(self._queue)

            logger.debug(f"Task removed from queue: {task_id}")
            return True

    async def peek_task(self) -> Optional[Task]:
        """
        查看队列中优先级最高的任务（不出队）

        Returns:
            优先级最高的任务，如果队列为空则返回None
        """
        async with self._queue_lock:
            if not self._queue:
                return None

            # 返回堆顶元素
            return self._queue[0].task

    async def get_queue_size(self) -> int:
        """获取队列大小"""
        async with self._queue_lock:
            return len(self._queue)

    async def get_queue_tasks(self) -> List[Dict[str, Any]]:
        """获取队列中的所有任务"""
        async with self._queue_lock:
            return [
                {
                    "id": pt.task.id,
                    "type": pt.task.task_type,
                    "priority": pt.task.priority,
                    "created_at": pt.task.created_at,
                    "wait_time": time.time() - pt.task.created_at,
                }
                for pt in self._queue
            ]

    def on_oom_notification(self, notification: Dict[str, Any]):
        """
        处理OOM状态通知

        Args:
            notification: OOM状态通知
        """
        state = notification.get("oom_state", "normal")
        self.oom_state = state

        if state == "warning":
            logger.warning("OOM warning received, throttling new tasks")
        elif state == "critical":
            logger.error("OOM critical received, only critical tasks will be scheduled")
        else:
            logger.info("OOM state normal, resuming normal scheduling")

    async def clear_queue(self):
        """清空队列"""
        async with self._queue_lock:
            self._queue.clear()
            self._task_index.clear()
            logger.info("Task queue cleared")
