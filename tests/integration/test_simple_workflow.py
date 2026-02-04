#!/usr/bin/env python3
"""
简单工作流程测试 - 直接使用系统组件
"""

import sys
import os
import asyncio
from pathlib import Path

# 设置环境变量
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['HF_DATASETS_OFFLINE'] = '1'
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['INFINITY_ANONYMOUS_USAGE_STATS'] = '0'

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))

from src.core.config.config_manager import ConfigManager
from src.core.vector.vector_store import VectorStore
from src.core.embedding.embedding_engine import EmbeddingEngine
from src.services.file.file_scanner import FileScanner
from src.services.media.media_processor import MediaProcessor


async def test_workflow():
    """测试工作流程"""
    print("="*60)
    print("msearch 简单工作流程测试")
    print("="*60)
    
    # 加载配置
    config_manager = ConfigManager('config/config.yml')
    config = config_manager.get_all()
    
    # 初始化组件
    print("\n[1/5] 初始化组件...")
    
    # 向量存储
    vector_store_config = {
        'data_dir': config.get('database.lancedb.data_dir', 'data/database/lancedb'),
        'collection_name': config.get('database.lancedb.collection_name', 'unified_vectors'),
        'index_type': config.get('database.lancedb.index_type', 'ivf_pq'),
        'num_partitions': config.get('database.lancedb.num_partitions', 128),
        'vector_dimension': config.get('database.lancedb.vector_dimension', 512)
    }
    vector_store = VectorStore(vector_store_config)
    print("✓ 向量存储初始化完成")
    
    # 向量化引擎
    embedding_engine = EmbeddingEngine(config)
    await embedding_engine.preload_models()
    print("✓ 向量化引擎初始化完成")
    
    # 文件扫描器
    scanner_config = {
        "recursive": True,
        "scan_images": True,
        "scan_videos": False,
        "scan_audio": False
    }
    scanner = FileScanner(scanner_config)
    print("✓ 文件扫描器初始化完成")
    
    # 媒体处理器
    media_processor = MediaProcessor(config)
    print("✓ 媒体处理器初始化完成")
    
    # 扫描文件
    print("\n[2/5] 扫描 testdata 目录...")
    testdata_dir = Path("testdata")
    files = scanner.scan_directory(str(testdata_dir))
    print(f"找到 {len(files)} 个文件")
    
    # 处理文件
    print("\n[3/5] 处理文件并索引...")
    processed_count = 0
    for i, file_path in enumerate(files[:10], 1):  # 只处理前10个文件
        print(f"\n处理文件 {i}/{min(10, len(files))}: {file_path}")
        
        try:
            # 处理文件
            result = media_processor.process_file(file_path)
            
            if result.get('status') == 'success':
                media_type = result.get('media_type')
                metadata = result.get('metadata', {})
                
                print(f"  ✓ 文件处理成功")
                print(f"    媒体类型: {media_type}")
                print(f"    文件名: {metadata.get('file_name', 'N/A')}")
                
                # 向量化
                if media_type == 'image':
                    embedding = await embedding_engine.embed_image(file_path)
                    print(f"  ✓ 向量化成功，向量维度: {len(embedding)}")
                    
                    # 存储到向量数据库
                    vector_data = {
                        'id': metadata.get('file_hash', ''),
                        'vector': embedding,
                        'modality': media_type,
                        'file_id': metadata.get('file_hash', ''),
                        'metadata': {
                            'file_name': metadata.get('file_name', ''),
                            'file_path': file_path,
                            'media_type': media_type,
                            'file_size': metadata.get('file_size', 0)
                        }
                    }
                    
                    vector_store.add_vector(vector_data)
                    print(f"  ✓ 向量存储成功")
                    
                    processed_count += 1
                else:
                    print(f"  ! 跳过非图像文件: {media_type}")
            else:
                print(f"  ✗ 文件处理失败: {result.get('error')}")
                
        except Exception as e:
            print(f"  ✗ 文件处理异常: {e}")
    
    print(f"\n总计: 成功处理 {processed_count} 个文件")
    
    # 测试搜索
    print("\n[4/5] 测试搜索功能...")
    
    keywords = ["老虎", "骑行", "樱桃", "人物", "风景", "猫"]
    
    for keyword in keywords:
        print(f"\n--- 搜索: '{keyword}' ---")
        print("="*60)
        
        try:
            # 向量化
            query_embedding = await embedding_engine.embed_text(keyword)
            
            # 搜索
            results = vector_store.search(query_embedding, limit=5)
            print(f"找到 {len(results)} 个结果")
            
            # 显示结果
            for j, result in enumerate(results, 1):
                file_name = result.get('file_name', result.get('metadata', {}).get('file_name', 'N/A'))
                file_path = result.get('file_path', result.get('metadata', {}).get('file_path', 'N/A'))
                media_type = result.get('modality', 'N/A')
                score = result.get('similarity', 0)
                
                print(f"\n[{j}] 相似度: {score:.4f}")
                print(f"    文件: {file_name}")
                print(f"    路径: {file_path}")
                print(f"    类型: {media_type}")
            
            if len(results) == 0:
                print("未找到任何结果")
        
        except Exception as e:
            print(f"搜索失败: {e}")
    
    # 统计信息
    print("\n[5/5] 向量存储统计...")
    stats = vector_store.get_collection_stats()
    print(f"总向量数: {stats.get('vector_count', 0)}")
    print(f"向量维度: {stats.get('vector_dimension', 'N/A')}")
    
    print("\n" + "="*60)
    print("所有测试完成！")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(test_workflow())
