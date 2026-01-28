#!/usr/bin/env python3
"""
msearch多进程启动器（优化版）
协调主进程、API服务、文件监控、向量化工作进程和任务工作进程的启动
采用SQLite+本地IPC方案，移除Redis依赖
"""

import subprocess
import sys
import os
import signal
import time
import argparse
from pathlib import Path
import shutil


class MultiprocessLauncher:
    """多进程启动器（优化版）"""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path
        self.processes = []
        self.shutdown_requested = False
        
        # 设置信号处理器
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """信号处理器"""
        print(f"\n接收到信号 {signum}，正在关闭所有进程...")
        self.shutdown_requested = True
        self.shutdown_all()
        sys.exit(0)
    
    def check_dependencies(self):
        """检查依赖项"""
        print("正在检查依赖项...")
        
        # 检查Python依赖
        try:
            import persistqueue
            print("✓ persist-queue 检查通过")
        except ImportError:
            print("✗ 未找到 persist-queue，请运行: pip install persist-queue")
            return False
        
        # 检查FFmpeg
        if not shutil.which('ffmpeg'):
            print("✗ 未找到 ffmpeg，请安装 FFmpeg")
            return False
        else:
            print("✓ ffmpeg 检查通过")
        
        # 检查FFprobe
        if not shutil.which('ffprobe'):
            print("✗ 未找到 ffprobe，请安装 FFmpeg")
            return False
        else:
            print("✓ ffprobe 检查通过")
        
        return True
    
    def start_main_process(self):
        """启动主进程协调器"""
        print("正在启动主进程协调器...")
        try:
            cmd = [sys.executable, 'src/main.py']
            if self.config_path:
                cmd.extend(['--config', self.config_path])
            
            main_process = subprocess.Popen(cmd)
            self.processes.append(('main_process', main_process))
            print(f"主进程协调器启动成功 (PID: {main_process.pid})")
            return True
        except Exception as e:
            print(f"启动主进程协调器失败: {e}")
            return False
    
    def start_main_multiprocess(self):
        """启动多进程主程序"""
        print("正在启动多进程主程序...")
        try:
            cmd = [sys.executable, 'src/main_multiprocess.py']
            if self.config_path:
                cmd.extend(['--config', self.config_path])
            
            main_process = subprocess.Popen(cmd)
            self.processes.append(('main_multiprocess', main_process))
            print(f"多进程主程序启动成功 (PID: {main_process.pid})")
            return True
        except Exception as e:
            print(f"启动多进程主程序失败: {e}")
            return False
    
    def start_api_server(self, host: str = '0.0.0.0', port: int = 8000):
        """启动API服务器"""
        print(f"正在启动API服务器 ({host}:{port})...")
        try:
            cmd = [sys.executable, 'src/api_server.py', '--host', host, '--port', str(port)]
            if self.config_path:
                cmd.extend(['--config', self.config_path])
            
            api_process = subprocess.Popen(cmd)
            self.processes.append(('api_server', api_process))
            print(f"API服务器启动成功 (PID: {api_process.pid})")
            return True
        except Exception as e:
            print(f"启动API服务器失败: {e}")
            return False
    
    def start_file_monitor_process(self):
        """启动文件监控进程（作为主进程的子任务）"""
        print("文件监控进程将由主进程协调器管理")
        return True
    
    def start_embedding_workers(self, count: int = 1):
        """启动向量化工作进程（作为主进程的子任务）"""
        print(f"向量化工作进程将由主进程协调器管理 (数量: {count})")
        return True
    
    def start_task_workers(self, count: int = 2):
        """启动任务工作进程（作为主进程的子任务）"""
        print(f"任务工作进程将由主进程协调器管理 (数量: {count})")
        return True
    
    def start_all(self, api_host: str = '0.0.0.0', api_port: int = 8000, 
                  embedding_workers: int = 1, task_workers: int = 2):
        """启动所有服务"""
        print("启动msearch多进程架构（优化版）...")
        
        # 1. 检查依赖项
        if not self.check_dependencies():
            print("依赖项检查失败，退出")
            return False
        
        # 2. 启动主进程协调器
        if not self.start_main_process():
            print("主进程协调器启动失败，退出")
            return False
        
        time.sleep(3)  # 等待主进程协调器启动其子进程
        
        # 3. 启动API服务器
        if not self.start_api_server(api_host, api_port):
            print("API服务器启动失败，退出")
            return False
        
        print("所有服务启动完成！")
        print(f"API服务: http://{api_host}:{api_port}")
        print("主进程协调器: 管理所有子进程")
        print("服务状态: 运行中")
        print("IPC方案: SQLite + 本地Unix Socket (无Redis依赖)")
        
        return True
    
    def start_multiprocess_architecture(self, api_host: str = '0.0.0.0', api_port: int = 8000):
        """启动多进程架构"""
        print("启动msearch多进程架构（优化版）...")
        
        # 1. 检查依赖项
        if not self.check_dependencies():
            print("依赖项检查失败，退出")
            return False
        
        # 2. 启动多进程主程序
        if not self.start_main_multiprocess():
            print("多进程主程序启动失败，退出")
            return False
        
        time.sleep(3)  # 等待多进程主程序启动其子进程
        
        # 3. 启动API服务器
        if not self.start_api_server(api_host, api_port):
            print("API服务器启动失败，退出")
            return False
        
        print("多进程架构启动完成！")
        print(f"API服务: http://{api_host}:{api_port}")
        print("多进程主程序: 管理所有子进程")
        print("服务状态: 运行中")
        print("IPC方案: SQLite + 本地Unix Socket (无Redis依赖)")
        
        return True
    
    def monitor_processes(self):
        """监控进程状态"""
        while not self.shutdown_requested:
            try:
                for name, process in self.processes:
                    if process.poll() is not None:
                        print(f"进程 {name} (PID: {process.pid}) 已退出")
                        # 进程意外退出，尝试重启
                        print(f"尝试重启进程 {name}...")
                        self.restart_process(name)
                
                time.sleep(5)  # 每5秒检查一次
            except Exception as e:
                print(f"监控进程时发生错误: {e}")
                time.sleep(5)
    
    def restart_process(self, name: str):
        """重启指定进程"""
        if name == 'api_server':
            self.start_api_server()
        elif name == 'main_process':
            self.start_main_process()
        elif name == 'main_multiprocess':
            self.start_main_multiprocess()
    
    def shutdown_all(self):
        """关闭所有进程"""
        print("正在关闭所有进程...")
        
        for name, process in reversed(self.processes):
            print(f"正在停止 {name} (PID: {process.pid})...")
            
            try:
                # 尝试优雅关闭
                process.terminate()
                try:
                    process.wait(timeout=10)  # 等待10秒
                except subprocess.TimeoutExpired:
                    # 如果超时，强制杀死
                    print(f"{name} 未在10秒内停止，强制杀死...")
                    process.kill()
                    process.wait()
            except Exception as e:
                print(f"停止 {name} 时出错: {e}")
        
        print("所有进程已关闭")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='msearch多进程启动器（优化版）')
    parser.add_argument('--config', type=str, help='配置文件路径')
    parser.add_argument('--api-host', type=str, default='0.0.0.0', help='API服务器主机地址')
    parser.add_argument('--api-port', type=int, default=8000, help='API服务器端口')
    parser.add_argument('--embedding-workers', type=int, default=1, help='向量化工作进程数量')
    parser.add_argument('--task-workers', type=int, default=2, help='任务工作进程数量')
    parser.add_argument('--mode', type=str, default='main', choices=['main', 'multiprocess'], 
                        help='启动模式: main=主进程协调器, multiprocess=多进程主程序')
    
    args = parser.parse_args()
    
    # 检查是否在项目根目录
    if not Path('src').exists() or not Path('config').exists():
        print("错误: 请在msearch项目根目录下运行此脚本")
        sys.exit(1)
    
    # 创建启动器
    launcher = MultiprocessLauncher(args.config)
    
    # 启动所有服务
    if args.mode == 'multiprocess':
        success = launcher.start_multiprocess_architecture(
            api_host=args.api_host,
            api_port=args.api_port
        )
    else:
        success = launcher.start_all(
            api_host=args.api_host,
            api_port=args.api_port,
            embedding_workers=args.embedding_workers,
            task_workers=args.task_workers
        )
    
    if success:
        print("\nmsearch服务已启动（优化版）")
        print(f"API服务地址: http://{args.api_host}:{args.api_port}")
        print("IPC方案: SQLite + 本地Unix Socket (无Redis依赖)")
        print("按 Ctrl+C 停止服务")
        
        try:
            # 监控进程状态
            launcher.monitor_processes()
        except KeyboardInterrupt:
            print("\n接收到中断信号，正在关闭...")
    else:
        print("启动失败")
        sys.exit(1)


if __name__ == '__main__':
    main()
