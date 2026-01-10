"""
文件监控器
负责实时监控文件系统变化
"""

import os
import time
from typing import List, Dict, Any, Callable, Optional
from pathlib import Path
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)


class FileMonitorEventHandler(FileSystemEventHandler):
    """文件监控事件处理器"""
    
    def __init__(self, callback: Callable[[str, str], None], debounce_delay: float = 0.5):
        """
        初始化事件处理器
        
        Args:
            callback: 文件变化回调函数
            debounce_delay: 防抖延迟（秒）
        """
        super().__init__()
        self.callback = callback
        self.debounce_delay = debounce_delay
        self.pending_events: Dict[str, float] = {}
    
    def on_created(self, event: FileSystemEvent) -> None:
        """文件创建事件"""
        if not event.is_directory:
            self._schedule_event(event.src_path, 'created')
    
    def on_modified(self, event: FileSystemEvent) -> None:
        """文件修改事件"""
        if not event.is_directory:
            self._schedule_event(event.src_path, 'modified')
    
    def on_deleted(self, event: FileSystemEvent) -> None:
        """文件删除事件"""
        if not event.is_directory:
            self._schedule_event(event.src_path, 'deleted')
    
    def on_moved(self, event: FileSystemEvent) -> None:
        """文件移动事件"""
        if not event.is_directory:
            self._schedule_event(event.src_path, 'moved')
            self._schedule_event(event.dest_path, 'created')
    
    def _schedule_event(self, file_path: str, event_type: str) -> None:
        """
        调度事件（防抖）
        
        Args:
            file_path: 文件路径
            event_type: 事件类型
        """
        event_key = f"{file_path}:{event_type}"
        now = time.time()
        
        # 检查是否已有待处理事件
        if event_key in self.pending_events:
            # 更新时间戳（防抖）
            self.pending_events[event_key] = now
        else:
            # 添加新事件
            self.pending_events[event_key] = now
    
    def process_pending_events(self) -> None:
        """处理待处理事件"""
        now = time.time()
        to_process = []
        
        # 找出需要处理的事件
        for event_key, timestamp in list(self.pending_events.items()):
            if now - timestamp >= self.debounce_delay:
                to_process.append(event_key)
        
        # 处理事件
        for event_key in to_process:
            file_path, event_type = event_key.rsplit(':', 1)
            try:
                self.callback(file_path, event_type)
            except Exception as e:
                logger.error(f"处理文件事件失败: {file_path}, {event_type}, {e}")
            
            # 从待处理列表中移除
            del self.pending_events[event_key]


class FileMonitor:
    """文件监控器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化文件监控器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.observer: Optional[Observer] = None
        self.event_handlers: Dict[str, FileMonitorEventHandler] = {}
        self.watch_paths: List[str] = []
        self.is_running = False
        self.check_interval = config.get('check_interval', 5)
        self.debounce_delay = config.get('debounce_delay', 500) / 1000.0
    
    def start(self) -> bool:
        """
        启动文件监控
        
        Returns:
            是否成功启动
        """
        try:
            if self.is_running:
                logger.warning("文件监控已在运行")
                return True
            
            # 创建观察者
            self.observer = Observer()
            
            # 添加监控路径
            monitoring_dirs = self.config.get('directories', [])
            for dir_config in monitoring_dirs:
                dir_path = dir_config.get('path')
                if dir_path and os.path.exists(dir_path):
                    self.add_watch_path(dir_path, dir_config.get('recursive', True))
            
            # 启动观察者
            self.observer.start()
            self.is_running = True
            
            logger.info(f"文件监控启动成功，监控路径: {self.watch_paths}")
            return True
        except Exception as e:
            logger.error(f"文件监控启动失败: {e}")
            return False
    
    def stop(self) -> None:
        """停止文件监控"""
        if self.observer and self.is_running:
            self.observer.stop()
            self.observer.join()
            self.is_running = False
            logger.info("文件监控已停止")
    
    def add_watch_path(self, path: str, recursive: bool = True) -> bool:
        """
        添加监控路径
        
        Args:
            path: 监控路径
            recursive: 是否递归监控
        
        Returns:
            是否成功添加
        """
        try:
            if not os.path.exists(path):
                logger.warning(f"监控路径不存在: {path}")
                return False
            
            # 创建事件处理器
            event_handler = FileMonitorEventHandler(
                callback=self._on_file_event,
                debounce_delay=self.debounce_delay
            )
            
            # 添加监控
            self.observer.schedule(event_handler, path, recursive=recursive)
            self.event_handlers[path] = event_handler
            self.watch_paths.append(path)
            
            logger.info(f"添加监控路径: {path}, 递归: {recursive}")
            return True
        except Exception as e:
            logger.error(f"添加监控路径失败: {path}, {e}")
            return False
    
    def remove_watch_path(self, path: str) -> bool:
        """
        移除监控路径
        
        Args:
            path: 监控路径
        
        Returns:
            是否成功移除
        """
        try:
            if path in self.event_handlers:
                # Watchdog不支持直接移除单个监控，需要重启
                logger.warning(f"移除监控路径需要重启: {path}")
                return False
            
            if path in self.watch_paths:
                self.watch_paths.remove(path)
                logger.info(f"移除监控路径: {path}")
                return True
            
            return False
        except Exception as e:
            logger.error(f"移除监控路径失败: {path}, {e}")
            return False
    
    def _on_file_event(self, file_path: str, event_type: str) -> None:
        """
        文件事件回调
        
        Args:
            file_path: 文件路径
            event_type: 事件类型
        """
        try:
            logger.info(f"文件事件: {event_type}, {file_path}")
            
            # 检查文件类型
            if not self._is_supported_file(file_path):
                return
            
            # 处理文件事件
            if event_type == 'created':
                self._handle_file_created(file_path)
            elif event_type == 'modified':
                self._handle_file_modified(file_path)
            elif event_type == 'deleted':
                self._handle_file_deleted(file_path)
            elif event_type == 'moved':
                self._handle_file_moved(file_path)
        
        except Exception as e:
            logger.error(f"处理文件事件失败: {file_path}, {event_type}, {e}")
    
    def _is_supported_file(self, file_path: str) -> bool:
        """
        检查文件是否为支持的类型
        
        Args:
            file_path: 文件路径
        
        Returns:
            是否支持
        """
        # 获取支持的格式
        supported_formats = []
        processing_config = self.config.get('processing', {})
        
        if 'image' in processing_config:
            supported_formats.extend(processing_config['image'].get('supported_formats', []))
        if 'video' in processing_config:
            supported_formats.extend(processing_config['video'].get('supported_formats', []))
        if 'audio' in processing_config:
            supported_formats.extend(processing_config['audio'].get('supported_formats', []))
        
        # 检查文件扩展名
        file_ext = Path(file_path).suffix.lower().lstrip('.')
        return file_ext in supported_formats
    
    def _handle_file_created(self, file_path: str) -> None:
        """
        处理文件创建事件
        
        Args:
            file_path: 文件路径
        """
        logger.info(f"检测到新文件: {file_path}")
        # TODO: 创建索引任务
        pass
    
    def _handle_file_modified(self, file_path: str) -> None:
        """
        处理文件修改事件
        
        Args:
            file_path: 文件路径
        """
        logger.info(f"检测到文件修改: {file_path}")
        # TODO: 更新索引任务
        pass
    
    def _handle_file_deleted(self, file_path: str) -> None:
        """
        处理文件删除事件
        
        Args:
            file_path: 文件路径
        """
        logger.info(f"检测到文件删除: {file_path}")
        # TODO: 删除索引任务
        pass
    
    def _handle_file_moved(self, file_path: str) -> None:
        """
        处理文件移动事件
        
        Args:
            file_path: 文件路径
        """
        logger.info(f"检测到文件移动: {file_path}")
        # TODO: 更新索引路径
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取监控状态
        
        Returns:
            状态字典
        """
        return {
            'is_running': self.is_running,
            'watch_paths': self.watch_paths,
            'check_interval': self.check_interval,
            'debounce_delay': self.debounce_delay
        }
    
    def process_pending_events(self) -> None:
        """处理所有待处理事件"""
        for event_handler in self.event_handlers.values():
            event_handler.process_pending_events()