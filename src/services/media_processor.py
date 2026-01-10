"""
媒体处理器
负责智能视频预处理、图像预处理、音频预处理
"""

import os
import subprocess
import json
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
import logging
import hashlib
from datetime import datetime
from PIL import Image
import numpy as np

logger = logging.getLogger(__name__)


class MediaProcessor:
    """媒体处理器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化媒体处理器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.processing_config = config.get('processing', {})
        
        # 缓存目录
        self.cache_dir = Path(config.get('system', {}).get('data_dir', 'data')) / 'cache'
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 缩略图目录
        self.thumbnail_dir = Path(config.get('system', {}).get('data_dir', 'data')) / 'thumbnails'
        self.thumbnail_dir.mkdir(parents=True, exist_ok=True)
    
    def has_media_value(self, file_path: str, file_type: str) -> bool:
        """
        判断媒体是否具有处理价值
        
        Args:
            file_path: 文件路径
            file_type: 文件类型
        
        Returns:
            是否具有价值
        """
        try:
            if file_type == 'audio':
                return self._has_audio_value(file_path)
            elif file_type == 'video':
                return self._has_video_value(file_path)
            else:
                return True  # 图像和文本始终有价值
        except Exception as e:
            logger.error(f"判断媒体价值失败: {file_path}, {e}")
            return False
    
    def _has_audio_value(self, audio_path: str) -> bool:
        """
        判断音频是否具有价值
        
        Args:
            audio_path: 音频文件路径
        
        Returns:
            是否具有价值
        """
        try:
            import librosa
            
            # 获取音频时长
            duration = librosa.get_duration(filename=audio_path)
            
            # 获取音频价值阈值
            value_threshold = self.processing_config.get('audio', {}).get('value_threshold', 5.0)
            
            # 判断时长
            return duration > value_threshold
        except Exception as e:
            logger.error(f"判断音频价值失败: {audio_path}, {e}")
            return False
    
    def _has_video_value(self, video_path: str) -> bool:
        """
        判断视频是否具有价值
        
        Args:
            video_path: 视频文件路径
        
        Returns:
            是否具有价值
        """
        try:
            # 获取视频时长
            duration = self._get_video_duration(video_path)
            
            # 视频始终有价值
            return duration > 0
        except Exception as e:
            logger.error(f"判断视频价值失败: {video_path}, {e}")
            return False
    
    def get_min_media_value_duration(self, media_type: str) -> float:
        """
        获取媒体最小价值时长
        
        Args:
            media_type: 媒体类型
        
        Returns:
            最小价值时长（秒）
        """
        if media_type == 'audio':
            return self.processing_config.get('audio', {}).get('value_threshold', 5.0)
        elif media_type == 'video':
            return 0.0  # 视频始终有价值
        else:
            return 0.0
    
    def is_short_video(self, video_path: str) -> bool:
        """
        判断是否为短视频
        
        Args:
            video_path: 视频文件路径
        
        Returns:
            是否为短视频
        """
        try:
            duration = self._get_video_duration(video_path)
            threshold = self.processing_config.get('video', {}).get('short_video', {}).get('threshold', 6.0)
            return duration <= threshold
        except Exception as e:
            logger.error(f"判断短视频失败: {video_path}, {e}")
            return False
    
    def process_image(self, image_path: str) -> Dict[str, Any]:
        """
        处理图像
        
        Args:
            image_path: 图像文件路径
        
        Returns:
            处理结果
        """
        try:
            # 获取图像信息
            image_info = self._get_image_info(image_path)
            
            # 预处理图像
            processed_path = self._preprocess_image(image_path)
            
            # 生成缩略图
            thumbnail_path = self._generate_thumbnail(image_path)
            
            return {
                'success': True,
                'original_path': image_path,
                'processed_path': processed_path,
                'thumbnail_path': thumbnail_path,
                'info': image_info
            }
        except Exception as e:
            logger.error(f"图像处理失败: {image_path}, {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def process_video(self, video_path: str) -> Dict[str, Any]:
        """
        处理视频
        
        Args:
            video_path: 视频文件路径
        
        Returns:
            处理结果
        """
        try:
            # 获取视频信息
            video_info = self._get_video_info(video_path)
            
            # 判断是否为短视频
            is_short = self.is_short_video(video_path)
            
            if is_short:
                # 短视频快速处理
                result = self._process_short_video(video_path, video_info)
            else:
                # 长视频切片处理
                result = self._process_long_video(video_path, video_info)
            
            return result
        except Exception as e:
            logger.error(f"视频处理失败: {video_path}, {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def process_audio(self, audio_path: str) -> Dict[str, Any]:
        """
        处理音频
        
        Args:
            audio_path: 音频文件路径
        
        Returns:
            处理结果
        """
        try:
            # 检查音频价值
            if not self._has_audio_value(audio_path):
                return {
                    'success': True,
                    'skipped': True,
                    'reason': 'audio_too_short',
                    'message': '音频时长≤5秒，跳过处理'
                }
            
            # 获取音频信息
            audio_info = self._get_audio_info(audio_path)
            
            # 预处理音频
            processed_path = self._preprocess_audio(audio_path)
            
            return {
                'success': True,
                'original_path': audio_path,
                'processed_path': processed_path,
                'info': audio_info
            }
        except Exception as e:
            logger.error(f"音频处理失败: {audio_path}, {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _process_short_video(self, video_path: str, video_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理短视频（≤6秒）
        
        Args:
            video_path: 视频文件路径
            video_info: 视频信息
        
        Returns:
            处理结果
        """
        try:
            duration = video_info['duration']
            short_config = self.processing_config.get('video', {}).get('short_video', {})
            
            # 提取帧数
            very_short_threshold = short_config.get('very_short_threshold', 2.0)
            short_segment_threshold = short_config.get('short_segment_threshold', 4.0)
            
            if duration <= very_short_threshold:
                # 极短视频：提取1帧
                num_frames = short_config.get('very_short_frames', 1)
            elif duration <= short_segment_threshold:
                # 短视频：提取2帧
                num_frames = short_config.get('short_frames', 2)
            else:
                # 中短视频：提取3帧
                num_frames = short_config.get('medium_short_frames', 3)
            
            # 提取帧
            frames = self._extract_frames(video_path, num_frames=num_frames)
            
            # 生成缩略图
            thumbnail_path = self._generate_video_thumbnail(video_path)
            
            return {
                'success': True,
                'is_short': True,
                'num_frames': num_frames,
                'frames': frames,
                'thumbnail_path': thumbnail_path,
                'info': video_info
            }
        except Exception as e:
            logger.error(f"短视频处理失败: {video_path}, {e}")
            raise
    
    def _process_long_video(self, video_path: str, video_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理长视频（>6秒）
        
        Args:
            video_path: 视频文件路径
            video_info: 视频信息
        
        Returns:
            处理结果
        """
        try:
            # 场景检测和切片
            segments = self._detect_video_scenes(video_path)
            
            # 生成缩略图
            thumbnail_path = self._generate_video_thumbnail(video_path)
            
            return {
                'success': True,
                'is_short': False,
                'segments': segments,
                'thumbnail_path': thumbnail_path,
                'info': video_info
            }
        except Exception as e:
            logger.error(f"长视频处理失败: {video_path}, {e}")
            raise
    
    def _get_image_info(self, image_path: str) -> Dict[str, Any]:
        """
        获取图像信息
        
        Args:
            image_path: 图像文件路径
        
        Returns:
            图像信息
        """
        try:
            with Image.open(image_path) as img:
                return {
                    'width': img.width,
                    'height': img.height,
                    'format': img.format,
                    'mode': img.mode,
                    'size': os.path.getsize(image_path)
                }
        except Exception as e:
            logger.error(f"获取图像信息失败: {image_path}, {e}")
            raise
    
    def _get_video_info(self, video_path: str) -> Dict[str, Any]:
        """
        获取视频信息
        
        Args:
            video_path: 视频文件路径
        
        Returns:
            视频信息
        """
        try:
            import cv2
            
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError(f"无法打开视频文件: {video_path}")
            
            # 获取视频信息
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            duration = frame_count / fps if fps > 0 else 0
            
            cap.release()
            
            return {
                'width': width,
                'height': height,
                'fps': fps,
                'frame_count': frame_count,
                'duration': duration,
                'size': os.path.getsize(video_path)
            }
        except Exception as e:
            logger.error(f"获取视频信息失败: {video_path}, {e}")
            raise
    
    def _get_audio_info(self, audio_path: str) -> Dict[str, Any]:
        """
        获取音频信息
        
        Args:
            audio_path: 音频文件路径
        
        Returns:
            音频信息
        """
        try:
            import librosa
            
            # 获取音频信息
            y, sr = librosa.load(audio_path, sr=None, duration=1.0)
            duration = librosa.get_duration(filename=audio_path)
            
            return {
                'sample_rate': sr,
                'channels': 1 if len(y.shape) == 1 else y.shape[0],
                'duration': duration,
                'size': os.path.getsize(audio_path)
            }
        except Exception as e:
            logger.error(f"获取音频信息失败: {audio_path}, {e}")
            raise
    
    def _preprocess_image(self, image_path: str) -> str:
        """
        预处理图像
        
        Args:
            image_path: 图像文件路径
        
        Returns:
            处理后的图像路径
        """
        try:
            # 计算文件哈希
            file_hash = self._calculate_file_hash(image_path)
            
            # 检查缓存
            cache_path = self.cache_dir / f"{file_hash}.jpg"
            if cache_path.exists():
                return str(cache_path)
            
            # 加载和预处理图像
            with Image.open(image_path) as img:
                # 转换为RGB
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # 调整大小
                max_resolution = self.processing_config.get('image', {}).get('max_resolution', 2048)
                if max(img.width, img.height) > max_resolution:
                    ratio = max_resolution / max(img.width, img.height)
                    new_size = (int(img.width * ratio), int(img.height * ratio))
                    img = img.resize(new_size, Image.LANCZOS)
                
                # 保存到缓存
                img.save(cache_path, 'JPEG', quality=85)
            
            return str(cache_path)
        except Exception as e:
            logger.error(f"图像预处理失败: {image_path}, {e}")
            raise
    
    def _preprocess_audio(self, audio_path: str) -> str:
        """
        预处理音频
        
        Args:
            audio_path: 音频文件路径
        
        Returns:
            处理后的音频路径
        """
        try:
            # 计算文件哈希
            file_hash = self._calculate_file_hash(audio_path)
            
            # 检查缓存
            cache_path = self.cache_dir / f"{file_hash}.wav"
            if cache_path.exists():
                return str(cache_path)
            
            # 加载和预处理音频
            import librosa
            
            audio_config = self.processing_config.get('audio', {})
            target_sample_rate = audio_config.get('sample_rate', 16000)
            target_channels = audio_config.get('channels', 1)
            
            # 加载音频
            y, sr = librosa.load(audio_path, sr=target_sample_rate, mono=(target_channels == 1))
            
            # 保存到缓存
            import soundfile as sf
            sf.write(cache_path, y, target_sample_rate)
            
            return str(cache_path)
        except Exception as e:
            logger.error(f"音频预处理失败: {audio_path}, {e}")
            raise
    
    def _detect_video_scenes(self, video_path: str) -> List[Dict[str, Any]]:
        """
        检测视频场景
        
        Args:
            video_path: 视频文件路径
        
        Returns:
            场景列表
        """
        try:
            # 使用FFmpeg进行场景检测
            max_duration = self.processing_config.get('video', {}).get('max_segment_duration', 5.0)
            scene_threshold = self.processing_config.get('video', {}).get('scene_threshold', 0.15)
            
            # 构建FFmpeg命令
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-vf', f'select=\'gt(scene,{scene_threshold})\',showinfo',
                '-f', 'null',
                '-'
            ]
            
            # 执行命令
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # 解析场景信息
            segments = self._parse_scene_info(result.stderr, video_path, max_duration)
            
            return segments
        except Exception as e:
            logger.error(f"场景检测失败: {video_path}, {e}")
            raise
    
    def _parse_scene_info(self, scene_info: str, video_path: str, max_duration: float) -> List[Dict[str, Any]]:
        """
        解析场景信息
        
        Args:
            scene_info: FFmpeg输出
            video_path: 视频文件路径
            max_duration: 最大切片时长
        
        Returns:
            场景列表
        """
        try:
            import re
            
            segments = []
            current_time = 0.0
            
            # 解析场景变化点
            pattern = r'pts_time:(\d+\.\d+)'
            matches = re.findall(pattern, scene_info)
            
            for match in matches:
                time = float(match)
                if time - current_time > max_duration:
                    segments.append({
                        'start_time': current_time,
                        'end_time': time,
                        'duration': time - current_time
                    })
                    current_time = time
            
            # 添加最后一个场景
            video_info = self._get_video_info(video_path)
            if current_time < video_info['duration']:
                segments.append({
                    'start_time': current_time,
                    'end_time': video_info['duration'],
                    'duration': video_info['duration'] - current_time
                })
            
            return segments
        except Exception as e:
            logger.error(f"解析场景信息失败: {e}")
            raise
    
    def _extract_frames(self, video_path: str, num_frames: int = 1) -> List[str]:
        """
        提取视频帧
        
        Args:
            video_path: 视频文件路径
            num_frames: 提取帧数
        
        Returns:
            帧文件路径列表
        """
        try:
            import cv2
            
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError(f"无法打开视频文件: {video_path}")
            
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # 计算帧间隔
            if num_frames == 1:
                frame_indices = [total_frames // 2]
            else:
                frame_indices = [int(i * total_frames / (num_frames + 1)) for i in range(1, num_frames + 1)]
            
            frames = []
            for frame_idx in frame_indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                if ret:
                    # 保存帧
                    frame_hash = self._calculate_file_hash(video_path)
                    frame_path = self.cache_dir / f"{frame_hash}_frame_{frame_idx}.jpg"
                    cv2.imwrite(str(frame_path), frame)
                    frames.append(str(frame_path))
            
            cap.release()
            return frames
        except Exception as e:
            logger.error(f"提取视频帧失败: {video_path}, {e}")
            raise
    
    def _generate_thumbnail(self, image_path: str) -> str:
        """
        生成图像缩略图
        
        Args:
            image_path: 图像文件路径
        
        Returns:
            缩略图路径
        """
        try:
            # 计算文件哈希
            file_hash = self._calculate_file_hash(image_path)
            
            # 缩略图路径
            thumbnail_path = self.thumbnail_dir / f"{file_hash}.jpg"
            
            # 检查是否已存在
            if thumbnail_path.exists():
                return str(thumbnail_path)
            
            # 生成缩略图
            thumbnail_size = self.processing_config.get('video', {}).get('thumbnail', {}).get('size', 256)
            
            with Image.open(image_path) as img:
                # 转换为RGB
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # 调整大小
                img.thumbnail((thumbnail_size, thumbnail_size), Image.LANCZOS)
                
                # 保存缩略图
                img.save(thumbnail_path, 'JPEG', quality=85)
            
            return str(thumbnail_path)
        except Exception as e:
            logger.error(f"生成图像缩略图失败: {image_path}, {e}")
            raise
    
    def _generate_video_thumbnail(self, video_path: str) -> str:
        """
        生成视频缩略图
        
        Args:
            video_path: 视频文件路径
        
        Returns:
            缩略图路径
        """
        try:
            # 计算文件哈希
            file_hash = self._calculate_file_hash(video_path)
            
            # 缩略图路径
            thumbnail_path = self.thumbnail_dir / f"{file_hash}.jpg"
            
            # 检查是否已存在
            if thumbnail_path.exists():
                return str(thumbnail_path)
            
            # 使用FFmpeg提取缩略图
            thumbnail_size = self.processing_config.get('video', {}).get('thumbnail', {}).get('size', 256)
            time_offset = self.processing_config.get('video', {}).get('thumbnail', {}).get('time_offset', 0.3)
            
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-ss', str(time_offset),
                '-vframes', '1',
                '-vf', f'scale={thumbnail_size}:{thumbnail_size}',
                '-q:v', '2',
                '-y',
                str(thumbnail_path)
            ]
            
            subprocess.run(cmd, capture_output=True, check=True)
            
            return str(thumbnail_path)
        except Exception as e:
            logger.error(f"生成视频缩略图失败: {video_path}, {e}")
            raise
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """
        计算文件哈希（SHA256）
        
        Args:
            file_path: 文件路径
        
        Returns:
            文件哈希（前16位）
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()[:16]
