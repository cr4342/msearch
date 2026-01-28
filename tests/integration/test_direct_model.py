#!/usr/bin/env python3
"""
直接测试模型加载和向量化
"""

import os
import sys
import asyncio
import time
from pathlib import Path

# 离线环境变量
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['HF_HUB_DISABLE_IMPORT_ERROR'] = '1'
os.environ['NO_PROXY'] = '*'

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)


def test_model_loading():
    """测试模型加载"""
    print("\n" + "="*60)
    print("测试1: 直接加载本地模型")
    print("="*60)
    
    from infinity_emb import AsyncEmbeddingEngine, EngineArgs
    
    model_path = PROJECT_ROOT / "data" / "models" / "chinese-clip-vit-base-patch16"
    print(f"模型路径: {model_path}")
    
    # 检查模型文件
    if not model_path.exists():
        print(f"  ✗ 模型目录不存在: {model_path}")
        return False
        
    config_file = model_path / "config.json"
    if not config_file.exists():
        print(f"  ✗ 配置文件不存在: {config_file}")
        return False
        
    print("  ✓ 模型文件存在")
    
    # 创建引擎参数
    engine_args = EngineArgs(
        model_name_or_path=str(model_path),
        engine="torch",
        dtype="float32",
        trust_remote_code=True,
        compile=False,
    )
    
    print("\n创建EmbeddingEngine...")
    engine = AsyncEmbeddingEngine.from_args(engine_args)
    
    print("\n启动引擎（加载模型）...")
    start = time.time()
    
    # 使用异步方式启动
    async def start_engine():
        return await engine.astart()
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_engine())
    loop.close()
    
    elapsed = time.time() - start
    print(f"  ✓ 引擎启动成功 (耗时: {elapsed:.1f}s)")
    
    return engine


def test_embedding(engine, file_path, modality):
    """测试向量化"""
    print(f"\n" + "="*60)
    print(f"测试: {modality}向量化 - {file_path.name}")
    print("="*60)
    
    if not file_path.exists():
        print(f"  ✗ 文件不存在: {file_path}")
        return None
        
    start = time.time()
    
    async def embed():
        if modality == "image":
            return await engine.embed(image=file_path)
        elif modality == "text":
            return await engine.embed(text=file_path)
        else:
            raise ValueError(f"不支持的模态: {modality}")
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(embed())
    loop.close()
    
    elapsed = time.time() - start
    embedding = result.embeddings[0]
    dim = len(embedding)
    
    print(f"  ✓ {modality}向量化成功")
    print(f"      维度: {dim}")
    print(f"      耗时: {elapsed:.2f}s")
    
    return embedding


def main():
    try:
        # 测试1: 加载模型
        engine = test_model_loading()
        if not engine:
            print("\n✗ 模型加载失败")
            return False
            
        # 测试2: 图像向量化
        img_path = PROJECT_ROOT / "testdata" / "周星驰.jpg"
        if img_path.exists():
            test_embedding(engine, img_path, "image")
        else:
            print(f"\n图像文件不存在: {img_path}")
            
        # 测试3: 文本向量化
        test_embedding(engine, "人物照片", "text")
        
        print("\n" + "="*60)
        print("✓ 所有直接测试通过！")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)