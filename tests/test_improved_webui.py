#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试改进后的 WebUI 功能
"""

import gradio_client as grc
import time

# WebUI URL
WEBUI_URL = "http://localhost:7860"

def test_improved_webui():
    """测试改进后的 WebUI 功能"""
    print("=" * 60)
    print("测试改进后的 WebUI 功能")
    print("=" * 60)
    
    try:
        # 连接到 Gradio 应用
        client = grc.Client(WEBUI_URL)
        print(f"✓ 成功连接到 WebUI: {WEBUI_URL}")
        
        # 测试 1: 文本搜索（改进的格式化）
        print("\n" + "=" * 60)
        print("测试 1: 文本搜索（改进的格式化）")
        print("=" * 60)
        
        result = client.predict(
            "熊猫",
            10,
            api_name="/search_text"
        )
        print(f"搜索结果:\n{result[:500]}...")
        
        time.sleep(2)
        
        # 测试 2: 多次搜索以验证历史记录
        print("\n" + "=" * 60)
        print("测试 2: 多次搜索以验证历史记录")
        print("=" * 60)
        
        keywords = ["老虎", "音乐", "风景"]
        for keyword in keywords:
            result = client.predict(
                keyword,
                5,
                api_name="/search_text"
            )
            result_count = result.count("个结果")
            print(f"搜索 '{keyword}': 找到 {result_count} 个结果")
            time.sleep(1)
        
        # 获取搜索历史
        print("\n" + "=" * 60)
        print("测试 3: 搜索历史记录")
        print("=" * 60)
        
        history_result = client.predict(
            api_name="/get_search_history"
        )
        print(f"搜索历史:\n{history_result[:800]}...")
        
        time.sleep(2)
        
        # 测试 4: 错误处理
        print("\n" + "=" * 60)
        print("测试 4: 错误处理")
        print("=" * 60)
        
        # 测试空输入
        empty_result = client.predict(
            "",
            10,
            api_name="/search_text"
        )
        print(f"空输入测试:\n{empty_result}")
        
        time.sleep(1)
        
        # 测试过长输入
        long_query = "测试" * 200
        long_result = client.predict(
            long_query,
            10,
            api_name="/search_text"
        )
        print(f"过长输入测试:\n{long_result[:300]}...")
        
        time.sleep(1)
        
        # 测试无效参数
        invalid_result = client.predict(
            "测试",
            150,  # 超过最大值 100
            api_name="/search_text"
        )
        print(f"无效参数测试:\n{invalid_result}")
        
        time.sleep(2)
        
        # 测试 5: 清空搜索历史
        print("\n" + "=" * 60)
        print("测试 5: 清空搜索历史")
        print("=" * 60)
        
        clear_result = client.predict(
            api_name="/clear_search_history"
        )
        print(f"清空历史结果:\n{clear_result}")
        
        # 验证历史已清空
        history_after_clear = client.predict(
            api_name="/get_search_history"
        )
        print(f"\n清空后的搜索历史:\n{history_after_clear[:300]}...")
        
        print("\n" + "=" * 60)
        print("✓ 所有测试完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_improved_webui()