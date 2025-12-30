"""
手动操作管理器
负责处理用户通过UI触发的手动操作，如全量扫描、重新向量化等
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import uuid

from src.core.retry import async_retry

from src.processing_service.orchestrator import ProcessingOrchestrator
from src.processing_service.task_manager import TaskManager
from src.core.config_manager import get_config_manager
from src.common.storage.database_adapter import DatabaseAdapter


logger = logging.getLogger(__name__)


class OperationType(str, Enum):
    """操作类型枚举"""
    FULL_SCAN = "full_scan"
    INCREMENTAL_SCAN = "incremental_scan"
    REINDEX = "reindex"
    REVECTORIZE = "revectorize"
    SPECIFIC_DIR_SCAN = "specific_dir_scan"
    CLEANUP_TEMP_FILES = "cleanup_temp_files"


class OperationStatus(str, Enum):
    """操作状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class OperationProgress:
    """操作进度数据类"""
    operation_id: str
    total_files: int
    processed_files: int
    success_count: int
    failed_count: int
    current_file: Optional[str]
    current_stage: str
    estimated_time_remaining: float
    processing_speed: float  # files per second
    progress_percentage: float
    start_time: datetime
    last_update: datetime


@dataclass
class OperationInfo:
    """操作信息数据类"""
    operation_id: str
    operation_type: OperationType
    status: OperationStatus
    parameters: Dict[str, Any]
    progress: OperationProgress
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]


class ManualOperationManager:
    """手动操作管理器"""
    
    def __init__(self, orchestrator: ProcessingOrchestrator = None, task_manager: TaskManager = None, config_manager=None):
        self.orchestrator = orchestrator or ProcessingOrchestrator()
        self.task_manager = task_manager or TaskManager()
        self.config_manager = config_manager or get_config_manager()
        self.db_adapter = DatabaseAdapter()
        
        # 当前运行的操作
        self.active_operations: Dict[str, OperationInfo] = {}
        
        # 操作历史
        self.operation_history: List[OperationInfo] = []
        
        # 事件回调
        self.event_callbacks: Dict[str, List[Callable]] = {
            'start': [],
            'progress': [],
            'complete': [],
            'error': []
        }
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("手动操作管理器初始化完成")
    
    async def start_operation(self, operation_type: OperationType, parameters: Dict[str, Any] = None) -> str:
        """
        启动手动操作
        
        Args:
            operation_type: 操作类型
            parameters: 操作参数
            
        Returns:
            操作ID
        """
        if parameters is None:
            parameters = {}
        
        operation_id = str(uuid.uuid4())
        
        # 创建初始操作信息
        initial_progress = OperationProgress(
            operation_id=operation_id,
            total_files=0,
            processed_files=0,
            success_count=0,
            failed_count=0,
            current_file=None,
            current_stage="初始化",
            estimated_time_remaining=0.0,
            processing_speed=0.0,
            progress_percentage=0.0,
            start_time=datetime.now(),
            last_update=datetime.now()
        )
        
        operation_info = OperationInfo(
            operation_id=operation_id,
            operation_type=operation_type,
            status=OperationStatus.PENDING,
            parameters=parameters,
            progress=initial_progress,
            created_at=datetime.now(),
            started_at=None,
            completed_at=None,
            error_message=None
        )
        
        # 检查是否有冲突操作
        if await self._has_conflicting_operation(operation_type, parameters):
            raise Exception(f"存在冲突的操作，无法启动 {operation_type}")
        
        # 添加到活跃操作
        self.active_operations[operation_id] = operation_info
        
        # 更新状态为运行中
        operation_info.status = OperationStatus.RUNNING
        operation_info.started_at = datetime.now()
        
        # 执行操作
        try:
            await self._execute_operation(operation_info)
        except Exception as e:
            self.logger.error(f"操作执行失败 {operation_id}: {e}")
            operation_info.status = OperationStatus.FAILED
            operation_info.error_message = str(e)
            operation_info.completed_at = datetime.now()
        
        # 移动到历史记录
        self.operation_history.append(operation_info)
        del self.active_operations[operation_id]
        
        # 触发完成事件
        await self._trigger_event('complete', operation_info)
        
        return operation_id
    
    async def _has_conflicting_operation(self, operation_type: OperationType, parameters: Dict[str, Any]) -> bool:
        """检查是否存在冲突的操作"""
        for op_id, op_info in self.active_operations.items():
            if op_info.status in [OperationStatus.RUNNING, OperationStatus.PAUSED]:
                # 检查是否操作相同目录
                if operation_type in [OperationType.FULL_SCAN, OperationType.INCREMENTAL_SCAN, OperationType.SPECIFIC_DIR_SCAN]:
                    # 获取当前操作涉及的目录
                    current_dirs = await self._get_operation_directories(operation_type, parameters)
                    existing_dirs = await self._get_operation_directories(op_info.operation_type, op_info.parameters)
                    
                    # 检查目录是否有重叠
                    if set(current_dirs) & set(existing_dirs):
                        return True
        
        return False
    
    async def _get_operation_directories(self, operation_type: OperationType, parameters: Dict[str, Any]) -> List[str]:
        """获取操作涉及的目录列表"""
        if operation_type == OperationType.SPECIFIC_DIR_SCAN:
            return [parameters.get('directory', '')]
        elif operation_type == OperationType.FULL_SCAN:
            # 获取配置中的所有监控目录
            monitored_dirs = self.config_manager.get_list('system.monitored_directories', [])
            return monitored_dirs
        else:
            # 对于其他操作类型，可能需要根据具体情况判断
            return []
    
    async def _execute_operation(self, operation_info: OperationInfo):
        """执行操作"""
        operation_type = operation_info.operation_type
        parameters = operation_info.parameters
        
        self.logger.info(f"开始执行操作: {operation_type} (ID: {operation_info.operation_id})")
        
        if operation_type == OperationType.FULL_SCAN:
            await self._execute_full_scan(operation_info)
        elif operation_type == OperationType.INCREMENTAL_SCAN:
            await self._execute_incremental_scan(operation_info)
        elif operation_type == OperationType.REINDEX:
            await self._execute_reindex(operation_info)
        elif operation_type == OperationType.REVECTORIZE:
            await self._execute_revectorize(operation_info)
        elif operation_type == OperationType.SPECIFIC_DIR_SCAN:
            await self._execute_specific_dir_scan(operation_info)
        elif operation_type == OperationType.CLEANUP_TEMP_FILES:
            await self._execute_cleanup_temp_files(operation_info)
        else:
            raise ValueError(f"不支持的操作类型: {operation_type}")
    
    async def _execute_full_scan(self, operation_info: OperationInfo):
        """执行全量扫描"""
        operation_info.progress.current_stage = "扫描目录"
        
        # 获取所有监控目录
        monitored_dirs = self.config_manager.get_list('system.monitored_directories', [])
        
        if not monitored_dirs:
            self.logger.warning("未配置监控目录")
            return
        
        # 获取所有需要处理的文件
        all_files = []
        for directory in monitored_dirs:
            files = await self._get_files_in_directory(directory)
            all_files.extend(files)
        
        operation_info.progress.total_files = len(all_files)
        
        # 开始处理文件
        await self._process_files_batch(operation_info, all_files)
    
    async def _execute_incremental_scan(self, operation_info: OperationInfo):
        """执行增量扫描"""
        operation_info.progress.current_stage = "增量扫描"
        
        # 获取所有监控目录
        monitored_dirs = self.config_manager.get_list('system.monitored_directories', [])
        
        if not monitored_dirs:
            self.logger.warning("未配置监控目录")
            return
        
        # 获取数据库中已处理的文件
        processed_files = await self.db_adapter.get_all_files()
        processed_paths = {f['file_path'] for f in processed_files}
        
        # 获取所有文件并过滤出未处理的
        all_files = []
        for directory in monitored_dirs:
            files = await self._get_files_in_directory(directory)
            for file_path in files:
                if file_path not in processed_paths:
                    all_files.append(file_path)
        
        operation_info.progress.total_files = len(all_files)
        
        # 开始处理文件
        await self._process_files_batch(operation_info, all_files)
    
    async def _execute_reindex(self, operation_info: OperationInfo):
        """执行重新索引"""
        operation_info.progress.current_stage = "重新索引"
        
        # 获取所有已处理的文件
        all_files = await self.db_adapter.get_all_files()
        file_paths = [f['file_path'] for f in all_files]
        
        operation_info.progress.total_files = len(file_paths)
        
        # 开始处理文件
        await self._process_files_batch(operation_info, file_paths)
    
    async def _execute_revectorize(self, operation_info: OperationInfo):
        """执行重新向量化"""
        operation_info.progress.current_stage = "重新向量化"
        
        # 获取所有已处理的文件
        all_files = await self.db_adapter.get_all_files()
        file_paths = [f['file_path'] for f in all_files]
        
        operation_info.progress.total_files = len(file_paths)
        
        # 开始处理文件
        await self._process_files_batch(operation_info, file_paths)
    
    async def _execute_specific_dir_scan(self, operation_info: OperationInfo):
        """执行指定目录扫描"""
        directory = operation_info.parameters.get('directory', '')
        if not directory:
            raise ValueError("未指定目录")
        
        operation_info.progress.current_stage = f"扫描目录: {directory}"
        
        # 获取目录中的文件
        files = await self._get_files_in_directory(directory)
        
        operation_info.progress.total_files = len(files)
        
        # 开始处理文件
        await self._process_files_batch(operation_info, files)
    
    async def _execute_cleanup_temp_files(self, operation_info: OperationInfo):
        """执行临时文件清理"""
        operation_info.progress.current_stage = "清理临时文件"
        
        # 获取可删除的临时文件
        temp_files = await self.db_adapter.get_temp_files_to_delete()
        
        operation_info.progress.total_files = len(temp_files)
        
        processed = 0
        success_count = 0
        failed_count = 0
        
        for temp_file in temp_files:
            try:
                # 删除物理文件
                import os
                if os.path.exists(temp_file['file_path']):
                    os.remove(temp_file['file_path'])
                
                # 更新数据库状态
                await self.db_adapter.mark_file_as_deleted(temp_file['file_id'])
                
                success_count += 1
            except Exception as e:
                self.logger.error(f"删除临时文件失败 {temp_file['file_path']}: {e}")
                failed_count += 1
            
            processed += 1
            operation_info.progress.processed_files = processed
            operation_info.progress.success_count = success_count
            operation_info.progress.failed_count = failed_count
            operation_info.progress.current_file = temp_file['file_path']
            operation_info.progress.progress_percentage = (processed / len(temp_files)) * 100 if len(temp_files) > 0 else 0
            
            # 更新进度时间
            operation_info.progress.last_update = datetime.now()
            
            # 触发进度事件
            await self._trigger_event('progress', operation_info)
            
            # 检查是否需要暂停
            if await self._should_pause_operation(operation_info.operation_id):
                await self._pause_operation(operation_info)
        
        operation_info.progress.current_stage = "清理完成"
    
    async def _process_files_batch(self, operation_info: OperationInfo, file_paths: List[str]):
        """批量处理文件"""
        processed = 0
        success_count = 0
        failed_count = 0
        
        start_time = datetime.now()
        
        for file_path in file_paths:
            try:
                # 更新进度信息
                operation_info.progress.current_file = file_path
                operation_info.progress.current_stage = f"处理文件 ({processed + 1}/{len(file_paths)})"
                
                # 提交处理任务
                task_id = await self.orchestrator.submit_file(file_path)
                
                # 等待任务完成
                task_result = await self.task_manager.wait_for_completion(task_id)
                
                if task_result.get('status') == 'completed':
                    success_count += 1
                else:
                    failed_count += 1
                    self.logger.warning(f"文件处理失败: {file_path}")
                
            except Exception as e:
                self.logger.error(f"处理文件失败 {file_path}: {e}")
                failed_count += 1
            
            processed += 1
            operation_info.progress.processed_files = processed
            operation_info.progress.success_count = success_count
            operation_info.progress.failed_count = failed_count
            operation_info.progress.progress_percentage = (processed / len(file_paths)) * 100 if len(file_paths) > 0 else 0
            
            # 计算处理速度和剩余时间
            elapsed_time = (datetime.now() - start_time).total_seconds()
            if processed > 0 and elapsed_time > 0:
                operation_info.progress.processing_speed = processed / elapsed_time
                remaining_files = len(file_paths) - processed
                operation_info.progress.estimated_time_remaining = remaining_files / operation_info.progress.processing_speed if operation_info.progress.processing_speed > 0 else 0
            
            # 更新进度时间
            operation_info.progress.last_update = datetime.now()
            
            # 触发进度事件
            await self._trigger_event('progress', operation_info)
            
            # 检查是否需要暂停
            if await self._should_pause_operation(operation_info.operation_id):
                await self._pause_operation(operation_info)
        
        operation_info.progress.current_stage = "处理完成"
    
    async def _get_files_in_directory(self, directory: str) -> List[str]:
        """获取目录中的文件列表"""
        import os
        
        supported_extensions = [
            '.jpg', '.jpeg', '.png', '.bmp', '.webp',  # 图像
            '.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.webm',  # 视频
            '.mp3', '.wav', '.flac', '.aac', '.m4a', '.ogg'  # 音频
        ]
        
        files = []
        
        for root, dirs, filenames in os.walk(directory):
            for filename in filenames:
                if any(filename.lower().endswith(ext) for ext in supported_extensions):
                    file_path = os.path.join(root, filename)
                    files.append(file_path)
        
        return files
    
    async def _should_pause_operation(self, operation_id: str) -> bool:
        """检查操作是否应该暂停"""
        # 实现暂停逻辑，可以通过外部信号或特定条件
        return False
    
    async def _pause_operation(self, operation_info: OperationInfo):
        """暂停操作"""
        operation_info.status = OperationStatus.PAUSED
        await self._trigger_event('pause', operation_info)
        
        # 等待恢复信号
        while operation_info.status == OperationStatus.PAUSED:
            await asyncio.sleep(1)
    
    async def stop_operation(self, operation_id: str) -> bool:
        """停止指定操作"""
        if operation_id not in self.active_operations:
            self.logger.warning(f"操作不存在: {operation_id}")
            return False
        
        operation_info = self.active_operations[operation_id]
        operation_info.status = OperationStatus.CANCELLED
        operation_info.completed_at = datetime.now()
        
        # 从活跃操作中移除
        del self.active_operations[operation_id]
        
        # 添加到历史记录
        self.operation_history.append(operation_info)
        
        self.logger.info(f"操作已停止: {operation_id}")
        return True
    
    async def pause_operation(self, operation_id: str) -> bool:
        """暂停指定操作"""
        if operation_id not in self.active_operations:
            self.logger.warning(f"操作不存在: {operation_id}")
            return False
        
        operation_info = self.active_operations[operation_id]
        if operation_info.status == OperationStatus.RUNNING:
            operation_info.status = OperationStatus.PAUSED
            await self._trigger_event('pause', operation_info)
            return True
        
        return False
    
    async def resume_operation(self, operation_id: str) -> bool:
        """恢复指定操作"""
        if operation_id not in self.active_operations:
            self.logger.warning(f"操作不存在: {operation_id}")
            return False
        
        operation_info = self.active_operations[operation_id]
        if operation_info.status == OperationStatus.PAUSED:
            operation_info.status = OperationStatus.RUNNING
            await self._trigger_event('resume', operation_info)
            return True
        
        return False
    
    def get_operation_progress(self, operation_id: str) -> Optional[OperationProgress]:
        """获取操作进度"""
        if operation_id in self.active_operations:
            return self.active_operations[operation_id].progress
        
        # 检查历史记录
        for op_info in self.operation_history:
            if op_info.operation_id == operation_id:
                return op_info.progress
        
        return None
    
    def get_operation_info(self, operation_id: str) -> Optional[OperationInfo]:
        """获取操作信息"""
        if operation_id in self.active_operations:
            return self.active_operations[operation_id]
        
        # 检查历史记录
        for op_info in self.operation_history:
            if op_info.operation_id == operation_id:
                return op_info
        
        return None
    
    def get_active_operations(self) -> List[OperationInfo]:
        """获取所有活跃操作"""
        return list(self.active_operations.values())
    
    def get_operation_history(self) -> List[OperationInfo]:
        """获取操作历史"""
        return self.operation_history
    
    def add_event_callback(self, event_type: str, callback: Callable):
        """添加事件回调"""
        if event_type not in self.event_callbacks:
            self.event_callbacks[event_type] = []
        
        self.event_callbacks[event_type].append(callback)
    
    async def _trigger_event(self, event_type: str, operation_info: OperationInfo):
        """触发事件"""
        if event_type in self.event_callbacks:
            for callback in self.event_callbacks[event_type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(operation_info)
                    else:
                        callback(operation_info)
                except Exception as e:
                    self.logger.error(f"事件回调执行失败: {e}")


# 全局手动操作管理器实例
_manual_operation_manager = None


def get_manual_operation_manager() -> ManualOperationManager:
    """获取全局手动操作管理器实例"""
    global _manual_operation_manager
    
    if _manual_operation_manager is None:
        _manual_operation_manager = ManualOperationManager()
    
    return _manual_operation_manager