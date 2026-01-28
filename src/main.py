"""
msearch主程序入口 - 多进程架构主进程
负责协调各个子进程并提供API服务
"""
import time
import signal
import sys
from pathlib import Path
import logging

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.ipc.process_manager import ProcessManager, ProcessConfig, ProcessType, create_default_process_manager
from src.ipc.redis_ipc import MainProcessIPC
from src.services.file.file_monitor_process import file_monitor_process
from src.services.embedding.embedding_worker_process import embedding_worker_process
from src.services.task.task_worker_process import task_worker_process

class MainProcessCoordinator:
    """主进程协调器"""
    
    def __init__(self, config: dict):
        self.config = config
        self.process_manager = create_default_process_manager()
        self.ipc_client = MainProcessIPC()
        self.shutdown_requested = False
        
        # 设置信号处理器
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """信号处理器"""
        print(f"\n接收到信号 {signum}，正在关闭主进程...")
        self.shutdown_requested = True
        self.shutdown()
        sys.exit(0)
    
    def setup_processes(self):
        """设置进程配置"""
        # 文件监控进程配置
        file_monitor_config = self.config.get("file_monitor", {
            "watched_dirs": ["/data/project/msearch/testdata"],
            "supported_extensions": [".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp", ".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a"],
            "recursive": True,
            "scan_interval": 300
        })
        
        self.process_manager.register_process_config(
            "file_monitor",
            ProcessConfig(
                process_type=ProcessType.FILE_MONITOR,
                target_func=file_monitor_process,
                args=(file_monitor_config,),
                num_instances=1,
                auto_restart=True
            )
        )
        
        # 向量化工作进程配置
        embedding_worker_config = self.config.get("embedding_worker", {
            "device": "cpu",
            "batch_size": 8,
            "models": {
                "chinese_clip_base": {
                    "model_name": "OFA-Sys/chinese-clip-vit-base-patch16",
                    "local_path": "data/models/chinese-clip-vit-base-patch16",
                    "device": "cpu",
                    "batch_size": 8
                }
            }
        })
        
        num_embedding_workers = self.config.get("num_embedding_workers", 1)
        self.process_manager.register_process_config(
            "embedding_worker",
            ProcessConfig(
                process_type=ProcessType.EMBEDDING_WORKER,
                target_func=embedding_worker_process,
                args=(embedding_worker_config,),
                num_instances=num_embedding_workers,
                auto_restart=True
            )
        )
        
        # 任务工作进程配置
        task_worker_config = self.config.get("task_worker", {})
        num_task_workers = self.config.get("num_task_workers", 2)
        
        self.process_manager.register_process_config(
            "task_worker",
            ProcessConfig(
                process_type=ProcessType.TASK_WORKER,
                target_func=task_worker_process,
                args=(task_worker_config,),
                num_instances=num_task_workers,
                auto_restart=True
            )
        )
    
    def start_ipc(self):
        """启动IPC连接"""
        if not self.ipc_client.connect():
            print("无法连接到Redis，主进程退出")
            return False
        
        print("主进程IPC连接成功")
        return True
    
    def start_processes(self):
        """启动所有子进程"""
        print("正在启动子进程...")
        self.process_manager.start_all_processes()
        print("所有子进程已启动")
    
    def monitor_system(self):
        """监控系统状态"""
        while not self.shutdown_requested:
            try:
                # 获取所有进程状态
                status = self.process_manager.get_all_process_status()
                print(f"进程状态: {status}")
                
                # 获取所有注册的进程
                processes = self.ipc_client.get_all_processes()
                print(f"注册进程: {processes}")
                
                # 更新主进程心跳
                self.ipc_client.update_heartbeat()
                
                # 等待一段时间
                time.sleep(10)  # 每10秒检查一次
                
            except Exception as e:
                print(f"监控系统时发生错误: {e}")
                time.sleep(5)
    
    def run(self):
        """运行主进程"""
        print("msearch主进程启动（多进程架构）")
        
        # 启动IPC
        if not self.start_ipc():
            return
        
        # 设置并启动子进程
        self.setup_processes()
        self.start_processes()
        
        # 启动系统监控
        self.monitor_system()
    
    def shutdown(self):
        """关闭主进程"""
        print("正在关闭主进程...")
        
        # 停止所有子进程
        self.process_manager.stop_all_processes()
        
        # 断开IPC连接
        self.ipc_client.disconnect()
        
        print("主进程已关闭")

def main():
    """主函数"""
    # 默认配置
    config = {
        "file_monitor": {
            "watched_dirs": ["./testdata"],
            "supported_extensions": [".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp", 
                                   ".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv",
                                   ".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a"],
            "recursive": True,
            "scan_interval": 300
        },
        "embedding_worker": {
            "device": "cpu",  # 根据系统配置调整
            "batch_size": 8,
            "models": {
                "chinese_clip_base": {
                    "model_name": "OFA-Sys/chinese-clip-vit-base-patch16",
                    "local_path": "data/models/chinese-clip-vit-base-patch16",
                    "device": "cpu",
                    "batch_size": 8
                }
            }
        },
        "task_worker": {},
        "num_embedding_workers": 1,
        "num_task_workers": 2
    }
    
    # 创建并运行主进程协调器
    coordinator = MainProcessCoordinator(config)
    
    try:
        coordinator.run()
    except KeyboardInterrupt:
        print("\n主进程被中断")
        coordinator.shutdown()


if __name__ == "__main__":
    main()