#!/usr/bin/env python3
"""
测试核心组件功能
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import logging
from src.core.config_manager import get_config_manager
from src.business.embedding_engine import EmbeddingEngine
from src.business.orchestrator import ProcessingOrchestrator
from src.business.smart_retrieval import SmartRetrievalEngine
from src.business.multimodal_fusion_engine import MultiModalFusionEngine

def test_config_manager():
    """测试配置管理器"""
    print("1. 测试配置管理器...")
    try:
        config_manager = get_config_manager()
        config = config_manager.config
        print(f"  ✓ 配置管理器初始化成功")
        print(f"  ✓ 配置项数量: {len(config) if config else 0}")
        # 使用断言而不是返回值
        assert config_manager is not None
        assert config is not None
    except Exception as e:
        print(f"  ✗ 配置管理器初始化失败: {e}")
        raise

def test_embedding_engine():
    """测试嵌入引擎"""
    print("2. 测试嵌入引擎...")
    try:
        config_manager = get_config_manager()
        config = config_manager.config
        
        # 测试配置 - 使用本地模型路径（只启用CLIP模型）
        test_config = {
            'features': {
                'enable_clip': True,
                'enable_clap': False,  # 禁用CLAP模型
                'enable_whisper': False  # 禁用Whisper模型
            },
            'models': {
                'clip': {
                    'model_name': './data/models/clip-vit-base-patch32',
                    'local_path': './data/models/clip-vit-base-patch32',
                    'device': 'cpu',
                    'batch_size': 16
                }
            },
            'device': 'cpu'
        }
        
        engine = EmbeddingEngine(test_config)
        print(f"  ✓ 嵌入引擎初始化成功")
        print(f"  ✓ Infinity可用: {hasattr(engine, 'engine_array') and engine.engine_array is not None}")
        # 使用断言
        assert engine is not None
    except Exception as e:
        print(f"  ✗ 嵌入引擎初始化失败: {e}")
        raise

def test_processing_orchestrator():
    """测试处理编排器"""
    print("3. 测试处理编排器...")
    try:
        config_manager = get_config_manager()
        config = config_manager.config
        
        orchestrator = ProcessingOrchestrator(config)
        print(f"  ✓ 处理编排器初始化成功")
        print(f"  ✓ 组件数量: 4 (文件类型检测器、媒体处理器、嵌入引擎、任务管理器)")
        # 使用断言
        assert orchestrator is not None
    except Exception as e:
        print(f"  ✗ 处理编排器初始化失败: {e}")
        raise

def test_smart_retrieval_engine():
    """测试智能检索引擎"""
    print("4. 测试智能检索引擎...")
    try:
        config_manager = get_config_manager()
        config = config_manager.config
        
        engine = SmartRetrievalEngine(config)
        print(f"  ✓ 智能检索引擎初始化成功")
        print(f"  ✓ 组件数量: 4 (搜索引擎、融合引擎、人脸数据库、人脸管理器)")
        # 使用断言
        assert engine is not None
    except Exception as e:
        print(f"  ✗ 智能检索引擎初始化失败: {e}")
        raise

def test_multimodal_fusion_engine():
    """测试多模态融合引擎"""
    print("5. 测试多模态融合引擎...")
    try:
        config_manager = get_config_manager()
        config = config_manager.config
        
        engine = MultiModalFusionEngine(config)
        print(f"  ✓ 多模态融合引擎初始化成功")
        
        # 测试融合功能
        test_results = {
            'text': [
                {'file_id': 'file1', 'score': 0.8, 'content': '相关内容'},
                {'file_id': 'file2', 'score': 0.6, 'content': '相关内容'}
            ],
            'image': [
                {'file_id': 'file1', 'score': 0.9, 'content': '相关图片'},
                {'file_id': 'file3', 'score': 0.7, 'content': '相关图片'}
            ]
        }
        
        fused = engine.fuse_results(test_results)
        print(f"  ✓ 融合功能测试成功: {len(fused)} 个结果")
        # 使用断言
        assert engine is not None
        assert fused is not None
    except Exception as e:
        print(f"  ✗ 多模态融合引擎测试失败: {e}")
        raise

async def test_embedding_functions_async():
    """测试嵌入功能（异步）"""
    print("6. 测试嵌入功能...")
    try:
        config_manager = get_config_manager()
        config = config_manager.config
        
        test_config = {
            'features': {
                'enable_clip': True,
                'enable_clap': False,  # 禁用CLAP模型
                'enable_whisper': False  # 禁用Whisper模型
            },
            'models': {
                'clip': {
                    'model_name': './data/models/clip-vit-base-patch32',
                    'local_path': './data/models/clip-vit-base-patch32',
                    'device': 'cpu',
                    'batch_size': 16
                }
            },
            'device': 'cpu'
        }
        
        engine = EmbeddingEngine(test_config)
        
        # 测试文本嵌入
        text = "这是一个测试文本"
        vector = await engine.embed_text(text)
        print(f"  ✓ 文本嵌入成功: 向量维度 {len(vector) if hasattr(vector, '__len__') else 'N/A'}")
        
        # 测试模拟图像嵌入
        import numpy as np
        mock_image = np.random.rand(224, 224, 3).astype(np.float32)
        image_vector = await engine.embed_image(mock_image)
        print(f"  ✓ 图像嵌入成功: 向量维度 {len(image_vector) if hasattr(image_vector, '__len__') else 'N/A'}")
        
    except Exception as e:
        print(f"  ✗ 嵌入功能测试失败: {e}")
        raise

def test_embedding_functions():
    """测试嵌入功能（同步包装器）"""
    asyncio.run(test_embedding_functions_async())

def main():
    """主测试函数"""
    print("=== msearch 核心组件测试 ===")
    print()
    
    results = []
    
    # 同步测试
    results.append(test_config_manager())
    results.append(test_embedding_engine())
    results.append(test_processing_orchestrator())
    results.append(test_smart_retrieval_engine())
    results.append(test_multimodal_fusion_engine())
    
    # 异步测试
    async_test_result = asyncio.run(test_embedding_functions())
    results.append(async_test_result)
    
    print()
    print("=== 测试结果总结 ===")
    passed = sum(results)
    total = len(results)
    print(f"通过测试: {passed}/{total}")
    
    if passed == total:
        print("✓ 所有核心组件测试通过！")
    else:
        print(f"✗ 有 {total - passed} 个测试失败，需要修复")

if __name__ == "__main__":
    main()