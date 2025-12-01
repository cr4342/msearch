"""
配置管理API路由
"""

import logging
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException

from src.core.config_manager import get_config_manager

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/config")
async def get_config():
    """
    获取系统配置
    
    Returns:
        系统配置信息
    """
    try:
        config_manager = get_config_manager()
        
        # 返回非敏感配置
        config = {
            "system": config_manager.get("system", {}),
            "media_processing": config_manager.get("media_processing", {}),
            "smart_retrieval": config_manager.get("smart_retrieval", {}),
            "orchestrator": config_manager.get("orchestrator", {}),
            "task_manager": config_manager.get("task_manager", {}),
            "features": {
                "enable_clip": config_manager.get("infinity.services.clip", {}) is not None,
                "enable_clap": config_manager.get("infinity.services.clap", {}) is not None,
                "enable_whisper": config_manager.get("infinity.services.whisper", {}) is not None,
                "enable_face_recognition": config_manager.get("face_recognition.enabled", False)
            }
        }
        
        return {
            "status": "success",
            "config": config
        }
        
    except Exception as e:
        logger.error(f"获取配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}")


@router.get("/config/monitored-directories")
async def get_monitored_directories():
    """
    获取监控目录列表
    
    Returns:
        监控目录列表
    """
    try:
        config_manager = get_config_manager()
        directories = config_manager.get("system.monitored_directories", [])
        
        return {
            "status": "success",
            "directories": directories
        }
        
    except Exception as e:
        logger.error(f"获取监控目录失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取监控目录失败: {str(e)}")


@router.post("/config/monitored-directories")
async def add_monitored_directory(directory: str):
    """
    添加监控目录
    
    Args:
        directory: 目录路径
        
    Returns:
        操作结果
    """
    try:
        import os
        from pathlib import Path
        
        # 验证目录存在
        if not os.path.exists(directory):
            raise HTTPException(status_code=400, detail=f"目录不存在: {directory}")
        
        if not os.path.isdir(directory):
            raise HTTPException(status_code=400, detail=f"路径不是目录: {directory}")
        
        config_manager = get_config_manager()
        directories = config_manager.get("system.monitored_directories", [])
        
        # 检查是否已存在
        if directory in directories:
            return {
                "status": "success",
                "message": "目录已在监控列表中",
                "directories": directories
            }
        
        # 添加目录
        directories.append(directory)
        config_manager.set("system.monitored_directories", directories)
        
        # 重新加载配置
        await config_manager.reload_config()
        
        # 通知文件监控器
        from fastapi import Request
        file_monitor = Request.app.state.file_monitor
        await file_monitor.add_directory(directory)
        
        logger.info(f"添加监控目录: {directory}")
        
        return {
            "status": "success",
            "message": f"已添加监控目录: {directory}",
            "directories": directories
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"添加监控目录失败: {e}")
        raise HTTPException(status_code=500, detail=f"添加监控目录失败: {str(e)}")


@router.delete("/config/monitored-directories")
async def remove_monitored_directory(directory: str):
    """
    移除监控目录
    
    Args:
        directory: 目录路径
        
    Returns:
        操作结果
    """
    try:
        config_manager = get_config_manager()
        directories = config_manager.get("system.monitored_directories", [])
        
        # 检查是否存在
        if directory not in directories:
            raise HTTPException(status_code=404, detail=f"目录不在监控列表中: {directory}")
        
        # 移除目录
        directories.remove(directory)
        config_manager.set("system.monitored_directories", directories)
        
        # 重新加载配置
        await config_manager.reload_config()
        
        # 通知文件监控器
        from fastapi import Request
        file_monitor = Request.app.state.file_monitor
        await file_monitor.remove_directory(directory)
        
        logger.info(f"移除监控目录: {directory}")
        
        return {
            "status": "success",
            "message": f"已移除监控目录: {directory}",
            "directories": directories
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"移除监控目录失败: {e}")
        raise HTTPException(status_code=500, detail=f"移除监控目录失败: {str(e)}")


@router.get("/config/supported-extensions")
async def get_supported_extensions():
    """
    获取支持的文件扩展名
    
    Returns:
        支持的文件扩展名列表
    """
    try:
        config_manager = get_config_manager()
        extensions = config_manager.get("system.supported_extensions", [])
        
        return {
            "status": "success",
            "extensions": extensions
        }
        
    except Exception as e:
        logger.error(f"获取支持的扩展名失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取支持的扩展名失败: {str(e)}")


@router.post("/config/reload")
async def reload_config():
    """
    重新加载配置
    
    Returns:
        操作结果
    """
    try:
        config_manager = get_config_manager()
        await config_manager.reload_config()
        
        logger.info("配置已重新加载")
        
        return {
            "status": "success",
            "message": "配置已重新加载"
        }
        
    except Exception as e:
        logger.error(f"重新加载配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"重新加载配置失败: {str(e)}")


@router.get("/config/models")
async def get_model_config():
    """
    获取模型配置信息
    
    Returns:
        模型配置信息
    """
    try:
        config_manager = get_config_manager()
        
        # 获取Infinity服务配置
        infinity_config = config_manager.get("infinity.services", {})
        
        # 获取模型状态
        from fastapi import Request
        retrieval_engine = Request.app.state.retrieval_engine
        
        model_status = {}
        if retrieval_engine and retrieval_engine.embedding_engine:
            model_status = await retrieval_engine.embedding_engine.health_check()
        
        models_info = {}
        for model_name, model_config in infinity_config.items():
            models_info[model_name] = {
                "model_id": model_config.get("model_id", "unknown"),
                "device": model_config.get("device", "unknown"),
                "port": model_config.get("port", None),
                "status": "loaded" if model_status.get(model_name, False) else "unavailable"
            }
        
        return {
            "status": "success",
            "models": models_info
        }
        
    except Exception as e:
        logger.error(f"获取模型配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取模型配置失败: {str(e)}")