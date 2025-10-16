"""
媒体预处理器 - 执行所有媒体文件的格式转换、质量优化和内容分析
"""
import os
from typing import Dict, Any
import logging
from src.processors.image_processor import ImageProcessor
from src.processors.video_processor import VideoProcessor
from src.processors.audio_processor import AudioProcessor
from src.processors.text_processor import TextProcessor
from src.processors.audio_classifier import AudioClassifier

logger = logging.getLogger(__name__)


class MediaProcessor:
    """媒体预处理器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化媒体预处理器
        
        Args:
            config: 配置字典
        """
        self.config = config
        
        # 初始化各个专业处理器
        self.image_processor = ImageProcessor(config)
        self.video_processor = VideoProcessor(config)
        self.audio_processor = AudioProcessor(config)
        self.text_processor = TextProcessor(config)
        self.audio_classifier = AudioClassifier()
        
        logger.info("媒体预处理器初始化完成")
    
    async def process_file(self, file_path: str, file_type: str) -> Dict[str, Any]:
        """
        处理文件
        
        Args:
            file_path: 文件路径
            file_type: 文件类型
            
        Returns:
            处理结果字典
        """
        try:
            logger.info(f"开始处理文件: {file_path}, 类型: {file_type}")
            
            # 根据文件类型选择相应的处理器
            if file_type == 'image':
                result = await self.image_processor.process_image(file_path)
            elif file_type == 'video':
                result = await self.video_processor.process_video(file_path)
            elif file_type == 'audio':
                result = await self.audio_processor.process_audio(file_path)
            elif file_type == 'text':
                result = await self.text_processor.process_text(file_path)
            else:
                raise ValueError(f"不支持的文件类型: {file_type}")
            
            logger.info(f"文件处理完成: {file_path}")
            
            return {
                'status': 'success',
                'file_path': file_path,
                'file_type': file_type,
                'result': result
            }
            
        except Exception as e:
            logger.error(f"文件处理失败: {file_path}, 错误: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'file_path': file_path,
                'file_type': file_type
            }
    
    async def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        提取文件元数据
        
        Args:
            file_path: 文件路径
            
        Returns:
            元数据字典
        """
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"文件不存在: {file_path}")
            
            # 获取基本文件信息
            stat = os.stat(file_path)
            
            metadata = {
                'file_path': file_path,
                'file_size': stat.st_size,
                'created_time': stat.st_ctime,
                'modified_time': stat.st_mtime,
                'access_time': stat.st_atime
            }
            
            logger.debug(f"提取文件元数据: {file_path}")
            return metadata
            
        except Exception as e:
            logger.error(f"提取元数据失败: {file_path}, 错误: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'file_path': file_path
            }


# 示例使用
if __name__ == "__main__":
    import asyncio
    
    # 配置示例
    config = {
        'processing': {
            'image': {
                'target_size': 224,
                'max_resolution': (1920, 1080),
                'quality_threshold': 0.5
            },
            'video': {
                'target_size': 224,
                'max_resolution': (1280, 720),
                'scene_threshold': 0.3,
                'frame_interval': 2.0
            },
            'audio': {
                'target_sample_rate': 16000,
                'target_channels': 1,
                'segment_duration': 10.0,
                'quality_threshold': 0.5
            },
            'text': {
                'max_file_size': 10 * 1024 * 1024,
                'encoding_priority': ['utf-8', 'gbk', 'gb2312', 'latin-1']
            }
        }
    }
    
    # 创建处理器实例
    # processor = MediaProcessor(config)
    
    # 处理文件 (需要实际的文件路径)
    # result = asyncio.run(processor.process_file("path/to/file.jpg", "image"))
    # print(result)