"""
存储接口定义
定义向量存储和数据库存储的抽象接口
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class VectorStore(ABC):
    """向量存储接口"""
    
    @abstractmethod
    def add_vector(self, vector: Dict[str, Any]) -> None:
        """
        添加单个向量
        
        Args:
            vector: 向量数据
        """
        pass
    
    @abstractmethod
    def add_vectors(self, vectors: List[Dict[str, Any]]) -> None:
        """
        添加多个向量
        
        Args:
            vectors: 向量数据列表
        """
        pass
    
    @abstractmethod
    def search(
        self, 
        query_vector: List[float], 
        limit: int = 20, 
        filter: Optional[Dict] = None,
        similarity_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        搜索向量
        
        Args:
            query_vector: 查询向量
            limit: 返回数量限制
            filter: 过滤条件
            similarity_threshold: 相似度阈值
            
        Returns:
            搜索结果列表
        """
        pass
    
    @abstractmethod
    def delete_by_file_id(self, file_id: str) -> int:
        """
        根据文件ID删除向量
        
        Args:
            file_id: 文件ID
            
        Returns:
            删除的向量数量
        """
        pass
    
    @abstractmethod
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        获取集合统计信息
        
        Returns:
            统计信息字典
        """
        pass
    
    @abstractmethod
    def get_vector_dimension(self) -> int:
        """
        获取向量维度
        
        Returns:
            向量维度
        """
        pass


class DatabaseManager(ABC):
    """数据库管理器接口"""
    
    @abstractmethod
    def add_file(self, file_metadata: Dict[str, Any]) -> bool:
        """
        添加文件元数据
        
        Args:
            file_metadata: 文件元数据
            
        Returns:
            是否添加成功
        """
        pass
    
    @abstractmethod
    def get_file_info(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        获取文件信息
        
        Args:
            file_id: 文件ID
            
        Returns:
            文件信息字典，如果不存在返回None
        """
        pass
    
    @abstractmethod
    def get_file_by_path(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        根据文件路径获取文件信息
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件信息字典，如果不存在返回None
        """
        pass
    
    @abstractmethod
    def update_file_status(self, file_id: str, status: str) -> bool:
        """
        更新文件状态
        
        Args:
            file_id: 文件ID
            status: 新状态
            
        Returns:
            是否更新成功
        """
        pass
    
    @abstractmethod
    def delete_file(self, file_id: str) -> bool:
        """
        删除文件
        
        Args:
            file_id: 文件ID
            
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
    def get_all_files(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        获取所有文件
        
        Args:
            limit: 返回数量限制
            offset: 偏移量
            
        Returns:
            文件列表
        """
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """
        获取数据库统计信息
        
        Returns:
            统计信息字典
        """
        pass