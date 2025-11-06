"""
人脸管理API路由
实现需求文档中关于人脸识别与聚类的功能
"""
from fastapi import APIRouter, HTTPException, File, UploadFile, Form
from typing import List, Dict, Any, Optional
import uuid
import logging
from pydantic import BaseModel

from src.business.face_manager import FaceManager
from src.core.config_manager import ConfigManager

logger = logging.getLogger(__name__)

router = APIRouter()
config_manager = ConfigManager()
# face_manager将在运行时初始化
face_manager = None

def init_face_manager(face_db, embedding_engine):
    """初始化人脸管理器"""
    global face_manager
    face_manager = FaceManager(config_manager.config, face_db, embedding_engine)

class PersonInfo(BaseModel):
    """人员信息模型"""
    name: str
    aliases: Optional[List[str]] = []
    description: Optional[str] = None


class FaceSearchRequest(BaseModel):
    """人脸搜索请求模型"""
    query: str
    top_k: int = 10
    threshold: float = 0.7


@router.post("/faces/persons")
async def add_person(
    name: str = Form(...),
    aliases: str = Form(None),
    description: str = Form(None),
    images: List[UploadFile] = File(...)
):
    """
    添加人脸到库
    实现需求2.1：用户上传人脸照片并设置人名，系统使用专业人脸识别模型创建高精度人脸特征库条目
    """
    try:
        # 解析别名
        aliases_list = []
        if aliases:
            aliases_list = [alias.strip() for alias in aliases.split(",") if alias.strip()]
        
        # 保存上传的图片并添加到人脸库
        image_paths = []
        for image in images:
            # 生成唯一文件名
            file_extension = image.filename.split(".")[-1]
            unique_filename = f"{str(uuid.uuid4())}.{file_extension}"
            image_path = f"/tmp/{unique_filename}"  # 实际应用中应使用配置的临时目录
            
            # 保存文件
            with open(image_path, "wb") as f:
                content = await image.read()
                f.write(content)
            
            image_paths.append(image_path)
        
        # 添加人员信息
        person_id = await face_manager.add_person(
            name=name,
            aliases=aliases_list,
            description=description,
            image_paths=image_paths
        )
        
        return {
            "success": True,
            "person_id": person_id,
            "message": f"成功添加人员: {name}"
        }
        
    except Exception as e:
        logger.error(f"添加人员失败: {e}")
        raise HTTPException(status_code=500, detail=f"添加人员失败: {str(e)}")


@router.get("/faces/persons")
async def get_persons():
    """获取所有人脸库信息"""
    try:
        persons = await face_manager.get_all_persons()
        return {
            "success": True,
            "persons": persons
        }
    except Exception as e:
        logger.error(f"获取人员列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取人员列表失败: {str(e)}")


@router.delete("/faces/persons/{person_id}")
async def delete_person(person_id: str):
    """删除人脸库中的人员"""
    try:
        await face_manager.delete_person(person_id)
        return {
            "success": True,
            "message": f"成功删除人员: {person_id}"
        }
    except Exception as e:
        logger.error(f"删除人员失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除人员失败: {str(e)}")


@router.post("/search/face")
async def search_by_face(request: FaceSearchRequest):
    """
    人脸搜索
    实现需求2.3：用户输入已预设的人名，系统自动调用对应人脸图片进行精确检索
    """
    try:
        results = await face_manager.search_faces(
            query=request.query,
            top_k=request.top_k,
            threshold=request.threshold
        )
        
        return {
            "success": True,
            "results": results,
            "query_type": "face_search"
        }
    except Exception as e:
        logger.error(f"人脸搜索失败: {e}")
        raise HTTPException(status_code=500, detail=f"人脸搜索失败: {str(e)}")


@router.get("/faces/status")
async def get_face_status():
    """获取人脸库状态"""
    try:
        status = await face_manager.get_status()
        return {
            "success": True,
            "status": status
        }
    except Exception as e:
        logger.error(f"获取人脸库状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取人脸库状态失败: {str(e)}")


@router.post("/faces/recognize")
async def recognize_faces_in_file(file: UploadFile = File(...)):
    """
    识别人脸文件中的所有人脸
    实现需求2.2：系统处理新的图片或视频，自动检测并匹配已知人脸
    """
    try:
        # 保存上传的文件
        file_extension = file.filename.split(".")[-1]
        unique_filename = f"{str(uuid.uuid4())}.{file_extension}"
        file_path = f"/tmp/{unique_filename}"  # 实际应用中应使用配置的临时目录
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # 识别人脸
        recognized_faces = await face_manager.recognize_faces_in_file(file_path)
        
        return {
            "success": True,
            "recognized_faces": recognized_faces
        }
        
    except Exception as e:
        logger.error(f"识别人脸失败: {e}")
        raise HTTPException(status_code=500, detail=f"识别人脸失败: {str(e)}")