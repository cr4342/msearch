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

        # Milvus配置
        self.uri = self.config_manager.get(
            "database.milvus.uri", "./data/milvus/milvus.db")
        self.data_dir = self.config_manager.get(
            "database.milvus.data_dir", "./data/milvus")
        os.makedirs(self.data_dir, exist_ok=True)

        self.host = self.config_manager.get(
            "database.milvus.host", "127.0.0.1")
        self.port = self.config_manager.get("database.milvus.port", 19530)

        # 集合配置
        self.collections_config = self.config_manager.get(
            "database.milvus.collections", {})

        # 客户端
        self.client: Optional[MilvusClient] = None
        self.collections: Dict[str, Collection] = {}

        # 集合映射
        self.collection_map = {
            'visual': 'image_vectors',
            'audio_music': 'audio_vectors',
            'audio_speech': 'audio_vectors',
            'face': 'face_vectors',
            'text': 'text_vectors'
        }

        self.logger.info("向量存储适配器初始化完成（基于 Milvus Lite）")

    async def connect(self) -> bool:
        """连接到Milvus Lite"""
        try:
            # 使用MilvusClient连接到Milvus Lite
            self.client = MilvusClient(
                uri=self.uri,  # 直接使用配置的URI
                db_name="default"
            )

            await self.initialize()
            return True
        except Exception as e:
            self.logger.error(f"Milvus连接失败: {e}")
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

            # 检查并创建人脸向量集合
            await self._create_collection_if_not_exists(
                self.collection_map['face'],
                512,  # FaceNet模型向量维度
                "人脸向量集合，用于人脸检索"
            )

            # 检查并创建文本向量集合
            await self._create_collection_if_not_exists(
                self.collection_map['text'],
                512,  # 文本模型向量维度
                "文本向量集合，用于文本检索"
            )

            self.logger.info("Milvus集合初始化完成")

        except Exception as e:
            self.logger.error(f"集合初始化失败: {e}")
            raise

    async def _create_collection_if_not_exists(self, collection_name: str, vector_size: int, description: str):
        """创建集合（如果不存在）"""
        try:
            if not self.client:
                raise ValueError("Milvus客户端未连接")

            # 检查集合是否存在
            if not self.client.has_collection(collection_name=collection_name):
                # 获取该集合的配置
                collection_config = self.collections_config.get(collection_name, {})
                
                # 获取索引参数
                metric_type = collection_config.get("metric_type", "COSINE")
                index_type = collection_config.get("index_type", "IVF_FLAT")
                index_params = collection_config.get("index_params", {"nlist": 1024})
                
                # 创建集合
                self.client.create_collection(
                    collection_name=collection_name,
                    dimension=vector_size,
                    metric_type=metric_type,
                    description=description
                )

                # 创建索引
                self.client.create_index(
                    collection_name=collection_name,
                    index_name="vector_index",
                    index_params={
                        "index_type": index_type,
                        "params": index_params
                    }
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
            if not self.client:
                raise ValueError("Milvus客户端未连接")

            collection_name = self.collection_map.get(collection_type)
            if not collection_name:
                raise ValueError(f"不支持的集合类型: {collection_type}")

            stored_ids = []
            batch_data = []

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

                batch_data.append({
                    "id": vector_id,
                    "vector": vector_data.tolist(),
                    **payload
                })

                # 批量插入
                if len(batch_data) >= batch_size:
                    # 确保集合存在
                    if vectors_data:
                        await self._create_collection_if_not_exists(collection_name, vector_data.shape[-1], "")

                    # 插入向量
                    self.client.insert(
                        collection_name=collection_name,
                        data=batch_data
                    )

                    # 清空批次
                    batch_data = []

            # 插入剩余的向量
            if batch_data:
                if vectors_data:
                    await self._create_collection_if_not_exists(collection_name, vectors_data[0][0].shape[-1], "")

                self.client.insert(
                    collection_name=collection_name,
                    data=batch_data
                )

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
