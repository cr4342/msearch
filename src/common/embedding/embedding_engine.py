"""
向量化引擎
使用Infinity封装各AI模型，提供向量化方法
"""

import asyncio
import logging
from typing import List, Union, Optional, Dict, Any
import numpy as np
from infinity_emb import AsyncEngineArray, EngineArgs

from src.core.config_manager import get_config_manager


class EmbeddingEngine:
    """向量化引擎"""
    
    def __init__(self, config_manager=None):
        self.config_manager = config_manager or get_config_manager()
        self.logger = logging.getLogger(__name__)
        
        # 模型配置
        self.models_config = self.config_manager.get("infinity.services", {})
        
        # 引擎实例
        self.engines: Dict[str, Any] = {}
        
        # 初始化模型
        self._initialize_models()
        
        self.logger.info("向量化引擎初始化完成")
    
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
            
            # 在异步上下文中调用同步方法
            loop = asyncio.get_event_loop()
            vector = await loop.run_in_executor(
                None, 
                lambda: engine.encode(image_data, "image")
            )
            
            return vector
            
        except Exception as e:
            self.logger.error(f"图像向量化失败: {e}")
            raise
    
    async def embed_image_async(self, image_data: bytes) -> np.ndarray:
        """
        异步图像向量化
        
        Args:
            image_data: 图像字节数据
            
        Returns:
            图像向量
        """
        return await self.embed_image(image_data)
    
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
            
            # 在异步上下文中调用同步方法
            loop = asyncio.get_event_loop()
            vector = await loop.run_in_executor(
                None, 
                lambda: engine.encode(text, "text")
            )
            
            return vector
            
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
            
            # 在异步上下文中调用同步方法
            loop = asyncio.get_event_loop()
            vector = await loop.run_in_executor(
                None, 
                lambda: engine.encode(text, "text")
            )
            
            return vector
            
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
            
            # 在异步上下文中调用同步方法
            loop = asyncio.get_event_loop()
            vector = await loop.run_in_executor(
                None, 
                lambda: engine.encode(audio_data, "audio")
            )
            
            return vector
            
        except Exception as e:
            self.logger.error(f"音频向量化失败: {e}")
            raise
    
    async def embed_audio_music_async(self, audio_data: bytes) -> np.ndarray:
        """
        异步音频向量化（音乐）
        
        Args:
            audio_data: 音频字节数据
            
        Returns:
            音频向量
        """
        return await self.embed_audio_music(audio_data)
    
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
    
    async def transcribe_and_embed_async(self, audio_data: bytes) -> np.ndarray:
        """
        异步转录并向量化语音
        
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