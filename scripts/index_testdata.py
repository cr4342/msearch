#!/usr/bin/env python3
"""
索引testdata目录中的文件
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
from src.core.database.database_manager import DatabaseManager
from src.core.vector.vector_store import VectorStore
from src.core.embedding.embedding_engine import EmbeddingEngine
from src.services.media.media_processor import MediaProcessor

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def index_files(directory: str):
    """
    索引目录中的文件
    
    Args:
        directory: 目录路径
    """
    # 设置离线环境变量
    os.environ['TRANSFORMERS_OFFLINE'] = '1'
    os.environ['HF_DATASETS_OFFLINE'] = '1'
    os.environ['HF_HUB_OFFLINE'] = '1'
    os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'
    os.environ['INFINITY_ANONYMOUS_USAGE_STATS'] = '0'
    
    logger.info("=" * 60)
    logger.info("开始索引文件")
    logger.info("=" * 60)
    
    # 加载配置
    config_manager = ConfigManager()
    config = config_manager.get_all()
    
    # 初始化组件
    logger.info("初始化组件...")
    
    # 数据库管理器
    db_path = config.get('database.sqlite.path', 'data/database/sqlite/msearch.db')
    database_manager = DatabaseManager(db_path)
    database_manager.initialize()
    logger.info("✓ 数据库管理器初始化完成")
    
    # 向量存储
    vector_store_config = {
        'data_dir': config.get('database.lancedb.data_dir', 'data/database/lancedb'),
        'collection_name': config.get('database.lancedb.collection_name', 'unified_vectors'),
        'index_type': config.get('database.lancedb.index_type', 'ivf_pq'),
        'num_partitions': config.get('database.lancedb.num_partitions', 128),
        'vector_dimension': config.get('database.lancedb.vector_dimension', 512)
    }
    vector_store = VectorStore(vector_store_config)
    vector_store.initialize()
    logger.info("✓ 向量存储初始化完成")
    
    # 向量化引擎
    embedding_engine = EmbeddingEngine(config)
    await embedding_engine.initialize()
    logger.info("✓ 向量化引擎初始化完成")
    
    # 媒体处理器
    media_processor = MediaProcessor(config)
    logger.info("✓ 媒体处理器初始化完成")
    
    # 扫描目录
    logger.info(f"\n扫描目录: {directory}")
    
    # 查找所有支持的文件
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp']
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm']
    audio_extensions = ['.mp3', '.wav', '.aac', '.flac', '.ogg', '.wma']
    
    files = []
    directory_path = Path(directory)
    
    if directory_path.exists() and directory_path.is_dir():
        for ext in image_extensions + video_extensions + audio_extensions:
            files.extend(directory_path.rglob(f'*{ext}'))
    
    logger.info(f"找到 {len(files)} 个文件")
    
    if len(files) == 0:
        logger.warning("未找到任何文件")
        return
    
    # 处理文件（只处理前5个文件进行测试）
    logger.info("\n开始处理文件（仅前5个）...")
    
    for i, file_path in enumerate(files[:5]):
        logger.info(f"\n[{i+1}/5] 处理文件: {file_path}")
        
        try:
            # 处理文件
            result = media_processor.process_file(str(file_path))
            
            if result.get('status') == 'success':
                media_type = result.get('media_type')
                metadata = result.get('metadata', {})
                
                logger.info(f"  ✓ 文件处理成功")
                logger.info(f"    媒体类型: {media_type}")
                logger.info(f"    文件大小: {metadata.get('file_size')} bytes")
                
                # 向量化
                if media_type == 'image':
                    embedding = await embedding_engine.embed_image(str(file_path))
                    logger.info(f"  ✓ 图像向量化完成，向量维度: {len(embedding) if embedding else 0}")
                elif media_type == 'video':
                    embedding = await embedding_engine.embed_video_segment(str(file_path))
                    logger.info(f"  ✓ 视频向量化完成，向量维度: {len(embedding) if embedding else 0}")
                elif media_type == 'audio':
                    embedding = await embedding_engine.embed_audio(str(file_path))
                    logger.info(f"  ✓ 音频向量化完成，向量维度: {len(embedding) if embedding else 0}")
                
                # 存储到向量数据库
                if embedding:
                    file_id = metadata.get('file_id', f"file_{i}")
                    vector_store.add_vector(
                        vector_id=f"{file_id}_vector",
                        vector=embedding,
                        file_id=file_id,
                        file_path=str(file_path),
                        file_name=file_path.name,
                        file_type=media_type,
                        modality=media_type,
                        metadata=metadata
                    )
                    logger.info(f"  ✓ 向量存储完成")
            else:
                logger.warning(f"  ✗ 文件处理失败: {result.get('error')}")
                
        except Exception as e:
            logger.error(f"  ✗ 处理文件失败: {e}")
    
    logger.info("\n" + "=" * 60)
    logger.info("索引完成")
    logger.info("=" * 60)
    
    # 关闭组件
    vector_store.close()
    database_manager.close()
    embedding_engine.shutdown()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='索引testdata目录中的文件')
    parser.add_argument('directory', type=str, help='目录路径', default='testdata')
    
    args = parser.parse_args()
    
    asyncio.run(index_files(args.directory))