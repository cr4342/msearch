"""
任务管理器
管理文件处理任务的生命周期，提供持久化任务队列
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

from src.common.storage.database_adapter import DatabaseAdapter


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"


class TaskManager:
    """任务管理器"""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        
        self.db_adapter = DatabaseAdapter()
        
        # 配置参数
        self.max_retry_attempts = self.config_manager.get("task_management.max_retries", 5)
        self.retry_delay = self.config_manager.get("task_management.retry_delay", 1)  # 秒
        self.retry_multiplier = self.config_manager.get("task_management.retry_multiplier", 2)  # 重试倍数
        self.task_timeout = self.config_manager.get("task_management.task_timeout", 3600)  # 秒
        
        # 运行状态
        self.is_running = False
        self.retry_task: Optional[asyncio.Task] = None
        
        self.logger.info("任务管理器初始化完成")
    
    async def start(self):
        """启动任务管理器"""
        self.logger.info("启动任务管理器")
        
        self.is_running = True
        
        # 启动重试任务
        self.retry_task = asyncio.create_task(self._retry_loop())
        
        self.logger.info("任务管理器启动完成")
    
    async def stop(self):
        """停止任务管理器"""
        self.logger.info("停止任务管理器")
        
        self.is_running = False
        
        # 停止重试任务
        if self.retry_task:
            self.retry_task.cancel()
            try:
                await self.retry_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("任务管理器已停止")
    
    async def create_task(self, file_id: str, task_type: str, status: str = TaskStatus.PENDING.value) -> str:
        """
        创建新任务
        
        Args:
            file_id: 文件ID
            task_type: 任务类型
            status: 任务状态
            
        Returns:
            任务ID
        """
        try:
            task_data = {
                'file_id': file_id,
                'task_type': task_type,
                'status': status,
                'created_at': datetime.now(),
                'updated_at': datetime.now(),
                'retry_count': 0,
                'max_retry_attempts': self.max_retry_attempts
            }
            
            task_id = await self.db_adapter.insert_task(task_data)
            
            self.logger.info(f"创建任务成功: task_id={task_id}, file_id={file_id}, task_type={task_type}")
            
            return task_id
            
        except Exception as e:
            self.logger.error(f"创建任务失败: file_id={file_id}, 错误: {e}")
            raise
    
    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务信息
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务信息字典，如果不存在返回None
        """
        try:
            task = await self.db_adapter.get_task(task_id)
            return task
        except Exception as e:
            self.logger.error(f"获取任务失败: task_id={task_id}, 错误: {e}")
            return None
    
    async def update_task_status(self, task_id: str, status: str, error_message: str = None) -> bool:
        """
        更新任务状态
        
        Args:
            task_id: 任务ID
            status: 新状态
            error_message: 错误信息
            
        Returns:
            更新是否成功
        """
        try:
            updates = {
                'status': status,
                'updated_at': datetime.now()
            }
            
            if error_message:
                updates['error_message'] = error_message
            
            # 如果任务失败，增加重试次数
            if status == TaskStatus.FAILED.value:
                task = await self.get_task(task_id)
                if task and task['retry_count'] < task['max_retry_attempts']:
                    # 计算指数退避延迟：初始延迟 * (重试倍数 ^ 重试次数)
                    retry_count = task['retry_count']
                    exponential_delay = self.retry_delay * (self.retry_multiplier ** retry_count)
                    
                    updates['status'] = TaskStatus.RETRY.value
                    updates['retry_count'] = retry_count + 1
                    updates['retry_at'] = datetime.now().timestamp() + exponential_delay
            
            success = await self.db_adapter.update_task(task_id, updates)
            
            if success:
                self.logger.debug(f"任务状态更新成功: task_id={task_id}, status={status}")
            else:
                self.logger.warning(f"任务状态更新失败: task_id={task_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"更新任务状态失败: task_id={task_id}, 错误: {e}")
            return False
    
    async def get_pending_tasks(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取待处理任务列表
        
        Args:
            limit: 返回任务数量限制
            
        Returns:
            待处理任务列表
        """
        try:
            tasks = await self.db_adapter.get_tasks_by_status(TaskStatus.PENDING.value, limit)
            return tasks
        except Exception as e:
            self.logger.error(f"获取待处理任务失败: 错误: {e}")
            return []
    
    async def get_processing_tasks(self) -> List[Dict[str, Any]]:
        """
        获取正在处理的任务列表
        
        Returns:
            正在处理的任务列表
        """
        try:
            tasks = await self.db_adapter.get_tasks_by_status(TaskStatus.PROCESSING.value)
            return tasks
        except Exception as e:
            self.logger.error(f"获取正在处理任务失败: 错误: {e}")
            return []
    
    async def get_failed_tasks(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取失败任务列表
        
        Args:
            limit: 返回任务数量限制
            
        Returns:
            失败任务列表
        """
        try:
            tasks = await self.db_adapter.get_tasks_by_status(TaskStatus.FAILED.value, limit)
            return tasks
        except Exception as e:
            self.logger.error(f"获取失败任务失败: 错误: {e}")
            return []
    
    async def retry_failed_task(self, task_id: str) -> bool:
        """
        重试失败任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            重试是否成功
        """
        try:
            task = await self.get_task(task_id)
            
            if not task:
                self.logger.warning(f"任务不存在: task_id={task_id}")
                return False
            
            if task['status'] != TaskStatus.FAILED.value:
                self.logger.warning(f"任务状态不是失败状态: task_id={task_id}, status={task['status']}")
                return False
            
            if task['retry_count'] >= task['max_retry_attempts']:
                self.logger.warning(f"任务重试次数已达上限: task_id={task_id}")
                return False
            
            # 重置任务状态为待处理
            success = await self.update_task_status(task_id, TaskStatus.PENDING.value)
            
            if success:
                self.logger.info(f"任务重试成功: task_id={task_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"重试任务失败: task_id={task_id}, 错误: {e}")
            return False
    
    async def _retry_loop(self):
        """重试循环"""
        while self.is_running:
            try:
                # 检查需要重试的任务
                await self._check_retry_tasks()
                
                # 等待下次检查
                await asyncio.sleep(self.retry_delay)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"重试循环异常: {e}")
                await asyncio.sleep(self.retry_delay)
    
    async def _check_retry_tasks(self):
        """检查需要重试的任务"""
        try:
            # 获取需要重试的任务
            retry_tasks = await self.db_adapter.get_retry_tasks()
            
            for task in retry_tasks:
                # 检查是否到了重试时间
                if datetime.now().timestamp() >= task['retry_at']:
                    # 重置为待处理状态
                    await self.update_task_status(task['id'], TaskStatus.PENDING.value)
                    self.logger.info(f"任务重置为待处理: task_id={task['id']}")
        
        except Exception as e:
            self.logger.error(f"检查重试任务失败: 错误: {e}")
    
    async def cleanup_old_tasks(self, days: int = 30) -> int:
        """
        清理旧任务
        
        Args:
            days: 保留天数
            
        Returns:
            清理的任务数量
        """
        try:
            cutoff_time = datetime.now().timestamp() - (days * 24 * 3600)
            
            deleted_count = await self.db_adapter.delete_old_tasks(cutoff_time)
            
            self.logger.info(f"清理旧任务完成: 删除了 {deleted_count} 个任务")
            
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"清理旧任务失败: 错误: {e}")
            return 0
    
    async def get_task_statistics(self) -> Dict[str, int]:
        """
        获取任务统计信息
        
        Returns:
            各状态任务数量统计
        """
        try:
            stats = await self.db_adapter.get_task_statistics()
            return stats
        except Exception as e:
            self.logger.error(f"获取任务统计失败: 错误: {e}")
            return {}