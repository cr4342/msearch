"""
任务管理器
为用户提供直观的任务进度展示和手动管理界面
"""
import asyncio
import logging
import os
import uuid
from typing import Dict, List, Optional, Any
from pathlib import Path

from src.core.config_manager import ConfigManager
from src.components.database_manager import DatabaseManager
from src.core.vector_store import VectorStore
from src.core.embedding_engine import EmbeddingEngine


class TaskManager:
    """任务管理器 - 为用户提供直观的任务进度展示和手动管理界面"""
    
    def __init__(self, config_manager: ConfigManager, database_manager: DatabaseManager, 
                 vector_store: VectorStore, embedding_engine: EmbeddingEngine):
        self.config_manager = config_manager
        self.database_manager = database_manager
        self.vector_store = vector_store
        self.embedding_engine = embedding_engine
        
        self.logger = logging.getLogger(__name__)
        
        # 任务状态存储
        self.tasks: Dict[str, Dict[str, Any]] = {}
        
        # 运行状态
        self.is_running = False
        
        # 任务队列
        self.task_queue = asyncio.Queue()
        
        # 最大并发任务数
        self.max_concurrent_tasks = self.config_manager.get_int("system.max_workers", 4)
        
        self.logger.info("任务管理器初始化完成")
    
    async def start(self):
        """启动任务管理器"""
        self.logger.info("启动任务管理器")
        self.is_running = True
        
        # 启动任务处理器
        self.task_processor = asyncio.create_task(self._process_tasks())
        
        self.logger.info("任务管理器启动完成")
    
    async def stop(self):
        """停止任务管理器"""
        self.logger.info("停止任务管理器")
        self.is_running = False
        
        # 停止任务处理器
        if hasattr(self, 'task_processor'):
            self.task_processor.cancel()
            try:
                await self.task_processor
            except asyncio.CancelledError:
                pass
        
        self.logger.info("任务管理器已停止")
    
    async def create_task(self, file_path: str, task_type: str) -> str:
        """创建处理任务"""
        task_id = str(uuid.uuid4())
        
        task_info = {
            'id': task_id,
            'file_path': file_path,
            'task_type': task_type,
            'status': 'PENDING',
            'progress': 0,
            'created_at': asyncio.get_event_loop().time(),
            'updated_at': asyncio.get_event_loop().time(),
            'retries': 0,
            'max_retries': self.config_manager.get_int("retry.max_attempts", 5)
        }
        
        self.tasks[task_id] = task_info
        
        # 添加到队列
        await self.task_queue.put(task_id)
        
        self.logger.info(f"创建任务: {task_id}, 文件: {file_path}, 类型: {task_type}")
        
        return task_id
    
    async def process_task(self, task_id: str):
        """处理单个任务"""
        if task_id not in self.tasks:
            self.logger.error(f"任务不存在: {task_id}")
            return
        
        task = self.tasks[task_id]
        file_path = task['file_path']
        
        try:
            # 更新任务状态为处理中
            await self._update_task_status(task_id, 'PROCESSING')
            
            # 根据文件类型进行处理
            file_ext = Path(file_path).suffix.lower()
            
            if file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.webp']:
                # 图像处理
                await self._process_image_task(task_id, file_path)
            elif file_ext in ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.webm', '.m4v', '.mpg', '.mpeg', '.3gp', '.ogv']:
                # 视频处理
                await self._process_video_task(task_id, file_path)
            elif file_ext in ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.opus', '.wma', '.amr', '.aiff', '.au']:
                # 音频处理
                await self._process_audio_task(task_id, file_path)
            elif file_ext in ['.txt', '.md', '.json', '.csv', '.xml', '.html', '.log']:
                # 文本处理
                await self._process_text_task(task_id, file_path)
            else:
                self.logger.warning(f"不支持的文件类型: {file_ext}")
                await self._update_task_status(task_id, 'FAILED', error=f"不支持的文件类型: {file_ext}")
                return
            
            # 更新任务状态为完成
            await self._update_task_status(task_id, 'COMPLETED')
            
            self.logger.info(f"任务完成: {task_id}, 文件: {file_path}")
            
        except Exception as e:
            self.logger.error(f"任务处理失败: {task_id}, 错误: {e}")
            
            # 检查是否需要重试
            task['retries'] += 1
            if task['retries'] < task['max_retries']:
                self.logger.info(f"任务将重试: {task_id}, 尝试次数: {task['retries'] + 1}")
                await self._update_task_status(task_id, 'PENDING')
                await self.task_queue.put(task_id)  # 重新加入队列
            else:
                await self._update_task_status(task_id, 'FAILED', error=str(e))
    
    async def _process_image_task(self, task_id: str, file_path: str):
        """处理图像任务"""
        self.logger.debug(f"处理图像任务: {task_id}, 文件: {file_path}")
        
        # 1. 预处理图像
        # 2. 向量化
        vector = await self.embedding_engine.embed_image_from_path(file_path)
        
        # 3. 存储向量
        await self.vector_store.insert_vectors(
            collection='image_vectors',
            vectors=[vector],
            ids=[task_id],
            metadata=[{
                'file_path': file_path,
                'file_type': 'image',
                'task_id': task_id
            }]
        )
        
        # 4. 更新进度
        await self._update_task_progress(task_id, 100)
    
    async def _process_video_task(self, task_id: str, file_path: str):
        """处理视频任务"""
        self.logger.debug(f"处理视频任务: {task_id}, 文件: {file_path}")
        
        # 1. 预处理视频（切片、音频分离等）
        # 2. 向量化视频帧
        vector = await self.embedding_engine.embed_video_frame_from_path(file_path)
        
        # 3. 存储向量
        await self.vector_store.insert_vectors(
            collection='video_vectors',
            vectors=[vector],
            ids=[task_id],
            metadata=[{
                'file_path': file_path,
                'file_type': 'video',
                'task_id': task_id
            }]
        )
        
        # 4. 更新进度
        await self._update_task_progress(task_id, 100)
    
    async def _process_audio_task(self, task_id: str, file_path: str):
        """处理音频任务"""
        self.logger.debug(f"处理音频任务: {task_id}, 文件: {file_path}")
        
        # 1. 预处理音频（分类等）
        # 2. 向量化音频
        vector = await self.embedding_engine.embed_audio_from_path(file_path)
        
        # 3. 存储向量
        await self.vector_store.insert_vectors(
            collection='audio_vectors',
            vectors=[vector],
            ids=[task_id],
            metadata=[{
                'file_path': file_path,
                'file_type': 'audio',
                'task_id': task_id
            }]
        )
        
        # 4. 更新进度
        await self._update_task_progress(task_id, 100)
    
    async def _process_text_task(self, task_id: str, file_path: str):
        """处理文本任务"""
        self.logger.debug(f"处理文本任务: {task_id}, 文件: {file_path}")
        
        # 1. 读取文本内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 2. 向量化文本
        vector = await self.embedding_engine.embed_text_for_visual(content)
        
        # 3. 存储向量
        await self.vector_store.insert_vectors(
            collection='text_vectors',
            vectors=[vector],
            ids=[task_id],
            metadata=[{
                'file_path': file_path,
                'file_type': 'text',
                'task_id': task_id
            }]
        )
        
        # 4. 更新进度
        await self._update_task_progress(task_id, 100)
    
    async def _update_task_status(self, task_id: str, status: str, error: Optional[str] = None):
        """更新任务状态"""
        if task_id in self.tasks:
            self.tasks[task_id]['status'] = status
            self.tasks[task_id]['updated_at'] = asyncio.get_event_loop().time()
            if error:
                self.tasks[task_id]['error'] = error
    
    async def _update_task_progress(self, task_id: str, progress: int):
        """更新任务进度"""
        if task_id in self.tasks:
            self.tasks[task_id]['progress'] = progress
            self.tasks[task_id]['updated_at'] = asyncio.get_event_loop().time()
    
    async def _process_tasks(self):
        """处理任务队列"""
        active_tasks = []
        
        while self.is_running:
            try:
                # 检查活跃任务
                completed_tasks = []
                for i, task in enumerate(active_tasks):
                    if task.done():
                        completed_tasks.append(i)
                
                # 移除已完成的任务
                for i in reversed(completed_tasks):
                    active_tasks.pop(i)
                
                # 检查是否可以启动新任务
                if (len(active_tasks) < self.max_concurrent_tasks and 
                    not self.task_queue.empty()):
                    
                    try:
                        task_id = self.task_queue.get_nowait()
                        task = asyncio.create_task(self.process_task(task_id))
                        active_tasks.append(task)
                    except asyncio.QueueEmpty:
                        pass
                
                # 等待一段时间再检查
                await asyncio.sleep(0.1)
                
            except asyncio.CancelledError:
                # 取消所有活跃任务
                for task in active_tasks:
                    task.cancel()
                
                # 等待所有任务完成
                if active_tasks:
                    await asyncio.gather(*active_tasks, return_exceptions=True)
                
                break
            except Exception as e:
                self.logger.error(f"任务处理器异常: {e}")
                await asyncio.sleep(1)
    
    async def get_all_tasks(self) -> List[Dict]:
        """获取所有任务信息"""
        return list(self.tasks.values())
    
    async def get_task_progress(self, task_id: str) -> Dict:
        """获取任务进度"""
        if task_id in self.tasks:
            task = self.tasks[task_id].copy()
            # 移除敏感信息
            if 'error' in task and task['status'] != 'FAILED':
                del task['error']
            return task
        return {}
    
    async def pause_task(self, task_id: str) -> None:
        """暂停任务"""
        if task_id in self.tasks:
            self.tasks[task_id]['status'] = 'PAUSED'
            self.logger.info(f"任务已暂停: {task_id}")
    
    async def resume_task(self, task_id: str) -> None:
        """恢复任务"""
        if task_id in self.tasks:
            if self.tasks[task_id]['status'] == 'PAUSED':
                self.tasks[task_id]['status'] = 'PENDING'
                await self.task_queue.put(task_id)
                self.logger.info(f"任务已恢复: {task_id}")
    
    async def cancel_task(self, task_id: str) -> None:
        """取消任务"""
        if task_id in self.tasks:
            self.tasks[task_id]['status'] = 'CANCELLED'
            self.logger.info(f"任务已取消: {task_id}")
    
    async def start_full_scan(self, directory: str) -> str:
        """启动全量扫描"""
        scan_task_id = str(uuid.uuid4())
        self.logger.info(f"启动全量扫描: {directory}, 任务ID: {scan_task_id}")
        
        # 扫描目录中的所有支持的文件
        supported_extensions = (
            '.jpg', '.jpeg', '.png', '.bmp', '.webp',  # 图像
            '.mp4', '.avi', '.mov', '.mkv', '.wmv', '.webm', '.m4v', '.mpg', '.mpeg', '.3gp', '.ogv',  # 视频
            '.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.opus', '.wma', '.amr', '.aiff', '.au',  # 音频
            '.txt', '.md', '.json', '.csv', '.xml', '.html', '.log'  # 文本
        )
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.lower().endswith(supported_extensions):
                    file_path = os.path.join(root, file)
                    await self.create_task(file_path, 'index')
        
        return scan_task_id

    async def start_incremental_scan(self, directory: str) -> str:
        """启动增量扫描"""
        scan_task_id = str(uuid.uuid4())
        self.logger.info(f"启动增量扫描: {directory}, 任务ID: {scan_task_id}")
        
        # 实现增量扫描逻辑
        # 这里只是示例，实际实现需要检查数据库中已有的文件
        await self.start_full_scan(directory)
        
        return scan_task_id

    async def reindex_file(self, file_path: str) -> str:
        """重新索引文件"""
        self.logger.info(f"重新索引文件: {file_path}")
        
        # 删除旧的向量
        # 这里需要根据文件路径删除相关的向量
        
        # 创建新的索引任务
        return await self.create_task(file_path, 'reindex')