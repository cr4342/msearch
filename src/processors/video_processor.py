"""
视频处理器 - 处理视频文件的场景检测、关键帧提取和时间戳管理
实现±2秒精度的视频时间戳处理，支持场景感知切片和多模态时间同步
"""
import os
import cv2
import numpy as np
import subprocess
import json
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import logging
from dataclasses import dataclass

from src.processors.timestamp_processor import (
    TimestampProcessor, TimestampInfo, ModalityType, TimeAccurateRetrieval
)

logger = logging.getLogger(__name__)


@dataclass
class VideoMetadata:
    """视频元数据"""
    duration: float
    fps: float
    width: int
    height: int
    frame_count: int
    codec: str
    bitrate: int
    has_audio: bool


@dataclass
class SceneInfo:
    """场景信息"""
    scene_id: int
    start_time: float
    end_time: float
    start_frame: int
    end_frame: int
    confidence: float
    is_boundary: bool


@dataclass
class KeyFrame:
    """关键帧信息"""
    frame_index: int
    timestamp: float
    scene_id: int
    frame_data: np.ndarray
    confidence: float
    is_scene_boundary: bool


class VideoProcessor:
    """视频处理器 - 实现场景检测、关键帧提取和精确时间戳管理"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化视频处理器
        
        Args:
            config: 配置字典
        """
        self.config = config
        
        # 从配置获取处理参数
        video_config = config.get('processing', {}).get('video', {})
        
        # 预处理配置
        preprocessing_config = video_config.get('preprocessing', {})
        self.target_resolution = preprocessing_config.get('resolution_conversion', {}).get('target_resolution', 720)
        self.target_codec = preprocessing_config.get('encoding', {}).get('target_codec', 'h264')
        self.target_bitrate = preprocessing_config.get('encoding', {}).get('target_bitrate', 2.0)
        self.max_fps = preprocessing_config.get('encoding', {}).get('max_fps', 30)
        
        # 关键帧提取配置
        frame_config = video_config.get('frame_extraction', {})
        self.short_video_interval = frame_config.get('short_video_interval', 2)  # 秒
        self.long_video_interval = frame_config.get('long_video_interval', 5)   # 秒
        self.long_video_threshold = frame_config.get('long_video_threshold', 120)  # 秒
        
        # 场景检测配置
        scene_config = video_config.get('scene_detection', {})
        self.scene_threshold = scene_config.get('threshold', 0.3)
        self.min_scene_length = scene_config.get('min_scene_length', 3)
        self.max_scene_length = scene_config.get('max_scene_length', 60)
        
        # CLIP模型输入尺寸
        self.clip_input_size = (224, 224)
        
        # 初始化时间戳处理器
        self.timestamp_processor = TimestampProcessor(config)
        
        # 处理限制
        self.max_duration = video_config.get('max_duration', 7200)  # 2小时
        self.max_file_size = video_config.get('max_file_size', 500) * 1024 * 1024  # MB转字节
        
        logger.info("视频处理器初始化完成")
    
    async def process_video(self, video_path: str) -> Dict[str, Any]:
        """
        处理视频文件 - 完整的视频处理流程
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            处理结果字典
        """
        try:
            logger.info(f"开始处理视频: {video_path}")
            
            # 验证文件
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"视频文件不存在: {video_path}")
            
            file_size = os.path.getsize(video_path)
            if file_size > self.max_file_size:
                raise ValueError(f"视频文件过大: {file_size / (1024*1024):.1f}MB > {self.max_file_size / (1024*1024):.1f}MB")
            
            # 使用异步执行器处理CPU密集型操作
            import asyncio
            loop = asyncio.get_event_loop()
            
            # 1. 提取视频元数据
            metadata = await loop.run_in_executor(None, self._extract_metadata, video_path)
            
            # 验证视频时长
            if metadata.duration > self.max_duration:
                raise ValueError(f"视频时长过长: {metadata.duration:.1f}s > {self.max_duration}s")
            
            # 2. 预处理视频(格式转换和分辨率降采样)
            preprocessed_path = await loop.run_in_executor(None, self._preprocess_video, video_path, metadata)
            
            # 3. 场景检测
            scenes = await loop.run_in_executor(None, self._detect_scenes, preprocessed_path, metadata)
            
            # 4. 关键帧提取
            keyframes = await loop.run_in_executor(None, self._extract_keyframes, preprocessed_path, scenes, metadata)
            
            # 5. 创建时间戳信息
            timestamp_infos = self._create_timestamp_infos(keyframes, video_path)
            
            # 6. 音频流分离(如果需要)
            audio_segments = []
            if metadata.has_audio:
                audio_segments = await loop.run_in_executor(None, self._extract_audio_segments, video_path, scenes)
            
            # 7. 多模态时间同步验证
            if audio_segments:
                all_timestamps = timestamp_infos + [seg['timestamp_info'] for seg in audio_segments]
                synchronized_timestamps = self.timestamp_processor.correct_timestamp_drift(all_timestamps)
                
                # 分离视频和音频时间戳
                video_timestamps = [ts for ts in synchronized_timestamps if ts.modality == ModalityType.VISUAL]
                audio_timestamps = [ts for ts in synchronized_timestamps if ts.modality != ModalityType.VISUAL]
            else:
                video_timestamps = timestamp_infos
                audio_timestamps = []
            
            logger.info(f"视频处理完成: {video_path}, 场景数: {len(scenes)}, 关键帧数: {len(keyframes)}")
            
            return {
                'status': 'success',
                'metadata': metadata.__dict__,
                'scenes': [scene.__dict__ for scene in scenes],
                'keyframes': [self._keyframe_to_dict(kf) for kf in keyframes],
                'video_timestamps': [ts.__dict__ for ts in video_timestamps],
                'audio_timestamps': [ts.__dict__ for ts in audio_timestamps],
                'audio_segments': audio_segments,
                'preprocessed_path': preprocessed_path,
                'file_path': video_path,
                'processing_stats': {
                    'original_duration': metadata.duration,
                    'original_resolution': f"{metadata.width}x{metadata.height}",
                    'target_resolution': f"{self.target_resolution}p",
                    'scenes_detected': len(scenes),
                    'keyframes_extracted': len(keyframes),
                    'timestamp_accuracy': f"±{self.timestamp_processor.accuracy_requirement}s"
                }
            }
            
        except Exception as e:
            logger.error(f"视频处理失败: {video_path}, 错误: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'file_path': video_path
            }
    
    def _extract_metadata(self, video_path: str) -> VideoMetadata:
        """
        提取视频元数据
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            视频元数据对象
        """
        try:
            # 使用ffprobe提取元数据
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            metadata = json.loads(result.stdout)
            
            # 提取视频流信息
            video_stream = None
            audio_stream = None
            
            for stream in metadata.get('streams', []):
                if stream['codec_type'] == 'video' and video_stream is None:
                    video_stream = stream
                elif stream['codec_type'] == 'audio' and audio_stream is None:
                    audio_stream = stream
            
            if not video_stream:
                raise ValueError("未找到视频流")
            
            # 解析视频信息
            duration = float(metadata['format'].get('duration', 0))
            fps = eval(video_stream.get('r_frame_rate', '30/1'))  # 处理分数形式的帧率
            width = int(video_stream.get('width', 0))
            height = int(video_stream.get('height', 0))
            frame_count = int(video_stream.get('nb_frames', duration * fps))
            codec = video_stream.get('codec_name', 'unknown')
            bitrate = int(metadata['format'].get('bit_rate', 0))
            has_audio = audio_stream is not None
            
            return VideoMetadata(
                duration=duration,
                fps=fps,
                width=width,
                height=height,
                frame_count=frame_count,
                codec=codec,
                bitrate=bitrate,
                has_audio=has_audio
            )
            
        except subprocess.CalledProcessError as e:
            logger.error(f"ffprobe执行失败: {e}")
            raise ValueError(f"无法提取视频元数据: {e}")
        except Exception as e:
            logger.error(f"元数据提取失败: {e}")
            raise
    
    def _preprocess_video(self, video_path: str, metadata: VideoMetadata) -> str:
        """
        预处理视频：格式转换和分辨率降采样
        
        Args:
            video_path: 原始视频路径
            metadata: 视频元数据
            
        Returns:
            预处理后的视频路径
        """
        try:
            # 检查是否需要预处理
            needs_preprocessing = (
                metadata.height > self.target_resolution or
                metadata.width > self.target_resolution * 16 / 9 or  # 假设16:9比例
                metadata.codec != self.target_codec or
                metadata.fps > self.max_fps
            )
            
            if not needs_preprocessing:
                logger.debug(f"视频无需预处理: {video_path}")
                return video_path
            
            # 创建临时输出文件
            output_dir = Path(video_path).parent / "preprocessed"
            output_dir.mkdir(exist_ok=True)
            
            output_path = output_dir / f"preprocessed_{Path(video_path).stem}.mp4"
            
            # 计算目标分辨率(保持宽高比)
            if metadata.height > metadata.width:
                # 竖屏视频
                target_height = self.target_resolution
                target_width = int(metadata.width * target_height / metadata.height)
            else:
                # 横屏视频
                target_width = int(self.target_resolution * 16 / 9)  # 假设16:9比例
                target_height = self.target_resolution
            
            # 构建ffmpeg命令
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-c:v', 'libx264',
                '-vf', f'scale={target_width}:{target_height}',
                '-r', str(min(metadata.fps, self.max_fps)),
                '-b:v', f'{self.target_bitrate}M',
                '-c:a', 'aac',
                '-b:a', '128k',
                '-y',  # 覆盖输出文件
                str(output_path)
            ]
            
            logger.debug(f"开始视频预处理: {metadata.width}x{metadata.height} -> {target_width}x{target_height}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            logger.info(f"视频预处理完成: {output_path}")
            return str(output_path)
            
        except subprocess.CalledProcessError as e:
            logger.error(f"视频预处理失败: {e.stderr}")
            raise ValueError(f"视频预处理失败: {e}")
        except Exception as e:
            logger.error(f"预处理过程出错: {e}")
            return video_path  # 返回原始路径作为备选
        
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"视频文件不存在: {video_path}")
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"无法打开视频文件: {video_path}")
        
        # 获取视频属性
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        cap.release()
        
        duration = frame_count / fps if fps > 0 else 0
        
        return {
            'width': width,
            'height': height,
            'fps': fps,
            'frame_count': frame_count,
            'duration': duration,
            'resolution': f"{width}x{height}"
        }
    
    def _detect_scenes(self, video_path: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        检测视频场景变化
        
        Args:
            video_path: 视频文件路径
            metadata: 视频元数据
            
        Returns:
            场景列表
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"无法打开视频文件: {video_path}")
        
        scenes = []
        prev_frame = None
        scene_start_frame = 0
        fps = metadata['fps']
        
        frame_idx = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # 每隔一定帧数进行场景检测以提高性能
            if frame_idx % int(fps/2) == 0:  # 每0.5秒检测一次
                # 转换为灰度图并计算直方图
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                if prev_frame is not None:
                    # 计算帧间差异
                    diff = cv2.absdiff(prev_frame, gray)
                    diff_score = np.mean(diff) / 255.0
                    
                    # 如果差异超过阈值，认为是场景变化
                    if diff_score > self.scene_threshold:
                        scene_end_frame = frame_idx
                        scene_duration = (scene_end_frame - scene_start_frame) / fps
                        
                        scenes.append({
                            'start_frame': scene_start_frame,
                            'end_frame': scene_end_frame,
                            'start_time': scene_start_frame / fps,
                            'end_time': scene_end_frame / fps,
                            'duration': scene_duration,
                            'confidence': diff_score
                        })
                        
                        scene_start_frame = frame_idx
                
                prev_frame = gray.copy()
            
            frame_idx += 1
        
        # 添加最后一个场景
        if scene_start_frame < frame_idx:
            scene_duration = (frame_idx - scene_start_frame) / fps
            scenes.append({
                'start_frame': scene_start_frame,
                'end_frame': frame_idx,
                'start_time': scene_start_frame / fps,
                'end_time': frame_idx / fps,
                'duration': scene_duration,
                'confidence': 0.5  # 默认置信度
            })
        
        cap.release()
        return scenes
    
    def _extract_keyframes(self, video_path: str, scenes: List[Dict[str, Any]], 
                          metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        从场景中提取关键帧
        
        Args:
            video_path: 视频文件路径
            scenes: 场景列表
            metadata: 视频元数据
            
        Returns:
            关键帧列表
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"无法打开视频文件: {video_path}")
        
        keyframes = []
        fps = metadata['fps']
        
        for scene in scenes:
            start_frame = scene['start_frame']
            end_frame = scene['end_frame']
            
            # 计算抽帧间隔(基于配置的秒数)
            frame_interval_frames = int(self.frame_interval * fps)
            if frame_interval_frames < 1:
                frame_interval_frames = 1
            
            # 在场景内按间隔抽帧
            for frame_idx in range(start_frame, min(end_frame, metadata['frame_count']), frame_interval_frames):
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                if ret:
                    # 处理帧
                    processed_frame = self._process_frame(frame)
                    
                    # 计算时间戳
                    timestamp = frame_idx / fps
                    
                    keyframes.append({
                        'frame_index': frame_idx,
                        'timestamp': timestamp,
                        'frame_data': processed_frame,
                        'scene_id': scenes.index(scene),
                        'resolution': processed_frame.shape[:2]
                    })
        
        cap.release()
        return keyframes
    
    def _process_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        处理单个视频帧
        
        Args:
            frame: 原始帧数据
            
        Returns:
            处理后的帧数据
        """
        # 调整尺寸
        height, width = frame.shape[:2]
        max_width, max_height = self.max_resolution
        
        if width > max_width or height > max_height:
            scale_x = max_width / width
            scale_y = max_height / height
            scale = min(scale_x, scale_y)
            
            new_width = int(width * scale)
            new_height = int(height * scale)
            frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)
        
        # 调整到目标尺寸 (224x224)
        processed_frame = cv2.resize(frame, (self.target_size, self.target_size), interpolation=cv2.INTER_LINEAR)
        
        # 转换为RGB格式
        rgb_frame = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
        
        # 归一化到[0, 1]范围
        normalized_frame = rgb_frame.astype(np.float32) / 255.0
        
        return normalized_frame
    
    def _extract_audio(self, video_path: str) -> List[Dict[str, Any]]:
        '''
        从视频中提取音频流(占位方法)
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            音频片段列表
        '''
        # 这里应该调用音频处理器来处理音频流
        # 暂时返回空列表
        return []


# 示例使用
if __name__ == "__main__":
    # 配置示例
    config = {
        'processing.video.target_size': 224,
        'processing.video.max_resolution': (1280, 720),
        'processing.video.scene_threshold': 0.3,
        'processing.video.frame_interval': 2.0
    }
    
    # 创建处理器实例
    processor = VideoProcessor(config)
    
    # 处理视频 (需要实际的视频文件路径)
    # result = processor.process_video("path/to/video.mp4")
    # print(result)  
  
    def _detect_scenes(self, video_path: str, metadata: VideoMetadata) -> List[SceneInfo]:
        """
        检测视频场景边界
        
        Args:
            video_path: 视频文件路径
            metadata: 视频元数据
            
        Returns:
            场景信息列表
        """
        try:
            scenes = []
            
            # 打开视频文件
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError(f"无法打开视频文件: {video_path}")
            
            # 初始化场景检测参数
            prev_frame = None
            scene_start_frame = 0
            scene_start_time = 0.0
            scene_id = 0
            frame_index = 0
            
            # 计算帧间隔(用于加速处理)
            frame_skip = max(1, int(metadata.fps / 5))  # 每秒采样5帧进行场景检测
            
            logger.debug(f"开始场景检测: 阈值={self.scene_threshold}, 帧间隔={frame_skip}")
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # 跳帧处理
                if frame_index % frame_skip != 0:
                    frame_index += 1
                    continue
                
                current_time = frame_index / metadata.fps
                
                # 转换为灰度图像进行场景检测
                gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                if prev_frame is not None:
                    # 计算帧间差异
                    diff = cv2.absdiff(prev_frame, gray_frame)
                    diff_score = np.mean(diff) / 255.0
                    
                    # 检测场景边界
                    if diff_score > self.scene_threshold:
                        # 创建前一个场景
                        scene_end_time = current_time
                        scene_duration = scene_end_time - scene_start_time
                        
                        # 验证场景长度
                        if scene_duration >= self.min_scene_length:
                            scene = SceneInfo(
                                scene_id=scene_id,
                                start_time=scene_start_time,
                                end_time=scene_end_time,
                                start_frame=scene_start_frame,
                                end_frame=frame_index,
                                confidence=min(diff_score, 1.0),
                                is_boundary=True
                            )
                            scenes.append(scene)
                            scene_id += 1
                        
                        # 开始新场景
                        scene_start_frame = frame_index
                        scene_start_time = current_time
                
                prev_frame = gray_frame.copy()
                frame_index += 1
                
                # 处理超长场景
                current_scene_duration = current_time - scene_start_time
                if current_scene_duration > self.max_scene_length:
                    # 强制分割场景
                    scene = SceneInfo(
                        scene_id=scene_id,
                        start_time=scene_start_time,
                        end_time=current_time,
                        start_frame=scene_start_frame,
                        end_frame=frame_index,
                        confidence=0.5,  # 强制分割的置信度较低
                        is_boundary=False
                    )
                    scenes.append(scene)
                    scene_id += 1
                    
                    scene_start_frame = frame_index
                    scene_start_time = current_time
            
            # 添加最后一个场景
            if scene_start_time < metadata.duration:
                final_scene = SceneInfo(
                    scene_id=scene_id,
                    start_time=scene_start_time,
                    end_time=metadata.duration,
                    start_frame=scene_start_frame,
                    end_frame=metadata.frame_count,
                    confidence=1.0,
                    is_boundary=False
                )
                scenes.append(final_scene)
            
            cap.release()
            
            logger.info(f"场景检测完成: 检测到{len(scenes)}个场景")
            return scenes
            
        except Exception as e:
            logger.error(f"场景检测失败: {e}")
            # 返回单个场景作为备选
            return [SceneInfo(
                scene_id=0,
                start_time=0.0,
                end_time=metadata.duration,
                start_frame=0,
                end_frame=metadata.frame_count,
                confidence=1.0,
                is_boundary=False
            )]
    
    def _extract_keyframes(self, video_path: str, scenes: List[SceneInfo], 
                          metadata: VideoMetadata) -> List[KeyFrame]:
        """
        提取关键帧
        
        Args:
            video_path: 视频文件路径
            scenes: 场景信息列表
            metadata: 视频元数据
            
        Returns:
            关键帧列表
        """
        try:
            keyframes = []
            
            # 确定抽帧间隔
            if metadata.duration <= self.long_video_threshold:
                frame_interval_seconds = self.short_video_interval
            else:
                frame_interval_seconds = self.long_video_interval
            
            frame_interval = int(frame_interval_seconds * metadata.fps)
            
            logger.debug(f"开始关键帧提取: 间隔={frame_interval_seconds}秒 ({frame_interval}帧)")
            
            # 打开视频文件
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError(f"无法打开视频文件: {video_path}")
            
            frame_index = 0
            
            # 为每个场景提取关键帧
            for scene in scenes:
                scene_start_frame = scene.start_frame
                scene_end_frame = scene.end_frame
                
                # 场景边界帧(必须提取)
                if scene.is_boundary:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, scene_start_frame)
                    ret, frame = cap.read()
                    if ret:
                        # 调整帧大小为CLIP输入尺寸
                        resized_frame = cv2.resize(frame, self.clip_input_size)
                        resized_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)
                        
                        keyframe = KeyFrame(
                            frame_index=scene_start_frame,
                            timestamp=scene.start_time,
                            scene_id=scene.scene_id,
                            frame_data=resized_frame,
                            confidence=scene.confidence,
                            is_scene_boundary=True
                        )
                        keyframes.append(keyframe)
                
                # 场景内均匀采样
                current_frame = scene_start_frame + frame_interval
                while current_frame < scene_end_frame:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
                    ret, frame = cap.read()
                    if ret:
                        # 调整帧大小为CLIP输入尺寸
                        resized_frame = cv2.resize(frame, self.clip_input_size)
                        resized_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)
                        
                        timestamp = current_frame / metadata.fps
                        
                        keyframe = KeyFrame(
                            frame_index=current_frame,
                            timestamp=timestamp,
                            scene_id=scene.scene_id,
                            frame_data=resized_frame,
                            confidence=1.0,
                            is_scene_boundary=False
                        )
                        keyframes.append(keyframe)
                    
                    current_frame += frame_interval
            
            cap.release()
            
            # 按时间戳排序
            keyframes.sort(key=lambda x: x.timestamp)
            
            logger.info(f"关键帧提取完成: 提取{len(keyframes)}个关键帧")
            return keyframes
            
        except Exception as e:
            logger.error(f"关键帧提取失败: {e}")
            return []
    
    def _create_timestamp_infos(self, keyframes: List[KeyFrame], video_path: str) -> List[TimestampInfo]:
        """
        为关键帧创建时间戳信息
        
        Args:
            keyframes: 关键帧列表
            video_path: 视频文件路径
            
        Returns:
            时间戳信息列表
        """
        timestamp_infos = []
        
        for i, keyframe in enumerate(keyframes):
            # 计算时间段(当前帧到下一帧)
            if i < len(keyframes) - 1:
                end_time = keyframes[i + 1].timestamp
            else:
                # 最后一帧，假设持续2秒
                end_time = keyframe.timestamp + 2.0
            
            duration = end_time - keyframe.timestamp
            
            timestamp_info = TimestampInfo(
                file_id=video_path,
                segment_id=f"frame_{keyframe.frame_index}",
                modality=ModalityType.VISUAL,
                start_time=keyframe.timestamp,
                end_time=end_time,
                duration=duration,
                frame_index=keyframe.frame_index,
                vector_id=None,  # 将在向量化后设置
                confidence=keyframe.confidence,
                scene_boundary=keyframe.is_scene_boundary
            )
            
            timestamp_infos.append(timestamp_info)
        
        # 应用重叠时间窗口
        overlapping_timestamps = self.timestamp_processor.create_overlapping_time_windows(timestamp_infos)
        
        return overlapping_timestamps
    
    def _extract_audio_segments(self, video_path: str, scenes: List[SceneInfo]) -> List[Dict[str, Any]]:
        """
        提取音频段
        
        Args:
            video_path: 视频文件路径
            scenes: 场景信息列表
            
        Returns:
            音频段信息列表
        """
        try:
            audio_segments = []
            
            # 创建临时音频文件
            temp_dir = Path(video_path).parent / "temp_audio"
            temp_dir.mkdir(exist_ok=True)
            
            for scene in scenes:
                # 提取场景音频
                audio_output = temp_dir / f"scene_{scene.scene_id}_audio.wav"
                
                cmd = [
                    'ffmpeg',
                    '-i', video_path,
                    '-ss', str(scene.start_time),
                    '-t', str(scene.end_time - scene.start_time),
                    '-vn',  # 不要视频
                    '-acodec', 'pcm_s16le',
                    '-ar', '16000',  # 16kHz采样率
                    '-ac', '1',      # 单声道
                    '-y',
                    str(audio_output)
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0 and audio_output.exists():
                    # 创建音频时间戳信息
                    timestamp_info = TimestampInfo(
                        file_id=video_path,
                        segment_id=f"audio_scene_{scene.scene_id}",
                        modality=ModalityType.AUDIO_MUSIC,  # 默认为音乐，后续可通过分类器调整
                        start_time=scene.start_time,
                        end_time=scene.end_time,
                        duration=scene.end_time - scene.start_time,
                        frame_index=None,
                        vector_id=None,
                        confidence=scene.confidence,
                        scene_boundary=scene.is_boundary
                    )
                    
                    audio_segment = {
                        'scene_id': scene.scene_id,
                        'audio_path': str(audio_output),
                        'timestamp_info': timestamp_info,
                        'extracted': True
                    }
                    audio_segments.append(audio_segment)
                else:
                    logger.warning(f"音频提取失败: 场景{scene.scene_id}")
            
            logger.info(f"音频段提取完成: 提取{len(audio_segments)}个音频段")
            return audio_segments
            
        except Exception as e:
            logger.error(f"音频段提取失败: {e}")
            return []
    
    def _keyframe_to_dict(self, keyframe: KeyFrame) -> Dict[str, Any]:
        """
        将关键帧对象转换为字典(用于JSON序列化)
        
        Args:
            keyframe: 关键帧对象
            
        Returns:
            关键帧字典
        """
        return {
            'frame_index': keyframe.frame_index,
            'timestamp': keyframe.timestamp,
            'scene_id': keyframe.scene_id,
            'confidence': keyframe.confidence,
            'is_scene_boundary': keyframe.is_scene_boundary,
            'frame_shape': keyframe.frame_data.shape if keyframe.frame_data is not None else None
        }
    
    async def get_video_frame_at_timestamp(self, video_path: str, timestamp: float) -> Optional[np.ndarray]:
        """
        获取指定时间戳的视频帧
        
        Args:
            video_path: 视频文件路径
            timestamp: 时间戳(秒)
            
        Returns:
            视频帧数据或None
        """
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            
            frame = await loop.run_in_executor(None, self._get_frame_sync, video_path, timestamp)
            return frame
            
        except Exception as e:
            logger.error(f"获取视频帧失败: {video_path}@{timestamp}s, 错误: {e}")
            return None
    
    def _get_frame_sync(self, video_path: str, timestamp: float) -> Optional[np.ndarray]:
        """
        同步获取指定时间戳的视频帧
        
        Args:
            video_path: 视频文件路径
            timestamp: 时间戳(秒)
            
        Returns:
            视频帧数据或None
        """
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return None
            
            # 设置到指定时间戳
            cap.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
            
            ret, frame = cap.read()
            cap.release()
            
            if ret:
                # 调整为CLIP输入尺寸
                resized_frame = cv2.resize(frame, self.clip_input_size)
                resized_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)
                return resized_frame
            
            return None
            
        except Exception as e:
            logger.error(f"同步获取视频帧失败: {e}")
            return None
    
    def validate_processing_result(self, result: Dict[str, Any]) -> bool:
        """
        验证处理结果的完整性和正确性
        
        Args:
            result: 处理结果字典
            
        Returns:
            验证是否通过
        """
        try:
            if result.get('status') != 'success':
                return False
            
            # 验证必要字段
            required_fields = ['metadata', 'scenes', 'keyframes', 'video_timestamps']
            for field in required_fields:
                if field not in result:
                    logger.error(f"处理结果缺少必要字段: {field}")
                    return False
            
            # 验证时间戳精度
            video_timestamps = result.get('video_timestamps', [])
            for ts_dict in video_timestamps:
                duration = ts_dict.get('duration', 0)
                if not self.timestamp_processor.validate_timestamp_accuracy(0, duration):
                    logger.warning(f"时间戳精度不满足要求: {duration}s")
            
            # 验证场景和关键帧数量的合理性
            scenes_count = len(result.get('scenes', []))
            keyframes_count = len(result.get('keyframes', []))
            
            if keyframes_count == 0:
                logger.error("未提取到任何关键帧")
                return False
            
            if scenes_count == 0:
                logger.error("未检测到任何场景")
                return False
            
            logger.info(f"处理结果验证通过: 场景数={scenes_count}, 关键帧数={keyframes_count}")
            return True
            
        except Exception as e:
            logger.error(f"处理结果验证失败: {e}")
            return False
