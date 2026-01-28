import os
import sys
import logging
import time
import threading
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FileMonitor:
    """
    文件监控器
    
    负责在后台实时监控文件变化并通知文件索引器
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化文件监控器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.monitored_directories = set()
        self.is_running = False
        self.monitor_threads = []
        self.event_handlers = {
            'created': [],
            'modified': [],
            'deleted': []
        }
        
        # 保存文件状态，用于检测变化
        self.file_states = {}
        
        # 监控配置
        self.monitor_interval = config.get('processing', {}).get('monitor_interval', 1.0)
        self.ignore_patterns = config.get('processing', {}).get('ignore_patterns', ['.*', '__pycache__', '*.swp', '*.tmp'])
        
        # 文件索引器
        self.file_indexer = None
        
        # 文件扫描器（用于批量扫描）
        self.file_scanner = None
        
        # 统计信息
        self.stats = {
            "monitored_directories": 0,
            "events_triggered": {
                "created": 0,
                "modified": 0,
                "deleted": 0
            }
        }
        
        logger.info("FileMonitor initialized")
    
    def set_file_indexer(self, file_indexer: Any) -> None:
        """
        设置文件索引器
        
        Args:
            file_indexer: 文件索引器实例
        """
        self.file_indexer = file_indexer
    
    def set_file_scanner(self, file_scanner: Any) -> None:
        """
        设置文件扫描器
        
        Args:
            file_scanner: 文件扫描器实例
        """
        self.file_scanner = file_scanner
    
    def initialize(self) -> bool:
        """
        初始化文件监控器
        
        Returns:
            是否初始化成功
        """
        try:
            logger.info("FileMonitor initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize FileMonitor: {e}")
            return False
    
    def start_monitoring(self) -> bool:
        """
        开始监控
        
        Returns:
            是否启动成功
        """
        if self.is_running:
            logger.warning("FileMonitor is already running")
            return False
        
        self.is_running = True
        
        # 启动监控线程
        thread = threading.Thread(target=self._monitor_loop, name="FileMonitor")
        thread.daemon = True
        thread.start()
        self.monitor_threads.append(thread)
        
        logger.info("FileMonitor started")
        return True
    
    def stop_monitoring(self) -> bool:
        """
        停止监控
        
        Returns:
            是否停止成功
        """
        if not self.is_running:
            logger.warning("FileMonitor is not running")
            return False
        
        self.is_running = False
        
        # 等待监控线程退出
        for thread in self.monitor_threads:
            if thread.is_alive():
                thread.join(timeout=5.0)
        
        self.monitor_threads.clear()
        logger.info("FileMonitor stopped")
        return True
    
    def add_directory(self, directory_path: str) -> bool:
        """
        添加监控目录
        
        Args:
            directory_path: 目录路径
        
        Returns:
            是否添加成功
        """
        try:
            # 检查目录是否存在
            if not os.path.exists(directory_path):
                logger.error(f"Directory not found: {directory_path}")
                return False
            
            # 检查目录是否已经被监控
            if directory_path in self.monitored_directories:
                logger.warning(f"Directory already monitored: {directory_path}")
                return False
            
            # 添加目录到监控列表
            self.monitored_directories.add(directory_path)
            logger.info(f"Added directory to monitor: {directory_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to add directory: {e}")
            return False
    
    def remove_directory(self, directory_path: str) -> bool:
        """
        移除监控目录
        
        Args:
            directory_path: 目录路径
        
        Returns:
            是否移除成功
        """
        try:
            if directory_path in self.monitored_directories:
                self.monitored_directories.remove(directory_path)
                logger.info(f"Removed directory from monitor: {directory_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to remove directory: {e}")
            return False
    
    def get_monitored_directories(self) -> List[str]:
        """
        获取所有监控目录
        
        Returns:
            监控目录列表
        """
        return list(self.monitored_directories)
    
    def register_event_handler(self, event_type: str, handler: Callable[[str, str], None]) -> None:
        """
        注册事件处理器
        
        Args:
            event_type: 事件类型
            handler: 事件处理函数
        """
        if event_type in self.event_handlers:
            self.event_handlers[event_type].append(handler)
            logger.info(f"Registered {event_type} event handler")
    
    def unregister_event_handler(self, event_type: str, handler: Callable[[str, str], None]) -> None:
        """
        取消注册事件处理器
        
        Args:
            event_type: 事件类型
            handler: 事件处理函数
        """
        if event_type in self.event_handlers and handler in self.event_handlers[event_type]:
            self.event_handlers[event_type].remove(handler)
            logger.info(f"Unregistered {event_type} event handler")
    
    def _monitor_loop(self) -> None:
        """
        监控循环
        """
        while self.is_running:
            try:
                # 检查所有监控目录
                for directory in self.monitored_directories:
                    self._scan_directory(directory, self.file_states)
                
                # 休眠指定时间
                time.sleep(self.monitor_interval)
            except Exception as e:
                logger.error(f"Monitor loop error: {e}")
                time.sleep(self.monitor_interval)
    
    def _scan_directory(self, directory: str, file_states: Dict[str, float]) -> None:
        """
        扫描目录并检测变化
        
        Args:
            directory: 目录路径
            file_states: 文件状态字典
        """
        try:
            # 收集所有当前文件
            all_current_files = set()
            
            # 遍历目录
            for root, dirs, files in os.walk(directory):
                # 过滤掉需要忽略的目录
                dirs[:] = [d for d in dirs if not self._should_ignore(d)]
                
                # 检查文件
                for file in files:
                    if self._should_ignore(file):
                        continue
                    
                    file_path = os.path.join(root, file)
                    all_current_files.add(file_path)
                    
                    # 检查文件变化
                    self._check_file_change(file_path, file_states)
            
            # 检查已删除的文件（在所有文件检查完成后）
            self._check_deleted_files(directory, all_current_files, file_states)
        except Exception as e:
            logger.error(f"Failed to scan directory {directory}: {e}")
    
    def _should_ignore(self, name: str) -> bool:
        """
        判断是否需要忽略该文件或目录
        
        Args:
            name: 文件或目录名称
        
        Returns:
            是否需要忽略
        """
        import fnmatch
        
        for pattern in self.ignore_patterns:
            if fnmatch.fnmatch(name, pattern):
                return True
        return False
    
    def _check_file_change(self, file_path: str, file_states: Dict[str, float]) -> None:
        """
        检查文件变化
        
        Args:
            file_path: 文件路径
            file_states: 文件状态字典
        """
        try:
            # 获取文件修改时间
            mtime = os.path.getmtime(file_path)
            
            if file_path not in file_states:
                # 新文件
                self._on_file_created(file_path)
            elif mtime != file_states[file_path]:
                # 文件被修改
                self._on_file_modified(file_path)
            
            # 更新文件状态
            file_states[file_path] = mtime
        except Exception as e:
            logger.error(f"Failed to check file change {file_path}: {e}")
    
    def _check_deleted_files(self, directory: str, current_files: set, file_states: Dict[str, float]) -> None:
        """
        检查已删除的文件
        
        Args:
            directory: 目录路径
            current_files: 当前文件集合
            file_states: 文件状态字典
        """
        # 检查所有文件状态中的文件
        for file_path in list(file_states.keys()):
            # 如果文件在当前目录且不在当前文件集合中，则认为已删除
            if file_path.startswith(directory) and file_path not in current_files:
                self._on_file_deleted(file_path)
                # 从文件状态中移除
                del file_states[file_path]
    
    def _on_file_created(self, file_path: str) -> None:
        """
        文件创建事件
        
        Args:
            file_path: 文件路径
        """
        logger.info(f"File created: {file_path}")
        
        # 调用所有注册的创建事件处理器
        for handler in list(self.event_handlers.get('created', [])):
            try:
                handler('created', file_path)
            except Exception as e:
                logger.error(f"Error in created event handler: {e}")
    
    def _on_file_modified(self, file_path: str) -> None:
        """
        文件修改事件
        
        Args:
            file_path: 文件路径
        """
        logger.info(f"File modified: {file_path}")
        
        # 调用所有注册的修改事件处理器
        for handler in list(self.event_handlers.get('modified', [])):
            try:
                handler('modified', file_path)
            except Exception as e:
                logger.error(f"Error in modified event handler: {e}")
    
    def _on_file_deleted(self, file_path: str) -> None:
        """
        文件删除事件
        
        Args:
            file_path: 文件路径
        """
        logger.info(f"File deleted: {file_path}")
        
        # 调用所有注册的删除事件处理器
        for handler in list(self.event_handlers.get('deleted', [])):
            try:
                handler('deleted', file_path)
            except Exception as e:
                logger.error(f"Error in deleted event handler: {e}")
    
    def scan_directory(self, directory_path: str, update_states: bool = True) -> List[str]:
        """
        扫描目录
        
        Args:
            directory_path: 目录路径
            update_states: 是否更新文件状态（默认True）
        
        Returns:
            文件列表
        """
        try:
            files = []
            
            for root, dirs, files_in_dir in os.walk(directory_path):
                # 过滤掉需要忽略的目录
                dirs[:] = [d for d in dirs if not self._should_ignore(d)]
                
                for file in files_in_dir:
                    if self._should_ignore(file):
                        continue
                    
                    file_path = os.path.join(root, file)
                    files.append(file_path)
                    # 更新文件状态，避免监控循环再次触发创建事件
                    if update_states:
                        try:
                            mtime = os.path.getmtime(file_path)
                            self.file_states[file_path] = mtime
                        except Exception as e:
                            logger.error(f"Failed to get mtime for {file_path}: {e}")
            
            logger.info(f"Scanned directory {directory_path}, found {len(files)} files")
            return files
        except Exception as e:
            logger.error(f"Failed to scan directory {directory_path}: {e}")
            return []
    
    def is_initialized(self) -> bool:
        """
        检查是否已初始化
        
        Returns:
            是否已初始化
        """
        return True


# 初始化函数
def create_file_monitor(config: Dict[str, Any]) -> FileMonitor:
    """
    创建文件监控器实例
    
    Args:
        config: 配置字典
    
    Returns:
        FileMonitor实例
    """
    file_monitor = FileMonitor(config)
    if not file_monitor.initialize():
        logger.error("Failed to create FileMonitor")
        raise RuntimeError("Failed to create FileMonitor")
    
    return file_monitor
