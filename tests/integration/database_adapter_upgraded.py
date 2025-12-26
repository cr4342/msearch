#!/usr/bin/env python3
"""
同步数据库适配器
为数据库升级测试提供同步API，包装现有的异步DatabaseAdapter
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

import asyncio
from typing import Dict, Any, List, Optional
from src.common.storage.database_adapter import DatabaseAdapter


class DatabaseAdapterUpgraded:
    """同步数据库适配器，用于数据库升级测试"""
    
    def __init__(self):
        """初始化数据库适配器"""
        self.db = DatabaseAdapter()
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
    
    def _run_async(self, coro):
        """运行异步函数并返回结果"""
        return self.loop.run_until_complete(coro)
    
    def insert_file(self, file_info: Dict[str, Any]) -> str:
        """插入文件记录"""
        # 确保文件信息包含必要字段
        if 'id' not in file_info:
            import uuid
            file_info['id'] = str(uuid.uuid4())
        
        if 'created_at' not in file_info:
            from datetime import datetime
            file_info['created_at'] = datetime.now().timestamp()
            file_info['modified_at'] = file_info['created_at']
        
        # 添加缺失的必填字段
        if 'file_size' not in file_info:
            file_info['file_size'] = 0
        
        # 处理字段名称差异（测试使用'hash'而不是'file_hash'）
        if 'hash' in file_info and 'file_hash' not in file_info:
            file_info['file_hash'] = file_info['hash']
        elif 'file_hash' not in file_info:
            file_info['file_hash'] = 'default_hash'
        
        return self._run_async(self.db.insert_file(file_info))
    
    def get_file_by_category(self, category: str) -> List[Dict[str, Any]]:
        """根据分类获取文件"""
        return self._run_async(self.db.get_file_by_category(category))
    
    def create_file_relationship(self, source_file_id: str, related_file_id: str, 
                              relationship_type: str, confidence_score: float,
                              metadata: Dict[str, Any]) -> bool:
        """创建文件关系"""
        return self._run_async(self.db.create_file_relationship(
            source_file_id, related_file_id, relationship_type, confidence_score, metadata
        ))
    
    def get_file_relationships(self, file_id: str) -> List[Dict[str, Any]]:
        """获取文件关系"""
        return self._run_async(self.db.get_file_relationships(file_id))
    
    def insert_video_segment(self, segment_data: Dict[str, Any]) -> str:
        """插入视频片段"""
        return self._run_async(self.db.insert_video_segment(segment_data))
    
    def get_video_segments_by_file(self, file_id: str) -> List[Dict[str, Any]]:
        """获取视频片段"""
        return self._run_async(self.db.get_video_segments_by_file(file_id))
    
    def get_deletable_files(self) -> List[Dict[str, Any]]:
        """获取可删除文件"""
        return self._run_async(self.db.get_deletable_files())
    
    def get_database_stats(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        return self._run_async(self.db.get_database_stats())
    
    def get_schema_version(self) -> Dict[str, Any]:
        """获取Schema版本"""
        return self._run_async(self.db.get_schema_version())
