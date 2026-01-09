"""
向量存储器
专注于 Milvus Lite 向量数据库操作
"""
import asyncio
import logging
from typing import List, Dict, Optional, Any
from pathlib import Path

from src.core.config_manager import ConfigManager

class VectorStore:
    """向量存储器 - 专注于 Milvus Lite 向量数据库操作"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        
        # 初始化Milvus Lite连接
        self.milvus_path = self.config_manager.get("database.milvus_lite_path", "data/database/milvus_lite.db")
        Path(self.milvus_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Milvus客户端
        self.client = None
        self.collections = {}
        
        # 运行状态
        self.is_running = False
        
        self.logger.info(f"向量存储器初始化完成，路径: {self.milvus_path}")
    
    async def start(self):
        """启动向量存储器"""
        self.logger.info("启动向量存储器")
        
        try:
            # 初始化Milvus连接
            await self._connect_milvus()
            
            # 创建默认集合
            await self._create_default_collections()
            
            self.is_running = True
            self.logger.info("向量存储器启动完成")
        except Exception as e:
            self.logger.error(f"向量存储器启动失败: {e}")
            raise
    
    async def stop(self):
        """停止向量存储器"""
        self.logger.info("停止向量存储器")
        
        # 关闭Milvus连接
        if self.client:
            # Milvus Lite不需要显式断开连接
            pass
        
        self.is_running = False
        self.logger.info("向量存储器已停止")
    
    async def _connect_milvus(self):
        """连接到Milvus Lite"""
        try:
            from pymilvus import MilvusClient
            
            # 确保目录存在
            Path(self.milvus_path).parent.mkdir(parents=True, exist_ok=True)
            
            # 初始化Milvus客户端
            self.client = MilvusClient(uri=self.milvus_path)
            
            self.logger.info("Milvus Lite连接成功")
        except ImportError:
            self.logger.error("pymilvus库未安装")
            raise
        except Exception as e:
            self.logger.error(f"Milvus Lite连接失败: {e}")
            raise
    
    async def _create_default_collections(self):
        """创建默认向量集合"""
        try:
            from pymilvus import DataType, FieldSchema, CollectionSchema
            
            # 定义集合配置
            collections_config = [
                {
                    'name': 'image_vectors',
                    'description': '图像向量存储',
                    'dimension': 512,
                    'metric_type': 'COSINE'
                },
                {
                    'name': 'video_vectors', 
                    'description': '视频帧向量存储',
                    'dimension': 512,
                    'metric_type': 'COSINE'
                },
                {
                    'name': 'audio_vectors',
                    'description': '音频向量存储', 
                    'dimension': 512,
                    'metric_type': 'COSINE'
                },
                {
                    'name': 'face_vectors',
                    'description': '人脸向量存储',
                    'dimension': 512, 
                    'metric_type': 'COSINE'
                },
                {
                    'name': 'text_vectors',
                    'description': '文本向量存储',
                    'dimension': 512,
                    'metric_type': 'COSINE'
                }
            ]
            
            # 创建每个集合
            for config in collections_config:
                collection_name = config['name']
                
                if not self.client.has_collection(collection_name):
                    # 定义集合架构
                    fields = [
                        FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, auto_id=False, max_length=65535),
                        FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=config['dimension']),
                        FieldSchema(name="file_path", dtype=DataType.VARCHAR, max_length=65535),
                        FieldSchema(name="file_type", dtype=DataType.VARCHAR, max_length=32),
                        FieldSchema(name="task_id", dtype=DataType.VARCHAR, max_length=64),
                        FieldSchema(name="timestamp", dtype=DataType.DOUBLE),
                        FieldSchema(name="metadata", dtype=DataType.JSON)
                    ]
                    
                    schema = CollectionSchema(
                        fields=fields,
                        description=config['description']
                    )
                    
                    # 创建集合
                    self.client.create_collection(
                        collection_name=collection_name,
                        schema=schema,
                        metric_type=config['metric_type'],
                        auto_id=False
                    )
                    
                    # 创建索引
                    self.client.create_index(
                        collection_name=collection_name,
                        field_name="vector",
                        index_params={
                            "index_type": "IVF_FLAT",
                            "metric_type": config['metric_type'],
                            "params": {"nlist": 128}
                        }
                    )
                    
                    self.logger.info(f"创建向量集合: {collection_name}")
                else:
                    self.logger.debug(f"向量集合已存在: {collection_name}")
                
                # 记录集合信息
                self.collections[collection_name] = config
        
        except Exception as e:
            self.logger.error(f"创建默认集合失败: {e}")
            raise
    
    async def create_collection(self, collection_name: str, dimension: int) -> None:
        """创建向量集合"""
        try:
            from pymilvus import DataType, FieldSchema, CollectionSchema
            
            if self.client.has_collection(collection_name):
                self.logger.warning(f"集合已存在: {collection_name}")
                return
            
            fields = [
                FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, auto_id=False, max_length=65535),
                FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=dimension),
                FieldSchema(name="file_path", dtype=DataType.VARCHAR, max_length=65535),
                FieldSchema(name="file_type", dtype=DataType.VARCHAR, max_length=32),
                FieldSchema(name="task_id", dtype=DataType.VARCHAR, max_length=64),
                FieldSchema(name="timestamp", dtype=DataType.DOUBLE),
                FieldSchema(name="metadata", dtype=DataType.JSON)
            ]
            
            schema = CollectionSchema(
                fields=fields,
                description=f"自定义向量集合: {collection_name}"
            )
            
            self.client.create_collection(
                collection_name=collection_name,
                schema=schema,
                metric_type="COSINE",
                auto_id=False
            )
            
            self.client.create_index(
                collection_name=collection_name,
                field_name="vector",
                index_params={
                    "index_type": "IVF_FLAT",
                    "metric_type": "COSINE",
                    "params": {"nlist": 128}
                }
            )
            
            self.collections[collection_name] = {
                'name': collection_name,
                'dimension': dimension,
                'metric_type': 'COSINE'
            }
            
            self.logger.info(f"创建向量集合: {collection_name}")
        except Exception as e:
            self.logger.error(f"创建集合失败: {collection_name}, 错误: {e}")
            raise
    
    async def drop_collection(self, collection_name: str) -> None:
        """删除向量集合"""
        try:
            if self.client.has_collection(collection_name):
                self.client.drop_collection(collection_name)
                if collection_name in self.collections:
                    del self.collections[collection_name]
                self.logger.info(f"删除向量集合: {collection_name}")
            else:
                self.logger.warning(f"集合不存在: {collection_name}")
        except Exception as e:
            self.logger.error(f"删除集合失败: {collection_name}, 错误: {e}")
            raise
    
    async def has_collection(self, collection_name: str) -> bool:
        """检查集合是否存在"""
        return self.client.has_collection(collection_name)
    
    async def insert_video_vector(self, vector: List[float], video_info: Dict) -> str:
        """插入视频向量，包含时间定位信息"""
        try:
            collection = "video_vectors"
            
            if not self.client.has_collection(collection):
                raise ValueError(f"集合不存在: {collection}")
            
            # 生成唯一ID
            import uuid
            vector_id = str(uuid.uuid4())
            
            # 准备插入数据
            data = {
                "id": vector_id,
                "vector": vector,
                "file_path": video_info.get("file_path", ""),
                "file_type": "video",
                "task_id": video_info.get("task_id", ""),
                "timestamp": video_info.get("absolute_timestamp", 0.0),
                "metadata": {
                    "video_uuid": video_info.get("video_uuid", ""),
                    "segment_id": video_info.get("segment_id", ""),
                    "vector_id": vector_id,
                    "absolute_timestamp": video_info.get("absolute_timestamp", 0.0),
                    "segment_file": video_info.get("segment_file", ""),
                    "original_file": video_info.get("original_file", ""),
                    "start_time": video_info.get("start_time", 0.0),
                    "end_time": video_info.get("end_time", 0.0),
                    "duration": video_info.get("duration", 0.0),
                    "frame_path": video_info.get("frame_path", ""),
                    "relative_position": video_info.get("relative_position", 0.0)
                }
            }
            
            # 插入向量
            self.client.insert(collection, [data])
            
            # 刷新集合以确保数据可用
            self.client.flush(collection)
            
            self.logger.info(f"插入视频向量到集合 {collection}: {vector_id}")
            return vector_id
        except Exception as e:
            self.logger.error(f"插入视频向量失败: {e}")
            raise
    
    async def get_vectors_with_timestamps(self, collection: str, query_vector: List[float], 
                                        limit: int) -> List[Dict]:
        """搜索向量并返回包含时间戳信息的结果"""
        try:
            if not self.client.has_collection(collection):
                raise ValueError(f"集合不存在: {collection}")
            
            # 执行搜索
            results = self.client.search(
                collection,
                [query_vector],
                limit=limit,
                output_fields=["id", "file_path", "file_type", "task_id", "timestamp", "metadata"]
            )
            
            # 格式化结果，包含时间戳信息
            formatted_results = []
            for result in results[0]:  # 取第一个查询的结果
                formatted_results.append({
                    'id': result['id'],
                    'distance': result['distance'],
                    'file_path': result['entity'].get('file_path', ''),
                    'file_type': result['entity'].get('file_type', ''),
                    'task_id': result['entity'].get('task_id', ''),
                    'timestamp': result['entity'].get('timestamp', 0.0),
                    'video_uuid': result['entity'].get('metadata', {}).get('video_uuid', ''),
                    'segment_id': result['entity'].get('metadata', {}).get('segment_id', ''),
                    'vector_id': result['entity'].get('metadata', {}).get('vector_id', ''),
                    'absolute_timestamp': result['entity'].get('metadata', {}).get('absolute_timestamp', 0.0),
                    'segment_file': result['entity'].get('metadata', {}).get('segment_file', ''),
                    'original_file': result['entity'].get('metadata', {}).get('original_file', ''),
                    'start_time': result['entity'].get('metadata', {}).get('start_time', 0.0),
                    'end_time': result['entity'].get('metadata', {}).get('end_time', 0.0),
                    'duration': result['entity'].get('metadata', {}).get('duration', 0.0),
                    'frame_path': result['entity'].get('metadata', {}).get('frame_path', ''),
                    'relative_position': result['entity'].get('metadata', {}).get('relative_position', 0.0)
                })
            
            self.logger.debug(f"向量搜索完成 {collection}: 找到 {len(formatted_results)} 个结果")
            return formatted_results
        except Exception as e:
            self.logger.error(f"搜索向量失败: {collection}, 错误: {e}")
            raise
    
    async def insert_vectors(self, collection: str, vectors: List[List[float]], 
                           ids: List[str], metadata: List[Dict] = None) -> None:
        """插入向量"""
        try:
            if not self.client.has_collection(collection):
                raise ValueError(f"集合不存在: {collection}")
            
            # 准备插入数据
            insert_data = []
            for i, (vector, vector_id) in enumerate(zip(vectors, ids)):
                data = {
                    "id": vector_id,
                    "vector": vector,
                    "file_path": metadata[i].get("file_path", "") if metadata else "",
                    "file_type": metadata[i].get("file_type", "") if metadata else "",
                    "task_id": metadata[i].get("task_id", "") if metadata else "",
                    "timestamp": metadata[i].get("timestamp", 0.0) if metadata else 0.0,
                    "metadata": metadata[i] if metadata else {}
                }
                insert_data.append(data)
            
            # 插入向量
            self.client.insert(collection, insert_data)
            
            # 刷新集合以确保数据可用
            self.client.flush(collection)
            
            self.logger.info(f"插入向量到集合 {collection}: {len(vectors)} 个")
        except Exception as e:
            self.logger.error(f"插入向量失败: {collection}, 错误: {e}")
            raise
    
    async def search_vectors(self, collection: str, query_vector: List[float], 
                           limit: int) -> List[Dict]:
        """搜索向量"""
        try:
            if not self.client.has_collection(collection):
                raise ValueError(f"集合不存在: {collection}")
            
            # 执行搜索
            results = self.client.search(
                collection,
                [query_vector],
                limit=limit,
                output_fields=["id", "file_path", "file_type", "task_id", "metadata"]
            )
            
            # 格式化结果
            formatted_results = []
            for result in results[0]:  # 取第一个查询的结果
                formatted_results.append({
                    'id': result['id'],
                    'distance': result['distance'],
                    'file_path': result['entity'].get('file_path', ''),
                    'file_type': result['entity'].get('file_type', ''),
                    'task_id': result['entity'].get('task_id', ''),
                    'metadata': result['entity'].get('metadata', {})
                })
            
            self.logger.debug(f"向量搜索完成 {collection}: 找到 {len(formatted_results)} 个结果")
            return formatted_results
        except Exception as e:
            self.logger.error(f"搜索向量失败: {collection}, 错误: {e}")
            raise
    
    async def delete_vectors(self, collection: str, ids: List[str]) -> None:
        """删除向量"""
        try:
            if not self.client.has_collection(collection):
                raise ValueError(f"集合不存在: {collection}")
            
            # 删除向量
            expr = f"id in [{','.join([f'\"{id}\"' for id in ids])}]"
            self.client.delete(collection, expr)
            
            self.logger.info(f"删除向量从集合 {collection}: {len(ids)} 个")
        except Exception as e:
            self.logger.error(f"删除向量失败: {collection}, 错误: {e}")
            raise
    
    async def batch_insert(self, collection: str, vectors: List[List[float]], 
                          ids: List[str]) -> None:
        """批量插入向量"""
        # 对于大量向量，分批插入
        batch_size = 1000
        for i in range(0, len(vectors), batch_size):
            batch_vectors = vectors[i:i+batch_size]
            batch_ids = ids[i:i+batch_size]
            
            await self.insert_vectors(collection, batch_vectors, batch_ids)
    
    async def batch_search(self, collection: str, query_vectors: List[List[float]], 
                          limit: int) -> List[List[Dict]]:
        """批量搜索向量"""
        results = []
        for query_vector in query_vectors:
            result = await self.search_vectors(collection, query_vector, limit)
            results.append(result)
        return results
    
    async def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """获取集合信息"""
        try:
            if not self.client.has_collection(collection_name):
                return {}
            
            # 获取集合统计信息
            stats = self.client.get_collection_stats(collection_name)
            
            return {
                'name': collection_name,
                'entity_count': stats['row_count'],
                'dimension': self.collections.get(collection_name, {}).get('dimension', 0)
            }
        except Exception as e:
            self.logger.error(f"获取集合信息失败: {collection_name}, 错误: {e}")
            return {}
    
    async def get_all_collections(self) -> List[str]:
        """获取所有集合名称"""
        try:
            # 获取Milvus中的所有集合
            all_collections = self.client.list_collections()
            
            # 只返回我们创建的集合
            our_collections = [name for name in all_collections 
                              if name in self.collections]
            
            return our_collections
        except Exception as e:
            self.logger.error(f"获取集合列表失败: {e}")
            return []
