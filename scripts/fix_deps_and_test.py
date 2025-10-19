#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
依赖解决和集成测试运行脚本
使用Python实现更可靠的依赖管理和测试执行
"""

import os
import sys
import subprocess
from pathlib import Path
import importlib.util
import time

# 获取项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
print(f"[INFO] 项目根目录: {PROJECT_ROOT}")

# 创建必要的目录
TEMP_DIR = PROJECT_ROOT / "tests" / "temp"
MOCKS_DIR = PROJECT_ROOT / "tests" / "mocks"
TEMP_DIR.mkdir(exist_ok=True)
MOCKS_DIR.mkdir(exist_ok=True)

# 设置环境变量
os.environ["PYTHONWARNINGS"] = "ignore"
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["CUDA_LAUNCH_BLOCKING"] = "1"
os.environ["TEMP_TEST_DIR"] = str(TEMP_DIR)
# 确保不在兼容模式下运行
if "COMPATIBILITY_MODE" in os.environ:
    del os.environ["COMPATIBILITY_MODE"]

def run_command(cmd, cwd=None, timeout=600, shell=False):
    """运行命令并返回结果"""
    print(f"[CMD] {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    try:
        # 对于Windows系统，确保使用正确的编码
        if os.name == 'nt':
            # 使用字节模式运行，然后手动解码
            result = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=False,  # 使用字节模式
                timeout=timeout,
                shell=shell
            )
            
            # 尝试用不同的编码解码输出
            def safe_decode(byte_str):
                if byte_str:
                    for encoding in ['utf-8', 'gbk', 'latin-1']:
                        try:
                            return byte_str.decode(encoding)
                        except UnicodeDecodeError:
                            continue
                    return str(byte_str)
                return ''
            
            stdout = safe_decode(result.stdout)
            stderr = safe_decode(result.stderr)
            
            if stdout:
                print(f"[STDOUT] {stdout.strip()}")
            if stderr:
                print(f"[STDERR] {stderr.strip()}")
                
            # 创建一个简单的结果对象
            class SimpleResult:
                def __init__(self, returncode, stdout, stderr):
                    self.returncode = returncode
                    self.stdout = stdout
                    self.stderr = stderr
            
            return SimpleResult(result.returncode, stdout, stderr)
        else:
            # 非Windows系统使用正常的text模式
            result = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
                shell=shell
            )
            if result.stdout:
                print(f"[STDOUT] {result.stdout.strip()}")
            if result.stderr:
                print(f"[STDERR] {result.stderr.strip()}")
            return result
            
    except Exception as e:
        print(f"[ERROR] 运行命令时出错: {e}")
        return None

def is_package_installed(package_name):
    """检查包是否已安装"""
    try:
        importlib.util.find_spec(package_name)
        return True
    except ImportError:
        return False

def install_package(package_name, extra_index=None):
    """安装Python包"""
    if is_package_installed(package_name):
        print(f"[INFO] 包 {package_name} 已安装，跳过")
        return True
    
    print(f"[INFO] 安装包 {package_name}...")
    cmd = [sys.executable, "-m", "pip", "install", package_name, 
           "-i", "https://pypi.tuna.tsinghua.edu.cn/simple"]
    
    if extra_index:
        cmd.extend(["--extra-index-url", extra_index])
    
    result = run_command(cmd)
    return result and result.returncode == 0

def create_mock_qdrant():
    """创建Qdrant客户端的mock实现"""
    mock_file = MOCKS_DIR / "mock_qdrant.py"
    mock_content = """
import sys
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建基本的模拟类
class MockQdrantClient:
    def __init__(self, *args, **kwargs):
        logger.info("使用模拟的Qdrant客户端，跳过实际连接")
    
    def __getattr__(self, name):
        def mock_method(*args, **kwargs):
            logger.info(f"调用模拟方法: {name} with args={args}, kwargs={kwargs}")
            return None
        return mock_method

# 替换实际模块
sys.modules['qdrant_client'] = type('module', (), {'QdrantClient': MockQdrantClient})
sys.modules['qdrant_client.QdrantClient'] = MockQdrantClient
logger.info("Qdrant客户端已被模拟，测试可以在无实际服务的情况下运行")
"""
    
    with open(mock_file, "w", encoding="utf-8") as f:
        f.write(mock_content)
    
    print(f"[INFO] 创建了Qdrant客户端mock: {mock_file}")

def prepare_test_environment():
    """准备测试环境"""
    # 创建mock qdrant
    create_mock_qdrant()
    
    # 修改测试运行脚本，添加mock路径
    test_script = PROJECT_ROOT / "tests" / "run_integration_tests_fixed.py"
    
    try:
        with open(test_script, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 确保导入了Path
        if "from pathlib import Path" not in content:
            import_pos = content.find("import sys\nimport os")
            if import_pos != -1:
                import_pos = content.find("\n", import_pos) + 1
                content = (content[:import_pos] + 
                          "from pathlib import Path\n" + 
                          content[import_pos:])
        
        # 添加mock模块路径
        if "mocks" not in content:
            mock_path_line = "# 添加mock模块路径\nsys.path.insert(0, str(Path(__file__).parent / 'mocks'))\n"
            if "from pathlib import Path" in content:
                import_pos = content.find("from pathlib import Path\n")
                if import_pos != -1:
                    import_pos += len("from pathlib import Path\n")
                    content = (content[:import_pos] + 
                              mock_path_line + 
                              content[import_pos:])
            else:
                # 如果没有Path导入，使用os.path
                content = content + "\n# 添加mock模块路径\nsys.path.insert(0, os.path.join(os.path.dirname(__file__), 'mocks'))\n"
                
            with open(test_script, "w", encoding="utf-8") as f:
                f.write(content)
                
            print(f"[INFO] 更新了测试脚本，添加了mock路径: {test_script}")
    except Exception as e:
        print(f"[WARNING] 修改测试脚本时出错: {e}")

def install_dependencies():
    """安装必要的依赖"""
    print("[INFO] 开始安装依赖...")
    
    # 先更新pip
    run_command([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    
    # 安装核心依赖
    core_packages = [
        "pytest", "numpy", "pandas", "fastapi", "uvicorn", "pydantic", 
        "starlette", "transformers", "pillow", "opencv-python", "librosa",
        "soundfile", "pydub", "scikit-learn", "openai-whisper", "tqdm",
        "colorama", "pyyaml", "watchdog", "psutil", "httpx", "requests",
        "sqlalchemy", "qdrant-client", "python-magic", "python-magic-bin"
    ]
    
    for package in core_packages:
        install_package(package)
    
    # 特殊处理PyTorch
    print("[INFO] 检查PyTorch...")
    if not is_package_installed("torch"):
        print("[INFO] 安装PyTorch CPU版本...")
        install_package("torch==1.13.1+cpu", "https://download.pytorch.org/whl/cpu")
        install_package("torchvision==0.14.1+cpu", "https://download.pytorch.org/whl/cpu")
    
    # 可选安装，可能引起问题的包
    optional_packages = ["facenet-pytorch", "mtcnn"]
    for package in optional_packages:
        try:
            install_package(package)
        except Exception:
            print(f"[WARNING] 无法安装可选包: {package}")

def run_integration_tests():
    """运行集成测试"""
    print("\n" + "="*50)
    print("[INFO] 开始运行集成测试")
    print("="*50)
    
    test_script = PROJECT_ROOT / "tests" / "run_integration_tests.py"
    result = run_command([sys.executable, str(test_script)], cwd=str(PROJECT_ROOT), timeout=1200)
    
    print("\n" + "="*50)
    if result and result.returncode == 0:
        print("[SUCCESS] 集成测试通过!")
        return True
    else:
        print(f"[INFO] 集成测试完成，返回代码: {result.returncode if result else 'N/A'}")
        return result and result.returncode == 0

def main():
    """主函数"""
    try:
        print("[INFO] 开始解决依赖并运行集成测试...")
        
        # 1. 准备测试环境
        prepare_test_environment()
        
        # 2. 安装依赖
        install_dependencies()
        
        # 3. 运行测试
        success = run_integration_tests()
        
        print("\n[INFO] 执行完成!")
        print("[INFO] 如需完整测试，请先运行 download_model_resources.bat 下载所有离线资源")
        
        return 0 if success else 1
    except Exception as e:
        print(f"[ERROR] 脚本执行时出错: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
