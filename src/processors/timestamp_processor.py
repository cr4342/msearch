"""
时间戳处理器 - 处理视频和音频的时间戳精确计算和同步验证
实现±2秒精度的时间戳处理，支持多模态时间同步
"""
import time
import numpy as np
from typing import Dict, Any, List, Tuple, Optional, NamedTuple
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ModalityType(Enum):
    """模态类型枚举"""
    VISUAL = "visual"
    AUDIO_MUSIC = "audio_music"
    AUDIO_SPEECH = "audio_speech"


@dataclass
class TimestampInfo:
    """时间戳信息数据类"""
    file_id: str
    segment_id: str
    modality: ModalityType
    start_time: float
    end_time: float
    duration: float
    frame_index: Optional[int] = None
    vector_id: Optional[str] = None
    confidence: float = 1.0
    scene_boundary: bool = False


@dataclass
class TimeStampedResult:
    """带时间戳的检索结果"""
    file_id: str
    start_time: float
    end_time: float
    score: float
    vector_id: str
    modality: ModalityType
    timestamp_info: TimestampInfo


class MergedTimeSegment:
    """合并的时间段"""
    
    def __init__(self, initial_result: TimeStampedResult):
        self.file_id = initial_result.file_id
        self.start_time = initial_result.start_time
        self.end_time = initial_result.end_time
        self.results = [initial_result]
        self.max_score = initial_result.score
        self.modalities = {initial_result.modality}
    
    def merge(self, result: TimeStampedResult):
        """合并另一个结果到当前时间段"""
        self.start_time = min(self.start_time, result.start_time)
        self.end_time = max(self.end_time, result.end_time)
        self.results.append(result)
        self.max_score = max(self.max_score, result.score)
        self.modalities.add(result.modality)


class TimestampProcessor:
    """时间戳处理器 - 实现±2秒精度的时间戳处理"""
    
    def __init__(self, config=None):
        """初始化时间戳处理器"""
        if config is not None:
            # 从配置中获取参数
            timestamp_config = config.get('processing', {}).get('video', {}).get('timestamp_processing', {})
            self.accuracy_requirement = timestamp_config.get('accuracy_requirement', 2.0)
            self.overlap_buffer = timestamp_config.get('overlap_buffer', 1.0)
            
            sync_tolerance_config = timestamp_config.get('sync_tolerance', {})
            self.sync_tolerance = {
                ModalityType.VISUAL: sync_tolerance_config.get('visual', 0.033),      # 帧级精度(30fps)
                ModalityType.AUDIO_MUSIC: sync_tolerance_config.get('audio_music', 0.1),   # 音频精度
                ModalityType.AUDIO_SPEECH: sync_tolerance_config.get('audio_speech', 0.2)   # 语音精度
            }
            
            self.enable_timestamp_validation = timestamp_config.get('enable_timestamp_validation', True)
            self.enable_drift_correction = timestamp_config.get('enable_drift_correction', True)
        else:
            # 默认值
            self.accuracy_requirement = 2.0  # ±2秒精度要求
            self.overlap_buffer = 1.0  # 1秒重叠缓冲
            self.sync_tolerance = {
                ModalityType.VISUAL: 0.033,      # 帧级精度(30fps)
                ModalityType.AUDIO_MUSIC: 0.1,   # 音频精度
                ModalityType.AUDIO_SPEECH: 0.2   # 语音精度
            }
            self.enable_timestamp_validation = True
            self.enable_drift_correction = True
        
        logger.info(f"时间戳处理器初始化完成 - 精度要求: ±{self.accuracy_requirement}秒")
    
    def calculate_frame_timestamp(self, frame_index: int, fps: float, time_base: float = 0.0) -> float:
        """
        计算帧级精确时间戳
        
        Args:
            frame_index: 帧索引
            fps: 帧率
            time_base: 时间基准偏移
            
        Returns:
            精确时间戳(秒)
        """
        if fps <= 0:
            raise ValueError(f"无效的帧率: {fps}")
        
        timestamp = (frame_index / fps) + time_base
        
        # 验证时间戳精度
        frame_duration = 1.0 / fps
        if self.enable_timestamp_validation:
            expected_precision = frame_duration
            if expected_precision > self.sync_tolerance[ModalityType.VISUAL]:
                logger.warning(f"帧级精度可能不足: {expected_precision:.4f}s > {self.sync_tolerance[ModalityType.VISUAL]:.4f}s")
        
        return timestamp
    
    def validate_timestamp_accuracy(self, duration: float) -> bool:
        """
        验证时间戳精度是否满足±2秒要求
        
        Args:
            duration: 持续时长
            
        Returns:
            是否满足精度要求
        """
        is_valid = duration <= (self.accuracy_requirement * 2)
        
        if not is_valid:
            logger.warning(f"时间戳精度不满足要求: duration={duration}s > {self.accuracy_requirement*2}s")
        else:
            logger.debug(f"时间戳精度验证通过: duration={duration}s")
        
        return is_valid
    
    def create_scene_aware_segments(self, video_path: str, scenes: List[Dict[str, Any]], 
                                  fps: float = 30.0) -> List[TimestampInfo]:
        """
        创建场景感知的时间切片
        
        Args:
            video_path: 视频路径
            scenes: 场景列表
            fps: 帧率
            
        Returns:
            场景感知的时间戳信息列表
        """
        segments = []
        
        for i, scene in enumerate(scenes):
            scene_start = scene.get('start_time', 0.0)
            scene_end = scene.get('end_time', scene_start + 60.0)  # 默认60秒
            scene_duration = scene_end - scene_start
            
            # 确保每个场景完整性
            if scene_duration > 120:  # 长场景需要切分
                # 在场景内部进行智能切分，避免破坏内容连续性
                sub_segments = self._split_long_scene(scene, max_duration=60.0, fps=fps)
                segments.extend(sub_segments)
            else:
                # 创建场景时间戳信息
                segment_info = TimestampInfo(
                    file_id=video_path,
                    segment_id=f"scene_{i}",
                    modality=ModalityType.VISUAL,
                    start_time=scene_start,
                    end_time=scene_end,
                    duration=scene_duration,
                    frame_index=int(scene_start * fps),
                    confidence=scene.get('confidence', 1.0),
                    scene_boundary=True
                )
                segments.append(segment_info)
        
        return segments
    
    def _split_long_scene(self, scene: Dict[str, Any], max_duration: float = 60.0, 
                         fps: float = 30.0) -> List[TimestampInfo]:
        """
        分割长场景，保持内容连续性
        
        Args:
            scene: 场景信息
            max_duration: 最大持续时长
            fps: 帧率
            
        Returns:
            分割后的时间戳信息列表
        """
        segments = []
        scene_start = scene.get('start_time', 0.0)
        scene_end = scene.get('end_time', scene_start + 60.0)
        scene_duration = scene_end - scene_start
        
        # 计算分割点
        num_segments = int(np.ceil(scene_duration / max_duration))
        segment_duration = scene_duration / num_segments
        
        for i in range(num_segments):
            segment_start = scene_start + (i * segment_duration)
            segment_end = min(segment_start + segment_duration, scene_end)
            
            # 添加重叠缓冲区(除了最后一个段)
            if i < num_segments - 1:
                segment_end += self.overlap_buffer
            
            segment_info = TimestampInfo(
                file_id=scene.get('file_id', ''),
                segment_id=f"scene_{scene.get('scene_id', 0)}_part_{i}",
                modality=ModalityType.VISUAL,
                start_time=segment_start,
                end_time=segment_end,
                duration=segment_end - segment_start,
                frame_index=int(segment_start * fps),
                confidence=scene.get('confidence', 1.0),
                scene_boundary=(i == 0)  # 只有第一个段标记为场景边界
            )
            segments.append(segment_info)
        
        return segments
    
    def correct_timestamp_drift(self, timestamps: List[TimestampInfo]) -> List[TimestampInfo]:
        """
        校正时间戳漂移，确保多模态同步
        
        Args:
            timestamps: 时间戳信息列表
            
        Returns:
            校正后的时间戳信息列表
        """
        if not self.enable_drift_correction:
            return timestamps
        
        # 使用视频时间轴作为基准
        video_baseline = self._extract_video_baseline(timestamps)
        if not video_baseline:
            logger.warning("未找到视频基准时间轴，跳过漂移校正")
            return timestamps
        
        corrected_timestamps = []
        for ts in timestamps:
            if ts.modality != ModalityType.VISUAL:
                # 校正音频时间戳到视频基准
                corrected_ts = self._align_to_video_baseline(ts, video_baseline)
                corrected_timestamps.append(corrected_ts)
            else:
                corrected_timestamps.append(ts)
        
        logger.debug(f"时间戳漂移校正完成: 处理{len(timestamps)}个时间戳")
        return corrected_timestamps
    
    def _extract_video_baseline(self, timestamps: List[TimestampInfo]) -> Optional[List[TimestampInfo]]:
        """
        提取视频时间轴作为基准
        
        Args:
            timestamps: 时间戳信息列表
            
        Returns:
            视频基准时间轴
        """
        video_timestamps = [ts for ts in timestamps if ts.modality == ModalityType.VISUAL]
        
        if not video_timestamps:
            return None
        
        # 按时间排序
        video_timestamps.sort(key=lambda x: x.start_time)
        return video_timestamps
    
    def _align_to_video_baseline(self, audio_ts: TimestampInfo, 
                                video_baseline: List[TimestampInfo]) -> TimestampInfo:
        """
        将音频时间戳对齐到视频基准
        
        Args:
            audio_ts: 音频时间戳信息
            video_baseline: 视频基准时间轴
            
        Returns:
            对齐后的音频时间戳信息
        """
        # 找到最接近的视频时间戳
        closest_video_ts = min(video_baseline, 
                              key=lambda x: abs(x.start_time - audio_ts.start_time))
        
        # 计算时间偏移
        time_offset = closest_video_ts.start_time - audio_ts.start_time
        
        # 应用校正
        corrected_ts = TimestampInfo(
            file_id=audio_ts.file_id,
            segment_id=audio_ts.segment_id,
            modality=audio_ts.modality,
            start_time=audio_ts.start_time + time_offset,
            end_time=audio_ts.end_time + time_offset,
            duration=audio_ts.duration,
            frame_index=audio_ts.frame_index,
            vector_id=audio_ts.vector_id,
            confidence=audio_ts.confidence,
            scene_boundary=audio_ts.scene_boundary
        )
        
        return corrected_ts
    
    
    

    
    def validate_multimodal_sync(self, visual_timestamp: float, audio_timestamp: float, 
                                modality: ModalityType) -> bool:
        """
        验证多模态时间同步精度
        
        Args:
            visual_timestamp: 视觉时间戳
            audio_timestamp: 音频时间戳
            modality: 音频模态类型
            
        Returns:
            是否满足同步精度要求
        """
        tolerance = self.sync_tolerance.get(modality, 0.2)
        time_diff = abs(visual_timestamp - audio_timestamp)
        
        is_synced = time_diff <= tolerance
        
        if not is_synced:
            logger.warning(f"多模态时间同步精度不足: 差异={time_diff:.4f}s, 容差={tolerance:.4f}s")
        
        return is_synced
    
    def merge_overlapping_segments(self, segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        合并重叠的时间段，提高检索连续性
        
        Args:
            segments: 时间段列表
            
        Returns:
            合并后的时间段列表
        """
        if not segments:
            return []
        
        # 按文件和时间排序
        sorted_segments = sorted(segments, key=lambda x: (x.get('file_id', ''), x['start_time']))
        
        merged_segments = []
        current_segment = None
        
        for segment in sorted_segments:
            if current_segment is None:
                current_segment = segment.copy()
            elif self._is_time_continuous(current_segment, segment):
                # 时间连续，合并到当前段
                current_segment = self._merge_segments(current_segment, segment)
            else:
                # 时间不连续，开始新段
                merged_segments.append(current_segment)
                current_segment = segment.copy()
        
        if current_segment:
            merged_segments.append(current_segment)
        
        logger.debug(f"时间段合并完成: 原始{len(segments)}段 -> 合并后{len(merged_segments)}段")
        return merged_segments
    
    def _is_time_continuous(self, segment1: Dict[str, Any], segment2: Dict[str, Any]) -> bool:
        """
        判断时间段是否连续(考虑±2秒精度要求)
        
        Args:
            segment1: 第一个时间段
            segment2: 第二个时间段
            
        Returns:
            是否连续
        """
        time_gap = segment2['start_time'] - segment1['end_time']
        is_continuous = abs(time_gap) <= self.accuracy_requirement
        return is_continuous
    
    def _merge_segments(self, segment1: Dict[str, Any], segment2: Dict[str, Any]) -> Dict[str, Any]:
        """
        合并两个时间段
        
        Args:
            segment1: 第一个时间段
            segment2: 第二个时间段
            
        Returns:
            合并后的时间段
        """
        merged = segment1.copy()
        merged['end_time'] = max(segment1['end_time'], segment2['end_time'])
        merged['duration'] = merged['end_time'] - merged['start_time']
        
        # 合并其他字段(如果存在)
        if 'confidence' in segment2:
            merged['confidence'] = max(merged.get('confidence', 0), segment2['confidence'])
        
        return merged


        return merged
    
    def batch_query_timestamps(self, vector_ids: List[str], 
                             timestamp_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        批量查询时间戳
        
        Args:
            vector_ids: 向量ID列表
            timestamp_data: 时间戳数据列表
            
        Returns:
            匹配的时间戳结果列表
        """
        results = []
        for vector_id in vector_ids:
            result = self.query_timestamp(vector_id, timestamp_data)
            if result:
                results.append(result)
        return results
    
    def query_timestamp(self, vector_id: str, 
                       timestamp_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        查询特定向量ID的时间戳
        
        Args:
            vector_id: 向量ID
            timestamp_data: 时间戳数据列表
            
        Returns:
            匹配的时间戳信息
        """
        for data in timestamp_data:
            if data.get('vector_id') == vector_id:
                return data.copy()
        return None
    
    def batch_process_timestamps(self, timestamps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        批量处理时间戳
        
        Args:
            timestamps: 时间戳列表
            
        Returns:
            处理后的时间戳列表
        """
        processed = []
        for ts in timestamps:
            # 验证时间戳精度
            duration = ts.get('duration', ts['end_time'] - ts['start_time'])
            if self.validate_timestamp_accuracy(duration):
                processed.append(ts)
        return processed
    
    def process_timestamps(self, timestamps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        处理时间戳列表
        
        Args:
            timestamps: 时间戳列表
            
        Returns:
            处理后的时间戳列表
        """
        return self.batch_process_timestamps(timestamps)
    
    def synchronize_multimodal_timestamps(self, video_timestamps: List[TimestampInfo], 
                                        audio_timestamps: List[TimestampInfo]) -> Tuple[List[TimestampInfo], List[TimestampInfo]]:
        """
        同步多模态时间戳，确保视频和音频时间对齐
        
        Args:
            video_timestamps: 视频时间戳列表
            audio_timestamps: 音频时间戳列表
            
        Returns:
            同步后的(视频时间戳, 音频时间戳)元组
        """
        try:
            if not self.enable_drift_correction:
                return video_timestamps, audio_timestamps
            
            # 使用视频时间轴作为基准
            if not video_timestamps:
                logger.warning("没有视频时间戳作为基准，跳过多模态同步")
                return video_timestamps, audio_timestamps
            
            synchronized_audio = []
            
            for audio_ts in audio_timestamps:
                # 找到最接近的视频时间戳
                closest_video_ts = min(video_timestamps, 
                                     key=lambda v_ts: abs(v_ts.start_time - audio_ts.start_time))
                
                # 计算时间偏移
                time_offset = closest_video_ts.start_time - audio_ts.start_time
                
                # 检查是否需要校正
                if abs(time_offset) > self.sync_tolerance.get(audio_ts.modality, 0.2):
                    # 应用时间校正
                    corrected_audio_ts = TimestampInfo(
                        file_id=audio_ts.file_id,
                        segment_id=f"{audio_ts.segment_id}_synced",
                        modality=audio_ts.modality,
                        start_time=audio_ts.start_time + time_offset,
                        end_time=audio_ts.end_time + time_offset,
                        duration=audio_ts.duration,
                        frame_index=audio_ts.frame_index,
                        vector_id=audio_ts.vector_id,
                        confidence=audio_ts.confidence,
                        scene_boundary=audio_ts.scene_boundary
                    )
                    synchronized_audio.append(corrected_audio_ts)
                    
                    logger.debug(f"音频时间戳已校正: segment_id={audio_ts.segment_id}, "
                               f"offset={time_offset:.3f}s")
                else:
                    # 不需要校正
                    synchronized_audio.append(audio_ts)
            
            logger.info(f"多模态时间戳同步完成: 视频{len(video_timestamps)}个, "
                       f"音频{len(synchronized_audio)}个")
            
            return video_timestamps, synchronized_audio
            
        except Exception as e:
            logger.error(f"多模态时间戳同步失败: {e}")
            return video_timestamps, audio_timestamps
    
    def create_overlapping_time_windows(self, timestamps: List[TimestampInfo]) -> List[TimestampInfo]:
        """
        创建重叠时间窗口，确保±2秒精度
        
        Args:
            timestamps: 原始时间戳列表
            
        Returns:
            带重叠窗口的时间戳列表
        """
        overlapping_timestamps = []
        
        for ts in timestamps:
            # 创建重叠时间窗口
            window_start = max(0, ts.start_time - self.overlap_buffer)
            window_end = ts.end_time + self.overlap_buffer
            window_duration = window_end - window_start
            
            # 验证窗口是否满足精度要求
            if self.validate_timestamp_accuracy(window_duration):
                overlapping_ts = TimestampInfo(
                    file_id=ts.file_id,
                    segment_id=f"{ts.segment_id}_overlap",
                    modality=ts.modality,
                    start_time=window_start,
                    end_time=window_end,
                    duration=window_duration,
                    frame_index=ts.frame_index,
                    vector_id=ts.vector_id,
                    confidence=ts.confidence,
                    scene_boundary=ts.scene_boundary
                )
                overlapping_timestamps.append(overlapping_ts)
            else:
                # 如果不满足精度要求，使用原始时间戳
                overlapping_timestamps.append(ts)
        
        return overlapping_timestamps


# 示例使用
if __name__ == "__main__":
    # 创建时间戳处理器实例
    processor = TimestampProcessor()
    
    # 计算帧时间戳
    timestamp = processor.calculate_frame_timestamp(60, 30.0)
    print(f"帧时间戳: {timestamp:.3f}s")
    
    # 验证时间戳精度
    is_valid = processor.validate_timestamp_accuracy(3.5)
    print(f"时间戳精度验证: {'通过' if is_valid else '不通过'}")
    
    # 验证多模态同步
    is_synced = processor.validate_multimodal_sync(10.0, 10.05, ModalityType.AUDIO_MUSIC)
    print(f"多模态同步验证: {'同步' if is_synced else '不同步'}")
    
    # 合并时间段示例
    segments = [
        {'file_id': 'file1', 'start_time': 10.0, 'end_time': 15.0},
        {'file_id': 'file1', 'start_time': 14.0, 'end_time': 20.0},
        {'file_id': 'file1', 'start_time': 25.0, 'end_time': 30.0}
    ]
    
    merged = processor.merge_overlapping_segments(segments)
    print(f"合并时间段: {merged}")