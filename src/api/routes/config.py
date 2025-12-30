"""
配置管理API路由实现
提供系统配置管理的REST API接口
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging
from pathlib import Path

from ...core.config_manager import ConfigManager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/config", tags=["config"])

# 数据模型
class MonitoringConfig(BaseModel):
    directories: List[str] = Field(..., description="监控目录列表")
    file_extensions: List[str] = Field(default=[], description="监控的文件扩展名")
    exclude_patterns: List[str] = Field(default=[], description="排除的文件模式")
    auto_process: bool = Field(default=True, description="是否自动处理新文件")

class PerformanceConfig(BaseModel):
    batch_size: int = Field(default=32, ge=1, le=128, description="批处理大小")
    max_workers: int = Field(default=4, ge=1, le=16, description="最大工作线程数")
    cache_size: int = Field(default=1000, ge=100, le=10000, description="缓存大小")
    gpu_memory_limit: Optional[float] = Field(default=None, ge=0.1, le=1.0, description="GPU内存限制比例")

class ModelConfig(BaseModel):
    clip_model: str = Field(default="openai/clip-vit-base-patch32", description="CLIP模型名称")
    clap_model: str = Field(default="laion/clap-htsat-fused", description="CLAP模型名称")
    whisper_model: str = Field(default="openai/whisper-base", description="Whisper模型名称")
    face_model: str = Field(default="facenet-pytorch", description="人脸识别模型名称")
    device: str = Field(default="auto", description="设备类型: auto, cpu, cuda")

class DatabaseConfig(BaseModel):
    sqlite_path: str = Field(..., description="SQLite数据库路径")
    milvus_host: str = Field(default="localhost", description="Milvus主机地址")
    milvus_port: int = Field(default=19530, ge=1, le=65535, description="Milvus端口")
    vector_dim: int = Field(default=512, ge=128, le=2048, description="向量维度")

class SystemConfig(BaseModel):
    monitoring: MonitoringConfig
    performance: PerformanceConfig
    models: ModelConfig
    database: DatabaseConfig
    log_level: str = Field(default="INFO", description="日志级别")
    data_directory: str = Field(..., description="数据目录路径")

class ConfigResponse(BaseModel):
    config: SystemConfig
    status: str = "success"
    message: str = ""

# 依赖注入
async def get_config_manager():
    """获取配置管理器实例"""
    return ConfigManager()

@router.get("/", response_model=ConfigResponse)
async def get_config(
    config_manager: ConfigManager = Depends(get_config_manager)
):
    """
    获取当前系统配置
    
    Returns:
        ConfigResponse: 系统配置信息
    """
    try:
        logger.info("获取系统配置")
        
        # 获取配置数据
        config_data = config_manager.get_all_config()
        
        # 构建配置对象
        system_config = SystemConfig(
            monitoring=MonitoringConfig(
                directories=config_data.get("monitoring", {}).get("directories", []),
                file_extensions=config_data.get("monitoring", {}).get("file_extensions", []),
                exclude_patterns=config_data.get("monitoring", {}).get("exclude_patterns", []),
                auto_process=config_data.get("monitoring", {}).get("auto_process", True)
            ),
            performance=PerformanceConfig(
                batch_size=config_data.get("performance", {}).get("batch_size", 32),
                max_workers=config_data.get("performance", {}).get("max_workers", 4),
                cache_size=config_data.get("performance", {}).get("cache_size", 1000),
                gpu_memory_limit=config_data.get("performance", {}).get("gpu_memory_limit")
            ),
            models=ModelConfig(
                clip_model=config_data.get("models", {}).get("clip_model", "openai/clip-vit-base-patch32"),
                clap_model=config_data.get("models", {}).get("clap_model", "laion/clap-htsat-fused"),
                whisper_model=config_data.get("models", {}).get("whisper_model", "openai/whisper-base"),
                face_model=config_data.get("models", {}).get("face_model", "facenet-pytorch"),
                device=config_data.get("models", {}).get("device", "auto")
            ),
            database=DatabaseConfig(
                sqlite_path=config_data.get("database", {}).get("sqlite_path", "data/msearch.db"),
                milvus_host=config_data.get("database", {}).get("milvus_host", "localhost"),
                milvus_port=config_data.get("database", {}).get("milvus_port", 19530),
                vector_dim=config_data.get("database", {}).get("vector_dim", 512)
            ),
            log_level=config_data.get("system", {}).get("log_level", "INFO"),
            data_directory=config_data.get("system", {}).get("data_directory", "data")
        )
        
        return ConfigResponse(
            config=system_config,
            status="success",
            message="配置获取成功"
        )
        
    except Exception as e:
        logger.error(f"获取配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}")

@router.post("/", response_model=ConfigResponse)
async def update_config(
    config: SystemConfig,
    config_manager: ConfigManager = Depends(get_config_manager)
):
    """
    更新系统配置
    
    Args:
        config: 新的系统配置
        config_manager: 配置管理器实例
    
    Returns:
        ConfigResponse: 更新结果
    """
    try:
        logger.info("更新系统配置")
        
        # 转换为配置字典
        config_dict = {
            "monitoring": {
                "directories": config.monitoring.directories,
                "file_extensions": config.monitoring.file_extensions,
                "exclude_patterns": config.monitoring.exclude_patterns,
                "auto_process": config.monitoring.auto_process
            },
            "performance": {
                "batch_size": config.performance.batch_size,
                "max_workers": config.performance.max_workers,
                "cache_size": config.performance.cache_size,
                "gpu_memory_limit": config.performance.gpu_memory_limit
            },
            "models": {
                "clip_model": config.models.clip_model,
                "clap_model": config.models.clap_model,
                "whisper_model": config.models.whisper_model,
                "face_model": config.models.face_model,
                "device": config.models.device
            },
            "database": {
                "sqlite_path": config.database.sqlite_path,
                "milvus_host": config.database.milvus_host,
                "milvus_port": config.database.milvus_port,
                "vector_dim": config.database.vector_dim
            },
            "system": {
                "log_level": config.log_level,
                "data_directory": config.data_directory
            }
        }
        
        # 更新配置
        await config_manager.update_config(config_dict)
        
        return ConfigResponse(
            config=config,
            status="success",
            message="配置更新成功"
        )
        
    except Exception as e:
        logger.error(f"更新配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新配置失败: {str(e)}")

@router.post("/monitoring", response_model=Dict[str, Any])
async def update_monitoring_config(
    monitoring_config: MonitoringConfig,
    config_manager: ConfigManager = Depends(get_config_manager)
):
    """
    更新监控配置
    
    Args:
        monitoring_config: 监控配置
        config_manager: 配置管理器实例
    
    Returns:
        Dict: 更新结果
    """
    try:
        logger.info("更新监控配置")
        
        # 验证目录路径
        for directory in monitoring_config.directories:
            if not Path(directory).exists():
                raise HTTPException(status_code=400, detail=f"目录不存在: {directory}")
        
        # 更新监控配置
        await config_manager.update_config({
            "monitoring": {
                "directories": monitoring_config.directories,
                "file_extensions": monitoring_config.file_extensions,
                "exclude_patterns": monitoring_config.exclude_patterns,
                "auto_process": monitoring_config.auto_process
            }
        })
        
        return {
            "status": "success",
            "message": "监控配置更新成功",
            "directories_count": len(monitoring_config.directories)
        }
        
    except Exception as e:
        logger.error(f"更新监控配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新监控配置失败: {str(e)}")

@router.post("/performance", response_model=Dict[str, Any])
async def update_performance_config(
    performance_config: PerformanceConfig,
    config_manager: ConfigManager = Depends(get_config_manager)
):
    """
    更新性能配置
    
    Args:
        performance_config: 性能配置
        config_manager: 配置管理器实例
    
    Returns:
        Dict: 更新结果
    """
    try:
        logger.info("更新性能配置")
        
        # 更新性能配置
        await config_manager.update_config({
            "performance": {
                "batch_size": performance_config.batch_size,
                "max_workers": performance_config.max_workers,
                "cache_size": performance_config.cache_size,
                "gpu_memory_limit": performance_config.gpu_memory_limit
            }
        })
        
        return {
            "status": "success",
            "message": "性能配置更新成功",
            "batch_size": performance_config.batch_size,
            "max_workers": performance_config.max_workers
        }
        
    except Exception as e:
        logger.error(f"更新性能配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新性能配置失败: {str(e)}")

@router.post("/models", response_model=Dict[str, Any])
async def update_model_config(
    model_config: ModelConfig,
    config_manager: ConfigManager = Depends(get_config_manager)
):
    """
    更新模型配置
    
    Args:
        model_config: 模型配置
        config_manager: 配置管理器实例
    
    Returns:
        Dict: 更新结果
    """
    try:
        logger.info("更新模型配置")
        
        # 更新模型配置
        await config_manager.update_config({
            "models": {
                "clip_model": model_config.clip_model,
                "clap_model": model_config.clap_model,
                "whisper_model": model_config.whisper_model,
                "face_model": model_config.face_model,
                "device": model_config.device
            }
        })
        
        return {
            "status": "success",
            "message": "模型配置更新成功",
            "device": model_config.device
        }
        
    except Exception as e:
        logger.error(f"更新模型配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新模型配置失败: {str(e)}")

@router.get("/validate")
async def validate_config(
    config_manager: ConfigManager = Depends(get_config_manager)
):
    """
    验证当前配置的有效性
    
    Returns:
        Dict: 验证结果
    """
    try:
        logger.info("验证配置")
        
        validation_results = await config_manager.validate_config()
        
        return {
            "status": "success" if validation_results["is_valid"] else "error",
            "message": "配置验证完成",
            "validation_results": validation_results
        }
        
    except Exception as e:
        logger.error(f"配置验证失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"配置验证失败: {str(e)}")

@router.post("/reset")
async def reset_config(
    config_manager: ConfigManager = Depends(get_config_manager)
):
    """
    重置配置为默认值
    
    Returns:
        Dict: 重置结果
    """
    try:
        logger.info("重置配置")
        
        await config_manager.reset_to_default()
        
        return {
            "status": "success",
            "message": "配置已重置为默认值"
        }
        
    except Exception as e:
        logger.error(f"重置配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"重置配置失败: {str(e)}")

@router.get("/directories/validate")
async def validate_directories(
    directories: List[str],
    config_manager: ConfigManager = Depends(get_config_manager)
):
    """
    验证目录路径的有效性
    
    Args:
        directories: 要验证的目录列表
    
    Returns:
        Dict: 验证结果
    """
    try:
        logger.info(f"验证目录: {directories}")
        
        validation_results = []
        for directory in directories:
            path = Path(directory)
            result = {
                "path": directory,
                "exists": path.exists(),
                "is_directory": path.is_dir() if path.exists() else False,
                "readable": path.exists() and os.access(path, os.R_OK),
                "writable": path.exists() and os.access(path, os.W_OK)
            }
            validation_results.append(result)
        
        all_valid = all(r["exists"] and r["is_directory"] and r["readable"] for r in validation_results)
        
        return {
            "status": "success" if all_valid else "warning",
            "message": "目录验证完成",
            "all_valid": all_valid,
            "results": validation_results
        }
        
    except Exception as e:
        logger.error(f"目录验证失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"目录验证失败: {str(e)}")