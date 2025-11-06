#!/usr/bin/env python3
"""
msearch 后端API服务主入口
基于FastAPI实现RESTful API服务
"""

import os
import sys
from pathlib import Path

# 将src目录添加到Python路径中
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from typing import List, Dict, Optional

from src.core.config import load_config
from src.core.logging_config import setup_logging, get_logger
from src.core.config_manager import get_config_manager
from src.business.orchestrator import ProcessingOrchestrator
from src.business.embedding_engine import get_embedding_engine

# 导入API路由
from src.api.routes import search, config, tasks, status, face

# 创建FastAPI应用实例
app = FastAPI(
    title="msearch API",
    description="msearch 多模态检索系统API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册API路由
app.include_router(search.router)
app.include_router(config.router)
app.include_router(tasks.router)
app.include_router(status.router)
app.include_router(face.router)
app.include_router(status.router)
app.include_router(face.router)

# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理"""
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": f"服务器内部错误: {str(exc)}"}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """HTTP异常处理"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "message": exc.detail}
    )

# 获取日志记录器
logger = get_logger(__name__)

# 获取配置
config = get_config_manager().config

# 获取处理编排器实例
processing_orchestrator = ProcessingOrchestrator(config)

# 健康检查端点




























if __name__ == "__main__":
    # 加载配置
    config = load_config()
    
    # 设置日志
    setup_logging(config)
    
    # 启动服务
    uvicorn.run(
        "src.api.main:app",
        host=config['fastapi']['host'],
        port=config['fastapi']['port'],
        reload=True,
        log_level="info"
    )