"""
嵌入引擎 - 使用Infinity Python-native模式统一管理AI模型，生成媒体内容向量
"""
import numpy as np
from typing import Dict, Any, List, Union
import logging

logger = logging.getLogger(__name__)

try:
    from infinity_emb import AsyncEngineArray, EngineArgs
    INFINITY_AVAILABLE = True
except ImportError:
    INFINITY_AVAILABLE = False
    logger.warning("Infinity未安装，将使用模拟向量生成")


class EmbeddingEngine:
    """嵌入引擎"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化嵌入引擎
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.model_mapping = {
            'image': 'clip',
            'text': 'clip',
            'audio_music': 'clap',
            'audio_speech': 'whisper'
        }
        
        if INFINITY_AVAILABLE:
            self._init_models()
        else:
            logger.warning("Infinity不可用，将使用模拟模式")
            self.engine_array = None
    
    def _init_models(self):
        """初始化所有AI模型"""
        try:
            engine_args = []
            
            # 从配置中获取模型设置
            infinity_config = self.config.get('infinity', {})
            services_config = infinity_config.get('services', {})
            
            # CLIP模型配置
            clip_config = services_config.get('clip', {})
            engine_args.append(EngineArgs(
                model_name_or_path=clip_config.get('model_id', 'openai/clip-vit-base-patch32'),
                device=clip_config.get('device', 'cpu'),
                model_warmup=True,
                batch_size=clip_config.get('max_batch_size', 32),
                dtype=clip_config.get('dtype', 'float16')
            ))
            
            # CLAP模型配置
            clap_config = services_config.get('clap', {})
            engine_args.append(EngineArgs(
                model_name_or_path=clap_config.get('model_id', 'laion/clap-htsat-fused'),
                device=clap_config.get('device', 'cpu'),
                model_warmup=True,
                batch_size=clap_config.get('max_batch_size', 16),
                dtype=clap_config.get('dtype', 'float16')
            ))
            
            # Whisper模型配置
            whisper_config = services_config.get('whisper', {})
            engine_args.append(EngineArgs(
                model_name_or_path=whisper_config.get('model_id', 'openai/whisper-base'),
                device=whisper_config.get('device', 'cpu'),
                model_warmup=True,
                batch_size=whisper_config.get('max_batch_size', 8),
                dtype=whisper_config.get('dtype', 'float16')
            ))
            
            self.engine_array = AsyncEngineArray.from_args(engine_args)
            logger.info("Infinity模型初始化完成")
        except Exception as e:
            logger.error(f"初始化Infinity模型失败: {e}")
            self.engine_array = None
    
    async def embed_content(self, content: Union[str, np.ndarray, List[np.ndarray]], 
                           content_type: str) -> np.ndarray:
        """
        统一的内容向量化接口
        
        Args:
            content: 内容数据（文本字符串、图片数据或音频数据）
            content_type: 内容类型 ('image', 'text', 'audio_music', 'audio_speech')
            
        Returns:
            向量表示 (512维)
        """
        if self.engine_array is not None:
            try:
                model = self.model_mapping.get(content_type)
                if not model:
                    raise ValueError(f"不支持的内容类型: {content_type}")
                
                logger.debug(f"使用{model.upper()}模型生成向量: 内容类型={content_type}")
                
                # 调用Infinity生成向量
                # Infinity的embed方法返回的是EmbeddingReturnType对象
                embedding_result = await self.engine_array.embed(content, model)
                
                # 提取向量数据
                if hasattr(embedding_result, 'embeddings'):
                    embeddings = embedding_result.embeddings
                else:
                    embeddings = embedding_result
                
                # 确保返回的是numpy数组
                if not isinstance(embeddings, np.ndarray):
                    embeddings = np.array(embeddings)
                
                logger.debug(f"向量生成完成: 形状={embeddings.shape}")
                return embeddings
            except Exception as e:
                logger.error(f"使用Infinity生成向量失败: {e}")
                return self._mock_embed_content(content, content_type)
        else:
            # 如果Infinity不可用，使用模拟方法
            return self._mock_embed_content(content, content_type)
    
    def _mock_embed_content(self, content: Union[str, np.ndarray, List[np.ndarray]], 
                           content_type: str) -> np.ndarray:
        """
        模拟向量生成（用于测试或Infinity不可用时）
        
        Args:
            content: 内容数据
            content_type: 内容类型
            
        Returns:
            模拟向量 (512维)
        """
        logger.warning(f"使用模拟向量生成: 内容类型={content_type}")
        
        # 生成512维的随机向量（模拟）
        mock_vector = np.random.rand(512).astype(np.float32)
        
        # 标准化向量（L2归一化）
        mock_vector = mock_vector / np.linalg.norm(mock_vector)
        
        return mock_vector
    
    async def embed_image(self, images: Union[np.ndarray, List[np.ndarray]]) -> np.ndarray:
        """
        图片向量化
        
        Args:
            images: 图片数据 (单张图片或图片列表)
            
        Returns:
            图片向量
        """
        return await self.embed_content(images, 'image')
    
    async def embed_text(self, text: str) -> np.ndarray:
        """
        文本向量化
        
        Args:
            text: 文本字符串
            
        Returns:
            文本向量
        """
        return await self.embed_content(text, 'text')
    
    async def embed_audio_music(self, audio: np.ndarray) -> np.ndarray:
        """
        音乐音频向量化
        
        Args:
            audio: 音频数据
            
        Returns:
            音频向量
        """
        return await self.embed_content(audio, 'audio_music')
    
    async def embed_audio_speech(self, audio: np.ndarray) -> np.ndarray:
        """
        语音音频向量化
        
        Args:
            audio: 音频数据
            
        Returns:
            音频向量
        """
        return await self.embed_content(audio, 'audio_speech')


# 全局嵌入引擎实例
_embedding_engine = None


def get_embedding_engine(config: Dict[str, Any] = None) -> EmbeddingEngine:
    """
    获取全局嵌入引擎实例
    
    Args:
        config: 配置字典，首次调用时需要提供
        
    Returns:
        嵌入引擎实例
    """
    global _embedding_engine
    if _embedding_engine is None:
        if config is None:
            raise ValueError("首次调用get_embedding_engine时必须提供config参数")
        _embedding_engine = EmbeddingEngine(config)
    return _embedding_engine


# 示例使用
if __name__ == "__main__":
    import asyncio
    
    # 配置示例
    config = {
        'features': {
            'enable_clip': True,
            'enable_clap': True,
            'enable_whisper': True
        },
        'models': {
            'clip_model': 'openai/clip-vit-base-patch32',
            'clap_model': 'laion/clap-htsat-fused',
            'whisper_model': 'openai/whisper-base'
        },
        'device': 'cpu'
    }
    
    # 创建引擎实例
    async def main():
        engine = get_embedding_engine(config)
        
        # 模拟图片向量化
        # image_data = np.random.rand(224, 224, 3).astype(np.float32)
        # image_vector = await engine.embed_image(image_data)
        # print(f"图片向量形状: {image_vector.shape}")
        
        # 模拟文本向量化
        # text_vector = await engine.embed_text("这是一段测试文本")
        # print(f"文本向量形状: {text_vector.shape}")
        
        # 模拟音频向量化
        # audio_data = np.random.rand(16000).astype(np.float32)  # 1秒音频数据
        # music_vector = await engine.embed_audio_music(audio_data)
        # speech_vector = await engine.embed_audio_speech(audio_data)
        # print(f"音乐向量形状: {music_vector.shape}")
        # print(f"语音向量形状: {speech_vector.shape}")
    
    # 运行异步主函数
    # asyncio.run(main())