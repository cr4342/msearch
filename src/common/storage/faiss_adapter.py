"""
FAISS向量存储适配器
为多模态检索系统提供FAISS向量数据库的封装
"""

import asyncio
import logging
import uuid
import pickle
import os
from typing import Dict, Any, Optional, List, Tuple

import numpy as np
import faiss

from src.core.config_manager import get_config_manager


class FaissAdapter:
    """FAISS向量存储适配器"""
    
    def __init__(self, config_manager=None):
        self.config_manager = config_manager or get_config_manager()
        self.logger = logging.getLogger(__name__)
        
        # FAISS配置
        self.data_dir = self.config_manager.get("database.faiss.data_dir", "./data/faiss")
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 集合配置
        self.collections_config = self.config_manager.get("database.faiss.collections", {})
        
        # 客户端（FAISS索引字典）
        self.indices: Dict[str, faiss.Index] = {}
        self.metadata_stores: Dict[str, Dict[str, Any]] = {}
        
        # 集合映射
        self.collection_map = {
            'visual': self.collections_config.get('visual_vectors', 'visual_vectors'),
            'audio_music': self.collections_config.get('audio_music_vectors', 'audio_music_vectors'),
            'audio_speech': self.collections_config.get('audio_speech_vectors', 'audio_speech_vectors'),
            'face': self.collections_config.get('face_vectors', 'face_vectors'),
            'text': self.collections_config.get('text_vectors', 'text_vectors')
        }
        
        self.logger.info("FAISS适配器初始化完成")
    
    async def connect(self) -> bool:
        """连接到FAISS（加载索引）"""
        try:
            await self.initialize()
            return True
        except Exception as e:
            self.logger.error(f"FAISS连接失败: {e}")
            return False
    
    async def disconnect(self):
        """断开FAISS连接（保存索引）"""
        try:
            # 保存所有索引
            for collection_name, index in self.indices.items():
                await self._save_index(collection_name, index)
            
            # 清空资源
            self.indices.clear()
            self.metadata_stores.clear()
            self.logger.info("FAISS连接已断开")
        except Exception as e:
            self.logger.error(f"断开FAISS连接失败: {e}")
    
    async def initialize(self):
        """初始化FAISS索引"""
        try:
            # 初始化所有集合
            await self._initialize_collections()
            
            self.logger.info("FAISS索引初始化完成")
            
        except Exception as e:
            self.logger.error(f"FAISS初始化失败: {e}")
            raise
    
    async def _initialize_collections(self):
        """初始化所有向量集合"""
        try:
            # 检查并创建视觉向量集合
            await self._create_collection_if_not_exists(
                self.collection_map['visual'],
                512,  # CLIP模型向量维度
                "视觉向量集合，用于图像和视频检索"
            )
            
            # 检查并创建音频音乐向量集合
            await self._create_collection_if_not_exists(
                self.collection_map['audio_music'],
                512,  # CLAP模型向量维度
                "音频音乐向量集合，用于音乐检索"
            )
            
            # 检查并创建音频语音向量集合
            await self._create_collection_if_not_exists(
                self.collection_map['audio_speech'],
                512,  # Whisper模型向量维度
                "音频语音向量集合，用于语音检索"
            )
            
            # 检查并创建人脸向量集合
            await self._create_collection_if_not_exists(
                self.collection_map['face'],
                512,  # FaceNet模型向量维度
                "人脸向量集合，用于人脸检索"
            )
            
            # 检查并创建文本向量集合
            await self._create_collection_if_not_exists(
                self.collection_map['text'],
                512,  # 文本模型向量维度
                "文本向量集合，用于文本检索"
            )
            
            self.logger.info("FAISS集合初始化完成")
            
        except Exception as e:
            self.logger.error(f"集合初始化失败: {e}")
            raise
    
    async def _create_collection_if_not_exists(self, collection_name: str, vector_size: int, description: str):
        """创建集合（如果不存在）"""
        try:
            index_path = os.path.join(self.data_dir, f"{collection_name}.index")
            metadata_path = os.path.join(self.data_dir, f"{collection_name}_metadata.pkl")
            
            if os.path.exists(index_path):
                # 加载已存在的索引
                index = faiss.read_index(index_path)
                self.indices[collection_name] = index
                
                # 加载元数据
                if os.path.exists(metadata_path):
                    with open(metadata_path, 'rb') as f:
                        self.metadata_stores[collection_name] = pickle.load(f)
                else:
                    self.metadata_stores[collection_name] = {}
                
                self.logger.debug(f"集合已存在: {collection_name}")
            else:
                # 创建新索引
                index = faiss.IndexFlatIP(vector_size)  # 内积索引，适用于归一化向量
                self.indices[collection_name] = index
                self.metadata_stores[collection_name] = {}
                
                # 保存索引
                await self._save_index(collection_name, index)
                
                self.logger.info(f"创建集合成功: {collection_name}")
                
        except Exception as e:
            self.logger.error(f"创建集合失败: {collection_name}, 错误: {e}")
            raise
    
    async def _save_index(self, collection_name: str, index: faiss.Index):
        """保存索引到文件"""
        try:
            index_path = os.path.join(self.data_dir, f"{collection_name}.index")
            metadata_path = os.path.join(self.data_dir, f"{collection_name}_metadata.pkl")
            
            # 保存索引
            faiss.write_index(index, index_path)
            
            # 保存元数据
            with open(metadata_path, 'wb') as f:
                pickle.dump(self.metadata_stores[collection_name], f)
            
            self.logger.debug(f"索引保存成功: {collection_name}")
            
        except Exception as e:
            self.logger.error(f"保存索引失败: {collection_name}, 错误: {e}")
            raise
    
    async def store_vector(self, 
                          collection_type: str, 
                          vector_data: np.ndarray, 
                          file_id: str,
                          segment_id: Optional[str] = None,
                          metadata: Optional[Dict[str, Any]] = None,
                          vector_id: Optional[str] = None) -> str:
        """
        存储向量
        
        Args:
            collection_type: 集合类型 ('visual', 'audio_music', 'audio_speech')
            vector_data: 向量数据
            file_id: 文件ID
            segment_id: 片段ID（可选）
            metadata: 元数据
            vector_id: 向量ID（可选，如果为None则自动生成）
            
        Returns:
            向量ID
        """
        try:
            collection_name = self.collection_map.get(collection_type)
            if not collection_name:
                raise ValueError(f"不支持的集合类型: {collection_type}")
            
            # 生成或使用提供的向量ID
            if vector_id is None:
                vector_id = str(uuid.uuid4())
            
            # 准备负载数据
            payload = {
                'file_id': file_id,
                'segment_id': segment_id,
                'collection_type': collection_type,
                'created_at': asyncio.get_event_loop().time(),
                **(metadata or {})
            }
            
            # 确保索引存在
            if collection_name not in self.indices:
                await self._create_collection_if_not_exists(collection_name, vector_data.shape[-1], "")
            
            # 添加向量到索引
            index = self.indices[collection_name]
            index.add(np.array([vector_data], dtype=np.float32))
            
            # 保存元数据
            # 向量ID映射到索引位置
            self.metadata_stores[collection_name][vector_id] = {
                'payload': payload,
                'index': index.ntotal - 1  # 最新添加的向量索引位置
            }
            
            # 保存索引
            await self._save_index(collection_name, index)
            
            self.logger.debug(f"向量存储成功: {vector_id}, 集合: {collection_name}")
            return vector_id
            
        except Exception as e:
            self.logger.error(f"存储向量失败: {e}")
            raise
    
    async def search_vectors(self, 
                           collection_type: str, 
                           query_vector: np.ndarray, 
                           limit: int = 10,
                           score_threshold: float = 0.7,
                           filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        搜索向量
        
        Args:
            collection_type: 集合类型
            query_vector: 查询向量
            limit: 返回结果数量限制
            score_threshold: 相似度阈值
            filters: 过滤条件
            
        Returns:
            搜索结果列表
        """
        try:
            collection_name = self.collection_map.get(collection_type)
            if not collection_name:
                raise ValueError(f"不支持的集合类型: {collection_type}")
            
            # 确保索引存在
            if collection_name not in self.indices:
                await self._create_collection_if_not_exists(collection_name, query_vector.shape[-1], "")
            
            index = self.indices[collection_name]
            metadata_store = self.metadata_stores[collection_name]
            
            if index.ntotal == 0:
                return []
            
            # 搜索向量
            distances, indices = index.search(np.array([query_vector], dtype=np.float32), limit)
            
            # 格式化结果
            results = []
            for i in range(indices.shape[1]):
                idx = indices[0][i]
                distance = distances[0][i]
                
                # 余弦相似度（因为使用了内积索引，且向量已归一化）
                score = distance
                
                if score < score_threshold:
                    continue
                
                # 查找对应的向量ID
                vector_id = None
                for vid, info in metadata_store.items():
                    if info['index'] == idx:
                        vector_id = vid
                        break
                
                if vector_id is not None:
                    results.append({
                        'id': vector_id,
                        'score': score,
                        'payload': metadata_store[vector_id]['payload']
                    })
            
            return results
            
        except Exception as e:
            self.logger.error(f"搜索向量失败: {e}")
            raise
    
    async def create_collection(self, 
                              collection_name: str, 
                              vector_size: int = 512,
                              distance_metric: str = "cosine") -> bool:
        """创建集合"""
        try:
            await self._create_collection_if_not_exists(collection_name, vector_size, "")
            return True
            
        except Exception as e:
            self.logger.error(f"创建集合失败: {collection_name}, 错误: {e}")
            return False
    
    async def store_vectors(self, 
                          collection_name: str,
                          vectors: List[List[float]],
                          point_ids: Optional[List[str]] = None,
                          payloads: Optional[List[Dict[str, Any]]] = None) -> List[str]:
        """存储向量"""
        try:
            # 确保索引存在
            if collection_name not in self.indices:
                await self._create_collection_if_not_exists(collection_name, len(vectors[0]), "")
            
            # 生成ID列表
            if point_ids is None:
                point_ids = [str(uuid.uuid4()) for _ in vectors]
            
            if payloads is None:
                payloads = [{} for _ in vectors]
            
            # 转换向量格式
            vectors_np = np.array(vectors, dtype=np.float32)
            
            # 添加向量到索引
            index = self.indices[collection_name]
            index.add(vectors_np)
            
            # 保存元数据
            start_idx = index.ntotal - len(vectors)
            for i, (point_id, payload) in enumerate(zip(point_ids, payloads)):
                self.metadata_stores[collection_name][point_id] = {
                    'payload': payload,
                    'index': start_idx + i
                }
            
            # 保存索引
            await self._save_index(collection_name, index)
            
            return point_ids
            
        except Exception as e:
            self.logger.error(f"存储向量失败: {e}")
            raise
    
    async def delete_vectors(self, 
                           collection_name: str,
                           point_ids: List[str]) -> bool:
        """删除向量"""
        try:
            # FAISS不支持直接删除向量，需要重建索引
            if collection_name not in self.indices:
                return False
            
            index = self.indices[collection_name]
            metadata_store = self.metadata_stores[collection_name]
            
            # 收集需要保留的向量和元数据
            keep_indices = []
            new_metadata = {}
            
            # 找出需要删除的索引位置
            delete_indices = {metadata_store[pid]['index'] for pid in point_ids if pid in metadata_store}
            
            # 收集需要保留的向量
            if index.ntotal > 0:
                # 获取所有向量
                all_vectors = faiss.vector_to_array(index).reshape(index.ntotal, -1)
                
                # 过滤需要保留的向量
                keep_vectors = []
                for i in range(index.ntotal):
                    if i not in delete_indices:
                        keep_vectors.append(all_vectors[i])
                        keep_indices.append(i)
                
                # 重建索引
                new_index = faiss.IndexFlatIP(all_vectors.shape[1])
                if keep_vectors:
                    new_index.add(np.array(keep_vectors, dtype=np.float32))
                
                # 更新索引
                self.indices[collection_name] = new_index
                
                # 更新元数据
                for vector_id, info in metadata_store.items():
                    if info['index'] not in delete_indices:
                        # 更新索引位置
                        new_index_pos = keep_indices.index(info['index'])
                        new_metadata[vector_id] = {
                            'payload': info['payload'],
                            'index': new_index_pos
                        }
                
                self.metadata_stores[collection_name] = new_metadata
                
                # 保存索引
                await self._save_index(collection_name, new_index)
            
            return True
            
        except Exception as e:
            self.logger.error(f"删除向量失败: {e}")
            return False
    
    async def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """获取集合信息"""
        try:
            if collection_name not in self.indices:
                return {}
            
            index = self.indices[collection_name]
            metadata_store = self.metadata_stores[collection_name]
            
            return {
                'name': collection_name,
                'vectors_count': index.ntotal,
                'status': 'healthy',
                'dimension': index.d
            }
            
        except Exception as e:
            self.logger.error(f"获取集合信息失败: {collection_name}, 错误: {e}")
            return {}
    
    async def delete_vector(self, collection_type: str, vector_id: str) -> bool:
        """删除单个向量"""
        try:
            collection_name = self.collection_map.get(collection_type)
            if not collection_name:
                raise ValueError(f"不支持的集合类型: {collection_type}")
            
            return await self.delete_vectors(collection_name, [vector_id])
            
        except Exception as e:
            self.logger.error(f"删除向量失败: {e}")
            return False
    
    async def delete_vectors_by_file(self, collection_type: str, file_id: str) -> int:
        """根据文件ID删除向量"""
        try:
            collection_name = self.collection_map.get(collection_type)
            if not collection_name:
                raise ValueError(f"不支持的集合类型: {collection_type}")
            
            metadata_store = self.metadata_stores[collection_name]
            
            # 查找该文件的所有向量ID
            file_vector_ids = []
            for vector_id, info in metadata_store.items():
                if info['payload']['file_id'] == file_id:
                    file_vector_ids.append(vector_id)
            
            if not file_vector_ids:
                return 0
            
            # 删除向量
            success = await self.delete_vectors(collection_name, file_vector_ids)
            
            self.logger.info(f"文件向量删除完成: {file_id}, 集合: {collection_name}")
            return len(file_vector_ids) if success else 0
            
        except Exception as e:
            self.logger.error(f"删除文件向量失败: {e}")
            return 0
    
    async def get_vector_count(self, collection_type: str) -> int:
        """获取集合中的向量数量"""
        try:
            collection_name = self.collection_map.get(collection_type)
            if not collection_name:
                raise ValueError(f"不支持的集合类型: {collection_type}")
            
            if collection_name not in self.indices:
                return 0
            
            index = self.indices[collection_name]
            return index.ntotal
            
        except Exception as e:
            self.logger.error(f"获取向量数量失败: {e}")
            return 0
    
    async def batch_store_vectors(self, 
                                collection_type: str, 
                                vectors_data: List[Tuple[np.ndarray, str, Optional[str], Dict[str, Any]]],
                                batch_size: int = 100) -> List[str]:
        """
        批量存储向量
        
        Args:
            collection_type: 集合类型
            vectors_data: 向量数据列表 [(向量, 文件ID, 片段ID, 元数据), ...]
            batch_size: 批处理大小
            
        Returns:
            向量ID列表
        """
        try:
            collection_name = self.collection_map.get(collection_type)
            if not collection_name:
                raise ValueError(f"不支持的集合类型: {collection_type}")
            
            stored_ids = []
            vectors_batch = []
            metadata_batch = []
            
            for vector_data, file_id, segment_id, metadata in vectors_data:
                vector_id = str(uuid.uuid4())
                stored_ids.append(vector_id)
                
                # 准备负载数据
                payload = {
                    'file_id': file_id,
                    'segment_id': segment_id,
                    'collection_type': collection_type,
                    'created_at': asyncio.get_event_loop().time(),
                    **(metadata or {})
                }
                
                vectors_batch.append(vector_data)
                metadata_batch.append((vector_id, payload))
                
                # 批量插入
                if len(vectors_batch) >= batch_size:
                    # 确保索引存在
                    if collection_name not in self.indices:
                        await self._create_collection_if_not_exists(collection_name, vector_data.shape[-1], "")
                    
                    index = self.indices[collection_name]
                    
                    # 添加向量到索引
                    vectors_np = np.array(vectors_batch, dtype=np.float32)
                    index.add(vectors_np)
                    
                    # 保存元数据
                    start_idx = index.ntotal - len(vectors_batch)
                    for i, (vector_id, payload) in enumerate(metadata_batch):
                        self.metadata_stores[collection_name][vector_id] = {
                            'payload': payload,
                            'index': start_idx + i
                        }
                    
                    # 清空批次
                    vectors_batch = []
                    metadata_batch = []
            
            # 插入剩余的向量
            if vectors_batch:
                if collection_name not in self.indices:
                    await self._create_collection_if_not_exists(collection_name, vectors_batch[0].shape[-1], "")
                
                index = self.indices[collection_name]
                vectors_np = np.array(vectors_batch, dtype=np.float32)
                index.add(vectors_np)
                
                # 保存元数据
                start_idx = index.ntotal - len(vectors_batch)
                for i, (vector_id, payload) in enumerate(metadata_batch):
                    self.metadata_stores[collection_name][vector_id] = {
                        'payload': payload,
                        'index': start_idx + i
                    }
            
            # 保存索引
            if collection_name in self.indices:
                await self._save_index(collection_name, self.indices[collection_name])
            
            self.logger.info(f"批量存储向量完成: {len(stored_ids)} 个向量, 集合: {collection_name}")
            return stored_ids
            
        except Exception as e:
            self.logger.error(f"批量存储向量失败: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            # 获取所有集合信息
            collections_info = {}
            for collection_type, collection_name in self.collection_map.items():
                try:
                    info = await self.get_collection_info(collection_name)
                    collections_info[collection_type] = info
                except Exception as e:
                    collections_info[collection_type] = {'error': str(e)}
            
            return {
                'status': 'healthy',
                'faiss': {
                    'data_dir': self.data_dir,
                    'collections': collections_info
                },
                'collections': collections_info,
                'total_vectors': sum(info.get('vectors_count', 0) for info in collections_info.values() if isinstance(info, dict))
            }
            
        except Exception as e:
            self.logger.error(f"FAISS健康检查失败: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
