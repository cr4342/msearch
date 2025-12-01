"""
批处理器
提供高效批处理机制来提升系统吞吐量
"""

import asyncio
import logging
import time
from typing import Callable, Any, List, Optional, Dict, Union
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from queue import Queue, Empty
from threading import Lock
from dataclasses import dataclass
from enum import Enum

from src.core.performance_monitor import PerformanceMonitor


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BatchTask:
    """批处理任务"""
    task_id: str
    data: Any
    callback: Optional[Callable] = None
    metadata: Optional[Dict] = None
    created_at: float = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()


class BatchProcessor:
    """批处理器"""
    
    def __init__(self, 
                 max_batch_size: int = 32,
                 batch_timeout: float = 1.0,
                 max_workers: int = 4,
                 use_multiprocessing: bool = False,
                 monitor: Optional[PerformanceMonitor] = None):
        self.max_batch_size = max_batch_size
        self.batch_timeout = batch_timeout
        self.max_workers = max_workers
        self.use_multiprocessing = use_multiprocessing
        self.monitor = monitor
        
        self.logger = logging.getLogger(__name__)
        
        # 任务队列
        self.pending_tasks: Queue = Queue()
        self.batch_queue: List[BatchTask] = []
        self.completed_tasks: Dict[str, Any] = {}
        self.task_lock = Lock()
        
        # 执行器
        if use_multiprocessing:
            self.executor = ProcessPoolExecutor(max_workers=max_workers)
        else:
            self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # 运行状态
        self.is_running = False
        self.batch_task: Optional[asyncio.Task] = None
        self.processing_lock = Lock()
        
        # 统计信息
        self.stats = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'batches_processed': 0,
            'average_batch_size': 0.0,
            'total_processing_time': 0.0
        }
        
        self.logger.info(f"批处理器初始化完成: max_batch_size={max_batch_size}, "
                        f"batch_timeout={batch_timeout}s, max_workers={max_workers}")
    
    async def start(self):
        """启动批处理器"""
        self.logger.info("启动批处理器")
        self.is_running = True
        self.batch_task = asyncio.create_task(self._batch_processing_loop())
    
    async def stop(self):
        """停止批处理器"""
        self.logger.info("停止批处理器")
        self.is_running = False
        
        if self.batch_task:
            self.batch_task.cancel()
            try:
                await self.batch_task
            except asyncio.CancelledError:
                pass
        
        # 关闭执行器
        self.executor.shutdown(wait=True)
    
    async def submit_task(self, task_id: str, data: Any, 
                         callback: Optional[Callable] = None,
                         metadata: Optional[Dict] = None) -> BatchTask:
        """提交任务"""
        task = BatchTask(
            task_id=task_id,
            data=data,
            callback=callback,
            metadata=metadata
        )
        
        self.pending_tasks.put(task)
        self.stats['total_tasks'] += 1
        
        self.logger.debug(f"任务已提交: {task_id}")
        return task
    
    async def get_result(self, task_id: str, timeout: Optional[float] = None) -> Any:
        """获取任务结果"""
        start_time = time.time()
        
        while True:
            with self.task_lock:
                if task_id in self.completed_tasks:
                    result = self.completed_tasks[task_id]
                    del self.completed_tasks[task_id]
                    return result
            
            if timeout and (time.time() - start_time) > timeout:
                raise TimeoutError(f"任务 {task_id} 超时")
            
            await asyncio.sleep(0.1)
    
    async def _batch_processing_loop(self):
        """批处理循环"""
        while self.is_running:
            try:
                # 收集任务直到达到批次大小或超时
                await self._collect_batch()
                
                # 处理批次
                if self.batch_queue:
                    await self._process_batch()
                
                await asyncio.sleep(0.1)  # 避免过度循环
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"批处理循环异常: {e}")
                await asyncio.sleep(0.5)
    
    async def _collect_batch(self):
        """收集批次任务"""
        batch_start_time = time.time()
        
        while (len(self.batch_queue) < self.max_batch_size and 
               (time.time() - batch_start_time) < self.batch_timeout):
            
            try:
                # 非阻塞方式获取任务
                task = self.pending_tasks.get_nowait()
                self.batch_queue.append(task)
            except Empty:
                # 队列为空，等待一小段时间
                if self.batch_queue:  # 如果已有任务，继续收集
                    await asyncio.sleep(0.01)
                    break
                else:  # 如果没有任务，等待新任务
                    try:
                        task = await asyncio.wait_for(
                            asyncio.get_event_loop().run_in_executor(
                                None, self.pending_tasks.get
                            ),
                            timeout=0.1
                        )
                        self.batch_queue.append(task)
                    except asyncio.TimeoutError:
                        break
    
    async def _process_batch(self):
        """处理批次"""
        if not self.batch_queue:
            return
        
        batch = self.batch_queue.copy()
        self.batch_queue.clear()
        
        batch_start_time = time.time()
        batch_size = len(batch)
        
        self.logger.debug(f"开始处理批次: {batch_size} 个任务")
        
        try:
            # 并行处理批次中的所有任务
            tasks = [self._process_single_task(task) for task in batch]
            await asyncio.gather(*tasks, return_exceptions=True)
            
            # 更新统计信息
            self.stats['batches_processed'] += 1
            processing_time = time.time() - batch_start_time
            self.stats['total_processing_time'] += processing_time
            
            # 计算平均批次大小
            if self.stats['batches_processed'] > 0:
                self.stats['average_batch_size'] = (
                    (self.stats['average_batch_size'] * (self.stats['batches_processed'] - 1) + batch_size) 
                    / self.stats['batches_processed']
                )
            
            self.logger.debug(f"批次处理完成: {batch_size} 个任务，耗时 {processing_time:.3f}s")
            
        except Exception as e:
            self.logger.error(f"批次处理失败: {e}")
            # 将失败的任务放回队列
            for task in batch:
                self.pending_tasks.put(task)
    
    async def _process_single_task(self, task: BatchTask):
        """处理单个任务"""
        task_start_time = time.time()
        
        try:
            # 记录任务开始
            if self.monitor:
                self.monitor.record_component_performance(
                    f"batch_task_{task.task_id}", 0, True
                )
            
            # 执行任务处理
            if hasattr(asyncio, 'iscoroutine_function') and asyncio.iscoroutine_function(task.callback):
                result = await task.callback(task.data)
            else:
                result = await asyncio.get_event_loop().run_in_executor(
                    self.executor,
                    lambda: task.callback(task.data) if task.callback else task.data
                )
            
            # 存储结果
            with self.task_lock:
                self.completed_tasks[task.task_id] = result
                self.stats['completed_tasks'] += 1
            
            processing_time = time.time() - task_start_time
            
            # 记录性能指标
            if self.monitor:
                self.monitor.record_component_performance(
                    f"batch_task_{task.task_id}", processing_time, True
                )
            
            self.logger.debug(f"任务完成: {task.task_id}, 耗时 {processing_time:.3f}s")
            
        except Exception as e:
            processing_time = time.time() - task_start_time
            
            # 存储错误信息
            with self.task_lock:
                self.completed_tasks[task.task_id] = e
                self.stats['failed_tasks'] += 1
            
            # 记录性能指标
            if self.monitor:
                self.monitor.record_component_performance(
                    f"batch_task_{task.task_id}", processing_time, False, str(e)
                )
            
            self.logger.error(f"任务失败: {task.task_id}, 错误: {e}")


class EmbeddingBatchProcessor(BatchProcessor):
    """专门的向量化批处理器"""
    
    def __init__(self, embedding_engine, monitor: Optional[PerformanceMonitor] = None, **kwargs):
        super().__init__(monitor=monitor, **kwargs)
        self.embedding_engine = embedding_engine
        
        self.logger.info("向量化批处理器初始化完成")
    
    async def batch_embed_images(self, image_data_list: List[bytes]) -> List:
        """批量图像向量化"""
        tasks = []
        
        for i, image_data in enumerate(image_data_list):
            task_id = f"image_embed_{i}_{time.time()}"
            task = await self.submit_task(
                task_id=task_id,
                data=image_data,
                callback=self.embedding_engine.embed_image
            )
            tasks.append((task_id, task))
        
        # 等待所有任务完成
        results = []
        for task_id, task in tasks:
            try:
                result = await self.get_result(task_id, timeout=30)
                results.append(result)
            except Exception as e:
                self.logger.error(f"图像向量化任务失败: {task_id}, 错误: {e}")
                results.append(None)
        
        return results
    
    async def batch_embed_texts(self, texts: List[str], modality: str = "visual") -> List:
        """批量文本向量化"""
        tasks = []
        
        for i, text in enumerate(texts):
            task_id = f"text_embed_{i}_{time.time()}"
            
            if modality == "visual":
                callback = self.embedding_engine.embed_text_for_visual
            elif modality == "music":
                callback = self.embedding_engine.embed_text_for_music
            else:
                raise ValueError(f"不支持的模态类型: {modality}")
            
            task = await self.submit_task(
                task_id=task_id,
                data=text,
                callback=callback
            )
            tasks.append((task_id, task))
        
        # 等待所有任务完成
        results = []
        for task_id, task in tasks:
            try:
                result = await self.get_result(task_id, timeout=30)
                results.append(result)
            except Exception as e:
                self.logger.error(f"文本向量化任务失败: {task_id}, 错误: {e}")
                results.append(None)
        
        return results
    
    async def batch_embed_audio(self, audio_data_list: List[bytes]) -> List:
        """批量音频向量化"""
        tasks = []
        
        for i, audio_data in enumerate(audio_data_list):
            task_id = f"audio_embed_{i}_{time.time()}"
            task = await self.submit_task(
                task_id=task_id,
                data=audio_data,
                callback=self.embedding_engine.embed_audio_music
            )
            tasks.append((task_id, task))
        
        # 等待所有任务完成
        results = []
        for task_id, task in tasks:
            try:
                result = await self.get_result(task_id, timeout=60)
                results.append(result)
            except Exception as e:
                self.logger.error(f"音频向量化任务失败: {task_id}, 错误: {e}")
                results.append(None)
        
        return results
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """获取处理统计信息"""
        base_stats = self.stats.copy()
        
        # 添加向量化特定统计
        if self.monitor:
            component_metrics = self.monitor.get_component_metrics()
            embedding_stats = {}
            
            for component_name, metrics in component_metrics.items():
                if 'embed' in component_name:
                    embedding_stats[component_name] = metrics
            
            base_stats['embedding_components'] = embedding_stats
        
        return base_stats


class DatabaseBatchProcessor(BatchProcessor):
    """专门的数据库批处理器"""
    
    def __init__(self, database_adapter, monitor: Optional[PerformanceMonitor] = None, **kwargs):
        super().__init__(monitor=monitor, **kwargs)
        self.database_adapter = database_adapter
        
        self.logger.info("数据库批处理器初始化完成")
    
    async def batch_insert_files(self, file_info_list: List[Dict]) -> List[str]:
        """批量插入文件记录"""
        tasks = []
        
        for i, file_info in enumerate(file_info_list):
            task_id = f"file_insert_{i}_{time.time()}"
            task = await self.submit_task(
                task_id=task_id,
                data=file_info,
                callback=self.database_adapter.insert_file
            )
            tasks.append((task_id, task))
        
        # 等待所有任务完成
        results = []
        for task_id, task in tasks:
            try:
                result = await self.get_result(task_id, timeout=30)
                results.append(result)
            except Exception as e:
                self.logger.error(f"文件插入任务失败: {task_id}, 错误: {e}")
                results.append(None)
        
        return results
    
    async def batch_update_files(self, file_updates: List[tuple]) -> List[bool]:
        """批量更新文件记录"""
        tasks = []
        
        for i, (file_id, updates) in enumerate(file_updates):
            task_id = f"file_update_{i}_{time.time()}"
            task = await self.submit_task(
                task_id=task_id,
                data=(file_id, updates),
                callback=lambda x: self.database_adapter.update_file(*x)
            )
            tasks.append((task_id, task))
        
        # 等待所有任务完成
        results = []
        for task_id, task in tasks:
            try:
                result = await self.get_result(task_id, timeout=30)
                results.append(result)
            except Exception as e:
                self.logger.error(f"文件更新任务失败: {task_id}, 错误: {e}")
                results.append(False)
        
        return results