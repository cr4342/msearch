import pytest
import sqlite3
from pathlib import Path
from src.core.database import DatabaseManager

class TestDatabaseManager:
    """测试数据库管理器类"""
    
    def test_initialization(self, temp_dir):
        """测试数据库初始化"""
        # 创建临时数据库路径
        db_path = Path(temp_dir) / "test.db"
        
        # 初始化数据库管理器
        db_manager = DatabaseManager(str(db_path))
        
        # 验证初始化
        assert db_manager is not None
        assert db_path.exists()
        
        # 关闭数据库连接
        db_manager.close()
    
    def test_create_tables(self, temp_dir):
        """测试创建数据库表"""
        # 创建临时数据库路径
        db_path = Path(temp_dir) / "test.db"
        
        # 初始化数据库管理器
        db_manager = DatabaseManager(str(db_path))
        
        # 验证表已创建
        connection = sqlite3.connect(str(db_path))
        cursor = connection.cursor()
        
        # 检查file_metadata表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='file_metadata'")
        assert cursor.fetchone() is not None
        
        # 检查video_metadata表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='video_metadata'")
        assert cursor.fetchone() is not None
        
        # 检查video_segments表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='video_segments'")
        assert cursor.fetchone() is not None
        
        # 检查vector_timestamp_map表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='vector_timestamp_map'")
        assert cursor.fetchone() is not None
        
        # 关闭连接
        connection.close()
        db_manager.close()
    
    def test_insert_file_metadata(self, temp_dir):
        """测试插入文件元数据"""
        # 创建临时数据库路径
        db_path = Path(temp_dir) / "test.db"
        
        # 初始化数据库管理器
        db_manager = DatabaseManager(str(db_path))
        
        # 测试文件元数据
        file_metadata = {
            'file_path': '/test/path/file.txt',
            'file_name': 'file.txt',
            'file_type': 'text',
            'file_size': 1024,
            'file_hash': 'test_hash_12345',
            'metadata': {'key': 'value'}
        }
        
        # 插入文件元数据
        file_id = db_manager.insert_file_metadata(file_metadata)
        
        # 验证插入成功
        assert file_id is not None
        
        # 获取插入的文件元数据
        retrieved_metadata = db_manager.get_file_metadata(file_id)
        assert retrieved_metadata is not None
        assert retrieved_metadata['file_path'] == file_metadata['file_path']
        assert retrieved_metadata['file_name'] == file_metadata['file_name']
        assert retrieved_metadata['file_type'] == file_metadata['file_type']
        assert retrieved_metadata['file_size'] == file_metadata['file_size']
        assert retrieved_metadata['file_hash'] == file_metadata['file_hash']
        
        # 关闭数据库连接
        db_manager.close()
    
    def test_update_file_metadata(self, temp_dir):
        """测试更新文件元数据"""
        # 创建临时数据库路径
        db_path = Path(temp_dir) / "test.db"
        
        # 初始化数据库管理器
        db_manager = DatabaseManager(str(db_path))
        
        # 测试文件元数据
        file_metadata = {
            'file_path': '/test/path/file.txt',
            'file_name': 'file.txt',
            'file_type': 'text',
            'file_size': 1024,
            'file_hash': 'test_hash_12345',
            'metadata': {'key': 'value'}
        }
        
        # 插入文件元数据
        file_id = db_manager.insert_file_metadata(file_metadata)
        
        # 更新文件状态
        update_result = db_manager.update_file_status(file_id, 'completed')
        assert update_result == True
        
        # 获取更新后的文件元数据
        retrieved_metadata = db_manager.get_file_metadata(file_id)
        assert retrieved_metadata['processing_status'] == 'completed'
        assert retrieved_metadata['processed_at'] is not None
        
        # 关闭数据库连接
        db_manager.close()
    
    def test_insert_video_metadata(self, temp_dir):
        """测试插入视频元数据"""
        # 创建临时数据库路径
        db_path = Path(temp_dir) / "test.db"
        
        # 初始化数据库管理器
        db_manager = DatabaseManager(str(db_path))
        
        # 先插入文件元数据
        file_metadata = {
            'file_path': '/test/path/video.mp4',
            'file_name': 'video.mp4',
            'file_type': 'video',
            'file_size': 1024 * 1024 * 100,  # 100MB
            'file_hash': 'video_hash_12345',
            'metadata': {'key': 'value'}
        }
        file_id = db_manager.insert_file_metadata(file_metadata)
        
        # 测试视频信息
        video_info = {
            'duration': 120.5,
            'width': 1920,
            'height': 1080,
            'fps': 30.0,
            'codec': 'h264',
            'is_short_video': False,
            'total_segments': 4
        }
        
        # 插入视频元数据
        video_id = db_manager.insert_video_metadata(file_id, video_info)
        
        # 验证插入成功
        assert video_id is not None
        
        # 获取插入的视频元数据
        retrieved_video_metadata = db_manager.get_video_metadata(file_id)
        assert retrieved_video_metadata is not None
        assert retrieved_video_metadata['duration'] == video_info['duration']
        assert retrieved_video_metadata['width'] == video_info['width']
        assert retrieved_video_metadata['height'] == video_info['height']
        assert retrieved_video_metadata['fps'] == video_info['fps']
        
        # 关闭数据库连接
        db_manager.close()
    
    def test_insert_video_segment(self, temp_dir):
        """测试插入视频片段"""
        # 创建临时数据库路径
        db_path = Path(temp_dir) / "test.db"
        
        # 初始化数据库管理器
        db_manager = DatabaseManager(str(db_path))
        
        # 先插入文件元数据
        file_metadata = {
            'file_path': '/test/path/video.mp4',
            'file_name': 'video.mp4',
            'file_type': 'video',
            'file_size': 1024 * 1024 * 100,  # 100MB
            'file_hash': 'video_hash_12345'
        }
        file_id = db_manager.insert_file_metadata(file_metadata)
        
        # 插入视频元数据
        video_info = {
            'duration': 120.5,
            'width': 1920,
            'height': 1080,
            'fps': 30.0
        }
        video_id = db_manager.insert_video_metadata(file_id, video_info)
        
        # 测试视频片段信息
        segment_info = {
            'segment_index': 0,
            'start_time': 0.0,
            'end_time': 30.0,
            'duration': 30.0,
            'is_full_video': False,
            'frame_count': 900,
            'key_frames': [0, 300, 600, 899]
        }
        
        # 插入视频片段
        segment_id = db_manager.insert_video_segment(video_id, segment_info)
        
        # 验证插入成功
        assert segment_id is not None
        
        # 获取插入的视频片段
        segments = db_manager.get_video_segments(video_id)
        assert len(segments) == 1
        assert segments[0]['segment_index'] == segment_info['segment_index']
        assert segments[0]['start_time'] == segment_info['start_time']
        assert segments[0]['end_time'] == segment_info['end_time']
        
        # 关闭数据库连接
        db_manager.close()
    
    def test_insert_vector_timestamp(self, temp_dir):
        """测试插入向量时间戳映射"""
        # 创建临时数据库路径
        db_path = Path(temp_dir) / "test.db"
        
        # 初始化数据库管理器
        db_manager = DatabaseManager(str(db_path))
        
        # 先插入文件元数据
        file_metadata = {
            'file_path': '/test/path/video.mp4',
            'file_name': 'video.mp4',
            'file_type': 'video',
            'file_size': 1024 * 1024 * 100,  # 100MB
            'file_hash': 'video_hash_12345'
        }
        file_id = db_manager.insert_file_metadata(file_metadata)
        
        # 插入视频元数据和片段
        video_info = {
            'duration': 120.5,
            'width': 1920,
            'height': 1080,
            'fps': 30.0
        }
        video_id = db_manager.insert_video_metadata(file_id, video_info)
        
        segment_info = {
            'segment_index': 0,
            'start_time': 0.0,
            'end_time': 30.0,
            'duration': 30.0
        }
        segment_id = db_manager.insert_video_segment(video_id, segment_info)
        
        # 插入向量时间戳映射
        vector_id = "test_vector_id_123"
        modality = "video"
        timestamp = 15.5
        confidence = 0.95
        
        map_id = db_manager.insert_vector_timestamp(vector_id, file_id, segment_id, modality, timestamp, confidence)
        
        # 验证插入成功
        assert map_id is not None
        
        # 获取插入的向量时间戳映射
        timestamp_info = db_manager.get_vector_timestamp(vector_id)
        assert timestamp_info is not None
        assert timestamp_info['vector_id'] == vector_id
        assert timestamp_info['file_id'] == file_id
        assert timestamp_info['segment_id'] == segment_id
        assert timestamp_info['modality'] == modality
        assert timestamp_info['timestamp'] == timestamp
        assert timestamp_info['confidence'] == confidence
        
        # 关闭数据库连接
        db_manager.close()
    
    def test_get_vectors_by_time_range(self, temp_dir):
        """测试获取指定时间范围内的向量"""
        # 创建临时数据库路径
        db_path = Path(temp_dir) / "test.db"
        
        # 初始化数据库管理器
        db_manager = DatabaseManager(str(db_path))
        
        # 先插入文件元数据
        file_metadata = {
            'file_path': '/test/path/video.mp4',
            'file_name': 'video.mp4',
            'file_type': 'video',
            'file_size': 1024 * 1024 * 100,  # 100MB
            'file_hash': 'video_hash_12345'
        }
        file_id = db_manager.insert_file_metadata(file_metadata)
        
        # 插入视频元数据和片段
        video_info = {
            'duration': 120.5,
            'width': 1920,
            'height': 1080,
            'fps': 30.0
        }
        video_id = db_manager.insert_video_metadata(file_id, video_info)
        
        segment_info = {
            'segment_index': 0,
            'start_time': 0.0,
            'end_time': 30.0,
            'duration': 30.0
        }
        segment_id = db_manager.insert_video_segment(video_id, segment_info)
        
        # 插入多个向量时间戳映射
        timestamps = [5.0, 10.0, 15.0, 20.0, 25.0]
        for i, ts in enumerate(timestamps):
            vector_id = f"test_vector_id_{i}"
            db_manager.insert_vector_timestamp(vector_id, file_id, segment_id, "video", ts)
        
        # 获取时间范围内的向量
        vectors_in_range = db_manager.get_vectors_by_time_range(file_id, 10.0, 20.0)
        
        # 验证结果
        assert len(vectors_in_range) == 3  # 10.0, 15.0, 20.0
        
        # 检查返回的时间戳是否在范围内
        for vector in vectors_in_range:
            assert 10.0 <= vector['timestamp'] <= 20.0
        
        # 关闭数据库连接
        db_manager.close()
    
    def test_get_video_timestamp_by_vector(self, temp_dir):
        """测试根据向量ID获取视频时间戳"""
        # 创建临时数据库路径
        db_path = Path(temp_dir) / "test.db"
        
        # 初始化数据库管理器
        db_manager = DatabaseManager(str(db_path))
        
        # 先插入文件元数据
        file_metadata = {
            'file_path': '/test/path/video.mp4',
            'file_name': 'video.mp4',
            'file_type': 'video',
            'file_size': 1024 * 1024 * 100,  # 100MB
            'file_hash': 'video_hash_12345'
        }
        file_id = db_manager.insert_file_metadata(file_metadata)
        
        # 插入视频元数据和片段
        video_info = {
            'duration': 120.5,
            'width': 1920,
            'height': 1080,
            'fps': 30.0
        }
        video_id = db_manager.insert_video_metadata(file_id, video_info)
        
        segment_info = {
            'segment_index': 0,
            'start_time': 0.0,
            'end_time': 30.0,
            'duration': 30.0
        }
        segment_id = db_manager.insert_video_segment(video_id, segment_info)
        
        # 插入向量时间戳映射
        vector_id = "test_vector_id_123"
        timestamp = 15.5
        db_manager.insert_vector_timestamp(vector_id, file_id, segment_id, "video", timestamp)
        
        # 根据向量ID获取时间戳
        retrieved_timestamp = db_manager.get_video_timestamp_by_vector(vector_id)
        
        # 验证结果
        assert retrieved_timestamp == timestamp
        
        # 关闭数据库连接
        db_manager.close()
    
    def test_get_file_references(self, temp_dir):
        """测试获取文件引用"""
        # 创建临时数据库路径
        db_path = Path(temp_dir) / "test.db"
        
        # 初始化数据库管理器
        db_manager = DatabaseManager(str(db_path))
        
        # 测试文件元数据
        file_hash = "test_hash_12345"
        file_metadata = {
            'file_path': '/test/path/file.txt',
            'file_name': 'file.txt',
            'file_type': 'text',
            'file_size': 1024,
            'file_hash': file_hash
        }
        
        # 插入文件元数据
        file_id = db_manager.insert_file_metadata(file_metadata)
        
        # 添加两个文件引用
        db_manager.add_file_reference(file_hash, '/test/path/file_copy1.txt')
        db_manager.add_file_reference(file_hash, '/test/path/file_copy2.txt')
        
        # 获取文件引用
        references = db_manager.get_file_references(file_hash)
        
        # 验证结果
        assert len(references) == 2  # 两个副本引用
        
        # 关闭数据库连接
        db_manager.close()
    
    def test_get_database_stats(self, temp_dir):
        """测试获取数据库统计信息"""
        # 创建临时数据库路径
        db_path = Path(temp_dir) / "test.db"
        
        # 初始化数据库管理器
        db_manager = DatabaseManager(str(db_path))
        
        # 获取统计信息
        stats = db_manager.get_database_stats()
        
        # 验证统计信息结构
        assert 'total_files' in stats
        assert 'status_counts' in stats
        assert 'type_counts' in stats
        assert 'database_size' in stats
        
        # 关闭数据库连接
        db_manager.close()
    
    def test_cleanup_orphaned_files(self, temp_dir):
        """测试清理无引用的文件"""
        # 创建临时数据库路径
        db_path = Path(temp_dir) / "test.db"
        
        # 初始化数据库管理器
        db_manager = DatabaseManager(str(db_path))
        
        # 测试文件元数据
        file_metadata = {
            'file_path': '/test/path/orphaned.txt',
            'file_name': 'orphaned.txt',
            'file_type': 'text',
            'file_size': 1024,
            'file_hash': 'orphan_hash_12345',
            'reference_count': 0  # 无引用
        }
        
        # 插入文件元数据
        file_id = db_manager.insert_file_metadata(file_metadata)
        
        # 清理无引用文件
        cleaned_count = db_manager.cleanup_orphaned_files()
        
        # 验证清理结果
        assert cleaned_count == 1
        
        # 验证文件已被删除
        retrieved = db_manager.get_file_metadata(file_id)
        assert retrieved is None
        
        # 关闭数据库连接
        db_manager.close()
