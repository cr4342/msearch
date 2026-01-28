#!/usr/bin/env python3
"""
检查数据库和向量库中的数据
"""
import os
import sys
import sqlite3
from pathlib import Path

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import lancedb
    import pyarrow as pa
except ImportError as e:
    print(f"错误: 缺少必要的依赖 - {e}")
    print("请运行: pip install lancedb pyarrow")
    sys.exit(1)


def check_sqlite_database():
    """检查SQLite数据库"""
    print("=" * 60)
    print("检查SQLite数据库")
    print("=" * 60)
    
    db_path = Path('data/database/sqlite/msearch.db')
    
    if not db_path.exists():
        print(f"\n错误: SQLite数据库文件不存在: {db_path}")
        return False
    
    print(f"\n数据库文件: {db_path}")
    print(f"文件大小: {db_path.stat().st_size / 1024:.2f} KB")
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # 获取所有表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"\n找到 {len(tables)} 个表:")
        for table in tables:
            table_name = table[0]
            print(f"\n  表名: {table_name}")
            
            # 获取表结构
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            print(f"  列数: {len(columns)}")
            for col in columns:
                print(f"    - {col[1]} ({col[2]})")
            
            # 获取行数
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            row_count = cursor.fetchone()[0]
            print(f"  行数: {row_count}")
            
            if row_count > 0:
                # 显示前几行数据
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 5;")
                rows = cursor.fetchall()
                print(f"  前5行数据:")
                for i, row in enumerate(rows, 1):
                    print(f"    行{i}: {row}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"\n错误: 检查SQLite数据库失败 - {e}")
        import traceback
        traceback.print_exc()
        return False


def check_lancedb():
    """检查LanceDB向量库"""
    print("\n" + "=" * 60)
    print("检查LanceDB向量库")
    print("=" * 60)
    
    lancedb_path = Path('data/database/lancedb')
    
    if not lancedb_path.exists():
        print(f"\n错误: LanceDB目录不存在: {lancedb_path}")
        return False
    
    print(f"\nLanceDB路径: {lancedb_path}")
    
    try:
        # 连接到LanceDB
        db = lancedb.connect(str(lancedb_path))
        
        # 获取所有表
        tables_response = db.list_tables()
        # 处理不同的返回类型
        if hasattr(tables_response, 'tables'):
            tables = tables_response.tables
        elif hasattr(tables_response, 'names'):
            tables = tables_response.names
        elif isinstance(tables_response, tuple) and len(tables_response) > 1:
            # 如果是元组，提取第二个元素（应该是表名列表）
            tables = tables_response[1] if isinstance(tables_response[1], list) else [tables_response[1]]
        elif isinstance(tables_response, list):
            tables = tables_response
        else:
            tables = [str(tables_response)]
        
        print(f"\n找到 {len(tables)} 个表:")
        for table_name in tables:
            print(f"\n  表名: {table_name}")
            
            # 打开表
            table = db.open_table(table_name)
            
            # 获取表结构
            schema = table.schema
            print(f"  列数: {len(schema)}")
            for field in schema:
                print(f"    - {field.name} ({field.type})")
            
            # 获取行数
            count = table.count_rows()
            print(f"  行数: {count}")
            
            if count > 0:
                # 显示前几行数据
                data = table.to_pandas()
                print(f"  前5行数据:")
                for i in range(min(5, len(data))):
                    row = data.iloc[i]
                    print(f"    行{i}:")
                    for col in data.columns:
                        value = row[col]
                        if isinstance(value, list) and len(value) > 5:
                            value = f"[{value[0]:.4f}, {value[1]:.4f}, ..., {value[-1]:.4f}] (len={len(value)})"
                        print(f"      {col}: {value}")
        
        return True
        
    except Exception as e:
        print(f"\n错误: 检查LanceDB失败 - {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("\n检查数据库和向量库中的数据\n")
    
    sqlite_ok = check_sqlite_database()
    lancedb_ok = check_lancedb()
    
    print("\n" + "=" * 60)
    print("检查结果")
    print("=" * 60)
    print(f"SQLite数据库: {'✓ 正常' if sqlite_ok else '✗ 失败'}")
    print(f"LanceDB向量库: {'✓ 正常' if lancedb_ok else '✗ 失败'}")
    print("=" * 60 + "\n")
    
    return sqlite_ok and lancedb_ok


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
