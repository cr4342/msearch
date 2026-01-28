import os
import sys
import logging
import time
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def calculate_file_hash(file_path: str) -> str:
    """
    计算文件的SHA256哈希值
    
    Args:
        file_path: 文件路径
    
    Returns:
        文件的SHA256哈希值
    """
    try:
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Error calculating file hash: {file_path}, {e}")
        return ""


def check_duplicate_file(file_path: str, existing_hashes: Dict[str, Dict[str, Any]]) -> Optional[str]:
    """
    检查文件是否重复
    
    Args:
        file_path: 文件路径
        existing_hashes: 已存在的文件哈希字典 {hash: {file_path, vector_id, ...}}
    
    Returns:
        如果文件重复，返回已存在的文件路径；否则返回None
    """
    try:
        # 计算文件哈希
        file_hash = calculate_file_hash(file_path)
        if not file_hash:
            return None
        
        # 检查是否存在于已知的哈希中
        if file_hash in existing_hashes:
            existing_file_info = existing_hashes[file_hash]
            existing_file_path = existing_file_info.get('file_path')
            logger.info(f"Duplicate file detected: {file_path} -> {existing_file_path}")
            return existing_file_path
        
        return None
    
    except Exception as e:
        logger.error(f"Error checking duplicate file: {file_path}, {e}")
        return None


class MediaInfoHelper:
    """媒体信息帮助类"""
    
    def __init__(self):
        self.supported_media_types = {
            'image': ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'],
            'video': ['mp4', 'avi', 'mkv', 'mov', 'wmv', 'flv'],
            'audio': ['mp3', 'wav', 'ogg', 'flac', 'aac'],
            'text': ['txt', 'md', 'json', 'yaml', 'yml']
        }
        
        # 媒体价值阈值配置
        self.min_media_value_duration = {
            'audio': 3.0,  # 音频超过3秒才有价值
            'video': 0.0   # 视频无最小价值时长限制
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
            
            # 返回基本信息
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
            # 模拟实现：返回随机时长
            # 实际实现时需要使用ffmpeg或其他库获取真实时长
            import random
            return random.uniform(0.1, 300.0)
        except Exception as e:
            logger.error(f"Failed to get media duration: {e}")
            return 0.0
    
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
                # 音频需要超过最小价值时长才有价值
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