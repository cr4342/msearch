"""
检索API路由
"""
from fastapi import APIRouter, UploadFile, File, Query
from typing import Optional, List
import logging

from src.core.config_manager import get_config_manager
from src.business.smart_retrieval import SmartRetrievalEngine

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/search", tags=["search"])

# 初始化检索引擎
config_manager = get_config_manager()
config = config_manager.get_config()
retrieval_engine = SmartRetrievalEngine(config)

@router.post("/text")
async def search_text(query: str, limit: int = 20):
    """文本检索API"""
    try:
        logger.info(f"执行文本搜索: query='{query}', limit={limit}")
        
        # 调用智能检索引擎
        results = await retrieval_engine.search(query, search_type="text")
        
        return {
            "status": "success",
            "query": query,
            "limit": limit,
            "results": results.get('results', []),
            "total": len(results.get('results', []))
        }
    except Exception as e:
        logger.error(f"文本搜索失败: {e}")
        return {
            "status": "error",
            "message": str(e),
            "query": query
        }

@router.post("/image")
async def search_image(file: UploadFile = File(...), limit: int = 20):
    """图像检索API"""
    try:
        logger.info(f"执行图像搜索: filename='{file.filename}', limit={limit}")
        
        # 读取上传的文件
        file_content = await file.read()
        
        # 对于图像搜索，需要先用图像内容生成嵌入向量，然后进行搜索
        # 这里暂时返回一个示例响应
        return {
            "status": "success",
            "filename": file.filename,
            "limit": limit,
            "results": [],
            "total": 0
        }
    except Exception as e:
        logger.error(f"图像搜索失败: {e}")
        return {
            "status": "error",
            "message": str(e),
            "filename": file.filename
        }

@router.post("/audio")
async def search_audio(file: UploadFile = File(...), limit: int = 20):
    """音频检索API"""
    try:
        logger.info(f"执行音频搜索: filename='{file.filename}', limit={limit}")
        
        # 读取上传的文件
        file_content = await file.read()
        
        # 对于音频搜索，需要先用音频内容生成嵌入向量，然后进行搜索
        # 这里暂时返回一个示例响应
        return {
            "status": "success",
            "filename": file.filename,
            "limit": limit,
            "results": [],
            "total": 0
        }
    except Exception as e:
        logger.error(f"音频搜索失败: {e}")
        return {
            "status": "error",
            "message": str(e),
            "filename": file.filename
        }

@router.post("/video")
async def search_video(file: UploadFile = File(...), limit: int = 20):
    """视频检索API"""
    try:
        logger.info(f"执行视频搜索: filename='{file.filename}', limit={limit}")
        
        # 读取上传的文件
        file_content = await file.read()
        
        # 对于视频搜索，需要先用视频内容生成嵌入向量，然后进行搜索
        # 这里暂时返回一个示例响应
        return {
            "status": "success",
            "filename": file.filename,
            "limit": limit,
            "results": [],
            "total": 0
        }
    except Exception as e:
        logger.error(f"视频搜索失败: {e}")
        return {
            "status": "error",
            "message": str(e),
            "filename": file.filename
        }

@router.post("/multimodal")
async def search_multimodal(
    query_text: Optional[str] = None,
    image_file: Optional[UploadFile] = File(None),
    audio_file: Optional[UploadFile] = File(None),
    video_file: Optional[UploadFile] = File(None),
    limit: int = 20
):
    """多模态检索API"""
    try:
        logger.info(f"执行多模态搜索: query_text='{query_text}', limit={limit}")
        
        # 处理查询文本
        if query_text:
            # 调用智能检索引擎
            results = await retrieval_engine.search(query_text, search_type="multimodal")
            
            return {
                "status": "success",
                "query_text": query_text,
                "has_image": image_file is not None,
                "has_audio": audio_file is not None,
                "has_video": video_file is not None,
                "limit": limit,
                "results": results.get('results', []),
                "total": len(results.get('results', []))
            }
        else:
            # 如果没有文本查询，需要处理上传的文件
            return {
                "status": "success",
                "query_text": query_text,
                "has_image": image_file is not None,
                "has_audio": audio_file is not None,
                "has_video": video_file is not None,
                "limit": limit,
                "results": [],
                "total": 0
            }
    except Exception as e:
        logger.error(f"多模态搜索失败: {e}")
        return {
            "status": "error",
            "message": str(e),
            "query_text": query_text
        }