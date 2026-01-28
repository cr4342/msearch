#!/usr/bin/env python3
"""
清理数据库中的占位符数据
"""
import os
import sys
import sqlite3
from pathlib import Path

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import lancedb
except ImportError as e:
    print(f"错误: 缺少必要的依赖 - {e}")
    print("请运行: pip install lancedb")
    sys.exit(1)


def clean_sqlite_database():
    """清理SQLite数据库"""
    print("=" * 60)
    print("清理SQLite数据库")
    print("=" * 60)
    
    db_path = Path('data/database/sqlite/msearch.db')
    
    if not db_path.exists():
        print(f"\n错误: SQLite数据库文件不存在: {db_path}")
        return False
    
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
            
            # 获取行数
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            row_count = cursor.fetchone()[0]
            print(f"  清空前行数: {row_count}")
            
            if row_count > 0:
                # 删除所有数据
                cursor.execute(f"DELETE FROM {table_name};")
                deleted_count = cursor.rowcount
                print(f"  已删除: {deleted_count} 行")
        
        conn.commit()
        conn.close()
        
        print("\nSQLite数据库清理完成")
        return True
        
    except Exception as e:
        print(f"\n错误: 清理SQLite数据库失败 - {e}")
        import traceback
        traceback.print_exc()
        return False


def clean_lancedb():
    """清理LanceDB向量库"""
    print("\n" + "=" * 60)
    print("清理LanceDB向量库")
    print("=" * 60)
    
    lancedb_path = Path('data/database/lancedb')
    
    if not lancedb_path.exists():
        print(f"\n错误: LanceDB目录不存在: {lancedb_path}")
        return False
    
    try:
        # 连接到LanceDB
        db = lancedb.connect(str(lancedb_path))
        
        # 获取所有表
        tables_response = db.list_tables()
        if hasattr(tables_response, 'tables'):
            tables = tables_response.tables
        elif hasattr(tables_response, 'names'):
            tables = tables_response.names
        elif isinstance(tables_response, tuple) and len(tables_response) > 1:
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
            
            # 获取行数
            count = table.count_rows()
            print(f"  清空前行数: {count}")
            
            if count > 0:
                # 删除所有数据
                table.delete(where="1=1")
                print(f"  已删除: {count} 行")
        
        print("\nLanceDB向量库清理完成")
        return True
        
    except Exception as e:
        print(f"\n错误: 清理LanceDB失败 - {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("\n清理数据库中的占位符数据\n")
    
    sqlite_ok = clean_sqlite_database()
    lancedb_ok = clean_lancedb()
    
    print("\n" + "=" * 60)
    print("清理结果")
    print("=" * 60)
    print(f"SQLite数据库: {'✓ 成功' if sqlite_ok else '✗ 失败'}")
    print(f"LanceDB向量库: {'✓ 成功' if lancedb_ok else '✗ 失败'}")
    print("=" * 60 + "\n")
    
    return sqlite_ok and lancedb_ok


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
