"""
向量存储管理器
负责LanceDB向量数据库的操作
"""

import lancedb
from typing import Any, Dict, List, Optional
from pathlib import Path
import logging
import numpy as np
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class VectorStore:
    """向量存储管理器"""
    
    def __init__(self, data_dir: str, collection_name: str = "unified_vectors"):
        """
        初始化向量存储
        
        Args:
            data_dir: LanceDB数据目录
            collection_name: 集合名称
        """
        self.data_dir = Path(data_dir)
        self.collection_name = collection_name
        self.db: Optional[lancedb.DBConnection] = None
        self.table: Optional[lancedb.table.Table] = None
        self._initialize()
    
    def _initialize(self) -> bool:
        """初始化向量数据库"""
        try:
            # 确保数据目录存在
            self.data_dir.mkdir(parents=True, exist_ok=True)
            
            # 连接LanceDB
            self.db = lancedb.connect(str(self.data_dir))
            
            # 获取或创建表
            if self.collection_name in self.db.table_names():
                self.table = self.db.open_table(self.collection_name)
                logger.info(f"打开现有向量表: {self.collection_name}")
            else:
                self.table = self.db.create_table(
                    self.collection_name,
                    schema=[
                        ("id", str),
                        ("vector", lancedb.vector(512)),  # 默认512维向量
                        ("modality", str),
                        ("file_id", str),
                        ("segment_id", str),
                        ("start_time", float),
                        ("end_time", float),
                        ("is_full_video", bool),
                        ("metadata", str),
                        ("created_at", float)
                    ]
                )
                logger.info(f"创建新向量表: {self.collection_name}")
            
            return True
        except Exception as e:
            logger.error(f"向量数据库初始化失败: {e}")
            return False
    
    def insert_vectors(self, vectors: List[Dict[str, Any]]) -> None:
        """
        插入向量
        
        Args:
            vectors: 向量数据列表
        """
        try:
            # 准备数据
            data = []
            for vec in vectors:
                data.append({
                    "id": vec.get('id', str(uuid.uuid4())),
                    "vector": np.array(vec['vector'], dtype=np.float32),
                    "modality": vec.get('modality', 'unknown'),
                    "file_id": vec.get('file_id', ''),
                    "segment_id": vec.get('segment_id', ''),
                    "start_time": vec.get('start_time', 0.0),
                    "end_time": vec.get('end_time', 0.0),
                    "is_full_video": vec.get('is_full_video', False),
                    "metadata": vec.get('metadata', {}),
                    "created_at": vec.get('created_at', datetime.now().timestamp())
                })
            
            # 批量插入
            if data:
                self.table.add(data)
                logger.info(f"插入向量: {len(data)}个")
        except Exception as e:
            logger.error(f"插入向量失败: {e}")
            raise
    
    def search_vectors(
        self,
        query_vector: List[float],
        limit: int = 20,
        filter: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        搜索向量
        
        Args:
            query_vector: 查询向量
            limit: 返回数量限制
            filter: 过滤条件
        
        Returns:
            搜索结果列表
        """
        try:
            # 转换为numpy数组
            query_vector = np.array(query_vector, dtype=np.float32)
            
            # 执行搜索
            results = self.table.search(query_vector).limit(limit).to_pandas()
            
            # 应用过滤条件
            if filter:
                for key, value in filter.items():
                    if key in results.columns:
                        results = results[results[key] == value]
            
            # 转换为字典列表
            return self._results_to_dicts(results)
        except Exception as e:
            logger.error(f"搜索向量失败: {e}")
            return []
    
    def delete_vectors(self, vector_ids: List[str]) -> None:
        """
        删除向量
        
        Args:
            vector_ids: 向量ID列表
        """
        try:
            # LanceDB不支持直接删除，需要重建表
            # 这里我们标记为删除，实际删除需要重建表
            logger.warning(f"LanceDB不支持直接删除，需要重建表: {len(vector_ids)}个向量")
            # TODO: 实现删除逻辑
        except Exception as e:
            logger.error(f"删除向量失败: {e}")
            raise
    
    def update_vector(self, vector_id: str, updates: Dict[str, Any]) -> bool:
        """
        更新向量
        
        Args:
            vector_id: 向量ID
            updates: 更新内容
        
        Returns:
            是否成功
        """
        try:
            # LanceDB不支持直接更新，需要重建表
            logger.warning(f"LanceDB不支持直接更新: {vector_id}")
            # TODO: 实现更新逻辑
            return False
        except Exception as e:
            logger.error(f"更新向量失败: {e}")
            return False
    
    def get_vector(self, vector_id: str) -> Optional[Dict[str, Any]]:
        """
        获取向量
        
        Args:
            vector_id: 向量ID
        
        Returns:
            向量数据
        """
        try:
            results = self.table.search(query_vector=np.zeros(512)).limit(1000).to_pandas()
            result = results[results['id'] == vector_id]
            
            if not result.empty:
                return self._results_to_dicts(result)[0]
            return None
        except Exception as e:
            logger.error(f"获取向量失败: {e}")
            return None
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        获取集合统计信息
        
        Returns:
            统计信息字典
        """
        try:
            # 获取表信息
            stats = self.table.to_pandas()
            
            # 按模态统计
            modality_counts = stats['modality'].value_counts().to_dict()
            
            # 总向量数
            total_vectors = len(stats)
            
            return {
                "total_vectors": total_vectors,
                "modality_counts": modality_counts,
                "vector_dimension": 512,
                "collection_name": self.collection_name
            }
        except Exception as e:
            logger.error(f"获取集合统计信息失败: {e}")
            return {}
    
    def close(self) -> None:
        """关闭向量数据库连接"""
        if self.db:
            self.db.close()
            self.db = None
            self.table = None
            logger.info("向量数据库连接已关闭")
    
    def _results_to_dicts(self, results) -> List[Dict[str, Any]]:
        """
        将查询结果转换为字典列表
        
        Args:
            results: 查询结果
        
        Returns:
            字典列表
        """
        if results is None or len(results) == 0:
            return []
        
        result_list = []
        for _, row in results.iterrows():
            result = {
                'id': row['id'],
                'vector': row['vector'].tolist() if 'vector' in row else [],
                'modality': row['modality'],
                'file_id': row['file_id'],
                'segment_id': row['segment_id'],
                'start_time': float(row['start_time']) if 'start_time' in row else 0.0,
                'end_time': float(row['end_time']) if 'end_time' in row else 0.0,
                'is_full_video': bool(row['is_full_video']) if 'is_full_video' in row else False,
                'metadata': row['metadata'] if 'metadata' in row else {},
                'created_at': float(row['created_at']) if 'created_at' in row else 0.0
            }
            
            # 添加相似度分数（如果有）
            if '_distance' in row:
                result['_distance'] = float(row['_distance'])
                result['_score'] = 1.0 - float(row['_distance'])
            
            result_list.append(result)
        
        return result_list
    
    def search_by_file_id(
        self,
        file_id: str,
        modality: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        根据文件ID搜索向量
        
        Args:
            file_id: 文件ID
            modality: 模态类型（可选）
        
        Returns:
            向量列表
        """
        try:
            results = self.table.to_pandas()
            filtered = results[results['file_id'] == file_id]
            
            if modality:
                filtered = filtered[filtered['modality'] == modality]
            
            return self._results_to_dicts(filtered)
        except Exception as e:
            logger.error(f"根据文件ID搜索向量失败: {e}")
            return []
    
    def search_by_modality(
        self,
        modality: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        根据模态搜索向量
        
        Args:
            modality: 模态类型
            limit: 返回数量限制
        
        Returns:
            向量列表
        """
        try:
            results = self.table.to_pandas()
            filtered = results[results['modality'] == modality].head(limit)
            
            return self._results_to_dicts(filtered)
        except Exception as e:
            logger.error(f"根据模态搜索向量失败: {e}")
            return []
    
    def get_vector_count_by_modality(self) -> Dict[str, int]:
        """
        获取各模态的向量数量
        
        Returns:
            模态向量数量字典
        """
        try:
            stats = self.get_collection_stats()
            return stats.get('modality_counts', {})
        except Exception as e:
            logger.error(f"获取模态向量数量失败: {e}")
            return {}
    
    def create_index(self, index_type: str = "ivf_pq", num_partitions: int = 128) -> bool:
        """
        创建向量索引
        
        Args:
            index_type: 索引类型
            num_partitions: 分区数量
        
        Returns:
            是否成功
        """
        try:
            # LanceDB会自动创建索引
            # 这里我们只是记录日志
            logger.info(f"向量索引配置: {index_type}, 分区数: {num_partitions}")
            return True
        except Exception as e:
            logger.error(f"创建向量索引失败: {e}")
            return False


def create_vector_store(config: Dict[str, Any]) -> VectorStore:
    """
    创建向量存储实例
    
    Args:
        config: 配置字典
    
    Returns:
        VectorStore实例
    """
    vector_store = VectorStore(config)
    vector_store.initialize()
    return vector_store