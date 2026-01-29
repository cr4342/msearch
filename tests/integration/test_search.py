#!/usr/bin/env python3
"""
检索测试脚本
验证向量检索功能是否正常工作
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
src_root = project_root / "src"
sys.path.insert(0, str(src_root))
sys.path.insert(0, str(project_root))

import lancedb
from PIL import Image
import numpy as np


def test_vector_search():
    """测试向量检索功能"""
    print("=" * 60)
    print("向量检索测试")
    print("=" * 60)
    
    # 连接到LanceDB
    db_path = "/data/project/msearch/data/database/lancedb"
    print(f"\n连接到LanceDB: {db_path}")
    
    try:
        db = lancedb.connect(db_path)
        table = db.open_table("unified_vectors")
        
        # 获取总记录数
        total_count = table.count_rows()
        print(f"✓ 数据库连接成功")
        print(f"  总记录数: {total_count}")
        
        if total_count == 0:
            print("\n⚠ 数据库中没有记录，无法进行检索测试")
            print("  请先运行: python scripts/index_testdata.py testdata")
            return False
        
        # 查看前几条记录
        print("\n查看前3条记录:")
        df = table.to_pandas()
        if len(df) > 0:
            df = df.head(3)
            for idx, row in df.iterrows():
                print(f"\n  记录 {idx + 1}:")
                print(f"    ID: {row.get('id', 'N/A')}")
                print(f"    文件路径: {row.get('file_path', 'N/A')}")
                print(f"    文件类型: {row.get('file_type', 'N/A')}")
                print(f"    模态: {row.get('modality', 'N/A')}")
        else:
            print("  ⚠ 数据库中没有记录")
        
        # 测试向量检索
        print("\n" + "=" * 60)
        print("测试向量检索")
        print("=" * 60)
        
        # 创建一个测试查询向量（512维，全零向量）
        query_vector = np.zeros(512, dtype=np.float32)
        
        # 执行检索
        print(f"\n执行检索（查询向量维度: {len(query_vector)}）...")
        results = table.search(query_vector).limit(5).to_pandas()
        
        print(f"✓ 检索完成，返回 {len(results)} 条结果")
        
        # 显示检索结果
        print("\n检索结果:")
        for idx, row in results.iterrows():
            score = row.get('_distance', 'N/A')
            file_path = row.get('file_path', 'N/A')
            file_type = row.get('file_type', 'N/A')
            
            print(f"\n  结果 {idx + 1}:")
            print(f"    相似度分数: {score}")
            print(f"    文件路径: {file_path}")
            print(f"    文件类型: {file_type}")
        
        print("\n" + "=" * 60)
        print("✓ 向量检索测试完成")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n✗ 检索测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_database_status():
    """测试数据库状态"""
    print("\n" + "=" * 60)
    print("数据库状态检查")
    print("=" * 60)
    
    db_path = "/data/project/msearch/data/database/lancedb"
    
    try:
        db = lancedb.connect(db_path)
        
        # 列出所有表
        tables = db.table_names()
        print(f"\n✓ 数据库连接成功")
        print(f"  表数量: {len(tables)}")
        print(f"  表名: {', '.join(tables)}")
        
        # 检查每个表的记录数
        for table_name in tables:
            table = db.open_table(table_name)
            count = table.count_rows()
            print(f"  表 '{table_name}': {count} 条记录")
        
        return True
        
    except Exception as e:
        print(f"\n✗ 数据库状态检查失败: {e}")
        return False


def main():
    """主函数"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 15 + "msearch 检索功能测试" + " " * 21 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    # 测试数据库状态
    success = test_database_status()
    
    if not success:
        print("\n✗ 数据库状态检查失败，无法继续")
        return False
    
    # 测试向量检索
    success = test_vector_search()
    
    if success:
        print("\n✓ 所有测试通过")
        return True
    else:
        print("\n✗ 检索测试失败")
        return False


if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)