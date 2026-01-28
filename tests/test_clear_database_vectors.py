#!/usr/bin/env python3
"""
测试清空数据库和向量库的功能
"""

import tempfile
import os
from pathlib import Path
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.database.database_manager import DatabaseManager
from src.core.vector.vector_store import VectorStore
import logging
import numpy as np

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_clear_database():
    """测试清空数据库功能"""
    logger.info("=== 测试清空数据库功能 ===")
    
    # 创建临时数据库路径
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        
        # 初始化数据库管理器
        db_manager = DatabaseManager(db_path)
        
        # 插入测试数据
        test_file = {
            "file_path": "/tmp/test_file.jpg",
            "file_name": "test_file.jpg",
            "file_type": "image",
            "file_size": 1024,
            "file_hash": "test_hash_123",
            "metadata": {"test_key": "test_value"}
        }
        
        file_id = db_manager.insert_file_metadata(test_file)
        logger.info(f"插入测试文件，ID: {file_id}")
        
        # 获取统计信息
        stats_before = db_manager.get_database_stats()
        logger.info(f"清空前数据库统计: {stats_before}")
        
        # 清空数据库
        success = db_manager.clear_database()
        logger.info(f"清空数据库: {'成功' if success else '失败'}")
        
        # 获取清空后的统计信息
        stats_after = db_manager.get_database_stats()
        logger.info(f"清空后数据库统计: {stats_after}")
        
        # 验证数据库已清空
        assert stats_after['total_files'] == 0, "数据库未成功清空"
        
        # 关闭数据库
        db_manager.close()
        
    logger.info("数据库清空测试通过\n")

def test_clear_vectors():
    """测试清空向量库功能"""
    logger.info("=== 测试清空向量库功能 ===")
    
    # 创建临时向量库路径
    with tempfile.TemporaryDirectory() as tmpdir:
        # 配置向量存储
        vector_config = {
            "data_dir": os.path.join(tmpdir, "lancedb"),
            "collection_name": "test_vectors",
            "vector_dimension": 128
        }
        
        # 初始化向量存储
        vector_store = VectorStore(vector_config)
        
        # 插入测试向量
        test_vectors = []
        for i in range(5):
            vector = {
                "id": f"test_vec_{i}",
                "vector": np.random.rand(128).tolist(),
                "modality": "image",
                "file_id": f"file_{i}",
                "metadata": {"test_key": f"test_value_{i}"}
            }
            test_vectors.append(vector)
        
        vector_store.insert_vectors(test_vectors)
        logger.info("插入5个测试向量")
        
        # 获取统计信息
        stats_before = vector_store.get_collection_stats()
        logger.info(f"清空前向量库统计: {stats_before}")
        
        # 清空向量库
        vector_store.clear_vectors()
        logger.info("清空向量库")
        
        # 获取清空后的统计信息
        stats_after = vector_store.get_collection_stats()
        logger.info(f"清空后向量库统计: {stats_after}")
        
        # 验证向量库已清空
        assert stats_after['total_vectors'] == 0, "向量库未成功清空"
        
        # 关闭向量库
        vector_store.close()
        
    logger.info("向量库清空测试通过\n")

if __name__ == "__main__":
    test_clear_database()
    test_clear_vectors()
    logger.info("所有测试都已通过!")
