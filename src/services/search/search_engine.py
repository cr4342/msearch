"""
搜索引擎 - 使用依赖注入
负责处理多模态向量检索
"""

import os
import sys
import logging
import time
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from abc import ABC, abstractmethod
from pathlib import Path

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmbeddingEngine(ABC):
    """向量化引擎接口"""

    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        pass

    @abstractmethod
    def embed_image(self, image_path: str) -> List[float]:
        pass

    @abstractmethod
    def embed_audio(self, audio_path: str) -> List[float]:
        pass

    @abstractmethod
    def embed_video_segment(
        self,
        video_path: str,
        start_time: float = 0.0,
        end_time: Optional[float] = None,
        aggregation: str = "mean",
    ) -> List[float]:
        pass


class VectorStore(ABC):
    """向量存储接口"""

    @abstractmethod
    def search_vectors(
        self,
        query_vector: List[float],
        k: int = 10,
        modalities: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_collection_stats(self) -> Dict[str, Any]:
        pass


class SearchEngine:
    """
    搜索引擎 - 使用依赖注入

    负责处理多模态向量检索
    """

    def __init__(
        self,
        embedding_engine: EmbeddingEngine,
        vector_store: VectorStore,
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化搜索引擎（使用依赖注入）

        Args:
            embedding_engine: 向量化引擎
            vector_store: 向量存储
            config: 搜索配置
        """
        self.embedding_engine = embedding_engine
        self.vector_store = vector_store
        self.config = config or {}

        self.default_modality_weights = self.config.get(
            "default_modality_weights",
            {"text": 1.0, "image": 1.0, "video": 1.0, "audio": 1.0},
        )
        self.audio_keywords = [
            keyword.lower()
            for keyword in self.config.get(
                "audio_keywords",
                [
                    "音乐",
                    "歌曲",
                    "BGM",
                    "背景音乐",
                    "讲话",
                    "会议",
                    "语音",
                    "对话",
                    "演讲",
                ],
            )
        ]
        self.audio_weight_multiplier = self.config.get("audio_weight_multiplier", 1.5)
        self.visual_weight_multiplier = self.config.get("visual_weight_multiplier", 0.7)

        logger.info("SearchEngine initialized (with dependency injection)")

    def initialize(self) -> bool:
        """
        初始化搜索引擎

        Returns:
            是否初始化成功
        """
        try:
            logger.info("SearchEngine initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize SearchEngine: {e}")
            return False

    async def search(
        self,
        query: str,
        k: int = 10,
        modalities: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        执行文本搜索

        支持跨模态检索：文本查询可以检索图像、视频和音频内容。
        音频检索使用专门的CLAP模型进行跨模态匹配。

        Args:
            query: 查询文本
            k: 返回结果数量
            modalities: 模态类型列表
            filters: 过滤条件

        Returns:
            搜索结果
        """
        try:
            start_time = time.time()
            logger.info(
                f"Searching with query: {query}, k: {k}, modalities: {modalities}"
            )

            all_results = []
            modalities = modalities or ["image", "video", "audio"]

            if "audio" in modalities:
                audio_results = await self._search_audio_with_text(query, k, filters)
                all_results.extend(audio_results)
                logger.debug(f"Audio search returned {len(audio_results)} results")

            image_video_modalities = [m for m in modalities if m in ["image", "video"]]
            if image_video_modalities:
                query_vector = await self.embedding_engine.embed_text(query)

                search_filters = {"modality": image_video_modalities}
                if filters:
                    search_filters.update(filters)

                image_video_results = self.vector_store.search(
                    query_vector,
                    limit=k,
                    filter=search_filters if search_filters else None
                )
                all_results.extend(image_video_results)
                logger.debug(f"Image/Video search returned {len(image_video_results)} results")

            modality_weights = self._get_modality_weights(query)
            weighted_results = self._apply_modality_weights(
                all_results, modality_weights
            )

            ranked_results = self._rank_results(weighted_results)

            aggregated_results = self._aggregate_results(ranked_results)

            formatted_results = self._format_results(aggregated_results)

            return {
                "status": "success",
                "query": query,
                "results": formatted_results,
                "total": len(formatted_results),
                "search_time": time.time() - start_time,
                "modalities": modalities,
                "k": k,
            }
        except Exception as e:
            logger.error(f"Failed to search: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "error": str(e),
                "query": query,
                "results": [],
                "total": 0,
            }

    async def _search_audio_with_text(
        self,
        query: str,
        k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        使用文本查询检索音频（跨模态检索）

        使用CLAP模型的文本-音频检索能力，将文本查询转换为音频向量空间进行匹配。

        Args:
            query: 查询文本
            k: 返回结果数量
            filters: 过滤条件

        Returns:
            音频搜索结果列表
        """
        try:
            audio_vector = await self.embedding_engine.embed_audio(
                query, model_type="audio_model", is_text_query=True
            )

            search_filters = {"modality": "audio"}
            if filters:
                search_filters.update(filters)

            audio_results = self.vector_store.search(
                audio_vector,
                limit=k,
                filter=search_filters if search_filters else None
            )

            logger.debug(f"Audio search completed: {len(audio_results)} results for query '{query}'")
            return audio_results

        except Exception as e:
            logger.warning(f"Audio search failed, skipping audio results: {e}")
            return []

    async def image_search(
        self,
        image_path: str,
        k: int = 10,
        modalities: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        执行图像搜索

        Args:
            image_path: 图像文件路径
            k: 返回结果数量
            modalities: 模态类型列表
            filters: 过滤条件

        Returns:
            搜索结果
        """
        try:
            start_time = time.time()
            logger.info(
                f"Searching with image: {image_path}, k: {k}, modalities: {modalities}"
            )

            # 1. 图像向量化
            query_vector = await self.embedding_engine.embed_image(image_path)

            # 2. 向量搜索
            search_results = self.vector_store.search(query_vector, limit=k)

            # 3. 结果排序和过滤
            ranked_results = self._rank_results(search_results)

            # 4. 结果聚合
            aggregated_results = self._aggregate_results(ranked_results)

            # 5. 结果格式化
            formatted_results = self._format_results(aggregated_results)

            return {
                "status": "success",
                "image_path": image_path,
                "results": formatted_results,
                "total": len(formatted_results),
                "search_time": time.time() - start_time,
                "modalities": modalities,
                "k": k,
            }
        except Exception as e:
            logger.error(f"Failed to search image: {e}")
            return {
                "status": "error",
                "error": str(e),
                "image_path": image_path,
                "results": [],
                "total": 0,
            }

    async def audio_search(
        self,
        audio_path: str,
        k: int = 10,
        modalities: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        执行音频搜索

        Args:
            audio_path: 音频文件路径
            k: 返回结果数量
            modalities: 模态类型列表
            filters: 过滤条件

        Returns:
            搜索结果
        """
        try:
            start_time = time.time()
            logger.info(
                f"Searching with audio: {audio_path}, k: {k}, modalities: {modalities}"
            )

            # 1. 音频向量化
            query_vector = await self.embedding_engine.embed_audio(audio_path)

            # 2. 向量搜索
            search_results = self.vector_store.search(query_vector, limit=k)

            # 3. 结果排序和过滤
            ranked_results = self._rank_results(search_results)

            # 4. 结果聚合
            aggregated_results = self._aggregate_results(ranked_results)

            # 5. 结果格式化
            formatted_results = self._format_results(aggregated_results)

            return {
                "status": "success",
                "audio_path": audio_path,
                "results": formatted_results,
                "total": len(formatted_results),
                "search_time": time.time() - start_time,
                "modalities": modalities,
                "k": k,
            }
        except Exception as e:
            logger.error(f"Failed to search audio: {e}")
            return {
                "status": "error",
                "error": str(e),
                "audio_path": audio_path,
                "results": [],
                "total": 0,
            }

    def _contains_audio_keywords(self, query: str) -> bool:
        """
        检测查询是否包含音频关键词

        Args:
            query: 查询文本

        Returns:
            是否包含音频关键词
        """
        if not query:
            return False
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in self.audio_keywords)

    def _get_modality_weights(self, query: str) -> Dict[str, float]:
        """
        根据查询文本获取模态权重

        Args:
            query: 查询文本

        Returns:
            模态权重字典
        """
        weights = dict(self.default_modality_weights)
        if self._contains_audio_keywords(query):
            weights["audio"] = weights.get("audio", 1.0) * self.audio_weight_multiplier
            if "image" in weights:
                weights["image"] *= self.visual_weight_multiplier
            if "video" in weights:
                weights["video"] *= self.visual_weight_multiplier
        return weights

    def _apply_modality_weights(
        self,
        results: List[Dict[str, Any]],
        weights: Dict[str, float],
    ) -> List[Dict[str, Any]]:
        """
        按模态权重调整结果相似度

        Args:
            results: 原始结果
            weights: 模态权重

        Returns:
            权重调整后的结果
        """
        if not results or not weights:
            return results

        for result in results:
            modality = result.get("modality")
            base_score = result.get("similarity", result.get("score", 0.0))
            weight = weights.get(modality, 1.0)
            adjusted_score = base_score * weight
            result["similarity"] = adjusted_score
            result["score"] = adjusted_score

        return results

    def _rank_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        结果排序

        Args:
            results: 原始结果

        Returns:
            排序后的结果
        """
        # 按相似度分数排序
        return sorted(
            results, key=lambda x: x.get("similarity", x.get("score", 0)), reverse=True
        )

    def _aggregate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        结果聚合

        Args:
            results: 排序后的结果

        Returns:
            聚合后的结果
        """
        # 按文件ID聚合，避免重复
        aggregated = {}
        for result in results:
            file_id = result.get("file_id")
            if file_id not in aggregated:
                aggregated[file_id] = result
            else:
                # 如果已存在，保留相似度更高的结果
                if result.get("score", 0) > aggregated[file_id].get("score", 0):
                    aggregated[file_id] = result

        return list(aggregated.values())

    def _format_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        结果格式化

        Args:
            results: 聚合后的结果

        Returns:
            格式化后的结果
        """
        formatted = []
        for result in results:
            # 从数据库获取缩略图路径
            thumbnail_path = None
            preview_path = None

            file_path = result.get("file_path")
            if file_path:
                try:
                    # 尝试从数据库获取缩略图路径
                    if hasattr(self, "database_manager") and self.database_manager:
                        thumbnail_path = self.database_manager.get_thumbnail_by_path(
                            file_path
                        )
                        preview_path = self.database_manager.get_preview_by_path(
                            file_path
                        )
                except Exception as e:
                    logger.warning(f"获取缩略图路径失败: {e}")

            # 从modality推断file_type
            file_type = result.get("file_type")
            if not file_type:
                modality = result.get("modality", "unknown")
                file_type_map = {
                    "image": "image",
                    "video": "video",
                    "audio": "audio",
                    "text": "text",
                }
                file_type = file_type_map.get(modality, "unknown")

            formatted.append(
                {
                    "file_id": result.get("file_id"),
                    "file_path": result.get("file_path"),
                    "file_name": result.get("file_name"),
                    "file_type": file_type,
                    "modality": result.get("modality"),
                    "score": result.get("similarity", result.get("score", 0)),
                    "thumbnail_path": thumbnail_path,
                    "preview_path": preview_path,
                    "metadata": result.get("metadata", {}),
                    "timestamp_info": result.get("timestamp_info", {}),
                }
            )

        return formatted


def create_search_engine(
    embedding_engine: EmbeddingEngine,
    vector_store: VectorStore,
    config: Optional[Dict[str, Any]] = None,
) -> SearchEngine:
    """
    创建SearchEngine实例（工厂函数）

    Args:
        embedding_engine: 向量化引擎
        vector_store: 向量存储
        config: 搜索配置

    Returns:
        SearchEngine实例
    """
    return SearchEngine(embedding_engine, vector_store, config=config)
