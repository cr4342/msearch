"""
API数据模型 - 通用模型
"""
from pydantic import BaseModel
from typing import Optional, Dict, Any


class CommonResponse(BaseModel):
    """通用响应模型"""
    status: str
    message: str
    data: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """错误响应模型"""
    status: str = "error"
    message: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class HealthCheckResponse(BaseModel):
    """健康检查响应模型"""
    status: str
    message: str
    timestamp: str