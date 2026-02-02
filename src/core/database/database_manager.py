"""
数据库管理器
负责SQLite数据库的连接、操作和管理
"""

import sqlite3
import hashlib
import json
from typing import Any, Dict, List, Optional
from pathlib import Path
import logging
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class DatabaseManager:
    """数据库管理器"""

    def __init__(self, db_path: str, enable_wal: bool = True):
        """
        初始化数据库管理器

        Args:
            db_path: 数据库文件路径
            enable_wal: 是否启用WAL模式
        """
        self.db_path = Path(db_path)
        self.enable_wal = enable_wal
        self.connection: Optional[sqlite3.Connection] = None
        self._initialize()

    def _initialize(self) -> bool:
        """初始化数据库"""
        return self.initialize()

    def initialize(self) -> bool:
        """初始化数据库"""
        try:
            # 确保数据库目录存在
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

            # 创建数据库连接
            self.connection = sqlite3.connect(
                str(self.db_path), check_same_thread=False, isolation_level=None
            )

            # 启用WAL模式
            if self.enable_wal:
                self.connection.execute("PRAGMA journal_mode=WAL")

            # 创建表
            self.create_tables()

            logger.info(f"数据库初始化成功: {self.db_path}")
            return True
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            return False

    def create_tables(self) -> None:
        """创建数据库表"""
        cursor = self.connection.cursor()

        # 文件元数据表
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS file_metadata (
                id TEXT PRIMARY KEY,
                file_path TEXT NOT NULL UNIQUE,
                file_name TEXT NOT NULL,
                file_type TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                file_hash TEXT NOT NULL,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                processed_at REAL,
                processing_status TEXT NOT NULL DEFAULT 'pending',
                metadata TEXT,
                thumbnail_path TEXT,
                preview_path TEXT,
                reference_count INTEGER DEFAULT 1
            )
        """
        )

        # 文件引用表
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS file_references (
                id TEXT PRIMARY KEY,
                file_hash TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_id TEXT NOT NULL,
                created_at REAL NOT NULL,
                FOREIGN KEY (file_id) REFERENCES file_metadata(id) ON DELETE CASCADE
            )
        """
        )

        # 视频元数据表
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS video_metadata (
                id TEXT PRIMARY KEY,
                file_id TEXT NOT NULL,
                duration REAL NOT NULL,
                width INTEGER NOT NULL,
                height INTEGER NOT NULL,
                fps REAL NOT NULL,
                codec TEXT,
                is_short_video INTEGER NOT NULL DEFAULT 0,
                total_segments INTEGER DEFAULT 0,
                created_at REAL NOT NULL,
                FOREIGN KEY (file_id) REFERENCES file_metadata(id) ON DELETE CASCADE
            )
        """
        )

        # 视频片段表
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS video_segments (
                id TEXT PRIMARY KEY,
                video_id TEXT NOT NULL,
                segment_index INTEGER NOT NULL,
                start_time REAL NOT NULL,
                end_time REAL NOT NULL,
                duration REAL NOT NULL,
                is_full_video INTEGER NOT NULL DEFAULT 0,
                frame_count INTEGER DEFAULT 0,
                key_frames TEXT,
                created_at REAL NOT NULL,
                FOREIGN KEY (video_id) REFERENCES video_metadata(id) ON DELETE CASCADE
            )
        """
        )

        # 向量时间戳映射表
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS vector_timestamp_map (
                id TEXT PRIMARY KEY,
                vector_id TEXT NOT NULL,
                file_id TEXT NOT NULL,
                segment_id TEXT,
                modality TEXT NOT NULL,
                timestamp REAL NOT NULL,
                confidence REAL DEFAULT 1.0,
                created_at REAL NOT NULL,
                FOREIGN KEY (file_id) REFERENCES file_metadata(id) ON DELETE CASCADE
            )
        """
        )

        # 创建索引
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_file_hash ON file_metadata(file_hash)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_file_status ON file_metadata(processing_status)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_ref_hash ON file_references(file_hash)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_video_file_id ON video_metadata(file_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_video_segments_video_id ON video_segments(video_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_vector_file_id ON vector_timestamp_map(file_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_vector_modality ON vector_timestamp_map(modality)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_vector_timestamp ON vector_timestamp_map(timestamp)"
        )

        self.connection.commit()
        logger.info("数据库表创建成功")

    def begin_transaction(self) -> None:
        """开始事务"""
        if self.connection:
            self.connection.execute("BEGIN")

    def commit(self) -> None:
        """提交事务"""
        if self.connection:
            self.connection.commit()

    def rollback(self) -> None:
        """回滚事务"""
        if self.connection:
            self.connection.rollback()

    def insert_file_metadata(self, metadata: Dict[str, Any]) -> str:
        """
        插入文件元数据

        Args:
            metadata: 文件元数据

        Returns:
            文件ID
        """
        try:
            file_id = metadata.get("id", str(uuid.uuid4()))
            now = datetime.now().timestamp()

            cursor = self.connection.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO file_metadata 
                (id, file_path, file_name, file_type, file_size, file_hash, 
                 created_at, updated_at, processed_at, processing_status, metadata, 
                 thumbnail_path, preview_path, reference_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    file_id,
                    metadata.get("file_path"),
                    metadata.get("file_name"),
                    metadata.get("file_type"),
                    metadata.get("file_size"),
                    metadata.get("file_hash"),
                    metadata.get("created_at", now),
                    now,
                    metadata.get("processed_at"),
                    metadata.get("processing_status", "pending"),
                    json.dumps(metadata.get("metadata", {})),
                    metadata.get("thumbnail_path"),
                    metadata.get("preview_path"),
                    metadata.get("reference_count", 1),
                ),
            )

            self.connection.commit()
            logger.debug(f"文件元数据插入成功: {file_id}")
            return file_id
        except Exception as e:
            logger.error(f"插入文件元数据失败: {e}")
            raise

    def get_file_by_path(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        根据文件路径获取文件元数据

        Args:
            file_path: 文件路径

        Returns:
            文件元数据，如果不存在则返回None
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                SELECT id, file_path, file_name, file_type, file_size, file_hash,
                       created_at, updated_at, processed_at, processing_status,
                       metadata, thumbnail_path, preview_path, reference_count
                FROM file_metadata 
                WHERE file_path = ?
            """,
                (file_path,),
            )

            row = cursor.fetchone()
            if row:
                return {
                    "id": row[0],
                    "file_path": row[1],
                    "file_name": row[2],
                    "file_type": row[3],
                    "file_size": row[4],
                    "file_hash": row[5],
                    "created_at": row[6],
                    "updated_at": row[7],
                    "processed_at": row[8],
                    "processing_status": row[9],
                    "metadata": json.loads(row[10]) if row[10] else {},
                    "thumbnail_path": row[11],
                    "preview_path": row[12],
                    "reference_count": row[13],
                }
            return None
        except Exception as e:
            logger.error(f"根据路径获取文件元数据失败: {e}")
            return None

    def get_file_metadata(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        获取文件元数据

        Args:
            file_id: 文件ID

        Returns:
            文件元数据
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                SELECT * FROM file_metadata WHERE id = ?
            """,
                (file_id,),
            )

            row = cursor.fetchone()
            if row:
                return self._row_to_dict(cursor, row)
            return None
        except Exception as e:
            logger.error(f"获取文件元数据失败: {e}")
            return None

    def update_file_metadata(self, file_id: str, updates: Dict[str, Any]) -> bool:
        """
        更新文件元数据

        Args:
            file_id: 文件ID
            updates: 更新内容

        Returns:
            是否成功
        """
        try:
            updates["updated_at"] = datetime.now().timestamp()

            set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
            values = list(updates.values())
            values.append(file_id)

            cursor = self.connection.cursor()
            cursor.execute(
                f"""
                UPDATE file_metadata SET {set_clause} WHERE id = ?
            """,
                values,
            )

            self.connection.commit()
            logger.debug(f"文件元数据更新成功: {file_id}")
            return True
        except Exception as e:
            logger.error(f"更新文件元数据失败: {e}")
            return False

    def delete_file_metadata(self, file_id: str) -> bool:
        """
        删除文件元数据

        Args:
            file_id: 文件ID

        Returns:
            是否成功
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("DELETE FROM file_metadata WHERE id = ?", (file_id,))
            self.connection.commit()
            logger.debug(f"文件元数据删除成功: {file_id}")
            return True
        except Exception as e:
            logger.error(f"删除文件元数据失败: {e}")
            return False

    def search_file_metadata(
        self, query: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        搜索文件元数据

        Args:
            query: 搜索查询
            limit: 返回数量限制

        Returns:
            文件元数据列表
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                SELECT * FROM file_metadata 
                WHERE file_name LIKE ? OR file_path LIKE ?
                LIMIT ?
            """,
                (f"%{query}%", f"%{query}%", limit),
            )

            rows = cursor.fetchall()
            return [self._row_to_dict(cursor, row) for row in rows]
        except Exception as e:
            logger.error(f"搜索文件元数据失败: {e}")
            return []

    def get_file_by_hash(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """
        根据文件哈希获取文件

        Args:
            file_hash: 文件哈希

        Returns:
            文件元数据
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                SELECT * FROM file_metadata WHERE file_hash = ?
            """,
                (file_hash,),
            )

            row = cursor.fetchone()
            if row:
                return self._row_to_dict(cursor, row)
            return None
        except Exception as e:
            logger.error(f"根据哈希获取文件失败: {e}")
            return None

    def get_files_by_status(
        self, status: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        根据状态获取文件

        Args:
            status: 处理状态
            limit: 返回数量限制

        Returns:
            文件元数据列表
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                SELECT * FROM file_metadata 
                WHERE processing_status = ?
                LIMIT ?
            """,
                (status, limit),
            )

            rows = cursor.fetchall()
            return [self._row_to_dict(cursor, row) for row in rows]
        except Exception as e:
            logger.error(f"根据状态获取文件失败: {e}")
            return []

    def update_file_status(self, file_id: str, status: str) -> bool:
        """
        更新文件状态

        Args:
            file_id: 文件ID
            status: 处理状态

        Returns:
            是否成功
        """
        return self.update_file_metadata(
            file_id,
            {
                "processing_status": status,
                "processed_at": (
                    datetime.now().timestamp() if status == "completed" else None
                ),
            },
        )

    def get_database_stats(self) -> Dict[str, Any]:
        """
        获取数据库统计信息

        Returns:
            统计信息字典
        """
        try:
            cursor = self.connection.cursor()

            # 总文件数
            cursor.execute("SELECT COUNT(*) FROM file_metadata")
            total_files = cursor.fetchone()[0]

            # 按状态统计
            cursor.execute(
                """
                SELECT processing_status, COUNT(*) 
                FROM file_metadata 
                GROUP BY processing_status
            """
            )
            status_counts = {row[0]: row[1] for row in cursor.fetchall()}

            # 按类型统计
            cursor.execute(
                """
                SELECT file_type, COUNT(*) 
                FROM file_metadata 
                GROUP BY file_type
            """
            )
            type_counts = {row[0]: row[1] for row in cursor.fetchall()}

            return {
                "total_files": total_files,
                "status_counts": status_counts,
                "type_counts": type_counts,
                "database_size": (
                    self.db_path.stat().st_size if self.db_path.exists() else 0
                ),
            }
        except Exception as e:
            logger.error(f"获取数据库统计信息失败: {e}")
            return {}

    def close(self) -> None:
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("数据库连接已关闭")

    # 基于文件哈希的去重和引用计数

    def get_or_create_file_by_hash(
        self, file_hash: str, file_path: str, metadata: Dict[str, Any]
    ) -> str:
        """
        根据文件哈希获取或创建文件记录

        Args:
            file_hash: 文件SHA256哈希
            file_path: 文件路径
            metadata: 文件元数据

        Returns:
            文件ID
        """
        # 1. 检查文件哈希是否已存在
        existing_file = self.get_file_by_hash(file_hash)

        if existing_file:
            # 2. 文件已存在，增加引用计数
            file_id = existing_file["id"]
            self.add_file_reference(file_hash, file_path)
            self.increment_reference_count(file_id)
            logger.info(f"文件已存在，增加引用: {file_id}")
            return file_id
        else:
            # 3. 文件不存在，创建新记录
            metadata["file_hash"] = file_hash
            metadata["file_path"] = file_path
            file_id = self.insert_file_metadata(metadata)

            # 4. 添加初始引用
            self.add_file_reference(file_hash, file_path)
            logger.info(f"创建新文件记录: {file_id}")
            return file_id

    def add_file_reference(self, file_hash: str, file_path: str) -> bool:
        """
        添加文件路径引用

        Args:
            file_hash: 文件哈希
            file_path: 文件路径

        Returns:
            是否成功
        """
        try:
            # 检查引用是否已存在
            cursor = self.connection.cursor()
            cursor.execute(
                """
                SELECT id FROM file_references 
                WHERE file_hash = ? AND file_path = ?
            """,
                (file_hash, file_path),
            )

            if cursor.fetchone():
                return True  # 引用已存在

            # 获取文件ID
            file_data = self.get_file_by_hash(file_hash)
            if not file_data:
                return False

            # 添加新引用
            ref_id = str(uuid.uuid4())
            now = datetime.now().timestamp()
            cursor.execute(
                """
                INSERT INTO file_references (id, file_hash, file_path, file_id, created_at)
                VALUES (?, ?, ?, ?, ?)
            """,
                (ref_id, file_hash, file_path, file_data["id"], now),
            )

            self.connection.commit()
            logger.debug(f"文件引用添加成功: {file_path}")
            return True
        except Exception as e:
            logger.error(f"添加文件引用失败: {e}")
            return False

    def remove_file_reference(self, file_hash: str, file_path: str) -> bool:
        """
        移除文件路径引用

        Args:
            file_hash: 文件哈希
            file_path: 文件路径

        Returns:
            是否成功
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                DELETE FROM file_references 
                WHERE file_hash = ? AND file_path = ?
            """,
                (file_hash, file_path),
            )

            self.connection.commit()
            logger.debug(f"文件引用移除成功: {file_path}")
            return True
        except Exception as e:
            logger.error(f"移除文件引用失败: {e}")
            return False

    def get_file_references(self, file_hash: str) -> List[str]:
        """
        获取文件的所有引用路径

        Args:
            file_hash: 文件哈希

        Returns:
            文件路径列表
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                SELECT file_path FROM file_references 
                WHERE file_hash = ?
            """,
                (file_hash,),
            )

            return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"获取文件引用失败: {e}")
            return []

    def get_reference_count(self, file_hash: str) -> int:
        """
        获取引用计数

        Args:
            file_hash: 文件哈希

        Returns:
            引用计数
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                SELECT COUNT(*) FROM file_references 
                WHERE file_hash = ?
            """,
                (file_hash,),
            )

            return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"获取引用计数失败: {e}")
            return 0

    def increment_reference_count(self, file_id: str) -> bool:
        """
        增加引用计数

        Args:
            file_id: 文件ID

        Returns:
            是否成功
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                UPDATE file_metadata 
                SET reference_count = reference_count + 1 
                WHERE id = ?
            """,
                (file_id,),
            )

            self.connection.commit()
            return True
        except Exception as e:
            logger.error(f"增加引用计数失败: {e}")
            return False

    def decrement_reference_count(self, file_id: str) -> bool:
        """
        减少引用计数

        Args:
            file_id: 文件ID

        Returns:
            是否成功
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                UPDATE file_metadata 
                SET reference_count = MAX(0, reference_count - 1) 
                WHERE id = ?
            """,
                (file_id,),
            )

            self.connection.commit()
            return True
        except Exception as e:
            logger.error(f"减少引用计数失败: {e}")
            return False

    def cleanup_orphaned_files(self) -> int:
        """
        清理无引用的文件

        Returns:
            清理的文件数量
        """
        try:
            cursor = self.connection.cursor()

            # 查找引用计数为0的文件
            cursor.execute(
                """
                SELECT id, file_path FROM file_metadata 
                WHERE reference_count = 0
            """
            )

            orphaned_files = cursor.fetchall()
            count = len(orphaned_files)

            # 删除无引用的文件
            for file_id, file_path in orphaned_files:
                cursor.execute("DELETE FROM file_metadata WHERE id = ?", (file_id,))

            self.connection.commit()
            logger.info(f"清理无引用文件: {count}个")
            return count
        except Exception as e:
            logger.error(f"清理无引用文件失败: {e}")
            return 0

    def update_file_hash(self, file_id: str, file_hash: str) -> bool:
        """
        更新文件哈希

        Args:
            file_id: 文件ID
            file_hash: 新的文件哈希

        Returns:
            是否成功
        """
        try:
            cursor = self.connection.cursor()
            now = datetime.now().timestamp()

            cursor.execute(
                """
                UPDATE file_metadata 
                SET file_hash = ?, updated_at = ?
                WHERE id = ?
            """,
                (file_hash, now, file_id),
            )

            self.connection.commit()
            logger.debug(f"文件哈希更新成功: {file_id}")
            return True
        except Exception as e:
            logger.error(f"更新文件哈希失败: {e}")
            return False

    def update_file_path(self, file_id: str, file_path: str) -> bool:
        """
        更新文件路径

        Args:
            file_id: 文件ID
            file_path: 新的文件路径

        Returns:
            是否成功
        """
        try:
            cursor = self.connection.cursor()
            now = datetime.now().timestamp()

            cursor.execute(
                """
                UPDATE file_metadata 
                SET file_path = ?, updated_at = ?
                WHERE id = ?
            """,
                (file_path, now, file_id),
            )

            self.connection.commit()
            logger.debug(f"文件路径更新成功: {file_id} -> {file_path}")
            return True
        except Exception as e:
            logger.error(f"更新文件路径失败: {e}")
            return False

    def _row_to_dict(self, cursor: sqlite3.Cursor, row: tuple) -> Dict[str, Any]:
        """
        将查询结果行转换为字典

        Args:
            cursor: 数据库游标
            row: 查询结果行

        Returns:
            字典
        """
        columns = [description[0] for description in cursor.description]
        result = {}

        for i, column in enumerate(columns):
            value = row[i]
            # 将JSON字符串转换为字典
            if column == "metadata" and value:
                try:
                    value = json.loads(value)
                except:
                    pass
            result[column] = value

        return result

    # 时间定位相关方法

    def insert_video_metadata(self, file_id: str, video_info: Dict[str, Any]) -> str:
        """
        插入视频元数据

        Args:
            file_id: 文件ID
            video_info: 视频信息

        Returns:
            视频元数据ID
        """
        try:
            video_id = str(uuid.uuid4())
            now = datetime.now().timestamp()

            cursor = self.connection.cursor()
            cursor.execute(
                """
                INSERT INTO video_metadata 
                (id, file_id, duration, width, height, fps, codec, is_short_video, total_segments, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    video_id,
                    file_id,
                    video_info.get("duration", 0),
                    video_info.get("width", 0),
                    video_info.get("height", 0),
                    video_info.get("fps", 0),
                    video_info.get("codec", ""),
                    1 if video_info.get("is_short_video", False) else 0,
                    video_info.get("total_segments", 0),
                    now,
                ),
            )

            self.connection.commit()
            logger.debug(f"视频元数据插入成功: {video_id}")
            return video_id
        except Exception as e:
            logger.error(f"插入视频元数据失败: {e}")
            raise

    def get_video_metadata(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        获取视频元数据

        Args:
            file_id: 文件ID

        Returns:
            视频元数据
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                SELECT * FROM video_metadata WHERE file_id = ?
            """,
                (file_id,),
            )

            row = cursor.fetchone()
            if row:
                return self._row_to_dict(cursor, row)
            return None
        except Exception as e:
            logger.error(f"获取视频元数据失败: {e}")
            return None

    def insert_video_segment(self, video_id: str, segment_info: Dict[str, Any]) -> str:
        """
        插入视频片段

        Args:
            video_id: 视频元数据ID
            segment_info: 片段信息

        Returns:
            片段ID
        """
        try:
            segment_id = str(uuid.uuid4())
            now = datetime.now().timestamp()

            cursor = self.connection.cursor()
            cursor.execute(
                """
                INSERT INTO video_segments 
                (id, video_id, segment_index, start_time, end_time, duration, is_full_video, frame_count, key_frames, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    segment_id,
                    video_id,
                    segment_info.get("segment_index", 0),
                    segment_info.get("start_time", 0),
                    segment_info.get("end_time", 0),
                    segment_info.get("duration", 0),
                    1 if segment_info.get("is_full_video", False) else 0,
                    segment_info.get("frame_count", 0),
                    json.dumps(segment_info.get("key_frames", [])),
                    now,
                ),
            )

            self.connection.commit()
            logger.debug(f"视频片段插入成功: {segment_id}")
            return segment_id
        except Exception as e:
            logger.error(f"插入视频片段失败: {e}")
            raise

    def get_video_segments(self, video_id: str) -> List[Dict[str, Any]]:
        """
        获取视频的所有片段

        Args:
            video_id: 视频元数据ID

        Returns:
            片段列表
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                SELECT * FROM video_segments 
                WHERE video_id = ? 
                ORDER BY segment_index
            """,
                (video_id,),
            )

            rows = cursor.fetchall()
            return [self._row_to_dict(cursor, row) for row in rows]
        except Exception as e:
            logger.error(f"获取视频片段失败: {e}")
            return []

    def insert_vector_timestamp(
        self,
        vector_id: str,
        file_id: str,
        segment_id: str,
        modality: str,
        timestamp: float,
        confidence: float = 1.0,
    ) -> str:
        """
        插入向量时间戳映射

        Args:
            vector_id: 向量ID
            file_id: 文件ID
            segment_id: 片段ID
            modality: 模态
            timestamp: 时间戳
            confidence: 置信度

        Returns:
            映射ID
        """
        try:
            map_id = str(uuid.uuid4())
            now = datetime.now().timestamp()

            cursor = self.connection.cursor()
            cursor.execute(
                """
                INSERT INTO vector_timestamp_map 
                (id, vector_id, file_id, segment_id, modality, timestamp, confidence, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    map_id,
                    vector_id,
                    file_id,
                    segment_id,
                    modality,
                    timestamp,
                    confidence,
                    now,
                ),
            )

            self.connection.commit()
            logger.debug(f"向量时间戳映射插入成功: {map_id}")
            return map_id
        except Exception as e:
            logger.error(f"插入向量时间戳映射失败: {e}")
            raise

    def get_vector_timestamp(self, vector_id: str) -> Optional[Dict[str, Any]]:
        """
        获取向量对应的时间戳

        Args:
            vector_id: 向量ID

        Returns:
            时间戳信息
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                SELECT * FROM vector_timestamp_map 
                WHERE vector_id = ?
            """,
                (vector_id,),
            )

            row = cursor.fetchone()
            if row:
                return self._row_to_dict(cursor, row)
            return None
        except Exception as e:
            logger.error(f"获取向量时间戳失败: {e}")
            return None

    def get_vectors_by_time_range(
        self,
        file_id: str,
        start_time: float,
        end_time: float,
        modality: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        获取指定时间范围内的向量

        Args:
            file_id: 文件ID
            start_time: 开始时间
            end_time: 结束时间
            modality: 模态筛选（可选）

        Returns:
            向量时间戳映射列表
        """
        try:
            cursor = self.connection.cursor()

            if modality:
                cursor.execute(
                    """
                    SELECT * FROM vector_timestamp_map 
                    WHERE file_id = ? AND timestamp >= ? AND timestamp <= ? AND modality = ?
                    ORDER BY timestamp
                """,
                    (file_id, start_time, end_time, modality),
                )
            else:
                cursor.execute(
                    """
                    SELECT * FROM vector_timestamp_map 
                    WHERE file_id = ? AND timestamp >= ? AND timestamp <= ?
                    ORDER BY timestamp
                """,
                    (file_id, start_time, end_time),
                )

            rows = cursor.fetchall()
            return [self._row_to_dict(cursor, row) for row in rows]
        except Exception as e:
            logger.error(f"获取时间范围内向量失败: {e}")
            return []

    def get_video_timestamp_by_vector(self, vector_id: str) -> Optional[float]:
        """
        根据向量ID获取视频时间戳

        Args:
            vector_id: 向量ID

        Returns:
            时间戳
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                SELECT timestamp FROM vector_timestamp_map 
                WHERE vector_id = ? AND modality IN ('video', 'image')
                LIMIT 1
            """,
                (vector_id,),
            )

            row = cursor.fetchone()
            if row:
                return row[0]
            return None
        except Exception as e:
            logger.error(f"获取视频时间戳失败: {e}")
            return None

    def get_video_timestamps_by_file(self, file_id: str) -> List[Dict[str, Any]]:
        """
        获取文件的所有视频时间戳

        Args:
            file_id: 文件ID

        Returns:
            时间戳列表
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                SELECT vector_id, timestamp, segment_id, confidence 
                FROM vector_timestamp_map 
                WHERE file_id = ? AND modality IN ('video', 'image')
                ORDER BY timestamp
            """,
                (file_id,),
            )

            return [
                {
                    "vector_id": row[0],
                    "timestamp": row[1],
                    "segment_id": row[2],
                    "confidence": row[3],
                }
                for row in cursor.fetchall()
            ]
        except Exception as e:
            logger.error(f"获取文件视频时间戳失败: {e}")
            return []

    def delete_vector_timestamps(self, file_id: str) -> bool:
        """
        删除文件的所有向量时间戳映射

        Args:
            file_id: 文件ID

        Returns:
            是否成功
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                DELETE FROM vector_timestamp_map 
                WHERE file_id = ?
            """,
                (file_id,),
            )

            self.connection.commit()
            logger.debug(f"删除文件向量时间戳映射成功: {file_id}")
            return True
        except Exception as e:
            logger.error(f"删除文件向量时间戳映射失败: {e}")
            return False

    def clear_database(self) -> bool:
        """
        清空数据库中所有表的数据

        Returns:
            是否成功
        """
        try:
            cursor = self.connection.cursor()

            # 禁用外键约束检查，以便安全地清空表
            cursor.execute("PRAGMA foreign_keys=OFF")

            # 按正确顺序清空表（先清空子表，再清空主表）
            tables = [
                "vector_timestamp_map",  # 依赖file_metadata
                "video_segments",  # 依赖video_metadata
                "video_metadata",  # 依赖file_metadata
                "file_references",  # 依赖file_metadata
                "file_metadata",  # 主表
            ]

            for table in tables:
                cursor.execute(f"DELETE FROM {table}")
                logger.debug(f"清空表成功: {table}")

            # 重新启用外键约束检查
            cursor.execute("PRAGMA foreign_keys=ON")

            self.connection.commit()
            logger.info("数据库已清空")
            return True
        except Exception as e:
            logger.error(f"清空数据库失败: {e}")
            # 确保外键约束检查被重新启用
            try:
                cursor = self.connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
            except:
                pass
            return False

    def get_thumbnail_by_path(self, file_path: str) -> Optional[str]:
        """
        根据文件路径获取缩略图路径

        Args:
            file_path: 文件路径

        Returns:
            缩略图路径，如果不存在则返回None
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                SELECT thumbnail_path 
                FROM file_metadata 
                WHERE file_path = ?
            """,
                (file_path,),
            )

            row = cursor.fetchone()
            if row:
                return row[0]
            return None
        except Exception as e:
            logger.error(f"获取缩略图路径失败: {e}")
            return None

    def get_preview_by_path(self, file_path: str) -> Optional[str]:
        """
        根据文件路径获取预览图路径

        Args:
            file_path: 文件路径

        Returns:
            预览图路径，如果不存在则返回None
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                SELECT preview_path 
                FROM file_metadata 
                WHERE file_path = ?
            """,
                (file_path,),
            )

            row = cursor.fetchone()
            if row:
                return row[0]
            return None
        except Exception as e:
            logger.error(f"获取预览图路径失败: {e}")
            return None

    def get_total_files(self) -> int:
        """
        获取总文件数

        Returns:
            文件总数
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM file_metadata")
            count = cursor.fetchone()[0]
            return count
        except Exception as e:
            logger.error(f"获取总文件数失败: {e}")
            return 0

    def get_indexed_files(self) -> int:
        """
        获取已索引文件数

        Returns:
            已索引文件数
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                'SELECT COUNT(*) FROM file_metadata WHERE processing_status = "completed"'
            )
            count = cursor.fetchone()[0]
            return count
        except Exception as e:
            logger.error(f"获取已索引文件数失败: {e}")
            return 0

    def get_all_files(self) -> List[Dict[str, Any]]:
        """
        获取所有文件

        Returns:
            文件列表
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "SELECT id, file_path, file_name, file_type FROM file_metadata"
            )
            files = []
            for row in cursor.fetchall():
                files.append(
                    {
                        "id": row[0],
                        "file_path": row[1],
                        "file_name": row[2],
                        "file_type": row[3],
                    }
                )
            return files
        except Exception as e:
            logger.error(f"获取所有文件失败: {e}")
            return []
