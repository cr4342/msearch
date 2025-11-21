"""
文件监控器
实时监控指定目录的文件变化，写入基础元数据，触发处理流程
"""

import asyncio
import hashlib
import logging
import os
import uuid
from pathlib import Path
from typing import Set, Dict, Any
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent, FileDeletedEvent

from src.common.storage.database_adapter import DatabaseAdapter


class FileMonitorHandler(FileSystemEventHandler):
    """文件系统事件处理器"""
    
    def __init__(self, file_monitor: 'FileMonitor'):
        self.file_monitor = file_monitor
        self.logger = logging.getLogger(__name__)
    
    def on_created(self, event):
        """文件创建事件"""
        if not event.is_directory:
            asyncio.create_task(self.file_monitor._handle_file_created(event.src_path))
    
    def on_modified(self, event):
        """文件修改事件"""
        if not event.is_directory:
            asyncio.create_task(self.file_monitor._handle_file_modified(event.src_path))
    
    def on_deleted(self, event):
        """文件删除事件"""
        if not event.is_directory:
            asyncio.create_task(self.file_monitor._handle_file_deleted(event.src_path))


class FileMonitor:
    """文件监控器"""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        self.db_adapter = DatabaseAdapter()
        
        # 监控配置
        self.monitored_directories = self.config_manager.get("system.monitored_directories", [])
        self.supported_extensions = set(
            self.config_manager.get("system.supported_extensions", 
                ['.jpg', '.jpeg', '.png', '.bmp', '.webp', '.mp4', '.avi', '.mov', '.mp3', '.wav', '.flac'])
        )
        self.debounce_delay = self.config_manager.get("system.debounce_delay", 0.5)
        
        # 防抖处理
        self.pending_files: Dict[str, asyncio.Task] = {}
        
        # 观察者
        self.observer = Observer()
        self.handler = FileMonitorHandler(self)
        
        self.logger.info(f"文件监控器初始化完成，监控目录: {self.monitored_directories}")
    
    async def start(self):
        """启动文件监控"""
        self.logger.info("启动文件监控服务")
        
        # 为每个监控目录创建观察者
        for directory in self.monitored_directories:
            if os.path.exists(directory):
                self.observer.schedule(self.handler, directory, recursive=True)
                self.logger.info(f"开始监控目录: {directory}")
            else:
                self.logger.warning(f"监控目录不存在: {directory}")
        
        self.observer.start()
        
        # 执行初始扫描
        await self._initial_scan()
    
    async def stop(self):
        """停止文件监控"""
        self.logger.info("停止文件监控服务")
        self.observer.stop()
        self.observer.join()
        
        # 取消所有待处理的任务
        for task in self.pending_files.values():
            task.cancel()
        
        self.pending_files.clear()
    
    async def _initial_scan(self):
        """初始扫描已存在的文件"""
        self.logger.info("执行初始文件扫描")
        
        for directory in self.monitored_directories:
            if not os.path.exists(directory):
                continue
            
            for root, dirs, files in os.walk(directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    if self._is_supported_file(file_path):
                        await self._process_file(file_path)
        
        self.logger.info("初始文件扫描完成")
    
    async def _handle_file_created(self, file_path: str):
        """处理文件创建事件"""
        if not self._is_supported_file(file_path):
            return
        
        self.logger.debug(f"检测到文件创建: {file_path}")
        await self._debounced_process_file(file_path)
    
    async def _handle_file_modified(self, file_path: str):
        """处理文件修改事件"""
        if not self._is_supported_file(file_path):
            return
        
        self.logger.debug(f"检测到文件修改: {file_path}")
        await self._debounced_process_file(file_path)
    
    async def _handle_file_deleted(self, file_path: str):
        """处理文件删除事件"""
        self.logger.debug(f"检测到文件删除: {file_path}")
        
        try:
            # 从数据库中删除文件记录
            file_id = await self._get_file_id_by_path(file_path)
            if file_id:
                await self.db_adapter.delete_file(file_id)
                self.logger.info(f"已删除文件记录: {file_path} (ID: {file_id})")
        except Exception as e:
            self.logger.error(f"删除文件记录失败: {file_path}, 错误: {e}")
    
    async def _debounced_process_file(self, file_path: str):
        """防抖处理文件"""
        # 取消之前的任务
        if file_path in self.pending_files:
            self.pending_files[file_path].cancel()
        
        # 创建新的延迟任务
        task = asyncio.create_task(self._delayed_process_file(file_path))
        self.pending_files[file_path] = task
    
    async def _delayed_process_file(self, file_path: str):
        """延迟处理文件"""
        await asyncio.sleep(self.debounce_delay)
        
        # 从待处理列表中移除
        self.pending_files.pop(file_path, None)
        
        # 处理文件
        await self._process_file(file_path)
    
    async def _process_file(self, file_path: str):
        """处理文件"""
        try:
            # 提取基础元数据
            file_info = await self._extract_file_metadata(file_path)
            
            # 检查文件是否已存在
            existing_file = await self._get_file_id_by_path(file_path)
            
            if existing_file:
                # 更新现有文件
                await self.db_adapter.update_file(existing_file, file_info)
                self.logger.debug(f"更新文件记录: {file_path}")
            else:
                # 插入新文件
                await self.db_adapter.insert_file(file_info)
                self.logger.info(f"新增文件记录: {file_path}")
                
                # 通知调度器有新文件
                # TODO: 实现调度器通知机制
        
        except Exception as e:
            self.logger.error(f"处理文件失败: {file_path}, 错误: {e}")
    
    def _is_supported_file(self, file_path: str) -> bool:
        """检查是否为支持的文件类型"""
        file_ext = Path(file_path).suffix.lower()
        return file_ext in self.supported_extensions
    
    async def _extract_file_metadata(self, file_path: str) -> Dict[str, Any]:
        """提取文件基础元数据"""
        file_path_obj = Path(file_path)
        
        # 计算文件hash
        file_hash = await self._calculate_file_hash(file_path)
        
        # 获取文件信息
        stat = file_path_obj.stat()
        
        return {
            'id': str(uuid.uuid4()),
            'file_path': file_path,
            'file_name': file_path_obj.name,
            'file_type': file_path_obj.suffix.lower(),
            'file_size': stat.st_size,
            'file_hash': file_hash,
            'created_at': stat.st_ctime,
            'modified_at': stat.st_mtime,
            'status': 'pending'
        }
    
    async def _calculate_file_hash(self, file_path: str) -> str:
        """计算文件hash"""
        hash_sha256 = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        
        return hash_sha256.hexdigest()
    
    async def _get_file_id_by_path(self, file_path: str) -> str:
        """根据文件路径获取文件ID"""
        try:
            files = await self.db_adapter.get_files_by_path(file_path)
            return files[0]['id'] if files else None
        except Exception:
            return None