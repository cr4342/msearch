"""
人脸识别API路由实现
提供人脸注册、识别和管理的REST API接口
"""

import json
import logging
import tempfile
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from ...common.storage.database_adapter import DatabaseAdapter
from ...search_service.face_manager import FaceManager, get_face_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/face", tags=["face"])


# 数据模型
class FaceRegisterRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="人名")
    description: Optional[str] = Field(default="", max_length=500, description="描述信息")
    tags: List[str] = Field(default=[], description="标签列表")


class FaceInfo(BaseModel):
    face_id: str
    name: str
    description: str
    tags: List[str]
    image_count: int
    created_at: str
    updated_at: str


class PersonRegistrationResponse(BaseModel):
    success: bool
    message: str
    data: Dict[str, Any]


@router.post("/face/register", response_model=PersonRegistrationResponse)
async def register_person(
    name: str = Form(...),
    description: Optional[str] = Form(""),
    aliases: Optional[str] = Form(None),
    image_files: Optional[List[UploadFile]] = File(None),
):
    """注册新人物。

    设计文档 3.1 节定义了人物注册接口：
    - 提供人物姓名、描述、别名和照片；
    - 自动提取人脸特征并存入数据库。
    """
    try:
        db = DatabaseAdapter()

        # 解析别名列表
        aliases_list: List[str] = []
        if aliases:
            try:
                parsed = json.loads(aliases)
                if isinstance(parsed, list):
                    aliases_list = [str(a) for a in parsed]
                else:
                    aliases_list = [str(aliases)]
            except json.JSONDecodeError:
                # 退化为单个字符串别名
                aliases_list = [aliases] if aliases else []

        # 组装人物数据并写入数据库
        person_data: Dict[str, Any] = {
            "name": name,
            "aliases": aliases_list,
            "description": description,
        }
        person_id = await db.insert_person(person_data)

        # 如果人脸识别可用，则为上传图片提取特征
        face_manager = get_face_manager()
        embedding_count = 0
        if face_manager and getattr(face_manager, "face_recognition_enabled", False):
            # 为每个上传文件创建临时图片并检测人脸
            for upload in image_files or []:
                # 将上传内容写入临时文件
                content = await upload.read()
                if not content:
                    continue

                with tempfile.NamedTemporaryFile(suffix=".jpg", delete=True) as tmp:
                    tmp.write(content)
                    tmp.flush()

                    faces_info = face_manager.detect_faces(tmp.name)
                    if not faces_info:
                        continue

                    # 只取第一张人脸的 embedding
                    embedding = faces_info[0].get("embedding")
                    if embedding is None:
                        continue

                    await db.insert_person_embedding(person_id, embedding)
                    embedding_count += 1

        uploaded_count = len(image_files) if image_files else 0
        logger.info(
            "人物注册成功: %s (ID: %s, 照片数: %d, 嵌入数: %d)",
            name,
            person_id,
            uploaded_count,
            embedding_count,
        )

        return {
            "success": True,
            "message": f"人物 {name} 添加成功",
            "data": {
                "person_id": person_id,
                "name": name,
                "aliases": aliases_list,
                "description": description,
                "image_file_count": uploaded_count,
                "embedding_count": embedding_count,
            },
        }
    except Exception as e:  # noqa: BLE001
        logger.error("添加人物失败: %s", e)
        raise HTTPException(status_code=500, detail=f"添加人物失败: {e}") from e


@router.get("/face/persons")
async def list_persons():
    """获取所有人名列表。

    与设计文档 3.2 节对齐，返回人物基础信息列表。
    """
    try:
        import sqlite3

        db = DatabaseAdapter()
        persons: List[Dict[str, Any]] = []

        with db.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, name, aliases, description FROM persons ORDER BY created_at DESC"
            )
            rows = cursor.fetchall()

            for row in rows:
                row_dict = dict(row)
                if row_dict.get("aliases"):
                    try:
                        row_dict["aliases"] = json.loads(row_dict["aliases"])
                    except json.JSONDecodeError:
                        row_dict["aliases"] = [row_dict["aliases"]]
                else:
                    row_dict["aliases"] = []
                persons.append(row_dict)

        return {
            "success": True,
            "message": "获取人名列表成功",
            "data": persons,
        }
    except Exception as e:  # noqa: BLE001
        logger.error("获取人名列表失败: %s", e)
        raise HTTPException(status_code=500, detail=f"获取人名列表失败: {e}") from e


@router.post("/face/search")
async def search_face(
    image_file: UploadFile = File(...),
    limit: int = Form(10),
):
    """人脸搜索。

    设计文档 3.3 节定义了基于上传图片的人脸搜索接口：
    - 上传单张人脸图片；
    - 返回匹配的人物及相似度。
    当前实现基于 person_embeddings 表中的特征向量做简单余弦相似度检索。
    """
    try:
        import tempfile

        # 检查人脸管理器是否可用
        face_manager = get_face_manager()
        if not face_manager or not getattr(face_manager, "face_recognition_enabled", False):
            return {
                "success": False,
                "message": "人脸识别功能不可用，请检查依赖是否安装",
                "error": "face_recognition_disabled",
            }

        # 读取上传图片并写入临时文件
        content = await image_file.read()
        if not content:
            raise HTTPException(status_code=400, detail="上传的人脸图片为空")

        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=True) as tmp:
            tmp.write(content)
            tmp.flush()

            faces_info = face_manager.detect_faces(tmp.name)

        if not faces_info:
            return {
                "success": False,
                "message": "未在图片中检测到人脸",
                "error": "no_face_detected",
            }

        # 只取第一张人脸作为查询
        query_embedding = faces_info[0].get("embedding")
        if query_embedding is None:
            return {
                "success": False,
                "message": "未能提取人脸特征",
                "error": "embedding_extraction_failed",
            }

        db = DatabaseAdapter()
        stored_embeddings = await db.get_all_person_embeddings()
        if not stored_embeddings:
            return {
                "success": False,
                "message": "人物库中暂无已注册的人脸特征",
                "error": "no_person_embeddings",
            }

        # 计算相似度
        matches = []
        for item in stored_embeddings:
            person_embedding = item["embedding"]
            similarity = face_manager._calculate_similarity(  # type: ignore[attr-defined]
                query_embedding, person_embedding
            )
            matches.append(
                {
                    "person_id": item["person_id"],
                    "person_name": item["name"],
                    "aliases": item["aliases"],
                    "similarity": float(similarity),
                    "confidence": float(similarity),
                }
            )

        # 按相似度排序并截断
        matches.sort(key=lambda m: m["similarity"], reverse=True)
        top_matches = matches[: max(1, min(limit, len(matches)))]

        return {
            "success": True,
            "message": "人脸搜索完成" if top_matches else "未找到匹配的人物",
            "data": {
                "query_image": image_file.filename,
                "matches": top_matches,
            },
        }
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        logger.error("人脸搜索请求处理失败: %s", e)
        raise HTTPException(status_code=500, detail=f"人脸搜索失败: {e}") from e