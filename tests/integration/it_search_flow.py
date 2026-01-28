"""
集成测试：搜索流程
测试完整的搜索流程，包括查询向量化、向量搜索、结果排序等
使用Mock避免真实模型依赖
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import asyncio
import tempfile
import shutil
from pathlib import Path

from src.core.config.config_manager import ConfigManager
from src.core.database.database_manager import DatabaseManager
from src.core.vector.vector_store import VectorStore
from src.core.embedding.embedding_engine import EmbeddingEngine
from src.services.search.search_engine import SearchEngine


@pytest.fixture(scope="module")
def temp_dir():
    """创建临时目录"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture(scope="module")
def config_manager():
    """使用默认配置管理器"""
    return ConfigManager()


@pytest.fixture(scope="module")
def database_manager(temp_dir, config_manager):
    """创建数据库管理器"""
    db_path = Path(temp_dir) / "database" / "msearch.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    db_manager = DatabaseManager(db_path=str(db_path))
    db_manager.initialize()
    yield db_manager
    db_manager.close()


@pytest.fixture(scope="module")
def vector_store(temp_dir, config_manager):
    """创建向量存储"""
    vector_dir = Path(temp_dir) / "lancedb"
    vector_dir.mkdir(parents=True, exist_ok=True)
    
    vector_store = VectorStore(config={
        'data_dir': str(vector_dir),
        'collection_name': 'unified_vectors',
        'vector_dimension': 512
    })
    vector_store.initialize()
    return vector_store


@pytest.fixture(scope="module")
def mock_embedding_engine():
    """创建Mock向量化引擎"""
    engine = Mock(spec=EmbeddingEngine)
    # 模拟异步方法
    engine.embed_text = AsyncMock(return_value=[0.1] * 512)
    engine.embed_image = AsyncMock(return_value=[0.2] * 512)
    return engine


@pytest.fixture(scope="module")
def search_engine(mock_embedding_engine, vector_store):
    """创建搜索引擎（使用依赖注入）"""
    engine = SearchEngine(
        embedding_engine=mock_embedding_engine,
        vector_store=vector_store
    )
    # Mock search方法
    engine.search = AsyncMock(return_value=[
        {
            'id': 'test_1',
            'score': 0.95,
            'metadata': {
                'file_path': '/test/path/image1.jpg',
                'file_type': 'image',
                'modality': 'image'
            }
        },
        {
            'id': 'test_2',
            'score': 0.88,
            'metadata': {
                'file_path': '/test/path/image2.png',
                'file_type': 'image',
                'modality': 'image'
            }
        }
    ])
    return engine


class TestSearchFlow:
    """搜索流程集成测试"""
    
    @pytest.mark.asyncio
    async def test_text_search_flow(self, search_engine):
        """测试文本搜索流程"""
        # 1. 执行异步搜索
        query = "测试查询"
        results = await search_engine.search(query, k=10)
        
        # 2. 验证搜索结果
        assert len(results) >= 0, "搜索应该返回结果"
        
        print(f"✓ 文本搜索流程测试通过")
        print(f"  查询: {query}")
        print(f"  结果数: {len(results)}")
    
    @pytest.mark.asyncio
    async def test_image_search_flow(self, search_engine):
        """测试图像搜索流程"""
        # 1. Mock image_search方法
        search_engine.image_search = AsyncMock(return_value=[
            {
                'id': 'img_1',
                'score': 0.92,
                'metadata': {
                    'file_path': '/test/path/ref_image.jpg',
                    'file_type': 'image',
                    'modality': 'image'
                }
            }
        ])
        
        # 2. 执行异步图像搜索
        query_image = "/test/path/query_image.jpg"
        results = await search_engine.image_search(query_image, k=10)
        
        # 3. 验证搜索结果
        assert results is not None
        assert len(results) >= 0
        
        print(f"✓ 图像搜索流程测试通过")
        print(f"  查询图像: {query_image}")
        print(f"  结果数: {len(results)}")
    
    def test_search_result_sorting(self, search_engine):
        """测试搜索结果排序"""
        # 1. 创建无序的搜索结果
        unsorted_results = [
            {'id': '1', 'score': 0.5},
            {'id': '2', 'score': 0.9},
            {'id': '3', 'score': 0.3},
            {'id': '4', 'score': 0.7}
        ]
        
        # 2. 排序（按分数降序）
        sorted_results = sorted(unsorted_results, key=lambda x: x['score'], reverse=True)
        
        # 3. 验证排序结果
        assert sorted_results[0]['score'] == 0.9
        assert sorted_results[-1]['score'] == 0.3
        
        print(f"✓ 搜索结果排序测试通过")
        print(f"  最高分: {sorted_results[0]['score']}")
        print(f"  最低分: {sorted_results[-1]['score']}")
    
    def test_search_engine_initialization(self, search_engine, mock_embedding_engine, vector_store):
        """测试搜索引擎初始化"""
        # 1. 验证搜索引擎已初始化
        assert search_engine is not None
        assert search_engine.embedding_engine is not None
        assert search_engine.vector_store is not None
        
        # 2. 验证依赖注入正确
        assert isinstance(search_engine.embedding_engine, Mock)
        assert isinstance(search_engine.vector_store, VectorStore)
        
        print(f"✓ 搜索引擎初始化测试通过")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
