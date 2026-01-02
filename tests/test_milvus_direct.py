#!/usr/bin/env python3
"""
直接测试Milvus Lite，不依赖任何项目代码
"""

import sys
print(f"Python版本: {sys.version}")
print(f"Python路径: {sys.executable}")

# 尝试安装pymilvus
print("\n尝试安装pymilvus...")
import subprocess
result = subprocess.run(
    [sys.executable, "-m", "pip", "install", "-U", "pymilvus"],
    capture_output=True,
    text=True
)
print(f"安装命令返回码: {result.returncode}")
print(f"安装stdout: {result.stdout}")
print(f"安装stderr: {result.stderr}")

# 尝试导入MilvusClient
print("\n尝试导入MilvusClient...")
try:
    from pymilvus import MilvusClient
    print("MilvusClient导入成功！")
    
    # 尝试创建客户端
    print("尝试创建MilvusClient...")
    client = MilvusClient("./data/milvus/milvus.db")
    print("MilvusClient创建成功！")
    
    # 尝试创建集合
    print("尝试创建集合...")
    client.create_collection(
        collection_name="test_collection",
        dimension=512,
        metric_type="COSINE",
        index_type="IVF_FLAT"
    )
    print("集合创建成功！")
    
    # 清理
    print("清理测试集合...")
    client.drop_collection("test_collection")
    print("测试完成！")
    
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
