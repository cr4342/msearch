"""
向量化引擎
负责AI模型的加载、初始化和推理
"""

import torch
from typing import Any, Dict, List, Optional
from pathlib import Path
import logging
import numpy as np
from PIL import Image
import librosa
import soundfile as sf
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)


class EmbeddingEngine:
    """向量化引擎"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化向量化引擎
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.models = {}
        self.model_cache_dir = Path(config.get('models', {}).get('cache_dir', 'data/models'))
        self.model_cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 硬件自适应模型配置
        self.image_video_models = config.get('models', {}).get('image_video_model', {})
        self.auto_select = self.image_video_models.get('auto_select', True)
        
        # 模型懒加载
        self._clip_model = None
        self._clap_model = None
        self._whisper_model = None
        
        # 设备配置
        self.device = self._get_device()
        
        logger.info(f"向量化引擎初始化完成，设备: {self.device}")
    
    def _get_device(self) -> str:
        """获取计算设备"""
        if torch.cuda.is_available():
            return "cuda"
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            return "mps"
        else:
            return "cpu"
    
    def _select_model(self) -> str:
        """
        根据硬件配置选择模型
        
        Returns:
            模型配置键
        """
        if not self.auto_select:
            # 使用配置中指定的模型
            model_name = self.config.get('models', {}).get('clip_model', 'openai/clip-vit-base-patch32')
            if 'mobileclip' in model_name.lower():
                return 'mobileclip'
            elif 'colsmol' in model_name.lower():
                return 'colsmol_500m'
            elif 'colqwen' in model_name.lower():
                return 'colqwen2_5_v0_2'
        
        # 自动选择模型
        if self.device == "cpu":
            # 低配硬件：使用MobileCLIP
            return 'mobileclip'
        elif self.device == "cuda":
            # 检查GPU内存
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)  # GB
            if gpu_memory >= 8:
                # 高配硬件：使用colqwen2.5
                return 'colqwen2_5_v0_2'
            elif gpu_memory >= 4:
                # 中配硬件：使用colSmol
                return 'colsmol_500m'
            else:
                # 低配GPU：使用MobileCLIP
                return 'mobileclip'
        else:
            # MPS或其他：使用MobileCLIP
            return 'mobileclip'
    
    def _get_clip_model_config(self) -> Dict[str, Any]:
        """获取CLIP模型配置"""
        model_key = self._select_model()
        return self.image_video_models.get(model_key, {
            'model_name': 'openai/clip-vit-base-patch32',
            'device': self.device,
            'batch_size': 16,
            'precision': 'float16'
        })
    
    def _load_clip_model(self):
        """加载CLIP模型（懒加载）"""
        if self._clip_model is None:
            try:
                from transformers import CLIPProcessor, CLIPModel
                
                config = self._get_clip_model_config()
                model_name = config['model_name']
                device = config['device']
                
                logger.info(f"加载CLIP模型: {model_name}")
                
                # 加载处理器和模型
                processor = CLIPProcessor.from_pretrained(model_name)
                model = CLIPModel.from_pretrained(model_name)
                
                # 设置精度
                if config.get('precision') == 'float16' and device != 'cpu':
                    model = model.half()
                
                model = model.to(device)
                model.eval()
                
                self._clip_model = {
                    'processor': processor,
                    'model': model,
                    'config': config
                }
                
                logger.info(f"CLIP模型加载成功")
            except Exception as e:
                logger.error(f"加载CLIP模型失败: {e}")
                raise
    
    def _load_clap_model(self):
        """加载CLAP模型（懒加载）"""
        if self._clap_model is None:
            try:
                import torch
                from transformers import ClapProcessor, ClapModel
                
                model_name = self.config.get('models', {}).get('clap_model', 'laion/clap-htsat-unfused')
                device = self.device if self.device != 'mps' else 'cpu'  # CLAP不支持MPS
                
                logger.info(f"加载CLAP模型: {model_name}")
                
                # 加载处理器和模型
                processor = ClapProcessor.from_pretrained(model_name)
                model = ClapModel.from_pretrained(model_name)
                
                # 设置精度
                if device != 'cpu':
                    model = model.half()
                
                model = model.to(device)
                model.eval()
                
                self._clap_model = {
                    'processor': processor,
                    'model': model,
                    'config': {
                        'model_name': model_name,
                        'device': device
                    }
                }
                
                logger.info(f"CLAP模型加载成功")
            except Exception as e:
                logger.error(f"加载CLAP模型失败: {e}")
                raise
    
    def _load_whisper_model(self):
        """加载Whisper模型（懒加载）"""
        if self._whisper_model is None:
            try:
                import whisper
                
                model_name = self.config.get('models', {}).get('whisper_model', 'openai/whisper-base')
                device = self.device if self.device != 'mps' else 'cpu'  # Whisper不支持MPS
                
                logger.info(f"加载Whisper模型: {model_name}")
                
                model = whisper.load_model(model_name, device=device)
                
                self._whisper_model = {
                    'model': model,
                    'config': {
                        'model_name': model_name,
                        'device': device
                    }
                }
                
                logger.info(f"Whisper模型加载成功")
            except Exception as e:
                logger.error(f"加载Whisper模型失败: {e}")
                raise
    
    def initialize(self) -> bool:
        """
        初始化向量化引擎
        
        Returns:
            是否成功
        """
        try:
            # 模型预热（可选）
            if self.config.get('models', {}).get('enable_model_warmup', False):
                logger.info("模型预热中...")
                self._load_clip_model()
                # 预热一次
                dummy_image = Image.new('RGB', (224, 224), color='white')
                self.embed_image_from_path.__wrapped__(self, dummy_image)
                logger.info("模型预热完成")
            
            return True
        except Exception as e:
            logger.error(f"向量化引擎初始化失败: {e}")
            return False
    
    def shutdown(self) -> None:
        """关闭向量化引擎"""
        # 释放模型
        if self._clip_model:
            del self._clip_model
            self._clip_model = None
        
        if self._clap_model:
            del self._clap_model
            self._clap_model = None
        
        if self._whisper_model:
            del self._whisper_model
            self._whisper_model = None
        
        # 清理GPU缓存
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        logger.info("向量化引擎已关闭")
    
    def embed_image(self, image_path: str) -> List[float]:
        """
        图像向量化
        
        Args:
            image_path: 图像文件路径
        
        Returns:
            向量嵌入
        """
        try:
            # 加载模型
            self._load_clip_model()
            
            # 加载图像
            image = Image.open(image_path).convert('RGB')
            
            # 预处理
            processor = self._clip_model['processor']
            inputs = processor(images=image, return_tensors="pt")
            
            # 推理
            model = self._clip_model['model']
            device = self._clip_model['config']['device']
            inputs = {k: v.to(device) for k, v in inputs.items()}
            
            with torch.no_grad():
                image_features = model.get_image_features(**inputs)
                # 归一化
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            
            return image_features.cpu().numpy().flatten().tolist()
        except Exception as e:
            logger.error(f"图像向量化失败: {e}")
            raise
    
    def embed_video_segment(self, video_path: str, start_time: float = 0.0, end_time: Optional[float] = None) -> List[float]:
        """
        视频片段向量化
        
        Args:
            video_path: 视频文件路径
            start_time: 开始时间（秒）
            end_time: 结束时间（秒）
        
        Returns:
            向量嵌入
        """
        try:
            # 加载模型
            self._load_clip_model()
            
            # 使用OpenCV提取帧
            import cv2
            
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            if end_time is None:
                end_time = start_time + 5.0  # 默认5秒片段
            
            # 计算帧数
            start_frame = int(start_time * fps)
            end_frame = int(end_time * fps)
            total_frames = end_frame - start_frame
            
            # 提取中间帧
            middle_frame = start_frame + total_frames // 2
            cap.set(cv2.CAP_PROP_POS_FRAMES, middle_frame)
            
            ret, frame = cap.read()
            if not ret:
                cap.release()
                raise ValueError("无法读取视频帧")
            
            # 转换为RGB
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = Image.fromarray(frame)
            
            cap.release()
            
            # 向量化
            processor = self._clip_model['processor']
            inputs = processor(images=image, return_tensors="pt")
            
            model = self._clip_model['model']
            device = self._clip_model['config']['device']
            inputs = {k: v.to(device) for k, v in inputs.items()}
            
            with torch.no_grad():
                image_features = model.get_image_features(**inputs)
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            
            return image_features.cpu().numpy().flatten().tolist()
        except Exception as e:
            logger.error(f"视频片段向量化失败: {e}")
            raise
    
    def embed_text(self, text: str, target_modality: str = 'image') -> List[float]:
        """
        文本向量化
        
        Args:
            text: 文本内容
            target_modality: 目标模态（image/video/audio）
        
        Returns:
            向量嵌入
        """
        try:
            # 如果目标模态是audio，使用CLAP模型
            if target_modality == 'audio':
                return self.embed_text_for_audio(text)
            
            # 加载CLIP模型
            self._load_clip_model()
            
            # 预处理
            processor = self._clip_model['processor']
            inputs = processor(text=[text], return_tensors="pt", padding=True, truncation=True)
            
            # 推理
            model = self._clip_model['model']
            device = self._clip_model['config']['device']
            inputs = {k: v.to(device) for k, v in inputs.items()}
            
            with torch.no_grad():
                text_features = model.get_text_features(**inputs)
                text_features = text_features / text_features.norm(dim=-1, keepdim=True)
            
            return text_features.cpu().numpy().flatten().tolist()
        except Exception as e:
            logger.error(f"文本向量化失败: {e}")
            raise
    
    def embed_text_for_audio(self, text: str) -> List[float]:
        """
        文本向量化（用于音频检索，使用CLAP模型）
        
        Args:
            text: 文本内容
        
        Returns:
            向量嵌入
        """
        try:
            # 加载CLAP模型
            self._load_clap_model()
            
            # 预处理
            processor = self._clap_model['processor']
            inputs = processor(text=text, return_tensors="pt", padding=True, truncation=True)
            
            # 推理
            model = self._clap_model['model']
            device = self._clap_model['config']['device']
            inputs = {k: v.to(device) for k, v in inputs.items()}
            
            with torch.no_grad():
                text_features = model.get_text_features(**inputs)
                text_features = text_features / text_features.norm(dim=-1, keepdim=True)
            
            return text_features.cpu().numpy().flatten().tolist()
        except Exception as e:
            logger.error(f"文本向量化失败: {e}")
            raise
    
    def transcribe_audio(self, audio_path: str) -> str:
        """
        音频转录（Whisper）
        
        Args:
            audio_path: 音频文件路径
        
        Returns:
            转录文本
        """
        try:
            # 加载模型
            self._load_whisper_model()
            
            model = self._whisper_model['model']
            
            # 转录
            result = model.transcribe(audio_path)
            
            return result['text']
        except Exception as e:
            logger.error(f"音频转录失败: {e}")
            raise
    
    def embed_audio_from_path(self, audio_path: str) -> List[float]:
        """
        音频向量化（CLAP）
        
        Args:
            audio_path: 音频文件路径
        
        Returns:
            向量嵌入
        """
        try:
            # 加载CLAP模型
            self._load_clap_model()
            
            # 加载音频
            audio_data, sr = librosa.load(audio_path, sr=48000)  # CLAP使用48kHz
            audio_data = audio_data[:480000]  # 限制为10秒
            
            # 预处理
            processor = self._clap_model['processor']
            inputs = processor(audios=audio_data, sampling_rate=sr, return_tensors="pt")
            
            # 推理
            model = self._clap_model['model']
            device = self._clap_model['config']['device']
            inputs = {k: v.to(device) for k, v in inputs.items()}
            
            with torch.no_grad():
                audio_features = model.get_audio_features(**inputs)
                audio_features = audio_features / audio_features.norm(dim=-1, keepdim=True)
            
            return audio_features.cpu().numpy().flatten().tolist()
        except Exception as e:
            logger.error(f"音频向量化失败: {e}")
            raise
    
    def embed_video_segments_batch(self, video_paths: List[str]) -> List[List[float]]:
        """
        批量视频片段向量化
        
        Args:
            video_paths: 视频文件路径列表
        
        Returns:
            向量嵌入列表
        """
        vectors = []
        for video_path in video_paths:
            try:
                vector = self.embed_video_segment(video_path)
                vectors.append(vector)
            except Exception as e:
                logger.error(f"批量向量化失败: {video_path}, {e}")
                vectors.append([])  # 空向量表示失败
        return vectors
    
    def get_current_model_info(self) -> Dict[str, Any]:
        """
        获取当前模型信息
        
        Returns:
            模型信息字典
        """
        model_key = self._select_model()
        model_config = self._get_clip_model_config()
        
        return {
            'model_key': model_key,
            'model_name': model_config.get('model_name'),
            'device': model_config.get('device'),
            'batch_size': model_config.get('batch_size'),
            'precision': model_config.get('precision'),
            'auto_select': self.auto_select
        }
    
    def switch_model(self, model_type: str, model_config: Dict[str, Any]) -> bool:
        """
        切换模型
        
        Args:
            model_type: 模型类型
            model_config: 模型配置
        
        Returns:
            是否成功
        """
        try:
            # 清理当前模型
            if self._clip_model:
                del self._clip_model
                self._clip_model = None
            
            # 更新配置
            if model_type == 'image_video':
                self.image_video_models = model_config
                self.auto_select = False
            
            # 重新加载模型
            self._load_clip_model()
            
            logger.info(f"模型切换成功: {model_type}")
            return True
        except Exception as e:
            logger.error(f"模型切换失败: {e}")
            return False
    
    def warmup_models(self) -> None:
        """模型预热"""
        try:
            logger.info("开始模型预热...")
            self._load_clip_model()
            
            # 预热CLIP模型
            dummy_text = "test"
            dummy_image = Image.new('RGB', (224, 224), color='white')
            
            self.embed_text(dummy_text)
            self.embed_image_from_path.__wrapped__(self, dummy_image)
            
            logger.info("模型预热完成")
        except Exception as e:
            logger.error(f"模型预热失败: {e}")
    
    def calculate_file_hash(self, file_path: str) -> str:
        """
        计算文件哈希（SHA256）
        
        Args:
            file_path: 文件路径
        
        Returns:
            文件哈希
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    # 包装方法以支持直接传递PIL Image对象
    @staticmethod
    def __wrapped__(self, image: Image.Image) -> List[float]:
        """内部方法：直接处理PIL Image对象"""
        try:
            self._load_clip_model()
            
            processor = self._clip_model['processor']
            inputs = processor(images=image, return_tensors="pt")
            
            model = self._clip_model['model']
            device = self._clip_model['config']['device']
            inputs = {k: v.to(device) for k, v in inputs.items()}
            
            with torch.no_grad():
                image_features = model.get_image_features(**inputs)
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            
            return image_features.cpu().numpy().flatten().tolist()
        except Exception as e:
            logger.error(f"图像向量化失败: {e}")
            raise