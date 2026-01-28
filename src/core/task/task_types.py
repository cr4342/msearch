"""
任务类型定义

集中定义任务相关的类型，避免循环导入
"""

from enum import Enum


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(Enum):
    """任务类型枚举"""
    # 核心任务
    IMAGE_PREPROCESS = "image_preprocess"
    VIDEO_PREPROCESS = "video_preprocess"
    AUDIO_PREPROCESS = "audio_preprocess"
    VIDEO_SLICE = "video_slice"
    FILE_EMBED_IMAGE = "file_embed_image"
    FILE_EMBED_VIDEO = "file_embed_video"
    FILE_EMBED_AUDIO = "file_embed_audio"
    FILE_EMBED_TEXT = "file_embed_text"
    
    # 辅助任务
    THUMBNAIL_GENERATE = "thumbnail_generate"
    PREVIEW_GENERATE = "preview_generate"
    FILE_SCAN = "file_scan"
