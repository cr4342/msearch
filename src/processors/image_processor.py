"""
图片处理器 - 处理图片文件的格式转换和尺寸标准化
"""
import os
from typing import Dict, Any
import cv2
import numpy as np
from PIL import Image
import logging

logger = logging.getLogger(__name__)


class ImageProcessor:
    """图片处理器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化图片处理器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.target_size = config.get('processing.image.target_size', 224)  # CLIP模型标准输入尺寸
        self.max_resolution = config.get('processing.image.max_resolution', (1920, 1080))
        self.quality_threshold = config.get('processing.image.quality_threshold', 0.5)
    
    async def process_image(self, image_path: str) -> Dict[str, Any]:
        """
        处理图片文件
        
        Args:
            image_path: 图片文件路径
            
        Returns:
            处理结果字典
        """
        try:
            logger.debug(f"开始处理图片: {image_path}")
            
            # 1. 读取图片
            image_data = self._read_image(image_path)
            
            # 2. 格式验证和转换
            validated_image = self._validate_and_convert(image_data)
            
            # 3. 尺寸调整
            resized_image = self._resize_image(validated_image)
            
            # 4. 质量评估
            quality_score = self._assess_quality(resized_image)
            
            # 5. 标准化处理
            normalized_image = self._normalize_image(resized_image)
            
            logger.debug(f"图片处理完成: {image_path}, 质量评分: {quality_score}")
            
            return {
                'status': 'success',
                'image_data': normalized_image,
                'original_size': image_data.shape[:2],
                'processed_size': normalized_image.shape[:2],
                'quality_score': quality_score,
                'file_path': image_path
            }
            
        except Exception as e:
            logger.error(f"图片处理失败: {image_path}, 错误: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'file_path': image_path
            }
    
    def _read_image(self, image_path: str) -> np.ndarray:
        """
        读取图片文件
        
        Args:
            image_path: 图片文件路径
            
        Returns:
            图片数据 (BGR格式)
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"图片文件不存在: {image_path}")
        
        # 使用OpenCV读取图片
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"无法读取图片文件: {image_path}")
        
        return image
    
    def _validate_and_convert(self, image: np.ndarray) -> np.ndarray:
        """
        验证和转换图片格式
        
        Args:
            image: 原始图片数据
            
        Returns:
            转换后的图片数据
        """
        # 确保图片有3个通道
        if len(image.shape) == 2:
            # 灰度图转RGB
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        elif len(image.shape) == 3 and image.shape[2] == 4:
            # RGBA转RGB
            image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
        
        return image
    
    def _resize_image(self, image: np.ndarray) -> np.ndarray:
        """
        调整图片尺寸
        
        Args:
            image: 原始图片数据
            
        Returns:
            调整尺寸后的图片数据
        """
        height, width = image.shape[:2]
        max_width, max_height = self.max_resolution
        
        # 如果图片尺寸超过最大分辨率，先降采样
        if width > max_width or height > max_height:
            # 计算缩放比例
            scale_x = max_width / width
            scale_y = max_height / height
            scale = min(scale_x, scale_y)
            
            new_width = int(width * scale)
            new_height = int(height * scale)
            
            # 使用OpenCV调整尺寸
            image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
        
        return image
    
    def _assess_quality(self, image: np.ndarray) -> float:
        """
        评估图片质量
        
        Args:
            image: 图片数据
            
        Returns:
            质量评分 (0-1)
        """
        # 简单的质量评估：基于图像清晰度
        # 使用拉普拉斯算子计算图像梯度
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # 将方差转换为0-1的质量评分
        # 假设方差大于1000表示高质量图片
        quality_score = min(laplacian_var / 1000.0, 1.0)
        
        return quality_score
    
    def _normalize_image(self, image: np.ndarray) -> np.ndarray:
        """
        标准化图片数据
        
        Args:
            image: 图片数据
            
        Returns:
            标准化后的图片数据
        """
        # 调整到目标尺寸 (224x224)
        resized = cv2.resize(image, (self.target_size, self.target_size), interpolation=cv2.INTER_LINEAR)
        
        # 转换为RGB格式
        rgb_image = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        
        # 归一化到[0, 1]范围
        normalized = rgb_image.astype(np.float32) / 255.0
        
        return normalized


# 示例使用
if __name__ == "__main__":
    # 配置示例
    config = {
        'processing.image.target_size': 224,
        'processing.image.max_resolution': (1920, 1080),
        'processing.image.quality_threshold': 0.5
    }
    
    # 创建处理器实例
    processor = ImageProcessor(config)
    
    # 处理图片 (需要实际的图片文件路径)
    # result = processor.process_image("path/to/image.jpg")
    # print(result)