"""
任务类型定义

集中定义任务相关的类型，避免循环导入
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import time


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
    
    # 辅助任务
    THUMBNAIL_GENERATE = "thumbnail_generate"
    PREVIEW_GENERATE = "preview_generate"
    FILE_SCAN = "file_scan"


@dataclass
class Task:
    """任务数据类"""
    id: str
    type: TaskType
    file_id: str
    file_path: str
    priority: int
    status: TaskStatus = TaskStatus.PENDING
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    progress: float = 0.0
    result: Any = None
    error_message: Optional[str] = None
    depends_on: List[str] = field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 3
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "file_id": self.file_id,
            "file_path": self.file_path,
            "priority": self.priority,
            "status": self.status.value,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "progress": self.progress,
            "result": self.result,
            "error_message": self.error_message,
            "depends_on": self.depends_on,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries
        }
