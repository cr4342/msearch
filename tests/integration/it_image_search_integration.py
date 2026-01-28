#!/usr/bin/env python3
"""
测试图片处理和检索流程
使用真实模型和testdata目录下的数据
"""

import os
import sys
import json
import time
from pathlib import Path
import shutil

# 设置matplotlib使用非交互式后端，避免ft2font错误
os.environ['MPLBACKEND'] = 'Agg'

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.config.config_manager import ConfigManager
from src.core.database.database_manager import DatabaseManager
from src.core.vector.vector_store import VectorStore
from src.core.embedding.embedding_engine import EmbeddingEngine
from src.services.media.media_processor import MediaProcessor
from src.data.extractors.noise_filter import NoiseFilterManager

def setup_test_environment():
    """设置测试环境"""
    # 创建临时目录
    test_dir = Path("test_temp")
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir()
    
    # 创建子目录
    (test_dir / "database").mkdir()
    (test_dir / "lancedb").mkdir()
    
    return test_dir

def get_test_images(testdata_dir, max_images=5):
    """获取测试图像"""
    image_extensions = {'.jpg', '.jpeg', '.png', '.webp'}
    images = []
    
    for file_path in testdata_dir.iterdir():
        if file_path.suffix.lower() in image_extensions and file_path.is_file():
            images.append(file_path)
            if len(images) >= max_images:
                break
    
    return images

def process_and_index_images(images, db_manager, vector_store, embedding_engine, media_processor, noise_filter):
    """处理和索引图像"""
    indexed_count = 0
    
    for image_path in images:
        print(f"\n处理图像: {image_path.name}")
        
        # 获取文件信息
        file_size = image_path.stat().st_size
        file_ext = image_path.suffix.lower().lstrip(".")
        
        # 噪音过滤
        media_info = {
            "width": 800,  # 假设值，实际应该从图像读取
            "height": 600,
            "file_size": file_size,
            "file_ext": file_ext
        }
        
        should_keep, reason = noise_filter.filter("image", media_info)
        if not should_keep:
            print(f"  跳过: {reason}")
            continue
        
        # 图像预处理
        try:
            processed = media_processor.process_image(str(image_path))
            if not processed:
                print(f"  预处理失败")
                continue
        except Exception as e:
            print(f"  预处理异常: {e}")
            continue
        
        # 图像向量化
        try:
            print(f"  正在向量化...")
            image_vector = embedding_engine.embed_image(str(image_path))
            if not image_vector:
                print(f"  向量化失败")
                continue
            print(f"  向量维度: {len(image_vector)}")
        except Exception as e:
            print(f"  向量化异常: {e}")
            import traceback
            traceback.print_exc()
            continue
        
        # 存储到数据库
        file_uuid = f"img_{file_size}_{indexed_count}"
        metadata = {
            "id": file_uuid,
            "file_path": str(image_path),
            "file_name": image_path.name,
            "file_size": file_size,
            "file_type": "image",
            "file_hash": f"hash_{file_size}"
        }
        
        try:
            db_manager.insert_file_metadata(metadata)
        except Exception as e:
            print(f"  数据库插入失败: {e}")
            continue
        
        # 存储到向量数据库
        vector_id = f"{file_uuid}_vector"
        vector_data = {
            "id": vector_id,
            "vector": image_vector,
            "modality": "image",
            "file_id": file_uuid,
            "segment_id": "",
            "start_time": 0.0,
            "end_time": 0.0,
            "is_full_video": False,
            "metadata": json.dumps(metadata),
            "created_at": time.time()
        }
        
        try:
            vector_store.add_vector(vector_data)
            print(f"  索引成功: {file_uuid}")
            indexed_count += 1
        except Exception as e:
            print(f"  向量存储失败: {e}")
            continue
    
    return indexed_count

def search_images(query_text, vector_store, embedding_engine, limit=5):
    """搜索图像"""
    print(f"\n搜索查询: {query_text}")
    
    # 向量化查询文本
    try:
        query_vector = embedding_engine.embed_text(query_text)
        print(f"查询向量维度: {len(query_vector)}")
    except Exception as e:
        print(f"查询向量化失败: {e}")
        return []
    
    # 搜索向量
    try:
        results = vector_store.search_vectors(
            query_vector=query_vector,
            limit=limit,
            filter={'modality': 'image'}
        )
        return results
    except Exception as e:
        print(f"搜索失败: {e}")
        return []

def main():
    """主函数"""
    print("=" * 60)
    print("图片处理和检索流程测试")
    print("=" * 60)
    
    # 设置测试环境
    print("\n1. 设置测试环境...")
    test_dir = setup_test_environment()
    print(f"测试目录: {test_dir}")
    
    # 初始化配置管理器
    print("\n2. 初始化配置管理器...")
    config_manager = ConfigManager()
    print(f"配置加载成功")    
    # 初始化数据库
    print("\n3. 初始化数据库...")
    db_manager = DatabaseManager(str(test_dir / "database" / "msearch.db"))
    print("数据库初始化成功")
    
    # 初始化向量存储
    print("\n4. 初始化向量存储...")
    vector_store = VectorStore({
        "data_dir": str(test_dir / "lancedb"),
        "collection_name": "unified_vectors",
        "index_type": "ivf_pq",
        "num_partitions": 128,
        "vector_dimension": 512
    })
    print("向量存储初始化成功")
    
    # 初始化向量化引擎
    print("\n5. 初始化向量化引擎...")
    embedding_engine = EmbeddingEngine(config=config_manager.config)
    print("向量化引擎初始化成功")
    
    # 初始化媒体处理器
    print("\n6. 初始化媒体处理器...")
    media_processor = MediaProcessor(config=config_manager.config)
    print("媒体处理器初始化成功")
    
    # 初始化噪音过滤器
    print("\n7. 初始化噪音过滤器...")
    noise_filter = NoiseFilterManager(config_manager.config.get("noise_filter", {}))
    print("噪音过滤器初始化成功")
    
    # 获取测试图像
    print("\n8. 获取测试图像...")
    testdata_dir = Path("testdata")
    if not testdata_dir.exists():
        print(f"错误: testdata目录不存在")
        return
    
    images = get_test_images(testdata_dir, max_images=5)
    print(f"找到 {len(images)} 个测试图像")
    for img in images:
        print(f"  - {img.name} ({img.stat().st_size} bytes)")
    
    if not images:
        print("错误: 没有找到测试图像")
        return
    
    # 处理和索引图像
    print("\n9. 处理和索引图像...")
    indexed_count = process_and_index_images(
        images, db_manager, vector_store, embedding_engine, media_processor, noise_filter
    )
    print(f"\n成功索引 {indexed_count} 个图像")
    
    # 搜索测试
    print("\n10. 搜索测试...")
    queries = ["风景", "人物", "建筑", "自然"]
    
    for query in queries:
        results = search_images(query, vector_store, embedding_engine, limit=3)
        print(f"\n查询: {query}")
        if results:
            for i, result in enumerate(results[:3], 1):
                # 计算相似度（距离越小，相似度越高）
                distance = result.get('_distance', 1.0)
                score = 1.0 - distance  # 将距离转换为相似度
                file_id = result.get('file_id', 'N/A')
                print(f"  {i}. 文件ID: {file_id}, 相似度: {score:.4f}")
        else:
            print("  未找到结果")
    
    # 清理
    print("\n11. 清理测试环境...")
    db_manager.close()
    vector_store.close()
    shutil.rmtree(test_dir)
    print("清理完成")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)

if __name__ == "__main__":
    main()