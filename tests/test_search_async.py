#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 WebUI 搜索功能 - 直接调用
"""

import sys
import os
from pathlib import Path
import asyncio

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))

from src.core.config.config_manager import ConfigManager
from src.core.vector.vector_store import VectorStore
from src.core.embedding.embedding_engine import EmbeddingEngine

async def test_search():
    """测试搜索功能"""
    print("="*60)
    print("测试搜索功能")
    print("="*60)
    
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
    keywords = ["熊猫", "老虎", "音乐", "风景"]
    
    for keyword in keywords:
        print(f"\n--- 搜索: '{keyword}' ---")
        print("="*60)
        
        try:
            # 向量化
            query_embedding = await embedding_engine.embed_text(keyword)
            print(f"查询向量维度: {len(query_embedding)}")
            
            # 向量检索
            results = vector_store.search(query_embedding, limit=10)
            print(f"找到 {len(results)} 个结果")
            
            # 格式化结果
            if len(results) == 0:
                print("未找到任何结果")
            else:
                for i, result in enumerate(results[:5]):
                    file_name = result.get('file_name', result.get('metadata', {}).get('file_name', result.get('file_path', '未知')))
                    file_path = result.get('file_path', result.get('metadata', {}).get('file_path', '未知'))
                    media_type = result.get('media_type', result.get('modality', '未知'))
                    score = result.get('score', result.get('similarity', 0))
                    
                    print(f"\n[{i+1}/{len(results)}]")
                    print(f"  文件: {file_name}")
                    print(f"  路径: {file_path}")
                    print(f"  类型: {media_type}")
                    print(f"  相似度: {score:.4f}")
            
        except Exception as e:
            print(f"搜索失败: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_search())