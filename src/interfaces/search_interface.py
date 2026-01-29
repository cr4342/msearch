"""
搜索引擎接口定义
定义搜索引擎的抽象接口
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class SearchEngine(ABC):
    """搜索引擎接口"""
    
    @abstractmethod
    async def search(
        self, 
        query: str, 
        k: int = 10, 
        modalities: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        执行文本搜索
        
        Args:
            query: 查询文本
            k: 返回结果数量
            modalities: 模态类型列表
            filters: 过滤条件
            
        Returns:
            搜索结果字典
        """
        pass
    
    @abstractmethod
    async def image_search(
        self, 
        image_path: str, 
        k: int = 10, 
        modalities: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        执行图像搜索
        
        Args:
            image_path: 图像文件路径
            k: 返回结果数量
            modalities: 模态类型列表
            filters: 过滤条件
            
        Returns:
            搜索结果字典
        """
        pass
    
    @abstractmethod
    async def audio_search(
        self, 
        audio_path: str, 
        k: int = 10, 
        modalities: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        执行音频搜索
        
        Args:
            audio_path: 音频文件路径
            k: 返回结果数量
            modalities: 模态类型列表
            filters: 过滤条件
            
        Returns:
            搜索结果字典
        """
        pass
    
    @abstractmethod
    async def video_search(
        self, 
        video_path: str, 
        k: int = 10, 
        modalities: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        执行视频搜索
        
        Args:
            video_path: 视频文件路径
            k: 返回结果数量
            modalities: 模态类型列表
            filters: 过滤条件
            
        Returns:
            搜索结果字典
        """
        pass