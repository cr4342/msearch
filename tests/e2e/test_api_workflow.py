#!/usr/bin/env python3
"""
使用 API 测试完整工作流程
"""

import requests
import json
import time
from pathlib import Path

API_URL = "http://localhost:8000"

def test_api_workflow():
    """测试 API 工作流程"""
    print("="*60)
    print("msearch API 工作流程测试")
    print("="*60)
    
    # 1. 健康检查
    print("\n[1/6] 健康检查")
    print("="*60)
    response = requests.get(f"{API_URL}/api/v1/health")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    
    # 2. 系统信息
    print("\n[2/6] 系统信息")
    print("="*60)
    response = requests.get(f"{API_URL}/api/v1/system/info")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    
    # 3. 索引状态
    print("\n[3/6] 索引状态")
    print("="*60)
    response = requests.get(f"{API_URL}/api/v1/index/status")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    
    # 4. 添加索引
    print("\n[4/6] 添加索引")
    print("="*60)
    
    # 获取 testdata 目录下的所有图片文件
    testdata_dir = Path("testdata")
    image_files = list(testdata_dir.glob("*.jpg")) + list(testdata_dir.glob("*.png"))
    image_files = [str(f) for f in image_files if f.is_file()]
    
    print(f"找到 {len(image_files)} 个图片文件")
    
    # 添加前 10 个文件到索引
    for i, file_path in enumerate(image_files[:10], 1):
        print(f"\n添加文件 {i}/{min(10, len(image_files))}: {file_path}")
        
        request_data = {
            "file_path": file_path,
            "file_type": "image",
            "priority": 5
        }
        
        response = requests.post(f"{API_URL}/api/v1/index/add", json=request_data)
        print(f"响应: {response.json()}")
        
        time.sleep(0.5)  # 等待一小段时间
    
    # 等待索引处理完成
    print("\n等待索引处理完成...")
    time.sleep(5)
    
    # 5. 测试搜索
    print("\n[5/6] 测试搜索")
    print("="*60)
    
    keywords = ["老虎", "骑行", "樱桃", "人物", "风景", "猫"]
    
    for keyword in keywords:
        print(f"\n--- 搜索: '{keyword}' ---")
        print("="*60)
        
        request_data = {
            "query": keyword,
            "top_k": 5
        }
        
        response = requests.post(f"{API_URL}/api/v1/search/text", json=request_data)
        result = response.json()
        
        print(f"查询: {result.get('query', 'N/A')}")
        print(f"结果数: {result.get('total', 0)}")
        
        if result.get('results'):
            print("\n搜索结果:")
            for i, item in enumerate(result['results'][:5], 1):
                score = item.get('score', 0)
                file_name = item.get('file_name', 'N/A')
                file_path = item.get('file_path', 'N/A')
                modality = item.get('modality', 'N/A')
                
                print(f"\n  [{i}] 相似度: {score:.4f}")
                print(f"      文件: {file_name}")
                print(f"      路径: {file_path}")
                print(f"      模态: {modality}")
        else:
            print("未找到匹配结果")
    
    # 6. 任务统计
    print("\n[6/6] 任务统计")
    print("="*60)
    response = requests.get(f"{API_URL}/api/v1/tasks/stats")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    
    print("\n" + "="*60)
    print("所有测试完成！")
    print("="*60)


if __name__ == "__main__":
    try:
        test_api_workflow()
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()
