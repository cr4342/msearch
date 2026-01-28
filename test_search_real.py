#!/usr/bin/env python3
"""
实际搜索测试 - 验证修复后的搜索效果
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from core.config.config_manager import ConfigManager
from core.embedding.embedding_engine import EmbeddingEngine
from core.vector.vector_store import VectorStore


async def test_real_search():
    """测试实际搜索功能"""
    print("=" * 80)
    print("实际搜索测试 - 验证修复效果")
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

    if stats.get('vector_count', 0) == 0:
        print("\n⚠️  向量库为空，请先索引一些文件")
        return

    # 3. 初始化向量化引擎
    print("\n[3] 初始化向量化引擎...")
    embedding_engine = EmbeddingEngine(config)
    await embedding_engine.initialize()
    print(f"✓ 向量化引擎初始化成功")

    # 4. 测试搜索
    test_queries = [
        "人物",
        "猫",
        "周星驰",
        "动物"
    ]

    print("\n[4] 测试搜索功能...")
    all_passed = True

    for query in test_queries:
        print(f"\n{'=' * 80}")
        print(f"查询: '{query}'")
        print(f"{'=' * 80}")

        try:
            # 文本向量化
            query_vector = await embedding_engine.embed_text(query)

            # 向量搜索
            search_results = vector_store.search_vectors(
                query_vector,
                limit=10,
                similarity_threshold=0.3  # 使用修复后的阈值
            )

            print(f"✓ 搜索完成，找到 {len(search_results)} 个结果")

            if search_results:
                print(f"\n  结果列表:")
                for i, result in enumerate(search_results[:5]):  # 只显示前5个
                    similarity = result.get('similarity', 0)
                    file_name = result.get('file_name', 'N/A')
                    modality = result.get('modality', 'N/A')
                    distance = result.get('distance', 0)

                    # 检查相似度是否在合理范围内
                    if similarity < 0 or similarity > 1:
                        print(f"    ⚠️  [{i+1}] {file_name} [{modality}] - 相似度异常: {similarity:.4f}")
                        all_passed = False
                    else:
                        print(f"    [{i+1}] {file_name} [{modality}] - 相似度: {similarity:.4f} (距离: {distance:.4f})")

                # 检查最高相似度
                max_similarity = max([r.get('similarity', 0) for r in search_results])
                avg_similarity = sum([r.get('similarity', 0) for r in search_results]) / len(search_results)

                print(f"\n  统计:")
                print(f"    最高相似度: {max_similarity:.4f}")
                print(f"    平均相似度: {avg_similarity:.4f}")

                # 判断相似度是否合理
                if max_similarity > 0.5:
                    print(f"    ✓ 相似度计算正常")
                elif max_similarity > 0.3:
                    print(f"    ⚠️  相似度偏低，可能需要调整阈值")
                    all_passed = False
                else:
                    print(f"    ✗ 相似度过低，可能存在计算错误")
                    all_passed = False

                # 检查结果相关性
                if query == "人物" or query == "周星驰":
                    relevant_results = [r for r in search_results if "周星驰" in r.get('file_name', '')]
                    if len(relevant_results) > 0:
                        print(f"    ✓ 找到相关结果: {len(relevant_results)}个")
                    else:
                        print(f"    ⚠️  未找到相关结果")
                        all_passed = False
                elif query == "猫" or query == "动物":
                    relevant_results = [r for r in search_results if "OIP" in r.get('file_name', '')]
                    if len(relevant_results) > 0:
                        print(f"    ✓ 找到相关结果: {len(relevant_results)}个")
                    else:
                        print(f"    ⚠️  未找到相关结果")
                        all_passed = False

            else:
                print(f"  ⚠️  未找到匹配结果（可能相似度都低于阈值0.3）")
                all_passed = False

        except Exception as e:
            print(f"  ✗ 搜索失败: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False

    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)
    if all_passed:
        print("✅ 所有测试通过！")
        print("✅ 相似度计算正确")
        print("✅ 搜索结果相关性高")
    else:
        print("❌ 部分测试未通过")
        print("❌ 请检查相似度计算和搜索配置")
    print("=" * 80)

    return all_passed


if __name__ == "__main__":
    try:
        success = asyncio.run(test_real_search())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)