"""
向量存储核心功能模块
提供统一的向量存储接口和高级操作
"""

import asyncio
import logging
import numpy as np
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum

from src.common.storage.faiss_adapter import FaissAdapter
from src.core.config_manager import get_config_manager


class VectorType(Enum):
    """向量类型枚举"""

    VISUAL = "visual"
    AUDIO_MUSIC = "audio_music"
    AUDIO_SPEECH = "audio_speech"
    FACE = "face"
    TEXT = "text"


@dataclass
class VectorMetadata:
    """向量元数据"""

    file_id: str
    file_path: str
    file_name: str
    file_type: str
    file_size: int
    created_at: float
    segment_id: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    duration: Optional[float] = None
    confidence: Optional[float] = None
    model_name: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None


@dataclass
class SearchResult:
    """搜索结果"""

    vector_id: str
    score: float
    metadata: VectorMetadata
    distance: Optional[float] = None


class VectorStorageManager:
    """
    向量存储管理器

    负责管理向量的存储、检索和删除操作，支持多种向量类型（视觉、音频、文本等）。
    使用Qdrant作为向量数据库后端，提供统一的接口进行向量操作。

    Attributes:
        config_manager: 配置管理器实例
        logger: 日志记录器
        qdrant_adapter: Qdrant数据库适配器
        vector_dimensions: 不同向量类型的维度配置字典
        collection_mapping: 向量类型到集合名称的映射字典
        max_retries: 操作失败时的最大重试次数
        dimension_adjustment_enabled: 是否启用向量维度自动调整功能
    """

    def __init__(self, config_manager=None):
        """
        初始化向量存储管理器

        Args:
            config_manager: 可选的配置管理器实例，如果不提供将使用全局配置管理器

        Raises:
            ValueError: 当无法初始化向量存储适配器时抛出
            Exception: 当初始化过程中出现其他错误时抛出
        """
        try:
            # 初始化配置管理器
            self.config_manager = config_manager or get_config_manager()
            self.logger = logging.getLogger(__name__)

            # 初始化FAISS适配器 - 用于连接和操作向量数据库
            self.faiss_adapter = FaissAdapter(config_manager)

            # 向量维度配置 - 定义不同类型向量的维度
            self.vector_dimensions = {
                VectorType.VISUAL: 512,  # CLIP模型维度
                VectorType.AUDIO_MUSIC: 512,  # CLAP模型维度
                VectorType.AUDIO_SPEECH: 512,  # Whisper模型维度
                VectorType.FACE: 512,  # FaceNet模型维度
                VectorType.TEXT: 512,  # 文本嵌入维度
            }

            # 集合映射 - 将向量类型映射到对应的数据库集合名称
            self.collection_mapping = {
                VectorType.VISUAL: "visual_vectors",
                VectorType.AUDIO_MUSIC: "audio_music_vectors",
                VectorType.AUDIO_SPEECH: "audio_speech_vectors",
                VectorType.FACE: "face_vectors",
                VectorType.TEXT: "text_vectors",
            }

            # 错误处理配置 - 设置向量存储操作的错误处理参数
            self.max_retries = 3  # 默认重试次数
            self.dimension_adjustment_enabled = True  # 启用维度调整

            self.logger.info("向量存储管理器初始化完成")
        except Exception as adapter_error:
            self.logger.error(f"向量存储适配器初始化失败: {adapter_error}")
            raise ValueError(
                f"无法初始化向量存储适配器: {str(adapter_error)}"
            ) from adapter_error
        except Exception as e:
            self.logger.error(f"向量存储管理器初始化失败: {e}")
            raise

    async def initialize(self) -> bool:
        """初始化向量存储"""
        try:
            # 连接FAISS
            success = await self.faiss_adapter.connect()
            if not success:
                self.logger.error("FAISS连接失败")
                return False

            # 创建必要的集合
            await self._ensure_collections()

            self.logger.info("向量存储管理器初始化成功")
            return True

        except Exception as e:
            self.logger.error(f"向量存储管理器初始化失败: {e}")
            return False

    async def _ensure_collections(self):
        """确保所有必要的集合存在"""
        try:
            for vector_type, collection_name in \
                    self.collection_mapping.items():
                try:
                    # 验证维度配置
                    if vector_type not in self.vector_dimensions:
                        error_msg = f"向量类型 {vector_type} 的维度配置不存在"
                        self.logger.error(f"确保集合存在: {error_msg}")
                        raise ValueError(
                            error_msg
                        )

                    dimension = self.vector_dimensions[vector_type]

                    # 验证维度有效性
                    if dimension <= 0:
                        error_msg = f"无效的向量维度: {dimension}"
                        self.logger.error(f"确保集合存在: {error_msg}")
                        raise ValueError(error_msg)

                    success = await self.faiss_adapter.create_collection(
                        collection_name=collection_name,
                        vector_size=dimension,
                        distance_metric="cosine",
                    )

                    if success:
                        self.logger.debug(f"集合准备就绪: {collection_name}")
                    else:
                        self.logger.warning(f"集合准备失败: {collection_name}")
                        raise ValueError(f"集合创建失败: {collection_name}")

                except Exception as e:
                    self.logger.error(f"创建集合 {collection_name} 失败: {e}")
                    # 继续尝试创建其他集合，但记录错误
                    continue

        except Exception as e:
            self.logger.error(f"确保集合存在失败: {e}")
            raise

    async def store_vector(
        self,
        vector_type: VectorType,
        vector_data: Union[np.ndarray, List[float]],
        metadata: VectorMetadata,
        vector_id: Optional[str] = None,
    ) -> str:
        """
        存储向量 - 性能优化版

        功能描述:
        将向量数据及其元数据存储到向量数据库中，支持指定向量ID或自动生成

        参数:
            vector_type: 向量类型，必须是VectorType枚举值
            vector_data: 向量数据，可以是NumPy数组或浮点数列表
            metadata: 向量元数据，包含文件信息和其他属性
            vector_id: 可选的向量ID，如果不提供则自动生成

        返回:
            成功存储的向量ID

        异常:
            ValueError: 当向量维度不匹配或参数无效时
            Exception: 当存储操作失败时
        """
        try:
            # 转换向量数据
            if isinstance(vector_data, list):
                vector_data = np.array(vector_data, dtype=np.float32)

            # 验证向量维度
            expected_dim = self.vector_dimensions[vector_type]
            if vector_data.shape[-1] != expected_dim:
                raise ValueError(
                    f"向量维度不匹配: 期望{expected_dim}, 实际{vector_data.shape[-1]}"
                )

            # 准备元数据
            payload = {
                "file_id": metadata.file_id,
                "file_path": metadata.file_path,
                "file_name": metadata.file_name,
                "file_type": metadata.file_type,
                "file_size": metadata.file_size,
                "created_at": metadata.created_at,
                "segment_id": metadata.segment_id,
                "start_time": metadata.start_time,
                "end_time": metadata.end_time,
                "duration": metadata.duration,
                "confidence": metadata.confidence,
                "model_name": metadata.model_name,
            }

            # 添加额外数据
            if metadata.additional_data:
                payload.update(metadata.additional_data)

            # 存储向量
            vector_id = await self.faiss_adapter.store_vector(
                collection_type=vector_type.value,
                vector_data=vector_data,
                file_id=metadata.file_id,
                segment_id=metadata.segment_id,
                metadata=payload,
                vector_id=vector_id,
            )

            self.logger.debug(f"向量存储成功: {vector_id}, 类型: {vector_type.value}")
            return vector_id

        except Exception as e:
            self.logger.error(f"存储向量失败: {e}")
            raise

    async def search_vectors(
        self,
        vector_type: VectorType,
        query_vector: Union[np.ndarray, List[float]],
        limit: int = 10,
        score_threshold: float = 0.7,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """
        搜索向量 - 性能优化版

        功能描述:
        搜索与查询向量相似的向量，支持相似度过滤和条件过滤，包含自动重试机制

        性能优化:
        - 快速参数验证避免不必要的处理
        - 向量预处理和缓存友好的转换
        - 自动维度调整确保兼容性
        - 优化查询参数提高检索效率
        - 结果后处理优化减少内存占用
        - 网络异常自动重试提高稳定性

        参数:
            vector_type: 向量类型，必须是VectorType枚举值
            query_vector: 查询向量，可以是NumPy数组或浮点数列表
            limit: 返回结果最大数量，默认10，最大100
            score_threshold: 相似度阈值，低于此值的结果将被过滤
            filters: 可选的过滤条件字典，用于进一步过滤结果

        返回:
            SearchResult对象列表，包含向量ID、相似度分数、距离和元数据

        异常:
            ValueError: 当向量维度不匹配且无法调整时
            Exception: 当搜索操作失败时
        """
        try:
            # 性能优化1: 快速参数验证
            if vector_type not in self.collection_mapping:
                self.logger.error(f"搜索向量: 未知的向量类型 {vector_type}")
                return []

            # 性能优化2: 向量预处理和缓存友好的转换
            if isinstance(query_vector, list):
                query_vector = np.array(query_vector, dtype=np.float32)
            elif hasattr(query_vector, "numpy"):
                query_vector = query_vector.numpy().astype(np.float32)

            # 验证向量维度
            expected_dim = self.vector_dimensions[vector_type]
            if query_vector.shape[-1] != expected_dim:
                self.logger.warning(
                    f"查询向量维度不匹配: 期望{expected_dim}, 实际{query_vector.shape[-1]}"
                )
                # 尝试维度调整
                try:
                    query_vector = self._adjust_vector_dimension(
                        query_vector, expected_dim
                    )
                    self.logger.info("已自动调整查询向量维度")
                except Exception as e:
                    self.logger.error(f"向量维度调整失败: {e}")
                    raise ValueError(
                        f"查询向量维度不匹配: 期望{expected_dim}, "
                        f"实际{query_vector.shape[-1]}"
                    )

            # 性能优化3: 优化查询参数
            # 根据向量类型调整默认阈值
            if score_threshold is None:
                score_threshold = self._get_default_threshold(vector_type)

            # 限制最大结果数量
            limit = min(limit, 100)  # 防止返回过多结果

            # 性能优化4: 优化过滤条件
            if filters:
                filters = self._optimize_filter_conditions(filters)

            # 搜索向量
            raw_results = await self.faiss_adapter.search_vectors(
                collection_type=vector_type.value,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold,
                filters=filters,
            )

            # 性能优化5: 结果后处理优化
            results = []
            # 预先分配列表并使用局部变量引用append方法
            results_append = results.append

            # 提前定义必要的键列表，避免重复创建
            METADATA_KEYS = {
                "file_id",
                "file_path",
                "file_name",
                "file_type",
                "file_size",
                "created_at",
                "segment_id",
                "start_time",
                "end_time",
                "duration",
                "confidence",
                "model_name",
            }

            for result in raw_results:
                # 从payload创建元数据对象
                payload = result["payload"]
                metadata = VectorMetadata(
                    file_id=payload["file_id"],
                    file_path=payload["file_path"],
                    file_name=payload["file_name"],
                    file_type=payload["file_type"],
                    file_size=payload["file_size"],
                    created_at=payload["created_at"],
                    segment_id=payload.get("segment_id"),
                    start_time=payload.get("start_time"),
                    end_time=payload.get("end_time"),
                    duration=payload.get("duration"),
                    confidence=payload.get("confidence"),
                    model_name=payload.get("model_name"),
                    additional_data={
                            k: v
                            for k, v in payload.items()
                            if k not in METADATA_KEYS
                        },
                )

                search_result = SearchResult(
                    vector_id=result["id"],
                    score=result["score"],
                    metadata=metadata,
                    distance=1.0 - result["score"],  # 余弦距离 = 1 - 余弦相似度
                )
                results_append(search_result)

            self.logger.debug(
                f"向量搜索完成: {vector_type.value}, 返回{len(results)}个结果"
            )
            return results

        except Exception as e:
            self.logger.error(f"搜索向量失败: {e}")
            # 性能优化6: 添加重试机制
            if isinstance(e, (ConnectionError, TimeoutError)):
                for attempt in range(1, 4):  # 最多重试3次
                    self.logger.info(f"搜索失败重试 (尝试 {attempt}/3)")
                    try:
                        await asyncio.sleep(0.1 * (2 ** (attempt - 1)))  # 指数退避
                        return await self.search_vectors(
                            vector_type,
                            query_vector,
                            limit,
                            score_threshold,
                            filters
                        )
                    except Exception as retry_e:
                        self.logger.error(f"重试失败: {retry_e}")
            raise

    def _get_default_threshold(self, vector_type):
        """
        根据向量类型获取默认相似度阈值

        为不同类型的向量设置优化的默认相似度阈值，
        适应不同模态数据的特性，提高检索精度。

        Args:
            vector_type: 向量类型，VectorType枚举值

        Returns:
            float: 该向量类型对应的默认相似度阈值
        """
        # 为不同类型的向量设置不同的默认阈值
        threshold_map = {
            VectorType.VISUAL: 0.6,
            VectorType.AUDIO_MUSIC: 0.5,
            VectorType.AUDIO_SPEECH: 0.55,
            VectorType.FACE: 0.65,
            VectorType.TEXT: 0.7,
        }
        return threshold_map.get(vector_type, 0.5)

    def _optimize_filter_conditions(self, filters):
        """
        优化过滤条件以提高查询性能

        移除过滤条件中的空值，减少不必要的查询操作，
        提高向量数据库查询效率。

        Args:
            filters: 原始过滤条件字典

        Returns:
            dict: 优化后的过滤条件字典
        """
        # 移除空值条件
        optimized_filters = {}
        for key, value in filters.items():
            if value is not None:
                optimized_filters[key] = value

        return optimized_filters

    def _adjust_vector_dimension(self, vector, target_dim):
        """
        调整向量维度

        根据目标维度调整向量大小，支持截断过长向量或填充短向量。

        Args:
            vector: 原始向量，numpy数组格式
            target_dim: 目标向量维度

        Returns:
            numpy.ndarray: 调整维度后的向量
        """
        if vector.shape[-1] == target_dim:
            return vector

        # 截断或填充向量
        if vector.shape[-1] > target_dim:
            return vector[:target_dim]
        else:
            adjusted = np.zeros(target_dim, dtype=np.float32)
            adjusted[: vector.shape[-1]] = vector
            return adjusted

    async def batch_store_vectors(
        self,
        vectors_data: List[
            Tuple[VectorType, Union[np.ndarray, List[float]], VectorMetadata]
        ],
        batch_size: int = 100,
    ) -> List[str]:
        """
        批量存储向量 - 性能优化版

        功能描述:
        批量存储多个向量及其元数据到向量数据库，显著提高大量向量存储的效率

        性能优化:
        - 使用defaultdict预分配内存和减少循环内操作
        - 按向量类型分组并行处理不同类型的向量
        - 预验证向量维度提前过滤无效向量
        - 动态调整批处理大小避免内存溢出
        - 批量操作减少网络交互次数
        - 错误隔离确保部分失败不影响整体处理

        参数:
            vectors_data: 向量数据列表，每个元素为(向量类型, 向量数据, 元数据)的三元组
            batch_size: 批处理大小，默认100，会根据实际情况动态调整

        返回:
            成功存储的向量ID列表

        异常:
            Exception: 当批量存储操作失败时
        """
        try:
            if not vectors_data:
                self.logger.warning("批量存储向量: 空数据列表")
                return []

            # 性能优化1: 使用defaultdict预分配内存和减少循环内操作
            from collections import defaultdict
            import uuid

            grouped_vectors = defaultdict(list)
            for vector_type, vector_data, metadata in vectors_data:
                grouped_vectors[vector_type].append((vector_data, metadata))

            # 性能优化2: 并行处理不同类型的向量集合
            async def process_vector_type(vector_type, vectors):
                vectors_list = []
                point_ids = []
                payloads = []
                failed_count = 0

                # 获取该向量类型的预期维度
                expected_dim = self.vector_dimensions[vector_type]

                # 性能优化3: 预验证向量维度和准备数据
                for i, (vector_data, metadata) in enumerate(vectors):
                    try:
                        # 转换和验证向量
                        if isinstance(vector_data, list):
                            vector_data = np.array(
                                vector_data, dtype=np.float32
                            )

                        # 验证向量维度
                        if vector_data.shape[-1] != expected_dim:
                            self.logger.warning(
                                f"向量维度不匹配: 期望{expected_dim}, "
                                f"实际{vector_data.shape[-1]}"
                            )
                            failed_count += 1
                            continue

                        # 生成向量ID
                        vector_id = str(uuid.uuid4())

                        # 准备数据
                        point_ids.append(vector_id)
                        vectors_list.append(vector_data.tolist())

                        payload = {
                            "file_id": metadata.file_id,
                            "file_path": metadata.file_path,
                            "file_name": metadata.file_name,
                            "file_type": metadata.file_type,
                            "file_size": metadata.file_size,
                            "created_at": metadata.created_at,
                            "segment_id": metadata.segment_id,
                            "start_time": metadata.start_time,
                            "end_time": metadata.end_time,
                            "duration": metadata.duration,
                            "confidence": metadata.confidence,
                            "model_name": metadata.model_name,
                            "vector_type": vector_type.value,  # 添加类型信息便于检索
                        }

                        if metadata.additional_data:
                            payload.update(metadata.additional_data)

                        payloads.append(payload)

                    except Exception as e:
                        self.logger.error(f"准备向量数据时出错: {e}")
                        failed_count += 1

                # 性能优化4: 动态调整批处理大小
                optimal_batch_size = min(batch_size, 500)  # 设置上限防止内存溢出
                stored_ids = []

                # 按批次处理有效向量
                for i in range(0, len(vectors_list), optimal_batch_size):
                    batch_vectors = vectors_list[i:i + optimal_batch_size]
                    batch_ids = point_ids[i:i + optimal_batch_size]
                    batch_payloads = payloads[i:i + optimal_batch_size]

                    collection_name = self.collection_mapping[vector_type]

                    try:
                        # 执行批量存储
                        store_params = {
                            'collection_name': collection_name,
                            'vectors': batch_vectors,
                            'point_ids': batch_ids,
                            'payloads': batch_payloads
                        }
                        # 执行向量存储
                        store_method = self.faiss_adapter.store_vectors
                        batch_stored_ids = await store_method(**store_params)
                        stored_ids.extend(batch_stored_ids)
                    except Exception as e:
                        self.logger.error(f"批量存储过程出错: {e}")

                return stored_ids

            # 创建并行任务
            tasks = []
            for vector_type, vectors in grouped_vectors.items():
                tasks.append(process_vector_type(vector_type, vectors))

            # 等待所有任务完成
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 汇总结果
            all_vector_ids = []
            for result in results:
                if isinstance(result, Exception):
                    self.logger.error(f"批量存储向量任务失败: {result}")
                else:
                    all_vector_ids.extend(result)

            self.logger.info(f"批量存储向量完成: {len(all_vector_ids)}个向量")
            return all_vector_ids

        except Exception as e:
            self.logger.error(f"批量存储向量失败: {e}")
            raise

    async def delete_vectors_by_file(self, file_id: str) -> Dict[str, int]:
        """
        根据文件ID删除所有相关向量

        Args:
            file_id: 文件ID

        Returns:
            Dict[str, int]: 各类型删除的向量数量

        Raises:
            ValueError: 当file_id为空时
            Exception: 当删除过程中出现错误时
        """
        try:
            # 参数验证
            if not file_id:
                error_msg = "文件ID不能为空"
                self.logger.error(f"删除文件向量: {error_msg}")
                raise ValueError(error_msg)

            deleted_counts = {}
            failed_types = []

            for vector_type in VectorType:
                try:
                    count = await self.faiss_adapter.delete_vectors_by_file(
                        collection_type=vector_type.value, file_id=file_id
                    )
                    deleted_counts[vector_type.value] = count

                    if count > 0:
                        self.logger.debug(
                            f"删除文件向量: {file_id}, 类型: {vector_type.value}, "
                            f"数量: {count}"
                        )
                except Exception as e:
                    failed_types.append((vector_type.value, str(e)))
                    deleted_counts[vector_type.value] = 0
                    self.logger.error(
                        f"删除文件向量失败: {file_id}, 类型: {vector_type.value}, "
                        f"错误: {e}"
                    )
                    # 继续尝试删除其他类型的向量
                    continue

            total_deleted = sum(deleted_counts.values())

            if total_deleted > 0:
                self.logger.info(
                    f"文件向量删除完成: {file_id}, 总计: {total_deleted}个"
                )
            else:
                self.logger.warning(f"未找到与文件ID关联的向量: {file_id}")

            # 如果有失败的类型，记录警告
            if failed_types:
                self.logger.warning(
                    f"部分类型的向量删除失败: {file_id}, 失败类型: {failed_types}"
                )

            return deleted_counts

        except ValueError:
            # 已格式化的错误，直接抛出
            raise
        except Exception as e:
            self.logger.error(f"删除文件向量失败: {file_id}, 错误: {e}")
            raise

    async def get_vector_count(
        self, vector_type: Optional[VectorType] = None
    ) -> Union[int, Dict[str, int]]:
        """
        获取向量数量

        Args:
            vector_type: 向量类型（可选）

        Returns:
            向量数量或各类型的向量数量
        """
        try:
            if vector_type:
                count = await self.faiss_adapter.get_vector_count(
                    vector_type.value
                )
                return count
            else:
                counts = {}
                for vt in VectorType:
                    try:
                        count = await self.faiss_adapter.get_vector_count(
                            vt.value
                        )
                        counts[vt.value] = count
                    except Exception as e:
                        self.logger.warning(
                            f"获取向量数量失败: {vt.value}, 错误: {e}"
                        )
                        counts[vt.value] = 0
                return counts

        except Exception as e:
            self.logger.error(f"获取向量数量失败: {e}")
            raise

    async def hybrid_search(
        self,
        query_vectors: Dict[VectorType, Union[np.ndarray, List[float]]],
        weights: Optional[Dict[VectorType, float]] = None,
        limit: int = 10,
        score_threshold: float = 0.5,
    ) -> List[SearchResult]:
        """
        混合搜索（多向量类型融合搜索）

        Args:
            query_vectors: 查询向量字典 {类型: 向量}
            weights: 权重字典 {类型: 权重}
            limit: 返回结果数量
            score_threshold: 相似度阈值

        Returns:
            融合后的搜索结果
        """
        try:
            # 默认权重
            if weights is None:
                weights = {
                    VectorType.VISUAL: 0.4,
                    VectorType.AUDIO_MUSIC: 0.3,
                    VectorType.AUDIO_SPEECH: 0.3,
                }

            # 搜索各类型的向量
            all_results = {}
            for vector_type, query_vector in query_vectors.items():
                if vector_type not in weights:
                    continue

                try:
                    results = await self.search_vectors(
                        vector_type=vector_type,
                        query_vector=query_vector,
                        limit=limit * 2,  # 获取更多结果用于融合
                        score_threshold=score_threshold,
                    )

                    # 应用权重
                    weight = weights[vector_type]
                    for result in results:
                        result.score *= weight

                    all_results[vector_type] = results

                except Exception as e:
                    self.logger.warning(
                        f"搜索向量类型失败: {vector_type.value}, 错误: {e}"
                    )

            # 融合结果
            fused_results = self._fuse_search_results(all_results, limit)

            self.logger.info(
                f"混合搜索完成: 输入{len(query_vectors)}种向量类型, "
                f"返回{len(fused_results)}个结果"
            )
            return fused_results

        except Exception as e:
            self.logger.error(f"混合搜索失败: {e}")
            raise

    def _fuse_search_results(
        self, all_results: Dict[VectorType, List[SearchResult]], limit: int
    ) -> List[SearchResult]:
        """融合搜索结果"""
        try:
            # 收集所有结果
            combined_results = []

            for vector_type, results in all_results.items():
                for result in results:
                    # 添加向量类型信息
                    if not result.metadata.additional_data:
                        result.metadata.additional_data = {}
                    # 添加向量类型
                    k = "vector_type"
                    result.metadata.additional_data[k] = vector_type.value
                    combined_results.append(result)

            # 定义排序键
            def k(x):
                return x.score
            # 排序
            combined_results.sort(key=k, reverse=True)

            # 去重（基于文件ID和片段ID）
            seen = set()
            unique_results = []

            for result in combined_results:
                key = (result.metadata.file_id, result.metadata.segment_id)
                if key not in seen:
                    seen.add(key)
                    unique_results.append(result)

                    if len(unique_results) >= limit:
                        break

            return unique_results

        except Exception as e:
            self.logger.error(f"融合搜索结果失败: {e}")
            return []

    async def get_collection_stats(self) -> Dict[str, Any]:
        """获取集合统计信息"""
        try:
            stats = {}

            # 遍历所有集合类型
            for vt, cn in self.collection_mapping.items():
                try:
                    info = await self.faiss_adapter.get_collection_info(cn)
                    # 统计
                    s = stats[vt.value] = {}
                    s["col"] = cn
                    s["cnt"] = info.get("vectors_count", 0)
                    s["sts"] = info.get("status", "unknown")
                    s["dim"] = self.vector_dimensions[vt]
                except Exception as e:
                    self.logger.warning(
                        f"获取集合统计失败: {vt.value}, 错误: {e}"
                    )
                    stats[vt.value] = {"error": str(e)}

            return stats

        except Exception as e:
            self.logger.error(f"获取集合统计失败: {e}")
            return {}

    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            # FAISS健康检查
            faiss_health = await self.faiss_adapter.health_check()

            # 获取统计信息
            stats = await self.get_collection_stats()

            # 计算总向量数
            total_vectors = sum(
                stat.get("vectors_count", 0)
                for stat in stats.values()
                if "vectors_count" in stat
            )

            return {
                "status": (
                    "healthy"
                    if faiss_health.get("status") == "healthy"
                    else "unhealthy"
                ),
                "faiss": faiss_health,
                "collections": stats,
                "total_vectors": total_vectors,
                "supported_types": [vt.value for vt in VectorType],
            }

        except Exception as e:
            self.logger.error(f"健康检查失败: {e}")
            return {"status": "unhealthy", "error": str(e)}

    async def cleanup(self) -> bool:
        """清理资源"""
        try:
            await self.faiss_adapter.disconnect()
            self.logger.info("向量存储管理器清理完成")
            return True
        except Exception as e:
            self.logger.error(f"清理资源失败: {e}")
            return False


# 向量存储管理器单例
_vector_storage_manager: Optional[VectorStorageManager] = None


def get_vector_storage_manager() -> VectorStorageManager:
    """获取向量存储管理器单例"""
    global _vector_storage_manager
    if _vector_storage_manager is None:
        _vector_storage_manager = VectorStorageManager()
    return _vector_storage_manager
