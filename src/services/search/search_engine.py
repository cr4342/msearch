"""
搜索引擎 - 使用依赖注入
负责处理多模态向量检索
"""

import os
import sys
import logging
import time
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from abc import ABC, abstractmethod
from pathlib import Path

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmbeddingEngine(ABC):
    """向量化引擎接口"""
    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        pass
    
    @abstractmethod
    def embed_image(self, image_path: str) -> List[float]:
        pass
    
    @abstractmethod
    def embed_audio(self, audio_path: str) -> List[float]:
        pass
    
    @abstractmethod
    def embed_video_segment(self, video_path: str, start_time: float = 0.0, end_time: Optional[float] = None, aggregation: str = 'mean') -> List[float]:
        pass


class VectorStore(ABC):
    """向量存储接口"""
    @abstractmethod
    def search_vectors(self, query_vector: List[float], k: int = 10, modalities: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    def get_collection_stats(self) -> Dict[str, Any]:
        pass


class SearchEngine:
    """
    搜索引擎 - 使用依赖注入
    
    负责处理多模态向量检索
    """
    
    def __init__(self, embedding_engine: EmbeddingEngine, vector_store: VectorStore):
        """
        初始化搜索引擎（使用依赖注入）
        
        Args:
            embedding_engine: 向量化引擎
            vector_store: 向量存储
        """
        self.embedding_engine = embedding_engine
        self.vector_store = vector_store
        
        logger.info("SearchEngine initialized (with dependency injection)")
    
    def initialize(self) -> bool:
        """
        初始化搜索引擎
        
        Returns:
            是否初始化成功
        """
        try:
            logger.info("SearchEngine initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize SearchEngine: {e}")
            return False
    
    async def search(self, query: str, k: int = 10, modalities: Optional[List[str]] = None, 
              filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        执行文本搜索
        
        Args:
            query: 查询文本
            k: 返回结果数量
            modalities: 模态类型列表
            filters: 过滤条件
            
        Returns:
            搜索结果
        """
        try:
            start_time = time.time()
            logger.info(f"Searching with query: {query}, k: {k}, modalities: {modalities}")
            
            # 1. 文本向量化
            query_vector = await self.embedding_engine.embed_text(query)
            
            # 2. 构建过滤条件
            search_filters = {}
            if modalities:
                search_filters['modality'] = modalities
            if filters:
                search_filters.update(filters)
            
            # 3. 向量搜索
            search_results = self.vector_store.search(
                query_vector, 
                limit=k, 
                filter=search_filters if search_filters else None
            )
            
            # 4. 结果排序和过滤
            ranked_results = self._rank_results(search_results)
            
            # 5. 结果聚合
            aggregated_results = self._aggregate_results(ranked_results)
            
            # 6. 结果格式化
            formatted_results = self._format_results(aggregated_results)
            
            return {
                'status': 'success',
                'query': query,
                'results': formatted_results,
                'total': len(formatted_results),
                'search_time': time.time() - start_time,
                'modalities': modalities,
                'k': k
            }
        except Exception as e:
            logger.error(f"Failed to search: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'query': query,
                'results': [],
                'total': 0
            }
    
    async def image_search(self, image_path: str, k: int = 10, modalities: Optional[List[str]] = None, 
                   filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        执行图像搜索
        
        Args:
            image_path: 图像文件路径
            k: 返回结果数量
            modalities: 模态类型列表
            filters: 过滤条件
        
        Returns:
            搜索结果
        """
        try:
            start_time = time.time()
            logger.info(f"Searching with image: {image_path}, k: {k}, modalities: {modalities}")
            
            # 1. 图像向量化
            query_vector = await self.embedding_engine.embed_image(image_path)
            
            # 2. 向量搜索
            search_results = self.vector_store.search(query_vector, limit=k)
            
            # 3. 结果排序和过滤
            ranked_results = self._rank_results(search_results)
            
            # 4. 结果聚合
            aggregated_results = self._aggregate_results(ranked_results)
            
            # 5. 结果格式化
            formatted_results = self._format_results(aggregated_results)
            
            return {
                'status': 'success',
                'image_path': image_path,
                'results': formatted_results,
                'total': len(formatted_results),
                'search_time': time.time() - start_time,
                'modalities': modalities,
                'k': k
            }
        except Exception as e:
            logger.error(f"Failed to search image: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'image_path': image_path,
                'results': [],
                'total': 0
            }
    
    async def audio_search(self, audio_path: str, k: int = 10, modalities: Optional[List[str]] = None, 
                   filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        执行音频搜索
        
        Args:
            audio_path: 音频文件路径
            k: 返回结果数量
            modalities: 模态类型列表
            filters: 过滤条件
        
        Returns:
            搜索结果
        """
        try:
            start_time = time.time()
            logger.info(f"Searching with audio: {audio_path}, k: {k}, modalities: {modalities}")
            
            # 1. 音频向量化
            query_vector = await self.embedding_engine.embed_audio(audio_path)
            
            # 2. 向量搜索
            search_results = self.vector_store.search(query_vector, limit=k)
            
            # 3. 结果排序和过滤
            ranked_results = self._rank_results(search_results)
            
            # 4. 结果聚合
            aggregated_results = self._aggregate_results(ranked_results)
            
            # 5. 结果格式化
            formatted_results = self._format_results(aggregated_results)
            
            return {
                'status': 'success',
                'audio_path': audio_path,
                'results': formatted_results,
                'total': len(formatted_results),
                'search_time': time.time() - start_time,
                'modalities': modalities,
                'k': k
            }
        except Exception as e:
            logger.error(f"Failed to search audio: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'audio_path': audio_path,
                'results': [],
                'total': 0
            }
    
    def _rank_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        结果排序
        
        Args:
            results: 原始结果
        
        Returns:
            排序后的结果
        """
        # 按相似度分数排序
        return sorted(results, key=lambda x: x.get('score', 0), reverse=True)
    
    def _aggregate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        结果聚合
        
        Args:
            results: 排序后的结果
        
        Returns:
            聚合后的结果
        """
        # 按文件ID聚合，避免重复
        aggregated = {}
        for result in results:
            file_id = result.get('file_id')
            if file_id not in aggregated:
                aggregated[file_id] = result
            else:
                # 如果已存在，保留相似度更高的结果
                if result.get('score', 0) > aggregated[file_id].get('score', 0):
                    aggregated[file_id] = result
        
        return list(aggregated.values())
    
    def _format_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        结果格式化
        
        Args:
            results: 聚合后的结果
        
        Returns:
            格式化后的结果
        """
        formatted = []
        for result in results:
            # 从数据库获取缩略图路径
            thumbnail_path = None
            preview_path = None
            
            file_path = result.get('file_path')
            if file_path:
                try:
                    # 尝试从数据库获取缩略图路径
                    if hasattr(self, 'database_manager') and self.database_manager:
                        thumbnail_path = self.database_manager.get_thumbnail_by_path(file_path)
                        preview_path = self.database_manager.get_preview_by_path(file_path)
                except Exception as e:
                    logger.warning(f"获取缩略图路径失败: {e}")
            
            # 从modality推断file_type
            file_type = result.get('file_type')
            if not file_type:
                modality = result.get('modality', 'unknown')
                file_type_map = {
                    'image': 'image',
                    'video': 'video',
                    'audio': 'audio',
                    'text': 'text'
                }
                file_type = file_type_map.get(modality, 'unknown')
            
            formatted.append({
                'file_id': result.get('file_id'),
                'file_path': result.get('file_path'),
                'file_name': result.get('file_name'),
                'file_type': file_type,
                'modality': result.get('modality'),
                'score': result.get('score', 0),
                'thumbnail_path': thumbnail_path,
                'preview_path': preview_path,
                'metadata': result.get('metadata', {}),
                'timestamp_info': result.get('timestamp_info', {})
            })
        
        return formatted


def create_search_engine(embedding_engine: EmbeddingEngine, vector_store: VectorStore) -> SearchEngine:
    """
    创建SearchEngine实例（工厂函数）
    
    Args:
        embedding_engine: 向量化引擎
        vector_store: 向量存储
    
    Returns:
        SearchEngine实例
    """
    return SearchEngine(embedding_engine, vector_store)