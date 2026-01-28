#!/usr/bin/env python3
"""
测试任务控制API接口
"""

import sys
import time
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_task_control_api():
    """测试任务控制API接口"""
    print("=" * 60)
    print("测试任务控制API接口")
    print("=" * 60)

    # 导入必要的模块
    try:
        import requests
        print("✓ requests模块已安装")
    except ImportError:
        print("✗ 需要安装requests模块: pip install requests")
        return False

    # API基础URL
    base_url = "http://localhost:8000"

    # 测试1: 获取任务统计
    print("\n1. 测试获取任务统计...")
    try:
        response = requests.get(f"{base_url}/api/v1/tasks/stats")
        if response.status_code == 200:
            stats = response.json()
            print(f"   ✓ 任务统计获取成功")
            print(f"   - 总任务数: {stats['task_stats']['overall']['total']}")
            print(f"   - 待处理: {stats['task_stats']['overall']['pending']}")
            print(f"   - 运行中: {stats['task_stats']['overall']['running']}")
            print(f"   - 已完成: {stats['task_stats']['overall']['completed']}")
        else:
            print(f"   ✗ 获取任务统计失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ 请求失败: {e}")
        return False

    # 测试2: 获取所有任务
    print("\n2. 测试获取所有任务...")
    try:
        response = requests.get(f"{base_url}/api/v1/tasks")
        if response.status_code == 200:
            tasks = response.json()
            print(f"   ✓ 获取任务列表成功")
            print(f"   - 任务总数: {tasks['total']}")
        else:
            print(f"   ✗ 获取任务列表失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ 请求失败: {e}")
        return False

    # 测试3: 取消所有任务
    print("\n3. 测试取消所有任务...")
    try:
        response = requests.post(
            f"{base_url}/api/v1/tasks/cancel-all",
            data={"cancel_running": False}
        )
        if response.status_code == 200:
            result = response.json()
            print(f"   ✓ 取消所有任务成功")
            print(f"   - 已取消: {result['result']['cancelled']}")
            print(f"   - 失败: {result['result']['failed']}")
        else:
            print(f"   ✗ 取消所有任务失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ 请求失败: {e}")
        return False

    # 测试4: 按类型取消任务
    print("\n4. 测试按类型取消任务...")
    try:
        response = requests.post(
            f"{base_url}/api/v1/tasks/cancel-by-type",
            data={"task_type": "image_preprocess", "cancel_running": False}
        )
        if response.status_code == 200:
            result = response.json()
            print(f"   ✓ 按类型取消任务成功")
            print(f"   - 任务类型: {result['result']['task_type']}")
            print(f"   - 已取消: {result['result']['cancelled']}")
            print(f"   - 失败: {result['result']['failed']}")
        else:
            print(f"   ✗ 按类型取消任务失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ 请求失败: {e}")
        return False

    # 测试5: 取消单个任务（不存在的任务）
    print("\n5. 测试取消单个任务（不存在的任务）...")
    try:
        response = requests.post(f"{base_url}/api/v1/tasks/nonexistent_task/cancel")
        if response.status_code == 404:
            print(f"   ✓ 正确返回404错误")
            print(f"   - 错误信息: {response.json()['detail']}")
        else:
            print(f"   ✗ 预期404错误，实际返回: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ 请求失败: {e}")
        return False

    # 测试6: 更新任务优先级（不存在的任务）
    print("\n6. 测试更新任务优先级（不存在的任务）...")
    try:
        response = requests.post(
            f"{base_url}/api/v1/tasks/nonexistent_task/priority",
            data={"priority": 1}
        )
        if response.status_code == 404:
            print(f"   ✓ 正确返回404错误")
            print(f"   - 错误信息: {response.json()['detail']}")
        else:
            print(f"   ✗ 预期404错误，实际返回: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ 请求失败: {e}")
        return False

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
    print("\n所有任务控制API接口测试通过！")
    print("\n可用的任务控制API接口：")
    print("  - GET  /api/v1/tasks/stats          获取任务统计")
    print("  - GET  /api/v1/tasks               获取所有任务")
    print("  - POST /api/v1/tasks/cancel-all    取消所有任务")
    print("  - POST /api/v1/tasks/cancel-by-type 按类型取消任务")
    print("  - POST /api/v1/tasks/{task_id}/cancel   取消单个任务")
    print("  - POST /api/v1/tasks/{task_id}/priority 更新任务优先级")

    return True

if __name__ == "__main__":
    print("\n请确保API服务器正在运行:")
    print("  python3 src/api_server.py")
    print("\n开始测试...")
    
    success = test_task_control_api()
    sys.exit(0 if success else 1)