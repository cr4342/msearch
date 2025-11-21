"""
文件监控API路由 - 提供文件监控状态查询、启动和停止功能
"""
import os
import logging
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel

from src.business.file_monitor import FileMonitor
from src.core.config_manager import ConfigManager

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/api/v1/monitoring", tags=["文件监控"])

# 全局文件监控实例
_file_monitor: FileMonitor = None
_config_manager: ConfigManager = None
_orchestrator = None


class MonitoringStatusResponse(BaseModel):
    """文件监控状态响应模型"""
    running: bool
    watched_directories: List[str]
    indexed_files: int = 0
    pending_files: int = 0


class StartMonitoringRequest(BaseModel):
    """启动文件监控请求模型"""
    directories: List[str] = None  # 可选，如果不提供则使用配置中的目录


class ApiResponse(BaseModel):
    """通用API响应模型"""
    success: bool
    message: str
    data: Any = None


class FileProcessingStatusResponse(BaseModel):
    """文件处理状态响应模型"""
    file_path: str
    task_id: str = None
    processing_status: str = None
    progress: int = 0
    error_message: str = None
    retry_count: int = 0
    created_at: str = None
    updated_at: str = None


class AllProcessingStatusResponse(BaseModel):
    """所有处理状态响应模型"""
    task_counts: Dict[str, int]
    total_tasks: int


def init_monitoring_service(config_manager: ConfigManager, orchestrator=None) -> FileMonitor:
    """
    初始化文件监控服务
    
    Args:
        config_manager: 配置管理器实例
        orchestrator: 处理编排器实例，用于处理文件变化
        
    Returns:
        文件监控实例
    """
    global _file_monitor, _config_manager, _orchestrator
    
    if _file_monitor is None:
        _config_manager = config_manager
        _orchestrator = orchestrator
        config = config_manager.get_all_config()
        
        # 创建文件监控实例
        _file_monitor = FileMonitor(config)
        
        # 添加文件变化回调，触发索引处理
        _file_monitor.add_callback(_handle_file_change)
        
        logger.info("文件监控服务初始化完成")
    
    return _file_monitor


def _handle_file_change(file_path: str, event_type: str):
    """
    处理文件变化，触发索引处理
    
    Args:
        file_path: 文件路径
        event_type: 事件类型
    """
    try:
        logger.info(f"检测到文件变化: {file_path}, 事件类型: {event_type}")
        
        # 如果有处理编排器，使用它来处理文件
        if _orchestrator:
            import asyncio
            try:
                # 尝试获取当前事件循环
                loop = asyncio.get_event_loop()
            except RuntimeError:
                # 如果没有事件循环，创建一个新的
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # 根据事件类型选择处理方法
            if event_type == "deleted":
                # 处理文件删除
                if loop.is_running():
                    # 如果事件循环正在运行，创建任务
                    asyncio.create_task(_orchestrator.delete_file(file_path))
                else:
                    # 如果事件循环未运行，直接运行
                    loop.run_until_complete(_orchestrator.delete_file(file_path))
            else:
                # 处理文件创建、修改和移动
                if loop.is_running():
                    # 如果事件循环正在运行，创建任务
                    asyncio.create_task(_orchestrator.process_file(file_path))
                else:
                    # 如果事件循环未运行，直接运行
                    loop.run_until_complete(_orchestrator.process_file(file_path))
        else:
            # 如果没有处理编排器，仅记录日志
            logger.info(f"文件 {file_path} 已加入处理队列(处理编排器未初始化)，事件类型: {event_type}")
        
    except Exception as e:
        logger.error(f"处理文件变化失败: {file_path}, 错误: {e}")


@router.get("/status", response_model=ApiResponse)
async def get_monitoring_status():
    """
    获取文件监控状态
    
    Returns:
        文件监控状态信息
    """
    try:
        if _file_monitor is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="文件监控服务未初始化"
            )
        
        # 获取监控状态
        is_running = _file_monitor.is_monitoring()
        watched_directories = _file_monitor.get_monitored_directories()
        
        # TODO: 获取实际的索引文件数和待处理文件数
        indexed_files = 0  # 从索引服务获取
        pending_files = 0  # 从索引服务获取
        
        status_data = MonitoringStatusResponse(
            running=is_running,
            watched_directories=watched_directories,
            indexed_files=indexed_files,
            pending_files=pending_files
        )
        
        return ApiResponse(
            success=True,
            message="获取文件监控状态成功",
            data=status_data.model_dump()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文件监控状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取文件监控状态失败: {str(e)}"
        )


@router.get("/file-status", response_model=ApiResponse)
async def get_file_processing_status(file_path: str = Query(..., description="文件路径")):
    """
    获取文件处理状态
    
    Args:
        file_path: 文件路径
        
    Returns:
        文件处理状态信息
    """
    try:
        if _orchestrator is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="处理编排器未初始化"
            )
        
        # 获取文件处理状态
        status_info = _orchestrator.get_file_processing_status(file_path)
        
        if status_info['status'] == 'success':
            return ApiResponse(
                success=True,
                message="获取文件处理状态成功",
                data=status_info
            )
        elif status_info['status'] == 'not_found':
            return ApiResponse(
                success=True,
                message="文件未被处理或任务已被清理",
                data=status_info
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=status_info.get('error', '获取文件处理状态失败')
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文件处理状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取文件处理状态失败: {str(e)}"
        )


@router.get("/processing-status", response_model=ApiResponse)
async def get_all_processing_status():
    """
    获取所有文件处理状态统计
    
    Returns:
        处理状态统计信息
    """
    try:
        if _orchestrator is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="处理编排器未初始化"
            )
        
        # 获取所有处理状态统计
        status_info = _orchestrator.get_all_processing_status()
        
        if status_info['status'] == 'success':
            return ApiResponse(
                success=True,
                message="获取处理状态统计成功",
                data=status_info
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=status_info.get('error', '获取处理状态统计失败')
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取处理状态统计失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取处理状态统计失败: {str(e)}"
        )


@router.post("/start", response_model=ApiResponse)
async def start_monitoring(request: StartMonitoringRequest = None):
    """
    启动文件监控
    
    Args:
        request: 启动监控请求，可指定监控目录
        
    Returns:
        操作结果
    """
    try:
        if _file_monitor is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="文件监控服务未初始化"
            )
        
        # 如果请求中指定了目录，更新监控目录
        if request and request.directories:
            # 停止当前监控
            if _file_monitor.is_monitoring():
                _file_monitor.stop_monitoring()
            
            # 更新监控目录
            for directory in request.directories:
                if os.path.exists(directory):
                    _file_monitor.add_directory(directory)
                else:
                    logger.warning(f"监控目录不存在: {directory}")
            
            # 更新配置
            if _config_manager:
                _config_manager.set_config('general.watch_directories', request.directories)
        
        # 启动监控
        _file_monitor.start_monitoring()
        
        return ApiResponse(
            success=True,
            message="文件监控已启动",
            data={
                "watched_directories": _file_monitor.get_monitored_directories()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"启动文件监控失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"启动文件监控失败: {str(e)}"
        )


@router.post("/stop", response_model=ApiResponse)
async def stop_monitoring():
    """
    停止文件监控
    
    Returns:
        操作结果
    """
    try:
        if _file_monitor is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="文件监控服务未初始化"
            )
        
        # 停止监控
        _file_monitor.stop_monitoring()
        
        return ApiResponse(
            success=True,
            message="文件监控已停止",
            data={}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"停止文件监控失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"停止文件监控失败: {str(e)}"
        )


@router.post("/directories/add", response_model=ApiResponse)
async def add_monitoring_directory(directory: str):
    """
    添加监控目录
    
    Args:
        directory: 要添加的目录路径
        
    Returns:
        操作结果
    """
    try:
        if _file_monitor is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="文件监控服务未初始化"
            )
        
        if not os.path.exists(directory):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"目录不存在: {directory}"
            )
        
        # 添加目录
        _file_monitor.add_directory(directory)
        
        # 更新配置
        if _config_manager:
            current_dirs = _config_manager.get_config('general.watch_directories', [])
            if directory not in current_dirs:
                current_dirs.append(directory)
                _config_manager.set_config('general.watch_directories', current_dirs)
        
        return ApiResponse(
            success=True,
            message=f"已添加监控目录: {directory}",
            data={
                "watched_directories": _file_monitor.get_monitored_directories()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"添加监控目录失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"添加监控目录失败: {str(e)}"
        )


@router.delete("/directories/{directory}", response_model=ApiResponse)
async def remove_monitoring_directory(directory: str):
    """
    移除监控目录
    
    Args:
        directory: 要移除的目录路径
        
    Returns:
        操作结果
    """
    try:
        if _file_monitor is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="文件监控服务未初始化"
            )
        
        # 移除目录
        _file_monitor.remove_directory(directory)
        
        # 更新配置
        if _config_manager:
            current_dirs = _config_manager.get_config('general.watch_directories', [])
            if directory in current_dirs:
                current_dirs.remove(directory)
                _config_manager.set_config('general.watch_directories', current_dirs)
        
        return ApiResponse(
            success=True,
            message=f"已移除监控目录: {directory}",
            data={
                "watched_directories": _file_monitor.get_monitored_directories()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"移除监控目录失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"移除监控目录失败: {str(e)}"
        )