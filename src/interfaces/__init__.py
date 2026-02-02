# -*- coding: utf-8 -*-
"""
抽象接口定义模块

定义核心业务组件的抽象接口，实现进程边界解耦。
所有业务逻辑依赖这些抽象接口，而不是具体实现。
"""

# 直接导入接口类
from .embedding_interface import EmbeddingEngine as EmbeddingEngineInterface
from .storage_interface import (
    VectorStore as VectorStoreInterface,
    DatabaseManager as DatabaseInterface,
)
from .search_interface import SearchEngine as SearchEngineInterface
from .indexer_interface import FileIndexer as FileIndexerInterface
from .task_interface import (
    TaskManagerInterface,
    TaskSchedulerInterface,
    TaskExecutorInterface,
    TaskMonitorInterface,
    TaskGroupManagerInterface,
)

__all__ = [
    # 向量化接口
    "EmbeddingEngineInterface",
    # 存储接口
    "VectorStoreInterface",
    "DatabaseInterface",
    # 搜索接口
    "SearchEngineInterface",
    # 索引接口
    "FileIndexerInterface",
    # 任务管理接口
    "TaskManagerInterface",
    "TaskSchedulerInterface",
    "TaskExecutorInterface",
    "TaskMonitorInterface",
    "TaskGroupManagerInterface",
]
