#!/usr/bin/env python3
"""
msearch API 服务启动脚本
"""

import uvicorn
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.api.app import app

if __name__ == "__main__":
    # 启动API服务
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=False,  # 生产环境关闭热重载
        access_log=True
    )