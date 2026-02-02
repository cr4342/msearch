"""
错误处理
定义统一的错误处理策略
"""

import logging
import time
from typing import Any, Callable, Dict, Optional, Type, TypeVar, Tuple
from functools import wraps
from .exceptions import MSearchError

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ErrorHandler:
    """错误处理器"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化错误处理器

        Args:
            config: 配置字典
        """
        self.config = config
        self.custom_handlers: Dict[str, Callable[[Exception], None]] = {}

    def handle_error(
        self, error: Exception, context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        处理错误

        Args:
            error: 异常对象
            context: 错误上下文
        """
        # 记录错误日志
        if isinstance(error, MSearchError):
            logger.error(f"{error} - Context: {error.context}")
        else:
            logger.error(f"Unexpected error: {str(error)} - Context: {context}")

    def format_error(self, error: Exception) -> str:
        """
        格式化错误信息

        Args:
            error: 异常对象

        Returns:
            格式化的错误信息
        """
        if isinstance(error, MSearchError):
            return f"[{error.error_code}] {error.message}"
        else:
            return f"[{type(error).__name__}] {str(error)}"

    def can_retry(self, error: Exception) -> bool:
        """
        判断错误是否可重试

        Args:
            error: 异常对象

        Returns:
            是否可重试
        """
        # 可重试的错误类型
        retryable_errors = (
            ConnectionError,
            TimeoutError,
            OSError,
        )

        return isinstance(error, retryable_errors)

    def get_retry_delay(
        self, attempt: int, initial_delay: float = 1.0, multiplier: float = 2.0
    ) -> float:
        """
        获取重试延迟

        Args:
            attempt: 尝试次数
            initial_delay: 初始延迟（秒）
            multiplier: 延迟倍数

        Returns:
            重试延迟（秒）
        """
        return initial_delay * (multiplier ** (attempt - 1))

    def convert_exception(
        self,
        error: Exception,
        target_error_type: Type[MSearchError],
        context: Optional[Dict[str, Any]] = None,
    ) -> MSearchError:
        """
        转换异常

        Args:
            error: 原始异常
            target_error_type: 目标异常类型
            context: 错误上下文

        Returns:
            转换后的异常
        """
        if isinstance(error, target_error_type):
            return error

        return target_error_type(
            message=str(error),
            context=context or {"original_error": type(error).__name__},
        )

    def get_error_code(self, error: Exception) -> str:
        """
        获取错误代码

        Args:
            error: 异常对象

        Returns:
            错误代码
        """
        if isinstance(error, MSearchError):
            return error.error_code
        else:
            return type(error).__name__

    def register_custom_handler(
        self, error_type: Type[Exception], handler: Callable[[Exception], None]
    ) -> None:
        """
        注册自定义错误处理器

        Args:
            error_type: 错误类型
            handler: 处理函数
        """
        self.custom_handlers[error_type.__name__] = handler
        logger.info(f"注册自定义错误处理器: {error_type.__name__}")

    def unregister_custom_handler(self, error_type: Type[Exception]) -> None:
        """
        注销自定义错误处理器

        Args:
            error_type: 错误类型
        """
        if error_type.__name__ in self.custom_handlers:
            del self.custom_handlers[error_type.__name__]
            logger.info(f"注销自定义错误处理器: {error_type.__name__}")


def retry(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    multiplier: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
):
    """
    重试装饰器

    Args:
        max_attempts: 最大尝试次数
        initial_delay: 初始延迟（秒）
        multiplier: 延迟倍数
        exceptions: 需要重试的异常类型

    Returns:
        装饰器函数
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_error = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_error = e
                    if attempt < max_attempts:
                        delay = initial_delay * (multiplier ** (attempt - 1))
                        logger.warning(
                            f"Attempt {attempt}/{max_attempts} failed: {str(e)}. Retrying in {delay:.1f}s..."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(f"All {max_attempts} attempts failed: {str(e)}")
                        raise
            raise last_error  # type: ignore

        return wrapper

    return decorator


def handle_errors(
    error_handler: Optional[ErrorHandler] = None,
    default_return: Any = None,
    log_errors: bool = True,
):
    """
    错误处理装饰器

    Args:
        error_handler: 错误处理器
        default_return: 默认返回值
        log_errors: 是否记录错误日志

    Returns:
        装饰器函数
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if error_handler:
                    error_handler.handle_error(e, {"function": func.__name__})
                elif log_errors:
                    logger.error(f"Error in {func.__name__}: {str(e)}")
                return default_return  # type: ignore

        return wrapper

    return decorator


def convert_errors(
    target_error_type: Type[MSearchError], context: Optional[Dict[str, Any]] = None
):
    """
    异常转换装饰器

    Args:
        target_error_type: 目标异常类型
        context: 错误上下文

    Returns:
        装饰器函数
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except MSearchError:
                raise
            except Exception as e:
                error_handler = ErrorHandler({})
                raise error_handler.convert_exception(e, target_error_type, context)

        return wrapper

    return decorator
