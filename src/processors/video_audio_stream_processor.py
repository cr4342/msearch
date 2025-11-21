"""
视频音频流处理器 - 专门处理视频和音频流的时间戳同步和精确匹配
实现±2秒精度的多模态流处理
"""
import os
import subprocess
import json
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
import logging
from dataclasses import dataclass

from src.processors.timestamp_processor import TimestampProcessor, TimestampInfo, ModalityType

logger = logging.getLogger(__name__)


@dataclass
class StreamInfo:
    """流信息数据类"""
    stream_type: str  # 'video' or 'audio'
    codec: str
    duration: float
    fps: Optional[float] = None  # 视频流专用
    sample_rate: Optional[int] = None  # 音频流专用
    channels: Optional[int] = None  # 音频流专用
    width: Optional[int] = None  # 视频流专用
    height: Optional[int] = None  # 视频流专用


@dataclass
class SynchronizedStream:
    """同步流数据类"""
    video_timestamps: List[TimestampInfo]
    audio_timestamps: List[TimestampInfo]
    sync_quality: float  # 同步质量评分 0-1
    time_drift: float  # 时间漂移(秒)
    sync_points: List[Tuple[float, float]]  # 同步点列表 (video_time, audio_time)


class VideoAudioStreamProcessor:
    """视频音频流处理器 - 实现多模态流的精确时间戳处理"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化视频音频流处理器
        
        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.timestamp_processor = TimestampProcessor(config)
        
        # 从配置获取流处理参数
        stream_config = self.config.get('processing', {}).get('stream', {})
        self.enable_audio_extraction = stream_config.get('enable_audio_extraction', True)
        self.enable_stream_sync = stream_config.get('enable_stream_sync', True)
        self.sync_tolerance = stream_config.get('sync_tolerance', 0.1)  # 100ms同步容差
        self.max_drift_correction = stream_config.get('max_drift_correction', 1.0)  # 最大1秒漂移校正
        
        logger.info("视频音频流处理器初始化完成")
    
    def analyze_media_streams(self, media_path: str) -> Dict[str, StreamInfo]:
        """
        分析媒体文件的流信息
        
        Args:
            media_path: 媒体文件路径
            
        Returns:
            流信息字典 {'video': StreamInfo, 'audio': StreamInfo}
        """
        try:
            # 使用ffprobe获取详细流信息
            cmd = [
                "ffprobe", "-v", "error", "-show_streams",
                "-of", "json", media_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                raise RuntimeError(f"ffprobe执行失败: {result.stderr}")
            
            probe_data = json.loads(result.stdout)
            streams = probe_data.get('streams', [])
            
            stream_info = {}
            
            # 解析视频流
            for stream in streams:
                if stream.get('codec_type') == 'video':
                    # 计算帧率
                    fps = 30.0  # 默认帧率
                    if 'r_frame_rate' in stream:
                        try:
                            fps_str = stream['r_frame_rate']
                            if '/' in fps_str:
                                num, den = fps_str.split('/')
                                fps = float(num) / float(den)
                            else:
                                fps = float(fps_str)
                        except:
                            pass
                    
                    video_info = StreamInfo(
                        stream_type='video',
                        codec=stream.get('codec_name', 'unknown'),
                        duration=float(stream.get('duration', 0)),
                        fps=fps,
                        width=stream.get('width'),
                        height=stream.get('height')
                    )
                    stream_info['video'] = video_info
                    break
            
            # 解析音频流
            for stream in streams:
                if stream.get('codec_type') == 'audio':
                    audio_info = StreamInfo(
                        stream_type='audio',
                        codec=stream.get('codec_name', 'unknown'),
                        duration=float(stream.get('duration', 0)),
                        sample_rate=stream.get('sample_rate'),
                        channels=stream.get('channels')
                    )
                    stream_info['audio'] = audio_info
                    break
            
            logger.debug(f"媒体流分析完成: {media_path}, 流数量={len(stream_info)}")
            return stream_info
            
        except Exception as e:
            logger.error(f"媒体流分析失败: {e}")
            return {}
    
    def process_video_stream(self, video_path: str, stream_info: StreamInfo, 
                           scenes: List[Dict[str, Any]] = None) -> List[TimestampInfo]:
        """
        处理视频流，生成精确时间戳
        
        Args:
            video_path: 视频文件路径
            stream_info: 视频流信息
            scenes: 场景信息列表
            
        Returns:
            视频流时间戳列表
        """
        try:
            fps = stream_info.fps or 30.0
            duration = stream_info.duration
            total_frames = int(fps * duration)
            
            # 使用时间戳处理器处理视频流
            video_timestamps = self.timestamp_processor.process_video_stream_timestamps(
                video_path, fps, total_frames, scenes
            )
            
            logger.info(f"视频流处理完成: {len(video_timestamps)}个时间戳, fps={fps:.2f}")
            return video_timestamps
            
        except Exception as e:
            logger.error(f"视频流处理失败: {e}")
            return []
    
    def process_audio_stream(self, audio_path: str, stream_info: StreamInfo, 
                           audio_segments: List[Dict[str, Any]] = None) -> List[TimestampInfo]:
        """
        处理音频流，生成精确时间戳
        
        Args:
            audio_path: 音频文件路径
            stream_info: 音频流信息
            audio_segments: 音频分类段信息
            
        Returns:
            音频流时间戳列表
        """
        try:
            sample_rate = stream_info.sample_rate or 16000
            
            # 如果没有提供音频分类段，创建默认段
            if not audio_segments:
                audio_segments = [{
                    'type': 'music',  # 默认为音乐
                    'start_time': 0.0,
                    'end_time': stream_info.duration,
                    'confidence': 1.0
                }]
            
            # 使用时间戳处理器处理音频流
            audio_timestamps = self.timestamp_processor.process_audio_stream_timestamps(
                audio_path, audio_segments, sample_rate
            )
            
            logger.info(f"音频流处理完成: {len(audio_timestamps)}个时间戳")
            return audio_timestamps
            
        except Exception as e:
            logger.error(f"音频流处理失败: {e}")
            return []
    
    def synchronize_video_audio_streams(self, video_timestamps: List[TimestampInfo], 
                                      audio_timestamps: List[TimestampInfo]) -> SynchronizedStream:
        """
        同步视频和音频流的时间戳
        
        Args:
            video_timestamps: 视频时间戳列表
            audio_timestamps: 音频时间戳列表
            
        Returns:
            同步流对象
        """
        try:
            if not self.enable_stream_sync:
                return SynchronizedStream(
                    video_timestamps=video_timestamps,
                    audio_timestamps=audio_timestamps,
                    sync_quality=1.0,
                    time_drift=0.0,
                    sync_points=[]
                )
            
            # 使用时间戳处理器进行同步
            synced_video, synced_audio = self.timestamp_processor.synchronize_multimodal_timestamps(
                video_timestamps, audio_timestamps
            )
            
            # 计算同步质量和时间漂移
            sync_quality, time_drift, sync_points = self._calculate_sync_metrics(
                video_timestamps, audio_timestamps, synced_video, synced_audio
            )
            
            synchronized_stream = SynchronizedStream(
                video_timestamps=synced_video,
                audio_timestamps=synced_audio,
                sync_quality=sync_quality,
                time_drift=time_drift,
                sync_points=sync_points
            )
            
            logger.info(f"流同步完成: 同步质量={sync_quality:.3f}, 时间漂移={time_drift:.3f}s")
            return synchronized_stream
            
        except Exception as e:
            logger.error(f"流同步失败: {e}")
            return SynchronizedStream(
                video_timestamps=video_timestamps,
                audio_timestamps=audio_timestamps,
                sync_quality=0.0,
                time_drift=0.0,
                sync_points=[]
            )
    
    def _calculate_sync_metrics(self, original_video: List[TimestampInfo], 
                              original_audio: List[TimestampInfo],
                              synced_video: List[TimestampInfo], 
                              synced_audio: List[TimestampInfo]) -> Tuple[float, float, List[Tuple[float, float]]]:
        """
        计算同步质量指标
        
        Args:
            original_video: 原始视频时间戳
            original_audio: 原始音频时间戳
            synced_video: 同步后视频时间戳
            synced_audio: 同步后音频时间戳
            
        Returns:
            (同步质量, 时间漂移, 同步点列表)
        """
        try:
            sync_points = []
            time_diffs = []
            
            # 找到对应的同步点
            for video_ts in synced_video:
                # 找到最接近的音频时间戳
                closest_audio = min(synced_audio, 
                                  key=lambda a_ts: abs(a_ts.start_time - video_ts.start_time))
                
                time_diff = abs(video_ts.start_time - closest_audio.start_time)
                
                if time_diff <= self.sync_tolerance * 2:  # 在容差范围内
                    sync_points.append((video_ts.start_time, closest_audio.start_time))
                    time_diffs.append(time_diff)
            
            # 计算同步质量(在容差范围内的点的比例)
            total_possible_points = min(len(synced_video), len(synced_audio))
            sync_quality = len(sync_points) / total_possible_points if total_possible_points > 0 else 0.0
            
            # 计算平均时间漂移
            time_drift = np.mean(time_diffs) if time_diffs else 0.0
            
            return sync_quality, time_drift, sync_points
            
        except Exception as e:
            logger.error(f"同步质量计算失败: {e}")
            return 0.0, 0.0, []
    
    def extract_synchronized_segments(self, media_path: str, 
                                    synchronized_stream: SynchronizedStream,
                                    target_duration: float = 30.0) -> List[Dict[str, Any]]:
        """
        提取同步的媒体段
        
        Args:
            media_path: 媒体文件路径
            synchronized_stream: 同步流对象
            target_duration: 目标段时长
            
        Returns:
            同步段信息列表
        """
        try:
            segments = []
            video_timestamps = synchronized_stream.video_timestamps
            audio_timestamps = synchronized_stream.audio_timestamps
            
            # 按时间排序
            video_timestamps.sort(key=lambda x: x.start_time)
            audio_timestamps.sort(key=lambda x: x.start_time)
            
            # 创建时间对齐的段
            current_time = 0.0
            segment_index = 0
            
            while current_time < max(
                video_timestamps[-1].end_time if video_timestamps else 0,
                audio_timestamps[-1].end_time if audio_timestamps else 0
            ):
                segment_end = current_time + target_duration
                
                # 找到时间范围内的视频和音频时间戳
                video_in_range = [
                    ts for ts in video_timestamps 
                    if ts.start_time < segment_end and ts.end_time > current_time
                ]
                
                audio_in_range = [
                    ts for ts in audio_timestamps 
                    if ts.start_time < segment_end and ts.end_time > current_time
                ]
                
                if video_in_range or audio_in_range:
                    segment_info = {
                        'segment_id': f"sync_segment_{segment_index}",
                        'start_time': current_time,
                        'end_time': segment_end,
                        'duration': target_duration,
                        'video_timestamps': len(video_in_range),
                        'audio_timestamps': len(audio_in_range),
                        'has_video': len(video_in_range) > 0,
                        'has_audio': len(audio_in_range) > 0,
                        'sync_quality': synchronized_stream.sync_quality
                    }
                    segments.append(segment_info)
                    segment_index += 1
                
                current_time = segment_end
            
            logger.info(f"同步段提取完成: {len(segments)}个段")
            return segments
            
        except Exception as e:
            logger.error(f"同步段提取失败: {e}")
            return []
    
    def validate_stream_synchronization(self, synchronized_stream: SynchronizedStream) -> Dict[str, Any]:
        """
        验证流同步质量
        
        Args:
            synchronized_stream: 同步流对象
            
        Returns:
            验证报告
        """
        try:
            validation_report = {
                'sync_quality': synchronized_stream.sync_quality,
                'time_drift': synchronized_stream.time_drift,
                'sync_points_count': len(synchronized_stream.sync_points),
                'video_segments': len(synchronized_stream.video_timestamps),
                'audio_segments': len(synchronized_stream.audio_timestamps),
                'quality_grade': 'unknown',
                'recommendations': []
            }
            
            # 质量评级
            if synchronized_stream.sync_quality >= 0.9:
                validation_report['quality_grade'] = 'excellent'
            elif synchronized_stream.sync_quality >= 0.7:
                validation_report['quality_grade'] = 'good'
            elif synchronized_stream.sync_quality >= 0.5:
                validation_report['quality_grade'] = 'fair'
            else:
                validation_report['quality_grade'] = 'poor'
            
            # 生成建议
            if synchronized_stream.sync_quality < 0.7:
                validation_report['recommendations'].append(
                    "同步质量较低，建议检查音视频流的时间基准"
                )
            
            if synchronized_stream.time_drift > self.max_drift_correction:
                validation_report['recommendations'].append(
                    f"时间漂移过大({synchronized_stream.time_drift:.3f}s)，建议重新处理媒体文件"
                )
            
            if len(synchronized_stream.sync_points) < 5:
                validation_report['recommendations'].append(
                    "同步点过少，可能影响时间戳精度"
                )
            
            logger.info(f"流同步验证完成: 质量等级={validation_report['quality_grade']}")
            return validation_report
            
        except Exception as e:
            logger.error(f"流同步验证失败: {e}")
            return {'error': str(e)}
    
    def process_multimodal_media(self, media_path: str, 
                                scenes: List[Dict[str, Any]] = None,
                                audio_segments: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        处理多模态媒体文件，生成同步的时间戳
        
        Args:
            media_path: 媒体文件路径
            scenes: 场景信息列表
            audio_segments: 音频分类段信息
            
        Returns:
            完整的多模态处理结果
        """
        try:
            logger.info(f"开始多模态媒体处理: {media_path}")
            
            # 分析媒体流
            stream_info = self.analyze_media_streams(media_path)
            
            if not stream_info:
                raise ValueError("无法分析媒体流信息")
            
            # 处理视频流
            video_timestamps = []
            if 'video' in stream_info:
                video_timestamps = self.process_video_stream(
                    media_path, stream_info['video'], scenes
                )
            
            # 处理音频流
            audio_timestamps = []
            if 'audio' in stream_info and self.enable_audio_extraction:
                audio_timestamps = self.process_audio_stream(
                    media_path, stream_info['audio'], audio_segments
                )
            
            # 同步多模态流
            synchronized_stream = self.synchronize_video_audio_streams(
                video_timestamps, audio_timestamps
            )
            
            # 验证同步质量
            validation_report = self.validate_stream_synchronization(synchronized_stream)
            
            # 提取同步段
            synchronized_segments = self.extract_synchronized_segments(
                media_path, synchronized_stream
            )
            
            result = {
                'status': 'success',
                'media_path': media_path,
                'stream_info': {
                    stream_type: {
                        'codec': info.codec,
                        'duration': info.duration,
                        'fps': info.fps,
                        'sample_rate': info.sample_rate,
                        'channels': info.channels,
                        'width': info.width,
                        'height': info.height
                    }
                    for stream_type, info in stream_info.items()
                },
                'synchronized_stream': {
                    'video_segments': len(synchronized_stream.video_timestamps),
                    'audio_segments': len(synchronized_stream.audio_timestamps),
                    'sync_quality': synchronized_stream.sync_quality,
                    'time_drift': synchronized_stream.time_drift,
                    'sync_points': len(synchronized_stream.sync_points)
                },
                'validation_report': validation_report,
                'synchronized_segments': synchronized_segments,
                'timestamp_accuracy': '±2s',
                'processing_config': {
                    'enable_audio_extraction': self.enable_audio_extraction,
                    'enable_stream_sync': self.enable_stream_sync,
                    'sync_tolerance': self.sync_tolerance
                }
            }
            
            logger.info(f"多模态媒体处理完成: 视频段{len(synchronized_stream.video_timestamps)}个, "
                       f"音频段{len(synchronized_stream.audio_timestamps)}个, "
                       f"同步质量={synchronized_stream.sync_quality:.3f}")
            
            return result
            
        except Exception as e:
            logger.error(f"多模态媒体处理失败: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'media_path': media_path
            }