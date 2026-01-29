#!/usr/bin/env python3
"""
音频检索诊断脚本
"""
import sys
import os
import asyncio
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_audio_search():
    """测试音频检索功能"""
    try:
        # 1. 测试导入
        logger.info("Step 1: 测试导入...")
        from src.core.embedding.embedding_engine import EmbeddingEngine
        from src.services.search.search_engine import SearchEngine
        from src.core.config.config_manager import ConfigManager
        logger.info("✓ 导入成功")
        
        # 2. 加载配置
        logger.info("\nStep 2: 加载配置...")
        config_manager = ConfigManager("config/config.yml")
        config = config_manager.config
        logger.info(f"✓ 配置加载成功")
        logger.info(f"  音频模型: {config.get('models', {}).get('audio_model', {}).get('model_name')}")
        logger.info(f"  音频采样率: {config.get('processing', {}).get('audio', {}).get('sample_rate')}")
        
        # 3. 初始化向量化引擎
        logger.info("\nStep 3: 初始化向量化引擎...")
        embedding_engine = EmbeddingEngine(config)
        await embedding_engine.initialize()
        logger.info("✓ 向量化引擎初始化成功")
        
        # 4. 初始化搜索引擎
        logger.info("\nStep 4: 初始化搜索引擎...")
        search_engine = SearchEngine(config)
        await search_engine.initialize()
        logger.info("✓ 搜索引擎初始化成功")
        
        # 5. 测试音频向量化
        logger.info("\nStep 5: 测试音频向量化...")
        test_audio = "/data/project/msearch/testdata/阿炳-二泉映月 (二胡版).mp3"
        if not os.path.exists(test_audio):
            logger.error(f"测试音频文件不存在: {test_audio}")
            return
        
        logger.info(f"测试音频: {test_audio}")
        try:
            audio_vector = await embedding_engine.embed_audio(test_audio)
            logger.info(f"✓ 音频向量化成功")
            logger.info(f"  向量维度: {len(audio_vector)}")
            logger.info(f"  向量前5个值: {audio_vector[:5]}")
        except Exception as e:
            logger.error(f"✗ 音频向量化失败: {e}", exc_info=True)
            return
        
        # 6. 测试音频搜索
        logger.info("\nStep 6: 测试音频搜索...")
        try:
            search_results = await search_engine.audio_search(
                audio_path=test_audio,
                k=5
            )
            logger.info(f"✓ 音频搜索成功")
            logger.info(f"  搜索结果数量: {search_results.get('total', 0)}")
            for i, result in enumerate(search_results.get('results', [])[:3]):
                logger.info(f"  结果{i+1}: {result.get('file_name', 'N/A')} (score: {result.get('score', 0):.4f})")
        except Exception as e:
            logger.error(f"✗ 音频搜索失败: {e}", exc_info=True)
            return
        
        # 7. 测试API接口
        logger.info("\nStep 7: 测试API接口...")
        try:
            # 模拟API请求
            from src.api.v1.schemas import AudioSearchRequest
            from src.api.v1.handlers import APIServer
            
            api_server = APIServer(config)
            request = AudioSearchRequest(
                query_audio=test_audio,
                top_k=5,
                threshold=0.3
            )
            response = await api_server.handle_audio_search(request)
            logger.info(f"✓ API接口测试成功")
            logger.info(f"  返回结果数量: {response.total_results}")
        except Exception as e:
            logger.error(f"✗ API接口测试失败: {e}", exc_info=True)
        
        logger.info("\n✓✓✓ 所有测试通过！音频检索功能正常工作 ✓✓✓")
        
    except Exception as e:
        logger.error(f"\n✗✗✗ 测试失败: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(test_audio_search())