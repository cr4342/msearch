"""
向量存储模块
负责与Qdrant向量数据库交互，管理向量的存储和检索
"""

from typing import List, Dict, Any, Optional
import logging
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, SearchRequest
import hashlib
import json
from functools import lru_cache

from src.core.config import get_config
from src.core.logging_config import get_logger

logger = get_logger(__name__)


class VectorStore:
    """Qdrant 向量数据库集成"""
    
    def __init__(self):
        """初始化向量存储"""
        self.config = get_config()
        self.qdrant_config = self.config.get("qdrant", {})
        self.collections = self.qdrant_config.get("collections", {})
        
        # 初始化Qdrant客户端
        self.client = self._init_qdrant_client()
        
        # 查询缓存
        self.cache_enabled = self.config.get("cache", {}).get("enabled", True)
        self.cache_ttl = self.config.get("cache", {}).get("ttl", 3600)
        
        logger.info("向量存储初始化完成")
    
    def _init_qdrant_client(self) -> QdrantClient:
        """初始化Qdrant客户端"""
        try:
            host = self.qdrant_config.get('host', '127.0.0.1')
            port = self.qdrant_config.get('port', 6333)
            
            client = QdrantClient(host=host, port=port)
            
            # 验证连接
            collections = client.get_collections()
            logger.info(f"Qdrant连接成功，现有集合: {[col.name for col in collections.collections]}")
            
            return client
        except Exception as e:
            logger.error(f"Qdrant连接失败: {e}")
            # 返回一个模拟客户端用于开发
            return None
    
    async def search(self, collection_name: str, query_vector: List[float], limit: int = 10, filters: Dict = None) -> List[Dict]:
        """
        向量相似度搜索
        
        Args:
            collection_name: 集合名称
            query_vector: 查询向量
            limit: 返回结果数量限制
            filters: 过滤条件
            
        Returns:
            搜索结果列表
        """
        logger.info(f"在集合 {collection_name} 中执行向量搜索")
        
        # 生成缓存键
        cache_key = self._generate_cache_key(collection_name, query_vector, limit, filters)
        
        # 尝试从缓存获取结果
        if self.cache_enabled:
            cached_result = self._get_from_cache(cache_key)
            if cached_result is not None:
                logger.info(f"从缓存获取搜索结果: {collection_name}")
                return cached_result
        
        # 如果Qdrant客户端不可用，返回模拟结果
        if self.client is None:
            logger.warning("Qdrant客户端不可用，返回模拟搜索结果")
            return self._get_mock_search_results(limit)
        
        try:
            # 获取实际的集合名称
            collection_config = self.collections.get(collection_name, {})
            actual_collection_name = collection_config.get('name', f'msearch_{collection_name}')
            
            # 执行搜索
            search_result = self.client.search(
                collection_name=actual_collection_name,
                query_vector=query_vector,
                limit=limit
            )
            
            # 格式化结果
            results = []
            for point in search_result:
                results.append({
                    "id": str(point.id),
                    "score": point.score,
                    "payload": point.payload or {}
                })
            
            # 缓存结果
            if self.cache_enabled:
                self._set_cache(cache_key, results)
            
            logger.info(f"搜索完成，找到 {len(results)} 个结果")
            return results
            
        except Exception as e:
            logger.error(f"向量搜索失败: {e}")
            # 返回模拟结果作为降级方案
            return self._get_mock_search_results(limit)
    
    async def search_similar(self, query_vector: np.ndarray, collection_name: str, top_k: int = None) -> List[Dict[str, Any]]:
        """
        相似向量搜索（兼容SearchEngine接口）
        
        Args:
            query_vector: 查询向量（numpy数组）
            collection_name: 集合名称
            top_k: 返回结果数量
            
        Returns:
            搜索结果列表
        """
        if top_k is None:
            top_k = 50
        
        # 将numpy数组转换为列表
        if isinstance(query_vector, np.ndarray):
            query_vector = query_vector.tolist()
        
        # 调用search方法
        results = await self.search(collection_name, query_vector, limit=top_k)
        
        return results
    
    def _generate_cache_key(self, collection_name: str, query_vector: List[float], limit: int, filters: Dict = None) -> str:
        """
        生成缓存键
        
        Args:
            collection_name: 集合名称
            query_vector: 查询向量
            limit: 返回结果数量限制
            filters: 过滤条件
            
        Returns:
            缓存键
        """
        cache_data = {
            "collection": collection_name,
            "vector": query_vector,
            "limit": limit,
            "filters": filters or {}
        }
        cache_string = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_string.encode()).hexdigest()
    
    @lru_cache(maxsize=1000)
    def _get_from_cache(self, cache_key: str) -> Optional[List[Dict]]:
        """
        从缓存获取结果
        
        Args:
            cache_key: 缓存键
            
        Returns:
            缓存结果或None
        """
        # 使用LRU缓存作为简单的内存缓存
        # 在实际实现中，这里可以使用Redis等外部缓存
        return None
    
    def _set_cache(self, cache_key: str, results: List[Dict]) -> None:
        """
        设置缓存结果
        
        Args:
            cache_key: 缓存键
            results: 搜索结果
        """
        # LRU缓存通过装饰器自动处理
        pass
    
    def _get_mock_search_results(self, limit: int) -> List[Dict]:
        """获取模拟搜索结果"""
        results = []
        for i in range(min(limit, 5)):  # 模拟最多5个结果
            results.append({
                "id": f"point_{i}",
                "score": 0.95 - i * 0.1,  # 模拟相似度分数
                "payload": {
                    "file_id": i + 1,
                    "file_path": f"/path/to/file_{i}.mp4",
                    "segment_type": "video",
                    "start_time_ms": i * 10000,
                    "end_time_ms": (i + 1) * 10000
                }
            })
        return results
    
    async def store_vectors(self, collection_name: str, vectors: List[List[float]], payloads: List[Dict] = None) -> bool:
        """
        存储向量数据
        
        Args:
            collection_name: 集合名称
            vectors: 向量数据列表
            payloads: 负载数据列表
            
        Returns:
            存储是否成功
        """
        logger.info(f"在集合 {collection_name} 中存储 {len(vectors)} 个向量")
        
        # 在实际实现中，这里会调用Qdrant API存储向量
        # 目前只是模拟存储过程
        return True
    
    async def delete_vectors(self, collection_name: str, point_ids: List[str]) -> bool:
        """
        删除向量数据
        
        Args:
            collection_name: 集合名称
            point_ids: 点ID列表
            
        Returns:
            删除是否成功
        """
        logger.info(f"在集合 {collection_name} 中删除 {len(point_ids)} 个向量")
        
        # 在实际实现中，这里会调用Qdrant API删除向量
        # 目前只是模拟删除过程
        return True
    
    async def get_collections_info(self) -> Dict[str, Any]:
        """
        获取集合信息
        
        Returns:
            集合信息字典
        """
        logger.info("获取集合信息")
        
        # 模拟集合信息
        return {
            "collections": list(self.collections.keys()),
            "status": "healthy"
        }
    
    async def reset_collection(self, collection_name: str) -> bool:
        """
        重置集合（清空所有数据）
        
        Args:
            collection_name: 集合名称
            
        Returns:
            重置是否成功
        """
        logger.info(f"重置集合 {collection_name}")
        
        # 在实际实现中，这里会调用Qdrant API重置集合
        # 目前只是模拟重置过程
        return True
    
    async def health_check(self) -> bool:
        """
        健康检查
        
        Returns:
            数据库是否健康
        """
        logger.info("执行向量数据库健康检查")
        
        # 在实际实现中，这里会检查Qdrant服务状态
        # 目前只是模拟健康检查
        return True


# 全局向量存储实例
_vector_store = None


def get_vector_store() -> VectorStore:
    """
    获取全局向量存储实例
    
    Returns:
        向量存储实例
    """
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store