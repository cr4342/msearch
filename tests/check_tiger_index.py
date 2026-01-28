import sys
import asyncio
import os
sys.path.insert(0, '/data/project/msearch')

from src.core.config.config_manager import ConfigManager
from src.core.vector.vector_store import VectorStore
from src.core.embedding.embedding_engine import EmbeddingEngine

async def check_tiger_index():
    """检查老虎图片索引情况"""
    print("初始化组件...")
    config_manager = ConfigManager('/data/project/msearch/config/config.yml')
    config = config_manager.config
    
    vector_store_config = {
        'data_dir': config.get('database.lancedb.data_dir', 'data/database/lancedb'),
        'collection_name': config.get('database.lancedb.collection_name', 'unified_vectors'),
        'index_type': config.get('database.lancedb.index_type', 'ivf_pq'),
        'num_partitions': config.get('database.lancedb.num_partitions', 128),
        'vector_dimension': config.get('database.lancedb.vector_dimension', 512)
    }
    vector_store = VectorStore(vector_store_config)
    print("✓ 向量存储初始化完成")
    
    embedding_engine = EmbeddingEngine(config)
    print("✓ 向量化引擎初始化完成")
    print()
    
    # 检查向量存储中的老虎图片
    tiger_image = '/data/project/msearch/testdata/OIP-C (5).jpg'
    print(f"检查老虎图片: {tiger_image}")
    
    # 1. 检查向量数量
    stats = vector_store.get_collection_stats()
    print(f"向量存储统计: {stats}")
    
    # 2. 搜索老虎图片
    print(f"\n搜索老虎图片向量...")
    query_embedding = await embedding_engine.embed_image(tiger_image)
    results = vector_store.search(query_embedding, limit=5)
    print(f"找到 {len(results)} 个相似向量:")
    
    for i, result in enumerate(results):
        print(f"[{i+1}] 相似度: {result.get('similarity', 0):.4f}")
        print(f"    文件: {result.get('file_name', '未知')}")
        print(f"    路径: {result.get('file_path', '未知')}")
        print(f"    模态: {result.get('modality', '未知')}")
    
    # 3. 测试文本搜索"老虎"
    print(f"\n测试文本搜索: '老虎'")
    text_embedding = await embedding_engine.embed_text("老虎")
    text_results = vector_store.search(text_embedding, limit=5)
    print(f"找到 {len(text_results)} 个结果:")
    
    for i, result in enumerate(text_results):
        print(f"[{i+1}] 相似度: {result.get('similarity', 0):.4f}")
        print(f"    文件: {result.get('file_name', '未知')}")
        print(f"    路径: {result.get('file_path', '未知')}")
        print(f"    模态: {result.get('modality', '未知')}")
    
    return True

if __name__ == "__main__":
    result = asyncio.run(check_tiger_index())
    sys.exit(0 if result else 1)
