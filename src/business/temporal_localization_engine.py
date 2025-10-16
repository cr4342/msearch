"""
时间定位引擎模块
负责多模态时间戳融合和精确时间定位
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from src.core.config_manager import get_config_manager
from src.core.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class TimestampMatch:
    """时间戳匹配结果"""
    timestamp: float  # 时间戳（秒）
    similarity: float  # 相似度分数
    modality: str  # 模态类型：visual/audio/speech
    segment_info: Optional[Dict] = None  # 片段信息


@dataclass
class FusedTimestamp:
    """融合时间戳结果"""
    timestamp: float  # 融合后的时间戳
    total_score: float  # 融合总分
    visual_score: float = 0.0  # 视觉模态分数
    audio_score: float = 0.0  # 音频模态分数
    speech_score: float = 0.0  # 语音模态分数
    confidence: float = 0.0  # 置信度


class TemporalLocalizationEngine:
    """时间定位引擎 - 多模态时间戳融合"""
    
    def __init__(self):
        self.config_manager = get_config_manager()
        self.config = self.config_manager.config
        
        # 默认权重配置
        self.default_weights = {
            "visual": 0.4,  # 视觉模态权重
            "audio": 0.3,   # 音频模态权重
            "speech": 0.3   # 语音模态权重
        }
        
        # 时间窗口配置
        self.time_window_size = 5  # 时间窗口大小（秒）
        self.min_confidence = 0.3  # 最小置信度阈值
        
        logger.info("时间定位引擎初始化完成")
    
    async def fuse_temporal_results(self, 
                                   visual_matches: List[TimestampMatch],
                                   audio_matches: List[TimestampMatch],
                                   speech_matches: List[TimestampMatch],
                                   weights: Optional[Dict[str, float]] = None) -> List[FusedTimestamp]:
        """
        融合多模态的时间戳结果
        
        Args:
            visual_matches: 视觉模态匹配结果
            audio_matches: 音频模态匹配结果
            speech_matches: 语音模态匹配结果
            weights: 各模态权重配置
            
        Returns:
            融合后的时间戳结果列表
        """
        logger.info(f"开始多模态时间戳融合: visual={len(visual_matches)}, "
                   f"audio={len(audio_matches)}, speech={len(speech_matches)}")
        
        try:
            # 使用配置权重或默认权重
            if weights is None:
                weights = self.default_weights
            
            # 收集所有时间戳到时间窗口
            time_windows = self._create_time_windows(visual_matches, audio_matches, speech_matches)
            
            # 计算每个时间窗口的融合得分
            fused_results = []
            for window_center, window_data in time_windows.items():
                fused_timestamp = self._calculate_fused_score(window_data, weights)
                
                # 过滤低置信度结果
                if fused_timestamp.confidence >= self.min_confidence:
                    fused_results.append(fused_timestamp)
            
            # 按融合总分排序
            fused_results.sort(key=lambda x: x.total_score, reverse=True)
            
            logger.info(f"多模态时间戳融合完成，返回 {len(fused_results)} 个融合结果")
            return fused_results
            
        except Exception as e:
            logger.error(f"多模态时间戳融合失败: {e}")
            return []
    
    def _create_time_windows(self, 
                            visual_matches: List[TimestampMatch],
                            audio_matches: List[TimestampMatch],
                            speech_matches: List[TimestampMatch]) -> Dict[float, Dict]:
        """创建时间窗口并聚合匹配结果"""
        time_windows = {}
        
        # 处理视觉匹配
        for match in visual_matches:
            window_key = self._round_to_window(match.timestamp)
            if window_key not in time_windows:
                time_windows[window_key] = {
                    "visual_matches": [],
                    "audio_matches": [],
                    "speech_matches": [],
                    "window_center": window_key
                }
            time_windows[window_key]["visual_matches"].append(match)
        
        # 处理音频匹配
        for match in audio_matches:
            window_key = self._round_to_window(match.timestamp)
            if window_key not in time_windows:
                time_windows[window_key] = {
                    "visual_matches": [],
                    "audio_matches": [],
                    "speech_matches": [],
                    "window_center": window_key
                }
            time_windows[window_key]["audio_matches"].append(match)
        
        # 处理语音匹配
        for match in speech_matches:
            window_key = self._round_to_window(match.timestamp)
            if window_key not in time_windows:
                time_windows[window_key] = {
                    "visual_matches": [],
                    "audio_matches": [],
                    "speech_matches": [],
                    "window_center": window_key
                }
            time_windows[window_key]["speech_matches"].append(match)
        
        return time_windows
    
    def _round_to_window(self, timestamp: float) -> float:
        """将时间戳舍入到时间窗口中心"""
        return round(timestamp / self.time_window_size) * self.time_window_size
    
    def _calculate_fused_score(self, window_data: Dict, weights: Dict[str, float]) -> FusedTimestamp:
        """计算时间窗口的融合得分"""
        window_center = window_data["window_center"]
        
        # 计算各模态的最高分数
        visual_max = max([match.similarity for match in window_data["visual_matches"]]) if window_data["visual_matches"] else 0.0
        audio_max = max([match.similarity for match in window_data["audio_matches"]]) if window_data["audio_matches"] else 0.0
        speech_max = max([match.similarity for match in window_data["speech_matches"]]) if window_data["speech_matches"] else 0.0
        
        # 计算融合总分
        total_score = (
            visual_max * weights["visual"] +
            audio_max * weights["audio"] +
            speech_max * weights["speech"]
        )
        
        # 计算置信度（基于匹配结果数量和分数）
        match_count = (
            len(window_data["visual_matches"]) +
            len(window_data["audio_matches"]) +
            len(window_data["speech_matches"])
        )
        confidence = min(total_score * (1 + match_count * 0.1), 1.0)
        
        return FusedTimestamp(
            timestamp=window_center,
            total_score=total_score,
            visual_score=visual_max,
            audio_score=audio_max,
            speech_score=speech_max,
            confidence=confidence
        )
    
    async def locate_best_timestamp(self, 
                                   visual_matches: List[TimestampMatch],
                                   audio_matches: List[TimestampMatch],
                                   speech_matches: List[TimestampMatch],
                                   weights: Optional[Dict[str, float]] = None) -> Optional[FusedTimestamp]:
        """定位最佳时间戳"""
        fused_results = await self.fuse_temporal_results(visual_matches, audio_matches, speech_matches, weights)
        
        if fused_results:
            return fused_results[0]  # 返回分数最高的结果
        
        return None
    
    async def locate_multiple_timestamps(self, 
                                       visual_matches: List[TimestampMatch],
                                       audio_matches: List[TimestampMatch],
                                       speech_matches: List[TimestampMatch],
                                       top_k: int = 3,
                                       weights: Optional[Dict[str, float]] = None) -> List[FusedTimestamp]:
        """定位多个最佳时间戳"""
        fused_results = await self.fuse_temporal_results(visual_matches, audio_matches, speech_matches, weights)
        
        return fused_results[:top_k]
    
    def adjust_weights_based_on_query(self, query: str) -> Dict[str, float]:
        """根据查询内容动态调整权重"""
        query_lower = query.lower()
        
        # 视觉相关关键词
        visual_keywords = ["图片", "图像", "照片", "画面", "视频", "视觉", "颜色", "形状"]
        # 音频相关关键词
        audio_keywords = ["音乐", "声音", "音频", "歌曲", "旋律", "节奏", "音效"]
        # 语音相关关键词
        speech_keywords = ["说话", "语音", "对话", "会议", "讨论", "讲话", "播客"]
        
        # 检测查询类型
        visual_count = sum(1 for keyword in visual_keywords if keyword in query_lower)
        audio_count = sum(1 for keyword in audio_keywords if keyword in query_lower)
        speech_count = sum(1 for keyword in speech_keywords if keyword in query_lower)
        
        # 动态调整权重
        if visual_count > audio_count and visual_count > speech_count:
            # 视觉主导查询
            return {"visual": 0.6, "audio": 0.2, "speech": 0.2}
        elif audio_count > visual_count and audio_count > speech_count:
            # 音频主导查询
            return {"visual": 0.2, "audio": 0.6, "speech": 0.2}
        elif speech_count > visual_count and speech_count > audio_count:
            # 语音主导查询
            return {"visual": 0.2, "audio": 0.2, "speech": 0.6}
        else:
            # 均衡查询
            return self.default_weights


# 全局时间定位引擎实例
_temporal_engine = None


def get_temporal_engine() -> TemporalLocalizationEngine:
    """获取全局时间定位引擎实例"""
    global _temporal_engine
    if _temporal_engine is None:
        _temporal_engine = TemporalLocalizationEngine()
    return _temporal_engine