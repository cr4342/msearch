#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MSearch 真实部署测试脚本
使用offline目录中的依赖进行真实部署和功能测试
"""

import os
import sys
import shutil
import subprocess
import time
import requests
from pathlib import Path

# 设置项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent.absolute()
OFFLINE_DIR = PROJECT_ROOT / "offline"
DEPLOY_DIR = Path(__file__).parent
CONFIG_DIR = DEPLOY_DIR / "config"
DATA_DIR = DEPLOY_DIR / "data"
MODELS_DIR = DEPLOY_DIR / "models"
LOGS_DIR = DEPLOY_DIR / "logs"

def print_status(message, status="INFO"):
    """打印状态信息"""
    colors = {
        "INFO": "\033[94m",
        "SUCCESS": "\033[92m", 
        "WARNING": "\033[93m",
        "ERROR": "\033[91m",
        "RESET": "\033[0m"
    }
    print(f"{colors.get(status, colors['INFO'])}[{status}] {message}{colors['RESET']}")

def run_command(cmd, cwd=None, timeout=300):
    """运行命令并返回结果"""
    print_status(f"执行命令: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd or str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=isinstance(cmd, str)
        )
        
        if result.stdout:
            print(f"输出: {result.stdout.strip()}")
        if result.stderr:
            print(f"错误: {result.stderr.strip()}")
            
        return result
    except subprocess.TimeoutExpired:
        print_status("命令执行超时", "ERROR")
        return None
    except Exception as e:
        print_status(f"命令执行出错: {e}", "ERROR")
        return None

def install_dependencies():
    """安装依赖，优先使用offline目录"""
    print_status("开始安装依赖...")
    
    # 设置环境变量
    os.environ["HF_HOME"] = str(MODELS_DIR / "huggingface")
    os.environ["TRANSFORMERS_CACHE"] = str(MODELS_DIR / "huggingface")
    
    # 检查offline目录中的依赖包
    offline_packages = OFFLINE_DIR / "packages" / "requirements"
    
    if offline_packages.exists():
        print_status("发现离线依赖包，优先使用离线安装...")
        
        # 使用离线包安装
        cmd = [
            sys.executable, "-m", "pip", "install",
            "--no-index",
            "--find-links", str(offline_packages),
            "-r", str(PROJECT_ROOT / "requirements.txt")
        ]
        
        result = run_command(cmd)
        if result and result.returncode == 0:
            print_status("离线依赖安装成功", "SUCCESS")
        else:
            print_status("离线安装失败，尝试在线安装...", "WARNING")
            # 回退到在线安装
            cmd = [
                sys.executable, "-m", "pip", "install",
                "-r", str(PROJECT_ROOT / "requirements.txt"),
                "-i", "https://pypi.tuna.tsinghua.edu.cn/simple"
            ]
            run_command(cmd)
    else:
        print_status("未找到离线依赖包，使用在线安装...", "WARNING")
        cmd = [
            sys.executable, "-m", "pip", "install",
            "-r", str(PROJECT_ROOT / "requirements.txt"),
            "-i", "https://pypi.tuna.tsinghua.edu.cn/simple"
        ]
        run_command(cmd)
    
    # 安装测试依赖
    print_status("安装测试依赖...")
    test_deps = [
        "pytest", "pytest-cov", "httpx", "requests"
    ]
    for dep in test_deps:
        cmd = [sys.executable, "-m", "pip", "install", dep, 
               "-i", "https://pypi.tuna.tsinghua.edu.cn/simple"]
        run_command(cmd)

def setup_config():
    """设置配置文件"""
    print_status("设置配置文件...")
    
    # 复制主配置文件
    main_config = PROJECT_ROOT / "config" / "config.yml"
    deploy_config = CONFIG_DIR / "config.yml"
    
    if main_config.exists():
        shutil.copy2(main_config, deploy_config)
        print_status("主配置文件已复制", "SUCCESS")
    else:
        print_status("主配置文件不存在，创建默认配置...", "WARNING")
        create_default_config(deploy_config)
    
    # 创建部署专用配置
    deploy_env = DEPLOY_DIR / "deploy_env.py"
    with open(deploy_env, "w", encoding="utf-8") as f:
        f.write(f"""
# 部署环境配置
import os
os.environ["DEPLOY_ROOT"] = r"{DEPLOY_DIR}"
os.environ["DEPLOY_CONFIG"] = r"{CONFIG_DIR}"
os.environ["DEPLOY_DATA"] = r"{DATA_DIR}"
os.environ["DEPLOY_MODELS"] = r"{MODELS_DIR}"
os.environ["DEPLOY_LOGS"] = r"{LOGS_DIR}"
os.environ["PYTHONPATH"] = f"{PROJECT_ROOT};{DEPLOY_DIR}"
os.environ["HF_HOME"] = r"{MODELS_DIR}/huggingface"
os.environ["TRANSFORMERS_CACHE"] = r"{MODELS_DIR}/huggingface"
""")
    
    print_status("配置文件设置完成", "SUCCESS")

def create_default_config(config_path):
    """创建默认配置文件"""
    config_content = f"""
system:
  name: "MSearch Deployment Test"
  version: "3.0"
  debug: true
  log_level: "INFO"

paths:
  data_dir: "{DATA_DIR}"
  models_dir: "{MODELS_DIR}"
  logs_dir: "{LOGS_DIR}"
  temp_dir: "{DATA_DIR}/temp"

database:
  sqlite:
    path: "{DATA_DIR}/database/msearch.db"
  qdrant:
    host: "localhost"
    port: 6333
    timeout: 30

infinity_services:
  clip:
    model_name: "clip-vit-base-patch32"
    port: 7997
    device: "cpu"
  clap:
    model_name: "clap-htsat-fused"
    port: 7998
    device: "cpu"
  whisper:
    model_name: "whisper-base"
    port: 7999
    device: "cpu"

processing:
  batch_size: 4
  max_workers: 2
  timeout: 300

testing:
  use_mock_services: false
  skip_gpu_tests: true
  enable_detailed_logging: true
"""
    
    with open(config_path, "w", encoding="utf-8") as f:
        f.write(config_content)

def setup_models():
    """设置模型，使用offline目录中的模型"""
    print_status("设置AI模型...")
    
    # 检查offline目录中的模型
    offline_models = OFFLINE_DIR / "models"
    
    if offline_models.exists():
        print_status("发现离线模型文件，创建符号链接...")
        
        model_links = [
            ("clip-vit-base-patch32", "clip"),
            ("clap-htsat-fused", "clap"),
            ("whisper-base", "whisper"),
            ("insightface", "insightface")
        ]
        
        for src_name, dst_name in model_links:
            src_model = offline_models / src_name
            dst_model = MODELS_DIR / dst_name
            
            if src_model.exists():
                if dst_model.exists():
                    shutil.rmtree(dst_model)
                
                # Windows下使用junction或直接复制
                try:
                    dst_model.symlink_to(src_model, target_is_directory=True)
                    print_status(f"创建模型符号链接: {dst_name}", "SUCCESS")
                except OSError:
                    # 如果符号链接失败，则复制
                    shutil.copytree(src_model, dst_model)
                    print_status(f"复制模型文件: {dst_name}", "SUCCESS")
            else:
                print_status(f"模型不存在: {src_name}", "WARNING")
    else:
        print_status("未找到离线模型文件，将在运行时下载...", "WARNING")

def start_services():
    """启动必要的服务"""
    print_status("启动服务...")
    
    # 启动Qdrant服务
    print_status("启动Qdrant向量数据库服务...")
    qdrant_cmd = f"start \"Qdrant Deploy\" cmd /c \"{PROJECT_ROOT}\\scripts\\start_qdrant.bat\""
    run_command(qdrant_cmd)
    
    # 等待Qdrant启动
    print_status("等待Qdrant服务启动...")
    time.sleep(10)
    
    # 启动API服务
    print_status("启动MSearch API服务...")
    api_cmd = f"start \"MSearch API Deploy\" cmd /c \"cd {PROJECT_ROOT} && set PYTHONPATH={DEPLOY_DIR} && python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload\""
    run_command(api_cmd)
    
    # 等待API服务启动
    print_status("等待API服务启动...")
    time.sleep(15)
    
    print_status("服务启动完成", "SUCCESS")

def test_api_health():
    """测试API健康状态"""
    print_status("测试API健康状态...")
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=10)
        if response.status_code == 200:
            print_status("API健康检查通过", "SUCCESS")
            return True
        else:
            print_status(f"API健康检查失败: {response.status_code}", "WARNING")
            return False
    except Exception as e:
        print_status(f"API连接失败: {e}", "ERROR")
        return False

def test_basic_functionality():
    """测试基本功能"""
    print_status("测试基本功能...")
    
    # 测试文本搜索
    try:
        search_data = {
            "query": "test search",
            "modality": "text",
            "limit": 5
        }
        response = requests.post("http://localhost:8000/search", 
                               json=search_data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            print_status(f"搜索测试通过，返回 {len(result.get('results', []))} 个结果", "SUCCESS")
            return True
        else:
            print_status(f"搜索测试失败: {response.status_code}", "WARNING")
            return False
    except Exception as e:
        print_status(f"搜索测试失败: {e}", "ERROR")
        return False

def run_unit_tests():
    """运行单元测试"""
    print_status("运行单元测试...")
    
    # 设置测试环境
    os.environ["PYTHONPATH"] = f"{PROJECT_ROOT};{DEPLOY_DIR}"
    
    # 运行单元测试
    cmd = [
        sys.executable, "-m", "pytest", 
        str(PROJECT_ROOT / "tests" / "unit"),
        "-v", "--tb=short", "--maxfail=5"
    ]
    
    result = run_command(cmd, timeout=600)
    
    if result and result.returncode == 0:
        print_status("单元测试通过", "SUCCESS")
        return True
    else:
        print_status("单元测试失败", "WARNING")
        return False

def main():
    """主函数"""
    print_status("开始MSearch真实部署测试...", "INFO")
    print_status(f"项目根目录: {PROJECT_ROOT}")
    print_status(f"部署目录: {DEPLOY_DIR}")
    print_status(f"离线资源目录: {OFFLINE_DIR}")
    
    try:
        # 1. 安装依赖
        print_status("\n=== 步骤1: 安装依赖 ===")
        install_dependencies()
        
        # 2. 设置配置
        print_status("\n=== 步骤2: 设置配置 ===")
        setup_config()
        
        # 3. 设置模型
        print_status("\n=== 步骤3: 设置模型 ===")
        setup_models()
        
        # 4. 启动服务
        print_status("\n=== 步骤4: 启动服务 ===")
        start_services()
        
        # 5. 测试API
        print_status("\n=== 步骤5: 测试API ===")
        api_health = test_api_health()
        
        # 6. 测试基本功能
        print_status("\n=== 步骤6: 测试基本功能 ===")
        basic_test = test_basic_functionality()
        
        # 7. 运行单元测试
        print_status("\n=== 步骤7: 运行单元测试 ===")
        unit_test_result = run_unit_tests()
        
        # 输出测试结果
        print_status("\n=== 测试结果汇总 ===")
        print_status(f"API健康检查: {'通过' if api_health else '失败'}", 
                   "SUCCESS" if api_health else "ERROR")
        print_status(f"基本功能测试: {'通过' if basic_test else '失败'}", 
                   "SUCCESS" if basic_test else "ERROR")
        print_status(f"单元测试: {'通过' if unit_test_result else '失败'}", 
                   "SUCCESS" if unit_test_result else "ERROR")
        
        if api_health and basic_test and unit_test_result:
            print_status("所有测试通过！", "SUCCESS")
            return 0
        else:
            print_status("部分测试失败，请检查日志", "WARNING")
            return 1
            
    except KeyboardInterrupt:
        print_status("用户中断了部署测试", "WARNING")
        return 1
    except Exception as e:
        print_status(f"部署测试失败: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())