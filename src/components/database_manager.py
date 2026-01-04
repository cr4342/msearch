"""
数据库管理器
直接使用 SQLite API 进行数据库操作
"""
import asyncio
import logging
import sqlite3
from typing import List, Dict, Any, Optional
from pathlib import Path

from src.core.config_manager import ConfigManager


class DatabaseManager:
    """数据库管理器 - 直接使用 SQLite API"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        
        # 数据库路径
        self.db_path = self.config_manager.get("database.sqlite_path", "data/database/msearch.db")
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # 连接池大小
        self.connection_pool_size = self.config_manager.get_int("database.connection_pool_size", 5)
        
        # 连接池
        self.connections = []
        
        # 运行状态
        self.is_running = False
        
        self.logger.info(f"数据库管理器初始化完成，路径: {self.db_path}")
    
    async def start(self):
        """启动数据库管理器"""
        self.logger.info("启动数据库管理器")
        
        # 初始化数据库表
        await self._initialize_database()
        
        self.is_running = True
        self.logger.info("数据库管理器启动完成")
    
    async def stop(self):
        """停止数据库管理器"""
        self.logger.info("停止数据库管理器")
        
        # 关闭所有数据库连接
        for conn in self.connections:
            try:
                conn.close()
            except:
                pass
        
        self.connections = []
        self.is_running = False
        self.logger.info("数据库管理器已停止")
    
    def _get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row  # 使结果可以通过列名访问
        return conn
    
    async def _initialize_database(self):
        """初始化数据库表"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # 创建 files 表 - 文件元数据
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS files (
                        id TEXT PRIMARY KEY,
                        file_path TEXT NOT NULL UNIQUE,
                        file_name TEXT NOT NULL,
                        file_type TEXT NOT NULL,
                        file_size INTEGER NOT NULL,
                        file_hash TEXT NOT NULL,
                        created_at REAL NOT NULL,
                        indexed_at REAL,
                        status TEXT DEFAULT 'pending',
                        metadata TEXT
                    )
                """)
                
                # 创建 video_segments 表 - 视频切片信息
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS video_segments (
                        id TEXT PRIMARY KEY,
                        file_id TEXT NOT NULL,
                        segment_index INTEGER NOT NULL,
                        start_time REAL NOT NULL,
                        end_time REAL NOT NULL,
                        duration REAL NOT NULL,
                        scene_boundary BOOLEAN DEFAULT 0,
                        has_audio BOOLEAN DEFAULT 0,
                        frame_count INTEGER DEFAULT 0,
                        created_at REAL NOT NULL,
                        FOREIGN KEY (file_id) REFERENCES files (id)
                    )
                """)
                
                # 创建 tasks 表 - 处理任务
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS tasks (
                        id TEXT PRIMARY KEY,
                        file_path TEXT NOT NULL,
                        task_type TEXT NOT NULL,
                        status TEXT DEFAULT 'pending',
                        progress INTEGER DEFAULT 0,
                        created_at REAL NOT NULL,
                        updated_at REAL NOT NULL,
                        error_message TEXT,
                        retry_count INTEGER DEFAULT 0,
                        max_retries INTEGER DEFAULT 5
                    )
                """)
                
                # 创建 persons 表 - 人物信息
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS persons (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL UNIQUE,
                        aliases TEXT,
                        description TEXT,
                        created_at REAL NOT NULL,
                        updated_at REAL NOT NULL
                    )
                """)
                
                # 创建 file_faces 表 - 人脸检测结果
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS file_faces (
                        id TEXT PRIMARY KEY,
                        file_id TEXT NOT NULL,
                        person_id TEXT,
                        timestamp REAL,
                        confidence REAL NOT NULL,
                        bbox TEXT NOT NULL,
                        created_at REAL NOT NULL,
                        FOREIGN KEY (file_id) REFERENCES files (id),
                        FOREIGN KEY (person_id) REFERENCES persons (id)
                    )
                """)
                
                # 创建索引以提高查询性能
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_path ON files(file_path)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_status ON files(status)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_video_segments_file_id ON video_segments(file_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_file_faces_file_id ON file_faces(file_id)")
                
                conn.commit()
                
            self.logger.info("数据库表结构初始化完成")
        except Exception as e:
            self.logger.error(f"数据库初始化失败: {e}")
            raise
    
    async def insert_file(self, file_info: Dict[str, Any]) -> str:
        """插入文件元数据"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO files 
                    (id, file_path, file_name, file_type, file_size, file_hash, created_at, status, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    file_info.get('id'),
                    file_info['file_path'],
                    file_info['file_name'],
                    file_info['file_type'],
                    file_info['file_size'],
                    file_info['file_hash'],
                    file_info['created_at'],
                    file_info.get('status', 'pending'),
                    file_info.get('metadata', '{}')
                ))
                
                conn.commit()
                
            self.logger.debug(f"插入文件记录: {file_info['file_path']}")
            return file_info.get('id')
        except Exception as e:
            self.logger.error(f"插入文件记录失败: {e}")
            raise
    
    async def get_file(self, file_id: str) -> Optional[Dict[str, Any]]:
        """获取文件记录"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM files WHERE id = ?", (file_id,))
                row = cursor.fetchone()
                
            if row:
                return dict(row)
            return None
        except Exception as e:
            self.logger.error(f"获取文件记录失败: {e}")
            return None
    
    async def get_file_by_path(self, file_path: str) -> Optional[Dict[str, Any]]:
        """根据路径获取文件记录"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM files WHERE file_path = ?", (file_path,))
                row = cursor.fetchone()
                
            if row:
                return dict(row)
            return None
        except Exception as e:
            self.logger.error(f"获取文件记录失败: {e}")
            return None
    
    async def update_file_status(self, file_path: str, status: str) -> bool:
        """更新文件状态"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute(
                    "UPDATE files SET status = ?, updated_at = ? WHERE file_path = ?",
                    (status, asyncio.get_event_loop().time(), file_path)
                )
                
                conn.commit()
                
            success = cursor.rowcount > 0
            if success:
                self.logger.debug(f"更新文件状态: {file_path} -> {status}")
            else:
                self.logger.warning(f"未找到文件: {file_path}")
                
            return success
        except Exception as e:
            self.logger.error(f"更新文件状态失败: {e}")
            return False
    
    async def create_task(self, task_info: Dict[str, Any]) -> str:
        """创建任务记录"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                task_id = task_info.get('id', str(hash(task_info['file_path'] + str(task_info['created_at']))))
                
                cursor.execute("""
                    INSERT INTO tasks 
                    (id, file_path, task_type, status, progress, created_at, updated_at, error_message)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    task_id,
                    task_info['file_path'],
                    task_info['task_type'],
                    task_info.get('status', 'pending'),
                    task_info.get('progress', 0),
                    task_info['created_at'],
                    task_info['updated_at'],
                    task_info.get('error_message', '')
                ))
                
                conn.commit()
                
            self.logger.debug(f"创建任务: {task_id}, 文件: {task_info['file_path']}")
            return task_id
        except Exception as e:
            self.logger.error(f"创建任务失败: {e}")
            raise
    
    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务记录"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
                row = cursor.fetchone()
                
            if row:
                return dict(row)
            return None
        except Exception as e:
            self.logger.error(f"获取任务记录失败: {e}")
            return None
    
    async def update_task_status(self, task_id: str, status: str, progress: int = None, 
                                error_message: str = None) -> bool:
        """更新任务状态"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                if progress is not None:
                    cursor.execute("""
                        UPDATE tasks 
                        SET status = ?, progress = ?, updated_at = ?, error_message = ?
                        WHERE id = ?
                    """, (status, progress, asyncio.get_event_loop().time(), error_message, task_id))
                else:
                    cursor.execute("""
                        UPDATE tasks 
                        SET status = ?, updated_at = ?, error_message = ?
                        WHERE id = ?
                    """, (status, asyncio.get_event_loop().time(), error_message, task_id))
                
                conn.commit()
                
            success = cursor.rowcount > 0
            if success:
                self.logger.debug(f"更新任务状态: {task_id} -> {status}")
                
            return success
        except Exception as e:
            self.logger.error(f"更新任务状态失败: {e}")
            return False
    
    async def get_pending_tasks(self) -> List[Dict[str, Any]]:
        """获取待处理任务"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM tasks WHERE status = 'PENDING' OR status = 'PROCESSING' ORDER BY created_at ASC")
                rows = cursor.fetchall()
                
            return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"获取待处理任务失败: {e}")
            return []
    
    async def insert_video_segment(self, segment_info: Dict[str, Any]) -> str:
        """插入视频切片信息"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                segment_id = segment_info.get('id', str(hash(segment_info['file_id'] + str(segment_info['segment_index']))))
                
                cursor.execute("""
                    INSERT INTO video_segments
                    (id, file_id, segment_index, start_time, end_time, duration, scene_boundary, has_audio, frame_count, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    segment_id,
                    segment_info['file_id'],
                    segment_info['segment_index'],
                    segment_info['start_time'],
                    segment_info['end_time'],
                    segment_info['duration'],
                    segment_info.get('scene_boundary', 0),
                    segment_info.get('has_audio', 0),
                    segment_info.get('frame_count', 0),
                    segment_info['created_at']
                ))
                
                conn.commit()
                
            self.logger.debug(f"插入视频切片: {segment_id}")
            return segment_id
        except Exception as e:
            self.logger.error(f"插入视频切片失败: {e}")
            raise
    
    async def get_video_segments_by_file(self, file_id: str) -> List[Dict[str, Any]]:
        """根据文件ID获取视频切片"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM video_segments WHERE file_id = ? ORDER BY segment_index ASC", (file_id,))
                rows = cursor.fetchall()
                
            return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"获取视频切片失败: {e}")
            return []
    
    async def add_person(self, person_info: Dict[str, Any]) -> str:
        """添加人物信息"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                person_id = person_info.get('id', str(hash(person_info['name'])))
                
                cursor.execute("""
                    INSERT OR REPLACE INTO persons
                    (id, name, aliases, description, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    person_id,
                    person_info['name'],
                    person_info.get('aliases', ''),
                    person_info.get('description', ''),
                    person_info.get('created_at', asyncio.get_event_loop().time()),
                    asyncio.get_event_loop().time()
                ))
                
                conn.commit()
                
            self.logger.debug(f"添加人物: {person_info['name']}")
            return person_id
        except Exception as e:
            self.logger.error(f"添加人物失败: {e}")
            raise
    
    async def get_person_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """根据姓名获取人物信息"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM persons WHERE name = ?", (name,))
                row = cursor.fetchone()
                
            if row:
                return dict(row)
            return None
        except Exception as e:
            self.logger.error(f"获取人物信息失败: {e}")
            return None
    
    async def insert_face_detection(self, face_info: Dict[str, Any]) -> str:
        """插入人脸检测结果"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                face_id = face_info.get('id', str(hash(face_info['file_id'] + str(face_info.get('timestamp', 0)))))
                
                cursor.execute("""
                    INSERT INTO file_faces
                    (id, file_id, person_id, timestamp, confidence, bbox, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    face_id,
                    face_info['file_id'],
                    face_info.get('person_id'),
                    face_info.get('timestamp'),
                    face_info['confidence'],
                    str(face_info['bbox']) if isinstance(face_info['bbox'], (list, tuple)) else face_info['bbox'],
                    face_info.get('created_at', asyncio.get_event_loop().time())
                ))
                
                conn.commit()
                
            self.logger.debug(f"插入人脸检测结果: {face_id}")
            return face_id
        except Exception as e:
            self.logger.error(f"插入人脸检测结果失败: {e}")
            raise
    
    async def get_faces_by_file(self, file_id: str) -> List[Dict[str, Any]]:
        """根据文件ID获取人脸检测结果"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM file_faces WHERE file_id = ?", (file_id,))
                rows = cursor.fetchall()
                
            return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"获取人脸检测结果失败: {e}")
            return []
    
    async def get_all_files(self) -> List[Dict[str, Any]]:
        """获取所有文件记录"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM files ORDER BY created_at DESC")
                rows = cursor.fetchall()
                
            return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"获取所有文件记录失败: {e}")
            return []