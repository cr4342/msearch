#!/usr/bin/env python3
"""
测试环境设置和优化脚本
解决Python 3.12兼容性、Qdrant启动和OpenCV依赖问题
"""

import os
import sys
import subprocess
import platform
import logging
import time
import requests
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TestEnvironmentSetup:
    """测试环境设置类"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.python_version = sys.version_info
        self.platform = platform.system().lower()
        self.arch = platform.machine().lower()
        
    def check_python_compatibility(self) -> bool:
        """检查Python版本兼容性"""
        logger.info(f"检查Python版本: {self.python_version}")
        
        if self.python_version >= (3, 12):
            logger.warning("检测到Python 3.12+，需要特殊处理某些依赖")
            return True
        elif self.python_version >= (3, 9):
            logger.info("Python版本兼容")
            return True
        else:
            logger.error(f"Python版本过低: {self.python_version}，需要3.9+")
            return False
    
    def install_compatible_dependencies(self) -> bool:
        """安装兼容的依赖包"""
        logger.info("安装Python 3.12兼容的依赖包...")
        
        # Python 3.12兼容的依赖版本
        compatible_packages = [
            "numpy>=1.24.0",
            "opencv-python-headless>=4.8.0",  # 使用headless版本避免GUI依赖
            "pillow>=10.1.0",
            "torch>=2.0.1",
            "torchvision>=0.15.2",
            "transformers>=4.35.0",
            "fastapi>=0.104.0",
            "uvicorn>=0.23.0",
            "pydantic>=2.5.0",
            "qdrant-client>=1.6.0",
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "psutil>=5.9.0",
            "pyyaml>=6.0.1",
            "requests>=2.31.0",
            "aiohttp>=3.8.0",
            "librosa>=0.10.0",
            "soundfile>=0.12.0",
        ]
        
        try:
            # 使用清华镜像加速安装
            cmd = [
                sys.executable, "-m", "pip", "install",
                "--upgrade", "--no-cache-dir",
                "-i", "https://pypi.tuna.tsinghua.edu.cn/simple",
            ] + compatible_packages
            
            logger.info("执行安装命令...")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0:
                logger.info("依赖包安装成功")
                return True
            else:
                logger.error(f"依赖包安装失败: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("依赖包安装超时")
            return False
        except Exception as e:
            logger.error(f"依赖包安装异常: {e}")
            return False
    
    def setup_opencv_environment(self) -> bool:
        """设置OpenCV环境"""
        logger.info("设置OpenCV环境...")
        
        try:
            # 测试OpenCV导入
            import cv2
            logger.info(f"OpenCV版本: {cv2.__version__}")
            
            # 设置OpenCV环境变量，避免GUI相关问题
            os.environ['OPENCV_IO_ENABLE_OPENEXR'] = '1'
            os.environ['OPENCV_IO_ENABLE_JASPER'] = '0'
            
            # 在Linux环境下设置显示相关环境变量
            if self.platform == 'linux':
                os.environ['QT_QPA_PLATFORM'] = 'offscreen'
                os.environ['DISPLAY'] = ':99'  # 虚拟显示
            
            return True
            
        except ImportError as e:
            logger.error(f"OpenCV导入失败: {e}")
            logger.info("尝试安装opencv-python-headless...")
            
            try:
                subprocess.run([
                    sys.executable, "-m", "pip", "install",
                    "opencv-python-headless>=4.8.0",
                    "-i", "https://pypi.tuna.tsinghua.edu.cn/simple"
                ], check=True)
                
                import cv2
                logger.info(f"OpenCV安装成功，版本: {cv2.__version__}")
                return True
                
            except Exception as install_error:
                logger.error(f"OpenCV安装失败: {install_error}")
                return False
    
    def setup_qdrant_service(self) -> bool:
        """设置Qdrant服务"""
        logger.info("设置Qdrant服务...")
        
        # 创建数据目录
        qdrant_data_dir = self.project_root / "data" / "database" / "qdrant"
        qdrant_data_dir.mkdir(parents=True, exist_ok=True)
        
        # 检查Qdrant二进制文件
        qdrant_bin = self.project_root / "offline" / "bin" / "qdrant"
        
        if not qdrant_bin.exists():
            logger.warning("Qdrant二进制文件不存在，尝试下载...")
            if not self._download_qdrant_binary():
                logger.error("Qdrant二进制文件下载失败")
                return False
        
        # 设置执行权限
        if self.platform in ['linux', 'darwin']:
            os.chmod(qdrant_bin, 0o755)
        
        return True
    
    def _download_qdrant_binary(self) -> bool:
        """下载Qdrant二进制文件"""
        logger.info("下载Qdrant二进制文件...")
        
        # 根据平台选择下载链接
        if self.platform == 'linux':
            if 'x86_64' in self.arch or 'amd64' in self.arch:
                url = "https://github.com/qdrant/qdrant/releases/latest/download/qdrant-x86_64-unknown-linux-musl.tar.gz"
            else:
                logger.error(f"不支持的Linux架构: {self.arch}")
                return False
        elif self.platform == 'windows':
            url = "https://github.com/qdrant/qdrant/releases/latest/download/qdrant-x86_64-pc-windows-msvc.zip"
        elif self.platform == 'darwin':
            url = "https://github.com/qdrant/qdrant/releases/latest/download/qdrant-x86_64-apple-darwin.tar.gz"
        else:
            logger.error(f"不支持的平台: {self.platform}")
            return False
        
        try:
            # 使用已有的下载脚本
            download_script = self.project_root / "scripts" / "download_qdrant_fixed.sh"
            if download_script.exists():
                result = subprocess.run([str(download_script)], cwd=self.project_root)
                return result.returncode == 0
            else:
                logger.error("下载脚本不存在")
                return False
                
        except Exception as e:
            logger.error(f"下载Qdrant失败: {e}")
            return False
    
    def start_qdrant_service(self) -> bool:
        """启动Qdrant服务"""
        logger.info("启动Qdrant服务...")
        
        try:
            # 检查服务是否已运行
            if self._check_qdrant_health():
                logger.info("Qdrant服务已在运行")
                return True
            
            # 启动服务
            qdrant_bin = self.project_root / "offline" / "bin" / "qdrant"
            config_file = self.project_root / "config" / "qdrant.yml"
            
            if not qdrant_bin.exists():
                logger.error("Qdrant二进制文件不存在")
                return False
            
            if not config_file.exists():
                logger.error("Qdrant配置文件不存在")
                return False
            
            # 启动命令
            cmd = [str(qdrant_bin), "--config-path", str(config_file)]
            
            # 在后台启动服务
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.project_root
            )
            
            # 保存PID
            pid_file = Path("/tmp/qdrant_test.pid")
            pid_file.write_text(str(process.pid))
            
            # 等待服务启动
            for i in range(30):  # 等待30秒
                time.sleep(1)
                if self._check_qdrant_health():
                    logger.info(f"Qdrant服务启动成功，PID: {process.pid}")
                    return True
            
            logger.error("Qdrant服务启动超时")
            process.terminate()
            return False
            
        except Exception as e:
            logger.error(f"启动Qdrant服务失败: {e}")
            return False
    
    def _check_qdrant_health(self) -> bool:
        """检查Qdrant服务健康状态"""
        try:
            response = requests.get("http://localhost:6333/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def stop_qdrant_service(self) -> bool:
        """停止Qdrant服务"""
        logger.info("停止Qdrant服务...")
        
        try:
            pid_file = Path("/tmp/qdrant_test.pid")
            if pid_file.exists():
                pid = int(pid_file.read_text().strip())
                try:
                    os.kill(pid, 15)  # SIGTERM
                    time.sleep(2)
                    os.kill(pid, 9)   # SIGKILL
                except ProcessLookupError:
                    pass  # 进程已不存在
                
                pid_file.unlink()
                logger.info("Qdrant服务已停止")
                return True
            else:
                logger.info("Qdrant服务未运行")
                return True
                
        except Exception as e:
            logger.error(f"停止Qdrant服务失败: {e}")
            return False
    
    def create_test_fixtures(self) -> bool:
        """创建测试固件"""
        logger.info("创建测试固件...")
        
        fixtures_dir = self.project_root / "tests" / "fixtures"
        fixtures_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建图片测试目录
        images_dir = fixtures_dir / "images"
        images_dir.mkdir(exist_ok=True)
        
        # 创建视频测试目录
        videos_dir = fixtures_dir / "videos"
        videos_dir.mkdir(exist_ok=True)
        
        # 创建简单的测试图片
        try:
            import cv2
            import numpy as np
            
            # 创建测试图片
            test_image = np.zeros((100, 100, 3), dtype=np.uint8)
            test_image[:, :] = [255, 0, 0]  # 蓝色图片
            
            test_image_path = images_dir / "test_image.jpg"
            cv2.imwrite(str(test_image_path), test_image)
            
            logger.info(f"创建测试图片: {test_image_path}")
            
        except Exception as e:
            logger.warning(f"创建测试图片失败: {e}")
        
        return True
    
    def setup_test_environment(self) -> bool:
        """完整的测试环境设置"""
        logger.info("开始设置测试环境...")
        
        steps = [
            ("检查Python兼容性", self.check_python_compatibility),
            ("安装兼容依赖", self.install_compatible_dependencies),
            ("设置OpenCV环境", self.setup_opencv_environment),
            ("设置Qdrant服务", self.setup_qdrant_service),
            ("启动Qdrant服务", self.start_qdrant_service),
            ("创建测试固件", self.create_test_fixtures),
        ]
        
        for step_name, step_func in steps:
            logger.info(f"执行步骤: {step_name}")
            try:
                if not step_func():
                    logger.error(f"步骤失败: {step_name}")
                    return False
                logger.info(f"步骤完成: {step_name}")
            except Exception as e:
                logger.error(f"步骤异常: {step_name} - {e}")
                return False
        
        logger.info("测试环境设置完成！")
        return True
    
    def cleanup_test_environment(self) -> bool:
        """清理测试环境"""
        logger.info("清理测试环境...")
        
        # 停止Qdrant服务
        self.stop_qdrant_service()
        
        # 清理临时文件
        temp_files = [
            Path("/tmp/qdrant_test.pid"),
        ]
        
        for temp_file in temp_files:
            if temp_file.exists():
                temp_file.unlink()
        
        logger.info("测试环境清理完成")
        return True

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="测试环境设置工具")
    parser.add_argument("--setup", action="store_true", help="设置测试环境")
    parser.add_argument("--cleanup", action="store_true", help="清理测试环境")
    parser.add_argument("--check", action="store_true", help="检查环境状态")
    
    args = parser.parse_args()
    
    setup = TestEnvironmentSetup()
    
    if args.setup:
        success = setup.setup_test_environment()
        sys.exit(0 if success else 1)
    elif args.cleanup:
        success = setup.cleanup_test_environment()
        sys.exit(0 if success else 1)
    elif args.check:
        # 检查环境状态
        logger.info(f"Python版本: {setup.python_version}")
        logger.info(f"平台: {setup.platform}")
        logger.info(f"架构: {setup.arch}")
        
        # 检查Qdrant服务
        if setup._check_qdrant_health():
            logger.info("Qdrant服务: 运行中")
        else:
            logger.info("Qdrant服务: 未运行")
        
        # 检查OpenCV
        try:
            import cv2
            logger.info(f"OpenCV版本: {cv2.__version__}")
        except ImportError:
            logger.info("OpenCV: 未安装")
        
        sys.exit(0)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()