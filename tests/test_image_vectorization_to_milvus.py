#!/usr/bin/env python3
"""
测试图片向量化存入Milvus的完整流程
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
import numpy as np
from PIL import Image

# 可选导入pytest，用于在pytest框架中运行
try:
    import pytest
except ImportError:
    pass

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.common.embedding.embedding_engine import EmbeddingEngine
from src.common.storage.milvus_adapter import MilvusAdapter
from src.core.config_manager import get_config_manager


import asyncio

def test_image_vectorization_to_milvus():
    """
    测试图片向量化存入Milvus的完整流程
    遵循Arrange-Act-Assert（AAA）模式
    """
    # Arrange：准备测试环境
    config_manager = get_config_manager()
    embedding_engine = EmbeddingEngine(config_manager)
    milvus_adapter = MilvusAdapter(config_manager)
    
    # 创建临时测试图片
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
        test_image_path = f.name
    
    # 创建一个简单的测试图片（红色背景，100x100）
    img = Image.new('RGB', (100, 100), color='red')
    img.save(test_image_path)
    
    async def run_async_test():
        """异步测试函数"""
        # 连接到Milvus
        await milvus_adapter.connect()
        
        # 读取图片字节数据
        with open(test_image_path, 'rb') as f:
            image_bytes = f.read()
        
        # Act：执行图片向量化和存入Milvus操作
        # 1. 使用真实模型生成图片向量
        embedding = await embedding_engine.embed_image(image_bytes)
        
        # 2. 将向量存入Milvus
        vector_id = await milvus_adapter.store_vector("visual", embedding, "test_image", None, {"description": "test_description"})
        
        return embedding, vector_id
    
    try:
        # 在同步函数中运行异步测试
        embedding, vector_id = asyncio.run(run_async_test())
        
        # Assert：验证结果
        # 1. 验证向量生成成功
        assert embedding is not None, "向量生成失败"
        assert isinstance(embedding, np.ndarray), "向量应该是numpy数组"
        assert len(embedding) == 512, f"向量维度应该是512，实际是{len(embedding)}"
        
        # 2. 验证向量存入Milvus成功
        assert vector_id is not None, "向量存入Milvus失败"
        assert isinstance(vector_id, (int, str)), "向量ID应该是整数或字符串"
        
        print(f"✅ 图片向量化存入Milvus测试通过")
        print(f"   向量ID: {vector_id}")
        print(f"   向量维度: {len(embedding)}")
        print(f"   向量示例: {embedding[:5]}...")
        
    finally:
        # 清理测试资源
        os.unlink(test_image_path)
        
        # 可选：从Milvus中删除测试向量
        if 'vector_id' in locals() and vector_id is not None:
            milvus_adapter.delete_vector(vector_id)


def test_image_folder_vectorization():
    """
    测试文件夹中多张图片的向量化和批量存入Milvus
    """
    # Arrange：准备测试环境
    config_manager = get_config_manager()
    embedding_engine = EmbeddingEngine(config_manager)
    milvus_adapter = MilvusAdapter(config_manager)
    
    # 创建临时测试文件夹
    test_folder = tempfile.mkdtemp()
    
    # 在临时文件夹中创建3张测试图片
    test_images = []
    for i in range(3):
        image_path = os.path.join(test_folder, f"test_image_{i}.jpg")
        img = Image.new('RGB', (100, 100), color=['red', 'green', 'blue'][i])
        img.save(image_path)
        test_images.append(image_path)
    
    async def run_async_test():
        """异步测试函数"""
        # 连接到Milvus
        await milvus_adapter.connect()
        
        vector_ids = []
        
        for image_path in test_images:
            # 读取图片字节数据
            with open(image_path, 'rb') as f:
                image_bytes = f.read()
            
            # 1. 使用真实模型生成图片向量
            embedding = await embedding_engine.embed_image(image_bytes)
            
            # 2. 将向量存入Milvus
            vector_id = await milvus_adapter.store_vector(
                "visual", 
                embedding, 
                os.path.basename(image_path), 
                None, 
                {"description": "test_image_description"}
            )
            
            vector_ids.append(vector_id)
        
        return vector_ids
    
    try:
        # 在同步函数中运行异步测试
        vector_ids = asyncio.run(run_async_test())
        
        # Assert：验证结果
        # 1. 验证所有向量生成成功
        assert len(vector_ids) == 3, f"应该生成3个向量，实际生成{len(vector_ids)}个"
        
        # 2. 验证所有向量ID都不为空
        for vector_id in vector_ids:
            assert vector_id is not None, "向量ID不应该为空"
        
        print(f"✅ 文件夹中多张图片向量化测试通过")
        print(f"   生成的向量ID: {vector_ids}")
        
    finally:
        # 清理测试资源
        shutil.rmtree(test_folder)
        
        # 从Milvus中删除测试向量
        for vector_id in vector_ids:
            if vector_id is not None:
                milvus_adapter.delete_vector(vector_id)


if __name__ == "__main__":
    # 运行测试
    print("开始测试图片向量化存入Milvus的完整流程...")
    
    try:
        test_image_vectorization_to_milvus()
        print("\n")
        test_image_folder_vectorization()
        print("\n✅ 所有测试通过！")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
