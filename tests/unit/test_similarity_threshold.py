#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试相似度阈值功能
"""

import sys
import os
from pathlib import Path
import asyncio

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

from src.core.config.config_manager import ConfigManager
from src.core.vector.vector_store import VectorStore
from src.core.embedding.embedding_engine import EmbeddingEngine

async def test_similarity_threshold():
    """测试相似度阈值功能"""
    print("=" * 60)
    print("测试相似度阈值功能")
    print("=" * 60)
    
    # 初始化组件
    config_manager = ConfigManager()
    config = config_manager.config
    
    # 向量存储
    vector_store_config = {
        'data_dir': config_manager.get('database.lancedb.data_dir', 'data/database/lancedb'),
        'collection_name': config_manager.get('database.lancedb.collection_name', 'unified_vectors'),
        'index_type': config_manager.get('database.lancedb.index_type', 'ivf_pq'),
        'num_partitions': config_manager.get('database.lancedb.num_partitions', 128),
        'vector_dimension': config_manager.get('database.lancedb.vector_dimension', 512)
    }
    vector_store = VectorStore(vector_store_config)
    print("✓ 向量存储初始化完成")
    
    # 向量化引擎
    embedding_engine = EmbeddingEngine(config)
    await embedding_engine.preload_models()
    print("✓ 向量化引擎初始化完成")
    
    # 测试关键词
    test_keywords = ["熊猫", "老虎"]
    thresholds = [0.0, 0.3, 0.4, 0.5]
    
    for keyword in test_keywords:
        print("\n" + "=" * 60)
        print(f"测试关键词: '{keyword}'")
        print("=" * 60)
        
        # 向量化
        query_embedding = await embedding_engine.embed_text(keyword)
        print(f"查询向量维度: {len(query_embedding)}")
        
        for threshold in thresholds:
            print(f"\n--- 相似度阈值: {threshold} ---")
            
            # 向量检索
            results = vector_store.search(
                query_embedding, 
                limit=20, 
                similarity_threshold=threshold
            )
            
            print(f"找到 {len(results)} 个结果")
            
            if len(results) > 0:
                # 显示前5个结果的相似度
                print("\n前5个结果的相似度:")
                for i, result in enumerate(results[:5]):
                    similarity = result.get('similarity', 0)
                    file_name = result.get('file_name', result.get('metadata', {}).get('file_name', '未知'))
                    print(f"  {i+1}. {file_name} - 相似度: {similarity:.4f}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_similarity_threshold())