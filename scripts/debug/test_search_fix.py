#!/usr/bin/env python3
"""
测试搜索修复效果
验证相似度计算是否正确
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from core.config.config_manager import ConfigManager
from core.embedding.embedding_engine import EmbeddingEngine
from core.vector.vector_store import VectorStore
from services.search.search_engine import SearchEngine


async def test_similarity_calculation():
    """测试相似度计算是否正确"""
    print("=" * 60)
    print("测试相似度计算修复效果")
    print("=" * 60)

    # 1. 加载配置
    print("\n[1] 加载配置...")
    config_manager = ConfigManager()
    config = config_manager.get_config()
    print(f"✓ 配置加载成功")
    print(f"  相似度阈值: {config.get('search', {}).get('similarity_threshold', 'N/A')}")

    # 2. 初始化向量存储
    print("\n[2] 初始化向量存储...")
    vector_store = VectorStore(config)
    stats = vector_store.get_stats()
    print(f"✓ 向量存储初始化成功")
    print(f"  向量数量: {stats.get('vector_count', 0)}")
    print(f"  向量维度: {stats.get('vector_dimension', 'N/A')}")

    if stats.get('vector_count', 0) == 0:
        print("\n⚠️  向量库为空，请先索引一些文件")
        return

    # 3. 初始化向量化引擎
    print("\n[3] 初始化向量化引擎...")
    embedding_engine = EmbeddingEngine(config)
    await embedding_engine.initialize()
    print(f"✓ 向量化引擎初始化成功")

    # 4. 创建搜索引擎
    print("\n[4] 创建搜索引擎...")
    search_engine = SearchEngine(embedding_engine, vector_store)
    print(f"✓ 搜索引擎创建成功")

    # 5. 测试搜索
    test_queries = [
        "猫",
        "老虎",
        "动物",
        "风景",
        "人物"
    ]

    print("\n[5] 测试搜索功能...")
    for query in test_queries:
        print(f"\n{'=' * 60}")
        print(f"查询: '{query}'")
        print(f"{'=' * 60}")

        result = await search_engine.search(
            query=query,
            k=10,
            modalities=['image', 'video']
        )

        if result.get('status') == 'success':
            results = result.get('results', [])
            print(f"✓ 搜索成功，找到 {len(results)} 个结果")
            print(f"  搜索耗时: {result.get('search_time', 0):.3f}秒")

            if results:
                print(f"\n  结果列表:")
                for i, item in enumerate(results[:5]):  # 只显示前5个结果
                    score = item.get('score', 0)
                    similarity = item.get('similarity', 0)
                    file_name = item.get('file_name', 'N/A')
                    modality = item.get('modality', 'N/A')

                    # 检查相似度是否在合理范围内
                    if similarity < 0 or similarity > 1:
                        print(f"    ⚠️  [{i+1}] {file_name} [{modality}] - 相似度异常: {similarity:.4f}")
                    else:
                        print(f"    [{i+1}] {file_name} [{modality}] - 相似度: {similarity:.4f}")

                # 检查最高相似度
                max_similarity = max([r.get('similarity', 0) for r in results])
                avg_similarity = sum([r.get('similarity', 0) for r in results]) / len(results)

                print(f"\n  统计:")
                print(f"    最高相似度: {max_similarity:.4f}")
                print(f"    平均相似度: {avg_similarity:.4f}")

                # 判断相似度是否合理
                if max_similarity > 0.5:
                    print(f"    ✓ 相似度计算正常")
                elif max_similarity > 0.3:
                    print(f"    ⚠️  相似度偏低，可能需要调整阈值")
                else:
                    print(f"    ✗ 相似度过低，可能存在计算错误")
            else:
                print(f"  ⚠️  未找到匹配结果")
        else:
            print(f"✗ 搜索失败: {result.get('error', 'Unknown error')}")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


async def test_distance_to_similarity():
    """测试距离到相似度的转换"""
    print("\n" + "=" * 60)
    print("测试距离到相似度转换")
    print("=" * 60)

    # 测试不同的距离值
    test_distances = [0.0, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0]

    print("\n距离 -> 相似度转换测试:")
    print(f"{'距离':<10} {'旧公式':<15} {'新公式':<15} {'差异':<10}")
    print("-" * 50)

    for distance in test_distances:
        # 旧公式：1.0 / (1.0 + distance)
        old_similarity = 1.0 / (1.0 + distance)

        # 新公式：1.0 - distance（余弦距离）
        new_similarity = 1.0 - distance
        new_similarity = max(0.0, min(1.0, new_similarity))

        diff = new_similarity - old_similarity

        print(f"{distance:<10.2f} {old_similarity:<15.4f} {new_similarity:<15.4f} {diff:<10.4f}")

    print("\n结论:")
    print("  - 新公式（1.0 - distance）适用于余弦距离")
    print("  - 新公式能正确反映余弦相似度")
    print("  - 新公式的相似度值更合理，更接近实际相关性")


if __name__ == "__main__":
    try:
        # 运行距离转换测试
        asyncio.run(test_distance_to_similarity())

        # 运行搜索测试
        asyncio.run(test_similarity_calculation())

    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
    except Exception as e:
        print(f"\n\n测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
