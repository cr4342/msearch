"""
缓存管理器
提供可配置的缓存策略，支持热冷数据分离和自动清理
"""

import os
import json
import time
import hashlib
import threading
import logging
from typing import Any, Dict, Optional, Callable, List
from pathlib import Path
from dataclasses import dataclass, field
from collections import OrderedDict

logger = logging.getLogger(__name__)


@dataclass
class CacheTypeConfig:
    """缓存类型配置"""
    max_size_gb: float = 0.0  # 缓存最大大小（GB），0表示无限制
    retention_policy: str = "lru"  # 淘汰策略：lru, lfu, ttl, fifo, none
    enable_protection: bool = False  # 启用缓存保护
    hot_data_threshold: int = 10  # 热数据访问次数阈值
    hot_data_ttl: int = 86400  # 热数据有效期（秒）
    cold_data_ttl: int = 604800  # 冷数据有效期（秒）
    
    # 扩展配置字段
    image_quality: int = 85  # 缩略图质量
    max_dimensions: tuple = (256, 256)  # 缩略图最大尺寸


@dataclass
class CacheConfig:
    """缓存配置"""
    enable: bool = True
    max_size_gb: float = 10.0  # 全局缓存总大小限制（GB）
    retention_policy: str = "lru"  # 全局淘汰策略
    hot_data_ttl: int = 86400  # 全局热数据有效期（秒）
    cold_data_ttl: int = 604800  # 全局冷数据有效期（秒）
    cleanup_interval: int = 3600  # 清理间隔（秒）
    min_free_space_gb: float = 2.0  # 系统最小可用空间（GB）
    hot_data_threshold: int = 10  # 全局热数据访问次数阈值
    enable_protection: bool = True  # 全局缓存保护开关
    
    # 各缓存类型配置
    vectors: CacheTypeConfig = field(default_factory=CacheTypeConfig)
    thumbnails: CacheTypeConfig = field(default_factory=CacheTypeConfig)
    previews: CacheTypeConfig = field(default_factory=CacheTypeConfig)
    metadata: CacheTypeConfig = field(default_factory=CacheTypeConfig)
    search_results: CacheTypeConfig = field(default_factory=CacheTypeConfig)
    models: CacheTypeConfig = field(default_factory=CacheTypeConfig)
    preprocessing: CacheTypeConfig = field(default_factory=CacheTypeConfig)
    
    def __post_init__(self):
        # 设置默认值
        self.vectors = CacheTypeConfig(
            max_size_gb=5.0,
            retention_policy="lfu",
            enable_protection=True,
            hot_data_threshold=100
        )
        
        self.thumbnails = CacheTypeConfig(
            max_size_gb=1.0,
            retention_policy="lru",
            enable_protection=False,
            image_quality=85,
            max_dimensions=(256, 256)
        )
        
        self.previews = CacheTypeConfig(
            max_size_gb=2.0,
            retention_policy="lru",
            enable_protection=True,
            hot_data_threshold=50
        )
        
        self.metadata = CacheTypeConfig(
            max_size_gb=0.5,
            retention_policy="ttl",
            enable_protection=True,
            hot_data_ttl=172800,  # 48小时
            cold_data_ttl=86400    # 24小时
        )
        
        self.search_results = CacheTypeConfig(
            max_size_gb=0.25,
            retention_policy="ttl",
            enable_protection=False,
            hot_data_ttl=3600,     # 1小时
            cold_data_ttl=1800     # 30分钟
        )
        
        self.models = CacheTypeConfig(
            max_size_gb=0.0,
            retention_policy="none",
            enable_protection=True
        )
        
        self.preprocessing = CacheTypeConfig(
            max_size_gb=5.0,
            retention_policy="fifo",
            enable_protection=False,
            cold_data_ttl=86400    # 24小时
        )


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    size_bytes: int
    created_at: float
    last_accessed_at: float
    access_count: int = 0
    is_hot: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'key': self.key,
            'size_bytes': self.size_bytes,
            'created_at': self.created_at,
            'last_accessed_at': self.last_accessed_at,
            'access_count': self.access_count,
            'is_hot': self.is_hot
        }


class CacheManager:
    """缓存管理器"""
    
    def __init__(self, config: CacheConfig, cache_dir: Optional[str] = None):
        """
        初始化缓存管理器
        
        Args:
            config: 缓存配置
            cache_dir: 缓存目录
        """
        self.config = config
        self.cache_dir = Path(cache_dir) if cache_dir else Path("data/cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 缓存存储 - 按类型分类
        self.caches: Dict[str, OrderedDict[str, CacheEntry]] = {
            'vectors': OrderedDict(),
            'thumbnails': OrderedDict(),
            'previews': OrderedDict(),
            'metadata': OrderedDict(),
            'search_results': OrderedDict(),
            'models': OrderedDict(),
            'preprocessing': OrderedDict()
        }
        self.cache_lock = threading.RLock()
        
        # 统计信息 - 按类型分类
        self.total_size_bytes = 0
        self.hit_count = 0
        self.miss_count = 0
        self.eviction_count = 0
        self.type_size_bytes: Dict[str, int] = {
            'vectors': 0,
            'thumbnails': 0,
            'previews': 0,
            'metadata': 0,
            'search_results': 0,
            'models': 0,
            'preprocessing': 0
        }
        
        # 控制线程
        self.is_running = False
        self.cleanup_thread: Optional[threading.Thread] = None
        
        # 缓存保护
        self.protected_keys: Dict[str, set[str]] = {
            'vectors': set(),
            'thumbnails': set(),
            'previews': set(),
            'metadata': set(),
            'search_results': set(),
            'models': set(),
            'preprocessing': set()
        }
        
        # 缓存保护优先级（值越高，优先级越高）
        self.protection_priority: Dict[str, int] = {
            'models': 10,
            'vectors': 8,
            'metadata': 7,
            'previews': 5,
            'search_results': 4,
            'thumbnails': 3,
            'preprocessing': 2
        }
        
        logger.info(f"缓存管理器初始化完成: max_size={config.max_size_gb}GB, policy={config.retention_policy}")
    
    def initialize(self) -> bool:
        """
        初始化缓存管理器
        
        Returns:
            是否成功
        """
        try:
            # 加载现有缓存
            self._load_cache_index()
            
            # 启动清理线程
            self.is_running = True
            self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
            self.cleanup_thread.start()
            
            logger.info("缓存管理器启动成功")
            return True
        except Exception as e:
            logger.error(f"缓存管理器启动失败: {e}")
            return False
    
    def shutdown(self) -> None:
        """关闭缓存管理器"""
        self.is_running = False
        
        if self.cleanup_thread:
            self.cleanup_thread.join(timeout=5.0)
        
        # 保存缓存索引
        self._save_cache_index()
        
        logger.info("缓存管理器已关闭")
    
    def get(self, key: str, cache_type: str = 'vectors') -> Optional[Any]:
        """
        获取缓存值
        
        Args:
            key: 缓存键
            cache_type: 缓存类型
        
        Returns:
            缓存值，如果不存在则返回None
        """
        with self.cache_lock:
            cache = self.caches.get(cache_type, self.caches['vectors'])
            entry = cache.get(key)
            
            if entry is None:
                self.miss_count += 1
                return None
            
            # 获取缓存类型配置
            type_config = getattr(self.config, cache_type, None) or self.config.vectors
            
            # 更新访问信息
            entry.last_accessed_at = time.time()
            entry.access_count += 1
            
            # 更新热数据状态
            if self.config.enable_protection and type_config.enable_protection:
                threshold = type_config.hot_data_threshold or self.config.hot_data_threshold
                if entry.access_count >= threshold:
                    entry.is_hot = True
                    self.protected_keys[cache_type].add(key)
            
            # 移动到末尾（LRU）
            retention_policy = type_config.retention_policy or self.config.retention_policy
            if retention_policy == "lru":
                cache.move_to_end(key)
            
            self.hit_count += 1
            return entry.value
    
    def set(self, key: str, value: Any, cache_type: str = 'vectors', size_bytes: Optional[int] = None) -> bool:
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            cache_type: 缓存类型
            size_bytes: 缓存大小（字节），如果为None则自动计算
        
        Returns:
            是否成功
        """
        if not self.config.enable:
            return False
        
        try:
            # 计算大小
            if size_bytes is None:
                size_bytes = self._calculate_size(value)
            
            with self.cache_lock:
                cache = self.caches.get(cache_type, self.caches['vectors'])
                
                # 获取缓存类型配置
                type_config = getattr(self.config, cache_type, None) or self.config.vectors
                
                # 检查是否超过单个缓存项限制
                max_single_size = self.config.max_size_gb * 1024 * 1024 * 1024 / 10  # 单个缓存项不超过总大小的10%
                if size_bytes > max_single_size:
                    logger.warning(f"缓存项过大，跳过缓存: {key} ({size_bytes} bytes > {max_single_size} bytes)")
                    return False
                
                # 检查是否已存在
                if key in cache:
                    # 更新现有缓存项
                    old_entry = cache[key]
                    self.total_size_bytes -= old_entry.size_bytes
                    self.type_size_bytes[cache_type] -= old_entry.size_bytes
                    del cache[key]
                
                # 检查是否需要清理
                self._ensure_space(size_bytes, cache_type)
                
                # 创建新缓存项
                now = time.time()
                entry = CacheEntry(
                    key=key,
                    value=value,
                    size_bytes=size_bytes,
                    created_at=now,
                    last_accessed_at=now,
                    access_count=0,
                    is_hot=False
                )
                
                cache[key] = entry
                self.total_size_bytes += size_bytes
                self.type_size_bytes[cache_type] += size_bytes
                
                return True
            
        except Exception as e:
            logger.error(f"设置缓存失败: {e}")
            return False
    
    def delete(self, key: str, cache_type: str = 'vectors') -> bool:
        """
        删除缓存项
        
        Args:
            key: 缓存键
            cache_type: 缓存类型
        
        Returns:
            是否成功
        """
        with self.cache_lock:
            cache = self.caches.get(cache_type, self.caches['vectors'])
            entry = cache.pop(key, None)
            if entry:
                self.total_size_bytes -= entry.size_bytes
                self.type_size_bytes[cache_type] -= entry.size_bytes
                self.protected_keys[cache_type].discard(key)
                return True
            return False
    
    def clear(self, cache_type: Optional[str] = None) -> None:
        """
        清空所有缓存或指定类型的缓存
        
        Args:
            cache_type: 缓存类型，如果为None则清空所有缓存
        """
        with self.cache_lock:
            if cache_type:
                # 清空指定类型的缓存
                cache = self.caches.get(cache_type, None)
                if cache:
                    cache.clear()
                    self.total_size_bytes -= self.type_size_bytes[cache_type]
                    self.type_size_bytes[cache_type] = 0
                    self.protected_keys[cache_type].clear()
                    logger.info(f"{cache_type}类型缓存已清空")
            else:
                # 清空所有缓存
                for cache_name in self.caches:
                    self.caches[cache_name].clear()
                    self.type_size_bytes[cache_name] = 0
                    self.protected_keys[cache_name].clear()
                self.total_size_bytes = 0
                logger.info("所有缓存已清空")
    
    def protect(self, key: str, cache_type: str = 'vectors') -> bool:
        """
        手动保护一个缓存项
        
        Args:
            key: 缓存键
            cache_type: 缓存类型
            
        Returns:
            是否成功保护
        """
        with self.cache_lock:
            cache = self.caches.get(cache_type, None)
            if cache and key in cache:
                self.protected_keys[cache_type].add(key)
                cache[key].is_hot = True
                logger.debug(f"手动保护缓存项: {key} ({cache_type})")
                return True
            return False
    
    def unprotect(self, key: str, cache_type: str = 'vectors') -> bool:
        """
        取消保护一个缓存项
        
        Args:
            key: 缓存键
            cache_type: 缓存类型
            
        Returns:
            是否成功取消保护
        """
        with self.cache_lock:
            cache = self.caches.get(cache_type, None)
            if cache and key in cache:
                self.protected_keys[cache_type].discard(key)
                cache[key].is_hot = False
                logger.debug(f"取消保护缓存项: {key} ({cache_type})")
                return True
            return False
    
    def is_protected(self, key: str, cache_type: str = 'vectors') -> bool:
        """
        检查缓存项是否受保护
        
        Args:
            key: 缓存键
            cache_type: 缓存类型
            
        Returns:
            是否受保护
        """
        with self.cache_lock:
            return key in self.protected_keys.get(cache_type, set())
    
    def _calculate_size(self, value: Any) -> int:
        """
        计算值的大小
        
        Args:
            value: 值
        
        Returns:
            大小（字节）
        """
        if isinstance(value, (str, bytes)):
            return len(value)
        elif isinstance(value, (dict, list)):
            return len(json.dumps(value))
        elif isinstance(value, Path):
            if value.exists():
                return value.stat().st_size
            return 0
        else:
            return len(str(value))
    
    def _ensure_space(self, required_bytes: int, cache_type: str = 'vectors') -> None:
        """
        确保有足够的空间
        
        Args:
            required_bytes: 需要的空间（字节）
            cache_type: 缓存类型
        """
        max_size_bytes = self.config.max_size_gb * 1024 * 1024 * 1024
        
        # 获取缓存类型配置
        type_config = getattr(self.config, cache_type, None) or self.config.vectors
        
        # 检查磁盘空间
        disk_usage = self.cache_dir.statvfs() if hasattr(self.cache_dir, 'statvfs') else None
        if disk_usage:
            free_space_gb = disk_usage.f_frsize * disk_usage.f_bavail / (1024**3)
            if free_space_gb < self.config.min_free_space_gb:
                logger.warning(f"磁盘空间不足，清理缓存: {free_space_gb}GB < {self.config.min_free_space_gb}GB")
                self._cleanup_cache(required_bytes, cache_type)
        
        # 检查全局缓存大小
        while (self.total_size_bytes + required_bytes) > max_size_bytes:
            self._evict_one(cache_type)
        
        # 检查类型缓存大小
        if type_config.max_size_gb > 0:
            max_type_size_bytes = type_config.max_size_gb * 1024 * 1024 * 1024
            while (self.type_size_bytes[cache_type] + required_bytes) > max_type_size_bytes:
                self._evict_one(cache_type)
    
    def _evict_one(self, cache_type: str = 'vectors') -> None:
        """
        淘汰一个缓存项
        
        Args:
            cache_type: 缓存类型
        """
        # 获取指定类型的缓存
        cache = self.caches.get(cache_type, None)
        
        # 如果指定类型的缓存为空，尝试其他类型的缓存
        if not cache:
            # 按保护优先级从低到高排序缓存类型
            sorted_cache_types = sorted(self.caches.items(), key=lambda x: self.protection_priority.get(x[0], 0))
            for ctype, ccache in sorted_cache_types:
                if ccache:
                    cache_type = ctype
                    cache = ccache
                    break
            else:
                return
        
        # 获取缓存类型配置
        type_config = getattr(self.config, cache_type, None) or self.config.vectors
        retention_policy = type_config.retention_policy or self.config.retention_policy
        
        # 根据策略选择淘汰项
        if retention_policy == "lru":
            # LRU：淘汰最久未使用的
            key = next(iter(cache))
        elif retention_policy == "lfu":
            # LFU：淘汰访问次数最少的
            key = min(cache.keys(), key=lambda k: cache[k].access_count)
        else:
            # TTL：淘汰过期的
            now = time.time()
            key = None
            for k, entry in cache.items():
                if k not in self.protected_keys[cache_type]:
                    if entry.is_hot:
                        ttl = type_config.hot_data_ttl or self.config.hot_data_ttl
                    else:
                        ttl = type_config.cold_data_ttl or self.config.cold_data_ttl
                    if now - entry.last_accessed_at > ttl:
                        key = k
                        break
            
            # 如果没有过期的，使用LRU
            if key is None:
                # 尝试找到一个非受保护的缓存项
                for k in cache:
                    if k not in self.protected_keys[cache_type]:
                        key = k
                        break
                else:
                    # 如果所有缓存项都受保护，尝试其他类型（按优先级从低到高）
                    sorted_cache_types = sorted(self.caches.items(), key=lambda x: self.protection_priority.get(x[0], 0))
                    for ctype, ccache in sorted_cache_types:
                        if ctype != cache_type and ccache:
                            # 尝试找到一个非受保护的缓存项
                            for k in ccache:
                                if k not in self.protected_keys[ctype]:
                                    cache_type = ctype
                                    cache = ccache
                                    key = k
                                    break
                            if key:
                                break
                    else:
                        # 如果所有缓存项都受保护，尝试取消保护优先级最低的缓存类型的一个项
                        logger.warning("所有缓存项都受保护，尝试取消保护优先级最低的缓存项")
                        sorted_cache_types = sorted(self.caches.items(), key=lambda x: self.protection_priority.get(x[0], 0))
                        for ctype, ccache in sorted_cache_types:
                            if ccache:
                                # 找到优先级最低的缓存类型中的第一个项
                                for k in ccache:
                                    cache_type = ctype
                                    cache = ccache
                                    key = k
                                    # 取消保护
                                    self.protected_keys[cache_type].discard(key)
                                    cache[key].is_hot = False
                                    logger.debug(f"取消保护缓存项: {key} ({cache_type}) 以进行淘汰")
                                    break
                                if key:
                                    break
                        else:
                            # 所有缓存项都受保护，无法淘汰
                            logger.error("所有缓存项都受保护，无法进行淘汰")
                            return
        
        # 删除缓存项
        entry = cache.pop(key)
        self.total_size_bytes -= entry.size_bytes
        self.type_size_bytes[cache_type] -= entry.size_bytes
        self.protected_keys[cache_type].discard(key)
        self.eviction_count += 1
        
        logger.debug(f"淘汰缓存项: {key} ({entry.size_bytes} bytes), 类型: {cache_type}")
    
    def _cleanup_cache(self, required_bytes: Optional[int] = None, cache_type: str = 'vectors') -> None:
        """
        清理缓存
        
        Args:
            required_bytes: 需要释放的空间（字节），如果为None则清理到目标大小
            cache_type: 缓存类型
        """
        target_size_bytes = self.config.max_size_gb * 1024 * 1024 * 1024 * 0.8  # 清理到80%
        
        if required_bytes:
            # 清理到满足需求
            while (self.total_size_bytes + required_bytes) > self.config.max_size_gb * 1024 * 1024 * 1024:
                self._evict_one(cache_type)
        else:
            # 清理到目标大小
            while self.total_size_bytes > target_size_bytes:
                self._evict_one(cache_type)
    
    def _cleanup_loop(self) -> None:
        """清理循环"""
        logger.info("缓存清理线程启动")
        
        while self.is_running:
            try:
                time.sleep(self.config.cleanup_interval)
                
                # 定期清理
                with self.cache_lock:
                    # 清理所有类型的缓存
                    for cache_type in self.caches:
                        self._cleanup_cache(None, cache_type)
                    
                    # 更新热数据状态
                    now = time.time()
                    for cache_type, cache in self.caches.items():
                        type_config = getattr(self.config, cache_type, None) or self.config.vectors
                        for key, entry in cache.items():
                            threshold = type_config.hot_data_threshold or self.config.hot_data_threshold
                            if entry.access_count >= threshold:
                                entry.is_hot = True
                                self.protected_keys[cache_type].add(key)
                            elif entry.is_hot:
                                ttl = type_config.hot_data_ttl or self.config.hot_data_ttl
                                if now - entry.last_accessed_at > ttl:
                                    entry.is_hot = False
                                    self.protected_keys[cache_type].discard(key)
                
            except Exception as e:
                logger.error(f"缓存清理失败: {e}")
        
        logger.info("缓存清理线程停止")
    
    def _load_cache_index(self) -> None:
        """加载缓存索引"""
        index_file = self.cache_dir / "cache_index.json"
        
        if not index_file.exists():
            return
        
        try:
            with open(index_file, 'r') as f:
                index_data = json.load(f)
            
            with self.cache_lock:
                for cache_type, cache_entries in index_data.items():
                    cache = self.caches.get(cache_type, None)
                    if not cache:
                        continue
                    
                    for key, entry_data in cache_entries.items():
                        # 只加载元数据，不加载实际值
                        cache[key] = CacheEntry(
                            key=key,
                            value=None,  # 值需要重新加载
                            size_bytes=entry_data['size_bytes'],
                            created_at=entry_data['created_at'],
                            last_accessed_at=entry_data['last_accessed_at'],
                            access_count=entry_data['access_count'],
                            is_hot=entry_data.get('is_hot', False)
                        )
                        self.total_size_bytes += entry_data['size_bytes']
                        self.type_size_bytes[cache_type] += entry_data['size_bytes']
            
            logger.info(f"加载缓存索引完成")
        except Exception as e:
            logger.warning(f"加载缓存索引失败: {e}")
    
    def _save_cache_index(self) -> None:
        """保存缓存索引"""
        index_file = self.cache_dir / "cache_index.json"
        
        try:
            with self.cache_lock:
                index_data = {}
                for cache_type, cache in self.caches.items():
                    cache_entries = {}
                    for key, entry in cache.items():
                        cache_entries[key] = entry.to_dict()
                    if cache_entries:
                        index_data[cache_type] = cache_entries
            
            with open(index_file, 'w') as f:
                json.dump(index_data, f, indent=2)
            
            logger.debug(f"保存缓存索引: {sum(len(entries) for entries in index_data.values())} 项")
        except Exception as e:
            logger.warning(f"保存缓存索引失败: {e}")
    
    def get_stats(self, cache_type: Optional[str] = None) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Args:
            cache_type: 缓存类型，如果为None则获取所有缓存的统计信息
        
        Returns:
            统计信息字典
        """
        with self.cache_lock:
            hit_rate = self.hit_count / (self.hit_count + self.miss_count) if (self.hit_count + self.miss_count) > 0 else 0.0
            
            if cache_type:
                # 获取指定类型的统计信息
                cache = self.caches.get(cache_type, None)
                if not cache:
                    return {}
                
                type_config = getattr(self.config, cache_type, None) or self.config.vectors
                return {
                    'enabled': self.config.enable,
                    'cache_type': cache_type,
                    'total_entries': len(cache),
                    'total_size_bytes': self.type_size_bytes[cache_type],
                    'total_size_gb': self.type_size_bytes[cache_type] / (1024**3),
                    'max_size_gb': type_config.max_size_gb,
                    'hit_count': self.hit_count,
                    'miss_count': self.miss_count,
                    'eviction_count': self.eviction_count,
                    'hit_rate': hit_rate,
                    'hot_data_count': len(self.protected_keys[cache_type]),
                    'retention_policy': type_config.retention_policy
                }
            else:
                # 获取所有缓存的统计信息
                return {
                    'enabled': self.config.enable,
                    'total_entries': sum(len(cache) for cache in self.caches.values()),
                    'total_size_bytes': self.total_size_bytes,
                    'total_size_gb': self.total_size_bytes / (1024**3),
                    'max_size_gb': self.config.max_size_gb,
                    'hit_count': self.hit_count,
                    'miss_count': self.miss_count,
                    'eviction_count': self.eviction_count,
                    'hit_rate': hit_rate,
                    'hot_data_count': sum(len(keys) for keys in self.protected_keys.values()),
                    'retention_policy': self.config.retention_policy,
                    'type_stats': {
                        cache_type: {
                            'entries': len(cache),
                            'size_bytes': self.type_size_bytes[cache_type],
                            'size_gb': self.type_size_bytes[cache_type] / (1024**3),
                            'hot_data_count': len(self.protected_keys[cache_type])
                        }
                        for cache_type, cache in self.caches.items()
                    }
                }
    
    def get_entries(self, cache_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取所有缓存项信息或指定类型的缓存项信息
        
        Args:
            cache_type: 缓存类型，如果为None则获取所有缓存项信息
        
        Returns:
            缓存项信息列表
        """
        with self.cache_lock:
            if cache_type:
                # 获取指定类型的缓存项信息
                cache = self.caches.get(cache_type, None)
                if not cache:
                    return []
                return [entry.to_dict() for entry in cache.values()]
            else:
                # 获取所有缓存项信息
                entries = []
                for cache in self.caches.values():
                    entries.extend([entry.to_dict() for entry in cache.values()])
                return entries
    
    def protect_key(self, key: str, cache_type: str = 'vectors') -> bool:
        """
        保护缓存键不被淘汰
        
        Args:
            key: 缓存键
            cache_type: 缓存类型
        
        Returns:
            是否成功
        """
        with self.cache_lock:
            cache = self.caches.get(cache_type, None)
            if cache and key in cache:
                self.protected_keys[cache_type].add(key)
                cache[key].is_hot = True
                return True
            return False
    
    def unprotect_key(self, key: str, cache_type: str = 'vectors') -> bool:
        """
        取消保护缓存键
        
        Args:
            key: 缓存键
            cache_type: 缓存类型
        
        Returns:
            是否成功
        """
        with self.cache_lock:
            cache = self.caches.get(cache_type, None)
            if cache and key in cache:
                self.protected_keys[cache_type].discard(key)
                cache[key].is_hot = False
                return True
            return False


def get_cache_key(*args: Any) -> str:
    """
    生成缓存键
    
    Args:
        *args: 缓存键的组成部分
    
    Returns:
        缓存键
    """
    key_str = ":".join(str(arg) for arg in args)
    return hashlib.md5(key_str.encode()).hexdigest()