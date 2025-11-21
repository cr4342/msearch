"""
搜索引擎 - 执行多模态向量搜索，管理查询处理和结果聚合
"""
import numpy as np
from typing import Dict, Any, List, Union
import logging
import uuid
import asyncio

logger = logging.getLogger(__name__)


class SearchEngine:
    """搜索引擎"""
    
    def __init__(self, config: Dict[str, Any], vector_store, embedding_engine):
        """
        初始化搜索引擎
        
        Args:
            config: 配置字典
            vector_store: 向量存储实例
            embedding_engine: 嵌入引擎实例
        """
        self.config = config
        self.vector_store = vector_store
        self.embedding_engine = embedding_engine
        self.top_k = config.get('search.top_k', 50)
        self.similarity_threshold = config.get('search.similarity_threshold', 0.5)
    
    async def search_by_vector(self, query_vector: np.ndarray, 
                              collection_name: str,
                              top_k: int = None) -> List[Dict[str, Any]]:
        """
        基于向量的搜索
        
        Args:
            query_vector: 查询向量
            collection_name: 集合名称
            top_k: 返回结果数量
            
        Returns:
            搜索结果列表
        """
        try:
            if top_k is None:
                top_k = self.top_k
            
            logger.debug(f"执行向量搜索: 集合={collection_name}, top_k={top_k}")
            
            # 将numpy数组转换为列表
            if isinstance(query_vector, np.ndarray):
                query_vector = query_vector.tolist()
            
            # 调用向量存储进行搜索
            results = await self.vector_store.search(
                collection_name, query_vector, top_k
            )
            
            # 过滤低相似度结果
            filtered_results = [
                result for result in results 
                if result.get('score', 0) >= self.similarity_threshold
            ]
            
            logger.debug(f"向量搜索完成: 找到{len(filtered_results)}个匹配结果")
            
            return filtered_results
            
        except Exception as e:
            logger.error(f"向量搜索失败: {e}")
            return []
    
    async def multimodal_search(self, query_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        多模态搜索
        
        Args:
            query_data: 查询数据字典，包含不同类型的内容
            
        Returns:
            搜索结果
        """
        try:
            logger.info(f"执行多模态搜索: 查询类型={list(query_data.keys())}")
            
            # 存储各模态的搜索结果
            modality_results = {}
            
            # 处理文本查询
            if 'text' in query_data:
                text_results = await self._search_text(query_data['text'])
                modality_results['text'] = text_results
            
            # 处理图片查询
            if 'image' in query_data:
                image_results = await self._search_image(query_data['image'])
                modality_results['image'] = image_results
            
            # 处理音频查询
            if 'audio' in query_data:
                audio_results = await self._search_audio(query_data['audio'])
                modality_results['audio'] = audio_results
            
            # 融合多模态结果
            fused_results = self._fuse_results(modality_results)
            
            logger.info(f"多模态搜索完成: 总结果数={len(fused_results)}")
            
            return {
                'status': 'success',
                'query_id': str(uuid.uuid4()),
                'results': fused_results,
                'modality_results': modality_results
            }
            
        except Exception as e:
            logger.error(f"多模态搜索失败: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'query_id': str(uuid.uuid4())
            }
    
    async def _search_text(self, text: str) -> List[Dict[str, Any]]:
        """
        文本搜索
        
        Args:
            text: 查询文本
            
        Returns:
            搜索结果
        """
        try:
            logger.debug(f"执行文本搜索: {text}")
            
            # 使用嵌入引擎将文本转换为向量
            query_vector = await self.embedding_engine.embed_content(text, 'text')
            
            # 执行向量搜索
            results = await self.search_by_vector(query_vector, 'text_collection')
            
            logger.debug(f"文本搜索完成: 找到{len(results)}个结果")
            return results
            
        except Exception as e:
            logger.error(f"文本搜索失败: {e}")
            return []
    
    async def _search_image(self, image_data: np.ndarray) -> List[Dict[str, Any]]:
        """
        图片搜索
        
        Args:
            image_data: 图片数据
            
        Returns:
            搜索结果
        """
        try:
            logger.debug("执行图片搜索")
            
            # 使用嵌入引擎将图片转换为向量
            query_vector = await self.embedding_engine.embed_content(image_data, 'image')
            
            # 执行向量搜索
            results = await self.search_by_vector(query_vector, 'image_collection')
            
            logger.debug(f"图片搜索完成: 找到{len(results)}个结果")
            return results
            
        except Exception as e:
            logger.error(f"图片搜索失败: {e}")
            return []
    
    async def _search_audio(self, audio_data: np.ndarray) -> List[Dict[str, Any]]:
        """
        音频搜索
        
        Args:
            audio_data: 音频数据
            
        Returns:
            搜索结果
        """
        try:
            logger.debug("执行音频搜索")
            
            # 使用嵌入引擎将音频转换为向量
            # 根据音频类型选择适当的模型
            audio_type = 'audio_music'  # 默认使用音乐模型
            if hasattr(audio_data, 'sample_rate') and audio_data.sample_rate < 16000:
                audio_type = 'audio_speech'  # 低采样率更适合语音
                
            query_vector = await self.embedding_engine.embed_content(audio_data, audio_type)
            
            # 执行向量搜索
            results = await self.search_by_vector(query_vector, 'audio_collection')
            
            logger.debug(f"音频搜索完成: 找到{len(results)}个结果")
            return results
            
        except Exception as e:
            logger.error(f"音频搜索失败: {e}")
            return []
    
    def _fuse_results(self, modality_results: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        融合多模态结果
        
        Args:
            modality_results: 各模态的搜索结果
            
        Returns:
            融合后的结果
        """
        # 简单的融合策略：合并所有结果并按文件ID分组
        # 实际实现中应该使用更复杂的融合算法
        
        # 收集所有结果
        all_results = []
        for modality, results in modality_results.items():
            for result in results:
                result_copy = result.copy()
                result_copy['modality'] = modality
                all_results.append(result_copy)
        
        # 按文件ID分组
        file_groups = {}
        for result in all_results:
            file_id = result.get('file_id', 'unknown')
            if file_id not in file_groups:
                file_groups[file_id] = []
            file_groups[file_id].append(result)
        
        # 为每个文件组计算综合得分
        fused_results = []
        for file_id, results in file_groups.items():
            # 简单平均得分
            avg_score = np.mean([r.get('score', 0) for r in results])
            
            # 使用第一个结果作为基础信息
            base_result = results[0].copy()
            base_result['score'] = float(avg_score)
            base_result['modalities'] = [r['modality'] for r in results]
            base_result['modality_count'] = len(results)
            
            fused_results.append(base_result)
        
        # 按得分排序
        fused_results.sort(key=lambda x: x['score'], reverse=True)
        
        logger.debug(f"结果融合完成: 原始{len(all_results)}个结果 -> 融合后{len(fused_results)}个结果")
        return fused_results
    
    async def search_by_time_range(self, file_id: str, start_time: float, 
                                  end_time: float) -> List[Dict[str, Any]]:
        """
        按时间范围搜索
        
        Args:
            file_id: 文件ID
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            时间范围内的结果
        """
        try:
            logger.debug(f"执行时间范围搜索: 文件={file_id}, 时间范围={start_time}-{end_time}")
            
            # 调用向量存储按时间范围查询
            results = await self.vector_store.search_by_time_range(
                file_id, start_time, end_time
            )
            
            logger.debug(f"时间范围搜索完成: 找到{len(results)}个结果")
            return results
            
        except Exception as e:
            logger.error(f"时间范围搜索失败: {e}")
            return []


# 示例使用
if __name__ == "__main__":
    import asyncio
    
    # 配置示例
    config = {
        'search.top_k': 50,
        'search.similarity_threshold': 0.5
    }
    
    # 创建搜索引擎实例(需要实际的向量存储实例)
    # engine = SearchEngine(config, vector_store)
    
    # 执行搜索(需要实际的查询数据)
    # results = asyncio.run(engine.multimodal_search({'text': '测试查询'}))
    # print(results)