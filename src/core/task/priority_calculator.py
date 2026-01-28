"""
优先级计算器
专门负责优先级计算，引入等待时间补偿和流水线连续性奖励
"""

import time
from datetime import datetime
from typing import Optional
import logging

from .task import Task


logger = logging.getLogger(__name__)


class PriorityCalculator:
    """优先级计算器"""
    
    def __init__(self):
        # 基础优先级映射
        self.base_priority_map = {
            # 高优先级：核心处理任务
            'file_preprocessing': 10,
            'image_preprocess': 9,
            'video_preprocess': 9,
            'audio_preprocess': 9,
            'file_embed_image': 8,
            'file_embed_video': 8,
            'file_embed_audio': 8,
            
            # 中优先级：常规任务
            'file_scan': 7,
            'video_slice': 6,
            'audio_segment': 6,
            
            # 低优先级：辅助任务
            'thumbnail_generate': 5,
            'preview_generate': 4,
            'search': 3,
            'search_multimodal': 3,
            'rank_results': 2,
            'filter_results': 2,
            
            # 默认优先级
            'default': 5
        }
        
        # 等待时间补偿参数
        self.wait_compensation_interval = 300  # 5分钟（秒）
        self.max_wait_compensation = 100  # 最大等待补偿值
        self.wait_compensation_step = 1   # 每个间隔增加的补偿值
    
    def calculate_priority(self, task: Task, wait_time_compensation: bool = True, 
                          pipeline_continuity: bool = True) -> int:
        """
        计算任务优先级
        
        Args:
            task: 任务对象
            wait_time_compensation: 是否启用等待时间补偿
            pipeline_continuity: 是否启用流水线连续性奖励
            
        Returns:
            计算后的优先级（数值越小优先级越高）
        """
        try:
            # 基础优先级
            base_priority = self.base_priority_map.get(task.task_type, self.base_priority_map['default'])
            
            # 文件级优先级（如果存在）
            file_priority = getattr(task, 'file_priority', 0) or 0
            
            # 等待时间补偿
            wait_compensation = 0
            if wait_time_compensation and task.created_at:
                if isinstance(task.created_at, datetime):
                    wait_time = (datetime.now() - task.created_at).total_seconds()
                else:
                    wait_time = time.time() - task.created_at
                
                # 计算等待时间补偿（每5分钟增加1点，最多增加100点）
                wait_intervals = int(wait_time / self.wait_compensation_interval)
                wait_compensation = min(self.max_wait_compensation, 
                                      wait_intervals * self.wait_compensation_step)
            
            # 流水线连续性奖励（如果属于同一文件的流水线任务）
            continuity_bonus = 0
            if pipeline_continuity and task.file_id:
                continuity_bonus = self._calculate_continuity_bonus(task)
            
            # 计算最终优先级
            # 使用公式：base_priority * 1000 + (文件优先级 * 100) + (等待补偿) + (连续性奖励)
            final_priority = (
                base_priority * 1000 +
                file_priority * 100 +
                (999 - wait_compensation) +  # 补偿值越高优先级越高（数值越小）
                continuity_bonus
            )
            
            # 确保优先级不为负
            final_priority = max(0, final_priority)
            
            logger.debug(f"任务 {task.id} 优先级计算: 基础={base_priority}, "
                        f"文件优先级={file_priority}, 等待补偿={wait_compensation}, "
                        f"连续性奖励={continuity_bonus}, 最终={final_priority}")
            
            return final_priority
            
        except Exception as e:
            logger.error(f"计算任务 {task.id} 优先级时发生错误: {e}")
            # 返回默认优先级
            return self.base_priority_map['default'] * 1000
    
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
            'file_preprocessing', 
            'image_preprocess',
            'video_preprocess', 
            'audio_preprocess',
            'file_embed_image', 
            'file_embed_video', 
            'file_embed_audio'
        ]
        return task_type in pipeline_tasks
    
    def _is_continuation_task(self, task: Task) -> bool:
        """
        检查是否为连续任务（同一文件的流水线任务）
        
        Args:
            task: 任务对象
            
        Returns:
            是否为连续任务
        """
        # 这里需要访问任务管理系统来检查同一文件的其他任务状态
        # 由于这是一个独立的组件，需要通过参数传入相关信息
        # 在实际实现中，这里可能需要与中央任务管理器集成
        return True  # 简化实现，实际应用中需要更复杂的逻辑
    
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
        return self.base_priority_map.get(task_type, self.base_priority_map['default'])
    
    def get_priority_details(self, task: Task) -> dict:
        """
        获取优先级计算详情
        
        Args:
            task: 任务对象
            
        Returns:
            优先级计算详情
        """
        base_priority = self.base_priority_map.get(task.task_type, self.base_priority_map['default'])
        file_priority = getattr(task, 'file_priority', 0) or 0
        
        wait_compensation = 0
        if task.created_at:
            if isinstance(task.created_at, datetime):
                wait_time = (datetime.now() - task.created_at).total_seconds()
            else:
                wait_time = time.time() - task.created_at
            wait_intervals = int(wait_time / self.wait_compensation_interval)
            wait_compensation = min(self.max_wait_compensation, 
                                  wait_intervals * self.wait_compensation_step)
        
        continuity_bonus = self._calculate_continuity_bonus(task)
        
        return {
            'task_type': task.task_type,
            'base_priority': base_priority,
            'file_priority': file_priority,
            'wait_compensation': wait_compensation,
            'continuity_bonus': continuity_bonus,
            'calculated_priority': self.calculate_priority(task)
        }