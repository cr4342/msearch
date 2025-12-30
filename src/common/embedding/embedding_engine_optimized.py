"""
优化的向量化引擎
集成缓存、批处理、性能监控等功能的高性能向量化引擎
"""

import asyncio
import logging
import hashlib
from typing import List, Union, Optional, Dict, Any
import numpy as np
from infinity_emb import AsyncEngineArray, EngineArgs

from src.core.config_manager import get_config_manager
from src.core.cache_manager import CacheManager
from src.core.performance_monitor import PerformanceMonitor, PerformanceMonitorDecorator
from src.core.batch_processor import EmbeddingBatchProcessor


class OptimizedEmbeddingEngine:
    """优化的向量化引擎"""
    
    def __init__(self, config_manager=None):
        self.config_manager = config_manager or get_config_manager()
        self.logger = logging.getLogger(__name__)
        
        # 初始化性能监控器
        self.performance_monitor = PerformanceMonitor(self.config_manager)
        self.performance_decorator = PerformanceMonitorDecorator(self.performance_monitor)
        
        # 初始化缓存管理器
        self.cache_manager = CacheManager(self.config_manager)
        
        # 初始化批处理器
        batch_config = self.config_manager.get("performance.batch_processing", {})
        self.batch_processor = EmbeddingBatchProcessor(
            embedding_engine=None,  # 将在初始化模型后设置
            monitor=self.performance_monitor,
            max_batch_size=batch_config.get("max_batch_size", 32),
            batch_timeout=batch_config.get("batch_timeout", 1.0),
            max_workers=batch_config.get("max_workers", 4),
            use_multiprocessing=batch_config.get("use_multiprocessing", False)
        )
        
        # 模型配置
        self.models_config = self.config_manager.get("infinity.services", {})
        
        # 引擎实例
        self.engines: Dict[str, Any] = {}
        
        # 初始化模型和批处理器
        self._initialize_models()
        
        # 设置批处理器的embedding引擎
        self.batch_processor.embedding_engine = self
        
        # 启动性能监控
        asyncio.create_task(self.performance_monitor.start())
        
        self.logger.info("优化的向量化引擎初始化完成")
    
    def _initialize_models(self):
        """初始化AI模型"""
        try:
            # 初始化CLIP模型
            if 'clip' in self.models_config:
                clip_config = self.models_config['clip']
                self.engines['clip'] = AsyncEngineArray.from_args([
                    EngineArgs(
                        model_name_or_path=clip_config['model_id'],
                        engine="torch",
                        device=clip_config.get('device', 'cuda:0'),
                        model_warmup=True,
                        dtype=clip_config.get('dtype', 'float16')
                    )
                ])
                self.logger.info(f"CLIP模型初始化成功: {clip_config['model_id']}")
            
            # 初始化CLAP模型
            if 'clap' in self.models_config:
                clap_config = self.models_config['clap']
                self.engines['clap'] = AsyncEngineArray.from_args([
                    EngineArgs(
                        model_name_or_path=clap_config['model_id'],
                        engine="torch",
                        device=clap_config.get('device', 'cuda:0'),
                        model_warmup=True,
                        dtype=clap_config.get('dtype', 'float16')
                    )
                ])
                self.logger.info(f"CLAP模型初始化成功: {clap_config['model_id']}")
            
            # 初始化Whisper模型
            if 'whisper' in self.models_config:
                whisper_config = self.models_config['whisper']
                self.engines['whisper'] = AsyncEngineArray.from_args([
                    EngineArgs(
                        model_name_or_path=whisper_config['model_id'],
                        engine="torch",
                        device=whisper_config.get('device', 'cuda:1'),
                        model_warmup=True,
                        dtype=whisper_config.get('dtype', 'float16')
                    )
                ])
                self.logger.info(f"Whisper模型初始化成功: {whisper_config['model_id']}")
        
        except Exception as e:
            self.logger.error(f"模型初始化失败: {e}")
            raise
    
    def _get_file_hash(self, data: bytes) -> str:
        """获取数据哈希值用于缓存"""
        return hashlib.md5(data).hexdigest()
    
    @PerformanceMonitorDecorator("embedding_engine")
    async def embed_image(self, image_data: bytes, use_cache: bool = True) -> np.ndarray:
        """
        优化的图像向量化
        
        Args:
            image_data: 图像字节数据
            use_cache: 是否使用缓存
            
        Returns:
            图像向量
        """
        try:
            # 检查缓存
            if use_cache:
                file_hash = self._get_file_hash(image_data)
                cached_vector = self.cache_manager.get_cached_vector(file_hash, 'clip')
                if cached_vector is not None:
                    self.logger.debug("图像向量缓存命中")
                    return cached_vector
            
            if 'clip' not in self.engines:
                raise RuntimeError("CLIP模型未初始化")
            
            # 使用CLIP模型进行图像向量化
            engine = self.engines['clip']
            
            # 在异步上下文中调用同步方法
            loop = asyncio.get_event_loop()
            vector = await loop.run_in_executor(
                None, 
                lambda: engine.encode(image_data, "image")
            )
            
            # 缓存结果
            if use_cache:
                file_hash = self._get_file_hash(image_data)
                self.cache_manager.set_cached_vector(file_hash, 'clip', vector)
            
            return vector
            
        except Exception as e:
            self.logger.error(f"图像向量化失败: {e}")
            raise
    
    async def embed_image_optimized(self, image_data: bytes, use_cache: bool = True) -> np.ndarray:
        """
        优化的图像向量化（别名）
        """
        return await self.embed_image(image_data, use_cache)
    
    @PerformanceMonitorDecorator("embedding_engine")
    async def embed_text_for_visual(self, text: str, use_cache: bool = True) -> np.ndarray:
        """
        优化的文本向量化（用于图像/视频检索）
        
        Args:
            text: 文本字符串
            use_cache: 是否使用缓存
            
        Returns:
            文本向量
        """
        try:
            # 检查缓存
            if use_cache:
                text_hash = hashlib.md5(text.encode()).hexdigest()
                cached_vector = self.cache_manager.get_cached_vector(text_hash, 'clip_text')
                if cached_vector is not None:
                    self.logger.debug("文本向量缓存命中")
                    return cached_vector
            
            if 'clip' not in self.engines:
                raise RuntimeError("CLIP模型未初始化")
            
            # 使用CLIP模型进行文本向量化
            engine = self.engines['clip']
            
            # 在异步上下文中调用同步方法
            loop = asyncio.get_event_loop()
            vector = await loop.run_in_executor(
                None, 
                lambda: engine.encode(text, "text")
            )
            
            # 缓存结果
            if use_cache:
                text_hash = hashlib.md5(text.encode()).hexdigest()
                self.cache_manager.set_cached_vector(text_hash, 'clip_text', vector)
            
            return vector
            
        except Exception as e:
            self.logger.error(f"文本向量化失败: {e}")
            raise
    
    @PerformanceMonitorDecorator("embedding_engine")
    async def embed_text_for_music(self, text: str, use_cache: bool = True) -> np.ndarray:
        """
        优化的文本向量化（用于音乐检索）
        
        Args:
            text: 文本字符串
            use_cache: 是否使用缓存
            
        Returns:
            文本向量
        """
        try:
            # 检查缓存
            if use_cache:
                text_hash = hashlib.md5(text.encode()).hexdigest()
                cached_vector = self.cache_manager.get_cached_vector(text_hash, 'clap_text')
                if cached_vector is not None:
                    self.logger.debug("音乐文本向量缓存命中")
                    return cached_vector
            
            if 'clap' not in self.engines:
                raise RuntimeError("CLAP模型未初始化")
            
            # 使用CLAP模型进行文本向量化
            engine = self.engines['clap']
            
            # 在异步上下文中调用同步方法
            loop = asyncio.get_event_loop()
            vector = await loop.run_in_executor(
                None, 
                lambda: engine.encode(text, "text")
            )
            
            # 缓存结果
            if use_cache:
                text_hash = hashlib.md5(text.encode()).hexdigest()
                self.cache_manager.set_cached_vector(text_hash, 'clap_text', vector)
            
            return vector
            
        except Exception as e:
            self.logger.error(f"音乐文本向量化失败: {e}")
            raise
    
    @PerformanceMonitorDecorator("embedding_engine")
    async def embed_audio_music(self, audio_data: bytes, use_cache: bool = True) -> np.ndarray:
        """
        优化的音频向量化（音乐）
        
        Args:
            audio_data: 音频字节数据
            use_cache: 是否使用缓存
            
        Returns:
            音频向量
        """
        try:
            # 检查缓存
            if use_cache:
                file_hash = self._get_file_hash(audio_data)
                cached_vector = self.cache_manager.get_cached_vector(file_hash, 'clap')
                if cached_vector is not None:
                    self.logger.debug("音频向量缓存命中")
                    return cached_vector
            
            if 'clap' not in self.engines:
                raise RuntimeError("CLAP模型未初始化")
            
            # 使用CLAP模型进行音频向量化
            engine = self.engines['clap']
            
            # 处理音频采样率，确保为48000Hz，且转换为单声道
            import io
            import librosa
            import soundfile as sf
            
            # 加载音频数据
            audio, sr = sf.read(io.BytesIO(audio_data))
            
            # 将多声道转换为单声道（取平均值）
            if len(audio.shape) > 1:
                audio = audio.mean(axis=1)
            
            # 重采样到48000Hz
            if sr != 48000:
                audio = librosa.resample(audio, orig_sr=sr, target_sr=48000)
                # 将重采样后的音频转换回字节格式
                buffer = io.BytesIO()
                sf.write(buffer, audio, 48000, format='wav')
                audio_data = buffer.getvalue()
            
            # 在异步上下文中调用同步方法
            loop = asyncio.get_event_loop()
            vector = await loop.run_in_executor(
                None, 
                lambda: engine.encode(audio_data, "audio")
            )
            
            # 缓存结果
            if use_cache:
                file_hash = self._get_file_hash(audio_data)
                self.cache_manager.set_cached_vector(file_hash, 'clap', vector)
            
            return vector
            
        except Exception as e:
            self.logger.error(f"音频向量化失败: {e}")
            raise
    
    @PerformanceMonitorDecorator("embedding_engine")
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
            
            # 在异步上下文中调用同步方法
            loop = asyncio.get_event_loop()
            text = await loop.run_in_executor(
                None, 
                lambda: engine.encode(audio_data, "audio")
            )
            
            # Whisper返回的是转录文本
            return text
            
        except Exception as e:
            self.logger.error(f"语音转录失败: {e}")
            raise
    
    @PerformanceMonitorDecorator("embedding_engine")
    async def transcribe_and_embed(self, audio_data: bytes, use_cache: bool = True) -> np.ndarray:
        """
        转录并向量化语音（使用Whisper + CLIP模型）
        
        Args:
            audio_data: 音频字节数据
            use_cache: 是否使用缓存
            
        Returns:
            语音向量
        """
        try:
            # 检查缓存
            if use_cache:
                file_hash = self._get_file_hash(audio_data)
                cached_vector = self.cache_manager.get_cached_vector(file_hash, 'whisper_clip')
                if cached_vector is not None:
                    self.logger.debug("转录并向量化结果缓存命中")
                    # 使用性能监控记录缓存命中
                    self.performance_monitor.record_event("cache_hit", "transcribe_and_embed")
                    return cached_vector
            
            # 先转录为文本
            text = await self.transcribe_audio(audio_data)
            
            # 再对文本进行向量化（使用CLIP）
            vector = await self.embed_text_for_visual(text, use_cache)
            
            # 缓存结果
            if use_cache:
                file_hash = self._get_file_hash(audio_data)
                self.cache_manager.set_cached_vector(file_hash, 'whisper_clip', vector)
            
            return vector
            
        except Exception as e:
            self.logger.error(f"转录并向量化失败: {e}")
            raise
    
    async def batch_embed_images_optimized(self, images_data: List[bytes], use_cache: bool = True) -> List[np.ndarray]:
        """
        优化的批量图像向量化
        
        Args:
            images_data: 图像字节数据列表
            use_cache: 是否使用缓存
            
        Returns:
            图像向量列表
        """
        try:
            if not self.batch_processor.is_running:
                await self.batch_processor.start()
            
            # 检查缓存
            if use_cache:
                cached_vectors = []
                uncached_data = []
                uncached_indices = []
                
                for i, image_data in enumerate(images_data):
                    file_hash = self._get_file_hash(image_data)
                    cached_vector = self.cache_manager.get_cached_vector(file_hash, 'clip')
                    if cached_vector is not None:
                        cached_vectors.append(cached_vector)
                    else:
                        uncached_data.append(image_data)
                        uncached_indices.append(i)
                
                if uncached_data:
                    # 处理未缓存的数据
                    vectors = await self.batch_processor.batch_embed_images(uncached_data)
                    
                    # 存储到缓存并合并结果
                    for i, (idx, vector) in enumerate(zip(uncached_indices, vectors)):
                        if vector is not None:
                            file_hash = self._get_file_hash(uncached_data[i])
                            self.cache_manager.set_cached_vector(file_hash, 'clip', vector)
                            cached_vectors.insert(idx, vector)
                        else:
                            cached_vectors.insert(idx, None)
                
                return cached_vectors
            else:
                # 直接批量处理
                return await self.batch_processor.batch_embed_images(images_data)
            
        except Exception as e:
            self.logger.error(f"批量图像向量化失败: {e}")
            raise
    
    async def batch_embed_texts_optimized(self, texts: List[str], modality: str = "visual", use_cache: bool = True) -> List[np.ndarray]:
        """
        优化的批量文本向量化
        
        Args:
            texts: 文本字符串列表
            modality: 模态类型 ("visual" 或 "music")
            use_cache: 是否使用缓存
            
        Returns:
            文本向量列表
        """
        try:
            if not self.batch_processor.is_running:
                await self.batch_processor.start()
            
            # 检查缓存
            if use_cache:
                cached_vectors = []
                uncached_texts = []
                uncached_indices = []
                
                for i, text in enumerate(texts):
                    text_hash = hashlib.md5(text.encode()).hexdigest()
                    model_name = 'clip_text' if modality == 'visual' else 'clap_text'
                    cached_vector = self.cache_manager.get_cached_vector(text_hash, model_name)
                    if cached_vector is not None:
                        cached_vectors.append(cached_vector)
                    else:
                        uncached_texts.append(text)
                        uncached_indices.append(i)
                
                if uncached_texts:
                    # 处理未缓存的数据
                    vectors = await self.batch_processor.batch_embed_texts(uncached_texts, modality)
                    
                    # 存储到缓存并合并结果
                    for i, (idx, vector) in enumerate(zip(uncached_indices, vectors)):
                        if vector is not None:
                            text_hash = hashlib.md5(uncached_texts[i].encode()).hexdigest()
                            model_name = 'clip_text' if modality == 'visual' else 'clap_text'
                            self.cache_manager.set_cached_vector(text_hash, model_name, vector)
                            cached_vectors.insert(idx, vector)
                        else:
                            cached_vectors.insert(idx, None)
                
                return cached_vectors
            else:
                # 直接批量处理
                return await self.batch_processor.batch_embed_texts(texts, modality)
            
        except Exception as e:
            self.logger.error(f"批量文本向量化失败: {e}")
            raise
    
    async def batch_embed_audio_optimized(self, audio_data_list: List[bytes], use_cache: bool = True) -> List[np.ndarray]:
        """
        优化的批量音频向量化
        
        Args:
            audio_data_list: 音频字节数据列表
            use_cache: 是否使用缓存
            
        Returns:
            音频向量列表
        """
        try:
            if not self.batch_processor.is_running:
                await self.batch_processor.start()
            
            # 检查缓存
            if use_cache:
                cached_vectors = []
                uncached_data = []
                uncached_indices = []
                
                for i, audio_data in enumerate(audio_data_list):
                    file_hash = self._get_file_hash(audio_data)
                    cached_vector = self.cache_manager.get_cached_vector(file_hash, 'clap')
                    if cached_vector is not None:
                        cached_vectors.append(cached_vector)
                    else:
                        uncached_data.append(audio_data)
                        uncached_indices.append(i)
                
                if uncached_data:
                    # 处理未缓存的数据
                    vectors = await self.batch_processor.batch_embed_audio(uncached_data)
                    
                    # 存储到缓存并合并结果
                    for i, (idx, vector) in enumerate(zip(uncached_indices, vectors)):
                        if vector is not None:
                            file_hash = self._get_file_hash(uncached_data[i])
                            self.cache_manager.set_cached_vector(file_hash, 'clap', vector)
                            cached_vectors.insert(idx, vector)
                        else:
                            cached_vectors.insert(idx, None)
                
                return cached_vectors
            else:
                # 直接批量处理
                return await self.batch_processor.batch_embed_audio(audio_data_list)
            
        except Exception as e:
            self.logger.error(f"批量音频向量化失败: {e}")
            raise
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        return self.cache_manager.get_cache_stats()
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        return self.performance_monitor.get_performance_report()
    
    def get_batch_stats(self) -> Dict[str, Any]:
        """获取批处理统计信息"""
        return self.batch_processor.get_processing_stats()
    
    def clear_cache(self):
        """清空缓存"""
        self.cache_manager.clear_all_caches()
        self.logger.info("所有缓存已清空")
    
    async def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """获取模型信息"""
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
    
    async def get_available_models(self) -> List[str]:
        """获取可用模型列表"""
        return list(self.engines.keys())
    
    async def health_check(self) -> Dict[str, bool]:
        """健康检查"""
        health_status = {}
        
        for model_name in self.engines.keys():
            try:
                # 简单的向量化测试
                if model_name == 'clip':
                    await self.embed_text_for_visual("test", use_cache=False)
                elif model_name == 'clap':
                    await self.embed_text_for_music("test", use_cache=False)
                elif model_name == 'whisper':
                    # Whisper测试跳过，因为需要音频数据
                    pass
                
                health_status[model_name] = True
                
            except Exception as e:
                self.logger.error(f"模型健康检查失败: {model_name}, 错误: {e}")
                health_status[model_name] = False
        
        return health_status
    
    async def shutdown(self):
        """优雅关闭"""
        self.logger.info("开始关闭优化的向量化引擎")
        
        # 停止批处理器
        await self.batch_processor.stop()
        
        # 停止性能监控器
        await self.performance_monitor.stop()
        
        self.logger.info("优化的向量化引擎已关闭")


# 创建全局优化的向量化引擎实例
_optimized_embedding_engine: Optional[OptimizedEmbeddingEngine] = None


def get_optimized_embedding_engine() -> OptimizedEmbeddingEngine:
    """获取全局优化的向量化引擎实例"""
    global _optimized_embedding_engine
    if _optimized_embedding_engine is None:
        _optimized_embedding_engine = OptimizedEmbeddingEngine()
    return _optimized_embedding_engine