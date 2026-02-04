"""
API数据模型定义
定义所有API请求和响应的数据结构
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class ModalityType(str, Enum):
    """模态类型枚举"""

    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"


class TaskStatus(str, Enum):
    """任务状态枚举"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# ==================== 搜索相关 ====================


class TextSearchRequest(BaseModel):
    """文本搜索请求"""

    query: str = Field(..., description="搜索查询文本", min_length=1, max_length=1000)
    top_k: int = Field(20, ge=1, le=100, description="返回结果数量")
    threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="相似度阈值")


class ImageSearchRequest(BaseModel):
    """图像搜索请求"""

    query_image: str = Field(..., description="图像文件路径或base64编码")
    top_k: int = Field(20, ge=1, le=100, description="返回结果数量")
    threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="相似度阈值")


class VideoSearchRequest(BaseModel):
    """视频搜索请求"""

    query_video: str = Field(..., description="视频文件路径或base64编码")
    top_k: int = Field(20, ge=1, le=100, description="返回结果数量")
    threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="相似度阈值")
    start_time: Optional[float] = Field(0.0, ge=0.0, description="视频开始时间")
    end_time: Optional[float] = Field(None, ge=0.0, description="视频结束时间")


class AudioSearchRequest(BaseModel):
    """音频搜索请求"""

    query_audio: str = Field(..., description="音频文件路径或base64编码")
    top_k: int = Field(20, ge=1, le=100, description="返回结果数量")
    threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="相似度阈值")


class SearchResultItem(BaseModel):
    """搜索结果项"""

    file_uuid: str
    file_path: str
    file_name: str
    file_type: str
    score: float
    modality: ModalityType
    thumbnail_path: Optional[str] = None
    preview_path: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp_info: Optional[Dict[str, float]] = None  # 视频时间戳信息


class SearchResponse(BaseModel):
    """搜索响应"""

    query: str
    total_results: int
    results: List[SearchResultItem]
    search_time: float
    query_type: ModalityType


# ==================== 索引相关 ====================


class IndexAddRequest(BaseModel):
    """添加索引请求"""

    file_paths: List[str] = Field(..., description="要索引的文件路径列表", min_length=1)
    recursive: bool = Field(False, description="是否递归处理子目录")
    priority: int = Field(5, ge=1, le=10, description="任务优先级")


class IndexRemoveRequest(BaseModel):
    """移除索引请求"""

    file_uuids: List[str] = Field(..., description="要移除的文件UUID列表", min_length=1)


class IndexStatusResponse(BaseModel):
    """索引状态响应"""

    total_files: int
    indexed_files: int
    pending_files: int
    failed_files: int
    indexing_tasks: List[Dict[str, Any]]


# ==================== 文件管理相关 ====================


class FileInfo(BaseModel):
    """文件信息"""

    file_uuid: str
    file_path: str
    file_name: str
    file_type: str
    file_size: int
    created_at: datetime
    modified_at: datetime
    indexed: bool
    has_thumbnail: bool
    has_preview: bool


class FilesListRequest(BaseModel):
    """文件列表请求"""

    file_type: Optional[str] = Field(None, description="文件类型过滤")
    indexed_only: bool = Field(False, description="仅返回已索引的文件")
    limit: int = Field(100, ge=1, le=1000, description="返回数量限制")
    offset: int = Field(0, ge=0, description="偏移量")


class FilesListResponse(BaseModel):
    """文件列表响应"""

    total_files: int
    files: List[FileInfo]


# ==================== 任务管理相关 ====================


class TaskInfo(BaseModel):
    """任务信息"""

    task_id: str
    task_type: str
    status: TaskStatus
    priority: int
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    progress: Optional[float] = None
    result: Optional[Dict[str, Any]] = None
    file_path: Optional[str] = None
    duration: Optional[float] = None
    tags: Optional[List[str]] = None


class TasksListRequest(BaseModel):
    """任务列表请求"""

    task_type: Optional[str] = Field(None, description="任务类型过滤")
    status: Optional[TaskStatus] = Field(None, description="状态过滤")
    limit: int = Field(100, ge=1, le=1000, description="返回数量限制")
    offset: int = Field(0, ge=0, description="偏移量")


class TasksListResponse(BaseModel):
    """任务列表响应"""

    total_tasks: int
    tasks: List[TaskInfo]


class TaskStatusResponse(BaseModel):
    """任务状态响应"""

    task_id: str
    task_type: str
    status: TaskStatus
    progress: Optional[float] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class ThreadPoolStatus(BaseModel):
    """线程池状态"""

    max_workers: int
    active_threads: int
    idle_threads: int
    load_percentage: int


class ThreadPoolStatusResponse(BaseModel):
    """线程池状态响应"""

    thread_pool: ThreadPoolStatus


# ==================== 系统信息相关 ====================


class SystemInfo(BaseModel):
    """系统信息"""

    version: str
    python_version: str
    platform: str
    uptime: float
    models: List[Dict[str, Any]]
    database_status: Dict[str, Any]
    vector_store_status: Dict[str, Any]


class SystemStats(BaseModel):
    """系统统计信息"""

    total_files: int
    indexed_files: int
    total_vectors: int
    active_tasks: int
    completed_tasks: int
    failed_tasks: int
    memory_usage: Dict[str, float]
    disk_usage: Dict[str, float]


class ModelInfo(BaseModel):
    """模型信息"""

    model_id: str
    model_name: str
    status: str
    embedding_dim: int
    device: str
    loaded: bool


# ==================== 通用响应 ====================


class ErrorResponse(BaseModel):
    """错误响应"""

    error: str
    message: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class SuccessResponse(BaseModel):
    """成功响应"""

    success: bool
    message: str
    data: Optional[Any] = None
    timestamp: datetime = Field(default_factory=datetime.now)
