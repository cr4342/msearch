"""
统一错误处理系统
提供错误分类、重试机制、优雅降级等功能
"""

import asyncio
import logging
import time
import traceback
from typing import Any, Dict, List, Optional, Callable, Union
from dataclasses import dataclass, asdict
from enum import Enum
from functools import wraps

from src.core.config_manager import get_config_manager


class ErrorSeverity(Enum):
    """错误严重级别"""
    LOW = "low"          # 轻微错误，不影响核心功能
    MEDIUM = "medium"    # 中等错误，部分功能受影响
    HIGH = "high"        # 严重错误，核心功能受影响
    CRITICAL = "critical"  # 关键错误，系统可能崩溃


class ErrorCategory(Enum):
    """错误分类"""
    SYSTEM = "system"              # 系统错误
    NETWORK = "network"            # 网络错误
    DATABASE = "database"          # 数据库错误
    AI_MODEL = "ai_model"          # AI模型错误
    FILE_PROCESSING = "file_processing"  # 文件处理错误
    CONFIGURATION = "configuration"  # 配置错误
    PERMISSION = "permission"      # 权限错误
    RESOURCE = "resource"          # 资源错误
    UNKNOWN = "unknown"            # 未知错误


class RetryStrategy(Enum):
    """重试策略"""
    FIXED_INTERVAL = "fixed_interval"      # 固定间隔
    EXPONENTIAL_BACKOFF = "exponential_backoff"  # 指数退避
    LINEAR_BACKOFF = "linear_backoff"      # 线性退避
    IMMEDIATE_RETRY = "immediate_retry"    # 立即重试


@dataclass
class ErrorInfo:
    """错误信息数据类"""
    error_id: str
    timestamp: float
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    details: Dict[str, Any]
    stack_trace: Optional[str] = None
    component: Optional[str] = None
    operation: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    recoverable: bool = True
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class RetryConfig:
    """重试配置"""
    max_attempts: int = 3
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    base_delay: float = 1.0
    max_delay: float = 60.0
    backoff_multiplier: float = 2.0
    jitter: bool = True
    recoverable_errors: List[Exception] = None


class ErrorClassifier:
    """错误分类器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 错误分类规则
        self.error_rules = {
            # 系统错误
            ErrorCategory.SYSTEM: [
                "MemoryError",
                "DiskError", 
                "OSError",
                "SystemError"
            ],
            # 网络错误
            ErrorCategory.NETWORK: [
                "ConnectionError",
                "TimeoutError",
                "NetworkError",
                "URLError",
                "ConnectionRefusedError",
                "ConnectionResetError"
            ],
            # 数据库错误
            ErrorCategory.DATABASE: [
                "DatabaseError",
                "IntegrityError",
                "OperationalError",
                "ProgrammingError",
                "sqlite3.Error"
            ],
            # AI模型错误
            ErrorCategory.AI_MODEL: [
                "ModelError",
                "ModelNotLoadedError",
                "InferenceError",
                "CUDAError",
                "TorchError"
            ],
            # 文件处理错误
            ErrorCategory.FILE_PROCESSING: [
                "FileNotFoundError",
                "PermissionError",
                "FileFormatError",
                "CorruptedFileError"
            ],
            # 配置错误
            ErrorCategory.CONFIGURATION: [
                "ConfigurationError",
                "ConfigNotFoundError",
                "InvalidConfigError"
            ],
            # 权限错误
            ErrorCategory.PERMISSION: [
                "PermissionError",
                "AccessDeniedError"
            ],
            # 资源错误
            ErrorCategory.RESOURCE: [
                "ResourceError",
                "ResourceExhaustedError",
                "OutOfMemoryError"
            ]
        }
    
    def classify_error(self, error: Exception) -> tuple[ErrorCategory, ErrorSeverity]:
        """分类错误"""
        error_name = type(error).__name__
        error_message = str(error).lower()
        
        # 根据错误类型分类
        for category, error_types in self.error_rules.items():
            for error_type in error_types:
                if error_type.lower() in error_name.lower():
                    return category, self._determine_severity(category, error, error_message)
        
        # 根据错误消息分类
        if any(keyword in error_message for keyword in ["timeout", "connection", "network"]):
            return ErrorCategory.NETWORK, self._determine_severity(ErrorCategory.NETWORK, error, error_message)
        
        elif any(keyword in error_message for keyword in ["database", "sqlite", "sql"]):
            return ErrorCategory.DATABASE, self._determine_severity(ErrorCategory.DATABASE, error, error_message)
        
        elif any(keyword in error_message for keyword in ["model", "ai", "inference", "cuda"]):
            return ErrorCategory.AI_MODEL, self._determine_severity(ErrorCategory.AI_MODEL, error, error_message)
        
        elif any(keyword in error_message for keyword in ["file", "not found", "permission"]):
            return ErrorCategory.FILE_PROCESSING, self._determine_severity(ErrorCategory.FILE_PROCESSING, error, error_message)
        
        else:
            return ErrorCategory.UNKNOWN, ErrorSeverity.MEDIUM
    
    def _determine_severity(self, category: ErrorCategory, error: Exception, message: str) -> ErrorSeverity:
        """确定错误严重级别"""
        # 根据错误类型和上下文确定严重级别
        if category == ErrorCategory.SYSTEM:
            return ErrorSeverity.CRITICAL
        elif category == ErrorCategory.AI_MODEL:
            return ErrorSeverity.HIGH
        elif category == ErrorCategory.DATABASE:
            return ErrorSeverity.HIGH
        elif category == ErrorCategory.NETWORK:
            return ErrorSeverity.MEDIUM
        elif category == ErrorCategory.FILE_PROCESSING:
            return ErrorSeverity.MEDIUM
        elif category == ErrorCategory.CONFIGURATION:
            return ErrorSeverity.HIGH
        elif category == ErrorCategory.PERMISSION:
            return ErrorSeverity.HIGH
        elif category == ErrorCategory.RESOURCE:
            return ErrorSeverity.HIGH
        else:
            return ErrorSeverity.MEDIUM


class RetryManager:
    """重试管理器"""
    
    def __init__(self, config_manager=None):
        self.config_manager = config_manager or get_config_manager()
        self.logger = logging.getLogger(__name__)
        
        # 默认重试配置
        self.default_retry_config = RetryConfig(
            max_attempts=self.config_manager.get("error_handling.retry.max_attempts", 3),
            strategy=RetryStrategy(self.config_manager.get("error_handling.retry.strategy", "exponential_backoff")),
            base_delay=self.config_manager.get("error_handling.retry.base_delay", 1.0),
            max_delay=self.config_manager.get("error_handling.retry.max_delay", 60.0),
            backoff_multiplier=self.config_manager.get("error_handling.retry.backoff_multiplier", 2.0)
        )
        
        # 统计信息
        self.retry_stats = {
            'total_retries': 0,
            'successful_retries': 0,
            'failed_retries': 0,
            'max_retries_reached': 0
        }
    
    def calculate_delay(self, attempt: int, config: RetryConfig) -> float:
        """计算重试延迟"""
        import random
        
        if config.strategy == RetryStrategy.IMMEDIATE_RETRY:
            return 0
        
        elif config.strategy == RetryStrategy.FIXED_INTERVAL:
            delay = config.base_delay
        
        elif config.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = config.base_delay * attempt
        
        elif config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = config.base_delay * (config.backoff_multiplier ** (attempt - 1))
        
        else:
            delay = config.base_delay
        
        # 限制最大延迟
        delay = min(delay, config.max_delay)
        
        # 添加抖动
        if config.jitter:
            delay = delay * (0.5 + random.random() * 0.5)
        
        return delay
    
    def should_retry(self, error: Exception, attempt: int, config: RetryConfig) -> bool:
        """判断是否应该重试"""
        if attempt >= config.max_attempts:
            return False
        
        # 检查是否可重试的错误
        if config.recoverable_errors:
            return any(isinstance(error, recoverable_error) for recoverable_error in config.recoverable_errors)
        
        # 默认可重试的错误类型
        retryable_errors = (
            ConnectionError,
            TimeoutError,
            OSError,
            DatabaseError,
            TemporaryError
        )
        
        return isinstance(error, retryable_errors)
    
    async def execute_with_retry(self, func: Callable, *args, retry_config: Optional[RetryConfig] = None, **kwargs) -> Any:
        """执行函数并重试"""
        config = retry_config or self.default_retry_config
        
        last_exception = None
        
        for attempt in range(1, config.max_attempts + 1):
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                # 成功执行
                if attempt > 1:
                    self.retry_stats['successful_retries'] += 1
                    self.logger.info(f"函数重试成功: {func.__name__}, 尝试次数: {attempt}")
                
                return result
                
            except Exception as e:
                last_exception = e
                self.retry_stats['total_retries'] += 1
                
                self.logger.warning(f"函数执行失败: {func.__name__}, 尝试 {attempt}/{config.max_attempts}, 错误: {e}")
                
                # 判断是否应该重试
                if not self.should_retry(e, attempt, config):
                    self.retry_stats['max_retries_reached'] += 1
                    self.logger.error(f"达到最大重试次数: {func.__name__}, 放弃重试")
                    break
                
                # 计算延迟并等待
                if attempt < config.max_attempts:
                    delay = self.calculate_delay(attempt, config)
                    self.logger.info(f"等待重试延迟: {delay:.2f}秒")
                    await asyncio.sleep(delay)
        
        # 所有重试都失败了
        self.retry_stats['failed_retries'] += 1
        raise last_exception
    
    def get_retry_stats(self) -> Dict[str, Any]:
        """获取重试统计信息"""
        total = self.retry_stats['total_retries']
        success_rate = self.retry_stats['successful_retries'] / total if total > 0 else 0
        
        return {
            **self.retry_stats,
            'success_rate': success_rate
        }


class GracefulDegradationManager:
    """优雅降级管理器"""
    
    def __init__(self, config_manager=None):
        self.config_manager = config_manager or get_config_manager()
        self.logger = logging.getLogger(__name__)
        
        # 降级策略配置
        self.degradation_strategies = {
            'ai_model': {
                'unavailable': '使用备用模型或禁用AI功能',
                'slow': '减少批处理大小，降低并发数',
                'error': '切换到缓存结果或返回默认响应'
            },
            'database': {
                'unavailable': '使用内存缓存，延迟写入',
                'slow': '减少查询复杂度，使用简单查询',
                'error': '使用备份数据库或只读模式'
            },
            'network': {
                'unavailable': '使用本地资源，离线模式',
                'slow': '增加超时时间，减少请求频率',
                'error': '启用重试机制，使用备用连接'
            },
            'file_processing': {
                'unavailable': '跳过处理，返回原始文件',
                'slow': '降低处理质量，加快处理速度',
                'error': '使用默认处理参数'
            }
        }
        
        # 系统状态
        self.system_health = {
            'ai_model': 'healthy',
            'database': 'healthy', 
            'network': 'healthy',
            'file_processing': 'healthy'
        }
        
        # 降级统计
        self.degradation_stats = {
            'total_degradations': 0,
            'successful_degradations': 0,
            'failed_degradations': 0
        }
    
    def update_component_health(self, component: str, status: str, error: Optional[Exception] = None):
        """更新组件健康状态"""
        self.system_health[component] = status
        
        if status == 'unhealthy':
            self.logger.warning(f"组件健康状态更新: {component} -> {status}")
            self._trigger_degradation(component, error)
        elif status == 'healthy':
            self.logger.info(f"组件健康状态更新: {component} -> {status}")
            self._restore_component(component)
    
    def _trigger_degradation(self, component: str, error: Optional[Exception]):
        """触发降级"""
        if component not in self.degradation_strategies:
            return
        
        self.degradation_stats['total_degradations'] += 1
        
        strategy = self.degradation_strategies[component].get('error', '使用默认策略')
        self.logger.warning(f"组件 {component} 降级: {strategy}")
        
        # 实际降级逻辑可以在这里实现
        # 例如：禁用某些功能、切换到备用方案等
    
    def _restore_component(self, component: str):
        """恢复组件"""
        self.logger.info(f"组件 {component} 已恢复正常")
    
    def get_degraded_operation(self, operation: str, context: Dict[str, Any]) -> Optional[Callable]:
        """获取降级操作"""
        # 根据操作和上下文返回降级实现
        if operation == 'embed_image':
            return self._degraded_embed_image
        elif operation == 'search':
            return self._degraded_search
        elif operation == 'process_file':
            return self._degraded_process_file
        else:
            return None
    
    async def _degraded_embed_image(self, image_data: bytes) -> Optional[Any]:
        """降级的图像向量化"""
        self.logger.warning("使用降级的图像向量化: 返回None")
        return None
    
    async def _degraded_search(self, query: str) -> List[Dict[str, Any]]:
        """降级的搜索操作"""
        self.logger.warning("使用降级的搜索: 返回空结果")
        return []
    
    async def _degraded_process_file(self, file_path: str) -> bool:
        """降级的文件处理"""
        self.logger.warning("使用降级的文件处理: 跳过处理")
        return True
    
    def get_system_health(self) -> Dict[str, str]:
        """获取系统健康状态"""
        return self.system_health.copy()
    
    def get_degradation_stats(self) -> Dict[str, Any]:
        """获取降级统计信息"""
        return self.degradation_stats.copy()


class ErrorHandler:
    """统一错误处理器"""
    
    def __init__(self, config_manager=None):
        self.config_manager = config_manager or get_config_manager()
        self.logger = logging.getLogger(__name__)
        
        # 初始化组件
        self.error_classifier = ErrorClassifier()
        self.retry_manager = RetryManager(config_manager)
        self.degradation_manager = GracefulDegradationManager(config_manager)
        
        # 配置
        self.enable_retry = self.config_manager.get("error_handling.enable_retry", True)
        self.enable_degradation = self.config_manager.get("error_handling.enable_degradation", True)
        self.log_all_errors = self.config_manager.get("error_handling.log_all_errors", True)
        
        # 错误统计
        self.error_statistics = {}
    
    def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> ErrorInfo:
        """处理错误"""
        # 分类错误
        category, severity = self.error_classifier.classify_error(error)
        
        # 创建错误信息
        error_info = ErrorInfo(
            error_id=f"{category.value}_{int(time.time())}_{hash(error)}",
            timestamp=time.time(),
            category=category,
            severity=severity,
            message=str(error),
            details={
                'error_type': type(error).__name__,
                'error_module': type(error).__module__
            },
            stack_trace=traceback.format_exc() if self.log_all_errors else None,
            context=context or {}
        )
        
        # 更新统计
        self._update_error_stats(error_info)
        
        # 记录错误日志
        self._log_error(error_info)
        
        # 根据严重级别处理
        if severity == ErrorSeverity.CRITICAL:
            self._handle_critical_error(error_info)
        elif severity == ErrorSeverity.HIGH:
            self._handle_high_severity_error(error_info)
        
        return error_info
    
    def _update_error_stats(self, error_info: ErrorInfo):
        """更新错误统计"""
        category = error_info.category.value
        
        if category not in self.error_statistics:
            self.error_statistics[category] = {
                'count': 0,
                'recent_errors': []
            }
        
        self.error_statistics[category]['count'] += 1
        self.error_statistics[category]['recent_errors'].append({
            'timestamp': error_info.timestamp,
            'severity': error_info.severity.value,
            'message': error_info.message
        })
        
        # 只保留最近100个错误
        if len(self.error_statistics[category]['recent_errors']) > 100:
            self.error_statistics[category]['recent_errors'] = \
                self.error_statistics[category]['recent_errors'][-100:]
    
    def _log_error(self, error_info: ErrorInfo):
        """记录错误日志"""
        log_message = f"[{error_info.category.value.upper()}] {error_info.message}"
        
        if error_info.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message, exc_info=True)
        elif error_info.severity == ErrorSeverity.HIGH:
            self.logger.error(log_message, exc_info=True)
        elif error_info.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(log_message, exc_info=False)
        else:
            self.logger.info(log_message, exc_info=False)
    
    def _handle_critical_error(self, error_info: ErrorInfo):
        """处理关键错误"""
        self.logger.critical(f"关键错误触发系统保护: {error_info.error_id}")
        
        # 可以在这里实现关键错误的特殊处理逻辑
        # 例如：保存系统状态、发送告警通知等
    
    def _handle_high_severity_error(self, error_info: ErrorInfo):
        """处理高严重级别错误"""
        self.logger.error(f"高严重级别错误: {error_info.error_id}")
        
        # 尝试触发降级
        if self.enable_degradation and error_info.component:
            self.degradation_manager.update_component_health(
                error_info.component, 'unhealthy', Exception(error_info.message)
            )
    
    def execute_with_error_handling(self, func: Callable, *args, context: Optional[Dict[str, Any]] = None, **kwargs) -> Any:
        """执行函数并处理错误"""
        try:
            # 首先尝试正常执行
            if hasattr(asyncio, 'iscoroutine_function') and asyncio.iscoroutine_function(func):
                return asyncio.run(func(*args, **kwargs))
            else:
                return func(*args, **kwargs)
                
        except Exception as e:
            # 错误处理
            error_info = self.handle_error(e, context)
            
            # 如果启用了重试，尝试重试
            if self.enable_retry and error_info.recoverable:
                self.logger.info(f"尝试重试函数: {func.__name__}")
                try:
                    return self.retry_manager.execute_with_retry(func, *args, **kwargs)
                except Exception as retry_error:
                    retry_error_info = self.handle_error(retry_error, context)
                    self.logger.error(f"重试失败: {func.__name__}")
                    raise retry_error
            
            # 重试失败或不需要重试，抛出原始错误
            raise e
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """获取错误统计信息"""
        return {
            'error_statistics': self.error_statistics,
            'retry_statistics': self.retry_manager.get_retry_stats(),
            'degradation_statistics': self.degradation_manager.get_degradation_stats(),
            'system_health': self.degradation_manager.get_system_health()
        }


def error_handler(context: Optional[Dict[str, Any]] = None):
    """错误处理装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            error_handler_instance = ErrorHandler()
            return error_handler_instance.execute_with_error_handling(func, *args, context=context, **kwargs)
        
        # 保留异步函数支持
        if hasattr(asyncio, 'iscoroutine_function') and asyncio.iscoroutine_function(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                error_handler_instance = ErrorHandler()
                return await error_handler_instance.execute_with_error_handling(func, *args, context=context, **kwargs)
            return async_wrapper
        
        return wrapper
    return decorator


# 全局错误处理器实例
_global_error_handler: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    """获取全局错误处理器"""
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = ErrorHandler()
    return _global_error_handler


# 临时错误类定义
class TemporaryError(Exception):
    """临时错误，可重试"""
    pass


class DatabaseError(Exception):
    """数据库错误"""
    pass
