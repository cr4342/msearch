"""
任务模型
定义任务的基本结构和属性
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid


class Task:
    """任务模型"""

    def __init__(
        self,
        id: str = None,
        task_type: str = "",
        task_data: Dict[str, Any] = None,
        priority: int = 5,
        file_id: str = None,
        file_path: str = None,
        depends_on: List[str] = None,
        group_id: str = None,
        status: str = "pending",
        created_at: datetime = None,
        started_at: datetime = None,
        completed_at: datetime = None,
        updated_at: datetime = None,
        error: str = None,
        file_priority: int = None,
        progress: float = 0.0,
        result: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化任务

        Args:
            id: 任务ID，如果为None则自动生成
            task_type: 任务类型
            task_data: 任务数据
            priority: 优先级
            file_id: 文件ID
            file_path: 文件路径
            depends_on: 依赖的任务ID列表
            group_id: 任务组ID
            status: 任务状态
            created_at: 创建时间
            started_at: 开始时间
            completed_at: 完成时间
            updated_at: 更新时间
            error: 错误信息
            file_priority: 文件优先级
            progress: 任务进度 (0.0-1.0)
            result: 任务结果
        """
        self.id = id or str(uuid.uuid4())
        self.task_id = self.id  # 添加 task_id 属性，与 id 保持一致
        self.task_type = task_type
        self.task_data = task_data or {}
        self.priority = priority
        self.file_id = file_id
        self.file_path = file_path
        self.depends_on = depends_on or []
        self.group_id = group_id
        self.status = status
        self.created_at = created_at or datetime.now()
        self.started_at = started_at
        self.completed_at = completed_at
        self.updated_at = updated_at or datetime.now()
        self.error = error
        self.file_priority = file_priority
        self.progress = progress
        self.result = result
        self.retry_count = 0
        self.max_retries = 3

    def to_dict(self) -> Dict[str, Any]:
        """
        将任务对象转换为字典
        
        Returns:
            Dict[str, Any]: 任务字典表示
        """
        return {
            "id": self.task_id,  # 主键使用 task_id
            "task_id": self.task_id,  # 兼容字段
            "task_type": self.task_type,
            "status": self.status,
            "priority": self.priority,
            "progress": self.progress,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "task_data": self.task_data,
            "file_id": self.file_id,
            "depends_on": self.depends_on,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """从字典创建任务"""
        # 解析时间字符串
        created_at = (
            datetime.fromisoformat(data["created_at"])
            if data.get("created_at")
            else None
        )
        started_at = (
            datetime.fromisoformat(data["started_at"])
            if data.get("started_at")
            else None
        )
        completed_at = (
            datetime.fromisoformat(data["completed_at"])
            if data.get("completed_at")
            else None
        )
        updated_at = (
            datetime.fromisoformat(data["updated_at"])
            if data.get("updated_at")
            else None
        )

        return cls(
            id=data.get("id"),
            task_type=data.get("task_type", ""),
            task_data=data.get("task_data", {}),
            priority=data.get("priority", 5),
            file_id=data.get("file_id"),
            file_path=data.get("file_path"),
            depends_on=data.get("depends_on", []),
            group_id=data.get("group_id"),
            status=data.get("status", "pending"),
            created_at=created_at,
            started_at=started_at,
            completed_at=completed_at,
            updated_at=updated_at,
            error=data.get("error"),
            file_priority=data.get("file_priority"),
            progress=data.get("progress", 0.0),
            result=data.get("result"),
        )

    def is_pipeline_task(self) -> bool:
        """检查是否为流水线任务"""
        pipeline_tasks = [
            "file_preprocessing",
            "image_preprocess",
            "video_preprocess",
            "audio_preprocess",
            "file_embed_image",
            "file_embed_video",
            "file_embed_audio",
            "video_slice",
            "audio_segment",
        ]
        return self.task_type in pipeline_tasks

    def is_core_task(self) -> bool:
        """检查是否为核心任务"""
        core_tasks = [
            "file_preprocessing",
            "file_embed_image",
            "file_embed_video",
            "file_embed_audio",
        ]
        return self.task_type in core_tasks

    def is_auxiliary_task(self) -> bool:
        """检查是否为辅助任务"""
        auxiliary_tasks = [
            "thumbnail_generate",
            "preview_generate",
            "search",
            "search_multimodal",
        ]
        return self.task_type in auxiliary_tasks

    def update_status(self, status: str, error: str = None) -> None:
        """更新任务状态"""
        self.status = status
        self.updated_at = datetime.now()
        if error:
            self.error = error
