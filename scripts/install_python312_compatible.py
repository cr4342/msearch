#!/usr/bin/env python3
"""
Python 3.12兼容性安装脚本
解决Python 3.12环境下的依赖包兼容性问题
"""
import os
import sys
import subprocess
import logging
import time
from pathlib import Path
from typing import List, Dict, Optional

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Python312CompatibilityInstaller:
    """Python 3.12兼容性安装器"""
    
    def __init__(self):
        self.python_version = sys.version_info
        self.is_python312 = self.python_version >= (3, 12)
        self.project_root = Path(__file__).parent.parent
        
        # Python 3.12兼容的包版本
        self.compatible_packages = {
            # 核心依赖
            'numpy': '>=1.24.0',
            'pandas': '>=2.0.0',
            'pydantic': '>=2.5.0',
            'fastapi': '>=0.104.0',
            'uvicorn': '>=0.23.0',
            
            # AI/ML依赖
            'torch': '>=2.0.1',
            'torchvision': '>=0.15.2',
            'transformers': '>=4.35.0',
            'sentence-transformers': '>=2.2.0',
            
            # 图像处理 - 使用headless版本避免GUI依赖
            'opencv-python-headless': '>=4.8.0',
            'Pillow': '>=10.1.0',
            'scikit-image': '>=0.21.0',
            
            # 音频处理
            'librosa': '>=0.10.0',
            'soundfile': '>=0.12.0',
            'pydub': '>=0.25.0',
            
            # 科学计算
            'scipy': '>=1.10.0',
            'scikit-learn': '>=1.3.0',
            
            # 系统工具
            'psutil': '>=5.9.0',
            'tqdm': '>=4.65.0',
            'pyyaml': '>=6.0.1',
            'python-dotenv': '>=1.0.0',
            
            # 测试工具
            'pytest': '>=7.4.0',
            'pytest-cov': '>=4.1.0',
            'pytest-asyncio': '>=0.21.0',
            'pytest-mock': '>=3.11.0',
            
            # HTTP客户端
            'httpx': '>=0.25.0',
            'requests': '>=2.31.0',
            'aiohttp': '>=3.8.0',
            'aiofiles': '>=23.0.0',
            
            # 数据库
            'sqlalchemy': '>=2.0.0',
        }
        
        # 可选包（如果安装失败不影响核心功能）
        self.optional_packages = {
            'infinity-emb[all]': '>=0.0.20',
            'qdrant-client': '>=1.6.0',
            'optimum[onnxruntime]': '>=1.14.0',
            'accelerate': '>=0.20.0',
        }
        
        # 系统依赖
        self.system_dependencies = {
            'ubuntu': [
                'build-essential',
                'libssl-dev',
                'libffi-dev',
                'python3-dev',
                'libgl1-mesa-glx',
                'libglib2.0-0',
                'libsm6',
                'libxext6',
                'libxrender-dev',
                'libgomp1',
                'libfontconfig1'
            ],
            'centos': [
                'gcc',
                'gcc-c++',
                'openssl-devel',
                'libffi-devel',
                'python3-devel'
            ]
        }
    
    def check_python_version(self) -> bool:
        """检查Python版本"""
        logger.info(f"Python版本: {self.python_version.major}.{self.python_version.minor}.{self.python_version.micro}")
        
        if self.python_version < (3, 9):
            logger.error("Python版本过低，需要Python 3.9或更高版本")
            return False
        elif self.python_version >= (3, 12):
            logger.warning("检测到Python 3.12，将使用兼容性安装模式")
            return True
        else:
            logger.info("Python版本兼容")
            return True
    
    def install_system_dependencies(self) -> bool:
        """安装系统依赖"""
        logger.info("检查并安装系统依赖...")
        
        try:
            # 检测系统类型
            if os.path.exists('/etc/debian_version'):
                system_type = 'ubuntu'
                package_manager = 'apt-get'
            elif os.path.exists('/etc/redhat-release'):
                system_type = 'centos'
                package_manager = 'yum'
            else:
                logger.warning("未识别的系统类型，跳过系统依赖安装")
                return True
            
            dependencies = self.system_dependencies.get(system_type, [])
            if not dependencies:
                logger.info("无需安装系统依赖")
                return True
            
            # 更新包管理器
            if system_type == 'ubuntu':
                subprocess.run(['sudo', 'apt-get', 'update'], check=False)
                install_cmd = ['sudo', 'apt-get', 'install', '-y'] + dependencies
            else:
                install_cmd = ['sudo', 'yum', 'install', '-y'] + dependencies
            
            logger.info(f"安装系统依赖: {' '.join(dependencies)}")
            result = subprocess.run(install_cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("系统依赖安装成功")
                return True
            else:
                logger.warning(f"系统依赖安装失败: {result.stderr}")
                return False
                
        except Exception as e:
            logger.warning(f"系统依赖安装异常: {e}")
            return False
    
    def upgrade_pip(self) -> bool:
        """升级pip"""
        logger.info("升级pip...")
        
        try:
            result = subprocess.run([
                sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("pip升级成功")
                return True
            else:
                logger.warning(f"pip升级失败: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"pip升级异常: {e}")
            return False
    
    def install_package(self, package: str, version: str = None, optional: bool = False) -> bool:
        """安装单个包"""
        package_spec = f"{package}{version}" if version else package
        
        try:
            logger.info(f"安装包: {package_spec}")
            
            # 使用国内镜像加速
            cmd = [
                sys.executable, '-m', 'pip', 'install',
                package_spec,
                '-i', 'https://pypi.tuna.tsinghua.edu.cn/simple',
                '--timeout', '120',
                '--retries', '3'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"✅ {package} 安装成功")
                return True
            else:
                if optional:
                    logger.warning(f"⚠️ 可选包 {package} 安装失败: {result.stderr}")
                else:
                    logger.error(f"❌ {package} 安装失败: {result.stderr}")
                return False
                
        except Exception as e:
            if optional:
                logger.warning(f"⚠️ 可选包 {package} 安装异常: {e}")
            else:
                logger.error(f"❌ {package} 安装异常: {e}")
            return False
    
    def install_core_packages(self) -> bool:
        """安装核心包"""
        logger.info("安装核心Python包...")
        
        success_count = 0
        total_count = len(self.compatible_packages)
        
        for package, version in self.compatible_packages.items():
            if self.install_package(package, version, optional=False):
                success_count += 1
            else:
                # 如果指定版本失败，尝试安装最新版本
                logger.warning(f"尝试安装 {package} 的最新版本...")
                if self.install_package(package, optional=False):
                    success_count += 1
        
        success_rate = success_count / total_count
        logger.info(f"核心包安装完成: {success_count}/{total_count} ({success_rate:.1%})")
        
        return success_rate >= 0.8  # 至少80%的核心包安装成功
    
    def install_optional_packages(self) -> bool:
        """安装可选包"""
        logger.info("安装可选Python包...")
        
        success_count = 0
        total_count = len(self.optional_packages)
        
        for package, version in self.optional_packages.items():
            if self.install_package(package, version, optional=True):
                success_count += 1
        
        success_rate = success_count / total_count if total_count > 0 else 1.0
        logger.info(f"可选包安装完成: {success_count}/{total_count} ({success_rate:.1%})")
        
        return True  # 可选包失败不影响整体安装
    
    def verify_installation(self) -> bool:
        """验证安装"""
        logger.info("验证安装结果...")
        
        # 关键模块验证
        critical_modules = [
            'numpy',
            'torch',
            'transformers',
            'fastapi',
            'pydantic'
        ]
        
        failed_modules = []
        
        for module in critical_modules:
            try:
                __import__(module)
                logger.info(f"✅ {module} 导入成功")
            except ImportError as e:
                logger.error(f"❌ {module} 导入失败: {e}")
                failed_modules.append(module)
        
        if failed_modules:
            logger.error(f"关键模块导入失败: {failed_modules}")
            return False
        
        # 可选模块验证
        optional_modules = [
            'infinity_emb',
            'cv2',
            'PIL'
        ]
        
        for module in optional_modules:
            try:
                __import__(module)
                logger.info(f"✅ {module} 导入成功")
            except ImportError:
                logger.warning(f"⚠️ 可选模块 {module} 未安装")
        
        logger.info("安装验证完成")
        return True
    
    def create_environment_script(self) -> bool:
        """创建环境设置脚本"""
        logger.info("创建环境设置脚本...")
        
        try:
            env_script = self.project_root / 'set_python312_env.sh'
            
            with open(env_script, 'w') as f:
                f.write("""#!/bin/bash
# Python 3.12环境设置脚本

# 设置环境变量
export PYTHONWARNINGS=ignore
export KMP_DUPLICATE_LIB_OK=TRUE
export CUDA_LAUNCH_BLOCKING=1

# OpenCV无头模式
export QT_QPA_PLATFORM=offscreen
export OPENCV_IO_ENABLE_OPENEXR=1
export OPENCV_IO_ENABLE_JASPER=0

# 设置Python路径
export PYTHONPATH="$(pwd):${PYTHONPATH}"

echo "Python 3.12环境变量已设置"
echo "使用方法: source set_python312_env.sh"
""")
            
            os.chmod(env_script, 0o755)
            logger.info(f"环境脚本已创建: {env_script}")
            return True
            
        except Exception as e:
            logger.error(f"创建环境脚本失败: {e}")
            return False
    
    def run_installation(self, check_only: bool = False, verify_only: bool = False) -> bool:
        """运行完整安装流程"""
        logger.info("开始Python 3.12兼容性安装...")
        
        if verify_only:
            return self.verify_installation()
        
        # 检查Python版本
        if not self.check_python_version():
            return False
        
        if check_only:
            logger.info("仅检查模式，跳过安装")
            return True
        
        # 安装系统依赖
        self.install_system_dependencies()
        
        # 升级pip
        if not self.upgrade_pip():
            logger.warning("pip升级失败，但继续安装")
        
        # 安装核心包
        if not self.install_core_packages():
            logger.error("核心包安装失败")
            return False
        
        # 安装可选包
        self.install_optional_packages()
        
        # 验证安装
        if not self.verify_installation():
            logger.error("安装验证失败")
            return False
        
        # 创建环境脚本
        self.create_environment_script()
        
        logger.info("Python 3.12兼容性安装完成！")
        return True

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Python 3.12兼容性安装脚本')
    parser.add_argument('--check-only', action='store_true', help='仅检查环境，不安装')
    parser.add_argument('--verify-only', action='store_true', help='仅验证安装结果')
    parser.add_argument('--install-packages', action='store_true', help='重新安装问题包')
    
    args = parser.parse_args()
    
    installer = Python312CompatibilityInstaller()
    
    try:
        success = installer.run_installation(
            check_only=args.check_only,
            verify_only=args.verify_only
        )
        
        if success:
            print("\n🎉 安装成功！")
            print("使用方法:")
            print("1. source set_python312_env.sh  # 设置环境变量")
            print("2. python3 -c \"import torch; print('PyTorch版本:', torch.__version__)\"")
            return 0
        else:
            print("\n❌ 安装失败，请检查日志")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️ 安装被用户中断")
        return 1
    except Exception as e:
        logger.error(f"安装过程异常: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())