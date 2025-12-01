"""
FastAPI应用实例
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.core.config_manager import get_config_manager
from src.core.logging_config import setup_logging
from src.search_service.smart_retrieval_engine import SmartRetrievalEngine
from src.processing_service.orchestrator import ProcessingOrchestrator
from src.processing_service.file_monitor import FileMonitor


# 全局组件实例
retrieval_engine: SmartRetrievalEngine = None
orchestrator: ProcessingOrchestrator = None
file_monitor: FileMonitor = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global retrieval_engine, orchestrator, file_monitor
    
    logger = logging.getLogger(__name__)
    
    # 启动时初始化
    logger.info("启动 msearch API 服务")
    
    try:
        # 初始化配置管理器
        config_manager = get_config_manager()
        
        # 初始化核心组件
        retrieval_engine = SmartRetrievalEngine(config_manager)
        orchestrator = ProcessingOrchestrator(config_manager)
        file_monitor = FileMonitor(config_manager)
        
        # 启动组件
        await retrieval_engine.start()
        await orchestrator.start()
        await file_monitor.start()
        
        # 将组件添加到应用状态
        app.state.retrieval_engine = retrieval_engine
        app.state.orchestrator = orchestrator
        app.state.file_monitor = file_monitor
        
        logger.info("msearch API 服务启动完成")
        
        yield
        
    except Exception as e:
        logger.error(f"API 服务启动失败: {e}")
        raise
    
    finally:
        # 关闭时清理
        logger.info("关闭 msearch API 服务")
        
        if file_monitor:
            await file_monitor.stop()
        if orchestrator:
            await orchestrator.stop()
        if retrieval_engine:
            await retrieval_engine.stop()
        
        logger.info("msearch API 服务已关闭")


def create_app() -> FastAPI:
    """创建FastAPI应用"""
    # 设置日志
    setup_logging("INFO")
    logger = logging.getLogger(__name__)
    
    # 创建FastAPI应用
    app = FastAPI(
        title="msearch 多模态检索系统",
        description="支持文本、图像、视频、音频的多模态智能检索系统",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # 配置CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 生产环境应该限制具体域名
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 注册异常处理器
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        logger.error(f"全局异常: {exc}")
        return JSONResponse(
            status_code=500,
            content={
                "error": "内部服务器错误",
                "message": str(exc),
                "type": type(exc).__name__
            }
        )
    
    # 注册路由
    from .routes.search import router as search_router
    from .routes.config import router as config_router
    from .routes.status import router as status_router
    from .routes.tasks import router as tasks_router
    
    app.include_router(search_router, prefix="/api", tags=["检索"])
    app.include_router(config_router, prefix="/api", tags=["配置"])
    app.include_router(status_router, prefix="/api", tags=["状态"])
    app.include_router(tasks_router, prefix="/api", tags=["任务"])
    
    # 健康检查端点
    @app.get("/health")
    async def health_check():
        """健康检查"""
        return {"status": "healthy", "message": "msearch API 服务运行正常"}
    
    return app


# 创建应用实例
app = create_app()