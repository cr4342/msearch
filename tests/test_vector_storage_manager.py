"""
向量存储管理器测试
测试向量存储管理器功能
"""

import pytest
import numpy as np
from unittest.mock import Mock, AsyncMock, patch
import asyncio

from src.common.storage.vector_storage_manager import VectorStorageManager, VectorType, VectorMetadata


class TestVectorStorageManager:
    """向量存储管理器测试类"""
    
    @pytest.fixture
    def mock_milvus_adapter(self):
        """模拟Milvus适配器"""
        adapter = Mock()
        adapter.connect = AsyncMock(return_value=True)
        adapter.disconnect = AsyncMock()
        adapter.store_vector = AsyncMock(return_value="vec_123")
        adapter.store_vectors = AsyncMock(return_value=["vec_1", "vec_2", "vec_3"])
        adapter.search_vectors = AsyncMock(return_value=[
            {
                'id': 'vec_1',
                'score': 0.95,
                'payload': {
                    'file_id': 'file_1',
                    'file_path': '/test/file1.jpg',
                    'file_name': 'file1.jpg',
                    'file_type': 'image',
                    'file_size': 1024,
                    'created_at': 1234567890.123
                }
            },
            {
                'id': 'vec_2',
                'score': 0.87,
                'payload': {
                    'file_id': 'file_2',
                    'file_path': '/test/file2.jpg',
                    'file_name': 'file2.jpg',
                    'file_type': 'image',
                    'file_size': 2048,
                    'created_at': 1234567891.123
                }
            }
        ])
        adapter.delete_vectors_by_file = AsyncMock(return_value=3)
        adapter.get_collection_info = AsyncMock(return_value={'vectors_count': 100, 'status': 'ready'})
        adapter.get_vector_count = AsyncMock(return_value=50)
        adapter.health_check = AsyncMock(return_value={'status': 'healthy'})
        return adapter
    
    @pytest.fixture
    def mock_config_manager(self):
        """模拟配置管理器"""
        config = Mock()
        
        # 设置不同的返回值，模拟真实的配置结构
        def get_side_effect(key, default=None):
            config_map = {
                'milvus.data_dir': './data/milvus',
                'milvus.collections': {
                    'visual_vectors': 'visual_vectors',
                    'audio_music_vectors': 'audio_music_vectors',
                    'audio_speech_vectors': 'audio_speech_vectors',
                    'face_vectors': 'face_vectors',
                    'text_vectors': 'text_vectors'
                },
                'milvus.dimension': 512,
                'system.log_level': 'INFO'
            }
            return config_map.get(key, default)
        
        config.get = Mock(side_effect=get_side_effect)
        return config
    
    @pytest.fixture
    def vector_storage_manager(self, mock_milvus_adapter, mock_config_manager):
        """向量存储管理器实例"""
        manager = VectorStorageManager(config_manager=mock_config_manager)
        manager.milvus_adapter = mock_milvus_adapter
        return manager
    
    @pytest.mark.asyncio
    async def test_vector_type_enum(self):
        """测试向量类型枚举"""
        assert VectorType.VISUAL.value == "visual"
        assert VectorType.AUDIO_MUSIC.value == "audio_music"
        assert VectorType.AUDIO_SPEECH.value == "audio_speech"
        assert VectorType.FACE.value == "face"
        assert VectorType.TEXT.value == "text"
    
    @pytest.mark.asyncio
    async def test_vector_metadata_creation(self):
        """测试向量元数据创建"""
        metadata = VectorMetadata(
            file_id='file_1',
            file_path='/test/file1.jpg',
            file_name='file1.jpg',
            file_type='image',
            file_size=1024,
            created_at=1234567890.123
        )
        
        assert metadata.file_id == 'file_1'
        assert metadata.file_path == '/test/file1.jpg'
        assert metadata.file_type == 'image'
        assert metadata.segment_id is None
    
    @pytest.mark.asyncio
    async def test_vector_storage_manager_initialization(self, vector_storage_manager, mock_config_manager):
        """测试向量存储管理器初始化"""
        assert vector_storage_manager is not None
        assert vector_storage_manager.config_manager == mock_config_manager
        assert vector_storage_manager.milvus_adapter is not None
        # 向量维度使用VectorType枚举作为键
        assert VectorType.VISUAL in vector_storage_manager.vector_dimensions
        assert vector_storage_manager.vector_dimensions[VectorType.VISUAL] == 512
    
    @pytest.mark.asyncio
    async def test_store_vector(self, vector_storage_manager, mock_milvus_adapter):
        """测试存储向量"""
        metadata = VectorMetadata(
            file_id='file_1',
            file_path='/test/file1.jpg',
            file_name='file1.jpg',
            file_type='image',
            file_size=1024,
            created_at=1234567890.123,
            segment_id='seg_1',
            start_time=0.0,
            end_time=5.0
        )
        
        vector = np.random.rand(512).astype(np.float32)
        
        vector_id = await vector_storage_manager.store_vector(
            vector_type=VectorType.VISUAL,
            vector_data=vector,
            metadata=metadata
        )
        
        assert vector_id == "vec_123"
        mock_milvus_adapter.store_vector.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_vectors(self, vector_storage_manager, mock_milvus_adapter):
        """测试搜索向量"""
        query_vector = np.random.rand(512).astype(np.float32)
        
        results = await vector_storage_manager.search_vectors(
            vector_type=VectorType.VISUAL,
            query_vector=query_vector,
            limit=5
        )
        
        assert isinstance(results, list)
        assert len(results) > 0
        mock_milvus_adapter.search_vectors.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_vectors_with_threshold(self, vector_storage_manager, mock_milvus_adapter):
        """测试带阈值的向量搜索"""
        query_vector = np.random.rand(512).astype(np.float32)
        
        results = await vector_storage_manager.search_vectors(
            vector_type=VectorType.VISUAL,
            query_vector=query_vector,
            limit=10,
            score_threshold=0.8
        )
        
        assert isinstance(results, list)
    
    @pytest.mark.asyncio
    async def test_search_audio_vectors(self, vector_storage_manager, mock_milvus_adapter):
        """测试搜索音频向量"""
        query_vector = np.random.rand(512).astype(np.float32)
        
        results = await vector_storage_manager.search_vectors(
            vector_type=VectorType.AUDIO_MUSIC,
            query_vector=query_vector,
            limit=3
        )
        
        assert isinstance(results, list)
        call_args = mock_milvus_adapter.search_vectors.call_args
        assert call_args[1]['collection_type'] == 'audio_music'
    
    @pytest.mark.asyncio
    async def test_search_face_vectors(self, vector_storage_manager, mock_milvus_adapter):
        """测试搜索人脸向量"""
        query_vector = np.random.rand(512).astype(np.float32)
        
        results = await vector_storage_manager.search_vectors(
            vector_type=VectorType.FACE,
            query_vector=query_vector,
            limit=2
        )
        
        assert isinstance(results, list)
        call_args = mock_milvus_adapter.search_vectors.call_args
        assert call_args[1]['collection_type'] == 'face'
    
    @pytest.mark.asyncio
    async def test_delete_vectors_by_file(self, vector_storage_manager, mock_milvus_adapter):
        """测试按文件删除向量"""
        result = await vector_storage_manager.delete_vectors_by_file('test_file_id')
        
        assert isinstance(result, dict)
        assert 'visual' in result
        mock_milvus_adapter.delete_vectors_by_file.assert_called()
    
    @pytest.mark.asyncio
    async def test_get_vector_count(self, vector_storage_manager, mock_milvus_adapter):
        """测试获取向量数量"""
        # 测试获取指定类型数量
        count = await vector_storage_manager.get_vector_count(VectorType.VISUAL)
        assert count == 50
        mock_milvus_adapter.get_vector_count.assert_called()
    
    @pytest.mark.asyncio
    async def test_get_all_vector_counts(self, vector_storage_manager, mock_milvus_adapter):
        """测试获取所有类型向量数量"""
        counts = await vector_storage_manager.get_vector_count()
        assert isinstance(counts, dict)
    
    @pytest.mark.asyncio
    async def test_health_check(self, vector_storage_manager, mock_milvus_adapter):
        """测试健康检查"""
        health = await vector_storage_manager.health_check()
        
        assert isinstance(health, dict)
        assert 'status' in health
        assert 'milvus' in health
        mock_milvus_adapter.health_check.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_collection_mapping(self, vector_storage_manager):
        """测试集合映射"""
        assert vector_storage_manager.collection_mapping[VectorType.VISUAL] == 'visual_vectors'
        assert vector_storage_manager.collection_mapping[VectorType.AUDIO_MUSIC] == 'audio_music_vectors'
        assert vector_storage_manager.collection_mapping[VectorType.FACE] == 'face_vectors'
    
    @pytest.mark.asyncio
    async def test_vector_dimension_validation(self, vector_storage_manager):
        """测试向量维度验证"""
        metadata = VectorMetadata(
            file_id='file_1',
            file_path='/test/file1.jpg',
            file_name='file1.jpg',
            file_type='image',
            file_size=1024,
            created_at=1234567890.123
        )
        
        # 正确维度的向量
        valid_vector = np.random.rand(512).astype(np.float32)
        
        # 无效维度的向量应该抛出异常
        invalid_vector = np.random.rand(256).astype(np.float32)
        
        with pytest.raises(ValueError):
            await vector_storage_manager.store_vector(
                vector_type=VectorType.VISUAL,
                vector_data=invalid_vector,
                metadata=metadata
            )
    
    @pytest.mark.asyncio
    async def test_search_with_list_input(self, vector_storage_manager, mock_milvus_adapter):
        """测试使用列表输入搜索"""
        query_vector = np.random.rand(512).astype(np.float32)
        
        # 转换为列表
        query_list = query_vector.tolist()
        
        results = await vector_storage_manager.search_vectors(
            vector_type=VectorType.VISUAL,
            query_vector=query_list,
            limit=5
        )
        
        assert isinstance(results, list)
    
    @pytest.mark.asyncio
    async def test_hybrid_search(self, vector_storage_manager, mock_milvus_adapter):
        """测试混合搜索"""
        # 设置搜索返回结果
        mock_milvus_adapter.search_vectors.return_value = [
            {
                'id': 'vec_1',
                'score': 0.8,
                'payload': {
                    'file_id': 'file_1',
                    'file_path': '/test/file1.jpg',
                    'file_name': 'file1.jpg',
                    'file_type': 'image',
                    'file_size': 1024,
                    'created_at': 1234567890.123
                }
            }
        ]
        
        query_vectors = {
            VectorType.VISUAL: np.random.rand(512).astype(np.float32),
            VectorType.AUDIO_MUSIC: np.random.rand(512).astype(np.float32)
        }
        
        results = await vector_storage_manager.hybrid_search(
            query_vectors=query_vectors,
            limit=5
        )
        
        assert isinstance(results, list)
    
    @pytest.mark.asyncio
    async def test_get_collection_stats(self, vector_storage_manager, mock_milvus_adapter):
        """测试获取集合统计"""
        mock_milvus_adapter.get_collection_info.return_value = {
            'vectors_count': 100,
            'status': 'ready'
        }
        
        stats = await vector_storage_manager.get_collection_stats()
        
        assert isinstance(stats, dict)
    
    @pytest.mark.asyncio
    async def test_batch_store_vectors(self, vector_storage_manager, mock_milvus_adapter):
        """测试批量存储向量"""
        metadata1 = VectorMetadata(
            file_id='file_1',
            file_path='/test/file1.jpg',
            file_name='file1.jpg',
            file_type='image',
            file_size=1024,
            created_at=1234567890.123
        )
        
        metadata2 = VectorMetadata(
            file_id='file_2',
            file_path='/test/file2.jpg',
            file_name='file2.jpg',
            file_type='image',
            file_size=2048,
            created_at=1234567891.123
        )
        
        vectors_data = [
            (VectorType.VISUAL, np.random.rand(512).astype(np.float32), metadata1),
            (VectorType.VISUAL, np.random.rand(512).astype(np.float32), metadata2)
        ]
        
        vector_ids = await vector_storage_manager.batch_store_vectors(vectors_data)
        
        assert isinstance(vector_ids, list)
    
    @pytest.mark.asyncio
    async def test_cleanup(self, vector_storage_manager, mock_milvus_adapter):
        """测试清理资源"""
        result = await vector_storage_manager.cleanup()
        
        assert result is True
        mock_milvus_adapter.disconnect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_error_handling_in_search(self, vector_storage_manager, mock_milvus_adapter):
        """测试搜索中的错误处理"""
        # 模拟搜索失败
        mock_milvus_adapter.search_vectors.side_effect = Exception("Search failed")
        
        query_vector = np.random.rand(512).astype(np.float32)
        
        with pytest.raises(Exception):
            await vector_storage_manager.search_vectors(
                vector_type=VectorType.VISUAL,
                query_vector=query_vector
            )
        
        # 恢复正常
        mock_milvus_adapter.search_vectors.side_effect = None
        mock_milvus_adapter.search_vectors.return_value = []
        
        results = await vector_storage_manager.search_vectors(
            vector_type=VectorType.VISUAL,
            query_vector=query_vector
        )
        assert results == []
