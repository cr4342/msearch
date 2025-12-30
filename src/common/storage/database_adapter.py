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
        self.db_path = self.config_manager.get(
            "database.sqlite.path", "./data/msearch.db")

        # 确保数据库目录存在
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        # 初始化数据库
        self._initialize_database()

        self.logger.info(f"数据库适配器初始化完成: {self.db_path}")

    def get_connection(self):
        """获取数据库连接"""
        timeout = self.config_manager.get("database.sqlite.timeout", 30)
        return sqlite3.connect(self.db_path, timeout=timeout)

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
                        can_delete BOOLEAN DEFAULT 0,
                        file_category TEXT DEFAULT '',
                        source_file_id TEXT
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
                        milvus_point_id TEXT,
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
                        has_audio BOOLEAN DEFAULT 0,
                        frame_count INTEGER DEFAULT 0,
                        created_at REAL NOT NULL
                    )
                """)

                # 创建文件关系表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS file_relationships (
                        id TEXT PRIMARY KEY,
                        source_file_id TEXT NOT NULL,
                        derived_file_id TEXT NOT NULL,
                        relationship_type TEXT NOT NULL,
                        metadata TEXT,
                        created_at REAL NOT NULL,
                        FOREIGN KEY (source_file_id) REFERENCES files (id),
                        FOREIGN KEY (derived_file_id) REFERENCES files (id)
                    )
                """)

                # 创建人物表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS persons (
                        id TEXT PRIMARY KEY,
                        name TEXT UNIQUE NOT NULL,
                        aliases TEXT,
                        description TEXT,
                        created_at REAL NOT NULL,
                        updated_at REAL NOT NULL
                    )
                """)

                # 创建人物向量表（用于人脸识别的特征向量存储）
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS person_embeddings (
                        id TEXT PRIMARY KEY,
                        person_id TEXT NOT NULL,
                        embedding BLOB NOT NULL,
                        created_at REAL NOT NULL,
                        FOREIGN KEY (person_id) REFERENCES persons (id)
                    )
                """)

                # 创建文件人脸表
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

                # 创建索引
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_files_path ON files(file_path)")
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_files_status ON files(status)")
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)")
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_tasks_file_id ON tasks(file_id)")
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_vectors_file_id ON vectors(file_id)")
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_media_segments_file_id ON media_segments(file_id)")
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_video_segments_file_uuid ON video_segments(file_uuid)")
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_video_segments_start_time ON video_segments(start_time)")
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_video_segments_end_time ON video_segments(end_time)")
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_file_relationships_source ON file_relationships(source_file_id)")
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_file_relationships_derived ON file_relationships(derived_file_id)")
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_file_faces_file_id ON file_faces(file_id)")
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_file_faces_person_id ON file_faces(person_id)")
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_file_faces_timestamp ON file_faces(timestamp)")

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
                        file_hash, created_at, modified_at, status, can_delete,
                        file_category, source_file_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    file_info.get('can_delete', False),
                    file_info.get('file_category', ''),
                    file_info.get('source_file_id')
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
                set_clause = ", ".join(
                    [f"{key} = ?" for key in updates.keys()])
                values = list(updates.values()) + [file_id]

                cursor.execute(
                    f"UPDATE files SET {set_clause} WHERE id = ?", values)

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

                # 处理字段名称差异（测试使用'hash'而不是'file_hash'）
                updates_copy = updates.copy()
                if 'hash' in updates_copy:
                    updates_copy['file_hash'] = updates_copy.pop('hash')

                # 构建更新语句
                set_clause = ", ".join(
                    [f"{key} = ?" for key in updates_copy.keys()])
                values = list(updates_copy.values()) + [file_path]

                cursor.execute(
                    f"UPDATE files SET {set_clause} WHERE file_path = ?", values)

                if cursor.rowcount == 0:
                    # 文件不存在，插入新记录
                    updates_copy['file_path'] = file_path
                    if 'id' not in updates_copy:
                        updates_copy['id'] = str(uuid.uuid4())
                    return await self.insert_file(updates_copy)

                # 获取文件ID
                cursor.execute(
                    "SELECT id FROM files WHERE file_path = ?", (file_path,))
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

                cursor.execute(
                    "SELECT * FROM files WHERE file_path = ?", (file_path,))
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

                cursor.execute(
                    "SELECT * FROM files WHERE file_path = ?", (file_path,))
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
                cursor.execute(
                    "DELETE FROM vectors WHERE file_id = ?", (file_id,))

                # 删除相关的媒体片段记录
                cursor.execute(
                    "DELETE FROM media_segments WHERE file_id = ?", (file_id,))

                # 删除相关的任务记录
                cursor.execute(
                    "DELETE FROM tasks WHERE file_id = ?", (file_id,))

                # 删除相关的视频片段记录
                cursor.execute(
                    "DELETE FROM video_segments WHERE file_uuid = ?", (file_id,))

                # 删除相关的文件人脸记录
                cursor.execute(
                    "DELETE FROM file_faces WHERE file_id = ?", (file_id,))

                # 删除相关的文件关系记录
                cursor.execute(
                    "DELETE FROM file_relationships WHERE source_file_id = ? OR derived_file_id = ?", (file_id, file_id))

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
            # 生成唯一ID（如果没有提供）
            task_id = task_data.get('id', str(uuid.uuid4()))

            with self.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT INTO tasks (
                        id, file_id, task_type, status, progress, error_message,
                        created_at, updated_at, retry_count, max_retry_attempts, retry_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    task_id,
                    task_data['file_id'],
                    task_data['task_type'],
                    task_data['status'],
                    task_data.get('progress', 0),
                    task_data.get('error_message'),
                    task_data['created_at'].timestamp() if isinstance(
                        task_data['created_at'], datetime) else task_data['created_at'],
                    task_data['updated_at'].timestamp() if isinstance(
                        task_data['updated_at'], datetime) else task_data['updated_at'],
                    task_data.get('retry_count', 0),
                    task_data.get('max_retry_attempts', 3),
                    task_data.get('retry_at')
                ))

                conn.commit()

            self.logger.debug(f"任务记录插入成功: {task_id}")
            return task_id

        except Exception as e:
            self.logger.error(f"插入任务记录失败: {e}")
            raise

    async def update_task(self, task_id: str, updates: Dict[str, Any]) -> bool:
        """更新任务记录"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # 构建更新语句
                set_clause = ", ".join(
                    [f"{key} = ?" for key in updates.keys()])
                values = list(updates.values()) + [task_id]

                cursor.execute(
                    f"UPDATE tasks SET {set_clause} WHERE id = ?", values)

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

                cursor.execute(
                    "DELETE FROM tasks WHERE updated_at < ?", (cutoff_time,))
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
                        segment.get('segment_type', 'unknown'),
                        i,
                        segment.get('metadata', {}).get(
                            'start_time', 0) * 1000,  # 转换为毫秒
                        segment.get('metadata', {}).get(
                            'end_time', 0) * 1000,    # 转换为毫秒
                        segment.get('metadata', {}).get(
                            'duration', 0) * 1000,    # 转换为毫秒
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
                    segment_data['metadata'] = json.loads(
                        segment_data['metadata'])

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
                            model_name, vector_type, milvus_point_id, created_at
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

            self.logger.debug(
                f"向量结果存储成功: file_id={file_id}, 向量数量={len(vectors)}")
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
                cursor.execute("DELETE FROM file_relationships")
                cursor.execute("DELETE FROM persons")
                cursor.execute("DELETE FROM file_faces")

                conn.commit()

            self.logger.info("数据库重置完成")
            return True

        except Exception as e:
            self.logger.error(f"数据库重置失败: {e}")
            return False

    async def get_file_by_category(self, category: str) -> List[Dict[str, Any]]:
        """根据分类获取文件"""
        try:
            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute(
                    "SELECT * FROM files WHERE file_category = ?", (category,))
                results = cursor.fetchall()

            return [dict(row) for row in results]

        except Exception as e:
            self.logger.error(f"根据分类获取文件失败: {e}")
            return []

    async def create_file_relationship(self, source_file_id: str, derived_file_id: str,
                                       relationship_type: str, metadata: Dict[str, Any] = None) -> bool:
        """创建文件关系"""
        try:
            import json

            with self.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT INTO file_relationships (
                        id, source_file_id, derived_file_id, relationship_type,
                        metadata, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    str(uuid.uuid4()),
                    source_file_id,
                    derived_file_id,
                    relationship_type,
                    json.dumps(metadata) if metadata else None,
                    datetime.now().timestamp()
                ))

                conn.commit()

            return True

        except Exception as e:
            self.logger.error(f"创建文件关系失败: {e}")
            return False

    async def get_file_relationships(self, file_id: str) -> List[Dict[str, Any]]:
        """获取文件关系"""
        try:
            import json

            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT * FROM file_relationships 
                    WHERE source_file_id = ? OR derived_file_id = ?
                """, (file_id, file_id))
                results = cursor.fetchall()

                relationships = []
                for row in results:
                    row_dict = dict(row)
                    if row_dict['metadata']:
                        row_dict['metadata'] = json.loads(row_dict['metadata'])
                    relationships.append(row_dict)

            return relationships

        except Exception as e:
            self.logger.error(f"获取文件关系失败: {e}")
            return []

    async def get_derived_files(self, source_file_id: str) -> List[Dict[str, Any]]:
        """获取派生文件"""
        try:
            import json

            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT * FROM file_relationships 
                    WHERE source_file_id = ?
                """, (source_file_id,))
                results = cursor.fetchall()

                derived_files = []
                for row in results:
                    row_dict = dict(row)
                    if row_dict['metadata']:
                        row_dict['metadata'] = json.loads(row_dict['metadata'])
                    derived_files.append(row_dict)

            return derived_files

        except Exception as e:
            self.logger.error(f"获取派生文件失败: {e}")
            return []

    async def insert_video_segment(self, segment_data: Dict[str, Any]) -> str:
        """插入视频片段"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                segment_id = segment_data.get('segment_id', str(uuid.uuid4()))

                cursor.execute("""
                    INSERT INTO video_segments (
                        segment_id, file_uuid, segment_index, start_time,
                        end_time, duration, scene_boundary, has_audio, frame_count, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    segment_id,
                    segment_data['file_uuid'],
                    segment_data['segment_index'],
                    segment_data['start_time'],
                    segment_data['end_time'],
                    segment_data['duration'],
                    segment_data.get('scene_boundary', False),
                    segment_data.get('has_audio', False),
                    segment_data.get('frame_count', 0),
                    datetime.now().timestamp()
                ))

                conn.commit()

            return segment_id

        except Exception as e:
            self.logger.error(f"插入视频片段失败: {e}")
            raise

    async def get_video_segments_by_file(self, file_id: str) -> List[Dict[str, Any]]:
        """获取视频片段"""
        try:
            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT * FROM video_segments 
                    WHERE file_uuid = ? 
                    ORDER BY segment_index ASC
                """, (file_id,))
                results = cursor.fetchall()

            return [dict(row) for row in results]

        except Exception as e:
            self.logger.error(f"获取视频片段失败: {e}")
            return []

    async def get_video_segment_by_file_and_time(self, file_id: str, timestamp: float) -> Optional[Dict[str, Any]]:
        """根据时间戳获取视频片段"""
        try:
            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT * FROM video_segments 
                    WHERE file_uuid = ? AND start_time <= ? AND end_time >= ?
                """, (file_id, timestamp, timestamp))
                result = cursor.fetchone()

            return dict(result) if result else None

        except Exception as e:
            self.logger.error(f"获取视频片段失败: {e}")
            return None

    async def get_video_segment_by_segment_id(self, segment_id: str) -> Optional[Dict[str, Any]]:
        """根据片段ID获取视频片段"""
        try:
            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute(
                    "SELECT * FROM video_segments WHERE segment_id = ?", (segment_id,))
                result = cursor.fetchone()

            return dict(result) if result else None

        except Exception as e:
            self.logger.error(f"获取视频片段失败: {e}")
            return None

    async def get_video_segments_by_time_range(self, file_id: str, start_time: float, end_time: float) -> List[Dict[str, Any]]:
        """根据时间范围获取视频片段"""
        try:
            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT * FROM video_segments 
                    WHERE file_uuid = ? AND start_time >= ? AND end_time <= ?
                    ORDER BY segment_index ASC
                """, (file_id, start_time, end_time))
                results = cursor.fetchall()

            return [dict(row) for row in results]

        except Exception as e:
            self.logger.error(f"获取视频片段失败: {e}")
            return []

    async def update_video_segment(self, segment_id: str, updates: Dict[str, Any]) -> bool:
        """更新视频片段"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # 构建更新语句
                set_clause = ", ".join(
                    [f"{key} = ?" for key in updates.keys()])
                values = list(updates.values()) + [segment_id]

                cursor.execute(
                    f"UPDATE video_segments SET {set_clause} WHERE segment_id = ?", values)

                conn.commit()

            success = cursor.rowcount > 0
            if success:
                self.logger.debug(f"视频片段更新成功: {segment_id}")

            return success

        except Exception as e:
            self.logger.error(f"更新视频片段失败: {e}")
            return False

    async def delete_video_segments(self, file_id: str) -> int:
        """删除视频片段"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    "DELETE FROM video_segments WHERE file_uuid = ?", (file_id,))
                deleted_count = cursor.rowcount

                conn.commit()

            self.logger.info(f"删除视频片段: {deleted_count} 个")
            return deleted_count

        except Exception as e:
            self.logger.error(f"删除视频片段失败: {e}")
            return 0

    async def get_video_segments_with_audio(self, file_id: str) -> List[Dict[str, Any]]:
        """获取包含音频的视频片段"""
        try:
            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT * FROM video_segments 
                    WHERE file_uuid = ? AND has_audio = 1
                    ORDER BY segment_index ASC
                """, (file_id,))
                results = cursor.fetchall()

            return [dict(row) for row in results]

        except Exception as e:
            self.logger.error(f"获取包含音频的视频片段失败: {e}")
            return []

    async def get_video_segments_with_scene_boundary(self, file_id: str) -> List[Dict[str, Any]]:
        """获取场景边界的视频片段"""
        try:
            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT * FROM video_segments 
                    WHERE file_uuid = ? AND scene_boundary = 1
                    ORDER BY segment_index ASC
                """, (file_id,))
                results = cursor.fetchall()

            return [dict(row) for row in results]

        except Exception as e:
            self.logger.error(f"获取场景边界的视频片段失败: {e}")
            return []

    async def get_video_segments_statistics(self, file_id: str) -> Dict[str, Any]:
        """获取视频片段统计信息"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # 总片段数
                cursor.execute(
                    "SELECT COUNT(*) FROM video_segments WHERE file_uuid = ?", (file_id,))
                total_segments = cursor.fetchone()[0]

                # 包含音频的片段数
                cursor.execute(
                    "SELECT COUNT(*) FROM video_segments WHERE file_uuid = ? AND has_audio = 1", (file_id,))
                audio_segments = cursor.fetchone()[0]

                # 场景边界的片段数
                cursor.execute(
                    "SELECT COUNT(*) FROM video_segments WHERE file_uuid = ? AND scene_boundary = 1", (file_id,))
                scene_boundary_segments = cursor.fetchone()[0]

                # 总时长
                cursor.execute(
                    "SELECT SUM(duration) FROM video_segments WHERE file_uuid = ?", (file_id,))
                total_duration = cursor.fetchone()[0] or 0

                # 最大和最小片段时长
                cursor.execute(
                    "SELECT MAX(duration), MIN(duration) FROM video_segments WHERE file_uuid = ?", (file_id,))
                max_min_duration = cursor.fetchone()
                max_duration = max_min_duration[0] or 0
                min_duration = max_min_duration[1] or 0

            return {
                'total_segments': total_segments,
                'audio_segments': audio_segments,
                'scene_boundary_segments': scene_boundary_segments,
                'total_duration': total_duration,
                'max_duration': max_duration,
                'min_duration': min_duration,
                'avg_duration': total_duration / total_segments if total_segments > 0 else 0
            }

        except Exception as e:
            self.logger.error(f"获取视频片段统计信息失败: {e}")
            return {}

    async def get_all_video_segments(self) -> List[Dict[str, Any]]:
        """获取所有视频片段"""
        try:
            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT * FROM video_segments 
                    ORDER BY file_uuid, segment_index ASC
                """)
                results = cursor.fetchall()

            return [dict(row) for row in results]

        except Exception as e:
            self.logger.error(f"获取所有视频片段失败: {e}")
            return []

    async def get_video_segments_by_search(self, search_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """根据搜索参数获取视频片段"""
        try:
            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                where_clauses = []
                params = []

                if search_params.get('file_uuid'):
                    where_clauses.append("file_uuid = ?")
                    params.append(search_params['file_uuid'])

                if search_params.get('scene_boundary') is not None:
                    where_clauses.append("scene_boundary = ?")
                    params.append(int(search_params['scene_boundary']))

                if search_params.get('has_audio') is not None:
                    where_clauses.append("has_audio = ?")
                    params.append(int(search_params['has_audio']))

                if search_params.get('min_duration'):
                    where_clauses.append("duration >= ?")
                    params.append(search_params['min_duration'])

                if search_params.get('max_duration'):
                    where_clauses.append("duration <= ?")
                    params.append(search_params['max_duration'])

                query = "SELECT * FROM video_segments"
                if where_clauses:
                    query += " WHERE " + " AND ".join(where_clauses)

                query += " ORDER BY file_uuid, segment_index ASC"

                cursor.execute(query, params)
                results = cursor.fetchall()

            return [dict(row) for row in results]

        except Exception as e:
            self.logger.error(f"根据搜索参数获取视频片段失败: {e}")
            return []

    async def insert_person(self, person_data: Dict[str, Any]) -> str:
        """插入人物信息"""
        try:
            import json

            with self.get_connection() as conn:
                cursor = conn.cursor()

                person_id = person_data.get('id', str(uuid.uuid4()))

                cursor.execute("""
                    INSERT INTO persons (
                        id, name, aliases, description, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    person_id,
                    person_data['name'],
                    json.dumps(person_data.get('aliases', [])),
                    person_data.get('description'),
                    datetime.now().timestamp(),
                    datetime.now().timestamp()
                ))

                conn.commit()

            return person_id

        except Exception as e:
            self.logger.error(f"插入人物信息失败: {e}")
            raise

    async def get_person_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """根据姓名获取人物信息"""
        try:
            import json

            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute("SELECT * FROM persons WHERE name = ?", (name,))
                result = cursor.fetchone()

                if result:
                    result_dict = dict(result)
                    if result_dict['aliases']:
                        result_dict['aliases'] = json.loads(
                            result_dict['aliases'])
                    return result_dict
                return None

        except Exception as e:
            self.logger.error(f"获取人物信息失败: {e}")
            return None

    async def get_person_by_id(self, person_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取人物信息"""
        try:
            import json

            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute(
                    "SELECT * FROM persons WHERE id = ?", (person_id,))
                result = cursor.fetchone()

                if result:
                    result_dict = dict(result)
                    if result_dict['aliases']:
                        result_dict['aliases'] = json.loads(
                            result_dict['aliases'])
                    return result_dict
                return None

        except Exception as e:
            self.logger.error(f"获取人物信息失败: {e}")
            return None

    async def search_persons_by_partial_name(self, partial_name: str) -> List[Dict[str, Any]]:
        """根据部分姓名搜索人物"""
        try:
            import json

            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute(
                    "SELECT * FROM persons WHERE name LIKE ?", (f"%{partial_name}%",))
                results = cursor.fetchall()

                persons = []
                for row in results:
                    row_dict = dict(row)
                    if row_dict['aliases']:
                        row_dict['aliases'] = json.loads(row_dict['aliases'])
                    persons.append(row_dict)

            return persons

        except Exception as e:
            self.logger.error(f"搜索人物信息失败: {e}")
            return []

    async def get_popular_persons(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取热门人物（按出现频率排序）"""
        try:
            import json

            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                # 先获取人脸记录中最多的人
                cursor.execute("""
                    SELECT person_id, COUNT(*) as face_count 
                    FROM file_faces 
                    WHERE person_id IS NOT NULL
                    GROUP BY person_id
                    ORDER BY face_count DESC
                    LIMIT ?
                """, (limit,))

                face_results = cursor.fetchall()

                persons = []
                for face_result in face_results:
                    cursor.execute(
                        "SELECT * FROM persons WHERE id = ?", (face_result['person_id'],))
                    person_result = cursor.fetchone()

                    if person_result:
                        person_dict = dict(person_result)
                        if person_dict['aliases']:
                            person_dict['aliases'] = json.loads(
                                person_dict['aliases'])
                        person_dict['face_count'] = face_result['face_count']
                        persons.append(person_dict)

            return persons

        except Exception as e:
            self.logger.error(f"获取热门人物失败: {e}")
            return []

    async def insert_person_embedding(self, person_id: str, embedding: "np.ndarray") -> str:
        """插入人物人脸特征向量到 person_embeddings 表。"""
        try:
            import numpy as np

            with self.get_connection() as conn:
                cursor = conn.cursor()

                embedding_id = str(uuid.uuid4())
                # 统一使用 float32 存储
                embedding_bytes = np.asarray(
                    embedding, dtype=np.float32).tobytes()

                cursor.execute(
                    """
                    INSERT INTO person_embeddings (
                        id, person_id, embedding, created_at
                    ) VALUES (?, ?, ?, ?)
                    """,
                    (
                        embedding_id,
                        person_id,
                        embedding_bytes,
                        datetime.now().timestamp(),
                    ),
                )

                conn.commit()

            return embedding_id

        except Exception as e:  # noqa: BLE001
            self.logger.error(f"插入人物向量失败: {e}")
            raise

    async def get_all_person_embeddings(self) -> List[Dict[str, Any]]:
        """获取所有人物的特征向量列表。"""
        try:
            import json
            import numpy as np

            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT pe.person_id, pe.embedding, p.name, p.aliases
                    FROM person_embeddings pe
                    JOIN persons p ON p.id = pe.person_id
                    """
                )
                rows = cursor.fetchall()

            embeddings: List[Dict[str, Any]] = []
            for row in rows:
                row_dict = dict(row)
                # 反序列化别名
                if row_dict.get('aliases'):
                    try:
                        row_dict['aliases'] = json.loads(row_dict['aliases'])
                    except json.JSONDecodeError:
                        row_dict['aliases'] = [row_dict['aliases']]
                else:
                    row_dict['aliases'] = []

                # 将 BLOB 转为 numpy 数组
                emb_array = np.frombuffer(
                    row_dict['embedding'], dtype=np.float32)
                embeddings.append(
                    {
                        'person_id': row_dict['person_id'],
                        'name': row_dict['name'],
                        'aliases': row_dict['aliases'],
                        'embedding': emb_array,
                    }
                )

            return embeddings

        except Exception as e:  # noqa: BLE001
            self.logger.error(f"获取人物向量列表失败: {e}")
            return []

    async def insert_file_face(self, face_data: Dict[str, Any]) -> str:
        """插入文件人脸信息"""
        try:
            import json

            with self.get_connection() as conn:
                cursor = conn.cursor()

                face_id = face_data.get('id', str(uuid.uuid4()))

                cursor.execute(
                    """
                    INSERT INTO file_faces (
                        id, file_id, person_id, timestamp, confidence, bbox, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        face_id,
                        face_data['file_id'],
                        face_data.get('person_id'),
                        face_data.get('timestamp'),
                        face_data['confidence'],
                        json.dumps(face_data['bbox']),
                        datetime.now().timestamp(),
                    ),
                )

                conn.commit()

            return face_id

        except Exception as e:  # noqa: BLE001
            self.logger.error(f"插入文件人脸信息失败: {e}")
            raise

    async def get_faces_by_file(self, file_id: str) -> List[Dict[str, Any]]:
        """获取文件中的人脸信息"""
        try:
            import json

            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT * FROM file_faces 
                    WHERE file_id = ?
                    ORDER BY timestamp ASC
                """, (file_id,))
                results = cursor.fetchall()

                faces = []
                for row in results:
                    row_dict = dict(row)
                    if row_dict['bbox']:
                        row_dict['bbox'] = json.loads(row_dict['bbox'])
                    faces.append(row_dict)

            return faces

        except Exception as e:
            self.logger.error(f"获取文件人脸信息失败: {e}")
            return []

    async def get_faces_by_person(self, person_id: str) -> List[Dict[str, Any]]:
        """获取某人的所有人脸信息"""
        try:
            import json

            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT * FROM file_faces 
                    WHERE person_id = ?
                    ORDER BY timestamp ASC
                """, (person_id,))
                results = cursor.fetchall()

                faces = []
                for row in results:
                    row_dict = dict(row)
                    if row_dict['bbox']:
                        row_dict['bbox'] = json.loads(row_dict['bbox'])
                    faces.append(row_dict)

            return faces

        except Exception as e:
            self.logger.error(f"获取某人的人脸信息失败: {e}")
            return []

    async def get_deletable_files(self) -> List[Dict[str, Any]]:
        """获取可删除文件"""
        try:
            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute("SELECT * FROM files WHERE can_delete = 1")
                results = cursor.fetchall()

            return [dict(row) for row in results]

        except Exception as e:
            self.logger.error(f"获取可删除文件失败: {e}")
            return []

    async def get_temp_files_to_delete(self) -> List[Dict[str, Any]]:
        """获取可删除的临时文件"""
        try:
            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT * FROM files 
                    WHERE can_delete = 1 AND status = 'completed'
                """)
                results = cursor.fetchall()

            return [dict(row) for row in results]

        except Exception as e:
            self.logger.error(f"获取可删除的临时文件失败: {e}")
            return []

    async def mark_file_as_deleted(self, file_id: str) -> bool:
        """标记文件为已删除"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    UPDATE files 
                    SET status = 'deleted', modified_at = ?
                    WHERE id = ?
                """, (datetime.now().timestamp(), file_id))

                conn.commit()

            success = cursor.rowcount > 0
            if success:
                self.logger.debug(f"文件标记为已删除: {file_id}")

            return success

        except Exception as e:
            self.logger.error(f"标记文件为已删除失败: {e}")
            return False

    async def get_all_files(self) -> List[Dict[str, Any]]:
        """获取所有文件"""
        try:
            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute("SELECT * FROM files ORDER BY created_at DESC")
                results = cursor.fetchall()

            return [dict(row) for row in results]

        except Exception as e:
            self.logger.error(f"获取所有文件失败: {e}")
            return []

    async def get_database_stats(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                stats = {}

                # 获取文件统计
                cursor.execute("SELECT COUNT(*) FROM files")
                stats['total_files'] = cursor.fetchone()[0]

                cursor.execute(
                    "SELECT COUNT(*) FROM files WHERE status = 'completed'")
                stats['completed_files'] = cursor.fetchone()[0]

                # 获取任务统计
                cursor.execute("SELECT COUNT(*) FROM tasks")
                stats['total_tasks'] = cursor.fetchone()[0]

                # 获取向量统计
                cursor.execute("SELECT COUNT(*) FROM vectors")
                stats['total_vectors'] = cursor.fetchone()[0]

                # 获取媒体片段统计
                cursor.execute("SELECT COUNT(*) FROM media_segments")
                stats['total_segments'] = cursor.fetchone()[0]

                # 获取视频片段统计
                cursor.execute("SELECT COUNT(*) FROM video_segments")
                stats['total_video_segments'] = cursor.fetchone()[0]

                # 获取文件关系统计
                cursor.execute("SELECT COUNT(*) FROM file_relationships")
                stats['total_file_relationships'] = cursor.fetchone()[0]

                # 获取人物统计
                cursor.execute("SELECT COUNT(*) FROM persons")
                stats['total_persons'] = cursor.fetchone()[0]

                # 获取文件人脸统计
                cursor.execute("SELECT COUNT(*) FROM file_faces")
                stats['total_file_faces'] = cursor.fetchone()[0]

            return stats

        except Exception as e:
            self.logger.error(f"获取数据库统计信息失败: {e}")
            return {}

    async def get_schema_version(self) -> Dict[str, Any]:
        """获取Schema版本"""
        return {
            'version': '1.0.0',
            'last_updated': datetime.now().timestamp()
        }
