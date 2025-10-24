"""
时间戳处理器 - 处理视频和音频的时间戳精确计算和同步验证
"""
import time
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class TimestampProcessor:
    """时间戳处理器"""
    
    def __init__(self, config=None):
        """初始化时间戳处理器"""
        if config is not None:
            # 从配置中获取参数
            self.accuracy_requirement = config.get('processing.video.timestamp_processing.accuracy_requirement', 2.0)
            sync_tolerance_config = config.get('processing.video.timestamp_processing.sync_tolerance', {})
            self.sync_tolerance = {
                'visual': sync_tolerance_config.get('visual', 0.033),      # 帧级精度(30fps)
                'audio_music': sync_tolerance_config.get('audio_music', 0.1),   # 音频精度
                'audio_speech': sync_tolerance_config.get('audio_speech', 0.2)   # 语音精度
            }
        else:
            # 默认值
            self.accuracy_requirement = 2.0  # ±2秒精度要求
            self.sync_tolerance = {
                'visual': 0.033,      # 帧级精度(30fps)
                'audio_music': 0.1,   # 音频精度
                'audio_speech': 0.2   # 语音精度
            }
    
    def process_scene_aware_timestamps(self, scene_boundaries: List[Dict[str, Any]], 
                                     frame_rate: float = 30.0) -> List[Dict[str, Any]]:
        """
        处理场景感知的时间戳
        
        Args:
            scene_boundaries: 场景边界列表
            frame_rate: 帧率
            
        Returns:
            场景感知的时间戳处理结果
        """
        processed_scenes = []
        
        for scene in scene_boundaries:
            scene_info = {
                'scene_id': scene['scene_id'],
                'start_time': scene['start_time'],
                'end_time': scene['end_time'],
                'duration': scene['end_time'] - scene['start_time'],
                'timestamps': []
            }
            
            # 在场景内生成时间戳
            current_time = scene['start_time']
            while current_time <= scene['end_time']:
                # 生成帧时间戳
                frame_index = int((current_time - scene['start_time']) * frame_rate)
                frame_timestamp = self.calculate_frame_timestamp(frame_index, frame_rate, scene['start_time'])
                
                scene_info['timestamps'].append({
                    'frame_index': frame_index,
                    'timestamp': frame_timestamp,
                    'relative_time': current_time - scene['start_time']
                })
                
                current_time += 1.0  # 每秒一个时间戳点
            
            processed_scenes.append(scene_info)
        
        return processed_scenes
    
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