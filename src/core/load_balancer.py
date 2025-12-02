负载均衡器
用于管理多个模型服务的负载均衡
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
import random
from collections import defaultdict


class ModelService:
    """模型服务实例"""
    
    def __init__(self, name: str, service_config: Dict[str, Any]):
        self.name = name
        self.port = service_config.get("port", 7997)
        self.model_id = service_config.get("model_id", "")
        self.device = service_config.get("device", "cpu")
        self.max_batch_size = service_config.get("max_batch_size", 32)
        self.current_load = 0
        self.status = "running"


class LoadBalancer:
    """负载均衡器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.services: Dict[str, List[ModelService]] = defaultdict(list)
        self.service_weights = {}
        
        self.logger.info("负载均衡器初始化完成")
    
    def add_service(self, service_type: str, service: ModelService):
        """添加服务"""
        self.services[service_type].append(service)
        self.logger.info(f"添加服务: {service_type} -> {service.name}:{service.port}")
    
    def set_service_weights(self, service_type: str, weights: Dict[str, float]):
        """设置服务权重"""
        self.service_weights[service_type] = weights
        self.logger.info(f"设置服务权重: {service_type} = {weights}")
    
    def get_best_service(self, service_type: str) -> Optional[ModelService]:
        """获取最优服务"""
        if service_type not in self.services:
            return None
        
        available_services = [s for s in self.services[service_type] if s.status == "running"]
        
        if not available_services:
            return None
        
        # 选择负载最轻的服务
        available_services.sort(key=lambda s: s.current_load)
        return available_services[0]
    
    async def route_request(self, service_type: str, request_data: Any) -> Optional[ModelService]:
        """路由请求"""
        service = self.get_best_service(service_type)
        
        if service:
            service.current_load += 1
            self.logger.debug(f"路由请求到 {service.name}:{service.port}")
        
        return service
    
    def release_service(self, service_type: str, service: ModelService):
        """释放服务"""
        if service.current_load > 0:
            service.current_load -= 1
        self.logger.debug(f"释放服务 {service.name}:{service.port}")
    
    def get_service_stats(self, service_type: str) -> Dict[str, Any]:
        """获取服务统计"""
        services = self.services.get(service_type, [])
        
        return {
            "total_services": len(services),
            "running_services": len([s for s in services if s.status == "running"]),
            "total_load": sum(s.current_load for s in services),
            "average_load": sum(s.current_load for s in services) / len(services) if services else 0
        }


# 全局负载均衡器实例
_load_balancer = None


def get_load_balancer(services_dict: Dict[str, Any] = None) -> LoadBalancer:
    """获取全局负载均衡器实例"""
    global _load_balancer
    
    if _load_balancer is None:
        _load_balancer = LoadBalancer()
    
    # 如果提供了服务字典，则注册服务
    if services_dict and isinstance(services_dict, dict):
        for service_name, service_config in services_dict.items():
            # 推断服务类型
            service_type = "clip" if "clip" in service_name else \
                          "clap" if "clap" in service_name else \
                          "whisper" if "whisper" in service_name else \
                          "unknown"
            
            service = ModelService(service_name, service_config)
            _load_balancer.add_service(service_type, service)
    
    return _load_balancer


async def route_request_to_model(service_type: str, request_data: Any) -> Optional[ModelService]:
    """路由请求到模型服务"""
    load_balancer = get_load_balancer()
    return await load_balancer.route_request(service_type, request_data)


def release_model_service(service_type: str, service: ModelService):
    """释放模型服务"""
    load_balancer = get_load_balancer()
    load_balancer.release_service(service_type, service)
"""
Infinity Embedding Inference Service (CLIP Image)
High performance CLIP model with Python-native inference
"""

from infinity_emb import Engine
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio
import logging
from typing import List, Optional, Dict, Any
import sys
import os


class EmbeddingRequest(BaseModel):
    texts: Optional[List[str]] = None
    images: Optional[List[str]] = None
    batch_size: Optional[int] = 32
    

class EmbeddingResponse(BaseModel):
    embeddings: List[List[float]]
    usage: Dict[str, Any]


app = FastAPI()
logger = logging.getLogger(__name__)


# 初始化Infinity CLIP服务
clip_engine = Engine(
    model_name_or_path="sentence-transformers/clip-ViT-B-32",
    device="auto",
    prefer_dtype="float32"
)


@app.post("/embeddings", response_model=EmbeddingResponse)
async def create_embeddings(request: EmbeddingRequest):
    try:
        embeddings_result = await clip_engine.embed(
            texts=request.texts,
            images=request.images,
            batch_size=request.batch_size or 32
        )
        
        return EmbeddingResponse(
            embeddings=embeddings_result.embeddings.tolist(),
            usage={"total": len(embeddings_result.embeddings)}
        )
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    return {"status": "healthy", "model": "clip-ViT-B-32"}


if __name__ == "__main__":
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=7997,
        log_level="info"
    )
"""
Infinity Embedding Inference Service (CLAP Audio)
High performance CLAP model with Python-native inference
"""

from infinity_emb import Engine
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio
import logging
from typing import List, Optional, Dict, Any
import sys
import os


class AudioEmbeddingRequest(BaseModel):
    audio_files: Optional[List[str]] = None
    texts: Optional[List[str]] = None
    batch_size: Optional[int] = 32
    

class AudioEmbeddingResponse(BaseModel):
    embeddings: List[List[float]]
    usage: Dict[str, Any]


app = FastAPI()
logger = logging.getLogger(__name__)


# 初始化Infinity CLAP服务
clap_engine = Engine(
    model_name_or_path="laion/clap-htsat-unfused",
    device="auto",
    prefer_dtype="float32"
)


@app.post("/embeddings", response_model=AudioEmbeddingResponse)
async def create_audio_embeddings(request: AudioEmbeddingRequest):
    try:
        embeddings_result = await clap_engine.embed(
            audio=request.audio_files,
            texts=request.texts,
            batch_size=request.batch_size or 32
        )
        
        return AudioEmbeddingResponse(
            embeddings=embeddings_result.embeddings.tolist(),
            usage={"total": len(embeddings_result.embeddings)}
        )
    except Exception as e:
        logger.error(f"Audio embedding generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    return {"status": "healthy", "model": "laion/clap-htsat-unfused"}


if __name__ == "__main__":
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=7998,
        log_level="info"
    )
"""
Infinity Transcription Service (Whisper)
High performance Whisper model with Python-native inference
"""

from infinity_emb import Engine
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio
import logging
from typing import List, Optional, Dict, Any
import sys
import os


class TranscriptionRequest(BaseModel):
    audio_files: List[str]
    language: Optional[str] = "zh"
    task: Optional[str] = "transcribe"
    

class TranscriptionSegment(BaseModel):
    text: str
    start: float
    end: float
    

class TranscriptionResponse(BaseModel):
    transcriptions: List[str]
    segments: List[List[TranscriptionSegment]]
    usage: Dict[str, Any]


app = FastAPI()
logger = logging.getLogger(__name__)


# 初始化Infinity Whisper服务
whisper_engine = Engine(
    model_name_or_path="openai/whisper-base",
    device="auto",
    prefer_dtype="float32"
)


@app.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(request: TranscriptionRequest):
    try:
        transcriptions_result = await whisper_engine.transcribe(
            audio_files=request.audio_files,
            language=request.language,
            task=request.task
        )
        
        # Convert segments to response format
        all_segments = []
        for segments in transcriptions_result.segments:
            segment_list = [TranscriptionSegment(text=seg.text, start=seg.start, end=seg.end) for seg in segments]
            all_segments.append(segment_list)
        
        return TranscriptionResponse(
            transcriptions=transcriptions_result.texts,
            segments=all_segments,
            usage={"total": len(transcriptions_result.texts)}
        )
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    return {"status": "healthy", "model": "openai/whisper-base"}


if __name__ == "__main__":
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=7999,
        log_level="info"
    )