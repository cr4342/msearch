#!/usr/bin/env python3
"""
真实模型离线处理测试
测试本地模型处理testdata数据，确保不依赖网络
"""
import os
import sys
from pathlib import Path

# 设置项目根目录
PROJECT_ROOT = Path(__file__).parent

# ============================================
# 设置离线环境变量（在导入任何模块之前）
# ============================================
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['HF_DATASETS_OFFLINE'] = '1'
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
os.environ['HF_HUB_DISABLE_IMPORT_ERROR'] = '1'
os.environ['HF_HOME'] = str(PROJECT_ROOT / "data" / "models")
os.environ['NO_PROXY'] = '*'
os.environ['no_proxy'] = '*'

print("=" * 60)
print("离线模式测试")
print("=" * 60)
print(f"TRANSFORMERS_OFFLINE: {os.environ.get('TRANSFORMERS_OFFLINE')}")
print(f"HF_HUB_OFFLINE: {os.environ.get('HF_HUB_OFFLINE')}")
print(f"HF_HOME: {os.environ.get('HF_HOME')}")
print()

# 现在可以安全导入模块
import asyncio
from infinity_emb import AsyncEmbeddingEngine, EngineArgs

async def test_models():
    """测试模型加载和推理"""
    print("=" * 60)
    print("1. 测试 EmbeddingEngine 初始化 (chinese-clip)")
    print("=" * 60)

    # 使用本地模型路径
    model_path = PROJECT_ROOT / "data" / "models" / "chinese-clip-vit-base-patch16"

    print(f"模型路径: {model_path}")
    print(f"路径存在: {model_path.exists()}")

    try:
        engine_args = EngineArgs(
            model_name_or_path=str(model_path),
            device="cpu",
            batch_size=1
        )
        engine = AsyncEmbeddingEngine.from_args(engine_args)
        await engine.__aenter__()
        print("✓ EmbeddingEngine (chinese-clip) 初始化成功")

        # 测试图像向量化
        print()
        print("=" * 60)
        print("2. 测试图像向量化")
        print("=" * 60)

        test_images = list((PROJECT_ROOT / "testdata").glob("*.jpg"))
        test_images += list((PROJECT_ROOT / "testdata").glob("*.png"))
        print(f"找到 {len(test_images)} 张测试图像")

        if test_images:
            # 测试第一张图像
            test_image = test_images[0]
            print(f"测试图像: {test_image.name}")

            emb = await engine.embed_image([str(test_image)])
            print(f"✓ 图像向量化成功，维度: {emb[0].shape}")

        # 测试文本向量化
        print()
        print("=" * 60)
        print("3. 测试文本向量化")
        print("=" * 60)

        test_texts = ["测试文本", "天空", "大海"]
        emb = await engine.embed_text(test_texts)
        print(f"✓ 文本向量化成功，维度: {emb[0].shape}")

        # 测试音频模型
        print()
        print("=" * 60)
        print("4. 测试音频模型 (CLAP)")
        print("=" * 60)

        audio_path = PROJECT_ROOT / "testdata" / "伍佰 & China Blue-泪桥.mp3"
        if audio_path.exists():
            print(f"测试音频: {audio_path.name}")

            # 加载CLAP模型
            clap_model_path = PROJECT_ROOT / "data" / "models" / "clap-htsat-unfused"
            clap_engine_args = EngineArgs(
                model_name_or_path=str(clap_model_path),
                device="cpu",
                batch_size=1
            )
            clap_engine = AsyncEmbeddingEngine.from_args(clap_engine_args)
            await clap_engine.__aenter__()

            emb = await clap_engine.embed_audio([str(audio_path)])
            print(f"✓ 音频向量化成功，维度: {emb[0].shape}")

        print()
        print("=" * 60)
        print("✓ 所有测试通过！模型可以在完全离线模式下运行")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_models())
    sys.exit(0 if result else 1)