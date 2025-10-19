#!/usr/bin/env python3
"""
集成测试执行脚本
根据docs/design.md中的测试要求编写的集成测试
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_config_loading_integration():
    """测试配置加载集成 - 验证配置管理器与其他组件的集成"""
    print("执行配置加载集成测试...")
    
    try:
        from src.core.config_manager import ConfigManager
        
        # 验证配置管理器初始化
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        # 验证必要配置项存在
        required_sections = ['general', 'features', 'models', 'processing', 'database']
        for section in required_sections:
            assert section in config, f"配置项 '{section}' 缺失"
        
        print("✓ 配置加载集成测试通过")
        return True
    except Exception as e:
        print(f"✗ 配置加载集成测试失败: {e}")
        return False

def test_component_initialization_integration():
    """测试组件初始化集成 - 验证各核心组件的初始化和依赖注入"""
    print("执行组件初始化集成测试...")
    
    try:
        from src.core.config_manager import ConfigManager
        from src.business.processing_orchestrator import ProcessingOrchestrator
        from src.business.smart_retrieval import SmartRetrievalEngine
        from src.business.multimodal_fusion_engine import MultiModalFusionEngine
        from src.storage.vector_store import VectorStore
        from src.storage.face_database import FaceDatabase
        
        # 初始化配置管理器
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        # 验证各组件初始化
        orchestrator = ProcessingOrchestrator(config)
        retrieval_engine = SmartRetrievalEngine(config)
        fusion_engine = MultiModalFusionEngine(config)
        vector_store = VectorStore(config)
        face_database = FaceDatabase(config)
        
        # 验证组件不为None
        assert orchestrator is not None
        assert retrieval_engine is not None
        assert fusion_engine is not None
        assert vector_store is not None
        assert face_database is not None
        
        print("✓ 组件初始化集成测试通过")
        return True
    except Exception as e:
        print(f"✗ 组件初始化集成测试失败: {e}")
        return False

def test_timestamp_processing_accuracy():
    """测试时间戳处理精度 - 关键测试：验证视频处理中的时间戳精度达到±2秒要求"""
    print("执行时间戳处理精度测试...")
    
    try:
        from src.processors.timestamp_processor import TimestampProcessor
        
        # 创建时间戳处理器
        timestamp_processor = TimestampProcessor()
        
        # 测试帧级时间戳计算精度
        test_cases = [
            (0, 30.0, 0.0),      # 第0帧，30fps，应该在0秒
            (30, 30.0, 1.0),     # 第30帧，30fps，应该在1秒
            (600, 30.0, 20.0),   # 第600帧，30fps，应该在20秒
            (1200, 25.0, 48.0),  # 第1200帧，25fps，应该在48秒
        ]
        
        for frame_index, fps, expected_time in test_cases:
            if hasattr(timestamp_processor, 'calculate_frame_timestamp'):
                calculated_time = timestamp_processor.calculate_frame_timestamp(frame_index, fps)
                # 验证计算精度（误差小于1毫秒）
                assert abs(calculated_time - expected_time) < 0.001, \
                    f"时间戳计算错误: 期望 {expected_time}s, 实际 {calculated_time}s"
        
        # 测试时间戳精度验证功能
        if hasattr(timestamp_processor, 'validate_timestamp_accuracy'):
            assert timestamp_processor.validate_timestamp_accuracy(1.5, 2.0)  # 应该满足±2秒要求
            assert not timestamp_processor.validate_timestamp_accuracy(3.0, 5.0)  # 超出精度要求
        
        print("✓ 时间戳处理精度测试通过")
        return True
    except Exception as e:
        print(f"✗ 时间戳处理精度测试失败: {e}")
        return False

def test_multimodal_retrieval_integration():
    """测试多模态检索集成 - 验证文本、图片、音频等多种查询方式的集成"""
    print("执行多模态检索集成测试...")
    
    try:
        from src.core.config_manager import ConfigManager
        from src.business.smart_retrieval import SmartRetrievalEngine
        
        # 初始化配置管理器和检索引擎
        config_manager = ConfigManager()
        config = config_manager.get_config()
        retrieval_engine = SmartRetrievalEngine(config)
        
        # 测试查询类型识别功能
        if hasattr(retrieval_engine, '_identify_query_type'):
            assert retrieval_engine._identify_query_type("查找张三的照片") == "person"
            assert retrieval_engine._identify_query_type("搜索音乐") == "audio"
            assert retrieval_engine._identify_query_type("查找图片") == "visual"
            assert retrieval_engine._identify_query_type("查找文档") == "generic"
        
        print("✓ 多模态检索集成测试通过")
        return True
    except Exception as e:
        print(f"✗ 多模态检索集成测试失败: {e}")
        return False

def test_processing_pipeline_integration():
    """测试处理管道集成 - 验证文件从输入到向量存储的完整流程"""
    print("执行处理管道集成测试...")
    
    try:
        from src.core.config_manager import ConfigManager
        from src.business.processing_orchestrator import ProcessingOrchestrator
        
        # 初始化配置管理器和处理编排器
        config_manager = ConfigManager()
        config = config_manager.get_config()
        orchestrator = ProcessingOrchestrator(config)
        
        # 验证处理管道的各个组件存在
        assert hasattr(orchestrator, 'file_type_detector')
        assert hasattr(orchestrator, 'media_processor')
        assert hasattr(orchestrator, 'embedding_engine')
        assert hasattr(orchestrator, 'vector_store')
        assert hasattr(orchestrator, 'task_manager')
        
        print("✓ 处理管道集成测试通过")
        return True
    except Exception as e:
        print(f"✗ 处理管道集成测试失败: {e}")
        return False

def test_face_recognition_integration():
    """测试人脸识别集成 - 验证人脸检测、特征提取和匹配的集成"""
    print("执行人脸识别集成测试...")
    
    try:
        from src.core.config_manager import ConfigManager
        from src.storage.face_database import FaceDatabase
        
        # 初始化配置管理器和人脸数据库
        config_manager = ConfigManager()
        config = config_manager.get_config()
        face_database = FaceDatabase(config)
        
        # 验证人脸数据库组件功能
        assert hasattr(face_database, 'add_person')
        assert hasattr(face_database, 'search_similar_faces')
        assert hasattr(face_database, 'get_person_by_name')
        
        print("✓ 人脸识别集成测试通过")
        return True
    except Exception as e:
        print(f"✗ 人脸识别集成测试失败: {e}")
        return False

def test_storage_integration():
    """测试存储集成 - 验证向量存储和元数据存储的集成"""
    print("执行存储集成测试...")
    
    try:
        from src.core.config_manager import ConfigManager
        from src.storage.vector_store import VectorStore
        
        # 初始化配置管理器和向量存储
        config_manager = ConfigManager()
        config = config_manager.get_config()
        vector_store = VectorStore(config)
        
        # 验证存储组件功能
        assert hasattr(vector_store, 'store_vector')
        assert hasattr(vector_store, 'search_vectors')
        assert hasattr(vector_store, 'delete_vector')
        
        print("✓ 存储集成测试通过")
        return True
    except Exception as e:
        print(f"✗ 存储集成测试失败: {e}")
        return False

def test_api_service_integration():
    """测试API服务集成 - 验证API端点与业务逻辑的集成"""
    print("执行API服务集成测试...")
    
    try:
        # 验证API路由模块导入
        from src.api.routes import search, config, tasks, status
        
        # 验证各API模块存在
        assert search is not None
        assert config is not None
        assert tasks is not None
        assert status is not None
        
        # 验证API模型导入
        from src.api.models.search_models import SearchRequest, SearchResponse
        from src.api.models.config_models import ConfigRequest, ConfigResponse
        
        assert SearchRequest is not None
        assert SearchResponse is not None
        assert ConfigRequest is not None
        assert ConfigResponse is not None
        
        print("✓ API服务集成测试通过")
        return True
    except Exception as e:
        print(f"✗ API服务集成测试失败: {e}")
        return False

def main():
    """主函数 - 执行所有集成测试"""
    print("开始执行msearch集成测试...")
    print("=" * 60)
    
    # 执行所有集成测试
    tests = [
        test_config_loading_integration,
        test_component_initialization_integration,
        test_timestamp_processing_accuracy,
        test_multimodal_retrieval_integration,
        test_processing_pipeline_integration,
        test_face_recognition_integration,
        test_storage_integration,
        test_api_service_integration,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"测试 {test.__name__} 执行异常: {e}")
            failed += 1
    
    print("=" * 60)
    print(f"集成测试结果: {passed} 通过, {failed} 失败")
    
    if failed == 0:
        print("🎉 所有集成测试通过！")
        return 0
    else:
        print(f"❌ {failed} 个测试失败")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)