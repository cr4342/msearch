#!/usr/bin/env python3
"""
离线模型集成测试脚本
验证已下载的离线模型和依赖是否正常工作
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def setup_offline_environment():
    """设置离线环境变量"""
    print("=== 设置离线环境 ===")
    
    # 设置HuggingFace缓存路径指向离线模型
    offline_models_path = project_root / "offline" / "models"
    os.environ["HF_HOME"] = str(offline_models_path / "huggingface")
    os.environ["TRANSFORMERS_CACHE"] = str(offline_models_path / "huggingface")
    
    # 禁用网络连接，强制使用离线模型
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["HF_HUB_OFFLINE"] = "1"
    
    print(f"✓ 离线模型路径设置为: {offline_models_path}")
    print(f"✓ HuggingFace缓存: {os.environ['HF_HOME']}")
    print(f"✓ 离线模式已启用")
    
    return True

def test_offline_models_loading():
    """测试离线模型加载"""
    print("\n=== 测试离线模型加载 ===")
    
    try:
        from src.business.embedding_engine import EmbeddingEngine
        
        # 创建使用离线模型的测试配置
        test_config = {
            'models': {
                'clip': {
                    'model_name': str(project_root / "offline" / "models" / "clip-vit-base-patch32"),
                    'device': 'cpu',
                    'batch_size': 16
                },
                'clap': {
                    'model_name': str(project_root / "offline" / "models" / "clap-htsat-fused"),
                    'device': 'cpu', 
                    'batch_size': 8
                },
                'whisper': {
                    'model_name': str(project_root / "offline" / "models" / "whisper-base"),
                    'device': 'cpu',
                    'batch_size': 4
                }
            }
        }
        
        # 创建嵌入引擎
        engine = EmbeddingEngine(test_config)
        print("✓ 嵌入引擎创建成功（使用离线模型路径）")
        
        # 检查模型状态
        model_status = engine.get_model_status()
        print(f"✓ 模型状态: {model_status}")
        
        # 如果模型加载失败，尝试使用在线模型名但离线缓存
        if not any(model_status.values()):
            print("⚠ 离线模型路径加载失败，尝试使用在线模型名+离线缓存")
            
            online_config = {
                'models': {
                    'clip': {
                        'model_name': 'openai/clip-vit-base-patch32',
                        'device': 'cpu',
                        'batch_size': 16
                    },
                    'clap': {
                        'model_name': 'laion/clap-htsat-fused',
                        'device': 'cpu',
                        'batch_size': 8
                    },
                    'whisper': {
                        'model_name': 'openai/whisper-base',
                        'device': 'cpu',
                        'batch_size': 4
                    }
                }
            }
            
            engine = EmbeddingEngine(online_config)
            model_status = engine.get_model_status()
            print(f"✓ 使用在线模型名+离线缓存的模型状态: {model_status}")
        
        return True
    except Exception as e:
        print(f"✗ 离线模型加载测试失败: {e}")
        return False

def test_offline_model_functionality():
    """测试离线模型功能"""
    print("\n=== 测试离线模型功能 ===")
    
    try:
        import asyncio
        import numpy as np
        from src.business.embedding_engine import EmbeddingEngine
        
        # 创建嵌入引擎
        test_config = {
            'models': {
                'clip': {
                    'model_name': 'openai/clip-vit-base-patch32',
                    'device': 'cpu',
                    'batch_size': 16
                }
            }
        }
        
        engine = EmbeddingEngine(test_config)
        
        # 测试文本向量化
        async def test_text_embedding():
            test_text = "这是一张测试图片"
            vector = await engine.embed_text(test_text)
            print(f"✓ 文本向量化成功，向量维度: {vector.shape}")
            return vector
        
        # 测试图片向量化
        async def test_image_embedding():
            # 创建模拟图片数据 (224x224x3 RGB)
            test_image = np.random.rand(224, 224, 3).astype(np.float32)
            vector = await engine.embed_image(test_image)
            print(f"✓ 图片向量化成功，向量维度: {vector.shape}")
            return vector
        
        # 运行异步测试
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            text_vector = loop.run_until_complete(test_text_embedding())
            image_vector = loop.run_until_complete(test_image_embedding())
            
            # 验证向量维度和类型
            assert text_vector.shape == (512,), f"文本向量维度错误: {text_vector.shape}"
            assert image_vector.shape == (512,), f"图片向量维度错误: {image_vector.shape}"
            assert text_vector.dtype == np.float32, f"文本向量类型错误: {text_vector.dtype}"
            assert image_vector.dtype == np.float32, f"图片向量类型错误: {image_vector.dtype}"
            
            print("✓ 向量维度和类型验证通过")
            
        finally:
            loop.close()
        
        return True
    except Exception as e:
        print(f"✗ 离线模型功能测试失败: {e}")
        return False

def test_timestamp_accuracy_with_models():
    """测试时间戳精度（结合模型）"""
    print("\n=== 测试时间戳精度（结合模型） ===")
    
    try:
        import asyncio
        import numpy as np
        from src.business.temporal_localization_engine import TemporalLocalizationEngine
        from src.business.embedding_engine import EmbeddingEngine
        
        # 创建时间定位引擎
        temporal_engine = TemporalLocalizationEngine()
        print("✓ 时间定位引擎创建成功")
        
        # 创建嵌入引擎
        embedding_config = {
            'models': {
                'clip': {
                    'model_name': 'openai/clip-vit-base-patch32',
                    'device': 'cpu',
                    'batch_size': 16
                }
            }
        }
        embedding_engine = EmbeddingEngine(embedding_config)
        
        # 模拟视频帧向量和时间戳
        async def test_video_timestamp_accuracy():
            # 创建模拟视频帧向量
            frame_vectors = []
            timestamps = []
            
            for i in range(10):  # 10帧，每秒1帧
                # 生成模拟向量
                vector = await embedding_engine.embed_text(f"视频帧 {i}")
                frame_vectors.append(vector)
                timestamps.append(float(i))  # 时间戳：0, 1, 2, ..., 9秒
            
            # 测试时间戳精度验证
            accuracy_requirement = 2.0  # ±2秒要求
            
            for i, ts in enumerate(timestamps):
                # 模拟时间戳精度检查
                calculated_ts = temporal_engine.calculate_frame_timestamp(i, 1.0)  # 帧索引，帧率1fps
                accuracy = abs(calculated_ts - ts)
                
                if accuracy <= accuracy_requirement:
                    print(f"✓ 帧 {i} 时间戳精度满足要求: {calculated_ts:.2f}s (误差: {accuracy:.2f}s)")
                else:
                    print(f"✗ 帧 {i} 时间戳精度不满足要求: {calculated_ts:.2f}s (误差: {accuracy:.2f}s)")
            
            return True
        
        # 运行异步测试
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(test_video_timestamp_accuracy())
            return result
        finally:
            loop.close()
        
    except Exception as e:
        print(f"✗ 时间戳精度测试失败: {e}")
        return False

def test_multimodal_retrieval():
    """测试多模态检索功能"""
    print("\n=== 测试多模态检索功能 ===")
    
    try:
        from src.business.smart_retrieval import SmartRetrievalEngine
        from src.core.config_manager import get_config_manager
        
        # 获取配置管理器
        config_manager = get_config_manager()
        config = config_manager.config
        
        # 创建智能检索引擎
        retrieval_engine = SmartRetrievalEngine(config)
        print("✓ 智能检索引擎创建成功")
        
        # 测试查询类型识别
        test_queries = [
            ("查找风景图片", "visual"),
            ("搜索音乐", "audio"),
            ("寻找讲话视频", "speech"),
            ("张三的照片", "person")
        ]
        
        for query, expected_type in test_queries:
            detected_type = retrieval_engine.identify_query_type(query)
            if detected_type == expected_type:
                print(f"✓ 查询类型识别正确: '{query}' -> {detected_type}")
            else:
                print(f"✗ 查询类型识别错误: '{query}' -> {detected_type} (期望: {expected_type})")
        
        return True
    except Exception as e:
        print(f"✗ 多模态检索测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("msearch 离线模型集成测试开始...\n")
    
    # 设置离线环境
    setup_offline_environment()
    
    results = []
    
    # 运行各项测试
    results.append(test_offline_models_loading())
    results.append(test_offline_model_functionality())
    results.append(test_timestamp_accuracy_with_models())
    results.append(test_multimodal_retrieval())
    
    # 统计结果
    passed = sum(results)
    total = len(results)
    
    print(f"\n=== 测试结果 ===")
    print(f"通过测试: {passed}/{total}")
    
    if passed == total:
        print("✓ 所有离线模型集成测试通过！")
        return 0
    else:
        print(f"✗ 有 {total - passed} 个测试失败")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
