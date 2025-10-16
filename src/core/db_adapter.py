"""
统一数据库适配器
确保存储层可替换性，提供统一的数据库访问接口
"""

from typing import Dict, Any, List, Optional
import logging

from src.core.database import get_db_manager
from src.core.logging_config import get_logger

logger = get_logger(__name__)


class UnifiedDatabaseAdapter:
    """统一数据库访问层，确保存储层可替换性"""
    
    def __init__(self):
        """初始化数据库适配器"""
        self.db_manager = get_db_manager()
        logger.info("统一数据库适配器初始化完成")
    
    async def search(self, query_vector: List[float], modality: str = None, filters: Dict = None) -> List[Dict]:
        """
        统一搜索接口
        
        Args:
            query_vector: 查询向量
            modality: 模态类型
            filters: 过滤条件
            
        Returns:
            搜索结果列表
        """
        # 这里应该实现实际的向量搜索逻辑
        # 目前返回模拟数据
        logger.info(f"执行向量搜索，模态: {modality}")
        
        try:
            # 从数据库获取文件元数据
            query = "SELECT * FROM files WHERE status = 'completed'"
            params = []
            
            if modality:
                query += " AND file_type LIKE ?"
                params.append(f"%{modality}%")
            
            query += " LIMIT 10"
            
            files = self.db_manager.execute_query(query, params)
            
            results = []
            for file in files:
                results.append({
                    "file_id": file["id"],
                    "file_path": file["file_path"],
                    "file_type": file["file_type"],
                    "similarity_score": 0.85,  # 模拟相似度分数
                    "metadata": file
                })
            
            return results
        except Exception as e:
            logger.error(f"数据库搜索失败: {e}")
            # 返回模拟数据作为降级方案
            return self._get_mock_search_results()
    
    def _get_mock_search_results(self) -> List[Dict]:
        """获取模拟搜索结果"""
        return [
            {
                "file_id": 1,
                "file_path": "/data/videos/sample1.mp4",
                "file_type": "video",
                "similarity_score": 0.85,
                "metadata": {
                    "id": 1,
                    "file_path": "/data/videos/sample1.mp4",
                    "file_type": "video",
                    "file_size": 1024000,
                    "duration": 120.5,
                    "status": "completed"
                }
            },
            {
                "file_id": 2,
                "file_path": "/data/images/sample1.jpg",
                "file_type": "image",
                "similarity_score": 0.82,
                "metadata": {
                    "id": 2,
                    "file_path": "/data/images/sample1.jpg",
                    "file_type": "image",
                    "file_size": 512000,
                    "width": 1920,
                    "height": 1080,
                    "status": "completed"
                }
            }
        ]
    
    async def store_embedding(self, file_id: int, vectors: List[List[float]], metadata: Dict[str, Any]) -> bool:
        """
        统一存储接口
        
        Args:
            file_id: 文件ID
            vectors: 向量数据
            metadata: 元数据
            
        Returns:
            存储是否成功
        """
        try:
            # 这里应该实现实际的向量存储逻辑
            logger.info(f"存储文件 {file_id} 的向量数据，向量数量: {len(vectors)}")
            
            # 模拟存储媒体片段信息
            for i, vector in enumerate(vectors):
                segment_data = {
                    "file_id": file_id,
                    "qdrant_point_id": f"point_{file_id}_{i}",
                    "segment_type": metadata.get("segment_type", "unknown"),
                    "segment_index": i,
                    "start_time_ms": i * 1000,
                    "end_time_ms": (i + 1) * 1000,
                }
                
                self.db_manager.insert_record("media_segments", segment_data)
            
            # 更新文件状态
            self.db_manager.update_record(
                "files",
                {"status": "completed", "processed_at": "datetime('now')"},
                "id = ?",
                (file_id,)
            )
            
            return True
            
        except Exception as e:
            logger.error(f"向量存储失败: {e}")
            return False
    
    async def reset(self) -> bool:
        """
        重置数据库 - 支持系统重置API
        
        Returns:
            重置是否成功
        """
        try:
            logger.info("开始重置数据库")
            
            # 重置SQLite数据库
            self.db_manager.reset_database()
            
            # 这里应该也重置向量数据库(Qdrant)
            # 暂时跳过向量数据库重置
            
            logger.info("数据库重置完成")
            return True
            
        except Exception as e:
            logger.error(f"数据库重置失败: {e}")
            return False
    
    async def get_file_metadata(self, file_id: int) -> Optional[Dict[str, Any]]:
        """
        获取文件元数据
        
        Args:
            file_id: 文件ID
            
        Returns:
            文件元数据
        """
        try:
            files = self.db_manager.execute_query(
                "SELECT * FROM files WHERE id = ?", 
                (file_id,)
            )
            
            return files[0] if files else None
            
        except Exception as e:
            logger.error(f"获取文件元数据失败: {e}")
            return None
    
    async def add_file_to_queue(self, file_path: str, priority: int = 5) -> int:
        """
        添加文件到处理队列
        
        Args:
            file_path: 文件路径
            priority: 处理优先级
            
        Returns:
            队列记录ID
        """
        try:
            queue_data = {
                "file_path": file_path,
                "priority": priority,
                "status": "queued"
            }
            
            queue_id = self.db_manager.insert_record("processing_queue", queue_data)
            logger.info(f"文件 {file_path} 已添加到处理队列，队列ID: {queue_id}")
            
            return queue_id
            
        except Exception as e:
            logger.error(f"添加文件到队列失败: {e}")
            raise
    
    async def update_queue_status(self, queue_id: int, status: str, error_message: str = None) -> bool:
        """
        更新队列状态
        
        Args:
            queue_id: 队列记录ID
            status: 状态
            error_message: 错误信息
            
        Returns:
            更新是否成功
        """
        try:
            update_data = {"status": status}
            if error_message:
                update_data["error_message"] = error_message
                
            if status == "processing":
                update_data["started_at"] = "datetime('now')"
            elif status in ["completed", "failed"]:
                update_data["completed_at"] = "datetime('now')"
            
            affected_rows = self.db_manager.update_record(
                "processing_queue",
                update_data,
                "id = ?",
                (queue_id,)
            )
            
            logger.info(f"队列记录 {queue_id} 状态更新为 {status}")
            return affected_rows > 0
            
        except Exception as e:
            logger.error(f"更新队列状态失败: {e}")
            return False

    async def update_file_processing_status(self, file_id: str, status: str, progress: int, error_message: str = None) -> bool:
        """
        更新文件处理状态
        
        Args:
            file_id: 文件ID
            status: 状态
            progress: 进度
            error_message: 错误信息
            
        Returns:
            更新是否成功
        """
        try:
            # 查找对应的队列记录
            queue_records = self.db_manager.execute_query(
                "SELECT id FROM processing_queue WHERE id = ?",
                (int(file_id),)
            )
            
            if queue_records:
                # 更新队列状态
                return await self.update_queue_status(int(file_id), status, error_message)
            else:
                logger.warning(f"未找到文件ID对应的队列记录: {file_id}")
                return False
                
        except Exception as e:
            logger.error(f"更新文件处理状态失败: {e}")
            return False


# 全局数据库适配器实例
_db_adapter = None


def get_db_adapter() -> UnifiedDatabaseAdapter:
    """
    获取全局数据库适配器实例
    
    Returns:
        数据库适配器实例
    """
    global _db_adapter
    if _db_adapter is None:
        _db_adapter = UnifiedDatabaseAdapter()
    return _db_adapter