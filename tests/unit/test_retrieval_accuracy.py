#!/usr/bin/env python3
"""
测试检索准确性
验证语义检索是否能正确找到相关文件
"""

import os
import sys
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
src_root = project_root / "src"
sys.path.insert(0, str(src_root))
sys.path.insert(0, str(project_root))

# 设置离线环境变量
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['HF_DATASETS_OFFLINE'] = '1'
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'

from core.config.config_manager import ConfigManager
from core.vector.vector_store import VectorStore
from core.embedding.embedding_engine import EmbeddingEngine


async def test_retrieval_accuracy():
    """测试检索准确性"""
    print("\n" + "="*70)
    print("测试检索准确性")
    print("="*70)
    
    # 加载配置
    config_manager = ConfigManager()
    config = config_manager.get_all()
    
    # 初始化向量存储
    vector_db_path = config.get('database', {}).get('vector_db_path', 'data/database/lancedb')
    vector_store_config = {
        'data_dir': vector_db_path,
        'collection_name': 'unified_vectors',
        'index_type': 'ivf_pq',
        'num_partitions': 128,
        'vector_dimension': 512
    }
    vector_store = VectorStore(vector_store_config)
    vector_store.initialize()
    print("✓ 向量存储初始化完成")
    
    # 获取所有向量记录
    all_records = vector_store.table.to_pandas()
    print(f"✓ 向量数据库中共有 {len(all_records)} 条记录")
    
    # 显示所有文件
    print("\n" + "-"*70)
    print("数据库中的文件:")
    print("-"*70)
    unique_files = all_records[['file_path', 'file_name', 'modality']].drop_duplicates()
    for idx, row in unique_files.iterrows():
        if row['file_path']:  # 过滤掉空路径
            print(f"  - {row['file_name']} ({row['modality']})")
    
    # 初始化向量化引擎
    embedding_engine = EmbeddingEngine(config)
    await embedding_engine.initialize()
    print("\n✓ 向量化引擎初始化完成")
    
    # 测试用例：查询和期望的文件
    test_cases = [
        {
            'query': '周星驰',
            'expected_files': ['周星驰.jpg'],
            'description': '人物搜索'
        },
        {
            'query': '人物肖像',
            'expected_files': ['周星驰.jpg'],
            'description': '人物肖像搜索'
        },
        {
            'query': '自然风景',
            'expected_files': ['8_3.jpg'],
            'description': '风景搜索'
        },
        {
            'query': '建筑物',
            'expected_files': ['18.jpg'],
            'description': '建筑搜索'
        },
        {
            'query': '小猫',
            'expected_files': ['OIP-C (5).jpg'],
            'description': '动物搜索'
        },
        {
            'query': '可爱动物',
            'expected_files': ['OIP-C (5).jpg'],
            'description': '可爱动物搜索'
        }
    ]
    
    print("\n" + "="*70)
    print("开始准确性测试")
    print("="*70)
    
    passed = 0
    failed = 0
    
    for test_case in test_cases:
        query = test_case['query']
        expected_files = test_case['expected_files']
        description = test_case['description']
        
        print(f"\n测试: {description}")
        print(f"  查询词: '{query}'")
        print(f"  期望文件: {expected_files}")
        
        # 生成查询向量
        query_embedding = await embedding_engine.embed_text(query)
        
        # 执行搜索
        results = vector_store.search(query_embedding, limit=5)
        
        if results:
            # 获取返回的文件名
            returned_files = [Path(r.get('file_path', '')).name for r in results]
            print(f"  返回文件: {returned_files}")
            
            # 检查是否包含期望的文件
            found_expected = any(exp in returned_files for exp in expected_files)
            
            if found_expected:
                # 找到期望的文件，检查排名
                for i, fname in enumerate(returned_files):
                    if fname in expected_files:
                        print(f"  ✓ 期望文件 '{fname}' 排名第 {i+1}")
                        print(f"    相似度: {results[i].get('similarity', 0):.4f}")
                        passed += 1
                        break
            else:
                print(f"  ✗ 未找到期望文件")
                failed += 1
        else:
            print(f"  ✗ 无返回结果")
            failed += 1
    
    # 测试图像搜索
    print("\n" + "-"*70)
    print("测试图像搜索")
    print("-"*70)
    
    # 查找测试图像
    testdata_dir = Path("testdata")
    image_files = list(testdata_dir.glob("*.jpg"))[:2]
    
    for test_image in image_files:
        print(f"\n使用图像搜索: {test_image.name}")
        
        # 生成图像向量
        query_embedding = await embedding_engine.embed_image(str(test_image))
        
        # 执行搜索
        results = vector_store.search(query_embedding, limit=3)
        
        if results:
            returned_files = [Path(r.get('file_path', '')).name for r in results]
            print(f"  返回文件: {returned_files}")
            
            # 检查是否找到自身
            if test_image.name in returned_files:
                idx = returned_files.index(test_image.name)
                similarity = results[idx].get('similarity', 0)
                print(f"  ✓ 自身文件排名第 {idx+1}, 相似度: {similarity:.4f}")
                if similarity >= 0.99:
                    passed += 1
                else:
                    print(f"  ✗ 相似度过低")
                    failed += 1
            else:
                print(f"  ✗ 未找到自身文件")
                failed += 1
        else:
            print(f"  ✗ 无返回结果")
            failed += 1
    
    # 关闭组件
    vector_store.close()
    await embedding_engine.shutdown()
    
    # 打印总结
    print("\n" + "="*70)
    print("测试结果总结")
    print("="*70)
    print(f"总测试数: {passed + failed}")
    print(f"通过: {passed}")
    print(f"失败: {failed}")
    print(f"准确率: {passed/(passed+failed)*100:.1f}%")
    
    if failed == 0:
        print("\n✓ 所有测试通过！检索准确性良好")
    else:
        print(f"\n✗ {failed} 个测试失败")
    
    print("="*70)


if __name__ == '__main__':
    asyncio.run(test_retrieval_accuracy())
