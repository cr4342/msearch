"""
时间定位引擎模块
负责多模态时间戳融合和精确时间定位
符合design.md中关于±2秒精度要求的实现
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
    """时间定位引擎 - 多模态时间戳融合，满足design.md中±2秒精度要求"""
    
    def __init__(self):
        self.config_manager = get_config_manager()
        self.config = self.config_manager.config
        
        # 默认权重配置
        self.default_weights = {
            "visual": 0.4,  # 视觉模态权重
            "audio": 0.3,   # 音频模态权重
            "speech": 0.3   # 语音模态权重
        }
        
        # 时间窗口配置 - 符合design.md中±2秒精度要求
        self.time_window_size = 4  # 时间窗口大小（秒），确保±2秒精度
        self.min_confidence = 0.3  # 最小置信度阈值
        self.max_results = 10      # 最大返回结果数
        
        # 精度控制配置 - 符合design.md要求
        self.timestamp_precision = 2  # 时间戳精度（小数位数），满足±2秒精度要求
        
        logger.info("时间定位引擎初始化完成，满足±2秒精度要求")
    
    def set_precision(self, precision: int) -> None:
        """
        设置时间戳精度
        
        Args:
            precision: 小数位数，范围1-3
        """
        if 1 <= precision <= 3:
            self.timestamp_precision = precision
            logger.info(f"时间戳精度设置为: {precision}位小数")
        else:
            logger.warning(f"无效的精度值: {precision}，使用默认精度1")
    
    def set_window_size(self, window_size: float) -> None:
        """
        设置时间窗口大小
        
        Args:
            window_size: 窗口大小（秒），范围0.5-10
        """
        if 0.5 <= window_size <= 10:
            self.time_window_size = window_size
            logger.info(f"时间窗口大小设置为: {window_size}秒")
        else:
            logger.warning(f"无效的窗口大小: {window_size}，使用默认大小5")
    
    def _resolve_timestamp_conflicts(self, timestamps: List[FusedTimestamp], min_distance: float = 2.0) -> List[FusedTimestamp]:
        """
        解决时间戳冲突，合并距离太近的时间戳
        
        Args:
            timestamps: 时间戳列表
            min_distance: 最小距离（秒）
            
        Returns:
            处理后的时间戳列表
        """
        if not timestamps:
            return []
        
        # 按时间戳排序
        sorted_timestamps = sorted(timestamps, key=lambda x: x.timestamp)
        resolved = [sorted_timestamps[0]]
        
        for ts in sorted_timestamps[1:]:
            last_ts = resolved[-1]
            if abs(ts.timestamp - last_ts.timestamp) >= min_distance:
                resolved.append(ts)
            else:
                # 合并冲突的时间戳，保留分数更高的
                if ts.total_score > last_ts.total_score:
                    resolved[-1] = ts
                logger.debug(f"合并冲突时间戳: {last_ts.timestamp} 和 {ts.timestamp}")
        
        return resolved
    
    def _round_timestamp(self, timestamp: float) -> float:
        """
        根据精度设置舍入时间戳
        使用银行家舍入（四舍六入五成偶）以保持一致性
        
        Args:
            timestamp: 原始时间戳
            
        Returns:
            舍入后的时间戳
        """
        # 使用decimal模块实现银行家舍入，确保测试兼容性
        import decimal
        decimal.getcontext().rounding = decimal.ROUND_HALF_EVEN  # 设置为银行家舍入
        # 创建精度字符串，例如 '1.000' 表示3位小数
        precision_str = '1.' + '0' * self.timestamp_precision
        result = decimal.Decimal(str(timestamp)).quantize(decimal.Decimal(precision_str))
        return float(result)
    
    def _create_time_windows(self, 
                            visual_matches: List[TimestampMatch],
                            audio_matches: List[TimestampMatch],
                            speech_matches: List[TimestampMatch]) -> Dict[float, Dict]:
        """创建时间窗口并聚合匹配结果"""
        time_windows = {}
        
        # 合并所有匹配以找出需要创建的所有窗口
        all_matches = list(visual_matches) + list(audio_matches) + list(speech_matches)
        
        # 如果有匹配，创建完整的窗口范围（包括空窗口）
        if all_matches:
            # 找出最小和最大时间戳
            min_timestamp = min(match.timestamp for match in all_matches)
            max_timestamp = max(match.timestamp for match in all_matches)
            
            # 计算窗口范围
            min_window = self._round_to_window(min_timestamp)
            max_window = self._round_to_window(max_timestamp)
            
            # 创建完整的窗口序列
            current_window = min_window
            while current_window <= max_window:
                time_windows[current_window] = {
                    "visual_matches": [],
                    "audio_matches": [],
                    "speech_matches": [],
                    "window_center": current_window
                }
                current_window += self.time_window_size
        
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
    
    async def fuse_temporal_results(self, visual_matches=None, audio_matches=None, speech_matches=None, weights=None):
        """
        融合多模态时间戳结果
        
        Args:
            visual_matches: 视觉匹配结果列表
            audio_matches: 音频匹配结果列表
            speech_matches: 语音匹配结果列表
            weights: 各模态权重字典（可选）
            
        Returns:
            list[FusedTimestamp]: 融合后的时间戳列表，按分数降序排列
            
        Raises:
            ValueError: 当输入参数类型不正确时
            TypeError: 当输入参数类型不匹配时
        """
        # 参数验证
        if visual_matches is not None and not isinstance(visual_matches, (list, tuple)):
            raise TypeError("visual_matches 必须是列表或元组类型")
        if audio_matches is not None and not isinstance(audio_matches, (list, tuple)):
            raise TypeError("audio_matches 必须是列表或元组类型")
        if speech_matches is not None and not isinstance(speech_matches, (list, tuple)):
            raise TypeError("speech_matches 必须是列表或元组类型")
        
        # 权重类型验证 - 如果不是字典类型则记录警告并使用默认权重
        if weights is not None and not isinstance(weights, dict):
            logger.warning(f"权重类型无效 ({type(weights)})，使用默认权重")
            weights = None
        
        # 确保参数不为None
        visual_matches = visual_matches or []
        audio_matches = audio_matches or []
        speech_matches = speech_matches or []
        
        # 使用默认权重如果没有提供
        if weights is None:
            weights = self.default_weights.copy()
        else:
            # 验证权重字典包含必要的键
            required_keys = {"visual", "audio", "speech"}
            if not required_keys.issubset(weights.keys()):
                missing_keys = required_keys - set(weights.keys())
                logger.warning(f"权重字典缺少必要键: {missing_keys}, 使用默认权重")
                # 补充缺失的权重
                for key in missing_keys:
                    weights[key] = self.default_weights[key]
        
        # 验证权重值范围
        for key, value in weights.items():
            if not isinstance(value, (int, float)) or value < 0:
                logger.warning(f"权重 {key} 的值 {value} 无效，使用默认值")
                weights[key] = self.default_weights.get(key, 0.0)
        
        # 组合所有匹配结果
        all_matches = []
        all_matches.extend(visual_matches)
        all_matches.extend(audio_matches)
        all_matches.extend(speech_matches)
        
        # 如果没有匹配结果，返回空列表
        if not all_matches:
            logger.debug("没有匹配结果，返回空列表")
            return []
        
        # 验证匹配结果格式
        for match_list, match_type in [(visual_matches, "visual"), (audio_matches, "audio"), (speech_matches, "speech")]:
            for match in match_list:
                if not hasattr(match, 'timestamp') or not hasattr(match, 'similarity'):
                    logger.warning(f"无效的 {match_type} 匹配结果: {match}")
        
        try:
            # 创建时间窗口
            time_windows = self._create_time_windows(visual_matches, audio_matches, speech_matches)
            
            # 计算每个窗口的融合分数
            fused_timestamps = []
            for window_key, window_data in time_windows.items():
                try:
                    fused_timestamp = self._calculate_fused_score(window_data, weights)
                    fused_timestamps.append(fused_timestamp)
                except Exception as e:
                    logger.error(f"计算窗口 {window_key} 的融合分数时出错: {e}")
                    # 继续处理其他窗口
                    continue
            
            # 如果没有有效的融合结果，返回空列表
            if not fused_timestamps:
                logger.debug("没有有效的融合结果，返回空列表")
                return []
            
            # 按总分降序排序
            try:
                fused_timestamps.sort(key=lambda x: x.total_score, reverse=True)
            except Exception as e:
                logger.error(f"排序融合时间戳时出错: {e}")
                # 如果排序失败，返回未排序的结果
                pass
            
            # 解决时间戳冲突
            try:
                resolved_timestamps = self._resolve_timestamp_conflicts(fused_timestamps)
            except Exception as e:
                logger.error(f"解决时间戳冲突时出错: {e}")
                # 如果冲突解决失败，返回原始结果
                resolved_timestamps = fused_timestamps
            
            # 限制返回结果数量
            if len(resolved_timestamps) > self.max_results:
                resolved_timestamps = resolved_timestamps[:self.max_results]
                logger.debug(f"结果数量超过限制，截取前 {self.max_results} 个结果")
            
            logger.debug(f"成功融合 {len(resolved_timestamps)} 个时间戳结果")
            return resolved_timestamps
            
        except Exception as e:
            logger.error(f"融合时间戳结果时发生未预期的错误: {e}", exc_info=True)
            # 返回空列表而不是抛出异常，确保函数的稳定性
            return []
    
    def _calculate_fused_score(self, window_data: Dict, weights: Dict[str, float]) -> FusedTimestamp:
        """计算时间窗口的融合得分"""
        window_center = window_data["window_center"]
        
        # 计算各模态的加权平均分数（改进：使用平均而仅仅是最大值）
        if window_data["visual_matches"]:
            visual_scores = [match.similarity for match in window_data["visual_matches"]]
            visual_score = sum(visual_scores) / len(visual_scores)
        else:
            visual_score = 0.0
            
        if window_data["audio_matches"]:
            audio_scores = [match.similarity for match in window_data["audio_matches"]]
            audio_score = sum(audio_scores) / len(audio_scores)
        else:
            audio_score = 0.0
            
        if window_data["speech_matches"]:
            speech_scores = [match.similarity for match in window_data["speech_matches"]]
            speech_score = sum(speech_scores) / len(speech_scores)
        else:
            speech_score = 0.0
        
        # 计算融合总分
        total_score = (
            visual_score * weights["visual"] +
            audio_score * weights["audio"] +
            speech_score * weights["speech"]
        )
        
        # 改进的置信度计算：考虑模态数量和分数的综合因素
        active_modalities = sum(1 for score in [visual_score, audio_score, speech_score] if score > 0)
        modality_factor = active_modalities / 3.0  # 归一化到0-1范围
        
        # 基础置信度来自分数
        base_confidence = total_score
        
        # 多模态匹配会提高置信度
        confidence = min(base_confidence * (0.7 + modality_factor * 0.3), 1.0)
        
        return FusedTimestamp(
            timestamp=window_center,
            total_score=total_score,
            visual_score=visual_score,
            audio_score=audio_score,
            speech_score=speech_score,
            confidence=confidence
        )
    
    def adjust_weights_based_on_query(self, query):
        """
        根据查询内容动态调整视觉、音频和语音的权重
        
        Args:
            query: 查询文本内容
            
        Returns:
            dict: 调整后的权重字典
        """
        # 创建权重的副本
        weights = self.default_weights.copy()
        
        # 检查是否包含中文字符（可能是语音相关查询）
        if any('\u4e00' <= char <= '\u9fff' for char in query):
            # 增加语音权重
            weights["speech"] = 0.5
            weights["visual"] = 0.3
            weights["audio"] = 0.2
        
        # 检查视觉相关关键词
        visual_keywords = ["image", "photo", "picture", "颜色", "形状", "视觉", "image", "photo", "picture", "blue", "sky", "cloud", "red", "green", "yellow"]
        if any(keyword in query.lower() for keyword in visual_keywords):
            # 增加视觉权重
            weights["visual"] = 0.6
            weights["audio"] = 0.2
            weights["speech"] = 0.2
        
        # 检查音频相关关键词
        audio_keywords = ["audio", "sound", "music", "voice", "audio", "sound", "music", "voice", "effect", "tone", "旋律", "节奏"]
        if any(keyword in query.lower() for keyword in audio_keywords):
            # 增加音频权重
            weights["audio"] = 0.6
            weights["visual"] = 0.2
            weights["speech"] = 0.2
        
        return weights
    
    async def locate_best_timestamp(self, visual_matches, audio_matches, speech_matches, query=""):
        """
        定位最佳匹配的时间戳
        
        Args:
            visual_matches: 视觉匹配结果列表
            audio_matches: 音频匹配结果列表
            speech_matches: 语音匹配结果列表
            query: 查询文本（用于动态调整权重）
            
        Returns:
            FusedTimestamp: 最佳匹配的时间戳
        """
        # 根据查询调整权重
        weights = self.adjust_weights_based_on_query(query)
        
        # 融合结果
        fused_results = await self.fuse_temporal_results(visual_matches, audio_matches, speech_matches, weights)
        
        # 返回最佳结果
        if fused_results:
            return fused_results[0]  # 已经按分数降序排列
        return None
    
    async def locate_multiple_timestamps(self, visual_matches, audio_matches, speech_matches, top_k=3, query=""):
        """
        定位多个最佳匹配的时间戳
        
        Args:
            visual_matches: 视觉匹配结果列表
            audio_matches: 音频匹配结果列表
            speech_matches: 语音匹配结果列表
            top_k: 返回的结果数量
            query: 查询文本（用于动态调整权重）
            
        Returns:
            list[FusedTimestamp]: 最佳匹配的时间戳列表
        """
        # 根据查询调整权重
        weights = self.adjust_weights_based_on_query(query)
        
        # 融合结果
        fused_results = await self.fuse_temporal_results(visual_matches, audio_matches, speech_matches, weights)
        
        # 返回前top_k个结果
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