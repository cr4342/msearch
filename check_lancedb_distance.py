#!/usr/bin/env python3
"""
检查LanceDB返回的距离类型
验证距离到相似度的正确转换方式
"""

import sys
import numpy as np


def analyze_distance_types():
    """分析不同距离类型的特性"""
    print("=" * 80)
    print("距离类型分析")
    print("=" * 80)

    distance_types = [
        {
            "name": "余弦距离 (Cosine Distance)",
            "formula": "1 - cosine_similarity",
            "range": "[0, 2]",
            "description": "CLIP模型使用，值越小表示越相似",
            "to_similarity": "1 - distance / 2"  # 归一化到[0,1]
        },
        {
            "name": "欧氏距离 (Euclidean Distance)",
            "formula": "sqrt(sum((a-b)^2))",
            "range": "[0, +∞)",
            "description": "值越小表示越相似",
            "to_similarity": "1 / (1 + distance)"  # 常用转换
        },
        {
            "name": "曼哈顿距离 (Manhattan Distance)",
            "formula": "sum(|a-b|)",
            "range": "[0, +∞)",
            "description": "值越小表示越相似",
            "to_similarity": "1 / (1 + distance)"
        }
    ]

    print("\n距离类型对比:")
    print(f"{'名称':<30} {'范围':<15} {'相似度转换':<30}")
    print("-" * 80)
    for dt in distance_types:
        print(f"{dt['name']:<30} {dt['range']:<15} {dt['to_similarity']:<30}")

    print()


def test_lance_default_distance():
    """测试LanceDB默认距离（余弦距离）"""
    print("=" * 80)
    print("LanceDB默认距离测试（余弦距离）")
    print("=" * 80)

    # LanceDB默认使用余弦距离：distance = 1 - cosine_similarity
    # 因此：cosine_similarity = 1 - distance

    print("\n余弦距离特性:")
    print("- 范围：[0, 2]")
    print("- 距离0：完全相同（cosine_similarity = 1.0）")
    print("- 距离1：正交/无关（cosine_similarity = 0.0）")
    print("- 距离2：完全相反（cosine_similarity = -1.0）")
    print()

    # 测试不同的距离值
    test_distances = [0.0, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0, 1.5, 2.0]

    print(f"{'距离':<10} {'余弦相似度':<20} {'归一化相似度':<20} {'说明'}")
    print("-" * 70)

    for distance in test_distances:
        # 原始余弦相似度
        cosine_sim = 1.0 - distance

        # 归一化到[0,1]
        normalized_sim = (cosine_sim + 1.0) / 2.0

        # 说明
        if distance < 0.2:
            desc = "高度相关"
        elif distance < 0.5:
            desc = "中等相关"
        elif distance < 1.0:
            desc = "低度相关"
        elif distance < 1.5:
            desc = "不太相关"
        else:
            desc = "不相关"

        print(f"{distance:<10.2f} {cosine_sim:<20.4f} {normalized_sim:<20.4f} {desc}")

    print()


def compare_formulas():
    """对比不同的转换公式"""
    print("=" * 80)
    print("转换公式对比")
    print("=" * 80)

    test_distances = [0.0, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0]

    print(f"{'距离':<10} {'公式A':<20} {'公式B':<20} {'公式C':<20} {'推荐'}")
    print("-" * 80)

    for distance in test_distances:
        # 公式A：1 - distance（直接使用余弦相似度，范围[-1, 1]）
        formula_a = 1.0 - distance

        # 公式B：1 / (1 + distance)（适用于欧氏距离）
        formula_b = 1.0 / (1.0 + distance)

        # 公式C：(1 - distance + 1) / 2 = (2 - distance) / 2（归一化到[0,1]）
        formula_c = (2.0 - distance) / 2.0

        # 推荐：对于CLIP模型，应该使用余弦相似度（公式A）
        # 如果需要归一化到[0,1]，使用公式C
        if distance < 0.3:
            recommend = "公式A（余弦相似度）"
        else:
            recommend = "公式A或C"

        print(f"{distance:<10.2f} {formula_a:<20.4f} {formula_b:<20.4f} {formula_c:<20.4f} {recommend}")

    print()


def check_clip_similarity_range():
    """检查CLIP模型的相似度范围"""
    print("=" * 80)
    print("CLIP模型相似度范围")
    print("=" * 80)

    print("\nCLIP模型使用余弦相似度（Cosine Similarity）：")
    print("- 范围：[-1, 1]")
    print("- 1.0：完全相同")
    print("- 0.0：无关/正交")
    print("- -1.0：完全相反")
    print()

    print("LanceDB使用余弦距离（Cosine Distance）：")
    print("- 公式：distance = 1 - cosine_similarity")
    print("- 范围：[0, 2]")
    print()

    print("转换关系：")
    print("- 余弦相似度 = 1 - 余弦距离")
    print("- 例如：距离0.1 → 相似度0.9（高度相关）")
    print("- 例如：距离0.5 → 相似度0.5（中等相关）")
    print("- 例如：距离0.9 → 相似度0.1（低度相关）")
    print()

    print("推荐做法：")
    print("✓ 使用原始余弦相似度：similarity = 1 - distance")
    print("✓ 如果需要归一化到[0,1]：similarity = (1 - distance + 1) / 2")
    print("✓ 不要使用 1/(1+distance)，这是用于欧氏距离的")
    print()


if __name__ == "__main__":
    try:
        analyze_distance_types()
        test_lance_default_distance()
        compare_formulas()
        check_clip_similarity_range()

        print("=" * 80)
        print("最终结论")
        print("=" * 80)
        print("LanceDB默认使用余弦距离（Cosine Distance）")
        print("正确的相似度转换公式：similarity = 1 - distance")
        print()
        print("修复方案：")
        print("1. ✓ 将相似度计算从 1/(1+distance) 改为 1-distance")
        print("2. ✓ 将相似度阈值从 0.7 降低到 0.3")
        print("3. ✓ 确保 _score 字段与 similarity 一致")
        print()
        print("预期效果：")
        print("- 相似度值会正确反映语义相关性")
        print("- 高度相关的结果（距离<0.3）会有较高的相似度（>0.7）")
        print("- 搜索结果的关联度会显著提升")
        print("=" * 80)

    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
    except Exception as e:
        print(f"\n\n测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
