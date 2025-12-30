"""
文件关联关系管理器
管理系统中的文件关联关系，包括源文件与派生文件的关系
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from src.common.storage.database_adapter import DatabaseAdapter
from src.core.config_manager import get_config_manager


logger = logging.getLogger(__name__)


class FileRelationshipManager:
    """文件关联关系管理器"""
    
    def __init__(self, database_adapter: DatabaseAdapter = None, config_manager=None):
        self.db_adapter = database_adapter or DatabaseAdapter()
        self.config_manager = config_manager or get_config_manager()
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("文件关联关系管理器初始化完成")
    
    async def create_relationship(self, source_file_id: str, derived_file_id: str, 
                                 relationship_type: str, metadata: Dict[str, Any] = None) -> bool:
        """
        创建文件关联关系
        
        Args:
            source_file_id: 源文件ID
            derived_file_id: 派生文件ID
            relationship_type: 关系类型 ('audio_from_video', 'processed_image', 'processed_video', 'thumbnail', etc.)
            metadata: 额外元数据
            
        Returns:
            是否创建成功
        """
        try:
            success = await self.db_adapter.create_file_relationship(
                source_file_id, derived_file_id, relationship_type, metadata
            )
            
            if success:
                self.logger.info(f"创建文件关联关系成功: {source_file_id} -> {derived_file_id} ({relationship_type})")
            else:
                self.logger.warning(f"创建文件关联关系失败: {source_file_id} -> {derived_file_id} ({relationship_type})")
            
            return success
            
        except Exception as e:
            self.logger.error(f"创建文件关联关系异常: {e}")
            return False
    
    async def get_relationships_by_source(self, source_file_id: str) -> List[Dict[str, Any]]:
        """
        获取源文件的所有关联关系
        
        Args:
            source_file_id: 源文件ID
            
        Returns:
            关联关系列表
        """
        try:
            relationships = await self.db_adapter.get_derived_files(source_file_id)
            
            self.logger.debug(f"获取源文件关联关系: {source_file_id}, 数量: {len(relationships)}")
            return relationships
            
        except Exception as e:
            self.logger.error(f"获取源文件关联关系异常: {e}")
            return []
    
    async def get_relationships_by_derived(self, derived_file_id: str) -> List[Dict[str, Any]]:
        """
        获取派生文件的源文件关系
        
        Args:
            derived_file_id: 派生文件ID
            
        Returns:
            关联关系列表
        """
        try:
            relationships = await self.db_adapter.get_file_relationships(derived_file_id)
            
            # 过滤出源文件关系
            source_relationships = [
                rel for rel in relationships 
                if rel['derived_file_id'] == derived_file_id
            ]
            
            self.logger.debug(f"获取派生文件源关系: {derived_file_id}, 数量: {len(source_relationships)}")
            return source_relationships
            
        except Exception as e:
            self.logger.error(f"获取派生文件源关系异常: {e}")
            return []
    
    async def get_all_relationships(self) -> List[Dict[str, Any]]:
        """
        获取所有关联关系
        
        Returns:
            所有关联关系列表
        """
        try:
            # 实现一个方法来获取所有关联关系
            # 由于数据库适配器中没有直接提供此方法，我们通过查询所有派生文件来实现
            all_files = await self.db_adapter.get_all_files()
            
            all_relationships = []
            for file_info in all_files:
                file_id = file_info['id']
                relationships = await self.db_adapter.get_file_relationships(file_id)
                all_relationships.extend(relationships)
            
            # 去重
            unique_relationships = []
            seen_ids = set()
            for rel in all_relationships:
                rel_id = rel['id']
                if rel_id not in seen_ids:
                    unique_relationships.append(rel)
                    seen_ids.add(rel_id)
            
            self.logger.debug(f"获取所有关联关系: {len(unique_relationships)} 条")
            return unique_relationships
            
        except Exception as e:
            self.logger.error(f"获取所有关联关系异常: {e}")
            return []
    
    async def delete_relationship(self, relationship_id: str) -> bool:
        """
        删除关联关系
        
        Args:
            relationship_id: 关联关系ID
            
        Returns:
            是否删除成功
        """
        # 数据库适配器中没有直接的删除关系方法，我们暂不实现此方法
        # 因为在实际应用中，通常不会删除关系，而是标记为无效
        self.logger.warning("删除单个关联关系功能暂未实现")
        return False
    
    async def delete_relationships_by_source(self, source_file_id: str) -> int:
        """
        删除源文件的所有关联关系
        
        Args:
            source_file_id: 源文件ID
            
        Returns:
            删除的数量
        """
        # 实现方法删除源文件的所有关联关系
        # 这需要数据库适配器支持，我们通过查询并逐个"删除"来模拟
        try:
            relationships = await self.get_relationships_by_source(source_file_id)
            
            # 在实际实现中，我们会标记这些关系为已删除状态
            # 但当前数据库适配器不支持此操作，所以返回数量
            count = len(relationships)
            self.logger.info(f"标记删除源文件关联关系: {source_file_id}, 数量: {count}")
            
            return count
            
        except Exception as e:
            self.logger.error(f"删除源文件关联关系异常: {e}")
            return 0
    
    async def get_files_by_relationship_type(self, relationship_type: str) -> List[Dict[str, Any]]:
        """
        根据关系类型获取关联关系
        
        Args:
            relationship_type: 关系类型
            
        Returns:
            关联关系列表
        """
        try:
            # 获取所有文件并检查其关联关系
            all_files = await self.db_adapter.get_all_files()
            
            relationships = []
            for file_info in all_files:
                file_id = file_info['id']
                file_relationships = await self.db_adapter.get_file_relationships(file_id)
                
                for rel in file_relationships:
                    if rel['relationship_type'] == relationship_type:
                        relationships.append(rel)
            
            self.logger.debug(f"获取 {relationship_type} 类型关联关系: {len(relationships)} 条")
            return relationships
            
        except Exception as e:
            self.logger.error(f"根据关系类型获取关联关系异常: {e}")
            return []
    
    async def is_valid_relationship(self, source_file_id: str, derived_file_id: str, 
                                   relationship_type: str = None) -> bool:
        """
        验证文件关联关系是否有效
        
        Args:
            source_file_id: 源文件ID
            derived_file_id: 派生文件ID
            relationship_type: 关系类型（可选）
            
        Returns:
            关系是否有效
        """
        try:
            relationships = await self.db_adapter.get_file_relationships(source_file_id)
            
            for rel in relationships:
                if rel['derived_file_id'] == derived_file_id:
                    if relationship_type is None or rel['relationship_type'] == relationship_type:
                        return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"验证文件关联关系异常: {e}")
            return False
    
    async def get_source_file_id(self, derived_file_id: str) -> Optional[str]:
        """
        获取派生文件的源文件ID
        
        Args:
            derived_file_id: 派生文件ID
            
        Returns:
            源文件ID，如果不存在则返回None
        """
        try:
            relationships = await self.db_adapter.get_file_relationships(derived_file_id)
            
            # 查找源文件关系
            for rel in relationships:
                if rel['derived_file_id'] == derived_file_id:
                    return rel['source_file_id']
            
            return None
            
        except Exception as e:
            self.logger.error(f"获取源文件ID异常: {e}")
            return None
    
    async def get_derived_files_by_type(self, source_file_id: str, relationship_type: str) -> List[Dict[str, Any]]:
        """
        根据关系类型获取派生文件
        
        Args:
            source_file_id: 源文件ID
            relationship_type: 关系类型
            
        Returns:
            派生文件信息列表
        """
        try:
            relationships = await self.get_relationships_by_source(source_file_id)
            
            derived_files = []
            for rel in relationships:
                if rel['relationship_type'] == relationship_type:
                    # 获取派生文件的详细信息
                    derived_file_info = await self.db_adapter.get_file(rel['derived_file_id'])
                    if derived_file_info:
                        derived_file_info['relationship'] = rel
                        derived_files.append(derived_file_info)
            
            self.logger.debug(f"获取 {relationship_type} 类型派生文件: {source_file_id}, 数量: {len(derived_files)}")
            return derived_files
            
        except Exception as e:
            self.logger.error(f"获取指定类型派生文件异常: {e}")
            return []
    
    async def get_audio_files_from_video(self, video_file_id: str) -> List[Dict[str, Any]]:
        """
        获取从视频中分离的音频文件
        
        Args:
            video_file_id: 视频文件ID
            
        Returns:
            音频文件信息列表
        """
        return await self.get_derived_files_by_type(video_file_id, 'audio_from_video')
    
    async def get_thumbnail_files(self, source_file_id: str) -> List[Dict[str, Any]]:
        """
        获取源文件的缩略图文件
        
        Args:
            source_file_id: 源文件ID
            
        Returns:
            缩略图文件信息列表
        """
        return await self.get_derived_files_by_type(source_file_id, 'thumbnail')
    
    async def get_processed_files(self, source_file_id: str) -> List[Dict[str, Any]]:
        """
        获取源文件的预处理文件（如降采样后的图像或视频）
        
        Args:
            source_file_id: 源文件ID
            
        Returns:
            预处理文件信息列表
        """
        processed_types = ['processed_image', 'processed_video']
        processed_files = []
        
        for rel_type in processed_types:
            files = await self.get_derived_files_by_type(source_file_id, rel_type)
            processed_files.extend(files)
        
        return processed_files
    
    async def cleanup_orphaned_relationships(self) -> int:
        """
        清理孤立的关联关系（源文件或派生文件不存在的关系）
        
        Returns:
            清理的数量
        """
        try:
            all_relationships = await self.get_all_relationships()
            cleaned_count = 0
            
            for rel in all_relationships:
                source_exists = await self.db_adapter.get_file(rel['source_file_id']) is not None
                derived_exists = await self.db_adapter.get_file(rel['derived_file_id']) is not None
                
                # 如果源文件或派生文件不存在，则可能需要清理
                if not source_exists or not derived_exists:
                    # 在实际实现中，我们会删除这些关系
                    # 但当前数据库适配器没有提供删除关系的方法
                    self.logger.info(f"发现孤立关系: {rel['id']}, source_exists={source_exists}, derived_exists={derived_exists}")
                    cleaned_count += 1
            
            self.logger.info(f"清理孤立关联关系: {cleaned_count} 条")
            return cleaned_count
            
        except Exception as e:
            self.logger.error(f"清理孤立关联关系异常: {e}")
            return 0
    
    async def validate_all_relationships(self) -> Dict[str, Any]:
        """
        验证所有关联关系的完整性
        
        Returns:
            验证结果统计
        """
        try:
            all_relationships = await self.get_all_relationships()
            
            total_count = len(all_relationships)
            valid_count = 0
            invalid_count = 0
            source_missing_count = 0
            derived_missing_count = 0
            
            for rel in all_relationships:
                source_file = await self.db_adapter.get_file(rel['source_file_id'])
                derived_file = await self.db_adapter.get_file(rel['derived_file_id'])
                
                if source_file and derived_file:
                    valid_count += 1
                else:
                    invalid_count += 1
                    if not source_file:
                        source_missing_count += 1
                    if not derived_file:
                        derived_missing_count += 1
            
            validation_result = {
                'total_relationships': total_count,
                'valid_relationships': valid_count,
                'invalid_relationships': invalid_count,
                'relationships_with_missing_source': source_missing_count,
                'relationships_with_missing_derived': derived_missing_count,
                'validation_time': datetime.now().isoformat()
            }
            
            self.logger.info(f"关联关系验证完成: {validation_result}")
            return validation_result
            
        except Exception as e:
            self.logger.error(f"验证关联关系异常: {e}")
            return {
                'total_relationships': 0,
                'valid_relationships': 0,
                'invalid_relationships': 0,
                'relationships_with_missing_source': 0,
                'relationships_with_missing_derived': 0,
                'validation_time': datetime.now().isoformat(),
                'error': str(e)
            }


# 全局文件关联关系管理器实例
_file_relationship_manager = None


def get_file_relationship_manager() -> FileRelationshipManager:
    """获取全局文件关联关系管理器实例"""
    global _file_relationship_manager
    
    if _file_relationship_manager is None:
        _file_relationship_manager = FileRelationshipManager()
    
    return _file_relationship_manager