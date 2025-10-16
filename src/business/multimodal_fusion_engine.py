"""
多模态融合搜索引擎模块
负责多模态搜索结果的融合和排序
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import numpy as np

from src.core.config_manager import get_config_manager
from src.core.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class SearchResult:
    """搜索基础结果"""
    file_id: str
    file_path: str
    file_type: str
    similarity: float
    modality: str  # text/image/audio/video
    metadata: Optional[Dict] = None


@dataclass
class FusedSearchResult:
    """融合搜索结果"""
    file_id: str
    file_path: str
    file_type: str
    final_score: float  # 融合后的最终分数
    text_score: float = 0.0
    image_score: float = 0.0
    audio_score: float = 0.0
    video_score: float = 0.0
    confidence: float = 0.0
    metadata: Optional[Dict] = None


class MultiModalFusionEngine:
    """多模态融合搜索引擎"""
    
    def __init__(self):
        self.config_manager = get_config_manager()
        self.config = self.config_manager.config
        
        # 默认融合权重
        self.default_fusion_weights = {
            "text": 0.3,
            "image": 0.25,
            "audio": 0.2,
            "video": 0.25
        }
        
        # 融合算法配置
        self.score_normalization = True  # 是否进行分数归一化
        self.min_confidence = 0.1  # 最小置信度阈值
        
        logger.info("多模态融合搜索引擎初始化完成")
    
    async def fuse_search_results(self, 
                                text_results: List[SearchResult],
                                image_results: List[SearchResult],
                                audio_results: List[SearchResult],
                                video_results: List[SearchResult],
                                query: str,
                                weights: Optional[Dict[str, float]] = None) -> List[FusedSearchResult]:
        """
        融合多模态搜索结果
        
        Args:
            text_results: 文本搜索结果
            image_results: 图像搜索结果
            audio_results: 音频搜索结果
            video_results: 音频搜索结果
            query: 搜索查询
            weights: 各模态权重配置
            
        Returns:
            融合后的搜索结果列表
        """
        logger.info(f"开始多模态搜索结果融合: text={len(text_results)}, "
                   f"image={len(image_results)}, audio={len(audio_results)}, video={len(video_results)}")
        
        try:
            # 动态调整权重
            if weights is None:
                weights = self._adjust_weights_based_on_query(query)
            
            # 合并所有结果
            all_results = self._combine_results_by_file(
                text_results, image_results, audio_results, video_results
            )
            
            # 计算融合分数
            fused_results = []
            for file_id, modality_scores in all_results.items():
                fused_result = self._calculate_fused_score(file_id, modality_scores, weights)
                
                # 过滤低置信度结果
                if fused_result.confidence >= self.min_confidence:
                    fused_results.append(fused_result)
            
            # 按最终分数排序
            fused_results.sort(key=lambda x: x.final_score, reverse=True)
            
            logger.info(f"多模态搜索结果融合完成，返回 {len(fused_results)} 个融合结果")
            return fused_results
            
        except Exception as e:
            logger.error(f"多模态搜索结果融合失败: {e}")
            return []
    
    def _combine_results_by_file(self, 
                               text_results: List[SearchResult],
                               image_results: List[SearchResult],
                               audio_results: List[SearchResult],
                               video_results: List[SearchResult]) -> Dict[str, Dict]:
        """按文件ID合并各模态的搜索结果"""
        combined_results = {}
        
        # 处理文本结果
        for result in text_results:
            if result.file_id not in combined_results:
                combined_results[result.file_id] = {
                    "file_path": result.file_path,
                    "file_type": result.file_type,
                    "text_score": result.similarity,
                    "image_score": 0.0,
                    "audio_score": 0.0,
                    "video_score": 0.0,
                    "metadata": result.metadata
                }
            else:
                combined_results[result.file_id]["text_score"] = max(
                    combined_results[result.file_id]["text_score"], result.similarity
                )
        
        # 处理图像结果
        for result in image_results:
            if result.file_id not in combined_results:
                combined_results[result.file_id] = {
                    "file_path": result.file_path,
                    "file_type": result.file_type,
                    "text_score": 0.0,
                    "image_score": result.similarity,
                    "audio_score": 0.0,
                    "video_score": 0.0,
                    "metadata": result.metadata
                }
            else:
                combined_results[result.file_id]["image_score"] = max(
                    combined_results[result.file_id]["image_score"], result.similarity
                )
        
        # 处理音频结果
        for result in audio_results:
            if result.file_id not in combined_results:
                combined_results[result.file_id] = {
                    "file_path": result.file_path,
                    "file_type": result.file_type,
                    "text_score": 0.0,
                    "image_score": 0.0,
                    "audio_score": result.similarity,
                    "video_score": 0.0,
                    "metadata": result.metadata
                }
            else:
                combined_results[result.file_id]["audio_score"] = max(
                    combined_results[result.file_id]["audio_score"], result.similarity
                )
        
        # 处理视频结果
        for result in video_results:
            if result.file_id not in combined_results:
                combined_results[result.file_id] = {
                    "file_path": result.file_path,
                    "file_type": result.file_type,
                    "text_score": 0.0,
                    "image_score": 0.0,
                    "audio_score": 0.0,
                    "video_score": result.similarity,
                    "metadata": result.metadata
                }
            else:
                combined_results[result.file_id]["video_score"] = max(
                    combined_results[result.file_id]["video_score"], result.similarity
                )
        
        return combined_results
    
    def _calculate_fused_score(self, 
                             file_id: str, 
                             modality_scores: Dict, 
                             weights: Dict[str, float]) -> FusedSearchResult:
        """计算融合分数"""
        
        # 获取各模态分数
        text_score = modality_scores["text_score"]
        image_score = modality_scores["image_score"]
        audio_score = modality_scores["audio_score"]
        video_score = modality_scores["video_score"]
        
        # 分数归一化
        if self.score_normalization:
            scores = [text_score, image_score, audio_score, video_score]
            max_score = max(scores) if max(scores) > 0 else 1.0
            if max_score > 0:
                text_score /= max_score
                image_score /= max_score
                audio_score /= max_score
                video_score /= max_score
        
        # 计算加权融合分数
        final_score = (
            text_score * weights["text"] +
            image_score * weights["image"] +
            audio_score * weights["audio"] +
            video_score * weights["video"]
        )
        
        # 计算置信度（基于有效模态数量和分数）
        valid_modalities = sum(1 for score in [text_score, image_score, audio_score, video_score] if score > 0)
        confidence = min(final_score * (1 + valid_modalities * 0.15), 1.0)
        
        return FusedSearchResult(
            file_id=file_id,
            file_path=modality_scores["file_path"],
            file_type=modality_scores["file_type"],
            final_score=final_score,
            text_score=text_score,
            image_score=image_score,
            audio_score=audio_score,
            video_score=video_score,
            confidence=confidence,
            metadata=modality_scores.get("metadata")
        )
    
    def _adjust_weights_based_on_query(self, query: str) -> Dict[str, float]:
        """根据查询内容动态调整权重"""
        query_lower = query.lower()
        
        # 文本相关关键词
        text_keywords = ["文档", "文本", "文章", "内容", "描述", "说明", "文字"]
        # 图像相关关键词
        image_keywords = ["图片", "图像", "照片", "画面", "视觉", "颜色", "形状", "截图"]
        # 音频相关关键词
        audio_keywords = ["音乐", "声音", "音频", "歌曲", "旋律", "节奏", "音效", "录音"]
        # 视频相关关键词
        video_keywords = ["视频", "影片", "录像", "电影", "动画", "剪辑", "录制"]
        
        # 检测查询类型
        text_count = sum(1 for keyword in text_keywords if keyword in query_lower)
        image_count = sum(1 for keyword in image_keywords if keyword in query_lower)
        audio_count = sum(1 for keyword in audio_keywords if keyword in query_lower)
        video_count = sum(1 for keyword in video_keywords if keyword in query_lower)
        
        # 动态调整权重
        if text_count > image_count and text_count > audio_count and text_count > video_count:
            # 文本主导查询
            return {"text": 0.5, "image": 0.2, "audio": 0.15, "video": 0.15}
        elif image_count > text_count and image_count > audio_count and image_count > video_count:
            # 图像主导查询
            return {"text": 0.15, "image": 0.5, "audio": 0.15, "video": 0.2}
        elif audio_count > text_count and audio_count > image_count and audio_count > video_count:
            # 音频主导查询
            return {"text": 0.15, "image": 0.15, "audio": 0.5, "video": 0.2}
        elif video_count > text_count and video_count > image_count and video_count > audio_count:
            # 视频主导查询
            return {"text": 0.15, "image": 0.2, "audio": 0.15, "video": 0.5}
        else:
            # 均衡查询
            return self.default_fusion_weights
    
    async def rank_results_by_relevance(self, 
                                      fused_results: List[FusedSearchResult],
                                      query: str,
                                      ranking_factors: Optional[Dict[str, float]] = None) -> List[FusedSearchResult]:
        """
        根据相关性对结果进行排序
        
        Args:
            fused_results: 融合后的搜索结果
            query: 搜索查询
            ranking_factors: 排序因子权重
            
        Returns:
            重新排序后的结果
        """
        if ranking_factors is None:
            ranking_factors = {
                "score": 0.6,      # 融合分数权重
                "recency": 0.2,    # 时效性权重
                "popularity": 0.1, # 流行度权重
                "quality": 0.1     # 质量权重
            }
        
        # 计算每个结果的综合排名分数
        ranked_results = []
        for result in fused_results:
            # 获取元数据
            metadata = result.metadata or {}
            
            # 计算各项排名因子
            score_factor = result.final_score
            recency_factor = self._calculate_recency_factor(metadata)
            popularity_factor = self._calculate_popularity_factor(metadata)
            quality_factor = self._calculate_quality_factor(metadata)
            
            # 计算综合排名分数
            ranking_score = (
                score_factor * ranking_factors["score"] +
                recency_factor * ranking_factors["recency"] +
                popularity_factor * ranking_factors["popularity"] +
                quality_factor * ranking_factors["quality"]
            )
            
            # 创建新的结果对象（保持原数据，添加排名分数）
            ranked_result = FusedSearchResult(
                file_id=result.file_id,
                file_path=result.file_path,
                file_type=result.file_type,
                final_score=ranking_score,  # 使用排名分数作为最终分数
                text_score=result.text_score,
                image_score=result.image_score,
                audio_score=result.audio_score,
                video_score=result.video_score,
                confidence=result.confidence,
                metadata=result.metadata
            )
            ranked_results.append(ranked_result)
        
        # 按排名分数排序
        ranked_results.sort(key=lambda x: x.final_score, reverse=True)
        
        return ranked_results
    
    def _calculate_recency_factor(self, metadata: Dict) -> float:
        """计算时效性因子"""
        # 这里可以基于文件创建时间、修改时间等计算时效性
        # 暂时返回默认值
        return 0.5
    
    def _calculate_popularity_factor(self, metadata: Dict) -> float:
        """计算流行度因子"""
        # 这里可以基于访问频率、下载次数等计算流行度
        # 暂时返回默认值
        return 0.5
    
    def _calculate_quality_factor(self, metadata: Dict) -> float:
        """计算质量因子"""
        # 这里可以基于文件大小、分辨率、时长等计算质量
        # 暂时返回默认值
        return 0.5


# 全局多模态融合引擎实例
_fusion_engine = None


def get_fusion_engine() -> MultiModalFusionEngine:
    """获取全局多模态融合引擎实例"""
    global _fusion_engine
    if _fusion_engine is None:
        _fusion_engine = MultiModalFusionEngine()
    return _fusion_engine