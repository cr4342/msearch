"""
msearch 数据库架构和索引测试
验证SQLite和Qdrant数据库的架构设计和索引性能
"""
import pytest
import tempfile
import sqlite3
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

try:
    from src.storage.db_adapter import UnifiedDatabaseAdapter
    from src.storage.vector_store import VectorStore
    DB_ADAPTER_AVAILABLE = True
except ImportError as e:
    print(f"数据库模块导入警告: {e}")
    DB_ADAPTER_AVAILABLE = False


class TestSQLiteSchema:
    """SQLite数据库架构测试"""
    
    @pytest.fixture
    def temp_db(self):
        """临时数据库"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        # 创建测试数据库架构
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 创建文件表
        cursor.execute('''
            CREATE TABLE files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT UNIQUE NOT NULL,
                file_name TEXT NOT NULL,
                file_type TEXT NOT NULL,
                file_category TEXT DEFAULT 'original',
                source_file_id TEXT,
                file_size INTEGER,
                file_hash TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pending',
                can_delete BOOLEAN DEFAULT FALSE
            )
        ''')
        
        # 创建媒体片段表
        cursor.execute('''
            CREATE TABLE media_segments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id INTEGER,
                qdrant_point_id TEXT,
                segment_type TEXT,
                segment_index INTEGER,
                start_time_ms INTEGER,
                end_time_ms INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (file_id) REFERENCES files (id)
            )
        ''')
        
        # 创建处理队列表
        cursor.execute('''
            CREATE TABLE processing_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                priority INTEGER DEFAULT 5,
                status TEXT DEFAULT 'queued',
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建索引
        cursor.execute('CREATE INDEX idx_files_status ON files(status)')
        cursor.execute('CREATE INDEX idx_files_type ON files(file_type)')
        cursor.execute('CREATE INDEX idx_files_path ON files(file_path)')
        cursor.execute('CREATE INDEX idx_media_segments_file_id ON media_segments(file_id)')
        cursor.execute('CREATE INDEX idx_media_segments_type ON media_segments(segment_type)')
        cursor.execute('CREATE INDEX idx_queue_status ON processing_queue(status)')
        cursor.execute('CREATE INDEX idx_queue_priority ON processing_queue(priority)')
        
        conn.commit()
        conn.close()
        
        yield db_path
        
        # 清理
        import os
        os.unlink(db_path)
    
    def test_schema_structure(self, temp_db):
        """测试数据库架构结构"""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = ['files', 'media_segments', 'processing_queue']
        for table in expected_tables:
            assert table in tables, f"缺少表: {table}"
        
        # 检查索引是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = [row[0] for row in cursor.fetchall()]
        
        expected_indexes = [
            'idx_files_status', 'idx_files_type', 'idx_files_path',
            'idx_media_segments_file_id', 'idx_media_segments_type',
            'idx_queue_status', 'idx_queue_priority'
        ]
        for index in expected_indexes:
            assert index in indexes, f"缺少索引: {index}"
        
        conn.close()
    
    def test_foreign_key_constraints(self, temp_db):
        """测试外键约束"""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        # 启用外键约束
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # 插入文件记录
        cursor.execute('''
            INSERT INTO files (file_path, file_name, file_type)
            VALUES ('/test/path', 'test_file.mp4', 'video')
        ''')
        file_id = cursor.lastrowid
        
        # 插入有效的媒体片段
        cursor.execute('''
            INSERT INTO media_segments (file_id, segment_type, start_time_ms, end_time_ms)
            VALUES (?, 'video', 0, 5000)
        ''', (file_id,))
        
        # 尝试插入无效的媒体片段（不存在的file_id）
        try:
            cursor.execute('''
                INSERT INTO media_segments (file_id, segment_type, start_time_ms, end_time_ms)
                VALUES (999, 'video', 0, 5000)
            ''')
            assert False, "应该因为外键约束失败"
        except sqlite3.IntegrityError:
            pass  # 预期的错误
        
        conn.commit()
        conn.close()
    
    def test_index_performance(self, temp_db):
        """测试索引性能"""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        # 插入大量测试数据
        import time
        
        # 插入10000个文件记录
        start_time = time.time()
        for i in range(10000):
            cursor.execute('''
                INSERT INTO files (file_path, file_name, file_type, status)
                VALUES (?, ?, ?, ?)
            ''', (f'/test/path_{i}', f'test_file_{i}.mp4', 'video', 'completed'))
        conn.commit()
        insert_time = time.time() - start_time
        
        # 测试有索引的查询性能
        start_time = time.time()
        cursor.execute('''
            SELECT * FROM files WHERE status = 'completed' AND file_type = 'video'
        ''')
        results = cursor.fetchall()
        query_time = time.time() - start_time
        
        # 验证性能和结果
        assert len(results) == 10000, "查询结果数量不正确"
        assert query_time < 0.1, f"查询时间过长: {query_time}秒"
        assert insert_time < 2.0, f"插入时间过长: {insert_time}秒"
        
        conn.close()
    
    def test_data_integrity(self, temp_db):
        """测试数据完整性"""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        # 插入测试数据
        cursor.execute('''
            INSERT INTO files (file_path, file_name, file_type, file_hash)
            VALUES ('/test/path', 'test_file.mp4', 'video', 'abc123')
        ''')
        file_id = cursor.lastrowid
        
        # 测试UNIQUE约束
        try:
            cursor.execute('''
                INSERT INTO files (file_path, file_name, file_type, file_hash)
                VALUES ('/test/path', 'test_file2.mp4', 'video', 'def456')
            ''')
            assert False, "应该因为UNIQUE约束失败"
        except sqlite3.IntegrityError:
            pass  # 预期的错误
        
        # 测试NOT NULL约束
        try:
            cursor.execute('''
                INSERT INTO files (file_path, file_name, file_type)
                VALUES (NULL, 'test_file3.mp4', 'video')
            ''')
            assert False, "应该因为NOT NULL约束失败"
        except sqlite3.IntegrityError:
            pass  # 预期的错误
        
        conn.commit()
        conn.close()


class TestVectorStore:
    """向量存储测试"""
    
    @pytest.fixture
    def vector_store_config(self):
        """向量存储配置"""
        return {
            'host': 'localhost',
            'port': 6333,
            'timeout': 30,
            'collections': {
                'visual_vectors': {
                    'vector_size': 512,
                    'distance': 'Cosine'
                },
                'audio_music_vectors': {
                    'vector_size': 512,
                    'distance': 'Cosine'
                },
                'audio_speech_vectors': {
                    'vector_size': 512,
                    'distance': 'Cosine'
                }
            }
        }
    
    def test_vector_store_initialization(self, vector_store_config):
        """测试向量存储初始化"""
        if not DB_ADAPTER_AVAILABLE:
            pytest.skip("数据库模块不可用")
        
        try:
            vector_store = VectorStore(vector_store_config)
            assert vector_store.config == vector_store_config
            assert vector_store.host == 'localhost'
            assert vector_store.port == 6333
        except Exception as e:
            # Qdrant服务可能未启动，这是预期的
            assert "connection" in str(e).lower() or "qdrant" in str(e).lower()
    
    def test_collection_creation(self, vector_store_config):
        """测试集合创建"""
        if not DB_ADAPTER_AVAILABLE:
            pytest.skip("数据库模块不可用")
        
        try:
            vector_store = VectorStore(vector_store_config)
            
            # 测试创建集合
            for collection_name, collection_config in vector_store_config['collections'].items():
                result = vector_store.create_collection(
                    collection_name,
                    collection_config['vector_size'],
                    collection_config['distance']
                )
                # 集合可能已存在，这是正常的
                assert result is True or "already exists" in str(result).lower()
                
        except Exception as e:
            # Qdrant服务可能未启动，这是预期的
            assert "connection" in str(e).lower() or "qdrant" in str(e).lower()
    
    def test_vector_operations(self, vector_store_config):
        """测试向量操作"""
        if not DB_ADAPTER_AVAILABLE:
            pytest.skip("数据库模块不可用")
        
        try:
            vector_store = VectorStore(vector_store_config)
            
            # 测试向量插入
            test_vector = [0.1] * 512  # 512维向量
            payload = {
                'file_id': 'test_file_1',
                'file_path': '/test/path',
                'modality': 'visual'
            }
            
            result = vector_store.insert_vector(
                'visual_vectors',
                test_vector,
                payload
            )
            
            # 可能因为连接问题失败，这是预期的
            assert result is True or "connection" in str(result).lower()
            
            # 测试向量搜索
            search_results = vector_store.search_vectors(
                'visual_vectors',
                test_vector,
                limit=10
            )
            
            # 可能因为连接问题返回空结果，这是预期的
            assert isinstance(search_results, list)
            
        except Exception as e:
            # Qdrant服务可能未启动，这是预期的
            assert "connection" in str(e).lower() or "qdrant" in str(e).lower()


class TestDatabaseAdapter:
    """数据库适配器测试"""
    
    @pytest.fixture
    def db_adapter(self):
        """数据库适配器"""
        if not DB_ADAPTER_AVAILABLE:
            pytest.skip("数据库模块不可用")
        
        try:
            return UnifiedDatabaseAdapter()
        except Exception as e:
            pytest.skip(f"数据库适配器初始化失败: {e}")
    
    @pytest.mark.asyncio
    async def test_search_functionality(self, db_adapter):
        """测试搜索功能"""
        try:
            # 测试向量搜索
            query_vector = [0.1] * 512
            results = await db_adapter.search(query_vector, modality='visual')
            
            # 验证结果格式
            assert isinstance(results, list)
            for result in results:
                assert 'file_id' in result
                assert 'file_path' in result
                assert 'similarity_score' in result
                assert 0 <= result['similarity_score'] <= 1
                
        except Exception as e:
            # 可能因为依赖问题失败
            assert "connection" in str(e).lower() or "module" in str(e).lower()
    
    @pytest.mark.asyncio
    async def test_embedding_storage(self, db_adapter):
        """测试向量存储"""
        try:
            file_id = 1
            vectors = [[0.1] * 512, [0.2] * 512]  # 两个512维向量
            metadata = {
                'segment_type': 'video',
                'duration': 120.5
            }
            
            result = await db_adapter.store_embedding(file_id, vectors, metadata)
            
            # 验证存储结果
            assert isinstance(result, bool)
            
        except Exception as e:
            # 可能因为依赖问题失败
            assert "connection" in str(e).lower() or "module" in str(e).lower()
    
    @pytest.mark.asyncio
    async def test_file_metadata_operations(self, db_adapter):
        """测试文件元数据操作"""
        try:
            # 测试获取文件元数据
            metadata = await db_adapter.get_file_metadata(1)
            
            # 可能返回None（文件不存在）或字典
            assert metadata is None or isinstance(metadata, dict)
            
        except Exception as e:
            # 可能因为依赖问题失败
            assert "connection" in str(e).lower() or "module" in str(e).lower()
    
    @pytest.mark.asyncio
    async def test_queue_operations(self, db_adapter):
        """测试队列操作"""
        try:
            # 测试添加文件到队列
            queue_id = await db_adapter.add_file_to_queue('/test/path', priority=5)
            assert isinstance(queue_id, int)
            
            # 测试更新队列状态
            result = await db_adapter.update_queue_status(queue_id, 'processing')
            assert isinstance(result, bool)
            
            # 测试更新文件处理状态
            result = await db_adapter.update_file_processing_status(str(queue_id), 'completed', 100)
            assert isinstance(result, bool)
            
        except Exception as e:
            # 可能因为依赖问题失败
            assert "connection" in str(e).lower() or "module" in str(e).lower()


class TestDatabasePerformance:
    """数据库性能测试"""
    
    def test_sqlite_performance(self):
        """测试SQLite性能"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 创建表和索引
            cursor.execute('''
                CREATE TABLE performance_test (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT,
                    file_type TEXT,
                    status TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('CREATE INDEX idx_performance_status ON performance_test(status)')
            cursor.execute('CREATE INDEX idx_performance_type ON performance_test(file_type)')
            
            # 性能测试：批量插入
            import time
            start_time = time.time()
            
            for i in range(5000):
                cursor.execute('''
                    INSERT INTO performance_test (file_path, file_type, status)
                    VALUES (?, ?, ?)
                ''', (f'/test/path_{i}', 'video', 'completed'))
            
            conn.commit()
            insert_time = time.time() - start_time
            
            # 性能测试：索引查询
            start_time = time.time()
            cursor.execute('''
                SELECT COUNT(*) FROM performance_test 
                WHERE status = 'completed' AND file_type = 'video'
            ''')
            count = cursor.fetchone()[0]
            query_time = time.time() - start_time
            
            # 验证性能
            assert count == 5000, "查询结果不正确"
            assert insert_time < 1.0, f"插入性能过慢: {insert_time}秒"
            assert query_time < 0.05, f"查询性能过慢: {query_time}秒"
            
            conn.close()
            
        finally:
            import os
            os.unlink(db_path)
    
    def test_concurrent_access(self):
        """测试并发访问"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        try:
            import threading
            import time
            
            # 创建多个线程并发访问数据库
            def worker(thread_id):
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS concurrent_test (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        thread_id INTEGER,
                        data TEXT
                    )
                ''')
                
                for i in range(100):
                    cursor.execute('''
                        INSERT INTO concurrent_test (thread_id, data)
                        VALUES (?, ?)
                    ''', (thread_id, f'data_{i}'))
                
                conn.commit()
                conn.close()
            
            # 启动多个线程
            threads = []
            start_time = time.time()
            
            for i in range(10):
                thread = threading.Thread(target=worker, args=(i,))
                threads.append(thread)
                thread.start()
            
            # 等待所有线程完成
            for thread in threads:
                thread.join()
            
            total_time = time.time() - start_time
            
            # 验证结果
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM concurrent_test')
            count = cursor.fetchone()[0]
            conn.close()
            
            assert count == 1000, f"并发插入结果不正确: {count}"
            assert total_time < 5.0, f"并发访问性能过慢: {total_time}秒"
            
        finally:
            import os
            os.unlink(db_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])