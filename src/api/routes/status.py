"""
系统状态API路由
"""

import logging
import psutil
import time
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Request

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/status")
async def get_system_status(request: Request):
    """
    获取系统状态
    
    Returns:
        系统状态信息
    """
    try:
        # 获取系统资源信息
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # 获取网络信息
        network = psutil.net_io_counters()
        
        # 获取进程信息
        process = psutil.Process()
        process_memory = process.memory_info()
        
        # 获取系统运行时间
        boot_time = psutil.boot_time()
        uptime = time.time() - boot_time
        
        # 获取服务状态
        app_state = request.app.state
        
        service_status = {
            "retrieval_engine": getattr(app_state, 'retrieval_engine', None) is not None,
            "orchestrator": getattr(app_state, 'orchestrator', None) is not None,
            "file_monitor": getattr(app_state, 'file_monitor', None) is not None
        }
        
        # 获取数据库统计
        try:
            from src.common.storage.database_adapter import DatabaseAdapter
            db_adapter = DatabaseAdapter()
            
            # 获取文件统计
            with db_adapter.get_connection() as conn:
                cursor = conn.cursor()
                
                # 总文件数
                cursor.execute("SELECT COUNT(*) FROM files")
                total_files = cursor.fetchone()[0]
                
                # 已处理文件数
                cursor.execute("SELECT COUNT(*) FROM files WHERE status = 'completed'")
                processed_files = cursor.fetchone()[0]
                
                # 待处理文件数
                cursor.execute("SELECT COUNT(*) FROM files WHERE status = 'pending'")
                pending_files = cursor.fetchone()[0]
                
                # 任务统计
                cursor.execute("SELECT status, COUNT(*) FROM tasks GROUP BY status")
                task_stats = dict(cursor.fetchall())
                
                # 向量统计
                cursor.execute("SELECT COUNT(*) FROM vectors")
                total_vectors = cursor.fetchone()[0]
            
            database_stats = {
                "total_files": total_files,
                "processed_files": processed_files,
                "pending_files": pending_files,
                "task_statistics": task_stats,
                "total_vectors": total_vectors,
                "processing_rate": processed_files / total_files * 100 if total_files > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"获取数据库统计失败: {e}")
            database_stats = {
                "error": str(e)
            }
        
        status_info = {
            "timestamp": time.time(),
            "uptime": uptime,
            "system": {
                "cpu_percent": cpu_percent,
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "used": memory.used,
                    "free": memory.free
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": (disk.used / disk.total) * 100
                },
                "network": {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv
                }
            },
            "process": {
                "pid": process.pid,
                "memory": {
                    "rss": process_memory.rss,
                    "vms": process_memory.vms
                },
                "cpu_percent": process.cpu_percent(),
                "num_threads": process.num_threads()
            },
            "services": service_status,
            "database": database_stats
        }
        
        return {
            "status": "success",
            "data": status_info
        }
        
    except Exception as e:
        logger.error(f"获取系统状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取系统状态失败: {str(e)}")


@router.get("/status/health")
async def health_check(request: Request):
    """
    健康检查
    
    Returns:
        健康状态
    """
    try:
        app_state = request.app.state
        
        # 检查核心服务状态
        services_healthy = True
        services_status = {}
        
        # 检查检索引擎
        if hasattr(app_state, 'retrieval_engine') and app_state.retrieval_engine:
            try:
                # 简单的健康检查
                if app_state.retrieval_engine.is_running:
                    services_status["retrieval_engine"] = "healthy"
                else:
                    services_status["retrieval_engine"] = "unhealthy"
                    services_healthy = False
            except Exception as e:
                services_status["retrieval_engine"] = f"error: {str(e)}"
                services_healthy = False
        else:
            services_status["retrieval_engine"] = "not_initialized"
            services_healthy = False
        
        # 检查调度器
        if hasattr(app_state, 'orchestrator') and app_state.orchestrator:
            try:
                if app_state.orchestrator.is_running:
                    services_status["orchestrator"] = "healthy"
                else:
                    services_status["orchestrator"] = "unhealthy"
                    services_healthy = False
            except Exception as e:
                services_status["orchestrator"] = f"error: {str(e)}"
                services_healthy = False
        else:
            services_status["orchestrator"] = "not_initialized"
            services_healthy = False
        
        # 检查文件监控器
        if hasattr(app_state, 'file_monitor') and app_state.file_monitor:
            try:
                if app_state.file_monitor.is_running:
                    services_status["file_monitor"] = "healthy"
                else:
                    services_status["file_monitor"] = "unhealthy"
                    services_healthy = False
            except Exception as e:
                services_status["file_monitor"] = f"error: {str(e)}"
                services_healthy = False
        else:
            services_status["file_monitor"] = "not_initialized"
            services_healthy = False
        
        # 检查数据库连接
        try:
            from src.common.storage.database_adapter import DatabaseAdapter
            db_adapter = DatabaseAdapter()
            with db_adapter.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
            services_status["database"] = "healthy"
        except Exception as e:
            services_status["database"] = f"error: {str(e)}"
            services_healthy = False
        
        # 检查系统资源
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            
            resource_warnings = []
            if cpu_percent > 90:
                resource_warnings.append(f"高CPU使用率: {cpu_percent}%")
            if memory.percent > 90:
                resource_warnings.append(f"高内存使用率: {memory.percent}%")
            
            if resource_warnings:
                services_status["resources"] = {
                    "status": "warning",
                    "warnings": resource_warnings
                }
            else:
                services_status["resources"] = {
                    "status": "healthy",
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent
                }
                
        except Exception as e:
            services_status["resources"] = f"error: {str(e)}"
            services_healthy = False
        
        overall_status = "healthy" if services_healthy else "unhealthy"
        
        return {
            "status": overall_status,
            "timestamp": time.time(),
            "services": services_status
        }
        
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return {
            "status": "error",
            "timestamp": time.time(),
            "error": str(e)
        }


@router.get("/health")
async def health(request: Request):
    """
    系统整体健康检查
    
    Returns:
        系统健康状态
    """
    return await health_check(request)


@router.get("/health/orchestrator")
async def health_orchestrator(request: Request):
    """
    调度器健康检查
    
    Returns:
        调度器健康状态
    """
    try:
        app_state = request.app.state
        
        if hasattr(app_state, 'orchestrator') and app_state.orchestrator:
            try:
                health_status = {
                    "status": "healthy" if app_state.orchestrator.is_running else "unhealthy",
                    "is_running": app_state.orchestrator.is_running,
                    "check_interval": app_state.orchestrator.check_interval,
                    "max_concurrent_tasks": app_state.orchestrator.max_concurrent_tasks
                }
            except Exception as e:
                health_status = {
                    "status": "error",
                    "error": str(e)
                }
        else:
            health_status = {
                "status": "unhealthy",
                "error": "调度器未初始化"
            }
        
        return {
            "component": "orchestrator",
            "status": health_status["status"],
            "details": health_status
        }
    except Exception as e:
        return {
            "component": "orchestrator",
            "status": "error",
            "details": {
                "error": str(e)
            }
        }


@router.get("/health/task-manager")
async def health_task_manager():
    """
    任务管理器健康检查
    
    Returns:
        任务管理器健康状态
    """
    try:
        from src.processing_service.task_manager import TaskManager
        from src.core.config_manager import get_config_manager
        
        config_manager = get_config_manager()
        task_manager = TaskManager(config_manager)
        
        # 获取任务统计
        stats = await task_manager.get_task_statistics()
        
        health_status = {
            "status": "healthy",
            "is_running": task_manager.is_running,
            "task_statistics": stats,
            "max_retry_attempts": task_manager.max_retry_attempts,
            "retry_delay": task_manager.retry_delay,
            "retry_multiplier": task_manager.retry_multiplier
        }
        
        return {
            "component": "task_manager",
            "status": "healthy",
            "details": health_status
        }
    except Exception as e:
        return {
            "component": "task_manager",
            "status": "error",
            "details": {
                "error": str(e)
            }
        }


@router.get("/health/media-processor")
async def health_media_processor():
    """
    媒体处理器健康检查
    
    Returns:
        媒体处理器健康状态
    """
    try:
        from src.processing_service.media_processor import MediaProcessor
        from src.core.config_manager import get_config_manager
        
        config_manager = get_config_manager()
        media_processor = MediaProcessor(config_manager)
        
        health_status = {
            "status": "healthy",
            "supported_formats": {
                "image": list(media_processor.image_extensions),
                "video": list(media_processor.video_extensions),
                "audio": list(media_processor.audio_extensions)
            }
        }
        
        return {
            "component": "media_processor",
            "status": "healthy",
            "details": health_status
        }
    except Exception as e:
        return {
            "component": "media_processor",
            "status": "error",
            "details": {
                "error": str(e)
            }
        }


@router.get("/health/embedding-engine")
async def health_embedding_engine():
    """
    向量化引擎健康检查
    
    Returns:
        向量化引擎健康状态
    """
    try:
        from src.common.embedding.embedding_engine import EmbeddingEngine
        from src.core.config_manager import get_config_manager
        
        config_manager = get_config_manager()
        embedding_engine = EmbeddingEngine(config_manager)
        
        # 检查模型可用性
        available_models = embedding_engine.get_available_models()
        model_info = {}
        for model in available_models:
            try:
                model_info[model] = embedding_engine.get_model_info(model)
            except Exception as e:
                model_info[model] = {
                    "status": "error",
                    "error": str(e)
                }
        
        # 执行简单的健康检查
        health_check_result = await embedding_engine.health_check()
        
        health_status = {
            "status": "healthy" if all(health_check_result.values()) else "unhealthy",
            "available_models": available_models,
            "model_info": model_info,
            "health_check": health_check_result
        }
        
        return {
            "component": "embedding_engine",
            "status": health_status["status"],
            "details": health_status
        }
    except Exception as e:
        return {
            "component": "embedding_engine",
            "status": "error",
            "details": {
                "error": str(e)
            }
        }


@router.get("/status/performance")
async def get_performance_metrics():
    """
    获取性能指标
    
    Returns:
        性能指标信息
    """
    try:
        # 获取系统性能指标
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # 获取进程性能指标
        process = psutil.Process()
        process_memory = process.memory_info()
        
        # 获取网络性能指标
        network = psutil.net_io_counters()
        
        # 获取数据库性能指标
        try:
            from src.common.storage.database_adapter import DatabaseAdapter
            db_adapter = DatabaseAdapter()
            
            with db_adapter.get_connection() as conn:
                cursor = conn.cursor()
                
                # 获取数据库大小
                cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
                db_size = cursor.fetchone()[0]
                
                # 获取索引统计
                cursor.execute("SELECT name, COUNT(*) FROM sqlite_master WHERE type = 'index' GROUP BY name")
                index_stats = dict(cursor.fetchall())
                
                # 获取表统计
                cursor.execute("""
                    SELECT name, COUNT(*) as row_count 
                    FROM sqlite_master m 
                    LEFT JOIN pragma_table_info(m.name) t ON 1=1 
                    WHERE m.type = 'table' AND m.name NOT LIKE 'sqlite_%'
                    GROUP BY m.name
                """)
                table_stats = dict(cursor.fetchall())
            
            database_performance = {
                "size_bytes": db_size,
                "size_mb": db_size / (1024 * 1024),
                "index_count": len(index_stats),
                "table_count": len(table_stats)
            }
            
        except Exception as e:
            logger.error(f"获取数据库性能指标失败: {e}")
            database_performance = {"error": str(e)}
        
        performance_metrics = {
            "timestamp": time.time(),
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": (disk.used / disk.total) * 100,
                "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
            },
            "process": {
                "cpu_percent": process.cpu_percent(),
                "memory_mb": process_memory.rss / (1024 * 1024),
                "memory_vms_mb": process_memory.vms / (1024 * 1024),
                "num_threads": process.num_threads(),
                "num_fds": process.num_fds() if hasattr(process, 'num_fds') else None
            },
            "network": {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv,
                "errin": network.errin,
                "errout": network.errout,
                "dropin": network.dropin,
                "dropout": network.dropout
            },
            "database": database_performance
        }
        
        return {
            "status": "success",
            "data": performance_metrics
        }
        
    except Exception as e:
        logger.error(f"获取性能指标失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取性能指标失败: {str(e)}")


@router.get("/status/logs")
async def get_recent_logs(
    lines: int = 100,
    level: str = "INFO"
):
    """
    获取最近的日志
    
    Args:
        lines: 返回的日志行数
        level: 日志级别过滤
        
    Returns:
        最近的日志内容
    """
    try:
        import os
        from pathlib import Path
        
        # 获取日志文件路径
        log_file = Path("./logs/msearch.log")
        
        if not log_file.exists():
            return {
                "status": "success",
                "logs": [],
                "message": "日志文件不存在"
            }
        
        # 读取日志文件的最后几行
        with open(log_file, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
        
        # 过滤日志级别
        if level.upper() != "ALL":
            filtered_lines = [
                line for line in all_lines 
                if level.upper() in line.split() or level.upper() == "ALL"
            ]
        else:
            filtered_lines = all_lines
        
        # 获取最后几行
        recent_lines = filtered_lines[-lines:] if len(filtered_lines) > lines else filtered_lines
        
        return {
            "status": "success",
            "logs": [line.strip() for line in recent_lines],
            "total_lines": len(filtered_lines),
            "requested_lines": lines
        }
        
    except Exception as e:
        logger.error(f"获取日志失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取日志失败: {str(e)}")