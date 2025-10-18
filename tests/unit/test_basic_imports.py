#!/usr/bin/env python3
"""
测试基础模块导入
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """测试所有核心模块导入"""
    modules_to_test = [
        # Core modules
        ("src.core.config_manager", "get_config_manager"),
        ("src.core.file_type_detector", "get_file_type_detector"),
        ("src.core.logger_manager", "get_logger"),
        ("src.core.logging_config", "setup_logging"),
        
        # Business modules
        ("src.business.embedding_engine", "EmbeddingEngine"),
        ("src.business.processing_orchestrator", "ProcessingOrchestrator"),
        ("src.business.smart_retrieval", "SmartRetrievalEngine"),
        ("src.business.multimodal_fusion_engine", "MultiModalFusionEngine"),
        ("src.business.file_monitor", "FileMonitor"),
        ("src.business.media_processor", "MediaProcessor"),
        ("src.business.temporal_localization_engine", "TemporalLocalizationEngine"),
        ("src.business.load_balancer", "get_load_balancer"),
        ("src.business.task_manager", "TaskManager"),
        
        # Storage modules
        ("src.storage.vector_store", "VectorStore"),
        ("src.storage.database", "Database"),
        ("src.storage.db_adapter", "DBAdapter"),
        ("src.storage.face_database", "FaceDatabase"),
        
        # API modules
        ("src.api.main", "app"),
        ("src.api.routes.search", "router"),
        ("src.api.routes.config", "router"),
        ("src.api.routes.status", "router"),
        ("src.api.routes.tasks", "router"),
        
        # Processor modules
        ("src.processors.audio_classifier", "AudioClassifier"),
        ("src.processors.audio_processor", "AudioProcessor"),
        ("src.processors.image_processor", "ImageProcessor"),
        ("src.processors.media_processor", "MediaProcessor"),
        ("src.processors.text_processor", "TextProcessor"),
        ("src.processors.timestamp_processor", "TimestampProcessor"),
        ("src.processors.video_processor", "VideoProcessor"),
    ]
    
    print("=== 模块导入测试 ===")
    print()
    
    failed_modules = []
    
    for module_path, attr_name in modules_to_test:
        try:
            module = __import__(module_path, fromlist=[attr_name])
            if hasattr(module, attr_name):
                print(f"✓ {module_path}.{attr_name}")
            else:
                print(f"✗ {module_path}.{attr_name} - 属性不存在")
                failed_modules.append(f"{module_path}.{attr_name}")
        except Exception as e:
            print(f"✗ {module_path}.{attr_name} - {e}")
            failed_modules.append(f"{module_path}.{attr_name}")
    
    print()
    print("=== 测试结果 ===")
    total = len(modules_to_test)
    passed = total - len(failed_modules)
    print(f"通过: {passed}/{total}")
    
    if failed_modules:
        print("\n失败的模块:")
        for module in failed_modules:
            print(f"  - {module}")
    else:
        print("✓ 所有模块导入成功！")

if __name__ == "__main__":
    test_imports()