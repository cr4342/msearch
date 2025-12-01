"""
Qdrant服务管理器
提供Qdrant数据库的启动、停止、健康检查等功能
"""

import asyncio
import logging
import os
import signal
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, Optional

from src.core.config_manager import get_config_manager


class QdrantServiceManager:
    """Qdrant服务管理器"""
    
    def __init__(self, config_manager=None):
        self.config_manager = config_manager or get_config_manager()
        self.logger = logging.getLogger(__name__)
        
        # 配置
        self.host = self.config_manager.get("database.qdrant.host", "localhost")
        self.port = self.config_manager.get("database.qdrant.port", 6333)
        self.data_dir = self._get_data_directory()
        
        # 进程管理
        self.process: Optional[subprocess.Popen] = None
        self.is_running = False
        
        # Docker相关 - 优先使用二进制，Docker作为备选
        self.use_docker = False  # 单机版优先使用二进制
        self.docker_available = self._check_docker_availability()
        
        self.logger.info(f"Qdrant服务管理器初始化完成: {self.host}:{self.port}")
        self.logger.info("🔧 配置为单机二进制版本启动")
    
    def _get_data_directory(self) -> str:
        """获取数据目录"""
        system_data_dir = self.config_manager.get("system.data_dir", "./data")
        return os.path.join(system_data_dir, "qdrant")
    
    def _check_docker_availability(self) -> bool:
        """检查Docker是否可用"""
        try:
            result = subprocess.run(['docker', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    async def start(self, force_restart: bool = False) -> bool:
        """启动Qdrant服务"""
        try:
            # 检查是否已经在运行
            if self.is_running and not force_restart:
                if await self.health_check():
                    self.logger.info("Qdrant服务已在运行")
                    return True
                else:
                    self.logger.warning("Qdrant服务异常，正在重启")
                    await self.stop()
            
            # 确保数据目录存在
            Path(self.data_dir).mkdir(parents=True, exist_ok=True)
            
            # 单机版优先使用二进制启动
            self.logger.info("🚀 启动Qdrant服务 (单机二进制版本)")
            
            # 首先尝试二进制启动
            success = await self._start_with_binary()
            if not success and self.docker_available:
                self.logger.warning("二进制启动失败，回退到Docker模式")
                success = await self._start_with_docker()
            
            return success
                
        except Exception as e:
            self.logger.error(f"启动Qdrant服务失败: {e}")
            return False
    
    async def _start_with_docker(self) -> bool:
        """使用Docker启动Qdrant"""
        try:
            # 检查容器是否已存在
            container_name = "msearch-qdrant"
            
            # 停止现有容器
            await self._stop_docker_container(container_name)
            
            # 构建Docker命令
            docker_cmd = [
                'docker', 'run', '-d',
                '--name', container_name,
                '-p', f'{self.port}:6333',
                '-p', f'{self.port + 1}:6334',  # gRPC端口
                '-v', f'{self.data_dir}:/qdrant/storage',
                '--restart', 'unless-stopped',
                'qdrant/qdrant:latest'
            ]
            
            self.logger.info(f"启动Qdrant Docker容器: {' '.join(docker_cmd)}")
            
            # 启动容器
            result = subprocess.run(docker_cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                self.logger.error(f"Docker启动失败: {result.stderr}")
                return False
            
            # 等待服务就绪
            success = await self._wait_for_ready()
            
            if success:
                self.is_running = True
                self.logger.info("Qdrant Docker容器启动成功")
            else:
                self.logger.error("Qdrant Docker容器启动失败")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Docker启动失败: {e}")
            return False
    
    async def _start_with_binary(self) -> bool:
        """使用二进制文件启动Qdrant"""
        try:
            # 检查Qdrant是否已安装
            qdrant_path = await self._download_qdrant_binary()
            if not qdrant_path:
                return False
            
            # 启动参数
            cmd = [
                qdrant_path,
                '--host', self.host,
                '--port', str(self.port),
                '--storage-path', self.data_dir
            ]
            
            self.logger.info(f"启动Qdrant进程: {' '.join(cmd)}")
            
            # 启动进程
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid  # 创建新的进程组
            )
            
            # 等待服务就绪
            success = await self._wait_for_ready()
            
            if success:
                self.is_running = True
                self.logger.info("Qdrant进程启动成功")
            else:
                self.logger.error("Qdrant进程启动失败")
            
            return success
            
        except Exception as e:
            self.logger.error(f"二进制启动失败: {e}")
            return False
    
    async def _download_qdrant_binary(self) -> Optional[str]:
        """下载Qdrant二进制文件（单机版）"""
        try:
            # 获取系统信息
            import platform
            system = platform.system().lower()
            machine = platform.machine().lower()
            
            # 选择合适的二进制文件
            if system == 'linux':
                if machine in ['x86_64', 'amd64']:
                    binary_name = 'qdrant-x86_64-unknown-linux-musl'
                else:
                    self.logger.error(f"不支持的机器架构: {machine}")
                    return None
            elif system == 'darwin':
                if machine in ['x86_64', 'amd64']:
                    binary_name = 'qdrant-x86_64-apple-darwin'
                elif machine in ['arm64', 'aarch64']:
                    binary_name = 'qdrant-aarch64-apple-darwin'
                else:
                    self.logger.error(f"不支持的机器架构: {machine}")
                    return None
            else:
                self.logger.error(f"不支持的操作系统: {system}")
                return None
            
            # 创建下载目录
            bin_dir = os.path.join(self.data_dir, 'bin')
            os.makedirs(bin_dir, exist_ok=True)
            
            binary_path = os.path.join(bin_dir, binary_name)
            
            # 检查是否已存在
            if os.path.exists(binary_path) and os.access(binary_path, os.X_OK):
                self.logger.info(f"✅ 使用已存在的Qdrant二进制文件: {binary_path}")
                return binary_path
            
            # 下载URL
            version = "v1.7.0"  # 使用稳定版本
            download_url = f"https://github.com/qdrant/qdrant/releases/download/{version}/{binary_name}"
            
            self.logger.info(f"📥 下载Qdrant {version} (单机二进制版本)")
            self.logger.info(f"📍 下载地址: {download_url}")
            self.logger.info(f"📂 保存到: {binary_path}")
            
            # 下载文件
            import requests
            response = requests.get(download_url, timeout=300)
            response.raise_for_status()
            
            # 写入文件
            with open(binary_path, 'wb') as f:
                f.write(response.content)
            
            # 设置执行权限
            os.chmod(binary_path, 0o755)
            
            # 验证文件
            file_size = os.path.getsize(binary_path)
            if file_size < 1024 * 1024:  # 小于1MB可能是错误页面
                self.logger.error("下载的文件太小，可能是404或错误页面")
                os.remove(binary_path)
                return None
            
            self.logger.info(f"✅ Qdrant {version} 下载完成 ({file_size / 1024 / 1024:.1f}MB)")
            return binary_path
            
        except Exception as e:
            self.logger.error(f"❌ 下载Qdrant失败: {e}")
            return None
    
    async def _stop_docker_container(self, container_name: str):
        """停止Docker容器"""
        try:
            # 检查容器是否存在
            result = subprocess.run(
                ['docker', 'ps', '--format', '{{.Names}}'],
                capture_output=True, text=True
            )
            
            if container_name in result.stdout:
                # 停止容器
                subprocess.run(
                    ['docker', 'rm', '-f', container_name],
                    capture_output=True, text=True
                )
                self.logger.debug(f"已停止Docker容器: {container_name}")
                
        except Exception as e:
            self.logger.warning(f"停止Docker容器失败: {e}")
    
    async def _wait_for_ready(self, timeout: int = 30) -> bool:
        """等待服务就绪"""
        try:
            import requests
            
            url = f"http://{self.host}:{self.port}/health"
            
            for i in range(timeout * 2):  # 每0.5秒检查一次
                try:
                    response = requests.get(url, timeout=2)
                    if response.status_code == 200:
                        self.logger.info("Qdrant服务就绪")
                        return True
                except requests.exceptions.RequestException:
                    pass
                
                await asyncio.sleep(0.5)
            
            self.logger.error(f"Qdrant服务启动超时 ({timeout}秒)")
            return False
            
        except Exception as e:
            self.logger.error(f"等待服务就绪失败: {e}")
            return False
    
    async def stop(self) -> bool:
        """停止Qdrant服务"""
        try:
            if self.use_docker:
                return await self._stop_docker()
            else:
                return await self._stop_binary()
                
        except Exception as e:
            self.logger.error(f"停止Qdrant服务失败: {e}")
            return False
    
    async def _stop_docker(self) -> bool:
        """停止Docker容器"""
        try:
            container_name = "msearch-qdrant"
            
            # 检查容器是否存在
            result = subprocess.run(
                ['docker', 'ps', '--format', '{{.Names}}'],
                capture_output=True, text=True
            )
            
            if container_name not in result.stdout:
                self.logger.info("Docker容器不存在")
                return True
            
            # 停止容器
            result = subprocess.run(
                ['docker', 'rm', '-f', container_name],
                capture_output=True, text=True
            )
            
            success = result.returncode == 0
            
            if success:
                self.is_running = False
                self.logger.info("Qdrant Docker容器已停止")
            else:
                self.logger.error(f"停止Docker容器失败: {result.stderr}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"停止Docker容器异常: {e}")
            return False
    
    async def _stop_binary(self) -> bool:
        """停止二进制进程（单机版）"""
        try:
            if not self.process:
                self.logger.info("Qdrant进程未运行（无活跃进程）")
                self.is_running = False
                return True
            
            if self.process.poll() is None:  # 进程仍在运行
                self.logger.info("🔄 停止Qdrant进程（单机二进制版本）")
                
                try:
                    # 首先尝试优雅终止
                    os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                    self.process.wait(timeout=5)
                    self.logger.info("✅ Qdrant进程已优雅停止")
                    
                except subprocess.TimeoutExpired:
                    # 强制杀死
                    self.logger.warning("优雅停止超时，强制终止进程")
                    os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                    self.process.wait()
                    self.logger.info("✅ Qdrant进程已强制停止")
                    
            else:
                self.logger.info("Qdrant进程已自然退出")
            
            self.is_running = False
            self.process = None
            return True
                
        except Exception as e:
            self.logger.error(f"❌ 停止二进制进程失败: {e}")
            self.is_running = False
            return False
    
    async def restart(self) -> bool:
        """重启Qdrant服务"""
        try:
            self.logger.info("重启Qdrant服务")
            await self.stop()
            await asyncio.sleep(2)  # 等待端口释放
            return await self.start(force_restart=True)
        except Exception as e:
            self.logger.error(f"重启Qdrant服务失败: {e}")
            return False
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            import requests
            
            url = f"http://{self.host}:{self.port}/health"
            response = requests.get(url, timeout=5)
            
            return response.status_code == 200
            
        except requests.exceptions.RequestException:
            return False
        except Exception as e:
            self.logger.error(f"Qdrant健康检查异常: {e}")
            return False
    
    async def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        try:
            is_healthy = await self.health_check()
            
            status_info = {
                'running': self.is_running and is_healthy,
                'healthy': is_healthy,
                'host': self.host,
                'port': self.port,
                'data_dir': self.data_dir,
                'method': 'docker' if self.use_docker else 'binary'
            }
            
            # 如果正在运行，获取详细信息
            if is_healthy:
                try:
                    import requests
                    
                    # 获取版本信息
                    response = requests.get(f"http://{self.host}:{self.port}/", timeout=5)
                    status_info['version'] = response.json().get('version', 'unknown')
                    
                    # 获取集合信息
                    collections_response = requests.get(
                        f"http://{self.host}:{self.port}/collections",
                        timeout=5
                    )
                    if collections_response.status_code == 200:
                        collections = collections_response.json()
                        status_info['collections_count'] = len(collections.get('result', {}).get('collections', []))
                    
                except Exception as e:
                    self.logger.warning(f"获取详细信息失败: {e}")
                    status_info['error'] = str(e)
            
            return status_info
            
        except Exception as e:
            self.logger.error(f"获取Qdrant状态失败: {e}")
            return {
                'running': False,
                'healthy': False,
                'error': str(e),
                'host': self.host,
                'port': self.port
            }
    
    async def install_dependencies(self) -> bool:
        """安装依赖"""
        try:
            if self.use_docker:
                self.logger.info("使用Docker，无需额外安装依赖")
                return True
            
            # 检查curl（用于健康检查）
            try:
                subprocess.run(['curl', '--version'], 
                             capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                self.logger.warning("curl未找到，某些功能可能受限")
            
            return True
            
        except Exception as e:
            self.logger.error(f"安装依赖失败: {e}")
            return False
    
    async def setup(self) -> bool:
        """设置环境"""
        try:
            # 安装依赖
            if not await self.install_dependencies():
                return False
            
            # 创建数据目录
            Path(self.data_dir).mkdir(parents=True, exist_ok=True)
            
            self.logger.info("Qdrant环境设置完成")
            return True
            
        except Exception as e:
            self.logger.error(f"设置Qdrant环境失败: {e}")
            return False