#!/usr/bin/env python3
"""
核心功能测试 - 只测试导入和基本功能
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_module_imports():
    """测试核心模块导入"""
    print("=== 核心模块导入测试 ===")
    
    modules_to_test = [
        ("配置管理器", "src.core.config_manager"),
        ("配置类", "src.core.config"),
        ("文件类型检测器", "src.core.file_type_detector"),
        ("日志管理器", "src.core.logger_manager"),
        ("日志配置", "src.core.logging_config"),
        ("嵌入引擎", "src.business.embedding_engine"),
        ("处理编排器", "src.business.processing_orchestrator"),
        ("智能检索引擎", "src.business.smart_retrieval"),
        ("媒体处理器", "src.business.media_processor"),
        ("向量存储", "src.storage.vector_store"),
        ("数据库", "src.storage.database"),
        ("API主应用", "src.api.main"),
    ]
    
    results = []
    for name, module_path in modules_to_test:
        try:
            module = __import__(module_path, fromlist=[''])
            print(f"✓ {name} 导入成功")
            results.append(True)
        except Exception as e:
            print(f"✗ {name} 导入失败: {e}")
            results.append(False)
    
    print(f"\n导入测试结果: {sum(results)}/{len(results)} 通过")
    return sum(results) == len(results)

def test_config_loading():
    """测试配置加载"""
    print("\n=== 配置加载测试 ===")
    
    try:
        from src.core.config_manager import get_config_manager
        config_manager = get_config_manager()
        config = config_manager.config
        
        required_keys = [
            'database.sqlite.path',
            'database.qdrant.host', 
            'infinity.services.clip.port'
        ]
        
        missing_keys = []
        for key in required_keys:
            value = config_manager.get(key)
            if value is None:
                missing_keys.append(key)
            else:
                print(f"✓ 配置项 {key} = {value}")
        
        if missing_keys:
            print(f"✗ 缺少配置项: {missing_keys}")
            return False
        else:
            print("✓ 所有必需配置项都存在")
            return True
            
    except Exception as e:
        print(f"✗ 配置加载失败: {e}")
        return False

def test_basic_functionality():
    """测试基本功能"""
    print("\n=== 基本功能测试 ===")
    
    try:
        from src.core.config_manager import get_config_manager
        config_manager = get_config_manager()
        
        # 测试配置管理器
        assert hasattr(config_manager, 'get'), "配置管理器缺少get方法"
        assert hasattr(config_manager, 'set'), "配置管理器缺少set方法"
        print("✓ 配置管理器方法检查通过")
        
        # 测试嵌入引擎类（不初始化）
        from src.business.embedding_engine import EmbeddingEngine
        assert hasattr(EmbeddingEngine, '__init__'), "嵌入引擎类缺少__init__方法"
        print("✓ 嵌入引擎类检查通过")
        
        # 测试处理编排器类（不初始化）
        from src.business.orchestrator import ProcessingOrchestrator
        assert hasattr(ProcessingOrchestrator, '__init__'), "处理编排器类缺少__init__方法"
        print("✓ 处理编排器类检查通过")
        
        return True
        
    except Exception as e:
        print(f"✗ 基本功能测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("msearch 核心功能测试")
    print("=" * 50)
    
    import_success = test_module_imports()
    config_success = test_config_loading()
    function_success = test_basic_functionality()
    
    print("\n" + "=" * 50)
    print("测试总结:")
    print(f"  模块导入: {'通过' if import_success else '失败'}")
    print(f"  配置加载: {'通过' if config_success else '失败'}") 
    print(f"  基本功能: {'通过' if function_success else '失败'}")
    
    if import_success and config_success and function_success:
        print("\n✓ 所有核心功能测试通过！")
        return 0
    else:
        print("\n✗ 部分测试失败，需要进一步检查")
        return 1

if __name__ == "__main__":
    sys.exit(main())