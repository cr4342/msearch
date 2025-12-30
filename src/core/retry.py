"""
重试装饰器
提供异步重试功能，支持自定义重试次数、延迟和退避策略
"""

import asyncio
from functools import wraps
from typing import Callable, Any, Optional
import logging

logger = logging.getLogger(__name__)


def async_retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
    include_exceptions: Optional[tuple] = None,
    exclude_exceptions: Optional[tuple] = None
):
    """
    异步重试装饰器
    
    Args:
        max_attempts: 最大重试次数
        delay: 初始延迟（秒）
        backoff: 退避因子，每次重试延迟乘以该因子
        exceptions: 需要重试的异常类型
        include_exceptions: 额外需要重试的异常类型
        exclude_exceptions: 不需要重试的异常类型
        
    Returns:
        装饰后的函数
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # 合并异常类型
            retry_exceptions = exceptions
            if include_exceptions:
                retry_exceptions = exceptions + include_exceptions
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    # 检查是否需要跳过该异常
                    if exclude_exceptions and isinstance(e, exclude_exceptions):
                        logger.error(f"异常 {type(e).__name__} 不需要重试，直接抛出: {e}")
                        raise
                    
                    # 检查是否是需要重试的异常
                    if not isinstance(e, retry_exceptions):
                        logger.error(f"异常 {type(e).__name__} 不在重试列表中，直接抛出: {e}")
                        raise
                    
                    # 最后一次尝试，直接抛出
                    if attempt == max_attempts - 1:
                        logger.error(f"所有重试失败，最后一次异常: {e}")
                        raise
                    
                    # 计算延迟
                    retry_delay = delay * (backoff ** attempt)
                    logger.warning(f"尝试 {attempt + 1}/{max_attempts} 失败，{retry_delay:.2f}秒后重试: {e}")
                    
                    await asyncio.sleep(retry_delay)
            
            return None
        
        return wrapper
    
    return decorator