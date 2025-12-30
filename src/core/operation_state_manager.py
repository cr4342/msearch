"""
操作状态管理器
管理系统中所有操作的状态，包括自动监控和手动操作
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import json
import sqlite3
import os
from contextlib import contextmanager

from src.core.config_manager import get_config_manager


logger = logging.getLogger(__name__)


class OperationType(str, Enum):
    """操作类型枚举"""
    FILE_MONITOR = "file_monitor"  # 文件监控操作
    PROCESSING_TASK = "processing_task"  # 处理任务
    MANUAL_OPERATION = "manual_operation"  # 手动操作
    INDEXING = "indexing"  # 索引操作
    SEARCH = "search"  # 搜索操作
    CLEANUP = "cleanup"  # 清理操作


class OperationStatus(str, Enum):
    """操作状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SCHEDULED = "scheduled"


@dataclass
class OperationState:
    """操作状态数据类"""
    operation_id: str
    operation_type: OperationType
    status: OperationStatus
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    progress: float  # 0-100
    details: Dict[str, Any]  # 操作详细信息
    error_message: Optional[str]
    parent_operation_id: Optional[str]  # 父操作ID
    priority: int  # 优先级，数值越小优先级越高


class OperationStateManager:
    """操作状态管理器"""
    
    def __init__(self, db_path: str = None, config_manager=None):
        self.config_manager = config_manager or get_config_manager()
        
        # 使用配置中的数据库路径，或使用默认路径
        if db_path:
            self.db_path = db_path
        else:
            data_dir = self.config_manager.get("system.data_dir", "./data")
            self.db_path = os.path.join(data_dir, "operation_states.db")
        
        # 确保目录存在
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # 初始化数据库
        self._init_database()
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"操作状态管理器初始化完成，数据库路径: {self.db_path}")
    
    def _init_database(self):
        """初始化数据库表"""
        with self._get_db_connection() as conn:
            # 创建操作状态表
            conn.execute('''
                CREATE TABLE IF NOT EXISTS operation_states (
                    operation_id TEXT PRIMARY KEY,
                    operation_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT,
                    progress REAL DEFAULT 0,
                    details TEXT,
                    error_message TEXT,
                    parent_operation_id TEXT,
                    priority INTEGER DEFAULT 0,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建索引
            conn.execute('CREATE INDEX IF NOT EXISTS idx_status ON operation_states(status)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_type ON operation_states(operation_type)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_parent ON operation_states(parent_operation_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_created ON operation_states(created_at)')
            
            conn.commit()
    
    @contextmanager
    def _get_db_connection(self):
        """获取数据库连接的上下文管理器"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 使结果可以通过列名访问
        try:
            yield conn
        finally:
            conn.close()
    
    def create_operation(self, operation_id: str, operation_type: OperationType, 
                        details: Dict[str, Any] = None, parent_operation_id: str = None, 
                        priority: int = 0) -> bool:
        """
        创建新操作
        
        Args:
            operation_id: 操作ID
            operation_type: 操作类型
            details: 操作详细信息
            parent_operation_id: 父操作ID
            priority: 优先级
            
        Returns:
            是否创建成功
        """
        try:
            with self._get_db_connection() as conn:
                conn.execute('''
                    INSERT INTO operation_states (
                        operation_id, operation_type, status, created_at, 
                        details, parent_operation_id, priority
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    operation_id, operation_type.value, OperationStatus.PENDING.value,
                    datetime.now().isoformat(), json.dumps(details or {}),
                    parent_operation_id, priority
                ))
                conn.commit()
                
                self.logger.info(f"创建操作: {operation_id}, 类型: {operation_type}")
                return True
                
        except Exception as e:
            self.logger.error(f"创建操作失败 {operation_id}: {e}")
            return False
    
    def update_operation_status(self, operation_id: str, status: OperationStatus, 
                               progress: float = None, error_message: str = None) -> bool:
        """
        更新操作状态
        
        Args:
            operation_id: 操作ID
            status: 新状态
            progress: 进度百分比
            error_message: 错误信息
            
        Returns:
            是否更新成功
        """
        try:
            with self._get_db_connection() as conn:
                update_fields = []
                update_values = []
                
                update_fields.append("status = ?")
                update_values.append(status.value)
                
                if progress is not None:
                    update_fields.append("progress = ?")
                    update_values.append(progress)
                
                if error_message is not None:
                    update_fields.append("error_message = ?")
                    update_values.append(error_message)
                
                # 根据状态更新时间字段
                if status == OperationStatus.RUNNING:
                    update_fields.append("started_at = ?")
                    update_values.append(datetime.now().isoformat())
                elif status in [OperationStatus.COMPLETED, OperationStatus.FAILED, OperationStatus.CANCELLED]:
                    update_fields.append("completed_at = ?")
                    update_values.append(datetime.now().isoformat())
                
                update_fields.append("updated_at = CURRENT_TIMESTAMP")
                
                query = f"UPDATE operation_states SET {', '.join(update_fields)} WHERE operation_id = ?"
                update_values.append(operation_id)
                
                conn.execute(query, update_values)
                conn.commit()
                
                if conn.total_changes > 0:
                    self.logger.debug(f"更新操作状态: {operation_id}, 状态: {status}")
                    return True
                else:
                    self.logger.warning(f"未找到操作: {operation_id}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"更新操作状态失败 {operation_id}: {e}")
            return False
    
    def update_operation_progress(self, operation_id: str, progress: float, details: Dict[str, Any] = None) -> bool:
        """
        更新操作进度
        
        Args:
            operation_id: 操作ID
            progress: 进度百分比
            details: 详细信息
            
        Returns:
            是否更新成功
        """
        try:
            with self._get_db_connection() as conn:
                update_fields = []
                update_values = []
                
                if progress is not None:
                    update_fields.append("progress = ?")
                    update_values.append(progress)
                
                if details is not None:
                    # 合并现有详情和新详情
                    current_details = self.get_operation_details(operation_id)
                    if current_details:
                        current_details.update(details)
                    else:
                        current_details = details
                    
                    update_fields.append("details = ?")
                    update_values.append(json.dumps(current_details))
                
                update_fields.append("updated_at = CURRENT_TIMESTAMP")
                
                query = f"UPDATE operation_states SET {', '.join(update_fields)} WHERE operation_id = ?"
                update_values.append(operation_id)
                
                conn.execute(query, update_values)
                conn.commit()
                
                if conn.total_changes > 0:
                    self.logger.debug(f"更新操作进度: {operation_id}, 进度: {progress}%")
                    return True
                else:
                    self.logger.warning(f"未找到操作: {operation_id}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"更新操作进度失败 {operation_id}: {e}")
            return False
    
    def get_operation_state(self, operation_id: str) -> Optional[OperationState]:
        """
        获取操作状态
        
        Args:
            operation_id: 操作ID
            
        Returns:
            操作状态，如果不存在则返回None
        """
        try:
            with self._get_db_connection() as conn:
                row = conn.execute(
                    'SELECT * FROM operation_states WHERE operation_id = ?', 
                    (operation_id,)
                ).fetchone()
                
                if row:
                    return OperationState(
                        operation_id=row['operation_id'],
                        operation_type=OperationType(row['operation_type']),
                        status=OperationStatus(row['status']),
                        created_at=datetime.fromisoformat(row['created_at']),
                        started_at=datetime.fromisoformat(row['started_at']) if row['started_at'] else None,
                        completed_at=datetime.fromisoformat(row['completed_at']) if row['completed_at'] else None,
                        progress=row['progress'],
                        details=json.loads(row['details']) if row['details'] else {},
                        error_message=row['error_message'],
                        parent_operation_id=row['parent_operation_id'],
                        priority=row['priority']
                    )
                else:
                    self.logger.debug(f"未找到操作: {operation_id}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"获取操作状态失败 {operation_id}: {e}")
            return None
    
    def get_operations_by_type(self, operation_type: OperationType) -> List[OperationState]:
        """
        根据操作类型获取操作列表
        
        Args:
            operation_type: 操作类型
            
        Returns:
            操作状态列表
        """
        try:
            with self._get_db_connection() as conn:
                rows = conn.execute(
                    'SELECT * FROM operation_states WHERE operation_type = ? ORDER BY created_at DESC', 
                    (operation_type.value,)
                ).fetchall()
                
                operations = []
                for row in rows:
                    operations.append(OperationState(
                        operation_id=row['operation_id'],
                        operation_type=OperationType(row['operation_type']),
                        status=OperationStatus(row['status']),
                        created_at=datetime.fromisoformat(row['created_at']),
                        started_at=datetime.fromisoformat(row['started_at']) if row['started_at'] else None,
                        completed_at=datetime.fromisoformat(row['completed_at']) if row['completed_at'] else None,
                        progress=row['progress'],
                        details=json.loads(row['details']) if row['details'] else {},
                        error_message=row['error_message'],
                        parent_operation_id=row['parent_operation_id'],
                        priority=row['priority']
                    ))
                
                return operations
                
        except Exception as e:
            self.logger.error(f"获取操作列表失败: {e}")
            return []
    
    def get_operations_by_status(self, status: OperationStatus) -> List[OperationState]:
        """
        根据状态获取操作列表
        
        Args:
            status: 操作状态
            
        Returns:
            操作状态列表
        """
        try:
            with self._get_db_connection() as conn:
                rows = conn.execute(
                    'SELECT * FROM operation_states WHERE status = ? ORDER BY created_at DESC', 
                    (status.value,)
                ).fetchall()
                
                operations = []
                for row in rows:
                    operations.append(OperationState(
                        operation_id=row['operation_id'],
                        operation_type=OperationType(row['operation_type']),
                        status=OperationStatus(row['status']),
                        created_at=datetime.fromisoformat(row['created_at']),
                        started_at=datetime.fromisoformat(row['started_at']) if row['started_at'] else None,
                        completed_at=datetime.fromisoformat(row['completed_at']) if row['completed_at'] else None,
                        progress=row['progress'],
                        details=json.loads(row['details']) if row['details'] else {},
                        error_message=row['error_message'],
                        parent_operation_id=row['parent_operation_id'],
                        priority=row['priority']
                    ))
                
                return operations
                
        except Exception as e:
            self.logger.error(f"获取操作列表失败: {e}")
            return []
    
    def get_active_operations(self) -> List[OperationState]:
        """
        获取所有活跃操作（运行中、暂停、待处理）
        
        Returns:
            活跃操作列表
        """
        try:
            with self._get_db_connection() as conn:
                rows = conn.execute('''
                    SELECT * FROM operation_states 
                    WHERE status IN (?, ?, ?) 
                    ORDER BY priority ASC, created_at DESC
                ''', (
                    OperationStatus.PENDING.value,
                    OperationStatus.RUNNING.value,
                    OperationStatus.PAUSED.value
                )).fetchall()
                
                operations = []
                for row in rows:
                    operations.append(OperationState(
                        operation_id=row['operation_id'],
                        operation_type=OperationType(row['operation_type']),
                        status=OperationStatus(row['status']),
                        created_at=datetime.fromisoformat(row['created_at']),
                        started_at=datetime.fromisoformat(row['started_at']) if row['started_at'] else None,
                        completed_at=datetime.fromisoformat(row['completed_at']) if row['completed_at'] else None,
                        progress=row['progress'],
                        details=json.loads(row['details']) if row['details'] else {},
                        error_message=row['error_message'],
                        parent_operation_id=row['parent_operation_id'],
                        priority=row['priority']
                    ))
                
                return operations
                
        except Exception as e:
            self.logger.error(f"获取活跃操作列表失败: {e}")
            return []
    
    def get_operation_details(self, operation_id: str) -> Optional[Dict[str, Any]]:
        """
        获取操作详细信息
        
        Args:
            operation_id: 操作ID
            
        Returns:
            操作详细信息，如果不存在则返回None
        """
        try:
            with self._get_db_connection() as conn:
                row = conn.execute(
                    'SELECT details FROM operation_states WHERE operation_id = ?', 
                    (operation_id,)
                ).fetchone()
                
                if row and row['details']:
                    return json.loads(row['details'])
                else:
                    return {}
                    
        except Exception as e:
            self.logger.error(f"获取操作详情失败 {operation_id}: {e}")
            return None
    
    def cancel_operation(self, operation_id: str) -> bool:
        """
        取消操作
        
        Args:
            operation_id: 操作ID
            
        Returns:
            是否取消成功
        """
        return self.update_operation_status(operation_id, OperationStatus.CANCELLED)
    
    def fail_operation(self, operation_id: str, error_message: str = None) -> bool:
        """
        标记操作失败
        
        Args:
            operation_id: 操作ID
            error_message: 错误信息
            
        Returns:
            是否标记成功
        """
        return self.update_operation_status(operation_id, OperationStatus.FAILED, error_message=error_message)
    
    def complete_operation(self, operation_id: str) -> bool:
        """
        标记操作完成
        
        Args:
            operation_id: 操作ID
            
        Returns:
            是否标记成功
        """
        return self.update_operation_status(operation_id, OperationStatus.COMPLETED, progress=100.0)
    
    def pause_operation(self, operation_id: str) -> bool:
        """
        暂停操作
        
        Args:
            operation_id: 操作ID
            
        Returns:
            是否暂停成功
        """
        return self.update_operation_status(operation_id, OperationStatus.PAUSED)
    
    def resume_operation(self, operation_id: str) -> bool:
        """
        恢复操作
        
        Args:
            operation_id: 操作ID
            
        Returns:
            是否恢复成功
        """
        return self.update_operation_status(operation_id, OperationStatus.RUNNING)
    
    def delete_operation(self, operation_id: str) -> bool:
        """
        删除操作记录
        
        Args:
            operation_id: 操作ID
            
        Returns:
            是否删除成功
        """
        try:
            with self._get_db_connection() as conn:
                conn.execute('DELETE FROM operation_states WHERE operation_id = ?', (operation_id,))
                conn.commit()
                
                if conn.total_changes > 0:
                    self.logger.info(f"删除操作记录: {operation_id}")
                    return True
                else:
                    self.logger.warning(f"未找到操作记录: {operation_id}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"删除操作记录失败 {operation_id}: {e}")
            return False
    
    def cleanup_old_operations(self, days: int = 30) -> int:
        """
        清理旧的操作记录
        
        Args:
            days: 保留天数
            
        Returns:
            删除的记录数
        """
        try:
            cutoff_date = datetime.now()
            cutoff_date = cutoff_date.replace(
                year=cutoff_date.year,
                month=cutoff_date.month,
                day=cutoff_date.day - days
            ).isoformat()
            
            with self._get_db_connection() as conn:
                # 只删除已完成、失败或取消的操作
                conn.execute('''
                    DELETE FROM operation_states 
                    WHERE created_at < ? AND status IN (?, ?, ?)
                ''', (
                    cutoff_date,
                    OperationStatus.COMPLETED.value,
                    OperationStatus.FAILED.value,
                    OperationStatus.CANCELLED.value
                ))
                conn.commit()
                
                deleted_count = conn.total_changes
                self.logger.info(f"清理了 {deleted_count} 条旧操作记录")
                return deleted_count
                
        except Exception as e:
            self.logger.error(f"清理旧操作记录失败: {e}")
            return 0
    
    def get_operation_statistics(self) -> Dict[str, Any]:
        """
        获取操作统计信息
        
        Returns:
            统计信息字典
        """
        try:
            with self._get_db_connection() as conn:
                # 总操作数
                total_count = conn.execute('SELECT COUNT(*) FROM operation_states').fetchone()[0]
                
                # 各状态操作数
                status_counts = {}
                for status in OperationStatus:
                    count = conn.execute(
                        'SELECT COUNT(*) FROM operation_states WHERE status = ?', 
                        (status.value,)
                    ).fetchone()[0]
                    status_counts[status.value] = count
                
                # 各类型操作数
                type_counts = {}
                for op_type in OperationType:
                    count = conn.execute(
                        'SELECT COUNT(*) FROM operation_states WHERE operation_type = ?', 
                        (op_type.value,)
                    ).fetchone()[0]
                    type_counts[op_type.value] = count
                
                return {
                    'total_operations': total_count,
                    'status_counts': status_counts,
                    'type_counts': type_counts
                }
                
        except Exception as e:
            self.logger.error(f"获取操作统计信息失败: {e}")
            return {
                'total_operations': 0,
                'status_counts': {status.value: 0 for status in OperationStatus},
                'type_counts': {op_type.value: 0 for op_type in OperationType}
            }
    
    def get_recent_operations(self, limit: int = 50) -> List[OperationState]:
        """
        获取最近的操作
        
        Args:
            limit: 限制数量
            
        Returns:
            最近操作列表
        """
        try:
            with self._get_db_connection() as conn:
                rows = conn.execute(
                    'SELECT * FROM operation_states ORDER BY created_at DESC LIMIT ?', 
                    (limit,)
                ).fetchall()
                
                operations = []
                for row in rows:
                    operations.append(OperationState(
                        operation_id=row['operation_id'],
                        operation_type=OperationType(row['operation_type']),
                        status=OperationStatus(row['status']),
                        created_at=datetime.fromisoformat(row['created_at']),
                        started_at=datetime.fromisoformat(row['started_at']) if row['started_at'] else None,
                        completed_at=datetime.fromisoformat(row['completed_at']) if row['completed_at'] else None,
                        progress=row['progress'],
                        details=json.loads(row['details']) if row['details'] else {},
                        error_message=row['error_message'],
                        parent_operation_id=row['parent_operation_id'],
                        priority=row['priority']
                    ))
                
                return operations
                
        except Exception as e:
            self.logger.error(f"获取最近操作失败: {e}")
            return []


# 全局操作状态管理器实例
_operation_state_manager = None


def get_operation_state_manager() -> OperationStateManager:
    """获取全局操作状态管理器实例"""
    global _operation_state_manager
    
    if _operation_state_manager is None:
        _operation_state_manager = OperationStateManager()
    
    return _operation_state_manager