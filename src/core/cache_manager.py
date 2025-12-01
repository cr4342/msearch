"""
缓存管理器
提供多种缓存机制来提升系统性能
"""

import asyncio
import hashlib
import json
import logging
import time
from typing import Any, Dict, List, Optional, Union
from collections import OrderedDict
from functools import wraps

from src.core.config_manager import get_config_manager


class MemoryCache:
    """内存缓存实现"""
    
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        self.max_size = max_size
        self.ttl = ttl  # 生存时间（秒）
        self.cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self.hits = 0
        self.misses = 0
    
    def _generate_key(self, *args, **kwargs) -> str:
        """生成缓存键"""
        key_data = {
            'args': args,
            'kwargs': sorted(kwargs.items())
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if key not in self.cache:
            self.misses += 1
            return None
        
        entry = self.cache[key]
        
        # 检查是否过期
        if time.time() - entry['timestamp'] > self.ttl:
            del self.cache[key]
            self.misses += 1
            return None
        
        # 移动到末尾（LRU）
        self.cache.move_to_end(key)
        self.hits += 1
        return entry['value']
    
    def set(self, key: str, value: Any) -> None:
        """设置缓存值"""
        # 检查容量限制
        if len(self.cache) >= self.max_size:
            # 删除最旧的项
            self.cache.popitem(last=False)
        
        self.cache[key] = {
            'value': value,
            'timestamp': time.time()
        }
    
    def clear(self) -> None:
        """清空缓存"""
        self.cache.clear()
        self.hits = 0
        self.misses = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        total = self.hits + self.misses
        hit_rate = self.hits / total if total > 0 else 0
        
        return {
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': hit_rate,
            'size': len(self.cache),
            'max_size': self.max_size
        }


class DiskCache:
    """磁盘缓存实现"""
    
    def __init__(self, cache_dir: str = "./data/cache", ttl: int = 86400):
        import os
        self.cache_dir = cache_dir
        self.ttl = ttl
        os.makedirs(cache_dir, exist_ok=True)
        self.hits = 0
        self.misses = 0
    
    def _get_file_path(self, key: str) -> str:
        """获取缓存文件路径"""
        return f"{self.cache_dir}/{key}.cache"
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        import pickle
        import os
        
        file_path = self._get_file_path(key)
        
        if not os.path.exists(file_path):
            self.misses += 1
            return None
        
        # 检查是否过期
        if time.time() - os.path.getmtime(file_path) > self.ttl:
            os.remove(file_path)
            self.misses += 1
            return None
        
        try:
            with open(file_path, 'rb') as f:
                data = pickle.load(f)
            self.hits += 1
            return data
        except Exception:
            self.misses += 1
            return None
    
    def set(self, key: str, value: Any) -> None:
        """设置缓存值"""
        import pickle
        import os
        
        file_path = self._get_file_path(key)
        
        try:
            with open(file_path, 'wb') as f:
                pickle.dump(value, f)
        except Exception as e:
            logging.error(f"磁盘缓存写入失败: {e}")
    
    def clear(self) -> None:
        """清空缓存"""
        import os
        import glob
        
        files = glob.glob(f"{self.cache_dir}/*.cache")
        for file_path in files:
            try:
                os.remove(file_path)
            except Exception:
                pass
        
        self.hits = 0
        self.misses = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        total = self.hits + self.misses
        hit_rate = self.hits / total if total > 0 else 0
        
        return {
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': hit_rate,
            'size': len(self.cache_dir)
        }


class VectorCache:
    """向量缓存，专门用于缓存向量数据"""
    
    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self.cache: OrderedDict[str, Any] = OrderedDict()
        self.hits = 0
        self.misses = 0
    
    def get_vector(self, file_hash: str, model_name: str) -> Optional[Any]:
        """获取向量缓存"""
        key = f"{file_hash}:{model_name}"
        
        if key not in self.cache:
            self.misses += 1
            return None
        
        self.cache.move_to_end(key)
        self.hits += 1
        return self.cache[key]
    
    def set_vector(self, file_hash: str, model_name: str, vector: Any) -> None:
        """设置向量缓存"""
        key = f"{file_hash}:{model_name}"
        
        if len(self.cache) >= self.max_size:
            self.cache.popitem(last=False)
        
        self.cache[key] = vector
    
    def clear(self) -> None:
        """清空向量缓存"""
        self.cache.clear()
        self.hits = 0
        self.misses = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        total = self.hits + self.misses
        hit_rate = self.hits / total if total > 0 else 0
        
        return {
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': hit_rate,
            'size': len(self.cache),
            'max_size': self.max_size
        }


class CacheManager:
    """缓存管理器"""
    
    def __init__(self, config_manager=None):
        self.config_manager = config_manager or get_config_manager()
        self.logger = logging.getLogger(__name__)
        
        # 初始化各种缓存
        self.memory_cache = MemoryCache(
            max_size=self.config_manager.get("cache.memory.max_size", 1000),
            ttl=self.config_manager.get("cache.memory.ttl", 3600)
        )
        
        self.disk_cache = DiskCache(
            cache_dir=self.config_manager.get("cache.disk.directory", "./data/cache"),
            ttl=self.config_manager.get("cache.disk.ttl", 86400)
        )
        
        self.vector_cache = VectorCache(
            max_size=self.config_manager.get("cache.vector.max_size", 10000)
        )
        
        # 缓存策略配置
        self.cache_strategies = {
            'embedding': self.vector_cache,  # 向量数据使用专门的向量缓存
            'preprocessing': self.memory_cache,  # 预处理结果使用内存缓存
            'metadata': self.disk_cache,  # 元数据使用磁盘缓存
            'query': self.memory_cache,  # 查询结果使用内存缓存
        }
        
        self.logger.info("缓存管理器初始化完成")
    
    def cache_result(self, cache_type: str, key: str = None, ttl: int = None):
        """缓存装饰器"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # 生成缓存键
                if key is None:
                    cache_key = f"{func.__name__}:{hashlib.md5(str(args + tuple(sorted(kwargs.items()))).encode()).hexdigest()}"
                else:
                    cache_key = key
                
                # 尝试从缓存获取
                cache = self.cache_strategies.get(cache_type, self.memory_cache)
                cached_result = cache.get(cache_key)
                
                if cached_result is not None:
                    self.logger.debug(f"缓存命中: {func.__name__}")
                    return cached_result
                
                # 执行函数并缓存结果
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                # 缓存结果
                cache.set(cache_key, result)
                self.logger.debug(f"缓存设置: {func.__name__}")
                
                return result
            return wrapper
        return decorator
    
    def get_cached_vector(self, file_hash: str, model_name: str) -> Optional[Any]:
        """获取缓存的向量"""
        return self.vector_cache.get_vector(file_hash, model_name)
    
    def set_cached_vector(self, file_hash: str, model_name: str, vector: Any) -> None:
        """缓存向量"""
        self.vector_cache.set_vector(file_hash, model_name, vector)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取所有缓存的统计信息"""
        return {
            'memory': self.memory_cache.get_stats(),
            'disk': self.disk_cache.get_stats(),
            'vector': self.vector_cache.get_stats()
        }
    
    def clear_all_caches(self) -> None:
        """清空所有缓存"""
        self.memory_cache.clear()
        self.disk_cache.clear()
        self.vector_cache.clear()
        
        self.logger.info("所有缓存已清空")
    
    def cleanup_expired(self) -> None:
        """清理过期的缓存项"""
        # 内存缓存会自动清理过期项
        # 磁盘缓存在get时会清理过期项
        pass