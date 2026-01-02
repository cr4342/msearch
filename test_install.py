#!/usr/bin/env python3
"""
测试安装是否成功
"""

import os
import sys

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 测试Milvus Lite连接
try:
    print("测试Milvus Lite连接...")
    from pymilvus import MilvusClient
    
    # 使用临时路径作为Milvus Lite的存储目录
    milvus_path = os.path.join(project_root, "temp", "test_milvus.db")
    os.makedirs(os.path.dirname(milvus_path), exist_ok=True)
    
    # 连接Milvus Lite
    client = MilvusClient(milvus_path, db_name="default")
    print(f"✓ 成功连接到Milvus Lite: {milvus_path}")
    
    # 获取所有集合
    collections = client.list_collections()
    print(f"✓ Milvus Lite包含 {len(collections)} 个集合: {collections}")
    
    # 创建一个测试集合
    test_collection = "test_collection"
    if test_collection not in collections:
        client.create_collection(
            collection_name=test_collection,
            dimension=128,
            primary_field_name="id",
            primary_field_type="VARCHAR",
            vector_field_name="vector",
            metric_type="COSINE"
        )
        print(f"✓ 成功创建测试集合: {test_collection}")
    
    # 插入测试数据
    import numpy as np
    vectors = [np.random.rand(128).tolist() for _ in range(5)]
    data = [
        {
            "id": f"id_{i}",
            "vector": vectors[i]
        } for i in range(5)
    ]
    client.insert(collection_name=test_collection, data=data)
    print(f"✓ 成功插入5条测试数据")
    
    # 搜索测试
    search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}
    results = client.search(
        collection_name=test_collection,
        data=[vectors[0]],
        limit=3,
        search_params=search_params
    )
    print(f"✓ 成功搜索到 {len(results[0])} 条结果")
    
    # 删除测试集合
    client.drop_collection(collection_name=test_collection)
    print(f"✓ 成功删除测试集合: {test_collection}")
    
    print("\nMilvus Lite测试通过！")
    
except Exception as e:
    print(f"✗ Milvus Lite测试失败: {e}")
    import traceback
    traceback.print_exc()

# 测试PyTorch安装
try:
    print("\n测试PyTorch安装...")
    import torch
    print(f"✓ PyTorch版本: {torch.__version__}")
    print(f"✓ CUDA可用: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"✓ CUDA版本: {torch.version.cuda}")
        print(f"✓ GPU设备: {torch.cuda.get_device_name(0)}")
    
    # 测试简单运算
    x = torch.tensor([1.0, 2.0, 3.0])
    y = x * 2
    print(f"✓ 张量运算: {x} * 2 = {y}")
    
    print("\nPyTorch测试通过！")
    
except Exception as e:
    print(f"✗ PyTorch测试失败: {e}")
    import traceback
    traceback.print_exc()

# 测试其他核心依赖
try:
    print("\n测试其他核心依赖...")
    
    # 测试transformers
    import transformers
    print(f"✓ Transformers版本: {transformers.__version__}")
    
    # 测试huggingface_hub
    import huggingface_hub
    print(f"✓ Hugging Face Hub版本: {huggingface_hub.__version__}")
    
    # 测试faiss
    import faiss
    print(f"✓ FAISS版本: {faiss.__version__}")
    
    print("\n其他核心依赖测试通过！")
    
except Exception as e:
    print(f"✗ 其他核心依赖测试失败: {e}")
    import traceback
    traceback.print_exc()

print("\n=== 安装测试完成 ===")
