"""
处理调度器
作为系统的核心调度组件，负责协调各专业处理模块的调用顺序和数据流转
"""

import asyncio
import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.common.storage.database_adapter import DatabaseAdapter
from src.processing_service.task_manager import TaskManager
from src.processing_service.media_processor import MediaProcessor
from src.common.embedding.embedding_engine import EmbeddingEngine


class ProcessingOrchestrator:
    """处理调度器"""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        
        # 初始化组件
        self.db_adapter = DatabaseAdapter()
        self.task_manager = TaskManager(config_manager)
        self.media_processor = MediaProcessor(config_manager)
        self.embedding_engine = EmbeddingEngine(config_manager)
        
        # 调度配置
        self.check_interval = self.config_manager.get("orchestrator.check_interval", 5.0)
        self.max_concurrent_tasks = self.config_manager.get("orchestrator.max_concurrent_tasks", 3)
        
        # 运行状态
        self.is_running = False
        self.scheduler_task: Optional[asyncio.Task] = None
        
        self.logger.info("处理调度器初始化完成")
    
    async def start(self):
        """启动调度器"""
        self.logger.info("启动处理调度器")
        
        self.is_running = True
        
        # 启动任务管理器
        await self.task_manager.start()
        
        # 启动调度循环
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())
        
        self.logger.info("处理调度器启动完成")
    
    async def stop(self):
        """停止调度器"""
        self.logger.info("停止处理调度器")
        
        self.is_running = False
        
        # 停止调度循环
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass
        
        # 停止任务管理器
        await self.task_manager.stop()
        
        self.logger.info("处理调度器已停止")
    
    async def _scheduler_loop(self):
        """调度循环"""
        while self.is_running:
            try:
                # 检查待处理任务
                await self._check_pending_tasks()
                
                # 等待下次检查
                await asyncio.sleep(self.check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"调度循环异常: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def _check_pending_tasks(self):
        """检查待处理任务"""
        try:
            # 获取待处理文件
            pending_files = await self.db_adapter.get_pending_files(limit=self.max_concurrent_tasks)
            
            if not pending_files:
                return
            
            self.logger.debug(f"发现 {len(pending_files)} 个待处理文件")
            
            # 为每个文件创建处理任务
            for file_info in pending_files:
                task_id = await self.task_manager.create_task(
                    file_id=file_info['id'],
                    task_type='processing',
                    status='pending'
                )
                
                # 异步处理文件
                asyncio.create_task(self._process_file(file_info, task_id))
        
        except Exception as e:
            self.logger.error(f"检查待处理任务失败: {e}")
    
    async def _process_file(self, file_info: Dict[str, Any], task_id: str):
        """处理单个文件"""
        import traceback
        try:
            self.logger.info(f"开始处理文件: {file_info['file_path']} (任务ID: {task_id})")
            
            # 更新任务状态为处理中
            await self.task_manager.update_task_status(task_id, 'processing')
            
            # 策略路由：根据文件类型选择处理策略
            self.logger.debug(f"确定处理策略: {file_info['file_path']}")
            processing_strategy = self._determine_processing_strategy(file_info)
            self.logger.debug(f"处理策略: {processing_strategy}")
            
            # 阶段一：预处理
            self.logger.debug(f"开始预处理: {file_info['file_path']}")
            await self._preprocess_file(file_info, task_id, processing_strategy)
            self.logger.debug(f"预处理完成: {file_info['file_path']}")
            
            # 阶段二：向量化
            self.logger.debug(f"开始向量化: {file_info['file_path']}")
            await self._vectorize_file(file_info, task_id, processing_strategy)
            self.logger.debug(f"向量化完成: {file_info['file_path']}")
            
            # 阶段三：存储
            self.logger.debug(f"开始存储结果: {file_info['file_path']}")
            await self._store_results(file_info, task_id)
            self.logger.debug(f"结果存储完成: {file_info['file_path']}")
            
            # 更新任务状态为完成
            await self.task_manager.update_task_status(task_id, 'completed')
            
            # 更新文件状态
            await self.db_adapter.update_file_status(file_info['id'], 'completed')
            
            self.logger.info(f"文件处理完成: {file_info['file_path']} (任务ID: {task_id})")
            
        except Exception as e:
            self.logger.error(f"文件处理失败: {file_info['file_path']}, 错误: {e}")
            self.logger.error(f"错误堆栈: {traceback.format_exc()}")
            
            # 更新任务状态为失败
            await self.task_manager.update_task_status(task_id, 'failed', str(e))
            
            # 更新文件状态
            await self.db_adapter.update_file_status(file_info['id'], 'failed')
    
    def _determine_processing_strategy(self, file_info: Dict[str, Any]) -> Dict[str, Any]:
        """根据文件类型确定处理策略"""
        file_type = file_info['file_type']
        
        # 从配置文件获取文件类型列表
        text_extensions = set(self.config_manager.get('file_types.text_extensions', [
            '.txt', '.md', '.json', '.csv', '.xml', '.html', '.log'
        ]))
        image_extensions = set(self.config_manager.get('file_types.image_extensions', [
            '.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tiff', '.tif', '.svg', '.heic', '.heif', '.ico'
        ]))
        video_extensions = set(self.config_manager.get('file_types.video_extensions', [
            '.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm', '.m4v', '.mpg', '.mpeg', '.3gp', '.ogv'
        ]))
        audio_extensions = set(self.config_manager.get('file_types.audio_extensions', [
            '.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.opus', '.wma'
        ]))
        
        # 文本处理策略
        if file_type in text_extensions:
            return {
                'modality': 'text',
                'preprocessing': None,  # 文本文件不需要预处理
                'vectorization': {
                    'model': 'clip',
                    'method': 'embed_text'
                }
            }
        
        # 图像处理策略
        elif file_type in image_extensions:
            return {
                'modality': 'image',
                'preprocessing': {
                    'resize': True,
                    'target_resolution': self.config_manager.get("media_processing.image.target_resolution", 720)
                },
                'vectorization': {
                    'model': 'clip',
                    'method': 'embed_image'
                }
            }
        
        # 视频处理策略
        elif file_type in video_extensions:
            return {
                'modality': 'video',
                'preprocessing': {
                    'scene_detection': True,
                    'max_segment_duration': self.config_manager.get("media_processing.video.max_segment_duration", 5),
                    'target_fps': self.config_manager.get("media_processing.video.target_fps", 8),
                    'audio_separation': True
                },
                'vectorization': {
                    'model': 'clip',
                    'method': 'embed_video_frames'
                }
            }
        
        # 音频处理策略
        elif file_type in audio_extensions:
            return {
                'modality': 'audio',
                'preprocessing': {
                    'format_conversion': True,
                    'sample_rate': self.config_manager.get("media_processing.audio.sample_rate", 16000),
                    'channels': 1
                },
                'vectorization': {
                    'model': 'clap',  # 音乐使用CLAP
                    'method': 'embed_audio'
                }
            }
        
        else:
            raise ValueError(f"不支持的文件类型: {file_type}")
    
    async def _preprocess_file(self, file_info: Dict[str, Any], task_id: str, strategy: Dict[str, Any]):
        """预处理文件"""
        self.logger.debug(f"开始预处理文件: {file_info['file_path']}")
        
        # 文本文件不需要预处理
        if strategy['modality'] == 'text':
            self.logger.debug(f"文本文件跳过预处理: {file_info['file_path']}")
            return
        
        # 调用媒体处理器进行预处理
        processed_data = await self.media_processor.process(
            file_path=file_info['file_path'],
            strategy=strategy['preprocessing']
        )
        
        # 存储预处理结果
        await self.db_adapter.store_preprocessing_result(
            file_id=file_info['id'],
            task_id=task_id,
            processed_data=processed_data
        )
        
        self.logger.debug(f"文件预处理完成: {file_info['file_path']}")
    
    async def _vectorize_file(self, file_info: Dict[str, Any], task_id: str, strategy: Dict[str, Any]):
        """向量化文件"""
        self.logger.debug(f"开始向量化文件: {file_info['file_path']}")
        
        # 获取预处理结果
        processed_data = await self.db_adapter.get_preprocessing_result(file_info['id'])
        
        # 根据策略进行向量化
        vectors = []
        segment_metadata = []
        
        collection_type = None
        if strategy['modality'] == 'text':
            # 文本向量化
            collection_type = 'text'
            # 读取文本文件内容
            with open(file_info['file_path'], 'r', encoding='utf-8') as f:
                text_content = f.read()
            # 向量化
            vector = await self.embedding_engine.embed_text(text_content)
            vectors.append(vector)
            segment_metadata.append({
                'id': str(uuid.uuid4()),
                'segment_type': 'text',
                'start_time': 0,
                'end_time': 0,
                'metadata': {
                    'text_length': len(text_content),
                    'content_preview': text_content[:100] if len(text_content) > 100 else text_content
                }
            })
        
        elif strategy['modality'] == 'image':
            # 图像向量化 - 从segments中获取图像数据
            collection_type = 'visual'
            for segment in processed_data.get('segments', []):
                if segment['segment_type'] == 'image':
                    # 读取图像文件数据
                    with open(segment['data_path'], 'rb') as f:
                        image_data = f.read()
                    # 向量化
                    vector = await self.embedding_engine.embed_image(image_data)
                    vectors.append(vector)
                    segment_metadata.append(segment)
        
        elif strategy['modality'] == 'video':
            # 视频帧向量化
            collection_type = 'visual'
            for segment in processed_data.get('segments', []):
                if segment['segment_type'] == 'video_frame':
                    # 读取视频帧文件数据
                    with open(segment['data_path'], 'rb') as f:
                        frame_data = f.read()
                    # 向量化
                    vector = await self.embedding_engine.embed_image(frame_data)
                    vectors.append(vector)
                    segment_metadata.append(segment)
        
        elif strategy['modality'] == 'audio':
            # 音频向量化
            collection_type = 'audio_music'
            for segment in processed_data.get('segments', []):
                if segment['segment_type'] == 'audio':
                    # 读取音频文件数据
                    with open(segment['data_path'], 'rb') as f:
                        audio_data = f.read()
                    # 向量化
                    vector = await self.embedding_engine.embed_audio_music(audio_data)
                    vectors.append(vector)
                    segment_metadata.append(segment)
        
        # 存储向量结果到本地SQLite数据库
        await self.db_adapter.store_vectors(
            file_id=file_info['id'],
            task_id=task_id,
            vectors=vectors,
            metadata=strategy['vectorization']
        )
        
        # 存储向量到Milvus Lite向量数据库
        if vectors and collection_type:
            # 准备向量数据
            vectors_data = []
            for i, (vector, metadata) in enumerate(zip(vectors, segment_metadata)):
                vectors_data.append((
                    vector,
                    file_info['id'],
                    metadata.get('id'),
                    {
                        'file_path': file_info['file_path'],
                        'file_name': file_info['file_name'],
                        'file_type': file_info['file_type'],
                        'modality': strategy['modality'],
                        'created_at': datetime.now().timestamp(),
                        **metadata.get('metadata', {})
                    }
                ))
            
            # 批量存储向量到Milvus Lite
            vector_ids = await self.embedding_engine.batch_store_vectors(
                collection_type=collection_type,
                vectors_data=vectors_data
            )
            
            self.logger.debug(f"向量存储到Milvus Lite成功: {len(vector_ids)}个向量")
        
        self.logger.debug(f"文件向量化完成: {file_info['file_path']}")
    
    async def _store_results(self, file_info: Dict[str, Any], task_id: str):
        """存储处理结果"""
        self.logger.debug(f"开始存储处理结果: {file_info['file_path']}")
        
        # 更新文件处理完成时间
        await self.db_adapter.update_file(
            file_id=file_info['id'],
            updates={
                'processed_at': datetime.now(),
                'status': 'completed'
            }
        )
        
        self.logger.debug(f"处理结果存储完成: {file_info['file_path']}")
    
    async def handle_file_notification(self, file_path: str):
        """处理文件监控通知"""
        self.logger.debug(f"收到文件通知: {file_path}")
        
        # 检查文件是否在数据库中且状态为pending
        file_info = await self.db_adapter.get_file_by_path(file_path)
        
        if file_info and file_info['status'] == 'pending':
            # 立即触发处理检查
            await self._check_pending_tasks()