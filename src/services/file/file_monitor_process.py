"""
文件监控进程 - 独立进程负责监控文件系统变化
"""
import time
import os
import json
from pathlib import Path
from typing import Dict, List, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from src.ipc.redis_ipc import FileMonitorIPC, RedisIPC


class FileMonitorHandler(FileSystemEventHandler):
    """文件监控事件处理器"""
    
    def __init__(self, ipc_client: RedisIPC, watched_dirs: List[str]):
        super().__init__()
        self.ipc_client = ipc_client
        self.watched_dirs = watched_dirs
        self.last_processed: Dict[str, float] = {}  # 防抖用
        self.debounce_time = 2.0  # 防抖时间2秒
    
    def _should_process_file(self, file_path: str) -> bool:
        """检查是否应该处理文件（防抖）"""
        current_time = time.time()
        last_time = self.last_processed.get(file_path, 0)
        
        if current_time - last_time > self.debounce_time:
            self.last_processed[file_path] = current_time
            return True
        return False
    
    def on_created(self, event):
        """文件创建事件"""
        if not event.is_directory and self._should_process_file(event.src_path):
            # 发送文件创建消息
            message = {
                "type": "file_created",
                "file_path": event.src_path,
                "timestamp": time.time()
            }
            self.ipc_client.send_message(message, "main")
    
    def on_modified(self, event):
        """文件修改事件"""
        if not event.is_directory and self._should_process_file(event.src_path):
            # 发送文件修改消息
            message = {
                "type": "file_modified", 
                "file_path": event.src_path,
                "timestamp": time.time()
            }
            self.ipc_client.send_message(message, "main")
    
    def on_deleted(self, event):
        """文件删除事件"""
        if not event.is_directory:
            # 发送文件删除消息
            message = {
                "type": "file_deleted",
                "file_path": event.src_path,
                "timestamp": time.time()
            }
            self.ipc_client.send_message(message, "main")
    
    def on_moved(self, event):
        """文件移动事件"""
        if not event.is_directory:
            # 发送文件移动消息
            message = {
                "type": "file_moved",
                "src_path": event.src_path,
                "dest_path": event.dest_path,
                "timestamp": time.time()
            }
            self.ipc_client.send_message(message, "main")


def scan_directory(directory: str, supported_extensions: List[str]) -> List[str]:
    """扫描目录并返回支持的文件列表"""
    files = []
    for root, _, filenames in os.walk(directory):
        for filename in filenames:
            if any(filename.lower().endswith(ext) for ext in supported_extensions):
                files.append(os.path.join(root, filename))
    return files


def file_monitor_process(config: Dict[str, any]):
    """文件监控进程的主函数"""
    # 从配置中获取参数
    watched_dirs = config.get("watched_dirs", ["/data/project/msearch/testdata"])
    supported_extensions = config.get("supported_extensions", [
        ".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp",  # 图像
        ".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv",   # 视频
        ".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a"   # 音频
    ])
    
    # 连接到Redis IPC
    ipc_client = FileMonitorIPC()
    if not ipc_client.connect():
        print("无法连接到Redis，文件监控进程退出")
        return
    
    print("文件监控进程启动，正在监控目录:", watched_dirs)
    
    # 初始化观察器
    observer = Observer()
    handler = FileMonitorHandler(ipc_client, watched_dirs)
    
    # 添加监控目录
    recursive = config.get("recursive", True) 
    for directory in watched_dirs:
        if os.path.exists(directory):
            observer.schedule(handler, directory, recursive=recursive)
            print(f"开始监控目录: {directory}")
    
    # 启动观察器
    observer.start()
    
    try:
        # 定期扫描目录，确保没有遗漏的文件
        scan_interval = config.get("scan_interval", 300)  # 5分钟扫描一次
        last_scan_time = 0
        
        while True:
            current_time = time.time()
            
            # 定期全量扫描
            if current_time - last_scan_time > scan_interval:
                print("执行全量目录扫描...")
                
                for directory in watched_dirs:
                    if os.path.exists(directory):
                        files = scan_directory(directory, supported_extensions)
                        print(f"在 {directory} 中发现 {len(files)} 个文件")
                        
                        # 发送扫描结果
                        message = {
                            "type": "directory_scan",
                            "directory": directory,
                            "files": files,
                            "timestamp": current_time
                        }
                        ipc_client.send_message(message, "main")
                
                last_scan_time = current_time
            
            # 更新心跳
            ipc_client.update_heartbeat()
            
            # 睡眠一小段时间
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("文件监控进程收到中断信号，正在停止...")
    finally:
        # 清理资源
        observer.stop()
        observer.join()
        ipc_client.disconnect()
        print("文件监控进程已停止")


if __name__ == "__main__":
    # 用于测试的配置
    test_config = {
        "watched_dirs": ["./testdata"],
        "supported_extensions": [".jpg", ".png", ".mp4", ".mp3"],
        "recursive": True,
        "scan_interval": 300
    }
    
    file_monitor_process(test_config)