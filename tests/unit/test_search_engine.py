"""
SearchEngine 单元测试
测试搜索引擎的核心功能，包括多模态搜索、结果融合等
"""

import pytest
import numpy as np
import asyncio
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from src.business.search_engine import SearchEngine
from src.business.embedding_engine import EmbeddingEngine, get_embedding_engine
from src.storage.vector_store import VectorStore, get_vector_store
from src.core.config import load_config


class TestSearchEngine:
    """SearchEngine测试类"""
    
    @pytest.fixture
    def config(self):
        """测试配置"""
        return {
            'search.top_k': 10,
            'search.similarity_threshold': 0.3
        }
    
    @pytest.fixture
    def mock_vector_store(self):
        """模拟向量存储"""
        mock = Mock(spec=VectorStore)
        
        # 模拟搜索结果
        async def mock_search(collection_name, query_vector, limit=10, filters=None):
            return [
                {
                    "id": f"point_{i}",
                    "score": 0.95 - i * 0.1,
                    "payload": {
                        "file_id": i + 1,
                        "file_path": f"/path/to/file_{i}.mp4",
                        "segment_type": "video",
                        "start_time_ms": i * 10000,
                        "end_time_ms": (i + 1) * 10000
                    }
                }
                for i in range(min(limit, 5))
            ]
        
        mock.search = AsyncMock(side_effect=mock_search)
        
        return mock
    
    @pytest.fixture
    def mock_embedding_engine(self):
        """模拟嵌入引擎"""
        mock = Mock(spec=EmbeddingEngine)
        
        # 模拟向量化结果
        async def mock_embed_content(content, content_type):
            # 返回固定维度的模拟向量
            if content_type == 'text':
                return np.random.rand(512).astype(np.float32)
            elif content_type == 'image':
                return np.random.rand(512).astype(np.float32)
            elif content_type in ['audio_music', 'audio_speech']:
                return np.random.rand(512).astype(np.float32)
            else:
                return np.random.rand(512).astype(np.float32)
        
        mock.embed_content = AsyncMock(side_effect=mock_embed_content)
        
        return mock
    
    @pytest.fixture
    def search_engine(self, config, mock_vector_store, mock_embedding_engine):
        """搜索引擎实例"""
        return SearchEngine(config, mock_vector_store, mock_embedding_engine)
    
    @pytest.mark.asyncio
    async def test_search_by_vector(self, search_engine, mock_vector_store):
        """测试基于向量的搜索"""
        # 准备测试数据
        query_vector = np.random.rand(512).astype(np.float32)
        collection_name = "test_collection"
        
        # 执行搜索
        results = await search_engine.search_by_vector(query_vector, collection_name, top_k=5)
        
        # 验证结果
        assert len(results) == 5, f"预期5个结果，实际{len(results)}个"
        assert mock_vector_store.search.called, "向量存储应该被调用"
        
        # 验证搜索参数
        call_args = mock_vector_store.search.call_args
        assert call_args[0][0] == collection_name, "集合名称应该匹配"
        assert call_args[0][2] == 5, "limit参数应该匹配"
        
        # 验证结果格式
        for result in results:
            assert 'id' in result, "结果应该包含ID"
            assert 'score' in result, "结果应该包含分数"
            assert 'payload' in result, "结果应该包含负载数据"
            assert result['score'] >= search_engine.similarity_threshold, "分数应该超过阈值"
    
    @pytest.mark.asyncio
    async def test_text_search(self, search_engine, mock_embedding_engine, mock_vector_store):
        """测试文本搜索"""
        query_text = "测试搜索文本"
        
        # 执行搜索
        results = await search_engine._search_text(query_text)
        
        # 验证嵌入引擎被调用
        assert mock_embedding_engine.embed_content.called, "嵌入引擎应该被调用"
        
        # 验证向量存储被调用
        assert mock_vector_store.search.called, "向量存储应该被调用"
        
        # 验证结果
        assert len(results) == 5, f"预期5个结果，实际{len(results)}个"
    
    @pytest.mark.asyncio
    async def test_image_search(self, search_engine, mock_embedding_engine, mock_vector_store):
        """测试图片搜索"""
        query_image = np.random.rand(224, 224, 3).astype(np.uint8)
        
        # 执行搜索
        results = await search_engine._search_image(query_image)
        
        # 验证嵌入引擎被调用
        assert mock_embedding_engine.embed_content.called, "嵌入引擎应该被调用"
        
        # 验证向量存储被调用
        assert mock_vector_store.search.called, "向量存储应该被调用"
        
        # 验证结果
        assert len(results) == 5, f"预期5个结果，实际{len(results)}个"
    
    @pytest.mark.asyncio
    async def test_audio_search(self, search_engine, mock_embedding_engine, mock_vector_store):
        """测试音频搜索"""
        query_audio = np.random.rand(16000).astype(np.float32)  # 1秒音频
        
        # 执行搜索
        results = await search_engine._search_audio(query_audio)
        
        # 验证嵌入引擎被调用
        assert mock_embedding_engine.embed_content.called, "嵌入引擎应该被调用"
        
        # 验证向量存储被调用
        assert mock_vector_store.search.called, "向量存储应该被调用"
        
        # 验证结果
        assert len(results) == 5, f"预期5个结果，实际{len(results)}个"
    
    @pytest.mark.asyncio
    async def test_multimodal_search_text_only(self, search_engine):
        """测试纯文本多模态搜索"""
        query_data = {'text': '测试多模态搜索'}
        
        # 执行搜索
        results = await search_engine.multimodal_search(query_data)
        
        # 验证结果结构
        assert results['status'] == 'success', "搜索状态应该成功"
        assert 'query_id' in results, "结果应该包含查询ID"
        assert 'results' in results, "结果应该包含搜索结果"
        assert 'modality_results' in results, "结果应该包含各模态结果"
        
        # 验证文本结果被包含
        assert 'text' in results['modality_results'], "应该包含文本搜索结果"
        assert len(results['modality_results']['text']) == 5, "应该有5个文本搜索结果"
    
    @pytest.mark.asyncio
    async def test_multimodal_search_multiple_modalities(self, search_engine):
        """测试多模态搜索（文本+图片）"""
        query_data = {
            'text': '测试文本搜索',
            'image': np.random.rand(224, 224, 3).astype(np.uint8)
        }
        
        # 执行搜索
        results = await search_engine.multimodal_search(query_data)
        
        # 验证结果结构
        assert results['status'] == 'success', "搜索状态应该成功"
        assert 'text' in results['modality_results'], "应该包含文本搜索结果"
        assert 'image' in results['modality_results'], "应该包含图片搜索结果"
        assert len(results['results']) > 0, "应该有融合后的结果"
    
    def test_result_fusion(self, search_engine):
        """测试结果融合"""
        # 准备模拟的多模态结果
        modality_results = {
            'text': [
                {'file_id': 1, 'score': 0.9, 'payload': {'path': 'file1.mp4'}},
                {'file_id': 2, 'score': 0.8, 'payload': {'path': 'file2.mp4'}},
            ],
            'image': [
                {'file_id': 1, 'score': 0.85, 'payload': {'path': 'file1.mp4'}},
                {'file_id': 3, 'score': 0.75, 'payload': {'path': 'file3.mp4'}},
            ]
        }
        
        # 执行结果融合
        fused_results = search_engine._fuse_results(modality_results)
        
        # 验证融合结果
        assert len(fused_results) == 3, "应该融合出3个不同的文件"
        
        # 验证文件1（出现在两个模态中）
        file1_results = [r for r in fused_results if r['file_id'] == 1]
        assert len(file1_results) == 1, "文件1应该只有一个融合结果"
        
        file1_result = file1_results[0]
        assert file1_result['score'] == pytest.approx(0.875, rel=1e-3), "文件1的得分应该是平均值"
        assert 'text' in file1_result['modalities'], "文件1应该包含文本模态"
        assert 'image' in file1_result['modalities'], "文件1应该包含图片模态"
        assert file1_result['modality_count'] == 2, "文件1应该有2个模态"
    
    @pytest.mark.asyncio
    async def test_search_with_error_handling(self, search_engine, mock_vector_store):
        """测试错误处理"""
        # 模拟向量存储抛出异常
        mock_vector_store.search.side_effect = Exception("模拟错误")
        
        # 执行搜索
        results = await search_engine.search_by_vector(
            np.random.rand(512), "test_collection"
        )
        
        # 验证错误处理
        assert results == [], "搜索失败时应该返回空列表"
    
    @pytest.mark.asyncio
    async def test_multimodal_search_with_error(self, search_engine, mock_embedding_engine):
        """测试多模态搜索的错误处理"""
        # 模拟嵌入引擎抛出异常
        mock_embedding_engine.embed_content.side_effect = Exception("嵌入失败")
        
        query_data = {'text': '测试错误处理'}
        
        # 执行搜索
        results = await search_engine.multimodal_search(query_data)
        
        # 验证错误处理 - 由于SearchEngine的设计，错误被捕获在模态方法中
        # 所以多模态搜索仍然成功，但结果为空
        assert results['status'] == 'success', "搜索状态应该成功（错误被模态方法捕获）"
        assert 'query_id' in results, "结果应该包含查询ID"
        assert 'modality_results' in results, "结果应该包含模态结果"
        assert len(results['modality_results']['text']) == 0, "文本结果应该为空（因为嵌入失败）"
    
    @pytest.mark.asyncio
    async def test_empty_query_handling(self, search_engine):
        """测试空查询处理"""
        query_data = {}  # 空查询
        
        # 执行搜索
        results = await search_engine.multimodal_search(query_data)
        
        # 验证空查询处理
        assert results['status'] == 'success', "空查询应该成功"
        assert len(results['results']) == 0, "空查询应该返回空结果"
        assert len(results['modality_results']) == 0, "空查询不应该有模态结果"


@pytest.mark.asyncio
async def test_search_engine_integration():
    """集成测试：使用真实组件"""
    print("\n=== 测试 SearchEngine 集成 ===")
    
    # 加载配置
    config = load_config()
    
    # 获取真实组件
    embedding_engine = get_embedding_engine(config)
    vector_store = get_vector_store()
    
    # 创建搜索引擎
    search_engine = SearchEngine(config, vector_store, embedding_engine)
    
    # 测试文本搜索
    print("测试文本搜索...")
    text_results = await search_engine._search_text("测试搜索")
    print(f"文本搜索结果数量: {len(text_results)}")
    
    # 测试图片搜索
    print("测试图片搜索...")
    test_image = np.random.rand(224, 224, 3).astype(np.float32)
    image_results = await search_engine._search_image(test_image)
    print(f"图片搜索结果数量: {len(image_results)}")
    
    # 测试多模态搜索
    print("测试多模态搜索...")
    query_data = {
        'text': '测试多模态搜索',
        'image': test_image
    }
    
    multimodal_results = await search_engine.multimodal_search(query_data)
    print(f"多模态搜索状态: {multimodal_results['status']}")
    print(f"融合结果数量: {len(multimodal_results['results'])}")
    print(f"各模态结果: {list(multimodal_results['modality_results'].keys())}")
    
    print("✓ SearchEngine 集成测试通过")


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "-s"])