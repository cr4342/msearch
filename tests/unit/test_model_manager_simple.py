#!/usr/bin/env python3
"""
简单测试模型管理器
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

print(f"项目根目录: {project_root}")
print(f"Python路径: {sys.path[:2]}")

# 直接导入模块
try:
    from core.models.model_manager import ModelConfig, ModelManager
    print("\n✓ 成功导入模型管理器模块")
except Exception as e:
    print(f"\n✗ 导入失败: {e}")
    sys.exit(1)


async def test():
    """测试"""
    print("\n" + "="*60)
    print("测试模型配置")
    print("="*60)

    try:
        # 1. 创建模型配置
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
            local_path=str(project_root / "data/models/chinese-clip-vit-large-patch14-336px")
        )

        print(f"\n✓ 创建模型配置成功:")
        print(f"  - 模型名称: {config.name}")
        print(f"  - 引擎类型: {config.engine}")
        print(f"  - 设备: {config.device}")
        print(f"  - 数据类型: {config.dtype}")
        print(f"  - 向量维度: {config.embedding_dim}")

        # 2. 检查本地模型路径
        if config.local_path and os.path.exists(config.local_path):
            print(f"\n✓ 本地模型路径存在: {config.local_path}")
            files = os.listdir(config.local_path)
            print(f"  - 目录文件数: {len(files)}")
        else:
            print(f"\n⚠ 本地模型路径不存在: {config.local_path}")

        # 3. 测试无效引擎
        print("\n" + "="*60)
        print("测试无效引擎类型验证")
        print("="*60)

        try:
            invalid_config = ModelConfig(
                name='test',
                engine='invalid_engine',  # 无效引擎
                device='cpu',
                embedding_dim=512
            )
            print("✗ 应该抛出异常，但没有")
        except ValueError as e:
            print(f"✓ 正确抛出 ValueError: {e}")

        return True

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import asyncio
    success = asyncio.run(test())
    sys.exit(0 if success else 1)
