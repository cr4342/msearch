# -*- coding: utf-8 -*-
"""
基于内容哈希的任务去重管理器

职责：
- 计算文件内容哈希
- 检查文件是否已存在
- 管理哈希索引
- 处理重复文件事件
"""

import os
import hashlib
import threading
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ContentHashDeduplicator:
    """
    基于内容哈希的任务去重管理器
    
    使用文件内容哈希（而非文件名）识别重复文件，实现：
    - 避免重复处理相同内容的文件
    - 支持文件移动检测（重命名或移动后不会重复处理）
    - 检测文件内容变化（修改后能重新处理）
    """
    
    def __init__(self, db_manager, config: Optional[Dict[str, Any]] = None):
        """
        初始化去重管理器
        
        Args:
            db_manager: 数据库管理器
            config: 配置字典
        """
        self.db = db_manager
        self.config = config or {}
        
        # 配置选项
        self.enabled = self.config.get('enabled', True)
        self.hash_algorithm = self.config.get('hash_algorithm', 'md5')
        self.video_sample_size = self.config.get('video_sample_size', 1024 * 1024)  # 1MB
        self.cache_size = self.config.get('cache_size', 1000)
        self.cache_ttl = self.config.get('cache_ttl', 3600)  # 1小时
        
        # 内存缓存: file_path -> (hash, timestamp)
        self._hash_cache: Dict[str, Tuple[str, datetime]] = {}
        self._cache_lock = threading.Lock()
        
        logger.info(f"内容哈希去重管理器初始化完成 (enabled={self.enabled})")
    
    def calculate_file_hash(self, file_path: str, file_type: str) -> Optional[str]:
        """
        计算文件内容哈希
        
        Args:
            file_path: 文件路径
            file_type: 文件类型 (image/video/audio)
            
        Returns:
            文件内容哈希，如果计算失败返回None
        """
        if not self.enabled:
            return None
        
        try:
            # 检查缓存
            with self._cache_lock:
                if file_path in self._hash_cache:
                    cached_hash, cached_time = self._hash_cache[file_path]
                    # 检查缓存是否过期
                    if datetime.now() - cached_time < timedelta(seconds=self.cache_ttl):
                        logger.debug(f"使用缓存的哈希值: {file_path}")
                        return cached_hash
            
            # 根据文件类型选择哈希策略
            if file_type == 'video':
                hash_value = self._calculate_video_hash(file_path)
            else:
                hash_value = self._calculate_full_hash(file_path)
            
            if hash_value:
                # 更新缓存
                with self._cache_lock:
                    self._hash_cache[file_path] = (hash_value, datetime.now())
                    # 清理过期缓存
                    self._cleanup_cache()
            
            return hash_value
            
        except Exception as e:
            logger.error(f"计算文件哈希失败: {file_path}, 错误: {e}")
            return None
    
    def _calculate_full_hash(self, file_path: str) -> Optional[str]:
        """
        计算完整文件哈希
        
        Args:
            file_path: 文件路径
            
        Returns:
            MD5哈希值
        """
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logger.error(f"计算完整哈希失败: {file_path}, 错误: {e}")
            return None
    
    def _calculate_video_hash(self, file_path: str) -> Optional[str]:
        """
        计算视频文件哈希（采样）
        
        对于大视频文件，采样计算前1MB和后1MB的哈希，平衡性能和准确性
        
        Args:
            file_path: 文件路径
            
        Returns:
            MD5哈希值
        """
        try:
            file_size = os.path.getsize(file_path)
            hash_md5 = hashlib.md5()
            
            with open(file_path, "rb") as f:
                # 读取前1MB
                hash_md5.update(f.read(self.video_sample_size))
                
                # 如果文件大于2MB，读取后1MB
                if file_size > 2 * self.video_sample_size:
                    f.seek(-self.video_sample_size, 2)
                    hash_md5.update(f.read())
            
            return hash_md5.hexdigest()
        except Exception as e:
            logger.error(f"计算视频哈希失败: {file_path}, 错误: {e}")
            return None
    
    def check_duplicate(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """
        检查文件是否已存在
        
        Args:
            file_hash: 文件内容哈希
            
        Returns:
            已存在的文件记录，如果不存在返回None
        """
        if not self.enabled or not file_hash:
            return None
        
        try:
            # 查询数据库
            return self.db.get_file_by_hash(file_hash)
        except Exception as e:
            logger.error(f"检查重复文件失败: {e}")
            return None
    
    def handle_duplicate(
        self,
        file_path: str,
        file_hash: str,
        existing_record: Dict[str, Any]
    ) -> str:
        """
        处理重复文件
        
        Args:
            file_path: 新文件路径
            file_hash: 文件哈希
            existing_record: 已存在的文件记录
            
        Returns:
            处理结果: 'skipped' | 'retry' | 'update_path' | 'new'
        """
        existing_status = existing_record.get('processing_status')
        existing_path = existing_record.get('file_path')
        file_id = existing_record.get('id')
        
        # 情况1: 已存在且处理完成
        if existing_status == 'completed':
            if existing_path != file_path:
                # 文件移动，更新路径
                logger.info(f"文件移动 detected: {existing_path} -> {file_path}")
                try:
                    self.db.update_file_path(file_id, file_path)
                    return 'update_path'
                except Exception as e:
                    logger.error(f"更新文件路径失败: {e}")
                    return 'skipped'
            else:
                # 完全重复，跳过
                logger.info(f"重复文件，跳过: {file_path}")
                return 'skipped'
        
        # 情况2: 已存在但处理失败
        elif existing_status == 'failed':
            logger.info(f"文件之前处理失败，重新提交: {file_path}")
            try:
                self.db.update_file_status(file_id, 'pending')
                return 'retry'
            except Exception as e:
                logger.error(f"更新文件状态失败: {e}")
                return 'skipped'
        
        # 情况3: 正在处理中
        elif existing_status == 'pending' or existing_status == 'processing':
            logger.info(f"文件正在处理中，跳过: {file_path}")
            return 'skipped'
        
        # 情况4: 其他状态
        else:
            logger.warning(f"未知状态 {existing_status}，跳过: {file_path}")
            return 'skipped'
    
    def process_new_file(
        self,
        file_path: str,
        file_type: str
    ) -> Tuple[bool, Optional[str], str]:
        """
        处理新文件（带去重检查）
        
        Args:
            file_path: 文件路径
            file_type: 文件类型
            
        Returns:
            (是否为新文件, 文件ID或None, 处理结果)
        """
        if not self.enabled:
            # 去重禁用，直接创建新记录
            file_id = self._create_new_file_record(file_path, file_type, None)
            return True, file_id, 'new'
        
        # 1. 计算文件哈希
        file_hash = self.calculate_file_hash(file_path, file_type)
        if not file_hash:
            logger.warning(f"无法计算文件哈希，按新文件处理: {file_path}")
            file_id = self._create_new_file_record(file_path, file_type, None)
            return True, file_id, 'new'
        
        # 2. 检查是否已存在
        existing = self.check_duplicate(file_hash)
        
        if existing:
            # 3. 处理重复
            result = self.handle_duplicate(file_path, file_hash, existing)
            
            if result == 'skipped':
                return False, None, 'skipped'
            elif result in ['retry', 'update_path']:
                return True, existing.get('id'), result
        
        # 4. 新文件，创建记录
        file_id = self._create_new_file_record(file_path, file_type, file_hash)
        return True, file_id, 'new'
    
    def _create_new_file_record(
        self,
        file_path: str,
        file_type: str,
        file_hash: Optional[str]
    ) -> str:
        """
        创建新文件记录
        
        Args:
            file_path: 文件路径
            file_type: 文件类型
            file_hash: 文件哈希
            
        Returns:
            文件ID
        """
        import uuid
        import time
        
        file_id = str(uuid.uuid4())
        
        try:
            self.db.insert_file_metadata({
                'id': file_id,
                'file_path': file_path,
                'file_name': os.path.basename(file_path),
                'file_type': file_type,
                'file_size': os.path.getsize(file_path),
                'file_hash': file_hash,
                'processing_status': 'pending',
                'created_at': time.time(),
                'updated_at': time.time()
            })
            logger.debug(f"创建新文件记录: {file_id}, {file_path}")
        except Exception as e:
            logger.error(f"创建文件记录失败: {e}")
            raise
        
        return file_id
    
    def _cleanup_cache(self):
        """清理过期缓存"""
        try:
            now = datetime.now()
            expired_keys = [
                path for path, (_, timestamp) in self._hash_cache.items()
                if now - timestamp > timedelta(seconds=self.cache_ttl)
            ]
            for key in expired_keys:
                del self._hash_cache[key]
            
            # 如果缓存过大，移除最旧的条目
            if len(self._hash_cache) > self.cache_size:
                sorted_items = sorted(
                    self._hash_cache.items(),
                    key=lambda x: x[1][1]  # 按时间戳排序
                )
                # 移除最旧的20%
                items_to_remove = int(self.cache_size * 0.2)
                for key, _ in sorted_items[:items_to_remove]:
                    del self._hash_cache[key]
        
        except Exception as e:
            logger.warning(f"清理缓存失败: {e}")
    
    def clear_cache(self):
        """清空哈希缓存"""
        with self._cache_lock:
            self._hash_cache.clear()
            logger.info("哈希缓存已清空")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            统计信息字典
        """
        with self._cache_lock:
            return {
                'cache_size': len(self._hash_cache),
                'max_cache_size': self.cache_size,
                'enabled': self.enabled,
                'hash_algorithm': self.hash_algorithm
            }
