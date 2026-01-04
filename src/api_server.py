#!/usr/bin/env python3
"""
msearch API 服务启动脚本
根据新的简化架构，API功能将集成到主应用中
"""
import sys
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 简单的API服务实现
def start_api_server():
    """启动API服务"""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("API服务功能已集成到主应用中")
    logger.info("请直接运行 main.py 启动完整服务")


if __name__ == "__main__":
    start_api_server()