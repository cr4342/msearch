"""
检索API路由
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Form, Request
from pydantic import BaseModel

from src.search_service.smart_retrieval_engine import SmartRetrievalEngine

router = APIRouter()
logger = logging.getLogger(__name__)


class SearchRequest(BaseModel):
    """搜索请求模型"""
    text: Optional[str] = None
    # 注意：image和audio需要通过File上传，不能通过JSON
    top_k: int = 10
    filters: Optional[Dict[str, Any]] = None


class SearchResponse(BaseModel):
    """搜索响应模型"""
    status: str
    text_query: Optional[str] = None
    has_image: bool = False
    has_audio: bool = False
    total_results: int
    results: List[Dict[str, Any]]
    execution_time: float


@router.post("/search", response_model=SearchResponse)
async def search(
    request: Request,
    text: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    audio: Optional[UploadFile] = File(None),
    top_k: int = Form(10),
    filters: Optional[str] = Form(None)
):
    """
    执行多模态混合检索
    
    Args:
        request: FastAPI请求对象
        text: 文本查询内容
        image: 图像查询数据
        audio: 音频查询数据
        top_k: 返回结果数量
        filters: 过滤条件（JSON字符串）
        
    Returns:
        搜索结果
    """
    import time
    import json
    start_time = time.time()
    
    try:
        # 解析过滤条件
        filter_dict = None
        if filters:
            try:
                filter_dict = json.loads(filters)
            except json.JSONDecodeError:
                logger.warning(f"无效的过滤条件JSON: {filters}")
        
        # 读取图像和音频数据
        image_data = None
        if image:
            image_data = await image.read()
        
        audio_data = None
        if audio:
            audio_data = await audio.read()
        
        # 获取检索引擎
        try:
            retrieval_engine: SmartRetrievalEngine = request.app.state.retrieval_engine
        except AttributeError:
            # 测试环境回退方案
            from src.search_service.smart_retrieval_engine import SmartRetrievalEngine
            from src.core.config_manager import get_config_manager
            config_manager = get_config_manager()
            retrieval_engine = SmartRetrievalEngine(config_manager)
            await retrieval_engine.start()
        
        # 执行检索
        results = await retrieval_engine.search(
            text=text,
            image=image_data,
            audio=audio_data,
            top_k=top_k,
            filters=filter_dict
        )
        
        execution_time = time.time() - start_time
        
        return SearchResponse(
            status="success",
            text_query=text,
            has_image=bool(image_data),
            has_audio=bool(audio_data),
            total_results=len(results),
            results=results,
            execution_time=execution_time
        )
        
    except Exception as e:
        logger.error(f"检索失败: {e}")
        raise HTTPException(status_code=500, detail=f"检索失败: {str(e)}")


@router.post("/search/image", response_model=SearchResponse)
async def search_by_image(
    request: Request,
    image: UploadFile = File(...),
    top_k: int = Form(10),
    filters: Optional[str] = Form(None)
):
    """
    以图搜图
    
    Args:
        request: FastAPI请求对象
        image: 图像文件
        top_k: 返回结果数量
        filters: 过滤条件（JSON字符串）
        
    Returns:
        搜索结果
    """
    import time
    import json
    start_time = time.time()
    
    try:
        # 读取图像数据
        image_data = await image.read()
        
        # 解析过滤条件
        filter_dict = None
        if filters:
            try:
                filter_dict = json.loads(filters)
            except json.JSONDecodeError:
                logger.warning(f"无效的过滤条件JSON: {filters}")
        
        # 获取检索引擎
        try:
            retrieval_engine: SmartRetrievalEngine = request.app.state.retrieval_engine
        except AttributeError:
            # 测试环境回退方案
            from src.search_service.smart_retrieval_engine import SmartRetrievalEngine
            from src.core.config_manager import get_config_manager
            config_manager = get_config_manager()
            retrieval_engine = SmartRetrievalEngine(config_manager)
            await retrieval_engine.start()
        
        # 执行检索
        results = await retrieval_engine.search(
            image=image_data,
            top_k=top_k,
            filters=filter_dict
        )
        
        execution_time = time.time() - start_time
        
        return SearchResponse(
            status="success",
            text_query=None,
            has_image=True,
            has_audio=False,
            total_results=len(results),
            results=results,
            execution_time=execution_time
        )
        
    except Exception as e:
        logger.error(f"以图搜图失败: {e}")
        raise HTTPException(status_code=500, detail=f"以图搜图失败: {str(e)}")


@router.post("/search/audio", response_model=SearchResponse)
async def search_by_audio(
    request: Request,
    audio: UploadFile = File(...),
    top_k: int = Form(10),
    filters: Optional[str] = Form(None)
):
    """
    以音频搜音频
    
    Args:
        request: FastAPI请求对象
        audio: 音频文件
        top_k: 返回结果数量
        filters: 过滤条件（JSON字符串）
        
    Returns:
        搜索结果
    """
    import time
    import json
    start_time = time.time()
    
    try:
        # 读取音频数据
        audio_data = await audio.read()
        
        # 解析过滤条件
        filter_dict = None
        if filters:
            try:
                filter_dict = json.loads(filters)
            except json.JSONDecodeError:
                logger.warning(f"无效的过滤条件JSON: {filters}")
        
        # 获取检索引擎
        try:
            retrieval_engine: SmartRetrievalEngine = request.app.state.retrieval_engine
        except AttributeError:
            # 测试环境回退方案
            from src.search_service.smart_retrieval_engine import SmartRetrievalEngine
            from src.core.config_manager import get_config_manager
            config_manager = get_config_manager()
            retrieval_engine = SmartRetrievalEngine(config_manager)
            await retrieval_engine.start()
        
        # 执行检索
        results = await retrieval_engine.search(
            audio=audio_data,
            top_k=top_k,
            filters=filter_dict
        )
        
        execution_time = time.time() - start_time
        
        return SearchResponse(
            status="success",
            text_query=None,
            has_image=False,
            has_audio=True,
            total_results=len(results),
            results=results,
            execution_time=execution_time
        )
        
    except Exception as e:
        logger.error(f"以音频搜音频失败: {e}")
        raise HTTPException(status_code=500, detail=f"以音频搜音频失败: {str(e)}")


@router.get("/similar/{file_id}")
async def get_similar_files(
    request: Request,
    file_id: str,
    top_k: int = Query(10, ge=1, le=100)
):
    """
    获取相似文件
    
    Args:
        request: FastAPI请求对象
        file_id: 文件ID
        top_k: 返回结果数量
        
    Returns:
        相似文件列表
    """
    try:
        # 获取检索引擎
        try:
            retrieval_engine: SmartRetrievalEngine = request.app.state.retrieval_engine
        except AttributeError:
            # 测试环境回退方案
            from src.search_service.smart_retrieval_engine import SmartRetrievalEngine
            from src.core.config_manager import get_config_manager
            config_manager = get_config_manager()
            retrieval_engine = SmartRetrievalEngine(config_manager)
            await retrieval_engine.start()
        
        # 获取相似文件
        results = await retrieval_engine.get_similar_files(file_id, top_k)
        
        return {
            "status": "success",
            "file_id": file_id,
            "total_results": len(results),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"获取相似文件失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取相似文件失败: {str(e)}")


@router.get("/suggestions")
async def get_search_suggestions(
    request: Request,
    query: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50)
):
    """
    获取搜索建议
    
    Args:
        request: FastAPI请求对象
        query: 部分查询
        limit: 返回建议数量
        
    Returns:
        搜索建议列表
    """
    try:
        # 获取检索引擎
        try:
            retrieval_engine: SmartRetrievalEngine = request.app.state.retrieval_engine
        except AttributeError:
            # 测试环境回退方案
            from src.search_service.smart_retrieval_engine import SmartRetrievalEngine
            from src.core.config_manager import get_config_manager
            config_manager = get_config_manager()
            retrieval_engine = SmartRetrievalEngine(config_manager)
            await retrieval_engine.start()
        
        # 获取搜索建议
        suggestions = await retrieval_engine.get_search_suggestions(query, limit)
        
        return {
            "status": "success",
            "query": query,
            "suggestions": suggestions
        }
        
    except Exception as e:
        logger.error(f"获取搜索建议失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取搜索建议失败: {str(e)}")


@router.get("/popular")
async def get_popular_searches(
    request: Request,
    limit: int = Query(10, ge=1, le=50)
):
    """
    获取热门搜索
    
    Args:
        request: FastAPI请求对象
        limit: 返回热门搜索数量
        
    Returns:
        热门搜索列表
    """
    try:
        # 获取检索引擎
        try:
            retrieval_engine: SmartRetrievalEngine = request.app.state.retrieval_engine
        except AttributeError:
            # 测试环境回退方案
            from src.search_service.smart_retrieval_engine import SmartRetrievalEngine
            from src.core.config_manager import get_config_manager
            config_manager = get_config_manager()
            retrieval_engine = SmartRetrievalEngine(config_manager)
            await retrieval_engine.start()
        
        # 获取热门搜索
        popular_searches = await retrieval_engine.get_popular_searches(limit)
        
        return {
            "status": "success",
            "popular_searches": popular_searches
        }
        
    except Exception as e:
        logger.error(f"获取热门搜索失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取热门搜索失败: {str(e)}")