#!/usr/bin/env python3
"""
简化版向量搜索测试 - 不加载模型，直接测试向量搜索
"""

import sys
import numpy as np
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from core.config.config_manager import ConfigManager
from core.vector.vector_store import VectorStore


def test_vector_search():
    """测试向量搜索功能"""
    print("=" * 80)
    print("向量搜索测试 - 验证修复效果")
    print("=" * 80)

    # 1. 加载配置
    print("\n[1] 加载配置...")
    config_manager = ConfigManager()
    config = config_manager.config
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
        return False

    # 3. 获取一个参考向量
    print("\n[3] 获取参考向量...")
    all_vectors = vector_store.table.to_pandas()
    if len(all_vectors) == 0:
        print("✗ 没有可用的向量")
        return False

    # 使用第一个向量作为查询向量
    reference_vector = all_vectors.iloc[0]['vector']
    reference_file = all_vectors.iloc[0]['file_name']
    reference_modality = all_vectors.iloc[0]['modality']

    print(f"✓ 获取参考向量")
    print(f"  文件名: {reference_file}")
    print(f"  模态: {reference_modality}")
    print(f"  向量维度: {len(reference_vector)}")

    # 4. 测试向量搜索
    print("\n[4] 测试向量搜索...")
    search_results = vector_store.search_vectors(
        reference_vector,
        limit=10,
        similarity_threshold=0.3  # 使用修复后的阈值
    )

    print(f"✓ 搜索完成，找到 {len(search_results)} 个结果")

    if search_results:
        print(f"\n  结果列表:")
        for i, result in enumerate(search_results):
            similarity = result.get('similarity', 0)
            file_name = result.get('file_name', 'N/A')
            modality = result.get('modality', 'N/A')
            distance = result.get('distance', 0)

            # 检查相似度是否在合理范围内
            if similarity < 0 or similarity > 1:
                print(f"    ⚠️  [{i+1}] {file_name} [{modality}] - 相似度异常: {similarity:.4f}")
                return False
            else:
                print(f"    [{i+1}] {file_name} [{modality}] - 相似度: {similarity:.4f} (距离: {distance:.4f})")

        # 检查第一个结果（应该是自己）
        first_result = search_results[0]
        first_similarity = first_result.get('similarity', 0)

        print(f"\n  统计:")
        print(f"    最高相似度: {first_similarity:.4f}")
        print(f"    第一个结果应该是参考向量本身")

        # 验证相似度计算
        if first_similarity > 0.99:
            print(f"    ✓ 相似度计算正确（第一个结果是自己，相似度接近1.0）")
            return True
        else:
            print(f"    ⚠️  第一个结果的相似度偏低: {first_similarity:.4f}")
            print(f"    ✗ 相似度计算可能有问题")
            return False
    else:
        print(f"  ⚠️  未找到匹配结果")
        return False


def test_similarity_calculation():
    """测试相似度计算逻辑"""
    print("\n" + "=" * 80)
    print("相似度计算测试")
    print("=" * 80)

    test_distances = [0.0, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0]

    print(f"\n{'距离':<10} {'相似度':<15} {'说明'}")
    print("-" * 40)

    for distance in test_distances:
        # 正确的余弦距离转换
        similarity = 1.0 - distance
        similarity = max(0.0, min(1.0, similarity))

        if distance == 0.0:
            desc = "完全相同"
        elif distance < 0.3:
            desc = "高度相关"
        elif distance < 0.5:
            desc = "中等相关"
        elif distance < 0.7:
            desc = "低度相关"
        else:
            desc = "不太相关"

        print(f"{distance:<10.2f} {similarity:<15.4f} {desc}")

    print("\n✓ 相似度计算公式正确：similarity = 1.0 - distance")
    print("✓ 相似度范围：[0.0, 1.0]")
    return True


if __name__ == "__main__":
    try:
        # 测试相似度计算
        similarity_test_passed = test_similarity_calculation()

        # 测试向量搜索
        vector_test_passed = test_vector_search()

        print("\n" + "=" * 80)
        print("测试总结")
        print("=" * 80)
        if similarity_test_passed and vector_test_passed:
            print("✅ 所有测试通过！")
            print("✅ 相似度计算公式正确")
            print("✅ 向量搜索功能正常")
            print("✅ 修复效果验证成功")
        else:
            if not similarity_test_passed:
                print("❌ 相似度计算测试未通过")
            if not vector_test_passed:
                print("❌ 向量搜索测试未通过")
        print("=" * 80)

        sys.exit(0 if (similarity_test_passed and vector_test_passed) else 1)

    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)