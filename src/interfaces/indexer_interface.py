"""
文件索引器接口定义
定义文件索引器的抽象接口
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class FileIndexer(ABC):
    """文件索引器接口"""
    
    @abstractmethod
    def index_file(self, file_path: str, submit_task: bool = True) -> Optional[Dict[str, Any]]:
        """
        索引单个文件
        
        Args:
            file_path: 文件路径
            submit_task: 是否自动提交处理任务
            
        Returns:
            文件元数据字典，如果索引失败返回None
        """
        pass
    
    @abstractmethod
    def index_files(self, file_paths: List[str], submit_task: bool = True) -> List[Dict[str, Any]]:
        """
        索引多个文件
        
        Args:
            file_paths: 文件路径列表
            submit_task: 是否自动提交处理任务
            
        Returns:
            文件元数据列表
        """
        pass
    
    @abstractmethod
    def index_directory(self, directory: str, recursive: bool = True) -> List[Dict[str, Any]]:
        """
        索引目录
        
        Args:
            directory: 目录路径
            recursive: 是否递归索引子目录
            
        Returns:
            文件元数据列表
        """
        pass
    
    @abstractmethod
    def get_indexed_files(self) -> List[Dict[str, Any]]:
        """
        获取已索引的文件列表
        
        Returns:
            文件元数据列表
        """
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """
        获取索引统计信息
        
        Returns:
            统计信息字典
        """
        pass