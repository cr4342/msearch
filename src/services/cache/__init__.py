"""
缓存服务模块
提供可配置的缓存策略，支持热冷数据分离和自动清理
"""

from .cache_manager import CacheManager, CacheConfig, get_cache_key

__all__ = ['CacheManager', 'CacheConfig', 'get_cache_key']