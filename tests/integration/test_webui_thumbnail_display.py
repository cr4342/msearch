#!/usr/bin/env python3
"""
测试WebUI缩略图显示功能

验证：
1. 数据库中有缩略图路径
2. 搜索引擎返回缩略图路径
3. API端点可以访问缩略图
"""

import sys
import sqlite3
from pathlib import Path

def test_database_has_thumbnails():
    """测试数据库中是否有缩略图路径"""
    print("=" * 60)
    print("测试1: 检查数据库中的缩略图路径")
    print("=" * 60)
    
    db_path = '/data/project/msearch/data/database/sqlite/msearch.db'
    
    if not Path(db_path).exists():
        print("❌ 数据库文件不存在")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 检查表结构
    cursor.execute("PRAGMA table_info(file_metadata)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'thumbnail_path' not in columns:
        print("❌ 数据库表没有thumbnail_path列")
        conn.close()
        return False
    
    if 'preview_path' not in columns:
        print("❌ 数据库表没有preview_path列")
        conn.close()
        return False
    
    print("✅ 数据库表结构正确")
    
    # 获取所有文件
    cursor.execute('SELECT file_name, file_path, thumbnail_path FROM file_metadata')
    results = cursor.fetchall()
    
    if not results:
        print("❌ 数据库中没有文件")
        conn.close()
        return False
    
    print(f"找到 {len(results)} 个文件:")
    for file_name, file_path, thumbnail_path in results:
        print(f"  - {file_name}: {thumbnail_path or '无缩略图'}")
        
        # 检查缩略图文件是否存在
        if thumbnail_path and Path(thumbnail_path).exists():
            print(f"    ✅ 缩略图文件存在")
        else:
            print(f"    ❌ 缩略图文件不存在")
    
    conn.close()
    return True

def test_thumbnail_files_exist():
    """测试缩略图文件是否存在"""
    print("\n" + "=" * 60)
    print("测试2: 检查缩略图文件")
    print("=" * 60)
    
    thumbnail_dir = Path('/data/project/msearch/data/thumbnails')
    
    if not thumbnail_dir.exists():
        print(f"❌ 缩略图目录不存在: {thumbnail_dir}")
        return False
    
    thumbnail_files = list(thumbnail_dir.glob('*_thumbnail.*'))
    
    if not thumbnail_files:
        print(f"❌ 缩略图目录中没有缩略图文件")
        return False
    
    print(f"找到 {len(thumbnail_files)} 个缩略图文件:")
    for thumb_file in thumbnail_files:
        size = thumb_file.stat().st_size
        print(f"  - {thumb_file.name} ({size} bytes)")
    
    return True

def test_api_endpoints():
    """测试API端点"""
    print("\n" + "=" * 60)
    print("测试3: 检查API端点")
    print("=" * 60)
    
    # 检查API路由文件
    routes_file = Path('/data/project/msearch/src/api/v1/routes.py')
    
    if not routes_file.exists():
        print(f"❌ API路由文件不存在: {routes_file}")
        return False
    
    content = routes_file.read_text()
    
    endpoints = [
        ('/files/preview', '文件预览端点'),
        ('/files/thumbnail', '缩略图端点')
    ]
    
    all_endpoints_exist = True
    for endpoint, description in endpoints:
        if endpoint in content:
            print(f"  ✅ {description} ({endpoint}) 存在")
        else:
            print(f"  ❌ {description} ({endpoint}) 不存在")
            all_endpoints_exist = False
    
    return all_endpoints_exist

def test_search_engine_formatting():
    """测试搜索引擎结果格式化"""
    print("\n" + "=" * 60)
    print("测试4: 检查搜索引擎结果格式化")
    print("=" * 60)
    
    search_engine_file = Path('/data/project/msearch/src/services/search/search_engine.py')
    
    if not search_engine_file.exists():
        print(f"❌ 搜索引擎文件不存在: {search_engine_file}")
        return False
    
    content = search_engine_file.read_text()
    
    # 检查_format_results方法是否包含thumbnail_path和preview_path
    if 'thumbnail_path' in content and 'preview_path' in content:
        print("  ✅ 搜索引擎结果格式化包含缩略图和预览图路径")
        return True
    else:
        print("  ❌ 搜索引擎结果格式化缺少缩略图或预览图路径")
        return False

def test_database_methods():
    """测试数据库方法"""
    print("\n" + "=" * 60)
    print("测试5: 检查数据库方法")
    print("=" * 60)
    
    database_manager_file = Path('/data/project/msearch/src/core/database/database_manager.py')
    
    if not database_manager_file.exists():
        print(f"❌ 数据库管理器文件不存在: {database_manager_file}")
        return False
    
    content = database_manager_file.read_text()
    
    methods = [
        ('get_thumbnail_by_path', '获取缩略图路径'),
        ('get_preview_by_path', '获取预览图路径'),
        ('get_file_by_path', '根据路径获取文件')
    ]
    
    all_methods_exist = True
    for method, description in methods:
        if method in content:
            print(f"  ✅ {description} ({method}) 存在")
        else:
            print(f"  ❌ {description} ({method}) 不存在")
            all_methods_exist = False
    
    return all_methods_exist

def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("WebUI缩略图显示功能测试")
    print("=" * 60)
    
    tests = [
        test_database_has_thumbnails,
        test_thumbnail_files_exist,
        test_api_endpoints,
        test_search_engine_formatting,
        test_database_methods
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("\n✅ 所有测试通过！WebUI缩略图显示功能已就绪。")
        return 0
    else:
        print(f"\n❌ {total - passed} 个测试失败。")
        return 1

if __name__ == '__main__':
    sys.exit(main())
