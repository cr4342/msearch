"""
任务管理API路由实现
提供文件处理和向量化任务管理的REST API接口
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import asyncio
import logging
from datetime import datetime
from enum import Enum

from ...processing_service.task_manager import TaskManager
from ...processing_service.orchestrator import ProcessingOrchestrator
from ...processing_service.manual_operation_manager import ManualOperationManager
from ...core.config_manager import ConfigManager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/tasks", tags=["tasks"])

# 枚举类型
class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskType(str, Enum):
    SCAN = "scan"
    PREPROCESS = "preprocess"
    VECTORIZE = "vectorize"
    FULL_SCAN = "full_scan"
    FULL_VECTORIZE = "full_vectorize"

# 数据模型
class TaskInfo(BaseModel):
    task_id: str
    task_type: TaskType
    status: TaskStatus
    file_path: Optional[str] = None
    progress: float = Field(ge=0.0, le=1.0, description="任务进度 (0.0-1.0)")
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = {}

class TaskListResponse(BaseModel):
    tasks: List[TaskInfo]
    total_count: int
    running_count: int
    pending_count: int
    completed_count: int
    failed_count: int

class ScanRequest(BaseModel):
    directories: Optional[List[str]] = None
    force_rescan: bool = Field(default=False, description="是否强制重新扫描")
    file_extensions: Optional[List[str]] = None

class VectorizeRequest(BaseModel):
    file_ids: Optional[List[str]] = None
    force_revectorize: bool = Field(default=False, description="是否强制重新向量化")
    batch_size: Optional[int] = Field(default=None, ge=1, le=128)

class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str

# 依赖注入
async def get_task_manager():
    """获取任务管理器实例"""
    config_manager = ConfigManager()
    return TaskManager(config_manager)

async def get_orchestrator():
    """获取处理调度器实例"""
    config_manager = ConfigManager()
    return ProcessingOrchestrator(config_manager)

async def get_manual_operation_manager():
    """获取手动操作管理器实例"""
    config_manager = ConfigManager()
    return ManualOperationManager(config_manager)

@router.get("/", response_model=TaskListResponse)
async def get_tasks(
    status: Optional[TaskStatus] = None,
    task_type: Optional[TaskType] = None,
    limit: int = Query(default=50, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    task_manager: TaskManager = Depends(get_task_manager)
):
    """
    获取任务列表
    
    Args:
        status: 任务状态过滤
        task_type: 任务类型过滤
        limit: 返回数量限制
        offset: 偏移量
        task_manager: 任务管理器实例
    
    Returns:
        TaskListResponse: 任务列表信息
    """
    try:
        logger.info(f"获取任务列表: status={status}, type={task_type}")
        
        # 获取任务列表
        tasks_data = await task_manager.get_tasks(
            status=status.value if status else None,
            task_type=task_type.value if task_type else None,
            limit=limit,
            offset=offset
        )
        
        # 转换为响应格式
        tasks = []
        for task_data in tasks_data["tasks"]:
            tasks.append(TaskInfo(
                task_id=task_data["task_id"],
                task_type=TaskType(task_data["task_type"]),
                status=TaskStatus(task_data["status"]),
                file_path=task_data.get("file_path"),
                progress=task_data.get("progress", 0.0),
                created_at=task_data["created_at"],
                started_at=task_data.get("started_at"),
                completed_at=task_data.get("completed_at"),
                error_message=task_data.get("error_message"),
                metadata=task_data.get("metadata", {})
            ))
        
        return TaskListResponse(
            tasks=tasks,
            total_count=tasks_data["total_count"],
            running_count=tasks_data["running_count"],
            pending_count=tasks_data["pending_count"],
            completed_count=tasks_data["completed_count"],
            failed_count=tasks_data["failed_count"]
        )
        
    except Exception as e:
        logger.error(f"获取任务列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取任务列表失败: {str(e)}")

@router.get("/{task_id}", response_model=TaskInfo)
async def get_task(
    task_id: str,
    task_manager: TaskManager = Depends(get_task_manager)
):
    """
    获取单个任务信息
    
    Args:
        task_id: 任务ID
        task_manager: 任务管理器实例
    
    Returns:
        TaskInfo: 任务信息
    """
    try:
        logger.info(f"获取任务信息: {task_id}")
        
        task_data = await task_manager.get_task(task_id)
        if not task_data:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        return TaskInfo(
            task_id=task_data["task_id"],
            task_type=TaskType(task_data["task_type"]),
            status=TaskStatus(task_data["status"]),
            file_path=task_data.get("file_path"),
            progress=task_data.get("progress", 0.0),
            created_at=task_data["created_at"],
            started_at=task_data.get("started_at"),
            completed_at=task_data.get("completed_at"),
            error_message=task_data.get("error_message"),
            metadata=task_data.get("metadata", {})
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取任务信息失败: {str(e)}")

@router.post("/scan", response_model=TaskResponse)
async def trigger_scan(
    request: ScanRequest,
    background_tasks: BackgroundTasks,
    manual_manager: ManualOperationManager = Depends(get_manual_operation_manager)
):
    """
    触发文件扫描任务
    
    Args:
        request: 扫描请求参数
        background_tasks: 后台任务
        manual_manager: 手动操作管理器实例
    
    Returns:
        TaskResponse: 任务创建结果
    """
    try:
        logger.info(f"触发文件扫描: directories={request.directories}")
        
        # 创建扫描任务
        task_id = await manual_manager.trigger_full_scan(
            directories=request.directories,
            force_rescan=request.force_rescan,
            file_extensions=request.file_extensions
        )
        
        return TaskResponse(
            task_id=task_id,
            status="success",
            message="文件扫描任务已创建"
        )
        
    except Exception as e:
        logger.error(f"触发文件扫描失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"触发文件扫描失败: {str(e)}")

@router.post("/vectorize", response_model=TaskResponse)
async def trigger_vectorization(
    request: VectorizeRequest,
    background_tasks: BackgroundTasks,
    manual_manager: ManualOperationManager = Depends(get_manual_operation_manager)
):
    """
    触发向量化任务
    
    Args:
        request: 向量化请求参数
        background_tasks: 后台任务
        manual_manager: 手动操作管理器实例
    
    Returns:
        TaskResponse: 任务创建结果
    """
    try:
        logger.info(f"触发向量化: file_ids={request.file_ids}")
        
        # 创建向量化任务
        task_id = await manual_manager.trigger_vectorization(
            file_ids=request.file_ids,
            force_revectorize=request.force_revectorize,
            batch_size=request.batch_size
        )
        
        return TaskResponse(
            task_id=task_id,
            status="success",
            message="向量化任务已创建"
        )
        
    except Exception as e:
        logger.error(f"触发向量化失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"触发向量化失败: {str(e)}")

@router.post("/full-process", response_model=TaskResponse)
async def trigger_full_process(
    request: ScanRequest,
    background_tasks: BackgroundTasks,
    manual_manager: ManualOperationManager = Depends(get_manual_operation_manager)
):
    """
    触发完整处理流程（扫描 + 向量化）
    
    Args:
        request: 处理请求参数
        background_tasks: 后台任务
        manual_manager: 手动操作管理器实例
    
    Returns:
        TaskResponse: 任务创建结果
    """
    try:
        logger.info(f"触发完整处理流程: directories={request.directories}")
        
        # 创建完整处理任务
        task_id = await manual_manager.trigger_full_process(
            directories=request.directories,
            force_rescan=request.force_rescan,
            file_extensions=request.file_extensions
        )
        
        return TaskResponse(
            task_id=task_id,
            status="success",
            message="完整处理任务已创建"
        )
        
    except Exception as e:
        logger.error(f"触发完整处理失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"触发完整处理失败: {str(e)}")

@router.delete("/{task_id}", response_model=TaskResponse)
async def cancel_task(
    task_id: str,
    task_manager: TaskManager = Depends(get_task_manager)
):
    """
    取消任务
    
    Args:
        task_id: 任务ID
        task_manager: 任务管理器实例
    
    Returns:
        TaskResponse: 取消结果
    """
    try:
        logger.info(f"取消任务: {task_id}")
        
        success = await task_manager.cancel_task(task_id)
        
        if success:
            return TaskResponse(
                task_id=task_id,
                status="success",
                message="任务已取消"
            )
        else:
            raise HTTPException(status_code=400, detail="任务无法取消或不存在")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取消任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"取消任务失败: {str(e)}")

@router.post("/{task_id}/retry", response_model=TaskResponse)
async def retry_task(
    task_id: str,
    task_manager: TaskManager = Depends(get_task_manager)
):
    """
    重试失败的任务
    
    Args:
        task_id: 任务ID
        task_manager: 任务管理器实例
    
    Returns:
        TaskResponse: 重试结果
    """
    try:
        logger.info(f"重试任务: {task_id}")
        
        new_task_id = await task_manager.retry_task(task_id)
        
        return TaskResponse(
            task_id=new_task_id,
            status="success",
            message="任务重试已创建"
        )
        
    except Exception as e:
        logger.error(f"重试任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"重试任务失败: {str(e)}")

@router.get("/stats/summary")
async def get_task_stats(
    task_manager: TaskManager = Depends(get_task_manager)
):
    """
    获取任务统计信息
    
    Returns:
        Dict: 任务统计数据
    """
    try:
        logger.info("获取任务统计信息")
        
        stats = await task_manager.get_task_stats()
        
        return {
            "status": "success",
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"获取任务统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取任务统计失败: {str(e)}")

@router.delete("/", response_model=Dict[str, Any])
async def clear_completed_tasks(
    older_than_days: int = Query(default=7, ge=1, le=365),
    task_manager: TaskManager = Depends(get_task_manager)
):
    """
    清理已完成的任务
    
    Args:
        older_than_days: 清理多少天前的任务
        task_manager: 任务管理器实例
    
    Returns:
        Dict: 清理结果
    """
    try:
        logger.info(f"清理已完成任务: older_than_days={older_than_days}")
        
        cleared_count = await task_manager.clear_completed_tasks(older_than_days)
        
        return {
            "status": "success",
            "message": f"已清理 {cleared_count} 个已完成任务",
            "cleared_count": cleared_count
        }
        
    except Exception as e:
        logger.error(f"清理任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"清理任务失败: {str(e)}")

@router.get("/progress/live")
async def get_live_progress(
    task_manager: TaskManager = Depends(get_task_manager)
):
    """
    获取实时任务进度
    
    Returns:
        Dict: 实时进度信息
    """
    try:
        progress_data = await task_manager.get_live_progress()
        
        return {
            "status": "success",
            "progress": progress_data
        }
        
    except Exception as e:
        logger.error(f"获取实时进度失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取实时进度失败: {str(e)}")