#!/usr/bin/env python3
# MSearch 服务停止脚本
# 功能：停止所有MSearch相关服务

import argparse
import os
import sys
import logging
import subprocess
import signal
import time
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# 添加项目根目录到Python路径
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.config_manager import get_config_manager

class ServicesManager:
    def __init__(self):
        self.config_manager = get_config_manager()
        self.logger = logging.getLogger(__name__)
        
        # 从配置文件加载服务配置
        self._load_config()
        
        self.logger.info("服务管理器初始化完成")
    
    def _load_config(self):
        """从配置文件加载服务配置"""
        # 获取服务配置
        services_config = self.config_manager.get("services", {
            'api': {
                'name': 'API服务',
                'pid_file': './data/api.pid',
                'stop_cmd': None
            },
            'ui': {
                'name': 'UI服务',
                'pid_file': './data/ui.pid',
                'stop_cmd': None
            },
            'processor': {
                'name': '媒体处理器',
                'pid_file': './data/processor.pid',
                'stop_cmd': None
            }
        })
        
        # 处理PID文件路径
        self.services = {}
        for service_name, config in services_config.items():
            pid_file = Path(config['pid_file'])
            if not pid_file.is_absolute():
                pid_file = PROJECT_ROOT / pid_file
            
            self.services[service_name] = {
                'name': config['name'],
                'pid_file': pid_file,
                'stop_cmd': config['stop_cmd']
            }
    
    def stop_service_by_pid(self, service_name: str, pid_file: Path):
        """通过PID文件停止服务"""
        if not pid_file.exists():
            self.logger.info(f"{service_name} PID文件不存在，可能未运行")
            return True
        
        try:
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            self.logger.info(f"停止{service_name} (PID: {pid})...")
            
            # 发送终止信号
            os.kill(pid, signal.SIGTERM)
            
            # 等待进程退出
            timeout = 10
            for i in range(timeout):
                try:
                    os.kill(pid, 0)  # 检查进程是否存在
                    time.sleep(1)
                except OSError:
                    break
            else:
                # 超时，强制终止
                self.logger.warning(f"{service_name} 停止超时，强制终止")
                os.kill(pid, signal.SIGKILL)
                time.sleep(1)
            
            # 删除PID文件
            pid_file.unlink()
            self.logger.info(f"{service_name} 已停止")
            return True
        except ValueError:
            self.logger.error(f"{service_name} PID文件格式错误")
            pid_file.unlink()
            return False
        except OSError as e:
            if e.errno == 3:  # 进程不存在
                self.logger.info(f"{service_name} 已停止")
                pid_file.unlink()
                return True
            else:
                self.logger.error(f"停止{service_name}失败: {e}")
                return False
        except Exception as e:
            self.logger.error(f"停止{service_name}失败: {e}")
            return False
    
    def stop_service_by_cmd(self, service_name: str, stop_cmd: list):
        """通过命令停止服务"""
        try:
            self.logger.info(f"执行命令停止{service_name}...")
            result = subprocess.run(stop_cmd, capture_output=True, text=True, cwd=str(PROJECT_ROOT))
            if result.returncode == 0:
                self.logger.info(f"{service_name} 已停止")
                return True
            else:
                self.logger.error(f"停止{service_name}失败: {result.stderr}")
                return False
        except Exception as e:
            self.logger.error(f"执行停止命令失败: {e}")
            return False
    
    def stop_service(self, service_name: str):
        """停止指定服务"""
        service = self.services.get(service_name)
        if not service:
            self.logger.error(f"未知服务: {service_name}")
            return False
        
        self.logger.info(f"=== 停止{service['name']} ===")
        
        # 先尝试通过PID文件停止
        if service['pid_file']:
            if self.stop_service_by_pid(service['name'], service['pid_file']):
                return True
        
        # 如果PID文件不存在或停止失败，尝试使用命令停止
        if service['stop_cmd']:
            return self.stop_service_by_cmd(service['name'], service['stop_cmd'])
        
        # 如果没有命令，尝试查找进程并停止
        return self.stop_service_by_process_name(service_name)
    
    def stop_service_by_process_name(self, service_name: str):
        """通过进程名停止服务"""
        try:
            # 跨平台进程查找方案
            # 先尝试使用psutil库（如果可用）
            try:
                import psutil
                
                # 查找相关进程
                process_names = {
                    'api': ['uvicorn', 'api'],
                    'ui': ['pyside6', 'ui'],
                    'processor': ['processor', 'media']
                }
                
                pnames = process_names.get(service_name, [service_name])
                
                for pname in pnames:
                    for proc in psutil.process_iter(['pid', 'cmdline']):
                        try:
                            cmdline = ' '.join(proc.cmdline())
                            if pname in cmdline:
                                pid = proc.pid
                                self.logger.info(f"停止{service_name}进程 (PID: {pid})...")
                                proc.terminate()
                                # 等待进程退出
                                try:
                                    proc.wait(timeout=5)
                                except psutil.TimeoutExpired:
                                    self.logger.warning(f"{service_name}进程 (PID: {pid}) 停止超时，强制终止")
                                    proc.kill()
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
            except ImportError:
                # 如果psutil不可用，使用平台特定命令
                import platform
                
                # 查找相关进程
                process_names = {
                    'api': ['uvicorn', 'api'],
                    'ui': ['pyside6', 'ui'],
                    'processor': ['processor', 'media']
                }
                
                pnames = process_names.get(service_name, [service_name])
                
                for pname in pnames:
                    if platform.system() == 'Linux':
                        # Linux平台使用pgrep
                        result = subprocess.run(['pgrep', '-f', pname], capture_output=True, text=True)
                        if result.returncode == 0:
                            pids = result.stdout.strip().split('\n')
                            for pid in pids:
                                if pid:
                                    self.logger.info(f"停止{service_name}进程 (PID: {pid})...")
                                    try:
                                        os.kill(int(pid), signal.SIGTERM)
                                    except OSError:
                                        pass
                    elif platform.system() == 'Windows':
                        # Windows平台使用taskkill
                        result = subprocess.run(['taskkill', '/f', '/im', f'*{pname}*'], capture_output=True, text=True)
                        if result.returncode == 0:
                            self.logger.info(f"停止{service_name}进程成功")
                    elif platform.system() == 'Darwin':
                        # macOS平台使用pgrep
                        result = subprocess.run(['pgrep', '-f', pname], capture_output=True, text=True)
                        if result.returncode == 0:
                            pids = result.stdout.strip().split('\n')
                            for pid in pids:
                                if pid:
                                    self.logger.info(f"停止{service_name}进程 (PID: {pid})...")
                                    try:
                                        os.kill(int(pid), signal.SIGTERM)
                                    except OSError:
                                        pass
            
            self.logger.info(f"{service_name} 已停止")
            return True
        except Exception as e:
            self.logger.error(f"通过进程名停止{service_name}失败: {e}")
            return False
    
    def stop_all_services(self):
        """停止所有服务"""
        self.logger.info("=== 开始停止所有服务 ===")
        
        # 停止顺序：API -> UI -> 处理器
        stop_order = ['api', 'ui', 'processor']
        
        for service_name in stop_order:
            self.stop_service(service_name)
        
        self.logger.info("=== 所有服务已停止 ===")
    
    def check_service_status(self, service_name: str):
        """检查服务状态"""
        service = self.services.get(service_name)
        if not service:
            self.logger.error(f"未知服务: {service_name}")
            return False
        
        # 检查PID文件
        if service['pid_file'] and service['pid_file'].exists():
            try:
                with open(service['pid_file'], 'r') as f:
                    pid = int(f.read().strip())
                
                # 检查进程是否存在
                os.kill(pid, 0)
                return True
            except (ValueError, OSError):
                # PID文件无效或进程不存在
                if service['pid_file'].exists():
                    service['pid_file'].unlink()
                return False
        
        # 检查进程是否正在运行
        return self.is_process_running(service_name)
    
    def is_process_running(self, service_name: str):
        """检查进程是否正在运行"""
        try:
            # 跨平台进程查找方案
            # 先尝试使用psutil库（如果可用）
            try:
                import psutil
                
                process_names = {
                    'api': ['uvicorn', 'api'],
                    'ui': ['pyside6', 'ui'],
                    'processor': ['processor', 'media']
                }
                
                pnames = process_names.get(service_name, [service_name])
                
                for pname in pnames:
                    for proc in psutil.process_iter(['cmdline']):
                        try:
                            cmdline = ' '.join(proc.cmdline())
                            if pname in cmdline:
                                return True
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
            except ImportError:
                # 如果psutil不可用，使用平台特定命令
                import platform
                
                process_names = {
                    'api': ['uvicorn', 'api'],
                    'ui': ['pyside6', 'ui'],
                    'processor': ['processor', 'media']
                }
                
                pnames = process_names.get(service_name, [service_name])
                
                for pname in pnames:
                    if platform.system() == 'Linux' or platform.system() == 'Darwin':
                        # Linux和macOS平台使用pgrep
                        result = subprocess.run(['pgrep', '-f', pname], capture_output=True, text=True)
                        if result.returncode == 0:
                            return True
                    elif platform.system() == 'Windows':
                        # Windows平台使用tasklist
                        result = subprocess.run(['tasklist', '/fi', f'IMAGENAME eq *{pname}*'], capture_output=True, text=True)
                        if pname in result.stdout:
                            return True
        
        return False
    
    def get_all_services_status(self):
        """获取所有服务状态"""
        status = {}
        for service_name in self.services:
            status[service_name] = self.check_service_status(service_name)
        return status
    
    def print_services_status(self):
        """打印所有服务状态"""
        self.logger.info("=== 服务状态 ===")
        status = self.get_all_services_status()
        for service_name, is_running in status.items():
            service = self.services[service_name]
            status_str = "运行中" if is_running else "已停止"
            self.logger.info(f"{service['name']}: {status_str}")

def main():
    parser = argparse.ArgumentParser(description="MSearch服务停止脚本")
    
    parser.add_argument('--service', type=str, help='指定要停止的服务 (api/ui/processor)')
    parser.add_argument('--status', action='store_true', help='查看服务状态')
    parser.add_argument('--all', action='store_true', help='停止所有服务 (默认)')
    
    args = parser.parse_args()
    
    manager = ServicesManager()
    
    try:
        if args.status:
            manager.print_services_status()
        elif args.service:
            manager.stop_service(args.service)
        else:
            # 默认停止所有服务
            manager.stop_all_services()
    except KeyboardInterrupt:
        logger.info("用户中断操作")
    except Exception as e:
        logger.error(f"执行命令失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()