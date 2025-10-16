"""
处理编排器模块
负责协调各专业处理模块的调用顺序和数据流转
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

from src.core.config_manager import get_config_manager
from src.core.logging_config import get_logger
from src.services.media_processor import get_media_processor
from src.models.model_manager import get_model_manager
from src.models.vector_store import get_vector_store
from src.core.db_adapter import get_db_adapter
from src.core.file_type_detector import get_file_type_detector

logger = get_logger(__name__)


class ProcessingOrchestrator:
    """处理编排器 - 负责策略路由和流程编排"""
    
    def __init__(self):
        """
        初始化处理编排器
        """
        self.config_manager = get_config_manager()
        self.db_adapter = get_db_adapter()
        
        # 初始化各处理模块
        self.media_processor = get_media_processor()
        self.model_manager = get_model_manager()
        self.vector_store = get_vector_store()
        
        # 处理状态跟踪
        self.processing_status = {}
        
        logger.info("处理编排器初始化完成")
    
    async def process_file(self, file_path: str, file_id: str) -> Dict[str, Any]:
        """
        处理文件 - 核心编排方法
        
        Args:
            file_path: 文件路径
            file_id: 文件ID
            
        Returns:
            处理结果字典
        """
        try:
            logger.info(f"开始处理文件: {file_path} (ID: {file_id})")
            
            # 更新处理状态
            await self._update_processing_status(file_id, "processing", 0)
            
            # 1. 策略路由 - 根据文件类型选择处理策略
            file_type = self._determine_file_type(file_path)
            processing_strategy = self._select_processing_strategy(file_type)
            
            # 2. 文件预处理
            await self._update_processing_status(file_id, "preprocessing", 10)
            preprocessed_data = await self._preprocess_file(file_path, file_type)
            
            # 3. 向量化处理
            await self._update_processing_status(file_id, "vectorizing", 50)
            vector_data = await self._vectorize_content(preprocessed_data, file_type, file_id)
            
            # 4. 存储向量数据
            await self._update_processing_status(file_id, "storing", 80)
            await self._store_vectors(vector_data, file_id)
            
            # 5. 完成处理
            await self._update_processing_status(file_id, "completed", 100)
            
            logger.info(f"文件处理完成: {file_path} (ID: {file_id})")
            
            return {
                "success": True,
                "file_id": file_id,
                "file_path": file_path,
                "file_type": file_type,
                "strategy": processing_strategy,
                "status": "completed"
            }
            
        except Exception as e:
            logger.error(f"文件处理失败: {file_path} (ID: {file_id}), 错误: {e}")
            await self._update_processing_status(file_id, "failed", 0, str(e))
            
            return {
                "success": False,
                "file_id": file_id,
                "file_path": file_path,
                "error": str(e),
                "status": "failed"
            }
    
    def _determine_file_type(self, file_path: str) -> str:
        """
        确定文件类型
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件类型
        """
        # 使用FileTypeDetector组件进行文件类型检测
        file_type_detector = get_file_type_detector()
        file_info = file_type_detector.detect_file_type(file_path)
        
        file_type = file_info['type']
        logger.debug(f"文件类型已确定: {file_path} -> {file_type} (信心度: {file_info['confidence']:.2f})")
        
        # 如果检测结果为unknown，尝试基于配置的文件扩展名进行回退检测
        if file_type == 'unknown':
            extension = Path(file_path).suffix.lower()
            # 配置中定义的文件类型映射作为回退
            file_type_mapping = self.config_manager.get('processing.file_type_mapping', {
                # 图片文件
                '.jpg': 'image',
                '.jpeg': 'image',
                '.png': 'image',
                '.bmp': 'image',
                '.gif': 'image',
                '.webp': 'image',
                # 视频文件
                '.mp4': 'video',
                '.avi': 'video',
                '.mov': 'video',
                '.mkv': 'video',
                '.webm': 'video',
                # 音频文件
                '.mp3': 'audio',
                '.wav': 'audio',
                '.ogg': 'audio',
                '.flac': 'audio',
                '.aac': 'audio',
                # 文本文件
                '.txt': 'text',
                '.md': 'text',
                '.csv': 'text',
                '.json': 'text',
                '.xml': 'text'
            })
            
            file_type = file_type_mapping.get(extension, 'unknown')
            if file_type != 'unknown':
                logger.debug(f"使用回退检测确定文件类型: {file_path} -> {file_type}")
                
        return file_type
    
    def _select_processing_strategy(self, file_type: str) -> str:
        """
        选择处理策略
        
        Args:
            file_type: 文件类型
            
        Returns:
            处理策略名称
        """
        strategy_mapping = {
            "image": "image_processing",
            "video": "video_processing",
            "audio": "audio_processing"
        }
        
        return strategy_mapping.get(file_type, "default_processing")
    
    async def _preprocess_file(self, file_path: str, file_type: str) -> Dict[str, Any]:
        """
        文件预处理
        
        Args:
            file_path: 文件路径
            file_type: 文件类型
            
        Returns:
            预处理结果数据
        """
        if file_type == "image":
            return await self.media_processor.process_image(file_path)
        elif file_type == "video":
            return await self.media_processor.process_video(file_path)
        elif file_type == "audio":
            return await self.media_processor.process_audio(file_path)
        else:
            # 对于未知类型，尝试作为文本处理
            return {
                "status": "success",
                "original_path": file_path,
                "file_type": "unknown",
                "media_type": "unknown"
            }
    
    async def _vectorize_content(self, preprocessed_data: Dict[str, Any], file_type: str, file_id: str) -> Dict[str, Any]:
        """
        向量化内容
        
        Args:
            preprocessed_data: 预处理数据
            file_type: 文件类型
            
        Returns:
            向量数据
        """
        try:
            vector_data = {
                "file_type": file_type,
                "segments": []
            }
            
            # 根据文件类型选择合适的向量化方法
            if file_type == "image":
                # 图片向量化
                processed_path = preprocessed_data.get("processed_path", preprocessed_data.get("original_path"))
                if processed_path:
                    vector = await self.model_manager.embed_image(processed_path)
                    vector_data["segments"].append({
                        "type": "image",
                        "vector": vector,
                        "timestamp": 0
                    })
                
            elif file_type == "video":
                # 视频向量化 - 处理多个片段
                chunks = preprocessed_data.get("chunks", [])
                for chunk in chunks:
                    chunk_index = chunk.get("index", 0)
                    start_time = chunk.get("start_time", 0)
                    end_time = chunk.get("end_time", 0)
                    
                    # 视觉向量化
                    chunk_path = chunk.get("output_path")
                    if chunk_path and Path(chunk_path).exists():
                        visual_vector = await self.model_manager.embed_image(chunk_path)
                        vector_data["segments"].append({
                            "type": "visual",
                            "vector": visual_vector,
                            "timestamp": start_time,
                            "end_time": end_time,
                            "chunk_index": chunk_index
                        })
                    
                    # 音频向量化（如果视频有音频）
                    # 这里可以调用智能音频处理
                    # 暂时跳过，实际实现中会处理视频音频
                
                # 提取关键帧向量化
                keyframes = preprocessed_data.get("keyframes", [])
                for i, keyframe_path in enumerate(keyframes):
                    if Path(keyframe_path).exists():
                        keyframe_vector = await self.model_manager.embed_image(keyframe_path)
                        vector_data["segments"].append({
                            "type": "keyframe",
                            "vector": keyframe_vector,
                            "timestamp": i * 10,  # 模拟时间戳
                            "keyframe_index": i
                        })
                
                # 人脸检测和索引（如果启用了人脸识别）
                if self.config_manager.get("face_recognition.enabled", True):
                    await self._index_video_faces(preprocessed_data, file_id)
            
            elif file_type == "image":
                # 图片向量化
                processed_path = preprocessed_data.get("processed_path", preprocessed_data.get("original_path"))
                if processed_path:
                    vector = await self.model_manager.embed_image(processed_path)
                    vector_data["segments"].append({
                        "type": "image",
                        "vector": vector,
                        "timestamp": 0
                    })
                
                # 人脸检测和索引（如果启用了人脸识别）
                if self.config_manager.get("face_recognition.enabled", True):
                    await self._index_image_faces(preprocessed_data, file_id)
                            
            elif file_type == "audio":
                # 音频向量化
                processed_path = preprocessed_data.get("processed_path", preprocessed_data.get("original_path"))
                if processed_path and Path(processed_path).exists():
                    # 智能处理音频（区分音乐和语音）
                    audio_results = await self.model_manager.process_video_audio_intelligently(
                        processed_path, is_video=False
                    )
                    
                    # 将处理结果添加到向量数据中
                    for audio_result in audio_results:
                        vector_data["segments"].append({
                            "type": audio_result["segment_type"],
                            "vector": audio_result["vector"],
                            "timestamp": audio_result.get("start_time", 0),
                            "end_time": audio_result.get("end_time", 0),
                            "transcribed_text": audio_result.get("transcribed_text", ""),
                            "quality_score": audio_result.get("quality_score", 0)
                        })
            
            return vector_data
            
        except Exception as e:
            logger.error(f"向量化处理失败: {e}")
            raise
    
    async def _store_vectors(self, vector_data: Dict[str, Any], file_id: str) -> bool:
        """
        存储向量数据
        
        Args:
            vector_data: 向量数据
            file_id: 文件ID
            
        Returns:
            存储是否成功
        """
        try:
            file_type = vector_data.get("file_type", "unknown")
            segments = vector_data.get("segments", [])
            
            # 为每个片段存储向量
            for i, segment in enumerate(segments):
                segment_type = segment.get("type", "unknown")
                vector = segment.get("vector")
                timestamp = segment.get("timestamp", 0)
                
                if not vector:
                    continue
                
                # 确定向量存储的集合名称
                collection_name = self._get_collection_name(segment_type)
                
                if collection_name:
                    # 准备元数据
                    metadata = {
                        "file_id": file_id,
                        "file_type": file_type,
                        "segment_type": segment_type,
                        "segment_index": i,
                        "start_time_ms": int(timestamp * 1000),
                        "end_time_ms": int(segment.get("end_time", timestamp) * 1000),
                        "quality_score": segment.get("quality_score", 1.0)
                    }
                    
                    # 添加额外的元数据
                    if "transcribed_text" in segment:
                        metadata["transcribed_text"] = segment["transcribed_text"]
                    
                    if "keyframe_index" in segment:
                        metadata["keyframe_index"] = segment["keyframe_index"]
                    
                    if "chunk_index" in segment:
                        metadata["chunk_index"] = segment["chunk_index"]
                    
                    # 存储向量
                    success = await self.vector_store.store_vectors(
                        collection_name=collection_name,
                        vectors=[vector],
                        payloads=[metadata]
                    )
                    
                    if not success:
                        logger.warning(f"向量存储失败: 集合 {collection_name}, 文件ID {file_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"向量存储失败: {e}")
            return False
    
    def _get_collection_name(self, segment_type: str) -> Optional[str]:
        """
        根据片段类型获取向量集合名称
        
        Args:
            segment_type: 片段类型
            
        Returns:
            集合名称或None
        """
        collection_mapping = {
            "image": "visual_vectors",
            "visual": "visual_vectors",
            "keyframe": "visual_vectors",
            "audio_music": "audio_music_vectors",
            "audio_speech": "audio_speech_vectors"
        }
        
        return collection_mapping.get(segment_type)
    
    async def _update_processing_status(self, file_id: str, status: str, progress: int, 
                                      error: Optional[str] = None):
        """
        更新处理状态
        
        Args:
            file_id: 文件ID
            status: 状态
            progress: 进度百分比
            error: 错误信息（可选）
        """
        try:
            # 更新内存状态
            self.processing_status[file_id] = {
                "status": status,
                "progress": progress,
                "error": error
            }
            
            # 更新数据库状态
            await self.db_adapter.update_queue_status(file_id, status, error)
            
        except Exception as e:
            logger.error(f"更新处理状态失败: {e}")
    
    def get_processing_status(self, file_id: str) -> Dict[str, Any]:
        """
        获取处理状态
        
        Args:
            file_id: 文件ID
            
        Returns:
            处理状态信息
        """
        return self.processing_status.get(file_id, {
            "status": "unknown",
            "progress": 0,
            "error": None
        })
    
    async def batch_process_files(self, file_list: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        批处理文件
        
        Args:
            file_list: 文件列表 [{"file_path": "...", "file_id": "..."}, ...]
            
        Returns:
            处理结果列表
        """
        try:
            logger.info(f"开始批处理 {len(file_list)} 个文件")
            
            # 获取批处理配置
            batch_config = self.config_manager.get('performance.batch_processing', {})
            max_concurrent = batch_config.get('max_concurrent', 4)
            
            # 创建任务组，限制并发数
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def process_with_semaphore(file_info):
                async with semaphore:
                    return await self.process_file(file_info["file_path"], file_info["file_id"])
            
            # 并发处理所有文件
            tasks = [process_with_semaphore(file_info) for file_info in file_list]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理异常结果
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"批处理文件失败: {file_list[i]['file_path']}, 错误: {result}")
                    processed_results.append({
                        "success": False,
                        "file_path": file_list[i]["file_path"],
                        "error": str(result)
                    })
                else:
                    processed_results.append(result)
            
            logger.info(f"批处理完成，成功: {len([r for r in processed_results if r.get('success')])}/{len(file_list)}")
            
            return processed_results
            
        except Exception as e:
            logger.error(f"批处理失败: {e}")
            raise
    
    async def _index_video_faces(self, preprocessed_data: Dict[str, Any], file_id: str):
        """为视频建立人脸索引"""
        try:
            from src.models.face_database import get_face_database
            
            face_db = get_face_database()
            
            # 获取视频路径
            video_path = preprocessed_data.get("original_path")
            if not video_path:
                logger.warning("无法获取视频路径，跳过人脸索引")
                return
            
            # 为视频建立人脸索引
            face_db.index_file_faces(file_id, video_path)
            
            logger.info(f"视频 {file_id} 的人脸索引建立完成")
        except Exception as e:
            logger.error(f"视频人脸索引失败: {e}")
    
    async def _index_image_faces(self, preprocessed_data: Dict[str, Any], file_id: str):
        """为图片建立人脸索引"""
        try:
            from src.models.face_database import get_face_database
            
            face_db = get_face_database()
            
            # 获取图片路径
            image_path = preprocessed_data.get("original_path")
            if not image_path:
                image_path = preprocessed_data.get("processed_path")
            if not image_path:
                logger.warning("无法获取图片路径，跳过人脸索引")
                return
            
            # 为图片建立人脸索引
            face_db.index_file_faces(file_id, image_path)
            
            logger.info(f"图片 {file_id} 的人脸索引建立完成")
        except Exception as e:
            logger.error(f"图片人脸索引失败: {e}")


# 全局处理编排器实例
_processing_orchestrator = None


def get_processing_orchestrator() -> ProcessingOrchestrator:
    """
    获取全局处理编排器实例
    
    Returns:
        处理编排器实例
    """
    global _processing_orchestrator
    if _processing_orchestrator is None:
        _processing_orchestrator = ProcessingOrchestrator()
    return _processing_orchestrator