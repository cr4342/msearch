"""
向量存储模块单元测试
测试VectorStore的核心功能
"""

import unittest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import asyncio
import sys
import os
import numpy as np

# 添加项目根目录到Python路径
project_root = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, project_root)

from src.storage.vector_store import VectorStore


class TestVectorStore(unittest.IsolatedAsyncioTestCase):
    """向量存储模块单元测试"""
    
    def setUp(self):
        """测试前的准备工作"""
        # 配置
        self.config = {
            "qdrant": {
                "host": "127.0.0.1",
                "port": 6333,
                "collections": {
                    "text_vectors": {
                        "name": "msearch_text_vectors"
                    },
                    "image_vectors": {
                        "name": "msearch_image_vectors"
                    },
                    "audio_vectors": {
                        "name": "msearch_audio_vectors"
                    }
                }
            },
            "cache": {
                "enabled": True,
                "ttl": 3600
            }
        }
    
    @patch('src.storage.vector_store.QdrantClient')
    def test_vector_store_initialization(self, mock_qdrant_client):
        """测试向量存储初始化"""
        # 创建模拟的Qdrant客户端
        mock_client_instance = Mock()
        mock_qdrant_client.return_value = mock_client_instance
        
        # 模拟get_collections方法返回
        mock_collections = Mock()
        mock_collections.collections = [Mock(name="msearch_text_vectors")]
        mock_client_instance.get_collections.return_value = mock_collections
        
        # 创建向量存储实例
        with patch('src.storage.vector_store.get_config', return_value=self.config):
            vector_store = VectorStore()
        
        # 验证Qdrant客户端是否被正确初始化
        self.assertIsNotNone(vector_store.client)
        self.assertTrue(vector_store.cache_enabled)
        self.assertEqual(vector_store.cache_ttl, 3600)
    
    @patch('src.storage.vector_store.QdrantClient')
    async def test_vector_search(self, mock_qdrant_client):
        """测试向量相似度搜索"""
        # 创建模拟的Qdrant客户端
        mock_client_instance = Mock()
        mock_qdrant_client.return_value = mock_client_instance
        
        # 模拟搜索结果
        mock_search_result = [
            Mock(id="point_1", score=0.95, payload={"file_id": 1, "file_path": "/path/file1.mp4"}),
            Mock(id="point_2", score=0.85, payload={"file_id": 2, "file_path": "/path/file2.jpg"})
        ]
        mock_client_instance.search.return_value = mock_search_result
        
        # 创建向量存储实例
        with patch('src.storage.vector_store.get_config', return_value=self.config):
            vector_store = VectorStore()
            vector_store.client = mock_client_instance  # 替换为模拟客户端
        
        # 执行搜索
        query_vector = [0.1, 0.2, 0.3, 0.4, 0.5]  # 5维查询向量
        results = await vector_store.search("text_vectors", query_vector, limit=10)
        
        # 验证结果
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["id"], "point_1")
        self.assertEqual(results[0]["score"], 0.95)
        self.assertEqual(results[0]["payload"]["file_id"], 1)
        self.assertEqual(results[1]["id"], "point_2")
        self.assertEqual(results[1]["score"], 0.85)
        
        # 验证Qdrant客户端的search方法是否被正确调用
        mock_client_instance.search.assert_called_once_with(
            collection_name="msearch_text_vectors",
            query_vector=query_vector,
            limit=10
        )
    
    @patch('src.storage.vector_store.QdrantClient')
    async def test_search_similar(self, mock_qdrant_client):
        """测试相似向量搜索"""
        # 创建模拟的Qdrant客户端
        mock_client_instance = Mock()
        mock_qdrant_client.return_value = mock_client_instance
        
        # 模拟搜索结果
        mock_search_result = [
            Mock(id="point_1", score=0.92, payload={"file_id": 3, "file_path": "/path/file3.wav"})
        ]
        mock_client_instance.search.return_value = mock_search_result
        
        # 创建向量存储实例
        with patch('src.storage.vector_store.get_config', return_value=self.config):
            vector_store = VectorStore()
            vector_store.client = mock_client_instance  # 替换为模拟客户端
        
        # 执行相似向量搜索
        query_vector = np.array([0.2, 0.3, 0.4, 0.5, 0.6])  # numpy数组
        results = await vector_store.search_similar(query_vector, "audio_vectors", top_k=20)
        
        # 验证结果
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], "point_1")
        self.assertEqual(results[0]["score"], 0.92)
        
        # 验证Qdrant客户端的search方法是否被正确调用
        # 注意：numpy数组应该被转换为列表
        mock_client_instance.search.assert_called_once_with(
            collection_name="msearch_audio_vectors",
            query_vector=[0.2, 0.3, 0.4, 0.5, 0.6],
            limit=20
        )
    
    @patch('src.storage.vector_store.QdrantClient')
    async def test_search_by_time_range(self, mock_qdrant_client):
        """测试按时间范围搜索"""
        # 创建模拟的Qdrant客户端
        mock_client_instance = Mock()
        mock_qdrant_client.return_value = mock_client_instance
        
        # 模拟时间范围搜索结果
        mock_search_result = [
            Mock(id="point_1", score=0.88, payload={
                "file_id": "file_123",
                "file_path": "/path/file123.mp4",
                "start_time": 10.5,
                "end_time": 15.2
            }),
            Mock(id="point_2", score=0.82, payload={
                "file_id": "file_123",
                "file_path": "/path/file123.mp4",
                "start_time": 18.0,
                "end_time": 22.5
            })
        ]
        mock_client_instance.search.return_value = mock_search_result
        
        # 创建向量存储实例
        with patch('src.storage.vector_store.get_config', return_value=self.config):
            vector_store = VectorStore()
            vector_store.client = mock_client_instance  # 替换为模拟客户端
        
        # 执行时间范围搜索
        results = await vector_store.search_by_time_range(
            file_id="file_123",
            start_time=10.0,
            end_time=25.0,
            collection_name="image_vectors"
        )
        
        # 验证结果
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["id"], "point_1")
        self.assertEqual(results[0]["score"], 0.88)
        self.assertEqual(results[0]["payload"]["start_time"], 10.5)
        self.assertEqual(results[0]["payload"]["end_time"], 15.2)
        self.assertEqual(results[1]["id"], "point_2")
        self.assertEqual(results[1]["score"], 0.82)
        
        # 验证Qdrant客户端的search方法是否被正确调用
        expected_filter = {
            "must": [
                {"key": "file_id", "match": {"value": "file_123"}},
                {"key": "start_time", "range": {"gte": 10.0}},
                {"key": "end_time", "range": {"lte": 25.0}}
            ]
        }
        mock_client_instance.search.assert_called_once_with(
            collection_name="msearch_image_vectors",
            query_filter=expected_filter
        )
    
    @patch('src.storage.vector_store.QdrantClient')
    async def test_store_vectors(self, mock_qdrant_client):
        """测试存储向量数据"""
        # 创建模拟的Qdrant客户端
        mock_client_instance = Mock()
        mock_qdrant_client.return_value = mock_client_instance
        
        # 创建向量存储实例
        with patch('src.storage.vector_store.get_config', return_value=self.config):
            vector_store = VectorStore()
            vector_store.client = mock_client_instance  # 替换为模拟客户端
        
        # 准备测试数据
        vectors = [
            [0.1, 0.2, 0.3],
            [0.4, 0.5, 0.6],
            [0.7, 0.8, 0.9]
        ]
        payloads = [
            {"file_id": 1, "file_path": "/path/file1.txt"},
            {"file_id": 2, "file_path": "/path/file2.jpg"},
            {"file_id": 3, "file_path": "/path/file3.mp4"}
        ]
        
        # 执行存储操作
        result = await vector_store.store_vectors("text_vectors", vectors, payloads)
        
        # 验证结果（模拟总是成功）
        self.assertTrue(result)
    
    @patch('src.storage.vector_store.QdrantClient')
    async def test_delete_vectors(self, mock_qdrant_client):
        """测试删除向量数据"""
        # 创建模拟的Qdrant客户端
        mock_client_instance = Mock()
        mock_qdrant_client.return_value = mock_client_instance
        
        # 创建向量存储实例
        with patch('src.storage.vector_store.get_config', return_value=self.config):
            vector_store = VectorStore()
            vector_store.client = mock_client_instance  # 替换为模拟客户端
        
        # 准备测试数据
        point_ids = ["point_1", "point_2", "point_3"]
        
        # 执行删除操作
        result = await vector_store.delete_vectors("image_vectors", point_ids)
        
        # 验证结果（模拟总是成功）
        self.assertTrue(result)
    
    @patch('src.storage.vector_store.QdrantClient')
    async def test_get_collections_info(self, mock_qdrant_client):
        """测试获取集合信息"""
        # 创建模拟的Qdrant客户端
        mock_client_instance = Mock()
        mock_qdrant_client.return_value = mock_client_instance
        
        # 模拟集合信息
        mock_collection_1 = Mock()
        mock_collection_1.name = "msearch_text_vectors"
        mock_collection_2 = Mock()
        mock_collection_2.name = "msearch_image_vectors"
        mock_collections = Mock()
        mock_collections.collections = [mock_collection_1, mock_collection_2]
        mock_client_instance.get_collections.return_value = mock_collections
        
        # 创建向量存储实例
        with patch('src.storage.vector_store.get_config', return_value=self.config):
            vector_store = VectorStore()
            vector_store.client = mock_client_instance  # 替换为模拟客户端
        
        # 获取集合信息
        info = await vector_store.get_collections_info()
        
        # 验证结果
        self.assertEqual(info["status"], "healthy")
        self.assertIn("text_vectors", info["collections"])
        self.assertIn("image_vectors", info["collections"])
    
    @patch('src.storage.vector_store.QdrantClient')
    async def test_reset_collection(self, mock_qdrant_client):
        """测试重置集合"""
        # 创建模拟的Qdrant客户端
        mock_client_instance = Mock()
        mock_qdrant_client.return_value = mock_client_instance
        
        # 创建向量存储实例
        with patch('src.storage.vector_store.get_config', return_value=self.config):
            vector_store = VectorStore()
            vector_store.client = mock_client_instance  # 替换为模拟客户端
        
        # 执行重置操作
        result = await vector_store.reset_collection("audio_vectors")
        
        # 验证结果（模拟总是成功）
        self.assertTrue(result)
    
    @patch('src.storage.vector_store.QdrantClient')
    async def test_health_check(self, mock_qdrant_client):
        """测试健康检查"""
        # 创建模拟的Qdrant客户端
        mock_client_instance = Mock()
        mock_qdrant_client.return_value = mock_client_instance
        
        # 创建向量存储实例
        with patch('src.storage.vector_store.get_config', return_value=self.config):
            vector_store = VectorStore()
            vector_store.client = mock_client_instance  # 替换为模拟客户端
        
        # 执行健康检查
        result = await vector_store.health_check()
        
        # 验证结果（模拟总是健康）
        self.assertTrue(result)
    
    def test_generate_cache_key(self):
        """测试生成缓存键"""
        with patch('src.storage.vector_store.get_config', return_value=self.config):
            vector_store = VectorStore()
        
        # 生成缓存键
        cache_key = vector_store._generate_cache_key(
            "text_vectors",
            [0.1, 0.2, 0.3],
            10,
            {"file_type": "image"}
        )
        
        # 验证缓存键不为空且是字符串
        self.assertIsInstance(cache_key, str)
        self.assertGreater(len(cache_key), 0)
        
        # 验证相同输入生成相同键
        cache_key_2 = vector_store._generate_cache_key(
            "text_vectors",
            [0.1, 0.2, 0.3],
            10,
            {"file_type": "image"}
        )
        self.assertEqual(cache_key, cache_key_2)
        
        # 验证不同输入生成不同键
        cache_key_3 = vector_store._generate_cache_key(
            "image_vectors",
            [0.1, 0.2, 0.3],
            10,
            {"file_type": "image"}
        )
        self.assertNotEqual(cache_key, cache_key_3)


if __name__ == '__main__':
    unittest.main()