#!/usr/bin/env python3
"""
msearch API 服务启动脚本
"""

import uvicorn
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.api.app import app
from src.core.config_manager import get_config_manager

if __name__ == "__main__":
    config_manager = get_config_manager()
    host = config_manager.get("api.host", "0.0.0.0")
    port = config_manager.get_int("api.port", 8000)
    log_level = config_manager.get("api.log_level", "info")
    reload = config_manager.get_bool("api.reload", False)
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level=log_level,
        reload=reload,
        access_log=True
    )