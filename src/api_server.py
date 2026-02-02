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
    def search(
        self, query_vector: List[float], top_k: int = 20
    ) -> List[Dict[str, Any]]:
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
    async def search(
        self,
        query: str,
        k: int = 10,
        modalities: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        pass


class FileIndexer(ABC):
    """文件索引器接口"""

    @abstractmethod
    def index_file(
        self, file_path: str, submit_task: bool = True
    ) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def index_directory(
        self, directory: str, recursive: bool = True
    ) -> List[Dict[str, Any]]:
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
        file_indexer: FileIndexer,
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
            redoc_url="/redoc",
        )

        # 配置CORS
        api_config = self.config.get("api", {})
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=api_config.get("cors_origins", ["*"]),
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
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
                    "sub_processes": await get_subprocess_status(),
                },
            }

        # 添加启动事件
        @self.app.on_event("startup")
        async def startup_event():
            """启动事件：启动文件监控和执行初始文件扫描"""
            self.logger.info("API服务器启动事件：开始启动服务")

            # 启动文件监控器
            await self._start_file_monitor()

            # 异步执行初始扫描，避免阻塞启动
            import asyncio

            asyncio.create_task(self._perform_initial_scan())

        # 添加关闭事件
        @self.app.on_event("shutdown")
        async def shutdown_event():
            """关闭事件：停止文件监控器"""
            self.logger.info("API服务器关闭事件：停止服务")
            await self._stop_file_monitor()

        # 初始化日志
        self._init_logging()

        # 注册其他路由（已废弃，使用新的路由系统）
        # self._register_routes()

        # 初始化文件监控器
        self.file_monitor = None

        self.logger = logging.getLogger("api_server")
        self.logger.info("API服务器初始化完成（多进程架构）")

    async def _start_file_monitor(self):
        """启动文件监控器"""
        try:
            from src.services.file.file_monitor import create_file_monitor

            self.logger.info("正在启动文件监控器...")

            # 创建文件监控器
            self.file_monitor = create_file_monitor(self.config.config)

            # 注册文件监控事件处理器
            self.file_monitor.register_event_handler("created", self._on_file_created)
            self.file_monitor.register_event_handler("modified", self._on_file_modified)
            self.file_monitor.register_event_handler("deleted", self._on_file_deleted)

            # 添加监控目录
            file_monitor_config = self.config.get("file_monitor", {})
            watch_directories = file_monitor_config.get("watch_directories", [])

            for directory in watch_directories:
                if os.path.exists(directory):
                    self.file_monitor.add_directory(directory)
                    self.logger.info(f"已添加监控目录: {directory}")
                else:
                    self.logger.warning(f"监控目录不存在: {directory}")

            # 启动监控
            if self.file_monitor.start_monitoring():
                self.logger.info("✓ 文件监控器启动成功")
            else:
                self.logger.error("✗ 文件监控器启动失败")

        except Exception as e:
            self.logger.error(f"启动文件监控器失败: {e}")
            import traceback

            traceback.print_exc()

    async def _stop_file_monitor(self):
        """停止文件监控器"""
        try:
            if self.file_monitor:
                self.logger.info("正在停止文件监控器...")
                if self.file_monitor.stop_monitoring():
                    self.logger.info("✓ 文件监控器已停止")
                else:
                    self.logger.error("✗ 文件监控器停止失败")
        except Exception as e:
            self.logger.error(f"停止文件监控器失败: {e}")

    def _on_file_created(self, event_type: str, file_path: str):
        """
        文件创建事件处理器

        Args:
            event_type: 事件类型
            file_path: 文件路径
        """
        try:
            self.logger.info(f"[文件监控] 检测到新文件: {file_path}")

            # 创建索引任务
            task_id = self.task_manager.create_task(
                task_type="file_scan", task_data={"file_path": file_path}, priority=5
            )

            self.logger.info(f"[文件监控] 已创建索引任务: {task_id} -> {file_path}")

        except Exception as e:
            self.logger.error(
                f"[文件监控] 处理文件创建事件失败: {file_path}, 错误: {e}"
            )

    def _on_file_modified(self, event_type: str, file_path: str):
        """
        文件修改事件处理器

        Args:
            event_type: 事件类型
            file_path: 文件路径
        """
        try:
            self.logger.info(f"[文件监控] 检测到文件修改: {file_path}")

            # 创建重新索引任务
            task_id = self.task_manager.create_task(
                task_type="file_scan",
                task_data={"file_path": file_path, "reindex": True},
                priority=5,
            )

            self.logger.info(f"[文件监控] 已创建重新索引任务: {task_id} -> {file_path}")

        except Exception as e:
            self.logger.error(
                f"[文件监控] 处理文件修改事件失败: {file_path}, 错误: {e}"
            )

    def _on_file_deleted(self, event_type: str, file_path: str):
        """
        文件删除事件处理器

        Args:
            event_type: 事件类型
            file_path: 文件路径
        """
        try:
            self.logger.info(f"[文件监控] 检测到文件删除: {file_path}")
            # 文件删除事件暂时不处理，后续可以添加删除索引的逻辑
        except Exception as e:
            self.logger.error(
                f"[文件监控] 处理文件删除事件失败: {file_path}, 错误: {e}"
            )

    async def _perform_initial_scan(self):
        """执行初始文件扫描和索引"""
        try:
            import os
            import fnmatch

            self.logger.info("开始执行初始文件扫描...")

            # 获取监视目录配置
            file_monitor_config = self.config.get("file_monitor", {})
            watch_directories = file_monitor_config.get("watch_directories", [])

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

                supported_extensions = file_monitor_config.get(
                    "supported_extensions",
                    [
                        ".jpg",
                        ".jpeg",
                        ".png",
                        ".bmp",
                        ".gif",
                        ".webp",
                        ".mp4",
                        ".avi",
                        ".mov",
                        ".mkv",
                        ".wmv",
                        ".flv",
                        ".mp3",
                        ".wav",
                        ".aac",
                        ".flac",
                        ".ogg",
                        ".m4a",
                    ],
                )

                for root, dirs, files in os.walk(watch_dir):
                    # 跳过忽略的目录
                    ignore_patterns = file_monitor_config.get("ignore_patterns", [])
                    dirs[:] = [
                        d
                        for d in dirs
                        if not any(
                            fnmatch.fnmatch(d, pattern) for pattern in ignore_patterns
                        )
                    ]

                    for filename in files:
                        file_path = os.path.join(root, filename)
                        file_ext = os.path.splitext(filename)[1].lower()

                        if file_ext in supported_extensions:
                            total_files += 1

                            try:
                                # 索引文件
                                self.logger.info(f"索引文件: {file_path}")
                                result = self.file_indexer.index_file(
                                    file_path, submit_task=False
                                )

                                if result is not None:
                                    indexed_files += 1
                                    self.logger.info(f"✓ 索引成功: {file_path}")

                                    # 直接执行向量化
                                    try:
                                        self.logger.info(f"开始向量化: {file_path}")

                                        # 根据文件类型选择向量化方法
                                        file_ext = os.path.splitext(filename)[1].lower()

                                        if file_ext in [
                                            ".jpg",
                                            ".jpeg",
                                            ".png",
                                            ".bmp",
                                            ".gif",
                                            ".webp",
                                        ]:
                                            # 图像向量化
                                            vector = (
                                                await self.embedding_engine.embed_image(
                                                    file_path
                                                )
                                            )
                                            modality = "image"
                                        elif file_ext in [
                                            ".mp4",
                                            ".avi",
                                            ".mov",
                                            ".mkv",
                                            ".wmv",
                                            ".flv",
                                        ]:
                                            # 视频向量化
                                            vector = await self.embedding_engine.embed_video_segment(
                                                file_path
                                            )
                                            modality = "video"
                                        elif file_ext in [
                                            ".mp3",
                                            ".wav",
                                            ".aac",
                                            ".flac",
                                            ".ogg",
                                            ".m4a",
                                        ]:
                                            # 音频向量化
                                            vector = (
                                                await self.embedding_engine.embed_audio(
                                                    file_path
                                                )
                                            )
                                            modality = "audio"
                                        else:
                                            # 未知类型，跳过
                                            self.logger.warning(
                                                f"未知文件类型: {file_path}"
                                            )
                                            continue

                                        # 将向量存储到数据库
                                        vector_data = {
                                            "id": result.id,
                                            "vector": vector,
                                            "file_id": result.id,
                                            "file_path": file_path,
                                            "file_name": filename,
                                            "modality": modality,
                                            "metadata": result.to_dict(),
                                            "segment_id": "full",
                                            "start_time": 0.0,
                                            "end_time": 0.0,
                                            "is_full_video": True,
                                            "created_at": result.created_at,
                                        }
                                        self.vector_store.add_vector(vector_data)

                                        self.logger.info(f"✓ 向量化成功: {file_path}")

                                    except Exception as embed_error:
                                        self.logger.error(
                                            f"向量化失败 {file_path}: {embed_error}"
                                        )
                                        import traceback

                                        traceback.print_exc()
                                else:
                                    self.logger.warning(f"✗ 索引失败: {file_path}")

                            except Exception as e:
                                self.logger.error(f"索引文件失败 {file_path}: {e}")

            self.logger.info(
                f"初始扫描完成: 总文件数={total_files}, 索引文件数={indexed_files}"
            )

        except Exception as e:
            self.logger.error(f"初始扫描失败: {e}")
            import traceback

            traceback.print_exc()

    def _init_logging(self) -> None:
        """初始化日志"""
        log_config = self.config.get("logging", {})
        log_level = log_config.get("level", "INFO")

        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    def _register_routes(self) -> None:
        """注册路由（已废弃，使用新的路由系统）"""
        pass

    async def get_subprocess_status():
        """获取线程池状态"""
        # 在单进程架构中，获取线程池状态
        try:
            return {"status": "single_process_mode"}
        except Exception as e:
            return {"error": str(e)}


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
    from src.core.database.database_manager import (
        DatabaseManager as DatabaseManagerImpl,
    )
    from src.core.vector.vector_store import VectorStore as VectorStoreImpl
    from src.core.embedding.embedding_engine import (
        EmbeddingEngine as EmbeddingEngineImpl,
    )
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
    db_path = config.config.get("database", {}).get(
        "metadata_db_path", "data/database/sqlite/msearch.db"
    )
    database_manager = DatabaseManagerImpl(db_path)

    # 创建向量存储
    vector_store = VectorStoreImpl(config.config)

    # 创建向量化引擎
    embedding_engine = EmbeddingEngineImpl(config.config)
    await embedding_engine.initialize()

    # 获取设备配置
    device = config.config.get("device", "cpu")

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
        device=device,
    )
    task_manager.start()

    # 创建搜索引擎
    search_engine = SearchEngineImpl(
        embedding_engine=embedding_engine, vector_store=vector_store
    )
    search_engine.initialize()

    # 创建文件索引器
    file_indexer = FileIndexerImpl(config=config.config, task_manager=task_manager)
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
        file_indexer=file_indexer,
    )

    return api_server


async def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="msearch API服务器（多进程架构）")
    parser.add_argument("--config", type=str, help="配置文件路径")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="主机地址")
    parser.add_argument("--port", type=int, default=8000, help="端口号")

    args = parser.parse_args()

    # 创建API服务器
    api_server = await create_api_server(args.config)

    # 启动服务器
    import uvicorn

    config = uvicorn.Config(app=api_server.app, host=args.host, port=args.port)
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
