#!/usr/bin/env python3
"""
msearch多进程主程序（优化版）
使用中央任务管理器和SQLite IPC方案
"""

import os
import sys
import time
import signal
import threading
from pathlib import Path
from typing import Dict, Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.task import CentralTaskManager, Task
from core.config.config_manager import ConfigManager
from ipc import MainProcessIPC
from services.media.video_slicer import VideoSlicer


class MainMultiprocessApp:
    """多进程主程序"""
    
    def __init__(self, config_path: str = "config/config.yml"):
        self.config_path = config_path
        self.config = None
        self.central_task_manager = None
        self.ipc = None
        self.running = False
        self.threads = []
        
        # 设置信号处理器
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """信号处理器"""
        print(f"\n接收到信号 {signum}，正在关闭...")
        self.shutdown()
        sys.exit(0)
    
    def initialize(self):
        """初始化应用"""
        print("正在初始化msearch多进程主程序...")
        
        try:
            # 加载配置
            self.config = ConfigManager(config_path=self.config_path)
            print(f"配置加载成功: {self.config_path}")
            
            # 初始化中央任务管理器
            device = self.config.get('models', {}).get('device', 'cpu')
            self.central_task_manager = CentralTaskManager(self.config.config, device)
            
            if not self.central_task_manager.initialize():
                print("中央任务管理器初始化失败")
                return False
            
            print("中央任务管理器初始化成功")
            
            # 初始化IPC（使用SQLite IPC）
            ipc_config = self.config.get('ipc', {})
            self.ipc = MainProcessIPC(ipc_config)
            
            if not self.ipc.connect():
                print("IPC连接失败")
                return False
            
            print("IPC连接成功")
            
            # 注册任务处理器
            self._register_task_handlers()
            
            print("应用初始化完成")
            return True
            
        except Exception as e:
            print(f"初始化失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _register_task_handlers(self):
        """注册任务处理器"""
        # 注册视频切片任务处理器
        self.central_task_manager.register_handler('video_slice', self._handle_video_slice_task)
        
        # 注册其他任务处理器
        # 可以根据需要添加更多处理器
        print("任务处理器注册完成")
    
    def _handle_video_slice_task(self, task_data: Dict[str, Any], task: Task) -> bool:
        """处理视频切片任务"""
        try:
            video_path = task_data.get('video_path')
            if not video_path or not os.path.exists(video_path):
                print(f"视频文件不存在: {video_path}")
                return False
            
            # 创建视频切片器
            strategy = task_data.get('strategy', 'hybrid')
            video_slicer = VideoSlicer(strategy=strategy)
            
            # 执行视频切片
            segments = video_slicer.slice_video(video_path)
            
            # 更新任务进度
            task.progress = 1.0
            task.result = segments
            
            print(f"视频切片完成: {video_path}, 生成 {len(segments)} 个片段")
            return True
            
        except Exception as e:
            print(f"处理视频切片任务失败: {e}")
            task.error = str(e)
            return False
    
    def start_worker_processes(self):
        """启动工作进程"""
        print("正在启动工作进程...")
        
        # 这里可以启动子进程或线程来处理不同类型的任务
        # 由于我们使用中央任务管理器，大部分工作由内部线程处理
        print("工作进程启动完成")
    
    def run(self):
        """运行主程序"""
        if not self.initialize():
            print("初始化失败，退出")
            return
        
        self.running = True
        print("msearch多进程主程序正在运行...")
        print("中央任务管理器: 管理所有任务")
        print("IPC方案: SQLite + 本地Unix Socket")
        print("按 Ctrl+C 停止服务")
        
        try:
            # 主循环
            while self.running:
                time.sleep(1)
                
                # 定期输出状态信息
                if int(time.time()) % 30 == 0:
                    stats = self.central_task_manager.get_statistics()
                    print(f"任务状态 - 队列: {stats.get('queue_size', 0)}, "
                          f"运行中: {stats.get('running_count', 0)}, "
                          f"资源: {stats.get('resource_state', 'unknown')}")
        
        except KeyboardInterrupt:
            print("\n接收到中断信号，正在关闭...")
        finally:
            self.shutdown()
    
    def shutdown(self):
        """关闭应用"""
        print("正在关闭msearch多进程主程序...")
        
        self.running = False
        
        # 关闭中央任务管理器
        if self.central_task_manager:
            self.central_task_manager.shutdown()
            print("中央任务管理器已关闭")
        
        # 关闭IPC
        if self.ipc:
            self.ipc.disconnect()
            print("IPC已断开")
        
        print("msearch多进程主程序已关闭")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='msearch多进程主程序（优化版）')
    parser.add_argument('--config', type=str, default='config/config.yml', 
                        help='配置文件路径')
    
    args = parser.parse_args()
    
    # 检查配置文件是否存在
    if not os.path.exists(args.config):
        print(f"配置文件不存在: {args.config}")
        # 尝试使用默认配置
        default_config = "config/config.yml"
        if os.path.exists(default_config):
            args.config = default_config
            print(f"使用默认配置: {default_config}")
        else:
            print("未找到配置文件，退出")
            sys.exit(1)
    
    # 创建并运行应用
    app = MainMultiprocessApp(args.config)
    app.run()


if __name__ == '__main__':
    main()