"""
数据库适配器
统一的数据库访问接口，支持存储层可替换性
"""

import asyncio
import logging
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

from src.core.config_manager import get_config_manager


class DatabaseAdapter:
    """数据库适配器"""
    
    def __init__(self, config_manager=None):
        self.config_manager = config_manager or get_config_manager()
        self.logger = logging.getLogger(__name__)
        
        # 数据库配置
        self.db_path = self.config_manager.get("database.sqlite.path", "./data/msearch.db")
        
        # 确保数据库目录存在
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # 初始化数据库
        self._initialize_database()
        
        self.logger.info(f"数据库适配器初始化完成: {self.db_path}")
    
    def get_connection(self):
        """获取数据库连接"""
        return sqlite3.connect(self.db_path, timeout=30)
    
    def _initialize_database(self):
        """初始化数据库表结构"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 创建文件表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS files (
                        id TEXT PRIMARY KEY,
                        file_path TEXT UNIQUE NOT NULL,
                        file_name TEXT NOT NULL,
                        file_type TEXT NOT NULL,
                        file_size INTEGER NOT NULL,
                        file_hash TEXT NOT NULL,
                        created_at REAL NOT NULL,
                        modified_at REAL NOT NULL,
                        processed_at REAL,
                        status TEXT DEFAULT 'pending',
                        can_delete BOOLEAN DEFAULT 0
                    )
                """)
                
                # 创建任务表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS tasks (
                        id TEXT PRIMARY KEY,
                        file_id TEXT NOT NULL,
                        task_type TEXT NOT NULL,
                        status TEXT DEFAULT 'pending',
                        progress INTEGER DEFAULT 0,
                        error_message TEXT,
                        created_at REAL NOT NULL,
                        updated_at REAL NOT NULL,
                        retry_count INTEGER DEFAULT 0,
                        max_retry_attempts INTEGER DEFAULT 3,
                        retry_at REAL,
                        FOREIGN KEY (file_id) REFERENCES files (id)
                    )
                """)
                
                # 创建媒体片段表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS media_segments (
                        id TEXT PRIMARY KEY,
                        file_id TEXT NOT NULL,
                        segment_type TEXT NOT NULL,
                        segment_index INTEGER NOT NULL,
                        start_time_ms REAL,
                        end_time_ms REAL,
                        duration_ms REAL,
                        data_path TEXT,
                        metadata TEXT,
                        created_at REAL NOT NULL,
                        FOREIGN KEY (file_id) REFERENCES files (id)
                    )
                """)
                
                # 创建向量表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS vectors (
                        id TEXT PRIMARY KEY,
                        file_id TEXT NOT NULL,
                        task_id TEXT,
                        segment_id TEXT,
                        vector_data BLOB NOT NULL,
                        model_name TEXT NOT NULL,
                        vector_type TEXT NOT NULL,
                        qdrant_point_id TEXT,
                        created_at REAL NOT NULL,
                        FOREIGN KEY (file_id) REFERENCES files (id),
                        FOREIGN KEY (task_id) REFERENCES tasks (id),
                        FOREIGN KEY (segment_id) REFERENCES media_segments (id)
                    )
                """)
                
                # 创建视频片段表（用于时间戳精确定位）
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS video_segments (
                        segment_id TEXT PRIMARY KEY,
                        file_uuid TEXT NOT NULL,
                        segment_index INTEGER NOT NULL,
                        start_time REAL NOT NULL,
                        end_time REAL NOT NULL,
                        duration REAL NOT NULL,
                        scene_boundary BOOLEAN DEFAULT 0,
                        created_at REAL NOT NULL
                    )
                """)
                
                # 创建索引
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_path ON files(file_path)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_status ON files(status)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_file_id ON tasks(file_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_vectors_file_id ON vectors(file_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_media_segments_file_id ON media_segments(file_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_video_segments_file_uuid ON video_segments(file_uuid)")
                
                conn.commit()
                
            self.logger.info("数据库表结构初始化完成")
            
        except Exception as e:
            self.logger.error(f"数据库初始化失败: {e}")
            raise
    
    async def insert_file(self, file_info: Dict[str, Any]) -> str:
        """插入文件记录"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO files (
                        id, file_path, file_name, file_type, file_size, 
                        file_hash, created_at, modified_at, status, can_delete
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    file_info['id'],
                    file_info['file_path'],
                    file_info['file_name'],
                    file_info['file_type'],
                    file_info['file_size'],
                    file_info['file_hash'],
                    file_info['created_at'],
                    file_info['modified_at'],
                    file_info.get('status', 'pending'),
                    file_info.get('can_delete', False)
                ))
                
                conn.commit()
                
            self.logger.debug(f"文件记录插入成功: {file_info['id']}")
            return file_info['id']
            
        except sqlite3.IntegrityError:
            # 文件已存在，更新记录
            return await self.update_file_by_path(file_info['file_path'], file_info)
        except Exception as e:
            self.logger.error(f"插入文件记录失败: {e}")
            raise
    
    async def update_file(self, file_id: str, updates: Dict[str, Any]) -> bool:
        """更新文件记录"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 构建更新语句
                set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
                values = list(updates.values()) + [file_id]
                
                cursor.execute(f"UPDATE files SET {set_clause} WHERE id = ?", values)
                
                conn.commit()
                
            success = cursor.rowcount > 0
            if success:
                self.logger.debug(f"文件记录更新成功: {file_id}")
            else:
                self.logger.warning(f"文件记录不存在: {file_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"更新文件记录失败: {e}")
            return False
    
    async def update_file_by_path(self, file_path: str, updates: Dict[str, Any]) -> str:
        """根据文件路径更新文件记录"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 构建更新语句
                set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
                values = list(updates.values()) + [file_path]
                
                cursor.execute(f"UPDATE files SET {set_clause} WHERE file_path = ?", values)
                
                if cursor.rowcount == 0:
                    # 文件不存在，插入新记录
                    updates['file_path'] = file_path
                    if 'id' not in updates:
                        updates['id'] = str(uuid.uuid4())
                    return await self.insert_file(updates)
                
                # 获取文件ID
                cursor.execute("SELECT id FROM files WHERE file_path = ?", (file_path,))
                result = cursor.fetchone()
                
                conn.commit()
                
            file_id = result[0] if result else None
            if file_id:
                self.logger.debug(f"文件记录更新成功: {file_path}")
            
            return file_id
            
        except Exception as e:
            self.logger.error(f"更新文件记录失败: {e}")
            raise
    
    async def get_file(self, file_id: str) -> Optional[Dict[str, Any]]:
        """获取文件记录"""
        try:
            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM files WHERE id = ?", (file_id,))
                result = cursor.fetchone()
                
            return dict(result) if result else None
            
        except Exception as e:
            self.logger.error(f"获取文件记录失败: {e}")
            return None
    
    async def get_file_by_path(self, file_path: str) -> Optional[Dict[str, Any]]:
        """根据文件路径获取文件记录"""
        try:
            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM files WHERE file_path = ?", (file_path,))
                result = cursor.fetchone()
                
            return dict(result) if result else None
            
        except Exception as e:
            self.logger.error(f"获取文件记录失败: {e}")
            return None
    
    async def get_files_by_path(self, file_path: str) -> List[Dict[str, Any]]:
        """根据文件路径获取文件记录列表"""
        try:
            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM files WHERE file_path = ?", (file_path,))
                results = cursor.fetchall()
                
            return [dict(row) for row in results]
            
        except Exception as e:
            self.logger.error(f"获取文件记录失败: {e}")
            return []
    
    async def get_pending_files(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取待处理文件列表"""
        try:
            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM files 
                    WHERE status = 'pending' 
                    ORDER BY created_at ASC 
                    LIMIT ?
                """, (limit,))
                
                results = cursor.fetchall()
                
            return [dict(row) for row in results]
            
        except Exception as e:
            self.logger.error(f"获取待处理文件失败: {e}")
            return []
    
    async def update_file_status(self, file_id: str, status: str) -> bool:
        """更新文件状态"""
        return await self.update_file(file_id, {'status': status, 'modified_at': datetime.now().timestamp()})
    
    async def delete_file(self, file_id: str) -> bool:
        """删除文件记录"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 删除相关的向量记录
                cursor.execute("DELETE FROM vectors WHERE file_id = ?", (file_id,))
                
                # 删除相关的媒体片段记录
                cursor.execute("DELETE FROM media_segments WHERE file_id = ?", (file_id,))
                
                # 删除相关的任务记录
                cursor.execute("DELETE FROM tasks WHERE file_id = ?", (file_id,))
                
                # 删除文件记录
                cursor.execute("DELETE FROM files WHERE id = ?", (file_id,))
                
                conn.commit()
                
            success = cursor.rowcount > 0
            if success:
                self.logger.debug(f"文件记录删除成功: {file_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"删除文件记录失败: {e}")
            return False
    
    async def insert_task(self, task_data: Dict[str, Any]) -> str:
        """插入任务记录"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO tasks (
                        id, file_id, task_type, status, progress, error_message,
                        created_at, updated_at, retry_count, max_retry_attempts, retry_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    task_data['id'],
                    task_data['file_id'],
                    task_data['task_type'],
                    task_data['status'],
                    task_data.get('progress', 0),
                    task_data.get('error_message'),
                    task_data['created_at'].timestamp() if isinstance(task_data['created_at'], datetime) else task_data['created_at'],
                    task_data['updated_at'].timestamp() if isinstance(task_data['updated_at'], datetime) else task_data['updated_at'],
                    task_data.get('retry_count', 0),
                    task_data.get('max_retry_attempts', 3),
                    task_data.get('retry_at')
                ))
                
                conn.commit()
                
            self.logger.debug(f"任务记录插入成功: {task_data['id']}")
            return task_data['id']
            
        except Exception as e:
            self.logger.error(f"插入任务记录失败: {e}")
            raise
    
    async def update_task(self, task_id: str, updates: Dict[str, Any]) -> bool:
        """更新任务记录"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 构建更新语句
                set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
                values = list(updates.values()) + [task_id]
                
                cursor.execute(f"UPDATE tasks SET {set_clause} WHERE id = ?", values)
                
                conn.commit()
                
            success = cursor.rowcount > 0
            if success:
                self.logger.debug(f"任务记录更新成功: {task_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"更新任务记录失败: {e}")
            return False
    
    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务记录"""
        try:
            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
                result = cursor.fetchone()
                
            return dict(result) if result else None
            
        except Exception as e:
            self.logger.error(f"获取任务记录失败: {e}")
            return None
    
    async def get_tasks_by_status(self, status: str, limit: int = None) -> List[Dict[str, Any]]:
        """根据状态获取任务列表"""
        try:
            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                query = "SELECT * FROM tasks WHERE status = ? ORDER BY created_at ASC"
                params = [status]
                
                if limit:
                    query += " LIMIT ?"
                    params.append(limit)
                
                cursor.execute(query, params)
                results = cursor.fetchall()
                
            return [dict(row) for row in results]
            
        except Exception as e:
            self.logger.error(f"获取任务列表失败: {e}")
            return []
    
    async def get_retry_tasks(self) -> List[Dict[str, Any]]:
        """获取需要重试的任务"""
        try:
            current_time = datetime.now().timestamp()
            
            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM tasks 
                    WHERE status = 'retry' AND retry_at <= ? 
                    ORDER BY retry_at ASC
                """, (current_time,))
                
                results = cursor.fetchall()
                
            return [dict(row) for row in results]
            
        except Exception as e:
            self.logger.error(f"获取重试任务失败: {e}")
            return []
    
    async def get_task_statistics(self) -> Dict[str, int]:
        """获取任务统计信息"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT status, COUNT(*) as count 
                    FROM tasks 
                    GROUP BY status
                """)
                
                results = cursor.fetchall()
                
            return {status: count for status, count in results}
            
        except Exception as e:
            self.logger.error(f"获取任务统计失败: {e}")
            return {}
    
    async def delete_old_tasks(self, cutoff_time: float) -> int:
        """删除旧任务"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("DELETE FROM tasks WHERE updated_at < ?", (cutoff_time,))
                deleted_count = cursor.rowcount
                
                conn.commit()
                
            self.logger.info(f"删除旧任务: {deleted_count} 个")
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"删除旧任务失败: {e}")
            return 0
    
    async def store_preprocessing_result(self, file_id: str, task_id: str, processed_data: Dict[str, Any]) -> bool:
        """存储预处理结果"""
        try:
            import json
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 存储媒体片段信息
                for i, segment in enumerate(processed_data.get('segments', [])):
                    segment_id = str(uuid.uuid4())
                    
                    cursor.execute("""
                        INSERT INTO media_segments (
                            id, file_id, segment_type, segment_index,
                            start_time_ms, end_time_ms, duration_ms,
                            data_path, metadata, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        segment_id,
                        file_id,
                        segment.get('type', 'unknown'),
                        i,
                        segment.get('start_time_ms'),
                        segment.get('end_time_ms'),
                        segment.get('duration_ms'),
                        segment.get('data_path'),
                        json.dumps(segment.get('metadata', {})),
                        datetime.now().timestamp()
                    ))
                
                conn.commit()
                
            self.logger.debug(f"预处理结果存储成功: file_id={file_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"存储预处理结果失败: {e}")
            return False
    
    async def get_preprocessing_result(self, file_id: str) -> Optional[Dict[str, Any]]:
        """获取预处理结果"""
        try:
            import json
            
            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM media_segments 
                    WHERE file_id = ? 
                    ORDER BY segment_index ASC
                """, (file_id,))
                
                segments = cursor.fetchall()
                
            if not segments:
                return None
            
            processed_data = {
                'segments': []
            }
            
            for segment in segments:
                segment_data = dict(segment)
                if segment_data['metadata']:
                    segment_data['metadata'] = json.loads(segment_data['metadata'])
                
                processed_data['segments'].append(segment_data)
            
            return processed_data
            
        except Exception as e:
            self.logger.error(f"获取预处理结果失败: {e}")
            return None
    
    async def store_vectors(self, file_id: str, task_id: str, vectors: List[Any], metadata: Dict[str, Any]) -> bool:
        """存储向量结果"""
        try:
            import pickle
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                for i, vector in enumerate(vectors):
                    vector_id = str(uuid.uuid4())
                    
                    # 序列化向量数据
                    vector_blob = pickle.dumps(vector)
                    
                    cursor.execute("""
                        INSERT INTO vectors (
                            id, file_id, task_id, vector_data, 
                            model_name, vector_type, qdrant_point_id, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        vector_id,
                        file_id,
                        task_id,
                        vector_blob,
                        metadata.get('model', 'unknown'),
                        metadata.get('method', 'unknown'),
                        f"point_{file_id}_{i}",
                        datetime.now().timestamp()
                    ))
                
                conn.commit()
                
            self.logger.debug(f"向量结果存储成功: file_id={file_id}, 向量数量={len(vectors)}")
            return True
            
        except Exception as e:
            self.logger.error(f"存储向量结果失败: {e}")
            return False
    
    async def reset_database(self) -> bool:
        """重置数据库"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 清空所有表
                cursor.execute("DELETE FROM vectors")
                cursor.execute("DELETE FROM media_segments")
                cursor.execute("DELETE FROM tasks")
                cursor.execute("DELETE FROM files")
                cursor.execute("DELETE FROM video_segments")
                
                conn.commit()
                
            self.logger.info("数据库重置完成")
            return True
            
        except Exception as e:
            self.logger.error(f"数据库重置失败: {e}")
            return False