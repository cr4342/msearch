#!/usr/bin/env python3
"""
简单测试Milvus Lite连接和基本操作
"""

import os
import sys
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_milvus_lite():
    """测试Milvus Lite"""
    logger.info("开始测试Milvus Lite...")
    
    try:
        # 安装milvus-lite
        logger.info("安装milvus-lite...")
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "milvus-lite"], check=True)
        logger.info("milvus-lite安装成功")
        
        # 导入MilvusClient
        logger.info("导入MilvusClient...")
        from pymilvus import MilvusClient
        logger.info("MilvusClient导入成功")
        
        # 创建测试目录
        test_dir = Path("./data/milvus")
        test_dir.mkdir(parents=True, exist_ok=True)
        
        # 测试连接Milvus Lite
        db_path = str(test_dir / "milvus.db")
        logger.info(f"测试连接Milvus Lite，数据库路径: {db_path}")
        
        # 直接使用文件路径创建MilvusClient
        client = MilvusClient(db_path)
        logger.info("Milvus Lite连接成功！")
        
        # 测试创建集合
        collection_name = "test_vectors"
        logger.info(f"测试创建集合: {collection_name}")
        
        # 定义集合模式
        schema = {
            "collection_name": collection_name,
            "dimension": 512,
            "metric_type": "COSINE",
            "index_type": "IVF_FLAT"
        }
        
        # 创建集合
        client.create_collection(**schema)
        logger.info(f"集合 {collection_name} 创建成功")
        
        # 测试插入向量
        logger.info("测试插入向量...")
        import numpy as np
        vectors = [np.random.rand(512).tolist() for _ in range(3)]
        data = [{"id": i, "vector": vectors[i]} for i in range(3)]
        
        result = client.insert(collection_name=collection_name, data=data)
        logger.info(f"向量插入成功，插入的向量数量: {len(result['insert_count'])}")
        
        # 测试搜索
        logger.info("测试向量搜索...")
        query_vector = vectors[0]
        search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}
        
        results = client.search(
            collection_name=collection_name,
            data=[query_vector],
            limit=2,
            search_params=search_params
        )
        
        logger.info(f"搜索成功，结果: {results}")
        
        # 测试获取集合信息
        logger.info("测试获取集合信息...")
        collection_info = client.describe_collection(collection_name=collection_name)
        logger.info(f"集合信息: {collection_info}")
        
        # 测试删除集合
        logger.info(f"测试删除集合: {collection_name}")
        client.drop_collection(collection_name=collection_name)
        logger.info(f"集合 {collection_name} 删除成功")
        
        logger.info("✅ Milvus Lite测试成功完成！")
        return True
        
    except Exception as e:
        logger.error(f"❌ Milvus Lite测试失败: {e}")
        import traceback
        logger.error(f"错误堆栈: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_milvus_lite()
    sys.exit(0 if success else 1)
