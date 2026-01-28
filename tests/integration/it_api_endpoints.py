#!/usr/bin/env python3
"""
测试 API 端点是否正常工作
"""

import sys
import time
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.api_server import APIServer

def test_api_endpoints():
    """测试 API 端点"""
    print("=" * 60)
    print("测试 API 端点")
    print("=" * 60)

    # 初始化服务器
    print("\n1. 初始化 API 服务器...")
    try:
        server = APIServer()
        print("   ✓ API 服务器初始化成功")
    except Exception as e:
        print(f"   ✗ API 服务器初始化失败: {e}")
        return False

    # 模拟 API 调用
    print("\n2. 测试任务统计端点...")
    try:
        task_manager = server.components['task_manager']
        stats = task_manager.get_task_stats()
        
        # 模拟 API 响应
        api_response = {
            'success': True,
            'stats': stats
        }
        
        print(f"   API 响应: {api_response}")
        print(f"   ✓ 待处理: {stats['pending_count']}")
        print(f"   ✓ 运行中: {stats['running_count']}")
        print(f"   ✓ 已完成: {stats['completed_count']}")
        print(f"   ✓ 失败: {stats['failed_count']}")
        
        if stats['pending_count'] > 0:
            print("   ✓ 任务统计正常")
        else:
            print("   ⚠ 暂无待处理任务")
    except Exception as e:
        print(f"   ✗ 任务统计失败: {e}")
        return False

    print("\n3. 测试任务列表端点...")
    try:
        pending_tasks = task_manager.get_pending_tasks(5)
        print(f"   返回任务数: {len(pending_tasks)}")
        
        if pending_tasks:
            print(f"   第一个任务: {pending_tasks[0]}")
            print("   ✓ 任务列表正常")
        else:
            print("   ⚠ 暂无任务")
    except Exception as e:
        print(f"   ✗ 任务列表失败: {e}")
        return False

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
    print("\n如果所有测试通过，API 端点应该能正常工作。")
    print("请确保：")
    print("  1. API 服务器正在运行（python3 src/api_server.py）")
    print("  2. WebUI 能够访问 http://localhost:8000")
    print("  3. 浏览器控制台没有错误信息")

    return True

if __name__ == "__main__":
    success = test_api_endpoints()
    sys.exit(0 if success else 1)