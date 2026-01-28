#!/usr/bin/env python3
"""
检查音频文件处理情况
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))

from src.core.config.config_manager import ConfigManager
from src.core.vector.vector_store import VectorStore


def check_audio_processing():
    """检查音频文件处理情况"""
    print("="*60)
    print("音频文件处理情况检查")
    print("="*60)
    
    # 加载配置
    config_manager = ConfigManager('config/config.yml')
    config = config_manager.get_all()
    
    # 初始化向量存储
    vector_store_config = {
        'data_dir': config.get('database.lancedb.data_dir', 'data/database/lancedb'),
        'collection_name': config.get('database.lancedb.collection_name', 'unified_vectors'),
        'index_type': config.get('database.lancedb.index_type', 'ivf_pq'),
        'num_partitions': config.get('database.lancedb.num_partitions', 128),
        'vector_dimension': config.get('database.lancedb.vector_dimension', 512)
    }
    
    try:
        import lancedb
        db = lancedb.connect(vector_store_config['data_dir'])
        table = db.open_table(vector_store_config['collection_name'])
        
        # 获取所有数据
        all_data = table.to_pandas()
        
        # 筛选音频数据
        audio_data = all_data[all_data['modality'] == 'audio']
        
        print(f"\n总向量数: {len(all_data)}")
        print(f"音频向量数: {len(audio_data)}")
        
        if len(audio_data) > 0:
            print("\n音频文件详情:")
            print("="*60)
            
            for i, row in audio_data.iterrows():
                # 解析 metadata
                import json
                metadata_dict = {}
                if 'metadata' in row:
                    if isinstance(row['metadata'], str):
                        try:
                            metadata_dict = json.loads(row['metadata']) if row['metadata'] else {}
                        except json.JSONDecodeError:
                            metadata_dict = {}
                    elif isinstance(row['metadata'], dict):
                        metadata_dict = row['metadata']
                
                file_name = metadata_dict.get('file_name', 'N/A')
                file_path = metadata_dict.get('file_path', 'N/A')
                vector_dim = len(row['vector']) if 'vector' in row else 0
                
                print(f"\n[{i+1}]")
                print(f"  文件名: {file_name}")
                print(f"  文件路径: {file_path}")
                print(f"  向量维度: {vector_dim}")
                print(f"  向量前5个值: {row['vector'][:5] if 'vector' in row else 'N/A'}")
        else:
            print("\n没有找到音频向量数据！")
        
        # 测试音频搜索
        print("\n" + "="*60)
        print("测试音频搜索")
        print("="*60)
        
        vector_store = VectorStore(vector_store_config)
        
        # 测试关键词
        test_keywords = ["音乐", "配音", "黄酒", "泪桥", "王杰", "伍佰"]
        
        for keyword in test_keywords:
            print(f"\n--- 搜索: '{keyword}' ---")
            
            # 搜索所有结果
            from src.core.embedding.embedding_engine import EmbeddingEngine
            import asyncio
            
            embedding_engine = EmbeddingEngine(config)
            asyncio.run(embedding_engine.preload_models())
            
            query_embedding = asyncio.run(embedding_engine.embed_text(keyword))
            results = vector_store.search(query_embedding, limit=10)
            
            # 筛选音频结果
            audio_results = [r for r in results if r.get('modality') == 'audio']
            image_results = [r for r in results if r.get('modality') == 'image']
            
            print(f"总结果: {len(results)}")
            print(f"  - 音频: {len(audio_results)}")
            print(f"  - 图像: {len(image_results)}")
            
            if audio_results:
                print("\n音频结果:")
                for j, result in enumerate(audio_results[:3], 1):
                    file_name = result.get('file_name', 'N/A')
                    score = result.get('similarity', 0)
                    print(f"  [{j}] {file_name} (相似度: {score:.4f})")
            else:
                print("未找到音频结果")
    
    except Exception as e:
        print(f"检查失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    check_audio_processing()
