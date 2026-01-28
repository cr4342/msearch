"""
多进程管理器 - 负责管理各个工作进程的生命周期
"""
import multiprocessing
import signal
import time
import os
import sys
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum


class ProcessType(Enum):
    MAIN = "main"
    FILE_MONITOR = "file_monitor"
    EMBEDDING_WORKER = "embedding_worker"
    TASK_WORKER = "task_worker"


@dataclass
class ProcessConfig:
    """进程配置"""
    process_type: ProcessType
    target_func: Callable
    args: tuple = ()
    kwargs: dict = None
    num_instances: int = 1  # 进程数量
    auto_restart: bool = True  # 是否自动重启失败的进程


class ProcessManager:
    """多进程管理器"""
    
    def __init__(self):
        self.processes: Dict[str, multiprocessing.Process] = {}
        self.configs: Dict[str, ProcessConfig] = {}
        self.process_status: Dict[str, str] = {}  # running, stopped, failed
        self.shutdown_requested = False
        
        # 注册信号处理器
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """信号处理器"""
        print(f"接收到信号 {signum}，正在关闭进程管理器...")
        self.shutdown_requested = True
        self.stop_all_processes()
        sys.exit(0)
    
    def register_process_config(self, name: str, config: ProcessConfig) -> None:
        """注册进程配置"""
        self.configs[name] = config
    
    def start_process(self, name: str) -> bool:
        """启动指定进程"""
        if name not in self.configs:
            print(f"错误: 未找到进程配置 {name}")
            return False
        
        config = self.configs[name]
        
        # 创建多个实例（对于可并行的进程类型）
        for i in range(config.num_instances):
            instance_name = f"{name}_{i}" if config.num_instances > 1 else name
            
            # 创建进程
            process = multiprocessing.Process(
                target=self._run_process,
                args=(config.target_func, config.args, config.kwargs or {}, instance_name),
                name=instance_name
            )
            
            # 启动进程
            process.start()
            self.processes[instance_name] = process
            self.process_status[instance_name] = "running"
            
            print(f"启动进程 {instance_name} (PID: {process.pid})")
        
        return True
    
    def _run_process(self, target_func: Callable, args: tuple, kwargs: dict, name: str) -> None:
        """运行进程的实际方法"""
        print(f"进程 {name} 开始运行...")
        try:
            # 执行目标函数
            target_func(*args, **kwargs)
        except KeyboardInterrupt:
            print(f"进程 {name} 接收到中断信号")
        except Exception as e:
            print(f"进程 {name} 发生错误: {e}")
            self.process_status[name] = "failed"
        finally:
            print(f"进程 {name} 结束运行")
            if name in self.process_status and self.process_status[name] != "failed":
                self.process_status[name] = "stopped"
    
    def stop_process(self, name: str) -> bool:
        """停止指定进程"""
        if name not in self.processes:
            print(f"错误: 进程 {name} 不存在")
            return False
        
        process = self.processes[name]
        
        if process.is_alive():
            print(f"正在停止进程 {name} (PID: {process.pid})")
            process.terminate()
            
            # 等待进程结束
            process.join(timeout=5)
            
            if process.is_alive():
                # 如果进程没有正常退出，强制杀死
                print(f"进程 {name} 未正常退出，强制杀死")
                process.kill()
                process.join()
        
        # 从管理器中移除
        del self.processes[name]
        if name in self.process_status:
            del self.process_status[name]
        
        return True
    
    def start_all_processes(self) -> None:
        """启动所有注册的进程"""
        print("正在启动所有进程...")
        
        # 按依赖顺序启动进程：
        # 1. 主进程 (Main) - 通常由外部启动
        # 2. 文件监控进程 (File Monitor)
        # 3. 向量化工作进程 (Embedding Worker)
        # 4. 任务工作进程 (Task Worker)
        
        # 启动文件监控进程
        if "file_monitor" in self.configs:
            self.start_process("file_monitor")
        
        # 启动向量化工作进程
        if "embedding_worker" in self.configs:
            self.start_process("embedding_worker")
        
        # 启动任务工作进程
        if "task_worker" in self.configs:
            self.start_process("task_worker")
        
        print("所有进程启动完成")
    
    def stop_all_processes(self) -> None:
        """停止所有进程"""
        print("正在停止所有进程...")
        
        # 创建副本以避免修改字典时的迭代问题
        process_names = list(self.processes.keys())
        
        for name in process_names:
            self.stop_process(name)
        
        print("所有进程已停止")
    
    def restart_process(self, name: str) -> bool:
        """重启指定进程"""
        if name in self.processes:
            self.stop_process(name)
        
        return self.start_process(name)
    
    def get_process_status(self, name: str) -> Optional[str]:
        """获取进程状态"""
        if name in self.processes:
            process = self.processes[name]
            if process.is_alive():
                return self.process_status.get(name, "running")
            else:
                return "stopped"
        return None
    
    def get_all_process_status(self) -> Dict[str, str]:
        """获取所有进程状态"""
        status = {}
        for name, process in self.processes.items():
            if process.is_alive():
                status[name] = self.process_status.get(name, "running")
            else:
                status[name] = "stopped"
        return status
    
    def monitor_processes(self, check_interval: float = 5.0) -> None:
        """监控进程状态，自动重启失败的进程"""
        print("开始监控进程...")
        
        while not self.shutdown_requested:
            try:
                for name, process in list(self.processes.items()):
                    if name in self.configs and self.configs[name].auto_restart:
                        # 检查进程是否还活着
                        if not process.is_alive():
                            print(f"进程 {name} 已退出，正在重启...")
                            # 从字典中移除已退出的进程
                            del self.processes[name]
                            if name in self.process_status:
                                del self.process_status[name]
                            
                            # 重启进程
                            self.start_process(name)
                
                time.sleep(check_interval)
            except Exception as e:
                print(f"监控进程时发生错误: {e}")
                time.sleep(check_interval)
    
    def wait_for_all(self) -> None:
        """等待所有进程结束"""
        for name, process in self.processes.items():
            try:
                process.join()
            except KeyboardInterrupt:
                print(f"等待进程 {name} 时被中断")
                break


def create_default_process_manager() -> ProcessManager:
    """创建默认的进程管理器"""
    manager = ProcessManager()
    
    # 这里可以注册默认的进程配置
    # 实际的进程函数将在其他模块中定义
    
    return manager