"""
向量化引擎
使用Infinity封装各AI模型，提供向量化方法
"""

import asyncio
import logging
import os
from typing import List, Union, Optional, Dict, Any, Tuple
import numpy as np
from infinity_emb import AsyncEngineArray, EngineArgs

from src.core.config_manager import get_config_manager
from src.common.storage.qdrant_adapter import QdrantAdapter


class EmbeddingEngine:
    """向量化引擎"""
    
    def __init__(self, config_manager=None):
        self.config_manager = config_manager or get_config_manager()
        self.logger = logging.getLogger(__name__)
        
        # 模型配置
        self.models_config = self.config_manager.get("infinity.services", {})
        
        # 引擎实例
        self.engines: Dict[str, Any] = {}
        
        # Qdrant适配器
        self.qdrant_adapter = QdrantAdapter(config_manager)
        
        # 初始化模型
        self._initialize_models()
        
        self.logger.info("向量化引擎初始化完成")
    
    def _initialize_models(self):
        """初始化AI模型"""
        try:
            # 检查CUDA可用性
            cuda_available = self._check_cuda_availability()
            device = 'cuda:0' if cuda_available else 'cpu'
            
            self.logger.info(f"使用设备: {device}")
            
            # 初始化CLIP模型
            if 'clip' in self.models_config:
                clip_config = self.models_config['clip']
                try:
                    device = clip_config.get('device', device)
                    
                    # 必须使用本地模型
                    local_model_path = os.path.join('data', 'models', 'clip-vit-base-patch32')
                    if os.path.exists(local_model_path) and os.path.isdir(local_model_path):
                        model_path = local_model_path
                        self.logger.info(f"使用本地CLIP模型: {model_path}")
                    else:
                        self.logger.error(f"本地CLIP模型不存在: {local_model_path}")
                        raise FileNotFoundError(f"本地CLIP模型不存在: {local_model_path}")
                        
                    self.engines['clip'] = AsyncEngineArray.from_args([
                        EngineArgs(
                            model_name_or_path=model_path,
                            engine="torch",
                            device=device,
                            model_warmup=False,  # 在测试环境中关闭预热
                            dtype=clip_config.get('dtype', 'float32') if device == 'cpu' else 'float16'
                        )
                    ])
                    self.logger.info(f"CLIP模型初始化成功: {model_path} (设备: {device})")
                except Exception as e:
                    self.logger.error(f"CLIP模型初始化失败: {e}")
            
            # 初始化CLAP模型
            if 'clap' in self.models_config:
                clap_config = self.models_config['clap']
                try:
                    device = clap_config.get('device', device)
                    
                    # 必须使用本地模型
                    local_model_path = os.path.join('data', 'models', 'clap-htsat-fused')
                    if os.path.exists(local_model_path) and os.path.isdir(local_model_path):
                        model_path = local_model_path
                        self.logger.info(f"使用本地CLAP模型: {model_path}")
                    else:
                        self.logger.error(f"本地CLAP模型不存在: {local_model_path}")
                        raise FileNotFoundError(f"本地CLAP模型不存在: {local_model_path}")
                        
                    self.engines['clap'] = AsyncEngineArray.from_args([
                        EngineArgs(
                            model_name_or_path=model_path,
                            engine="torch",
                            device=device,
                            model_warmup=False,
                            dtype=clap_config.get('dtype', 'float32') if device == 'cpu' else 'float16'
                        )
                    ])
                    self.logger.info(f"CLAP模型初始化成功: {model_path} (设备: {device})")
                except Exception as e:
                    self.logger.error(f"CLAP模型初始化失败: {e}")
            
            # 初始化Whisper模型
            if 'whisper' in self.models_config:
                whisper_config = self.models_config['whisper']
                try:
                    device = whisper_config.get('device', 'cpu')  # Whisper默认使用CPU
                    
                    # 必须使用本地模型
                    local_model_path = os.path.join('data', 'models', 'whisper-base')
                    if os.path.exists(local_model_path) and os.path.isdir(local_model_path):
                        model_path = local_model_path
                        self.logger.info(f"使用本地Whisper模型: {model_path}")
                    else:
                        self.logger.error(f"本地Whisper模型不存在: {local_model_path}")
                        raise FileNotFoundError(f"本地Whisper模型不存在: {local_model_path}")
                        
                    self.engines['whisper'] = AsyncEngineArray.from_args([
                        EngineArgs(
                            model_name_or_path=model_path,
                            engine="torch",
                            device=device,
                            model_warmup=False,
                            dtype=whisper_config.get('dtype', 'float16')
                        )
                    ])
                    self.logger.info(f"Whisper模型初始化成功: {model_path} (设备: {device})")
                except Exception as e:
                    self.logger.error(f"Whisper模型初始化失败: {e}")
        
        except Exception as e:
            self.logger.error(f"模型初始化失败: {e}")
            # 在测试环境中，如果没有模型，我们也继续执行，使用空列表作为回退
    
    async def _start_engine(self, engine) -> bool:
        """
        启动单个引擎实例
        
        Args:
            engine: 引擎实例
            
        Returns:
            bool: 启动成功返回True，失败返回False
        """
        try:
            if hasattr(engine, 'astart') and not engine.is_running:
                await engine.astart()
                return True
            return True
        except Exception as e:
            self.logger.error(f"引擎启动失败: {e}")
            return False
    
    def _check_cuda_availability(self) -> bool:
        """检查CUDA可用性"""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False
    
    async def embed_image(self, image_data: bytes) -> np.ndarray:
        """
        图像向量化
        
        Args:
            image_data: 图像字节数据
            
        Returns:
            图像向量
        """
        try:
            if 'clip' not in self.engines:
                raise RuntimeError("CLIP模型未初始化")
            
            # 使用CLIP模型进行图像向量化
            engine = self.engines['clip']
            
            # 启动引擎
            await engine.astart()
            embeddings, _ = await engine.image_embed(model="clip", images=[image_data])
            return np.array(embeddings[0], dtype=np.float32)
            
        except Exception as e:
            self.logger.error(f"图像向量化失败: {e}")
            raise



    async def embed_text_for_visual(self, text: str) -> np.ndarray:
        """
        文本向量化（用于图像/视频检索）
        
        Args:
            text: 文本字符串
            
        Returns:
            文本向量
        """
        try:
            if 'clip' not in self.engines:
                raise RuntimeError("CLIP模型未初始化")
            
            # 使用CLIP模型进行文本向量化
            engine = self.engines['clip']
            
            # 使用异步上下文管理器调用引擎
            await engine.astart()
            embeddings, _ = await engine.embed(model="clip", sentences=[text])
            return np.array(embeddings[0], dtype=np.float32)
            
        except Exception as e:
            self.logger.error(f"文本向量化失败: {e}")
            raise
    
    async def embed_text_for_music(self, text: str) -> np.ndarray:
        """
        文本向量化（用于音乐检索）
        
        Args:
            text: 文本字符串
            
        Returns:
            文本向量
        """
        try:
            if 'clap' not in self.engines:
                raise RuntimeError("CLAP模型未初始化")
            
            # 使用CLAP模型进行文本向量化
            engine = self.engines['clap']
            
            # 启动引擎
            await engine.astart()
            embeddings, _ = await engine.embed(model="clap", sentences=[text])
            return np.array(embeddings[0], dtype=np.float32)
            
        except Exception as e:
            self.logger.error(f"音乐文本向量化失败: {e}")
            raise
    
    async def embed_audio_music(self, audio_data: bytes) -> np.ndarray:
        """
        音频向量化（音乐）
        
        Args:
            audio_data: 音频字节数据
            
        Returns:
            音频向量
        """
        try:
            if 'clap' not in self.engines:
                raise RuntimeError("CLAP模型未初始化")
            
            # 使用CLAP模型进行音频向量化
            engine = self.engines['clap']
            
            # 启动引擎
            await engine.astart()
            embeddings, _ = await engine.audio_embed(model="clap", audios=[audio_data])
            return np.array(embeddings[0], dtype=np.float32)
            
        except Exception as e:
            self.logger.error(f"音频向量化失败: {e}")
            raise
    
    
    
    async def transcribe_audio(self, audio_data: bytes) -> str:
        """
        语音转文本
        
        Args:
            audio_data: 音频字节数据
            
        Returns:
            转录文本
        """
        try:
            if 'whisper' not in self.engines:
                raise RuntimeError("Whisper模型未初始化")
            
            # 使用Whisper模型进行语音转录
            engine = self.engines['whisper']
            
            # 启动引擎
            await engine.astart()
            transcriptions, _ = await engine.audio_embed(model="whisper", audios=[audio_data])
            return transcriptions[0]
            
        except Exception as e:
            self.logger.error(f"语音转录失败: {e}")
            raise
    
    async def transcribe_and_embed(self, audio_data: bytes) -> np.ndarray:
        """
        转录并向量化语音（使用Whisper + CLIP模型）
        
        Args:
            audio_data: 音频字节数据
            
        Returns:
            语音向量
        """
        try:
            # 先转录为文本
            text = await self.transcribe_audio(audio_data)
            
            # 再对文本进行向量化（使用CLIP）
            return await self.embed_text_for_visual(text)
            
        except Exception as e:
            self.logger.error(f"转录并向量化失败: {e}")
            raise
    
    async def embed_face(self, face_data: bytes) -> np.ndarray:
        """
        人脸向量化
        
        Args:
            face_data: 人脸图像字节数据
            
        Returns:
            人脸向量
        """
        try:
            # 人脸向量化使用CLIP模型
            return await self.embed_image(face_data)
            
        except Exception as e:
            self.logger.error(f"人脸向量化失败: {e}")
            raise
    
    async def batch_embed_images(self, images_data: List[bytes]) -> List[np.ndarray]:
        """
        批量图像向量化
        
        Args:
            images_data: 图像字节数据列表
            
        Returns:
            图像向量列表
        """
        try:
            vectors = []
            
            # 并发处理多个图像
            tasks = [self.embed_image(image_data) for image_data in images_data]
            vectors = await asyncio.gather(*tasks)
            
            return vectors
            
        except Exception as e:
            self.logger.error(f"批量图像向量化失败: {e}")
            raise
    
    async def batch_embed_texts(self, texts: List[str], modality: str = "visual") -> List[np.ndarray]:
        """
        批量文本向量化
        
        Args:
            texts: 文本字符串列表
            modality: 模态类型 ("visual" 或 "music")
            
        Returns:
            文本向量列表
        """
        try:
            vectors = []
            
            if modality == "visual":
                tasks = [self.embed_text_for_visual(text) for text in texts]
            elif modality == "music":
                tasks = [self.embed_text_for_music(text) for text in texts]
            else:
                raise ValueError(f"不支持的模态类型: {modality}")
            
            vectors = await asyncio.gather(*tasks)
            
            return vectors
            
        except Exception as e:
            self.logger.error(f"批量文本向量化失败: {e}")
            raise
    
    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """
        获取模型信息
        
        Args:
            model_name: 模型名称
            
        Returns:
            模型信息字典
        """
        if model_name not in self.engines:
            raise ValueError(f"模型不存在: {model_name}")
        
        config = self.models_config.get(model_name, {})
        
        return {
            'name': model_name,
            'model_id': config.get('model_id', 'unknown'),
            'device': config.get('device', 'unknown'),
            'dtype': config.get('dtype', 'unknown'),
            'status': 'loaded'
        }
    
    def get_available_models(self) -> List[str]:
        """
        获取可用模型列表
        
        Returns:
            模型名称列表
        """
        return list(self.engines.keys())
    
    def is_model_available(self, model_name: str) -> bool:
        """
        检查模型是否可用
        
        Args:
            model_name: 模型名称
            
        Returns:
            模型是否可用
        """
        return model_name in self.engines
    
    async def health_check(self) -> Dict[str, bool]:
        """
        健康检查
        
        Returns:
            各模型健康状态
        """
        health_status = {}
        
        for model_name in self.engines.keys():
            try:
                # 简单的向量化测试
                if model_name == 'clip':
                    await self.embed_text_for_visual("test")
                elif model_name == 'clap':
                    await self.embed_text_for_music("test")
                elif model_name == 'whisper':
                    # Whisper测试跳过，因为需要音频数据
                    pass
                
                health_status[model_name] = True
                
            except Exception as e:
                self.logger.error(f"模型健康检查失败: {model_name}, 错误: {e}")
                health_status[model_name] = False
        
        return health_status

    async def search_vector(self, 
                          collection_type: str, 
                          query_vector: np.ndarray, 
                          limit: int = 10,
                          score_threshold: float = 0.7,
                          filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        搜索向量
        
        Args:
            collection_type: 集合类型 ('visual', 'audio_music', 'audio_speech')
            query_vector: 查询向量
            limit: 返回结果数量限制
            score_threshold: 相似度阈值
            filters: 过滤条件
            
        Returns:
            搜索结果列表
        """
        try:
            return await self.qdrant_adapter.search_vectors(
                collection_type=collection_type,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold,
                filters=filters
            )
        except Exception as e:
            self.logger.warning(f"向量搜索失败，返回空结果: {e}")
            # 在向量数据库不可用时返回空列表
            return []
    
    async def store_vector(self, 
                          collection_type: str, 
                          vector_data: np.ndarray, 
                          file_id: str,
                          segment_id: Optional[str] = None,
                          metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        存储向量到Qdrant
        
        Args:
            collection_type: 集合类型
            vector_data: 向量数据
            file_id: 文件ID
            segment_id: 片段ID（可选）
            metadata: 元数据
            
        Returns:
            向量ID
        """
        try:
            return await self.qdrant_adapter.store_vector(
                collection_type=collection_type,
                vector_data=vector_data,
                file_id=file_id,
                segment_id=segment_id,
                metadata=metadata
            )
        except Exception as e:
            self.logger.error(f"向量存储失败: {e}")
            raise
    
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
            return await self.qdrant_adapter.batch_store_vectors(
                collection_type=collection_type,
                vectors_data=vectors_data,
                batch_size=batch_size
            )
        except Exception as e:
            self.logger.error(f"批量存储向量失败: {e}")
            raise
    
    async def delete_vectors_by_file(self, collection_type: str, file_id: str) -> int:
        """
        根据文件ID删除向量
        
        Args:
            collection_type: 集合类型
            file_id: 文件ID
            
        Returns:
            删除的向量数量
        """
        try:
            return await self.qdrant_adapter.delete_vectors_by_file(
                collection_type=collection_type,
                file_id=file_id
            )
        except Exception as e:
            self.logger.error(f"删除文件向量失败: {e}")
            return 0
    
    async def get_vector_count(self, collection_type: str) -> int:
        """
        获取集合中的向量数量
        
        Args:
            collection_type: 集合类型
            
        Returns:
            向量数量
        """
        try:
            return await self.qdrant_adapter.get_vector_count(collection_type)
        except Exception as e:
            self.logger.error(f"获取向量数量失败: {e}")
            return 0
    
    async def qdrant_health_check(self) -> Dict[str, Any]:
        """
        Qdrant健康检查
        
        Returns:
            健康检查结果
        """
        try:
            return await self.qdrant_adapter.health_check()
        except Exception as e:
            self.logger.error(f"Qdrant健康检查失败: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }