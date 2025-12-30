"""
任务管理器测试
测试任务管理器功能
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from src.processing_service.task_manager import TaskManager, TaskStatus
from src.common.storage.database_adapter import DatabaseAdapter


class TestTaskManager:
    """任务管理器测试类"""
    
    @pytest.fixture
    def mock_db_adapter(self):
        """模拟数据库适配器"""
        adapter = Mock(spec=DatabaseAdapter)
        adapter.insert_task = AsyncMock(return_value='task_123')
        adapter.get_task = AsyncMock(return_value={
            'id': 'task_123',
            'file_id': 'file_123',
            'task_type': 'vectorization',
            'status': 'pending',
            'progress': 0,
            'retry_count': 0,
            'max_retry_attempts': 5,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        })
        adapter.update_task = AsyncMock(return_value=True)
        adapter.get_tasks_by_status = AsyncMock(return_value=[])
        adapter.get_retry_tasks = AsyncMock(return_value=[])
        adapter.delete_old_tasks = AsyncMock(return_value=0)
        adapter.get_task_statistics = AsyncMock(return_value={'pending': 0, 'processing': 0, 'completed': 0, 'failed': 0})
        return adapter
    
    @pytest.fixture
    def mock_config_manager(self):
        """模拟配置管理器"""
        config = Mock()
        config.get = Mock(side_effect=lambda key, default=None: {
            'task_management.max_retries': 5,
            'task_management.retry_delay': 1,
            'task_management.retry_multiplier': 2,
            'task_management.task_timeout': 3600
        }.get(key, default))
        return config
    
    @pytest.fixture
    def task_manager(self, mock_db_adapter, mock_config_manager):
        """任务管理器实例"""
        manager = TaskManager(mock_config_manager)
        manager.db_adapter = mock_db_adapter
        return manager
    
    def test_task_status_enum(self):
        """测试任务状态枚举"""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.PROCESSING.value == "processing"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.RETRY.value == "retry"
    
    @pytest.mark.asyncio
    async def test_task_manager_initialization(self, task_manager, mock_config_manager):
        """测试任务管理器初始化"""
        assert task_manager is not None
        assert task_manager.db_adapter is not None
        assert task_manager.config_manager == mock_config_manager
        assert task_manager.max_retry_attempts == 5
    
    @pytest.mark.asyncio
    async def test_create_task(self, task_manager, mock_db_adapter):
        """测试创建任务"""
        # 模拟 insert_task 返回任务ID
        mock_db_adapter.insert_task.return_value = 'new_task_456'
        
        task_id = await task_manager.create_task(
            file_id='test_file_1',
            task_type='vectorization',
            status=TaskStatus.PENDING.value
        )
        
        assert task_id == 'new_task_456'
        mock_db_adapter.insert_task.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_task(self, task_manager, mock_db_adapter):
        """测试获取任务"""
        task = await task_manager.get_task('task_123')
        
        assert task is not None
        assert task['id'] == 'task_123'
        assert task['task_type'] == 'vectorization'
        mock_db_adapter.get_task.assert_called_once_with('task_123')
    
    @pytest.mark.asyncio
    async def test_update_task_status(self, task_manager, mock_db_adapter):
        """测试更新任务状态"""
        # 设置 get_task 返回值
        mock_db_adapter.get_task.return_value = {
            'id': 'task_123',
            'status': 'pending',
            'retry_count': 0,
            'max_retry_attempts': 5
        }
        
        success = await task_manager.update_task_status('task_123', TaskStatus.PROCESSING.value)
        
        assert success is True
        mock_db_adapter.update_task.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_task_status_with_error(self, task_manager, mock_db_adapter):
        """测试更新任务状态带错误信息"""
        mock_db_adapter.get_task.return_value = {
            'id': 'task_123',
            'status': 'pending',
            'retry_count': 0,
            'max_retry_attempts': 5
        }
        
        success = await task_manager.update_task_status(
            'task_123', 
            TaskStatus.FAILED.value,
            error_message="Test error"
        )
        
        assert success is True
        # 验证调用时包含错误信息
        call_args = mock_db_adapter.update_task.call_args
        assert call_args[0][0] == 'task_123'
        # 更新参数是第二个位置参数（字典形式）
        updates = call_args[0][1]
        assert 'error_message' in updates
        assert updates['error_message'] == 'Test error'
    
    @pytest.mark.asyncio
    async def test_get_pending_tasks(self, task_manager, mock_db_adapter):
        """测试获取待处理任务"""
        mock_db_adapter.get_tasks_by_status.return_value = [
            {'id': 'task_1', 'status': 'pending'},
            {'id': 'task_2', 'status': 'pending'}
        ]
        
        tasks = await task_manager.get_pending_tasks(limit=10)
        
        assert isinstance(tasks, list)
        mock_db_adapter.get_tasks_by_status.assert_called_once_with('pending', 10)
    
    @pytest.mark.asyncio
    async def test_get_processing_tasks(self, task_manager, mock_db_adapter):
        """测试获取正在处理的任务"""
        mock_db_adapter.get_tasks_by_status.return_value = [
            {'id': 'task_1', 'status': 'processing'}
        ]
        
        tasks = await task_manager.get_processing_tasks()
        
        assert isinstance(tasks, list)
        mock_db_adapter.get_tasks_by_status.assert_called_once_with('processing')
    
    @pytest.mark.asyncio
    async def test_get_failed_tasks(self, task_manager, mock_db_adapter):
        """测试获取失败任务"""
        mock_db_adapter.get_tasks_by_status.return_value = [
            {'id': 'task_1', 'status': 'failed'}
        ]
        
        tasks = await task_manager.get_failed_tasks(limit=5)
        
        assert isinstance(tasks, list)
        mock_db_adapter.get_tasks_by_status.assert_called_once_with('failed', 5)
    
    @pytest.mark.asyncio
    async def test_task_lifecycle(self, task_manager, mock_db_adapter):
        """测试任务生命周期"""
        # 模拟任务不存在
        mock_db_adapter.get_task.return_value = None
        
        # 创建任务
        mock_db_adapter.insert_task.return_value = 'lifecycle_task_id'
        task_id = await task_manager.create_task(
            file_id='lifecycle_test_file',
            task_type='processing',
            status=TaskStatus.PENDING.value
        )
        assert task_id is not None
        
        # 获取任务 - 返回 None 因为模拟设置
        task = await task_manager.get_task(task_id)
        # 这里因为 get_task 被设置为返回 None，所以验证逻辑
        assert task is None or task['id'] == task_id
        
        # 更新为处理中
        mock_db_adapter.get_task.return_value = {
            'id': task_id,
            'status': 'pending',
            'retry_count': 0,
            'max_retry_attempts': 5
        }
        await task_manager.update_task_status(task_id, TaskStatus.PROCESSING.value)
        
        # 更新为完成
        mock_db_adapter.get_task.return_value = {
            'id': task_id,
            'status': 'processing',
            'retry_count': 0,
            'max_retry_attempts': 5
        }
        await task_manager.update_task_status(task_id, TaskStatus.COMPLETED.value)
    
    @pytest.mark.asyncio
    async def test_retry_failed_task(self, task_manager, mock_db_adapter):
        """测试重试失败任务"""
        # 模拟任务失败但可以重试
        mock_db_adapter.get_task.return_value = {
            'id': 'task_123',
            'status': 'failed',
            'retry_count': 0,
            'max_retry_attempts': 5
        }
        
        success = await task_manager.retry_failed_task('task_123')
        
        assert success is True
        # 验证状态被重置为 pending
        call_args = mock_db_adapter.update_task.call_args
        assert call_args[0][0] == 'task_123'
        # 更新参数是第二个位置参数（字典形式）
        updates = call_args[0][1]
        assert updates['status'] == 'pending'
    
    @pytest.mark.asyncio
    async def test_retry_task_not_found(self, task_manager, mock_db_adapter):
        """测试重试不存在的任务"""
        mock_db_adapter.get_task.return_value = None
        
        success = await task_manager.retry_failed_task('nonexistent_task')
        
        assert success is False
    
    @pytest.mark.asyncio
    async def test_retry_task_max_attempts_exceeded(self, task_manager, mock_db_adapter):
        """测试重试次数超限"""
        mock_db_adapter.get_task.return_value = {
            'id': 'task_123',
            'status': 'failed',
            'retry_count': 5,
            'max_retry_attempts': 5
        }
        
        success = await task_manager.retry_failed_task('task_123')
        
        assert success is False
        # update_task 不应该被调用
        mock_db_adapter.update_task.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_task_statistics(self, task_manager, mock_db_adapter):
        """测试获取任务统计"""
        mock_db_adapter.get_task_statistics.return_value = {
            'pending': 5,
            'processing': 2,
            'completed': 100,
            'failed': 3
        }
        
        stats = await task_manager.get_task_statistics()
        
        assert isinstance(stats, dict)
        assert stats['pending'] == 5
        assert stats['completed'] == 100
        mock_db_adapter.get_task_statistics.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cleanup_old_tasks(self, task_manager, mock_db_adapter):
        """测试清理旧任务"""
        mock_db_adapter.delete_old_tasks.return_value = 10
        
        deleted_count = await task_manager.cleanup_old_tasks(days=30)
        
        assert deleted_count == 10
        mock_db_adapter.delete_old_tasks.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_error_handling_in_create_task(self, task_manager, mock_db_adapter):
        """测试创建任务时的错误处理"""
        mock_db_adapter.insert_task.side_effect = Exception("Database error")
        
        with pytest.raises(Exception):
            await task_manager.create_task(
                file_id='error_test_file',
                task_type='vectorization'
            )
        
        # 恢复正常状态
        mock_db_adapter.insert_task.side_effect = None
        mock_db_adapter.insert_task.return_value = 'recovery_task_123'
        
        task_id = await task_manager.create_task(
            file_id='error_test_file',
            task_type='vectorization'
        )
        assert task_id == 'recovery_task_123'
