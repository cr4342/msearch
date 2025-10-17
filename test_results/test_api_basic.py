#!/usr/bin/env python3
"""
测试API基础功能
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api.main import app
from src.core.config_manager import get_config_manager
from src.business.embedding_engine import get_embedding_engine

def test_api_app():
    """测试API应用实例"""
    print("1. 测试API应用实例...")
    try:
        assert hasattr(app, 'routes'), "FastAPI应用缺少routes属性"
        assert hasattr(app, 'openapi'), "FastAPI应用缺少openapi属性"
        print("  ✓ FastAPI应用初始化成功")
        return True
    except Exception as e:
        print(f"  ✗ FastAPI应用测试失败: {e}")
        return False

def test_config_manager():
    """测试配置管理器"""
    print("2. 测试配置管理器...")
    try:
        config_manager = get_config_manager()
        config = config_manager.config
        assert isinstance(config, dict), "配置不是字典类型"
        assert len(config) > 0, "配置为空"
        print(f"  ✓ 配置管理器测试成功，配置项数: {len(config)}")
        return True
    except Exception as e:
        print(f"  ✗ 配置管理器测试失败: {e}")
        return False

def test_embedding_engine():
    """测试嵌入引擎"""
    print("3. 测试嵌入引擎...")
    try:
        config_manager = get_config_manager()
        config = config_manager.config
        
        # 创建测试配置
        test_config = {
            'features': {
                'enable_clip': True,
                'enable_clap': True,
                'enable_whisper': True
            },
            'models': {
                'clip_model': 'openai/clip-vit-base-patch32',
                'clap_model': 'laion/clap-htsat-fused',
                'whisper_model': 'openai/whisper-base'
            },
            'device': 'cpu'
        }
        
        engine = get_embedding_engine(test_config)
        assert hasattr(engine, 'embed_text'), "嵌入引擎缺少embed_text方法"
        assert hasattr(engine, 'embed_image'), "嵌入引擎缺少embed_image方法"
        print("  ✓ 嵌入引擎初始化成功")
        return True
    except Exception as e:
        print(f"  ✗ 嵌入引擎测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=== API基础功能测试 ===")
    print()
    
    results = []
    results.append(test_api_app())
    results.append(test_config_manager())
    results.append(test_embedding_engine())
    
    print()
    print("=== 测试结果 ===")
    passed = sum(results)
    total = len(results)
    print(f"通过测试: {passed}/{total}")
    
    if passed == total:
        print("✓ 所有基础功能测试通过！")
    else:
        print(f"✗ 有 {total - passed} 个测试失败")

if __name__ == "__main__":
    main()