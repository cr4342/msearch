"""
嵌入引擎 - 使用Infinity Python-native模式统一管理AI模型，生成媒体内容向量
符合design.md中关于michaelfeil/infinity集成的要求
"""
import numpy as np
from typing import Dict, Any, List, Union
import logging
import os

logger = logging.getLogger(__name__)

try:
    from infinity_emb import AsyncEngineArray, EngineArgs
    INFINITY_AVAILABLE = True
except ImportError:
    INFINITY_AVAILABLE = False
    logger.warning("Infinity未安装，将使用模拟向量生成")


class EmbeddingEngine:
    """嵌入引擎 - 符合design.md中关于Python-native模式集成的要求"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化嵌入引擎
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 模型映射 - 根据内容类型选择对应的模型
        self.model_mapping = {
            'image': 'clip',
            'text': 'clip',
            'audio_music': 'clap',
            'audio_speech': 'whisper'
        }
        
        # 模型健康状态
        self.model_health = {
            'clip': False,
            'clap': False,
            'whisper': False
        }
        
        # 初始化Infinity引擎数组
        self.engine_array = None
        self._init_infinity_engine()
    
    def _init_infinity_engine(self):
        """初始化Infinity引擎 - 使用本地模型，不进行网络下载"""
        try:
            from infinity_emb import AsyncEngineArray, EngineArgs
            
            # 从配置中获取模型设置
            models_config = self.config.get('models', {})
            models_storage = self.config.get('models_storage', {})
            
            # 设置环境变量，强制使用离线模式
            os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'
            os.environ['TRANSFORMERS_OFFLINE'] = '1'  # 强制离线模式
            os.environ['HF_HUB_OFFLINE'] = '1'
            
            # 如果配置中指定了模型缓存目录，设置环境变量
            if models_storage.get('models_dir'):
                os.environ['TRANSFORMERS_CACHE'] = models_storage.get('models_dir')
                os.environ['HF_HOME'] = models_storage.get('models_dir')
            
            # 初始化成功的模型列表
            successful_models = []
            
            # CLIP模型配置 - 使用本地路径
            clip_config = models_config.get('clip', {})
            # 优先使用本地路径，如果没有则使用默认本地路径
            clip_model = clip_config.get('local_path', clip_config.get('model_name', './data/models/clip'))
            
            # 确保使用绝对路径
            if not os.path.isabs(clip_model):
                project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                # 移除开头的./或../，避免重复路径
                if clip_model.startswith('./'):
                    clip_model = clip_model[2:]
                elif clip_model.startswith('../'):
                    clip_model = clip_model[3:]
                clip_model = os.path.join(project_root, clip_model)
            
            try:
                # 检查本地模型是否存在
                if os.path.exists(clip_model):
                    clip_engine_args = EngineArgs(
                        model_name_or_path=clip_model,
                        device=clip_config.get('device', 'cpu'),
                        model_warmup=True,
                        batch_size=clip_config.get('batch_size', 16),
                        dtype='float32'
                    )
                    
                    successful_models.append(clip_engine_args)
                    self.model_health['clip'] = True
                    self.logger.info(f"本地CLIP模型 {clip_model} 初始化成功")
                else:
                    self.logger.warning(f"本地CLIP模型路径不存在: {clip_model}")
                    raise FileNotFoundError(f"CLIP模型路径不存在: {clip_model}")
                
            except Exception as e:
                self.logger.error(f"本地CLIP模型初始化失败: {e}")
                # 不尝试从网络下载，直接标记为失败
            
            # CLAP模型配置 - 使用本地路径
            clap_config = models_config.get('clap', {})
            clap_model = clap_config.get('local_path', clap_config.get('model_name', './data/models/clap'))
            
            # 确保使用绝对路径
            if not os.path.isabs(clap_model):
                project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                # 移除开头的./或../，避免重复路径
                if clap_model.startswith('./'):
                    clap_model = clap_model[2:]
                elif clap_model.startswith('../'):
                    clap_model = clap_model[3:]
                clap_model = os.path.join(project_root, clap_model)
            
            try:
                # 检查本地模型是否存在
                if os.path.exists(clap_model):
                    # 优先使用safetensors格式的模型文件
                    safetensors_path = os.path.join(clap_model, 'model.safetensors')
                    if os.path.exists(safetensors_path):
                        # 如果存在safetensors文件，使用它
                        clap_engine_args = EngineArgs(
                            model_name_or_path=clap_model,
                            device=clap_config.get('device', 'cpu'),
                            model_warmup=True,
                            batch_size=clap_config.get('batch_size', 8),
                            dtype='float32'
                        )
                        
                        successful_models.append(clap_engine_args)
                        self.model_health['clap'] = True
                        self.logger.info(f"本地CLAP模型 {clap_model} 初始化成功（使用safetensors格式）")
                    else:
                        # 如果没有safetensors文件，尝试使用pytorch格式
                        clap_engine_args = EngineArgs(
                            model_name_or_path=clap_model,
                            device=clap_config.get('device', 'cpu'),
                            model_warmup=True,
                            batch_size=clap_config.get('batch_size', 8),
                            dtype='float32'
                        )
                        
                        successful_models.append(clap_engine_args)
                        self.model_health['clap'] = True
                        self.logger.info(f"本地CLAP模型 {clap_model} 初始化成功（使用pytorch格式）")
                else:
                    self.logger.warning(f"本地CLAP模型路径不存在: {clap_model}")
                    raise FileNotFoundError(f"CLAP模型路径不存在: {clap_model}")
                
            except Exception as e:
                self.logger.error(f"本地CLAP模型初始化失败: {e}")
                # 不尝试从网络下载，直接标记为失败
            
            # Whisper模型配置 - 使用本地路径
            whisper_config = models_config.get('whisper', {})
            whisper_model = whisper_config.get('local_path', whisper_config.get('model_name', './data/models/whisper'))
            
            # 确保使用绝对路径
            if not os.path.isabs(whisper_model):
                project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                # 移除开头的./或../，避免重复路径
                if whisper_model.startswith('./'):
                    whisper_model = whisper_model[2:]
                elif whisper_model.startswith('../'):
                    whisper_model = whisper_model[3:]
                whisper_model = os.path.join(project_root, whisper_model)
            
            try:
                # 检查本地模型是否存在
                if os.path.exists(whisper_model):
                    whisper_engine_args = EngineArgs(
                        model_name_or_path=whisper_model,
                        device=whisper_config.get('device', 'cpu'),
                        model_warmup=True,
                        batch_size=whisper_config.get('batch_size', 4),
                        dtype='float32'
                    )
                    
                    successful_models.append(whisper_engine_args)
                    self.model_health['whisper'] = True
                    self.logger.info(f"本地Whisper模型 {whisper_model} 初始化成功")
                else:
                    self.logger.warning(f"本地Whisper模型路径不存在: {whisper_model}")
                    raise FileNotFoundError(f"Whisper模型路径不存在: {whisper_model}")
                
            except Exception as e:
                self.logger.error(f"本地Whisper模型初始化失败: {e}")
                # 不尝试从网络下载，直接标记为失败
            
            # 如果有成功加载的模型，创建引擎数组
            if successful_models:
                try:
                    # 使用AsyncEngineArray.from_args的正确方式
                    self.engine_array = AsyncEngineArray.from_args(successful_models)
                    self.logger.info(f"Infinity引擎初始化完成，成功加载 {len(successful_models)} 个本地模型")
                except Exception as e:
                    self.logger.error(f"创建引擎数组失败: {e}")
                    self.engine_array = None
                    raise RuntimeError(f"创建引擎数组失败: {e}")
            else:
                self.logger.error("没有成功加载任何本地模型")
                raise RuntimeError("无法加载本地模型，请检查模型文件是否存在且路径配置正确")
                
        except Exception as e:
            self.logger.error(f"初始化Infinity引擎失败: {e}")
            raise RuntimeError(f"初始化嵌入引擎失败: {e}")
    
    async def embed_content(self, content: Union[str, np.ndarray, List[np.ndarray]], 
                           content_type: str) -> np.ndarray:
        """
        统一的内容向量化接口 - 改进版本，支持批处理和更好的错误处理
        
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
                
                # 检查模型健康状态
                if not self.model_health.get(model, False):
                    raise RuntimeError(f"模型 {model} 不可用")
                
                self.logger.debug(f"使用{model.upper()}模型生成向量: 内容类型={content_type}")
                
                # 预处理内容数据
                processed_content = self._preprocess_content(content, content_type)
                
                # 调用Infinity生成向量
                # 根据技术实现文档，需要通过索引访问具体引擎实例，并使用async with上下文管理器
                engine_index = 0  # 默认使用第一个引擎（通常是CLIP）
                if model == 'clap':
                    engine_index = 1  # CLAP模型
                elif model == 'whisper':
                    engine_index = 2  # Whisper模型
                
                # 获取对应的引擎实例
                engine = self.engine_array[engine_index]
                
                # 使用async with上下文管理器调用embed方法
                async with engine:
                    if content_type == 'text':
                        # 文本嵌入
                        if isinstance(processed_content, (list, tuple)):
                            embedding_result = await engine.embed(processed_content)
                        else:
                            embedding_result = await engine.embed([processed_content])
                    elif content_type == 'image':
                        # 图像嵌入 - 使用关键字参数images
                        if isinstance(processed_content, (list, tuple)):
                            embedding_result = await engine.image_embed(images=processed_content)
                        else:
                            embedding_result = await engine.image_embed(images=[processed_content])
                    elif content_type in ['audio_music', 'audio_speech']:
                        # 音频嵌入（使用CLAP模型）
                        if isinstance(processed_content, (list, tuple)):
                            embedding_result = await engine.audio_embed(audios=processed_content)
                        else:
                            embedding_result = await engine.audio_embed(audios=[processed_content])
                    else:
                        # 默认使用文本嵌入
                        if isinstance(processed_content, (list, tuple)):
                            embedding_result = await engine.embed(processed_content)
                        else:
                            embedding_result = await engine.embed([processed_content])
                
                # 提取向量数据 - Infinity返回(embeddings, usage)元组
                if isinstance(embedding_result, tuple) and len(embedding_result) >= 1:
                    embeddings = embedding_result[0]  # 第一个元素是嵌入向量
                else:
                    embeddings = embedding_result
                
                # 确保返回的是numpy数组
                if not isinstance(embeddings, np.ndarray):
                    embeddings = np.array(embeddings)
                
                # 后处理向量
                processed_embeddings = self._postprocess_embeddings(embeddings, content_type)
                
                self.logger.debug(f"向量生成完成: 形状={processed_embeddings.shape}")
                return processed_embeddings
                
            except Exception as e:
                self.logger.error(f"使用Infinity生成向量失败: {e}")
                raise RuntimeError(f"向量生成失败: {e}")
        else:
            raise RuntimeError("嵌入引擎未正确初始化")
    
    def _preprocess_content(self, content: Union[str, np.ndarray, List[np.ndarray]], 
                             content_type: str) -> Union[str, np.ndarray, List[np.ndarray]]:
        """
        预处理内容数据
        
        Args:
            content: 原始内容
            content_type: 内容类型
            
        Returns:
            预处理后的内容
        """
        try:
            if content_type == 'text':
                # 文本预处理
                if isinstance(content, str):
                    # 清理文本，移除多余空白
                    content = content.strip()
                    if len(content) == 0:
                        content = "empty text"  # 避免空文本
                    return content
                else:
                    return str(content)
                    
            elif content_type == 'image':
                # 图片预处理
                if isinstance(content, np.ndarray):
                    # 确保图片格式正确
                    if content.dtype != np.float32:
                        content = content.astype(np.float32)
                    
                    # 归一化到0-1范围
                    if content.max() > 1.0:
                        content = content / 255.0
                    
                    # 确保是RGB格式
                    if len(content.shape) == 2:  # 灰度图
                        content = np.stack([content] * 3, axis=-1)
                    elif len(content.shape) == 3 and content.shape[2] == 4:  # RGBA
                        content = content[:, :, :3]
                    
                    return content
                else:
                    return content
                    
            elif content_type in ['audio_music', 'audio_speech']:
                # 音频预处理
                if isinstance(content, np.ndarray):
                    # 确保音频数据格式正确
                    if content.dtype != np.float32:
                        content = content.astype(np.float32)
                    
                    # 归一化音频
                    max_val = np.abs(content).max()
                    if max_val > 0:
                        content = content / max_val
                    
                    return content
                else:
                    return content
                    
            else:
                return content
                
        except Exception as e:
            self.logger.warning(f"内容预处理失败: {e}，使用原始内容")
            return content
    
    def _postprocess_embeddings(self, embeddings: np.ndarray, content_type: str) -> np.ndarray:
        """
        后处理生成的向量
        
        Args:
            embeddings: 原始向量
            content_type: 内容类型
            
        Returns:
            处理后的向量
        """
        try:
            # 确保向量是float32类型
            if embeddings.dtype != np.float32:
                embeddings = embeddings.astype(np.float32)
            
            # 确保向量被归一化（L2归一化）
            if len(embeddings.shape) == 1:
                # 单个向量
                norm = np.linalg.norm(embeddings)
                if norm > 0:
                    embeddings = embeddings / norm
            else:
                # 多个向量
                norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
                norms[norms == 0] = 1  # 避免除零
                embeddings = embeddings / norms
            
            return embeddings
            
        except Exception as e:
            self.logger.warning(f"向量后处理失败: {e}，使用原始向量")
            return embeddings
    
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
    
    async def embed_image(self, images: Union[str, List[str], np.ndarray, List[np.ndarray]]) -> np.ndarray:
        """
        图像向量化 - 支持路径和numpy数组
        
        Args:
            images: 图像路径（字符串或列表）或图像数据（numpy数组或列表）
            
        Returns:
            图像向量
        """
        if self.engine_array is not None:
            try:
                # 获取CLIP模型用于图像向量化
                clip_engine = self.engine_array[0]  # 假设第一个是CLIP模型
                
                # 检查是否是numpy数组类型（图像数据）
                if isinstance(images, np.ndarray) or (isinstance(images, list) and len(images) > 0 and isinstance(images[0], np.ndarray)):
                    # 使用embed_content方法处理numpy数组
                    return await self.embed_content(images, 'image')
                
                # 处理路径字符串
                if isinstance(images, str):
                    # 单个路径
                    processed_content = [images]
                else:
                    # 路径列表
                    processed_content = images
                
                # 使用async with上下文管理器
                async with clip_engine:
                    # 使用关键字参数images传入路径列表
                    embedding_result = await clip_engine.image_embed(images=processed_content)
                
                # 提取向量数据
                if isinstance(embedding_result, tuple) and len(embedding_result) >= 1:
                    embeddings = embedding_result[0]
                    if isinstance(embeddings, list) and len(embeddings) > 0:
                        return np.array(embeddings[0])
                
                return np.array([])
                
            except Exception as e:
                self.logger.error(f"图像向量化失败: {e}")
                return np.array([])
        else:
            self.logger.error("嵌入引擎未正确初始化")
            return np.array([])
    
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
    
    async def transcribe_speech(self, audio: np.ndarray) -> str:
        """
        使用Whisper模型将语音转换为文本
        
        Args:
            audio: 音频数据
            
        Returns:
            转录文本
        """
        if self.engine_array is not None:
            try:
                # 检查Whisper模型是否可用
                if not self.model_health.get('whisper', False):
                    raise RuntimeError("Whisper模型不可用")
                
                self.logger.debug("使用Whisper模型进行语音转文本")
                
                # 使用Whisper模型进行语音转文本
                # 注意：这里需要特殊的处理，因为Whisper返回的是文本而不是向量
                # 这里简化实现，实际应用中需要根据infinity_emb的API进行调整
                transcription_result = await self.engine_array.embed(audio, 'whisper')
                
                # 提取转录文本
                if hasattr(transcription_result, 'text'):
                    return transcription_result.text
                elif isinstance(transcription_result, dict) and 'text' in transcription_result:
                    return transcription_result['text']
                elif isinstance(transcription_result, str):
                    return transcription_result
                else:
                    # 如果返回的是向量或其他格式，尝试转换为文本
                    return str(transcription_result)
                    
            except Exception as e:
                self.logger.error(f"使用Whisper进行语音转文本失败: {e}")
                raise RuntimeError(f"语音转文本失败: {e}")
        else:
            raise RuntimeError("嵌入引擎未正确初始化")
    
    def get_model_status(self) -> Dict[str, bool]:
        """
        获取模型状态
        
        Returns:
            模型健康状态字典
        """
        return self.model_health.copy()
    
    def is_model_available(self, model_name: str) -> bool:
        """
        检查指定模型是否可用
        
        Args:
            model_name: 模型名称 ('clip', 'clap', 'whisper')
            
        Returns:
            模型是否可用
        """
        return self.model_health.get(model_name, False)
    
    async def batch_embed_text(self, texts: List[str]) -> List[np.ndarray]:
        """
        批量文本向量化
        
        Args:
            texts: 文本列表
            
        Returns:
            向量列表
        """
        if not texts:
            return []
        
        # 如果支持批处理，使用批处理
        if self.engine_array is not None and self.model_health.get('clip', False):
            try:
                # 批处理文本
                batch_result = await self.engine_array.embed(texts, 'clip')
                
                if hasattr(batch_result, 'embeddings'):
                    embeddings = batch_result.embeddings
                else:
                    embeddings = batch_result
                
                if isinstance(embeddings, np.ndarray):
                    # 确保返回的是列表
                    return [embeddings[i] for i in range(len(texts))]
                else:
                    return embeddings
                    
            except Exception as e:
                self.logger.error(f"批量文本向量化失败: {e}")
        
        # 回退到逐个处理
        return [await self.embed_text(text) for text in texts]
    
    async def batch_embed_image(self, images: List[np.ndarray]) -> List[np.ndarray]:
        """
        批量图片向量化
        
        Args:
            images: 图片列表
            
        Returns:
            向量列表
        """
        if not images:
            return []
        
        # 如果支持批处理，使用批处理
        if self.engine_array is not None and self.model_health.get('clip', False):
            try:
                # 批处理图片
                batch_result = await self.engine_array.embed(images, 'clip')
                
                if hasattr(batch_result, 'embeddings'):
                    embeddings = batch_result.embeddings
                else:
                    embeddings = batch_result
                
                if isinstance(embeddings, np.ndarray):
                    # 确保返回的是列表
                    return [embeddings[i] for i in range(len(images))]
                else:
                    return embeddings
                    
            except Exception as e:
                self.logger.error(f"批量图片向量化失败: {e}")
        
        # 回退到逐个处理
        return [await self.embed_image(image) for image in images]


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