"""
优先级计算器
专门负责优先级计算，引入等待时间补偿和流水线连续性奖励
"""

import time
from datetime import datetime
from typing import Optional, Dict
import logging

from .task import Task


logger = logging.getLogger(__name__)


class PriorityCalculator:
    """优先级计算器"""

    def __init__(self):
        # 基础优先级映射（根据设计文档和IFLOW.md）
        self.base_priority_map = {
            "file_scan": 3,
            "image_preprocess": 1,
            "video_preprocess": 1,
            "audio_preprocess": 1,
            "file_embed_image": 1,
            "file_embed_video": 3,
            "file_embed_audio": 4,
            "file_embed_text": 1,
            "video_slice": 3,
            "thumbnail_generate": 2,
            "preview_generate": 2,
            "default": 5,
        }

        # 类型优先级映射（根据设计文档和IFLOW.md）
        self.type_priority_map = {
            "file_scan": 3,
            "image_preprocess": 4,
            "video_preprocess": 4,
            "audio_preprocess": 4,
            "file_embed_image": 1,
            "file_embed_video": 2,
            "file_embed_audio": 3,
            "file_embed_text": 1,
            "video_slice": 2,
            "thumbnail_generate": 5,
            "preview_generate": 6,
            "default": 5,
        }

        # 等待时间补偿参数（根据设计文档）
        self.wait_compensation_interval = 60  # 1分钟（秒）
        self.max_wait_compensation = 999  # 最大等待补偿值
        self.wait_compensation_step = 1  # 每个间隔增加的补偿值

    def calculate_priority(
        self, task: Task, file_info: Dict = None, file_priority: int = 5, central_task_manager=None
    ) -> int:
        """
        计算任务优先级（根据设计文档公式）

        Args:
            task: 任务对象
            file_info: 文件信息字典
            file_priority: 文件级优先级（1-10）
            central_task_manager: 中央任务管理器实例（用于检查连续性）

        Returns:
            计算后的优先级（数值越小优先级越高）

        公式：final_priority = base_priority * 1000 + file_priority * 100 + type_priority * 10 + wait_compensation
        """
        try:
            # 基础优先级（0-9）
            base_priority = self.base_priority_map.get(
                task.task_type, self.base_priority_map["default"]
            )

            # 类型优先级（0-9）
            type_priority = self.type_priority_map.get(
                task.task_type, self.type_priority_map["default"]
            )

            # 等待时间补偿（0-999）
            wait_compensation = 0
            if task.created_at:
                if isinstance(task.created_at, datetime):
                    # 如果是datetime对象，计算时间差
                    wait_time = (datetime.now() - task.created_at).total_seconds()
                elif isinstance(task.created_at, (int, float)):
                    # 如果是时间戳（float/int），转换为datetime再计算
                    wait_time = time.time() - task.created_at
                else:
                    # 其他情况，使用当前时间
                    wait_time = 0

                # 计算等待时间补偿（每1分钟增加1点，最多增加999点）
                wait_intervals = int(wait_time / self.wait_compensation_interval)
                wait_compensation = min(
                    self.max_wait_compensation,
                    wait_intervals * self.wait_compensation_step,
                )

            # 计算流水线连续性奖励
            continuity_bonus = self._calculate_continuity_bonus(task)

            # 如果提供了中央任务管理器，使用更精确的连续性判断
            if central_task_manager:
                if self._is_continuation_task(task, central_task_manager):
                    continuity_bonus = -20  # 负值表示提高优先级

            # 计算最终优先级（根据设计文档公式）
            final_priority = (
                base_priority * 1000  # 基础优先级权重：1000
                + file_priority * 100  # 文件级优先级权重：100
                + type_priority * 10  # 类型优先级权重：10
                + wait_compensation  # 等待时间补偿权重：1
                + continuity_bonus  # 流水线连续性奖励
            )

            logger.debug(
                f"任务 {task.id} 优先级计算: 基础={base_priority}, "
                f"文件优先级={file_priority}, 类型优先级={type_priority}, "
                f"等待补偿={wait_compensation}, 连续性奖励={continuity_bonus}, 最终={final_priority}"
            )

            return final_priority

        except Exception as e:
            logger.error(f"计算任务 {task.id} 优先级时发生错误: {e}")
            # 返回默认优先级
            return self.base_priority_map["default"] * 1000

    def _calculate_continuity_bonus(self, task: Task) -> int:
        """
        计算流水线连续性奖励

        Args:
            task: 任务对象

        Returns:
            连续性奖励值（负值表示提高优先级）
        """
        # 检查是否为核心流水线任务
        if self._is_pipeline_task(task.task_type):
            # 检查同一文件是否还有其他流水线任务在等待
            if self._is_continuation_task(task):
                # 如果是连续的流水线任务，给予优先级提升奖励
                return -20  # 负值表示提高优先级
        return 0

    def _is_pipeline_task(self, task_type: str) -> bool:
        """检查是否为核心流水线任务"""
        pipeline_tasks = [
            "file_preprocessing",
            "image_preprocess",
            "video_preprocess",
            "audio_preprocess",
            "file_embed_image",
            "file_embed_video",
            "file_embed_audio",
            "file_embed_text",  # 添加文本嵌入任务
        ]
        return task_type in pipeline_tasks

    def _is_continuation_task(self, task: Task, central_task_manager=None) -> bool:
        """
        检查是否为连续任务（同一文件的流水线任务）

        Args:
            task: 任务对象
            central_task_manager: 中央任务管理器实例（可选）

        Returns:
            是否为连续任务
        """
        if not task.file_id or not central_task_manager:
            return False

        # 检查同一文件是否还有其他流水线任务在等待
        # 通过中央任务管理器检查任务组状态
        try:
            # 如果提供了中央任务管理器，通过它检查任务组
            group = central_task_manager.get_task_group(task.file_id)
            if group:
                # 检查是否有已完成的流水线任务
                completed_tasks = group.get_completed_tasks()
                pending_tasks = group.get_pending_tasks()
                
                # 如果当前任务是流水线任务，且在同一文件中还有其他已处理的任务
                # 则认为它是连续任务，应获得优先级提升
                if self._is_pipeline_task(task.task_type):
                    # 检查是否有已处理过的流水线任务
                    for completed_task in completed_tasks:
                        if self._is_pipeline_task(completed_task.task_type):
                            return True
        except Exception as e:
            logger.warning(f"检查连续任务时出错: {e}")
        
        return False

    def update_base_priority(self, task_type: str, priority: int) -> None:
        """
        更新基础优先级

        Args:
            task_type: 任务类型
            priority: 新优先级
        """
        self.base_priority_map[task_type] = priority
        logger.info(f"更新任务类型 {task_type} 的基础优先级为 {priority}")

    def get_base_priority(self, task_type: str) -> int:
        """
        获取基础优先级

        Args:
            task_type: 任务类型

        Returns:
            基础优先级
        """
        return self.base_priority_map.get(task_type, self.base_priority_map["default"])

    def get_priority_details(self, task: Task) -> dict:
        """
        获取优先级计算详情

        Args:
            task: 任务对象

        Returns:
            优先级计算详情
        """
        base_priority = self.base_priority_map.get(
            task.task_type, self.base_priority_map["default"]
        )
        file_priority = getattr(task, "file_priority", 0) or 0

        wait_compensation = 0
        if task.created_at:
            if isinstance(task.created_at, datetime):
                wait_time = (datetime.now() - task.created_at).total_seconds()
            else:
                wait_time = time.time() - task.created_at
            wait_intervals = int(wait_time / self.wait_compensation_interval)
            wait_compensation = min(
                self.max_wait_compensation, wait_intervals * self.wait_compensation_step
            )

        continuity_bonus = self._calculate_continuity_bonus(task)

        return {
            "task_type": task.task_type,
            "base_priority": base_priority,
            "file_priority": file_priority,
            "wait_compensation": wait_compensation,
            "continuity_bonus": continuity_bonus,
            "calculated_priority": self.calculate_priority(task),
        }
