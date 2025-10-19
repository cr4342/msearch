#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MSearch 使用Mock的测试脚本
"""

import os
import sys
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

def setup_mocks():
    """设置Mock"""
    print_status("设置Mock...")
    
    try:
        # 导入Mock嵌入引擎
        mock_engine_path = PROJECT_ROOT / "tests" / "deployment_test" / "mock_embedding_engine.py"
        if mock_engine_path.exists():
            exec(open(mock_engine_path).read())
            print_status("✓ Mock嵌入引擎设置成功")
            return True
        else:
            print_status("✗ Mock引擎文件不存在", "ERROR")
            return False
    except Exception as e:
        print_status(f"✗ Mock设置失败: {e}", "ERROR")
        return False

def test_api_startup():
    """测试API启动"""
    print_status("测试API启动...")
    
    try:
        # 设置Mock
        if not setup_mocks():
            return False
        
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

def test_embedding_engine():
    """测试嵌入引擎"""
    print_status("测试嵌入引擎...")
    
    try:
        # 设置Mock
        if not setup_mocks():
            return False
        
        from src.business.embedding_engine import EmbeddingEngine
        
        config = {
            'models': {
                'clip': {
                    'model_name': 'clip-vit-base-patch32',
                    'device': 'cpu'
                }
            }
        }
        
        engine = EmbeddingEngine(config)
        print_status("✓ 嵌入引擎创建成功")
        
        # 测试模型健康状态
        if engine.get_model_health('clip'):
            print_status("✓ CLIP模型健康状态正常")
        
        return True
    except Exception as e:
        print_status(f"嵌入引擎测试失败: {e}", "ERROR")
        return False

def main():
    """主函数"""
    print_status("开始MSearch Mock测试...", "INFO")
    print_status(f"项目根目录: {PROJECT_ROOT}")
    
    tests = [
        ("基本功能测试", test_basic_functionality),
        ("嵌入引擎测试", test_embedding_engine),
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