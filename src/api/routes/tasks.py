"""
任务管理API路由
"""

import logging
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Query, Request

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/tasks")
async def get_tasks(
    status: str = Query(None, description="任务状态过滤"),
    limit: int = Query(50, ge=1, le=1000, description="返回任务数量限制")
):
    """
    获取任务列表
    
    Args:
        status: 任务状态过滤 (pending, processing, completed, failed, retry)
        limit: 返回任务数量限制
        
    Returns:
        任务列表
    """
    try:
        from src.processing_service.task_manager import TaskManager
        from src.core.config_manager import get_config_manager
        
        config_manager = get_config_manager()
        task_manager = TaskManager(config_manager)
        
        if status:
            if status == "pending":
                tasks = await task_manager.get_pending_tasks(limit)
            elif status == "processing":
                tasks = await task_manager.get_processing_tasks()
            elif status == "failed":
                tasks = await task_manager.get_failed_tasks(limit)
            elif status == "retry":
                tasks = await task_manager.db_adapter.get_tasks_by_status("retry", limit)
            else:
                # 获取所有状态的任务
                tasks = await task_manager.db_adapter.get_tasks_by_status(status, limit)
        else:
            # 获取所有任务
            from src.common.storage.database_adapter import DatabaseAdapter
            db_adapter = DatabaseAdapter()
            
            with db_adapter.get_connection() as conn:
                import sqlite3
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                query = "SELECT * FROM tasks ORDER BY created_at DESC LIMIT ?"
                cursor.execute(query, (limit,))
                results = cursor.fetchall()
                
                tasks = [dict(row) for row in results]
        
        return {
            "status": "success",
            "total_tasks": len(tasks),
            "tasks": tasks
        }
        
    except Exception as e:
        logger.error(f"获取任务列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取任务列表失败: {str(e)}")


@router.get("/tasks/{task_id}")
async def get_task(task_id: str):
    """
    获取任务详情
    
    Args:
        task_id: 任务ID
        
    Returns:
        任务详情
    """
    try:
        from src.processing_service.task_manager import TaskManager
        from src.core.config_manager import get_config_manager
        
        config_manager = get_config_manager()
        task_manager = TaskManager(config_manager)
        task = await task_manager.get_task(task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")
        
        return {
            "status": "success",
            "task": task
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务详情失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取任务详情失败: {str(e)}")


@router.post("/tasks/{task_id}/retry")
async def retry_task(task_id: str):
    """
    重试任务
    
    Args:
        task_id: 任务ID
        
    Returns:
        操作结果
    """
    try:
        from src.processing_service.task_manager import TaskManager
        from src.core.config_manager import get_config_manager
        
        config_manager = get_config_manager()
        task_manager = TaskManager(config_manager)
        success = await task_manager.retry_failed_task(task_id)
        
        if not success:
            raise HTTPException(status_code=400, detail=f"任务重试失败: {task_id}")
        
        return {
            "status": "success",
            "message": f"任务重试成功: {task_id}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重试任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"重试任务失败: {str(e)}")


@router.get("/tasks/statistics")
async def get_task_statistics():
    """
    获取任务统计信息
    
    Returns:
        任务统计信息
    """
    try:
        from src.processing_service.task_manager import TaskManager
        from src.core.config_manager import get_config_manager
        
        config_manager = get_config_manager()
        task_manager = TaskManager(config_manager)
        stats = await task_manager.get_task_statistics()
        
        return {
            "status": "success",
            "statistics": stats
        }
        
    except Exception as e:
        logger.error(f"获取任务统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取任务统计失败: {str(e)}")


@router.delete("/tasks/cleanup")
async def cleanup_old_tasks(
    days: int = Query(30, ge=1, le=365, description="保留天数")
):
    """
    清理旧任务
    
    Args:
        days: 保留天数
        
    Returns:
        操作结果
    """
    try:
        from src.processing_service.task_manager import TaskManager
        from src.core.config_manager import get_config_manager
        
        config_manager = get_config_manager()
        task_manager = TaskManager(config_manager)
        deleted_count = await task_manager.cleanup_old_tasks(days)
        
        return {
            "status": "success",
            "deleted_count": deleted_count,
            "message": f"已清理 {deleted_count} 个旧任务"
        }
        
    except Exception as e:
        logger.error(f"清理旧任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"清理旧任务失败: {str(e)}")


@router.get("/tasks/files/{file_id}")
async def get_file_tasks(file_id: str):
    """
    获取文件的所有任务
    
    Args:
        file_id: 文件ID
        
    Returns:
        文件任务列表
    """
    try:
        from src.common.storage.database_adapter import DatabaseAdapter
        
        db_adapter = DatabaseAdapter()
        
        with db_adapter.get_connection() as conn:
            import sqlite3
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT * FROM tasks WHERE file_id = ? ORDER BY created_at DESC",
                (file_id,)
            )
            results = cursor.fetchall()
            
            tasks = [dict(row) for row in results]
        
        return {
            "status": "success",
            "file_id": file_id,
            "total_tasks": len(tasks),
            "tasks": tasks
        }
        
    except Exception as e:
        logger.error(f"获取文件任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取文件任务失败: {str(e)}")


@router.post("/tasks/pause")
async def pause_task_processing(request: Request):
    """
    暂停任务处理
    
    Returns:
        操作结果
    """
    try:
        orchestrator = request.app.state.orchestrator
        
        if not orchestrator:
            raise HTTPException(status_code=503, detail="调度器服务不可用")
        
        # 暂停调度器
        orchestrator.is_running = False
        
        logger.info("任务处理已暂停")
        
        return {
            "status": "success",
            "message": "任务处理已暂停"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"暂停任务处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"暂停任务处理失败: {str(e)}")


@router.post("/tasks/resume")
async def resume_task_processing(request: Request):
    """
    恢复任务处理
    
    Returns:
        操作结果
    """
    try:
        orchestrator = request.app.state.orchestrator
        
        if not orchestrator:
            raise HTTPException(status_code=503, detail="调度器服务不可用")
        
        # 恢复调度器
        if not orchestrator.is_running:
            orchestrator.is_running = True
            # 重新启动调度循环
            orchestrator.scheduler_task = orchestrator.loop.create_task(orchestrator._scheduler_loop())
        
        logger.info("任务处理已恢复")
        
        return {
            "status": "success",
            "message": "任务处理已恢复"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"恢复任务处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"恢复任务处理失败: {str(e)}")


@router.get("/tasks/queue")
async def get_task_queue_status():
    """
    获取任务队列状态
    
    Returns:
        任务队列状态信息
    """
    try:
        from src.processing_service.task_manager import TaskManager
        from src.common.storage.database_adapter import DatabaseAdapter
        from src.core.config_manager import get_config_manager
        
        config_manager = get_config_manager()
        task_manager = TaskManager(config_manager)
        db_adapter = DatabaseAdapter()
        
        # 获取各状态任务数量
        stats = await task_manager.get_task_statistics()
        
        # 获取待处理任务详情
        pending_tasks = await task_manager.get_pending_tasks(10)
        
        # 获取正在处理任务详情
        processing_tasks = await task_manager.get_processing_tasks()
        
        # 获取重试任务详情
        retry_tasks = await task_manager.db_adapter.get_tasks_by_status("retry", 10)
        
        queue_status = {
            "statistics": stats,
            "pending_tasks": pending_tasks[:5],  # 只返回前5个
            "processing_tasks": processing_tasks[:5],  # 只返回前5个
            "retry_tasks": retry_tasks[:5],  # 只返回前5个
            "queue_length": {
                "pending": len(pending_tasks),
                "processing": len(processing_tasks),
                "retry": len(retry_tasks)
            }
        }
        
        return {
            "status": "success",
            "queue_status": queue_status
        }
        
    except Exception as e:
        logger.error(f"获取任务队列状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取任务队列状态失败: {str(e)}")