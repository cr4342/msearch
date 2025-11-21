"""
精确时间检索引擎 - 实现±2秒精度的时间戳检索
支持多模态时间同步和时间段合并

核心功能：
1. 视频时间戳精确匹配(±2秒精度)
2. 多模态时间同步验证
3. 场景感知的时间段合并
4. 重叠时间窗口处理
5. 时间连续性检测
"""
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
import logging
from dataclasses import dataclass

from src.processors.timestamp_processor import (
    TimestampInfo, ModalityType, TimeStampedResult, MergedTimeSegment
)
from src.storage.timestamp_database import TimestampDatabase, TimestampQueryBuilder

logger = logging.getLogger(__name__)


@dataclass
class RetrievalQuery:
    """检索查询参数"""
    query_vector: np.ndarray
    target_modality: ModalityType
    file_id: Optional[str] = None
    time_range: Optional[Tuple[float, float]] = None
    min_confidence: float = 0.0
    top_k: int = 50


@dataclass
class TimeAccurateResult:
    """精确时间检索结果"""
    file_id: str
    start_time: float
    end_time: float
    duration: float
    score: float
    confidence: float
    modality: ModalityType
    vector_id: str
    segment_id: str
    time_accuracy: str
    is_merged: bool = False
    merged_count: int = 1


class TimeAccurateRetrievalEngine:
    """精确时间检索引擎 - 实现±2秒精度的时间戳检索"""
    
    def __init__(self, config: Dict[str, Any], vector_store, timestamp_db: TimestampDatabase):
        """
        初始化精确时间检索引擎
        
        Args:
            config: 配置字典
            vector_store: 向量存储实例
            timestamp_db: 时间戳数据库实例
        """
        self.config = config
        self.vector_store = vector_store
        self.timestamp_db = timestamp_db
        
        # 从配置获取检索参数
        retrieval_config = config.get('search', {}).get('timestamp_retrieval', {})
        self.accuracy_requirement = retrieval_config.get('accuracy_requirement', 2.0)  # ±2秒
        self.overlap_buffer = 1.0  # 1秒重叠缓冲
        self.enable_segment_merging = retrieval_config.get('enable_segment_merging', True)
        self.merge_threshold = retrieval_config.get('merge_threshold', 2.0)
        self.continuity_detection = retrieval_config.get('continuity_detection', True)
        self.max_gap_tolerance = retrieval_config.get('max_gap_tolerance', 4.0)
        
        logger.info(f"精确时间检索引擎初始化完成 - 精度要求: ±{self.accuracy_requirement}秒")
    
    async def retrieve_with_timestamp(self, query: RetrievalQuery) -> List[TimeAccurateResult]:
        """
        带时间戳的精确检索
        
        Args:
            query: 检索查询参数
            
        Returns:
            精确时间检索结果列表
        """
        try:
            logger.debug(f"开始精确时间检索: modality={query.target_modality.value}, top_k={query.top_k}")
            
            # 1. 向量相似度检索
            similar_vectors = await self._vector_search(query.query_vector, query.target_modality, query.top_k * 2)
            
            if not similar_vectors:
                logger.warning("向量检索未返回任何结果")
                return []
            
            # 2. 获取时间戳信息
            timestamped_results = []
            for vector_result in similar_vectors:
                timestamp_info = self.timestamp_db.get_timestamp_info_by_vector_id(vector_result['vector_id'])
                
                if timestamp_info and self._validate_time_accuracy(timestamp_info):
                    # 应用查询过滤条件
                    if self._matches_query_filters(timestamp_info, query):
                        result = TimeStampedResult(
                            file_id=timestamp_info.file_id,
                            start_time=timestamp_info.start_time,
                            end_time=timestamp_info.end_time,
                            score=vector_result['score'],
                            vector_id=vector_result['vector_id'],
                            modality=query.target_modality,
                            timestamp_info=timestamp_info
                        )
                        timestamped_results.append(result)
            
            logger.debug(f"获取到{len(timestamped_results)}个带时间戳的结果")
            
            # 3. 时间段合并与去重(如果启用)
            if self.enable_segment_merging:
                merged_results = self._merge_overlapping_segments(timestamped_results)
                logger.debug(f"时间段合并完成: {len(timestamped_results)} -> {len(merged_results)}")
            else:
                merged_results = [MergedTimeSegment(result) for result in timestamped_results]
            
            # 4. 按相似度和时间连续性排序
            final_results = self._sort_by_relevance_and_continuity(merged_results)
            
            # 5. 转换为TimeAccurateResult格式
            accurate_results = self._convert_to_accurate_results(final_results[:query.top_k])
            
            logger.info(f"精确时间检索完成: 返回{len(accurate_results)}个结果")
            
            return accurate_results
            
        except Exception as e:
            logger.error(f"精确时间检索失败: {e}")
            return []
    
    def _validate_time_accuracy(self, timestamp_info: TimestampInfo) -> bool:
        """验证时间戳精度是否满足±2秒要求"""
        return timestamp_info.duration <= (self.accuracy_requirement * 2)
    
    def _matches_query_filters(self, timestamp_info: TimestampInfo, query: RetrievalQuery) -> bool:
        """检查时间戳信息是否匹配查询过滤条件"""
        # 文件ID过滤
        if query.file_id and timestamp_info.file_id != query.file_id:
            return False
        
        # 时间范围过滤
        if query.time_range:
            start_time, end_time = query.time_range
            if not (timestamp_info.start_time <= end_time and timestamp_info.end_time >= start_time):
                return False
        
        # 置信度过滤
        if timestamp_info.confidence < query.min_confidence:
            return False
        
        return True
    
    def _merge_overlapping_segments(self, results: List[TimeStampedResult]) -> List[MergedTimeSegment]:
        """合并重叠的时间段，提高检索连续性"""
        if not results:
            return []
        
        merged_segments = []
        
        # 按文件和时间排序
        sorted_results = sorted(results, key=lambda x: (x.file_id, x.start_time))
        
        current_segment = None
        for result in sorted_results:
            if current_segment is None:
                current_segment = MergedTimeSegment(result)
            elif self._is_time_continuous(current_segment, result):
                # 时间连续，合并到当前段
                current_segment.merge(result)
            else:
                # 时间不连续，开始新段
                merged_segments.append(current_segment)
                current_segment = MergedTimeSegment(result)
        
        if current_segment:
            merged_segments.append(current_segment)
        
        return merged_segments
    
    def _is_time_continuous(self, segment: MergedTimeSegment, result: TimeStampedResult) -> bool:
        """判断时间段是否连续(考虑±2秒精度要求)"""
        if not self.continuity_detection:
            return False
        
        # 检查是否为同一文件
        if segment.file_id != result.file_id:
            return False
        
        # 计算时间间隔
        time_gap = result.start_time - segment.end_time
        
        # 判断连续性
        is_continuous = abs(time_gap) <= self.merge_threshold
        
        if is_continuous:
            logger.debug(f"检测到连续时间段: gap={time_gap:.3f}s <= {self.merge_threshold}s")
        
        return is_continuous
    
    def _sort_by_relevance_and_continuity(self, segments: List[MergedTimeSegment]) -> List[MergedTimeSegment]:
        """按相似度和时间连续性排序"""
        try:
            # 计算综合得分：相似度 + 连续性奖励 + 多模态奖励
            for segment in segments:
                # 基础相似度得分
                base_score = segment.max_score
                
                # 连续性奖励(合并的段数越多，奖励越高)
                continuity_bonus = (len(segment.results) - 1) * 0.05
                
                # 多模态奖励(包含多种模态的段得分更高)
                multimodal_bonus = (len(segment.modalities) - 1) * 0.1
                
                # 场景边界奖励
                scene_boundary_bonus = 0.02 if any(r.timestamp_info.scene_boundary for r in segment.results) else 0
                
                # 计算最终得分
                segment.final_score = base_score + continuity_bonus + multimodal_bonus + scene_boundary_bonus
                
                logger.debug(f"段得分计算: base={base_score:.3f}, continuity={continuity_bonus:.3f}, "
                           f"multimodal={multimodal_bonus:.3f}, final={segment.final_score:.3f}")
            
            # 按综合得分排序
            segments.sort(key=lambda x: x.final_score, reverse=True)
            
            return segments
            
        except Exception as e:
            logger.error(f"结果排序失败: {e}")
            return segments
    
    def _convert_to_accurate_results(self, segments: List[MergedTimeSegment]) -> List[TimeAccurateResult]:
        """转换为TimeAccurateResult格式"""
        accurate_results = []
        
        for segment in segments:
            # 使用得分最高的结果作为代表
            best_result = max(segment.results, key=lambda x: x.score)
            
            accurate_result = TimeAccurateResult(
                file_id=segment.file_id,
                start_time=segment.start_time,
                end_time=segment.end_time,
                duration=segment.end_time - segment.start_time,
                score=segment.final_score,
                confidence=best_result.timestamp_info.confidence,
                modality=best_result.modality,
                vector_id=best_result.vector_id,
                segment_id=best_result.timestamp_info.segment_id,
                time_accuracy=f"±{self.accuracy_requirement}s",
                is_merged=len(segment.results) > 1,
                merged_count=len(segment.results)
            )
            
            accurate_results.append(accurate_result)
        
        return accurate_results
    
    async def _vector_search(self, query_vector: np.ndarray, modality: ModalityType, 
                           top_k: int) -> List[Dict[str, Any]]:
        """
        向量相似度搜索
        
        Args:
            query_vector: 查询向量
            modality: 目标模态
            top_k: 返回结果数量
            
        Returns:
            向量搜索结果列表
        """
        try:
            # 根据模态类型选择集合
            collection_mapping = {
                ModalityType.VISUAL: 'image_collection',
                ModalityType.AUDIO_MUSIC: 'audio_collection',
                ModalityType.AUDIO_SPEECH: 'audio_collection'
            }
            
            collection_name = collection_mapping.get(modality, 'image_collection')
            
            # 执行向量搜索
            search_results = await self.vector_store.search_vectors(
                collection_name=f"msearch_{collection_name}",
                query_vector=query_vector,
                top_k=top_k,
                score_threshold=0.1  # 最低相似度阈值
            )
            
            return search_results
            
        except Exception as e:
            logger.error(f"向量搜索失败: {e}")
            return []
    
    def get_video_segments_by_time_range(self, file_id: str, start_time: float, 
                                       end_time: float) -> List[TimeAccurateResult]:
        """
        获取指定时间范围内的视频段
        
        Args:
            file_id: 文件ID
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            时间范围内的结果列表
        """
        try:
            # 使用查询构建器
            query_builder = TimestampQueryBuilder(self.timestamp_db)
            timestamp_infos = (query_builder
                             .filter_by_file_id(file_id)
                             .filter_by_time_range(start_time, end_time)
                             .order_by_time()
                             .execute())
            
            # 转换为TimeAccurateResult
            results = []
            for ts_info in timestamp_infos:
                result = TimeAccurateResult(
                    file_id=ts_info.file_id,
                    start_time=ts_info.start_time,
                    end_time=ts_info.end_time,
                    duration=ts_info.duration,
                    score=ts_info.confidence,  # 使用置信度作为得分
                    confidence=ts_info.confidence,
                    modality=ts_info.modality,
                    vector_id=ts_info.vector_id or "",
                    segment_id=ts_info.segment_id,
                    time_accuracy=f"±{self.accuracy_requirement}s",
                    is_merged=False,
                    merged_count=1
                )
                results.append(result)
            
            logger.debug(f"时间范围查询完成: file_id={file_id}, "
                        f"range=[{start_time}, {end_time}], 结果数={len(results)}")
            
            return results
            
        except Exception as e:
            logger.error(f"时间范围查询失败: {e}")
            return []
    
    def get_scene_boundaries(self, file_id: str) -> List[TimeAccurateResult]:
        """
        获取文件的所有场景边界
        
        Args:
            file_id: 文件ID
            
        Returns:
            场景边界结果列表
        """
        try:
            # 使用查询构建器查询场景边界
            query_builder = TimestampQueryBuilder(self.timestamp_db)
            timestamp_infos = (query_builder
                             .filter_by_file_id(file_id)
                             .filter_scene_boundaries_only()
                             .order_by_time()
                             .execute())
            
            # 转换为TimeAccurateResult
            results = []
            for ts_info in timestamp_infos:
                result = TimeAccurateResult(
                    file_id=ts_info.file_id,
                    start_time=ts_info.start_time,
                    end_time=ts_info.end_time,
                    duration=ts_info.duration,
                    score=ts_info.confidence,
                    confidence=ts_info.confidence,
                    modality=ts_info.modality,
                    vector_id=ts_info.vector_id or "",
                    segment_id=ts_info.segment_id,
                    time_accuracy=f"±{self.accuracy_requirement}s",
                    is_merged=False,
                    merged_count=1
                )
                results.append(result)
            
            logger.debug(f"场景边界查询完成: file_id={file_id}, 场景数={len(results)}")
            
            return results
            
        except Exception as e:
            logger.error(f"场景边界查询失败: {e}")
            return []
    
    def get_multimodal_synchronized_results(self, file_id: str, 
                                          target_timestamp: float,
                                          time_window: float = 5.0) -> Dict[str, List[TimeAccurateResult]]:
        """
        获取多模态同步的结果
        
        Args:
            file_id: 文件ID
            target_timestamp: 目标时间戳
            time_window: 时间窗口大小
            
        Returns:
            按模态分组的同步结果
        """
        try:
            start_time = max(0, target_timestamp - time_window / 2)
            end_time = target_timestamp + time_window / 2
            
            # 查询所有模态的时间戳信息
            all_timestamp_infos = self.timestamp_db.get_timestamp_infos_by_time_range(
                file_id, start_time, end_time
            )
            
            # 按模态分组
            results_by_modality = {}
            for ts_info in all_timestamp_infos:
                modality_key = ts_info.modality.value
                
                if modality_key not in results_by_modality:
                    results_by_modality[modality_key] = []
                
                result = TimeAccurateResult(
                    file_id=ts_info.file_id,
                    start_time=ts_info.start_time,
                    end_time=ts_info.end_time,
                    duration=ts_info.duration,
                    score=ts_info.confidence,
                    confidence=ts_info.confidence,
                    modality=ts_info.modality,
                    vector_id=ts_info.vector_id or "",
                    segment_id=ts_info.segment_id,
                    time_accuracy=f"±{self.accuracy_requirement}s",
                    is_merged=False,
                    merged_count=1
                )
                
                results_by_modality[modality_key].append(result)
            
            # 按时间排序每个模态的结果
            for modality_results in results_by_modality.values():
                modality_results.sort(key=lambda x: x.start_time)
            
            logger.debug(f"多模态同步查询完成: file_id={file_id}, "
                        f"timestamp={target_timestamp}, 模态数={len(results_by_modality)}")
            
            return results_by_modality
            
        except Exception as e:
            logger.error(f"多模态同步查询失败: {e}")
            return {}
    
    def get_precise_video_segment(self, file_id: str, target_timestamp: float, 
                                 context_window: float = 10.0) -> Optional[TimeAccurateResult]:
        """
        获取精确的视频段，支持帧级定位
        
        Args:
            file_id: 文件ID
            target_timestamp: 目标时间戳
            context_window: 上下文窗口大小
            
        Returns:
            最匹配的视频段结果
        """
        try:
            # 查询目标时间戳附近的视觉模态数据
            start_time = max(0, target_timestamp - context_window / 2)
            end_time = target_timestamp + context_window / 2
            
            visual_timestamps = self.timestamp_db.get_timestamp_infos_by_time_range(
                file_id, start_time, end_time, ModalityType.VISUAL
            )
            
            if not visual_timestamps:
                logger.warning(f"未找到视频段: file_id={file_id}, timestamp={target_timestamp}")
                return None
            
            # 找到最接近目标时间戳的段
            best_match = min(visual_timestamps, 
                           key=lambda ts: abs(ts.start_time + ts.duration/2 - target_timestamp))
            
            # 验证时间精度
            if not self._validate_time_accuracy(best_match):
                logger.warning(f"视频段时间精度不满足要求: duration={best_match.duration}s")
                return None
            
            result = TimeAccurateResult(
                file_id=best_match.file_id,
                start_time=best_match.start_time,
                end_time=best_match.end_time,
                duration=best_match.duration,
                score=best_match.confidence,
                confidence=best_match.confidence,
                modality=best_match.modality,
                vector_id=best_match.vector_id or "",
                segment_id=best_match.segment_id,
                time_accuracy=f"±{self.accuracy_requirement}s",
                is_merged=False,
                merged_count=1
            )
            
            logger.debug(f"精确视频段定位成功: segment_id={best_match.segment_id}, "
                        f"time_diff={abs(best_match.start_time + best_match.duration/2 - target_timestamp):.3f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"精确视频段定位失败: {e}")
            return None
    
    def get_continuous_video_timeline(self, file_id: str, 
                                    start_time: float = 0.0, 
                                    end_time: Optional[float] = None) -> List[TimeAccurateResult]:
        """
        获取连续的视频时间线
        
        Args:
            file_id: 文件ID
            start_time: 开始时间
            end_time: 结束时间(None表示到文件末尾)
            
        Returns:
            连续的时间线段列表
        """
        try:
            # 查询指定时间范围内的所有视觉段
            if end_time is None:
                # 获取文件的所有视觉时间戳
                all_visual_timestamps = self.timestamp_db.get_timestamp_infos_by_file_id(
                    file_id, ModalityType.VISUAL
                )
                if all_visual_timestamps:
                    end_time = max(ts.end_time for ts in all_visual_timestamps)
                else:
                    end_time = start_time + 3600  # 默认1小时
            
            visual_timestamps = self.timestamp_db.get_timestamp_infos_by_time_range(
                file_id, start_time, end_time, ModalityType.VISUAL
            )
            
            if not visual_timestamps:
                logger.warning(f"未找到视频时间线数据: file_id={file_id}")
                return []
            
            # 按时间排序
            visual_timestamps.sort(key=lambda x: x.start_time)
            
            # 转换为TimeAccurateResult并检测时间连续性
            timeline_results = []
            for ts_info in visual_timestamps:
                if self._validate_time_accuracy(ts_info):
                    result = TimeAccurateResult(
                        file_id=ts_info.file_id,
                        start_time=ts_info.start_time,
                        end_time=ts_info.end_time,
                        duration=ts_info.duration,
                        score=ts_info.confidence,
                        confidence=ts_info.confidence,
                        modality=ts_info.modality,
                        vector_id=ts_info.vector_id or "",
                        segment_id=ts_info.segment_id,
                        time_accuracy=f"±{self.accuracy_requirement}s",
                        is_merged=False,
                        merged_count=1
                    )
                    timeline_results.append(result)
            
            # 检测时间间隙
            gaps = []
            for i in range(len(timeline_results) - 1):
                current_end = timeline_results[i].end_time
                next_start = timeline_results[i + 1].start_time
                gap_duration = next_start - current_end
                
                if gap_duration > self.accuracy_requirement:
                    gaps.append({
                        'start_time': current_end,
                        'end_time': next_start,
                        'duration': gap_duration,
                        'after_segment': timeline_results[i].segment_id,
                        'before_segment': timeline_results[i + 1].segment_id
                    })
            
            if gaps:
                logger.info(f"检测到{len(gaps)}个时间间隙，总时长: "
                           f"{sum(gap['duration'] for gap in gaps):.2f}秒")
            
            logger.debug(f"视频时间线获取完成: file_id={file_id}, 段数={len(timeline_results)}, "
                        f"时间范围=[{start_time:.2f}, {end_time:.2f}]")
            
            return timeline_results
            
        except Exception as e:
            logger.error(f"获取视频时间线失败: {e}")
            return []
    
    def validate_retrieval_accuracy(self, results: List[TimeAccurateResult]) -> Dict[str, Any]:
        """
        验证检索结果的时间精度
        
        Args:
            results: 检索结果列表
            
        Returns:
            验证报告
        """
        try:
            validation_report = {
                'total_results': len(results),
                'accuracy_compliant': 0,
                'accuracy_violations': 0,
                'avg_duration': 0.0,
                'max_duration': 0.0,
                'min_duration': float('inf'),
                'violations': []
            }
            
            if not results:
                return validation_report
            
            durations = []
            for result in results:
                duration = result.duration
                durations.append(duration)
                
                # 检查是否满足±2秒精度要求
                if duration <= (self.accuracy_requirement * 2):
                    validation_report['accuracy_compliant'] += 1
                else:
                    validation_report['accuracy_violations'] += 1
                    validation_report['violations'].append({
                        'segment_id': result.segment_id,
                        'duration': duration,
                        'required_max': self.accuracy_requirement * 2
                    })
            
            # 计算统计信息
            validation_report['avg_duration'] = np.mean(durations)
            validation_report['max_duration'] = np.max(durations)
            validation_report['min_duration'] = np.min(durations)
            validation_report['accuracy_rate'] = validation_report['accuracy_compliant'] / len(results)
            
            logger.info(f"时间精度验证完成: 合规率={validation_report['accuracy_rate']:.2%}")
            
            return validation_report
            
        except Exception as e:
            logger.error(f"时间精度验证失败: {e}")
            return {'error': str(e)}


class VideoTimelineGenerator:
    """视频时间线生成器 - 为视频生成可视化时间线"""
    
    def __init__(self, retrieval_engine: TimeAccurateRetrievalEngine):
        self.retrieval_engine = retrieval_engine
        self.logger = logging.getLogger(__name__)
    
    def generate_timeline(self, file_id: str, resolution: int = 100) -> Dict[str, Any]:
        """
        生成视频时间线
        
        Args:
            file_id: 文件ID
            resolution: 时间线分辨率(时间点数量)
            
        Returns:
            时间线数据
        """
        try:
            # 获取文件的所有时间戳信息
            all_timestamps = self.retrieval_engine.timestamp_db.get_timestamp_infos_by_file_id(file_id)
            
            if not all_timestamps:
                return {'error': '未找到时间戳信息'}
            
            # 计算时间范围
            start_time = min(ts.start_time for ts in all_timestamps)
            end_time = max(ts.end_time for ts in all_timestamps)
            duration = end_time - start_time
            
            # 生成时间线点
            time_points = []
            time_step = duration / resolution
            
            for i in range(resolution):
                point_time = start_time + (i * time_step)
                
                # 查找该时间点的相关段
                relevant_segments = []
                for ts in all_timestamps:
                    if ts.start_time <= point_time <= ts.end_time:
                        relevant_segments.append(ts)
                
                # 计算该时间点的活动强度
                activity_score = sum(ts.confidence for ts in relevant_segments)
                
                time_point = {
                    'time': point_time,
                    'activity_score': activity_score,
                    'segment_count': len(relevant_segments),
                    'modalities': list(set(ts.modality.value for ts in relevant_segments))
                }
                
                time_points.append(time_point)
            
            # 获取场景边界
            scene_boundaries = self.retrieval_engine.get_scene_boundaries(file_id)
            
            timeline_data = {
                'file_id': file_id,
                'start_time': start_time,
                'end_time': end_time,
                'duration': duration,
                'resolution': resolution,
                'time_points': time_points,
                'scene_boundaries': [
                    {
                        'time': sb.start_time,
                        'confidence': sb.confidence,
                        'segment_id': sb.segment_id
                    }
                    for sb in scene_boundaries
                ],
                'statistics': {
                    'total_segments': len(all_timestamps),
                    'visual_segments': len([ts for ts in all_timestamps if ts.modality == ModalityType.VISUAL]),
                    'audio_segments': len([ts for ts in all_timestamps if ts.modality != ModalityType.VISUAL]),
                    'scene_count': len(scene_boundaries),
                    'avg_confidence': np.mean([ts.confidence for ts in all_timestamps])
                }
            }
            
            logger.info(f"时间线生成完成: file_id={file_id}, 分辨率={resolution}, 场景数={len(scene_boundaries)}")
            
            return timeline_data
            
        except Exception as e:
            logger.error(f"时间线生成失败: {e}")
            return {'error': str(e)}