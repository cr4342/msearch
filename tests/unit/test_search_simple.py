#!/usr/bin/env python3
"""
最简化诊断脚本：直接测试检索
"""

import sys
sys.path.insert(0, 'src')

from src.core.config.config_manager import ConfigManager
from src.core.vector.vector_store import VectorStore

def test_search():
    """测试检索"""
    print("=" * 80)
    print("检索测试")
    print("=" * 80)

    # 初始化
    print("\n初始化...")
    config_manager = ConfigManager()
    vector_store = VectorStore(config_manager.config)
    print("✓ 初始化完成\n")

    # 测试检索
    query_texts = ["老虎", "男人", "女人", "猫", "狗"]
    all_results = {}

    for query_text in query_texts:
        try:
            print(f"\n查询: '{query_text}'")
            print("-" * 80)

            # 执行检索
            results = vector_store.search_vectors(
                query_text=query_text,
                limit=10,
                modality='image'
            )

            print(f"返回结果数: {len(results)}")

            if len(results) == 0:
                print("✗ 没有返回结果")
                continue

            # 显示结果
            print("\n检索结果:")
            for i, result in enumerate(results[:10], 1):
                file_path = result.get('file_path', 'N/A')
                similarity = result.get('_score', 0.0)
                distance = result.get('_distance', 0.0)
                print(f"  {i}. {file_path}")
                print(f"     相似度: {similarity:.3f}, 距离: {distance:.3f}")

            # 保存结果路径
            all_results[query_text] = [r.get('file_path') for r in results]

        except Exception as e:
            print(f"✗ 检索失败: {e}")
            import traceback
            traceback.print_exc()

    # 分析结果重叠
    print("\n" + "=" * 80)
    print("结果重叠分析")
    print("=" * 80)

    if len(all_results) >= 2:
        queries = list(all_results.keys())

        for i in range(len(queries)):
            for j in range(i+1, len(queries)):
                query1, query2 = queries[i], queries[j]
                results1 = all_results[query1]
                results2 = all_results[query2]

                overlap = set(results1) & set(results2)
                overlap_rate = len(overlap) / len(results1) if results1 else 0

                print(f"\n'{query1}' vs '{query2}':")
                print(f"  重叠: {len(overlap)}/{len(results1)} ({overlap_rate:.1%})")

                if overlap_rate > 0.8:
                    print(f"  ⚠️ 警告: 重叠率过高!")
                    print(f"  ⚠️ 可能原因:")
                    print(f"     1. 向量存储中文件数量过少")
                    print(f"     2. 文件向量计算有问题（所有文件的向量相同或非常相似）")
                    print(f"     3. 查询向量计算有问题（所有查询的向量相同或非常相似）")

    # 获取向量统计
    print("\n" + "=" * 80)
    print("向量统计")
    print("=" * 80)

    try:
        stats = vector_store.get_stats()
        print(f"总向量数: {stats.get('total_vectors', 'N/A')}")

        modality_stats = vector_store.get_vector_count_by_modality()
        print(f"按模态统计:")
        for modality, count in modality_stats.items():
            print(f"  {modality}: {count}")

    except Exception as e:
        print(f"✗ 获取统计失败: {e}")

    print("\n" + "=" * 80)

if __name__ == '__main__':
    test_search()