"""
API服务器 - 单进程架构
提供RESTful API接口，使用线程池处理并发任务
"""

import os
import sys
import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod

import logging
from fastapi import FastAPI, HTTPException, Query, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入API路由
from src.api.v1.routes import router as api_v1_router


class ConfigManager(ABC):
    """配置管理器接口"""
    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        pass
    
    @property
    @abstractmethod
    def config(self) -> Dict[str, Any]:
        pass


class DatabaseManager(ABC):
    """数据库管理器接口"""
    @abstractmethod
    def get_file_info(self, file_id: str) -> Optional[Dict[str, Any]]:
        pass


class VectorStore(ABC):
    """向量存储接口"""
    @abstractmethod
    def search(self, query_vector: List[float], top_k: int = 20) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    def get_collection_stats(self) -> Dict[str, Any]:
        pass


class EmbeddingEngine(ABC):
    """向量化引擎接口"""
    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        pass
    
    @abstractmethod
    def embed_image(self, image_path: str) -> List[float]:
        pass
    
    @abstractmethod
    def embed_audio(self, audio_path: str) -> List[float]:
        pass


class TaskManager(ABC):
    """任务管理器接口"""
    @abstractmethod
    def get_task_stats(self) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        pass


class SearchEngine(ABC):
    """搜索引擎接口"""
    @abstractmethod
    async def search(self, query: str, k: int = 10, modalities: Optional[List[str]] = None, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        pass


class FileIndexer(ABC):
    """文件索引器接口"""
    @abstractmethod
    def index_file(self, file_path: str, submit_task: bool = True) -> Optional[Dict[str, Any]]:
        pass
    
    @abstractmethod
    def index_directory(self, directory: str, recursive: bool = True) -> List[Dict[str, Any]]:
        pass


class APIServer:
    """API服务器 - 使用依赖注入，适配多进程架构"""

    def __init__(
        self,
        config: ConfigManager,
        database_manager: DatabaseManager,
        vector_store: VectorStore,
        embedding_engine: EmbeddingEngine,
        task_manager: TaskManager,
        search_engine: SearchEngine,
        file_indexer: FileIndexer
    ):
        """
        初始化API服务器（使用依赖注入）
        
        Args:
            config: 配置管理器
            database_manager: 数据库管理器
            vector_store: 向量存储
            embedding_engine: 向量化引擎
            task_manager: 任务管理器
            search_engine: 搜索引擎
            file_indexer: 文件索引器
        """
        self.config = config
        self.database_manager = database_manager
        self.vector_store = vector_store
        self.embedding_engine = embedding_engine
        self.task_manager = task_manager
        self.search_engine = search_engine
        self.file_indexer = file_indexer
        
        # 创建FastAPI应用
        self.app = FastAPI(
            title="msearch API",
            description="多模态检索系统API（多进程架构）",
            version="2.0.0",
            docs_url="/docs",
            redoc_url="/redoc"
        )
        
        # 配置CORS
        api_config = self.config.get('api', {})
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=api_config.get('cors_origins', ['*']),
            allow_credentials=True,
            allow_methods=['*'],
            allow_headers=['*'],
        )
        
        # 注册路由
        # 设置APIServer实例到routes模块
        from src.api.v1 import routes
        routes.set_api_server_instance(self)
        
        self.app.include_router(api_v1_router)
        
        # 注册根路由
        @self.app.get("/")
        async def root():
            return {
                "service": "msearch API Server",
                "version": "2.0.0 (Multiprocess Architecture)",
                "status": "running",
                "docs": "/docs",
                "redoc": "/redoc",
                "components": {
                    "main_process": True,
                    "sub_processes": await get_subprocess_status()
                }
            }
        
        # 添加启动事件
        @self.app.on_event("startup")
        async def startup_event():
            """启动事件：执行初始文件扫描和索引"""
            self.logger.info("API服务器启动事件：开始执行初始文件扫描和索引")
            
            # 异步执行初始扫描，避免阻塞启动
            import asyncio
            asyncio.create_task(self._perform_initial_scan())
        
        # 初始化日志
        self._init_logging()
        
        # 注册其他路由
        self._register_routes()
        
        self.logger = logging.getLogger('api_server')
        self.logger.info("API服务器初始化完成（多进程架构）")
    
    async def _perform_initial_scan(self):
        """执行初始文件扫描和索引"""
        try:
            import os
            import fnmatch
            
            self.logger.info("开始执行初始文件扫描...")
            
            # 获取监视目录配置
            file_monitor_config = self.config.get('file_monitor', {})
            watch_directories = file_monitor_config.get('watch_directories', [])
            
            if not watch_directories:
                self.logger.warning("未配置监视目录，跳过初始扫描")
                return
            
            self.logger.info(f"监视目录: {watch_directories}")
            
            # 扫描所有监视目录
            total_files = 0
            indexed_files = 0
            
            for watch_dir in watch_directories:
                if not os.path.exists(watch_dir):
                    self.logger.warning(f"监视目录不存在: {watch_dir}")
                    continue
                
                self.logger.info(f"扫描目录: {watch_dir}")
                
                # 扫描目录中的文件
                
                supported_extensions = file_monitor_config.get('supported_extensions', [
                    '.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp',
                    '.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv',
                    '.mp3', '.wav', '.aac', '.flac', '.ogg', '.m4a'
                ])
                
                for root, dirs, files in os.walk(watch_dir):
                    # 跳过忽略的目录
                    ignore_patterns = file_monitor_config.get('ignore_patterns', [])
                    dirs[:] = [d for d in dirs if not any(fnmatch.fnmatch(d, pattern) for pattern in ignore_patterns)]
                    
                    for filename in files:
                        file_path = os.path.join(root, filename)
                        file_ext = os.path.splitext(filename)[1].lower()
                        
                        if file_ext in supported_extensions:
                            total_files += 1
                            
                            try:
                                # 索引文件
                                self.logger.info(f"索引文件: {file_path}")
                                result = self.file_indexer.index_file(file_path, submit_task=False)
                                
                                if result is not None:
                                    indexed_files += 1
                                    self.logger.info(f"✓ 索引成功: {file_path}")
                                    
                                    # 直接执行向量化
                                    try:
                                        self.logger.info(f"开始向量化: {file_path}")
                                        
                                        # 根据文件类型选择向量化方法
                                        file_ext = os.path.splitext(filename)[1].lower()
                                        
                                        if file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp']:
                                            # 图像向量化
                                            vector = await self.embedding_engine.embed_image(file_path)
                                            modality = 'image'
                                        elif file_ext in ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv']:
                                            # 视频向量化
                                            vector = await self.embedding_engine.embed_video_segment(file_path)
                                            modality = 'video'
                                        elif file_ext in ['.mp3', '.wav', '.aac', '.flac', '.ogg', '.m4a']:
                                            # 音频向量化
                                            vector = await self.embedding_engine.embed_audio(file_path)
                                            modality = 'audio'
                                        else:
                                            # 未知类型，跳过
                                            self.logger.warning(f"未知文件类型: {file_path}")
                                            continue
                                        
                                        # 将向量存储到数据库
                                        vector_data = {
                                            'id': result.id,
                                            'vector': vector,
                                            'file_id': result.id,
                                            'file_path': file_path,
                                            'file_name': filename,
                                            'modality': modality,
                                            'metadata': result.to_dict(),
                                            'segment_id': 'full',
                                            'start_time': 0.0,
                                            'end_time': 0.0,
                                            'is_full_video': True,
                                            'created_at': result.created_at
                                        }
                                        self.vector_store.add_vector(vector_data)
                                        
                                        self.logger.info(f"✓ 向量化成功: {file_path}")
                                        
                                    except Exception as embed_error:
                                        self.logger.error(f"向量化失败 {file_path}: {embed_error}")
                                        import traceback
                                        traceback.print_exc()
                                else:
                                    self.logger.warning(f"✗ 索引失败: {file_path}")
                                    
                            except Exception as e:
                                self.logger.error(f"索引文件失败 {file_path}: {e}")
            
            self.logger.info(f"初始扫描完成: 总文件数={total_files}, 索引文件数={indexed_files}")
            
        except Exception as e:
            self.logger.error(f"初始扫描失败: {e}")
            import traceback
            traceback.print_exc()

    def _init_logging(self) -> None:
        """初始化日志"""
        log_config = self.config.get('logging', {})
        log_level = log_config.get('level', 'INFO')

        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    def _register_routes(self) -> None:
        """注册路由"""
        
        @self.app.get("/api/v1/health")
        async def health_check():
            """健康检查"""
            return JSONResponse({
                "status": "healthy",
                "components": {
                    "database": "ok",
                    "vector_store": "ok",
                    "embedding_engine": "ok",
                    "task_manager": "ok",
                    "sub_processes": await get_subprocess_status()
                }
            })

        @self.app.get("/api/v1/system/info")
        async def system_info():
            """系统信息"""
            return JSONResponse({
                "status": "ok",
                "architecture": "multiprocess",
                "config": {
                    "model": self.config.get('models.available_models.chinese_clip_large.model_name', 'unknown'),
                    "device": self.config.get('models.available_models.chinese_clip_large.device', 'unknown'),
                    "embedding_dim": self.config.get('models.available_models.chinese_clip_large.embedding_dim', 512)
                },
                "processes": await get_subprocess_status()
            })

        @self.app.post("/api/v1/search/text")
        async def search_text(
            query: str = Form(...),
            top_k: int = Form(20),
            threshold: Optional[float] = Form(None)
        ):
            """文本搜索"""
            try:
                # 向量化查询 - 通过任务系统分发到向量化工作进程
                query_vector = await self.embedding_engine.embed_text(query)
                
                # 搜索
                results = self.vector_store.search_vectors(query_vector, top_k, similarity_threshold=threshold)
                
                return JSONResponse({
                    "query": query,
                    "results": results,
                    "total": len(results)
                })
            except Exception as e:
                self.logger.error(f"文本搜索失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/v1/search/image")
        async def search_image(
            image: UploadFile = File(...),
            top_k: int = Form(20)
        ):
            """图像搜索"""
            try:
                # 保存上传的图像
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
                    content = await image.read()
                    tmp_file.write(content)
                    tmp_path = tmp_file.name
                
                # 向量化图像 - 通过任务系统分发到向量化工作进程
                query_vector = await self.embedding_engine.embed_image(tmp_path)
                
                # 搜索
                results = self.vector_store.search_vectors(query_vector, top_k)
                
                # 清理临时文件
                os.unlink(tmp_path)
                
                return JSONResponse({
                    "image": image.filename,
                    "results": results,
                    "total": len(results)
                })
            except Exception as e:
                self.logger.error(f"图像搜索失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/v1/search/audio")
        async def search_audio(
            audio: UploadFile = File(...),
            top_k: int = Form(20)
        ):
            """音频搜索"""
            try:
                # 保存上传的音频
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                    content = await audio.read()
                    tmp_file.write(content)
                    tmp_path = tmp_file.name
                
                # 向量化音频 - 通过任务系统分发到向量化工作进程
                query_vector = await self.embedding_engine.embed_audio(tmp_path)
                
                # 搜索
                results = self.vector_store.search_vectors(query_vector, top_k)
                
                # 清理临时文件
                os.unlink(tmp_path)
                
                return JSONResponse({
                    "audio": audio.filename,
                    "results": results,
                    "total": len(results)
                })
            except Exception as e:
                self.logger.error(f"音频搜索失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/v1/tasks/stats")
        async def task_stats():
            """任务统计"""
            try:
                stats = self.task_manager.get_statistics()
                return JSONResponse(stats)
            except Exception as e:
                self.logger.error(f"获取任务统计失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/v1/tasks/{task_id}")
        async def get_task(task_id: str):
            """获取任务详情"""
            try:
                task = self.task_manager.get_task_status(task_id)
                if not task:
                    raise HTTPException(status_code=404, detail="任务不存在")
                return JSONResponse(task)
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"获取任务详情失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/v1/tasks")
        async def get_all_tasks(status: Optional[str] = None, task_type: Optional[str] = None):
            """获取所有任务"""
            try:
                tasks = self.task_manager.get_all_tasks(status=status, task_type=task_type)
                return JSONResponse({
                    'total': len(tasks),
                    'tasks': tasks
                })
            except Exception as e:
                self.logger.error(f"获取所有任务失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/v1/tasks/{task_id}/cancel")
        async def cancel_task(task_id: str):
            """取消任务"""
            try:
                success = self.task_manager.cancel_task(task_id)
                if success:
                    return JSONResponse({
                        'success': True,
                        'message': f'任务已取消: {task_id}'
                    })
                else:
                    raise HTTPException(status_code=404, detail='任务不存在或无法取消')
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"取消任务失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/v1/tasks/{task_id}/priority")
        async def update_task_priority(task_id: str, priority: int = Form(...)):
            """更新任务优先级"""
            try:
                success = self.task_manager.update_task_priority(task_id, priority)
                if success:
                    return JSONResponse({
                        'success': True,
                        'message': f'任务优先级已更新: {task_id} -> {priority}'
                    })
                else:
                    raise HTTPException(status_code=404, detail='任务不存在')
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"更新任务优先级失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/v1/tasks/cancel-all")
        async def cancel_all_tasks(cancel_running: bool = Form(False)):
            """取消所有任务"""
            try:
                result = self.task_manager.cancel_all_tasks(cancel_running=cancel_running)
                return JSONResponse({
                    'success': True,
                    'message': f'已取消{result["cancelled"]}个任务',
                    'result': result
                })
            except Exception as e:
                self.logger.error(f"取消所有任务失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/v1/tasks/cancel-by-type")
        async def cancel_tasks_by_type(task_type: str = Form(...), cancel_running: bool = Form(False)):
            """按类型取消任务"""
            try:
                result = self.task_manager.cancel_tasks_by_type(task_type, cancel_running=cancel_running)
                return JSONResponse({
                    'success': True,
                    'message': f'已取消{result["cancelled"]}个{task_type}任务',
                    'result': result
                })
            except Exception as e:
                self.logger.error(f"按类型取消任务失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/v1/vector/stats")
        async def vector_stats():
            """向量统计"""
            try:
                stats = self.vector_store.get_collection_stats()
                return JSONResponse(stats)
            except Exception as e:
                self.logger.error(f"获取向量统计失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        async def get_subprocess_status():
            """获取线程池状态"""
            # 在单进程架构中，获取线程池状态
            try:
                if hasattr(self, 'thread_pool_manager') and self.thread_pool_manager:
                    return self.thread_pool_manager.get_statistics()
                else:
                    # 如果没有thread_pool_manager，返回空状态
                    return {"status": "no_thread_pool_manager"}
            except Exception as e:
                self.logger.error(f"获取线程池状态失败: {e}")
                return {"error": str(e)}

        print("路由注册完成")


async def create_api_server(config_path: Optional[str] = None) -> APIServer:
    """
    创建APIServer实例
    
    Args:
        config_path: 配置文件路径
    
    Returns:
        APIServer实例
    """
    # 导入实际实现
    from src.core.config.config_manager import ConfigManager as ConfigManagerImpl
    from src.core.database.database_manager import DatabaseManager as DatabaseManagerImpl
    from src.core.vector.vector_store import VectorStore as VectorStoreImpl
    from src.core.embedding.embedding_engine import EmbeddingEngine as EmbeddingEngineImpl
    from src.core.task.central_task_manager import CentralTaskManager as TaskManagerImpl
    from src.core.task.task_scheduler import TaskScheduler
    from src.core.task.task_executor import OptimizedTaskExecutor
    from src.core.task.task_monitor import OptimizedTaskMonitor
    from src.core.task.group_manager import OptimizedGroupManager
    from src.services.search.search_engine import SearchEngine as SearchEngineImpl
    from src.services.file.file_indexer import FileIndexer as FileIndexerImpl
    
    # 创建配置管理器
    if config_path:
        config = ConfigManagerImpl(config_path=config_path)
    else:
        config = ConfigManagerImpl()
    
    # 创建数据库管理器
    db_path = config.config.get('database', {}).get('metadata_db_path', 'data/database/sqlite/msearch.db')
    database_manager = DatabaseManagerImpl(db_path)
    
    # 创建向量存储
    vector_store = VectorStoreImpl(config.config)
    
    # 创建向量化引擎
    embedding_engine = EmbeddingEngineImpl(config.config)
    await embedding_engine.initialize()
    
    # 获取设备配置
    device = config.config.get('device', 'cpu')
    
    # 创建任务管理器的依赖组件
    task_scheduler = TaskScheduler(config.config)
    task_executor = OptimizedTaskExecutor()
    task_monitor = OptimizedTaskMonitor()
    task_group_manager = OptimizedGroupManager()
    
    # 创建任务管理器
    task_manager = TaskManagerImpl(
        config=config.config,
        task_scheduler=task_scheduler,
        task_executor=task_executor,
        task_monitor=task_monitor,
        task_group_manager=task_group_manager,
        device=device
    )
    task_manager.start()
    
    # 创建搜索引擎
    search_engine = SearchEngineImpl(
        embedding_engine=embedding_engine,
        vector_store=vector_store
    )
    search_engine.initialize()
    
    # 创建文件索引器
    file_indexer = FileIndexerImpl(
        config=config.config,
        task_manager=task_manager
    )
    # 将依赖传递给file_indexer
    file_indexer.vector_store = vector_store
    file_indexer.embedding_engine = embedding_engine
    
    # 创建API服务器实例
    api_server = APIServer(
        config=config,
        database_manager=database_manager,
        vector_store=vector_store,
        embedding_engine=embedding_engine,
        task_manager=task_manager,
        search_engine=search_engine,
        file_indexer=file_indexer
    )
    
    return api_server


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='msearch API服务器（多进程架构）')
    parser.add_argument('--config', type=str, help='配置文件路径')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='主机地址')
    parser.add_argument('--port', type=int, default=8000, help='端口号')
    
    args = parser.parse_args()
    
    # 创建API服务器
    api_server = await create_api_server(args.config)
    
    # 启动服务器
    import uvicorn
    config = uvicorn.Config(app=api_server.app, host=args.host, port=args.port)
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == '__main__':
    asyncio.run(main())