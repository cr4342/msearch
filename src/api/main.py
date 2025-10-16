#!/usr/bin/env python3
"""
msearch 后端API服务主入口
基于FastAPI实现RESTful API服务
"""

import os
import sys
from pathlib import Path

# 将src目录添加到Python路径中
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from typing import List, Dict, Optional

from src.core.config import load_config
from src.core.logging_config import setup_logging, get_logger
from src.core.processing_orchestrator import get_processing_orchestrator

# 创建FastAPI应用实例
app = FastAPI(
    title="msearch API",
    description="msearch 多模态检索系统API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理"""
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": f"服务器内部错误: {str(exc)}"}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """HTTP异常处理"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "message": exc.detail}
    )

# 获取日志记录器
logger = get_logger(__name__)

# 获取处理编排器实例
processing_orchestrator = get_processing_orchestrator()

# 健康检查端点
@app.get("/health", summary="健康检查")
async def health_check():
    """健康检查端点"""
    return {
        "success": True,
        "message": "服务运行正常",
        "data": {
            "status": "healthy",
            "timestamp": __import__('datetime').datetime.now().isoformat()
        }
    }

# 系统版本端点
@app.get("/api/v1/system/version", summary="获取系统版本")
async def get_system_version():
    """获取系统版本信息"""
    return {
        "success": True,
        "message": "版本信息获取成功",
        "data": {
            "version": "v0.1",
            "environment": os.getenv("ENVIRONMENT", "development")
        }
    }

# 系统状态端点
@app.get("/api/v1/system/status", summary="获取系统状态")
async def get_system_status():
    """获取系统状态信息"""
    import psutil
    import time
    
    # 获取系统资源使用情况
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return {
        "success": True,
        "message": "系统状态获取成功",
        "data": {
            "cpu_usage": f"{cpu_percent}%",
            "memory_usage": f"{memory.percent}%",
            "memory_available": f"{memory.available / (1024**3):.2f} GB",
            "disk_usage": f"{(disk.used / disk.total) * 100:.2f}%",
            "disk_available": f"{disk.free / (1024**3):.2f} GB",
            "uptime": f"{time.time() - psutil.boot_time():.0f} seconds"
        }
    }

# 数据库状态端点
@app.get("/api/v1/system/db-status", summary="获取数据库状态")
async def get_database_status():
    """获取数据库连接状态"""
    # 这里应该实际检查数据库连接状态
    # 目前返回模拟数据
    return {
        "success": True,
        "message": "数据库状态检查完成",
        "data": {
            "sqlite_connected": True,
            "qdrant_connected": True,
            "sqlite_version": "3.35.0",
            "qdrant_version": "1.1.0"
        }
    }

# 获取配置端点
@app.get("/api/v1/config", summary="获取系统配置")
async def get_system_config():
    """
    获取系统配置信息
    """
    try:
        from src.core.config import get_config
        
        # 获取当前配置
        config = get_config()
        
        # 返回配置信息（隐藏敏感信息）
        safe_config = {
            "hardware_mode": config.get("hardware_mode", "cpu"),
            "paths": {
                "watch_directories": config.get("paths", {}).get("watch_directories", []),
                "sqlite_db_path": config.get("paths", {}).get("sqlite_db_path", ""),
                "log_file_path": config.get("paths", {}).get("log_file_path", "")
            },
            "preprocessing": config.get("preprocessing", {}),
            "system": config.get("system", {}),
            "fastapi": config.get("fastapi", {}),
            "qdrant": {
                "host": config.get("qdrant", {}).get("host", ""),
                "port": config.get("qdrant", {}).get("port", 0),
                "collections": config.get("qdrant", {}).get("collections", {})
            }
        }
        
        return {
            "success": True,
            "message": "配置信息获取成功",
            "data": safe_config
        }
    except Exception as e:
        logger.error(f"获取配置信息失败: {e}")
        raise HTTPException(500, f"获取配置信息失败: {str(e)}")

# 更新配置端点
@app.put("/api/v1/config", summary="更新系统配置")
async def update_system_config(config_updates: dict):
    """
    更新系统配置信息
    
    参数:
    - config_updates: 配置更新内容
    """
    try:
        from src.core.config import get_config
        import yaml
        from pathlib import Path
        
        # 获取配置文件路径
        config_path = Path(__file__).parent.parent.parent / "config" / "config.yml"
        
        # 加载当前配置
        with open(config_path, 'r', encoding='utf-8') as f:
            current_config = yaml.safe_load(f)
        
        # 更新配置
        def update_nested_dict(d, u):
            for k, v in u.items():
                if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                    update_nested_dict(d[k], v)
                else:
                    d[k] = v
            return d
        
        updated_config = update_nested_dict(current_config, config_updates)
        
        # 保存更新后的配置
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(updated_config, f, allow_unicode=True, default_flow_style=False)
        
        return {
            "success": True,
            "message": "配置更新成功",
            "data": updated_config
        }
    except Exception as e:
        logger.error(f"更新配置失败: {e}")
        raise HTTPException(500, f"更新配置失败: {str(e)}")

# 系统重置端点
@app.post("/api/v1/system/reset", summary="系统重置")
async def system_reset(reset_type: str = "all"):
    """
    系统重置API - 实现前后端完全分离的关键接口
    
    参数:
    - reset_type: 重置类型 (all-全部重置, database-仅数据库, index-仅索引)
    """
    try:
        # 这里应该实现实际的重置逻辑
        # 目前返回模拟数据
        return {
            "success": True,
            "message": f"系统重置成功: {reset_type}",
            "data": {"reset_type": reset_type}
        }
    except Exception as e:
        raise HTTPException(500, f"重置失败: {str(e)}")

# 文件处理端点
@app.post("/api/v1/files/process", summary="处理文件")
async def process_file(file_path: str, file_id: int):
    """
    处理文件API - 使用ProcessingOrchestrator编排处理流程
    
    参数:
    - file_path: 文件路径
    - file_id: 文件ID
    """
    try:
        # 使用处理编排器处理文件
        result = await processing_orchestrator.process_file(file_path, str(file_id))
        
        return {
            "success": result["success"],
            "message": "文件处理完成" if result["success"] else "文件处理失败",
            "data": result
        }
    except Exception as e:
        logger.error(f"文件处理失败: {e}")
        raise HTTPException(500, f"文件处理失败: {str(e)}")

# 批量文件处理端点
@app.post("/api/v1/files/batch-process", summary="批量处理文件")
async def batch_process_files(file_list: List[Dict[str, str]]):
    """
    批量处理文件API
    
    参数:
    - file_list: 文件列表 [{"file_path": "...", "file_id": "..."}, ...]
    """
    try:
        # 使用处理编排器批量处理文件
        results = await processing_orchestrator.batch_process_files(file_list)
        
        success_count = len([r for r in results if r.get("success")])
        
        return {
            "success": True,
            "message": f"批量处理完成: {success_count}/{len(results)} 成功",
            "data": results
        }
    except Exception as e:
        logger.error(f"批量文件处理失败: {e}")
        raise HTTPException(500, f"批量文件处理失败: {str(e)}")

# 获取文件处理状态端点
@app.get("/api/v1/files/process-status/{file_id}", summary="获取文件处理状态")
async def get_process_status(file_id: int):
    """
    获取文件处理状态API
    
    参数:
    - file_id: 文件ID
    """
    try:
        # 获取处理状态
        status = processing_orchestrator.get_processing_status(str(file_id))
        
        return {
            "success": True,
            "message": "状态获取成功",
            "data": status
        }
    except Exception as e:
        logger.error(f"获取处理状态失败: {e}")
        raise HTTPException(500, f"获取处理状态失败: {str(e)}")

# 文件监控状态端点
@app.get("/api/v1/monitoring/status", summary="获取文件监控状态")
async def get_monitoring_status():
    """
    获取文件监控状态
    
    Returns:
        监控状态信息
    """
    try:
        from src.services.file_monitor import get_file_monitor
        
        # 获取文件监控器实例
        file_monitor = get_file_monitor()
        
        # 获取监控状态
        status = file_monitor.get_monitoring_status()
        
        return {
            "success": True,
            "message": "监控状态获取成功",
            "data": status
        }
    except Exception as e:
        logger.error(f"获取监控状态失败: {e}")
        raise HTTPException(500, f"获取监控状态失败: {str(e)}")

# 启动文件监控端点
@app.post("/api/v1/monitoring/start", summary="启动文件监控")
async def start_monitoring():
    """
    启动文件监控服务
    """
    try:
        from src.services.file_monitor import get_file_monitor
        
        # 获取文件监控器实例
        file_monitor = get_file_monitor()
        
        # 启动监控
        file_monitor.start_monitoring()
        
        return {
            "success": True,
            "message": "文件监控已启动",
            "data": file_monitor.get_monitoring_status()
        }
    except Exception as e:
        logger.error(f"启动文件监控失败: {e}")
        raise HTTPException(500, f"启动文件监控失败: {str(e)}")

# 停止文件监控端点
@app.post("/api/v1/monitoring/stop", summary="停止文件监控")
async def stop_monitoring():
    """
    停止文件监控服务
    """
    try:
        from src.services.file_monitor import get_file_monitor
        
        # 获取文件监控器实例
        file_monitor = get_file_monitor()
        
        # 停止监控
        file_monitor.stop_monitoring()
        
        return {
            "success": True,
            "message": "文件监控已停止",
            "data": file_monitor.get_monitoring_status()
        }
    except Exception as e:
        logger.error(f"停止文件监控失败: {e}")
        raise HTTPException(500, f"停止文件监控失败: {str(e)}")

# 文本检索端点
@app.post("/api/v1/search/text", summary="文本检索")
async def search_text(query: str, limit: int = 20):
    """
    文本检索API - 支持跨模态检索

    参数:
    - query: 查询文本
    - limit: 返回结果数量限制
    """
    try:
        from src.models.model_manager import get_model_manager
        from src.models.vector_store import get_vector_store
        from src.core.db_adapter import get_db_adapter
        
        # 获取模型管理器、向量存储和数据库适配器实例
        model_manager = get_model_manager()
        vector_store = get_vector_store()
        db_adapter = get_db_adapter()
        
        # 检查模型状态
        model_status = model_manager.get_model_status()
        if not model_status["infinity_available"]:
            raise HTTPException(503, "Infinity服务不可用，请检查服务状态")
        if not model_status["qdrant_available"]:
            raise HTTPException(503, "Qdrant向量数据库不可用，请检查服务状态")
        
        # 文本向量化
        logger.info(f"开始文本检索: {query}")
        text_vectors = await model_manager.embed_text_for_search(query)
        
        # 在不同模态的向量数据库中搜索
        results = []
        
        # 搜索CLIP向量（图像/视频）
        if "clip_vector" in text_vectors:
            clip_results = await vector_store.search(
                collection_name="msearch_clip_v1",
                query_vector=text_vectors["clip_vector"],
                limit=limit
            )
            results.extend(clip_results)
        
        # 搜索CLAP向量（音频）
        if "clap_vector" in text_vectors:
            clap_results = await vector_store.search(
                collection_name="msearch_clap_v1",
                query_vector=text_vectors["clap_vector"],
                limit=limit
            )
            results.extend(clap_results)
        
        # 按相似度排序并限制数量
        results.sort(key=lambda x: x["score"], reverse=True)
        results = results[:limit]
        
        # 获取详细文件信息
        detailed_results = []
        for result in results:
            # 从数据库获取详细信息
            file_metadata = await db_adapter.get_file_metadata(result["payload"].get("file_id"))
            if file_metadata:
                detailed_results.append({
                    "id": result["id"],
                    "score": result["score"],
                    "file_path": file_metadata.get("file_path", ""),
                    "file_type": file_metadata.get("file_type", "unknown"),
                    "start_time_ms": result["payload"].get("start_time_ms", 0),
                    "end_time_ms": result["payload"].get("end_time_ms", 0),
                    "metadata": {
                        **file_metadata,
                        "vector_metadata": result["payload"]
                    }
                })
        
        return {
            "success": True,
            "message": "文本检索完成",
            "data": {
                "query": query,
                "results": detailed_results,
                "total": len(detailed_results)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文本检索失败: {e}")
        raise HTTPException(500, f"文本检索失败: {str(e)}")

# 图像检索端点
@app.post("/api/v1/search/image", summary="图像检索")
async def search_image(file: UploadFile = File(...), limit: int = 20):
    """
    图像检索API - 以图搜图/视频
    
    参数:
    - file: 图像文件
    - limit: 返回结果数量限制
    """
    try:
        import tempfile
        import os
        from src.models.model_manager import get_model_manager
        from src.models.vector_store import get_vector_store
        
        # 获取模型管理器和向量存储实例
        model_manager = get_model_manager()
        vector_store = get_vector_store()
        
        # 保存上传的文件到临时位置
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(await file.read())
            tmp_file_path = tmp_file.name
        
        try:
            # 图像向量化
            logger.info(f"开始图像检索: {file.filename}")
            image_vector = await model_manager.embed_image(tmp_file_path)
            
            # 在CLIP向量数据库中搜索（图像/视频）
            results = await vector_store.search(
                collection_name="msearch_clip_v1",
                query_vector=image_vector,
                limit=limit
            )
            
            # 获取详细文件信息
            detailed_results = []
            for result in results:
                detailed_results.append({
                    "id": result["id"],
                    "score": result["score"],
                    "file_path": result["payload"].get("file_path", ""),
                    "file_type": result["payload"].get("segment_type", "unknown"),
                    "start_time_ms": result["payload"].get("start_time_ms", 0),
                    "end_time_ms": result["payload"].get("end_time_ms", 0),
                    "metadata": result["payload"]
                })
            
            return {
                "success": True,
                "message": "图像检索完成",
                "data": {
                    "query_image": file.filename,
                    "results": detailed_results,
                    "total": len(detailed_results)
                }
            }
        finally:
            # 清理临时文件
            os.unlink(tmp_file_path)
    except Exception as e:
        logger.error(f"图像检索失败: {e}")
        raise HTTPException(500, f"图像检索失败: {str(e)}")

# 音频检索端点
@app.post("/api/v1/search/audio", summary="音频检索")
async def search_audio(file: UploadFile = File(...), limit: int = 20):
    """
    音频检索API - 以音频搜音频/视频
    
    参数:
    - file: 音频文件
    - limit: 返回结果数量限制
    """
    try:
        import tempfile
        import os
        from src.models.model_manager import get_model_manager
        from src.models.vector_store import get_vector_store
        
        # 获取模型管理器和向量存储实例
        model_manager = get_model_manager()
        vector_store = get_vector_store()
        
        # 保存上传的文件到临时位置
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(await file.read())
            tmp_file_path = tmp_file.name
        
        try:
            # 音频处理和向量化
            logger.info(f"开始音频检索: {file.filename}")
            
            # 智能处理音频（区分音乐和语音）
            audio_results = await model_manager.process_video_audio_intelligently(tmp_file_path)
            
            # 合并所有音频片段的向量进行搜索
            all_results = []
            for audio_result in audio_results:
                if audio_result['segment_type'] == 'audio_music':
                    # 音乐片段使用CLAP向量数据库搜索
                    results = await vector_store.search(
                        collection_name="msearch_clap_v1",
                        query_vector=audio_result['vector'],
                        limit=limit
                    )
                    # 为每个结果添加音频类型信息
                    for result in results:
                        result["segment_type"] = "audio_music"
                        result["transcribed_text"] = None
                    all_results.extend(results)
                elif audio_result['segment_type'] == 'audio_speech':
                    # 语音片段使用CLIP向量数据库搜索（通过转录文本）
                    results = await vector_store.search(
                        collection_name="msearch_clip_v1",
                        query_vector=audio_result['vector'],
                        limit=limit
                    )
                    # 为每个结果添加音频类型信息和转录文本
                    for result in results:
                        result["segment_type"] = "audio_speech"
                        result["transcribed_text"] = audio_result.get('transcribed_text', '')
                    all_results.extend(results)
            
            # 按相似度排序并限制数量
            all_results.sort(key=lambda x: x["score"], reverse=True)
            all_results = all_results[:limit]
            
            # 获取详细文件信息
            detailed_results = []
            for result in all_results:
                detailed_results.append({
                    "id": result["id"],
                    "score": result["score"],
                    "file_path": result["payload"].get("file_path", ""),
                    "file_type": result["payload"].get("segment_type", "unknown"),
                    "segment_type": result.get("segment_type", "unknown"),
                    "start_time_ms": result["payload"].get("start_time_ms", 0),
                    "end_time_ms": result["payload"].get("end_time_ms", 0),
                    "transcribed_text": result.get("transcribed_text", ""),
                    "metadata": result["payload"]
                })
            
            return {
                "success": True,
                "message": "音频检索完成",
                "data": {
                    "query_audio": file.filename,
                    "results": detailed_results,
                    "total": len(detailed_results)
                }
            }
        finally:
            # 清理临时文件
            os.unlink(tmp_file_path)
    except Exception as e:
        logger.error(f"音频检索失败: {e}")
        raise HTTPException(500, f"音频检索失败: {str(e)}")

# 视频检索端点
@app.post("/api/v1/search/video", summary="视频检索")
async def search_video(file: UploadFile = File(...), limit: int = 20):
    """
    视频检索API - 以视频搜视频/图像
    
    参数:
    - file: 视频文件
    - limit: 返回结果数量限制
    """
    try:
        import tempfile
        import os
        from src.models.model_manager import get_model_manager
        from src.models.vector_store import get_vector_store
        from src.services.media_processor import get_media_processor
        
        # 获取模型管理器和向量存储实例
        model_manager = get_model_manager()
        vector_store = get_vector_store()
        media_processor = get_media_processor()
        
        # 保存上传的文件到临时位置
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(await file.read())
            tmp_file_path = tmp_file.name
        
        try:
            # 视频帧向量化
            logger.info(f"开始视频检索: {file.filename}")
            frame_vectors = await model_manager.embed_video_frames(tmp_file_path)
            
            # 获取视频信息用于时间戳定位
            video_info = media_processor._get_video_info(tmp_file_path)
            
            # 合并所有视频帧的向量进行搜索
            all_results = []
            for i, frame_vector in enumerate(frame_vectors):
                # 在CLIP向量数据库中搜索（图像/视频）
                results = await vector_store.search(
                    collection_name="msearch_clip_v1",
                    query_vector=frame_vector,
                    limit=limit
                )
                
                # 为每个结果添加帧索引信息
                for result in results:
                    result["frame_index"] = i
                    result["frame_vector"] = frame_vector
                all_results.extend(results)
            
            # 按相似度排序并限制数量
            all_results.sort(key=lambda x: x["score"], reverse=True)
            all_results = all_results[:limit]
            
            # 获取详细文件信息
            detailed_results = []
            for result in all_results:
                detailed_results.append({
                    "id": result["id"],
                    "score": result["score"],
                    "file_path": result["payload"].get("file_path", ""),
                    "file_type": result["payload"].get("segment_type", "unknown"),
                    "start_time_ms": result["payload"].get("start_time_ms", 0),
                    "end_time_ms": result["payload"].get("end_time_ms", 0),
                    "frame_index": result.get("frame_index", 0),
                    "metadata": result["payload"]
                })
            
            return {
                "success": True,
                "message": "视频检索完成",
                "data": {
                    "query_video": file.filename,
                    "results": detailed_results,
                    "total": len(detailed_results)
                }
            }
        finally:
            # 清理临时文件
            os.unlink(tmp_file_path)
    except Exception as e:
        logger.error(f"视频检索失败: {e}")
        raise HTTPException(500, f"视频检索失败: {str(e)}")

# 多模态检索端点
@app.post("/api/v1/search/multimodal", summary="多模态检索")
async def search_multimodal(
    query_text: str = None,
    image_file: UploadFile = File(None),
    audio_file: UploadFile = File(None),
    video_file: UploadFile = File(None),
    limit: int = 20
):
    """
    多模态检索API - 支持文本、图像、音频、视频混合查询
    
    参数:
    - query_text: 查询文本
    - image_file: 图像文件
    - audio_file: 音频文件
    - video_file: 视频文件
    - limit: 返回结果数量限制
    """
    try:
        import tempfile
        import os
        from src.models.model_manager import get_model_manager
        from src.models.vector_store import get_vector_store
        from src.core.db_adapter import get_db_adapter
        
        # 获取模型管理器、向量存储和数据库适配器实例
        model_manager = get_model_manager()
        vector_store = get_vector_store()
        db_adapter = get_db_adapter()
        
        # 检查模型状态
        model_status = model_manager.get_model_status()
        if not model_status["infinity_available"]:
            raise HTTPException(503, "Infinity服务不可用，请检查服务状态")
        if not model_status["qdrant_available"]:
            raise HTTPException(503, "Qdrant向量数据库不可用，请检查服务状态")
        
        # 收集所有查询向量
        all_results = []
        
        # 文本查询处理
        if query_text:
            logger.info(f"处理文本查询: {query_text}")
            text_vectors = await model_manager.embed_text_for_search(query_text)
            
            # 搜索CLIP向量（图像/视频）
            if "clip_vector" in text_vectors:
                clip_results = await vector_store.search(
                    collection_name="msearch_clip_v1",
                    query_vector=text_vectors["clip_vector"],
                    limit=limit
                )
                all_results.extend(clip_results)
            
            # 搜索CLAP向量（音频）
            if "clap_vector" in text_vectors:
                clap_results = await vector_store.search(
                    collection_name="msearch_clap_v1",
                    query_vector=text_vectors["clap_vector"],
                    limit=limit
                )
                all_results.extend(clap_results)
        
        # 图像查询处理
        if image_file:
            logger.info(f"处理图像查询: {image_file.filename}")
            
            # 保存上传的文件到临时位置
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                tmp_file.write(await image_file.read())
                tmp_file_path = tmp_file.name
            
            try:
                # 图像向量化
                image_vector = await model_manager.embed_image(tmp_file_path)
                
                # 在CLIP向量数据库中搜索（图像/视频）
                image_results = await vector_store.search(
                    collection_name="msearch_clip_v1",
                    query_vector=image_vector,
                    limit=limit
                )
                all_results.extend(image_results)
            finally:
                # 清理临时文件
                os.unlink(tmp_file_path)
        
        # 音频查询处理
        if audio_file:
            logger.info(f"处理音频查询: {audio_file.filename}")
            
            # 保存上传的文件到临时位置
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                tmp_file.write(await audio_file.read())
                tmp_file_path = tmp_file.name
            
            try:
                # 音频处理和向量化
                audio_results = await model_manager.process_video_audio_intelligently(tmp_file_path)
                
                # 合并所有音频片段的向量进行搜索
                for audio_result in audio_results:
                    if audio_result['segment_type'] == 'audio_music':
                        # 音乐片段使用CLAP向量数据库搜索
                        results = await vector_store.search(
                            collection_name="msearch_clap_v1",
                            query_vector=audio_result['vector'],
                            limit=limit
                        )
                        all_results.extend(results)
                    elif audio_result['segment_type'] == 'audio_speech':
                        # 语音片段使用CLIP向量数据库搜索（通过转录文本）
                        results = await vector_store.search(
                            collection_name="msearch_clip_v1",
                            query_vector=audio_result['vector'],
                            limit=limit
                        )
                        all_results.extend(results)
            finally:
                # 清理临时文件
                os.unlink(tmp_file_path)
        
        # 视频查询处理
        if video_file:
            logger.info(f"处理视频查询: {video_file.filename}")
            
            # 保存上传的文件到临时位置
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                tmp_file.write(await video_file.read())
                tmp_file_path = tmp_file.name
            
            try:
                # 视频帧向量化
                frame_vectors = await model_manager.embed_video_frames(tmp_file_path)
                
                # 合并所有视频帧的向量进行搜索
                for frame_vector in frame_vectors:
                    # 在CLIP向量数据库中搜索（图像/视频）
                    results = await vector_store.search(
                        collection_name="msearch_clip_v1",
                        query_vector=frame_vector,
                        limit=limit
                    )
                    all_results.extend(results)
            finally:
                # 清理临时文件
                os.unlink(tmp_file_path)
        
        # 按相似度排序并限制数量
        all_results.sort(key=lambda x: x["score"], reverse=True)
        all_results = all_results[:limit]
        
        # 多模态结果融合
        fused_results = await model_manager.fuse_multimodal_results(all_results)
        fused_results = fused_results[:limit]
        
        # 获取详细文件信息
        detailed_results = []
        for result in fused_results:
            # 从数据库获取详细信息
            file_metadata = await db_adapter.get_file_metadata(result["payload"].get("file_id"))
            if file_metadata:
                detailed_result = {
                    "id": result["id"],
                    "score": result["score"],
                    "fused_score": result.get("fused_score", result["score"]),
                    "modality_scores": result.get("modality_scores", {}),
                    "file_path": file_metadata.get("file_path", ""),
                    "file_type": file_metadata.get("file_type", "unknown"),
                    "start_time_ms": result["payload"].get("start_time_ms", 0),
                    "end_time_ms": result["payload"].get("end_time_ms", 0),
                    "metadata": {
                        **file_metadata,
                        "vector_metadata": result["payload"]
                    }
                }
                detailed_results.append(detailed_result)
        
        return {
            "success": True,
            "message": "多模态检索完成",
            "data": {
                "query_text": query_text,
                "query_image": image_file.filename if image_file else None,
                "query_audio": audio_file.filename if audio_file else None,
                "query_video": video_file.filename if video_file else None,
                "results": detailed_results,
                "total": len(detailed_results)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"多模态检索失败: {e}")
        raise HTTPException(500, f"多模态检索失败: {str(e)}")

# 时间线搜索端点
@app.post("/api/v1/search/timeline", summary="时间线搜索")
async def search_timeline(
    query: str = None,
    time_range: Dict[str, str] = None,
    file_types: List[str] = None,
    limit: int = 20
):
    """
    时间线搜索API - 按时间范围搜索媒体文件
    
    参数:
    - query: 查询文本
    - time_range: 时间范围 {"start": "2024-01-01T00:00:00Z", "end": "2024-01-31T23:59:59Z"}
    - file_types: 文件类型列表 ["video", "audio", "image"]
    - limit: 返回结果数量限制
    """
    try:
        from src.models.model_manager import get_model_manager
        from src.models.vector_store import get_vector_store
        from src.core.db_adapter import get_db_adapter
        from datetime import datetime
        
        # 获取模型管理器、向量存储和数据库适配器实例
        model_manager = get_model_manager()
        vector_store = get_vector_store()
        db_adapter = get_db_adapter()
        
        # 构建数据库查询条件
        conditions = []
        params = []
        
        # 时间范围过滤
        if time_range:
            start_time = time_range.get("start")
            end_time = time_range.get("end")
            
            if start_time:
                conditions.append("created_at >= ?")
                params.append(start_time)
            
            if end_time:
                conditions.append("created_at <= ?")
                params.append(end_time)
        
        # 文件类型过滤
        if file_types:
            type_conditions = []
            for file_type in file_types:
                type_conditions.append("file_type = ?")
                params.append(file_type)
            
            if type_conditions:
                conditions.append(f"({' OR '.join(type_conditions)})")
        
        # 查询数据库获取符合条件的文件
        query_sql = "SELECT * FROM files"
        if conditions:
            query_sql += " WHERE " + " AND ".join(conditions)
        
        query_sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        files = db_adapter.db_manager.execute_query(query_sql, tuple(params))
        
        # 如果有查询文本，进行向量搜索
        all_results = []
        if query and files:
            # 文本向量化
            text_vectors = await model_manager.embed_text_for_search(query)
            
            # 收集文件ID用于过滤搜索结果
            file_ids = [str(file["id"]) for file in files]
            
            # 在不同模态的向量数据库中搜索
            # 搜索CLIP向量（图像/视频）
            if "clip_vector" in text_vectors:
                clip_results = await vector_store.search(
                    collection_name="msearch_clip_v1",
                    query_vector=text_vectors["clip_vector"],
                    limit=limit * 2  # 获取更多结果用于过滤
                )
                
                # 过滤结果，只保留符合条件的文件
                for result in clip_results:
                    if str(result["payload"].get("file_id", "")) in file_ids:
                        all_results.append(result)
            
            # 搜索CLAP向量（音频）
            if "clap_vector" in text_vectors:
                clap_results = await vector_store.search(
                    collection_name="msearch_clap_v1",
                    query_vector=text_vectors["clap_vector"],
                    limit=limit * 2  # 获取更多结果用于过滤
                )
                
                # 过滤结果，只保留符合条件的文件
                for result in clap_results:
                    if str(result["payload"].get("file_id", "")) in file_ids:
                        all_results.append(result)
        
        # 如果没有查询文本，直接使用时间过滤的结果
        if not query:
            # 为每个文件创建虚拟搜索结果
            for file in files:
                all_results.append({
                    "id": f"file_{file['id']}",
                    "score": 1.0,
                    "payload": {
                        "file_id": file["id"],
                        "file_path": file["file_path"],
                        "file_type": file["file_type"],
                        "created_at": file["created_at"]
                    }
                })
        
        # 按相似度排序并限制数量
        all_results.sort(key=lambda x: x["score"], reverse=True)
        all_results = all_results[:limit]
        
        # 获取详细文件信息
        detailed_results = []
        for result in all_results:
            # 从数据库获取详细信息
            file_metadata = await db_adapter.get_file_metadata(result["payload"].get("file_id"))
            if file_metadata:
                detailed_results.append({
                    "id": result["id"],
                    "score": result["score"],
                    "file_path": file_metadata.get("file_path", ""),
                    "file_type": file_metadata.get("file_type", "unknown"),
                    "created_at": file_metadata.get("created_at", ""),
                    "start_time_ms": result["payload"].get("start_time_ms", 0),
                    "end_time_ms": result["payload"].get("end_time_ms", 0),
                    "metadata": {
                        **file_metadata,
                        "vector_metadata": result["payload"]
                    }
                })
        
        return {
            "success": True,
            "message": "时间线搜索完成",
            "data": {
                "query": query,
                "time_range": time_range,
                "file_types": file_types,
                "results": detailed_results,
                "total": len(detailed_results)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"时间线搜索失败: {e}")
        raise HTTPException(500, f"时间线搜索失败: {str(e)}")

# 人脸识别API
@app.post("/api/v1/face/persons", summary="添加人物到人脸库")
async def add_person_to_face_database(
    name: str,
    image_files: List[UploadFile] = File(...),
    aliases: str = None,
    description: str = None
):
    """
    添加人物到人脸库API
    
    参数:
    - name: 人物姓名
    - image_files: 人物照片文件列表
    - aliases: 人物别名（JSON数组字符串）
    - description: 人物描述
    """
    try:
        from src.models.face_database import get_face_database
        import tempfile
        import os
        
        face_db = get_face_database()
        
        # 保存上传的文件到临时位置
        image_paths = []
        temp_files = []
        
        try:
            for image_file in image_files:
                # 创建临时文件
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(image_file.filename)[1]) as tmp_file:
                    tmp_file.write(await image_file.read())
                    temp_files.append(tmp_file.name)
                    image_paths.append(tmp_file.name)
            
            # 解析别名
            alias_list = None
            if aliases:
                import json
                alias_list = json.loads(aliases)
            
            # 添加人物到人脸库
            person_id = face_db.add_person(name, image_paths, alias_list, description)
            
            return {
                "success": True,
                "message": f"人物 {name} 添加成功",
                "data": {"person_id": person_id}
            }
        finally:
            # 清理临时文件
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
    except Exception as e:
        logger.error(f"添加人物到人脸库失败: {e}")
        raise HTTPException(500, f"添加人物到人脸库失败: {str(e)}")

@app.get("/api/v1/face/persons", summary="获取所有人名列表")
async def get_all_person_names():
    """
    获取所有人名列表API
    """
    try:
        from src.models.face_database import get_face_database
        import sqlite3
        
        face_db = get_face_database()
        
        # 获取所有人名
        with sqlite3.connect(face_db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, aliases, description FROM persons")
            persons = []
            for row in cursor.fetchall():
                persons.append({
                    "id": row[0],
                    "name": row[1],
                    "aliases": row[2] and json.loads(row[2]) or [],
                    "description": row[3]
                })
        
        return {
            "success": True,
            "message": "获取人名列表成功",
            "data": persons
        }
    except Exception as e:
        logger.error(f"获取人名列表失败: {e}")
        raise HTTPException(500, f"获取人名列表失败: {str(e)}")

@app.post("/api/v1/face/search", summary="人脸搜索")
async def search_faces(image_file: UploadFile = File(...), limit: int = 10):
    """
    人脸搜索API
    
    参数:
    - image_file: 人脸图片文件
    - limit: 返回结果数量限制
    """
    try:
        from src.models.face_database import get_face_database
        from src.models.face_model_manager import get_face_model_manager
        import tempfile
        import os
        import numpy as np
        
        face_db = get_face_database()
        face_model_manager = get_face_model_manager()
        
        # 保存上传的文件到临时位置
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(image_file.filename)[1]) as tmp_file:
            tmp_file.write(await image_file.read())
            tmp_file_path = tmp_file.name
        
        try:
            # 检测并提取人脸特征
            face_features = face_model_manager.detect_and_extract_faces(tmp_file_path)
            
            if not face_features:
                raise HTTPException(400, "未在图片中检测到人脸")
            
            # 使用第一个人脸进行搜索
            main_face = face_features[0]
            query_vector = np.array(main_face['features'], dtype=np.float32)
            
            # 搜索相似人脸
            matches = face_db.search_similar_faces(query_vector, limit)
            
            return {
                "success": True,
                "message": "人脸搜索完成",
                "data": {
                    "query_image": image_file.filename,
                    "matches": matches
                }
            }
        finally:
            # 清理临时文件
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"人脸搜索失败: {e}")
        raise HTTPException(500, f"人脸搜索失败: {str(e)}")

if __name__ == "__main__":
    # 加载配置
    config = load_config()
    
    # 设置日志
    setup_logging(config)
    
    # 启动服务
    uvicorn.run(
        "src.api.main:app",
        host=config['fastapi']['host'],
        port=config['fastapi']['port'],
        reload=True,
        log_level="info"
    )