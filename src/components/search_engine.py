"""
检索引擎
实现多模态检索功能
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional

from src.core.config_manager import ConfigManager
from src.components.database_manager import DatabaseManager
from src.core.vector_store import VectorStore
from src.core.embedding_engine import EmbeddingEngine


class SearchEngine:
    """检索引擎 - 实现多模态检索功能"""
    
    def __init__(self, config_manager: ConfigManager, 
                 database_manager: DatabaseManager,
                 vector_store: VectorStore,
                 embedding_engine: EmbeddingEngine):
        self.config_manager = config_manager
        self.database_manager = database_manager
        self.vector_store = vector_store
        self.embedding_engine = embedding_engine
        
        self.logger = logging.getLogger(__name__)
        
        # 默认检索限制
        self.default_limit = 10
        self.default_threshold = 0.7
        
        # 运行状态
        self.is_running = False
        
        self.logger.info("检索引擎初始化完成")
    
    async def start(self):
        """启动检索引擎"""
        self.logger.info("启动检索引擎")
        self.is_running = True
        self.logger.info("检索引擎启动完成")
    
    async def stop(self):
        """停止检索引擎"""
        self.logger.info("停止检索引擎")
        self.is_running = False
        self.logger.info("检索引擎已停止")
    
    async def search_by_text(self, query: str, limit: int = None) -> List[Dict[str, Any]]:
        """文本检索"""
        if limit is None:
            limit = self.default_limit
        
        self.logger.debug(f"文本检索: {query[:50]}..., 限制: {limit}")
        
        try:
            # 1. 向量化查询文本
            query_vector = await self.embedding_engine.embed_text_for_visual(query)
            
            # 2. 确定要搜索的集合
            collections = ['image_vectors', 'video_vectors', 'text_vectors']
            
            # 3. 在所有相关集合中搜索
            all_results = []
            for collection in collections:
                if await self.vector_store.has_collection(collection):
                    results = await self.vector_store.search_vectors(
                        collection=collection,
                        query_vector=query_vector,
                        limit=limit
                    )
                    all_results.extend(results)
            
            # 4. 合并和排序结果
            all_results.sort(key=lambda x: x['distance'], reverse=True)
            
            # 5. 丰富结果数据
            enriched_results = await self._enrich_results(all_results)
            
            self.logger.info(f"文本检索完成，找到 {len(enriched_results)} 个结果")
            return enriched_results[:limit]
            
        except Exception as e:
            self.logger.error(f"文本检索失败: {e}")
            return []
    
    async def search_by_image_from_path(self, image_path: str, limit: int = None) -> List[Dict[str, Any]]:
        """从文件路径进行图像检索"""
        if limit is None:
            limit = self.default_limit
        
        self.logger.debug(f"图像检索: {image_path}, 限制: {limit}")
        
        try:
            # 1. 向量化图像
            query_vector = await self.embedding_engine.embed_image_from_path(image_path)
            
            # 2. 搜索相似图像
            collections = ['image_vectors', 'video_vectors']  # 图像可检索视频帧
            all_results = []
            
            for collection in collections:
                if await self.vector_store.has_collection(collection):
                    results = await self.vector_store.search_vectors(
                        collection=collection,
                        query_vector=query_vector,
                        limit=limit
                    )
                    all_results.extend(results)
            
            # 3. 合并和排序结果
            all_results.sort(key=lambda x: x['distance'], reverse=True)
            
            # 4. 丰富结果数据
            enriched_results = await self._enrich_results(all_results)
            
            self.logger.info(f"图像检索完成，找到 {len(enriched_results)} 个结果")
            return enriched_results[:limit]
            
        except Exception as e:
            self.logger.error(f"图像检索失败: {e}")
            return []
    
    async def search_by_audio_from_path(self, audio_path: str, limit: int = None) -> List[Dict[str, Any]]:
        """从文件路径进行音频检索"""
        if limit is None:
            limit = self.default_limit
        
        self.logger.debug(f"音频检索: {audio_path}, 限制: {limit}")
        
        try:
            # 1. 判断音频类型并选择合适的向量化方法
            query_vector = await self.embedding_engine.embed_audio_from_path(audio_path)
            
            # 2. 确定搜索集合
            # 音频可检索音频、视频（音频轨道）和文本（转录内容）
            collections = ['audio_vectors', 'video_vectors', 'text_vectors']
            all_results = []
            
            for collection in collections:
                if await self.vector_store.has_collection(collection):
                    results = await self.vector_store.search_vectors(
                        collection=collection,
                        query_vector=query_vector,
                        limit=limit
                    )
                    all_results.extend(results)
            
            # 3. 合并和排序结果
            all_results.sort(key=lambda x: x['distance'], reverse=True)
            
            # 4. 丰富结果数据
            enriched_results = await self._enrich_results(all_results)
            
            self.logger.info(f"音频检索完成，找到 {len(enriched_results)} 个结果")
            return enriched_results[:limit]
            
        except Exception as e:
            self.logger.error(f"音频检索失败: {e}")
            return []
    
    async def hybrid_search(self, text_query: Optional[str] = None,
                           image_path: Optional[str] = None,
                           audio_path: Optional[str] = None,
                           limit: int = None) -> List[Dict[str, Any]]:
        """混合检索"""
        if limit is None:
            limit = self.default_limit
        
        self.logger.debug(f"混合检索 - 文本: {text_query is not None}, "
                         f"图像: {image_path is not None}, "
                         f"音频: {audio_path is not None}")
        
        try:
            all_query_vectors = []
            
            # 生成各种查询向量
            if text_query:
                text_vector = await self.embedding_engine.embed_text_for_visual(text_query)
                all_query_vectors.append(('text', text_vector))
            
            if image_path:
                image_vector = await self.embedding_engine.embed_image_from_path(image_path)
                all_query_vectors.append(('image', image_vector))
            
            if audio_path:
                audio_vector = await self.embedding_engine.embed_audio_from_path(audio_path)
                all_query_vectors.append(('audio', audio_vector))
            
            if not all_query_vectors:
                self.logger.warning("没有有效的查询输入")
                return []
            
            # 对每个查询向量执行搜索
            all_results = []
            for query_type, query_vector in all_query_vectors:
                collections = self._get_collections_for_query_type(query_type)
                
                for collection in collections:
                    if await self.vector_store.has_collection(collection):
                        results = await self.vector_store.search_vectors(
                            collection=collection,
                            query_vector=query_vector,
                            limit=limit
                        )
                        all_results.extend(results)
            
            # 合并重复结果（基于文件路径）
            merged_results = self._merge_duplicate_results(all_results)
            
            # 按相关性排序
            merged_results.sort(key=lambda x: x.get('avg_distance', 1.0))
            
            # 丰富结果数据
            enriched_results = await self._enrich_results(merged_results)
            
            self.logger.info(f"混合检索完成，找到 {len(enriched_results)} 个唯一结果")
            return enriched_results[:limit]
            
        except Exception as e:
            self.logger.error(f"混合检索失败: {e}")
            return []
    
    def _get_collections_for_query_type(self, query_type: str) -> List[str]:
        """获取与查询类型匹配的集合列表"""
        if query_type == 'text':
            return ['image_vectors', 'video_vectors', 'text_vectors', 'audio_vectors']
        elif query_type == 'image':
            return ['image_vectors', 'video_vectors']
        elif query_type == 'audio':
            return ['audio_vectors', 'video_vectors', 'text_vectors']
        else:
            return ['image_vectors', 'video_vectors', 'text_vectors', 'audio_vectors']
    
    def _merge_duplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """合并重复的检索结果"""
        unique_results = {}
        
        for result in results:
            file_path = result.get('file_path', '')
            
            if file_path in unique_results:
                # 如果已存在相同文件路径的结果，合并距离信息
                existing = unique_results[file_path]
                
                # 计算平均距离（相似度越高，距离值越小越好）
                if 'distances' not in existing:
                    existing['distances'] = [existing['distance']]
                
                existing['distances'].append(result['distance'])
                existing['avg_distance'] = sum(existing['distances']) / len(existing['distances'])
                existing['distance'] = min(existing['distances'])  # 使用最佳匹配距离
                existing['match_count'] = existing.get('match_count', 1) + 1
            else:
                result_copy = result.copy()
                result_copy['distances'] = [result_copy['distance']]
                result_copy['avg_distance'] = result_copy['distance']
                result_copy['match_count'] = 1
                unique_results[file_path] = result_copy
        
        # 返回按平均距离排序的结果
        sorted_results = sorted(
            unique_results.values(),
            key=lambda x: x['avg_distance']
        )
        
        return sorted_results
    
    async def _enrich_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """丰富检索结果，添加额外的元数据"""
        enriched_results = []
        
        for result in results:
            enriched_result = result.copy()
            
            # 从数据库获取额外的文件信息
            file_info = await self.database_manager.get_file_by_path(result.get('file_path', ''))
            if file_info:
                enriched_result['file_info'] = file_info
                enriched_result['file_size'] = file_info.get('file_size')
                enriched_result['created_at'] = file_info.get('created_at')
                enriched_result['file_metadata'] = file_info.get('metadata')
            
            # 如果是视频结果，获取视频切片信息
            if result.get('file_type') == 'video':
                video_segments = await self.database_manager.get_video_segments_by_file(file_info.get('id', '') if file_info else '')
                enriched_result['video_segments'] = video_segments
            
            # 如果包含人脸信息，获取人脸检测结果
            faces = await self.database_manager.get_faces_by_file(file_info.get('id', '') if file_info else '')
            if faces:
                enriched_result['faces'] = faces
            
            enriched_results.append(enriched_result)
        
        return enriched_results
    
    async def identify_query_type(self, query: str) -> str:
        """识别查询类型（人名、音乐、语音、视觉等）"""
        # 简单的关键词匹配
        music_keywords = ['音乐', '歌曲', 'MV', '音乐视频', '歌', '曲子', '旋律', '节拍']
        speech_keywords = ['讲话', '演讲', '会议', '访谈', '对话', '发言', '语音']
        visual_keywords = ['画面', '场景', '图像', '图片', '视频画面', '截图']
        
        query_lower = query.lower()
        
        # 检查是否为人名（简单规则：2-4个字符的中文）
        if len(query) >= 2 and len(query) <= 4 and all('\u4e00' <= char <= '\u9fff' for char in query):
            # 常见姓氏列表（简化版）
            common_surnames = ['张', '王', '李', '刘', '陈', '杨', '赵', '黄', '周', '吴',
                              '徐', '孙', '胡', '朱', '高', '林', '何', '郭', '马', '罗']
            if query[0] in common_surnames:
                return 'person'
        
        # 检查其他类型
        for keyword in music_keywords:
            if keyword in query_lower:
                return 'music'
        
        for keyword in speech_keywords:
            if keyword in query_lower:
                return 'speech'
        
        for keyword in visual_keywords:
            if keyword in query_lower:
                return 'visual'
        
        # 默认为通用查询
        return 'general'
    
    async def get_search_suggestions(self, partial_query: str) -> List[str]:
        """获取搜索建议"""
        # 简单实现：返回包含部分查询的热门搜索
        # 在实际应用中，这可能基于历史搜索记录或知识库
        suggestions = [
            f"{partial_query} 相关",
            f"{partial_query} 高清",
            f"{partial_query} 最新",
            f"热门 {partial_query}",
            f"推荐 {partial_query}"
        ]
        
        return suggestions[:5]  # 限制返回5个建议