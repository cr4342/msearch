#!/usr/bin/env python3
"""
msearch 多模态检索系统主入口
"""

import asyncio
import logging
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.config_manager import get_config_manager
from src.core.logging_config import setup_logging
from src.processing_service.file_monitor import FileMonitor
from src.processing_service.orchestrator import ProcessingOrchestrator
from src.search_service.smart_retrieval_engine import SmartRetrievalEngine


async def main():
    """主函数"""
    # 初始化配置管理器
    config_manager = get_config_manager()
    
    # 设置日志系统
    setup_logging(config_manager.get("system.log_level", "INFO"))
    logger = logging.getLogger(__name__)
    
    logger.info("启动 msearch 多模态检索系统")
    
    try:
        # 初始化核心组件
        file_monitor = FileMonitor(config_manager)
        orchestrator = ProcessingOrchestrator(config_manager)
        search_engine = SmartRetrievalEngine(config_manager)
        
        # 启动文件监控
        await file_monitor.start()
        
        # 启动处理调度器
        await orchestrator.start()
        
        # 启动检索服务
        await search_engine.start()
        
        logger.info("所有服务启动完成")
        
        # 保持运行
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("收到停止信号，正在关闭服务...")
            
    except Exception as e:
        logger.error(f"系统启动失败: {e}")
        sys.exit(1)
    
    finally:
        # 清理资源
        if 'file_monitor' in locals():
            await file_monitor.stop()
        if 'orchestrator' in locals():
            await orchestrator.stop()
        if 'search_engine' in locals():
            await search_engine.stop()
        
        logger.info("系统已关闭")


if __name__ == "__main__":
    asyncio.run(main())