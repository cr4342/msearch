#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MSearch 简化部署测试脚本
用于验证基本功能和模型加载
"""

import os
import sys
import time
from pathlib import Path

# 设置项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

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

def test_basic_imports():
    """测试基本导入"""
    print_status("测试基本导入...")
    
    try:
        # 测试核心模块导入
        from src.core.config import load_config
        print_status("✓ config模块导入成功")
        
        from src.core.logging_config import setup_logging
        print_status("✓ logging_config模块导入成功")
        
        from src.core.config_manager import get_config_manager
        print_status("✓ config_manager模块导入成功")
        
        return True
    except Exception as e:
        print_status(f"基本导入失败: {e}", "ERROR")
        return False

def test_model_loading():
    """测试模型加载"""
    print_status("测试模型加载...")
    
    try:
        # 设置环境变量
        os.environ["HF_HOME"] = str(PROJECT_ROOT / "offline" / "models")
        os.environ["TRANSFORMERS_CACHE"] = str(PROJECT_ROOT / "offline" / "models")
        
        # 测试CLIP模型
        from transformers import CLIPModel, CLIPProcessor
        
        clip_path = PROJECT_ROOT / "offline" / "models" / "clip-vit-base-patch32"
        if clip_path.exists():
            print_status("加载CLIP模型...")
            clip_model = CLIPModel.from_pretrained(str(clip_path), local_files_only=True)
            clip_processor = CLIPProcessor.from_pretrained(str(clip_path), local_files_only=True)
            print_status("✓ CLIP模型加载成功", "SUCCESS")
        else:
            print_status("CLIP模型路径不存在，尝试在线加载...", "WARNING")
            clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
            clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
            print_status("✓ CLIP模型在线加载成功", "SUCCESS")
        
        # 测试CLAP模型
        from transformers import CLAPModel, CLAPProcessor
        
        clap_path = PROJECT_ROOT / "offline" / "models" / "clap-htsat-fused"
        if clap_path.exists():
            print_status("加载CLAP模型...")
            clap_model = CLAPModel.from_pretrained(str(clap_path), local_files_only=True)
            clap_processor = CLAPProcessor.from_pretrained(str(clap_path), local_files_only=True)
            print_status("✓ CLAP模型加载成功", "SUCCESS")
        else:
            print_status("CLAP模型路径不存在，跳过...", "WARNING")
        
        # 测试Whisper模型
        from transformers import WhisperForConditionalGeneration, WhisperProcessor
        
        whisper_path = PROJECT_ROOT / "offline" / "models" / "whisper-base"
        if whisper_path.exists():
            print_status("加载Whisper模型...")
            whisper_model = WhisperForConditionalGeneration.from_pretrained(str(whisper_path), local_files_only=True)
            whisper_processor = WhisperProcessor.from_pretrained(str(whisper_path), local_files_only=True)
            print_status("✓ Whisper模型加载成功", "SUCCESS")
        else:
            print_status("Whisper模型路径不存在，跳过...", "WARNING")
        
        return True
    except Exception as e:
        print_status(f"模型加载失败: {e}", "ERROR")
        return False

def test_basic_functionality():
    """测试基本功能"""
    print_status("测试基本功能...")
    
    try:
        # 测试配置加载
        from src.core.config import load_config
        config = load_config()
        print_status("✓ 配置加载成功")
        
        # 测试日志设置
        from src.core.logging_config import setup_logging
        setup_logging(config)
        print_status("✓ 日志设置成功")
        
        # 测试配置管理器
        from src.core.config_manager import get_config_manager
        config_manager = get_config_manager()
        print_status("✓ 配置管理器初始化成功")
        
        return True
    except Exception as e:
        print_status(f"基本功能测试失败: {e}", "ERROR")
        return False

def test_api_startup():
    """测试API启动"""
    print_status("测试API启动...")
    
    try:
        # 测试API导入
        from src.api.main import app
        print_status("✓ API应用导入成功")
        
        # 测试API配置
        print(f"API标题: {app.title}")
        print(f"API版本: {app.version}")
        print_status("✓ API配置检查成功")
        
        return True
    except Exception as e:
        print_status(f"API启动测试失败: {e}", "ERROR")
        return False

def main():
    """主函数"""
    print_status("开始MSearch简化部署测试...", "INFO")
    print_status(f"项目根目录: {PROJECT_ROOT}")
    
    tests = [
        ("基本导入测试", test_basic_imports),
        ("模型加载测试", test_model_loading),
        ("基本功能测试", test_basic_functionality),
        ("API启动测试", test_api_startup)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print_status(f"\n=== {test_name} ===")
        try:
            if test_func():
                passed += 1
                print_status(f"{test_name}通过", "SUCCESS")
            else:
                print_status(f"{test_name}失败", "ERROR")
        except Exception as e:
            print_status(f"{test_name}异常: {e}", "ERROR")
    
    print_status(f"\n=== 测试结果汇总 ===")
    print_status(f"通过: {passed}/{total}", "SUCCESS" if passed == total else "WARNING")
    
    if passed == total:
        print_status("所有测试通过！", "SUCCESS")
        return 0
    else:
        print_status("部分测试失败", "WARNING")
        return 1

if __name__ == "__main__":
    sys.exit(main())