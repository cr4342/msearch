#!/usr/bin/env python3
"""
综合集成测试
按照设计文档和测试策略要求进行全面测试
"""
import sys
import os
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def test_system_architecture():
    """测试系统架构完整性"""
    print("=== 系统架构完整性测试 ===")
    
    # 测试分层架构
    layers = {
        "用户界面层": ["src.gui"],
        "API服务层": ["src.api"],
        "业务逻辑层": ["src.business"],
        "存储层": ["src.storage"],
        "核心组件层": ["src.core"],
        "处理器层": ["src.processors"],
    }
    
    results = {}
    for layer_name, modules in layers.items():
        try:
            for module_path in modules:
                __import__(module_path, fromlist=[''])
            results[layer_name] = True
            print(f"  ✓ {layer_name}: 导入成功")
        except Exception as e:
            results[layer_name] = False
            print(f"  ✗ {layer_name}: 导入失败 - {e}")
    
    return results

def test_configuration_driven_architecture():
    """测试配置驱动架构"""
    print("\n=== 配置驱动架构测试 ===")
    
    try:
        from src.core.config_manager import get_config_manager
        
        config_manager = get_config_manager()
        config = config_manager.config
        
        # 验证关键配置项
        required_configs = [
            'general',
            'features', 
            'models',
            'processing',
            'database',
            'logging'
        ]
        
        missing_configs = []
        for config_key in required_configs:
            if config_key not in config:
                missing_configs.append(config_key)
            else:
                print(f"  ✓ 配置项 '{config_key}' 存在")
        
        if missing_configs:
            print(f"  ✗ 缺少配置项: {missing_configs}")
            return False
        
        print("  ✓ 配置驱动架构验证通过")
        return True
        
    except Exception as e:
        print(f"  ✗ 配置驱动架构测试失败: {e}")
        return False

def test_data_storage_integration():
    """测试数据存储集成"""
    print("\n=== 数据存储集成测试 ===")
    
    try:
        from src.storage.database import DatabaseManager
        from src.storage.vector_store import VectorStore
        
        # 测试SQLite数据库
        db_manager = DatabaseManager()
        tables = db_manager.execute_query("SELECT name FROM sqlite_master WHERE type='table';")
        print(f"  ✓ SQLite数据库: {len(tables)} 个表")
        
        # 测试向量存储
        vector_store = VectorStore()
        print("  ✓ 向量存储: 初始化成功")
        
        return True
        
    except Exception as e:
        print(f"  ✗ 数据存储集成测试失败: {e}")
        return False

def test_timestamp_accuracy_requirements():
    """测试时间戳精度要求"""
    print("\n=== 时间戳精度要求测试 ===")
    
    try:
        from src.processors.timestamp_processor import TimestampProcessor
        
        processor = TimestampProcessor()
        
        # 测试帧级精度计算
        fps = 30.0
        frame_timestamp = processor.calculate_frame_timestamp(60, fps)
        expected_timestamp = 60 / fps  # 2.0秒
        
        precision_error = abs(frame_timestamp - expected_timestamp)
        print(f"  ✓ 帧级精度: 误差 {precision_error:.6f}s (要求 <0.001s)")
        
        # 测试±2秒精度要求
        duration = 3.5  # 3.5秒片段
        is_accurate = processor.validate_timestamp_accuracy(duration)
        print(f"  ✓ ±2秒精度要求: {duration}s片段 {'满足' if is_accurate else '不满足'}")
        
        # 测试多模态同步容差
        visual_time = 10.0
        audio_time = 10.05  # 50ms偏差
        is_synced = processor.validate_multimodal_sync(visual_time, audio_time, 'audio_music')
        print(f"  ✓ 多模态同步: 50ms偏差 {'在容差内' if is_synced else '超出容差'}")
        
        return precision_error < 0.001 and is_accurate and is_synced
        
    except Exception as e:
        print(f"  ✗ 时间戳精度测试失败: {e}")
        return False

def test_multimodal_architecture():
    """测试多模态架构"""
    print("\n=== 多模态架构测试 ===")
    
    try:
        from src.core.config_manager import get_config_manager
        
        config_manager = get_config_manager()
        config = config_manager.config
        
        # 验证多模态配置
        models_config = config.get('models', {})
        required_models = ['clip', 'clap', 'whisper']
        
        for model_name in required_models:
            if model_name in models_config:
                print(f"  ✓ {model_name.upper()}模型配置存在")
            else:
                print(f"  ✗ {model_name.upper()}模型配置缺失")
                return False
        
        # 验证向量存储配置
        vector_config = config.get('vector_storage', {})
        stored_types = vector_config.get('stored_vector_types', [])
        expected_types = ['image_vectors', 'video_vectors', 'audio_vectors', 'face_vectors']
        
        for vector_type in expected_types:
            if vector_type in stored_types:
                print(f"  ✓ {vector_type} 存储配置存在")
            else:
                print(f"  ✗ {vector_type} 存储配置缺失")
                return False
        
        print("  ✓ 多模态架构验证通过")
        return True
        
    except Exception as e:
        print(f"  ✗ 多模态架构测试失败: {e}")
        return False

def test_smart_retrieval_architecture():
    """测试智能检索架构"""
    print("\n=== 智能检索架构测试 ===")
    
    try:
        from src.core.config_manager import get_config_manager
        
        config_manager = get_config_manager()
        config = config_manager.config
        
        # 验证检索配置
        search_config = config.get('search', {})
        
        # 验证查询路由配置
        query_routing = search_config.get('query_routing', {})
        required_keywords = ['visual_keywords', 'audio_keywords', 'speech_keywords', 'person_keywords']
        
        for keyword_type in required_keywords:
            if keyword_type in query_routing:
                keywords = query_routing[keyword_type]
                print(f"  ✓ {keyword_type}: {len(keywords)} 个关键词")
            else:
                print(f"  ✗ {keyword_type} 配置缺失")
                return False
        
        # 验证动态权重配置
        weights_config = search_config.get('weights', {})
        required_weight_types = ['default', 'visual_query', 'audio_query', 'speech_query', 'person_query']
        
        for weight_type in required_weight_types:
            if weight_type in weights_config:
                print(f"  ✓ {weight_type} 权重配置存在")
            else:
                print(f"  ✗ {weight_type} 权重配置缺失")
                return False
        
        print("  ✓ 智能检索架构验证通过")
        return True
        
    except Exception as e:
        print(f"  ✗ 智能检索架构测试失败: {e}")
        return False

def test_performance_requirements():
    """测试性能要求"""
    print("\n=== 性能要求测试 ===")
    
    try:
        # 测试配置加载性能
        start_time = time.time()
        from src.core.config_manager import get_config_manager
        config_manager = get_config_manager()
        config_load_time = time.time() - start_time
        print(f"  ✓ 配置加载时间: {config_load_time:.3f}s")
        
        # 测试数据库查询性能
        start_time = time.time()
        from src.storage.database import DatabaseManager
        db_manager = DatabaseManager()
        tables = db_manager.execute_query("SELECT name FROM sqlite_master WHERE type='table';")
        db_query_time = time.time() - start_time
        print(f"  ✓ 数据库查询时间: {db_query_time:.3f}s")
        
        # 验证性能指标
        performance_ok = config_load_time < 1.0 and db_query_time < 0.1
        print(f"  {'✓' if performance_ok else '✗'} 性能要求: {'满足' if performance_ok else '不满足'}")
        
        return performance_ok
        
    except Exception as e:
        print(f"  ✗ 性能要求测试失败: {e}")
        return False

def generate_integration_test_report():
    """生成集成测试报告"""
    print("\n" + "=" * 60)
    print("msearch 智能多模态检索系统 - 集成测试报告")
    print("=" * 60)
    print(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"测试环境: Windows")
    print("=" * 60)
    
    # 执行所有测试
    tests = [
        ("系统架构完整性", test_system_architecture),
        ("配置驱动架构", test_configuration_driven_architecture),
        ("数据存储集成", test_data_storage_integration),
        ("时间戳精度要求", test_timestamp_accuracy_requirements),
        ("多模态架构", test_multimodal_architecture),
        ("智能检索架构", test_smart_retrieval_architecture),
        ("性能要求", test_performance_requirements),
    ]
    
    results = []
    total_start_time = time.time()
    
    for test_name, test_func in tests:
        print(f"\n执行测试: {test_name}")
        test_start_time = time.time()
        
        try:
            success = test_func()
            if isinstance(success, dict):
                # 对于返回字典的测试（如架构测试）
                success = all(success.values())
        except Exception as e:
            print(f"  ✗ 测试执行异常: {e}")
            success = False
        
        test_duration = time.time() - test_start_time
        results.append((test_name, success, test_duration))
    
    total_duration = time.time() - total_start_time
    
    # 生成测试报告
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    for test_name, success, duration in results:
        status = "✓ 通过" if success else "✗ 失败"
        print(f"{status} {test_name} - 耗时: {duration:.3f}s")
    
    print("=" * 60)
    print(f"测试覆盖率: {passed}/{total} ({passed/total*100:.1f}%)")
    print(f"总耗时: {total_duration:.3f}s")
    
    if passed == total:
        print("\n🎉 所有集成测试通过！系统架构符合设计要求。")
        print("\n✅ 验证项目:")
        print("  - 分层架构设计正确")
        print("  - 配置驱动架构完整")
        print("  - 时间戳精度满足±2秒要求")
        print("  - 多模态架构配置完整")
        print("  - 智能检索架构设计合理")
        print("  - 性能指标满足要求")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败，需要进一步优化")
        return 1

def main():
    """主函数"""
    return generate_integration_test_report()

if __name__ == "__main__":
    sys.exit(main())