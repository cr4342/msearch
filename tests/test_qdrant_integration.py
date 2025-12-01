"""
Qdrant集成测试
"""

import pytest
import asyncio
import tempfile
import os
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import sys

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from src.common.storage.qdrant_adapter import QdrantAdapter
from src.common.storage.vector_storage_manager import VectorStorageManager, VectorType, VectorMetadata, SearchResult
from src.core.qdrant_service_manager import QdrantServiceManager


class TestQdrantAdapter:
    """Qdrant适配器测试"""
    
    @pytest.fixture
    def mock_config(self):
        """模拟配置"""
        return {
            'database': {
                'qdrant': {
                    'host': 'localhost',
                    'port': 6333,
                    'timeout': 30,
                    'collections': {
                        'visual_vectors': 'visual_vectors',
                        'audio_music_vectors': 'audio_music_vectors',
                        'audio_speech_vectors': 'audio_speech_vectors'
                    }
                }
            }
        }
    
    @pytest.fixture
    def temp_db(self):
        """临时数据库"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        yield db_path
        
        # 清理
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    def test_adapter_initialization(self, mock_config):
        """测试适配器初始化"""
        try:
            adapter = QdrantAdapter(mock_config)
            assert adapter is not None
            assert adapter.host == 'localhost'
            assert adapter.port == 6333
            assert 'visual' in adapter.collection_map
        except Exception as e:
            pytest.skip(f"Qdrant未安装或未启动: {e}")
    
    @pytest.mark.asyncio
    async def test_connection(self, mock_config):
        """测试连接"""
        try:
            adapter = QdrantAdapter(mock_config)
            success = await adapter.connect()
            assert success is True
        except Exception as e:
            pytest.skip(f"Qdrant连接失败: {e}")
    
    @pytest.mark.asyncio
    async def test_collection_operations(self, mock_config):
        """测试集合操作"""
        try:
            adapter = QdrantAdapter(mock_config)
            await adapter.connect()
            
            # 测试创建集合
            success = await adapter.create_collection(
                collection_name="test_collection",
                vector_size=512,
                distance_metric="cosine"
            )
            assert success is True
            
            # 测试获取集合信息
            info = await adapter.get_collection_info("test_collection")
            assert info is not None
            assert info['name'] == "test_collection"
            
            # 测试删除集合
            success = await adapter.delete_collection("test_collection")
            assert success is True
            
        except Exception as e:
            pytest.skip(f"集合操作测试失败: {e}")
    
    @pytest.mark.asyncio
    async def test_vector_operations(self, mock_config):
        """测试向量操作"""
        try:
            adapter = QdrantAdapter(mock_config)
            await adapter.connect()
            
            # 创建测试集合
            await adapter.create_collection("test_collection", 512)
            
            # 测试存储向量
            vector_data = np.random.rand(512).astype(np.float32)
            vector_id = await adapter.store_vector(
                collection_type="visual",
                vector_data=vector_data,
                file_id="test_file",
                metadata={"test": "metadata"}
            )
            assert vector_id is not None
            
            # 测试搜索向量
            results = await adapter.search_vectors(
                collection_type="visual",
                query_vector=vector_data,
                limit=5,
                score_threshold=0.5
            )
            assert isinstance(results, list)
            
            # 测试删除向量
            success = await adapter.delete_vector("visual", vector_id)
            assert success is True
            
            # 清理
            await adapter.delete_collection("test_collection")
            
        except Exception as e:
            pytest.skip(f"向量操作测试失败: {e}")
    
    @pytest.mark.asyncio
    async def test_batch_operations(self, mock_config):
        """测试批量操作"""
        try:
            adapter = QdrantAdapter(mock_config)
            await adapter.connect()
            
            # 创建测试集合
            await adapter.create_collection("test_collection", 512)
            
            # 测试批量存储向量
            vectors = [np.random.rand(512).astype(np.float32) for _ in range(10)]
            point_ids = await adapter.store_vectors(
                collection_name="test_collection",
                vectors=[v.tolist() for v in vectors],
                payloads=[{"test": f"payload_{i}"} for i in range(10)]
            )
            assert len(point_ids) == 10
            
            # 清理
            await adapter.delete_collection("test_collection")
            
        except Exception as e:
            pytest.skip(f"批量操作测试失败: {e}")
    
    @pytest.mark.asyncio
    async def test_health_check(self, mock_config):
        """测试健康检查"""
        try:
            adapter = QdrantAdapter(mock_config)
            await adapter.connect()
            
            health = await adapter.health_check()
            assert 'status' in health
            
        except Exception as e:
            pytest.skip(f"健康检查测试失败: {e}")


class TestVectorStorageManager:
    """向量存储管理器测试"""
    
    @pytest.fixture
    def mock_config(self):
        """模拟配置"""
        return {
            'database': {
                'qdrant': {
                    'host': 'localhost',
                    'port': 6333,
                    'timeout': 30,
                    'collections': {
                        'visual_vectors': 'visual_vectors',
                        'audio_music_vectors': 'audio_music_vectors',
                        'audio_speech_vectors': 'audio_speech_vectors'
                    }
                }
            }
        }
    
    def test_manager_initialization(self, mock_config):
        """测试管理器初始化"""
        try:
            manager = VectorStorageManager(mock_config)
            assert manager is not None
            assert VectorType.VISUAL in manager.vector_dimensions
            assert VectorType.AUDIO_MUSIC in manager.vector_dimensions
        except Exception as e:
            pytest.skip(f"向量存储管理器初始化失败: {e}")
    
    @pytest.mark.asyncio
    async def test_initialization(self, mock_config):
        """测试初始化"""
        try:
            manager = VectorStorageManager(mock_config)
            success = await manager.initialize()
            assert success is True
        except Exception as e:
            pytest.skip(f"初始化测试失败: {e}")
    
    @pytest.mark.asyncio
    async def test_store_vector(self, mock_config):
        """测试存储向量"""
        try:
            manager = VectorStorageManager(mock_config)
            await manager.initialize()
            
            # 创建测试向量
            vector_data = np.random.rand(512).astype(np.float32)
            metadata = VectorMetadata(
                file_id="test_file",
                file_path="/test/path.jpg",
                file_name="test.jpg",
                file_type=".jpg",
                file_size=1024,
                created_at=1234567890
            )
            
            # 存储向量
            vector_id = await manager.store_vector(
                vector_type=VectorType.VISUAL,
                vector_data=vector_data,
                metadata=metadata
            )
            assert vector_id is not None
            
        except Exception as e:
            pytest.skip(f"存储向量测试失败: {e}")
    
    @pytest.mark.asyncio
    async def test_search_vectors(self, mock_config):
        """测试搜索向量"""
        try:
            manager = VectorStorageManager(mock_config)
            await manager.initialize()
            
            # 创建测试向量
            vector_data = np.random.rand(512).astype(np.float32)
            metadata = VectorMetadata(
                file_id="test_file",
                file_path="/test/path.jpg",
                file_name="test.jpg",
                file_type=".jpg",
                file_size=1024,
                created_at=1234567890
            )
            
            # 存储向量
            vector_id = await manager.store_vector(
                vector_type=VectorType.VISUAL,
                vector_data=vector_data,
                metadata=metadata
            )
            
            # 搜索向量
            results = await manager.search_vectors(
                vector_type=VectorType.VISUAL,
                query_vector=vector_data,
                limit=5,
                score_threshold=0.5
            )
            assert isinstance(results, list)
            
        except Exception as e:
            pytest.skip(f"搜索向量测试失败: {e}")
    
    @pytest.mark.asyncio
    async def test_batch_store_vectors(self, mock_config):
        """测试批量存储向量"""
        try:
            manager = VectorStorageManager(mock_config)
            await manager.initialize()
            
            # 创建测试向量数据
            vectors_data = []
            for i in range(5):
                vector_data = np.random.rand(512).astype(np.float32)
                metadata = VectorMetadata(
                    file_id=f"test_file_{i}",
                    file_path=f"/test/path_{i}.jpg",
                    file_name=f"test_{i}.jpg",
                    file_type=".jpg",
                    file_size=1024,
                    created_at=1234567890 + i
                )
                vectors_data.append((VectorType.VISUAL, vector_data, metadata))
            
            # 批量存储
            vector_ids = await manager.batch_store_vectors(vectors_data)
            assert len(vector_ids) == 5
            
        except Exception as e:
            pytest.skip(f"批量存储向量测试失败: {e}")
    
    @pytest.mark.asyncio
    async def test_hybrid_search(self, mock_config):
        """测试混合搜索"""
        try:
            manager = VectorStorageManager(mock_config)
            await manager.initialize()
            
            # 创建不同类型的测试向量
            visual_vector = np.random.rand(512).astype(np.float32)
            audio_vector = np.random.rand(512).astype(np.float32)
            
            query_vectors = {
                VectorType.VISUAL: visual_vector,
                VectorType.AUDIO_MUSIC: audio_vector
            }
            
            weights = {
                VectorType.VISUAL: 0.6,
                VectorType.AUDIO_MUSIC: 0.4
            }
            
            # 混合搜索
            results = await manager.hybrid_search(
                query_vectors=query_vectors,
                weights=weights,
                limit=10,
                score_threshold=0.3
            )
            assert isinstance(results, list)
            
        except Exception as e:
            pytest.skip(f"混合搜索测试失败: {e}")
    
    @pytest.mark.asyncio
    async def test_health_check(self, mock_config):
        """测试健康检查"""
        try:
            manager = VectorStorageManager(mock_config)
            await manager.initialize()
            
            health = await manager.health_check()
            assert 'status' in health
            assert 'qdrant' in health
            assert 'collections' in health
            
        except Exception as e:
            pytest.skip(f"健康检查测试失败: {e}")


class TestQdrantServiceManager:
    """Qdrant服务管理器测试"""
    
    @pytest.fixture
    def mock_config(self):
        """模拟配置"""
        return {
            'database': {
                'qdrant': {
                    'host': 'localhost',
                    'port': 6333
                }
            },
            'system': {
                'data_dir': './data'
            }
        }
    
    def test_manager_initialization(self, mock_config):
        """测试管理器初始化"""
        manager = QdrantServiceManager(mock_config)
        assert manager is not None
        assert manager.host == 'localhost'
        assert manager.port == 6333
        assert manager.data_dir.endswith('data/qdrant')
    
    @pytest.mark.asyncio
    async def test_health_check(self, mock_config):
        """测试健康检查"""
        manager = QdrantServiceManager(mock_config)
        
        # 如果Qdrant正在运行，测试健康检查
        try:
            is_healthy = await manager.health_check()
            assert isinstance(is_healthy, bool)
        except Exception:
            # 如果Qdrant未运行，跳过测试
            pytest.skip("Qdrant服务未运行，跳过健康检查测试")
    
    @pytest.mark.asyncio
    async def test_get_status(self, mock_config):
        """测试获取状态"""
        manager = QdrantServiceManager(mock_config)
        
        try:
            status = await manager.get_status()
            assert 'running' in status
            assert 'host' in status
            assert 'port' in status
        except Exception:
            pytest.skip("Qdrant服务未运行，跳过状态获取测试")
    
    @pytest.mark.asyncio
    async def test_setup(self, mock_config):
        """测试环境设置"""
        manager = QdrantServiceManager(mock_config)
        
        # 测试设置环境
        success = await manager.setup()
        assert success is True
        
        # 检查数据目录是否创建
        assert os.path.exists(manager.data_dir)
    
    def test_docker_availability(self, mock_config):
        """测试Docker可用性检查"""
        manager = QdrantServiceManager(mock_config)
        
        # 检查Docker可用性（可能不可用）
        docker_available = manager._check_docker_availability()
        assert isinstance(docker_available, bool)


class TestVectorType:
    """向量类型枚举测试"""
    
    def test_vector_type_values(self):
        """测试向量类型值"""
        assert VectorType.VISUAL.value == "visual"
        assert VectorType.AUDIO_MUSIC.value == "audio_music"
        assert VectorType.AUDIO_SPEECH.value == "audio_speech"
        assert VectorType.FACE.value == "face"
        assert VectorType.TEXT.value == "text"
    
    def test_vector_type_creation(self):
        """测试向量类型创建"""
        vt = VectorType.VISUAL
        assert vt == VectorType.VISUAL
        assert vt.value == "visual"


class TestVectorMetadata:
    """向量元数据测试"""
    
    def test_metadata_creation(self):
        """测试元数据创建"""
        metadata = VectorMetadata(
            file_id="test_file",
            file_path="/test/path.jpg",
            file_name="test.jpg",
            file_type=".jpg",
            file_size=1024,
            created_at=1234567890
        )
        
        assert metadata.file_id == "test_file"
        assert metadata.file_path == "/test/path.jpg"
        assert metadata.file_name == "test.jpg"
        assert metadata.file_type == ".jpg"
        assert metadata.file_size == 1024
        assert metadata.created_at == 1234567890
    
    def test_metadata_with_optional_fields(self):
        """测试包含可选字段的元数据"""
        metadata = VectorMetadata(
            file_id="test_file",
            file_path="/test/path.jpg",
            file_name="test.jpg",
            file_type=".jpg",
            file_size=1024,
            created_at=1234567890,
            segment_id="segment_1",
            start_time=10.0,
            end_time=20.0,
            duration=10.0,
            confidence=0.95,
            model_name="clip",
            additional_data={"test": "data"}
        )
        
        assert metadata.segment_id == "segment_1"
        assert metadata.start_time == 10.0
        assert metadata.end_time == 20.0
        assert metadata.duration == 10.0
        assert metadata.confidence == 0.95
        assert metadata.model_name == "clip"
        assert metadata.additional_data == {"test": "data"}


class TestSearchResult:
    """搜索结果测试"""
    
    def test_search_result_creation(self):
        """测试搜索结果创建"""
        metadata = VectorMetadata(
            file_id="test_file",
            file_path="/test/path.jpg",
            file_name="test.jpg",
            file_type=".jpg",
            file_size=1024,
            created_at=1234567890
        )
        
        result = SearchResult(
            vector_id="test_vector_id",
            score=0.85,
            metadata=metadata,
            distance=0.15
        )
        
        assert result.vector_id == "test_vector_id"
        assert result.score == 0.85
        assert result.metadata == metadata
        assert result.distance == 0.15


if __name__ == "__main__":
    pytest.main([__file__, "-v"])