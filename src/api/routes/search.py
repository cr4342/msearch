"""
搜索API路由实现
提供多模态检索功能的REST API接口
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio
import logging
from pathlib import Path
import tempfile
import os

from ...search_service.smart_retrieval_engine import SmartRetrievalEngine
from ...common.embedding.embedding_engine import EmbeddingEngine
from ...core.config_manager import ConfigManager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/search", tags=["search"])

# 数据模型
class TextSearchRequest(BaseModel):
    query: str
    limit: int = 20
    modalities: List[str] = ["visual", "audio", "text"]
    weights: Optional[Dict[str, float]] = None

class SearchResult(BaseModel):
    file_path: str
    similarity_score: float
    timestamp: Optional[float] = None
    thumbnail_path: Optional[str] = None
    file_type: str
    metadata: Dict[str, Any] = {}

class SearchResponse(BaseModel):
    results: List[SearchResult]
    total_count: int
    query_time: float
    query_type: str

# 依赖注入
async def get_retrieval_engine():
    """获取检索引擎实例"""
    config_manager = ConfigManager()
    return SmartRetrievalEngine(config_manager)

async def get_embedding_engine():
    """获取向量化引擎实例"""
    config_manager = ConfigManager()
    return EmbeddingEngine(config_manager)

@router.post("/text", response_model=SearchResponse)
async def text_search(
    request: TextSearchRequest,
    retrieval_engine: SmartRetrievalEngine = Depends(get_retrieval_engine)
):
    """
    基于文本的多模态检索
    
    Args:
        request: 文本搜索请求
        retrieval_engine: 检索引擎实例
    
    Returns:
        SearchResponse: 搜索结果
    """
    try:
        logger.info(f"执行文本搜索: {request.query}")
        
        # 执行检索
        results = await retrieval_engine.search(
            query=request.query,
            query_type="text",
            modalities=request.modalities,
            limit=request.limit,
            weights=request.weights
        )
        
        # 转换结果格式
        search_results = []
        for result in results:
            search_results.append(SearchResult(
                file_path=result.get("file_path", ""),
                similarity_score=result.get("similarity_score", 0.0),
                timestamp=result.get("timestamp"),
                thumbnail_path=result.get("thumbnail_path"),
                file_type=result.get("file_type", "unknown"),
                metadata=result.get("metadata", {})
            ))
        
        return SearchResponse(
            results=search_results,
            total_count=len(search_results),
            query_time=results[0].get("query_time", 0.0) if results else 0.0,
            query_type="text"
        )
        
    except Exception as e:
        logger.error(f"文本搜索失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")

@router.post("/image", response_model=SearchResponse)
async def image_search(
    file: UploadFile = File(...),
    limit: int = 20,
    modalities: List[str] = ["visual"],
    retrieval_engine: SmartRetrievalEngine = Depends(get_retrieval_engine),
    embedding_engine: EmbeddingEngine = Depends(get_embedding_engine)
):
    """
    基于图像的多模态检索
    
    Args:
        file: 上传的图像文件
        limit: 返回结果数量限制
        modalities: 检索的模态类型
        retrieval_engine: 检索引擎实例
        embedding_engine: 向量化引擎实例
    
    Returns:
        SearchResponse: 搜索结果
    """
    try:
        logger.info(f"执行图像搜索: {file.filename}")
        
        # 验证文件类型
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="只支持图像文件")
        
        # 保存临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # 生成图像向量
            image_vector = await embedding_engine.encode_image(temp_file_path)
            
            # 执行检索
            results = await retrieval_engine.search_by_vector(
                vector=image_vector,
                query_type="image",
                modalities=modalities,
                limit=limit
            )
            
            # 转换结果格式
            search_results = []
            for result in results:
                search_results.append(SearchResult(
                    file_path=result.get("file_path", ""),
                    similarity_score=result.get("similarity_score", 0.0),
                    timestamp=result.get("timestamp"),
                    thumbnail_path=result.get("thumbnail_path"),
                    file_type=result.get("file_type", "unknown"),
                    metadata=result.get("metadata", {})
                ))
            
            return SearchResponse(
                results=search_results,
                total_count=len(search_results),
                query_time=results[0].get("query_time", 0.0) if results else 0.0,
                query_type="image"
            )
            
        finally:
            # 清理临时文件
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
        
    except Exception as e:
        logger.error(f"图像搜索失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")

@router.post("/audio", response_model=SearchResponse)
async def audio_search(
    file: UploadFile = File(...),
    limit: int = 20,
    modalities: List[str] = ["audio"],
    retrieval_engine: SmartRetrievalEngine = Depends(get_retrieval_engine),
    embedding_engine: EmbeddingEngine = Depends(get_embedding_engine)
):
    """
    基于音频的多模态检索
    
    Args:
        file: 上传的音频文件
        limit: 返回结果数量限制
        modalities: 检索的模态类型
        retrieval_engine: 检索引擎实例
        embedding_engine: 向量化引擎实例
    
    Returns:
        SearchResponse: 搜索结果
    """
    try:
        logger.info(f"执行音频搜索: {file.filename}")
        
        # 验证文件类型
        if not file.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="只支持音频文件")
        
        # 保存临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # 音频分类和处理
            audio_type = await embedding_engine.classify_audio(temp_file_path)
            
            if audio_type == "music":
                # 使用CLAP模型处理音乐
                audio_vector = await embedding_engine.encode_audio_music(temp_file_path)
                search_modalities = ["audio_music"]
            elif audio_type == "speech":
                # 使用Whisper模型转录语音
                transcription = await embedding_engine.transcribe_audio(temp_file_path)
                # 按文本检索
                results = await retrieval_engine.search(
                    query=transcription,
                    query_type="speech",
                    modalities=["text", "audio_speech"],
                    limit=limit
                )
                
                # 转换结果格式
                search_results = []
                for result in results:
                    search_results.append(SearchResult(
                        file_path=result.get("file_path", ""),
                        similarity_score=result.get("similarity_score", 0.0),
                        timestamp=result.get("timestamp"),
                        thumbnail_path=result.get("thumbnail_path"),
                        file_type=result.get("file_type", "unknown"),
                        metadata={**result.get("metadata", {}), "transcription": transcription}
                    ))
                
                return SearchResponse(
                    results=search_results,
                    total_count=len(search_results),
                    query_time=results[0].get("query_time", 0.0) if results else 0.0,
                    query_type="speech"
                )
            else:
                raise HTTPException(status_code=400, detail="无法识别的音频类型")
            
            # 对于音乐类型，执行向量检索
            results = await retrieval_engine.search_by_vector(
                vector=audio_vector,
                query_type="audio",
                modalities=search_modalities,
                limit=limit
            )
            
            # 转换结果格式
            search_results = []
            for result in results:
                search_results.append(SearchResult(
                    file_path=result.get("file_path", ""),
                    similarity_score=result.get("similarity_score", 0.0),
                    timestamp=result.get("timestamp"),
                    thumbnail_path=result.get("thumbnail_path"),
                    file_type=result.get("file_type", "unknown"),
                    metadata=result.get("metadata", {})
                ))
            
            return SearchResponse(
                results=search_results,
                total_count=len(search_results),
                query_time=results[0].get("query_time", 0.0) if results else 0.0,
                query_type="audio"
            )
            
        finally:
            # 清理临时文件
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
        
    except Exception as e:
        logger.error(f"音频搜索失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")

@router.post("/multimodal", response_model=SearchResponse)
async def multimodal_search(
    query: Optional[str] = None,
    image_file: Optional[UploadFile] = File(None),
    audio_file: Optional[UploadFile] = File(None),
    limit: int = 20,
    modalities: List[str] = ["visual", "audio", "text"],
    weights: Optional[Dict[str, float]] = None,
    retrieval_engine: SmartRetrievalEngine = Depends(get_retrieval_engine)
):
    """
    多模态混合检索
    
    Args:
        query: 文本查询
        image_file: 图像文件
        audio_file: 音频文件
        limit: 返回结果数量限制
        modalities: 检索的模态类型
        weights: 各模态权重
        retrieval_engine: 检索引擎实例
    
    Returns:
        SearchResponse: 搜索结果
    """
    try:
        logger.info("执行多模态混合搜索")
        
        # 验证至少有一种输入
        if not any([query, image_file, audio_file]):
            raise HTTPException(status_code=400, detail="至少需要提供一种查询输入")
        
        # 执行混合检索
        results = await retrieval_engine.multimodal_search(
            text_query=query,
            image_file=image_file,
            audio_file=audio_file,
            modalities=modalities,
            limit=limit,
            weights=weights
        )
        
        # 转换结果格式
        search_results = []
        for result in results:
            search_results.append(SearchResult(
                file_path=result.get("file_path", ""),
                similarity_score=result.get("similarity_score", 0.0),
                timestamp=result.get("timestamp"),
                thumbnail_path=result.get("thumbnail_path"),
                file_type=result.get("file_type", "unknown"),
                metadata=result.get("metadata", {})
            ))
        
        return SearchResponse(
            results=search_results,
            total_count=len(search_results),
            query_time=results[0].get("query_time", 0.0) if results else 0.0,
            query_type="multimodal"
        )
        
    except Exception as e:
        logger.error(f"多模态搜索失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")

@router.get("/suggestions")
async def get_search_suggestions(
    query: str,
    limit: int = 10,
    retrieval_engine: SmartRetrievalEngine = Depends(get_retrieval_engine)
):
    """
    获取搜索建议
    
    Args:
        query: 查询文本
        limit: 建议数量限制
        retrieval_engine: 检索引擎实例
    
    Returns:
        List[str]: 搜索建议列表
    """
    try:
        suggestions = await retrieval_engine.get_search_suggestions(query, limit)
        return {"suggestions": suggestions}
        
    except Exception as e:
        logger.error(f"获取搜索建议失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取建议失败: {str(e)}")