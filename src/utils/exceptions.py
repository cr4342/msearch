from datetime import datetime

class MSearchError(Exception):
    """
    MSearch基础异常类
    """
    def __init__(self, message: str, error_code: str = None, cause: Exception = None):
        """
        初始化基础异常
        
        Args:
            message: 错误消息
            error_code: 错误代码（可选）
            cause: 原始异常（可选）
        """
        self.message = message
        self.error_code = error_code or "MSERR_UNKNOWN"
        self.cause = cause
        self.timestamp = datetime.now()
        
        super().__init__(message)
        
        if cause:
            self.__cause__ = cause
    
    def __str__(self):
        base_str = f"[{self.error_code}] {self.message}"
        if self.cause:
            base_str += f" (原因: {str(self.cause)})"
        return base_str
    
    def to_dict(self):
        """
        转换为字典格式
        """
        return {
            "error_code": self.error_code,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "cause": str(self.cause) if self.cause else None
        }

class VectorStorageError(MSearchError):
    """
    向量存储相关异常
    """
    def __init__(self, message: str, error_code: str = "VECTOR_STORAGE_ERROR", cause: Exception = None):
        super().__init__(message, error_code, cause)

class VectorDimensionError(MSearchError):
    """
    向量维度不匹配异常
    """
    def __init__(self, message: str, expected_dim: int = None, actual_dim: int = None, cause: Exception = None):
        self.expected_dim = expected_dim
        self.actual_dim = actual_dim
        error_msg = message
        if expected_dim is not None and actual_dim is not None:
            error_msg = f"{message} (期望: {expected_dim}, 实际: {actual_dim})"
        super().__init__(error_msg, "VECTOR_DIMENSION_ERROR", cause)

class CollectionNotFoundError(MSearchError):
    """
    集合未找到异常
    """
    def __init__(self, message: str, collection_name: str = None, cause: Exception = None):
        self.collection_name = collection_name
        super().__init__(message, "COLLECTION_NOT_FOUND", cause)

class ConnectionError(MSearchError):
    """
    连接错误异常
    """
    def __init__(self, message: str, endpoint: str = None, cause: Exception = None):
        self.endpoint = endpoint
        super().__init__(message, "CONNECTION_ERROR", cause)

class TimeoutError(MSearchError):
    """
    超时异常
    """
    def __init__(self, message: str, operation: str = None, timeout: float = None, cause: Exception = None):
        self.operation = operation
        self.timeout = timeout
        error_msg = message
        if operation and timeout:
            error_msg = f"{message} (操作: {operation}, 超时时间: {timeout}s)"
        super().__init__(error_msg, "TIMEOUT_ERROR", cause)

class ValidationError(MSearchError):
    """
    参数验证异常
    """
    def __init__(self, message: str, field: str = None, value: any = None, cause: Exception = None):
        self.field = field
        self.value = value
        error_msg = message
        if field is not None:
            error_msg = f"{message} (字段: {field})"
        super().__init__(error_msg, "VALIDATION_ERROR", cause)

class ProcessingError(MSearchError):
    """
    处理异常
    """
    def __init__(self, message: str, step: str = None, cause: Exception = None):
        self.step = step
        error_msg = message
        if step:
            error_msg = f"{message} (步骤: {step})"
        super().__init__(error_msg, "PROCESSING_ERROR", cause)
