"""
优化的数据库适配器
提供高性能的数据库访问接口，包含连接池、查询优化、缓存等功能
"""

import asyncio
import logging
import sqlite3
import uuid
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
import threading

from src.core.config_manager import get_config_manager
from src.core.cache_manager import CacheManager


class DatabaseConnectionPool:
    """数据库连接池"""
    
    def __init__(self, db_path: str, pool_size: int = 10, timeout: float = 30.0):
        self.db_path = db_path
        self.pool_size = pool_size
        self.timeout = timeout
        self.pool = []
        self.lock = threading.Lock()
        self.initialized = False
    
    def initialize(self):
        """初始化连接池"""
        if self.initialized:
            return
        
        with self.lock:
            if self.initialized:
                return
            
            for _ in range(self.pool_size):
                try:
                    conn = sqlite3.connect(
                        self.db_path,
                        timeout=self.timeout,
                        check_same_thread=False
                    )
                    conn.row_factory = sqlite3.Row
                    self.pool.append(conn)
                except Exception as e:
                    logging.error(f"数据库连接创建失败: {e}")
            
            self.initialized = True
            logging.info(f"数据库连接池初始化完成: {len(self.pool)} 个连接")
    
    @asynccontextmanager
    async def get_connection(self):
        """获取数据库连接"""
        self.initialize()
        
        start_time = time.time()
        while True:
            with self.lock:
                if self.pool:
                    conn = self.pool.pop()
                    break
            
            if time.time() - start_time > self.timeout:
                raise RuntimeError("获取数据库连接超时")
            
            await asyncio.sleep(0.01)
        
        try:
            yield conn
        finally:
            with self.lock:
                if len(self.pool) < self.pool_size:
                    self.pool.append(conn)
    
    def close_all(self):
        """关闭所有连接"""
        with self.lock:
            for conn in self.pool:
                try:
                    conn.close()
                except Exception:
                    pass
            self.pool.clear()
        
        logging.info("数据库连接池已关闭")


class OptimizedDatabaseAdapter:
    """优化的数据库适配器"""
    
    def __init__(self, config_manager=None, cache_manager: Optional[CacheManager] = None):
        self.config_manager = config_manager or get_config_manager()
        self.cache_manager = cache_manager
        self.logger = logging.getLogger(__name__)
        
        # 数据库配置
        self.db_path = self.config_manager.get("database.sqlite.path", "./data/msearch.db")
        self.pool_size = self.config_manager.get("database.sqlite.connection_pool_size", 10)
        self.timeout = self.config_manager.get("database.sqlite.timeout", 30)
        
        # 确保数据库目录存在
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # 连接池
        self.connection_pool = DatabaseConnectionPool(
            db_path=self.db_path,
            pool_size=self.pool_size,
            timeout=self.timeout
        )
        
        # 线程池执行器用于同步操作
        self.executor = ThreadPoolExecutor(max_workers=self.pool_size)
        
        # 查询统计
        self.query_stats = {
            'total_queries': 0,
            'cache_hits': 0,
            'slow_queries': 0,
            'average_time': 0.0
        }
        
        # 初始化数据库
        self._initialize_database_optimized()
        
        self.logger.info(f"优化的数据库适配器初始化完成: {self.db_path}")
    
    def _initialize_database_optimized(self):
        """初始化数据库（优化版）"""
        async def init_db():
            async with self.connection_pool.get_connection() as conn:
                cursor = conn.cursor()
                
                # 创建所有表
                await self._create_tables_optimized(cursor)
                
                # 创建性能优化的索引
                await self._create_performance_indexes(cursor)
                
                # 启用WAL模式以提高并发性能
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.execute("PRAGMA cache_size=10000")
                cursor.execute("PRAGMA temp_store=MEMORY")
                
                conn.commit()
        
        asyncio.run(init_db())
    
    async def _create_tables_optimized(self, cursor):
        """创建优化的表结构"""
        # 文件表（优化版）
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
                metadata TEXT,
                tags TEXT,
                description TEXT
            )
        """)
        
        # 任务表（优化版）
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
                priority INTEGER DEFAULT 5,
                result TEXT,
                FOREIGN KEY (file_id) REFERENCES files (id)
            )
        """)
        
        # 媒体片段表（优化版）
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
                quality_score REAL,
                created_at REAL NOT NULL,
                FOREIGN KEY (file_id) REFERENCES files (id)
            )
        """)
        
        # 向量表（优化版）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vectors (
                id TEXT PRIMARY KEY,
                file_id TEXT NOT NULL,
                task_id TEXT,
                segment_id TEXT,
                vector_data BLOB NOT NULL,
                model_name TEXT NOT NULL,
                vector_type TEXT NOT NULL,
                -- milvus_lite_id TEXT, -- Milvus Lite doesn't use point ids
                created_at REAL NOT NULL,
                vector_hash TEXT,
                quality_score REAL,
                FOREIGN KEY (file_id) REFERENCES files (id),
                FOREIGN KEY (task_id) REFERENCES tasks (id),
                FOREIGN KEY (segment_id) REFERENCES media_segments (id)
            )
        """)
        
        # 视频片段表（时间戳精确定位）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS video_segments (
                segment_id TEXT PRIMARY KEY,
                file_uuid TEXT NOT NULL,
                segment_index INTEGER NOT NULL,
                start_time REAL NOT NULL,
                end_time REAL NOT NULL,
                duration REAL NOT NULL,
                scene_boundary BOOLEAN DEFAULT 0,
                frame_count INTEGER,
                keyframe_timestamps TEXT,
                audio_present BOOLEAN DEFAULT 0,
                created_at REAL NOT NULL
            )
        """)
        
        # 性能统计表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                component_name TEXT NOT NULL,
                operation_type TEXT NOT NULL,
                execution_time REAL NOT NULL,
                success BOOLEAN NOT NULL,
                timestamp REAL NOT NULL,
                metadata TEXT
            )
        """)
    
    async def _create_performance_indexes(self, cursor):
        """创建性能优化索引"""
        # 复合索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_status_created ON files(status, created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status_priority ON tasks(status, priority)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_file_status ON tasks(file_id, status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_vectors_file_model ON vectors(file_id, model_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_media_segments_file_type ON media_segments(file_id, segment_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_video_segments_file_time ON video_segments(file_uuid, start_time)")
        
        # 全文搜索索引
        cursor.execute("CREATE VIRTUAL TABLE IF NOT EXISTS files_fts USING fts5(file_name, description, tags, content='files', content_rowid='rowid')")
        
        # 性能统计索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_perf_component_time ON performance_stats(component_name, timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_perf_operation_time ON performance_stats(operation_type, timestamp)")
    
    async def insert_file_optimized(self, file_info: Dict[str, Any]) -> str:
        """优化的文件插入"""
        start_time = time.time()
        
        try:
            async with self.connection_pool.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO files (
                        id, file_path, file_name, file_type, file_size, 
                        file_hash, created_at, modified_at, status, can_delete,
                        metadata, tags, description
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    str(file_info.get('metadata', {})),
                    file_info.get('tags', ''),
                    file_info.get('description', '')
                ))
                
                # 更新FTS表
                cursor.execute("""
                    INSERT OR REPLACE INTO files_fts(rowid, file_name, description, tags)
                    VALUES ((SELECT rowid FROM files WHERE id = ?), ?, ?, ?)
                """, (
                    file_info['id'],
                    file_info['file_name'],
                    file_info.get('description', ''),
                    file_info.get('tags', '')
                ))
                
                conn.commit()
                
            # 更新缓存
            if self.cache_manager:
                cache_key = f"file:{file_info['file_path']}"
                self.cache_manager.memory_cache.set(cache_key, file_info)
            
            execution_time = time.time() - start_time
            await self._record_performance_stat('database', 'insert_file', execution_time, True)
            
            self.logger.debug(f"文件插入优化完成: {file_info['id']}, 耗时: {execution_time:.3f}s")
            return file_info['id']
            
        except Exception as e:
            execution_time = time.time() - start_time
            await self._record_performance_stat('database', 'insert_file', execution_time, False)
            self.logger.error(f"文件插入失败: {e}")
            raise
    
    @CacheManager.cache_result('metadata', ttl=300)
    async def get_file_optimized(self, file_id: str) -> Optional[Dict[str, Any]]:
        """优化的文件获取（带缓存）"""
        start_time = time.time()
        
        try:
            async with self.connection_pool.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM files 
                    WHERE id = ?
                """, (file_id,))
                
                result = cursor.fetchone()
                
            if result:
                file_info = dict(result)
                # 解析JSON字段
                if file_info.get('metadata'):
                    file_info['metadata'] = eval(file_info['metadata'])
                
                execution_time = time.time() - start_time
                await self._record_performance_stat('database', 'get_file', execution_time, True)
                
                return file_info
            else:
                execution_time = time.time() - start_time
                await self._record_performance_stat('database', 'get_file', execution_time, True)
                return None
            
        except Exception as e:
            execution_time = time.time() - start_time
            await self._record_performance_stat('database', 'get_file', execution_time, False)
            self.logger.error(f"获取文件失败: {e}")
            return None
    
    @CacheManager.cache_result('metadata', ttl=60)
    async def search_files_optimized(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """优化的文件搜索（带FTS）"""
        start_time = time.time()
        
        try:
            async with self.connection_pool.get_connection() as conn:
                cursor = conn.cursor()
                
                # 使用FTS进行全文搜索
                cursor.execute("""
                    SELECT f.*, 
                           bm25(files_fts, 'file_name', 'description', 'tags') as rank
                    FROM files f
                    JOIN files_fts ON files_fts.rowid = f.rowid
                    WHERE files_fts MATCH ?
                    ORDER BY rank ASC
                    LIMIT ?
                """, (query, limit))
                
                results = cursor.fetchall()
                
            file_list = []
            for result in results:
                file_info = dict(result)
                if file_info.get('metadata'):
                    file_info['metadata'] = eval(file_info['metadata'])
                file_list.append(file_info)
            
            execution_time = time.time() - start_time
            await self._record_performance_stat('database', 'search_files', execution_time, True)
            
            self.logger.debug(f"文件搜索完成: 查询='{query}', 结果数={len(file_list)}, 耗时: {execution_time:.3f}s")
            return file_list
            
        except Exception as e:
            execution_time = time.time() - start_time
            await self._record_performance_stat('database', 'search_files', execution_time, False)
            self.logger.error(f"文件搜索失败: {e}")
            return []
    
    async def batch_insert_files_optimized(self, file_info_list: List[Dict[str, Any]]) -> List[str]:
        """批量插入文件（优化版）"""
        start_time = time.time()
        
        try:
            async with self.connection_pool.get_connection() as conn:
                cursor = conn.cursor()
                
                # 使用批量插入提高性能
                cursor.executemany("""
                    INSERT OR REPLACE INTO files (
                        id, file_path, file_name, file_type, file_size, 
                        file_hash, created_at, modified_at, status, can_delete,
                        metadata, tags, description
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [
                    (
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
                        str(file_info.get('metadata', {})),
                        file_info.get('tags', ''),
                        file_info.get('description', '')
                    )
                    for file_info in file_info_list
                ])
                
                # 批量更新FTS表
                fts_data = [
                    (file_info['id'], file_info['file_name'], file_info.get('description', ''), file_info.get('tags', ''))
                    for file_info in file_info_list
                ]
                cursor.executemany("""
                    INSERT OR REPLACE INTO files_fts(rowid, file_name, description, tags)
                    VALUES ((SELECT rowid FROM files WHERE id = ?), ?, ?, ?)
                """, fts_data)
                
                conn.commit()
                
            file_ids = [file_info['id'] for file_info in file_info_list]
            
            # 更新缓存
            if self.cache_manager:
                for file_info in file_info_list:
                    cache_key = f"file:{file_info['file_path']}"
                    self.cache_manager.memory_cache.set(cache_key, file_info)
            
            execution_time = time.time() - start_time
            await self._record_performance_stat('database', 'batch_insert_files', execution_time, True)
            
            self.logger.info(f"批量文件插入完成: {len(file_info_list)} 个文件, 耗时: {execution_time:.3f}s")
            return file_ids
            
        except Exception as e:
            execution_time = time.time() - start_time
            await self._record_performance_stat('database', 'batch_insert_files', execution_time, False)
            self.logger.error(f"批量文件插入失败: {e}")
            raise
    
    async def get_pending_files_optimized(self, limit: int = 50) -> List[Dict[str, Any]]:
        """优化的待处理文件获取"""
        start_time = time.time()
        
        try:
            async with self.connection_pool.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM files 
                    WHERE status = 'pending' 
                    ORDER BY created_at ASC 
                    LIMIT ?
                """, (limit,))
                
                results = cursor.fetchall()
                
            file_list = []
            for result in results:
                file_info = dict(result)
                if file_info.get('metadata'):
                    file_info['metadata'] = eval(file_info['metadata'])
                file_list.append(file_info)
            
            execution_time = time.time() - start_time
            await self._record_performance_stat('database', 'get_pending_files', execution_time, True)
            
            return file_list
            
        except Exception as e:
            execution_time = time.time() - start_time
            await self._record_performance_stat('database', 'get_pending_files', execution_time, False)
            self.logger.error(f"获取待处理文件失败: {e}")
            return []
    
    async def _record_performance_stat(self, component: str, operation: str, execution_time: float, success: bool):
        """记录性能统计"""
        try:
            async with self.connection_pool.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO performance_stats (
                        component_name, operation_type, execution_time, success, timestamp
                    ) VALUES (?, ?, ?, ?, ?)
                """, (component, operation, execution_time, success, time.time()))
                
                conn.commit()
            
            # 更新统计信息
            self.query_stats['total_queries'] += 1
            
            if execution_time > 1.0:  # 超过1秒的查询被认为是慢查询
                self.query_stats['slow_queries'] += 1
            
            # 计算平均时间
            self.query_stats['average_time'] = (
                (self.query_stats['average_time'] * (self.query_stats['total_queries'] - 1) + execution_time)
                / self.query_stats['total_queries']
            )
            
        except Exception as e:
            self.logger.debug(f"性能统计记录失败: {e}")
    
    async def get_performance_stats(self) -> Dict[str, Any]:
        """获取数据库性能统计"""
        try:
            async with self.connection_pool.get_connection() as conn:
                cursor = conn.cursor()
                
                # 获取最近的性能统计
                cursor.execute("""
                    SELECT 
                        component_name,
                        operation_type,
                        COUNT(*) as query_count,
                        AVG(execution_time) as avg_time,
                        MAX(execution_time) as max_time,
                        SUM(CASE WHEN success THEN 1 ELSE 0 END) as success_count,
                        SUM(CASE WHEN NOT success THEN 1 ELSE 0 END) as error_count
                    FROM performance_stats 
                    WHERE timestamp > ?
                    GROUP BY component_name, operation_type
                    ORDER BY avg_time DESC
                """, (time.time() - 3600,))  # 最近1小时
                
                results = cursor.fetchall()
                
            component_stats = {}
            for result in results:
                key = f"{result['component_name']}_{result['operation_type']}"
                component_stats[key] = dict(result)
                component_stats[key]['success_rate'] = result['success_count'] / result['query_count']
            
            return {
                'overall_stats': self.query_stats,
                'component_stats': component_stats
            }
            
        except Exception as e:
            self.logger.error(f"获取性能统计失败: {e}")
            return {'overall_stats': self.query_stats, 'component_stats': {}}
    
    async def cleanup_old_data(self, days: int = 30) -> int:
        """清理旧数据"""
        start_time = time.time()
        
        try:
            cutoff_time = time.time() - (days * 24 * 3600)
            
            async with self.connection_pool.get_connection() as conn:
                cursor = conn.cursor()
                
                # 清理旧的性能统计
                cursor.execute("DELETE FROM performance_stats WHERE timestamp < ?", (cutoff_time,))
                deleted_perf_count = cursor.rowcount
                
                # 清理已完成的任务
                cursor.execute("""
                    DELETE FROM tasks 
                    WHERE status = 'completed' AND updated_at < ?
                """, (cutoff_time,))
                deleted_task_count = cursor.rowcount
                
                conn.commit()
            
            execution_time = time.time() - start_time
            
            self.logger.info(f"数据清理完成: 删除了 {deleted_perf_count} 个性能记录, "
                           f"{deleted_task_count} 个任务记录, 耗时: {execution_time:.3f}s")
            
            return deleted_perf_count + deleted_task_count
            
        except Exception as e:
            execution_time = time.time() - start_time
            await self._record_performance_stat('database', 'cleanup_old_data', execution_time, False)
            self.logger.error(f"数据清理失败: {e}")
            return 0
    
    def close(self):
        """关闭数据库连接池"""
        self.connection_pool.close_all()
        self.executor.shutdown(wait=True)
        self.logger.info("数据库连接池已关闭")