import asyncio
import logging
import signal
import sys
from typing import List

from src.core.task_manager import TaskManager
from src.core.embedding_engine import EmbeddingEngine
from src.core.vector_store import VectorStore
from src.core.config_manager import ConfigManager
from src.core.infinity_manager import InfinityManager
from src.components.database_manager import DatabaseManager
from src.components.search_engine import SearchEngine

class MSearchApp:
    """msearch主应用"""
    
    def __init__(self):
        self.config_manager = ConfigManager('config/config.yml')
        self.logger = logging.getLogger(__name__)
        
        # 初始化组件
        self.database_manager = DatabaseManager(self.config_manager)
        self.infinity_manager = InfinityManager(self.config_manager)
        self.vector_store = VectorStore(self.config_manager)
        self.embedding_engine = EmbeddingEngine(self.config_manager)
        self.search_engine = SearchEngine(
            self.config_manager,
            self.vector_store,
            self.embedding_engine,
            self.database_manager
        )
        self.task_manager = TaskManager(
            self.config_manager,
            self.database_manager,
            self.vector_store,
            self.embedding_engine
        )
        
        # 运行状态
        self.is_running = False
        
        self.logger.info("msearch应用初始化完成")
    
    async def start(self):
        """启动应用"""
        self.logger.info("启动msearch应用")
        
        try:
            # 启动数据库管理器
            await self.database_manager.start()
            
            # 启动向量存储
            await self.vector_store.start()
            
            # 启动Infinity管理器
            await self.infinity_manager.start()
            
            # 启动向量化引擎
            await self.embedding_engine.start()
            
            # 启动任务管理器
            await self.task_manager.start()
            
            self.is_running = True
            self.logger.info("msearch应用启动完成")
        except Exception as e:
            self.logger.error(f"应用启动失败: {e}")
            raise
    
    async def stop(self):
        """停止应用"""
        self.logger.info("停止msearch应用")
        
        # 停止任务管理器
        await self.task_manager.stop()
        
        # 停止向量化引擎（内部会停止 InfinityManager）
        await self.embedding_engine.stop()
        
        # 停止向量存储
        await self.vector_store.stop()
        
        # 停止数据库管理器
        await self.database_manager.stop()
        
        self.is_running = False
        self.logger.info("msearch应用已停止")
    
    async def run_indexing_workflow(self, file_paths: List[str]):
        """运行索引工作流程"""
        if not self.is_running:
            raise RuntimeError("应用未启动")
        
        self.logger.info(f"开始索引 {len(file_paths)} 个文件")
        
        # 为每个文件创建任务
        task_ids = []
        for file_path in file_paths:
            task_id = await self.task_manager.create_task(file_path, 'index')
            task_ids.append(task_id)
        
        self.logger.info(f"创建了 {len(task_ids)} 个索引任务")
        
        # 等待任务完成
        while True:
            completed = 0
            for task_id in task_ids:
                task_info = await self.task_manager.get_task_progress(task_id)
                if task_info.get('status') in ['COMPLETED', 'FAILED']:
                    completed += 1
            
            if completed == len(task_ids):
                break
            
            self.logger.info(f"任务进度: {completed}/{len(task_ids)}")
            await asyncio.sleep(1)
    
    async def run_search_workflow(self, query: str):
        """运行搜索工作流程"""
        if not self.is_running:
            raise RuntimeError("应用未启动")
        
        self.logger.info(f"搜索查询: {query}")
        
        # 执行多模态搜索
        results = await self.search_engine.search_multimodal(query)
        
        self.logger.info(f"找到 {len(results)} 个结果")
        return results


async def main():
    """主函数"""
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    app = MSearchApp()
    
    # 注册信号处理器用于优雅关闭
    def signal_handler():
        asyncio.create_task(app.stop())
    
    signal.signal(signal.SIGINT, lambda s, f: signal_handler())
    signal.signal(signal.SIGTERM, lambda s, f: signal_handler())
    
    try:
        # 启动应用
        await app.start()
        
        # 示例：运行一些基本操作
        print("msearch应用运行中...")
        print("3大核心块已启动:")
        print("- 核心块1: 任务管理器 (TaskManager)")
        print("- 核心块2: 向量化引擎 (EmbeddingEngine)") 
        print("- 核心块3: 向量存储 (VectorStore)")
        
        # 这里可以添加实际的索引或搜索操作
        # 例如:
        # await app.run_indexing_workflow(['/path/to/media/files'])
        # await app.run_search_workflow('搜索查询')
        
        # 保持应用运行
        while app.is_running:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("\n收到中断信号，正在关闭...")
    except Exception as e:
        print(f"应用运行出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await app.stop()
        print("应用已关闭")


if __name__ == "__main__":
    asyncio.run(main())