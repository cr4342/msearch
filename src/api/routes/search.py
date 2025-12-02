"""
检索API路由
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Form
from pydantic import BaseModel

from src.search_service.smart_retrieval_engine import SmartRetrievalEngine

router = APIRouter()
logger = logging.getLogger(__name__)


class SearchRequest(BaseModel):
    """搜索请求模型"""
    query: str
    query_type: str = "text"  # text, image, audio
    top_k: int = 10
    filters: Optional[Dict[str, Any]] = None


class SearchResponse(BaseModel):
    """搜索响应模型"""
    status: str
    query: str
    total_results: int
    results: List[Dict[str, Any]]
    execution_time: float


@router.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """
    执行多模态检索
    
    Args:
        request: 搜索请求
        
    Returns:
        搜索结果
    """
    import time
    start_time = time.time()
    
    try:
        # 获取检索引擎
        from fastapi import Request
        
        # 在测试环境中，Request可能没有正确的app state
        # 我们直接创建或使用全局实例
        try:
            retrieval_engine: SmartRetrievalEngine = Request.app.state.retrieval_engine
        except AttributeError:
            # 测试环境回退方案
            from src.search_service.smart_retrieval_engine import SmartRetrievalEngine
            from src.core.config_manager import get_config_manager
            config_manager = get_config_manager()
            retrieval_engine = SmartRetrievalEngine(config_manager)
            await retrieval_engine.start()
        
        # 执行检索
        results = await retrieval_engine.search(
            query=request.query,
            query_type=request.query_type,
            top_k=request.top_k,
            filters=request.filters
        )
        
        execution_time = time.time() - start_time
        
        return SearchResponse(
            status="success",
            query=request.query,
            total_results=len(results),
            results=results,
            execution_time=execution_time
        )
        
    except Exception as e:
        logger.error(f"检索失败: {e}")
        raise HTTPException(status_code=500, detail=f"检索失败: {str(e)}")


@router.post("/search/image", response_model=SearchResponse)
async def search_by_image(
    image: UploadFile = File(...),
    top_k: int = Form(10),
    filters: Optional[str] = Form(None)
):
    """
    以图搜图
    
    Args:
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
        from fastapi import Request
        
        # 在测试环境中，Request可能没有正确的app state
        # 我们直接创建或使用全局实例
        try:
            retrieval_engine: SmartRetrievalEngine = Request.app.state.retrieval_engine
        except AttributeError:
            # 测试环境回退方案
            from src.search_service.smart_retrieval_engine import SmartRetrievalEngine
            from src.core.config_manager import get_config_manager
            config_manager = get_config_manager()
            retrieval_engine = SmartRetrievalEngine(config_manager)
            await retrieval_engine.start()
        
        # 执行检索
        results = await retrieval_engine.search(
            query=image_data,
            query_type="image",
            top_k=top_k,
            filters=filter_dict
        )
        
        execution_time = time.time() - start_time
        
        return SearchResponse(
            status="success",
            query=f"image_search_{image.filename}",
            total_results=len(results),
            results=results,
            execution_time=execution_time
        )
        
    except Exception as e:
        logger.error(f"以图搜图失败: {e}")
        raise HTTPException(status_code=500, detail=f"以图搜图失败: {str(e)}")


@router.post("/search/audio", response_model=SearchResponse)
async def search_by_audio(
    audio: UploadFile = File(...),
    top_k: int = Form(10),
    filters: Optional[str] = Form(None)
):
    """
    以音频搜音频
    
    Args:
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
        from fastapi import Request
        
        # 在测试环境中，Request可能没有正确的app state
        # 我们直接创建或使用全局实例
        try:
            retrieval_engine: SmartRetrievalEngine = Request.app.state.retrieval_engine
        except AttributeError:
            # 测试环境回退方案
            from src.search_service.smart_retrieval_engine import SmartRetrievalEngine
            from src.core.config_manager import get_config_manager
            config_manager = get_config_manager()
            retrieval_engine = SmartRetrievalEngine(config_manager)
            await retrieval_engine.start()
        
        # 执行检索
        results = await retrieval_engine.search(
            query=audio_data,
            query_type="audio",
            top_k=top_k,
            filters=filter_dict
        )
        
        execution_time = time.time() - start_time
        
        return SearchResponse(
            status="success",
            query=f"audio_search_{audio.filename}",
            total_results=len(results),
            results=results,
            execution_time=execution_time
        )
        
    except Exception as e:
        logger.error(f"以音频搜音频失败: {e}")
        raise HTTPException(status_code=500, detail=f"以音频搜音频失败: {str(e)}")


@router.get("/similar/{file_id}")
async def get_similar_files(
    file_id: str,
    top_k: int = Query(10, ge=1, le=100)
):
    """
    获取相似文件
    
    Args:
        file_id: 文件ID
        top_k: 返回结果数量
        
    Returns:
        相似文件列表
    """
    try:
        # 获取检索引擎
        from fastapi import Request
        
        # 在测试环境中，Request可能没有正确的app state
        # 我们直接创建或使用全局实例
        try:
            retrieval_engine: SmartRetrievalEngine = Request.app.state.retrieval_engine
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
    query: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50)
):
    """
    获取搜索建议
    
    Args:
        query: 部分查询
        limit: 返回建议数量
        
    Returns:
        搜索建议列表
    """
    try:
        # 获取检索引擎
        from fastapi import Request
        
        # 在测试环境中，Request可能没有正确的app state
        # 我们直接创建或使用全局实例
        try:
            retrieval_engine: SmartRetrievalEngine = Request.app.state.retrieval_engine
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
    limit: int = Query(10, ge=1, le=50)
):
    """
    获取热门搜索
    
    Args:
        limit: 返回热门搜索数量
        
    Returns:
        热门搜索列表
    """
    try:
        # 获取检索引擎
        from fastapi import Request
        
        # 在测试环境中，Request可能没有正确的app state
        # 我们直接创建或使用全局实例
        try:
            retrieval_engine: SmartRetrievalEngine = Request.app.state.retrieval_engine
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