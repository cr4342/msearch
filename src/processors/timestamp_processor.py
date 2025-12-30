"""
时间戳处理器
处理视频和音频的时间戳信息
"""

from typing import Dict, Any, List, Optional, Tuple
import logging
import cv2
import numpy as np
from dataclasses import dataclass
from enum import Enum
import subprocess
import json


logger = logging.getLogger(__name__)


class ModalityType(str, Enum):
    """模态类型枚举"""
    VISUAL = "visual"
    AUDIO_MUSIC = "audio_music"
    AUDIO_VOICE = "audio_voice"
    AUDIO_NOISE = "audio_noise"
    TEXT = "text"


@dataclass
class TimestampInfo:
    """时间戳信息数据类"""
    file_id: str
    segment_id: str
    start_time: float
    end_time: float
    duration: float
    modality: ModalityType
    confidence: float
    vector_id: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class TimeStampedResult:
    """带时间戳的结果数据类"""
    file_id: str
    segment_id: str
    timestamp: float
    modality: ModalityType
    confidence: float
    data: Any


@dataclass
class MergedTimeSegment:
    """合并后的时间段数据类"""
    start_time: float
    end_time: float
    duration: float
    modalities: List[ModalityType]
    segments: List[TimestampInfo]
    confidence: float


class TimestampProcessor:
    """时间戳处理器类"""

    # 默认配置键名映射到配置文件路径
    CONFIG_KEYS = {
        'scene_detection_threshold': 'timestamp_processing.scene_detection_threshold',
        'max_segment_duration': 'timestamp_processing.max_segment_duration',
        'keyframe_interval': 'timestamp_processing.keyframe_interval',
        'timestamp_accuracy': 'timestamp_processing.precision_requirement',
        'ffmpeg_timeout': 'media_processing.ffmpeg.timeout',
    }
    
    def __init__(self, config: Dict[str, Any] = None):
        """初始化时间戳处理器"""
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        # 从配置中获取时间戳精度参数
        self.scene_detection_threshold = self.config.get('scene_detection_threshold', 0.15)
        self.max_segment_duration = self.config.get('max_segment_duration', 5.0)  # 5秒
        self.keyframe_interval = self.config.get('keyframe_interval', 2.0)  # 2秒
        self.timestamp_accuracy = self.config.get('timestamp_accuracy', 2.0)  # ±2秒精度
        self.ffmpeg_timeout = self.config.get('ffmpeg_timeout', 60)  # FFmpeg超时
    
    def extract_timestamps(self, media_path: str) -> List[Dict[str, float]]:
        """从媒体文件中提取时间戳"""
        self.logger.info(f"提取时间戳: {media_path}")
        
        try:
            # 获取视频元数据
            metadata = self._get_video_metadata(media_path)
            if not metadata:
                return []
            
            # 获取场景边界
            scene_boundaries = self._get_scene_boundaries_ffmpeg(media_path)
            
            # 获取关键帧时间戳
            keyframe_timestamps = self._get_keyframe_timestamps_cv2(media_path)
            
            # 合并场景边界和关键帧
            all_timestamps = self._merge_timestamps(scene_boundaries, keyframe_timestamps, metadata['duration'])
            
            return all_timestamps
            
        except Exception as e:
            self.logger.error(f"提取时间戳失败: {e}")
            return []
    
    def _get_video_metadata(self, video_path: str) -> Dict[str, Any]:
        """获取视频元数据"""
        try:
            # 使用ffprobe获取视频元数据
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.ffmpeg_timeout)
            
            if result.returncode != 0:
                self.logger.error(f"ffprobe失败: {result.stderr}")
                return {}
            
            metadata = json.loads(result.stdout)
            
            # 提取视频流信息
            video_stream = None
            for stream in metadata.get('streams', []):
                if stream.get('codec_type') == 'video':
                    video_stream = stream
                    break
            
            if not video_stream:
                self.logger.error("未找到视频流")
                return {}
            
            duration = float(video_stream.get('duration', metadata['format'].get('duration', 0)))
            fps = eval(video_stream.get('avg_frame_rate', '0')) or 30.0  # 默认30fps
            
            return {
                'duration': duration,
                'fps': fps,
                'width': video_stream.get('width', 0),
                'height': video_stream.get('height', 0),
                'codec': video_stream.get('codec_name', 'unknown')
            }
            
        except Exception as e:
            self.logger.error(f"获取视频元数据失败: {e}")
            return {}
    
    def _get_scene_boundaries_ffmpeg(self, video_path: str) -> List[float]:
        """使用FFmpeg获取场景边界"""
        try:
            # 使用FFmpeg的scene检测滤镜
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-vf', f'scene_detect=threshold={self.scene_detection_threshold}',
                '-f', 'null', '-'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.ffmpeg_timeout)
            
            # 解析FFmpeg输出以找到场景边界
            scene_boundaries = []
            
            # 从stderr中提取场景检测信息
            for line in result.stderr.split('\n'):
                if 'scene_score' in line:
                    # 示例: [scene_detect @ 0x...] frame:123 scene_score:0.456
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part.startswith('scene_score:'):
                            try:
                                score = float(part.split(':')[1])
                                if score > self.scene_detection_threshold:
                                    # 找到帧号
                                    for j in range(i-1, max(-1, i-5), -1):
                                        if j < len(parts) and parts[j].startswith('frame:'):
                                            frame_num = int(parts[j].split(':')[1])
                                            fps = self._get_video_metadata(video_path).get('fps', 30.0)
                                            timestamp = frame_num / fps
                                            scene_boundaries.append(timestamp)
                                            break
                            except:
                                continue
                            
            return sorted(list(set(scene_boundaries)))
            
        except Exception as e:
            self.logger.error(f"FFmpeg场景检测失败: {e}")
            return []
    
    def _get_keyframe_timestamps_cv2(self, video_path: str) -> List[float]:
        """使用OpenCV获取关键帧时间戳"""
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                self.logger.error(f"无法打开视频: {video_path}")
                return []
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / fps if fps > 0 else 0
            
            keyframe_timestamps = []
            frame_interval = int(fps * self.keyframe_interval)
            
            frame_num = 0
            while frame_num < total_frames:
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
                ret, frame = cap.read()
                
                if ret:
                    timestamp = frame_num / fps
                    keyframe_timestamps.append(timestamp)
                
                frame_num += frame_interval
            
            cap.release()
            return keyframe_timestamps
            
        except Exception as e:
            self.logger.error(f"OpenCV关键帧提取失败: {e}")
            return []
    
    def _merge_timestamps(self, scene_boundaries: List[float], keyframe_timestamps: List[float], duration: float) -> List[Dict[str, float]]:
        """合并场景边界和关键帧时间戳"""
        # 合并所有时间戳并排序
        all_timestamps = sorted(set(scene_boundaries + keyframe_timestamps))
        
        # 确保包含视频开始和结束时间
        if all_timestamps:
            if all_timestamps[0] > 0:
                all_timestamps.insert(0, 0.0)
            if all_timestamps[-1] < duration:
                all_timestamps.append(duration)
        else:
            all_timestamps = [0.0, duration]
        
        # 按最大段时长切分时间戳
        final_timestamps = []
        for i in range(len(all_timestamps)):
            if i == 0:
                continue
                
            start_time = all_timestamps[i-1]
            end_time = all_timestamps[i]
            segment_duration = end_time - start_time
            
            # 如果段太长，按最大时长切分
            if segment_duration > self.max_segment_duration:
                num_segments = int(segment_duration / self.max_segment_duration) + 1
                segment_length = segment_duration / num_segments
                
                for j in range(num_segments):
                    segment_start = start_time + j * segment_length
                    segment_end = start_time + (j + 1) * segment_length
                    final_timestamps.append({
                        'start_time': segment_start,
                        'end_time': min(segment_end, end_time),
                        'duration': min(segment_length, end_time - segment_start)
                    })
            else:
                final_timestamps.append({
                    'start_time': start_time,
                    'end_time': end_time,
                    'duration': segment_duration
                })
        
        return final_timestamps
    
    def process_timestamps(self, timestamps: List[Dict[str, float]]) -> List[Dict[str, float]]:
        """处理时间戳数据"""
        # 实现基本的时间戳处理功能
        return timestamps
    
    def get_scene_boundaries(self, media_path: str) -> List[float]:
        """获取场景边界时间戳"""
        return self._get_scene_boundaries_ffmpeg(media_path)
    
    def get_keyframe_timestamps(self, media_path: str) -> List[float]:
        """获取关键帧时间戳"""
        return self._get_keyframe_timestamps_cv2(media_path)
    
    def calculate_absolute_timestamp(self, segment_start_time: float, frame_timestamp_in_segment: float) -> float:
        """
        根据切片开始时间和帧在切片内的相对时间计算绝对时间戳
        
        Args:
            segment_start_time: 切片开始时间
            frame_timestamp_in_segment: 帧在切片内的相对时间
        
        Returns:
            绝对时间戳
        """
        absolute_timestamp = segment_start_time + frame_timestamp_in_segment
        
        # 验证时间戳的合理性
        if frame_timestamp_in_segment < 0:
            self.logger.warning(f"帧时间戳不能为负数: {frame_timestamp_in_segment}")
            absolute_timestamp = segment_start_time
        
        return absolute_timestamp
    
    def validate_timestamp_accuracy(self, calculated_timestamp: float, expected_timestamp: float) -> bool:
        """
        验证时间戳精度是否满足要求（±2秒）
        
        Args:
            calculated_timestamp: 计算出的时间戳
            expected_timestamp: 期望的时间戳
        
        Returns:
            是否满足精度要求
        """
        return abs(calculated_timestamp - expected_timestamp) <= self.timestamp_accuracy
    
    def get_video_segments(self, video_path: str) -> List[Dict[str, Any]]:
        """
        获取视频分段信息，包括精确的时间戳
        
        Args:
            video_path: 视频文件路径
        
        Returns:
            视频分段信息列表
        """
        try:
            metadata = self._get_video_metadata(video_path)
            if not metadata:
                return []
            
            # 获取场景边界
            scene_boundaries = self._get_scene_boundaries_ffmpeg(video_path)
            
            # 生成视频分段
            segments = []
            duration = metadata['duration']
            
            # 从0开始，使用场景边界和最大段长度切分视频
            start_time = 0.0
            segment_index = 0
            
            for boundary in sorted(scene_boundaries):
                if boundary <= start_time:
                    continue
                
                # 检查段长度是否超过最大限制
                if boundary - start_time > self.max_segment_duration:
                    # 切分当前段
                    current_end = start_time + self.max_segment_duration
                    segments.append({
                        'segment_id': f"seg_{segment_index:06d}",
                        'file_uuid': video_path,
                        'segment_index': segment_index,
                        'start_time': start_time,
                        'end_time': current_end,
                        'duration': current_end - start_time,
                        'scene_boundary': False,  # 非场景边界切分
                        'has_audio': True  # 假设都有音频
                    })
                    segment_index += 1
                    start_time = current_end
                    continue
                
                # 创建场景边界段
                segments.append({
                    'segment_id': f"seg_{segment_index:06d}",
                    'file_uuid': video_path,
                    'segment_index': segment_index,
                    'start_time': start_time,
                    'end_time': boundary,
                    'duration': boundary - start_time,
                    'scene_boundary': True,  # 场景边界切分
                    'has_audio': True
                })
                segment_index += 1
                start_time = boundary
            
            # 处理最后一个片段（到视频末尾）
            if start_time < duration:
                if duration - start_time > self.max_segment_duration:
                    # 如果最后一段仍然太长，继续切分
                    while start_time < duration:
                        current_end = min(start_time + self.max_segment_duration, duration)
                        segments.append({
                            'segment_id': f"seg_{segment_index:06d}",
                            'file_uuid': video_path,
                            'segment_index': segment_index,
                            'start_time': start_time,
                            'end_time': current_end,
                            'duration': current_end - start_time,
                            'scene_boundary': False,
                            'has_audio': True
                        })
                        segment_index += 1
                        start_time = current_end
                else:
                    segments.append({
                        'segment_id': f"seg_{segment_index:06d}",
                        'file_uuid': video_path,
                        'segment_index': segment_index,
                        'start_time': start_time,
                        'end_time': duration,
                        'duration': duration - start_time,
                        'scene_boundary': False,
                        'has_audio': True
                    })
            
            return segments
            
        except Exception as e:
            self.logger.error(f"获取视频分段失败: {e}")
            return []
    
    def get_frame_timestamp_in_segment(self, segment_duration: float) -> float:
        """
        获取片段中帧的时间戳（对于5秒以内的片段，使用中间帧）
        
        Args:
            segment_duration: 片段时长
        
        Returns:
            帧在片段内的相对时间戳
        """
        # 对于5秒以内的片段，提取中间帧
        return segment_duration / 2.0
    
    def get_video_timestamp_with_accuracy(self, segment_info: Dict[str, Any], frame_in_segment: float = None) -> float:
        """
        获取视频的精确时间戳
        
        Args:
            segment_info: 片段信息
            frame_in_segment: 帧在片段内的相对时间（如果为None，使用中间帧）
        
        Returns:
            绝对时间戳
        """
        if frame_in_segment is None:
            frame_in_segment = self.get_frame_timestamp_in_segment(segment_info['duration'])
        
        return self.calculate_absolute_timestamp(segment_info['start_time'], frame_in_segment)
