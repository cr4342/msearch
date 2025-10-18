#!/usr/bin/env python3
"""
测试EmbeddingEngine的脚本
"""
import asyncio
import sys
import os
import pytest
import numpy as np
import yaml

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.business.embedding_engine import get_embedding_engine

def load_config():
    """加载配置文件"""
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    config_path = os.path.join(project_root, 'config', 'config.yml')
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

@pytest.mark.asyncio
async def test_embedding_engine():
    """测试嵌入引擎"""
    print("=== 测试EmbeddingEngine ===")
    
    # 加载配置
    config = load_config()
    
    # 创建引擎实例
    engine = get_embedding_engine(config)
    
    print("✓ 嵌入引擎初始化完成")
    
    # 测试文本向量化
    try:
        test_text = "这是一段测试文本"
        print(f"测试文本: {test_text}")
        
        text_vector = await engine.embed_text(test_text)
        print(f"✓ 文本向量化成功: 形状={text_vector.shape}")
        print(f"   向量范数: {np.linalg.norm(text_vector):.4f}")
        
    except Exception as e:
        print(f"✗ 文本向量化失败: {e}")
        return False
    
    # 测试模拟图片向量化（使用随机数据）
    try:
        test_image = np.random.rand(224, 224, 3).astype(np.float32)
        print("测试图片向量化...")
        
        image_vector = await engine.embed_image(test_image)
        print(f"✓ 图片向量化成功: 形状={image_vector.shape}")
        print(f"   向量范数: {np.linalg.norm(image_vector):.4f}")
        
    except Exception as e:
        print(f"✗ 图片向量化失败: {e}")
        return False
    
    # 测试向量相似度
    try:
        similarity = np.dot(text_vector, image_vector) / (np.linalg.norm(text_vector) * np.linalg.norm(image_vector))
        print(f"✓ 向量相似度计算成功: {similarity:.4f}")
        
    except Exception as e:
        print(f"✗ 向量相似度计算失败: {e}")
        return False
    
    print("\n=== 所有测试通过 ===")
    return True

@pytest.mark.asyncio
async def test_embedding_engine_mock_mode():
    """测试嵌入引擎的模拟模式"""
    print("=== 测试EmbeddingEngine模拟模式 ===")
    
    # 加载配置
    config = load_config()
    
    # 创建引擎实例（强制模拟模式）
    engine = get_embedding_engine(config)
    engine.engine_array = None  # 强制设置为None以触发模拟模式
    
    # 测试文本向量化（模拟模式）
    test_text = "测试文本"
    text_vector = await engine.embed_text(test_text)
    
    assert text_vector.shape == (512,), f"期望向量形状为(512,)，实际为{text_vector.shape}"
    assert abs(np.linalg.norm(text_vector) - 1.0) < 0.01, "模拟向量应该被归一化"
    
    print(f"✓ 模拟文本向量生成成功: 形状={text_vector.shape}")
    
    # 测试图片向量化（模拟模式）
    test_image = np.random.rand(224, 224, 3).astype(np.float32)
    image_vector = await engine.embed_image(test_image)
    
    assert image_vector.shape == (512,), f"期望向量形状为(512,)，实际为{image_vector.shape}"
    assert abs(np.linalg.norm(image_vector) - 1.0) < 0.01, "模拟向量应该被归一化"
    
    print(f"✓ 模拟图片向量生成成功: 形状={image_vector.shape}")
    
    print("\n=== 所有测试通过 ===")
    return True

@pytest.mark.asyncio
async def test_embedding_engine_model_status():
    """测试模型状态管理功能"""
    print("\n=== 测试 EmbeddingEngine 模型状态管理 ===")
    
    # 加载配置
    config = load_config()
    
    # 获取引擎实例
    engine = get_embedding_engine(config)
    assert engine is not None, "无法获取 EmbeddingEngine 实例"
    
    # 测试模型状态获取
    model_status = engine.get_model_status()
    print(f"模型状态: {model_status}")
    
    assert isinstance(model_status, dict), "模型状态应该是字典类型"
    assert 'clip' in model_status, "应该包含clip模型状态"
    assert 'clap' in model_status, "应该包含clap模型状态"
    assert 'whisper' in model_status, "应该包含whisper模型状态"
    
    # 测试模型可用性检查
    for model_name in ['clip', 'clap', 'whisper']:
        is_available = engine.is_model_available(model_name)
        print(f"模型 {model_name} 可用性: {is_available}")
        assert isinstance(is_available, bool), f"模型 {model_name} 可用性应该是布尔值"
    
    print("✓ 模型状态管理测试通过")
    
    return True

@pytest.mark.asyncio
async def test_embedding_engine_batch_processing():
    """测试批量处理功能"""
    print("\n=== 测试 EmbeddingEngine 批量处理 ===")
    
    # 加载配置
    config = load_config()
    
    # 获取引擎实例
    engine = get_embedding_engine(config)
    assert engine is not None, "无法获取 EmbeddingEngine 实例"
    
    # 准备测试数据
    test_texts = ["测试文本1", "测试文本2", "测试文本3"]
    test_images = [np.random.rand(224, 224, 3).astype(np.float32) for _ in range(3)]
    
    # 测试批量文本向量化
    print("测试批量文本向量化...")
    text_vectors = await engine.batch_embed_text(test_texts)
    
    assert len(text_vectors) == len(test_texts), f"批量文本向量数量不匹配: {len(text_vectors)} != {len(test_texts)}"
    
    for i, vector in enumerate(text_vectors):
        assert isinstance(vector, np.ndarray), f"文本向量 {i} 应该是numpy数组"
        assert vector.shape[0] == 512, f"文本向量 {i} 维度应该是512"
        # 检查向量是否归一化
        norm = np.linalg.norm(vector)
        assert abs(norm - 1.0) < 0.01, f"文本向量 {i} 未正确归一化: norm={norm}"
    
    print("✓ 批量文本向量化测试通过")
    
    # 测试批量图片向量化
    print("测试批量图片向量化...")
    image_vectors = await engine.batch_embed_image(test_images)
    
    assert len(image_vectors) == len(test_images), f"批量图片向量数量不匹配: {len(image_vectors)} != {len(test_images)}"
    
    for i, vector in enumerate(image_vectors):
        assert isinstance(vector, np.ndarray), f"图片向量 {i} 应该是numpy数组"
        assert vector.shape[0] == 512, f"图片向量 {i} 维度应该是512"
        # 检查向量是否归一化
        norm = np.linalg.norm(vector)
        assert abs(norm - 1.0) < 0.01, f"图片向量 {i} 未正确归一化: norm={norm}"
    
    print("✓ 批量图片向量化测试通过")
    
    # 测试空列表处理
    empty_text_vectors = await engine.batch_embed_text([])
    assert len(empty_text_vectors) == 0, "空文本列表应该返回空列表"
    
    empty_image_vectors = await engine.batch_embed_image([])
    assert len(empty_image_vectors) == 0, "空图片列表应该返回空列表"
    
    print("✓ 空列表处理测试通过")
    
    return True

if __name__ == "__main__":
    result = asyncio.run(test_embedding_engine())
    sys.exit(0 if result else 1)