import os
import sys
import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 导入独立的媒体处理器
from src.services.media.image_preprocessor import ImagePreprocessor
from src.services.media.video_preprocessor import VideoPreprocessor
from src.services.media.audio_preprocessor import AudioPreprocessor
from src.services.media.media_utils import (
    MediaInfoHelper,
    calculate_file_hash,
    check_duplicate_file,
)


class MediaProcessor:
    """
    媒体处理器类

    整合多个独立的媒体处理器，提供统一的媒体处理接口
    """

    def __init__(self, config: Dict[str, Any] = None, thumbnail_generator=None):
        """
        初始化媒体处理器

        Args:
            config: 配置字典
            thumbnail_generator: 缩略图生成器（可选）
        """
        self.config = config or {}
        self.thumbnail_generator = thumbnail_generator

        # 初始化独立的媒体处理器
        self.image_preprocessor = ImagePreprocessor(config)
        self.video_preprocessor = VideoPreprocessor(config)
        self.audio_preprocessor = AudioPreprocessor(config)

        # 初始化媒体信息帮助类
        self.media_info_helper = MediaInfoHelper(self.config)

        # 文件哈希缓存（用于重复检测）
        self.file_hash_cache: Dict[str, str] = {}

        logger.info("MediaProcessor initialized")

    def initialize(self) -> bool:
        """
        初始化媒体处理器

        Returns:
            是否初始化成功
        """
        try:
            # 初始化所有独立处理器
            image_init = self.image_preprocessor.initialize()
            video_init = self.video_preprocessor.initialize()
            audio_init = self.audio_preprocessor.initialize()

            if not all([image_init, video_init, audio_init]):
                logger.error("Failed to initialize all media processors")
                return False

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
        return self.media_info_helper.has_media_value(file_path)

    def get_min_media_value_duration(self, media_type: str) -> float:
        """
        获取媒体类型的最小价值时长

        Args:
            media_type: 媒体类型

        Returns:
            最小价值时长
        """
        return self.media_info_helper.get_min_media_value_duration(media_type)

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
                    "status": "error",
                    "error": f"File not found: {file_path}",
                    "file_path": file_path,
                }

            # 计算文件哈希（用于重复检测）
            file_hash = calculate_file_hash(file_path)

            # 缓存文件哈希
            self.file_hash_cache[file_path] = file_hash

            # 检查文件是否有价值
            if not self.has_media_value(file_path):
                logger.info(f"File has no media value: {file_path}")
                return {
                    "status": "skipped",
                    "reason": "no_media_value",
                    "file_path": file_path,
                    "hash": file_hash,
                }

            # 获取媒体类型
            media_type, ext = self.media_info_helper.get_media_type(file_path)
            if not media_type:
                logger.error(f"Unsupported media type: {file_path}")
                return {
                    "status": "error",
                    "error": f"Unsupported media type: {file_path}",
                    "file_path": file_path,
                    "hash": file_hash,
                }

            # 根据媒体类型调用相应的处理方法
            if media_type == "image":
                return self.process_image(file_path)
            elif media_type == "video":
                return self.process_video(file_path)
            elif media_type == "audio":
                return self.process_audio(file_path)
            elif media_type == "text":
                return self.process_text(file_path)

            return {
                "status": "error",
                "error": f"Unknown media type: {media_type}",
                "file_path": file_path,
                "hash": file_hash,
            }
        except Exception as e:
            logger.error(f"Failed to process file: {e}")
            return {"status": "error", "error": str(e), "file_path": file_path}

    def _calculate_file_hash(self, file_path: str) -> str:
        """
        计算文件的SHA256哈希值

        Args:
            file_path: 文件路径

        Returns:
            文件的SHA256哈希值
        """
        return calculate_file_hash(file_path)

    def check_duplicate_file(
        self, file_path: str, existing_hashes: Dict[str, Dict[str, Any]]
    ) -> Optional[str]:
        """
        检查文件是否重复

        Args:
            file_path: 文件路径
            existing_hashes: 已存在的文件哈希字典 {hash: {file_path, vector_id, ...}}

        Returns:
            如果文件重复，返回已存在的文件路径；否则返回None
        """
        return check_duplicate_file(file_path, existing_hashes)

    def process_image(self, image_path: str) -> Dict[str, Any]:
        """
        处理图像文件

        Args:
            image_path: 图像文件路径

        Returns:
            处理结果
        """
        return self.image_preprocessor.process_image(image_path)

    def process_video(self, video_path: str) -> Dict[str, Any]:
        """
        处理视频文件

        Args:
            video_path: 视频文件路径

        Returns:
            处理结果
        """
        return self.video_preprocessor.process_video(video_path)

    def process_audio(self, audio_path: str) -> Dict[str, Any]:
        """
        处理音频文件

        Args:
            audio_path: 音频文件路径

        Returns:
            处理结果
        """
        return self.audio_preprocessor.process_audio(audio_path)

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
            with open(text_path, "r", encoding="utf-8") as f:
                content = f.read()

            return {
                "status": "success",
                "file_path": text_path,
                "media_type": "text",
                "content": content,
                "length": len(content),
                "processed_at": time.time(),
            }
        except Exception as e:
            logger.error(f"Failed to process text: {e}")
            return {"status": "error", "error": str(e), "file_path": text_path}

    def get_media_type(self, file_path: str) -> Tuple[Optional[str], str]:
        """
        获取文件的媒体类型

        Args:
            file_path: 文件路径

        Returns:
            (媒体类型, 文件扩展名)
        """
        return self.media_info_helper.get_media_type(file_path)

    def get_media_info(self, file_path: str) -> Dict[str, Any]:
        """
        获取媒体文件信息

        Args:
            file_path: 文件路径

        Returns:
            媒体信息
        """
        return self.media_info_helper.get_media_info(file_path)

    def get_media_duration(self, file_path: str) -> float:
        """
        获取媒体文件时长

        Args:
            file_path: 文件路径

        Returns:
            媒体时长（秒）
        """
        return self.media_info_helper.get_media_duration(file_path)

    def get_supported_media_types(self) -> List[str]:
        """
        获取支持的媒体类型

        Returns:
            支持的媒体类型列表
        """
        return self.media_info_helper.get_supported_media_types()

    def is_supported_media_type(self, file_path: str) -> bool:
        """
        判断是否支持该媒体类型

        Args:
            file_path: 文件路径

        Returns:
            是否支持
        """
        return self.media_info_helper.is_supported_media_type(file_path)

    def get_processing_time(self, file_path: str) -> float:
        """
        获取处理时间（模拟）

        Args:
            file_path: 文件路径

        Returns:
            处理时间
        """
        return self.media_info_helper.get_processing_time(file_path)

    # 扩展方法：视频特定功能
    def extract_audio_from_video(self, video_path: str) -> str:
        """
        从视频中提取音频

        Args:
            video_path: 视频文件路径

        Returns:
            音频文件路径
        """
        return self.video_preprocessor.extract_audio_from_video(video_path)


# 初始化函数
def create_media_processor(config: Dict[str, Any] = None) -> MediaProcessor:
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
