#!/usr/bin/env python3
"""
设置测试环境脚本
解决Python环境管理和依赖问题
"""
import os
import sys
import subprocess
import venv
from pathlib import Path
import logging

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_virtual_environment():
    """创建虚拟环境"""
    project_root = Path(__file__).parent
    venv_path = project_root / "venv_test"
    
    if venv_path.exists():
        logger.info(f"虚拟环境已存在: {venv_path}")
        return venv_path
    
    logger.info(f"创建虚拟环境: {venv_path}")
    venv.create(venv_path, with_pip=True)
    
    return venv_path

def install_dependencies(venv_path):
    """安装依赖包"""
    pip_path = venv_path / "bin" / "pip"
    if not pip_path.exists():
        pip_path = venv_path / "Scripts" / "pip.exe"  # Windows
    
    # 基础依赖
    basic_deps = [
        "pytest>=7.0.0",
        "pytest-cov>=4.0.0", 
        "pytest-mock>=3.10.0",
        "pytest-asyncio>=0.21.0",
        "pyyaml>=6.0",
        "numpy>=1.24.0",
        "psutil>=5.9.0",
        "fastapi>=0.100.0",
        "uvicorn>=0.20.0",
        "pydantic>=2.0.0"
    ]
    
    logger.info("安装基础依赖...")
    for dep in basic_deps:
        try:
            subprocess.run([str(pip_path), "install", dep], check=True, capture_output=True)
            logger.info(f"已安装: {dep}")
        except subprocess.CalledProcessError as e:
            logger.warning(f"安装失败: {dep} - {e}")

def setup_test_directories():
    """设置测试目录结构"""
    project_root = Path(__file__).parent
    test_dirs = [
        "tests/deployment_test/logs",
        "tests/deployment_test/config", 
        "tests/deployment_test/data",
        "tests/deployment_test/models",
        "tests/cpu_mode",
        "tests/real_model",
        "tests/performance",
        "tests/integration"
    ]
    
    for test_dir in test_dirs:
        dir_path = project_root / test_dir
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"创建目录: {dir_path}")

def create_mock_models():
    """创建模拟模型文件用于测试"""
    project_root = Path(__file__).parent
    models_dir = project_root / "tests/deployment_test/models"
    
    # 创建模拟模型目录结构
    model_dirs = [
        "clip-vit-base-patch32",
        "clap-htsat-fused", 
        "whisper-base"
    ]
    
    for model_dir in model_dirs:
        model_path = models_dir / model_dir
        model_path.mkdir(parents=True, exist_ok=True)
        
        # 创建模拟配置文件
        config_file = model_path / "config.json"
        with open(config_file, 'w') as f:
            f.write('{"model_type": "mock", "architectures": ["MockModel"]}')
        
        logger.info(f"创建模拟模型: {model_path}")

def create_test_config():
    """创建测试配置文件"""
    project_root = Path(__file__).parent
    config_dir = project_root / "tests/deployment_test/config"
    
    config_content = """
# 测试环境配置
device: cpu
models:
  clip:
    local_path: "./tests/deployment_test/models/clip-vit-base-patch32"
    device: cpu
    batch_size: 2
  clap:
    local_path: "./tests/deployment_test/models/clap-htsat-fused"
    device: cpu
    batch_size: 1
  whisper:
    local_path: "./tests/deployment_test/models/whisper-base"
    device: cpu
    batch_size: 1

processing:
  batch_size: 2
  max_concurrent_tasks: 1

api:
  host: "127.0.0.1"
  port: 8000

logging:
  level: INFO
  handlers:
    console:
      enabled: true
      level: INFO
    file:
      enabled: true
      level: DEBUG
      path: "./tests/deployment_test/logs/test.log"
"""
    
    config_file = config_dir / "test_config.yml"
    with open(config_file, 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    logger.info(f"创建测试配置: {config_file}")

def create_activation_script():
    """创建虚拟环境激活脚本"""
    project_root = Path(__file__).parent
    venv_path = project_root / "venv_test"
    
    # Linux/Mac 激活脚本
    activate_script = project_root / "activate_test_env.sh"
    with open(activate_script, 'w') as f:
        f.write(f"""#!/bin/bash
# 激活测试环境
source {venv_path}/bin/activate
export PYTHONPATH="{project_root}:$PYTHONPATH"
export PYTHONWARNINGS=ignore
echo "测试环境已激活"
echo "Python路径: $(which python)"
echo "项目路径: {project_root}"
""")
    
    os.chmod(activate_script, 0o755)
    logger.info(f"创建激活脚本: {activate_script}")

def main():
    """主函数"""
    logger.info("开始设置测试环境...")
    
    try:
        # 1. 创建虚拟环境
        venv_path = create_virtual_environment()
        
        # 2. 安装依赖
        install_dependencies(venv_path)
        
        # 3. 设置目录结构
        setup_test_directories()
        
        # 4. 创建模拟模型
        create_mock_models()
        
        # 5. 创建测试配置
        create_test_config()
        
        # 6. 创建激活脚本
        create_activation_script()
        
        logger.info("测试环境设置完成！")
        logger.info(f"虚拟环境路径: {venv_path}")
        logger.info("使用方法:")
        logger.info("1. 激活环境: source activate_test_env.sh")
        logger.info("2. 运行测试: ./run_tests_optimized.sh")
        
    except Exception as e:
        logger.error(f"设置测试环境失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()