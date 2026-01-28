"""
API路由定义
定义所有API端点
"""

from fastapi import APIRouter, HTTPException, Depends, Form
from typing import Optional

from .schemas import (
    TextSearchRequest, ImageSearchRequest, VideoSearchRequest, AudioSearchRequest,
    SearchResponse,
    IndexAddRequest, IndexRemoveRequest, IndexStatusResponse,
    FilesListRequest, FilesListResponse, FileInfo,
    TasksListRequest, TasksListResponse, TaskStatusResponse,
    SystemInfo, SystemStats,
    ErrorResponse, SuccessResponse
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
        search_engine=_api_server_instance.search_engine if hasattr(_api_server_instance, 'search_engine') else None,
        file_indexer=_api_server_instance.file_indexer if hasattr(_api_server_instance, 'file_indexer') else None,
        task_manager=_api_server_instance.task_manager,
        database_manager=_api_server_instance.database_manager,
        vector_store=_api_server_instance.vector_store,
        config_manager=_api_server_instance.config
    )


# ==================== 搜索端点 ====================

@router.post("/search/text", response_model=SearchResponse)
async def search_text(
    request: TextSearchRequest,
    handlers: APIHandlers = Depends(get_handlers)
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
    request: ImageSearchRequest,
    handlers: APIHandlers = Depends(get_handlers)
):
    """
    图像搜索
    
    使用图像查询搜索相似的图像、视频文件
    """
    try:
        return await handlers.handle_image_search(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search/video", response_model=SearchResponse)
async def search_video(
    request: VideoSearchRequest,
    handlers: APIHandlers = Depends(get_handlers)
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
    request: AudioSearchRequest,
    handlers: APIHandlers = Depends(get_handlers)
):
    """
    音频搜索
    
    使用音频查询搜索相似的音频、视频文件
    """
    try:
        return await handlers.handle_audio_search(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 索引端点 ====================


@router.post("/index/file", response_model=SuccessResponse)
async def index_file(
    file_path: str = Form(...),
    handlers: APIHandlers = Depends(get_handlers)
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
    handlers: APIHandlers = Depends(get_handlers)
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
async def reindex_all(
    handlers: APIHandlers = Depends(get_handlers)
):
    """
    重新索引所有文件
    """
    try:
        return await handlers.handle_reindex_all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/index/add", response_model=SuccessResponse)
async def add_index(
    request: IndexAddRequest,
    handlers: APIHandlers = Depends(get_handlers)
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
    request: IndexRemoveRequest,
    handlers: APIHandlers = Depends(get_handlers)
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
async def get_index_status(
    handlers: APIHandlers = Depends(get_handlers)
):
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
    handlers: APIHandlers = Depends(get_handlers)
):
    """
    获取文件列表
    
    获取系统中所有文件的列表
    """
    try:
        request = FilesListRequest(
            file_type=file_type,
            indexed_only=indexed_only,
            limit=limit,
            offset=offset
        )
        return await handlers.handle_files_list(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/files/{file_uuid}", response_model=FileInfo)
async def get_file_info(
    file_uuid: str,
    handlers: APIHandlers = Depends(get_handlers)
):
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


@router.get("/files/preview")
async def get_file_preview(
    path: str,
    handlers: APIHandlers = Depends(get_handlers)
):
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
        if file_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
            return FileResponse(file_path, media_type=f"image/{file_path.suffix[1:]}")
        
        # 如果是视频文件，返回预览图
        elif file_path.suffix.lower() in ['.mp4', '.avi', '.mov', '.mkv', '.flv']:
            # 查找对应的缩略图
            thumbnail_path = handlers.database_manager.get_thumbnail_by_path(str(file_path))
            if thumbnail_path and Path(thumbnail_path).exists():
                return FileResponse(thumbnail_path, media_type="image/jpeg")
            else:
                raise HTTPException(status_code=404, detail="预览图不存在")
        
        # 如果是音频文件，返回音频可视化
        elif file_path.suffix.lower() in ['.mp3', '.wav', '.flac', '.aac', '.ogg']:
            # 返回音频波形图
            return {"error": "音频预览功能开发中"}
        
        else:
            raise HTTPException(status_code=400, detail="不支持的文件类型")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/files/thumbnail")
async def get_file_thumbnail(
    path: str,
    handlers: APIHandlers = Depends(get_handlers)
):
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

@router.get("/tasks/list", response_model=TasksListResponse)
async def list_tasks(
    task_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    handlers: APIHandlers = Depends(get_handlers)
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
            offset=offset
        )
        return await handlers.handle_tasks_list(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    handlers: APIHandlers = Depends(get_handlers)
):
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
async def cancel_task(
    task_id: str,
    handlers: APIHandlers = Depends(get_handlers)
):
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


# ==================== 系统信息端点 ====================

@router.get("/system/info", response_model=SystemInfo)
async def get_system_info(
    handlers: APIHandlers = Depends(get_handlers)
):
    """
    获取系统信息
    
    获取系统版本、模型配置等信息
    """
    try:
        return await handlers.handle_system_info()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system/stats", response_model=SystemStats)
async def get_system_stats(
    handlers: APIHandlers = Depends(get_handlers)
):
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
    return {
        "status": "healthy",
        "service": "msearch API",
        "version": "1.0.0"
    }