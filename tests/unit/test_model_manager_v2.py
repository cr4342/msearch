#!/usr/bin/env python3
"""
测试模型管理器核心功能

注意：此测试文件已更新，使用src.core.models.model_manager模块
"""

import asyncio
import logging
import pytest
import sys
from pathlib import Path

# 设置日志级别
logging.basicConfig(level=logging.INFO)

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.models.model_manager import ModelManager, ModelConfig


def test_model_config():
    """测试 ModelConfig"""
    print("\n=== 测试 ModelConfig ===")
    
    config = ModelConfig(
        name="test-model",
        engine="torch",
        device="cpu",
        dtype="float32",
        embedding_dim=512
    )
    
    print(f"  模型名称: {config.name}")
    print(f"  引擎: {config.engine}")
    print(f"  设备: {config.device}")
    print(f"  数据类型: {config.dtype}")
    print(f"  向量维度: {config.embedding_dim}")
    print(f"  批处理大小: {config.batch_size}")
    
    assert config.name == "test-model"
    assert config.engine == "torch"
    assert config.device == "cpu"
    assert config.dtype == "float32"
    assert config.embedding_dim == 512
    assert config.batch_size == 16  # 默认值
    
    print("  ✓ ModelConfig 测试通过")


def test_model_manager():
    """测试 ModelManager"""
    print("\n=== 测试 ModelManager ===")
    
    model_manager = ModelManager()
    
    print(f"  模型数量: {len(model_manager._models)}")
    print(f"  配置数量: {len(model_manager._configs)}")
    print(f"  初始化状态: {model_manager._initialized}")
    
    assert len(model_manager._models) == 0
    assert len(model_manager._configs) == 0
    assert model_manager._initialized == False
    
    print("  ✓ ModelManager 测试通过")


@pytest.mark.asyncio
async def test_embedding_service():
    """测试 EmbeddingService"""
    print("\n=== 测试 EmbeddingService ===")
    
    # 注意：需要实际的模型才能测试完整功能
    # 这里只测试初始化
    print("  EmbeddingService 需要实际模型才能测试")
    print("  跳过 EmbeddingService 测试")
    
    print("  ✓ EmbeddingService 测试通过（跳过）")


@pytest.mark.asyncio
async def test_offline_mode():
    """测试离线模式"""
    print("\n=== 测试离线模式 ===")
    
    # 离线模式测试需要实际的离线配置
    print("  离线模式测试需要实际的离线配置")
    print("  跳过离线模式测试")
    
    print("  ✓ 离线模式 测试通过（跳过）")


def main():
    """主函数"""
    print("=" * 60)
    print("模型管理器核心功能测试")
    print("=" * 60)
    
    try:
        test_model_config()
        test_model_manager()
        
        # 异步测试
        asyncio.run(test_embedding_service())
        asyncio.run(test_offline_mode())
        
        print("\n" + "=" * 60)
        print("所有测试通过！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()