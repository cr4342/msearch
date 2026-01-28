#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 WebUI 搜索功能
"""

import requests
import json
import time

# WebUI URL
WEBUI_URL = "http://localhost:7860"

def test_text_search():
    """测试文本搜索"""
    print("="*60)
    print("测试 WebUI 文本搜索功能")
    print("="*60)
    
    # 测试关键词
    keywords = ["熊猫", "老虎", "音乐", "风景"]
    
    for keyword in keywords:
        print(f"\n--- 搜索: '{keyword}' ---")
        print("="*60)
        
        try:
            # 使用 Gradio API 进行搜索
            response = requests.post(f"{WEBUI_URL}/gradio_api/predict", json={
                "data": [
                    keyword,  # 查询文本
                    10  # top_k
                ],
                "fn_index": 0  # search_text 函数的索引
            }, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                print(f"搜索结果: {result}")
                
                if 'data' in result and len(result['data']) > 0:
                    search_output = result['data'][0]
                    print(f"\n{search_output}")
                else:
                    print("未找到结果")
            else:
                print(f"请求失败: {response.status_code}")
                print(f"错误信息: {response.text}")
                
        except Exception as e:
            print(f"搜索失败: {e}")
            import traceback
            traceback.print_exc()
        
        time.sleep(2)

if __name__ == "__main__":
    test_text_search()