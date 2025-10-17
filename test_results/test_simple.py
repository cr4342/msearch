#!/usr/bin/env python3
"""
简化API功能测试
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_config_manager():
    """测试配置管理器"""
    print("1. 测试配置管理器...")
    try:
        from src.core.config_manager import get_config_manager
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
    print("2. 测试嵌入引擎...")
    try:
        from src.core.config_manager import get_config_manager
        from src.business.embedding_engine import get_embedding_engine
        
        config_manager = get_config_manager()
        config = config_manager.config
        
        # 使用实际的配置结构
        test_config = {
            'infinity': {
                'services': {
                    'clip': {
                        'model_id': 'openai/clip-vit-base-patch32',
                        'device': 'cpu',
                        'max_batch_size': 32,
                        'dtype': 'float16'
                    }
                }
            }
        }
        
        engine = get_embedding_engine(test_config)
        assert hasattr(engine, 'embed_text'), "嵌入引擎缺少embed_text方法"
        assert hasattr(engine, 'embed_image'), "嵌入引擎缺少embed_image方法"
        print("  ✓ 嵌入引擎初始化成功")
        return True
    except Exception as e:
        print(f"  ✗ 嵌入引擎测试失败: {e}")
        return False

def test_processing_orchestrator():
    """测试处理编排器"""
    print("3. 测试处理编排器...")
    try:
        from src.core.config_manager import get_config_manager
        from src.business.processing_orchestrator import ProcessingOrchestrator
        
        config_manager = get_config_manager()
        config = config_manager.config
        
        # 创建处理编排器实例
        orchestrator = ProcessingOrchestrator(config)
        assert hasattr(orchestrator, 'process_file'), "处理编排器缺少process_file方法"
        assert hasattr(orchestrator, 'get_task_status'), "处理编排器缺少get_task_status方法"
        print("  ✓ 处理编排器初始化成功")
        return True
    except Exception as e:
        print(f"  ✗ 处理编排器测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=== 简化功能测试 ===")
    print()
    
    results = []
    results.append(test_config_manager())
    results.append(test_embedding_engine())
    results.append(test_processing_orchestrator())
    
    print()
    print("=== 测试结果 ===")
    passed = sum(results)
    total = len(results)
    print(f"通过测试: {passed}/{total}")
    
    if passed == total:
        print("✓ 所有基础功能测试通过！")
        return 0
    else:
        print(f"✗ 有 {total - passed} 个测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())