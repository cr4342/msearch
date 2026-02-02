"""
异常定义
定义系统异常类
"""

from typing import Any, Dict, Optional


class MSearchError(Exception):
    """MSearch自定义异常基类"""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化异常

        Args:
            message: 错误消息
            error_code: 错误代码
            context: 错误上下文
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "UNKNOWN_ERROR"
        self.context = context or {}

    def __str__(self) -> str:
        """返回错误信息"""
        return f"[{self.error_code}] {self.message}"


class ConfigError(MSearchError):
    """配置错误"""

    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, "CONFIG_ERROR", context)


class DatabaseError(MSearchError):
    """数据库错误"""

    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, "DATABASE_ERROR", context)


class VectorStoreError(MSearchError):
    """向量存储错误"""

    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, "VECTOR_STORE_ERROR", context)


class EmbeddingError(MSearchError):
    """向量化错误"""

    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, "EMBEDDING_ERROR", context)


class TaskError(MSearchError):
    """任务错误"""

    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, "TASK_ERROR", context)


class FileError(MSearchError):
    """文件错误"""

    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, "FILE_ERROR", context)


class ModelError(MSearchError):
    """模型错误"""

    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, "MODEL_ERROR", context)


class HardwareError(MSearchError):
    """硬件错误"""

    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, "HARDWARE_ERROR", context)


class ValidationError(MSearchError):
    """验证错误"""

    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, "VALIDATION_ERROR", context)


class APIError(MSearchError):
    """API错误"""

    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, "API_ERROR", context)


class CacheError(MSearchError):
    """缓存错误"""

    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, "CACHE_ERROR", context)


class MediaProcessingError(MSearchError):
    """媒体处理错误"""

    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, "MEDIA_PROCESSING_ERROR", context)


class SearchError(MSearchError):
    """搜索错误"""

    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, "SEARCH_ERROR", context)
