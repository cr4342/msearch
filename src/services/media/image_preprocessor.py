import os
import sys
import logging
import time
from typing import Dict, Any
from pathlib import Path

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 导入媒体处理通用工具
from src.services.media.media_utils import MediaInfoHelper, calculate_file_hash


class ImagePreprocessor:
    """图像处理器类"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化图像处理器
        
        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.media_info_helper = MediaInfoHelper()
        
        logger.info("ImagePreprocessor initialized")
    
    def initialize(self) -> bool:
        """
        初始化图像处理器
        
        Returns:
            是否初始化成功
        """
        try:
            logger.info("ImagePreprocessor initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize ImagePreprocessor: {e}")
            return False
    
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
            image_info = self.media_info_helper.get_media_info(image_path)
            
            # 返回图像处理结果
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
    

    
    def has_media_value(self, file_path: str) -> bool:
        """
        判断图像文件是否有价值
        
        Args:
            file_path: 文件路径
        
        Returns:
            是否有价值
        """
        return self.media_info_helper.has_media_value(file_path)
    
    def get_media_info(self, file_path: str) -> Dict[str, Any]:
        """
        获取图像媒体信息
        
        Args:
            file_path: 文件路径
        
        Returns:
            媒体信息
        """
        return self.media_info_helper.get_media_info(file_path)
    
    def calculate_hash(self, file_path: str) -> str:
        """
        计算文件哈希值
        
        Args:
            file_path: 文件路径
        
        Returns:
            文件哈希值
        """
        return calculate_file_hash(file_path)