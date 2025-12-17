"""
Qdrant向量存储适配器
为多模态检索系统提供Qdrant向量数据库的封装
"""

import asyncio
import logging
import uuid
from typing import Dict, Any, Optional, List, Tuple

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    Distance, VectorParams, PointStruct,
    Filter, FieldCondition, MatchValue, MatchAny
)

from src.core.config_manager import get_config_manager


class QdrantAdapter:
    """Qdrant向量存储适配器"""
    
    def __init__(self, config_manager=None):
        self.config_manager = config_manager or get_config_manager()
        self.logger = logging.getLogger(__name__)
        
        # Qdrant配置
        self.host = self.config_manager.get("database.qdrant.host", "localhost")
        self.port = self.config_manager.get("database.qdrant.port", 6333)
        self.timeout = self.config_manager.get("database.qdrant.timeout", 30)
        
        # 集合配置
        self.collections_config = self.config_manager.get("database.qdrant.collections", {})
        
        # 客户端
        self.client: Optional[QdrantClient] = None
        
        # 集合映射
        self.collection_map = {
            'visual': self.collections_config.get('visual_vectors', 'visual_vectors'),
            'audio_music': self.collections_config.get('audio_music_vectors', 'audio_music_vectors'),
            'audio_speech': self.collections_config.get('audio_speech_vectors', 'audio_speech_vectors')
        }
        
        self.logger.info("Qdrant适配器初始化完成")
    
    async def connect(self) -> bool:
        """连接到Qdrant"""
        try:
            await self.initialize()
            return True
        except Exception as e:
            self.logger.error(f"Qdrant连接失败: {e}")
            return False
    
    async def disconnect(self):
        """断开Qdrant连接"""
        try:
            if self.client:
                # Qdrant客户端没有明确的断开连接方法
                # 清理资源
                self.client = None
                self.logger.info("Qdrant连接已断开")
        except Exception as e:
            self.logger.error(f"断开Qdrant连接失败: {e}")
    
    async def initialize(self):
        """初始化Qdrant客户端"""
        try:
            # 创建客户端
            self.client = QdrantClient(
                host=self.host,
                port=self.port,
                timeout=self.timeout,
                grpc_port=self.port + 1  # gRPC端口通常是HTTP端口+1
            )
            
            # 测试连接
            await self._test_connection()
            
            # 初始化集合
            await self._initialize_collections()
            
            self.logger.info("Qdrant客户端初始化完成")
            
        except Exception as e:
            self.logger.error(f"Qdrant初始化失败: {e}")
            raise
    
    async def _test_connection(self):
        """测试连接"""
        try:
            # 获取集合列表
            collections = self.client.get_collections()
            self.logger.info(f"Qdrant连接成功，当前集合数量: {len(collections.collections)}")
        except Exception as e:
            self.logger.error(f"Qdrant连接测试失败: {e}")
            raise
    
    async def _initialize_collections(self):
        """初始化向量集合"""
        try:
            # 检查并创建视觉向量集合
            await self._create_collection_if_not_exists(
                self.collection_map['visual'],
                512,  # CLIP模型向量维度
                "视觉向量集合，用于图像和视频检索"
            )
            
            # 检查并创建音频音乐向量集合
            await self._create_collection_if_not_exists(
                self.collection_map['audio_music'],
                512,  # CLAP模型向量维度
                "音频音乐向量集合，用于音乐检索"
            )
            
            # 检查并创建音频语音向量集合
            await self._create_collection_if_not_exists(
                self.collection_map['audio_speech'],
                512,  # Whisper模型向量维度
                "音频语音向量集合，用于语音检索"
            )
            
            self.logger.info("Qdrant集合初始化完成")
            
        except Exception as e:
            self.logger.error(f"集合初始化失败: {e}")
            raise
    
    async def _create_collection_if_not_exists(self, collection_name: str, vector_size: int, description: str):
        """创建集合（如果不存在）"""
        try:
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if collection_name not in collection_names:
                # 创建集合
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=vector_size,
                        distance=Distance.COSINE
                    )
                )
                
                self.logger.info(f"创建集合成功: {collection_name}")
            else:
                self.logger.debug(f"集合已存在: {collection_name}")
                
        except Exception as e:
            self.logger.error(f"创建集合失败: {collection_name}, 错误: {e}")
            raise
    
    async def store_vector(self, 
                          collection_type: str, 
                          vector_data: np.ndarray, 
                          file_id: str,
                          segment_id: Optional[str] = None,
                          metadata: Optional[Dict[str, Any]] = None,
                          vector_id: Optional[str] = None) -> str:
        """
        存储向量
        
        Args:
            collection_type: 集合类型 ('visual', 'audio_music', 'audio_speech')
            vector_data: 向量数据
            file_id: 文件ID
            segment_id: 片段ID（可选）
            metadata: 元数据
            vector_id: 向量ID（可选，如果为None则自动生成）
            
        Returns:
            向量ID
        """
        try:
            if self.client is None:
                await self.initialize()
            
            collection_name = self.collection_map.get(collection_type)
            if not collection_name:
                raise ValueError(f"不支持的集合类型: {collection_type}")
            
            # 生成或使用提供的向量ID
            if vector_id is None:
                vector_id = str(uuid.uuid4())
            
            # 准备负载数据
            payload = {
                'file_id': file_id,
                'segment_id': segment_id,
                'collection_type': collection_type,
                'created_at': asyncio.get_event_loop().time(),
                **(metadata or {})
            }
            
            # 创建点数据
            point = PointStruct(
                id=vector_id,
                vector=vector_data.tolist(),
                payload=payload
            )
            
            # 插入向量
            self.client.upsert(
                collection_name=collection_name,
                points=[point]
            )
            
            self.logger.debug(f"向量存储成功: {vector_id}, 集合: {collection_name}")
            return vector_id
            
        except Exception as e:
            self.logger.error(f"存储向量失败: {e}")
            raise
    
    async def search_vectors(self, 
                           collection_type: str, 
                           query_vector: np.ndarray, 
                           limit: int = 10,
                           score_threshold: float = 0.7,
                           filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        搜索向量
        
        Args:
            collection_type: 集合类型
            query_vector: 查询向量
            limit: 返回结果数量限制
            score_threshold: 相似度阈值
            filters: 过滤条件
            
        Returns:
            搜索结果列表
        """
        try:
            if self.client is None:
                await self.initialize()
            
            collection_name = self.collection_map.get(collection_type)
            if not collection_name:
                raise ValueError(f"不支持的集合类型: {collection_type}")
            
            # 构建过滤条件
            search_filter = self._build_filter(filters) if filters else None
            
            # 搜索向量
            # 处理不同版本的Qdrant客户端方法名差异
            try:
                search_results = self.client.search(
                    collection_name=collection_name,
                    query_vector=query_vector.tolist(),
                    limit=limit,
                    score_threshold=score_threshold,
                    query_filter=search_filter
                )
            except AttributeError:
                # 尝试使用旧版本的方法名
                search_results = self.client.search_points(
                    collection_name=collection_name,
                    query_vector=query_vector.tolist(),
                    limit=limit,
                    score_threshold=score_threshold,
                    query_filter=search_filter
                )
            
            # 格式化结果
            results = []
            for result in search_results:
                results.append({
                    'id': str(result.id),
                    'score': result.score,
                    'payload': result.payload
                })
            
            return results
            
        except Exception as e:
            self.logger.error(f"搜索向量失败: {e}")
            raise
    
    async def create_collection(self, 
                              collection_name: str, 
                              vector_size: int = 512,
                              distance_metric: str = "cosine") -> bool:
        """创建集合"""
        try:
            if self.client is None:
                await self.initialize()
            
            # 检查集合是否已存在
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if collection_name in collection_names:
                self.logger.info(f"集合已存在: {collection_name}")
                return True
            
            # 创建集合
            distance = Distance.COSINE if distance_metric == "cosine" else Distance.EUCLID
            
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=distance
                )
            )
            
            self.logger.info(f"集合创建成功: {collection_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"创建集合失败: {collection_name}, 错误: {e}")
            return False
    
    async def delete_collection(self, collection_name: str) -> bool:
        """删除集合"""
        try:
            if self.client is None:
                await self.initialize()
            
            self.client.delete_collection(collection_name=collection_name)
            
            self.logger.info(f"集合删除成功: {collection_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"删除集合失败: {collection_name}, 错误: {e}")
            return False
    
    async def store_vectors(self, 
                          collection_name: str,
                          vectors: List[List[float]],
                          point_ids: Optional[List[str]] = None,
                          payloads: Optional[List[Dict[str, Any]]] = None) -> List[str]:
        """存储向量"""
        try:
            if self.client is None:
                await self.initialize()
            
            # 生成ID列表
            if point_ids is None:
                point_ids = [str(uuid.uuid4()) for _ in vectors]
            
            if payloads is None:
                payloads = [{} for _ in vectors]
            
            # 创建点数据
            points = []
            for i, (vector, point_id, payload) in enumerate(zip(vectors, point_ids, payloads)):
                point = PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=payload
                )
                points.append(point)
            
            # 批量插入
            self.client.upsert(
                collection_name=collection_name,
                points=points
            )
            
            return point_ids
            
        except Exception as e:
            self.logger.error(f"存储向量失败: {e}")
            raise
    
    async def delete_vectors(self, 
                           collection_name: str,
                           point_ids: List[str]) -> bool:
        """删除向量"""
        try:
            if self.client is None:
                await self.initialize()
            
            # 转换ID格式
            ids = [uuid.UUID(point_id) if isinstance(point_id, str) else point_id 
                   for point_id in point_ids]
            
            # 删除向量
            for point_id in ids:
                self.client.delete(
                    collection_name=collection_name,
                    points_selector=point_id
                )
            
            return True
            
        except Exception as e:
            self.logger.error(f"删除向量失败: {e}")
            return False
    
    async def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """获取集合信息"""
        try:
            if self.client is None:
                await self.initialize()
            
            collection_info = self.client.get_collection(collection_name)
            
            return {
                'name': collection_name,
                'vectors_count': collection_info.vectors_count,
                'status': str(collection_info.status),
                'config': {
                    'vectors': str(collection_info.config.params.vectors) if collection_info.config.params.vectors else None
                }
            }
            
        except Exception as e:
            self.logger.error(f"获取集合信息失败: {collection_name}, 错误: {e}")
            return {}
    
    async def delete_vector(self, collection_type: str, vector_id: str) -> bool:
        """删除单个向量"""
        try:
            if self.client is None:
                await self.initialize()
            
            collection_name = self.collection_map.get(collection_type)
            if not collection_name:
                raise ValueError(f"不支持的集合类型: {collection_type}")
            
            # 转换ID格式
            point_id = uuid.UUID(vector_id) if isinstance(vector_id, str) else vector_id
            
            # 删除向量
            self.client.delete(
                collection_name=collection_name,
                points_selector=point_id
            )
            
            self.logger.debug(f"向量删除成功: {vector_id}, 集合: {collection_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"删除向量失败: {e}")
            return False
    
    async def delete_vectors_by_file(self, collection_type: str, file_id: str) -> int:
        """根据文件ID删除向量"""
        try:
            if self.client is None:
                await self.initialize()
            
            collection_name = self.collection_map.get(collection_type)
            if not collection_name:
                raise ValueError(f"不支持的集合类型: {collection_type}")
            
            # 构建过滤条件
            filter_condition = Filter(
                must=[
                    FieldCondition(
                        key="file_id",
                        match=MatchValue(value=file_id)
                    )
                ]
            )
            
            # 删除匹配的向量
            result = self.client.delete(
                collection_name=collection_name,
                points_selector=filter_condition
            )
            
            self.logger.info(f"文件向量删除完成: {file_id}, 集合: {collection_name}")
            return result.count
            
        except Exception as e:
            self.logger.error(f"删除文件向量失败: {e}")
            return 0
    
    async def get_vector_count(self, collection_type: str) -> int:
        """获取集合中的向量数量"""
        try:
            if self.client is None:
                await self.initialize()
            
            collection_name = self.collection_map.get(collection_type)
            if not collection_name:
                raise ValueError(f"不支持的集合类型: {collection_type}")
            
            collection_info = self.client.get_collection(collection_name)
            return collection_info.vectors_count
            
        except Exception as e:
            self.logger.error(f"获取向量数量失败: {e}")
            return 0
    
    def _build_filter(self, filters: Dict[str, Any]) -> Optional[Filter]:
        """构建过滤条件"""
        try:
            filter_conditions = []
            
            for key, value in filters.items():
                if isinstance(value, list):
                    # 列表匹配
                    filter_conditions.append(
                        FieldCondition(
                            key=key,
                            match=MatchAny(any=value)
                        )
                    )
                else:
                    # 单值匹配
                    filter_conditions.append(
                        FieldCondition(
                            key=key,
                            match=MatchValue(value=value)
                        )
                    )
            
            if filter_conditions:
                return Filter(must=filter_conditions)
            
            return None
            
        except Exception as e:
            self.logger.error(f"构建过滤条件失败: {e}")
            return None
    
    async def batch_store_vectors(self, 
                                collection_type: str, 
                                vectors_data: List[Tuple[np.ndarray, str, Optional[str], Dict[str, Any]]],
                                batch_size: int = 100) -> List[str]:
        """
        批量存储向量
        
        Args:
            collection_type: 集合类型
            vectors_data: 向量数据列表 [(向量, 文件ID, 片段ID, 元数据), ...]
            batch_size: 批处理大小
            
        Returns:
            向量ID列表
        """
        try:
            if self.client is None:
                await self.initialize()
            
            collection_name = self.collection_map.get(collection_type)
            if not collection_name:
                raise ValueError(f"不支持的集合类型: {collection_type}")
            
            stored_ids = []
            points = []
            
            for vector_data, file_id, segment_id, metadata in vectors_data:
                vector_id = str(uuid.uuid4())
                stored_ids.append(vector_id)
                
                # 准备负载数据
                payload = {
                    'file_id': file_id,
                    'segment_id': segment_id,
                    'collection_type': collection_type,
                    'created_at': asyncio.get_event_loop().time(),
                    **(metadata or {})
                }
                
                # 创建点数据
                point = PointStruct(
                    id=vector_id,
                    vector=vector_data.tolist(),
                    payload=payload
                )
                points.append(point)
                
                # 批量插入
                if len(points) >= batch_size:
                    self.client.upsert(
                        collection_name=collection_name,
                        points=points
                    )
                    points = []
            
            # 插入剩余的点
            if points:
                self.client.upsert(
                    collection_name=collection_name,
                    points=points
                )
            
            self.logger.info(f"批量存储向量完成: {len(stored_ids)} 个向量, 集合: {collection_name}")
            return stored_ids
            
        except Exception as e:
            self.logger.error(f"批量存储向量失败: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            if self.client is None:
                await self.initialize()
            
            # 获取所有集合信息
            collections_info = {}
            for collection_type, collection_name in self.collection_map.items():
                try:
                    info = await self.get_collection_info(collection_name)
                    collections_info[collection_type] = info
                except Exception as e:
                    collections_info[collection_type] = {'error': str(e)}
            
            return {
                'status': 'healthy',
                'collections': collections_info,
                'host': self.host,
                'port': self.port
            }
            
        except Exception as e:
            self.logger.error(f"Qdrant健康检查失败: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'host': self.host,
                'port': self.port
            }