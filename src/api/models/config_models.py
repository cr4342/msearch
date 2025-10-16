"""
API数据模型 - 配置相关
"""
from pydantic import BaseModel
from typing import Dict, Any, Optional


class ConfigRequest(BaseModel):
    """配置请求模型"""
    config: Dict[str, Any]


class ConfigResponse(BaseModel):
    """配置响应模型"""
    status: str
    message: str
    config: Optional[Dict[str, Any]] = None


class SystemStatus(BaseModel):
    """系统状态模型"""
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    uptime: float
    status: str


class StatusResponse(BaseModel):
    """状态响应模型"""
    status: str
    message: str
    data: Optional[SystemStatus] = None