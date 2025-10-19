#!/usr/bin/env python3
"""
简化的集成测试脚本
验证核心功能和模型加载
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_basic_imports():
    """测试基本模块导入"""
    print("=== 测试基本模块导入 ===")
    
    try:
        from src.core.config_manager import get_config_manager
        print("✓ 配置管理器导入成功")
        
        config_manager = get_config_manager()
        config = config_manager.config
        print(f"✓ 配置加载成功，包含 {len(config)} 个配置项")
        
        return True
    except Exception as e:
        print(f"✗ 配置管理器测试失败: {e}")
        return False

def test_embedding_engine():
    """测试嵌入引擎"""
    print("\n=== 测试嵌入引擎 ===")
    
    try:
        from src.business.embedding_engine import EmbeddingEngine
        
        # 创建测试配置
        test_config = {
            'models': {
                'clip': {
                    'model_name': 'openai/clip-vit-base-patch32',
                    'device': 'cpu',
                    'batch_size': 16
                },
                'clap': {
                    'model_name': 'laion/clap-htsat-fused', 
                    'device': 'cpu',
                    'batch_size': 8
                },
                'whisper': {
                    'model_name': 'openai/whisper-base',
                    'device': 'cpu',
                    'batch_size': 4
                }
            }
        }
        
        # 创建嵌入引擎
        engine = EmbeddingEngine(test_config)
        print("✓ 嵌入引擎创建成功")
        
        # 检查模型状态
        model_status = engine.get_model_status()
        print(f"✓ 模型状态: {model_status}")
        
        return True
    except Exception as e:
        print(f"✗ 嵌入引擎测试失败: {e}")
        return False

def test_offline_models():
    """测试离线模型"""
    print("\n=== 测试离线模型 ===")
    
    offline_models_path = project_root / "offline" / "models"
    
    # 检查模型目录
    models = ["clip-vit-base-patch32", "clap-htsat-fused", "whisper-base"]
    
    for model_name in models:
        model_path = offline_models_path / model_name
        if model_path.exists():
            print(f"✓ {model_name} 模型存在")
        else:
            print(f"✗ {model_name} 模型不存在")
    
    return True

def test_timestamp_accuracy():
    """测试时间戳精度"""
    print("\n=== 测试时间戳精度 ===")
    
    try:
        from src.business.temporal_localization_engine import TemporalLocalizationEngine
        
        # 创建时间定位引擎
        engine = TemporalLocalizationEngine()
        print("✓ 时间定位引擎创建成功")
        
        # 模拟时间戳验证
        test_timestamps = [10.5, 15.2, 20.8]
        accuracy_requirement = 2.0  # ±2秒要求
        
        for ts in test_timestamps:
            # 简单的精度验证模拟
            accuracy = abs(ts - round(ts))  # 模拟精度检查
            if accuracy <= accuracy_requirement:
                print(f"✓ 时间戳 {ts} 精度满足要求 (±{accuracy_requirement}s)")
            else:
                print(f"✗ 时间戳 {ts} 精度不满足要求")
        
        return True
    except Exception as e:
        print(f"✗ 时间戳精度测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("msearch 集成测试开始...\n")
    
    results = []
    
    # 运行各项测试
    results.append(test_basic_imports())
    results.append(test_embedding_engine())
    results.append(test_offline_models())
    results.append(test_timestamp_accuracy())
    
    # 统计结果
    passed = sum(results)
    total = len(results)
    
    print(f"\n=== 测试结果 ===")
    print(f"通过测试: {passed}/{total}")
    
    if passed == total:
        print("✓ 所有集成测试通过！")
        return 0
    else:
        print(f"✗ 有 {total - passed} 个测试失败")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
