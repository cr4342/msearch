"""
ManualOperationManager单元测试
"""

import pytest
import asyncio
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from typing import Dict, Any, List

from src.processing_service.manual_operation_manager import (
    ManualOperationManager, 
    OperationType, 
    OperationStatus
)
from src.processing_service.orchestrator import ProcessingOrchestrator
from src.processing_service.task_manager import TaskManager


class TestManualOperationManager:
    """ManualOperationManager单元测试类"""
    
    @pytest.fixture
    def manual_operation_manager(self):
        """创建ManualOperationManager实例"""
        # 模拟依赖
        mock_orchestrator = MagicMock(spec=ProcessingOrchestrator)
        mock_task_manager = MagicMock(spec=TaskManager)
        
        return ManualOperationManager(
            orchestrator=mock_orchestrator,
            task_manager=mock_task_manager
        )
    
    @pytest.fixture
    def sample_directory(self):
        """创建测试用的目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建测试文件
            with open(os.path.join(tmpdir, 'test.jpg'), 'w') as f:
                f.write('test')
            with open(os.path.join(tmpdir, 'test.mp4'), 'w') as f:
                f.write('test')
            yield tmpdir
    
    def test_initialization(self, manual_operation_manager):
        """测试ManualOperationManager初始化"""
        assert manual_operation_manager is not None
        assert hasattr(manual_operation_manager, 'active_operations')
        assert hasattr(manual_operation_manager, 'operation_history')
    
    def test_get_active_operations(self, manual_operation_manager):
        """测试获取活跃操作"""
        result = manual_operation_manager.get_active_operations()
        assert isinstance(result, list)
        assert len(result) == 0
    
    def test_get_operation_history(self, manual_operation_manager):
        """测试获取操作历史"""
        result = manual_operation_manager.get_operation_history()
        assert isinstance(result, list)
    
    @patch.object(ManualOperationManager, '_execute_operation')
    async def test_start_operation(self, mock_execute_operation, manual_operation_manager):
        """测试启动操作"""
        # 模拟执行操作成功
        mock_execute_operation.return_value = None
        
        operation_id = await manual_operation_manager.start_operation(
            OperationType.FULL_SCAN,
            {}
        )
        
        assert operation_id is not None
        assert isinstance(operation_id, str)
        assert len(operation_id) > 0
    
    @patch.object(ManualOperationManager, '_has_conflicting_operation')
    @patch.object(ManualOperationManager, '_execute_operation')
    async def test_start_conflicting_operation(self, 
                                            mock_execute_operation, 
                                            mock_has_conflicting_operation, 
                                            manual_operation_manager):
        """测试启动冲突操作"""
        # 模拟存在冲突操作
        mock_has_conflicting_operation.return_value = True
        
        with pytest.raises(Exception):
            await manual_operation_manager.start_operation(
                OperationType.FULL_SCAN,
                {}
            )
    
    async def test_get_files_in_directory(self, manual_operation_manager, sample_directory):
        """测试获取目录中的文件"""
        files = await manual_operation_manager._get_files_in_directory(sample_directory)
        
        assert files is not None
        assert isinstance(files, list)
        assert len(files) >= 2
    
    async def test_get_files_in_empty_directory(self, manual_operation_manager):
        """测试获取空目录中的文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            files = await manual_operation_manager._get_files_in_directory(tmpdir)
            
            assert files is not None
            assert isinstance(files, list)
            assert len(files) == 0
    
    @patch.object(ManualOperationManager, '_get_files_in_directory')
    @patch.object(ManualOperationManager, '_process_files_batch')
    async def test_execute_full_scan(self, 
                                   mock_process_files_batch, 
                                   mock_get_files_in_directory, 
                                   manual_operation_manager):
        """测试执行全量扫描"""
        # 模拟依赖
        mock_get_files_in_directory.return_value = ["/test/file1.jpg", "/test/file2.mp4"]
        mock_process_files_batch.return_value = None
        
        # 创建操作信息
        from src.processing_service.manual_operation_manager import OperationInfo, OperationProgress
        import datetime
        
        operation_info = OperationInfo(
            operation_id="test_op_id",
            operation_type=OperationType.FULL_SCAN,
            status=OperationStatus.RUNNING,
            parameters={},
            progress=OperationProgress(
                operation_id="test_op_id",
                total_files=0,
                processed_files=0,
                success_count=0,
                failed_count=0,
                current_file=None,
                current_stage="初始化",
                estimated_time_remaining=0.0,
                processing_speed=0.0,
                progress_percentage=0.0,
                start_time=datetime.datetime.now(),
                last_update=datetime.datetime.now()
            ),
            created_at=datetime.datetime.now(),
            started_at=datetime.datetime.now(),
            completed_at=None,
            error_message=None
        )
        
        # 模拟配置管理器返回监控目录
        with patch.object(manual_operation_manager.config_manager, 'get_list') as mock_get_list:
            mock_get_list.return_value = ["/test/dir1", "/test/dir2"]
            
            await manual_operation_manager._execute_full_scan(operation_info)
            
            # 验证调用
            assert mock_get_files_in_directory.called
            assert mock_process_files_batch.called
    
    @patch.object(ManualOperationManager, '_get_files_in_directory')
    @patch.object(ManualOperationManager, '_process_files_batch')
    @patch.object(ManualOperationManager.db_adapter, 'get_all_files')
    async def test_execute_incremental_scan(self, 
                                          mock_get_all_files, 
                                          mock_process_files_batch, 
                                          mock_get_files_in_directory, 
                                          manual_operation_manager):
        """测试执行增量扫描"""
        # 模拟依赖
        mock_get_all_files.return_value = [{"file_path": "/test/existing_file.jpg"}]
        mock_get_files_in_directory.return_value = ["/test/existing_file.jpg", "/test/new_file.mp4"]
        mock_process_files_batch.return_value = None
        
        # 创建操作信息
        from src.processing_service.manual_operation_manager import OperationInfo, OperationProgress
        import datetime
        
        operation_info = OperationInfo(
            operation_id="test_op_id",
            operation_type=OperationType.INCREMENTAL_SCAN,
            status=OperationStatus.RUNNING,
            parameters={},
            progress=OperationProgress(
                operation_id="test_op_id",
                total_files=0,
                processed_files=0,
                success_count=0,
                failed_count=0,
                current_file=None,
                current_stage="初始化",
                estimated_time_remaining=0.0,
                processing_speed=0.0,
                progress_percentage=0.0,
                start_time=datetime.datetime.now(),
                last_update=datetime.datetime.now()
            ),
            created_at=datetime.datetime.now(),
            started_at=datetime.datetime.now(),
            completed_at=None,
            error_message=None
        )
        
        # 模拟配置管理器返回监控目录
        with patch.object(manual_operation_manager.config_manager, 'get_list') as mock_get_list:
            mock_get_list.return_value = ["/test/dir1"]
            
            await manual_operation_manager._execute_incremental_scan(operation_info)
            
            # 验证调用
            assert mock_get_all_files.called
            assert mock_get_files_in_directory.called
            assert mock_process_files_batch.called
    
    @patch.object(ManualOperationManager.db_adapter, 'get_all_files')
    @patch.object(ManualOperationManager, '_process_files_batch')
    async def test_execute_reindex(self, 
                                 mock_process_files_batch, 
                                 mock_get_all_files, 
                                 manual_operation_manager):
        """测试执行重新索引"""
        # 模拟依赖
        mock_get_all_files.return_value = [{"file_path": "/test/file1.jpg"}, {"file_path": "/test/file2.mp4"}]
        mock_process_files_batch.return_value = None
        
        # 创建操作信息
        from src.processing_service.manual_operation_manager import OperationInfo, OperationProgress
        import datetime
        
        operation_info = OperationInfo(
            operation_id="test_op_id",
            operation_type=OperationType.REINDEX,
            status=OperationStatus.RUNNING,
            parameters={},
            progress=OperationProgress(
                operation_id="test_op_id",
                total_files=0,
                processed_files=0,
                success_count=0,
                failed_count=0,
                current_file=None,
                current_stage="初始化",
                estimated_time_remaining=0.0,
                processing_speed=0.0,
                progress_percentage=0.0,
                start_time=datetime.datetime.now(),
                last_update=datetime.datetime.now()
            ),
            created_at=datetime.datetime.now(),
            started_at=datetime.datetime.now(),
            completed_at=None,
            error_message=None
        )
        
        await manual_operation_manager._execute_reindex(operation_info)
        
        # 验证调用
        assert mock_get_all_files.called
        assert mock_process_files_batch.called
    
    @patch.object(ManualOperationManager, '_get_files_in_directory')
    @patch.object(ManualOperationManager, '_process_files_batch')
    async def test_execute_specific_dir_scan(self, 
                                           mock_process_files_batch, 
                                           mock_get_files_in_directory, 
                                           manual_operation_manager, 
                                           sample_directory):
        """测试执行指定目录扫描"""
        # 模拟依赖
        mock_get_files_in_directory.return_value = [os.path.join(sample_directory, 'test.jpg'), 
                                                  os.path.join(sample_directory, 'test.mp4')]
        mock_process_files_batch.return_value = None
        
        # 创建操作信息
        from src.processing_service.manual_operation_manager import OperationInfo, OperationProgress
        import datetime
        
        operation_info = OperationInfo(
            operation_id="test_op_id",
            operation_type=OperationType.SPECIFIC_DIR_SCAN,
            status=OperationStatus.RUNNING,
            parameters={"directory": sample_directory},
            progress=OperationProgress(
                operation_id="test_op_id",
                total_files=0,
                processed_files=0,
                success_count=0,
                failed_count=0,
                current_file=None,
                current_stage="初始化",
                estimated_time_remaining=0.0,
                processing_speed=0.0,
                progress_percentage=0.0,
                start_time=datetime.datetime.now(),
                last_update=datetime.datetime.now()
            ),
            created_at=datetime.datetime.now(),
            started_at=datetime.datetime.now(),
            completed_at=None,
            error_message=None
        )
        
        await manual_operation_manager._execute_specific_dir_scan(operation_info)
        
        # 验证调用
        assert mock_get_files_in_directory.called
        assert mock_process_files_batch.called
    
    async def test_has_conflicting_operation(self, manual_operation_manager):
        """测试检查冲突操作"""
        # 测试无冲突操作
        result = await manual_operation_manager._has_conflicting_operation(
            OperationType.FULL_SCAN,
            {}
        )
        assert not result
    
    async def test_get_operation_directories(self, manual_operation_manager):
        """测试获取操作涉及的目录"""
        # 测试全量扫描
        with patch.object(manual_operation_manager.config_manager, 'get_list') as mock_get_list:
            mock_get_list.return_value = ["/test/dir1", "/test/dir2"]
            
            dirs = await manual_operation_manager._get_operation_directories(
                OperationType.FULL_SCAN,
                {}
            )
            
            assert dirs == ["/test/dir1", "/test/dir2"]
        
        # 测试特定目录扫描
        dirs = await manual_operation_manager._get_operation_directories(
            OperationType.SPECIFIC_DIR_SCAN,
            {"directory": "/test/specific_dir"}
        )
        
        assert dirs == ["/test/specific_dir"]
    
    @patch.object(ManualOperationManager.db_adapter, 'get_temp_files_to_delete')
    @patch.object(ManualOperationManager.db_adapter, 'mark_file_as_deleted')
    async def test_execute_cleanup_temp_files(self, 
                                            mock_mark_file_as_deleted, 
                                            mock_get_temp_files_to_delete, 
                                            manual_operation_manager):
        """测试执行临时文件清理"""
        # 模拟依赖
        mock_get_temp_files_to_delete.return_value = [
            {"file_id": "temp_file_1", "file_path": "/tmp/temp1.jpg"},
            {"file_id": "temp_file_2", "file_path": "/tmp/temp2.mp4"}
        ]
        mock_mark_file_as_deleted.return_value = None
        
        # 创建操作信息
        from src.processing_service.manual_operation_manager import OperationInfo, OperationProgress
        import datetime
        
        operation_info = OperationInfo(
            operation_id="test_op_id",
            operation_type=OperationType.CLEANUP_TEMP_FILES,
            status=OperationStatus.RUNNING,
            parameters={},
            progress=OperationProgress(
                operation_id="test_op_id",
                total_files=0,
                processed_files=0,
                success_count=0,
                failed_count=0,
                current_file=None,
                current_stage="初始化",
                estimated_time_remaining=0.0,
                processing_speed=0.0,
                progress_percentage=0.0,
                start_time=datetime.datetime.now(),
                last_update=datetime.datetime.now()
            ),
            created_at=datetime.datetime.now(),
            started_at=datetime.datetime.now(),
            completed_at=None,
            error_message=None
        )
        
        # 模拟文件存在
        with patch('src.processing_service.manual_operation_manager.os.path.exists') as mock_exists:
            mock_exists.return_value = True
            
            with patch('src.processing_service.manual_operation_manager.os.remove') as mock_remove:
                mock_remove.return_value = None
                
                await manual_operation_manager._execute_cleanup_temp_files(operation_info)
                
                # 验证调用
                assert mock_get_temp_files_to_delete.called
                assert mock_remove.called
                assert mock_mark_file_as_deleted.called
    
    async def test_stop_operation(self, manual_operation_manager):
        """测试停止操作"""
        # 测试停止不存在的操作
        result = await manual_operation_manager.stop_operation("non_existent_op_id")
        assert not result
    
    async def test_pause_resume_operation(self, manual_operation_manager):
        """测试暂停和恢复操作"""
        # 测试暂停不存在的操作
        result = await manual_operation_manager.pause_operation("non_existent_op_id")
        assert not result
        
        # 测试恢复不存在的操作
        result = await manual_operation_manager.resume_operation("non_existent_op_id")
        assert not result
    
    def test_get_operation_info(self, manual_operation_manager):
        """测试获取操作信息"""
        # 测试获取不存在的操作信息
        result = manual_operation_manager.get_operation_info("non_existent_op_id")
        assert result is None
    
    def test_get_operation_progress(self, manual_operation_manager):
        """测试获取操作进度"""
        # 测试获取不存在的操作进度
        result = manual_operation_manager.get_operation_progress("non_existent_op_id")
        assert result is None
    
    def test_add_event_callback(self, manual_operation_manager):
        """测试添加事件回调"""
        # 测试添加回调
        def test_callback(operation_info):
            pass
        
        manual_operation_manager.add_event_callback('start', test_callback)
        assert 'start' in manual_operation_manager.event_callbacks
        assert len(manual_operation_manager.event_callbacks['start']) == 1
    
    async def test_trigger_event(self, manual_operation_manager):
        """测试触发事件"""
        # 测试触发事件
        called = False
        
        def test_callback(operation_info):
            nonlocal called
            called = True
        
        manual_operation_manager.add_event_callback('test', test_callback)
        
        # 创建操作信息
        from src.processing_service.manual_operation_manager import OperationInfo, OperationProgress
        import datetime
        
        operation_info = OperationInfo(
            operation_id="test_op_id",
            operation_type=OperationType.FULL_SCAN,
            status=OperationStatus.RUNNING,
            parameters={},
            progress=OperationProgress(
                operation_id="test_op_id",
                total_files=0,
                processed_files=0,
                success_count=0,
                failed_count=0,
                current_file=None,
                current_stage="初始化",
                estimated_time_remaining=0.0,
                processing_speed=0.0,
                progress_percentage=0.0,
                start_time=datetime.datetime.now(),
                last_update=datetime.datetime.now()
            ),
            created_at=datetime.datetime.now(),
            started_at=datetime.datetime.now(),
            completed_at=None,
            error_message=None
        )
        
        await manual_operation_manager._trigger_event('test', operation_info)
        
        assert called
    
    @patch.object(ManualOperationManager, '_execute_full_scan')
    @patch.object(ManualOperationManager, '_execute_incremental_scan')
    @patch.object(ManualOperationManager, '_execute_reindex')
    @patch.object(ManualOperationManager, '_execute_revectorize')
    @patch.object(ManualOperationManager, '_execute_specific_dir_scan')
    @patch.object(ManualOperationManager, '_execute_cleanup_temp_files')
    async def test_execute_operation(self, 
                                   mock_cleanup, 
                                   mock_specific_dir, 
                                   mock_revectorize, 
                                   mock_reindex, 
                                   mock_incremental, 
                                   mock_full_scan, 
                                   manual_operation_manager):
        """测试执行不同类型的操作"""
        # 模拟所有操作方法
        mock_full_scan.return_value = None
        mock_incremental.return_value = None
        mock_reindex.return_value = None
        mock_revectorize.return_value = None
        mock_specific_dir.return_value = None
        mock_cleanup.return_value = None
        
        # 创建操作信息
        from src.processing_service.manual_operation_manager import OperationInfo, OperationProgress
        import datetime
        
        operation_info = OperationInfo(
            operation_id="test_op_id",
            operation_type=OperationType.FULL_SCAN,
            status=OperationStatus.RUNNING,
            parameters={},
            progress=OperationProgress(
                operation_id="test_op_id",
                total_files=0,
                processed_files=0,
                success_count=0,
                failed_count=0,
                current_file=None,
                current_stage="初始化",
                estimated_time_remaining=0.0,
                processing_speed=0.0,
                progress_percentage=0.0,
                start_time=datetime.datetime.now(),
                last_update=datetime.datetime.now()
            ),
            created_at=datetime.datetime.now(),
            started_at=datetime.datetime.now(),
            completed_at=None,
            error_message=None
        )
        
        # 测试全量扫描
        await manual_operation_manager._execute_operation(operation_info)
        assert mock_full_scan.called
        
        # 测试增量扫描
        operation_info.operation_type = OperationType.INCREMENTAL_SCAN
        await manual_operation_manager._execute_operation(operation_info)
        assert mock_incremental.called
        
        # 测试重新索引
        operation_info.operation_type = OperationType.REINDEX
        await manual_operation_manager._execute_operation(operation_info)
        assert mock_reindex.called
        
        # 测试重新向量化
        operation_info.operation_type = OperationType.REVECTORIZE
        await manual_operation_manager._execute_operation(operation_info)
        assert mock_revectorize.called
        
        # 测试特定目录扫描
        operation_info.operation_type = OperationType.SPECIFIC_DIR_SCAN
        await manual_operation_manager._execute_operation(operation_info)
        assert mock_specific_dir.called
        
        # 测试清理临时文件
        operation_info.operation_type = OperationType.CLEANUP_TEMP_FILES
        await manual_operation_manager._execute_operation(operation_info)
        assert mock_cleanup.called
        
        # 测试无效操作类型
        operation_info.operation_type = "invalid_operation_type"
        with pytest.raises(ValueError):
            await manual_operation_manager._execute_operation(operation_info)
    
    async def test_should_pause_operation(self, manual_operation_manager):
        """测试检查操作是否应该暂停"""
        result = await manual_operation_manager._should_pause_operation("test_op_id")
        assert not result
    
    async def test_pause_operation(self, manual_operation_manager):
        """测试暂停操作"""
        # 创建操作信息
        from src.processing_service.manual_operation_manager import OperationInfo, OperationProgress
        import datetime
        
        operation_info = OperationInfo(
            operation_id="test_op_id",
            operation_type=OperationType.FULL_SCAN,
            status=OperationStatus.RUNNING,
            parameters={},
            progress=OperationProgress(
                operation_id="test_op_id",
                total_files=0,
                processed_files=0,
                success_count=0,
                failed_count=0,
                current_file=None,
                current_stage="初始化",
                estimated_time_remaining=0.0,
                processing_speed=0.0,
                progress_percentage=0.0,
                start_time=datetime.datetime.now(),
                last_update=datetime.datetime.now()
            ),
            created_at=datetime.datetime.now(),
            started_at=datetime.datetime.now(),
            completed_at=None,
            error_message=None
        )
        
        # 添加到活跃操作
        manual_operation_manager.active_operations["test_op_id"] = operation_info
        
        # 测试暂停操作
        result = await manual_operation_manager.pause_operation("test_op_id")
        assert result
        assert operation_info.status == OperationStatus.PAUSED
        
        # 测试恢复操作
        result = await manual_operation_manager.resume_operation("test_op_id")
        assert result
        assert operation_info.status == OperationStatus.RUNNING