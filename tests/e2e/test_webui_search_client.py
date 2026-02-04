#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 WebUI 搜索功能 - 使用 Gradio 客户端
"""

import gradio_client as grc
import time

# WebUI URL
WEBUI_URL = "http://localhost:7860"

def test_text_search():
    """测试文本搜索"""
    print("="*60)
    print("测试 WebUI 文本搜索功能")
    print("="*60)
    
    try:
        # 连接到 Gradio 应用
        client = grc.Client(WEBUI_URL)
        print(f"✓ 成功连接到 WebUI: {WEBUI_URL}")
        
        # 查看可用的 API 端点
        print("\n可用的 API 端点:")
        for fn_name, fn_info in client.view_api.all_endpoints.items():
            print(f"  - {fn_name}: {fn_info}")
        
        # 测试关键词
        keywords = ["熊猫", "老虎", "音乐", "风景"]
        
        for keyword in keywords:
            print(f"\n--- 搜索: '{keyword}' ---")
            print("="*60)
            
            try:
                # 调用搜索函数（使用第一个可用的函数）
                result = client.predict(
                    keyword,  # 查询文本
                    10,  # top_k
                    fn_index=0  # 使用第一个函数
                )
                
                print(f"搜索结果:\n{result}")
                
            except Exception as e:
                print(f"搜索失败: {e}")
                import traceback
                traceback.print_exc()
            
            time.sleep(2)
            
    except Exception as e:
        print(f"连接 WebUI 失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_text_search()