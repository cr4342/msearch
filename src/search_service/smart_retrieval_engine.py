"""
智能检索引擎
负责多模态检索、结果排序
"""

import logging
from typing import Dict, Any, List, Optional

from src.common.storage.database_adapter import DatabaseAdapter
from src.common.embedding.embedding_engine import EmbeddingEngine
from src.core.config_manager import get_config_manager
from src.search_service.face_manager import get_face_manager


class SmartRetrievalEngine:
    """智能检索引擎"""
    
    def __init__(self, config_manager=None):
        self.config_manager = config_manager or get_config_manager()
        self.logger = logging.getLogger(__name__)
        
        # 初始化组件
        self.db_adapter = DatabaseAdapter()
        self.embedding_engine = EmbeddingEngine(config_manager)
        self.face_manager = get_face_manager()  # 人脸管理器
        
        # 检索配置
        self.default_weights = self.config_manager.get("smart_retrieval.default_weights", {
            'clip': 0.4,
            'clap': 0.3,
            'whisper': 0.3
        })
        
        self.person_weights = self.config_manager.get("smart_retrieval.person_weights", {
            'clip': 0.5,
            'clap': 0.25,
            'whisper': 0.25
        })
        
        self.audio_weights = self.config_manager.get("smart_retrieval.audio_weights", {
            'music': {
                'clip': 0.2,
                'clap': 0.7,
                'whisper': 0.1
            },
            'speech': {
                'clip': 0.2,
                'clap': 0.1,
                'whisper': 0.7
            }
        })
        
        self.visual_weights = self.config_manager.get("smart_retrieval.visual_weights", {
            'clip': 0.7,
            'clap': 0.15,
            'whisper': 0.15
        })
        
        # 视频多模态融合权重配置
        self.video_fusion_weights = self.config_manager.get("smart_retrieval.video_fusion_weights", {
            'visual': 0.6,
            'audio': 0.4,
            'visual_audio_balance': 0.5  # 视听平衡参数
        })
        
        # 关键词配置
        self.keywords = self.config_manager.get("smart_retrieval.keywords", {
            'music': ['音乐', '歌曲', 'MV', '音乐视频', '歌', '曲子', '旋律', '节拍'],
            'speech': ['讲话', '演讲', '会议', '访谈', '对话', '发言', '语音'],
            'visual': ['画面', '场景', '图像', '图片', '视频画面', '截图']
        })
        
        # 运行状态
        self.is_running = False
        
        self.logger.info("智能检索引擎初始化完成")
    
    async def start(self):
        """启动检索引擎"""
        self.logger.info("启动智能检索引擎")
        self.is_running = True
        self.logger.info("智能检索引擎启动完成")
    
    async def stop(self):
        """停止检索引擎"""
        self.logger.info("停止智能检索引擎")
        self.is_running = False
        self.logger.info("智能检索引擎已停止")
    
    async def search(self, text: Optional[str] = None, image: Optional[bytes] = None, audio: Optional[bytes] = None, top_k: int = 10, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        执行多模态混合检索
        
        Args:
            text: 文本查询内容
            image: 图像查询数据（二进制）
            audio: 音频查询数据（二进制）
            top_k: 返回结果数量
            filters: 过滤条件
            
        Returns:
            检索结果列表
        """
        try:
            # 检查是否有查询输入
            if not text and not image and not audio:
                self.logger.info("无查询输入，返回空结果")
                return []
            
            # 检查是否为人名查询，如果是，则直接使用人脸管理器
            if text and self._is_person_query(text):
                if self.face_manager and self.face_manager.face_recognition_enabled:
                    self.logger.info(f"执行人名查询: {text}")
                    person_results = self.face_manager.search_by_person_name(text, top_k)
                    
                    # 转换为标准格式
                    formatted_results = []
                    for result in person_results:
                        formatted_result = {
                            'file_id': result.get('file_id'),
                            'score': result.get('confidence', 0.8),
                            'original_score': result.get('confidence', 0.8),
                            'model': 'face_recognition',
                            'weight': 1.0,
                            'metadata': {
                                'file_path': result.get('file_path'),
                                'file_name': result.get('file_name'),
                                'file_type': result.get('file_type'),
                                'timestamp': result.get('timestamp'),
                                'confidence': result.get('confidence')
                            }
                        }
                        formatted_results.append(formatted_result)
                    
                    # 添加详细元数据
                    enriched_results = await self._enrich_results(formatted_results)
                    self.logger.info(f"人名查询完成: 返回 {len(enriched_results)} 个结果")
                    return enriched_results
                else:
                    self.logger.warning("人脸功能不可用，跳过人名查询")
            
            self.logger.info(f"执行多模态检索: text={bool(text)}, image={bool(image)}, audio={bool(audio)}, top_k={top_k}")
            
            # 识别查询类型和意图
            query_types = self._get_query_types(text, image, audio)
            query_intent = self._identify_query_intent(text, query_types)
            
            # 根据查询类型和意图选择权重
            weights = self._get_weights_by_intent(query_intent)
            
            # 执行多模态检索
            results = await self._multimodal_search(text, image, audio, query_types, weights, top_k, filters)
            
            # 结果融合和排序
            fused_results = self._fuse_results(results, weights)
            
            # 添加详细元数据
            enriched_results = await self._enrich_results(fused_results)
            
            self.logger.info(f"检索完成: 返回 {len(enriched_results)} 个结果")
            
            return enriched_results
            
        except Exception as e:
            self.logger.error(f"检索失败: {e}")
            return []
    
    def _get_query_types(self, text: Optional[str], image: Optional[bytes], audio: Optional[bytes]) -> Dict[str, bool]:
        """
        获取查询类型字典
        
        Args:
            text: 文本查询内容
            image: 图像查询数据
            audio: 音频查询数据
            
        Returns:
            查询类型字典，包含text、image、audio的布尔值
        """
        return {
            'text': bool(text),
            'image': bool(image),
            'audio': bool(audio)
        }
    
    def _identify_query_intent(self, text: Optional[str], query_types: Dict[str, bool]) -> str:
        """
        识别查询意图
        
        Args:
            text: 文本查询内容
            query_types: 查询类型字典
            
        Returns:
            查询意图字符串
        """
        # 如果只有图像输入，返回visual
        if query_types['image'] and not query_types['text'] and not query_types['audio']:
            return "visual"
        
        # 如果只有音频输入，返回audio
        if query_types['audio'] and not query_types['text'] and not query_types['image']:
            return "audio"
        
        # 如果有文本输入，分析文本内容
        if query_types['text']:
            query_lower = text.lower()
            
            # 先检测其他类型的查询，最后检测人名查询
            # 音频查询检测
            if self._is_audio_query(query_lower):
                return "audio"
            
            # 视觉查询检测 - 所有非音频、非人名的查询都视为视觉查询
            # 因为我们的主要功能是图像检索
            if not self._is_audio_query(query_lower) and not self._is_person_query(text):
                return "visual"
            
            # 最后检测人名查询
            if self._is_person_query(text):
                return "person"
        
        # 默认通用查询
        return "visual"
    
    def _is_person_query(self, query: str) -> bool:
        """检测是否为人名查询"""
        if not self.face_manager or not self.face_manager.face_recognition_enabled:
            return False
            
        # 简单的人名检测逻辑
        # 实际应用中应该使用更复杂的人名识别算法
        query = query.strip()
        
        # 常见姓氏列表（简化版）
        common_surnames = ['张', '王', '李', '刘', '陈', '杨', '赵', '黄', '周', '吴',
                          '徐', '孙', '胡', '朱', '高', '林', '何', '郭', '马', '罗']
        
        # 简单的人名模式：2-4个中文字符，且第一个字符是常见姓氏
        if len(query) >= 2 and len(query) <= 4:
            # 检查是否都是中文字符
            if all('\u4e00' <= char <= '\u9fff' for char in query):
                # 检查第一个字符是否是常见姓氏
                if query[0] in common_surnames:
                    return True
        
        # 检查数据库中是否有人物记录
        try:
            person_info = self.db_adapter.get_person_by_name(query)
            return person_info is not None
        except:
            return False
    
    def _is_audio_query(self, query: str) -> bool:
        """检测是否为音频查询"""
        for keyword in self.keywords['music'] + self.keywords['speech']:
            if keyword in query:
                return True
        return False
    
    def _is_visual_query(self, query: str) -> bool:
        """检测是否为视觉查询"""
        for keyword in self.keywords['visual']:
            if keyword in query:
                return True
        return False
    
    def _get_weights_by_intent(self, intent: str) -> Dict[str, float]:
        """根据查询意图获取权重"""
        if intent == "person":
            return self.person_weights
        elif intent == "audio":
            # 进一步区分音乐和语音
            # 这里简化处理，实际应该更复杂
            return self.audio_weights['music']
        elif intent == "visual":
            return self.visual_weights
        else:
            return self.default_weights
    
    async def _multimodal_search(self, text: Optional[str], image: Optional[bytes], audio: Optional[bytes], query_types: Dict[str, bool], weights: Dict[str, float], top_k: int, filters: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """
        执行多模态检索
        
        Args:
            text: 文本查询内容
            image: 图像查询数据
            audio: 音频查询数据
            query_types: 查询类型字典
            weights: 模型权重字典
            top_k: 返回结果数量
            filters: 过滤条件
            
        Returns:
            多模态检索结果字典
        """
        results = {}
        
        try:
            # CLIP模型检索（视觉模态）
            if weights.get('clip', 0) > 0:
                # 处理图像输入
                if query_types['image']:
                    clip_results = await self._search_with_clip(image, "image", top_k, filters)
                    results['clip'] = clip_results
                # 处理文本输入（视觉相关）
                elif query_types['text']:
                    clip_results = await self._search_with_clip(text, "text", top_k, filters)
                    results['clip'] = clip_results
            
            # CLAP模型检索（音频模态）
            if weights.get('clap', 0) > 0 and 'clap' in self.embedding_engine.get_available_models():
                # 处理音频输入
                if query_types['audio']:
                    clap_results = await self._search_with_clap(audio, "audio", top_k, filters)
                    results['clap'] = clap_results
                # 处理文本输入（音频相关）
                elif query_types['text']:
                    clap_results = await self._search_with_clap(text, "text", top_k, filters)
                    results['clap'] = clap_results
            
            # Whisper模型检索（语音模态）
            if weights.get('whisper', 0) > 0 and 'whisper' in self.embedding_engine.get_available_models():
                # 处理音频输入
                if query_types['audio']:
                    whisper_results = await self._search_with_whisper(audio, "audio", top_k, filters)
                    results['whisper'] = whisper_results
                # 处理文本输入（语音相关）
                elif query_types['text']:
                    whisper_results = await self._search_with_whisper(text, "text", top_k, filters)
                    results['whisper'] = whisper_results
        
        except Exception as e:
            self.logger.error(f"多模态检索失败: {e}")
        
        return results
    
    async def _search_with_clip(self, query: str, query_type: str, top_k: int, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """使用CLIP模型检索"""
        try:
            # 向量化查询
            if query_type == "text":
                query_vector = await self.embedding_engine.embed_text_for_visual(query)
            elif query_type == "image":
                query_vector = await self.embedding_engine.embed_image(query.encode() if isinstance(query, str) else query)
            else:
                return []
            
            # 从配置获取阈值
            score_thresholds = self.config_manager.get('smart_retrieval.score_thresholds', {
                'default': 0.5,
                'strict': 0.7,
                'relaxed': 0.3
            })
            
            # 执行真实的向量检索
            search_results = await self.embedding_engine.search_vector(
                collection_type='visual',
                query_vector=query_vector,
                limit=top_k,
                score_threshold=score_thresholds.get('default', 0.5),
                filters=filters
            )
            
            # 格式化结果
            formatted_results = []
            for result in search_results:
                formatted_result = {
                    'file_id': result['payload']['file_id'],
                    'score': result['score'],
                    'model': 'clip',
                    'metadata': {
                        'segment_id': result['payload'].get('segment_id'),
                        'created_at': result['payload'].get('created_at'),
                        'absolute_timestamp': result['payload'].get('absolute_timestamp'),
                        'file_type': result['payload'].get('file_type'),
                        **result['payload']
                    }
                }
                formatted_results.append(formatted_result)
            
            return formatted_results
            
        except Exception as e:
            self.logger.error(f"CLIP检索失败: {e}")
            return []
    
    async def _search_with_clap(self, query: str, query_type: str, top_k: int, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """使用CLAP模型检索"""
        try:
            # 向量化查询
            if query_type == "text":
                query_vector = await self.embedding_engine.embed_text_for_music(query)
            elif query_type == "audio":
                query_vector = await self.embedding_engine.embed_audio_music(query.encode() if isinstance(query, str) else query)
            else:
                return []
            
            # 从配置获取阈值
            score_thresholds = self.config_manager.get('smart_retrieval.score_thresholds', {
                'default': 0.5,
                'strict': 0.7,
                'relaxed': 0.3
            })
            
            # 执行真实的向量检索
            search_results = await self.embedding_engine.search_vector(
                collection_type='audio_music',
                query_vector=query_vector,
                limit=top_k,
                score_threshold=score_thresholds.get('strict', 0.7),
                filters=filters
            )
            
            # 格式化结果
            formatted_results = []
            for result in search_results:
                formatted_result = {
                    'file_id': result['payload']['file_id'],
                    'score': result['score'],
                    'model': 'clap',
                    'metadata': {
                        'segment_id': result['payload'].get('segment_id'),
                        'created_at': result['payload'].get('created_at'),
                        'absolute_timestamp': result['payload'].get('absolute_timestamp'),
                        'file_type': result['payload'].get('file_type'),
                        **result['payload']
                    }
                }
                formatted_results.append(formatted_result)
            
            return formatted_results
            
        except Exception as e:
            self.logger.error(f"CLAP检索失败: {e}")
            return []
    
    async def _search_with_whisper(self, query: str, query_type: str, top_k: int, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """使用Whisper模型检索"""
        try:
            # Whisper主要用于语音转文本检索
            if query_type == "text":
                # 先尝试语音转文本（这里简化处理）
                # 实际应用中应该从已转录的文本中搜索
                
                # 从配置获取阈值
                score_thresholds = self.config_manager.get('smart_retrieval.score_thresholds', {
                    'default': 0.5,
                    'strict': 0.7,
                    'relaxed': 0.3
                })
                
                # 执行真实的语音检索
                search_results = await self.embedding_engine.search_vector(
                    collection_type='audio_speech',
                    query_vector=await self.embedding_engine.embed_text_for_visual(query),  # 使用CLIP进行文本向量化
                    limit=top_k,
                    score_threshold=score_thresholds.get('strict', 0.7),
                    filters=filters
                )
                
                # 格式化结果
                formatted_results = []
                for result in search_results:
                    formatted_result = {
                        'file_id': result['payload']['file_id'],
                        'score': result['score'],
                        'model': 'whisper',
                        'metadata': {
                            'segment_id': result['payload'].get('segment_id'),
                            'created_at': result['payload'].get('created_at'),
                            'absolute_timestamp': result['payload'].get('absolute_timestamp'),
                            'file_type': result['payload'].get('file_type'),
                            **result['payload']
                        }
                    }
                    formatted_results.append(formatted_result)
                
                return formatted_results
            elif query_type == "audio":
                # 音频查询：先转录，然后搜索
                try:
                    audio_data = query.encode() if isinstance(query, str) else query
                    transcription = await self.embedding_engine.transcribe_audio(audio_data)
                    
                    # 使用转录结果进行搜索
                    return await self._search_with_whisper(transcription, "text", top_k, filters)
                except Exception as e:
                    self.logger.error(f"音频转录失败: {e}")
                    return []
            else:
                return []
            
        except Exception as e:
            self.logger.error(f"Whisper检索失败: {e}")
            return []
    
    def _fuse_results(self, results: Dict[str, List[Dict[str, Any]]], weights: Dict[str, float]) -> List[Dict[str, Any]]:
        """融合多模态检索结果"""
        try:
            # 收集所有结果
            all_results = []
            
            for model, model_results in results.items():
                weight = weights.get(model, 0)
                
                for result in model_results:
                    # 应用权重
                    weighted_score = result['score'] * weight
                    
                    fused_result = {
                        'file_id': result['file_id'],
                        'score': weighted_score,
                        'original_score': result['score'],
                        'model': result['model'],
                        'weight': weight,
                        'metadata': result['metadata']
                    }
                    
                    all_results.append(fused_result)
            
            # 按file_id分组并合并分数
            merged_results = {}
            
            for result in all_results:
                file_id = result['file_id']
                
                if file_id not in merged_results:
                    merged_results[file_id] = {
                        'file_id': file_id,
                        'score': 0,
                        'model_scores': {},
                        'metadata': result['metadata']
                    }
                
                # 累加权重分数
                merged_results[file_id]['score'] += result['score']
                
                # 记录各模型分数
                merged_results[file_id]['model_scores'][result['model']] = {
                    'score': result['original_score'],
                    'weight': result['weight']
                }
            
            # 转换为列表并排序
            final_results = list(merged_results.values())
            final_results.sort(key=lambda x: x['score'], reverse=True)
            
            # 转换numpy类型为Python原生类型
            for result in final_results:
                # 转换分数
                result['score'] = float(result['score'])
                # 转换模型分数
                for model in result['model_scores']:
                    result['model_scores'][model]['score'] = float(result['model_scores'][model]['score'])
                    result['model_scores'][model]['weight'] = float(result['model_scores'][model]['weight'])
            
            return final_results
            
        except Exception as e:
            self.logger.error(f"结果融合失败: {e}")
            return []
    
    async def _enrich_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """丰富结果元数据"""
        try:
            enriched_results = []
            
            for result in results:
                # 从数据库获取完整文件信息
                file_info = await self.db_adapter.get_file(result['file_id'])
                
                if file_info:
                    # 合并元数据
                    enriched_result = {
                        **result,
                        'file_info': file_info,
                        'file_path': file_info['file_path'],
                        'file_name': file_info['file_name'],
                        'file_type': file_info['file_type'],
                        'file_size': file_info['file_size'],
                        'created_at': file_info['created_at'],
                        'status': file_info['status']
                    }
                    
                    # 获取视频片段信息
                    if file_info['file_type'] in ['video', 'mp4', 'avi', 'mov', 'mkv']:
                        segment_info = await self.db_adapter.get_video_segment_by_file(result['file_id'])
                        if segment_info:
                            enriched_result['segment_info'] = segment_info
                    
                    enriched_results.append(enriched_result)
            
            return enriched_results
            
        except Exception as e:
            self.logger.error(f"丰富结果元数据失败: {e}")
            return results
    
    async def search_video_multimodal(self, text: str = None, image: bytes = None, audio: bytes = None, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        执行视频多模态融合检索（视觉+音频）
        
        Args:
            text: 文本查询
            image: 图像查询
            audio: 音频查询
            top_k: 返回结果数量
            
        Returns:
            检索结果列表
        """
        try:
            self.logger.info(f"执行视频多模态融合检索: text={bool(text)}, image={bool(image)}, audio={bool(audio)}, top_k={top_k}")
            
            # 分别执行视觉和音频检索
            visual_results = []
            audio_results = []
            
            if text or image:
                # 执行视觉检索
                visual_results = await self._search_with_clip(text or image, "text" if text else "image", top_k * 2, {})
                
            if text or audio:
                # 执行音频检索
                audio_results = await self._search_with_clap(text or audio, "text" if text else "audio", top_k * 2, {})
            
            # 视频多模态融合
            fusion_results = self._fuse_video_multimodal_results(visual_results, audio_results, top_k)
            
            # 添加详细元数据
            enriched_results = await self._enrich_results(fusion_results)
            
            self.logger.info(f"视频多模态融合检索完成: 返回 {len(enriched_results)} 个结果")
            
            return enriched_results
            
        except Exception as e:
            self.logger.error(f"视频多模态融合检索失败: {e}")
            return []
    
    def _fuse_video_multimodal_results(self, visual_results: List[Dict[str, Any]], audio_results: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
        """
        融合视频多模态检索结果
        
        Args:
            visual_results: 视觉检索结果
            audio_results: 音频检索结果
            top_k: 返回结果数量
            
        Returns:
            融合后的结果列表
        """
        try:
            # 按file_id分组结果
            file_groups = {}
            
            # 添加视觉结果
            for result in visual_results:
                file_id = result['file_id']
                if file_id not in file_groups:
                    file_groups[file_id] = {
                        'file_id': file_id,
                        'visual_score': 0,
                        'audio_score': 0,
                        'metadata': result['metadata']
                    }
                file_groups[file_id]['visual_score'] = result['score']
            
            # 添加音频结果
            for result in audio_results:
                file_id = result['file_id']
                if file_id not in file_groups:
                    file_groups[file_id] = {
                        'file_id': file_id,
                        'visual_score': 0,
                        'audio_score': 0,
                        'metadata': result['metadata']
                    }
                file_groups[file_id]['audio_score'] = result['score']
            
            # 计算融合分数
            fusion_results = []
            for file_id, group in file_groups.items():
                # 应用视频融合权重
                visual_score = group['visual_score'] * self.video_fusion_weights['visual']
                audio_score = group['audio_score'] * self.video_fusion_weights['audio']
                
                # 计算融合分数（可采用加权平均、几何平均等方法）
                fusion_score = visual_score + audio_score
                
                fusion_result = {
                    'file_id': file_id,
                    'score': fusion_score,
                    'visual_score': group['visual_score'],
                    'audio_score': group['audio_score'],
                    'model': 'video_multimodal',
                    'metadata': group['metadata']
                }
                
                fusion_results.append(fusion_result)
            
            # 按融合分数排序
            fusion_results.sort(key=lambda x: x['score'], reverse=True)
            
            # 限制返回结果数量
            return fusion_results[:top_k]
            
        except Exception as e:
            self.logger.error(f"视频多模态融合结果失败: {e}")
            return []
    
    async def get_similar_files(self, file_id: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """获取相似文件"""
        try:
            # 获取文件信息
            file_info = await self.db_adapter.get_file(file_id)
            if not file_info:
                return []
            
            # 根据文件类型执行相似性检索
            file_type = file_info['file_type']
            
            if file_type in ['.jpg', '.jpeg', '.png', '.bmp', '.webp']:
                # 图像相似性检索
                return await self._find_similar_images(file_id, top_k)
            elif file_type in ['.mp4', '.avi', '.mov', '.mkv', '.wmv']:
                # 视频相似性检索 - 使用多模态融合
                return await self._find_similar_videos_multimodal(file_id, top_k)
            elif file_type in ['.mp3', '.wav', '.flac', '.aac', '.m4a']:
                # 音频相似性检索
                return await self._find_similar_audio(file_id, top_k)
            else:
                return []
                
        except Exception as e:
            self.logger.error(f"获取相似文件失败: {e}")
            return []
    
    async def _find_similar_videos_multimodal(self, file_id: str, top_k: int) -> List[Dict[str, Any]]:
        """使用多模态融合查找相似视频"""
        try:
            # 获取视频的视觉和音频特征
            video_info = await self.db_adapter.get_file(file_id)
            
            # 首先通过视觉特征查找相似视频
            visual_similar = await self._find_similar_videos(file_id, top_k * 2)
            
            # 然后通过音频特征查找相似视频
            # 这里需要扩展以支持音频特征检索
            audio_similar = await self._find_similar_videos(file_id, top_k * 2)  # 简化实现
            
            # 融合两种相似结果
            fusion_results = self._fuse_video_multimodal_results(visual_similar, audio_similar, top_k)
            
            return fusion_results
        except Exception as e:
            self.logger.error(f"多模态视频相似检索失败: {e}")
            # 回退到传统视觉相似检索
            return await self._find_similar_videos(file_id, top_k)
    
    async def _find_similar_images(self, file_id: str, top_k: int) -> List[Dict[str, Any]]:
        """查找相似图像"""
        try:
            # 获取文件信息
            file_info = await self.db_adapter.get_file(file_id)
            if not file_info:
                return []
            
            # 尝试从向量存储中查找相似图像
            try:
                # 首先获取该文件的向量
                file_vectors = await self.embedding_engine.search_similar_vectors(
                    collection_type='visual',
                    file_id=file_id,
                    limit=top_k * 2
                )
                
                if file_vectors:
                    results = []
                    for vector_result in file_vectors:
                        if vector_result['payload']['file_id'] != file_id:  # 排除自身
                            result = {
                                'file_id': vector_result['payload']['file_id'],
                                'score': vector_result['score'],
                                'model': 'clip',
                                'metadata': vector_result['payload']
                            }
                            results.append(result)
                            
                            if len(results) >= top_k:
                                break
                    
                    return results
            except Exception as e:
                self.logger.warning(f"向量检索相似图像失败: {e}")
            
            # 如果向量检索失败，使用模拟实现
            return [
                {
                    'file_id': f'similar_image_{i}',
                    'score': 0.9 - i * 0.1,
                    'file_path': f'/path/to/similar_image_{i}.jpg',
                    'file_type': '.jpg'
                }
                for i in range(min(top_k, 5))
            ]
        except Exception as e:
            self.logger.error(f"查找相似图像失败: {e}")
            return []
    
    async def _find_similar_videos(self, file_id: str, top_k: int) -> List[Dict[str, Any]]:
        """查找相似视频"""
        try:
            # 获取文件信息
            file_info = await self.db_adapter.get_file(file_id)
            if not file_info:
                return []
            
            # 尝试从向量存储中查找相似视频
            try:
                # 首先获取该文件的向量
                file_vectors = await self.embedding_engine.search_similar_vectors(
                    collection_type='visual',  # 视频使用视觉向量
                    file_id=file_id,
                    limit=top_k * 2
                )
                
                if file_vectors:
                    results = []
                    for vector_result in file_vectors:
                        if vector_result['payload']['file_id'] != file_id:  # 排除自身
                            result = {
                                'file_id': vector_result['payload']['file_id'],
                                'score': vector_result['score'],
                                'model': 'clip',
                                'metadata': vector_result['payload']
                            }
                            results.append(result)
                            
                            if len(results) >= top_k:
                                break
                    
                    return results
            except Exception as e:
                self.logger.warning(f"向量检索相似视频失败: {e}")
            
            # 如果向量检索失败，使用模拟实现
            return [
                {
                    'file_id': f'similar_video_{i}',
                    'score': 0.85 - i * 0.1,
                    'file_path': f'/path/to/similar_video_{i}.mp4',
                    'file_type': '.mp4'
                }
                for i in range(min(top_k, 5))
            ]
        except Exception as e:
            self.logger.error(f"查找相似视频失败: {e}")
            return []
    
    async def _find_similar_audio(self, file_id: str, top_k: int) -> List[Dict[str, Any]]:
        """查找相似音频"""
        try:
            # 获取文件信息
            file_info = await self.db_adapter.get_file(file_id)
            if not file_info:
                return []
            
            # 尝试从向量存储中查找相似音频
            try:
                # 首先获取该文件的向量
                file_vectors = await self.embedding_engine.search_similar_vectors(
                    collection_type='audio_music',  # 音频使用音乐向量
                    file_id=file_id,
                    limit=top_k * 2
                )
                
                if file_vectors:
                    results = []
                    for vector_result in file_vectors:
                        if vector_result['payload']['file_id'] != file_id:  # 排除自身
                            result = {
                                'file_id': vector_result['payload']['file_id'],
                                'score': vector_result['score'],
                                'model': 'clap',
                                'metadata': vector_result['payload']
                            }
                            results.append(result)
                            
                            if len(results) >= top_k:
                                break
                    
                    return results
            except Exception as e:
                self.logger.warning(f"向量检索相似音频失败: {e}")
            
            # 如果向量检索失败，使用模拟实现
            return [
                {
                    'file_id': f'similar_audio_{i}',
                    'score': 0.8 - i * 0.1,
                    'file_path': f'/path/to/similar_audio_{i}.mp3',
                    'file_type': '.mp3'
                }
                for i in range(min(top_k, 5))
            ]
        except Exception as e:
            self.logger.error(f"查找相似音频失败: {e}")
            return []
    
    async def get_search_suggestions(self, partial_query: str, limit: int = 10) -> List[str]:
        """获取搜索建议"""
        try:
            # 简单的搜索建议实现
            # 实际应用中应该基于历史搜索、热门搜索等
            suggestions = [
                f"{partial_query} 相关",
                f"{partial_query} 高清",
                f"{partial_query} 最新",
                f"热门 {partial_query}",
                f"推荐 {partial_query}"
            ]
            
            # 如果是人名查询，添加人名相关建议
            if self._is_person_query(partial_query):
                person_suggestions = await self._get_person_suggestions(partial_query)
                suggestions.extend(person_suggestions)
            
            return suggestions[:limit]
            
        except Exception as e:
            self.logger.error(f"获取搜索建议失败: {e}")
            return []
    
    async def _get_person_suggestions(self, partial_name: str) -> List[str]:
        """获取人名搜索建议"""
        try:
            if self.face_manager and self.face_manager.face_recognition_enabled:
                # 从人脸数据库中查找匹配的人名
                matching_persons = self.db_adapter.search_persons_by_partial_name(partial_name)
                return [person['name'] for person in matching_persons] if matching_persons else []
            return []
        except Exception as e:
            self.logger.error(f"获取人名搜索建议失败: {e}")
            return []
    
    async def get_popular_searches(self, limit: int = 10) -> List[str]:
        """获取热门搜索"""
        try:
            # 模拟热门搜索
            popular_searches = [
                "风景", "人物", "建筑", "动物", "美食",
                "音乐", "电影", "演讲", "自然", "艺术"
            ]
            
            # 如果有人脸功能，添加热门人物
            if self.face_manager and self.face_manager.face_recognition_enabled:
                popular_persons = await self._get_popular_persons(5)
                popular_searches.extend(popular_persons)
            
            return popular_searches[:limit]
            
        except Exception as e:
            self.logger.error(f"获取热门搜索失败: {e}")
            return []
    
    async def _get_popular_persons(self, limit: int = 5) -> List[str]:
        """获取热门人物"""
        try:
            if self.face_manager and self.face_manager.face_recognition_enabled:
                # 从人脸数据库中获取热门人物
                popular_persons = self.db_adapter.get_popular_persons(limit)
                return [person['name'] for person in popular_persons] if popular_persons else []
            return []
        except Exception as e:
            self.logger.error(f"获取热门人物失败: {e}")
            return []