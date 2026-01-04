"""
向量化引擎
专注于AI模型管理和向量化处理，提供统一的向量化接口
"""
import asyncio
import logging
from typing import List, Optional
from pathlib import Path

from src.core.config_manager import ConfigManager
from src.core.infinity_manager import InfinityManager


class EmbeddingEngine:
    """向量化引擎 - 专注于AI模型管理和向量化处理"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        
        # 初始化Infinity管理器
        self.infinity_manager = InfinityManager(config_manager)
        
        # 运行状态
        self.is_running = False
        
        self.logger.info("向量化引擎初始化完成")
    
    async def start(self):
        """启动向量化引擎"""
        self.logger.info("启动向量化引擎")
        
        # 启动Infinity管理器
        await self.infinity_manager.start()
        
        self.is_running = True
        self.logger.info("向量化引擎启动完成")
    
    async def stop(self):
        """停止向量化引擎"""
        self.logger.info("停止向量化引擎")
        
        # 停止Infinity管理器
        await self.infinity_manager.stop()
        
        self.is_running = False
        self.logger.info("向量化引擎已停止")
    
    async def embed_image_from_path(self, file_path: str) -> List[float]:
        """从文件路径进行图像向量化"""
        self.logger.debug(f"图像向量化: {file_path}")
        
        # 读取图像文件
        with open(file_path, 'rb') as f:
            image_data = f.read()
        
        # 使用CLIP模型进行向量化
        return await self.infinity_manager.embed_image(image_data)
    
    async def embed_video_frame_from_path(self, file_path: str) -> List[float]:
        """从文件路径进行视频帧向量化"""
        self.logger.debug(f"视频帧向量化: {file_path}")
        
        # 读取视频文件并提取帧
        with open(file_path, 'rb') as f:
            video_data = f.read()
        
        # 使用CLIP模型进行向量化
        return await self.infinity_manager.embed_video_frame(video_data)
    
    async def embed_audio_from_path(self, file_path: str) -> List[float]:
        """从文件路径进行音频向量化"""
        self.logger.debug(f"音频向量化: {file_path}")
        
        # 读取音频文件
        with open(file_path, 'rb') as f:
            audio_data = f.read()
        
        # 使用CLAP或Whisper模型进行向量化，根据音频内容类型
        file_ext = Path(file_path).suffix.lower()
        if file_ext in ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.opus']:
            # 对于音乐类音频使用CLAP
            return await self.infinity_manager.embed_audio_music(audio_data)
        else:
            # 对于语音类音频使用Whisper
            return await self.infinity_manager.embed_audio_speech(audio_data)
    
    async def embed_text_for_visual(self, text: str) -> List[float]:
        """文本向量化（用于视觉检索）"""
        self.logger.debug(f"文本向量化（视觉）: {text[:50]}...")
        
        # 使用CLIP模型进行文本向量化
        return await self.infinity_manager.embed_text_clip(text)
    
    async def embed_text_for_music(self, text: str) -> List[float]:
        """文本向量化（用于音乐检索）"""
        self.logger.debug(f"文本向量化（音乐）: {text[:50]}...")
        
        # 使用CLAP模型进行文本向量化
        return await self.infinity_manager.embed_text_clap(text)
    
    async def transcribe_audio_from_path(self, file_path: str) -> str:
        """从文件路径进行语音转录"""
        self.logger.debug(f"语音转录: {file_path}")
        
        # 读取音频文件
        with open(file_path, 'rb') as f:
            audio_data = f.read()
        
        # 使用Whisper模型进行转录
        return await self.infinity_manager.transcribe_audio(audio_data)
    
    async def transcribe_and_embed_from_path(self, file_path: str) -> List[float]:
        """从文件路径进行转录并向量化"""
        self.logger.debug(f"语音转录并向量化: {file_path}")
        
        # 转录音频
        transcription = await self.transcribe_audio_from_path(file_path)
        
        # 使用CLIP模型对转录文本进行向量化
        return await self.embed_text_for_visual(transcription)
    
    async def embed_face_from_path(self, file_path: str) -> List[float]:
        """从文件路径进行人脸向量化"""
        self.logger.debug(f"人脸向量化: {file_path}")
        
        # 读取图像文件
        with open(file_path, 'rb') as f:
            image_data = f.read()
        
        # 使用FaceNet模型进行人脸向量化
        return await self.infinity_manager.embed_face(image_data)
    
    async def embed_batch(self, items: List[dict]) -> List[List[float]]:
        """批量向量化"""
        self.logger.debug(f"批量向量化: {len(items)} 项")
        
        results = []
        for item in items:
            item_type = item.get('type')
            item_data = item.get('data')
            
            if item_type == 'image_path':
                result = await self.embed_image_from_path(item_data)
            elif item_type == 'audio_path':
                result = await self.embed_audio_from_path(item_data)
            elif item_type == 'text':
                result = await self.embed_text_for_visual(item_data)
            elif item_type == 'video_path':
                result = await self.embed_video_frame_from_path(item_data)
            else:
                self.logger.warning(f"未知的批量向量化类型: {item_type}")
                result = [0.0] * 512  # 返回零向量作为默认值
            
            results.append(result)
        
        return results