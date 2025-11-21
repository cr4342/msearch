"""
数据库管理模块
负责SQLite数据库的初始化和管理
"""

import sqlite3
import os
from pathlib import Path
from typing import Dict, Any, List
import logging

from src.core.config import get_config
from src.core.logging_config import get_logger

logger = get_logger(__name__)


class DatabaseManager:
    """SQLite数据库管理器"""
    
    def __init__(self, db_path: str = None):
        """
        初始化数据库管理器
        
        Args:
            db_path: 数据库文件路径
        """
        if db_path is None:
            config = get_config()
            # 从配置中获取数据库路径
            db_path = config.get("database", {}).get("sqlite", {}).get("path", "./data/database/msearch.db")
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """初始化数据库表结构"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 创建文件信息表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS files (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        file_path TEXT NOT NULL UNIQUE,
                        file_name TEXT NOT NULL,
                        file_hash TEXT NOT NULL,
                        file_type TEXT NOT NULL,
                        file_size INTEGER NOT NULL,
                        status TEXT NOT NULL DEFAULT 'pending',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        processed_at TIMESTAMP,
                        metadata TEXT
                    )
                """)
                
                # 创建媒体片段表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS media_segments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        file_id INTEGER NOT NULL,
                        qdrant_point_id VARCHAR(36) NOT NULL UNIQUE,
                        segment_type TEXT NOT NULL,
                        segment_index INTEGER,
                        start_time_ms INTEGER,
                        end_time_ms INTEGER,
                        keyframe_path TEXT,
                        scene_change_score REAL,
                        transcribed_text TEXT,
                        audio_classification TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
                    )
                """)
                
                # 创建人名档案表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS person_profiles (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        person_name TEXT UNIQUE NOT NULL,
                        reference_images TEXT,
                        classification_count INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # 创建人名分类结果表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS person_classifications (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        person_id INTEGER,
                        file_id INTEGER,
                        confidence_score REAL,
                        classification_method TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (person_id) REFERENCES person_profiles(id),
                        FOREIGN KEY (file_id) REFERENCES files(id)
                    )
                """)
                
                # 创建系统配置表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS config (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # 创建处理队列表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS processing_queue (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        file_path TEXT NOT NULL,
                        priority INTEGER DEFAULT 5,
                        retry_count INTEGER DEFAULT 0,
                        max_retries INTEGER DEFAULT 3,
                        error_message TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        started_at TIMESTAMP,
                        completed_at TIMESTAMP,
                        status TEXT DEFAULT 'queued'
                    )
                """)
                
                conn.commit()
                logger.info("数据库表结构初始化完成")
                
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            raise
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        """
        执行查询语句
        
        Args:
            query: SQL查询语句
            params: 查询参数
            
        Returns:
            查询结果列表
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"查询执行失败: {e}")
            raise
    
    def execute_update(self, query: str, params: tuple = None) -> int:
        """
        执行更新语句
        
        Args:
            query: SQL更新语句
            params: 更新参数
            
        Returns:
            受影响的行数
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                conn.commit()
                return cursor.rowcount
                
        except Exception as e:
            logger.error(f"更新执行失败: {e}")
            raise
    
    def insert_record(self, table: str, data: Dict[str, Any]) -> int:
        """
        插入记录
        
        Args:
            table: 表名
            data: 要插入的数据字典
            
        Returns:
            插入记录的ID
        """
        try:
            columns = ", ".join(data.keys())
            placeholders = ", ".join(["?" for _ in data])
            query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
            params = tuple(data.values())
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                return cursor.lastrowid
                
        except Exception as e:
            logger.error(f"记录插入失败: {e}")
            raise
    
    def update_record(self, table: str, data: Dict[str, Any], condition: str, params: tuple = None) -> int:
        """
        更新记录
        
        Args:
            table: 表名
            data: 要更新的数据字典
            condition: 更新条件
            params: 条件参数
            
        Returns:
            受影响的行数
        """
        try:
            set_clause = ", ".join([f"{key} = ?" for key in data.keys()])
            query = f"UPDATE {table} SET {set_clause} WHERE {condition}"
            query_params = tuple(data.values()) + (params if params else ())
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(query, query_params)
                conn.commit()
                return cursor.rowcount
                
        except Exception as e:
            logger.error(f"记录更新失败: {e}")
            raise
    
    def delete_record(self, table: str, condition: str, params: tuple = None) -> int:
        """
        删除记录
        
        Args:
            table: 表名
            condition: 删除条件
            params: 条件参数
            
        Returns:
            受影响的行数
        """
        try:
            query = f"DELETE FROM {table} WHERE {condition}"
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(query, params if params else ())
                conn.commit()
                return cursor.rowcount
                
        except Exception as e:
            logger.error(f"记录删除失败: {e}")
            raise
    
    def reset_database(self):
        """重置数据库(清空所有数据)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 清空所有表数据
                tables = [
                    "processing_queue",
                    "person_classifications", 
                    "person_profiles",
                    "media_segments",
                    "files",
                    "config"
                ]
                
                for table in tables:
                    cursor.execute(f"DELETE FROM {table}")
                
                conn.commit()
                logger.info("数据库重置完成")
                
        except Exception as e:
            logger.error(f"数据库重置失败: {e}")
            raise


# 全局数据库管理器实例
_db_manager = None


def get_db_manager() -> DatabaseManager:
    """
    获取全局数据库管理器实例
    
    Returns:
        数据库管理器实例
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager