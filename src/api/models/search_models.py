"""
API数据模型 - 检索相关
"""
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from enum import Enum


class SearchType(str, Enum):
    """检索类型枚举"""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    MULTIMODAL = "multimodal"


class SearchRequest(BaseModel):
    """检索请求模型"""
    query: str
    search_type: SearchType = SearchType.TEXT
    limit: int = 20
    filters: Optional[Dict[str, Any]] = None
    include_metadata: bool = True


class SearchResult(BaseModel):
    """检索结果模型"""
    id: str
    score: float
    file_path: str
    file_type: str
    start_time_ms: Optional[float] = None
    end_time_ms: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class SearchResponse(BaseModel):
    """检索响应模型"""
    query: str
    results: List[SearchResult]
    total: int
    processing_time: float