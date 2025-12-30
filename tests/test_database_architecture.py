"""
数据库架构测试
测试数据库架构设计和功能
"""

import pytest
import tempfile
import os
import sqlite3
import time
from unittest.mock import Mock, patch

from src.common.storage.database_adapter import DatabaseAdapter
from src.common.storage.vector_storage_manager import VectorStorageManager
from src.processing_service.task_manager import TaskManager


class TestDatabaseArchitecture:
    """数据库架构测试类"""
    
    @pytest.fixture
    def temp_db_path(self):
        """临时数据库路径"""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_file.close()
        yield temp_file.name
        os.unlink(temp_file.name)
    
    @pytest.fixture
    def database_adapter(self, temp_db_path):
        """数据库适配器实例"""
        adapter = DatabaseAdapter()
        # 临时修改数据库路径为测试路径
        original_path = adapter.db_path
        adapter.db_path = temp_db_path
        # 重新初始化数据库
        adapter._initialize_database()
        yield adapter
        adapter.db_path = original_path
    
    def test_database_initialization(self, database_adapter):
        """测试数据库初始化"""
        # 验证所有必需的表都已创建
        with database_adapter.get_connection() as conn:
            cursor = conn.cursor()
            
            # 检查表是否存在
            tables = ['files', 'tasks', 'media_segments', 'vectors', 'video_segments', 
                     'file_relationships', 'persons', 'file_faces']
            
            for table in tables:
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                result = cursor.fetchone()
                assert result is not None, f"表 {table} 未创建"
    
    @pytest.mark.asyncio
    async def test_file_operations(self, database_adapter):
        """测试文件操作"""
        # 插入文件记录
        file_info = {
            'id': 'test_file_id_1',
            'file_path': '/test/path/file1.jpg',
            'file_name': 'file1.jpg',
            'file_type': '.jpg',
            'file_size': 1024,
            'file_hash': 'test_hash_1',
            'created_at': 1234567890.123,
            'modified_at': 1234567890.123,
            'status': 'completed'
        }
        
        file_id = await database_adapter.insert_file(file_info)
        assert file_id == 'test_file_id_1'
        
        # 获取文件记录
        retrieved_file = await database_adapter.get_file('test_file_id_1')
        assert retrieved_file is not None
        assert retrieved_file['file_path'] == '/test/path/file1.jpg'
        assert retrieved_file['file_size'] == 1024
        
        # 更新文件状态
        success = await database_adapter.update_file_status('test_file_id_1', 'processed')
        assert success is True
        
        # 验证状态更新
        updated_file = await database_adapter.get_file('test_file_id_1')
        assert updated_file['status'] == 'processed'
    
    @pytest.mark.asyncio
    async def test_task_operations(self, database_adapter):
        """测试任务操作"""
        from datetime import datetime
        
        # 插入任务记录
        task_data = {
            'file_id': 'test_file_id_1',
            'task_type': 'vectorization',
            'status': 'pending',
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        
        task_id = await database_adapter.insert_task(task_data)
        assert task_id is not None
        
        # 获取任务记录
        task = await database_adapter.get_task(task_id)
        assert task is not None
        assert task['file_id'] == 'test_file_id_1'
        assert task['task_type'] == 'vectorization'
        
        # 更新任务
        success = await database_adapter.update_task(task_id, {'status': 'completed', 'progress': 100})
        assert success is True
        
        # 验证更新
        updated_task = await database_adapter.get_task(task_id)
        assert updated_task['status'] == 'completed'
        assert updated_task['progress'] == 100
    
    @pytest.mark.asyncio
    async def test_video_segment_operations(self, database_adapter):
        """测试视频片段操作"""
        # 插入视频片段
        segment_data = {
            'file_uuid': 'test_video_uuid',
            'segment_index': 0,
            'start_time': 0.0,
            'end_time': 4.8,
            'duration': 4.8,
            'scene_boundary': True,
            'has_audio': True
        }
        
        segment_id = await database_adapter.insert_video_segment(segment_data)
        assert segment_id is not None
        
        # 获取视频片段
        segments = await database_adapter.get_video_segments_by_file('test_video_uuid')
        assert len(segments) == 1
        assert segments[0]['start_time'] == 0.0
        assert segments[0]['end_time'] == 4.8
        assert segments[0]['scene_boundary'] == 1  # SQLite中布尔值存储为整数
        
        # 测试按时间获取片段
        segment_by_time = await database_adapter.get_video_segment_by_file_and_time('test_video_uuid', 2.0)
        assert segment_by_time is not None
        assert 2.0 >= segment_by_time['start_time'] and 2.0 <= segment_by_time['end_time']
    
    @pytest.mark.asyncio
    async def test_file_relationship_operations(self, database_adapter):
        """测试文件关系操作"""
        # 创建源文件
        source_file_info = {
            'id': 'source_file_id',
            'file_path': '/test/source.mp4',
            'file_name': 'source.mp4',
            'file_type': '.mp4',
            'file_size': 1024000,
            'file_hash': 'source_hash',
            'created_at': 1234567890.123,
            'modified_at': 1234567890.123,
            'status': 'completed'
        }
        await database_adapter.insert_file(source_file_info)
        
        # 创建派生文件
        derived_file_info = {
            'id': 'derived_file_id',
            'file_path': '/test/derived.wav',
            'file_name': 'derived.wav',
            'file_type': '.wav',
            'file_size': 512000,
            'file_hash': 'derived_hash',
            'created_at': 1234567891.123,
            'modified_at': 1234567891.123,
            'status': 'completed'
        }
        await database_adapter.insert_file(derived_file_info)
        
        # 创建文件关系
        success = await database_adapter.create_file_relationship(
            'source_file_id', 
            'derived_file_id', 
            'audio_from_video',
            {'conversion_time': 1234567892.123}
        )
        assert success is True
        
        # 获取关系
        relationships = await database_adapter.get_file_relationships('source_file_id')
        assert len(relationships) >= 1  # 可能包含从两个方向查询的结果
        
        # 检查是否有正确的源-派生关系
        correct_relationship = next((rel for rel in relationships 
                                   if rel['source_file_id'] == 'source_file_id' 
                                   and rel['derived_file_id'] == 'derived_file_id'), None)
        assert correct_relationship is not None
        assert correct_relationship['relationship_type'] == 'audio_from_video'
    
    @pytest.mark.asyncio
    async def test_person_and_face_operations(self, database_adapter):
        """测试人物和人脸操作"""
        # 插入人物信息
        person_data = {
            'name': '张三',
            'aliases': ['张三丰'],
            'description': '测试人物'
        }
        
        person_id = await database_adapter.insert_person(person_data)
        assert person_id is not None
        
        # 获取人物信息
        person = await database_adapter.get_person_by_name('张三')
        assert person is not None
        assert person['name'] == '张三'
        assert '张三丰' in person['aliases']
        
        # 插入文件人脸信息
        face_data = {
            'file_id': 'test_file_id_1',
            'person_id': person_id,
            'timestamp': 10.5,
            'confidence': 0.95,
            'bbox': [10, 10, 100, 100]  # [x, y, width, height]
        }
        
        face_id = await database_adapter.insert_file_face(face_data)
        assert face_id is not None
        
        # 获取文件人脸信息
        faces = await database_adapter.get_faces_by_file('test_file_id_1')
        assert len(faces) == 1
        assert faces[0]['person_id'] == person_id
        assert faces[0]['confidence'] == 0.95
    
    @pytest.mark.asyncio
    async def test_database_statistics(self, database_adapter):
        """测试数据库统计信息"""
        # 插入一些测试文件用于统计
        for i in range(5):
            file_info = {
                'id': f'stats_file_{i}',
                'file_path': f'/test/stats_test_file_{i}.jpg',
                'file_name': f'stats_test_file_{i}.jpg',
                'file_type': '.jpg',
                'file_size': 1024 * (i + 1),
                'file_hash': f'stats_test_hash_{i}',
                'created_at': time.time() - 1000,
                'modified_at': time.time() - 500,
                'processed_at': time.time(),
                'status': 'completed' if i % 2 == 0 else 'pending'
            }
            await database_adapter.insert_file(file_info)
        
        stats = await database_adapter.get_database_stats()
        
        assert 'total_files' in stats
        assert 'completed_files' in stats
        assert stats['total_files'] >= 5
        
        # 插入一个测试视频片段
        segment_data = {
            'file_uuid': 'stats_test_video_uuid',
            'segment_index': 0,
            'start_time': 0.0,
            'end_time': 10.0,
            'duration': 10.0,
            'scene_boundary': True,
            'has_audio': True
        }
        await database_adapter.insert_video_segment(segment_data)
        
        # 验证视频片段统计
        video_stats = await database_adapter.get_video_segments_statistics('stats_test_video_uuid')
        assert 'total_segments' in video_stats
        assert 'total_duration' in video_stats
        assert video_stats['total_segments'] == 1  # 我们刚刚插入的片段
    
    @pytest.mark.asyncio
    async def test_search_functionality(self, database_adapter):
        """测试搜索功能"""
        # 插入测试数据用于搜索
        segment_data = {
            'file_uuid': 'search_test_uuid',
            'segment_index': 0,
            'start_time': 0.0,
            'end_time': 5.0,
            'duration': 5.0,
            'scene_boundary': True,
            'has_audio': True
        }
        await database_adapter.insert_video_segment(segment_data)
        
        # 插入另一个片段
        segment_data2 = {
            'file_uuid': 'search_test_uuid',
            'segment_index': 1,
            'start_time': 5.0,
            'end_time': 10.0,
            'duration': 5.0,
            'scene_boundary': False,
            'has_audio': False
        }
        await database_adapter.insert_video_segment(segment_data2)
        
        # 测试按文件获取片段
        segments = await database_adapter.get_video_segments_by_file('search_test_uuid')
        assert len(segments) == 2
        
        # 测试按时间范围获取片段
        # 注意：方法查找完全在指定范围内的片段
        range_segments = await database_adapter.get_video_segments_by_time_range('search_test_uuid', 0.0, 5.0)
        assert len(range_segments) >= 1  # 找到完全在0-5范围内的片段
        
        # 测试特定搜索参数 - 查找有场景边界的片段
        search_params = {
            'file_uuid': 'search_test_uuid',
            'scene_boundary': True
        }
        boundary_segments = await database_adapter.get_video_segments_by_search(search_params)
        scene_boundary_count = sum(1 for s in [segment_data, segment_data2] if s['scene_boundary'])
        assert len(boundary_segments) >= scene_boundary_count
    
    @pytest.mark.asyncio
    async def test_database_schema_version(self, database_adapter):
        """测试数据库Schema版本"""
        schema_info = await database_adapter.get_schema_version()
        assert 'version' in schema_info
        assert 'last_updated' in schema_info
        assert schema_info['version'] == '1.0.0'