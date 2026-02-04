#!/usr/bin/env python3
"""
直接测试搜索功能（不通过API）
"""

import sys
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))

from src.core.config.config_manager import ConfigManager
from src.core.vector.vector_store import VectorStore
from src.core.embedding.embedding_engine import EmbeddingEngine


async def test_search():
    """测试搜索功能"""
    print("="*60)
    print("msearch 搜索功能测试")
    print("="*60)
    
    # 加载配置
    config_manager = ConfigManager('config/config.yml')
    config = config_manager.get_all()
    
    # 初始化组件
    print("\n[1/4] 初始化向量存储...")
    vector_store_config = {
        'data_dir': config.get('database.lancedb.data_dir', 'data/database/lancedb'),
        'collection_name': config.get('database.lancedb.collection_name', 'unified_vectors'),
        'index_type': config.get('database.lancedb.index_type', 'ivf_pq'),
        'num_partitions': config.get('database.lancedb.num_partitions', 128),
        'vector_dimension': config.get('database.lancedb.vector_dimension', 512)
    }
    vector_store = VectorStore(vector_store_config)
    stats = vector_store.get_collection_stats()
    print(f"✓ 向量存储初始化完成")
    print(f"  总向量数: {stats.get('vector_count', 0)}")
    print(f"  向量维度: {stats.get('vector_dimension', '未知')}")
    
    print("\n[2/4] 初始化向量化引擎...")
    embedding_engine = EmbeddingEngine(config)
    await embedding_engine.preload_models()
    print("✓ 向量化引擎初始化完成")
    
    # 测试搜索
    test_queries = [
        "老虎",
        "骑行",
        "樱桃",
        "人物",
        "风景",
        "猫"
    ]
    
    print("\n[3/4] 测试搜索功能...")
    for i, query in enumerate(test_queries, 1):
        print(f"\n--- 测试 {i}/{len(test_queries)}: '{query}' ---")
        print("="*60)
        
        try:
            # 向量化
            query_embedding = await embedding_engine.embed_text(query)
            print(f"查询向量维度: {len(query_embedding)}")
            
            # 搜索
            results = vector_store.search(query_embedding, limit=5)
            print(f"找到 {len(results)} 个结果")
            
            # 显示结果
            for j, result in enumerate(results, 1):
                file_name = result.get('file_name', result.get('metadata', {}).get('file_name', result.get('file_path', '未知')))
                file_path = result.get('file_path', result.get('metadata', {}).get('file_path', '未知'))
                media_type = result.get('media_type', result.get('modality', '未知'))
                score = result.get('score', result.get('similarity', 0))
                
                print(f"\n[{j}] 相似度: {score:.4f}")
                print(f"    文件: {file_name}")
                print(f"    路径: {file_path}")
                print(f"    类型: {media_type}")
            
            if len(results) == 0:
                print("未找到任何结果")
        
        except Exception as e:
            print(f"搜索失败: {e}")
    
    print("\n[4/4] 测试完成")
    print("="*60)
    print("所有搜索测试完成！")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(test_search())
