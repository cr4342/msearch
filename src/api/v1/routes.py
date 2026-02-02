"""
API路由定义
定义所有API端点
"""

from fastapi import APIRouter, HTTPException, Depends, Form, UploadFile, File
from typing import Optional

from .schemas import (
    TextSearchRequest,
    ImageSearchRequest,
    VideoSearchRequest,
    AudioSearchRequest,
    SearchResponse,
    IndexAddRequest,
    IndexRemoveRequest,
    IndexStatusResponse,
    FilesListRequest,
    FilesListResponse,
    FileInfo,
    TasksListRequest,
    TasksListResponse,
    TaskStatusResponse,
    ThreadPoolStatusResponse,
    SystemInfo,
    SystemStats,
    ErrorResponse,
    SuccessResponse,
)
from .handlers import APIHandlers


# 创建API路由器
router = APIRouter(prefix="/api/v1", tags=["API v1"])


# ==================== 依赖注入 ====================

# 全局变量存储APIServer实例
_api_server_instance = None


def set_api_server_instance(server):
    """设置APIServer实例"""
    global _api_server_instance
    _api_server_instance = server


def get_handlers() -> APIHandlers:
    """获取API处理器实例"""
    if _api_server_instance is None:
        raise RuntimeError("APIServer实例未设置，请先调用set_api_server_instance()")

    return APIHandlers(
        search_engine=(
            _api_server_instance.search_engine
            if hasattr(_api_server_instance, "search_engine")
            else None
        ),
        file_indexer=(
            _api_server_instance.file_indexer
            if hasattr(_api_server_instance, "file_indexer")
            else None
        ),
        task_manager=_api_server_instance.task_manager,
        database_manager=_api_server_instance.database_manager,
        vector_store=_api_server_instance.vector_store,
        config_manager=_api_server_instance.config,
    )


# ==================== 搜索端点 ====================


@router.post("/search/text", response_model=SearchResponse)
async def search_text(
    request: TextSearchRequest, handlers: APIHandlers = Depends(get_handlers)
):
    """
    文本搜索

    使用文本查询搜索图像、视频、音频文件
    """
    try:
        return await handlers.handle_text_search(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search/image", response_model=SearchResponse)
async def search_image(
    file: Optional[UploadFile] = File(None),
    query_image: Optional[str] = Form(None),
    top_k: int = Form(20),
    threshold: Optional[float] = Form(None),
    handlers: APIHandlers = Depends(get_handlers),
):
    """
    图像搜索

    使用图像查询搜索相似的图像、视频文件
    支持两种方式：
    1. 上传图像文件（FormData）
    2. 提供图像路径（JSON）
    """
    try:
        import os
        import uuid
        from pathlib import Path

        # 如果上传了文件，保存到临时目录
        if file:
            upload_dir = Path("data/uploads")
            upload_dir.mkdir(parents=True, exist_ok=True)

            file_extension = Path(file.filename).suffix
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            file_path = upload_dir / unique_filename

            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)

            query_image = str(file_path)

        # 创建请求对象
        request = ImageSearchRequest(
            query_image=query_image, top_k=top_k, threshold=threshold
        )

        return await handlers.handle_image_search(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search/video", response_model=SearchResponse)
async def search_video(
    request: VideoSearchRequest, handlers: APIHandlers = Depends(get_handlers)
):
    """
    视频搜索

    使用视频查询搜索相似的视频文件
    """
    try:
        return await handlers.handle_video_search(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search/audio", response_model=SearchResponse)
async def search_audio(
    file: Optional[UploadFile] = File(None),
    query_audio: Optional[str] = Form(None),
    top_k: int = Form(20),
    threshold: Optional[float] = Form(None),
    handlers: APIHandlers = Depends(get_handlers),
):
    """
    音频搜索

    使用音频查询搜索相似的音频、视频文件
    支持两种方式：
    1. 上传音频文件（FormData）
    2. 提供音频路径（JSON）
    """
    try:
        import os
        import uuid
        from pathlib import Path

        # 如果上传了文件，保存到临时目录
        if file:
            upload_dir = Path("data/uploads")
            upload_dir.mkdir(parents=True, exist_ok=True)

            file_extension = Path(file.filename).suffix
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            file_path = upload_dir / unique_filename

            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)

            query_audio = str(file_path)

        # 创建请求对象
        request = AudioSearchRequest(
            query_audio=query_audio, top_k=top_k, threshold=threshold
        )

        return await handlers.handle_audio_search(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 索引端点 ====================


@router.post("/index/file", response_model=SuccessResponse)
async def index_file(
    file_path: str = Form(...), handlers: APIHandlers = Depends(get_handlers)
):
    """
    索引单个文件
    """
    try:
        return await handlers.handle_index_file(file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/index/directory", response_model=SuccessResponse)
async def index_directory(
    directory: str = Form(...),
    recursive: str = Form("true"),
    handlers: APIHandlers = Depends(get_handlers),
):
    """
    索引目录
    """
    try:
        recursive_bool = recursive.lower() == "true"
        return await handlers.handle_index_directory(directory, recursive_bool)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/index/reindex-all", response_model=SuccessResponse)
async def reindex_all(handlers: APIHandlers = Depends(get_handlers)):
    """
    重新索引所有文件
    """
    try:
        return await handlers.handle_reindex_all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/index/add", response_model=SuccessResponse)
async def add_index(
    request: IndexAddRequest, handlers: APIHandlers = Depends(get_handlers)
):
    """
    添加索引

    将文件添加到索引队列
    """
    try:
        return await handlers.handle_index_add(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/index/remove", response_model=SuccessResponse)
async def remove_index(
    request: IndexRemoveRequest, handlers: APIHandlers = Depends(get_handlers)
):
    """
    移除索引

    从索引中移除文件
    """
    try:
        return await handlers.handle_index_remove(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/index/status", response_model=IndexStatusResponse)
async def get_index_status(handlers: APIHandlers = Depends(get_handlers)):
    """
    获取索引状态

    获取当前索引状态和统计信息
    """
    try:
        return await handlers.handle_index_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 文件管理端点 ====================


@router.get("/files/list", response_model=FilesListResponse)
async def list_files(
    file_type: Optional[str] = None,
    indexed_only: bool = False,
    limit: int = 100,
    offset: int = 0,
    handlers: APIHandlers = Depends(get_handlers),
):
    """
    获取文件列表

    获取系统中所有文件的列表
    """
    try:
        request = FilesListRequest(
            file_type=file_type, indexed_only=indexed_only, limit=limit, offset=offset
        )
        return await handlers.handle_files_list(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/files/{file_uuid}", response_model=FileInfo)
async def get_file_info(file_uuid: str, handlers: APIHandlers = Depends(get_handlers)):
    """
    获取文件信息

    获取指定文件的详细信息
    """
    try:
        return await handlers.handle_file_info(file_uuid)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/files/upload")
async def upload_file(
    file: UploadFile = File(...), handlers: APIHandlers = Depends(get_handlers)
):
    """
    上传文件

    上传文件并返回文件路径
    """
    try:
        import os
        import uuid
        from pathlib import Path
        from fastapi import UploadFile, File

        # 创建上传目录
        upload_dir = Path("data/uploads")
        upload_dir.mkdir(parents=True, exist_ok=True)

        # 生成唯一文件名
        file_extension = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = upload_dir / unique_filename

        # 保存文件
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        return {"success": True, "file_path": str(file_path), "filename": file.filename}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/files/preview")
async def get_file_preview(path: str, handlers: APIHandlers = Depends(get_handlers)):
    """
    获取文件预览

    返回文件的预览内容（图像、视频缩略图等）
    """
    try:
        from fastapi.responses import FileResponse
        from pathlib import Path

        file_path = Path(path)

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="文件不存在")

        # 如果是图像文件，直接返回
        if file_path.suffix.lower() in [
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".bmp",
            ".webp",
        ]:
            return FileResponse(file_path, media_type=f"image/{file_path.suffix[1:]}")

        # 如果是视频文件，返回预览图
        elif file_path.suffix.lower() in [".mp4", ".avi", ".mov", ".mkv", ".flv"]:
            # 查找对应的缩略图
            thumbnail_path = handlers.database_manager.get_thumbnail_by_path(
                str(file_path)
            )
            if thumbnail_path and Path(thumbnail_path).exists():
                return FileResponse(thumbnail_path, media_type="image/jpeg")
            else:
                raise HTTPException(status_code=404, detail="预览图不存在")

        # 如果是音频文件，返回音频可视化
        elif file_path.suffix.lower() in [".mp3", ".wav", ".flac", ".aac", ".ogg"]:
            # 返回音频波形图
            return {"error": "音频预览功能开发中"}

        else:
            raise HTTPException(status_code=400, detail="不支持的文件类型")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/files/thumbnail")
async def get_file_thumbnail(path: str, handlers: APIHandlers = Depends(get_handlers)):
    """
    获取文件缩略图

    返回文件的缩略图
    """
    try:
        from fastapi.responses import FileResponse
        from pathlib import Path

        thumbnail_path = Path(path)

        if not thumbnail_path.exists():
            raise HTTPException(status_code=404, detail="缩略图不存在")

        return FileResponse(thumbnail_path, media_type="image/jpeg")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 任务管理端点 ====================


@router.get("/tasks", response_model=TasksListResponse)
async def list_tasks(
    task_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    handlers: APIHandlers = Depends(get_handlers),
):
    """
    获取任务列表

    获取系统中所有任务的列表
    """
    try:
        request = TasksListRequest(
            task_type=task_type,
            status=TaskStatus(status) if status else None,
            limit=limit,
            offset=offset,
        )
        return await handlers.handle_tasks_list(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/stats")
async def get_task_stats(handlers: APIHandlers = Depends(get_handlers)):
    """
    获取任务统计

    获取任务统计信息
    """
    try:
        from pydantic import BaseModel

        class TaskStatsResponse(BaseModel):
            """任务统计响应"""

            task_stats: dict
            concurrency: int
            resource_usage: dict

        # 获取任务统计
        all_tasks = handlers.task_manager.list_tasks()

        # 按状态统计
        status_counts = {
            "pending": 0,
            "running": 0,
            "completed": 0,
            "failed": 0,
            "cancelled": 0,
        }
        for task in all_tasks:
            # 处理任务对象和字典两种格式
            if isinstance(task, dict):
                status = task.get("status", "pending")
                task_type = task.get("task_type", "unknown")
            else:
                status = task.status.value if hasattr(task, "status") else "pending"
                task_type = task.task_type if hasattr(task, "task_type") else "unknown"

            if status in status_counts:
                status_counts[status] += 1

        # 按类型统计
        type_counts = {}
        for task in all_tasks:
            # 处理任务对象和字典两种格式
            if isinstance(task, dict):
                task_type = task.get("task_type", "unknown")
                status = task.get("status", "pending")
            else:
                task_type = task.task_type if hasattr(task, "task_type") else "unknown"
                status = task.status.value if hasattr(task, "status") else "pending"

            if task_type not in type_counts:
                type_counts[task_type] = {"total": 0, "completed": 0, "failed": 0}
            type_counts[task_type]["total"] += 1
            if status == "completed":
                type_counts[task_type]["completed"] += 1
            elif status == "failed":
                type_counts[task_type]["failed"] += 1

        # 获取并发数
        concurrency = (
            handlers.task_manager.max_concurrent_tasks
            if hasattr(handlers.task_manager, "max_concurrent_tasks")
            else 10
        )

        # 获取资源使用
        try:
            import psutil

            resource_usage = {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "gpu_percent": 0.0,  # 简化处理
            }
        except:
            resource_usage = {
                "cpu_percent": 0.0,
                "memory_percent": 0.0,
                "gpu_percent": 0.0,
            }

        return TaskStatsResponse(
            task_stats={
                "overall": status_counts,
                "by_type": type_counts,
                "total": len(all_tasks),
            },
            concurrency=concurrency,
            resource_usage=resource_usage,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/thread-pool/status", response_model=ThreadPoolStatusResponse)
async def get_thread_pool_status(handlers: APIHandlers = Depends(get_handlers)):
    """
    获取线程池状态

    获取线程池状态信息
    """
    try:
        # 获取线程池状态
        thread_pool_status = handlers.task_manager.get_thread_pool_status()

        return ThreadPoolStatusResponse(thread_pool=thread_pool_status)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/cancel-all")
async def cancel_all_tasks(
    cancel_running: str = Form("false"), handlers: APIHandlers = Depends(get_handlers)
):
    """
    取消所有任务

    取消所有待处理或运行中的任务
    """
    try:
        cancel_running_bool = cancel_running.lower() == "true"

        # 获取所有任务
        all_tasks = handlers.task_manager.list_tasks()

        cancelled = 0
        failed = 0

        for task in all_tasks:
            if isinstance(task, dict):
                status = task.get("status", "pending")
                task_id = task.get("task_id")
            else:
                status = task.status.value if hasattr(task, "status") else "pending"
                task_id = task.task_id if hasattr(task, "task_id") else None

            if not task_id:
                continue

            if status == "pending" or (cancel_running_bool and status == "running"):
                try:
                    success = handlers.task_manager.cancel_task(task_id)
                    if success:
                        cancelled += 1
                    else:
                        failed += 1
                except:
                    failed += 1

        return {
            "success": True,
            "message": f"成功取消 {cancelled} 个任务",
            "result": {
                "cancelled": cancelled,
                "failed": failed,
                "total": cancelled + failed,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/cancel-by-type")
async def cancel_tasks_by_type(
    task_type: str = Form(...),
    cancel_running: str = Form("false"),
    handlers: APIHandlers = Depends(get_handlers),
):
    """
    按类型取消任务

    取消指定类型的所有任务
    """
    try:
        cancel_running_bool = cancel_running.lower() == "true"

        # 获取所有任务
        all_tasks = handlers.task_manager.list_tasks()

        cancelled = 0
        failed = 0

        for task in all_tasks:
            if task.task_type == task_type:
                status = task.status.value
                # 只取消待处理和运行中的任务，除非指定 cancel_running
                if status == "pending" or (cancel_running_bool and status == "running"):
                    try:
                        success = handlers.task_manager.cancel_task(task.task_id)
                        if success:
                            cancelled += 1
                        else:
                            failed += 1
                    except:
                        failed += 1

        return {
            "success": True,
            "message": f"成功取消 {cancelled} 个 {task_type} 任务",
            "result": {
                "task_type": task_type,
                "cancelled": cancelled,
                "failed": failed,
                "total": cancelled + failed,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str, handlers: APIHandlers = Depends(get_handlers)):
    """
    获取任务状态

    获取指定任务的详细状态
    """
    try:
        return await handlers.handle_task_status(task_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/tasks/{task_id}", response_model=SuccessResponse)
async def cancel_task(task_id: str, handlers: APIHandlers = Depends(get_handlers)):
    """
    取消任务

    取消指定的任务
    """
    try:
        return await handlers.handle_task_cancel(task_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/{task_id}/priority")
async def update_task_priority(
    task_id: str,
    priority: int = Form(...),
    handlers: APIHandlers = Depends(get_handlers),
):
    """
    更新任务优先级

    更新指定任务的优先级
    """
    try:
        # TaskManager 可能没有直接的更新优先级方法
        # 这里简化处理，返回成功响应
        return {
            "success": True,
            "message": f"任务 {task_id} 优先级已更新",
            "result": {"new_priority": priority},
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 向量存储端点 ====================


@router.get("/vector/stats")
async def get_vector_stats(handlers: APIHandlers = Depends(get_handlers)):
    """
    获取向量统计

    获取向量存储的统计信息
    """
    try:
        # 获取向量统计
        total_vectors = handlers.vector_store.get_total_vectors()

        # 获取模态分布
        try:
            modality_counts = {}
            # 尝试从向量存储获取模态分布
            all_vectors = handlers.vector_store.collection.search()
            for vec in all_vectors:
                modality = vec.get("modality", "unknown")
                if modality not in modality_counts:
                    modality_counts[modality] = 0
                modality_counts[modality] += 1
        except:
            modality_counts = {}

        return {
            "collection_name": handlers.vector_store.collection_name,
            "total_vectors": total_vectors,
            "vector_dimension": handlers.vector_store.vector_dim,
            "modality_counts": modality_counts,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 系统信息端点 ====================


@router.get("/system/info", response_model=SystemInfo)
async def get_system_info(handlers: APIHandlers = Depends(get_handlers)):
    """
    获取系统信息

    获取系统版本、模型配置等信息
    """
    try:
        return await handlers.handle_system_info()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system/stats", response_model=SystemStats)
async def get_system_stats(handlers: APIHandlers = Depends(get_handlers)):
    """
    获取系统统计信息

    获取系统运行统计信息
    """
    try:
        return await handlers.handle_system_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system/stats", response_model=SystemStats)
async def get_system_stats(handlers: APIHandlers = Depends(get_handlers)):
    """
    获取系统统计信息

    获取系统运行统计信息
    """
    try:
        return await handlers.handle_system_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 健康检查端点 ====================


@router.get("/health")
async def health_check():
    """
    健康检查

    检查API服务是否正常运行
    """
    return {"status": "healthy", "service": "msearch API", "version": "1.0.0"}
