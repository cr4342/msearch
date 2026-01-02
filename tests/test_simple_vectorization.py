#!/usr/bin/env python3
"""
简单测试向量化流程：直接使用模型生成向量并存储到Milvus
"""

import os
import sys
import logging
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_simple_vectorization():
    """测试简单向量化流程"""
    logger.info("开始测试简单向量化流程...")
    
    try:
        # 1. 初始化配置
        from src.core.config_manager import get_config_manager
        config_manager = get_config_manager()
        
        # 2. 初始化Milvus适配器
        from src.common.storage.milvus_adapter import MilvusAdapter
        milvus_adapter = MilvusAdapter(config_manager)
        
        # 3. 连接Milvus
        logger.info("连接Milvus...")
        if not await milvus_adapter.connect():
            logger.error("Milvus连接失败")
            return False
        logger.info("Milvus连接成功")
        
        # 4. 测试集合创建
        logger.info("创建测试集合...")
        test_collection = "test_vectors"
        
        # 5. 准备测试向量数据
        logger.info("准备测试向量数据...")
        import numpy as np
        vectors = [np.random.rand(512).astype(np.float32) for _ in range(3)]
        
        # 6. 批量存储向量
        logger.info("批量存储向量...")
        # 构造向量数据格式：[(向量, 文件ID, 片段ID, 元数据), ...]
        vectors_data = []
        for i, vector in enumerate(vectors):
            vectors_data.append((
                vector,
                f"test_file_{i}",
                f"segment_{i}",
                {"test_key": f"test_value_{i}"}
            ))
        
        # 使用visual集合类型
        vector_ids = await milvus_adapter.batch_store_vectors(
            collection_type="visual",
            vectors_data=vectors_data
        )
        
        logger.info(f"向量存储成功，生成的向量ID: {vector_ids}")
        
        # 7. 测试向量搜索
        logger.info("测试向量搜索...")
        query_vector = vectors[0]  # 使用第一个向量作为查询
        results = await milvus_adapter.search_vectors(
            collection_type="visual",
            query_vector=query_vector,
            limit=2
        )
        
        logger.info(f"搜索结果: {results}")
        
        # 8. 测试获取向量数量
        logger.info("测试获取向量数量...")
        vector_count = await milvus_adapter.get_vector_count("visual")
        logger.info(f"visual集合中的向量数量: {vector_count}")
        
        # 9. 断开连接
        await milvus_adapter.disconnect()
        logger.info("Milvus连接已断开")
        
        logger.info("✅ 简单向量化流程测试成功完成！")
        return True
        
    except Exception as e:
        logger.error(f"❌ 简单向量化流程测试失败: {e}")
        import traceback
        logger.error(f"错误堆栈: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    import asyncio
    success = asyncio.run(test_simple_vectorization())
    sys.exit(0 if success else 1)