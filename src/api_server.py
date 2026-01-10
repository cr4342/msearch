"""
API服务器
提供RESTful API接口
"""

from fastapi import FastAPI, HTTPException, Query, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Any, Dict, List, Optional
import logging
from pathlib import Path
import sys

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.config import ConfigManager
from src.core.database_manager import DatabaseManager
from src.core.vector_store import VectorStore
from src.core.embedding_engine import EmbeddingEngine
from src.core.hardware_detector import HardwareDetector
from src.core.task_manager import TaskManager

logger = logging.getLogger(__name__)


class APIServer:
    """API服务器"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化API服务器
        
        Args:
            config_path: 配置文件路径
        """
        # 初始化配置
        if config_path:
            self.config = ConfigManager(config_file=config_path)
        else:
            self.config = ConfigManager()
        
        # 初始化日志
        self._init_logging()
        
        # 初始化FastAPI应用
        self.app = FastAPI(
            title="msearch API",
            description="多模态检索系统API",
            version="1.0.0"
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
        
        # 初始化组件
        self.components = {}
        self._initialize_components()
        
        # 注册路由
        self._register_routes()
        
        logger.info("API服务器初始化完成")
    
    def _init_logging(self) -> None:
        """初始化日志"""
        log_config = self.config.get('logging', {})
        log_level = log_config.get('level', 'INFO')
        
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def _initialize_components(self) -> None:
        """初始化组件"""
        try:
            # 硬件检测器
            self.components['hardware_detector'] = HardwareDetector()
            logger.info("硬件检测器初始化完成")
            
            # 数据库管理器
            db_config = self.config.get('database', {})
            db_path = db_config.get('sqlite_path', 'data/database/sqlite/msearch.db')
            self.components['database_manager'] = DatabaseManager(db_path)
            logger.info("数据库管理器初始化完成")
            
            # 向量存储
            self.components['vector_store'] = VectorStore(self.config.config)
            self.components['vector_store'].initialize()
            logger.info("向量存储初始化完成")
            
            # 向量化引擎
            self.components['embedding_engine'] = EmbeddingEngine(self.config.config)
            self.components['embedding_engine'].initialize()
            logger.info("向量化引擎初始化完成")
            
            # 任务管理器
            self.components['task_manager'] = TaskManager(self.config.config)
            self.components['task_manager'].initialize()
            logger.info("任务管理器初始化完成")
            
        except Exception as e:
            logger.error(f"组件初始化失败: {e}")
            raise
    
    def _register_routes(self) -> None:
        """注册路由"""
        
        @self.app.get('/')
        async def root():
            """根路径"""
            return {
                'message': 'msearch API Server',
                'version': '1.0.0',
                'status': 'running'
            }
        
        @self.app.get('/health')
        async def health_check():
            """健康检查"""
            return {
                'status': 'healthy',
                'components': {
                    'database': 'ok',
                    'vector_store': 'ok',
                    'embedding_engine': 'ok',
                    'task_manager': 'ok'
                }
            }
        
        @self.app.get('/api/v1/system/info')
        async def get_system_info():
            """获取系统信息"""
            hardware_detector = self.components['hardware_detector']
            hardware_info = hardware_detector.get_hardware_info()
            hardware_profile = hardware_detector.get_hardware_profile()
            
            return {
                'hardware': hardware_info,
                'profile': hardware_profile,
                'recommended_model': hardware_detector.get_recommended_model()
            }
        
        @self.app.get('/api/v1/models/info')
        async def get_models_info():
            """获取模型信息"""
            embedding_engine = self.components['embedding_engine']
            return embedding_engine.get_current_model_info()
        
        @self.app.post('/api/v1/search')
        async def search(
            query: str = Form(...),
            modality: str = Form('image'),
            limit: int = Query(20, ge=1, le=100)
        ):
            """
            检索接口
            
            Args:
                query: 查询内容
                modality: 目标模态
                limit: 返回结果数量
            """
            try:
                embedding_engine = self.components['embedding_engine']
                vector_store = self.components['vector_store']
                
                # 向量化查询
                query_vector = embedding_engine.embed_text(query, target_modality=modality)
                
                # 检索向量
                results = vector_store.search_vectors(
                    query_vector=query_vector,
                    limit=limit,
                    filter={'modality': modality} if modality else None
                )
                
                return {
                    'success': True,
                    'query': query,
                    'modality': modality,
                    'results': results,
                    'count': len(results)
                }
            except Exception as e:
                logger.error(f"检索失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post('/api/v1/search/image')
        async def search_by_image(
            file: UploadFile = File(...)
        ):
            """
            图像检索接口
            
            Args:
                file: 上传的图像文件
            """
            try:
                embedding_engine = self.components['embedding_engine']
                vector_store = self.components['vector_store']
                
                # 保存临时文件
                temp_file = Path(f"/tmp/{file.filename}")
                with open(temp_file, 'wb') as f:
                    f.write(await file.read())
                
                # 向量化图像
                query_vector = embedding_engine.embed_image(str(temp_file))
                
                # 检索向量
                results = vector_store.search_vectors(
                    query_vector=query_vector,
                    limit=20,
                    filter={'modality': 'image'}
                )
                
                # 删除临时文件
                temp_file.unlink()
                
                return {
                    'success': True,
                    'filename': file.filename,
                    'results': results,
                    'count': len(results)
                }
            except Exception as e:
                logger.error(f"图像检索失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get('/api/v1/files')
        async def get_files(
            status: Optional[str] = Query(None),
            limit: int = Query(100, ge=1, le=1000)
        ):
            """
            获取文件列表
            
            Args:
                status: 文件状态筛选
                limit: 返回数量限制
            """
            try:
                database_manager = self.components['database_manager']
                
                if status:
                    files = database_manager.get_files_by_status(status, limit)
                else:
                    files = database_manager.search_file_metadata('', limit)
                
                return {
                    'success': True,
                    'files': files,
                    'count': len(files)
                }
            except Exception as e:
                logger.error(f"获取文件列表失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get('/api/v1/files/{file_id}')
        async def get_file(file_id: str):
            """
            获取文件详情
            
            Args:
                file_id: 文件ID
            """
            try:
                database_manager = self.components['database_manager']
                file_data = database_manager.get_file_metadata(file_id)
                
                if not file_data:
                    raise HTTPException(status_code=404, detail='文件不存在')
                
                return {
                    'success': True,
                    'file': file_data
                }
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"获取文件详情失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get('/api/v1/tasks')
        async def get_tasks(
            status: Optional[str] = Query(None),
            limit: int = Query(100, ge=1, le=1000)
        ):
            """
            获取任务列表
            
            Args:
                status: 任务状态筛选
                limit: 返回数量限制
            """
            try:
                task_manager = self.components['task_manager']
                
                if status == 'pending':
                    tasks = task_manager.get_pending_tasks(limit)
                elif status == 'running':
                    tasks = task_manager.get_running_tasks(limit)
                elif status == 'completed':
                    tasks = task_manager.get_completed_tasks(limit)
                elif status == 'failed':
                    tasks = task_manager.get_failed_tasks(limit)
                else:
                    all_tasks = []
                    all_tasks.extend(task_manager.get_pending_tasks(limit))
                    all_tasks.extend(task_manager.get_running_tasks(limit))
                    all_tasks.extend(task_manager.get_completed_tasks(limit))
                    all_tasks.extend(task_manager.get_failed_tasks(limit))
                    tasks = all_tasks[:limit]
                
                return {
                    'success': True,
                    'tasks': tasks,
                    'count': len(tasks)
                }
            except Exception as e:
                logger.error(f"获取任务列表失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get('/api/v1/tasks/{task_id}')
        async def get_task(task_id: str):
            """
            获取任务详情
            
            Args:
                task_id: 任务ID
            """
            try:
                task_manager = self.components['task_manager']
                task = task_manager.get_task(task_id)
                
                if not task:
                    raise HTTPException(status_code=404, detail='任务不存在')
                
                return {
                    'success': True,
                    'task': task
                }
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"获取任务详情失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get('/api/v1/tasks/stats')
        async def get_task_stats():
            """获取任务统计信息"""
            try:
                task_manager = self.components['task_manager']
                stats = task_manager.get_task_stats()
                
                return {
                    'success': True,
                    'stats': stats
                }
            except Exception as e:
                logger.error(f"获取任务统计信息失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get('/api/v1/database/stats')
        async def get_database_stats():
            """获取数据库统计信息"""
            try:
                database_manager = self.components['database_manager']
                stats = database_manager.get_database_stats()
                
                return {
                    'success': True,
                    'stats': stats
                }
            except Exception as e:
                logger.error(f"获取数据库统计信息失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
    
    def run(self, host: str = '0.0.0.0', port: int = 8000):
        """
        运行API服务器
        
        Args:
            host: 主机地址
            port: 端口号
        """
        import uvicorn
        
        api_config = self.config.get('api', {})
        host = api_config.get('host', host)
        port = api_config.get('port', port)
        
        logger.info(f"启动API服务器: http://{host}:{port}")
        uvicorn.run(self.app, host=host, port=port)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='msearch API Server')
    parser.add_argument('--config', '-c', type=str, help='配置文件路径')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='主机地址')
    parser.add_argument('--port', type=int, default=8000, help='端口号')
    
    args = parser.parse_args()
    
    # 创建API服务器
    server = APIServer(config_path=args.config)
    
    # 运行服务器
    server.run(host=args.host, port=args.port)


if __name__ == '__main__':
    main()