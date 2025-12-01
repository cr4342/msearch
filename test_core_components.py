#!/usr/bin/env python3
"""
msearch 多模态检索系统核心组件综合测试
验证所有核心模块的基本导入和初始化功能
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(project_root, 'src'))

def test_core_components():
    """测试核心组件"""
    print("🚀 开始msearch核心组件综合测试...")
    print("=" * 60)
    
    test_results = []
    
    # 1. 配置管理器
    try:
        from src.core.config_manager import ConfigManager
        config_manager = ConfigManager()
        test_results.append(("配置管理器", "✅ PASS", None))
        print("✅ 配置管理器: 导入和初始化成功")
    except Exception as e:
        test_results.append(("配置管理器", "❌ FAIL", str(e)))
        print(f"❌ 配置管理器: 失败 - {e}")
    
    # 2. 数据库适配器
    try:
        from src.common.storage.database_adapter import DatabaseAdapter
        db_adapter = DatabaseAdapter()
        test_results.append(("数据库适配器", "✅ PASS", None))
        print("✅ 数据库适配器: 导入和初始化成功")
    except Exception as e:
        test_results.append(("数据库适配器", "❌ FAIL", str(e)))
        print(f"❌ 数据库适配器: 失败 - {e}")
    
    # 3. 向量化引擎
    try:
        from src.common.embedding.embedding_engine import EmbeddingEngine
        test_results.append(("向量化引擎", "✅ PASS", None))
        print("✅ 向量化引擎: 导入成功")
    except Exception as e:
        test_results.append(("向量化引擎", "❌ FAIL", str(e)))
        print(f"❌ 向量化引擎: 失败 - {e}")
    
    # 4. 文件监控器
    try:
        from src.processing_service.file_monitor import FileMonitor, FileMonitorHandler
        test_results.append(("文件监控器", "✅ PASS", None))
        print("✅ 文件监控器: 导入成功")
    except Exception as e:
        test_results.append(("文件监控器", "❌ FAIL", str(e)))
        print(f"❌ 文件监控器: 失败 - {e}")
    
    # 5. 媒体处理器
    try:
        from src.processing_service.media_processor import MediaProcessor
        test_results.append(("媒体处理器", "✅ PASS", None))
        print("✅ 媒体处理器: 导入成功")
    except Exception as e:
        test_results.append(("媒体处理器", "❌ FAIL", str(e)))
        print(f"❌ 媒体处理器: 失败 - {e}")
    
    # 6. 智能检索引擎
    try:
        from src.search_service.smart_retrieval_engine import SmartRetrievalEngine
        test_results.append(("智能检索引擎", "✅ PASS", None))
        print("✅ 智能检索引擎: 导入成功")
    except Exception as e:
        test_results.append(("智能检索引擎", "❌ FAIL", str(e)))
        print(f"❌ 智能检索引擎: 失败 - {e}")
    
    # 7. 处理调度器
    try:
        from src.processing_service.orchestrator import ProcessingOrchestrator
        test_results.append(("处理调度器", "✅ PASS", None))
        print("✅ 处理调度器: 导入成功")
    except Exception as e:
        test_results.append(("处理调度器", "❌ FAIL", str(e)))
        print(f"❌ 处理调度器: 失败 - {e}")
    
    # 8. 任务管理器
    try:
        from src.processing_service.task_manager import TaskManager
        test_results.append(("任务管理器", "✅ PASS", None))
        print("✅ 任务管理器: 导入成功")
    except Exception as e:
        test_results.append(("任务管理器", "❌ FAIL", str(e)))
        print(f"❌ 任务管理器: 失败 - {e}")
    
    # 9. 错误处理系统
    try:
        from src.utils.error_handling import ErrorHandler, ErrorClassifier, RetryManager, GracefulDegradationManager
        test_results.append(("错误处理系统", "✅ PASS", None))
        print("✅ 错误处理系统: 导入成功")
    except Exception as e:
        test_results.append(("错误处理系统", "❌ FAIL", str(e)))
        print(f"❌ 错误处理系统: 失败 - {e}")
    
    # 10. 性能优化组件
    try:
        from src.core.cache_manager import CacheManager
        from src.core.performance_monitor import PerformanceMonitor
        from src.core.batch_processor import BatchProcessor
        test_results.append(("性能优化组件", "✅ PASS", None))
        print("✅ 性能优化组件: 导入成功")
    except Exception as e:
        test_results.append(("性能优化组件", "❌ FAIL", str(e)))
        print(f"❌ 性能优化组件: 失败 - {e}")
    
    print("\n" + "=" * 60)
    print("📊 测试结果汇总:")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for component, status, error in test_results:
        if status == "✅ PASS":
            passed += 1
            print(f"{component:<20} {status}")
        else:
            failed += 1
            print(f"{component:<20} {status}")
            if error:
                print(f"  错误详情: {error}")
    
    print("-" * 60)
    print(f"总计: {len(test_results)} 个组件")
    print(f"通过: {passed} 个")
    print(f"失败: {failed} 个")
    print(f"成功率: {passed/len(test_results)*100:.1f}%")
    
    if failed == 0:
        print("\n🎉 所有核心组件测试通过！")
        return True
    else:
        print(f"\n⚠️  有 {failed} 个组件测试失败")
        return False

if __name__ == "__main__":
    success = test_core_components()
    sys.exit(0 if success else 1)