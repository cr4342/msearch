"""
配置API路由
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging
from src.core.config_manager import get_config_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/config", tags=["config"])

# 获取配置管理器实例
config_manager = get_config_manager()

@router.get("/")
async def get_system_config():
    """获取系统配置API"""
    try:
        config = config_manager.get_config()
        return {
            "status": "success",
            "data": config,
            "message": "系统配置获取成功"
        }
    except Exception as e:
        logger.error(f"获取系统配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取系统配置失败: {str(e)}")

@router.put("/")
async def update_system_config(config_update: Dict[str, Any]):
    """更新系统配置API"""
    try:
        # 验证配置更新
        if not config_update:
            raise HTTPException(status_code=400, detail="配置更新数据不能为空")
        
        # 更新配置
        updated_config = config_manager.update_config(config_update)
        
        return {
            "status": "success",
            "data": updated_config,
            "message": "系统配置更新成功"
        }
    except Exception as e:
        logger.error(f"更新系统配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新系统配置失败: {str(e)}")

@router.get("/status")
async def get_system_status():
    """获取系统状态API"""
    try:
        config = config_manager.get_config()
        
        # 构建系统状态信息
        status_info = {
            "system": {
                "version": "0.1.0",
                "status": "running",
                "uptime": "待实现"
            },
            "services": {
                "api_service": "running",
                "processing_service": "running",
                "search_service": "running"
            },
            "config": {
                "loaded": True,
                "last_modified": "待实现"
            }
        }
        
        return {
            "status": "success",
            "data": status_info,
            "message": "系统状态获取成功"
        }
    except Exception as e:
        logger.error(f"获取系统状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取系统状态失败: {str(e)}")