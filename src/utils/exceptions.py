from datetime import datetime

# 统一错误码定义
class ErrorCode:
    """
    统一错误码定义
    格式: ERR-XXX-YYY
    - XXX: 3位功能模块代码
    - YYY: 3位错误类型代码
    """
    # 模块代码
    MODULE_GENERAL = "000"  # 通用模块
    MODULE_MONITOR = "003"  # 文件监控模块
    MODULE_MEDIA = "004"  # 媒体处理模块
    MODULE_VECTOR = "005"  # 向量化模块
    MODULE_DB = "006"  # 数据库模块
    MODULE_SEARCH = "007"  # 检索模块
    MODULE_TASK = "008"  # 任务管理模块
    MODULE_ORCH = "009"  # 调度器模块
    MODULE_API = "010"  # API服务模块
    
    # 错误类型代码
    ERROR_PARAM_INVALID = "001"  # 参数无效
    ERROR_NOT_FOUND = "002"  # 未找到
    ERROR_EXECUTION_FAILED = "003"  # 执行失败
    ERROR_TIMEOUT = "007"  # 超时
    ERROR_VALIDATION = "010"  # 验证错误
    ERROR_CONNECTION = "011"  # 连接错误
    ERROR_INTERNAL = "999"  # 内部错误
    
    # 通用错误码
    ERR_GENERAL_INVALID_PARAM = f"ERR-{MODULE_GENERAL}-{ERROR_PARAM_INVALID}"
    ERR_GENERAL_NOT_FOUND = f"ERR-{MODULE_GENERAL}-{ERROR_NOT_FOUND}"
    ERR_GENERAL_EXECUTION_FAILED = f"ERR-{MODULE_GENERAL}-{ERROR_EXECUTION_FAILED}"
    ERR_GENERAL_TIMEOUT = f"ERR-{MODULE_GENERAL}-{ERROR_TIMEOUT}"
    ERR_GENERAL_VALIDATION = f"ERR-{MODULE_GENERAL}-{ERROR_VALIDATION}"
    ERR_GENERAL_CONNECTION = f"ERR-{MODULE_GENERAL}-{ERROR_CONNECTION}"
    ERR_GENERAL_INTERNAL = f"ERR-{MODULE_GENERAL}-{ERROR_INTERNAL}"
    
    # 文件监控错误码
    ERR_MONITOR_INVALID_PATH = f"ERR-{MODULE_MONITOR}-{ERROR_PARAM_INVALID}"
    ERR_MONITOR_FILE_NOT_FOUND = f"ERR-{MODULE_MONITOR}-{ERROR_NOT_FOUND}"
    
    # 媒体处理错误码
    ERR_MEDIA_PROCESSING_FAILED = f"ERR-{MODULE_MEDIA}-{ERROR_EXECUTION_FAILED}"
    
    # 向量化错误码
    ERR_VECTOR_INVALID_INPUT = f"ERR-{MODULE_VECTOR}-{ERROR_PARAM_INVALID}"
    ERR_VECTOR_DIMENSION_MISMATCH = f"ERR-{MODULE_VECTOR}-{ERROR_EXECUTION_FAILED}"
    ERR_VECTOR_EXECUTION_FAILED = f"ERR-{MODULE_VECTOR}-{ERROR_EXECUTION_FAILED}"
    ERR_VECTOR_TIMEOUT = f"ERR-{MODULE_VECTOR}-{ERROR_TIMEOUT}"
    
    # 数据库错误码
    ERR_DB_EXECUTION_FAILED = f"ERR-{MODULE_DB}-{ERROR_EXECUTION_FAILED}"
    
    # 检索错误码
    ERR_SEARCH_EXECUTION_FAILED = f"ERR-{MODULE_SEARCH}-{ERROR_EXECUTION_FAILED}"
    
    # 任务管理错误码
    ERR_TASK_EXECUTION_FAILED = f"ERR-{MODULE_TASK}-{ERROR_EXECUTION_FAILED}"
    
    # 调度器错误码
    ERR_ORCH_INTERNAL_ERROR = f"ERR-{MODULE_ORCH}-{ERROR_INTERNAL}"
    
    # API服务错误码
    ERR_API_PARAM_INVALID = f"ERR-{MODULE_API}-{ERROR_PARAM_INVALID}"


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
        self.error_code = error_code or ErrorCode.ERR_GENERAL_INTERNAL
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
    def __init__(self, message: str, error_code: str = ErrorCode.ERR_VECTOR_EXECUTION_FAILED, cause: Exception = None):
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
        super().__init__(error_msg, ErrorCode.ERR_VECTOR_DIMENSION_MISMATCH, cause)

class CollectionNotFoundError(MSearchError):
    """
    集合未找到异常
    """
    def __init__(self, message: str, collection_name: str = None, cause: Exception = None):
        self.collection_name = collection_name
        super().__init__(message, ErrorCode.ERR_VECTOR_INVALID_INPUT, cause)

class ConnectionError(MSearchError):
    """
    连接错误异常
    """
    def __init__(self, message: str, endpoint: str = None, cause: Exception = None):
        self.endpoint = endpoint
        super().__init__(message, ErrorCode.ERR_GENERAL_CONNECTION, cause)

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
        super().__init__(error_msg, ErrorCode.ERR_GENERAL_TIMEOUT, cause)

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
        super().__init__(error_msg, ErrorCode.ERR_GENERAL_VALIDATION, cause)

class ProcessingError(MSearchError):
    """
    处理异常
    """
    def __init__(self, message: str, step: str = None, cause: Exception = None):
        self.step = step
        error_msg = message
        if step:
            error_msg = f"{message} (步骤: {step})"
        super().__init__(error_msg, ErrorCode.ERR_MEDIA_PROCESSING_FAILED, cause)

class TaskExecutionError(MSearchError):
    """
    任务执行异常
    """
    def __init__(self, message: str, task_id: str = None, cause: Exception = None):
        self.task_id = task_id
        error_msg = message
        if task_id:
            error_msg = f"{message} (任务ID: {task_id})"
        super().__init__(error_msg, ErrorCode.ERR_TASK_EXECUTION_FAILED, cause)

class OrchestratorError(MSearchError):
    """
    调度器异常
    """
    def __init__(self, message: str, cause: Exception = None):
        super().__init__(message, ErrorCode.ERR_ORCH_INTERNAL, cause)

class FileMonitorError(MSearchError):
    """
    文件监控异常
    """
    def __init__(self, message: str, path: str = None, cause: Exception = None):
        self.path = path
        error_msg = message
        if path:
            error_msg = f"{message} (路径: {path})"
        super().__init__(error_msg, ErrorCode.ERR_MONITOR_INVALID_PATH, cause)