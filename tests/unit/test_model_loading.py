"""
简单测试脚本：测试模型加载
"""
import sys
import os
import asyncio
from pathlib import Path

# 设置离线模式环境变量
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from infinity_emb import AsyncEmbeddingEngine, EngineArgs


async def test_model_loading():
    """测试模型加载"""
    print("=" * 60)
    print("测试模型加载")
    print("=" * 60)
    
    model_path = "data/models/chinese-clip-vit-base-patch16"
    
    print(f"\n1. 检查模型路径: {model_path}")
    if not os.path.exists(model_path):
        print(f"   错误: 模型路径不存在")
        return False
    
    print(f"   模型路径存在")
    
    print(f"\n2. 检查模型文件")
    model_files = os.listdir(model_path)
    print(f"   找到 {len(model_files)} 个文件")
    for f in model_files[:10]:
        print(f"   - {f}")
    
    print(f"\n3. 创建EngineArgs")
    try:
        engine_args = EngineArgs(
            model_name_or_path=model_path,
            engine="torch",
            device="cpu",
            dtype="float32",
            trust_remote_code=True,
            compile=False,
            embedding_dtype="float32",
            pooling_method="mean",
            batch_size=4,
            model_warmup=False
        )
        print(f"   EngineArgs创建成功")
    except Exception as e:
        print(f"   错误: EngineArgs创建失败 - {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print(f"\n4. 创建AsyncEmbeddingEngine")
    try:
        client = AsyncEmbeddingEngine.from_args(engine_args)
        print(f"   AsyncEmbeddingEngine创建成功")
    except Exception as e:
        print(f"   错误: AsyncEmbeddingEngine创建失败 - {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print(f"\n5. 启动模型（这可能需要几分钟）")
    try:
        await client.astart()
        print(f"   模型启动成功")
    except Exception as e:
        print(f"   错误: 模型启动失败 - {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print(f"\n6. 测试文本向量化")
    try:
        result, _ = await client.embed(["测试文本"])
        print(f"   文本向量化成功，向量维度: {len(result[0])}")
    except Exception as e:
        print(f"   错误: 文本向量化失败 - {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print(f"\n7. 停止模型")
    try:
        await client.astop()
        print(f"   模型停止成功")
    except Exception as e:
        print(f"   警告: 模型停止失败 - {e}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(test_model_loading())
        if success:
            print("\n测试成功!")
        else:
            print("\n测试失败")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
