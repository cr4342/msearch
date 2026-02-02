"""
msearch主程序入口 - 单进程架构
使用线程池处理并发任务，提供API服务和文件监控
"""

import sys
import signal
import logging
from pathlib import Path
from typing import Dict, Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.config.config_manager import ConfigManager
from src.core.task.thread_pool_manager import ThreadPoolManager
from src.core.task.sqlite_task_queue import SQLiteTaskQueue
from src.api_server import create_api_server
from src.services.file.file_monitor import FileMonitor, create_file_monitor

logger = logging.getLogger(__name__)


class MSearchApplication:
    """msearch主应用程序 - 单进程架构"""

    def __init__(self, config_path: str = "config/config.yml"):
        """
        初始化应用程序

        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.config = None
        self.config_manager = None
        self.thread_pool_manager = None
        self.task_queue = None
        self.api_server = None
        self.file_monitor = None
        self.shutdown_requested = False

        # 设置信号处理器
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """信号处理器"""
        logger.info(f"接收到信号 {signum}，正在关闭应用程序...")
        self.shutdown_requested = True
        self.shutdown()
        sys.exit(0)

    def initialize(self) -> bool:
        """
        初始化应用程序

        Returns:
            bool: 初始化是否成功
        """
        try:
            # 1. 加载配置
            logger.info("加载配置...")
            self.config_manager = ConfigManager(self.config_path)
            self.config = self.config_manager.config
            logger.info("配置加载成功")

            # 2. 初始化线程池管理器
            logger.info("初始化线程池管理器...")
            thread_pools_config = self.config.get(
                "thread_pools",
                {
                    "embedding": {
                        "min_workers": 1,
                        "max_workers": 4,
                        "queue_size": 100,
                        "task_timeout": 300,
                    },
                    "io": {
                        "min_workers": 4,
                        "max_workers": 8,
                        "queue_size": 200,
                        "task_timeout": 60,
                    },
                    "task": {
                        "min_workers": 4,
                        "max_workers": 8,
                        "queue_size": 200,
                        "task_timeout": 120,
                    },
                },
            )
            self.thread_pool_manager = ThreadPoolManager(thread_pools_config)
            logger.info("线程池管理器初始化成功")

            # 3. 初始化任务队列
            logger.info("初始化任务队列...")
            task_queue_config = self.config.get(
                "task_queue",
                {"path": "data/task_queue.db", "max_size": 10000, "auto_commit": True},
            )
            self.task_queue = SQLiteTaskQueue(
                db_path=task_queue_config["path"],
                max_size=task_queue_config.get("max_size", 10000),
            )
            logger.info("任务队列初始化成功")

            # 4. 初始化文件监视器
            logger.info("初始化文件监视器...")
            file_monitor_config = self.config.get(
                "file_monitor",
                {
                    "watch_directories": ["/data/project/msearch/testdata"],
                    "debounce_interval": 500,
                    "batch_size": 100,
                    "enabled": True,
                },
            )
            self.file_monitor = create_file_monitor(file_monitor_config)
            if self.file_monitor:
                self.file_monitor.start_monitoring()
                logger.info("文件监视器初始化成功")
            else:
                logger.warning("文件监视器初始化失败，将跳过文件监控")

            # 5. 初始化API服务器
            logger.info("初始化API服务器...")
            # 使用create_api_server工厂函数创建API服务器（async函数）
            import asyncio

            async def _create_server():
                return await create_api_server("config/config.yml")

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self.api_server = loop.run_until_complete(_create_server())
            logger.info("API服务器初始化成功")

            logger.info("应用程序初始化完成")
            return True

        except Exception as e:
            logger.error(f"应用程序初始化失败: {e}", exc_info=True)
            return False

    def start(self):
        """启动应用程序"""
        if not self.initialize():
            logger.error("应用程序初始化失败，无法启动")
            return

        logger.info("启动msearch应用程序...")

        try:
            # 启动API服务器（阻塞运行）
            import uvicorn

            host = self.config.get("api", {}).get("host", "0.0.0.0")
            port = self.config.get("api", {}).get("port", 8000)

            logger.info(f"API服务器启动在 http://{host}:{port}")
            uvicorn.run(self.api_server.app, host=host, port=port, log_level="info")

        except Exception as e:
            logger.error(f"应用程序运行失败: {e}", exc_info=True)
        finally:
            self.shutdown()

    def shutdown(self):
        """关闭应用程序"""
        if self.shutdown_requested:
            return

        logger.info("正在关闭应用程序...")

        try:
            # 停止文件监视器
            if self.file_monitor:
                self.file_monitor.stop_monitoring()
                logger.info("文件监视器已停止")

            # 停止API服务器
            if self.api_server:
                # API服务器由uvicorn管理，会自动关闭
                logger.info("API服务器已停止")

            # 停止线程池
            if self.thread_pool_manager:
                self.thread_pool_manager.shutdown(wait=True)
                logger.info("线程池已停止")

            # 关闭任务队列
            if self.task_queue:
                self.task_queue.close()
                logger.info("任务队列已关闭")

            logger.info("应用程序已关闭")

        except Exception as e:
            logger.error(f"关闭应用程序时发生错误: {e}", exc_info=True)


def main():
    """主函数"""
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # 创建并启动应用程序
    app = MSearchApplication()
    app.start()


if __name__ == "__main__":
    main()
