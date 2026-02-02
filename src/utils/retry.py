"""
重试机制
提供灵活的重试策略
"""

import time
import logging
from typing import Callable, Type, Tuple, Any, Optional

logger = logging.getLogger(__name__)


class RetryStrategy:
    """重试策略"""

    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        multiplier: float = 2.0,
        max_delay: float = 60.0,
        jitter: bool = False,
    ):
        """
        初始化重试策略

        Args:
            max_attempts: 最大尝试次数
            initial_delay: 初始延迟（秒）
            multiplier: 延迟倍数
            max_delay: 最大延迟（秒）
            jitter: 是否添加随机抖动
        """
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.multiplier = multiplier
        self.max_delay = max_delay
        self.jitter = jitter

    def get_delay(self, attempt: int) -> float:
        """
        获取重试延迟

        Args:
            attempt: 尝试次数

        Returns:
            延迟时间（秒）
        """
        delay = self.initial_delay * (self.multiplier ** (attempt - 1))
        delay = min(delay, self.max_delay)

        if self.jitter:
            import random

            delay = delay * (0.5 + random.random())

        return delay

    def should_retry(self, attempt: int, error: Optional[Exception] = None) -> bool:
        """
        判断是否应该重试

        Args:
            attempt: 当前尝试次数
            error: 异常对象

        Returns:
            是否应该重试
        """
        return attempt < self.max_attempts


def retry_on_exception(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    multiplier: float = 2.0,
    max_delay: float = 60.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[int, Exception], None]] = None,
):
    """
    异常重试装饰器

    Args:
        max_attempts: 最大尝试次数
        initial_delay: 初始延迟（秒）
        multiplier: 延迟倍数
        max_delay: 最大延迟（秒）
        exceptions: 需要重试的异常类型
        on_retry: 重试回调函数

    Returns:
        装饰器函数
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        def wrapper(*args, **kwargs) -> Any:
            strategy = RetryStrategy(max_attempts, initial_delay, multiplier, max_delay)
            last_error = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_error = e
                    if strategy.should_retry(attempt, e):
                        delay = strategy.get_delay(attempt)
                        logger.warning(
                            f"Attempt {attempt}/{max_attempts} failed: {str(e)}. Retrying in {delay:.1f}s..."
                        )
                        if on_retry:
                            on_retry(attempt, e)
                        time.sleep(delay)
                    else:
                        logger.error(f"All {max_attempts} attempts failed: {str(e)}")
                        raise

            raise last_error  # type: ignore

        return wrapper

    return decorator


def retry_on_condition(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    multiplier: float = 2.0,
    condition: Callable[[Any], bool] = lambda result: result is None,
):
    """
    条件重试装饰器

    Args:
        max_attempts: 最大尝试次数
        initial_delay: 初始延迟（秒）
        multiplier: 延迟倍数
        condition: 重试条件函数

    Returns:
        装饰器函数
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        def wrapper(*args, **kwargs) -> Any:
            strategy = RetryStrategy(max_attempts, initial_delay, multiplier)
            last_result = None

            for attempt in range(1, max_attempts + 1):
                try:
                    result = func(*args, **kwargs)
                    if not condition(result):
                        return result

                    if strategy.should_retry(attempt):
                        delay = strategy.get_delay(attempt)
                        logger.warning(
                            f"Attempt {attempt}/{max_attempts} did not meet condition. Retrying in {delay:.1f}s..."
                        )
                        time.sleep(delay)
                    else:
                        return result

                    last_result = result
                except Exception as e:
                    logger.error(f"Attempt {attempt}/{max_attempts} failed: {str(e)}")
                    raise

            return last_result

        return wrapper

    return decorator


def exponential_backoff(
    max_attempts: int = 3, base_delay: float = 1.0, max_delay: float = 60.0
):
    """
    指数退避装饰器

    Args:
        max_attempts: 最大尝试次数
        base_delay: 基础延迟（秒）
        max_delay: 最大延迟（秒）

    Returns:
        装饰器函数
    """
    return retry_on_exception(
        max_attempts=max_attempts,
        initial_delay=base_delay,
        multiplier=2.0,
        max_delay=max_delay,
    )
