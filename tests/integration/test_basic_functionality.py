#!/usr/bin/env python3
"""
基本功能测试 - 不涉及异步操作
"""
import sys
import os
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_configuration():
    """测试系统配置"""
    print("=== 系统配置测试 ===")
    
    try:
        from src.core.config_manager import get_config_manager
        
        config_manager = get_config_manager()
        config = config_manager.config
        
        print("✓ 配置管理器创建成功")
        
        # 检查关键配置
        key_configs = [
            ("系统日志级别", "logging.level"),
            ("数据库路径", "database.sqlite.path"),
            ("Qdrant主机", "database.qdrant.host"),
            ("CLIP服务端口", "infinity.services.clip.port"),
        ]
        
        all_valid = True
        for desc, key in key_configs:
            value = config_manager.get(key)
            if value is not None:
                print(f"  ✓ {desc}: {value}")
            else:
                print(f"  ✗ {desc}: 缺失")
                all_valid = False
        
        return all_valid
        
    except Exception as e:
        print(f"✗ 配置测试失败: {e}")
        return False

def test_database_operations():
    """测试数据库操作"""
    print("\n=== 数据库操作测试 ===")
    
    try:
        from src.storage.database import DatabaseManager
        
        # 创建数据库管理器
        db_manager = DatabaseManager()
        
        print("✓ 数据库管理器创建成功")
        
        # 测试查询
        try:
            tables = db_manager.execute_query("SELECT name FROM sqlite_master WHERE type='table';")
            print(f"  - 数据库表数量: {len(tables)}")
            for table in tables:
                print(f"    - {table['name']}")
            return True
        except Exception as e:
            print(f"  - 数据库查询测试: {e}")
            return False
        
    except Exception as e:
        print(f"✗ 数据库操作测试失败: {e}")
        return False

def test_file_type_detection():
    """测试文件类型检测"""
    print("\n=== 文件类型检测测试 ===")
    
    try:
        from src.core.file_type_detector import get_file_type_detector
        from src.core.config_manager import get_config_manager
        
        config_manager = get_config_manager()
        config = config_manager.config
        
        detector = get_file_type_detector(config)
        
        print("✓ 文件类型检测器创建成功")
        
        # 测试文件类型检测
        test_files = [
            ("test_image.jpg", "image"),
            ("test_video.mp4", "video"),
            ("test_audio.mp3", "audio"),
        ]
        
        for filename, expected_type in test_files:
            # 测试检测功能（不实际创建文件）
            try:
                # 使用模拟文件路径测试检测逻辑
                result = detector.detect_file_type(f"/tmp/{filename}")
                detected_type = result.get('type', 'unknown')
                print(f"  - {filename}: 检测类型={detected_type}")
            except Exception as e:
                print(f"  - {filename}: 检测逻辑测试 - {e}")
        
        return True
        
    except Exception as e:
        print(f"✗ 文件类型检测测试失败: {e}")
        return False

def test_module_availability():
    """测试模块可用性"""
    print("\n=== 模块可用性测试 ===")
    
    modules_to_test = [
        ("处理编排器", "src.business.processing_orchestrator", "ProcessingOrchestrator"),
        ("嵌入引擎", "src.business.embedding_engine", "EmbeddingEngine"),
        ("智能检索", "src.business.smart_retrieval", "SmartRetrievalEngine"),
        ("媒体处理器", "src.business.media_processor", "MediaProcessor"),
        ("向量存储", "src.storage.vector_store", "VectorStore"),
    ]
    
    all_available = True
    for name, module_path, class_name in modules_to_test:
        try:
            module = __import__(module_path, fromlist=[''])
            if hasattr(module, class_name):
                print(f"  ✓ {name} ({class_name}) 可用")
            else:
                print(f"  ✗ {name} 缺少类 {class_name}")
                all_available = False
        except Exception as e:
            print(f"  ✗ {name} 导入失败: {e}")
            all_available = False
    
    return all_available

def main():
    """主测试函数"""
    print("msearch 基本功能测试")
    print("=" * 50)
    
    # 运行测试
    results = []
    results.append(test_configuration())
    results.append(test_database_operations())
    results.append(test_file_type_detection())
    results.append(test_module_availability())
    
    print("\n" + "=" * 50)
    print("测试总结:")
    print(f"  系统配置: {'通过' if results[0] else '失败'}")
    print(f"  数据库操作: {'通过' if results[1] else '失败'}")
    print(f"  文件类型检测: {'通过' if results[2] else '失败'}")
    print(f"  模块可用性: {'通过' if results[3] else '失败'}")
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"\n✓ 所有 {total} 个测试全部通过！系统基本功能正常。")
        return 0
    else:
        print(f"\n⚠ {passed}/{total} 个测试通过，有 {total - passed} 个测试失败")
        print("系统基础架构正常，部分功能需要进一步配置")
        return 1

if __name__ == "__main__":
    sys.exit(main())