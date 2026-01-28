"""
缓存策略管理器
支持可配置的缓存大小、保留策略、热冷数据管理和清理机制
"""

import os
import json
import time
import heapq
import logging
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class EvictionPolicy(Enum):
    """缓存淘汰策略"""
    LRU = "lru"  # 最近最少使用
    LFU = "lfu"  # 最少使用频率
    FIFO = "fifo"  # 先进先出
    TTL = "ttl"  # 基于时间


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    size: int
    created_at: float
    last_accessed: float
    access_count: int = 0
    ttl: Optional[float] = None
    is_hot: bool = False


@dataclass
class CacheConfig:
    """缓存配置"""
    max_size: int = 5368709120  # 5GB
    ttl: float = 2592000  # 30天
    eviction_policy: EvictionPolicy = EvictionPolicy.LFU
    enable_hot_cold: bool = True
    hot_threshold: int = 10  # 访问次数>=10为热数据
    cold_ttl: float = 604800  # 7天
    enable_protection: bool = True
    protected_keys: List[str] = field(default_factory=list)


class CacheStrategyManager:
    """缓存策略管理器"""
    
    def __init__(self, cache_dir: str, config: Optional[CacheConfig] = None):
        """
        初始化缓存策略管理器
        
        Args:
            cache_dir: 缓存目录
            config: 缓存配置
        """
        self.cache_dir = Path(cache_dir)
        self.config = config or CacheConfig()
        
        # 缓存存储
        self.cache: Dict[str, CacheEntry] = {}
        
        # 访问记录（用于LRU/LFU）
        self.access_heap: List[Tuple[float, str]] = []
        
        # 统计信息
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'total_size': 0
        }
        
        # 创建缓存目录
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 加载持久化的缓存
        self._load_cache_from_disk()
        
        logger.info(f"缓存策略管理器初始化完成: {self.cache_dir}")
    
    def _load_cache_from_disk(self) -> None:
        """从磁盘加载缓存"""
        try:
            cache_file = self.cache_dir / "cache_index.json"
            if cache_file.exists():
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                
                for key, entry_data in data.items():
                    entry = CacheEntry(
                        key=key,
                        value=entry_data['value'],
                        size=entry_data['size'],
                        created_at=entry_data['created_at'],
                        last_accessed=entry_data['last_accessed'],
                        access_count=entry_data['access_count'],
                        ttl=entry_data.get('ttl'),
                        is_hot=entry_data.get('is_hot', False)
                    )
                    
                    # 检查是否过期
                    if not self._is_expired(entry):
                        self.cache[key] = entry
                        self.stats['total_size'] += entry.size
                        heapq.heappush(self.access_heap, (entry.last_accessed, key))
                
                logger.info(f"从磁盘加载缓存: {len(self.cache)}个条目")
        except Exception as e:
            logger.warning(f"从磁盘加载缓存失败: {e}")
    
    def _save_cache_to_disk(self) -> None:
        """保存缓存到磁盘"""
        try:
            cache_file = self.cache_dir / "cache_index.json"
            data = {}
            
            for key, entry in self.cache.items():
                data[key] = {
                    'value': entry.value,
                    'size': entry.size,
                    'created_at': entry.created_at,
                    'last_accessed': entry.last_accessed,
                    'access_count': entry.access_count,
                    'ttl': entry.ttl,
                    'is_hot': entry.is_hot
                }
            
            with open(cache_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"保存缓存到磁盘失败: {e}")
    
    def _is_expired(self, entry: CacheEntry) -> bool:
        """
        检查缓存条目是否过期
        
        Args:
            entry: 缓存条目
        
        Returns:
            是否过期
        """
        current_time = time.time()
        
        # 检查TTL
        if entry.ttl and current_time - entry.created_at > entry.ttl:
            return True
        
        # 检查冷数据TTL
        if self.config.enable_hot_cold and not entry.is_hot:
            if current_time - entry.created_at > self.config.cold_ttl:
                return True
        
        return False
    
    def _evict_entries(self, required_size: int) -> int:
        """
        淘汰缓存条目以释放空间
        
        Args:
            required_size: 需要释放的空间大小
        
        Returns:
            淘汰的条目数量
        """
        evicted_count = 0
        freed_size = 0
        
        # 根据淘汰策略排序
        entries_to_evict = []
        
        if self.config.eviction_policy == EvictionPolicy.LRU:
            # 最近最少使用
            entries = sorted(self.cache.items(), key=lambda x: x[1].last_accessed)
        elif self.config.eviction_policy == EvictionPolicy.LFU:
            # 最少使用频率
            entries = sorted(self.cache.items(), key=lambda x: x[1].access_count)
        elif self.config.eviction_policy == EvictionPolicy.FIFO:
            # 先进先出
            entries = sorted(self.cache.items(), key=lambda x: x[1].created_at)
        else:
            # TTL优先
            entries = sorted(self.cache.items(), key=lambda x: x[1].created_at)
        
        for key, entry in entries:
            # 跳过受保护的条目
            if self.config.enable_protection and key in self.config.protected_keys:
                continue
            
            # 删除条目
            del self.cache[key]
            freed_size += entry.size
            evicted_count += 1
            self.stats['evictions'] += 1
            
            # 检查是否释放了足够的空间
            if freed_size >= required_size:
                break
        
        self.stats['total_size'] -= freed_size
        logger.info(f"淘汰缓存条目: {evicted_count}个, 释放空间: {freed_size/1024/1024:.2f}MB")
        
        return evicted_count
    
    def _update_hot_cold_status(self, entry: CacheEntry) -> None:
        """
        更新热冷数据状态
        
        Args:
            entry: 缓存条目
        """
        if self.config.enable_hot_cold:
            if entry.access_count >= self.config.hot_threshold:
                entry.is_hot = True
            else:
                entry.is_hot = False
    
    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值
        
        Args:
            key: 缓存键
        
        Returns:
            缓存值，不存在或过期则返回None
        """
        if key not in self.cache:
            self.stats['misses'] += 1
            return None
        
        entry = self.cache[key]
        
        # 检查是否过期
        if self._is_expired(entry):
            del self.cache[key]
            self.stats['total_size'] -= entry.size
            self.stats['misses'] += 1
            logger.debug(f"缓存过期: {key}")
            return None
        
        # 更新访问记录
        entry.last_accessed = time.time()
        entry.access_count += 1
        self.stats['hits'] += 1
        
        # 更新热冷状态
        self._update_hot_cold_status(entry)
        
        return entry.value
    
    def put(self, key: str, value: Any, size: int, ttl: Optional[float] = None) -> bool:
        """
        存储缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            size: 数据大小（字节）
            ttl: 生存时间（秒）
        
        Returns:
            是否成功
        """
        current_time = time.time()
        
        # 检查是否已存在
        if key in self.cache:
            old_entry = self.cache[key]
            self.stats['total_size'] -= old_entry.size
        
        # 检查是否需要淘汰
        required_size = size - (self.stats['total_size'] if key not in self.cache else 0)
        if self.stats['total_size'] + size > self.config.max_size:
            self._evict_entries(required_size)
        
        # 创建新条目
        entry = CacheEntry(
            key=key,
            value=value,
            size=size,
            created_at=current_time,
            last_accessed=current_time,
            access_count=0,
            ttl=ttl or self.config.ttl,
            is_hot=False
        )
        
        self.cache[key] = entry
        self.stats['total_size'] += size
        
        # 更新访问堆
        heapq.heappush(self.access_heap, (current_time, key))
        
        return True
    
    def delete(self, key: str) -> bool:
        """
        删除缓存条目
        
        Args:
            key: 缓存键
        
        Returns:
            是否成功
        """
        if key in self.cache:
            entry = self.cache[key]
            del self.cache[key]
            self.stats['total_size'] -= entry.size
            return True
        return False
    
    def clear(self) -> None:
        """清空所有缓存"""
        self.cache.clear()
        self.access_heap.clear()
        self.stats['total_size'] = 0
        logger.info("缓存已清空")
    
    def cleanup_expired(self) -> int:
        """
        清理过期缓存
        
        Returns:
            清理的条目数量
        """
        expired_keys = []
        
        for key, entry in self.cache.items():
            if self._is_expired(entry):
                expired_keys.append(key)
        
        for key in expired_keys:
            self.delete(key)
        
        logger.info(f"清理过期缓存: {len(expired_keys)}个条目")
        return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            统计信息字典
        """
        hit_rate = 0
        total_access = self.stats['hits'] + self.stats['misses']
        if total_access > 0:
            hit_rate = self.stats['hits'] / total_access
        
        hot_count = sum(1 for entry in self.cache.values() if entry.is_hot)
        cold_count = len(self.cache) - hot_count
        
        return {
            'total_entries': len(self.cache),
            'total_size': self.stats['total_size'],
            'max_size': self.config.max_size,
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'evictions': self.stats['evictions'],
            'hit_rate': hit_rate,
            'hot_entries': hot_count,
            'cold_entries': cold_count,
            'eviction_policy': self.config.eviction_policy.value,
            'enable_hot_cold': self.config.enable_hot_cold
        }
    
    def get_config(self) -> Dict[str, Any]:
        """
        获取缓存配置
        
        Returns:
            配置字典
        """
        return {
            'max_size': self.config.max_size,
            'ttl': self.config.ttl,
            'eviction_policy': self.config.eviction_policy.value,
            'enable_hot_cold': self.config.enable_hot_cold,
            'hot_threshold': self.config.hot_threshold,
            'cold_ttl': self.config.cold_ttl,
            'enable_protection': self.config.enable_protection,
            'protected_keys': self.config.protected_keys
        }
    
    def update_config(self, **kwargs) -> None:
        """
        更新缓存配置
        
        Args:
            **kwargs: 配置参数
        """
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                logger.info(f"更新缓存配置: {key}={value}")
        
        # 如果新的max_size小于当前大小，触发淘汰
        if 'max_size' in kwargs and self.stats['total_size'] > self.config.max_size:
            self._evict_entries(self.stats['total_size'] - self.config.max_size)
    
    def add_protected_key(self, key: str) -> None:
        """
        添加受保护的缓存键
        
        Args:
            key: 缓存键
        """
        if key not in self.config.protected_keys:
            self.config.protected_keys.append(key)
            logger.info(f"添加受保护键: {key}")
    
    def remove_protected_key(self, key: str) -> None:
        """
        移除受保护的缓存键
        
        Args:
            key: 缓存键
        """
        if key in self.config.protected_keys:
            self.config.protected_keys.remove(key)
            logger.info(f"移除受保护键: {key}")
    
    def save_to_disk(self) -> None:
        """保存缓存到磁盘"""
        self._save_cache_to_disk()
    
    def load_from_disk(self) -> None:
        """从磁盘加载缓存"""
        self._load_cache_from_disk()
