#!/usr/bin/env python3
"""
基本结构测试脚本
用于验证项目的基本结构和模块导入
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_module_imports():
    """测试模块导入"""
    print("测试模块导入...")
    
    # 测试核心模块导入
    try:
        from src.core.config_manager import ConfigManager
        print("✓ ConfigManager 导入成功")
    except ImportError as e:
        print(f"✗ ConfigManager 导入失败: {e}")
    
    try:
        from src.core.file_type_detector import FileTypeDetector
        print("✓ FileTypeDetector 导入成功")
    except ImportError as e:
        print(f"✗ FileTypeDetector 导入失败: {e}")
    
    # 测试业务模块导入
    try:
        from src.business.processing_orchestrator import ProcessingOrchestrator
        print("✓ ProcessingOrchestrator 导入成功")
    except ImportError as e:
        print(f"✗ ProcessingOrchestrator 导入失败: {e}")
    
    try:
        from src.business.embedding_engine import EmbeddingEngine
        print("✓ EmbeddingEngine 导入成功")
    except ImportError as e:
        print(f"✗ EmbeddingEngine 导入失败: {e}")
    
    try:
        from src.business.smart_retrieval import SmartRetrievalEngine
        print("✓ SmartRetrievalEngine 导入成功")
    except ImportError as e:
        print(f"✗ SmartRetrievalEngine 导入失败: {e}")
    
    try:
        from src.business.multimodal_fusion_engine import MultiModalFusionEngine
        print("✓ MultiModalFusionEngine 导入成功")
    except ImportError as e:
        print(f"✗ MultiModalFusionEngine 导入失败: {e}")
    
    # 测试存储模块导入
    try:
        from src.storage.vector_store import VectorStore
        print("✓ VectorStore 导入成功")
    except ImportError as e:
        print(f"✗ VectorStore 导入失败: {e}")
    
    try:
        from src.storage.face_database import FaceDatabase
        print("✓ FaceDatabase 导入成功")
    except ImportError as e:
        print(f"✗ FaceDatabase 导入失败: {e}")
    
    # 测试API模块导入
    try:
        from src.api.routes.search import router as search_router
        print("✓ Search API 导入成功")
    except ImportError as e:
        print(f"✗ Search API 导入失败: {e}")
    
    try:
        from src.api.routes.config import router as config_router
        print("✓ Config API 导入成功")
    except ImportError as e:
        print(f"✗ Config API 导入失败: {e}")
    
    try:
        from src.api.routes.tasks import router as tasks_router
        print("✓ Tasks API 导入成功")
    except ImportError as e:
        print(f"✗ Tasks API 导入失败: {e}")
    
    try:
        from src.api.routes.status import router as status_router
        print("✓ Status API 导入成功")
    except ImportError as e:
        print(f"✗ Status API 导入失败: {e}")

def test_config_loading():
    """测试配置加载"""
    print("\n测试配置加载...")
    
    try:
        from src.core.config_manager import ConfigManager
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        # 检查必要配置项
        required_sections = ['general', 'features', 'models', 'processing']
        for section in required_sections:
            if section in config:
                print(f"✓ 配置项 '{section}' 存在")
            else:
                print(f"✗ 配置项 '{section}' 缺失")
        
        print("✓ 配置加载成功")
    except Exception as e:
        print(f"✗ 配置加载失败: {e}")

def test_basic_instantiation():
    """测试基本实例化"""
    print("\n测试基本实例化...")
    
    try:
        from src.core.config_manager import ConfigManager
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        # 测试处理编排器实例化
        try:
            from src.business.processing_orchestrator import ProcessingOrchestrator
            orchestrator = ProcessingOrchestrator(config)
            print("✓ ProcessingOrchestrator 实例化成功")
        except Exception as e:
            print(f"✗ ProcessingOrchestrator 实例化失败: {e}")
        
        # 测试智能检索引擎实例化
        try:
            from src.business.smart_retrieval import SmartRetrievalEngine
            retrieval_engine = SmartRetrievalEngine(config)
            print("✓ SmartRetrievalEngine 实例化成功")
        except Exception as e:
            print(f"✗ SmartRetrievalEngine 实例化失败: {e}")
        
        # 测试多模态融合引擎实例化
        try:
            from src.business.multimodal_fusion_engine import MultiModalFusionEngine
            fusion_engine = MultiModalFusionEngine(config)
            print("✓ MultiModalFusionEngine 实例化成功")
        except Exception as e:
            print(f"✗ MultiModalFusionEngine 实例化失败: {e}")
            
    except Exception as e:
        print(f"✗ 基本实例化测试失败: {e}")

def main():
    """主函数"""
    print("=== msearch 项目基本结构测试 ===\n")
    
    test_module_imports()
    test_config_loading()
    test_basic_instantiation()
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    main()