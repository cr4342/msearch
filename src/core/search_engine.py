import os
import sys
import logging
import time
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

from src.core.config import ConfigManager
from src.core.embedding_engine import EmbeddingEngine
from src.core.vector_store import VectorStore

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SearchEngine:
    """
    搜索引擎
    
    负责处理多模态向量检索
    """
    
    def __init__(self, config: Dict[str, Any], embedding_engine: EmbeddingEngine, vector_store: VectorStore):
        """
        初始化搜索引擎
        
        Args:
            config: 配置字典
            embedding_engine: 向量化引擎
            vector_store: 向量存储
        """
        self.config = config
        self.embedding_engine = embedding_engine
        self.vector_store = vector_store
        
        logger.info("SearchEngine initialized")
    
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
    
    def search(self, query: str, k: int = 10, modalities: Optional[List[str]] = None, 
              filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        执行搜索
        
        Args:
            query: 查询文本
            k: 返回结果数量
            modalities: 模态类型列表
            filters: 过滤条件
        
        Returns:
            搜索结果
        """
        try:
            logger.info(f"Searching with query: {query}, k: {k}, modalities: {modalities}")
            
            # 1. 文本向量化
            query_vector = self.embedding_engine.embed_text(query)
            
            # 2. 向量搜索
            search_results = self.vector_store.search_vectors(query_vector, k=k, modalities=modalities)
            
            # 3. 结果排序和过滤
            ranked_results = self._rank_results(search_results)
            
            # 4. 结果聚合
            aggregated_results = self._aggregate_results(ranked_results)
            
            # 5. 结果格式化
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
                'query': query
            }
    
    def image_search(self, image_path: str, k: int = 10, modalities: Optional[List[str]] = None, 
                    filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        图像搜索
        
        Args:
            image_path: 图像文件路径
            k: 返回结果数量
            modalities: 模态类型列表
            filters: 过滤条件
        
        Returns:
            搜索结果
        """
        try:
            logger.info(f"Image searching with image: {image_path}, k: {k}, modalities: {modalities}")
            
            # 1. 图像向量化
            query_vector = self.embedding_engine.embed_image_from_path(image_path)
            
            # 2. 向量搜索
            search_results = self.vector_store.search_vectors(query_vector, k=k, modalities=modalities)
            
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
            logger.error(f"Failed to image search: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'image_path': image_path
            }
    
    def _rank_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        对搜索结果进行排序
        
        Args:
            results: 搜索结果列表
        
        Returns:
            排序后的结果
        """
        # 根据相似度分数排序（相似度越高，_distance值越小）
        sorted_results = sorted(results, key=lambda x: x['similarity'])
        return sorted_results
    
    def _aggregate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        聚合搜索结果
        
        Args:
            results: 搜索结果列表
        
        Returns:
            聚合后的结果
        """
        # 简化实现：直接返回结果
        return results
    
    def _format_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        格式化搜索结果
        
        Args:
            results: 搜索结果列表
        
        Returns:
            格式化后的结果
        """
        formatted_results = []
        
        for result in results:
            formatted_results.append({
                'id': result['id'],
                'modality': result['modality'],
                'file_id': result['file_id'],
                'segment_id': result['segment_id'],
                'start_time': result['start_time'],
                'end_time': result['end_time'],
                'similarity': 1.0 - result['similarity'],  # 转换为相似度分数（0-1）
                'metadata': result['metadata']
            })
        
        return formatted_results
    
    def get_top_k_results(self, results: List[Dict[str, Any]], k: int = 10) -> List[Dict[str, Any]]:
        """
        获取前k个结果
        
        Args:
            results: 搜索结果列表
            k: 返回结果数量
        
        Returns:
            前k个结果
        """
        return results[:k]
    
    def deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        去重搜索结果
        
        Args:
            results: 搜索结果列表
        
        Returns:
            去重后的结果
        """
        seen = set()
        unique_results = []
        
        for result in results:
            result_key = f"{result['file_id']}_{result['segment_id']}"
            if result_key not in seen:
                seen.add(result_key)
                unique_results.append(result)
        
        return unique_results
    
    def filter_results_by_modality(self, results: List[Dict[str, Any]], modalities: List[str]) -> List[Dict[str, Any]]:
        """
        按模态过滤结果
        
        Args:
            results: 搜索结果列表
            modalities: 模态类型列表
        
        Returns:
            过滤后的结果
        """
        return [result for result in results if result['modality'] in modalities]
    
    def get_search_stats(self) -> Dict[str, Any]:
        """
        获取搜索统计信息
        
        Returns:
            统计信息
        """
        try:
            return {
                'vector_count': self.vector_store.get_vector_count(),
                'dimension': self.vector_store.vector_dimension,
                'has_lancedb': hasattr(self.vector_store, 'db')
            }
        except Exception as e:
            logger.error(f"Failed to get search stats: {e}")
            return {}
    
    def close(self) -> None:
        """
        关闭搜索引擎
        """
        try:
            logger.info("SearchEngine closed")
        except Exception as e:
            logger.error(f"Failed to close SearchEngine: {e}")


# 初始化函数
def create_search_engine(config: Dict[str, Any], embedding_engine: EmbeddingEngine, vector_store: VectorStore) -> SearchEngine:
    """
    创建搜索引擎实例
    
    Args:
        config: 配置字典
        embedding_engine: 向量化引擎
        vector_store: 向量存储
    
    Returns:
        SearchEngine实例
    """
    search_engine = SearchEngine(config, embedding_engine, vector_store)
    if not search_engine.initialize():
        logger.error("Failed to create SearchEngine")
        raise RuntimeError("Failed to create SearchEngine")
    
    return search_engine
