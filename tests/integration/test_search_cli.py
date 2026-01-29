#!/usr/bin/env python3
"""
检索功能测试脚本
使用CLI方式测试向量检索功能
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
src_root = project_root / "src"
sys.path.insert(0, str(src_root))
sys.path.insert(0, str(project_root))

import lancedb
import numpy as np
from PIL import Image
from core.embedding.embedding_engine import EmbeddingEngine
from core.config.config_manager import ConfigManager
import asyncio


async def test_image_search():
    """测试图像检索功能"""
    print("=" * 60)
    print("图像检索测试")
    print("=" * 60)
    
    # 加载配置
    config_manager = ConfigManager()
    config = config_manager.get_all()
    
    # 初始化向量化引擎
    embedding_engine = EmbeddingEngine(config)
    await embedding_engine.initialize()
    print("✓ 向量化引擎初始化完成")
    
    # 连接到LanceDB
    db_path = "/data/project/msearch/data/database/lancedb"
    db = lancedb.connect(db_path)
    table = db.open_table("unified_vectors")
    
    print(f"✓ 数据库连接成功，共有 {table.count_rows()} 条记录")
    
    # 测试1: 使用图像文件进行检索
    test_image = "testdata/周星驰.jpg"
    if Path(test_image).exists():
        print(f"\n测试1: 使用图像文件 '{test_image}' 进行检索")
        
        # 生成查询向量
        query_vector = await embedding_engine.embed_image(test_image)
        print(f"✓ 查询向量生成完成，维度: {len(query_vector)}")
        
        # 执行检索
        results = table.search(query_vector).limit(3).to_pandas()
        
        print(f"✓ 检索完成，返回 {len(results)} 条结果")
        print("\n检索结果:")
        for idx, row in results.iterrows():
            file_path = row.get('file_path', 'N/A')
            file_type = row.get('file_type', 'N/A')
            distance = row.get('_distance', 'N/A')
            print(f"  {idx+1}. {file_path} ({file_type}) - 距离: {distance}")
    else:
        print(f"\n⚠ 测试图像不存在: {test_image}")
    
    # 测试2: 使用文本进行检索
    print("\n" + "=" * 60)
    print("测试2: 使用文本查询进行检索")
    print("=" * 60)
    
    # 注意：当前模型不支持文本查询，这里使用随机向量演示
    print("\n注意：当前使用的Chinese-CLIP模型不支持文本查询")
    print("使用随机向量进行演示检索...")
    
    random_vector = np.random.randn(512).astype(np.float32)
    results = table.search(random_vector).limit(3).to_pandas()
    
    print(f"✓ 检索完成，返回 {len(results)} 条结果")
    print("\n检索结果:")
    for idx, row in results.iterrows():
        file_path = row.get('file_path', 'N/A')
        file_type = row.get('file_type', 'N/A')
        distance = row.get('_distance', 'N/A')
        print(f"  {idx+1}. {file_path} ({file_type}) - 距离: {distance}")
    
    # 关闭引擎
    embedding_engine.shutdown()
    
    print("\n" + "=" * 60)
    print("✓ 图像检索测试完成")
    print("=" * 60)


def test_database_query():
    """测试数据库查询功能"""
    print("\n" + "=" * 60)
    print("数据库查询测试")
    print("=" * 60)
    
    db_path = "/data/project/msearch/data/database/lancedb"
    db = lancedb.connect(db_path)
    table = db.open_table("unified_vectors")
    
    # 查询所有记录
    df = table.to_pandas()
    
    print(f"\n✓ 数据库共有 {len(df)} 条记录")
    
    # 按文件类型统计
    if 'file_type' in df.columns:
        type_counts = df['file_type'].value_counts()
        print("\n按文件类型统计:")
        for file_type, count in type_counts.items():
            print(f"  {file_type}: {count} 条")
    
    # 显示所有文件路径
    if 'file_path' in df.columns:
        print("\n已索引的文件:")
        for idx, row in df.iterrows():
            file_path = row.get('file_path', 'N/A')
            if file_path and file_path != 'N/A':
                print(f"  {idx+1}. {file_path}")
    
    print("\n" + "=" * 60)
    print("✓ 数据库查询测试完成")
    print("=" * 60)


async def main():
    """主函数"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 15 + "msearch 检索功能测试" + " " * 21 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    # 测试数据库查询
    test_database_query()
    
    # 测试图像检索
    await test_image_search()
    
    print("\n" + "╔" + "=" * 58 + "╗")
    print("║" + " " * 18 + "所有测试完成" + " " * 24 + "║")
    print("╚" + "=" * 58 + "╝")
    print()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
