# -*- coding: utf-8 -*-
"""
结果排序器模块

提供搜索结果排序和融合功能。
"""

from typing import Optional, Dict, Any, List
import numpy as np

from ...data.models.search_models import SearchResultItem, MultimodalSearchResult


class ResultRanker:
    """结果排序器"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化结果排序器

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.logger = None

        # 排序配置
        self.default_weights = self.config.get(
            "default_weights",
            {"text": 1.0, "image": 1.0, "audio": 1.0, "video": 1.0, "face": 1.0},
        )

        # 去重配置
        self.enable_deduplication = self.config.get("enable_deduplication", True)
        self.deduplication_threshold = self.config.get("deduplication_threshold", 0.95)

    def rank_results(
        self, results: List[SearchResultItem], reverse: bool = True
    ) -> List[SearchResultItem]:
        """
        对结果进行排序

        Args:
            results: 搜索结果列表
            reverse: 是否降序排序

        Returns:
            排序后的搜索结果列表
        """
        try:
            # 按相似度排序
            sorted_results = sorted(
                results, key=lambda x: x.similarity, reverse=reverse
            )

            return sorted_results

        except Exception as e:
            if self.logger:
                self.logger.error(f"排序结果失败: {e}")
            return results

    def fuse_results(
        self, multimodal_result: MultimodalSearchResult
    ) -> List[SearchResultItem]:
        """
        融合多模态搜索结果

        Args:
            multimodal_result: 多模态搜索结果对象

        Returns:
            融合后的搜索结果列表
        """
        try:
            # 收集所有结果
            all_results = []

            if multimodal_result.text_results:
                all_results.extend(
                    [
                        (r, "text", multimodal_result.weights.get("text", 1.0))
                        for r in multimodal_result.text_results
                    ]
                )

            if multimodal_result.image_results:
                all_results.extend(
                    [
                        (r, "image", multimodal_result.weights.get("image", 1.0))
                        for r in multimodal_result.image_results
                    ]
                )

            if multimodal_result.audio_results:
                all_results.extend(
                    [
                        (r, "audio", multimodal_result.weights.get("audio", 1.0))
                        for r in multimodal_result.audio_results
                    ]
                )

            if multimodal_result.video_results:
                all_results.extend(
                    [
                        (r, "video", multimodal_result.weights.get("video", 1.0))
                        for r in multimodal_result.video_results
                    ]
                )

            if multimodal_result.face_results:
                all_results.extend(
                    [
                        (r, "face", multimodal_result.weights.get("face", 1.0))
                        for r in multimodal_result.face_results
                    ]
                )

            # 融合结果
            fused_results = self._fuse_by_file_id(all_results)

            # 排序
            fused_results = self.rank_results(fused_results)

            return fused_results

        except Exception as e:
            if self.logger:
                self.logger.error(f"融合结果失败: {e}")
            return []

    def _fuse_by_file_id(self, weighted_results: List[tuple]) -> List[SearchResultItem]:
        """
        按文件ID融合结果

        Args:
            weighted_results: 带权重的结果列表 [(result, modality, weight), ...]

        Returns:
            融合后的搜索结果列表
        """
        # 按文件ID分组
        file_groups = {}

        for result, modality, weight in weighted_results:
            file_id = result.file_id

            if file_id not in file_groups:
                file_groups[file_id] = {
                    "results": [],
                    "max_similarity": 0.0,
                    "total_similarity": 0.0,
                    "count": 0,
                }

            # 应用权重
            weighted_similarity = result.similarity * weight

            file_groups[file_id]["results"].append(
                (result, modality, weighted_similarity)
            )
            file_groups[file_id]["max_similarity"] = max(
                file_groups[file_id]["max_similarity"], weighted_similarity
            )
            file_groups[file_id]["total_similarity"] += weighted_similarity
            file_groups[file_id]["count"] += 1

        # 融合每个文件的结果
        fused_results = []

        for file_id, group in file_groups.items():
            # 使用最大相似度作为最终相似度
            final_similarity = group["max_similarity"]

            # 或者使用平均相似度
            # final_similarity = group["total_similarity"] / group["count"]

            # 选择第一个结果作为基础
            base_result, base_modality, _ = group["results"][0]

            # 创建融合结果
            fused_result = SearchResultItem(
                file_id=base_result.file_id,
                file_path=base_result.file_path,
                file_name=base_result.file_name,
                file_type=base_result.file_type,
                similarity=final_similarity,
                modality=base_modality,
                timestamp=base_result.timestamp,
                segment_id=base_result.segment_id,
                thumbnail_path=base_result.thumbnail_path,
            )

            # 添加所有模态信息到元数据
            modalities = [modality for _, modality, _ in group["results"]]
            fused_result.metadata["modalities"] = modalities
            fused_result.metadata["match_count"] = group["count"]

            fused_results.append(fused_result)

        return fused_results

    def deduplicate_results(
        self, results: List[SearchResultItem]
    ) -> List[SearchResultItem]:
        """
        去重搜索结果

        Args:
            results: 搜索结果列表

        Returns:
            去重后的搜索结果列表
        """
        if not self.enable_deduplication:
            return results

        try:
            # 按文件ID去重
            seen_files = set()
            deduplicated_results = []

            for result in results:
                if result.file_id not in seen_files:
                    seen_files.add(result.file_id)
                    deduplicated_results.append(result)

            return deduplicated_results

        except Exception as e:
            if self.logger:
                self.logger.error(f"去重结果失败: {e}")
            return results

    def filter_by_threshold(
        self, results: List[SearchResultItem], threshold: float
    ) -> List[SearchResultItem]:
        """
        按阈值过滤结果

        Args:
            results: 搜索结果列表
            threshold: 相似度阈值

        Returns:
            过滤后的搜索结果列表
        """
        try:
            filtered_results = [r for r in results if r.similarity >= threshold]
            return filtered_results

        except Exception as e:
            if self.logger:
                self.logger.error(f"过滤结果失败: {e}")
            return results

    def apply_weights(
        self, results: List[SearchResultItem], weights: Dict[str, float]
    ) -> List[SearchResultItem]:
        """
        应用权重到结果

        Args:
            results: 搜索结果列表
            weights: 权重字典 {modality: weight}

        Returns:
            应用权重后的搜索结果列表
        """
        try:
            for result in results:
                weight = weights.get(result.modality, 1.0)
                result.similarity = result.similarity * weight

            return results

        except Exception as e:
            if self.logger:
                self.logger.error(f"应用权重失败: {e}")
            return results

    def normalize_scores(
        self, results: List[SearchResultItem]
    ) -> List[SearchResultItem]:
        """
        归一化分数

        Args:
            results: 搜索结果列表

        Returns:
            归一化后的搜索结果列表
        """
        try:
            if not results:
                return results

            # 获取所有分数
            scores = [r.similarity for r in results]

            # 计算最小值和最大值
            min_score = min(scores)
            max_score = max(scores)

            # 归一化到[0, 1]
            if max_score - min_score > 0:
                for result in results:
                    result.similarity = (result.similarity - min_score) / (
                        max_score - min_score
                    )

            return results

        except Exception as e:
            if self.logger:
                self.logger.error(f"归一化分数失败: {e}")
            return results

    def re_rank_by_recency(
        self, results: List[SearchResultItem], recency_weight: float = 0.1
    ) -> List[SearchResultItem]:
        """
        按时间重新排序

        Args:
            results: 搜索结果列表
            recency_weight: 时间权重（0-1）

        Returns:
            重新排序后的搜索结果列表
        """
        try:
            if not results or recency_weight <= 0:
                return results

            # 获取所有时间戳
            timestamps = [r.metadata.get("created_at", 0) for r in results]

            # 计算时间分数
            if timestamps and max(timestamps) > 0:
                for result in results:
                    timestamp = result.metadata.get("created_at", 0)
                    time_score = timestamp / max(timestamps)

                    # 融合相似度分数和时间分数
                    result.similarity = (
                        1 - recency_weight
                    ) * result.similarity + recency_weight * time_score

            # 重新排序
            return self.rank_results(results)

        except Exception as e:
            if self.logger:
                self.logger.error(f"按时间重新排序失败: {e}")
            return results

    def get_top_k(
        self, results: List[SearchResultItem], k: int
    ) -> List[SearchResultItem]:
        """
        获取前K个结果

        Args:
            results: 搜索结果列表
            k: 结果数量

        Returns:
            前K个搜索结果
        """
        try:
            # 先排序
            sorted_results = self.rank_results(results)

            # 返回前K个
            return sorted_results[:k]

        except Exception as e:
            if self.logger:
                self.logger.error(f"获取前K个结果失败: {e}")
            return results[:k]

    def calculate_diversity(self, results: List[SearchResultItem]) -> float:
        """
        计算结果的多样性

        Args:
            results: 搜索结果列表

        Returns:
            多样性分数（0-1）
        """
        try:
            if len(results) < 2:
                return 0.0

            # 计算文件类型的多样性
            file_types = set(r.file_type for r in results)
            type_diversity = len(file_types) / len(results)

            # 计算模态的多样性
            modalities = set(r.modality for r in results)
            modality_diversity = len(modalities) / len(results)

            # 平均多样性
            diversity = (type_diversity + modality_diversity) / 2

            return diversity

        except Exception as e:
            if self.logger:
                self.logger.error(f"计算多样性失败: {e}")
            return 0.0
