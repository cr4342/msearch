#!/usr/bin/env python3
"""
简化的API集成测试
跳过有外部依赖的模块
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

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

def test_database_manager():
    """测试数据库管理器"""
    print("2. 测试数据库管理器...")
    try:
        from src.storage.database import DatabaseManager
        db_manager = DatabaseManager()
        
        # 测试数据库连接
        tables = db_manager.execute_query("SELECT name FROM sqlite_master WHERE type='table';")
        assert len(tables) > 0, "数据库中没有表"
        print(f"  ✓ 数据库管理器测试成功，表数量: {len(tables)}")
        return True
    except Exception as e:
        print(f"  ✗ 数据库管理器测试失败: {e}")
        return False

def test_vector_store():
    """测试向量存储"""
    print("3. 测试向量存储...")
    try:
        from src.storage.vector_store import VectorStore
        vector_store = VectorStore()
        
        # 测试向量存储初始化
        assert hasattr(vector_store, 'client'), "向量存储缺少client属性"
        print("  ✓ 向量存储初始化成功")
        return True
    except Exception as e:
        print(f"  ✗ 向量存储测试失败: {e}")
        return False

def test_file_type_detector():
    """测试文件类型检测器"""
    print("4. 测试文件类型检测器...")
    try:
        from src.core.config_manager import get_config_manager
        from src.core.file_type_detector import get_file_type_detector
        
        config_manager = get_config_manager()
        detector = get_file_type_detector(config_manager.config)
        
        # 测试基于扩展名的检测
        result = detector.detect_file_type("test.jpg")
        assert 'type' in result, "检测结果缺少type字段"
        print(f"  ✓ 文件类型检测器测试成功，检测结果: {result}")
        return True
    except Exception as e:
        print(f"  ✗ 文件类型检测器测试失败: {e}")
        return False

def test_task_manager():
    """测试任务管理器"""
    print("5. 测试任务管理器...")
    try:
        from src.business.task_manager import TaskManager
        from src.core.config_manager import get_config_manager
        
        config_manager = get_config_manager()
        
        # 测试任务管理器类是否可以导入
        assert TaskManager is not None, "任务管理器类导入失败"
        print("  ✓ 任务管理器类导入成功（跳过初始化测试）")
        return True
    except Exception as e:
        print(f"  ✗ 任务管理器测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=== 简化API集成测试 ===")
    print()
    
    tests = [
        ("配置管理器", test_config_manager),
        ("数据库管理器", test_database_manager),
        ("向量存储", test_vector_store),
        ("文件类型检测器", test_file_type_detector),
        ("任务管理器", test_task_manager),
    ]
    
    results = []
    for test_name, test_func in tests:
        success = test_func()
        results.append((test_name, success))
    
    print()
    print("=== 测试结果 ===")
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "通过" if success else "失败"
        print(f"{status}: {test_name}")
    
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("✓ 所有简化API集成测试通过！")
        return 0
    else:
        print(f"✗ 有 {total - passed} 个测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())