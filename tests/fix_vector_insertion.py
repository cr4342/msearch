import sys
import asyncio
import os
sys.path.insert(0, '/data/project/msearch')

from src.core.config.config_manager import ConfigManager
from src.core.vector.vector_store import VectorStore
from src.core.embedding.embedding_engine import EmbeddingEngine

async def fix_vector_insertion():
    """修复向量插入和检索"""
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
    
    # 处理所有图片文件
    testdata_dir = '/data/project/msearch/testdata'
    image_files = [f for f in os.listdir(testdata_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    print(f"找到 {len(image_files)} 个图片文件")
    
    for image_file in image_files:
        image_path = f"{testdata_dir}/{image_file}"
        print(f"\n处理图片: {image_file}")
        
        # 向量化
        embedding = await embedding_engine.embed_image(image_path)
        print(f"✓ 向量化成功，向量维度: {len(embedding)}")
        
        # 生成正确的向量数据
        vector_data = {
            'modality': 'image',
            'file_path': image_path,
            'file_name': image_file,
            'file_type': os.path.splitext(image_file)[1][1:].lower(),
            'vector': embedding
        }
        
        # 插入向量
        vector_store.add_vector(vector_data)
        print(f"✓ 向量存储成功")
    
    # 测试语义检索
    print("\n=== 测试语义检索 ===")
    test_queries = ["老虎", "人物", "风景", "动物"]
    
    for query in test_queries:
        print(f"\n搜索: '{query}'")
        query_embedding = await embedding_engine.embed_text(query)
        
        # 搜索向量
        results = vector_store.search(query_embedding, limit=3)
        print(f"找到 {len(results)} 个结果:")
        
        for i, result in enumerate(results):
            print(f"[{i+1}] 相似度: {result.get('similarity', 0):.4f}")
            print(f"    文件: {result.get('file_name', '未知')}")
            print(f"    路径: {result.get('file_path', '未知')}")
            print(f"    模态: {result.get('modality', '未知')}")
    
    return True

if __name__ == "__main__":
    result = asyncio.run(fix_vector_insertion())
    sys.exit(0 if result else 1)
