# -*- coding: utf-8 -*-
"""
文件索引器模块

提供文件索引管理功能，支持单文件索引、目录索引和批量索引。
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path
import uuid
import sys

# 处理导入路径
if __name__ == "__main__":
    from data.constants import IndexStatus, ProcessingStatus, FileType
    from data.models.base_models import FileMetadata
    from data.extractors.metadata_extractor import MetadataExtractor
else:
    try:
        from ...data.constants import IndexStatus, ProcessingStatus, FileType
        from ...data.models.base_models import FileMetadata
        from ...data.extractors.metadata_extractor import MetadataExtractor
    except ImportError:
        from data.constants import IndexStatus, ProcessingStatus, FileType
        from data.models.base_models import FileMetadata
        from data.extractors.metadata_extractor import MetadataExtractor


class FileIndexer:
    """文件索引器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, task_manager: Optional[Any] = None):
        """
        初始化文件索引器
        
        Args:
            config: 配置字典
            task_manager: 任务管理器实例，用于提交任务
        """
        self.config = config or {}
        self.logger = None
        
        # 元数据提取器
        self.metadata_extractor = MetadataExtractor()
        
        # 索引状态管理
        self.indexed_files: Dict[str, FileMetadata] = {}  # file_id -> FileMetadata
        self.file_index: Dict[str, str] = {}  # file_path -> file_id
        
        # 任务管理器
        self.task_manager = task_manager
        
        # 初始化统计信息
        self.stats = {
            "total_files": 0,
            "indexed_files": 0,
            "duplicate_files": 0,
            "processing_files": 0,
            "completed_files": 0
        }
    
    def set_task_manager(self, task_manager: Any) -> None:
        """
        设置任务管理器
        
        Args:
            task_manager: 任务管理器实例
        """
        self.task_manager = task_manager
    
    def index_file(self, file_path: str, submit_task: bool = True) -> Optional[FileMetadata]:
        """
        索引单个文件
        
        Args:
            file_path: 文件路径
            submit_task: 是否自动提交处理任务
            
        Returns:
            文件元数据对象，如果索引失败返回None
        """
        try:
            # 检查文件是否已索引
            if file_path in self.file_index:
                file_id = self.file_index[file_path]
                return self.indexed_files.get(file_id)
            
            # 检查文件是否重复
            duplicate_file_id = self.check_duplicate(file_path)
            if duplicate_file_id:
                if self.logger:
                    self.logger.info(f"文件重复，已跳过: {file_path}, 重复文件ID: {duplicate_file_id}")
                self.stats["duplicate_files"] += 1
                return None
            
            # 生成文件ID
            file_id = str(uuid.uuid4())
            
            # 提取文件元数据
            extracted_metadata = self.metadata_extractor.extract(file_path)
            
            if extracted_metadata is None:
                if self.logger:
                    self.logger.error(f"提取文件元数据失败: {file_path}")
                return None
            
            # 创建 FileMetadata 对象
            # 将字符串file_type转换为FileType枚举
            file_type_str = extracted_metadata.get('file_type', 'unknown')
            try:
                file_type = FileType(file_type_str)
            except ValueError:
                file_type = FileType.UNKNOWN
            
            metadata = FileMetadata(
                id=file_id,
                file_path=extracted_metadata.get('file_path', file_path),
                file_name=extracted_metadata.get('file_name', Path(file_path).name),
                file_type=file_type,
                file_size=extracted_metadata.get('file_size', 0),
                file_hash=extracted_metadata.get('file_hash', ''),
                created_at=datetime.now().timestamp(),
                updated_at=datetime.now().timestamp(),
                processing_status=ProcessingStatus.PENDING
            )
            
            # 保存到索引
            self.indexed_files[file_id] = metadata
            self.file_index[file_path] = file_id
            
            # 更新统计信息
            self.stats["indexed_files"] += 1
            self.stats["total_files"] += 1
            
            if self.logger:
                self.logger.info(f"文件索引成功: {file_path}, 文件ID: {file_id}")
            
            # 提交任务到调度器
            if submit_task and self.task_manager:
                self._submit_processing_task(metadata)
            
            return metadata
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"索引文件失败: {file_path}, 错误: {e}")
            return None
    
    def index_files(self, file_paths: List[str], submit_task: bool = True) -> List[FileMetadata]:
        """
        批量索引文件
        
        Args:
            file_paths: 文件路径列表
            submit_task: 是否自动提交处理任务
            
        Returns:
            文件元数据对象列表
        """
        indexed_metadata = []
        
        for file_path in file_paths:
            metadata = self.index_file(file_path, submit_task=False)
            if metadata:
                indexed_metadata.append(metadata)
        
        # 批量提交任务
        if submit_task and self.task_manager and indexed_metadata:
            for metadata in indexed_metadata:
                self._submit_processing_task(metadata)
        
        return indexed_metadata
    
    def update_file(self, file_path: str, submit_task: bool = True) -> Optional[FileMetadata]:
        """
        更新文件索引
        
        Args:
            file_path: 文件路径
            submit_task: 是否自动提交处理任务
            
        Returns:
            文件元数据对象，如果更新失败返回None
        """
        try:
            # 检查文件是否已索引
            if file_path in self.file_index:
                file_id = self.file_index[file_path]
                
                # 更新元数据
                extracted_metadata = self.metadata_extractor.extract(file_path)
                
                if extracted_metadata:
                    # 创建 FileMetadata 对象
                    # 将字符串file_type转换为FileType枚举
                    file_type_str = extracted_metadata.get('file_type', 'unknown')
                    try:
                        file_type = FileType(file_type_str)
                    except ValueError:
                        file_type = FileType.UNKNOWN
                    
                    metadata = FileMetadata(
                        id=file_id,
                        file_path=extracted_metadata.get('file_path', file_path),
                        file_name=extracted_metadata.get('file_name', Path(file_path).name),
                        file_type=file_type,
                        file_size=extracted_metadata.get('file_size', 0),
                        file_hash=extracted_metadata.get('file_hash', ''),
                        created_at=datetime.now().timestamp(),
                        updated_at=datetime.now().timestamp(),
                        processing_status=ProcessingStatus.PENDING
                    )
                    
                    # 保存到索引
                    self.indexed_files[file_id] = metadata
                    
                    if self.logger:
                        self.logger.info(f"文件索引更新成功: {file_path}")
                    
                    # 提交任务到调度器
                    if submit_task and self.task_manager:
                        self._submit_processing_task(metadata)
                    
                    return metadata
            else:
                # 文件未索引，直接索引
                return self.index_file(file_path, submit_task)
            
            return None
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"更新文件索引失败: {file_path}, 错误: {e}")
            return None
    
    def delete_file(self, file_path: str) -> bool:
        """
        删除文件索引
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否删除成功
        """
        try:
            if file_path in self.file_index:
                file_id = self.file_index[file_path]
                return self.remove_file(file_id)
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f"删除文件索引失败: {file_path}, 错误: {e}")
            return False
    
    def _submit_processing_task(self, metadata: FileMetadata) -> Optional[str]:
        """
        提交文件处理任务到调度器
        
        Args:
            metadata: 文件元数据对象
            
        Returns:
            任务ID，如果提交失败返回None
        """
        try:
            if not self.task_manager:
                return None
            
            # 根据文件类型选择任务类型
            task_type_map = {
                "image": "file_embed_image",
                "video": "file_embed_video",
                "audio": "file_embed_audio"
            }
            
            task_type = task_type_map.get(metadata.file_type.value, "file_embed_unknown")
            
            # 提交任务
            task_data = {
                "file_id": metadata.file_id,
                "file_path": metadata.file_path,
                "file_type": metadata.file_type.value,
                "file_hash": metadata.file_hash,
                "metadata": metadata.to_dict()
            }
            
            task_id = self.task_manager.create_task(
                task_type=task_type,
                task_data=task_data,
                priority=5,
                max_retries=3
            )
            
            if self.logger:
                self.logger.info(f"任务提交成功: {task_id}, 文件: {metadata.file_path}, 任务类型: {task_type}")
            
            return task_id
        except Exception as e:
            if self.logger:
                self.logger.error(f"提交任务失败: {metadata.file_path}, 错误: {e}")
            return None
    
    def index_directory(self, directory: str, recursive: bool = True) -> List[FileMetadata]:
        """
        索引目录
        
        Args:
            directory: 目录路径
            recursive: 是否递归扫描
            
        Returns:
            文件元数据列表
        """
        from .file_scanner import FileScanner
        
        try:
            # 扫描目录
            scanner = FileScanner(self.config)
            scanner.recursive = recursive
            file_paths = scanner.scan_directory(directory)
            
            # 索引所有文件
            metadata_list = []
            for file_path in file_paths:
                metadata = self.index_file(file_path)
                if metadata:
                    metadata_list.append(metadata)
            
            if self.logger:
                self.logger.info(f"目录索引完成: {directory}, 共索引 {len(metadata_list)} 个文件")
            
            return metadata_list
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"索引目录失败: {directory}, 错误: {e}")
            return []
    
    def index_batch(self, file_paths: List[str]) -> List[FileMetadata]:
        """
        批量索引文件
        
        Args:
            file_paths: 文件路径列表
            
        Returns:
            文件元数据列表
        """
        metadata_list = []
        
        for file_path in file_paths:
            metadata = self.index_file(file_path)
            if metadata:
                metadata_list.append(metadata)
        
        return metadata_list
    
    def update_file_status(self, file_id: str, status: ProcessingStatus) -> bool:
        """
        更新文件处理状态
        
        Args:
            file_id: 文件ID
            status: 处理状态
            
        Returns:
            是否更新成功
        """
        try:
            if file_id in self.indexed_files:
                metadata = self.indexed_files[file_id]
                metadata.processing_status = status
                
                if status == ProcessingStatus.COMPLETED:
                    metadata.processed_at = datetime.now().timestamp()
                
                return True
            return False
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"更新文件状态失败: {file_id}, 错误: {e}")
            return False
    
    def get_file_metadata(self, file_id: str) -> Optional[FileMetadata]:
        """
        获取文件元数据
        
        Args:
            file_id: 文件ID
            
        Returns:
            文件元数据对象，如果不存在返回None
        """
        return self.indexed_files.get(file_id)
    
    def get_file_id(self, file_path: str) -> Optional[str]:
        """
        根据文件路径获取文件ID
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件ID，如果不存在返回None
        """
        return self.file_index.get(file_path)
    
    def remove_file(self, file_id: str) -> bool:
        """
        从索引中移除文件
        
        Args:
            file_id: 文件ID
            
        Returns:
            是否移除成功
        """
        try:
            if file_id in self.indexed_files:
                metadata = self.indexed_files[file_id]
                file_path = metadata.file_path
                
                # 从索引中移除
                del self.indexed_files[file_id]
                if file_path in self.file_index:
                    del self.file_index[file_path]
                
                if self.logger:
                    self.logger.info(f"文件已从索引中移除: {file_id}")
                
                return True
            return False
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"移除文件失败: {file_id}, 错误: {e}")
            return False
    
    def check_duplicate(self, file_path: str) -> Optional[str]:
        """
        检查文件是否重复（基于文件哈希）
        
        Args:
            file_path: 文件路径
            
        Returns:
            如果重复返回原文件ID，否则返回None
        """
        try:
            # 提取当前文件的哈希
            import hashlib
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            file_hash = sha256_hash.hexdigest()
            
            # 检查是否有相同哈希的文件
            for file_id, metadata in self.indexed_files.items():
                if metadata.file_hash == file_hash:
                    return file_id
            
            return None
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"检查文件重复失败: {file_path}, 错误: {e}")
            return None
    
    def add_reference(self, file_id: str) -> bool:
        """
        增加文件引用计数
        
        Args:
            file_id: 文件ID
            
        Returns:
            是否增加成功
        """
        try:
            if file_id in self.indexed_files:
                self.indexed_files[file_id].reference_count += 1
                return True
            return False
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"增加引用计数失败: {file_id}, 错误: {e}")
            return False
    
    def remove_reference(self, file_id: str) -> bool:
        """
        减少文件引用计数
        
        Args:
            file_id: 文件ID
            
        Returns:
            是否减少成功
        """
        try:
            if file_id in self.indexed_files:
                metadata = self.indexed_files[file_id]
                metadata.reference_count -= 1
                
                # 如果引用计数为0，自动移除
                if metadata.reference_count <= 0:
                    self.remove_file(file_id)
                
                return True
            return False
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"减少引用计数失败: {file_id}, 错误: {e}")
            return False
    
    def get_index_stats(self) -> Dict[str, Any]:
        """
        获取索引统计信息
        
        Returns:
            统计信息字典
        """
        stats = {
            "total_files": len(self.indexed_files),
            "by_status": {},
            "by_type": {}
        }
        
        for metadata in self.indexed_files.values():
            # 按状态统计
            status = metadata.processing_status.value
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
            
            # 按类型统计
            file_type = metadata.file_type.value
            stats["by_type"][file_type] = stats["by_type"].get(file_type, 0) + 1
        
        return stats
    
    def cleanup_orphaned_files(self) -> List[str]:
        """
        清理无引用的文件
        
        Returns:
            被清理的文件ID列表
        """
        orphaned_ids = []
        
        for file_id, metadata in list(self.indexed_files.items()):
            if metadata.reference_count <= 0:
                orphaned_ids.append(file_id)
                self.remove_file(file_id)
        
        if self.logger and orphaned_ids:
            self.logger.info(f"清理了 {len(orphaned_ids)} 个无引用文件")
        
        return orphaned_ids