"""
文件监控服务 - 实时监控指定目录的文件变化，触发索引处理流程
"""
import os
import time
from typing import Dict, Any, List, Callable
from pathlib import Path
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logger = logging.getLogger(__name__)


class FileMonitorHandler(FileSystemEventHandler):
    """文件监控事件处理器"""
    
    def __init__(self, callback: Callable[[str, str], None], config: Dict[str, Any]):
        """
        初始化事件处理器
        
        Args:
            callback: 文件变化回调函数
            config: 配置字典
        """
        self.callback = callback
        self.config = config
        self.file_extensions = config.get('file_monitoring.file_extensions', {
            'image': ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp'],
            'video': ['.mp4', '.avi', '.mov', '.mkv', '.webm'],
            'audio': ['.mp3', '.wav', '.ogg', '.flac', '.aac'],
            'text': ['.txt', '.md', '.csv', '.json', '.xml']
        })
        
        # 所有支持的扩展名
        self.supported_extensions = set()
        for extensions in self.file_extensions.values():
            self.supported_extensions.update(extensions)
    
    def on_deleted(self, event):
        """处理文件删除事件"""
        if not event.is_directory:
            self._handle_file_event(event.src_path, "deleted")
    
    def on_created(self, event):
        """处理文件创建事件"""
        if not event.is_directory:
            self._handle_file_event(event.src_path, "created")
    
    def on_modified(self, event):
        """处理文件修改事件"""
        if not event.is_directory:
            self._handle_file_event(event.src_path, "modified")
    
    def on_moved(self, event):
        """处理文件移动事件"""
        if not event.is_directory:
            self._handle_file_event(event.dest_path, "moved")
    
    def _handle_file_event(self, file_path: str, event_type: str):
        """
        处理文件事件
        
        Args:
            file_path: 文件路径
            event_type: 事件类型
        """
        try:
            # 检查文件扩展名是否受支持
            extension = Path(file_path).suffix.lower()
            if extension not in self.supported_extensions:
                return
            
            # 对于删除事件，不需要检查文件是否准备就绪
            if event_type != "deleted":
                # 检查文件是否完全写入
                if not self._is_file_ready(file_path):
                    # 等待文件准备就绪
                    time.sleep(1)
                    if not self._is_file_ready(file_path):
                        logger.warning(f"文件未准备就绪，跳过处理: {file_path}")
                        return
            
            logger.debug(f"检测到文件变化: {file_path}, 事件类型: {event_type}")
            
            # 调用回调函数
            if self.callback:
                self.callback(file_path, event_type)
                
        except Exception as e:
            logger.error(f"处理文件事件失败: {file_path}, 错误: {e}")
    
    def _is_file_ready(self, file_path: str) -> bool:
        """
        检查文件是否准备就绪(完全写入)
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件是否准备就绪
        """
        try:
            # 尝试打开文件进行读取，如果成功则文件已准备就绪
            with open(file_path, 'rb') as f:
                f.read(1)
            return True
        except:
            return False


class FileMonitor:
    """文件监控服务"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化文件监控服务
        
        Args:
            config: 配置字典
        """
        self.config = config
        # 使用嵌套键访问配置
        general_config = config.get('general', {})
        self.directories = general_config.get('watch_directories', [])
        self.observer = Observer()
        self.handlers = {}
        self.callbacks = []
        
        logger.info("文件监控服务初始化完成")
    
    def add_callback(self, callback: Callable[[str, str], None]):
        """
        添加文件变化回调函数
        
        Args:
            callback: 回调函数，接收文件路径和事件类型作为参数
        """
        self.callbacks.append(callback)
    
    def start_monitoring(self):
        """开始监控"""
        try:
            if not self.directories:
                logger.warning("未配置监控目录")
                return
            
            # 为每个目录创建事件处理器
            for directory in self.directories:
                if not os.path.exists(directory):
                    logger.warning(f"监控目录不存在: {directory}")
                    continue
                
                # 创建事件处理器
                handler = FileMonitorHandler(self._handle_file_change, self.config)
                self.handlers[directory] = handler
                
                # 添加监控
                self.observer.schedule(handler, directory, recursive=True)
                logger.info(f"开始监控目录: {directory}")
            
            # 启动监控
            self.observer.start()
            logger.info("文件监控服务已启动")
            
        except Exception as e:
            logger.error(f"启动文件监控失败: {e}")
            raise
    
    def stop_monitoring(self):
        """停止监控"""
        try:
            self.observer.stop()
            self.observer.join()
            logger.info("文件监控服务已停止")
        except Exception as e:
            logger.error(f"停止文件监控失败: {e}")
    
    def _handle_file_change(self, file_path: str, event_type: str):
        """
        处理文件变化
        
        Args:
            file_path: 文件路径
            event_type: 事件类型
        """
        try:
            logger.debug(f"处理文件变化: {file_path}, 事件类型: {event_type}")
            
            # 调用所有回调函数
            for callback in self.callbacks:
                try:
                    callback(file_path, event_type)
                except Exception as e:
                    logger.error(f"回调函数执行失败: {e}")
                    
        except Exception as e:
            logger.error(f"处理文件变化失败: {file_path}, 错误: {e}")
    
    def get_monitored_directories(self) -> List[str]:
        """
        获取监控的目录列表
        
        Returns:
            监控目录列表
        """
        return self.directories.copy()
    
    def add_directory(self, directory: str):
        """
        添加监控目录
        
        Args:
            directory: 要监控的目录路径
        """
        if directory not in self.directories:
            self.directories.append(directory)
            
            # 如果监控已启动，添加新的监控
            if self.observer.is_alive():
                handler = FileMonitorHandler(self._handle_file_change, self.config)
                self.handlers[directory] = handler
                self.observer.schedule(handler, directory, recursive=True)
                logger.info(f"添加监控目录: {directory}")
    
    def remove_directory(self, directory: str):
        """
        移除监控目录
        
        Args:
            directory: 要移除的目录路径
        """
        if directory in self.directories:
            self.directories.remove(directory)
            
            # 如果监控已启动，移除监控
            if directory in self.handlers:
                # watchdog不直接支持移除监控，需要重启监控服务
                logger.warning("Watchdog不支持动态移除监控，如需移除目录请重启监控服务")
    
    def is_monitoring(self) -> bool:
        """
        检查监控是否正在运行
        
        Returns:
            监控是否正在运行
        """
        return self.observer.is_alive()


# 示例使用
if __name__ == "__main__":
    # 配置示例
    config = {
        'general': {
            'watch_directories': ['~/Documents', '~/Pictures', '~/Videos']
        },
        'file_monitoring.file_extensions': {
            'image': ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp'],
            'video': ['.mp4', '.avi', '.mov', '.mkv', '.webm'],
            'audio': ['.mp3', '.wav', '.ogg', '.flac', '.aac'],
            'text': ['.txt', '.md', '.csv', '.json', '.xml']
        }
    }
    
    # 文件变化回调函数
    def file_change_callback(file_path: str, event_type: str):
        print(f"文件变化: {file_path}, 事件类型: {event_type}")
    
    # 创建文件监控服务
    # monitor = FileMonitor(config)
    # monitor.add_callback(file_change_callback)
    # 
    # # 启动监控
    # monitor.start_monitoring()
    # 
    # try:
    #     # 保持程序运行
    #     while True:
    #         time.sleep(1)
    # except KeyboardInterrupt:
    #     # 停止监控
    #     monitor.stop_monitoring()