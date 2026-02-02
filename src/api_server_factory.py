"""
API服务器工厂
创建API服务器实例及其所有依赖
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.config.config_manager import ConfigManager
from src.core.database.database_manager import DatabaseManager
from src.core.vector.vector_store import VectorStore
from src.core.embedding.embedding_engine import EmbeddingEngine
from src.core.task.central_task_manager import CentralTaskManager
from src.services.search.search_engine import SearchEngine
from src.services.file.file_indexer import FileIndexer
from src.api_server import APIServer


def create_api_server(config_path: str = "config/config.yml") -> APIServer:
    """
    创建API服务器实例

    Args:
        config_path: 配置文件路径

    Returns:
        API服务器实例
    """
    # 1. 创建配置管理器
    config_manager = ConfigManager(config_path=config_path)

    # 2. 创建数据库管理器
    database_manager = DatabaseManager(config_manager.config)

    # 3. 创建向量存储
    vector_store = VectorStore(config_manager.config)

    # 4. 创建向量化引擎
    embedding_engine = EmbeddingEngine(config_manager.config)

    # 5. 创建任务管理器
    device = config_manager.config.get("models", {}).get("device", "cpu")
    task_manager = CentralTaskManager(config_manager.config, device)
    task_manager.initialize()

    # 6. 创建搜索引擎
    search_engine = SearchEngine(
        embedding_engine=embedding_engine,
        vector_store=vector_store,
        config=config_manager.config.get("search", {}),
    )
    search_engine.initialize()

    # 7. 创建文件索引器
    file_indexer = FileIndexer(config=config_manager.config, task_manager=task_manager)
    # 将依赖传递给file_indexer
    file_indexer.vector_store = vector_store
    file_indexer.embedding_engine = embedding_engine

    # 8. 创建API服务器
    api_server = APIServer(
        config=config_manager,
        database_manager=database_manager,
        vector_store=vector_store,
        embedding_engine=embedding_engine,
        task_manager=task_manager,
        search_engine=search_engine,
        file_indexer=file_indexer,
    )

    return api_server


if __name__ == "__main__":
    # 测试工厂函数
    api_server = create_api_server()
    print("API服务器创建成功")
