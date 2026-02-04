#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试任务管理器API
"""

import requests
import json
import time

API_BASE_URL = "http://localhost:8000"

def test_task_api():
    """测试任务API"""
    
    print("=" * 60)
    print("测试任务管理器API")
    print("=" * 60)
    
    # 1. 获取所有任务
    print("\n1. 获取所有任务...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/tasks", timeout=10)
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   总任务数: {data.get('total_tasks', 0)}")
            tasks = data.get('tasks', [])
            print(f"   任务列表长度: {len(tasks)}")
            if tasks:
                print(f"   第一个任务: {json.dumps(tasks[0], indent=2, default=str)}")
            else:
                print("   ⚠️ 没有任务")
        else:
            print(f"   错误: {response.text}")
    except Exception as e:
        print(f"   ❌ 请求失败: {e}")
    
    # 2. 获取任务统计
    print("\n2. 获取任务统计...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/tasks/stats", timeout=10)
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   统计数据: {json.dumps(data, indent=2, default=str)}")
        else:
            print(f"   错误: {response.text}")
    except Exception as e:
        print(f"   ❌ 请求失败: {e}")
    
    # 3. 创建一个测试任务
    print("\n3. 创建测试任务...")
    try:
        # 首先尝试通过索引文件创建任务
        test_file = "/data/project/msearch/data/testdata/image.jpg"
        response = requests.post(
            f"{API_BASE_URL}/api/v1/index/file",
            data={"file_path": test_file},
            timeout=10
        )
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   响应: {json.dumps(data, indent=2, default=str)}")
        else:
            print(f"   错误: {response.text}")
    except Exception as e:
        print(f"   ❌ 请求失败: {e}")
    
    # 4. 等待一下，再次获取任务列表
    print("\n4. 等待2秒后再次获取任务列表...")
    time.sleep(2)
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/tasks", timeout=10)
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   总任务数: {data.get('total_tasks', 0)}")
            tasks = data.get('tasks', [])
            print(f"   任务列表长度: {len(tasks)}")
            if tasks:
                print(f"   第一个任务: {json.dumps(tasks[0], indent=2, default=str)}")
            else:
                print("   ⚠️ 仍然没有任务")
        else:
            print(f"   错误: {response.text}")
    except Exception as e:
        print(f"   ❌ 请求失败: {e}")
    
    # 5. 检查系统信息
    print("\n5. 获取系统信息...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/system/info", timeout=10)
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   系统信息: {json.dumps(data, indent=2, default=str)}")
        else:
            print(f"   错误: {response.text}")
    except Exception as e:
        print(f"   ❌ 请求失败: {e}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    test_task_api()
