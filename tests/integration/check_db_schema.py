#!/usr/bin/env python3
"""
检查数据库结构
"""

import sqlite3
from pathlib import Path

def check_database_schema():
    """检查数据库结构"""
    db_path = Path("./data/msearch.db")
    
    if not db_path.exists():
        print("❌ 数据库文件不存在")
        return
    
    print(f"📍 检查数据库: {db_path.absolute()}")
    print()
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # 获取所有表
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = cursor.fetchall()
            
            print("📊 数据库表:")
            for table in tables:
                print(f"  - {table[0]}")
            print()
            
            # 检查每个表的结构
            for table_name in [t[0] for t in tables]:
                print(f"🔍 {table_name} 表结构:")
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                
                for col in columns:
                    cid, name, col_type, notnull, default, pk = col
                    pk_str = " (PK)" if pk else ""
                    default_str = f" DEFAULT {default}" if default else ""
                    notnull_str = " NOT NULL" if notnull else ""
                    print(f"  {name}: {col_type}{notnull_str}{default_str}{pk_str}")
                
                print()
            
    except Exception as e:
        print(f"❌ 检查数据库结构失败: {e}")

if __name__ == "__main__":
    check_database_schema()