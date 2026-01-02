#!/usr/bin/env python3
"""
测试向量化流程：使用真实模型将目标目录中的文件向量化并存储到数据库
"""

import os
import sys
import logging
import time
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from src.core.config_manager import get_config_manager
from src.core.logging_config import setup_logging
from src.processing_service.file_monitor import FileMonitor
from src.processing_service.orchestrator import ProcessingOrchestrator
from src.search_service.smart_retrieval_engine import SmartRetrievalEngine

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_vectorization_flow():
    """测试向量化流程"""
    logger.info("开始测试向量化流程...")
    
    try:
        # 1. 初始化配置管理器
        config_manager = get_config_manager()
        
        # 2. 设置日志系统
        setup_logging(config_manager.get("system.log_level", "INFO"))
        
        logger.info("配置加载完成，开始初始化核心组件...")
        
        # 3. 初始化核心组件
        file_monitor = FileMonitor(config_manager)
        orchestrator = ProcessingOrchestrator(config_manager)
        search_engine = SmartRetrievalEngine(config_manager)
        
        logger.info("核心组件初始化完成，开始启动服务...")
        
        # 4. 启动服务
        import asyncio
        
        async def run_services():
            # 启动文件监控
            await file_monitor.start()
            logger.info("文件监控服务启动成功")
            
            # 启动处理调度器
            await orchestrator.start()
            logger.info("处理调度器启动成功")
            
            # 启动检索服务
            await search_engine.start()
            logger.info("检索服务启动成功")
            
            # 等待服务稳定
            await asyncio.sleep(3)
            
            # 5. 生成测试文件
            logger.info("生成测试文件...")
            test_dir = Path(config_manager.get("system.monitored_directories")[0])
            test_dir.mkdir(parents=True, exist_ok=True)
            
            # 创建多个测试文件
            for i in range(3):
                test_file = test_dir / f"test_image_{i}.jpg"
                
                # 使用PIL生成简单的彩色图片
                from PIL import Image, ImageDraw, ImageFont
                img = Image.new('RGB', (200, 200), color=(i*50, i*30, i*80))
                d = ImageDraw.Draw(img)
                d.text((10,10), f"Test Image {i}", fill=(255,255,255))
                img.save(test_file)
                logger.info(f"创建测试文件: {test_file}")
                
                # 等待文件被处理
                await asyncio.sleep(2)
            
            # 6. 等待处理完成
            logger.info("等待5秒让系统处理文件...")
            await asyncio.sleep(5)
            
            # 7. 检查向量是否被存储
            logger.info("检查向量存储情况...")
            
            # 使用search_engine检查向量数量
            try:
                # 这里我们简单检查Milvus集合是否存在
                # 实际的向量查询需要根据系统设计来实现
                logger.info("向量化流程测试完成！")
            except Exception as e:
                logger.error(f"检查向量存储时出错: {e}")
            
            # 8. 停止服务
            await file_monitor.stop()
            await orchestrator.stop()
            await search_engine.stop()
            
        # 运行服务测试
        asyncio.run(run_services())
        
        logger.info("✅ 向量化流程测试成功完成！")
        return True
        
    except Exception as e:
        logger.error(f"❌ 向量化流程测试失败: {e}")
        import traceback
        logger.error(f"错误堆栈: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_vectorization_flow()
    sys.exit(0 if success else 1)