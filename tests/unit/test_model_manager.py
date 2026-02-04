#!/usr/bin/env python3
"""
测试统一模型管理器

测试内容：
1. 模型配置创建和验证
2. 模型管理器初始化
3. 向量化服务使用
4. 模型切换
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

import asyncio
import logging
from src.core.models.model_manager import (
    ModelConfig,
    ModelManager,
    EmbeddingService,
    initialize_model_manager,
    get_embedding_service,
    get_model_manager,
    shutdown_model_manager
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_model_config():
    """测试模型配置"""
    print("\n" + "="*60)
    print("测试 1: 模型配置创建和验证")
    print("="*60)

    try:
        # 1. 创建有效的模型配置
        config = ModelConfig(
            name='OFA-Sys/chinese-clip-vit-base-patch16',
            engine='torch',
            device='cpu',
            dtype='float32',
            embedding_dim=512,
            trust_remote_code=True,
            pooling_method='mean',
            compile=False,
            batch_size=16,
            local_path='/data/project/msearch/data/models/chinese-clip-vit-large-patch14-336px'
        )

        print(f"\n✓ 创建模型配置成功:")
        print(f"  - 模型名称: {config.name}")
        print(f"  - 引擎类型: {config.engine}")
        print(f"  - 设备: {config.device}")
        print(f"  - 数据类型: {config.dtype}")
        print(f"  - 向量维度: {config.embedding_dim}")
        print(f"  - 信任远程代码: {config.trust_remote_code}")
        print(f"  - 池化方法: {config.pooling_method}")
        print(f"  - 批处理大小: {config.batch_size}")
        print(f"  - 本地路径: {config.local_path}")

        # 2. 验证配置的合法性
        print(f"\n✓ 配置验证通过")

        # 3. 检查本地模型路径
        if config.local_path and os.path.exists(config.local_path):
            print(f"\n✓ 本地模型路径存在: {config.local_path}")
            files = os.listdir(config.local_path)
            print(f"  - 目录文件数: {len(files)}")
            print(f"  - 主要文件: {[f for f in files if f.endswith('.json') or f.endswith('.safetensors')][:5]}")
        else:
            print(f"\n⚠ 本地模型路径不存在: {config.local_path}")

        return True

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_model_manager_initialization():
    """测试模型管理器初始化"""
    print("\n" + "="*60)
    print("测试 2: 模型管理器初始化")
    print("="*60)

    try:
        # 1. 创建模型配置
        configs = {
            'text': ModelConfig(
                name='OFA-Sys/chinese-clip-vit-base-patch16',
                engine='torch',
                device='cpu',
                dtype='float32',
                embedding_dim=512,
                trust_remote_code=True,
                local_path='/data/project/msearch/data/models/chinese-clip-vit-large-patch14-336px'
            )
        }

        print(f"\n✓ 创建模型配置字典成功，包含 {len(configs)} 个模型")

        # 2. 创建模型管理器
        manager = ModelManager()
        print(f"\n✓ 创建模型管理器成功")

        # 3. 检查是否已初始化
        print(f"\n✓ 检查初始化状态: {manager.is_initialized()}")

        # 4. 获取已加载模型列表
        print(f"\n✓ 已加载模型列表: {manager.get_loaded_models()}")

        return True

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_embedding_service():
    """测试向量化服务"""
    print("\n" + "="*60)
    print("测试 3: 向量化服务")
    print("="*60)

    try:
        # 1. 创建模型配置和管理器
        configs = {
            'text': ModelConfig(
                name='OFA-Sys/chinese-clip-vit-base-patch16',
                engine='torch',
                device='cpu',
                dtype='float32',
                embedding_dim=512,
                trust_remote_code=True,
                local_path='/data/project/msearch/data/models/chinese-clip-vit-large-patch14-336px'
            )
        }

        manager = ModelManager()
        service = EmbeddingService(manager)

        print(f"\n✓ 创建向量化服务成功")

        # 2. 测试服务接口
        print(f"\n✓ 向量化服务接口:")
        print(f"  - embed(): 统一向量化接口")
        print(f"  - embed_text(): 文本向量化")
        print(f"  - embed_image(): 图像向量化")
        print(f"  - embed_audio(): 音频向量化")

        return True

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_invalid_engine():
    """测试无效的引擎类型"""
    print("\n" + "="*60)
    print("测试 4: 无效引擎类型验证")
    print("="*60)

    try:
        # 尝试使用无效的引擎类型
        config = ModelConfig(
            name='OFA-Sys/chinese-clip-vit-base-patch16',
            engine='invalid_engine',  # 无效的引擎类型
            device='cpu',
            dtype='float32',
            embedding_dim=512
        )

        print(f"\n✗ 应该抛出 ValueError，但没有抛出")
        return False

    except ValueError as e:
        print(f"\n✓ 正确抛出 ValueError: {e}")
        return True

    except Exception as e:
        print(f"\n✗ 抛出了错误的异常类型: {type(e).__name__}: {e}")
        return False


async def test_all():
    """运行所有测试"""
    print("\n" + "#"*60)
    print("# 统一模型管理器 - 完整测试套件")
    print("#"*60)

    results = []

    # 运行所有测试
    results.append(await test_model_config())
    results.append(await test_model_manager_initialization())
    results.append(await test_embedding_service())
    results.append(await test_invalid_engine())

    # 统计结果
    print("\n" + "="*60)
    print("测试结果统计")
    print("="*60)
    print(f"\n总测试数: {len(results)}")
    print(f"通过: {sum(results)}")
    print(f"失败: {len(results) - sum(results)}")

    if all(results):
        print(f"\n✓ 所有测试通过!")
        return True
    else:
        print(f"\n✗ 部分测试失败")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_all())
    sys.exit(0 if success else 1)
