"""
时间戳处理器 - 处理视频和音频的时间戳精确计算和同步验证
"""
import time
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class TimestampProcessor:
    """时间戳处理器"""
    
    def __init__(self):
        """初始化时间戳处理器"""
        self.accuracy_requirement = 2.0  # ±2秒精度要求
        self.sync_tolerance = {
            'visual': 0.033,      # 帧级精度(30fps)
            'audio_music': 0.1,   # 音频精度
            'audio_speech': 0.2   # 语音精度
        }
    
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
    
    def validate_timestamp_accuracy(self, duration: float) -> bool:
        """
        验证时间戳精度是否满足要求
        
        Args:
            duration: 时间段持续时长
            
        Returns:
            是否满足精度要求
        """
        is_valid = duration <= (self.accuracy_requirement * 2)
        
        if not is_valid:
            logger.warning(f"时间戳精度不满足要求: duration={duration}s > {self.accuracy_requirement*2}s")
        else:
            logger.debug(f"时间戳精度验证通过: duration={duration}s")
        
        return is_valid
    
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