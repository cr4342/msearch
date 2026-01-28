#!/usr/bin/env python3
"""
测试文件监视和多模态搜索功能
"""

import sys
import os
import asyncio
import time
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


async def test_file_monitoring_and_search():
    """测试文件监视和多模态搜索"""
    print("="*60)
    print("msearch 文件监视和多模态搜索测试")
    print("="*60)
    
    # 加载配置
    config_manager = ConfigManager('config/config.yml')
    config = config_manager.get_all()
    
    # 初始化组件
    print("\n[1/6] 初始化组件...")
    
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
        "scan_videos": True,
        "scan_audio": True
    }
    scanner = FileScanner(scanner_config)
    print("✓ 文件扫描器初始化完成")
    
    # 媒体处理器
    media_processor = MediaProcessor(config)
    print("✓ 媒体处理器初始化完成")
    
    # 扫描文件
    print("\n[2/6] 扫描 testdata 目录...")
    testdata_dir = Path("testdata")
    files = scanner.scan_directory(str(testdata_dir))
    print(f"找到 {len(files)} 个文件")
    
    # 统计文件类型
    image_files = [f for f in files if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp'))]
    audio_files = [f for f in files if f.lower().endswith(('.mp3', '.wav', '.flac', '.aac', '.ogg'))]
    video_files = [f for f in files if f.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.flv'))]
    
    print(f"  - 图像文件: {len(image_files)}")
    print(f"  - 音频文件: {len(audio_files)}")
    print(f"  - 视频文件: {len(video_files)}")
    
    # 处理文件
    print("\n[3/6] 处理文件并索引...")
    processed_count = 0
    processed_images = 0
    processed_audio = 0
    
    for i, file_path in enumerate(files, 1):
        try:
            # 处理文件
            result = media_processor.process_file(file_path)
            
            if result.get('status') == 'success':
                media_type = result.get('media_type')
                metadata = result.get('metadata', {})
                file_name = metadata.get('file_name', file_path)
                
                # 向量化
                if media_type == 'image':
                    embedding = await embedding_engine.embed_image(file_path)
                    processed_images += 1
                    print(f"[{i}/{len(files)}] ✓ 图像: {file_name}")
                    
                elif media_type == 'audio':
                    embedding = await embedding_engine.embed_audio(file_path)
                    processed_audio += 1
                    print(f"[{i}/{len(files)}] ✓ 音频: {file_name}")
                    
                else:
                    print(f"[{i}/{len(files)}] ! 跳过: {media_type}")
                    continue
                
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
                processed_count += 1
                
            else:
                print(f"[{i}/{len(files)}] ✗ 处理失败: {result.get('error')}")
                
        except Exception as e:
            print(f"[{i}/{len(files)}] ✗ 异常: {e}")
    
    print(f"\n总计: 成功处理 {processed_count} 个文件")
    print(f"  - 图像: {processed_images}")
    print(f"  - 音频: {processed_audio}")
    
    # 测试多关键词搜索
    print("\n[4/6] 测试多关键词搜索...")
    
    # 测试关键词列表
    test_keywords = [
        ("熊猫", "image"),
        ("无人机", "audio"),
        ("黄酒", "audio"),
        ("泪桥", "audio"),
        ("王杰", "audio"),
        ("谁明浪子心", "audio"),
        ("伍佰", "audio")
    ]
    
    for keyword, expected_type in test_keywords:
        print(f"\n--- 搜索: '{keyword}' (期望类型: {expected_type}) ---")
        print("="*60)
        
        try:
            # 向量化
            query_embedding = await embedding_engine.embed_text(keyword)
            
            # 搜索
            results = vector_store.search(query_embedding, limit=5)
            
            # 过滤结果
            filtered_results = [r for r in results if r.get('modality') == expected_type]
            
            print(f"找到 {len(results)} 个结果 (过滤后: {len(filtered_results)})")
            
            # 显示结果
            for j, result in enumerate(filtered_results[:3], 1):
                file_name = result.get('file_name', result.get('metadata', {}).get('file_name', 'N/A'))
                file_path = result.get('file_path', result.get('metadata', {}).get('file_path', 'N/A'))
                media_type = result.get('modality', 'N/A')
                score = result.get('similarity', 0)
                
                print(f"\n[{j}] 相似度: {score:.4f}")
                print(f"    文件: {file_name}")
                print(f"    路径: {file_path}")
                print(f"    类型: {media_type}")
            
            if len(filtered_results) == 0:
                print("未找到匹配结果")
        
        except Exception as e:
            print(f"搜索失败: {e}")
    
    # 测试跨模态搜索
    print("\n[5/6] 测试跨模态搜索...")
    cross_modal_keywords = ["音乐", "风景", "动物"]
    
    for keyword in cross_modal_keywords:
        print(f"\n--- 跨模态搜索: '{keyword}' ---")
        print("="*60)
        
        try:
            # 向量化
            query_embedding = await embedding_engine.embed_text(keyword)
            
            # 搜索
            results = vector_store.search(query_embedding, limit=10)
            
            # 统计结果类型
            image_results = [r for r in results if r.get('modality') == 'image']
            audio_results = [r for r in results if r.get('modality') == 'audio']
            
            print(f"总结果: {len(results)}")
            print(f"  - 图像: {len(image_results)}")
            print(f"  - 音频: {len(audio_results)}")
            
            # 显示最佳结果
            if image_results:
                print("\n最佳图像:")
                result = image_results[0]
                file_name = result.get('file_name', 'N/A')
                score = result.get('similarity', 0)
                print(f"  {file_name} (相似度: {score:.4f})")
            
            if audio_results:
                print("\n最佳音频:")
                result = audio_results[0]
                file_name = result.get('file_name', 'N/A')
                score = result.get('similarity', 0)
                print(f"  {file_name} (相似度: {score:.4f})")
        
        except Exception as e:
            print(f"搜索失败: {e}")
    
    # 统计信息
    print("\n[6/6] 向量存储统计...")
    stats = vector_store.get_collection_stats()
    print(f"总向量数: {stats.get('vector_count', 0)}")
    print(f"向量维度: {stats.get('vector_dimension', 'N/A')}")
    
    # 统计模态分布
    print("\n模态分布:")
    try:
        import lancedb
        db = lancedb.connect(vector_store_config['data_dir'])
        table = db.open_table(vector_store_config['collection_name'])
        all_data = table.to_pandas()
        
        modality_counts = all_data['modality'].value_counts()
        for modality, count in modality_counts.items():
            print(f"  - {modality}: {count}")
    except Exception as e:
        print(f"  无法获取模态分布: {e}")
    
    print("\n" + "="*60)
    print("所有测试完成！")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(test_file_monitoring_and_search())
