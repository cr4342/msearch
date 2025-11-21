"""
人脸管理器 - 处理人脸相关的特征提取、索引和检索功能
"""
import numpy as np
from typing import Dict, Any, List, Optional
import logging
import uuid

logger = logging.getLogger(__name__)


class FaceManager:
    """人脸管理器"""
    
    def __init__(self, config: Dict[str, Any], face_database, embedding_engine):
        """
        初始化人脸管理器
        
        Args:
            config: 配置字典
            face_database: 人脸数据库实例
            embedding_engine: 嵌入引擎实例
        """
        self.config = config
        self.face_database = face_database
        self.embedding_engine = embedding_engine
        self.similarity_threshold = config.get('face.similarity_threshold', 0.7)
    
    async def register_face(self, image_path: str, person_name: str, 
                           aliases: List[str] = None) -> Dict[str, Any]:
        """
        注册新人脸
        
        Args:
            image_path: 人脸图片路径
            person_name: 人物姓名
            aliases: 别名列表
            
        Returns:
            注册结果
        """
        try:
            logger.info(f"注册新人脸: 姓名={person_name}, 图片={image_path}")
            
            # 1. 提取人脸特征向量
            face_vector = await self._extract_face_features(image_path)
            if face_vector is None:
                return {
                    'status': 'error',
                    'error': '无法提取人脸特征',
                    'person_name': person_name
                }
            
            # 2. 在人脸数据库中注册
            person_id = await self.face_database.add_person(
                name=person_name,
                aliases=aliases or []
            )
            
            # 3. 存储人脸特征向量
            vector_id = f"face_person_{person_id}_img_{uuid.uuid4().hex[:8]}"
            await self.face_database.store_face_vector(
                vector_id=vector_id,
                person_id=person_id,
                image_path=image_path,
                face_vector=face_vector
            )
            
            logger.info(f"人脸注册成功: 姓名={person_name}, 人物ID={person_id}")
            
            return {
                'status': 'success',
                'person_id': person_id,
                'person_name': person_name,
                'vector_id': vector_id
            }
            
        except Exception as e:
            logger.error(f"人脸注册失败: 姓名={person_name}, 错误={e}")
            return {
                'status': 'error',
                'error': str(e),
                'person_name': person_name
            }
    
    async def recognize_face(self, image_path: str) -> Dict[str, Any]:
        """
        识别人脸
        
        Args:
            image_path: 待识别人脸图片路径
            
        Returns:
            识别结果
        """
        try:
            logger.info(f"识别人脸: 图片={image_path}")
            
            # 1. 提取人脸特征向量
            face_vector = await self._extract_face_features(image_path)
            if face_vector is None:
                return {
                    'status': 'error',
                    'error': '无法提取人脸特征',
                    'image_path': image_path
                }
            
            # 2. 在人脸数据库中搜索相似人脸
            matches = await self.face_database.search_similar_faces(
                face_vector, 
                top_k=5,
                threshold=self.similarity_threshold
            )
            
            # 3. 返回最佳匹配
            if matches:
                best_match = matches[0]
                logger.info(f"人脸识别成功: 匹配到 {best_match['person_name']}, "
                           f"置信度={best_match['confidence']:.3f}")
                
                return {
                    'status': 'success',
                    'match': best_match,
                    'all_matches': matches,
                    'image_path': image_path
                }
            else:
                logger.info("人脸识别完成: 未找到匹配的人脸")
                return {
                    'status': 'success',
                    'match': None,
                    'all_matches': [],
                    'image_path': image_path
                }
            
        except Exception as e:
            logger.error(f"人脸识别失败: 图片={image_path}, 错误={e}")
            return {
                'status': 'error',
                'error': str(e),
                'image_path': image_path
            }
    
    async def search_by_person_name(self, person_name: str) -> Dict[str, Any]:
        """
        根据人名搜索相关文件
        
        Args:
            person_name: 人物姓名
            
        Returns:
            搜索结果
        """
        try:
            logger.info(f"按人名搜索: 姓名={person_name}")
            
            # 1. 解析人名(包括别名)
            person_info = await self.face_database.get_person_by_name(person_name)
            if not person_info:
                logger.info(f"未找到人物: 姓名={person_name}")
                return {
                    'status': 'success',
                    'person_info': None,
                    'files': []
                }
            
            # 2. 搜索与该人物相关的文件
            files = await self.face_database.get_files_by_person(person_info['id'])
            
            logger.info(f"人名搜索完成: 找到{len(files)}个相关文件")
            
            return {
                'status': 'success',
                'person_info': person_info,
                'files': files
            }
            
        except Exception as e:
            logger.error(f"人名搜索失败: 姓名={person_name}, 错误={e}")
            return {
                'status': 'error',
                'error': str(e),
                'person_name': person_name
            }
    
    async def _extract_face_features(self, image_path: str) -> Optional[np.ndarray]:
        """
        提取人脸特征向量
        
        Args:
            image_path: 图片路径
            
        Returns:
            人脸特征向量或None
        """
        try:
            # 这里应该使用专门的人脸检测和特征提取模型(如FaceNet、MTCNN等)
            # 暂时使用嵌入引擎的CLIP模型作为占位符
            
            # 模拟人脸检测和裁剪
            # 实际实现中应该先检测人脸位置，然后裁剪人脸区域
            
            # 使用嵌入引擎提取特征(模拟)
            # 注意：这应该使用专门的人脸识别模型，而不是CLIP
            face_vector = await self.embedding_engine.embed_image(image_path)
            
            return face_vector
            
        except Exception as e:
            logger.error(f"提取人脸特征失败: 图片={image_path}, 错误={e}")
            return None
    
    async def update_person_aliases(self, person_name: str, 
                                   aliases: List[str]) -> Dict[str, Any]:
        """
        更新人物别名
        
        Args:
            person_name: 人物姓名
            aliases: 新的别名列表
            
        Returns:
            更新结果
        """
        try:
            logger.info(f"更新人物别名: 姓名={person_name}, 别名={aliases}")
            
            # 获取人物信息
            person_info = await self.face_database.get_person_by_name(person_name)
            if not person_info:
                return {
                    'status': 'error',
                    'error': f'未找到人物: {person_name}',
                    'person_name': person_name
                }
            
            # 更新别名
            await self.face_database.update_person_aliases(
                person_id=person_info['id'],
                aliases=aliases
            )
            
            logger.info(f"人物别名更新成功: 姓名={person_name}")
            
            return {
                'status': 'success',
                'person_name': person_name,
                'aliases': aliases
            }
            
        except Exception as e:
            logger.error(f"更新人物别名失败: 姓名={person_name}, 错误={e}")
            return {
                'status': 'error',
                'error': str(e),
                'person_name': person_name
            }


# 示例使用
if __name__ == "__main__":
    import asyncio
    
    # 配置示例
    config = {
        'face.similarity_threshold': 0.7
    }
    
    # 创建人脸管理器实例(需要实际的数据库和嵌入引擎实例)
    # manager = FaceManager(config, face_database, embedding_engine)
    
    # 注册人脸(需要实际的图片文件)
    # result = asyncio.run(manager.register_face("path/to/face.jpg", "张三"))
    # print(result)
    
    # 识别人脸(需要实际的图片文件)
    # result = asyncio.run(manager.recognize_face("path/to/unknown_face.jpg"))
    # print(result)