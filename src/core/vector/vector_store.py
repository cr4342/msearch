"""
向量存储管理器
负责LanceDB向量数据库的操作
"""

import lancedb
import json
from typing import Any, Dict, List, Optional
from pathlib import Path
import logging
import numpy as np
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class VectorStore:
    """向量存储管理器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化向量存储
        
        Args:
            config: 配置字典，包含向量存储的相关配置
        """
        self.config = config
        
        # 支持两种配置方式：
        # 1. 直接配置：data_dir
        # 2. database配置：vector_db_path
        database_config = config.get('database', {})
        if 'vector_db_path' in database_config:
            self.data_dir = Path(database_config['vector_db_path'])
        else:
            self.data_dir = Path(config.get('data_dir', 'data/database/lancedb'))
        
        self.collection_name = config.get('collection_name', 'unified_vectors')
        self.index_type = config.get('index_type', 'ivf_pq')
        self.num_partitions = config.get('num_partitions', 128)
        self.vector_dimension = config.get('vector_dimension', 512)
        
        self.db: Optional[lancedb.DBConnection] = None
        self.table: Optional[lancedb.table.Table] = None
        
        # 记录初始化信息
        logger.info(f"初始化向量存储: data_dir={self.data_dir}, collection_name={self.collection_name}")
        
        self._initialize()
    
    def initialize(self) -> bool:
        """初始化向量数据库"""
        return self._initialize()
    
    def _initialize(self) -> bool:
        """初始化向量数据库"""
        try:
            # 确保数据目录存在
            self.data_dir.mkdir(parents=True, exist_ok=True)
            
            # 连接LanceDB
            self.db = lancedb.connect(str(self.data_dir))
            logger.info(f"LanceDB连接成功: {self.data_dir}")
            
            # 获取现有表列表
            list_response = self.db.list_tables()
            existing_tables = list_response.tables if hasattr(list_response, 'tables') else []
            logger.info(f"现有表列表: {existing_tables}")

            # 获取或创建表
            if self.collection_name in existing_tables:
                self.table = self.db.open_table(self.collection_name)
                logger.info(f"打开现有向量表: {self.collection_name}")
            else:
                logger.info(f"创建新向量表: {self.collection_name}")
                # 创建表，使用示例向量确保正确的表结构
                self.table = self.db.create_table(
                    self.collection_name,
                    data=[
                        {
                            "id": "temp_init_vector",
                            "vector": np.zeros(self.vector_dimension, dtype=np.float32),
                            "modality": "temp",
                            "file_id": "",
                            "file_path": "",
                            "file_type": "",
                            "file_name": "",
                            "segment_id": "",
                            "start_time": 0.0,
                            "end_time": 0.0,
                            "is_full_video": False,
                            "metadata": "",
                            "created_at": 0.0
                        }
                    ]
                )
                logger.info(f"新向量表创建成功: {self.collection_name}")
                
                # 临时初始化向量将在后续操作中被忽略
                logger.info("新向量表创建成功，临时初始化向量将在后续操作中被忽略")
            
            # 验证table对象
            if self.table is None:
                raise ValueError("向量表对象初始化失败")
            
            logger.info(f"向量存储初始化成功: table={self.table}, collection_name={self.collection_name}")
            return True
        except Exception as e:
            logger.error(f"向量数据库初始化失败: {e}")
            logger.error(f"向量存储状态: db={self.db is not None}, table={self.table is not None}")
            import traceback
            logger.error(f"详细错误堆栈: {traceback.format_exc()}")
            # 确保在失败时设置table为None
            self.table = None
            return False
    
    def add_vector(self, vector: Dict[str, Any]) -> None:
        """
        添加单个向量
        
        Args:
            vector: 向量数据
        """
        self.insert_vectors([vector])
    
    def add_vectors(self, vectors: List[Dict[str, Any]]) -> None:
        """
        添加多个向量
        
        Args:
            vectors: 向量数据列表
        """
        self.insert_vectors(vectors)
    
    def insert_vectors(self, vectors: List[Dict[str, Any]]) -> None:
        """
        插入向量
        
        Args:
            vectors: 向量数据列表
        """
        try:
            # 检查是否存在临时初始化向量
            # 如果存在，先获取所有向量，过滤掉临时向量
            all_vectors = self.table.to_pandas()
            has_temp_vector = "temp_init_vector" in all_vectors['id'].values
            
            # 准备数据
            data = []
            for vec in vectors:
                # 处理metadata字段
                metadata = vec.get('metadata', {})
                if isinstance(metadata, dict):
                    # 从metadata中提取file_path和file_type
                    file_path = vec.get('file_path', metadata.get('file_path', ''))
                    file_type = vec.get('file_type', metadata.get('file_type', ''))
                    file_name = vec.get('file_name', metadata.get('file_name', ''))
                    metadata_json = json.dumps(metadata)
                else:
                    file_path = vec.get('file_path', '')
                    file_type = vec.get('file_type', '')
                    file_name = vec.get('file_name', '')
                    metadata_json = json.dumps({})
                
                data.append({
                    "id": vec.get('id', str(uuid.uuid4())),
                    "vector": np.array(vec['vector'], dtype=np.float32),
                    "modality": vec.get('modality', 'unknown'),
                    "file_id": vec.get('file_id', ''),
                    "file_path": file_path,
                    "file_type": file_type,
                    "file_name": file_name,
                    "segment_id": vec.get('segment_id', ''),
                    "start_time": vec.get('start_time', 0.0),
                    "end_time": vec.get('end_time', 0.0),
                    "is_full_video": vec.get('is_full_video', False),
                    "metadata": metadata_json,
                    "created_at": vec.get('created_at', datetime.now().timestamp())
                })
            
            # 批量插入
            if data:
                if has_temp_vector:
                    # 过滤掉临时向量
                    vectors_to_keep = all_vectors[all_vectors['id'] != "temp_init_vector"]
                    # 添加新向量
                    new_vectors = vectors_to_keep.to_dict('records')
                    for d in data:
                        new_vectors.append(d)
                    # 替换旧表
                    self.db.drop_table(self.collection_name)
                    self.table = self.db.create_table(
                        self.collection_name,
                        data=new_vectors
                    )
                    logger.info(f"删除临时初始化向量并插入新向量: {len(data)}个")
                else:
                    # 直接添加
                    self.table.add(data)
                    logger.info(f"插入向量: {len(data)}个")
        except Exception as e:
            logger.error(f"插入向量失败: {e}")
            raise
    
    def search(
        self,
        query_vector: List[float],
        limit: int = 20,
        filter: Optional[Dict] = None,
        similarity_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        搜索向量
        
        Args:
            query_vector: 查询向量
            limit: 返回数量限制（当使用similarity_threshold时，此参数作为最大返回数量）
            filter: 过滤条件
            similarity_threshold: 相似度阈值，高于此值的结果才会返回
        
        Returns:
            搜索结果列表
        """
        return self.search_vectors(query_vector, limit, filter, similarity_threshold)
    
    def search_vectors(
        self,
        query_vector: List[float],
        limit: int = 20,
        filter: Optional[Dict] = None,
        similarity_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        搜索向量
        
        Args:
            query_vector: 查询向量
            limit: 返回数量限制（当使用similarity_threshold时，此参数作为最大返回数量）
            filter: 过滤条件
            similarity_threshold: 相似度阈值，高于此值的结果才会返回
        
        Returns:
            搜索结果列表
        """
        try:
            # 转换为numpy数组
            query_vector = np.array(query_vector, dtype=np.float32)
            
            # 如果设置了相似度阈值，我们需要先获取足够多的结果，然后过滤
            actual_limit = limit if similarity_threshold is None else max(limit * 2, 100)  # 获取更多结果用于过滤
            
            # 执行搜索（使用余弦相似度）
            # LanceDB支持metric参数: "cosine", "l2", "dot"
            results = self.table.search(query_vector, vector_column_name="vector")\
                .metric("cosine")\
                .limit(actual_limit)\
                .to_pandas()
            
            # 应用过滤条件
            if filter:
                for key, value in filter.items():
                    if key in results.columns:
                        results = results[results[key] == value]
            
            # 转换为字典列表（带有相似度计算）
            result_dicts = self._results_to_dicts(results)
            
            # 过滤掉临时初始化向量
            result_dicts = [r for r in result_dicts if r.get('id') != "temp_init_vector"]
            
            # 按相似度排序
            result_dicts = sorted(result_dicts, key=lambda x: x['similarity'], reverse=True)
            
            # 去重：根据file_path去重，保留相似度最高的
            seen_files = set()
            unique_results = []
            for r in result_dicts:
                file_path = r.get('file_path', '')
                if file_path and file_path not in seen_files:
                    seen_files.add(file_path)
                    unique_results.append(r)
            result_dicts = unique_results
            
            # 如果设置了相似度阈值，过滤结果
            if similarity_threshold is not None:
                result_dicts = [r for r in result_dicts if r['similarity'] >= similarity_threshold]
            
            # 限制最终返回数量
            return result_dicts[:limit]
        except Exception as e:
            logger.error(f"搜索向量失败: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取向量存储统计信息
        
        Returns:
            统计信息字典
        """
        try:
            stats = {
                'data_dir': str(self.data_dir),
                'collection_name': self.collection_name,
                'vector_dimension': self.vector_dimension,
                'index_type': self.index_type,
                'num_partitions': self.num_partitions
            }
            
            # 获取向量数量
            if self.table is not None:
                try:
                    # 使用count方法
                    vector_count = self.table.count_rows()
                    stats['vector_count'] = vector_count
                except Exception as e:
                    # 回退到to_pandas方法
                    try:
                        df = self.table.to_pandas()
                        stats['vector_count'] = len(df)
                    except Exception as e2:
                        stats['vector_count'] = 0
            else:
                stats['vector_count'] = 0
            
            return stats
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {
                'data_dir': str(self.data_dir),
                'collection_name': self.collection_name,
                'vector_dimension': self.vector_dimension,
                'vector_count': 0
            }
    
    def delete_vectors(self, vector_ids: List[str]) -> None:
        """
        删除向量
        
        Args:
            vector_ids: 向量ID列表
        """
        try:
            # LanceDB不支持直接删除，需要重建表
            logger.info(f"开始删除向量: {len(vector_ids)}个向量")
            
            # 获取所有不在要删除列表中的向量
            all_vectors = self.table.to_pandas()
            vectors_to_keep = all_vectors[~all_vectors['id'].isin(vector_ids)]
            
            # 如果所有向量都被删除了
            if vectors_to_keep.empty:
                # 删除旧表并创建新的空表
                self.db.drop_table(self.collection_name)
                # 使用空数据创建表，确保正确的表结构但不添加任何向量
                import pandas as pd
                empty_df = pd.DataFrame({
                    "id": pd.Series([], dtype="string"),
                    "vector": pd.Series([], dtype="object"),
                    "modality": pd.Series([], dtype="string"),
                    "file_id": pd.Series([], dtype="string"),
                    "segment_id": pd.Series([], dtype="string"),
                    "start_time": pd.Series([], dtype="float64"),
                    "end_time": pd.Series([], dtype="float64"),
                    "is_full_video": pd.Series([], dtype="boolean"),
                    "metadata": pd.Series([], dtype="string"),
                    "created_at": pd.Series([], dtype="float64")
                })
                self.table = self.db.create_table(
                    self.collection_name,
                    data=empty_df
                )
                logger.info(f"所有向量都已删除，创建了空向量表")
                return
            
            # 替换旧表
            self.db.drop_table(self.collection_name)
            
            # 创建新表并重新插入保留的数据
            self.table = self.db.create_table(
                self.collection_name,
                data=vectors_to_keep.to_dict('records')
            )
            
            logger.info(f"成功删除向量: {len(vector_ids)}个向量，剩余向量: {len(vectors_to_keep)}个")
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
            logger.info(f"开始更新向量: {vector_id}")
            
            # 获取所有向量
            all_vectors = self.table.to_pandas()
            
            # 检查要更新的向量是否存在
            if vector_id not in all_vectors['id'].values:
                logger.warning(f"要更新的向量不存在: {vector_id}")
                return False
            
            # 找到要更新的向量
            vector_index = all_vectors[all_vectors['id'] == vector_id].index[0]
            vector_to_update = all_vectors.iloc[vector_index]
            
            # 应用更新
            for key, value in updates.items():
                if key in vector_to_update:
                    if key == "metadata":
                        vector_to_update[key] = json.dumps(value)
                    else:
                        vector_to_update[key] = value
            
            # 更新数据框
            all_vectors.iloc[vector_index] = vector_to_update
            
            # 替换旧表
            self.db.drop_table(self.collection_name)
            
            # 创建新表并重新插入数据
            self.table = self.db.create_table(
                self.collection_name,
                data=all_vectors.to_dict('records')
            )
            
            logger.info(f"成功更新向量: {vector_id}")
            return True
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
            results = self.table.search(np.zeros(self.vector_dimension)).limit(1000).to_pandas()
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
                "vector_count": total_vectors,  # 兼容测试用例
                "modality_counts": modality_counts,
                "vector_dimension": self.vector_dimension,
                "collection_name": self.collection_name
            }
        except Exception as e:
            logger.error(f"获取集合统计信息失败: {e}")
            return {}
    
    def close(self) -> None:
        """关闭向量数据库连接"""
        try:
            if self.db:
                # LanceDB的DBConnection对象不需要显式关闭
                # 只需要清理引用
                self.db = None
                self.table = None
                logger.info("向量数据库连接已关闭")
        except Exception as e:
            logger.error(f"关闭向量数据库连接时出错: {e}")
            # 即使出错也要清理引用
            self.db = None
            self.table = None
    
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
            # 过滤掉临时初始化向量
            if row['id'] == 'temp_init_vector' or row['modality'] == 'temp':
                continue
                
            # 计算相似度 (cosine distance转换为cosine similarity)
            # LanceDB的余弦距离 = 1 - cosine_similarity
            # 所以 cosine_similarity = 1 - cosine_distance
            if '_distance' in row:
                cosine_distance = float(row['_distance'])
                # 将余弦距离转换为余弦相似度
                # 余弦距离范围是[0, 2]，其中0表示完全相同，2表示完全相反
                # 余弦相似度范围是[-1, 1]，其中1表示完全相同，-1表示完全相反
                # 我们将其归一化到[0, 1]范围
                cosine_similarity = 1.0 - cosine_distance
                # 归一化到[0, 1]范围 (将[-1, 1]映射到[0, 1])
                similarity = (cosine_similarity + 1.0) / 2.0
                # 确保相似度在[0, 1]范围内
                similarity = max(0.0, min(1.0, similarity))
            else:
                similarity = 0.0
            
            # 获取文件名和路径（metadata可能是字符串或字典）
            metadata_dict = {}
            if 'metadata' in row:
                if isinstance(row['metadata'], str):
                    try:
                        metadata_dict = json.loads(row['metadata']) if row['metadata'] else {}
                    except json.JSONDecodeError:
                        metadata_dict = {}
                elif isinstance(row['metadata'], dict):
                    metadata_dict = row['metadata']
            
            file_name = metadata_dict.get('file_name', '')
            file_path = metadata_dict.get('file_path', '')
            
            result = {
                'id': row['id'],
                'vector': row['vector'].tolist() if 'vector' in row else [],
                'modality': row['modality'],
                'file_id': row['file_id'],
                'segment_id': row['segment_id'],
                'start_time': float(row['start_time']) if 'start_time' in row else 0.0,
                'end_time': float(row['end_time']) if 'end_time' in row else 0.0,
                'is_full_video': bool(row['is_full_video']) if 'is_full_video' in row else False,
                'metadata': json.loads(row['metadata']) if 'metadata' in row and isinstance(row['metadata'], str) and row['metadata'] else (row['metadata'] if 'metadata' in row and isinstance(row['metadata'], dict) else {}),
                'created_at': float(row['created_at']) if 'created_at' in row else 0.0,
                'distance': float(row['_distance']) if '_distance' in row else 0.0,
                'similarity': similarity,
                'file_name': file_name,
                'file_path': file_path
            }
            
            # 添加相似度分数（如果有）
            if '_distance' in row:
                result['_distance'] = float(row['_distance'])
                result['_score'] = similarity  # 使用计算好的相似度
            
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
    
    def create_index(self, index_type: str = None, num_partitions: int = None) -> bool:
        """
        创建向量索引
        
        注意：LanceDB 0.26.1版本自动管理索引，无需手动创建
        
        Args:
            index_type: 索引类型（可选，默认使用配置的值）
            num_partitions: 分区数量（可选，默认使用配置的值）
        
        Returns:
            是否成功
        """
        try:
            if not self.table:
                return False
            
            # LanceDB 0.26.1版本自动管理索引，无需手动创建
            logger.info("LanceDB自动管理索引，无需手动创建")
            return True
        except Exception as e:
            logger.error(f"创建向量索引失败: {e}")
            return False
            
    def clear_vectors(self) -> None:
        """
        清空向量库中的所有向量数据
        """
        try:
            logger.info(f"开始清空向量库: {self.collection_name}")
            
            # 删除旧表
            self.db.drop_table(self.collection_name)
            
            # 创建一个新的空表，使用LanceDB自动创建schema的方式
            # 先创建一个临时的空DataFrame来初始化表结构
            import pandas as pd
            import pyarrow as pa
            
            # 创建空的DataFrame，包含所有需要的字段
            empty_df = pd.DataFrame({
                "id": pd.Series([], dtype="string"),
                "vector": pd.Series([], dtype="object"),  # 将在LanceDB中转换为向量类型
                "modality": pd.Series([], dtype="string"),
                "file_id": pd.Series([], dtype="string"),
                "segment_id": pd.Series([], dtype="string"),
                "start_time": pd.Series([], dtype="float64"),
                "end_time": pd.Series([], dtype="float64"),
                "is_full_video": pd.Series([], dtype="boolean"),
                "metadata": pd.Series([], dtype="string"),
                "created_at": pd.Series([], dtype="float64")
            })
            
            # 创建表（LanceDB会自动推断schema）
            self.table = self.db.create_table(
                self.collection_name,
                empty_df,
                mode="overwrite"
            )
            
            logger.info(f"成功清空向量库: {self.collection_name}")
        except Exception as e:
            logger.error(f"清空向量库失败: {e}")
            raise


def create_vector_store(config: Dict[str, Any]) -> VectorStore:
    """
    创建向量存储实例
    
    Args:
        config: 配置字典，包含向量存储的相关配置
    
    Returns:
        VectorStore实例
    """
    # 提取lancedb配置
    lancedb_config = config.get('database', {}).get('lancedb', {})
    
    # 确保data_dir存在
    if 'data_dir' not in lancedb_config:
        lancedb_config['data_dir'] = config.get('data_dir', 'data/database/lancedb')
    
    # 创建VectorStore实例
    vector_store = VectorStore(lancedb_config)
    
    # 创建索引（如果需要）
    if config.get('create_index', True):
        vector_store.create_index()
    
    return vector_store