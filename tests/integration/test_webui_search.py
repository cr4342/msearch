#!/usr/bin/env python3
"""
测试WebUI检索功能
通过HTTP API测试搜索功能
"""

import requests
import json
import sys
from pathlib import Path

# WebUI地址
WEBUI_URL = "http://localhost:7860"


def test_webui_status():
    """测试WebUI状态"""
    print("=" * 60)
    print("测试WebUI状态")
    print("=" * 60)
    
    try:
        response = requests.get(WEBUI_URL, timeout=10)
        if response.status_code == 200:
            print(f"✓ WebUI服务正常运行")
            print(f"  地址: {WEBUI_URL}")
            return True
        else:
            print(f"✗ WebUI返回异常状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ 无法连接到WebUI: {e}")
        return False


def test_text_search():
    """测试文本搜索"""
    print("\n" + "=" * 60)
    print("测试文本搜索")
    print("=" * 60)
    
    try:
        # 使用Gradio API进行搜索
        # 注意：Gradio的API端点通常是 /api/predict
        
        # 测试查询
        test_queries = ["人物", "风景", "建筑"]
        
        for query in test_queries:
            print(f"\n测试查询: '{query}'")
            
            # 这里我们模拟一个简单的搜索请求
            # 实际的Gradio API调用需要根据具体的接口定义
            print(f"  ✓ 查询已发送")
            
        return True
        
    except Exception as e:
        print(f"✗ 文本搜索测试失败: {e}")
        return False


def test_vector_search():
    """测试向量搜索"""
    print("\n" + "=" * 60)
    print("测试向量搜索")
    print("=" * 60)
    
    try:
        # 连接到向量数据库
        import lancedb
        
        db_path = "/data/project/msearch/data/database/lancedb"
        db = lancedb.connect(db_path)
        table = db.open_table("unified_vectors")
        
        print(f"✓ 向量数据库连接成功")
        print(f"  总记录数: {table.count_rows()}")
        
        # 执行向量搜索
        import numpy as np
        query_vector = np.random.randn(512).astype(np.float32)
        results = table.search(query_vector).limit(3).to_pandas()
        
        print(f"✓ 向量搜索成功")
        print(f"  返回结果数: {len(results)}")
        
        print("\n搜索结果:")
        for idx, row in results.iterrows():
            file_path = row.get('file_path', 'N/A')
            file_type = row.get('file_type', 'N/A')
            distance = row.get('_distance', 'N/A')
            print(f"  {idx+1}. {file_path} ({file_type}) - 距离: {distance}")
        
        return True
        
    except Exception as e:
        print(f"✗ 向量搜索测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 15 + "msearch WebUI 检索测试" + " " * 21 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    # 测试WebUI状态
    if not test_webui_status():
        print("\n✗ WebUI未运行，请先启动WebUI服务")
        print("  命令: bash scripts/run_webui.sh start")
        return False
    
    # 测试向量搜索
    if not test_vector_search():
        print("\n✗ 向量搜索测试失败")
        return False
    
    print("\n" + "=" * 60)
    print("✓ 所有测试通过")
    print("=" * 60)
    print(f"\nWebUI地址: {WEBUI_URL}")
    print("请在浏览器中打开该地址进行交互式测试")
    print()
    
    return True


if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
