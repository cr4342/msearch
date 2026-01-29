"""
线程池管理器

管理三个主要线程池：
1. Embedding Pool: 向量化任务
2. I/O Pool: 文件读写、数据库操作
3. Task Pool: 预处理任务
"""

import logging
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Callable, Dict, Any, Optional
import threading
import queue

logger = logging.getLogger(__name__)


class ThreadPoolManager:
    """线程池管理器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化线程池管理器
        
        Args:
            config: 线程池配置
                {
                    "embedding": {"min_workers": 1, "max_workers": 4, "queue_size": 100, "task_timeout": 300},
                    "io": {"min_workers": 4, "max_workers": 8, "queue_size": 200, "task_timeout": 60},
                    "task": {"min_workers": 4, "max_workers": 8, "queue_size": 200, "task_timeout": 120}
                }
        """
        self.config = config
        self.pools: Dict[str, ThreadPoolExecutor] = {}
        self.task_queues: Dict[str, queue.Queue] = {}
        self.running = False
        self._lock = threading.Lock()
        self._init_pools()
        
    def _init_pools(self):
        """初始化线程池"""
        logger.info("初始化线程池管理器...")
        
        # 向量化线程池
        if 'embedding' in self.config:
            embedding_config = self.config['embedding']
            self.pools['embedding'] = ThreadPoolExecutor(
                max_workers=embedding_config.get('max_workers', 4),
                thread_name_prefix='EmbeddingWorker'
            )
            self.task_queues['embedding'] = queue.Queue(
                maxsize=embedding_config.get('queue_size', 100)
            )
            logger.info(f"Embedding Pool 初始化: max_workers={embedding_config.get('max_workers', 4)}, "
                       f"queue_size={embedding_config.get('queue_size', 100)}")
        
        # I/O线程池
        if 'io' in self.config:
            io_config = self.config['io']
            self.pools['io'] = ThreadPoolExecutor(
                max_workers=io_config.get('max_workers', 8),
                thread_name_prefix='IOWorker'
            )
            self.task_queues['io'] = queue.Queue(
                maxsize=io_config.get('queue_size', 200)
            )
            logger.info(f"I/O Pool 初始化: max_workers={io_config.get('max_workers', 8)}, "
                       f"queue_size={io_config.get('queue_size', 200)}")
        
        # 任务线程池
        if 'task' in self.config:
            task_config = self.config['task']
            self.pools['task'] = ThreadPoolExecutor(
                max_workers=task_config.get('max_workers', 8),
                thread_name_prefix='TaskWorker'
            )
            self.task_queues['task'] = queue.Queue(
                maxsize=task_config.get('queue_size', 200)
            )
            logger.info(f"Task Pool 初始化: max_workers={task_config.get('max_workers', 8)}, "
                       f"queue_size={task_config.get('queue_size', 200)}")
        
        self.running = True
        logger.info("线程池管理器初始化完成")
    
    def submit_task(self, pool_name: str, task: Callable, *args, **kwargs) -> Future:
        """
        提交任务到指定线程池
        
        Args:
            pool_name: 线程池名称 (embedding/io/task)
            task: 要执行的任务函数
            *args: 任务参数
            **kwargs: 任务关键字参数
            
        Returns:
            Future对象
            
        Raises:
            ValueError: 未知的线程池名称
        """
        if not self.running:
            raise RuntimeError("线程池管理器已停止")
            
        with self._lock:
            pool = self.pools.get(pool_name)
            if not pool:
                raise ValueError(f"未知的线程池: {pool_name}")
            
            future = pool.submit(task, *args, **kwargs)
            logger.debug(f"任务已提交到 {pool_name} 线程池")
            return future
    
    def get_pool_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有线程池的统计信息
        
        Returns:
            线程池统计信息字典
        """
        stats = {}
        with self._lock:
            for name, pool in self.pools.items():
                stats[name] = {
                    'max_workers': pool._max_workers,
                    'thread_count': pool._threads.__len__() if hasattr(pool, '_threads') else 0,
                    'pending_tasks': pool._work_queue.qsize() if hasattr(pool, '_work_queue') else 0
                }
        return stats
    
    def shutdown(self, wait: bool = True):
        """
        关闭所有线程池
        
        Args:
            wait: 是否等待所有任务完成
        """
        logger.info("正在关闭线程池管理器...")
        self.running = False
        
        with self._lock:
            for name, pool in self.pools.items():
                logger.info(f"关闭 {name} 线程池...")
                pool.shutdown(wait=wait)
            
            self.pools.clear()
            self.task_queues.clear()
        
        logger.info("线程池管理器已关闭")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown(wait=True)
        return False