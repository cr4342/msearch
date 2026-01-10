import os
import sys
import logging
import time
from typing import Dict, Any, List, Optional
from pathlib import Path

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MediaProcessor:
    """
    媒体处理器
    
    负责处理不同类型的媒体文件
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化媒体处理器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.supported_media_types = {
            'image': ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'],
            'video': ['mp4', 'avi', 'mkv', 'mov', 'wmv', 'flv'],
            'audio': ['mp3', 'wav', 'ogg', 'flac', 'aac'],
            'text': ['txt', 'md', 'json', 'yaml', 'yml']
        }
        
        # 媒体价值阈值配置
        self.min_media_value_duration = {
            'audio': 5.0,  # 音频超过5秒才有价值
            'video': 0.0   # 视频无最小价值时长限制
        }
        
        logger.info("MediaProcessor initialized")
    
    def initialize(self) -> bool:
        """
        初始化媒体处理器
        
        Returns:
            是否初始化成功
        """
        try:
            logger.info("MediaProcessor initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize MediaProcessor: {e}")
            return False
    
    def has_media_value(self, file_path: str) -> bool:
        """
        判断媒体文件是否有价值
        
        Args:
            file_path: 文件路径
        
        Returns:
            是否有价值
        """
        try:
            # 获取文件类型
            media_type, ext = self.get_media_type(file_path)
            if not media_type:
                return False
            
            # 根据媒体类型判断是否有价值
            if media_type == 'audio':
                # 音频需要超过5秒才有价值
                duration = self.get_media_duration(file_path)
                min_duration = self.min_media_value_duration.get(media_type, 0.0)
                return duration >= min_duration
            elif media_type == 'video':
                # 视频无最小价值时长限制
                return True
            elif media_type == 'image':
                # 图像都有价值
                return True
            elif media_type == 'text':
                # 文本需要有内容
                return os.path.getsize(file_path) > 0
            
            return False
        except Exception as e:
            logger.error(f"Failed to check media value: {e}")
            return False
    
    def get_min_media_value_duration(self, media_type: str) -> float:
        """
        获取媒体类型的最小价值时长
        
        Args:
            media_type: 媒体类型
        
        Returns:
            最小价值时长
        """
        return self.min_media_value_duration.get(media_type, 0.0)
    
    def process_file(self, file_path: str) -> Dict[str, Any]:
        """
        处理媒体文件
        
        Args:
            file_path: 文件路径
        
        Returns:
            处理结果
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                return {
                    'status': 'error',
                    'error': f"File not found: {file_path}",
                    'file_path': file_path
                }
            
            # 检查文件是否有价值
            if not self.has_media_value(file_path):
                logger.info(f"File has no media value: {file_path}")
                return {
                    'status': 'skipped',
                    'reason': 'no_media_value',
                    'file_path': file_path
                }
            
            # 获取媒体类型
            media_type, ext = self.get_media_type(file_path)
            if not media_type:
                logger.error(f"Unsupported media type: {file_path}")
                return {
                    'status': 'error',
                    'error': f"Unsupported media type: {file_path}",
                    'file_path': file_path
                }
            
            # 根据媒体类型调用相应的处理方法
            if media_type == 'image':
                return self.process_image(file_path)
            elif media_type == 'video':
                return self.process_video(file_path)
            elif media_type == 'audio':
                return self.process_audio(file_path)
            elif media_type == 'text':
                return self.process_text(file_path)
            
            return {
                'status': 'error',
                'error': f"Unknown media type: {media_type}",
                'file_path': file_path
            }
        except Exception as e:
            logger.error(f"Failed to process file: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'file_path': file_path
            }
    
    def process_image(self, image_path: str) -> Dict[str, Any]:
        """
        处理图像文件
        
        Args:
            image_path: 图像文件路径
        
        Returns:
            处理结果
        """
        logger.info(f"Processing image: {image_path}")
        
        try:
            # 获取图像信息
            image_info = self.get_media_info(image_path)
            
            # 简化实现：返回图像信息
            return {
                'status': 'success',
                'file_path': image_path,
                'media_type': 'image',
                'metadata': image_info,
                'processed_at': time.time()
            }
        except Exception as e:
            logger.error(f"Failed to process image: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'file_path': image_path
            }
    
    def process_video(self, video_path: str) -> Dict[str, Any]:
        """
        处理视频文件
        
        Args:
            video_path: 视频文件路径
        
        Returns:
            处理结果
        """
        logger.info(f"Processing video: {video_path}")
        
        try:
            # 获取视频信息
            video_info = self.get_media_info(video_path)
            duration = video_info.get('duration', 0.0)
            
            # 确定视频是否为短视频
            is_short_video = duration <= 6.0
            
            # 处理视频：提取关键帧和分段
            segments = self._extract_video_segments(video_path, is_short_video)
            
            return {
                'status': 'success',
                'file_path': video_path,
                'media_type': 'video',
                'metadata': video_info,
                'is_short_video': is_short_video,
                'segments': segments,
                'processed_at': time.time()
            }
        except Exception as e:
            logger.error(f"Failed to process video: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'file_path': video_path
            }
    
    def _extract_video_segments(self, video_path: str, is_short_video: bool) -> List[Dict[str, Any]]:
        """
        提取视频分段
        
        Args:
            video_path: 视频文件路径
            is_short_video: 是否为短视频
        
        Returns:
            分段结果
        """
        try:
            # 获取视频信息
            video_info = self.get_media_info(video_path)
            duration = video_info.get('duration', 0.0)
            
            segments = []
            
            if is_short_video:
                # 短视频：统一使用segment_id="full"
                segments.append({
                    'segment_id': 'full',
                    'start_time': 0.0,
                    'end_time': duration,
                    'duration': duration,
                    'is_short_segment': True
                })
            else:
                # 长视频：按5秒分段
                segment_duration = 5.0
                num_segments = max(1, int(duration / segment_duration))
                
                for i in range(num_segments):
                    start_time = i * segment_duration
                    end_time = min((i + 1) * segment_duration, duration)
                    
                    segments.append({
                        'segment_id': f'segment_{i}',
                        'start_time': start_time,
                        'end_time': end_time,
                        'duration': end_time - start_time,
                        'is_short_segment': False
                    })
            
            return segments
        except Exception as e:
            logger.error(f"Failed to extract video segments: {e}")
            return []
    
    def process_audio(self, audio_path: str) -> Dict[str, Any]:
        """
        处理音频文件
        
        Args:
            audio_path: 音频文件路径
        
        Returns:
            处理结果
        """
        logger.info(f"Processing audio: {audio_path}")
        
        try:
            # 检查音频是否有价值
            if not self.has_media_value(audio_path):
                return {
                    'status': 'skipped',
                    'reason': 'audio_too_short',
                    'file_path': audio_path
                }
            
            # 获取音频信息
            audio_info = self.get_media_info(audio_path)
            
            return {
                'status': 'success',
                'file_path': audio_path,
                'media_type': 'audio',
                'metadata': audio_info,
                'processed_at': time.time()
            }
        except Exception as e:
            logger.error(f"Failed to process audio: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'file_path': audio_path
            }
    
    def process_text(self, text_path: str) -> Dict[str, Any]:
        """
        处理文本文件
        
        Args:
            text_path: 文本文件路径
        
        Returns:
            处理结果
        """
        logger.info(f"Processing text: {text_path}")
        
        try:
            # 获取文本内容
            with open(text_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return {
                'status': 'success',
                'file_path': text_path,
                'media_type': 'text',
                'content': content,
                'length': len(content),
                'processed_at': time.time()
            }
        except Exception as e:
            logger.error(f"Failed to process text: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'file_path': text_path
            }
    
    def get_media_type(self, file_path: str) -> Tuple[Optional[str], str]:
        """
        获取文件的媒体类型
        
        Args:
            file_path: 文件路径
        
        Returns:
            (媒体类型, 文件扩展名)
        """
        try:
            # 获取文件扩展名
            ext = Path(file_path).suffix.lower()[1:]  # 去掉点
            
            # 判断媒体类型
            for media_type, exts in self.supported_media_types.items():
                if ext in exts:
                    return media_type, ext
            
            return None, ext
        except Exception as e:
            logger.error(f"Failed to get media type: {e}")
            return None, ''
    
    def get_media_info(self, file_path: str) -> Dict[str, Any]:
        """
        获取媒体文件信息
        
        Args:
            file_path: 文件路径
        
        Returns:
            媒体信息
        """
        try:
            # 基本文件信息
            file_stats = os.stat(file_path)
            
            # 获取媒体类型
            media_type, ext = self.get_media_type(file_path)
            
            # 简化实现：返回基本信息
            media_info = {
                'file_path': file_path,
                'file_name': Path(file_path).name,
                'file_size': file_stats.st_size,
                'media_type': media_type,
                'extension': ext,
                'created_at': file_stats.st_ctime,
                'modified_at': file_stats.st_mtime
            }
            
            # 添加媒体特定信息
            if media_type in ['audio', 'video']:
                media_info['duration'] = self.get_media_duration(file_path)
            
            return media_info
        except Exception as e:
            logger.error(f"Failed to get media info: {e}")
            return {}
    
    def get_media_duration(self, file_path: str) -> float:
        """
        获取媒体文件时长
        
        Args:
            file_path: 文件路径
        
        Returns:
            媒体时长（秒）
        """
        try:
            # 简化实现：返回随机时长
            # 实际实现时需要使用ffmpeg或其他库获取真实时长
            import random
            return random.uniform(0.1, 300.0)
        except Exception as e:
            logger.error(f"Failed to get media duration: {e}")
            return 0.0
    
    def get_supported_media_types(self) -> List[str]:
        """
        获取支持的媒体类型
        
        Returns:
            支持的媒体类型列表
        """
        return list(self.supported_media_types.keys())
    
    def is_supported_media_type(self, file_path: str) -> bool:
        """
        判断是否支持该媒体类型
        
        Args:
            file_path: 文件路径
        
        Returns:
            是否支持
        """
        media_type, _ = self.get_media_type(file_path)
        return media_type is not None
    
    def get_processing_time(self, file_path: str) -> float:
        """
        获取处理时间（模拟）
        
        Args:
            file_path: 文件路径
        
        Returns:
            处理时间
        """
        try:
            # 模拟处理时间：根据文件大小和类型计算
            file_size = os.path.getsize(file_path)
            media_type, _ = self.get_media_type(file_path)
            
            # 处理时间系数（秒/MB）
            time_coefficients = {
                'image': 0.001,
                'video': 0.01,
                'audio': 0.005,
                'text': 0.0001
            }
            
            coefficient = time_coefficients.get(media_type, 0.001)
            processing_time = (file_size / (1024 * 1024)) * coefficient
            
            return max(0.1, processing_time)  # 最小处理时间0.1秒
        except Exception as e:
            logger.error(f"Failed to estimate processing time: {e}")
            return 1.0


# 初始化函数
def create_media_processor(config: Dict[str, Any]) -> MediaProcessor:
    """
    创建媒体处理器实例
    
    Args:
        config: 配置字典
    
    Returns:
        MediaProcessor实例
    """
    media_processor = MediaProcessor(config)
    if not media_processor.initialize():
        logger.error("Failed to create MediaProcessor")
        raise RuntimeError("Failed to create MediaProcessor")
    
    return media_processor
