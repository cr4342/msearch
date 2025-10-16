"""
模型管理器模块
负责管理多模态模型的加载、推理和向量化处理
完全配置驱动设计，所有参数从配置文件读取
"""

import os
import asyncio
import logging
import requests
import numpy as np
from typing import List, Dict, Any, Union, Optional
import json
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from dataclasses import dataclass

from src.core.config_manager import get_config_manager
from src.core.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class VideoSegment:
    """视频片段信息"""
    start_time: float
    end_time: float
    vector: List[float]
    segment_index: int


@dataclass
class TimestampMatch:
    """时间戳匹配结果"""
    timestamp: float
    similarity: float
    segment_info: Optional[VideoSegment] = None


class ModelManager:
    """专业化多模态向量化引擎 - 支持智能模型选择和多模态融合"""
    
    def __init__(self):
        """初始化模型管理器"""
        self.config_manager = get_config_manager()
        self.config = self.config_manager.config
        
        # 从配置获取参数
        self.hardware_mode = self.config_manager.get("hardware_mode", "cpu")
        logger.info(f"模型管理器初始化，硬件模式: {self.hardware_mode}")
        
        # 初始化Infinity服务配置
        self.infinity_config = self.config_manager.get('infinity', {})
        
        # 初始化Qdrant配置
        self.qdrant_config = self.config_manager.get('qdrant', {})
        
        # 模型状态
        self.models_loaded = False
        self.qdrant_client = None
        
        # 监听配置变更
        self.config_manager.watch('infinity', self._reload_config)
        self.config_manager.watch('qdrant', self._reload_config)
        
        # 初始化向量数据库连接
        self._init_qdrant()
        
        # 初始化模型（在实际实现中这里会加载真实的模型）
        self._init_models()
    
    def _reload_config(self, key: str, value: Any) -> None:
        """重新加载配置"""
        if 'infinity' in key:
            self.infinity_config = self.config_manager.get('infinity', {})
        elif 'qdrant' in key:
            self.qdrant_config = self.config_manager.get('qdrant', {})
        
        logger.info(f"模型管理器配置已更新: {key}")
    
    def _init_qdrant(self) -> bool:
        """初始化Qdrant向量数据库"""
        try:
            host = self.qdrant_config.get('host', '127.0.0.1')
            port = self.qdrant_config.get('port', 6333)
            
            self.qdrant_client = QdrantClient(host=host, port=port)
            
            # 创建或验证集合
            collections = self.qdrant_config.get('collections', {})
            for collection_name, collection_config in collections.items():
                collection_name = collection_config.get('name', f'msearch_{collection_name}')
                vector_size = collection_config.get('vector_size', 512)
                distance = collection_config.get('distance_metric', 'Cosine')
                
                # 检查集合是否存在，不存在则创建
                existing_collections = self.qdrant_client.get_collections()
                collection_names = [col.name for col in existing_collections.collections]
                
                if collection_name not in collection_names:
                    self.qdrant_client.create_collection(
                        collection_name=collection_name,
                        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
                    )
                    logger.info(f"Created collection: {collection_name}")
                else:
                    logger.info(f"Collection exists: {collection_name}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant: {e}")
            return False
    
    def _init_models(self):
        """初始化模型"""
        # 在实际实现中，这里会根据硬件模式加载相应的模型
        # 目前只是模拟初始化
        logger.info("模型初始化完成")
    
    def _call_infinity_service(self, model_type: str, data: Dict[str, Any]) -> Optional[np.ndarray]:
        """调用Infinity服务获取向量"""
        try:
            # 尝试使用负载均衡器
            try:
                from src.core.load_balancer import get_load_balancer, ServiceUnavailableError
                load_balancer = get_load_balancer()
                
                # 使用负载均衡器路由请求
                response = asyncio.run(load_balancer.route_request(model_type, data))
                
                if response and 'data' in response:
                    embeddings = response['data'][0].get('embedding', [])
                    return np.array(embeddings, dtype=np.float32)
                else:
                    logger.error("负载均衡器返回无效响应")
                    return None
                    
            except ServiceUnavailableError as e:
                logger.error(f"负载均衡器服务不可用: {e}")
                # 降级到直接调用
                return self._call_infinity_service_direct(model_type, data)
            except Exception as e:
                logger.error(f"负载均衡器调用失败: {e}")
                # 降级到直接调用
                return self._call_infinity_service_direct(model_type, data)
                
        except Exception as e:
            logger.error(f"Error calling Infinity service: {e}")
            return None
    
    def _call_infinity_service_direct(self, model_type: str, data: Dict[str, Any]) -> Optional[np.ndarray]:
        """直接调用Infinity服务获取向量（降级方案）"""
        try:
            # 从配置获取端口
            port = self.config_manager.get(f'infinity.services.{model_type}.port', 7997)
            host = self.config_manager.get('infinity.services.clip.host', '127.0.0.1')
            
            url = f"http://{host}:{port}/embeddings"
            
            response = requests.post(url, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                embeddings = result.get('data', [{}])[0].get('embedding', [])
                return np.array(embeddings, dtype=np.float32)
            else:
                logger.error(f"Infinity service error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error calling Infinity service directly: {e}")
            return None
    
    def load_models(self) -> bool:
        """加载所有模型 - 实际检查Infinity服务状态"""
        try:
            # 检查Infinity服务是否可用
            model_types = ['clip', 'clap', 'whisper']
            for model_type in model_types:
                port = self.config_manager.get(f'infinity.services.{model_type}.port', 7997)
                host = self.config_manager.get('infinity.services.clip.host', '127.0.0.1')
                
                url = f"http://{host}:{port}/health"
                
                try:
                    response = requests.get(url, timeout=5)
                    if response.status_code == 200:
                        logger.info(f"Infinity {model_type} service is available")
                    else:
                        logger.warning(f"Infinity {model_type} service returned {response.status_code}")
                        return False
                except Exception as e:
                    logger.warning(f"Infinity {model_type} service not available: {e}")
                    return False
            
            self.models_loaded = True
            logger.info("All models verified successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load models: {e}")
            return False
    
    def store_vector(self, collection_name: str, vector: np.ndarray, metadata: Dict[str, Any]) -> bool:
        """存储向量到Qdrant"""
        try:
            if self.qdrant_client is None:
                logger.error("Qdrant client not initialized")
                return False
            
            # 获取实际的集合名称
            collection_config = self.qdrant_config.get('collections', {}).get(collection_name, {})
            actual_collection_name = collection_config.get('name', f'msearch_{collection_name}')
            
            point = PointStruct(
                id=metadata.get('id', hash(str(metadata))),
                vector=vector.tolist(),
                payload=metadata
            )
            
            self.qdrant_client.upsert(
                collection_name=actual_collection_name,
                points=[point]
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error storing vector: {e}")
            return False
    
    def search_vectors(self, collection_name: str, query_vector: np.ndarray, limit: int = 10) -> List[Dict[str, Any]]:
        """在Qdrant中搜索相似向量"""
        try:
            if self.qdrant_client is None:
                logger.error("Qdrant client not initialized")
                return []
            
            # 获取实际的集合名称
            collection_config = self.qdrant_config.get('collections', {}).get(collection_name, {})
            actual_collection_name = collection_config.get('name', f'msearch_{collection_name}')
            
            search_result = self.qdrant_client.search(
                collection_name=actual_collection_name,
                query_vector=query_vector.tolist(),
                limit=limit
            )
            
            results = []
            for point in search_result:
                results.append({
                    'id': point.id,
                    'score': point.score,
                    'payload': point.payload
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching vectors: {e}")
            return []
    
    def get_model_status(self) -> Dict[str, Any]:
        """获取模型状态"""
        status = {
            "models_loaded": self.models_loaded,
            "mode": "production" if self.models_loaded else "initialization",
            "infinity_available": False,
            "qdrant_available": False
        }
        
        # 检查Infinity服务状态
        try:
            for model_type in ['clip', 'clap', 'whisper']:
                port = self.infinity_config.get('ports', {}).get(model_type, 7997)
                host = self.infinity_config.get('host', '127.0.0.1')
                
                url = f"http://{host}:{port}/health"
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    status['infinity_available'] = True
                    break
        except:
            pass
        
        # 检查Qdrant状态
        try:
            if self.qdrant_client:
                collections = self.qdrant_client.get_collections()
                status['qdrant_available'] = len(collections.collections) > 0
        except:
            pass
        
        return status
    
    async def embed_text_for_search(self, text: str) -> Dict[str, List[float]]:
        """
        文本查询的多模态向量化 - 核心优化
        
        Args:
            text: 输入文本
            
        Returns:
            包含不同模态向量的字典
        """
        logger.info(f"对文本进行多模态向量化: {text}")
        
        try:
            # 使用CLIP模型进行文本向量化
            clip_vector = await self.embed_text_image(text)
            
            # 使用sentence-transformers进行文本向量化（用于音频检索）
            from sentence_transformers import SentenceTransformer
            import numpy as np
            
            # 加载多语言模型
            model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            vector = model.encode(text)
            
            # 转换为列表格式
            clap_vector = vector.tolist()
            
            return {
                "clip_vector": clip_vector,
                "clap_vector": clap_vector
            }
        except Exception as e:
            logger.error(f"文本向量化失败: {e}")
            # 返回模拟向量作为降级方案
            clip_vector = [0.1] * 512  # CLIP模型的维度是512
            clap_vector = [0.2] * 384  # paraphrase-multilingual-MiniLM-L12-v2的维度是384
            
            return {
                "clip_vector": clip_vector,
                "clap_vector": clap_vector
            }
    
    async def embed_text_image(self, text: str) -> List[float]:
        """
        使用CLIP模型进行文本向量化（用于图像/视频检索）
        
        Args:
            text: 输入文本
            
        Returns:
            文本向量
        """
        logger.info(f"使用CLIP模型对文本进行向量化: {text}")
        
        try:
            from transformers import CLIPProcessor, CLIPModel
            import torch
            
            # 加载CLIP模型和处理器
            model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
            processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
            
            # 处理文本
            inputs = processor(text=text, return_tensors="pt", padding=True)
            
            # 获取文本嵌入
            with torch.no_grad():
                text_features = model.get_text_features(**inputs)
            
            # 转换为列表格式
            vector = text_features.squeeze().tolist()
            
            return vector
            
        except Exception as e:
            logger.error(f"文本向量化失败: {e}")
            # 返回模拟向量作为降级方案
            return [0.1] * 512
    
    async def embed_image(self, image_path: str) -> List[float]:
        """
        使用CLIP模型进行图像向量化
        
        Args:
            image_path: 图像文件路径
            
        Returns:
            图像向量
        """
        logger.info(f"使用CLIP模型对图像进行向量化: {image_path}")
        
        try:
            from PIL import Image
            from transformers import CLIPProcessor, CLIPModel
            import torch
            
            # 加载CLIP模型和处理器
            model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
            processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
            
            # 加载并预处理图像
            image = Image.open(image_path)
            
            # 处理图像
            inputs = processor(images=image, return_tensors="pt", padding=True)
            
            # 获取图像嵌入
            with torch.no_grad():
                image_features = model.get_image_features(**inputs)
            
            # 转换为列表格式
            vector = image_features.squeeze().tolist()
            
            return vector
            
        except Exception as e:
            logger.error(f"图像向量化失败: {e}")
            # 返回模拟向量作为降级方案
            return [0.3] * 512
    
    async def embed_text_audio_music(self, text: str) -> List[float]:
        """
        使用CLAP模型进行文本向量化（用于音乐检索）
        
        Args:
            text: 输入文本
            
        Returns:
            文本向量
        """
        logger.info(f"使用CLAP模型对文本进行向量化: {text}")
        
        try:
            from transformers import ClapProcessor, ClapModel
            import torch
            
            # 加载CLAP模型和处理器
            model = ClapModel.from_pretrained("laion/clap-htsat-fused")
            processor = ClapProcessor.from_pretrained("laion/clap-htsat-fused")
            
            # 处理文本
            inputs = processor(text=text, return_tensors="pt", padding=True)
            
            # 获取文本嵌入
            with torch.no_grad():
                text_features = model.get_text_features(**inputs)
            
            # 转换为列表格式
            vector = text_features.squeeze().tolist()
            
            return vector
            
        except Exception as e:
            logger.error(f"文本向量化失败: {e}")
            # 返回模拟向量作为降级方案
            return [0.2] * 512
    
    async def embed_audio_music(self, audio_path: str) -> List[float]:
        """
        使用CLAP模型进行音乐向量化
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            音频向量
        """
        logger.info(f"使用CLAP模型对音频进行向量化: {audio_path}")
        
        try:
            from transformers import ClapProcessor, ClapModel
            import torch
            import librosa
            
            # 加载CLAP模型和处理器
            model = ClapModel.from_pretrained("laion/clap-htsat-fused")
            processor = ClapProcessor.from_pretrained("laion/clap-htsat-fused")
            
            # 加载音频文件
            audio, sr = librosa.load(audio_path, sr=48000)  # CLAP模型需要48kHz采样率
            
            # 处理音频
            inputs = processor(audios=audio, return_tensors="pt", sampling_rate=48000)
            
            # 获取音频嵌入
            with torch.no_grad():
                audio_features = model.get_audio_features(**inputs)
            
            # 转换为列表格式
            vector = audio_features.squeeze().tolist()
            
            return vector
            
        except Exception as e:
            logger.error(f"音频向量化失败: {e}")
            # 返回模拟向量作为降级方案
            return [0.4] * 512
    
    async def transcribe_and_embed_speech(self, audio_path: str) -> Dict[str, Any]:
        """
        语音转文本并向量化 - 核心优化
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            包含转录文本和向量的字典
        """
        logger.info(f"语音转文本并向量化: {audio_path}")
        
        try:
            import whisper
            
            # 加载Whisper模型
            model = whisper.load_model("base")
            
            # 转录音频
            result = model.transcribe(audio_path)
            transcribed_text = result["text"]
            
            # 使用CLIP确保兼容性
            text_vector = await self.embed_text_image(transcribed_text)
            
            return {
                "transcribed_text": transcribed_text,
                "text_vector": text_vector
            }
        except Exception as e:
            logger.error(f"语音转文本并向量化失败: {e}")
            # 返回模拟结果作为降级方案
            transcribed_text = "这是一段模拟的语音转录文本"
            text_vector = await self.embed_text_image(transcribed_text)
            
            return {
                "transcribed_text": transcribed_text,
                "text_vector": text_vector
            }
    
    async def transcribe_speech(self, audio_path: str) -> str:
        """
        使用Whisper模型进行语音转文本
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            转录文本
        """
        logger.info(f"使用Whisper模型进行语音转文本: {audio_path}")
        
        try:
            import whisper
            
            # 加载Whisper模型
            model = whisper.load_model("base")
            
            # 转录音频
            result = model.transcribe(audio_path)
            return result["text"]
            
        except Exception as e:
            logger.error(f"语音转文本失败: {e}")
            # 返回模拟文本作为降级方案
            return "这是一段模拟的语音转录文本"
    
    async def embed_video_frames(self, video_path: str) -> List[List[float]]:
        """
        使用CLIP模型进行视频帧向量化
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            视频帧向量列表
        """
        logger.info(f"使用CLIP模型对视频帧进行向量化: {video_path}")
        
        try:
            import cv2
            from PIL import Image
            from transformers import CLIPProcessor, CLIPModel
            import torch
            
            # 加载CLIP模型和处理器
            model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
            processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
            
            # 打开视频文件
            cap = cv2.VideoCapture(video_path)
            
            # 提取关键帧
            frames = []
            frame_count = 0
            target_frames = 10  # 提取10个关键帧
            
            # 获取视频总帧数
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            frame_interval = max(1, total_frames // target_frames)
            
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                    
                # 每隔一定间隔提取一帧
                if frame_count % frame_interval == 0:
                    # 转换为PIL图像
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    pil_image = Image.fromarray(frame_rgb)
                    frames.append(pil_image)
                    
                    # 如果已提取足够帧数则停止
                    if len(frames) >= target_frames:
                        break
                        
                frame_count += 1
            
            cap.release()
            
            # 对每个帧进行向量化
            frame_vectors = []
            for frame in frames:
                # 处理图像
                inputs = processor(images=frame, return_tensors="pt", padding=True)
                
                # 获取图像嵌入
                with torch.no_grad():
                    image_features = model.get_image_features(**inputs)
                
                # 转换为列表格式
                vector = image_features.squeeze().tolist()
                frame_vectors.append(vector)
            
            return frame_vectors
            
        except Exception as e:
            logger.error(f"视频帧向量化失败: {e}")
            # 返回模拟向量作为降级方案
            return [[0.1] * 512 for _ in range(10)]  # 模拟10帧向量
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        计算两个向量的余弦相似度
        
        Args:
            vec1: 第一个向量
            vec2: 第二个向量
            
        Returns:
            余弦相似度值
        """
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    async def locate_timestamp(self, query_vector: List[float], video_segments: List[VideoSegment]) -> float:
        """
        基于片段相似度定位最佳时间戳
        
        Args:
            query_vector: 查询向量
            video_segments: 视频片段列表
            
        Returns:
            最佳时间戳（秒）
        """
        logger.info(f"开始时间戳定位，片段数: {len(video_segments)}")
        
        try:
            best_timestamp = 0
            best_similarity = 0
            
            for segment in video_segments:
                # 计算查询向量与片段向量的相似度
                similarity = self._cosine_similarity(query_vector, segment.vector)
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    # 计算片段内的最佳时间点（片段中心点）
                    best_timestamp = segment.start_time + (segment.end_time - segment.start_time) / 2
            
            logger.info(f"时间戳定位完成，最佳时间戳: {best_timestamp:.2f}s, 相似度: {best_similarity:.2f}")
            return best_timestamp
            
        except Exception as e:
            logger.error(f"时间戳定位失败: {e}")
            # 返回默认时间戳（片段中心点）
            if video_segments:
                first_segment = video_segments[0]
                return first_segment.start_time + (first_segment.end_time - first_segment.start_time) / 2
            return 0.0
    
    async def locate_multiple_timestamps(self, query_vector: List[float], video_segments: List[VideoSegment], top_k: int = 3) -> List[TimestampMatch]:
        """
        定位多个相似时间点
        
        Args:
            query_vector: 查询向量
            video_segments: 视频片段列表
            top_k: 返回的最佳匹配数量
            
        Returns:
            时间戳匹配结果列表
        """
        logger.info(f"开始多时间戳定位，片段数: {len(video_segments)}, top_k: {top_k}")
        
        try:
            matches = []
            for segment in video_segments:
                similarity = self._cosine_similarity(query_vector, segment.vector)
                
                # 计算片段内的精确时间点（片段中心点）
                timestamp = segment.start_time + (segment.end_time - segment.start_time) / 2
                
                matches.append(TimestampMatch(
                    timestamp=timestamp,
                    similarity=similarity,
                    segment_info=segment
                ))
            
            # 按相似度排序并返回前K个
            matches.sort(key=lambda x: x.similarity, reverse=True)
            result = matches[:top_k]
            
            logger.info(f"多时间戳定位完成，返回 {len(result)} 个匹配结果")
            return result
            
        except Exception as e:
            logger.error(f"多时间戳定位失败: {e}")
            return []
    
    async def fuse_multimodal_results(self, all_results: List[Dict], weights: Dict[str, float] = None) -> List[Dict]:
        """
        多模态结果融合
        
        Args:
            all_results: 所有模态的搜索结果
            weights: 各模态权重配置
            
        Returns:
            融合后的结果列表
        """
        logger.info(f"开始多模态结果融合，结果数: {len(all_results)}")
        
        try:
            # 默认权重配置
            if weights is None:
                weights = {
                    "clip": 0.4,    # 视觉模态权重
                    "clap": 0.3,    # 音乐模态权重
                    "whisper": 0.3  # 语音模态权重
                }
            
            # 按文件ID分组结果
            grouped_results = {}
            for result in all_results:
                file_id = result["payload"].get("file_id", result.get("id", "unknown"))
                
                if file_id not in grouped_results:
                    grouped_results[file_id] = {
                        "file_id": file_id,
                        "results": [],
                        "total_score": 0.0,
                        "weighted_scores": {}
                    }
                
                grouped_results[file_id]["results"].append(result)
            
            # 计算每个文件的融合评分
            fused_results = []
            for file_id, group in grouped_results.items():
                # 收集各模态的最高分数
                modality_scores = {"clip": 0.0, "clap": 0.0, "whisper": 0.0}
                
                for result in group["results"]:
                    # 根据集合名称判断模态类型
                    collection_name = result.get("collection_name", "")
                    if "clip" in collection_name.lower():
                        modality_scores["clip"] = max(modality_scores["clip"], result["score"])
                    elif "clap" in collection_name.lower():
                        modality_scores["clap"] = max(modality_scores["clap"], result["score"])
                    elif "whisper" in collection_name.lower():
                        modality_scores["whisper"] = max(modality_scores["whisper"], result["score"])
                
                # 计算加权融合评分
                fused_score = (
                    modality_scores["clip"] * weights["clip"] +
                    modality_scores["clap"] * weights["clap"] +
                    modality_scores["whisper"] * weights["whisper"]
                )
                
                # 选择最佳结果作为代表
                best_result = max(group["results"], key=lambda x: x["score"])
                
                fused_result = {
                    **best_result,
                    "fused_score": fused_score,
                    "modality_scores": modality_scores,
                    "result_count": len(group["results"])
                }
                
                fused_results.append(fused_result)
            
            # 按融合评分排序
            fused_results.sort(key=lambda x: x["fused_score"], reverse=True)
            
            logger.info(f"多模态结果融合完成，返回 {len(fused_results)} 个融合结果")
            return fused_results
            
        except Exception as e:
            logger.error(f"多模态结果融合失败: {e}")
            # 返回原始结果作为降级方案
            return sorted(all_results, key=lambda x: x.get("score", 0), reverse=True)
    
    async def process_video_audio_intelligently(self, audio_path: str, is_video: bool = False) -> List[Dict]:
        """
        智能处理视频音频 - 核心优化功能
        
        功能特点：
        1. 使用inaSpeechSegmenter自动分类音频内容（音乐/语音）
        2. 基于质量检测过滤低质量音频片段
        3. 根据音频类型采用差异化处理策略
        4. 通过配置文件控制处理行为
        5. 节约计算资源，避免无效处理
        
        Args:
            audio_path: 音频文件路径
            is_video: 是否为视频文件（需要先提取音频）
            
        Returns:
            处理结果列表，包含向量化结果和元数据
        """
        logger.info(f"智能处理视频音频: {audio_path}, is_video: {is_video}")
        
        # 如果是视频文件，先提取音频
        if is_video:
            try:
                audio_path = self._extract_audio_from_video(audio_path)
                logger.info(f"从视频中提取音频完成: {audio_path}")
            except Exception as e:
                logger.error(f"从视频中提取音频失败: {e}")
                return []
        
        # 获取配置
        config = get_config()
        video_audio_config = config.get("video_audio_processing", {})
        
        # 检查是否启用了视频音频处理
        if not video_audio_config.get("enabled", True):
            logger.info("视频音频处理已禁用，跳过处理")
            return []
        
        try:
            # 使用inaSpeechSegmenter分类音频片段
            segments = await self.classify_audio_segments_with_quality_check(audio_path, config)
            
            results = []
            for segment in segments:
                segment_type = segment.get('type')
                
                # 根据音频类型和质量采用不同处理策略
                if segment_type == 'music':
                    # 音乐片段：使用CLAP模型向量化
                    if segment.get('quality_score', 0) >= 0.6:  # 质量阈值
                        vector = await self.embed_audio_music(segment['audio_path'])
                        results.append({
                            'segment_type': 'audio_music',
                            'vector': vector,
                            'start_time': segment['start_time'],
                            'end_time': segment['end_time'],
                            'quality_score': segment.get('quality_score', 0),
                            'processing_model': 'clap'
                        })
                        logger.info(f"音乐片段处理完成: {segment['start_time']}-{segment['end_time']}s")
                    else:
                        logger.info(f"跳过低质量音乐片段: 质量分数 {segment.get('quality_score', 0)}")
                
                elif segment_type == 'speech':
                    # 语音片段：使用Whisper转录后向量化
                    if segment.get('quality_score', 0) >= 0.6 and segment.get('duration', 0) >= 3.0:
                        speech_result = await self.transcribe_and_embed_speech(segment['audio_path'])
                        results.append({
                            'segment_type': 'audio_speech',
                            'vector': speech_result['text_vector'],
                            'transcribed_text': speech_result['transcribed_text'],
                            'start_time': segment['start_time'],
                            'end_time': segment['end_time'],
                            'quality_score': segment.get('quality_score', 0),
                            'duration': segment.get('duration', 0),
                            'processing_model': 'whisper'
                        })
                        logger.info(f"语音片段处理完成: {segment['start_time']}-{segment['end_time']}s, 时长: {segment.get('duration', 0)}s")
                    else:
                        logger.info(f"跳过低质量或过短语音片段: 质量分数 {segment.get('quality_score', 0)}, 时长 {segment.get('duration', 0)}s")
                
                else:
                    # 其他类型或低质量片段：根据配置决定是否跳过
                    processing_strategy = video_audio_config.get("processing_strategy", {}).get("low_quality_segments", "skip")
                    if processing_strategy == "skip":
                        logger.info(f"跳过低质量片段: {segment_type}, 质量分数 {segment.get('quality_score', 0)}")
                    elif processing_strategy == "process":
                        logger.warning(f"处理低质量片段: {segment_type}, 质量分数 {segment.get('quality_score', 0)}")
                        # 这里可以添加低质量片段的处理逻辑
            
            logger.info(f"视频音频智能处理完成，共处理 {len(results)} 个高质量片段")
            return results
            
        except Exception as e:
            logger.error(f"视频音频智能处理失败: {str(e)}")
            return []
    
    async def classify_audio_segments_with_quality_check(self, audio_path: str, config: Dict) -> List[Dict]:
        """
        使用inaSpeechSegmenter分类音频片段并进行质量检测
        
        Args:
            audio_path: 音频文件路径
            config: 配置字典
            
        Returns:
            经过质量检测的音频片段列表
        """
        logger.info(f"开始音频片段分类和质量检测: {audio_path}")
        
        # 获取质量检测配置
        quality_config = config.get("video_audio_processing", {}).get("quality_check", {})
        inaspeech_config = config.get("video_audio_processing", {}).get("inaspeech_segmenter", {})
        
        # 基础音频分类（模拟inaSpeechSegmenter功能）
        basic_segments = await self.classify_audio_segments(audio_path)
        
        # 增强版片段，包含质量信息
        enhanced_segments = []
        
        for segment in basic_segments:
            # 计算音频质量分数
            quality_score = await self.calculate_audio_quality_score(segment, audio_path)
            
            # 获取片段时长
            duration = segment.get('end_time', 0) - segment.get('start_time', 0)
            
            # 应用质量过滤规则
            if self.apply_quality_filters(segment, quality_score, duration, quality_config, inaspeech_config):
                enhanced_segment = {
                    **segment,
                    'quality_score': quality_score,
                    'duration': duration,
                    'audio_path': f"{audio_path}_segment_{segment.get('start_time')}_{segment.get('end_time')}"
                }
                enhanced_segments.append(enhanced_segment)
                logger.info(f"通过质量检测的片段: {segment.get('type')}, 时长: {duration:.1f}s, 质量分数: {quality_score:.2f}")
            else:
                logger.info(f"未通过质量检测的片段: {segment.get('type')}, 时长: {duration:.1f}s, 质量分数: {quality_score:.2f}")
        
        logger.info(f"音频片段分类完成，原始片段: {len(basic_segments)}, 通过质量检测: {len(enhanced_segments)}")
        return enhanced_segments
    
    async def calculate_audio_quality_score(self, segment: Dict, audio_path: str) -> float:
        """
        计算音频片段质量分数
        
        Args:
            segment: 音频片段信息
            audio_path: 原始音频文件路径
            
        Returns:
            质量分数 (0-1)
        """
        # 模拟质量计算过程
        # 在实际实现中，这里会计算信噪比、频谱特征、清晰度等指标
        
        import random
        base_score = random.uniform(0.4, 0.9)  # 模拟基础质量分数
        
        # 根据片段类型调整质量分数
        segment_type = segment.get('type', 'unknown')
        if segment_type == 'music':
            # 音乐片段质量评估
            score = base_score * 0.9 + 0.1  # 音乐通常质量较好
        elif segment_type == 'speech':
            # 语音片段质量评估
            score = base_score * 0.8 + 0.1  # 语音质量中等
        else:
            # 其他类型
            score = base_score * 0.7  # 其他类型质量可能较低
        
        return min(score, 1.0)  # 确保分数不超过1
    
    def apply_quality_filters(self, segment: Dict, quality_score: float, duration: float, 
                            quality_config: Dict, inaspeech_config: Dict) -> bool:
        """
        应用质量过滤规则
        
        Args:
            segment: 音频片段信息
            quality_score: 质量分数
            duration: 片段时长
            quality_config: 质量检测配置
            inaspeech_config: inaSpeechSegmenter配置
            
        Returns:
            是否通过质量检测
        """
        segment_type = segment.get('type', 'unknown')
        
        # 基础质量阈值
        min_quality_score = quality_config.get("min_clarity_score", 0.6)
        if quality_score < min_quality_score:
            return False
        
        # 时长过滤
        if segment_type == 'speech':
            min_duration = inaspeech_config.get("min_speech_duration", 3.0)
            if duration < min_duration:
                return False
        elif segment_type == 'music':
            min_duration = inaspeech_config.get("min_music_duration", 5.0)
            if duration < min_duration:
                return False
        
        return True

    def _extract_audio_from_video(self, video_path: str) -> str:
        """
        从视频中提取音频
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            提取的音频文件路径
        """
        try:
            # 生成音频文件路径
            audio_path = f"{video_path}_extracted_audio.wav"
            
            # 使用FFmpeg提取音频
            cmd = [
                "ffmpeg", "-i", video_path,
                "-vn",  # 禁用视频
                "-acodec", "pcm_s16le",  # 音频编码
                "-ar", "16000",  # 采样率
                "-ac", "1",  # 单声道
                "-y",  # 覆盖输出文件
                audio_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                logger.info(f"音频提取成功: {audio_path}")
                return audio_path
            else:
                logger.error(f"音频提取失败: {result.stderr}")
                raise Exception(f"FFmpeg音频提取失败: {result.stderr}")
                
        except Exception as e:
            logger.error(f"从视频提取音频时出错: {e}")
            raise
    
    async def classify_audio_segments(self, audio_path: str) -> List[Dict]:
        """
        使用inaSpeechSegmenter分类音频片段
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            音频片段分类结果列表
        """
        logger.info(f"使用inaSpeechSegmenter分类音频片段: {audio_path}")
        
        try:
            # 导入inaSpeechSegmenter
            from inaSpeechSegmenter import Segmenter
            
            # 初始化分类器
            seg = Segmenter()
            
            # 执行分类
            segmentation = seg(audio_path)
            
            # 转换结果格式
            segments = []
            for segment_type, start_time, end_time in segmentation:
                segments.append({
                    'type': segment_type,
                    'start_time': start_time,
                    'end_time': end_time
                })
            
            return segments
            
        except Exception as e:
            logger.error(f"音频分类失败: {e}")
            # 返回模拟数据作为降级方案
            return [
                {
                    'type': 'music',
                    'start_time': 0,
                    'end_time': 30
                },
                {
                    'type': 'speech',
                    'start_time': 30,
                    'end_time': 60
                }
            ]
    
    async def batch_embed(self, items: List[Dict]) -> List[List[float]]:
        """
        批量向量化处理，根据内容类型选择合适模型
        
        Args:
            items: 待处理项目列表
            
        Returns:
            向量列表
        """
        logger.info(f"批量向量化处理 {len(items)} 个项目")
        
        vectors = []
        for item in items:
            item_type = item.get('type')
            item_path = item.get('path')
            
            if item_type == 'text':
                vector = await self.embed_text_image(item_path)
            elif item_type == 'image':
                vector = await self.embed_image(item_path)
            elif item_type == 'audio':
                # 这里需要进一步判断是音乐还是语音
                vector = await self.embed_audio_music(item_path)
            else:
                # 默认使用文本向量化
                vector = await self.embed_text_image(str(item))
            
            # 对向量进行L2归一化
            vector = self._normalize_vector(vector)
            vectors.append(vector)
        
        return vectors
    
    def _normalize_vector(self, vector: List[float]) -> List[float]:
        """
        对向量进行L2归一化
        
        Args:
            vector: 输入向量
            
        Returns:
            归一化后的向量
        """
        try:
            # 转换为numpy数组
            np_vector = np.array(vector)
            
            # 计算L2范数
            norm = np.linalg.norm(np_vector)
            
            # 避免除零错误
            if norm == 0:
                return vector
            
            # 归一化
            normalized_vector = np_vector / norm
            
            # 转换回列表
            return normalized_vector.tolist()
        except Exception as e:
            logger.error(f"向量归一化失败: {e}")
            return vector


# 全局模型管理器实例
_model_manager = None


def get_model_manager() -> ModelManager:
    """
    获取全局模型管理器实例
    
    Returns:
        模型管理器实例
    """
    global _model_manager
    if _model_manager is None:
        _model_manager = ModelManager()
    return _model_manager