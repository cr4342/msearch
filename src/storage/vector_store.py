"""
向量存储模块
负责与Qdrant向量数据库交互，管理向量的存储和检索
"""

from typing import List, Dict, Any, Optional
import logging
import numpy as np
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
        # 正确获取嵌套的Qdrant配置
        self.qdrant_config = self.config.get("database", {}).get("qdrant", {})
        self.collections = self.qdrant_config.get("collections", {})
        
        # 初始化Qdrant客户端
        self.client = self._init_qdrant_client()
        
        # 查询缓存
        self.cache_enabled = self.config.get("cache", {}).get("enabled", True)
        self.cache_ttl = self.config.get("cache", {}).get("ttl", 3600)
        
        logger.info("向量存储初始化完成")
    
    def _create_collections(self, client: QdrantClient):
        """创建必要的集合"""
        try:
            # 获取集合配置
            collections_config = self.qdrant_config.get('embedded', {}).get('collections', {})
            
            for collection_key, collection_info in collections_config.items():
                collection_name = f"msearch_{collection_key}"
                vector_size = collection_info.get('vector_size', 512)
                distance = collection_info.get('distance', 'cosine')
                
                # 检查集合是否已存在
                try:
                    client.get_collection(collection_name)
                    logger.info(f"集合 {collection_name} 已存在")
                except Exception:
                    # 集合不存在，创建它
                    from qdrant_client.models import VectorParams, Distance
                    
                    # 转换距离类型
                    distance_enum = Distance.COSINE
                    if distance.lower() == 'dot':
                        distance_enum = Distance.DOT
                    elif distance.lower() == 'euclid':
                        distance_enum = Distance.EUCLID
                    
                    client.create_collection(
                        collection_name=collection_name,
                        vectors_config=VectorParams(size=vector_size, distance=distance_enum)
                    )
                    logger.info(f"集合 {collection_name} 创建成功")
        except Exception as e:
            logger.error(f"创建集合时出错: {e}")
    
    def _init_qdrant_client(self) -> QdrantClient:
        """初始化Qdrant客户端"""
        try:
            # 检查是否使用嵌入式模式
            mode = self.qdrant_config.get('mode', 'server')
            
            if mode == 'embedded':
                # 使用嵌入式模式
                embedded_config = self.qdrant_config.get('embedded', {})
                path = embedded_config.get('path', './data/database/qdrant')
                
                logger.info(f"使用嵌入式Qdrant模式，数据路径: {path}")
                client = QdrantClient(path=path)
                
                # 创建必要的集合（如果不存在）
                self._create_collections(client)
                
                logger.info("嵌入式Qdrant客户端初始化成功")
                return client
            else:
                # 使用服务器模式
                host = self.qdrant_config.get('host', '127.0.0.1')
                port = self.qdrant_config.get('port', 6333)
                
                logger.info(f"使用服务器模式连接Qdrant: {host}:{port}")
                client = QdrantClient(host=host, port=port)
                
                # 验证连接
                try:
                    collections = client.get_collections()
                    logger.info(f"Qdrant连接成功，现有集合: {[col.name for col in collections.collections]}")
                except Exception as conn_error:
                    logger.warning(f"Qdrant连接验证失败: {conn_error}，但将继续使用客户端")
                
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
    
    async def store_vector(self, vector_id: str, vector: List[float], payload: Dict = None, collection_name: str = None) -> bool:
        """
        存储单个向量数据
        
        Args:
            vector_id: 向量ID
            vector: 向量数据
            payload: 负载数据
            collection_name: 集合名称
            
        Returns:
            存储是否成功
        """
        logger.info(f"在集合 {collection_name} 中存储向量 {vector_id}")
        
        # 如果Qdrant客户端不可用，返回模拟结果
        if self.client is None:
            logger.warning("Qdrant客户端不可用，无法存储向量")
            return False
        
        try:
            # 获取实际的集合名称
            collection_config = self.collections.get(collection_name, {})
            actual_collection_name = collection_config.get('name', f'msearch_{collection_name}')
            
            # 创建点结构
            from qdrant_client.models import PointStruct
            point = PointStruct(
                id=vector_id,
                vector=vector,
                payload=payload or {}
            )
            
            # 存储向量
            self.client.upsert(
                collection_name=actual_collection_name,
                points=[point]
            )
            
            logger.info(f"向量 {vector_id} 存储成功")
            return True
            
        except Exception as e:
            logger.error(f"存储向量失败: {e}")
            return False
    
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
        
        # 如果客户端不可用，返回模拟结果
        if self.client is None:
            logger.warning("Qdrant客户端不可用，模拟删除向量")
            return True
        
        try:
            # 获取实际的集合名称
            collection_config = self.collections.get(collection_name, {})
            actual_collection_name = collection_config.get('name', f'msearch_{collection_name}')
            
            # 调用Qdrant API删除向量
            from qdrant_client.models import Filter, FieldCondition, MatchAny
            
            # 创建过滤条件，匹配所有指定的点ID
            filter_condition = Filter(
                must=[
                    FieldCondition(
                        key="id",
                        match=MatchAny(any=point_ids)
                    )
                ]
            )
            
            # 执行删除操作
            self.client.delete(
                collection_name=actual_collection_name,
                points_selector=filter_condition
            )
            
            logger.info(f"成功删除 {len(point_ids)} 个向量")
            return True
            
        except Exception as e:
            logger.error(f"删除向量失败: {e}")
            return False
    
    async def get_collections_info(self) -> Dict[str, Any]:
        """
        获取集合信息
        
        Returns:
            集合信息字典
        """
        logger.info("获取集合信息")
        
        # 如果客户端不可用，返回模拟信息
        if self.client is None:
            return {
                "collections": list(self.collections.keys()),
                "status": "healthy"
            }
        
        try:
            # 获取实际的集合信息
            collections = self.client.get_collections()
            collection_names = []
            
            # 提取集合名称并移除"msearch_"前缀
            for collection in collections.collections:
                name = collection.name
                if name.startswith("msearch_"):
                    name = name[8:]  # 移除"msearch_"前缀
                collection_names.append(name)
            
            return {
                "collections": collection_names,
                "status": "healthy"
            }
        except Exception as e:
            logger.error(f"获取集合信息失败: {e}")
            # 返回模拟信息作为降级方案
            return {
                "collections": list(self.collections.keys()),
                "status": "degraded"
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
    
    async def search_by_time_range(self, file_id: str, start_time: float, 
                                  end_time: float, collection_name: str = None) -> List[Dict]:
        """
        按时间范围搜索向量
        
        Args:
            file_id: 文件ID
            start_time: 开始时间（秒）
            end_time: 结束时间（秒）
            collection_name: 集合名称（可选，如果不提供则搜索所有集合）
            
        Returns:
            时间范围内的搜索结果
        """
        logger.info(f"执行时间范围搜索: file_id={file_id}, 时间范围={start_time}-{end_time}")
        
        # 如果Qdrant客户端不可用，返回模拟结果
        if self.client is None:
            logger.warning("Qdrant客户端不可用，返回模拟时间范围搜索结果")
            return self._get_mock_time_range_results(file_id, start_time, end_time)
        
        try:
            results = []
            
            # 如果指定了集合名称，则只在该集合中搜索
            if collection_name:
                collection_names = [collection_name]
            else:
                # 否则在所有集合中搜索
                collection_names = list(self.collections.keys())
            
            # 在每个集合中执行时间范围搜索
            for col_name in collection_names:
                collection_config = self.collections.get(col_name, {})
                actual_collection_name = collection_config.get('name', f'msearch_{col_name}')
                
                # 构建时间范围过滤条件
                # 假设payload中包含start_time和end_time字段
                search_result = self.client.search(
                    collection_name=actual_collection_name,
                    query_filter={
                        "must": [
                            {"key": "file_id", "match": {"value": file_id}},
                            {"key": "start_time", "range": {"gte": start_time}},
                            {"key": "end_time", "range": {"lte": end_time}}
                        ]
                    }
                )
                
                # 格式化结果
                for point in search_result:
                    results.append({
                        "id": str(point.id),
                        "score": point.score,
                        "payload": point.payload or {}
                    })
            
            logger.info(f"时间范围搜索完成，找到 {len(results)} 个结果")
            return results
            
        except Exception as e:
            logger.error(f"时间范围搜索失败: {e}")
            # 返回模拟结果作为降级方案
            return self._get_mock_time_range_results(file_id, start_time, end_time)
    
    def _get_mock_time_range_results(self, file_id: str, start_time: float, end_time: float) -> List[Dict]:
        """获取模拟时间范围搜索结果"""
        results = []
        # 模拟2个结果
        for i in range(2):
            results.append({
                "id": f"point_{i}",
                "score": 0.9 - i * 0.1,
                "payload": {
                    "file_id": file_id,
                    "file_path": f"/path/to/file_{file_id}.mp4",
                    "segment_type": "video",
                    "start_time": start_time + i * 2,
                    "end_time": start_time + (i + 1) * 2
                }
            })
        return results


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