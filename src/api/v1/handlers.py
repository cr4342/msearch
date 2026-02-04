"""
API处理器
处理所有API请求的业务逻辑
"""

import logging
import asyncio
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

from .schemas import (
    TextSearchRequest,
    ImageSearchRequest,
    VideoSearchRequest,
    AudioSearchRequest,
    SearchResponse,
    SearchResultItem,
    ModalityType,
    IndexAddRequest,
    IndexRemoveRequest,
    IndexStatusResponse,
    FilesListRequest,
    FilesListResponse,
    FileInfo,
    TasksListRequest,
    TasksListResponse,
    TaskInfo,
    TaskStatusResponse,
    TaskStatus,
    SystemInfo,
    SystemStats,
    ModelInfo,
    ErrorResponse,
    SuccessResponse,
)

logger = logging.getLogger(__name__)


class APIHandlers:
    """API处理器类"""

    def __init__(
        self,
        search_engine,
        file_indexer,
        task_manager,
        database_manager,
        vector_store,
        config_manager,
    ):
        """
        初始化API处理器

        Args:
            search_engine: 搜索引擎
            file_indexer: 文件索引器
            task_manager: 任务管理器
            database_manager: 数据库管理器
            vector_store: 向量存储
            config_manager: 配置管理器
        """
        self.search_engine = search_engine
        self.file_indexer = file_indexer
        self.task_manager = task_manager
        self.database_manager = database_manager
        self.vector_store = vector_store
        self.config_manager = config_manager

    # ==================== 搜索处理器 ====================

    async def handle_text_search(self, request: TextSearchRequest) -> SearchResponse:
        """
        处理文本搜索请求

        Args:
            request: 文本搜索请求

        Returns:
            搜索响应
        """
        try:
            start_time = time.time()

            # 使用搜索引擎进行文本搜索
            search_response = await self.search_engine.search(
                query=request.query,
                k=request.top_k,
                modalities=["image", "video", "audio", "text"],
            )

            search_time = time.time() - start_time

            # 获取结果列表
            results = search_response.get("results", [])

            # 转换结果格式
            search_results = []
            for result in results:
                # 从modality推断file_type
                modality = result.get("modality", "unknown")
                file_type_map = {
                    "image": "image",
                    "video": "video",
                    "audio": "audio",
                    "text": "text",
                }
                file_type = file_type_map.get(modality, "unknown")

                search_results.append(
                    SearchResultItem(
                        file_uuid=result.get("file_id", ""),
                        file_path=result.get("file_path", ""),
                        file_name=result.get("file_name", ""),
                        file_type=file_type,
                        score=result.get("similarity", 0.0),
                        modality=(
                            ModalityType(modality)
                            if modality in ["image", "video", "audio", "text"]
                            else ModalityType.TEXT
                        ),
                        thumbnail_path=result.get("thumbnail_path"),
                        preview_path=result.get("preview_path"),
                        metadata=result.get("metadata"),
                        timestamp_info=(
                            {
                                "start_time": result.get("start_time", 0.0),
                                "end_time": result.get("end_time", 0.0),
                                "is_full_video": result.get("is_full_video", False),
                            }
                            if result.get("start_time") is not None
                            else None
                        ),
                    )
                )

            return SearchResponse(
                query=request.query,
                total_results=len(search_results),
                results=search_results,
                search_time=search_time,
                query_type=ModalityType.TEXT,
            )

        except Exception as e:
            logger.error(f"文本搜索失败: {e}")
            raise

    async def handle_image_search(self, request: ImageSearchRequest) -> SearchResponse:
        """处理图像搜索请求"""
        try:
            start_time = time.time()

            # 使用搜索引擎进行图像搜索
            response = await self.search_engine.image_search(
                image_path=request.query_image, k=request.top_k
            )

            search_time = time.time() - start_time

            # 转换结果格式
            search_results = []
            results = response.get("results", [])
            for result in results:
                search_results.append(
                    SearchResultItem(
                        file_uuid=result.get("file_uuid", ""),
                        file_path=result.get("file_path", ""),
                        file_name=result.get("file_name", ""),
                        file_type=result.get("file_type", ""),
                        score=result.get("score", 0.0),
                        modality=ModalityType.IMAGE,
                        thumbnail_path=result.get("thumbnail_path"),
                        preview_path=result.get("preview_path"),
                        metadata=result.get("metadata"),
                        timestamp_info=result.get("timestamp_info"),
                    )
                )

            return SearchResponse(
                query=request.query_image,
                total_results=len(search_results),
                results=search_results,
                search_time=search_time,
                query_type=ModalityType.IMAGE,
            )

        except Exception as e:
            logger.error(f"图像搜索失败: {e}")
            raise

    async def handle_video_search(self, request: VideoSearchRequest) -> SearchResponse:
        """处理视频搜索请求"""
        try:
            start_time = time.time()

            # 使用搜索引擎进行视频搜索
            results = await self.search_engine.search(
                query=request.query_video,
                modalities=["video"],
                k=request.top_k,
                filters={
                    "start_time": request.start_time,
                    "end_time": request.end_time,
                },
            )

            search_time = time.time() - start_time

            # 转换结果格式
            search_results = []
            for result in results:
                search_results.append(
                    SearchResultItem(
                        file_uuid=result.get("file_uuid", ""),
                        file_path=result.get("file_path", ""),
                        file_name=result.get("file_name", ""),
                        file_type=result.get("file_type", ""),
                        score=result.get("score", 0.0),
                        modality=ModalityType.VIDEO,
                        thumbnail_path=result.get("thumbnail_path"),
                        preview_path=result.get("preview_path"),
                        metadata=result.get("metadata"),
                        timestamp_info=result.get("timestamp_info"),
                    )
                )

            return SearchResponse(
                query=request.query_video,
                total_results=len(search_results),
                results=search_results,
                search_time=search_time,
                query_type=ModalityType.VIDEO,
            )

        except Exception as e:
            logger.error(f"视频搜索失败: {e}")
            raise

    async def handle_audio_search(self, request: AudioSearchRequest) -> SearchResponse:
        """处理音频搜索请求"""
        try:
            start_time = time.time()

            # 使用搜索引擎进行音频搜索
            response = await self.search_engine.audio_search(
                audio_path=request.query_audio, k=request.top_k
            )

            search_time = time.time() - start_time

            # 转换结果格式
            search_results = []
            results = response.get("results", [])
            for result in results:
                search_results.append(
                    SearchResultItem(
                        file_uuid=result.get("file_uuid", ""),
                        file_path=result.get("file_path", ""),
                        file_name=result.get("file_name", ""),
                        file_type=result.get("file_type", ""),
                        score=result.get("score", 0.0),
                        modality=ModalityType.AUDIO,
                        thumbnail_path=result.get("thumbnail_path"),
                        preview_path=result.get("preview_path"),
                        metadata=result.get("metadata"),
                        timestamp_info=result.get("timestamp_info"),
                    )
                )

            return SearchResponse(
                query=request.query_audio,
                total_results=len(search_results),
                results=search_results,
                search_time=search_time,
                query_type=ModalityType.AUDIO,
            )

        except Exception as e:
            logger.error(f"音频搜索失败: {e}")
            raise

    # ==================== 索引处理器 ====================

    async def handle_index_add(self, request: IndexAddRequest) -> SuccessResponse:
        """
        处理添加索引请求

        Args:
            request: 添加索引请求

        Returns:
            成功响应
        """
        try:
            # 为每个文件创建索引任务
            task_ids = []
            for file_path in request.file_paths:
                task_id = self.task_manager.create_task(
                    task_type="file_scan",
                    task_data={"file_path": file_path, "recursive": request.recursive},
                    priority=request.priority,
                )
                task_ids.append(task_id)

            return SuccessResponse(
                success=True,
                message=f"成功创建{len(task_ids)}个索引任务",
                data={"task_ids": task_ids},
            )

        except Exception as e:
            logger.error(f"添加索引失败: {e}")
            raise

    async def handle_index_remove(self, request: IndexRemoveRequest) -> SuccessResponse:
        """
        处理移除索引请求

        Args:
            request: 移除索引请求

        Returns:
            成功响应
        """
        try:
            # 从数据库中移除文件索引
            removed_count = 0
            for file_uuid in request.file_uuids:
                success = self.database_manager.remove_file(file_uuid)
                if success:
                    removed_count += 1

            return SuccessResponse(
                success=True,
                message=f"成功移除{removed_count}个文件索引",
                data={
                    "removed_count": removed_count,
                    "requested_count": len(request.file_uuids),
                },
            )

        except Exception as e:
            logger.error(f"移除索引失败: {e}")
            raise

    async def handle_index_status(self) -> IndexStatusResponse:
        """
        处理索引状态请求

        Returns:
            索引状态响应
        """
        try:
            # 获取索引统计信息
            total_files = self.database_manager.get_total_files()
            indexed_files = self.database_manager.get_indexed_files()

            # 获取待处理和失败的任务
            pending_tasks = self.task_manager.get_tasks_by_status("pending")
            failed_tasks = self.task_manager.get_tasks_by_status("failed")

            # 获取当前正在进行的索引任务
            indexing_tasks = []
            for task in pending_tasks:
                if task.task_type in [
                    "file_scan",
                    "image_preprocess",
                    "video_preprocess",
                    "audio_preprocess",
                ]:
                    indexing_tasks.append(
                        {
                            "task_id": task.task_id,
                            "task_type": task.task_type,
                            "status": task.status.value,
                            "created_at": (
                                task.created_at.isoformat() if task.created_at else None
                            ),
                        }
                    )

            return IndexStatusResponse(
                total_files=total_files,
                indexed_files=indexed_files,
                pending_files=len(pending_tasks),
                failed_files=len(failed_tasks),
                indexing_tasks=indexing_tasks,
            )

        except Exception as e:
            logger.error(f"获取索引状态失败: {e}")
            raise

    async def handle_index_file(self, file_path: str) -> SuccessResponse:
        """
        处理索引单个文件请求

        Args:
            file_path: 文件路径

        Returns:
            成功响应
        """
        try:
            import os

            if not os.path.exists(file_path):
                return SuccessResponse(
                    success=False, message=f"文件不存在: {file_path}", data={}
                )

            # 创建索引任务
            task_id = self.task_manager.create_task(
                task_type="file_scan", task_data={"file_path": file_path}, priority=5
            )

            return SuccessResponse(
                success=True, message=f"成功创建索引任务", data={"task_id": task_id}
            )

        except Exception as e:
            logger.error(f"索引文件失败: {e}")
            raise

    async def handle_index_directory(
        self, directory: str, recursive: bool = True
    ) -> SuccessResponse:
        """
        处理索引目录请求

        Args:
            directory: 目录路径
            recursive: 是否递归索引子目录

        Returns:
            成功响应
        """
        try:
            import os
            from pathlib import Path

            if not os.path.isdir(directory):
                return SuccessResponse(
                    success=False, message=f"目录不存在: {directory}", data={}
                )

            # 扫描目录中的文件
            file_paths = []
            path = Path(directory)

            image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp"}
            video_extensions = {".mp4", ".avi", ".mov", ".mkv", ".flv", ".wmv"}
            audio_extensions = {".mp3", ".wav", ".aac", ".ogg", ".flac", ".wma"}

            if recursive:
                files = path.rglob("*")
            else:
                files = path.glob("*")

            for file in files:
                if file.is_file():
                    ext = file.suffix.lower()
                    if (
                        ext in image_extensions
                        or ext in video_extensions
                        or ext in audio_extensions
                    ):
                        file_paths.append(str(file))

            # 创建索引任务
            task_ids = []
            for file_path in file_paths[:100]:  # 限制最多100个文件
                task_id = self.task_manager.create_task(
                    task_type="file_scan",
                    task_data={"file_path": file_path},
                    priority=5,
                )
                task_ids.append(task_id)

            return SuccessResponse(
                success=True,
                message=f"成功创建{len(task_ids)}个索引任务",
                data={
                    "task_id": task_ids[0] if task_ids else None,
                    "stats": {
                        "total_files": len(file_paths),
                        "image_files": len(
                            [
                                f
                                for f in file_paths
                                if Path(f).suffix.lower() in image_extensions
                            ]
                        ),
                        "video_files": len(
                            [
                                f
                                for f in file_paths
                                if Path(f).suffix.lower() in video_extensions
                            ]
                        ),
                        "audio_files": len(
                            [
                                f
                                for f in file_paths
                                if Path(f).suffix.lower() in audio_extensions
                            ]
                        ),
                        "other_files": len(file_paths)
                        - len(
                            [
                                f
                                for f in file_paths
                                if Path(f).suffix.lower() in image_extensions
                                or Path(f).suffix.lower() in video_extensions
                                or Path(f).suffix.lower() in audio_extensions
                            ]
                        ),
                    },
                },
            )

        except Exception as e:
            logger.error(f"索引目录失败: {e}")
            raise

    async def handle_reindex_all(self) -> SuccessResponse:
        """
        处理重新索引所有文件请求

        Returns:
            成功响应
        """
        try:
            # 获取所有已索引的文件
            files = self.database_manager.get_all_files()

            # 重新创建索引任务
            task_ids = []
            for file_info in files[:100]:  # 限制最多100个文件
                task_id = self.task_manager.create_task(
                    task_type="file_scan",
                    task_data={"file_path": file_info["file_path"]},
                    priority=5,
                )
                task_ids.append(task_id)

            return SuccessResponse(
                success=True,
                message=f"成功创建{len(task_ids)}个重新索引任务",
                data={"task_id": task_ids[0] if task_ids else None},
            )

        except Exception as e:
            logger.error(f"重新索引失败: {e}")
            raise

    # ==================== 文件管理处理器 ====================

    async def handle_files_list(self, request: FilesListRequest) -> FilesListResponse:
        """
        处理文件列表请求

        Args:
            request: 文件列表请求

        Returns:
            文件列表响应
        """
        try:
            # 从数据库获取文件列表
            files_data = self.database_manager.list_files(
                file_type=request.file_type,
                indexed_only=request.indexed_only,
                limit=request.limit,
                offset=request.offset,
            )

            # 转换为FileInfo对象
            files = []
            for file_data in files_data:
                files.append(
                    FileInfo(
                        file_uuid=file_data.get("file_uuid", ""),
                        file_path=file_data.get("file_path", ""),
                        file_name=file_data.get("file_name", ""),
                        file_type=file_data.get("file_type", ""),
                        file_size=file_data.get("file_size", 0),
                        created_at=(
                            datetime.fromisoformat(file_data["created_at"])
                            if file_data.get("created_at")
                            else datetime.now()
                        ),
                        modified_at=(
                            datetime.fromisoformat(file_data["modified_at"])
                            if file_data.get("modified_at")
                            else datetime.now()
                        ),
                        indexed=file_data.get("indexed", False),
                        has_thumbnail=file_data.get("has_thumbnail", False),
                        has_preview=file_data.get("has_preview", False),
                    )
                )

            # 获取总数
            total_files = self.database_manager.get_total_files()

            return FilesListResponse(total_files=total_files, files=files)

        except Exception as e:
            logger.error(f"获取文件列表失败: {e}")
            raise

    async def handle_file_info(self, file_uuid: str) -> FileInfo:
        """
        处理文件信息请求

        Args:
            file_uuid: 文件UUID

        Returns:
            文件信息
        """
        try:
            # 从数据库获取文件信息
            file_data = self.database_manager.get_file_info(file_uuid)

            if not file_data:
                raise ValueError(f"文件不存在: {file_uuid}")

            return FileInfo(
                file_uuid=file_data.get("file_uuid", ""),
                file_path=file_data.get("file_path", ""),
                file_name=file_data.get("file_name", ""),
                file_type=file_data.get("file_type", ""),
                file_size=file_data.get("file_size", 0),
                created_at=(
                    datetime.fromisoformat(file_data["created_at"])
                    if file_data.get("created_at")
                    else datetime.now()
                ),
                modified_at=(
                    datetime.fromisoformat(file_data["modified_at"])
                    if file_data.get("modified_at")
                    else datetime.now()
                ),
                indexed=file_data.get("indexed", False),
                has_thumbnail=file_data.get("has_thumbnail", False),
                has_preview=file_data.get("has_preview", False),
            )

        except Exception as e:
            logger.error(f"获取文件信息失败: {e}")
            raise

    # ==================== 任务管理处理器 ====================

    async def handle_tasks_list(self, request: TasksListRequest) -> TasksListResponse:
        """
        处理任务列表请求

        Args:
            request: 任务列表请求

        Returns:
            任务列表响应
        """
        try:
            # 获取任务列表 - 不传递limit和offset参数因为CentralTaskManager.list_tasks不支持
            all_tasks = self.task_manager.list_tasks(
                task_type=request.task_type,
                status=request.status.value if request.status else None,
            )

            # 转换为TaskInfo对象
            all_task_infos = []
            for task in all_tasks:
                # 确保task对象有必要的属性
                if hasattr(task, 'to_dict'):
                    task_dict = task.to_dict()
                else:
                    # 如果是字典格式，直接使用
                    task_dict = task if isinstance(task, dict) else {}
                
                # 获取状态值
                status_value = task_dict.get('status', getattr(task, 'status', 'pending'))
                # 确保状态值是有效的TaskStatus
                try:
                    task_status = TaskStatus(status_value)
                except ValueError:
                    # 如果状态值无效，使用默认的pending状态
                    task_status = TaskStatus.PENDING
                
                # 创建TaskInfo对象
                # 从result中提取file_path（如果有）
                result_data = task_dict.get('result', getattr(task, 'result', None)) or {}
                file_path = result_data.get('file_path', '') if isinstance(result_data, dict) else ''
                
                # 使用 task_id 字段，因为现在 Task.to_dict() 同时包含 id 和 task_id
                task_id = task_dict.get('task_id', getattr(task, 'task_id', task_dict.get('id', getattr(task, 'id', ''))))
                
                task_info = TaskInfo(
                    task_id=task_id,
                    task_type=task_dict.get('task_type', getattr(task, 'task_type', '')),
                    status=task_status,
                    priority=task_dict.get('priority', getattr(task, 'priority', 5)),
                    created_at=task_dict.get('created_at', getattr(task, 'created_at', None)),
                    started_at=task_dict.get('started_at', getattr(task, 'started_at', None)),
                    completed_at=task_dict.get('completed_at', getattr(task, 'completed_at', None)),
                    error_message=task_dict.get('error', getattr(task, 'error', None)),
                    progress=task_dict.get('progress', getattr(task, 'progress', 0.0)),
                    result=result_data,
                    file_path=file_path,
                    duration=task_dict.get('duration', getattr(task, 'duration', None)),
                    tags=task_dict.get('tags', getattr(task, 'tags', None)) or [],
                )
                all_task_infos.append(task_info)

            # 应用分页
            total_tasks = len(all_task_infos)
            
            # 按offset和limit进行分页
            start_index = request.offset
            end_index = start_index + request.limit
            paged_tasks = all_task_infos[start_index:end_index]

            return TasksListResponse(total_tasks=total_tasks, tasks=paged_tasks)

        except Exception as e:
            logger.error(f"获取任务列表失败: {e}")
            raise

    async def handle_task_status(self, task_id: str) -> TaskStatusResponse:
        """
        处理任务状态请求

        Args:
            task_id: 任务ID

        Returns:
            任务状态响应
        """
        try:
            # 获取任务信息
            task = self.task_manager.get_task(task_id)

            if not task:
                raise ValueError(f"任务不存在: {task_id}")

            return TaskStatusResponse(
                task_id=task.task_id,  # 使用 task_id 而不是 id
                task_type=task.task_type,
                status=TaskStatus(task.status),
                progress=task.progress,
                result=task.result,
                error_message=task.error,
            )

        except Exception as e:
            logger.error(f"获取任务状态失败: {e}")
            raise

    async def handle_task_cancel(self, task_id: str) -> SuccessResponse:
        """
        处理取消任务请求

        Args:
            task_id: 任务ID

        Returns:
            成功响应
        """
        try:
            # 取消任务
            success = self.task_manager.cancel_task(task_id)

            if success:
                return SuccessResponse(success=True, message=f"任务已取消: {task_id}")
            else:
                raise ValueError(f"无法取消任务: {task_id}")

        except Exception as e:
            logger.error(f"取消任务失败: {e}")
            raise

    async def handle_task_pause(self, task_id: str) -> SuccessResponse:
        """
        处理暂停任务请求

        Args:
            task_id: 任务ID

        Returns:
            成功响应
        """
        try:
            # 获取任务状态
            task = self.task_manager.get_task(task_id)
            if not task:
                raise ValueError(f"任务不存在: {task_id}")
            
            if task.status != "running":
                raise ValueError(f"任务状态不是运行中，无法暂停: {task.status}")
            
            # 暂停任务 - 目前实现为取消任务，在后续版本中可以扩展为真正的暂停
            success = self.task_manager.cancel_task(task_id)
            
            if success:
                return SuccessResponse(success=True, message=f"任务已暂停: {task_id}")
            else:
                raise ValueError(f"无法暂停任务: {task_id}")

        except Exception as e:
            logger.error(f"暂停任务失败: {e}")
            raise

    async def handle_task_resume(self, task_id: str) -> SuccessResponse:
        """
        处理恢复任务请求

        Args:
            task_id: 任务ID

        Returns:
            成功响应
        """
        try:
            # 获取任务状态
            task = self.task_manager.get_task(task_id)
            if not task:
                raise ValueError(f"任务不存在: {task_id}")
            
            if task.status != "cancelled" and task.status != "paused":
                raise ValueError(f"任务状态不是已取消或已暂停，无法恢复: {task.status}")
                
            # 恢复任务 - 重新提交任务到队列
            new_task_id = self.task_manager.create_task(
                task_type=task.task_type,
                task_data=task.task_data,
                priority=task.priority,
                file_id=task.file_id,
                depends_on=task.depends_on
            )
            
            if new_task_id:
                return SuccessResponse(
                    success=True, 
                    message=f"任务已恢复: {task_id} -> {new_task_id}",
                    data={"new_task_id": new_task_id}
                )
            else:
                raise ValueError(f"无法恢复任务: {task_id}")

        except Exception as e:
            logger.error(f"恢复任务失败: {e}")
            raise

    async def handle_task_retry(self, task_id: str) -> SuccessResponse:
        """
        处理重试任务请求

        Args:
            task_id: 任务ID

        Returns:
            成功响应
        """
        try:
            # 获取任务状态
            task = self.task_manager.get_task(task_id)
            if not task:
                raise ValueError(f"任务不存在: {task_id}")
            
            if task.status != "failed":
                raise ValueError(f"任务状态不是失败，无法重试: {task.status}")
                
            # 重试任务 - 重新提交任务到队列
            new_task_id = self.task_manager.create_task(
                task_type=task.task_type,
                task_data=task.task_data,
                priority=task.priority,
                file_id=task.file_id,
                depends_on=task.depends_on
            )
            
            if new_task_id:
                return SuccessResponse(
                    success=True, 
                    message=f"任务已重试: {task_id} -> {new_task_id}",
                    data={"new_task_id": new_task_id}
                )
            else:
                raise ValueError(f"无法重试任务: {task_id}")

        except Exception as e:
            logger.error(f"重试任务失败: {e}")
            raise

    async def handle_task_archive(self, task_id: str) -> SuccessResponse:
        """
        处理归档任务请求

        Args:
            task_id: 任务ID

        Returns:
            成功响应
        """
        try:
            # 获取任务状态
            task = self.task_manager.get_task(task_id)
            if not task:
                raise ValueError(f"任务不存在: {task_id}")
                
            # 目前实现为简单删除任务（在后续版本中可以实现真正的归档）
            success = self.task_manager.cancel_task(task_id)
            
            if success:
                return SuccessResponse(success=True, message=f"任务已归档: {task_id}")
            else:
                raise ValueError(f"无法归档任务: {task_id}")

        except Exception as e:
            logger.error(f"归档任务失败: {e}")
            raise

    # ==================== 系统信息处理器 ====================

    async def handle_system_info(self) -> SystemInfo:
        """
        处理系统信息请求

        Returns:
            系统信息
        """
        try:
            import platform as plt
            import os

            # 获取模型信息
            models_config = self.config_manager.get("models", {})
            available_models = models_config.get("available_models", {})

            model_infos = []
            for model_id, model_config in available_models.items():
                model_infos.append(
                    ModelInfo(
                        model_id=model_id,
                        model_name=model_config.get("model_name", ""),
                        status="loaded",  # 简化处理
                        embedding_dim=model_config.get("embedding_dim", 0),
                        device=model_config.get("device", "cpu"),
                        loaded=True,  # 简化处理
                    )
                )

            # 获取向量存储统计 - 添加错误处理
            try:
                vector_stats = self.vector_store.get_collection_stats()
                total_vectors = vector_stats.get("total_vectors", 0)
                collection_name = self.vector_store.collection_name
                vector_store_connected = True
            except Exception as e:
                logger.warning(f"获取向量存储统计失败: {e}")
                total_vectors = 0
                collection_name = "unknown"
                vector_store_connected = False

            # 获取数据库状态 - 添加错误处理
            try:
                total_files = self.database_manager.get_total_files()
                database_connected = True
            except Exception as e:
                logger.warning(f"获取数据库文件数失败: {e}")
                total_files = 0
                database_connected = False

            # 获取数据库状态
            database_status = {
                "connected": database_connected,
                "total_files": total_files,
                "total_vectors": total_vectors,
            }

            # 获取向量存储状态
            vector_store_status = {
                "connected": vector_store_connected,
                "total_vectors": total_vectors,
                "collection_name": collection_name,
            }

            return SystemInfo(
                version="1.0.0",
                python_version=plt.python_version(),
                platform=plt.platform(),
                uptime=time.time(),
                models=model_infos,
                database_status=database_status,
                vector_store_status=vector_store_status,
            )

        except Exception as e:
            logger.error(f"获取系统信息失败: {e}")
            # 返回最小化的系统信息而不是完全失败
            import platform as plt
            return SystemInfo(
                version="1.0.0",
                python_version=plt.python_version(),
                platform=plt.platform(),
                uptime=time.time(),
                models=[],
                database_status={
                    "connected": False,
                    "total_files": 0,
                    "total_vectors": 0,
                },
                vector_store_status={
                    "connected": False,
                    "total_vectors": 0,
                    "collection_name": "unknown",
                },
            )

    async def handle_system_stats(self) -> SystemStats:
        """
        处理系统统计请求

        Returns:
            系统统计信息
        """
        try:
            import psutil

            # 获取任务统计
            all_tasks = self.task_manager.list_tasks()
            active_tasks = [t for t in all_tasks if t.status.value == "running"]
            completed_tasks = [t for t in all_tasks if t.status.value == "completed"]
            failed_tasks = [t for t in all_tasks if t.status.value == "failed"]

            # 获取内存使用
            memory = psutil.virtual_memory()
            memory_usage = {
                "total_gb": memory.total / (1024**3),
                "used_gb": memory.used / (1024**3),
                "available_gb": memory.available / (1024**3),
                "percent": memory.percent,
            }

            # 获取磁盘使用
            disk = psutil.disk_usage("/")
            disk_usage = {
                "total_gb": disk.total / (1024**3),
                "used_gb": disk.used / (1024**3),
                "free_gb": disk.free / (1024**3),
                "percent": disk.percent,
            }

            return SystemStats(
                total_files=self.database_manager.get_total_files(),
                indexed_files=self.database_manager.get_indexed_files(),
                total_vectors=self.vector_store.get_total_vectors(),
                active_tasks=len(active_tasks),
                completed_tasks=len(completed_tasks),
                failed_tasks=len(failed_tasks),
                memory_usage=memory_usage,
                disk_usage=disk_usage,
            )

        except Exception as e:
            logger.error(f"获取系统统计失败: {e}")
            raise
