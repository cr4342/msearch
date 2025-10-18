#!/usr/bin/env python3
"""
快速模块导入测试 - 不初始化复杂组件
"""
import sys
import os
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_import_without_init():
    """测试模块导入但不初始化"""
    print("=== 快速模块导入测试 ===")
    
    modules_to_test = [
        ("配置管理器", "src.core.config_manager", "get_config_manager"),
        ("配置类", "src.core.config", "load_config"),
        ("文件类型检测器", "src.core.file_type_detector", "get_file_type_detector"),
        ("日志管理器", "src.core.logger_manager", "get_logger"),
        ("日志配置", "src.core.logging_config", "setup_logging"),
        ("嵌入引擎", "src.business.embedding_engine", "EmbeddingEngine"),
        ("处理编排器", "src.business.processing_orchestrator", "ProcessingOrchestrator"),
        ("智能检索引擎", "src.business.smart_retrieval", "SmartRetrievalEngine"),
        ("媒体处理器", "src.business.media_processor", "MediaProcessor"),
        ("向量存储", "src.storage.vector_store", "VectorStore"),
        ("数据库", "src.storage.database", "DatabaseManager"),
    ]
    
    results = []
    for name, module_path, attr_name in modules_to_test:
        try:
            start_time = time.time()
            module = __import__(module_path, fromlist=[''])
            if hasattr(module, attr_name):
                print(f"✓ {name} 导入成功 - 耗时: {time.time()-start_time:.2f}s")
                results.append(True)
            else:
                print(f"⚠ {name} 导入成功但缺少属性 {attr_name} - 耗时: {time.time()-start_time:.2f}s")
                results.append(False)
        except Exception as e:
            print(f"✗ {name} 导入失败: {e}")
            results.append(False)
    
    print(f"\n导入测试结果: {sum(results)}/{len(results)} 通过")
    return sum(results) == len(results)

def test_config_access():
    """测试配置访问"""
    print("\n=== 配置访问测试 ===")
    
    try:
        from src.core.config_manager import get_config_manager
        config_manager = get_config_manager()
        
        # 检查必需配置项
        required_configs = [
            ("数据库SQLite路径", "database.sqlite.path"),
            ("Qdrant主机", "database.qdrant.host"),
            ("CLIP服务端口", "infinity.services.clip.port"),
            ("日志级别", "logging.level"),
        ]
        
        all_present = True
        for desc, key in required_configs:
            value = config_manager.get(key)
            if value is not None:
                print(f"✓ {desc}: {value}")
            else:
                print(f"✗ {desc}: 缺失")
                all_present = False
        
        return all_present
        
    except Exception as e:
        print(f"✗ 配置访问失败: {e}")
        return False

def main():
    """主测试函数"""
    print("msearch 快速模块导入测试")
    print("=" * 50)
    
    import_success = test_import_without_init()
    config_success = test_config_access()
    
    print("\n" + "=" * 50)
    print("测试总结:")
    print(f"  模块导入: {'通过' if import_success else '失败'}")
    print(f"  配置访问: {'通过' if config_success else '失败'}") 
    
    if import_success and config_success:
        print("\n✓ 所有快速测试通过！系统基础架构正常。")
        return 0
    else:
        print("\n✗ 部分测试失败，需要进一步检查")
        return 1

if __name__ == "__main__":
    sys.exit(main())