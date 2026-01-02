"""
向量存储适配器
为多模态检索系统提供统一的向量存储访问接口（当前实现基于 Milvus Lite 向量数据库）
"""

import asyncio
import logging
import uuid
import os
from typing import Dict, Any, Optional, List, Tuple

import numpy as np
from pymilvus import (  # type: ignore
    connections,
    FieldSchema,
    CollectionSchema,
    DataType,
    Collection,
    utility,
    MilvusClient
)

from src.core.config_manager import get_config_manager


class VectorStorageAdapter:
    """向量存储适配器（基于 Milvus Lite 实现）"""

    def __init__(self, config_manager=None):
        self.config_manager = config_manager or get_config_manager()
        self.logger = logging.getLogger(__name__)

        # 获取向量数据库类型
        self.vector_db_type = self.config_manager.get("vector_db.type", "milvus")
        self.logger.info(f"使用向量数据库类型: {self.vector_db_type}")
        
        # 如果是 milvus_lite 类型，使用正确的文件路径格式
        if self.vector_db_type == "milvus_lite":
            self.data_dir = self.config_manager.get("vector_db.data_dir", "./data/milvus")
            # 对于Milvus Lite，URI应该直接是文件路径，而不是file://格式
            self.uri = os.path.abspath(os.path.join(self.data_dir, "milvus.db"))
            self.host = None
            self.port = None
        else:
            # 传统 Milvus 服务器配置
            self.uri = self.config_manager.get(
                "database.milvus.uri", "http://127.0.0.1:19530")
            self.data_dir = self.config_manager.get(
                "database.milvus.data_dir", "./data/milvus")
            self.host = self.config_manager.get(
                "database.milvus.host", "127.0.0.1")
            self.port = self.config_manager.get("database.milvus.port", 19530)
        
        os.makedirs(self.data_dir, exist_ok=True)

        # 集合配置
        self.collections_config = self.config_manager.get(
            "vector_db.collections", {})

        # 客户端
        self.client: Optional[MilvusClient] = None
        self.collections: Dict[str, Collection] = {}

        # 集合映射
        self.collection_map = {
            'visual': 'visual_vectors',
            'audio_music': 'audio_music_vectors',
            'audio_speech': 'audio_speech_vectors',
            'face': 'face_vectors',
            'text': 'text_vectors'
        }

        self.logger.info(f"向量存储适配器初始化完成（基于 {self.vector_db_type}）")

    async def connect(self) -> bool:
        """连接到向量数据库"""
        try:
            if self.vector_db_type == "milvus_lite":
                # 对于Milvus Lite，使用正确的连接方式
                # 注意：pymilvus 2.3.0可能不支持MilvusClient直接连接本地文件
                # 我们将尝试使用传统的连接方式
                from pymilvus import connections
                
                # 对于Milvus Lite，我们需要先检查milvus_lite模块是否可用
                try:
                    import milvus_lite
                    # 使用文件路径作为连接参数
                    self.client = MilvusClient(
                        self.uri,  # 直接使用文件路径作为构造参数
                        db_name="default"
                    )
                except ImportError:
                    # 如果milvus_lite模块不可用，尝试使用传统连接方式
                    connections.connect(
                        alias="default",
                        host="localhost",
                        port="19530"
                    )
                    # 创建一个伪客户端，只用于初始化
                    self.client = None
            else:
                # 传统 Milvus 服务器
                self.client = MilvusClient(
                    uri=self.uri,
                    db_name="default"
                )

            await self.initialize()
            return True
        except Exception as e:
            self.logger.error(f"向量数据库连接失败: {e}")
            return False

    async def disconnect(self):
        """断开Milvus连接"""
        try:
            if self.client:
                # Milvus Lite不需要显式断开连接
                self.client = None
            self.logger.info("Milvus连接已断开")
        except Exception as e:
            self.logger.error(f"断开Milvus连接失败: {e}")

    async def initialize(self):
        """初始化Milvus集合"""
        try:
            # 初始化所有集合
            await self._initialize_collections()
            self.logger.info("Milvus集合初始化完成")
        except Exception as e:
            self.logger.error(f"Milvus初始化失败: {e}")
            raise

    async def _initialize_collections(self):
        """初始化所有向量集合"""
        try:
            from pymilvus import utility, FieldSchema, CollectionSchema, DataType, Collection
            
            # 检查并创建所有集合
            for collection_type, collection_name in self.collection_map.items():
                if not utility.has_collection(collection_name):
                    # 定义字段
                    fields = [
                        FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=64, is_primary=True, auto_id=False),
                        FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=512),
                        FieldSchema(name="file_id", dtype=DataType.VARCHAR, max_length=256),
                        FieldSchema(name="segment_id", dtype=DataType.VARCHAR, max_length=64, nullable=True),
                        FieldSchema(name="collection_type", dtype=DataType.VARCHAR, max_length=32),
                        FieldSchema(name="created_at", dtype=DataType.DOUBLE),
                        FieldSchema(name="test_key", dtype=DataType.VARCHAR, max_length=64, nullable=True)  # 示例元数据字段
                    ]
                    
                    # 创建模式
                    schema = CollectionSchema(
                        fields=fields,
                        description=f"{collection_type}向量集合"
                    )
                    
                    # 创建集合
                    collection = Collection(name=collection_name, schema=schema)
                    
                    # 创建索引
                    index_params = {
                        "index_type": "IVF_FLAT",
                        "params": {"nlist": 128},
                        "metric_type": "COSINE"
                    }
                    collection.create_index(
                        field_name="vector",
                        index_params=index_params
                    )
                    
                    self.logger.info(f"创建集合成功: {collection_name}")
                else:
                    self.logger.debug(f"集合已存在: {collection_name}")

            self.logger.info("Milvus集合初始化完成")

        except Exception as e:
            self.logger.error(f"集合初始化失败: {e}")
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
            if not self.client:
                raise ValueError("Milvus客户端未连接")

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

            # 确保集合存在
            await self._create_collection_if_not_exists(collection_name, vector_data.shape[-1], "")

            # 插入向量
            result = self.client.insert(
                collection_name=collection_name,
                data=[{
                    "id": vector_id,
                    "vector": vector_data.tolist(),
                    **payload
                }]
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
                             score_threshold: float = None,
                             filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        搜索向量

        Args:
            collection_type: 集合类型
            query_vector: 查询向量
            limit: 返回结果数量限制
            score_threshold: 相似度阈值，从配置读取默认
            filters: 过滤条件

        Returns:
            搜索结果列表
        """
        try:
            if not self.client:
                raise ValueError("Milvus客户端未连接")

            # 从配置获取默认阈值
            if score_threshold is None:
                score_threshold = self.config_manager.get(
                    'vector_db.default_score_threshold', 0.7
                )

            collection_name = self.collection_map.get(collection_type)
            if not collection_name:
                raise ValueError(f"不支持的集合类型: {collection_type}")

            # 确保集合存在
            await self._create_collection_if_not_exists(collection_name, query_vector.shape[-1], "")

            # 获取该集合的配置
            collection_config = self.collections_config.get(collection_name, {})
            
            # 获取搜索参数
            metric_type = collection_config.get("metric_type", "COSINE")
            search_params = collection_config.get("search_params", {"nprobe": 10})
            
            # 构建搜索参数
            search_params = {
                "metric_type": metric_type,
                "params": search_params
            }

            # 搜索向量
            results = self.client.search(
                collection_name=collection_name,
                data=[query_vector.tolist()],
                limit=limit,
                search_params=search_params,
                output_fields=["file_id", "segment_id",
                               "collection_type", "created_at"]
            )

            # 格式化结果
            formatted_results = []
            for result in results[0]:  # 只处理第一个查询结果
                score = result["distance"]
                if score < score_threshold:
                    continue

                formatted_results.append({
                    'id': result["id"],
                    'score': score,
                    'payload': {
                        'file_id': result.get("file_id"),
                        'segment_id': result.get("segment_id"),
                        'collection_type': result.get("collection_type"),
                        'created_at': result.get("created_at")
                    }
                })

            return formatted_results

        except Exception as e:
            self.logger.error(f"搜索向量失败: {e}")
            raise

    async def create_collection(self,
                                collection_name: str,
                                vector_size: int = 512,
                                distance_metric: str = "cosine") -> bool:
        """创建集合"""
        try:
            await self._create_collection_if_not_exists(collection_name, vector_size, "")
            return True

        except Exception as e:
            self.logger.error(f"创建集合失败: {collection_name}, 错误: {e}")
            return False

    async def store_vectors(self,
                            collection_name: str,
                            vectors: List[List[float]],
                            point_ids: Optional[List[str]] = None,
                            payloads: Optional[List[Dict[str, Any]]] = None) -> List[str]:
        """存储向量"""
        try:
            if not self.client:
                raise ValueError("Milvus客户端未连接")

            # 生成ID列表
            if point_ids is None:
                point_ids = [str(uuid.uuid4()) for _ in vectors]

            if payloads is None:
                payloads = [{} for _ in vectors]

            # 确保集合存在
            if vectors:
                await self._create_collection_if_not_exists(collection_name, len(vectors[0]), "")

            # 准备插入数据
            insert_data = []
            for vector, point_id, payload in zip(vectors, point_ids, payloads):
                insert_data.append({
                    "id": point_id,
                    "vector": vector,
                    **payload
                })

            # 插入向量
            result = self.client.insert(
                collection_name=collection_name,
                data=insert_data
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
            if not self.client:
                raise ValueError("Milvus客户端未连接")

            # 删除向量
            result = self.client.delete(
                collection_name=collection_name,
                ids=point_ids
            )

            return True

        except Exception as e:
            self.logger.error(f"删除向量失败: {e}")
            return False

    async def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """获取集合信息"""
        try:
            if not self.client:
                raise ValueError("Milvus客户端未连接")

            # 获取集合统计信息
            stats = self.client.get_collection_stats(
                collection_name=collection_name)

            return {
                'name': collection_name,
                'vectors_count': stats["row_count"],
                'status': 'healthy',
                'dimension': stats.get("dimension", 512)
            }

        except Exception as e:
            self.logger.error(f"获取集合信息失败: {collection_name}, 错误: {e}")
            return {}

    async def delete_vector(self, collection_type: str, vector_id: str) -> bool:
        """删除单个向量"""
        try:
            collection_name = self.collection_map.get(collection_type)
            if not collection_name:
                raise ValueError(f"不支持的集合类型: {collection_type}")

            return await self.delete_vectors(collection_name, [vector_id])

        except Exception as e:
            self.logger.error(f"删除向量失败: {e}")
            return False

    async def delete_vectors_by_file(self, collection_type: str, file_id: str) -> int:
        """根据文件ID删除向量"""
        try:
            if not self.client:
                raise ValueError("Milvus客户端未连接")

            collection_name = self.collection_map.get(collection_type)
            if not collection_name:
                raise ValueError(f"不支持的集合类型: {collection_type}")

            # 查找该文件的所有向量ID
            search_results = self.client.query(
                collection_name=collection_name,
                filter=f"file_id == '{file_id}'",
                output_fields=["id"]
            )

            file_vector_ids = [result["id"] for result in search_results]
            if not file_vector_ids:
                return 0

            # 删除向量
            await self.delete_vectors(collection_name, file_vector_ids)

            self.logger.info(f"文件向量删除完成: {file_id}, 集合: {collection_name}")
            return len(file_vector_ids)

        except Exception as e:
            self.logger.error(f"删除文件向量失败: {e}")
            return 0

    async def get_vector_count(self, collection_type: str) -> int:
        """获取集合中的向量数量"""
        try:
            if not self.client:
                raise ValueError("Milvus客户端未连接")

            collection_name = self.collection_map.get(collection_type)
            if not collection_name:
                raise ValueError(f"不支持的集合类型: {collection_type}")

            # 获取集合统计信息
            stats = self.client.get_collection_stats(
                collection_name=collection_name)
            return stats["row_count"]

        except Exception as e:
            self.logger.error(f"获取向量数量失败: {e}")
            return 0

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
            from pymilvus import Collection
            
            collection_name = self.collection_map.get(collection_type)
            if not collection_name:
                raise ValueError(f"不支持的集合类型: {collection_type}")

            # 获取集合
            collection = Collection(collection_name)
            
            stored_ids = []
            batch_data = []
            
            for vector_data, file_id, segment_id, metadata in vectors_data:
                vector_id = str(uuid.uuid4())
                stored_ids.append(vector_id)

                # 准备插入数据
                insert_data = {
                    "id": vector_id,
                    "vector": vector_data.tolist(),
                    "file_id": file_id,
                    "segment_id": segment_id,
                    "collection_type": collection_type,
                    "created_at": asyncio.get_event_loop().time(),
                    "test_key": metadata.get("test_key", "") if metadata else ""
                }
                
                batch_data.append(insert_data)

                # 批量插入
                if len(batch_data) >= batch_size:
                    # 转换为插入格式
                    insert_list = {
                        "id": [item["id"] for item in batch_data],
                        "vector": [item["vector"] for item in batch_data],
                        "file_id": [item["file_id"] for item in batch_data],
                        "segment_id": [item["segment_id"] for item in batch_data],
                        "collection_type": [item["collection_type"] for item in batch_data],
                        "created_at": [item["created_at"] for item in batch_data],
                        "test_key": [item["test_key"] for item in batch_data]
                    }
                    
                    # 插入数据
                    collection.insert(insert_list)
                    collection.flush()
                    
                    # 清空批次
                    batch_data = []

            # 插入剩余的向量
            if batch_data:
                insert_list = {
                    "id": [item["id"] for item in batch_data],
                    "vector": [item["vector"] for item in batch_data],
                    "file_id": [item["file_id"] for item in batch_data],
                    "segment_id": [item["segment_id"] for item in batch_data],
                    "collection_type": [item["collection_type"] for item in batch_data],
                    "created_at": [item["created_at"] for item in batch_data],
                    "test_key": [item["test_key"] for item in batch_data]
                }
                
                collection.insert(insert_list)
                collection.flush()

            self.logger.info(
                f"批量存储向量完成: {len(stored_ids)} 个向量, 集合: {collection_name}")
            return stored_ids

        except Exception as e:
            self.logger.error(f"批量存储向量失败: {e}")
            raise

    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            if not self.client:
                return {
                    'status': 'unhealthy',
                    'error': 'Milvus客户端未连接'
                }

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
                'milvus': {
                    'data_dir': self.data_dir,
                    'collections': collections_info
                },
                'collections': collections_info,
                'total_vectors': sum(info.get('vectors_count', 0) for info in collections_info.values() if isinstance(info, dict))
            }

        except Exception as e:
            self.logger.error(f"Milvus健康检查失败: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }


# 别名兼容
MilvusAdapter = VectorStorageAdapter
