#!/usr/bin/env python3
"""
测试语义检索功能
"""

import os
import sys
import asyncio
import numpy as np
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
src_root = project_root / "src"
sys.path.insert(0, str(src_root))
sys.path.insert(0, str(project_root))

# 设置离线环境变量
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['HF_DATASETS_OFFLINE'] = '1'
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'

from core.config.config_manager import ConfigManager
from core.vector.vector_store import VectorStore
from core.embedding.embedding_engine import EmbeddingEngine


async def test_semantic_search():
    """测试语义检索"""
    print("\n" + "="*60)
    print("测试语义检索功能")
    print("="*60)
    
    # 加载配置
    config_manager = ConfigManager()
    config = config_manager.get_all()
    
    # 初始化向量存储
    vector_db_path = config.get('database', {}).get('vector_db_path', 'data/database/lancedb')
    vector_store_config = {
        'data_dir': vector_db_path,
        'collection_name': 'unified_vectors',
        'index_type': 'ivf_pq',
        'num_partitions': 128,
        'vector_dimension': 512
    }
    vector_store = VectorStore(vector_store_config)
    vector_store.initialize()
    print("✓ 向量存储初始化完成")
    
    # 初始化向量化引擎
    embedding_engine = EmbeddingEngine(config)
    await embedding_engine.initialize()
    print("✓ 向量化引擎初始化完成")
    
    # 测试文本搜索
    print("\n" + "-"*60)
    print("测试1: 文本语义搜索")
    print("-"*60)
    
    test_queries = [
        "人物",
        "风景",
        "建筑",
        "动物",
        "卡通"
    ]
    
    for query in test_queries:
        print(f"\n查询: '{query}'")
        
        # 生成查询向量
        query_embedding = await embedding_engine.embed_text(query)
        
        # 执行搜索
        results = vector_store.search(query_embedding, limit=3)
        
        print(f"  找到 {len(results)} 个结果:")
        for i, result in enumerate(results[:3]):
            file_path = result.get('file_path', 'N/A')
            similarity = result.get('similarity', 0)
            file_type = result.get('file_type', 'unknown')
            print(f"    {i+1}. {Path(file_path).name} ({file_type}, 相似度: {similarity:.4f})")
    
    # 测试图像搜索
    print("\n" + "-"*60)
    print("测试2: 图像语义搜索")
    print("-"*60)
    
    # 查找测试图像
    testdata_dir = Path("testdata")
    image_files = list(testdata_dir.glob("*.jpg"))[:2]
    
    for test_image in image_files:
        print(f"\n使用图像搜索: {test_image.name}")
        
        # 生成图像向量
        query_embedding = await embedding_engine.embed_image(str(test_image))
        
        # 执行搜索
        results = vector_store.search(query_embedding, limit=3)
        
        print(f"  找到 {len(results)} 个相似结果:")
        for i, result in enumerate(results[:3]):
            file_path = result.get('file_path', 'N/A')
            similarity = result.get('similarity', 0)
            print(f"    {i+1}. {Path(file_path).name} (相似度: {similarity:.4f})")
    
    # 关闭组件
    vector_store.close()
    await embedding_engine.shutdown()
    
    print("\n" + "="*60)
    print("语义检索测试完成")
    print("="*60)


if __name__ == '__main__':
    asyncio.run(test_semantic_search())
