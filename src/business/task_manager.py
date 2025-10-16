"""
任务队列管理器 - 统一管理文件索引任务的生命周期
"""
import sqlite3
import uuid
import time
from typing import Dict, Any, List, Optional
from enum import Enum
import logging
import asyncio
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"      # 等待处理
    PROCESSING = "processing" # 正在处理
    COMPLETED = "completed"   # 处理完成
    FAILED = "failed"         # 处理失败
    CANCELLED = "cancelled"   # 已取消


class TaskPriority(Enum):
    """任务优先级枚举"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class Task:
    """任务数据类"""
    id: str
    file_path: str
    status: TaskStatus
    priority: TaskPriority
    created_at: float
    updated_at: float
    progress: int = 0
    error_message: Optional[str] = None
    retry_count: int = 0


class TaskManager:
    """任务队列管理器"""
    
    def __init__(self, config: Dict[str, Any], db_path: str = "data/db/tasks.db"):
        """
        初始化任务管理器
        
        Args:
            config: 配置字典
            db_path: 数据库文件路径
        """
        self.config = config
        self.db_path = db_path
        self.max_retry_count = config.get('task.max_retry_count', 3)
        self.max_concurrent_tasks = config.get('task.max_concurrent_tasks', 4)
        
        # 初始化数据库
        self._init_database()
        
        # 任务队列
        self.task_queue = asyncio.PriorityQueue()
        self.active_tasks = {}  # 正在处理的任务
        
        logger.info("任务管理器初始化完成")
    
    def _init_database(self):
        """初始化数据库表"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 创建任务表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    file_path TEXT NOT NULL,
                    status TEXT NOT NULL,
                    priority INTEGER NOT NULL,
                    progress INTEGER DEFAULT 0,
                    error_message TEXT,
                    retry_count INTEGER DEFAULT 0,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    UNIQUE(file_path, status)
                )
            ''')
            
            # 创建索引
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_tasks_file_path ON tasks(file_path)
            ''')
            
            conn.commit()
            conn.close()
            
            logger.debug("任务数据库初始化完成")
        except Exception as e:
            logger.error(f"初始化任务数据库失败: {e}")
            raise
    
    async def add_task(self, file_path: str, priority: TaskPriority = TaskPriority.NORMAL) -> str:
        """
        添加新任务到队列
        
        Args:
            file_path: 文件路径
            priority: 任务优先级
            
        Returns:
            任务ID
        """
        try:
            task_id = str(uuid.uuid4())
            now = time.time()
            
            task = Task(
                id=task_id,
                file_path=file_path,
                status=TaskStatus.PENDING,
                priority=priority,
                created_at=now,
                updated_at=now
            )
            
            # 保存到数据库
            self._save_task_to_db(task)
            
            # 添加到队列（优先级队列，数值越小优先级越高）
            await self.task_queue.put((-priority.value, task))
            
            logger.info(f"添加任务到队列: ID={task_id}, 文件={file_path}, 优先级={priority.name}")
            return task_id
            
        except Exception as e:
            logger.error(f"添加任务失败: 文件={file_path}, 错误={e}")
            raise
    
    async def get_next_task(self) -> Optional[Task]:
        """
        获取下一个待处理任务
        
        Returns:
            任务对象或None
        """
        try:
            if self.task_queue.empty():
                return None
            
            # 检查并发限制
            if len(self.active_tasks) >= self.max_concurrent_tasks:
                return None
            
            # 从队列获取任务
            _, task = await self.task_queue.get()
            
            # 更新任务状态为处理中
            task.status = TaskStatus.PROCESSING
            task.updated_at = time.time()
            self._save_task_to_db(task)
            
            # 添加到活动任务列表
            self.active_tasks[task.id] = task
            
            logger.debug(f"获取任务: ID={task.id}, 文件={task.file_path}")
            return task
            
        except Exception as e:
            logger.error(f"获取任务失败: {e}")
            return None
    
    def update_task_progress(self, task_id: str, progress: int, 
                            status: TaskStatus = None) -> bool:
        """
        更新任务进度
        
        Args:
            task_id: 任务ID
            progress: 进度百分比 (0-100)
            status: 任务状态
            
        Returns:
            是否更新成功
        """
        try:
            if task_id not in self.active_tasks:
                logger.warning(f"任务不存在或已完成: ID={task_id}")
                return False
            
            task = self.active_tasks[task_id]
            task.progress = max(0, min(100, progress))
            task.updated_at = time.time()
            
            if status:
                task.status = status
            
            self._save_task_to_db(task)
            
            logger.debug(f"更新任务进度: ID={task_id}, 进度={progress}%, 状态={task.status.value}")
            return True
            
        except Exception as e:
            logger.error(f"更新任务进度失败: ID={task_id}, 错误={e}")
            return False
    
    def complete_task(self, task_id: str, success: bool = True, 
                     error_message: str = None) -> bool:
        """
        完成任务
        
        Args:
            task_id: 任务ID
            success: 是否成功
            error_message: 错误信息（如果失败）
            
        Returns:
            是否完成成功
        """
        try:
            if task_id not in self.active_tasks:
                logger.warning(f"任务不存在或已完成: ID={task_id}")
                return False
            
            task = self.active_tasks[task_id]
            task.updated_at = time.time()
            
            if success:
                task.status = TaskStatus.COMPLETED
                task.progress = 100
                logger.info(f"任务完成: ID={task_id}, 文件={task.file_path}")
            else:
                task.status = TaskStatus.FAILED
                task.error_message = error_message
                logger.error(f"任务失败: ID={task_id}, 文件={task.file_path}, 错误={error_message}")
            
            # 保存到数据库
            self._save_task_to_db(task)
            
            # 从活动任务中移除
            del self.active_tasks[task_id]
            
            return True
            
        except Exception as e:
            logger.error(f"完成任务失败: ID={task_id}, 错误={e}")
            return False
    
    async def retry_failed_tasks(self) -> int:
        """
        重试失败的任务
        
        Returns:
            重试的任务数量
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 查询可重试的失败任务
            cursor.execute('''
                SELECT id, file_path, retry_count FROM tasks 
                WHERE status = ? AND retry_count < ?
                ORDER BY retry_count ASC, created_at ASC
            ''', (TaskStatus.FAILED.value, self.max_retry_count))
            
            failed_tasks = cursor.fetchall()
            retry_count = 0
            
            for task_id, file_path, current_retry_count in failed_tasks:
                if current_retry_count < self.max_retry_count:
                    # 更新重试次数
                    new_retry_count = current_retry_count + 1
                    cursor.execute('''
                        UPDATE tasks 
                        SET status = ?, retry_count = ?, updated_at = ?
                        WHERE id = ?
                    ''', (TaskStatus.PENDING.value, new_retry_count, time.time(), task_id))
                    
                    # 重新添加到队列
                    task = Task(
                        id=task_id,
                        file_path=file_path,
                        status=TaskStatus.PENDING,
                        priority=TaskPriority.NORMAL,
                        created_at=time.time(),
                        updated_at=time.time(),
                        retry_count=new_retry_count
                    )
                    await self.task_queue.put((-TaskPriority.NORMAL.value, task))
                    
                    logger.info(f"重试任务: ID={task_id}, 文件={file_path}, 重试次数={new_retry_count}")
                    retry_count += 1
            
            conn.commit()
            conn.close()
            
            logger.info(f"重试任务完成: 共重试{retry_count}个任务")
            return retry_count
            
        except Exception as e:
            logger.error(f"重试失败任务失败: {e}")
            return 0
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务状态信息
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, file_path, status, priority, progress, 
                       error_message, retry_count, created_at, updated_at
                FROM tasks WHERE id = ?
            ''', (task_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    'id': row[0],
                    'file_path': row[1],
                    'status': row[2],
                    'priority': TaskPriority(row[3]),
                    'progress': row[4],
                    'error_message': row[5],
                    'retry_count': row[6],
                    'created_at': row[7],
                    'updated_at': row[8]
                }
            
            return None
            
        except Exception as e:
            logger.error(f"获取任务状态失败: ID={task_id}, 错误={e}")
            return None
    
    def get_pending_tasks(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取待处理任务列表
        
        Args:
            limit: 返回任务数量限制
            
        Returns:
            任务列表
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, file_path, status, priority, progress, 
                       error_message, retry_count, created_at, updated_at
                FROM tasks 
                WHERE status = ?
                ORDER BY priority DESC, created_at ASC
                LIMIT ?
            ''', (TaskStatus.PENDING.value, limit))
            
            rows = cursor.fetchall()
            conn.close()
            
            tasks = []
            for row in rows:
                tasks.append({
                    'id': row[0],
                    'file_path': row[1],
                    'status': row[2],
                    'priority': TaskPriority(row[3]),
                    'progress': row[4],
                    'error_message': row[5],
                    'retry_count': row[6],
                    'created_at': row[7],
                    'updated_at': row[8]
                })
            
            return tasks
            
        except Exception as e:
            logger.error(f"获取待处理任务失败: {e}")
            return []
    
    def _save_task_to_db(self, task: Task):
        """
        保存任务到数据库
        
        Args:
            task: 任务对象
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO tasks 
                (id, file_path, status, priority, progress, error_message, 
                 retry_count, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                task.id,
                task.file_path,
                task.status.value,
                task.priority.value,
                task.progress,
                task.error_message,
                task.retry_count,
                task.created_at,
                task.updated_at
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"保存任务到数据库失败: ID={task.id}, 错误={e}")
            raise


# 示例使用
if __name__ == "__main__":
    import asyncio
    
    # 配置示例
    config = {
        'task.max_retry_count': 3,
        'task.max_concurrent_tasks': 4
    }
    
    # 创建任务管理器实例
    # task_manager = TaskManager(config)
    
    # 添加任务
    # task_id = asyncio.run(task_manager.add_task("/path/to/file.mp4", TaskPriority.HIGH))
    # print(f"添加任务: {task_id}")
    
    # 获取任务状态
    # status = task_manager.get_task_status(task_id)
    # print(f"任务状态: {status}")