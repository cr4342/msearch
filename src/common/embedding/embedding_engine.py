"""
向量化引擎
使用Infinity封装各AI模型，提供向量化方法
支持延迟加载和优雅降级
"""

import asyncio
import logging
import os
from typing import List, Union, Optional, Dict, Any, Tuple
import numpy as np

from src.core.config_manager import get_config_manager
from src.common.storage.milvus_adapter import MilvusAdapter
from src.core.retry import async_retry


class EmbeddingEngine:
    """向量化引擎"""
    
    def __init__(self, config_manager=None):
        self.config_manager = config_manager or get_config_manager()
        self.logger = logging.getLogger(__name__)
        
        # 模型配置
        self.models_config = self.config_manager.get("infinity.services", {})
        self.logger.info(f"加载模型配置: {list(self.models_config.keys())}")
        
        # 引擎实例
        self.engines: Dict[str, Any] = {}
        self.engine_initialized: Dict[str, bool] = {}
        
        # Milvus适配器
        self.milvus_adapter = MilvusAdapter(config_manager)
        self.logger.info("Milvus适配器初始化完成")
        
        # 延迟初始化标志
        self._models_loaded = False
        
        # 记录可用模型
        available_models = self.get_available_models()
        self.logger.info(f"向量化引擎初始化完成，可用模型: {available_models}")
        
        # Milvus连接状态
        self._milvus_connected = False
        self._milvus_connecting = False
        
    async def connect_milvus(self):
        """连接Milvus"""
        if self._milvus_connected or self._milvus_connecting:
            return self._milvus_connected
        
        self._milvus_connecting = True
        try:
            if await self.milvus_adapter.connect():
                self.logger.info("Milvus连接成功")
                self._milvus_connected = True
            else:
                self.logger.error("Milvus连接失败")
        except Exception as e:
            self.logger.error(f"Milvus连接异常: {e}")
        finally:
            self._milvus_connecting = False
        
        return self._milvus_connected
    
    def _initialize_engine_module(self):
        """延迟初始化infinity_emb模块"""
        try:
            from infinity_emb import AsyncEngineArray, EngineArgs
            return AsyncEngineArray, EngineArgs
        except ImportError as e:
            self.logger.error(f"无法导入infinity_emb模块: {e}")
            self.logger.warning("将使用模拟模式运行")
            return None, None
    
    def _check_model_path(self, model_path: str) -> bool:
        """检查模型路径是否存在"""
        if model_path is None:
            return False
        return os.path.exists(model_path) and os.path.isdir(model_path)
    
    def _initialize_models(self):
        """初始化AI模型（延迟加载）"""
        if self._models_loaded:
            return
        
        self.logger.info("开始初始化AI模型...")
        
        # 延迟导入
        AsyncEngineArray, EngineArgs = self._initialize_engine_module()
        
        if AsyncEngineArray is None:
            self.logger.warning("infinity_emb模块不可用，使用模拟模式")
            self._models_loaded = True
            return
        
        try:
            # 检查CUDA可用性
            cuda_available = self._check_cuda_availability()
            device = 'cuda:0' if cuda_available else 'cpu'
            self.logger.info(f"使用设备: {device}")
            
            # 初始化CLIP模型
            self._init_clip_model(AsyncEngineArray, EngineArgs, device)
            
            # 初始化CLAP模型
            self._init_clap_model(AsyncEngineArray, EngineArgs, device)
            
            # 初始化Whisper模型
            self._init_whisper_model(AsyncEngineArray, EngineArgs)
            
            self._models_loaded = True
            self.logger.info("所有模型初始化完成")
            
        except Exception as e:
            self.logger.error(f"模型初始化过程中出错: {e}")
            self.logger.warning("将使用模拟模式继续运行")
            self._models_loaded = True
    
    def _init_clip_model(self, AsyncEngineArray, EngineArgs, default_device):
        """初始化CLIP模型"""
        if 'clip' not in self.models_config:
            return
            
        clip_config = self.models_config['clip']
        try:
            device = clip_config.get('device', default_device)
            local_model_path = clip_config.get('model_path')
            
            if local_model_path and self._check_model_path(local_model_path):
                self.engines['clip'] = AsyncEngineArray.from_args([
                    EngineArgs(
                        model_name_or_path=local_model_path,
                        engine="torch",
                        device=device,
                        model_warmup=False,
                        dtype=clip_config.get('dtype', 'float32') if device == 'cpu' else 'float16'
                    )
                ])
                self.engine_initialized['clip'] = True
                self.logger.info(f"CLIP模型初始化成功: {local_model_path} (设备: {device})")
            else:
                self.logger.warning(f"本地CLIP模型路径不存在或未配置: {local_model_path}")
                self.engine_initialized['clip'] = False
                
        except Exception as e:
            self.logger.error(f"CLIP模型初始化失败: {e}")
            self.engine_initialized['clip'] = False
    
    def _init_clap_model(self, AsyncEngineArray, EngineArgs, default_device):
        """初始化CLAP模型"""
        if 'clap' not in self.models_config:
            return
            
        clap_config = self.models_config['clap']
        try:
            device = clap_config.get('device', default_device)
            local_model_path = clap_config.get('model_path')
            
            if local_model_path and self._check_model_path(local_model_path):
                self.engines['clap'] = AsyncEngineArray.from_args([
                    EngineArgs(
                        model_name_or_path=local_model_path,
                        engine="torch",
                        device=device,
                        model_warmup=False,
                        dtype=clap_config.get('dtype', 'float32') if device == 'cpu' else 'float16'
                    )
                ])
                self.engine_initialized['clap'] = True
                self.logger.info(f"CLAP模型初始化成功: {local_model_path} (设备: {device})")
            else:
                self.logger.warning(f"本地CLAP模型路径不存在或未配置: {local_model_path}")
                self.engine_initialized['clap'] = False
                
        except Exception as e:
            self.logger.error(f"CLAP模型初始化失败: {e}")
            self.engine_initialized['clap'] = False
    
    def _init_whisper_model(self, AsyncEngineArray, EngineArgs):
        """初始化Whisper模型"""
        if 'whisper' not in self.models_config:
            return
            
        whisper_config = self.models_config['whisper']
        try:
            device = whisper_config.get('device', 'cpu')
            local_model_path = whisper_config.get('model_path')
            
            if local_model_path and self._check_model_path(local_model_path):
                self.engines['whisper'] = AsyncEngineArray.from_args([
                    EngineArgs(
                        model_name_or_path=local_model_path,
                        engine="torch",
                        device=device,
                        model_warmup=False,
                        dtype=whisper_config.get('dtype', 'float16')
                    )
                ])
                self.engine_initialized['whisper'] = True
                self.logger.info(f"Whisper模型初始化成功: {local_model_path} (设备: {device})")
            else:
                self.logger.warning(f"本地Whisper模型路径不存在或未配置: {local_model_path}")
                self.engine_initialized['whisper'] = False
                
        except Exception as e:
            self.logger.error(f"Whisper模型初始化失败: {e}")
            self.engine_initialized['whisper'] = False
    
    def _check_cuda_availability(self) -> bool:
        """检查CUDA可用性"""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False
    
    def _ensure_model_loaded(self, model_name: str) -> bool:
        """确保模型已加载"""
        if not self._models_loaded:
            self._initialize_models()
        return self.engine_initialized.get(model_name, False)
    
    @async_retry(max_attempts=3, delay=1.0, backoff=2.0)
    async def embed_image(self, image_data: bytes) -> np.ndarray:
        """
        图像向量化
        
        Args:
            image_data: 图像字节数据
            
        Returns:
            图像向量
        """
        async def _do_embed():
            if 'clip' not in self.engines:
                raise RuntimeError("CLIP模型未初始化")
            engine = self.engines['clip']
            await engine.astart()
            embeddings, _ = await engine.image_embed(model="clip", images=[image_data])
            return np.array(embeddings[0], dtype=np.float32)
        
        return await self._safe_embed('clip', _do_embed)
        
    async def _safe_embed(self, model_name: str, embed_fn) -> np.ndarray:
        """安全的向量化调用"""
        if not self._ensure_model_loaded(model_name):
            self.logger.warning(f"{model_name}模型未初始化，返回零向量")
            return np.zeros(512, dtype=np.float32)
        
        try:
            return await embed_fn()
        except RuntimeError as e:
            self.logger.error(f"{model_name}模型运行时错误: {e}")
            return np.zeros(512, dtype=np.float32)
        except ValueError as e:
            self.logger.error(f"{model_name}模型参数错误: {e}")
            return np.zeros(512, dtype=np.float32)
        except asyncio.TimeoutError as e:
            self.logger.error(f"{model_name}向量化超时: {e}")
            return np.zeros(512, dtype=np.float32)
        except ImportError as e:
            self.logger.error(f"{model_name}模型依赖缺失: {e}")
            return np.zeros(512, dtype=np.float32)
        except Exception as e:
            self.logger.error(f"{model_name}向量化失败: {e}")
            return np.zeros(512, dtype=np.float32)
    
    @async_retry(max_attempts=3, delay=1.0, backoff=2.0)
    async def embed_image(self, image_data: bytes) -> np.ndarray:
        """
        图像向量化
        
        Args:
            image_data: 图像字节数据
            
        Returns:
            图像向量
        """
        async def _do_embed():
            if 'clip' not in self.engines:
                raise RuntimeError("CLIP模型未初始化")
            engine = self.engines['clip']
            await engine.astart()
            embeddings, _ = await engine.image_embed(model="clip", images=[image_data])
            return np.array(embeddings[0], dtype=np.float32)
        
        return await self._safe_embed('clip', _do_embed)

    @async_retry(max_attempts=3, delay=1.0, backoff=2.0)
    async def embed_text_for_visual(self, text: str) -> np.ndarray:
        """
        文本向量化（用于图像/视频检索）
        
        Args:
            text: 文本字符串
            
        Returns:
            文本向量
        """
        async def _do_embed():
            if 'clip' not in self.engines:
                raise RuntimeError("CLIP模型未初始化")
            engine = self.engines['clip']
            await engine.astart()
            embeddings, _ = await engine.embed(model="clip", sentences=[text])
            return np.array(embeddings[0], dtype=np.float32)
        
        return await self._safe_embed('clip', _do_embed)
    
    @async_retry(max_attempts=3, delay=1.0, backoff=2.0)
    async def embed_text_for_music(self, text: str) -> np.ndarray:
        """
        文本向量化（用于音乐检索）
        
        Args:
            text: 文本字符串
            
        Returns:
            文本向量
        """
        async def _do_embed():
            if 'clap' not in self.engines:
                raise RuntimeError("CLAP模型未初始化")
            engine = self.engines['clap']
            await engine.astart()
            embeddings, _ = await engine.embed(model="clap", sentences=[text])
            return np.array(embeddings[0], dtype=np.float32)
        
        return await self._safe_embed('clap', _do_embed)
    
    @async_retry(max_attempts=3, delay=1.0, backoff=2.0)
    async def embed_audio_music(self, audio_data: bytes) -> np.ndarray:
        """
        音频向量化（音乐）
        
        Args:
            audio_data: 音频字节数据
            
        Returns:
            音频向量
        """
        async def _do_embed():
            if 'clap' not in self.engines:
                raise RuntimeError("CLAP模型未初始化")
            engine = self.engines['clap']
            await engine.astart()
            
            # 处理音频
            import io
            import librosa
            import soundfile as sf
            
            try:
                audio, sr = sf.read(io.BytesIO(audio_data))
                if len(audio.shape) > 1:
                    audio = audio.mean(axis=1)
                if sr != 48000:
                    audio = librosa.resample(audio, orig_sr=sr, target_sr=48000)
                
                buffer = io.BytesIO()
                sf.write(buffer, audio, 48000, format='wav')
                processed_audio = buffer.getvalue()
            except sf.SoundFileError as e:
                self.logger.error(f"音频文件格式错误: {e}")
                raise RuntimeError(f"音频文件格式错误: {e}")
            except librosa.ParameterError as e:
                self.logger.error(f"音频重采样参数错误: {e}")
                raise RuntimeError(f"音频重采样参数错误: {e}")
            except Exception as e:
                self.logger.error(f"音频预处理错误: {e}")
                raise RuntimeError(f"音频预处理错误: {e}")
            
            embeddings, _ = await engine.audio_embed(model="clap", audios=[processed_audio])
            return np.array(embeddings[0], dtype=np.float32)
        
        return await self._safe_embed('clap', _do_embed)
    
    @async_retry(max_attempts=3, delay=1.0, backoff=2.0)
    async def transcribe_audio(self, audio_data: bytes) -> str:
        """
        语音转文本
        
        Args:
            audio_data: 音频字节数据
            
        Returns:
            转录文本
        """
        async def _do_transcribe():
            if 'whisper' not in self.engines:
                raise RuntimeError("Whisper模型未初始化")
            engine = self.engines['whisper']
            await engine.astart()
            transcriptions, _ = await engine.audio_embed(model="whisper", audios=[audio_data])
            return transcriptions[0]
        
        return await self._safe_embed('whisper', _do_transcribe)
    
    async def transcribe_and_embed(self, audio_data: bytes) -> np.ndarray:
        """
        转录并向量化语音（使用Whisper + CLIP模型）
        
        Args:
            audio_data: 音频字节数据
            
        Returns:
            语音向量
        """
        text = await self.transcribe_audio(audio_data)
        return await self.embed_text_for_visual(text)
    
    async def embed_text(self, text: str, modality: str = "visual") -> np.ndarray:
        """
        文本向量化（通用方法）
        
        Args:
            text: 文本字符串
            modality: 模态类型 ("visual" 或 "music")
            
        Returns:
            文本向量
        """
        if modality == "visual":
            return await self.embed_text_for_visual(text)
        elif modality == "music":
            return await self.embed_text_for_music(text)
        else:
            raise ValueError(f"不支持的模态类型: {modality}")
    
    async def embed_face(self, face_data: bytes) -> np.ndarray:
        """
        人脸向量化
        
        Args:
            face_data: 人脸图像字节数据
            
        Returns:
            人脸向量
        """
        return await self.embed_image(face_data)
    
    async def batch_embed_images(self, images_data: List[bytes]) -> List[np.ndarray]:
        """
        批量图像向量化
        
        Args:
            images_data: 图像字节数据列表
            
        Returns:
            图像向量列表
        """
        tasks = [self.embed_image(image_data) for image_data in images_data]
        return await asyncio.gather(*tasks)
    
    async def batch_embed_texts(self, texts: List[str], modality: str = "visual") -> List[np.ndarray]:
        """
        批量文本向量化
        
        Args:
            texts: 文本字符串列表
            modality: 模态类型 ("visual" 或 "music")
            
        Returns:
            文本向量列表
        """
        if modality == "visual":
            tasks = [self.embed_text_for_visual(text) for text in texts]
        elif modality == "music":
            tasks = [self.embed_text_for_music(text) for text in texts]
        else:
            raise ValueError(f"不支持的模态类型: {modality}")
        
        return await asyncio.gather(*tasks)
    
    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """
        获取模型信息
        
        Args:
            model_name: 模型名称
            
        Returns:
            模型信息字典
        """
        if model_name not in self.engines:
            return {
                'name': model_name,
                'model_id': 'unknown',
                'device': 'unknown',
                'dtype': 'unknown',
                'status': 'unavailable'
            }
        
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
        
        for model_name in self.models_config.keys():
            try:
                if model_name not in self.engines:
                    health_status[model_name] = False
                    continue
                
                if model_name == 'clip':
                    await self.embed_text_for_visual("test")
                elif model_name == 'clap':
                    await self.embed_text_for_music("test")
                elif model_name == 'whisper':
                    health_status[model_name] = True
                    continue
                
                health_status[model_name] = True
                
            except Exception as e:
                self.logger.error(f"模型健康检查失败: {model_name}, 错误: {e}")
                health_status[model_name] = False
        
        return health_status

    async def search_vector(self, 
                          collection_type: str, 
                          query_vector: np.ndarray, 
                          limit: int = 10,
                          score_threshold: float = None,
                          filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        搜索向量
        
        Args:
            collection_type: 集合类型 ('visual', 'audio_music', 'audio_speech')
            query_vector: 查询向量
            limit: 返回结果数量限制
            score_threshold: 相似度阈值，从配置读取默认
            filters: 过滤条件
            
        Returns:
            搜索结果列表
        """
        try:
            # 从配置获取默认阈值
            if score_threshold is None:
                score_threshold = self.config_manager.get(
                    'vector_db.default_score_threshold', 0.7
                )
            
            return await self.milvus_adapter.search_vectors(
                collection_type=collection_type,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold,
                filters=filters
            )
        except Exception as e:
            self.logger.warning(f"向量搜索失败，返回空结果: {e}")
            return []
    
    async def store_vector(self, 
                          collection_type: str, 
                          vector_data: np.ndarray, 
                          file_id: str,
                          segment_id: Optional[str] = None,
                          metadata: Optional[Dict[str, Any]] = None,
                          vector_id: Optional[str] = None) -> str:
        """
        存储向量到Milvus
        
        Args:
            collection_type: 集合类型
            vector_data: 向量数据
            file_id: 文件ID
            segment_id: 片段ID（可选）
            metadata: 元数据
            vector_id: 向量ID（可选）
            
        Returns:
            向量ID
        """
        try:
            return await self.milvus_adapter.store_vector(
                collection_type=collection_type,
                vector_data=vector_data,
                file_id=file_id,
                segment_id=segment_id,
                metadata=metadata,
                vector_id=vector_id
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
            # 确保Milvus已连接
            await self.connect_milvus()
            
            return await self.milvus_adapter.batch_store_vectors(
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
            return await self.milvus_adapter.delete_vectors_by_file(
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
            return await self.milvus_adapter.get_vector_count(collection_type)
        except Exception as e:
            self.logger.error(f"获取向量数量失败: {e}")
            return 0
    
    async def milvus_health_check(self) -> Dict[str, Any]:
        """
        Milvus健康检查
        
        Returns:
            健康检查结果
        """
        try:
            return await self.milvus_adapter.health_check()
        except Exception as e:
            self.logger.error(f"Milvus健康检查失败: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }


# 创建全局向量化引擎实例
_embedding_engine: Optional[EmbeddingEngine] = None


def get_embedding_engine() -> EmbeddingEngine:
    """获取全局向量化引擎实例"""
    global _embedding_engine
    if _embedding_engine is None:
        _embedding_engine = EmbeddingEngine()
    return _embedding_engine