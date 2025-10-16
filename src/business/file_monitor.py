"""
文件监控服务模块
基于Watchdog实现文件系统监控，自动发现并处理新增的媒体文件
"""

import os
import time
from pathlib import Path
from typing import List, Callable, Dict, Any
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

from src.core.config import get_config
from src.core.logging_config import get_logger
from src.core.db_adapter import get_db_adapter

logger = get_logger(__name__)


class FileMonitorHandler(FileSystemEventHandler):
    """文件监控事件处理器"""
    
    def __init__(self, callback: Callable[[str, str], None]):
        """
        初始化文件监控事件处理器
        
        Args:
            callback: 文件事件回调函数，参数为(文件路径, 事件类型)
        """
        self.callback = callback
        super().__init__()
    
    def on_created(self, event: FileSystemEvent):
        """处理文件创建事件"""
        if not event.is_directory:
            logger.info(f"检测到新文件: {event.src_path}")
            self.callback(event.src_path, "created")
    
    def on_modified(self, event: FileSystemEvent):
        """处理文件修改事件"""
        if not event.is_directory:
            logger.info(f"检测到文件修改: {event.src_path}")
            self.callback(event.src_path, "modified")
    
    def on_moved(self, event: FileSystemEvent):
        """处理文件移动事件"""
        if not event.is_directory:
            logger.info(f"检测到文件移动: {event.src_path} -> {event.dest_path}")
            self.callback(event.dest_path, "moved")
    
    def on_deleted(self, event: FileSystemEvent):
        """处理文件删除事件"""
        if not event.is_directory:
            logger.info(f"检测到文件删除: {event.src_path}")
            self.callback(event.src_path, "deleted")


class FileSystemMonitor:
    """文件系统监控器"""
    
    def __init__(self):
        """初始化文件系统监控器"""
        self.config = get_config()
        self.watch_directories = self.config.get("paths", {}).get("watch_directories", ["./testdata"])
        self.observer = Observer()
        self.db_adapter = get_db_adapter()
        self.is_running = False
        logger.info("文件系统监控器初始化完成")
    
    def start_monitoring(self):
        """开始监控"""
        if self.is_running:
            logger.warning("文件监控器已在运行中")
            return
        
        # 创建事件处理器
        handler = FileMonitorHandler(self._handle_file_event)
        
        # 为每个监控目录添加观察者
        for directory in self.watch_directories:
            if os.path.exists(directory):
                self.observer.schedule(handler, directory, recursive=True)
                logger.info(f"开始监控目录: {directory}")
            else:
                logger.warning(f"监控目录不存在: {directory}")
        
        # 启动观察者
        self.observer.start()
        self.is_running = True
        logger.info("文件监控器已启动")
    
    def stop_monitoring(self):
        """停止监控"""
        if not self.is_running:
            logger.warning("文件监控器未在运行")
            return
        
        self.observer.stop()
        self.observer.join()
        self.is_running = False
        logger.info("文件监控器已停止")
    
    def _handle_file_event(self, file_path: str, event_type: str):
        """
        处理文件事件
        
        Args:
            file_path: 文件路径
            event_type: 事件类型 (created, modified, moved, deleted)
        """
        try:
            # 检查文件扩展名是否支持
            if self._is_supported_file(file_path):
                logger.info(f"处理文件事件: {file_path} ({event_type})")
                
                # 将文件添加到处理队列
                if event_type in ["created", "modified", "moved"]:
                    self._add_to_processing_queue(file_path)
                elif event_type == "deleted":
                    self._remove_from_processing_queue(file_path)
        except Exception as e:
            logger.error(f"处理文件事件失败: {e}")
    
    def _is_supported_file(self, file_path: str) -> bool:
        """
        检查文件是否为支持的格式
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否为支持的文件格式
        """
        supported_formats = self.config.get("system", {}).get("supported_formats", {})
        
        # 获取文件扩展名
        file_extension = Path(file_path).suffix.lower().lstrip('.')
        
        # 检查是否在支持的格式列表中
        for format_list in supported_formats.values():
            if file_extension in format_list:
                return True
        
        return False
    
    async def _add_to_processing_queue(self, file_path: str):
        """
        将文件添加到处理队列
        
        Args:
            file_path: 文件路径
        """
        try:
            # 检查文件是否已经在队列中
            existing_files = await self._get_files_in_queue()
            if file_path in existing_files:
                logger.info(f"文件已在处理队列中: {file_path}")
                return
            
            # 添加到处理队列
            queue_id = await self.db_adapter.add_file_to_queue(file_path)
            logger.info(f"文件已添加到处理队列: {file_path} (队列ID: {queue_id})")
        except Exception as e:
            logger.error(f"添加文件到处理队列失败: {e}")
    
    async def _remove_from_processing_queue(self, file_path: str):
        """
        从处理队列中移除文件
        
        Args:
            file_path: 文件路径
        """
        try:
            # 这里应该从数据库中删除相关的队列记录
            # 暂时只记录日志
            logger.info(f"文件已从处理队列中移除: {file_path}")
        except Exception as e:
            logger.error(f"从处理队列移除文件失败: {e}")
    
    async def _get_files_in_queue(self) -> List[str]:
        """
        获取处理队列中的所有文件
        
        Returns:
            文件路径列表
        """
        try:
            # 查询数据库获取处理队列中的文件
            query = "SELECT file_path FROM processing_queue WHERE status IN ('queued', 'processing')"
            results = self.db_adapter.db_manager.execute_query(query)
            return [row["file_path"] for row in results]
        except Exception as e:
            logger.error(f"获取处理队列文件列表失败: {e}")
            return []
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """
        获取监控状态
        
        Returns:
            监控状态信息
        """
        return {
            "is_running": self.is_running,
            "watched_directories": self.watch_directories,
            "supported_formats": self.config.get("system", {}).get("supported_formats", {})
        }


# 全局文件监控器实例
_file_monitor = None


def get_file_monitor() -> FileSystemMonitor:
    """
    获取全局文件监控器实例
    
    Returns:
        文件监控器实例
    """
    global _file_monitor
    if _file_monitor is None:
        _file_monitor = FileSystemMonitor()
    return _file_monitor