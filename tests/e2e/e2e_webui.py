#!/usr/bin/env python3
"""
测试 WebUI 功能
验证 WebUI 文件和 API 集成
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def test_webui_files():
    """测试 WebUI 文件是否存在"""
    print("=" * 60)
    print("测试 WebUI 文件")
    print("=" * 60)

    webui_dir = project_root / "webui"
    required_files = [
        "index.html",
        "styles.css",
        "app.js",
        "README.md"
    ]

    all_exist = True
    for file_name in required_files:
        file_path = webui_dir / file_name
        exists = file_path.exists()
        status = "✓" if exists else "✗"
        print(f"{status} {file_name}: {'存在' if exists else '不存在'}")
        if not exists:
            all_exist = False

    if all_exist:
        print("\n✓ 所有 WebUI 文件都存在")
    else:
        print("\n✗ 部分 WebUI 文件缺失")
        return False

    return True

def test_api_server_import():
    """测试 API 服务器导入"""
    print("\n" + "=" * 60)
    print("测试 API 服务器导入")
    print("=" * 60)

    try:
        from src.api_server import APIServer
        print("✓ API 服务器导入成功")
        return True
    except Exception as e:
        print(f"✗ API 服务器导入失败: {e}")
        return False

def test_webui_html_structure():
    """测试 WebUI HTML 结构"""
    print("\n" + "=" * 60)
    print("测试 WebUI HTML 结构")
    print("=" * 60)

    html_file = project_root / "webui" / "index.html"
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()

    required_elements = [
        ('<nav class="navbar">', '导航栏'),
        ('<section id="page-search"', '搜索页面'),
        ('<section id="page-tasks"', '任务管理页面'),
        ('<section id="page-files"', '文件管理页面'),
        ('<section id="page-system"', '系统状态页面'),
        ('<script src="app.js">', 'JavaScript 脚本'),
        ('<link rel="stylesheet" href="styles.css">', 'CSS 样式')
    ]

    all_present = True
    for element, description in required_elements:
        present = element in html_content
        status = "✓" if present else "✗"
        print(f"{status} {description}: {'存在' if present else '不存在'}")
        if not present:
            all_present = False

    if all_present:
        print("\n✓ 所有必需的 HTML 元素都存在")
    else:
        print("\n✗ 部分 HTML 元素缺失")
        return False

    return True

def test_app_js_features():
    """测试 JavaScript 功能"""
    print("\n" + "=" * 60)
    print("测试 JavaScript 功能")
    print("=" * 60)

    js_file = project_root / "webui" / "app.js"
    with open(js_file, 'r', encoding='utf-8') as f:
        js_content = f.read()

    required_functions = [
        ('performTextSearch', '文本搜索'),
        ('performImageSearch', '图像搜索'),
        ('performAudioSearch', '音频搜索'),
        ('refreshTasks', '刷新任务'),
        ('refreshFiles', '刷新文件'),
        ('loadSystemInfo', '加载系统信息'),
        ('showToast', '显示通知'),
        ('showLoading', '显示加载遮罩')
    ]

    all_present = True
    for func_name, description in required_functions:
        present = func_name in js_content
        status = "✓" if present else "✗"
        print(f"{status} {description}: {'存在' if present else '不存在'}")
        if not present:
            all_present = False

    if all_present:
        print("\n✓ 所有必需的 JavaScript 功能都存在")
    else:
        print("\n✗ 部分 JavaScript 功能缺失")
        return False

    return True

def test_css_styles():
    """测试 CSS 样式"""
    print("\n" + "=" * 60)
    print("测试 CSS 样式")
    print("=" * 60)

    css_file = project_root / "webui" / "styles.css"
    with open(css_file, 'r', encoding='utf-8') as f:
        css_content = f.read()

    required_classes = [
        ('.navbar', '导航栏'),
        ('.page', '页面'),
        ('.search-container', '搜索容器'),
        ('.result-card', '结果卡片'),
        ('.task-item', '任务项'),
        ('.file-item', '文件项'),
        ('.stat-card', '统计卡片'),
        ('.loading-overlay', '加载遮罩'),
        ('.toast', '通知')
    ]

    all_present = True
    for class_name, description in required_classes:
        present = class_name in css_content
        status = "✓" if present else "✗"
        print(f"{status} {description}: {'存在' if present else '不存在'}")
        if not present:
            all_present = False

    if all_present:
        print("\n✓ 所有必需的 CSS 样式都存在")
    else:
        print("\n✗ 部分 CSS 样式缺失")
        return False

    return True

def test_api_endpoints():
    """测试 API 端点定义"""
    print("\n" + "=" * 60)
    print("测试 API 端点定义")
    print("=" * 60)

    api_file = project_root / "src" / "api_server.py"
    with open(api_file, 'r', encoding='utf-8') as f:
        api_content = f.read()

    required_endpoints = [
        ("@self.app.get('/')", "根路径"),
        ("@self.app.get('/health')", "健康检查"),
        ("@self.app.get('/api/v1/system/info')", "系统信息"),
        ("@self.app.get('/api/v1/models/info')", "模型信息"),
        ("@self.app.post('/api/v1/search')", "检索"),
        ("@self.app.post('/api/v1/search/image')", "图像检索"),
        ("@self.app.get('/api/v1/tasks')", "任务列表"),
        ("@self.app.get('/api/v1/tasks/stats')", "任务统计"),
        ("@self.app.get('/api/v1/files')", "文件列表"),
        ("@self.app.get('/api/v1/database/stats')", "数据库统计")
    ]

    all_present = True
    for endpoint, description in required_endpoints:
        present = endpoint in api_content
        status = "✓" if present else "✗"
        print(f"{status} {description}: {'存在' if present else '不存在'}")
        if not present:
            all_present = False

    if all_present:
        print("\n✓ 所有必需的 API 端点都存在")
    else:
        print("\n✗ 部分 API 端点缺失")
        return False

    return True

def test_static_files_mount():
    """测试静态文件挂载"""
    print("\n" + "=" * 60)
    print("测试静态文件挂载")
    print("=" * 60)

    api_file = project_root / "src" / "api_server.py"
    with open(api_file, 'r', encoding='utf-8') as f:
        api_content = f.read()

    has_static_mount = 'StaticFiles' in api_content and 'webui' in api_content
    status = "✓" if has_static_mount else "✗"
    print(f"{status} 静态文件挂载: {'已配置' if has_static_mount else '未配置'}")

    if has_static_mount:
        print("\n✓ 静态文件挂载已正确配置")
        return True
    else:
        print("\n✗ 静态文件挂载未配置")
        return False

def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("msearch WebUI 功能测试")
    print("=" * 60)

    tests = [
        ("WebUI 文件", test_webui_files),
        ("API 服务器导入", test_api_server_import),
        ("HTML 结构", test_webui_html_structure),
        ("JavaScript 功能", test_app_js_features),
        ("CSS 样式", test_css_styles),
        ("API 端点", test_api_endpoints),
        ("静态文件挂载", test_static_files_mount)
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} 测试失败: {e}")
            results.append((test_name, False))

    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{status}: {test_name}")

    print(f"\n总计: {passed}/{total} 测试通过")

    if passed == total:
        print("\n✓ 所有测试通过！WebUI 已准备就绪。")
        print("\n启动 API 服务器后，访问以下地址使用 WebUI:")
        print("  http://localhost:8000")
        print("  http://localhost:8000/webui/index.html")
        return 0
    else:
        print(f"\n✗ {total - passed} 个测试失败，请检查相关配置。")
        return 1

if __name__ == "__main__":
    sys.exit(main())
