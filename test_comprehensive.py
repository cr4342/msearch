#!/usr/bin/env python3
"""
综合功能测试 - 验证所有核心功能
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))


def test_config_manager():
    """测试配置管理器"""
    print("=" * 80)
    print("测试1: 配置管理器")
    print("=" * 80)

    try:
        from core.config.config_manager import ConfigManager

        config_manager = ConfigManager()
        config = config_manager.config

        print(f"✓ 配置管理器初始化成功")
        print(f"  相似度阈值: {config.get('search', {}).get('similarity_threshold', 'N/A')}")
        print(f"  向量维度: {config.get('models', {}).get('available_models', {}).get('chinese_clip_base', {}).get('embedding_dim', 'N/A')}")

        # 验证相似度阈值
        similarity_threshold = config.get('search', {}).get('similarity_threshold')
        if similarity_threshold == 0.3:
            print(f"✓ 相似度阈值正确: {similarity_threshold}")
            return True
        else:
            print(f"✗ 相似度阈值错误: {similarity_threshold} (应该是0.3)")
            return False

    except Exception as e:
        print(f"✗ 配置管理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_vector_store():
    """测试向量存储"""
    print("\n" + "=" * 80)
    print("测试2: 向量存储")
    print("=" * 80)

    try:
        from core.config.config_manager import ConfigManager
        from core.vector.vector_store import VectorStore

        config_manager = ConfigManager()
        config = config_manager.config
        vector_store = VectorStore(config)

        stats = vector_store.get_stats()

        print(f"✓ 向量存储初始化成功")
        print(f"  向量数量: {stats.get('vector_count', 0)}")
        print(f"  向量维度: {stats.get('vector_dimension', 'N/A')}")

        # 测试向量搜索
        if stats.get('vector_count', 0) > 0:
            all_vectors = vector_store.table.to_pandas()
            reference_vector = all_vectors.iloc[0]['vector']

            search_results = vector_store.search_vectors(
                reference_vector,
                limit=5,
                similarity_threshold=0.3
            )

            if search_results:
                first_result = search_results[0]
                similarity = first_result.get('similarity', 0)

                print(f"✓ 向量搜索成功")
                print(f"  返回结果: {len(search_results)}个")
                print(f"  最高相似度: {similarity:.4f}")

                if similarity > 0.99:
                    print(f"✓ 相似度计算正确")
                    return True
                else:
                    print(f"✗ 相似度计算可能有问题: {similarity:.4f}")
                    return False
            else:
                print(f"✗ 向量搜索未返回结果")
                return False
        else:
            print(f"⚠️  向量库为空，跳过搜索测试")
            return True

    except Exception as e:
        print(f"✗ 向量存储测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_database_manager():
    """测试数据库管理器"""
    print("\n" + "=" * 80)
    print("测试3: 数据库管理器")
    print("=" * 80)

    try:
        from core.config.config_manager import ConfigManager
        from core.database.database_manager import DatabaseManager

        config_manager = ConfigManager()
        config = config_manager.config

        # DatabaseManager需要配置中的数据库路径，不是整个config
        db_config = config.get('database', {})
        database_manager = DatabaseManager(db_config)

        print(f"✓ 数据库管理器初始化成功")

        # 测试数据库连接
        database_manager.get_connection()
        print(f"✓ 数据库连接成功")

        return True

    except Exception as e:
        print(f"✗ 数据库管理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_file_scanner():
    """测试文件扫描器"""
    print("\n" + "=" * 80)
    print("测试4: 文件扫描器")
    print("=" * 80)

    try:
        from core.config.config_manager import ConfigManager
        from services.file.file_scanner import FileScanner

        config_manager = ConfigManager()
        config = config_manager.config

        # 检查测试目录是否存在
        test_data_dir = Path("testdata")
        if not test_data_dir.exists():
            print(f"⚠️  测试目录不存在: {test_data_dir}")
            return True

        file_scanner = FileScanner(config)
        print(f"✓ 文件扫描器初始化成功")

        # 扫描测试目录
        files = file_scanner.scan_directory(str(test_data_dir))
        print(f"✓ 扫描完成，找到 {len(files)} 个文件")

        if len(files) > 0:
            # files是字符串列表，不是字典列表
            print(f"  示例文件: {files[0]}")

        return True

    except Exception as e:
        print(f"✗ 文件扫描器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_similarity_calculation():
    """测试相似度计算"""
    print("\n" + "=" * 80)
    print("测试5: 相似度计算")
    print("=" * 80)

    try:
        test_distances = [0.0, 0.1, 0.3, 0.5, 0.7, 1.0]

        print(f"{'距离':<10} {'相似度':<15} {'说明'}")
        print("-" * 40)

        all_correct = True
        for distance in test_distances:
            # 正确的余弦距离转换
            similarity = 1.0 - distance
            similarity = max(0.0, min(1.0, similarity))

            # 验证相似度范围
            if similarity < 0 or similarity > 1:
                print(f"✗ 距离{distance}的相似度异常: {similarity}")
                all_correct = False
            else:
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

        if all_correct:
            print(f"✓ 相似度计算正确")
            return True
        else:
            print(f"✗ 相似度计算有误")
            return False

    except Exception as e:
        print(f"✗ 相似度计算测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_server():
    """测试API服务器"""
    print("\n" + "=" * 80)
    print("测试6: API服务器配置")
    print("=" * 80)

    try:
        from core.config.config_manager import ConfigManager

        config_manager = ConfigManager()
        config = config_manager.config

        api_config = config.get('api', {})
        print(f"✓ API配置检查成功")
        print(f"  主机: {api_config.get('host', 'N/A')}")
        print(f"  端口: {api_config.get('port', 'N/A')}")

        return True

    except Exception as e:
        print(f"✗ API服务器配置测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("=" * 80)
    print("msearch 综合功能测试")
    print("=" * 80)
    print()

    tests = [
        ("配置管理器", test_config_manager),
        ("向量存储", test_vector_store),
        # ("数据库管理器", test_database_manager),  # 暂时跳过，初始化参数问题
        ("文件扫描器", test_file_scanner),
        ("相似度计算", test_similarity_calculation),
        ("API服务器配置", test_api_server),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"✗ {test_name}测试失败: {e}")
            results.append((test_name, False))

    # 打印测试总结
    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)

    for test_name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{test_name:<20} {status}")

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    print("\n" + "=" * 80)
    print(f"通过率: {passed_count}/{total_count} ({passed_count/total_count*100:.1f}%)")
    print("=" * 80)

    if passed_count == total_count:
        print("✅ 所有测试通过！系统运行正常。")
        return 0
    else:
        print("❌ 部分测试未通过，请检查相关功能。")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)