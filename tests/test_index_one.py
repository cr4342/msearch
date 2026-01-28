#!/usr/bin/env python3
"""
测试索引单个文件
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.config.config_manager import ConfigManager
from src.core.embedding.embedding_engine import EmbeddingEngine
from src.core.vector.vector_store import VectorStore

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_index_one_file(file_path: str):
    """
    测试索引单个文件
    
    Args:
        file_path: 文件路径
    """
    # 设置离线环境变量
    os.environ['TRANSFORMERS_OFFLINE'] = '1'
    os.environ['HF_DATASETS_OFFLINE'] = '1'
    os.environ['HF_HUB_OFFLINE'] = '1'
    
    logger.info("=" * 60)
    logger.info("测试索引单个文件")
    logger.info("=" * 60)
    logger.info(f"文件路径: {file_path}")
    
    # 加载配置
    config_manager = ConfigManager()
    config = config_manager.get_all()
    
    # 初始化组件
    logger.info("初始化组件...")
    
    # 向量化引擎
    embedding_engine = EmbeddingEngine(config)
    await embedding_engine.initialize()
    logger.info("✓ 向量化引擎初始化完成")
    
    # 向量化文件
    logger.info(f"\n开始向量化文件...")
    file_ext = Path(file_path).suffix.lower()
    
    if file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp']:
        embedding = await embedding_engine.embed_image(file_path)
        logger.info(f"✓ 图像向量化完成，向量维度: {len(embedding)}")
        modality = 'image'
    elif file_ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
        embedding = await embedding_engine.embed_video_segment(file_path)
        logger.info(f"✓ 视频向量化完成，向量维度: {len(embedding)}")
        modality = 'video'
    elif file_ext in ['.mp3', '.wav', '.aac', '.flac', '.ogg', '.wma']:
        embedding = await embedding_engine.embed_audio(file_path)
        logger.info(f"✓ audio向量化完成，向量维度: {len(embedding)}")
        modality = 'audio'
    else:
        logger.error(f"不支持的文件类型: {file_ext}")
        return
    
    # 存储到向量数据库
    if embedding:
        logger.info("\n存储向量到数据库...")
        
        vector_store_config = {
            'data_dir': config.get('database.lancedb.data_dir', 'data/database/lancedb'),
            'collection_name': config.get('database.lancedb.collection_name', 'unified_vectors'),
            'index_type': config.get('database.lancedb.index_type', 'ivf_pq'),
            'num_partitions': config.get('database.lancedb.num_partitions', 128),
            'vector_dimension': config.get('database.lancedb.vector_dimension', 512)
        }
        vector_store = VectorStore(vector_store_config)
        vector_store.initialize()
        
        file_name = Path(file_path).name
        vector_store.add_vector(
            vector_id="test_vector",
            vector=embedding,
            file_id="test_file",
            file_path=file_path,
            file_name=file_name,
            file_type=modality,
            modality=modality,
            metadata={'test': True}
        )
        logger.info("✓ 向量存储完成")
        
        vector_store.close()
    else:
        logger.error("向量化失败")
    
    # 关闭组件
    embedding_engine.shutdown()
    
    logger.info("\n" + "=" * 60)
    logger.info("测试完成")
    logger.info("=" * 60)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='测试索引单个文件')
    parser.add_argument('file_path', type=str, help='文件路径')
    
    args = parser.parse_args()
    
    asyncio.run(test_index_one_file(args.file_path))