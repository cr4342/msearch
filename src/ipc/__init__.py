"""
进程间通信模块

提供SQLite队列 + Unix Socket/Named Pipe + 共享内存的进程间通信方案
替代Redis，更适合桌面应用
"""

from .sqlite_ipc import (
    IPCBase,
    SQLiteIPC,
    LocalIPC,
    LRUCache,
    MainProcessIPC,
    FileMonitorIPC,
    EmbeddingWorkerIPC,
    TaskWorkerIPC
)

# 为了向后兼容，保留RedisIPC的导入，但标记为已弃用
try:
    from .redis_ipc import (
        IPCBase as RedisIPCBase,
        RedisIPC,
        MainProcessIPC as RedisMainProcessIPC,
        FileMonitorIPC as RedisFileMonitorIPC,
        EmbeddingWorkerIPC as RedisEmbeddingWorkerIPC,
        TaskWorkerIPC as RedisTaskWorkerIPC
    )
    import warnings
    warnings.warn(
        "Redis IPC is deprecated. Use SQLiteIPC instead.",
        DeprecationWarning,
        stacklevel=2
    )
except ImportError:
    pass

__all__ = [
    # SQLite IPC (推荐)
    "IPCBase",
    "SQLiteIPC",
    "LocalIPC",
    "LRUCache",
    "MainProcessIPC",
    "FileMonitorIPC",
    "EmbeddingWorkerIPC",
    "TaskWorkerIPC",
]
