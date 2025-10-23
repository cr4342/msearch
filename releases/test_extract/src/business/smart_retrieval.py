"""
智能检索引擎 - 融合多模态向量搜索结果，提供统一的排序和重排机制
"""
import re
from typing import Dict, Any, List
import logging
from src.business.search_engine import SearchEngine
from src.business.multimodal_fusion_engine import MultiModalFusionEngine
from src.business.face_manager import FaceManager
from src.storage.face_database import FaceDatabase

logger = logging.getLogger(__name__)


class SmartRetrievalEngine:
    """智能检索引擎"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化智能检索引擎
        
        Args:
            config: 配置字典
        """
        self.config = config
        
        # 初始化组件
        # 注意：这里需要传入实际的vector_store和embedding_engine实例，暂时用None占位
        self.search_engine = SearchEngine(config, None, None)
        self.fusion_engine = MultiModalFusionEngine(config)
        
        # FaceDatabase需要数据库路径，从配置中获取
        db_path = config.get('database', {}).get('sqlite', {}).get('path', './data/db/msearch.db')
        self.face_database = FaceDatabase(db_path)
        self.face_manager = FaceManager(config, self.face_database, None)
        
        # 从配置加载关键词
        self.audio_keywords = config.get('retrieval.audio_keywords', [
            '音乐', '歌曲', '旋律', '节奏', '节拍', '乐器', '演奏', '演唱',
            'audio', 'music', 'song', 'melody', 'rhythm', 'instrument'
        ])
        
        self.visual_keywords = config.get('retrieval.visual_keywords', [
            '图片', '照片', '图像', '画面', '视觉', '颜色', '场景',
            'image', 'photo', 'picture', 'visual', 'color', 'scene'
        ])
        
        logger.info("智能检索引擎初始化完成")
    
    async def search(self, query: str, search_type: str = "smart") -> Dict[str, Any]:
        """
        智能搜索
        
        Args:
            query: 查询字符串
            search_type: 搜索类型
            
        Returns:
            搜索结果字典
        """
        try:
            logger.info(f"执行智能搜索: 查询='{query}', 类型={search_type}")
            
            # 1. 识别查询类型
            query_type = self._identify_query_type(query)
            logger.debug(f"查询类型识别: {query_type}")
            
            # 2. 根据查询类型执行相应的搜索策略
            if query_type == "person":
                results = await self._person_search(query)
            elif query_type == "audio":
                results = await self._audio_search(query)
            elif query_type == "visual":
                results = await self._visual_search(query)
            else:
                results = await self._generic_search(query)
            
            logger.info(f"智能搜索完成: 查询='{query}', 找到{len(results.get('results', []))}个结果")
            
            return results
            
        except Exception as e:
            logger.error(f"智能搜索失败: 查询='{query}', 错误={e}")
            return {
                'status': 'error',
                'error': str(e),
                'query': query
            }
    
    def _identify_query_type(self, query: str) -> str:
        """
        识别查询类型
        
        Args:
            query: 查询字符串
            
        Returns:
            查询类型 ("person", "audio", "visual", "generic")
        """
        # 检查是否包含人名（从数据库中获取）
        # 这里简化处理，实际应该查询数据库中的所有人名
        person_names = self._get_person_names()
        for name in person_names:
            if name in query:
                return "person"
        
        # 检查是否包含音频相关关键词
        for keyword in self.audio_keywords:
            if keyword in query:
                return "audio"
        
        # 检查是否包含视觉相关关键词
        for keyword in self.visual_keywords:
            if keyword in query:
                return "visual"
        
        # 默认通用查询
        return "generic"
    
    def _get_person_names(self) -> List[str]:
        """
        获取所有人名列表
        
        Returns:
            人名列表
        """
        try:
            # 从人脸数据库获取所有人名
            persons = self.face_database.get_all_persons()
            names = []
            for person in persons:
                names.append(person['name'])
                # 添加别名
                if person.get('aliases'):
                    names.extend(person['aliases'])
            return names
        except Exception as e:
            logger.warning(f"获取人名列表失败: {e}")
            return []
    
    async def _person_search(self, query: str) -> Dict[str, Any]:
        """
        人名搜索（人脸预检索）
        
        Args:
            query: 查询字符串
            
        Returns:
            搜索结果
        """
        try:
            logger.debug(f"执行人名搜索: {query}")
            
            # 1. 识别人名
            person_name = self._extract_person_name(query)
            if not person_name:
                return await self._generic_search(query)
            
            # 2. 人脸预检索生成文件白名单
            face_search_result = await self.face_manager.search_by_person_name(person_name)
            if face_search_result['status'] != 'success' or not face_search_result.get('files'):
                # 如果没有人脸搜索结果，回退到通用搜索
                return await self._generic_search(query)
            
            # 3. 获取白名单文件ID
            whitelist_file_ids = [f['file_id'] for f in face_search_result['files']]
            
            # 4. 在白名单内进行多模态检索
            # 这里简化处理，实际应该调用搜索引擎在指定文件范围内搜索
            # 暂时返回人脸搜索结果
            return {
                'status': 'success',
                'query': query,
                'query_type': 'person',
                'results': face_search_result['files'],
                'whitelist_used': True,
                'whitelist_size': len(whitelist_file_ids)
            }
            
        except Exception as e:
            logger.error(f"人名搜索失败: {query}, 错误={e}")
            return await self._generic_search(query)
    
    def _extract_person_name(self, query: str) -> str:
        """
        从查询中提取人名
        
        Args:
            query: 查询字符串
            
        Returns:
            人名或None
        """
        person_names = self._get_person_names()
        for name in person_names:
            if name in query:
                return name
        return None
    
    async def _audio_search(self, query: str) -> Dict[str, Any]:
        """
        音频搜索（提升音频权重）
        
        Args:
            query: 查询字符串
            
        Returns:
            搜索结果
        """
        try:
            logger.debug(f"执行音频搜索: {query}")
            
            # 1. 执行多模态搜索
            search_data = {'text': query}
            search_result = await self.search_engine.multimodal_search(search_data)
            
            if search_result['status'] != 'success':
                return search_result
            
            # 2. 动态调整权重（提升音频相关权重）
            # 这里简化处理，实际应该在融合引擎中调整权重
            weights = {
                'text': 0.3,
                'image': 0.2,
                'audio_music': 0.3,
                'audio_speech': 0.2
            }
            
            # 3. 融合结果
            fused_results = self.fusion_engine.fuse_results(
                search_result['modality_results'], 
                weights
            )
            
            return {
                'status': 'success',
                'query': query,
                'query_type': 'audio',
                'results': fused_results,
                'weights_used': weights
            }
            
        except Exception as e:
            logger.error(f"音频搜索失败: {query}, 错误={e}")
            return await self._generic_search(query)
    
    async def _visual_search(self, query: str) -> Dict[str, Any]:
        """
        视觉搜索（提升视觉权重）
        
        Args:
            query: 查询字符串
            
        Returns:
            搜索结果
        """
        try:
            logger.debug(f"执行视觉搜索: {query}")
            
            # 1. 执行多模态搜索
            search_data = {'text': query}
            search_result = await self.search_engine.multimodal_search(search_data)
            
            if search_result['status'] != 'success':
                return search_result
            
            # 2. 动态调整权重（提升视觉相关权重）
            # 这里简化处理，实际应该在融合引擎中调整权重
            weights = {
                'text': 0.2,
                'image': 0.5,
                'audio_music': 0.15,
                'audio_speech': 0.15
            }
            
            # 3. 融合结果
            fused_results = self.fusion_engine.fuse_results(
                search_result['modality_results'], 
                weights
            )
            
            return {
                'status': 'success',
                'query': query,
                'query_type': 'visual',
                'results': fused_results,
                'weights_used': weights
            }
            
        except Exception as e:
            logger.error(f"视觉搜索失败: {query}, 错误={e}")
            return await self._generic_search(query)
    
    async def _generic_search(self, query: str) -> Dict[str, Any]:
        """
        通用搜索（默认权重分配）
        
        Args:
            query: 查询字符串
            
        Returns:
            搜索结果
        """
        try:
            logger.debug(f"执行通用搜索: {query}")
            
            # 1. 执行多模态搜索
            search_data = {'text': query}
            search_result = await self.search_engine.multimodal_search(search_data)
            
            if search_result['status'] != 'success':
                return search_result
            
            # 2. 使用默认权重
            weights = {
                'text': 0.25,
                'image': 0.25,
                'audio_music': 0.25,
                'audio_speech': 0.25
            }
            
            # 3. 融合结果
            fused_results = self.fusion_engine.fuse_results(
                search_result['modality_results'], 
                weights
            )
            
            # 4. 如果结果包含时间戳信息，进行时间戳处理
            if fused_results:
                processed_results = await self._process_timestamps(fused_results, query)
            else:
                processed_results = fused_results
            
            return {
                'status': 'success',
                'query': query,
                'query_type': 'generic',
                'results': processed_results,
                'raw_results': fused_results,  # 保留原始结果
                'weights_used': weights
            }
            
        except Exception as e:
            logger.error(f"通用搜索失败: {query}, 错误={e}")
            return {
                'status': 'error',
                'error': str(e),
                'query': query
            }
    
    async def _process_timestamps(self, results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """
        处理时间戳信息，提供精确的时间定位
        
        Args:
            results: 搜索结果列表
            query: 查询字符串
            
        Returns:
            处理后的时间戳结果
        """
        try:
            # 导入时间定位引擎
            from src.business.temporal_localization_engine import get_temporal_engine
            temporal_engine = get_temporal_engine()
            
            processed_results = []
            
            # 按文件分组处理结果
            file_groups = {}
            for result in results:
                file_id = result.get('file_id', 'unknown')
                if file_id not in file_groups:
                    file_groups[file_id] = []
                file_groups[file_id].append(result)
            
            # 为每个文件处理时间戳
            for file_id, file_results in file_groups.items():
                # 提取各模态的时间戳信息
                visual_matches = []
                audio_matches = []
                speech_matches = []
                
                for result in file_results:
                    payload = result.get('payload', {})
                    modality = result.get('modality', '')
                    score = result.get('score', 0)
                    
                    # 提取时间戳信息
                    start_time = payload.get('start_time', 0)
                    end_time = payload.get('end_time', 0)
                    timestamp = (start_time + end_time) / 2  # 使用中间时间点
                    
                    # 根据模态类型分类
                    if modality == 'image' or modality == 'visual':
                        visual_matches.append({
                            'timestamp': timestamp,
                            'similarity': score,
                            'modality': 'visual'
                        })
                    elif modality == 'audio_music':
                        audio_matches.append({
                            'timestamp': timestamp,
                            'similarity': score,
                            'modality': 'audio'
                        })
                    elif modality == 'audio_speech':
                        speech_matches.append({
                            'timestamp': timestamp,
                            'similarity': score,
                            'modality': 'speech'
                        })
                
                # 使用时间定位引擎融合多模态时间戳
                if visual_matches or audio_matches or speech_matches:
                    fused_timestamps = await temporal_engine.fuse_temporal_results(
                        visual_matches, audio_matches, speech_matches
                    )
                    
                    # 为每个结果添加融合后的时间戳信息
                    for result in file_results:
                        # 添加最佳匹配时间戳
                        if fused_timestamps:
                            best_timestamp = fused_timestamps[0]
                            result['best_timestamp'] = {
                                'timestamp': best_timestamp.timestamp,
                                'confidence': best_timestamp.confidence,
                                'total_score': best_timestamp.total_score
                            }
                            # 添加所有时间戳信息
                            result['all_timestamps'] = [
                                {
                                    'timestamp': ts.timestamp,
                                    'confidence': ts.confidence,
                                    'total_score': ts.total_score,
                                    'visual_score': ts.visual_score,
                                    'audio_score': ts.audio_score,
                                    'speech_score': ts.speech_score
                                }
                                for ts in fused_timestamps
                            ]
                        processed_results.append(result)
                else:
                    # 没有时间戳信息，直接添加结果
                    for result in file_results:
                        processed_results.append(result)
            
            # 按时间戳置信度排序
            processed_results.sort(
                key=lambda x: x.get('best_timestamp', {}).get('confidence', 0), 
                reverse=True
            )
            
            logger.debug(f"时间戳处理完成: 处理了{len(processed_results)}个结果")
            return processed_results
            
        except Exception as e:
            logger.error(f"时间戳处理失败: {e}")
            # 如果时间戳处理失败，返回原始结果
            return results


# 示例使用
if __name__ == "__main__":
    import asyncio
    
    # 配置示例
    config = {
        'retrieval': {
            'audio_keywords': [
                '音乐', '歌曲', '旋律', '节奏', '节拍', '乐器', '演奏', '演唱',
                'audio', 'music', 'song', 'melody', 'rhythm', 'instrument'
            ],
            'visual_keywords': [
                '图片', '照片', '图像', '画面', '视觉', '颜色', '场景',
                'image', 'photo', 'picture', 'visual', 'color', 'scene'
            ]
        }
    }
    
    # 创建引擎实例
    # engine = SmartRetrievalEngine(config)
    
    # 执行搜索
    # result = asyncio.run(engine.search("包含张三的会议照片"))
    # print(result)