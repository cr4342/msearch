"""
处理编排器 - 作为处理策略路由器和流程编排器，协调各专业处理模块的调用顺序和数据流转
"""
import uuid
from typing import Dict, Any
import logging
from src.business.media_processor import MediaProcessor
from src.business.embedding_engine import EmbeddingEngine
from src.business.task_manager import TaskManager
from src.storage.vector_store import VectorStore
from src.core.file_type_detector import get_file_type_detector

logger = logging.getLogger(__name__)


class ProcessingOrchestrator:
    """处理编排器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化处理编排器
        
        Args:
            config: 配置字典
        """
        self.config = config
        
        # 初始化组件
        self.file_type_detector = get_file_type_detector(config)
        self.media_processor = MediaProcessor(config)
        self.embedding_engine = EmbeddingEngine(config)
        self.task_manager = TaskManager(config)
        self.vector_store = VectorStore(config)
        
        logger.info("处理编排器初始化完成")
    
    async def process_file(self, file_path: str) -> Dict[str, Any]:
        """
        处理文件的完整流程
        
        Args:
            file_path: 文件路径
            
        Returns:
            处理结果字典
        """
        file_id = str(uuid.uuid4())
        
        try:
            logger.info(f"开始处理文件: {file_path}, file_id: {file_id}")
            
            # 1. 创建任务
            task_id = await self.task_manager.add_task(file_path)
            
            # 2. 更新任务状态为处理中
            self.task_manager.update_task_progress(task_id, 10, status="processing")
            
            # 3. 检测文件类型
            file_type_info = self.file_type_detector.detect_file_type(file_path)
            file_type = file_type_info['type']
            
            if file_type == 'unknown':
                raise ValueError(f"不支持的文件类型: {file_path}")
            
            logger.debug(f"文件类型检测完成: {file_path} -> {file_type}")
            
            # 4. 更新任务进度
            self.task_manager.update_task_progress(task_id, 20)
            
            # 5. 媒体预处理
            preprocessing_result = await self.media_processor.process_file(file_path, file_type)
            
            if preprocessing_result['status'] != 'success':
                raise ValueError(f"预处理失败: {preprocessing_result.get('error')}")
            
            logger.debug(f"媒体预处理完成: {file_path}")
            
            # 6. 更新任务进度
            self.task_manager.update_task_progress(task_id, 50)
            
            # 7. 向量化处理
            vectorization_result = await self._vectorize_content(preprocessing_result, file_type)
            
            if vectorization_result['status'] != 'success':
                raise ValueError(f"向量化失败: {vectorization_result.get('error')}")
            
            logger.debug(f"向量化处理完成: {file_path}")
            
            # 8. 更新任务进度
            self.task_manager.update_task_progress(task_id, 80)
            
            # 9. 存储向量和元数据
            storage_result = await self._store_results(
                file_id, file_path, file_type, 
                preprocessing_result, vectorization_result
            )
            
            if storage_result['status'] != 'success':
                raise ValueError(f"存储失败: {storage_result.get('error')}")
            
            logger.debug(f"结果存储完成: {file_path}")
            
            # 10. 完成任务
            self.task_manager.update_task_progress(task_id, 100)
            self.task_manager.complete_task(task_id, success=True)
            
            logger.info(f"文件处理完成: {file_path}, file_id: {file_id}")
            
            return {
                'status': 'success',
                'file_id': file_id,
                'file_path': file_path,
                'file_type': file_type,
                'processing_time': vectorization_result.get('processing_time', 0)
            }
            
        except Exception as e:
            logger.error(f"文件处理失败: {file_path}, 错误: {e}")
            
            # 更新任务状态为失败
            task_id = self._find_task_id_by_file(file_path)
            if task_id:
                self.task_manager.complete_task(task_id, success=False, error_message=str(e))
            
            return {
                'status': 'error',
                'error': str(e),
                'file_id': file_id,
                'file_path': file_path
            }
    
    async def _vectorize_content(self, preprocessing_result: Dict[str, Any], 
                                file_type: str) -> Dict[str, Any]:
        """
        向量化处理内容
        
        Args:
            preprocessing_result: 预处理结果
            file_type: 文件类型
            
        Returns:
            向量化结果字典
        """
        try:
            import time
            start_time = time.time()
            
            result_data = preprocessing_result['result']
            
            if file_type == 'image':
                # 图片向量化
                image_data = result_data['image_data']
                vector = await self.embedding_engine.embed_image(image_data)
                
                return {
                    'status': 'success',
                    'vectors': [vector],
                    'vector_type': 'image',
                    'processing_time': time.time() - start_time
                }
                
            elif file_type == 'video':
                # 视频向量化（处理关键帧）
                keyframes = result_data['keyframes']
                vectors = []
                
                for keyframe in keyframes:
                    frame_data = keyframe['frame_data']
                    vector = await self.embedding_engine.embed_image(frame_data)
                    vectors.append({
                        'vector': vector,
                        'timestamp': keyframe['timestamp'],
                        'frame_index': keyframe['frame_index']
                    })
                
                return {
                    'status': 'success',
                    'vectors': vectors,
                    'vector_type': 'video',
                    'processing_time': time.time() - start_time
                }
                
            elif file_type == 'audio':
                # 音频向量化
                segments = result_data['segments']
                vectors = []
                
                for segment in segments:
                    audio_data = segment['audio_data']
                    # 根据音频分类选择不同的模型
                    audio_type = result_data['classification']['primary_type']
                    
                    if audio_type == 'music':
                        vector = await self.embedding_engine.embed_audio_music(audio_data)
                    else:  # speech or noise
                        vector = await self.embedding_engine.embed_audio_speech(audio_data)
                    
                    vectors.append({
                        'vector': vector,
                        'start_time': segment['start_time'],
                        'end_time': segment['end_time']
                    })
                
                return {
                    'status': 'success',
                    'vectors': vectors,
                    'vector_type': 'audio',
                    'processing_time': time.time() - start_time
                }
                
            elif file_type == 'text':
                # 文本向量化
                cleaned_content = result_data['cleaned_content']
                vector = await self.embedding_engine.embed_text(cleaned_content)
                
                return {
                    'status': 'success',
                    'vectors': [vector],
                    'vector_type': 'text',
                    'processing_time': time.time() - start_time
                }
                
            else:
                raise ValueError(f"不支持的文件类型向量化: {file_type}")
                
        except Exception as e:
            logger.error(f"向量化处理失败: {file_type}, 错误: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def _store_results(self, file_id: str, file_path: str, file_type: str,
                            preprocessing_result: Dict[str, Any], 
                            vectorization_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        存储向量和元数据
        
        Args:
            file_id: 文件ID
            file_path: 文件路径
            file_type: 文件类型
            preprocessing_result: 预处理结果
            vectorization_result: 向量化结果
            
        Returns:
            存储结果字典
        """
        try:
            # 1. 存储文件元数据
            metadata = {
                'file_id': file_id,
                'file_path': file_path,
                'file_type': file_type,
                'status': 'completed'
            }
            
            # 2. 根据向量类型选择存储集合
            vector_type = vectorization_result['vector_type']
            collection_name = f"{vector_type}_vectors"
            
            # 3. 存储向量
            vectors = vectorization_result['vectors']
            
            if vector_type == 'image' or vector_type == 'text':
                # 单向量存储
                vector = vectors[0]
                vector_id = f"{vector_type}_{file_id}"
                await self.vector_store.store_vector(vector_id, vector, metadata, collection_name)
                
            elif vector_type == 'video':
                # 视频帧向量存储
                for i, frame_vector_data in enumerate(vectors):
                    vector = frame_vector_data['vector']
                    vector_id = f"{vector_type}_{file_id}_frame_{i}"
                    
                    # 添加时间戳信息
                    frame_metadata = metadata.copy()
                    frame_metadata['timestamp'] = frame_vector_data['timestamp']
                    frame_metadata['frame_index'] = frame_vector_data['frame_index']
                    
                    await self.vector_store.store_vector(vector_id, vector, frame_metadata, collection_name)
                    
            elif vector_type == 'audio':
                # 音频片段向量存储
                for i, audio_vector_data in enumerate(vectors):
                    vector = audio_vector_data['vector']
                    vector_id = f"{vector_type}_{file_id}_segment_{i}"
                    
                    # 添加时间戳信息
                    audio_metadata = metadata.copy()
                    audio_metadata['start_time'] = audio_vector_data['start_time']
                    audio_metadata['end_time'] = audio_vector_data['end_time']
                    
                    await self.vector_store.store_vector(vector_id, vector, audio_metadata, collection_name)
            
            logger.debug(f"向量存储完成: {file_path} -> {collection_name}")
            
            return {
                'status': 'success',
                'stored_vectors': len(vectors),
                'collection_name': collection_name
            }
            
        except Exception as e:
            logger.error(f"结果存储失败: {file_path}, 错误: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _find_task_id_by_file(self, file_path: str) -> str:
        """
        根据文件路径查找任务ID
        
        Args:
            file_path: 文件路径
            
        Returns:
            任务ID或None
        """
        # 这里应该实现根据文件路径查找任务ID的逻辑
        # 暂时返回None
        return None


# 示例使用
if __name__ == "__main__":
    import asyncio
    
    # 配置示例
    config = {
        'task': {
            'max_retry_count': 3,
            'max_concurrent_tasks': 4
        },
        'processing': {
            'image': {
                'target_size': 224,
                'max_resolution': (1920, 1080),
                'quality_threshold': 0.5
            },
            'video': {
                'target_size': 224,
                'max_resolution': (1280, 720),
                'scene_threshold': 0.3,
                'frame_interval': 2.0
            },
            'audio': {
                'target_sample_rate': 16000,
                'target_channels': 1,
                'segment_duration': 10.0,
                'quality_threshold': 0.5
            },
            'text': {
                'max_file_size': 10 * 1024 * 1024,
                'encoding_priority': ['utf-8', 'gbk', 'gb2312', 'latin-1']
            }
        },
        'file_monitoring.file_extensions': {
            'image': ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp'],
            'video': ['.mp4', '.avi', '.mov', '.mkv', '.webm'],
            'audio': ['.mp3', '.wav', '.ogg', '.flac', '.aac'],
            'text': ['.txt', '.md', '.csv', '.json', '.xml']
        },
        'file_monitoring.mime_types': {
            'image': ['image/jpeg', 'image/png', 'image/bmp', 'image/gif', 'image/webp'],
            'video': ['video/mp4', 'video/x-msvideo', 'video/quicktime', 'video/x-matroska', 'video/webm'],
            'audio': ['audio/mpeg', 'audio/wav', 'audio/ogg', 'audio/flac', 'audio/aac'],
            'text': ['text/plain', 'text/markdown', 'text/csv', 'application/json', 'application/xml']
        }
    }
    
    # 创建编排器实例
    # orchestrator = ProcessingOrchestrator(config)
    
    # 处理文件 (需要实际的文件路径)
    # result = asyncio.run(orchestrator.process_file("path/to/file.jpg"))
    # print(result)