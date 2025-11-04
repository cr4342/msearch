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
            
            # 添加重叠缓冲区（除了最后一个段）
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
    
    def correct_timestamp_drift(self, timestamps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        纠正时间戳漂移
        
        Args:
            timestamps: 带漂移的时间戳列表
            
        Returns:
            纠正后的时间戳列表
        """
        if not timestamps:
            return []
        
        # 找到视觉时间戳作为基准
        visual_timestamps = [ts for ts in timestamps if ts['modality'] == 'visual']
        if not visual_timestamps:
            # 如果没有视觉时间戳，使用第一个时间戳作为基准
            base_timestamp = timestamps[0]
            base_time = base_timestamp['start_time']
        else:
            base_timestamp = visual_timestamps[0]
            base_time = base_timestamp['start_time']
        
        corrected_timestamps = []
        for ts in timestamps:
            corrected_ts = ts.copy()
            
            # 根据模态类型应用不同的漂移校正
            if ts['modality'] == 'audio_music':
                # 音频音乐漂移校正
                corrected_ts['start_time'] = base_time
                corrected_ts['end_time'] = base_time + (ts['end_time'] - ts['start_time'])
            elif ts['modality'] == 'audio_speech':
                # 语音漂移校正
                corrected_ts['start_time'] = base_time
                corrected_ts['end_time'] = base_time + (ts['end_time'] - ts['start_time'])
            else:
                # 视觉或其它模态，保持不变
                corrected_ts['start_time'] = base_time
                corrected_ts['end_time'] = base_time + (ts['end_time'] - ts['start_time'])
            
            corrected_timestamps.append(corrected_ts)
        
        return corrected_timestamps
    
    def calculate_frame_timestamp(self, frame_index: int, fps: float, time_base: float = 0.0) -> float:
        """
        计算帧级精确时间戳
        
        Args:
            frame_index: 帧索引
            fps: 帧率
            time_base: 时间基准偏移
            
        Returns:
            时间戳(秒)
        """
        if fps <= 0:
            raise ValueError(f"无效的帧率: {fps}")
        
        timestamp = (frame_index / fps) + time_base
        logger.debug(f"计算帧时间戳: frame_index={frame_index}, fps={fps}, timestamp={timestamp:.3f}s")
        
        # 精度验证
        if abs(timestamp - round(timestamp, 3)) > 0.001:
            logger.warning(f"时间戳精度可能不足: {timestamp}")
        
        return timestamp
    

    
    def validate_multimodal_sync(self, visual_timestamp: float, audio_timestamp: float, 
                                modality: str) -> bool:
        """
        验证多模态时间同步精度
        
        Args:
            visual_timestamp: 视觉时间戳
            audio_timestamp: 音频时间戳
            modality: 模态类型
            
        Returns:
            是否同步
        """
        tolerance = self.sync_tolerance.get(modality, 0.2)
        time_diff = abs(visual_timestamp - audio_timestamp)
        is_synced = time_diff <= tolerance
        
        if not is_synced:
            logger.warning(f"多模态时间不同步: 视觉={visual_timestamp:.3f}s, 音频={audio_timestamp:.3f}s, "
                          f"差异={time_diff:.3f}s, 容差={tolerance:.3f}s")
        
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
        
        # 合并其他字段（如果存在）
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
    is_synced = processor.validate_multimodal_sync(10.0, 10.05, 'audio_music')
    print(f"多模态同步验证: {'同步' if is_synced else '不同步'}")
    
    # 合并时间段示例
    segments = [
        {'file_id': 'file1', 'start_time': 10.0, 'end_time': 15.0},
        {'file_id': 'file1', 'start_time': 14.0, 'end_time': 20.0},
        {'file_id': 'file1', 'start_time': 25.0, 'end_time': 30.0}
    ]
    
    merged = processor.merge_overlapping_segments(segments)
    print(f"合并时间段: {merged}") 
   
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
    
    def process_video_stream_timestamps(self, video_path: str, fps: float, 
                                      total_frames: int, scenes: List[Dict[str, Any]] = None) -> List[TimestampInfo]:
        """
        处理视频流的时间戳，支持场景感知和帧级精度
        
        Args:
            video_path: 视频文件路径
            fps: 帧率
            total_frames: 总帧数
            scenes: 场景信息列表（可选）
            
        Returns:
            视频流时间戳信息列表
        """
        try:
            timestamps = []
            
            if scenes:
                # 基于场景的时间戳处理
                for i, scene in enumerate(scenes):
                    scene_start_time = scene.get('start_time', 0.0)
                    scene_end_time = scene.get('end_time', scene_start_time + 60.0)
                    scene_duration = scene_end_time - scene_start_time
                    
                    # 计算场景的起始和结束帧
                    start_frame = int(scene_start_time * fps)
                    end_frame = int(scene_end_time * fps)
                    
                    # 验证场景时间精度
                    if self.validate_timestamp_accuracy(scene_duration):
                        timestamp_info = TimestampInfo(
                            file_id=video_path,
                            segment_id=f"video_scene_{i}",
                            modality=ModalityType.VISUAL,
                            start_time=scene_start_time,
                            end_time=scene_end_time,
                            duration=scene_duration,
                            frame_index=start_frame,
                            confidence=scene.get('confidence', 1.0),
                            scene_boundary=True
                        )
                        timestamps.append(timestamp_info)
                        
                        # 如果场景太长，进行内部分割
                        if scene_duration > self.accuracy_requirement * 2:
                            sub_timestamps = self._split_long_scene_timestamps(
                                video_path, scene_start_time, scene_end_time, fps, i
                            )
                            timestamps.extend(sub_timestamps)
                    else:
                        logger.warning(f"场景时间精度不满足要求: scene_{i}, duration={scene_duration}s")
            else:
                # 基于固定间隔的时间戳处理
                frame_interval = max(1, int(fps * self.accuracy_requirement))  # 每2秒一个时间戳
                
                for frame_idx in range(0, total_frames, frame_interval):
                    timestamp = self.calculate_frame_timestamp(frame_idx, fps)
                    end_timestamp = min(timestamp + self.accuracy_requirement, total_frames / fps)
                    duration = end_timestamp - timestamp
                    
                    if self.validate_timestamp_accuracy(duration):
                        timestamp_info = TimestampInfo(
                            file_id=video_path,
                            segment_id=f"video_frame_{frame_idx}",
                            modality=ModalityType.VISUAL,
                            start_time=timestamp,
                            end_time=end_timestamp,
                            duration=duration,
                            frame_index=frame_idx,
                            confidence=1.0,
                            scene_boundary=False
                        )
                        timestamps.append(timestamp_info)
            
            logger.info(f"视频流时间戳处理完成: {len(timestamps)}个时间戳, fps={fps}")
            return timestamps
            
        except Exception as e:
            logger.error(f"视频流时间戳处理失败: {e}")
            return []
    
    def _split_long_scene_timestamps(self, video_path: str, start_time: float, 
                                   end_time: float, fps: float, scene_id: int) -> List[TimestampInfo]:
        """
        分割长场景的时间戳
        
        Args:
            video_path: 视频路径
            start_time: 场景开始时间
            end_time: 场景结束时间
            fps: 帧率
            scene_id: 场景ID
            
        Returns:
            分割后的时间戳列表
        """
        timestamps = []
        scene_duration = end_time - start_time
        
        # 计算分割数量
        num_segments = int(np.ceil(scene_duration / (self.accuracy_requirement * 2)))
        segment_duration = scene_duration / num_segments
        
        for i in range(num_segments):
            segment_start = start_time + (i * segment_duration)
            segment_end = min(segment_start + segment_duration, end_time)
            
            # 添加重叠缓冲区（除了最后一个段）
            if i < num_segments - 1:
                segment_end += self.overlap_buffer
            
            frame_index = int(segment_start * fps)
            
            timestamp_info = TimestampInfo(
                file_id=video_path,
                segment_id=f"video_scene_{scene_id}_part_{i}",
                modality=ModalityType.VISUAL,
                start_time=segment_start,
                end_time=segment_end,
                duration=segment_end - segment_start,
                frame_index=frame_index,
                confidence=1.0,
                scene_boundary=(i == 0)  # 只有第一个段标记为场景边界
            )
            timestamps.append(timestamp_info)
        
        return timestamps
    
    def process_audio_stream_timestamps(self, audio_path: str, audio_segments: List[Dict[str, Any]], 
                                      sample_rate: int = 16000) -> List[TimestampInfo]:
        """
        处理音频流的时间戳，支持音乐和语音分类
        
        Args:
            audio_path: 音频文件路径
            audio_segments: 音频分类段信息
            sample_rate: 采样率
            
        Returns:
            音频流时间戳信息列表
        """
        try:
            timestamps = []
            
            for i, segment in enumerate(audio_segments):
                segment_type = segment.get('type', 'unknown')  # music, speech, noise
                start_time = segment.get('start_time', 0.0)
                end_time = segment.get('end_time', start_time + 10.0)
                duration = end_time - start_time
                confidence = segment.get('confidence', 1.0)
                
                # 根据音频类型确定模态
                if segment_type == 'music':
                    modality = ModalityType.AUDIO_MUSIC
                elif segment_type == 'speech':
                    modality = ModalityType.AUDIO_SPEECH
                else:
                    continue  # 跳过噪音段
                
                # 验证时间精度
                if self.validate_timestamp_accuracy(duration):
                    timestamp_info = TimestampInfo(
                        file_id=audio_path,
                        segment_id=f"audio_{segment_type}_{i}",
                        modality=modality,
                        start_time=start_time,
                        end_time=end_time,
                        duration=duration,
                        frame_index=None,  # 音频没有帧索引
                        confidence=confidence,
                        scene_boundary=False
                    )
                    timestamps.append(timestamp_info)
                    
                    # 如果音频段太长，进行分割
                    if duration > self.accuracy_requirement * 2:
                        sub_timestamps = self._split_long_audio_timestamps(
                            audio_path, start_time, end_time, modality, segment_type, i
                        )
                        timestamps.extend(sub_timestamps)
                else:
                    logger.warning(f"音频段时间精度不满足要求: {segment_type}_{i}, duration={duration}s")
            
            logger.info(f"音频流时间戳处理完成: {len(timestamps)}个时间戳")
            return timestamps
            
        except Exception as e:
            logger.error(f"音频流时间戳处理失败: {e}")
            return []
    
    def _split_long_audio_timestamps(self, audio_path: str, start_time: float, 
                                   end_time: float, modality: ModalityType, 
                                   segment_type: str, segment_id: int) -> List[TimestampInfo]:
        """
        分割长音频段的时间戳
        
        Args:
            audio_path: 音频路径
            start_time: 段开始时间
            end_time: 段结束时间
            modality: 模态类型
            segment_type: 段类型
            segment_id: 段ID
            
        Returns:
            分割后的时间戳列表
        """
        timestamps = []
        segment_duration = end_time - start_time
        
        # 根据音频类型确定分割策略
        if modality == ModalityType.AUDIO_MUSIC:
            max_duration = 30.0  # 音乐段最大30秒
        else:  # AUDIO_SPEECH
            max_duration = 10.0  # 语音段最大10秒
        
        # 计算分割数量
        num_segments = int(np.ceil(segment_duration / max_duration))
        sub_duration = segment_duration / num_segments
        
        for i in range(num_segments):
            sub_start = start_time + (i * sub_duration)
            sub_end = min(sub_start + sub_duration, end_time)
            
            timestamp_info = TimestampInfo(
                file_id=audio_path,
                segment_id=f"audio_{segment_type}_{segment_id}_part_{i}",
                modality=modality,
                start_time=sub_start,
                end_time=sub_end,
                duration=sub_end - sub_start,
                frame_index=None,
                confidence=1.0,
                scene_boundary=False
            )
            timestamps.append(timestamp_info)
        
        return timestamps
    



class TimeAccurateRetrieval:
    """精确时间检索器 - 实现±2秒精度的时间戳检索"""
    
    def __init__(self, accuracy_requirement: float = 2.0):
        self.accuracy_requirement = accuracy_requirement  # ±2秒
        self.overlap_buffer = 1.0  # 1秒重叠缓冲
        self.logger = logging.getLogger(__name__)
    
    async def retrieve_with_timestamp(self, query_vector: np.ndarray, 
                                    target_modality: ModalityType,
                                    top_k: int = 50) -> List[TimeStampedResult]:
        """
        带时间戳的精确检索
        
        Args:
            query_vector: 查询向量
            target_modality: 目标模态
            top_k: 返回结果数量
            
        Returns:
            带时间戳的检索结果列表
        """
        try:
            # 1. 向量相似度检索
            similar_vectors = await self._vector_search(query_vector, top_k * 2)
            
            # 2. 获取时间戳信息
            timestamped_results = []
            for vector_result in similar_vectors:
                timestamp_info = await self._get_timestamp_info(
                    vector_result['vector_id'], target_modality
                )
                
                if timestamp_info and self._validate_time_accuracy(timestamp_info):
                    result = TimeStampedResult(
                        file_id=timestamp_info.file_id,
                        start_time=timestamp_info.start_time,
                        end_time=timestamp_info.end_time,
                        score=vector_result['score'],
                        vector_id=vector_result['vector_id'],
                        modality=target_modality,
                        timestamp_info=timestamp_info
                    )
                    timestamped_results.append(result)
            
            # 3. 时间段合并与去重
            merged_results = self._merge_overlapping_segments(timestamped_results)
            
            # 4. 按相似度和时间连续性排序
            return self._sort_by_relevance_and_continuity(merged_results)[:top_k]
            
        except Exception as e:
            self.logger.error(f"时间戳检索失败: {e}")
            return []
    
    def _validate_time_accuracy(self, timestamp_info: TimestampInfo) -> bool:
        """验证时间戳精度是否满足±2秒要求"""
        return timestamp_info.duration <= (self.accuracy_requirement * 2)
    
    def _merge_overlapping_segments(self, results: List[TimeStampedResult]) -> List[MergedTimeSegment]:
        """合并重叠的时间段，提高检索连续性"""
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
        time_gap = result.start_time - segment.end_time
        return abs(time_gap) <= self.accuracy_requirement
    
    def _sort_by_relevance_and_continuity(self, segments: List[MergedTimeSegment]) -> List[TimeStampedResult]:
        """按相似度和时间连续性排序"""
        # 计算综合得分：相似度 + 连续性奖励
        for segment in segments:
            continuity_bonus = len(segment.results) * 0.1  # 连续性奖励
            segment.final_score = segment.max_score + continuity_bonus
        
        # 按综合得分排序
        segments.sort(key=lambda x: x.final_score, reverse=True)
        
        # 转换回TimeStampedResult列表
        final_results = []
        for segment in segments:
            # 使用得分最高的结果作为代表
            best_result = max(segment.results, key=lambda x: x.score)
            final_results.append(best_result)
        
        return final_results
    
    async def _vector_search(self, query_vector: np.ndarray, top_k: int) -> List[Dict[str, Any]]:
        """向量相似度搜索 - 占位符实现"""
        # TODO: 实现实际的向量搜索逻辑
        return []
    
    async def _get_timestamp_info(self, vector_id: str, modality: ModalityType) -> Optional[TimestampInfo]:
        """获取向量的时间戳信息 - 占位符实现"""
        # TODO: 实现从数据库获取时间戳信息的逻辑
        return None


class MultiModalTimeSyncValidator:
    """多模态时间同步验证器"""
    
    def __init__(self):
        self.sync_tolerance = {
            ModalityType.VISUAL: 0.033,      # 帧级精度(30fps)
            ModalityType.AUDIO_MUSIC: 0.1,   # 音频精度
            ModalityType.AUDIO_SPEECH: 0.2   # 语音精度
        }
        self.logger = logging.getLogger(__name__)
    
    def validate_multimodal_sync(self, visual_timestamp: float, audio_timestamp: float, 
                                modality: ModalityType) -> bool:
        """验证多模态时间同步精度"""
        tolerance = self.sync_tolerance.get(modality, 0.2)
        time_diff = abs(visual_timestamp - audio_timestamp)
        return time_diff <= tolerance
    
    def correct_timestamp_drift(self, timestamps: List[TimestampInfo]) -> List[TimestampInfo]:
        """校正时间戳漂移，确保多模态同步"""
        # 使用视频时间轴作为基准
        video_baseline = self._extract_video_baseline(timestamps)
        
        corrected_timestamps = []
        for ts in timestamps:
            if ts.modality != ModalityType.VISUAL and video_baseline:
                # 校正音频时间戳到视频基准
                corrected_time = self._align_to_video_baseline(ts, video_baseline)
                corrected_timestamps.append(corrected_time)
            else:
                corrected_timestamps.append(ts)
        
        return corrected_timestamps
    
    def _extract_video_baseline(self, timestamps: List[TimestampInfo]) -> List[TimestampInfo]:
        """提取视频时间轴作为基准"""
        return [ts for ts in timestamps if ts.modality == ModalityType.VISUAL]
    
    def _align_to_video_baseline(self, ts: TimestampInfo, 
                                video_baseline: List[TimestampInfo]) -> TimestampInfo:
        """将时间戳对齐到视频基准"""
        if not video_baseline:
            return ts
        
        # 找到最接近的视频时间戳
        closest_video = min(video_baseline, key=lambda x: abs(x.start_time - ts.start_time))
        time_offset = closest_video.start_time - ts.start_time
        
        # 创建校正后的时间戳
        return TimestampInfo(
            file_id=ts.file_id,
            segment_id=ts.segment_id,
            modality=ts.modality,
            start_time=ts.start_time + time_offset,
            end_time=ts.end_time + time_offset,
            duration=ts.duration,
            frame_index=ts.frame_index,
            vector_id=ts.vector_id,
            confidence=ts.confidence,
            scene_boundary=ts.scene_boundary
        )