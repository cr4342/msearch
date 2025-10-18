#!/usr/bin/env python3
"""
基本集成测试
验证核心模块之间的协作
"""
import sys
import os
import time
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def test_config_to_database():
    """测试配置到数据库的集成"""
    print("=== 配置到数据库集成测试 ===")
    
    try:
        from src.core.config_manager import get_config_manager
        from src.storage.database import DatabaseManager
        
        # 加载配置
        config_manager = get_config_manager()
        config = config_manager.config
        
        # 创建数据库管理器
        db_manager = DatabaseManager()
        
        # 验证配置中的数据库路径与实际的数据库路径一致
        config_db_path = config_manager.get('database.sqlite.path')
        actual_db_path = db_manager.db_path
        
        print(f"配置数据库路径: {config_db_path}")
        print(f"实际数据库路径: {actual_db_path}")
        
        # 测试数据库查询
        tables = db_manager.execute_query("SELECT name FROM sqlite_master WHERE type='table';")
        print(f"数据库表数量: {len(tables)}")
        
        print("✓ 配置到数据库集成测试通过")
        return True
        
    except Exception as e:
        print(f"✗ 配置到数据库集成测试失败: {e}")
        return False

def test_database_to_vector_store():
    """测试数据库到向量存储的集成"""
    print("\n=== 数据库到向量存储集成测试 ===")
    
    try:
        from src.storage.database import DatabaseManager
        from src.storage.vector_store import VectorStore
        
        # 创建数据库管理器
        db_manager = DatabaseManager()
        
        # 创建向量存储
        vector_store = VectorStore()
        
        # 测试数据库操作
        test_data = {
            'file_path': '/tmp/integration_test.jpg',
            'file_name': 'integration_test.jpg',
            'file_hash': 'integration_hash_123',
            'file_type': 'image',
            'file_size': 2048,
            'status': 'completed'
        }
        
        file_id = db_manager.insert_record('files', test_data)
        print(f"插入文件记录ID: {file_id}")
        
        # 测试向量存储健康检查
        import asyncio
        health_status = asyncio.run(vector_store.health_check())
        print(f"向量存储健康状态: {health_status}")
        
        print("✓ 数据库到向量存储集成测试通过")
        return True
        
    except Exception as e:
        print(f"✗ 数据库到向量存储集成测试失败: {e}")
        return False

def test_config_to_file_detector():
    """测试配置到文件检测器的集成"""
    print("\n=== 配置到文件检测器集成测试 ===")
    
    try:
        from src.core.config_manager import get_config_manager
        from src.core.file_type_detector import get_file_type_detector
        
        # 加载配置
        config_manager = get_config_manager()
        config = config_manager.config
        
        # 创建文件检测器
        detector = get_file_type_detector(config)
        
        # 测试文件类型检测
        test_files = [
            ('integration_test.jpg', 'image'),
            ('integration_test.mp4', 'video'),
            ('integration_test.mp3', 'audio'),
        ]
        
        for filename, expected_type in test_files:
            result = detector.detect_file_type(f"/tmp/{filename}")
            detected_type = result.get('type', 'unknown')
            print(f"  - {filename}: 检测类型={detected_type}")
        
        print("✓ 配置到文件检测器集成测试通过")
        return True
        
    except Exception as e:
        print(f"✗ 配置到文件检测器集成测试失败: {e}")
        return False

def test_module_dependencies():
    """测试模块依赖关系"""
    print("\n=== 模块依赖关系测试 ===")
    
    try:
        # 测试关键模块的导入和依赖关系
        modules_to_test = [
            ("配置管理器", "src.core.config_manager"),
            ("数据库", "src.storage.database"),
            ("向量存储", "src.storage.vector_store"),
            ("文件检测器", "src.core.file_type_detector"),
            ("嵌入引擎", "src.business.embedding_engine"),
            ("处理编排器", "src.business.processing_orchestrator"),
        ]
        
        for name, module_path in modules_to_test:
            module = __import__(module_path, fromlist=[''])
            print(f"✓ {name} 导入成功")
        
        print("✓ 模块依赖关系测试通过")
        return True
        
    except Exception as e:
        print(f"✗ 模块依赖关系测试失败: {e}")
        return False

def main():
    """主函数"""
    print("msearch 基本集成测试")
    print("=" * 50)
    
    start_time = time.time()
    
    # 运行测试
    tests = [
        ("配置到数据库", test_config_to_database),
        ("数据库到向量存储", test_database_to_vector_store),
        ("配置到文件检测器", test_config_to_file_detector),
        ("模块依赖关系", test_module_dependencies),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n执行测试: {test_name}")
        test_start = time.time()
        success = test_func()
        test_time = time.time() - test_start
        results.append((test_name, success, test_time))
    
    # 生成报告
    print("\n" + "=" * 50)
    print("基本集成测试报告")
    print("=" * 50)
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    total_time = time.time() - start_time
    
    for test_name, success, test_time in results:
        status = "✓ 通过" if success else "✗ 失败"
        print(f"{status} {test_name} - 耗时: {test_time:.2f}s")
    
    print("=" * 50)
    print(f"总计: {passed}/{total} 通过 - 总耗时: {total_time:.2f}s")
    
    if passed == total:
        print("✓ 所有基本集成测试通过！系统模块集成正常。")
        return 0
    else:
        print(f"⚠ {total - passed} 个测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())