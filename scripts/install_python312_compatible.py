#!/usr/bin/env python3
"""
Python 3.12兼容依赖安装脚本
解决Python 3.12环境下的包兼容性问题
"""

import os
import sys
import subprocess
import logging
import platform
from pathlib import Path

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Python312Installer:
    """Python 3.12兼容安装器"""
    
    def __init__(self):
        self.python_version = sys.version_info
        self.platform = platform.system().lower()
        self.project_root = Path(__file__).parent.parent
        
    def check_python_version(self) -> bool:
        """检查Python版本"""
        logger.info(f"当前Python版本: {self.python_version}")
        
        if self.python_version >= (3, 12):
            logger.info("检测到Python 3.12+，将使用兼容配置")
            return True
        elif self.python_version >= (3, 9):
            logger.info("Python版本兼容")
            return True
        else:
            logger.error(f"Python版本过低: {self.python_version}，需要3.9+")
            return False
    
    def get_compatible_packages(self) -> dict:
        """获取兼容的包版本"""
        
        # Python 3.12兼容的包版本
        packages = {
            # 核心科学计算包
            "numpy": ">=1.24.0",
            "scipy": ">=1.10.0",
            "pandas": ">=2.0.0",
            
            # 深度学习框架
            "torch": ">=2.0.1",
            "torchvision": ">=0.15.2",
            "transformers": ">=4.35.0",
            
            # 图像和视频处理
            "opencv-python-headless": ">=4.8.0",  # 使用headless版本
            "pillow": ">=10.1.0",
            "scikit-image": ">=0.21.0",
            
            # 音频处理
            "librosa": ">=0.10.0",
            "soundfile": ">=0.12.0",
            "pydub": ">=0.25.0",
            
            # Web框架
            "fastapi": ">=0.104.0",
            "uvicorn": ">=0.23.0",
            "pydantic": ">=2.5.0",
            "starlette": ">=0.27.0",
            "httpx": ">=0.25.0",
            "requests": ">=2.31.0",
            "aiohttp": ">=3.8.0",
            "aiofiles": ">=23.0.0",
            "python-multipart": ">=0.0.6",
            
            # 数据库
            "sqlalchemy": ">=2.0.0",
            "qdrant-client": ">=1.6.0",
            
            # 系统工具
            "psutil": ">=5.9.0",
            "watchdog": ">=3.0.0",
            "tqdm": ">=4.65.0",
            "colorama": ">=0.4.0",
            "pyyaml": ">=6.0.1",
            "python-dotenv": ">=1.0.0",
            "chardet": ">=5.0.0",
            
            # 测试工具
            "pytest": ">=7.0.0",
            "pytest-asyncio": ">=0.21.0",
            "pytest-cov": ">=4.0.0",
            "pytest-mock": ">=3.10.0",
            "pytest-timeout": ">=2.1.0",
        }
        
        return packages
    
    def install_system_dependencies(self) -> bool:
        """安装系统依赖"""
        logger.info("检查系统依赖...")
        
        if self.platform == 'linux':
            # 检查是否需要安装系统包
            system_packages = [
                'libgl1-mesa-glx',  # OpenCV依赖
                'libglib2.0-0',     # OpenCV依赖
                'libsm6',           # OpenCV依赖
                'libxext6',         # OpenCV依赖
                'libxrender-dev',   # OpenCV依赖
                'libgomp1',         # 多线程支持
                'libfontconfig1',   # 字体支持
                'libice6',          # X11依赖
                'libxrandr2',       # X11依赖
                'libasound2-dev',   # 音频支持
                'ffmpeg',           # 视频处理
            ]
            
            # 检查apt是否可用
            try:
                subprocess.run(['which', 'apt-get'], check=True, capture_output=True)
                logger.info("检测到apt包管理器，建议手动安装系统依赖:")
                logger.info(f"sudo apt-get update && sudo apt-get install -y {' '.join(system_packages)}")
            except subprocess.CalledProcessError:
                logger.info("未检测到apt包管理器，跳过系统依赖检查")
        
        return True
    
    def install_python_packages(self) -> bool:
        """安装Python包"""
        logger.info("安装Python 3.12兼容的包...")
        
        packages = self.get_compatible_packages()
        
        # 分批安装，避免依赖冲突
        install_groups = [
            # 基础科学计算包
            ["numpy", "scipy", "pandas"],
            
            # 深度学习框架
            ["torch", "torchvision"],
            
            # 图像处理
            ["opencv-python-headless", "pillow", "scikit-image"],
            
            # 音频处理
            ["librosa", "soundfile", "pydub"],
            
            # Web框架
            ["fastapi", "uvicorn", "pydantic", "starlette"],
            
            # HTTP客户端
            ["httpx", "requests", "aiohttp", "aiofiles", "python-multipart"],
            
            # 数据库和存储
            ["sqlalchemy", "qdrant-client"],
            
            # AI模型
            ["transformers"],
            
            # 系统工具
            ["psutil", "watchdog", "tqdm", "colorama", "pyyaml", "python-dotenv", "chardet"],
            
            # 测试工具
            ["pytest", "pytest-asyncio", "pytest-cov", "pytest-mock", "pytest-timeout"],
        ]
        
        for group in install_groups:
            if not self._install_package_group(group, packages):
                logger.error(f"安装包组失败: {group}")
                return False
        
        return True
    
    def _install_package_group(self, group: list, packages: dict) -> bool:
        """安装包组"""
        logger.info(f"安装包组: {group}")
        
        # 构建安装命令
        install_specs = []
        for package in group:
            if package in packages:
                install_specs.append(f"{package}{packages[package]}")
            else:
                install_specs.append(package)
        
        cmd = [
            sys.executable, "-m", "pip", "install",
            "--upgrade", "--no-cache-dir",
            "-i", "https://pypi.tuna.tsinghua.edu.cn/simple",
        ] + install_specs
        
        try:
            logger.info(f"执行: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            if result.returncode == 0:
                logger.info(f"包组安装成功: {group}")
                return True
            else:
                logger.error(f"包组安装失败: {group}")
                logger.error(f"错误输出: {result.stderr}")
                
                # 尝试单独安装每个包
                logger.info("尝试单独安装包...")
                return self._install_packages_individually(install_specs)
                
        except subprocess.TimeoutExpired:
            logger.error(f"包组安装超时: {group}")
            return False
        except Exception as e:
            logger.error(f"包组安装异常: {group} - {e}")
            return False
    
    def _install_packages_individually(self, packages: list) -> bool:
        """单独安装包"""
        success_count = 0
        
        for package in packages:
            cmd = [
                sys.executable, "-m", "pip", "install",
                "--upgrade", "--no-cache-dir",
                "-i", "https://pypi.tuna.tsinghua.edu.cn/simple",
                package
            ]
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                if result.returncode == 0:
                    logger.info(f"包安装成功: {package}")
                    success_count += 1
                else:
                    logger.warning(f"包安装失败: {package} - {result.stderr}")
            except Exception as e:
                logger.warning(f"包安装异常: {package} - {e}")
        
        # 如果大部分包安装成功，认为整体成功
        return success_count >= len(packages) * 0.7
    
    def verify_installation(self) -> bool:
        """验证安装"""
        logger.info("验证安装...")
        
        critical_packages = [
            "numpy", "opencv-python-headless", "torch", "fastapi", 
            "qdrant-client", "pytest", "pyyaml", "requests"
        ]
        
        failed_packages = []
        
        for package in critical_packages:
            try:
                # 尝试导入包
                if package == "opencv-python-headless":
                    import cv2
                    logger.info(f"OpenCV版本: {cv2.__version__}")
                elif package == "numpy":
                    import numpy as np
                    logger.info(f"NumPy版本: {np.__version__}")
                elif package == "torch":
                    import torch
                    logger.info(f"PyTorch版本: {torch.__version__}")
                elif package == "fastapi":
                    import fastapi
                    logger.info(f"FastAPI版本: {fastapi.__version__}")
                elif package == "qdrant-client":
                    import qdrant_client
                    logger.info(f"Qdrant客户端版本: {qdrant_client.__version__}")
                elif package == "pytest":
                    import pytest
                    logger.info(f"Pytest版本: {pytest.__version__}")
                elif package == "pyyaml":
                    import yaml
                    logger.info(f"PyYAML可用")
                elif package == "requests":
                    import requests
                    logger.info(f"Requests版本: {requests.__version__}")
                
            except ImportError as e:
                logger.error(f"包导入失败: {package} - {e}")
                failed_packages.append(package)
        
        if failed_packages:
            logger.error(f"以下关键包导入失败: {failed_packages}")
            return False
        
        logger.info("所有关键包验证通过")
        return True
    
    def setup_environment(self) -> bool:
        """设置环境"""
        logger.info("设置环境变量...")
        
        # 设置OpenCV环境变量
        os.environ['OPENCV_IO_ENABLE_OPENEXR'] = '1'
        os.environ['OPENCV_IO_ENABLE_JASPER'] = '0'
        
        if self.platform == 'linux':
            os.environ['QT_QPA_PLATFORM'] = 'offscreen'
            # 不设置DISPLAY，让系统自动处理
        
        # 设置PyTorch环境变量
        os.environ['TORCH_HOME'] = str(self.project_root / "data" / "models" / "torch")
        
        # 创建必要的目录
        dirs_to_create = [
            self.project_root / "logs",
            self.project_root / "data" / "models",
            self.project_root / "data" / "database" / "qdrant",
            self.project_root / "tests" / "fixtures" / "images",
            self.project_root / "tests" / "fixtures" / "videos",
        ]
        
        for dir_path in dirs_to_create:
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"创建目录: {dir_path}")
        
        return True
    
    def install_all(self) -> bool:
        """完整安装流程"""
        logger.info("开始Python 3.12兼容安装...")
        
        steps = [
            ("检查Python版本", self.check_python_version),
            ("安装系统依赖", self.install_system_dependencies),
            ("安装Python包", self.install_python_packages),
            ("设置环境", self.setup_environment),
            ("验证安装", self.verify_installation),
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
        
        logger.info("Python 3.12兼容安装完成！")
        return True

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Python 3.12兼容依赖安装器")
    parser.add_argument("--check-only", action="store_true", help="只检查环境")
    parser.add_argument("--install-packages", action="store_true", help="只安装Python包")
    parser.add_argument("--verify-only", action="store_true", help="只验证安装")
    
    args = parser.parse_args()
    
    installer = Python312Installer()
    
    if args.check_only:
        success = installer.check_python_version()
    elif args.install_packages:
        success = installer.install_python_packages()
    elif args.verify_only:
        success = installer.verify_installation()
    else:
        success = installer.install_all()
    
    if success:
        logger.info("操作完成")
        sys.exit(0)
    else:
        logger.error("操作失败")
        sys.exit(1)

if __name__ == "__main__":
    main()