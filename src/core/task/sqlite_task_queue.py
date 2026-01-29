"""
SQLite任务队列管理器

使用SQLite实现持久化任务队列，支持：
- 任务持久化
- 任务优先级
- 任务状态跟踪
- 任务依赖关系
- 重试机制
"""

import sqlite3
import json
import logging
import threading
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class TaskType(Enum):
    """任务类型"""
    FILE_SCAN = "file_scan"
    FILE_PREPROCESS = "file_preprocess"
    FILE_EMBED = "file_embed"
    THUMBNAIL_GENERATE = "thumbnail_generate"
    PREVIEW_GENERATE = "preview_generate"
    SEARCH = "search"


@dataclass
class Task:
    """任务数据结构"""
    id: str
    task_type: str
    task_data: Dict[str, Any]
    priority: int
    status: str
    created_at: float
    updated_at: float
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    retries: int = 0
    max_retries: int = 3
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """从字典创建"""
        return cls(**data)


class SQLiteTaskQueue:
    """SQLite任务队列管理器"""
    
    def __init__(self, db_path: str, max_size: int = 10000):
        """
        初始化任务队列
        
        Args:
            db_path: SQLite数据库文件路径
            max_size: 队列最大长度
        """
        self.db_path = db_path
        self.max_size = max_size
        self._lock = threading.Lock()
        self._init_db()
        
    def _init_db(self):
        """初始化数据库"""
        logger.info(f"初始化任务队列数据库: {self.db_path}")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建任务队列表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS task_queue (
                id TEXT PRIMARY KEY,
                task_type TEXT NOT NULL,
                task_data TEXT NOT NULL,
                priority INTEGER NOT NULL,
                status TEXT NOT NULL,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                started_at REAL,
                completed_at REAL,
                retries INTEGER DEFAULT 0,
                max_retries INTEGER DEFAULT 3,
                error_message TEXT
            )
        ''')
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_priority ON task_queue(priority, status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON task_queue(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_created_at ON task_queue(created_at)')
        
        conn.commit()
        conn.close()
        
        logger.info("任务队列数据库初始化完成")
    
    def add_task(self, task: Task) -> bool:
        """
        添加任务到队列
        
        Args:
            task: 任务对象
            
        Returns:
            是否添加成功
        """
        with self._lock:
            try:
                # 检查队列大小
                if self._get_queue_size() >= self.max_size:
                    logger.warning(f"任务队列已满 (max_size={self.max_size})")
                    return False
                
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO task_queue 
                    (id, task_type, task_data, priority, status, created_at, updated_at, max_retries)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    task.id,
                    task.task_type,
                    json.dumps(task.task_data),
                    task.priority,
                    task.status,
                    task.created_at,
                    task.updated_at,
                    task.max_retries
                ))
                
                conn.commit()
                conn.close()
                
                logger.debug(f"任务已添加到队列: {task.id} (type={task.task_type}, priority={task.priority})")
                return True
                
            except sqlite3.IntegrityError:
                logger.warning(f"任务已存在: {task.id}")
                return False
            except Exception as e:
                logger.error(f"添加任务失败: {e}")
                return False
    
    def get_next_task(self, task_type: Optional[str] = None) -> Optional[Task]:
        """
        获取下一个待处理任务
        
        Args:
            task_type: 可选的任务类型过滤
            
        Returns:
            任务对象，如果没有则返回None
        """
        with self._lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                if task_type:
                    cursor.execute('''
                        SELECT * FROM task_queue 
                        WHERE status = ? AND task_type = ?
                        ORDER BY priority DESC, created_at ASC
                        LIMIT 1
                    ''', (TaskStatus.PENDING.value, task_type))
                else:
                    cursor.execute('''
                        SELECT * FROM task_queue 
                        WHERE status = ?
                        ORDER BY priority DESC, created_at ASC
                        LIMIT 1
                    ''', (TaskStatus.PENDING.value,))
                
                row = cursor.fetchone()
                if row:
                    # 更新任务状态为处理中
                    task_id = row[0]
                    now = time.time()
                    cursor.execute('''
                        UPDATE task_queue 
                        SET status = ?, updated_at = ?, started_at = ?
                        WHERE id = ?
                    ''', (TaskStatus.PROCESSING.value, now, now, task_id))
                    
                    conn.commit()
                    
                    # 创建任务对象
                    task_data = {
                        'id': row[0],
                        'task_type': row[1],
                        'task_data': json.loads(row[2]),
                        'priority': row[3],
                        'status': TaskStatus.PROCESSING.value,
                        'created_at': row[5],
                        'updated_at': now,
                        'started_at': now,
                        'completed_at': row[7],
                        'retries': row[8],
                        'max_retries': row[9],
                        'error_message': row[10]
                    }
                    
                    conn.close()
                    return Task.from_dict(task_data)
                
                conn.close()
                return None
                
            except Exception as e:
                logger.error(f"获取任务失败: {e}")
                return None
    
    def update_task_status(self, task_id: str, status: TaskStatus, 
                          error_message: Optional[str] = None) -> bool:
        """
        更新任务状态
        
        Args:
            task_id: 任务ID
            status: 新状态
            error_message: 错误消息（可选）
            
        Returns:
            是否更新成功
        """
        with self._lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                now = time.time()
                cursor.execute('''
                    UPDATE task_queue 
                    SET status = ?, updated_at = ?, completed_at = ?, error_message = ?
                    WHERE id = ?
                ''', (status.value, now, now if status == TaskStatus.COMPLETED else None, error_message, task_id))
                
                conn.commit()
                conn.close()
                
                logger.debug(f"任务状态已更新: {task_id} -> {status.value}")
                return True
                
            except Exception as e:
                logger.error(f"更新任务状态失败: {e}")
                return False
    
    def retry_task(self, task_id: str) -> bool:
        """
        重试任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否重试成功
        """
        with self._lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # 检查重试次数
                cursor.execute('''
                    SELECT retries, max_retries FROM task_queue WHERE id = ?
                ''', (task_id,))
                
                row = cursor.fetchone()
                if not row:
                    conn.close()
                    return False
                
                retries, max_retries = row
                if retries >= max_retries:
                    logger.warning(f"任务已达到最大重试次数: {task_id}")
                    conn.close()
                    return False
                
                # 更新重试次数和状态
                now = time.time()
                cursor.execute('''
                    UPDATE task_queue 
                    SET status = ?, updated_at = ?, retries = retries + 1,
                        started_at = NULL, completed_at = NULL
                    WHERE id = ?
                ''', (TaskStatus.PENDING.value, now, task_id))
                
                conn.commit()
                conn.close()
                
                logger.info(f"任务已重试: {task_id} (retries={retries+1}/{max_retries})")
                return True
                
            except Exception as e:
                logger.error(f"重试任务失败: {e}")
                return False
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务状态字典，如果不存在则返回None
        """
        with self._lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('SELECT * FROM task_queue WHERE id = ?', (task_id,))
                row = cursor.fetchone()
                
                conn.close()
                
                if row:
                    return {
                        'id': row[0],
                        'task_type': row[1],
                        'task_data': json.loads(row[2]),
                        'priority': row[3],
                        'status': row[4],
                        'created_at': row[5],
                        'updated_at': row[6],
                        'started_at': row[7],
                        'completed_at': row[8],
                        'retries': row[9],
                        'max_retries': row[10],
                        'error_message': row[11]
                    }
                
                return None
                
            except Exception as e:
                logger.error(f"获取任务状态失败: {e}")
                return None
    
    def get_queue_stats(self) -> Dict[str, int]:
        """
        获取队列统计信息
        
        Returns:
            统计信息字典
        """
        with self._lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # 按状态统计
                cursor.execute('''
                    SELECT status, COUNT(*) FROM task_queue GROUP BY status
                ''')
                
                stats = {}
                for row in cursor.fetchall():
                    stats[row[0]] = row[1]
                
                conn.close()
                
                return stats
                
            except Exception as e:
                logger.error(f"获取队列统计失败: {e}")
                return {}
    
    def _get_queue_size(self) -> int:
        """获取队列大小"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM task_queue')
            count = cursor.fetchone()[0]
            
            conn.close()
            return count
            
        except Exception as e:
            logger.error(f"获取队列大小失败: {e}")
            return 0
    
    def cleanup_old_tasks(self, days: int = 7) -> int:
        """
        清理旧任务
        
        Args:
            days: 保留天数
            
        Returns:
            清理的任务数量
        """
        with self._lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cutoff_time = time.time() - (days * 24 * 3600)
                cursor.execute('''
                    DELETE FROM task_queue 
                    WHERE status = ? AND completed_at < ?
                ''', (TaskStatus.COMPLETED.value, cutoff_time))
                
                deleted = cursor.rowcount
                conn.commit()
                conn.close()
                
                logger.info(f"清理了 {deleted} 个旧任务")
                return deleted
                
            except Exception as e:
                logger.error(f"清理旧任务失败: {e}")
                return 0
    
    def close(self):
        """关闭数据库连接"""
        logger.info("关闭任务队列数据库")
        # SQLite会自动管理连接，这里只是占位符