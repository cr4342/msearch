"""
人脸聚类管理器 - 实现人脸聚类功能
"""
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
import logging
from sklearn.cluster import DBSCAN, KMeans
from sklearn.metrics.pairwise import cosine_distances
import uuid
import os

logger = logging.getLogger(__name__)


class FaceClusterManager:
    """人脸聚类管理器"""
    
    def __init__(self, config: Dict[str, Any], face_database=None, embedding_engine=None):
        """
        初始化人脸聚类管理器
        
        Args:
            config: 配置字典
            face_database: 人脸数据库实例
            embedding_engine: 嵌入引擎实例
        """
        self.config = config
        self.face_database = face_database
        self.embedding_engine = embedding_engine
        
        # 聚类配置
        clustering_config = config.get('face_clustering', {})
        self.method = clustering_config.get('method', 'dbscan')  # 'dbscan' 或 'kmeans'
        self.threshold = clustering_config.get('similarity_threshold', 0.7)
        self.min_samples = clustering_config.get('min_samples', 2)
        self.epsilon = clustering_config.get('eps', 0.3)
        
        logger.info(f"人脸聚类管理器初始化完成: 方法={self.method}, 阈值={self.threshold}")
    
    async def cluster_faces(self, face_images: List[str], 
                           auto_assign_names: bool = True) -> Dict[str, Any]:
        """
        对人脸进行聚类
        
        Args:
            face_images: 人脸图片路径列表
            auto_assign_names: 是否自动分配名称
            
        Returns:
            聚类结果
        """
        try:
            logger.info(f"开始人脸聚类: 图片数量={len(face_images)}")
            
            # 1. 提取所有人脸特征向量
            face_vectors = []
            valid_images = []
            
            for image_path in face_images:
                vector = await self._extract_face_features(image_path)
                if vector is not None and len(vector) > 0:
                    face_vectors.append(vector)
                    valid_images.append(image_path)
                else:
                    logger.warning(f"无法提取人脸特征: {image_path}")
            
            if len(face_vectors) < 2:
                logger.warning("人脸数量不足，无法进行聚类")
                return {
                    'status': 'success',
                    'clusters': [],
                    'unclustered': valid_images,
                    'total_faces': len(valid_images)
                }
            
            # 2. 执行聚类
            clusters = await self._perform_clustering(face_vectors, valid_images)
            
            # 3. 保存聚类结果到数据库
            if auto_assign_names:
                await self._save_cluster_results(clusters)
            
            logger.info(f"人脸聚类完成: 共{len(clusters)}个聚类")
            return {
                'status': 'success',
                'clusters': clusters,
                'total_faces': len(valid_images),
                'clustered_faces': sum(len(cluster['faces']) for cluster in clusters),
                'unclustered': [img for img in valid_images 
                               if not any(img in [f['image_path'] for f in cluster['faces']] 
                                        for cluster in clusters)]
            }
            
        except Exception as e:
            logger.error(f"人脸聚类失败: {e}", exc_info=True)
            return {
                'status': 'error',
                'error': str(e)
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
            if self.embedding_engine is None:
                logger.error("嵌入引擎未初始化")
                return None
            
            # 使用嵌入引擎提取特征
            # 注意：实际应用中应该使用专门的人脸识别模型(如FaceNet)
            face_vector = await self.embedding_engine.embed_image(image_path)
            
            # 标准化向量
            if face_vector is not None and len(face_vector) > 0:
                # L2归一化
                norm = np.linalg.norm(face_vector)
                if norm > 0:
                    face_vector = face_vector / norm
            
            return face_vector
            
        except Exception as e:
            logger.error(f"提取人脸特征失败: 图片={image_path}, 错误={e}")
            return None
    
    async def _perform_clustering(self, face_vectors: List[np.ndarray], 
                                 face_images: List[str]) -> List[Dict[str, Any]]:
        """
        执行人脸聚类
        
        Args:
            face_vectors: 人脸特征向量列表
            face_images: 对应的图片路径列表
            
        Returns:
            聚类结果
        """
        try:
            if self.method == 'dbscan':
                return await self._dbscan_clustering(face_vectors, face_images)
            elif self.method == 'kmeans':
                return await self._kmeans_clustering(face_vectors, face_images)
            else:
                raise ValueError(f"不支持的聚类方法: {self.method}")
                
        except Exception as e:
            logger.error(f"执行聚类失败: {e}")
            # 使用默认方法返回单个聚类
            return [{'cluster_id': f'cluster_{uuid.uuid4().hex[:8]}', 
                    'cluster_name': f'Cluster_{uuid.uuid4().hex[:8]}',
                    'faces': [{'image_path': img, 'vector': vec, 'similarity': 1.0} 
                             for img, vec in zip(face_images, face_vectors)]}]
    
    async def _dbscan_clustering(self, face_vectors: List[np.ndarray], 
                                face_images: List[str]) -> List[Dict[str, Any]]:
        """
        使用DBSCAN算法进行人脸聚类
        
        Args:
            face_vectors: 人脸特征向量列表
            face_images: 对应的图片路径列表
            
        Returns:
            聚类结果
        """
        try:
            # 将向量转换为numpy数组
            X = np.array(face_vectors)
            
            # 计算距离矩阵(余弦距离)
            # DBSCAN需要距离矩阵
            distance_matrix = cosine_distances(X)
            
            # 执行DBSCAN聚类
            dbscan = DBSCAN(
                eps=self.epsilon, 
                min_samples=self.min_samples, 
                metric='precomputed'
            )
            
            cluster_labels = dbscan.fit_predict(distance_matrix)
            
            # 组织聚类结果
            clusters = {}
            for idx, (label, image_path, vector) in enumerate(zip(cluster_labels, face_images, face_vectors)):
                if label == -1:  # 噪声点
                    cluster_id = f'noise_{uuid.uuid4().hex[:8]}'
                    cluster_name = f'Noise_{uuid.uuid4().hex[:8]}'
                else:
                    cluster_id = f'cluster_{label}'
                    cluster_name = f'Cluster_{label}'
                
                if cluster_id not in clusters:
                    clusters[cluster_id] = {
                        'cluster_id': cluster_id,
                        'cluster_name': cluster_name,
                        'faces': [],
                        'size': 0
                    }
                
                # 计算与聚类中心的相似度(简化计算)
                cluster_faces = clusters[cluster_id]['faces']
                if len(cluster_faces) == 0:
                    similarity = 1.0  # 第一个点的相似度为1
                else:
                    # 计算与第一个点的相似度(作为代表)
                    similarity = 1 - distance_matrix[idx][cluster_faces[0]['index']]
                
                clusters[cluster_id]['faces'].append({
                    'image_path': image_path,
                    'vector': vector,
                    'similarity': similarity,
                    'index': idx  # 用于后续距离计算
                })
                clusters[cluster_id]['size'] += 1
            
            # 转换为列表并过滤噪声聚类(如果需要)
            cluster_list = list(clusters.values())
            
            # 过滤掉太小的聚类(可选)
            filtered_clusters = [cluster for cluster in cluster_list if cluster['size'] >= self.min_samples]
            
            logger.info(f"DBSCAN聚类完成: 生成{len(cluster_list)}个聚类, "
                       f"过滤后剩余{len(filtered_clusters)}个聚类")
            
            return filtered_clusters
            
        except Exception as e:
            logger.error(f"DBSCAN聚类失败: {e}", exc_info=True)
            return []
    
    async def _kmeans_clustering(self, face_vectors: List[np.ndarray], 
                                face_images: List[str]) -> List[Dict[str, Any]]:
        """
        使用KMeans算法进行人脸聚类
        
        Args:
            face_vectors: 人脸特征向量列表
            face_images: 对应的图片路径列表
            
        Returns:
            聚类结果
        """
        try:
            # 将向量转换为numpy数组
            X = np.array(face_vectors)
            
            # 确定聚类数量(使用肘部法则的简化版本)
            n_samples = len(face_vectors)
            max_clusters = min(self.min_samples * 2, max(2, n_samples // 2))
            
            if n_samples <= 2:
                n_clusters = 1
            elif n_samples < max_clusters:
                # 根据样本数量估算聚类数
                n_clusters = min(max(2, n_samples // max(1, self.min_samples)), max_clusters)  
            else:
                n_clusters = max_clusters
            
            if n_clusters > n_samples:
                n_clusters = max(1, n_samples)
            
            # 执行KMeans聚类
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(X)
            
            # 组织聚类结果
            clusters = {}
            for idx, (label, image_path, vector) in enumerate(zip(cluster_labels, face_images, face_vectors)):
                cluster_id = f'cluster_{label}'
                cluster_name = f'Cluster_{label}'
                
                if cluster_id not in clusters:
                    clusters[cluster_id] = {
                        'cluster_id': cluster_id,
                        'cluster_name': cluster_name,
                        'faces': [],
                        'size': 0,
                        'centroid': kmeans.cluster_centers_[label]  # 聚类中心
                    }
                
                # 计算与聚类中心的相似度
                centroid = kmeans.cluster_centers_[label]
                similarity = 1 - cosine_distances([vector], [centroid])[0][0]
                
                clusters[cluster_id]['faces'].append({
                    'image_path': image_path,
                    'vector': vector,
                    'similarity': similarity
                })
                clusters[cluster_id]['size'] += 1
            
            logger.info(f"KMeans聚类完成: 生成{len(clusters)}个聚类")
            
            return list(clusters.values())
            
        except Exception as e:
            logger.error(f"KMeans聚类失败: {e}", exc_info=True)
            return []
    
    async def _save_cluster_results(self, clusters: List[Dict[str, Any]]) -> bool:
        """
        保存聚类结果到数据库
        
        Args:
            clusters: 聚类结果列表
            
        Returns:
            保存是否成功
        """
        try:
            logger.info(f"保存聚类结果到数据库: 聚类数量={len(clusters)}")
            
            if self.face_database is None:
                logger.warning("人脸数据库未初始化，跳过保存聚类结果")
                return False
            
            for cluster in clusters:
                if len(cluster['faces']) >= self.min_samples:
                    # 为聚类生成一个名称(使用聚类ID)
                    cluster_name = cluster.get('cluster_name', f"Cluster_{cluster['cluster_id']}")
                    
                    # 获取聚类中的所有人脸向量以生成平均特征
                    face_vectors = [face['vector'] for face in cluster['faces']]
                    if face_vectors:
                        avg_vector = np.mean(face_vectors, axis=0)
                        
                        # 在数据库中创建一个代表这个聚类的人物
                        person_id = await self.face_database.add_person(
                            name=cluster_name,
                            aliases=[],
                            is_cluster=True  # 标记为聚类
                        )
                        
                        # 为聚类中的每个脸添加关联
                        for face in cluster['faces']:
                            vector_id = f"cluster_face_{uuid.uuid4().hex[:8]}"
                            await self.face_database.store_face_vector(
                                vector_id=vector_id,
                                person_id=person_id,
                                image_path=face['image_path'],
                                face_vector=face['vector']
                            )
            
            logger.info("聚类结果保存完成")
            return True
            
        except Exception as e:
            logger.error(f"保存聚类结果失败: {e}", exc_info=True)
            return False
    
    async def suggest_cluster_names(self, cluster_id: str, 
                                   name_suggestions: List[str]) -> Dict[str, Any]:
        """
        为聚类建议名称
        
        Args:
            cluster_id: 聚类ID
            name_suggestions: 名称建议列表
            
        Returns:
            建议结果
        """
        try:
            logger.info(f"为聚类建议名称: 聚类ID={cluster_id}")
            
            if self.face_database is None:
                logger.warning("人脸数据库未初始化，无法更新聚类名称")
                return {
                    'status': 'error',
                    'error': '人脸数据库未初始化'
                }
            
            # 从数据库查找聚类信息
            persons = await self.face_database.get_all_persons()
            target_person = None
            for person in persons:
                if person.get('id') == cluster_id or person.get('name') == cluster_id:
                    target_person = person
                    break
            
            if target_person is None:
                return {
                    'status': 'error',
                    'error': f'未找到聚类: {cluster_id}'
                }
            
            # 更新聚类名称
            new_name = name_suggestions[0] if name_suggestions else target_person['name']
            await self.face_database.update_person_name(target_person['id'], new_name)
            
            # 如果有别名，也可以添加
            if len(name_suggestions) > 1:
                all_aliases = target_person.get('aliases', [])
                all_aliases.extend(name_suggestions[1:])
                await self.face_database.update_person_aliases(target_person['id'], all_aliases)
            
            return {
                'status': 'success',
                'cluster_id': cluster_id,
                'suggested_names': name_suggestions,
                'new_name': new_name
            }
            
        except Exception as e:
            logger.error(f"建议聚类名称失败: {e}", exc_info=True)
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def merge_clusters(self, cluster_ids: List[str], 
                            new_name: str) -> Dict[str, Any]:
        """
        合并多个聚类
        
        Args:
            cluster_ids: 要合并的聚类ID列表
            new_name: 新的聚类名称
            
        Returns:
            合并结果
        """
        try:
            logger.info(f"合并聚类: 聚类ID={cluster_ids}, 新名称={new_name}")
            
            if self.face_database is None:
                logger.warning("人脸数据库未初始化，无法合并聚类")
                return {
                    'status': 'error',
                    'error': '人脸数据库未初始化'
                }
            
            # 获取所有要合并的聚类信息
            all_faces = []
            for cluster_id in cluster_ids:
                # 获取聚类相关的人脸向量
                face_vectors = await self.face_database.get_face_vectors_by_person_id(cluster_id)
                all_faces.extend(face_vectors)
            
            if not all_faces:
                return {
                    'status': 'error',
                    'error': '没有找到要合并的人脸数据'
                }
            
            # 创建新的人物
            new_person_id = await self.face_database.add_person(
                name=new_name,
                aliases=[],
                is_cluster=True
            )
            
            # 将所有人脸向量关联到新的人物
            for face_data in all_faces:
                vector_id = f"merged_face_{uuid.uuid4().hex[:8]}"
                await self.face_database.store_face_vector(
                    vector_id=vector_id,
                    person_id=new_person_id,
                    image_path=face_data.get('image_path', ''),
                    face_vector=face_data.get('vector', np.array([]))
                )
            
            # 删除原始聚类
            for cluster_id in cluster_ids:
                await self.face_database.delete_person(cluster_id)
            
            return {
                'status': 'success',
                'merged_cluster_id': new_person_id,
                'original_clusters': cluster_ids,
                'new_name': new_name
            }
            
        except Exception as e:
            logger.error(f"合并聚类失败: {e}", exc_info=True)
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def split_cluster(self, cluster_id: str, 
                          face_ids_to_move: List[str],
                          new_cluster_name: str) -> Dict[str, Any]:
        """
        拆分聚类
        
        Args:
            cluster_id: 原聚类ID
            face_ids_to_move: 要移动到新聚类的人脸ID列表
            new_cluster_name: 新聚类名称
            
        Returns:
            拆分结果
        """
        try:
            logger.info(f"拆分聚类: 聚类ID={cluster_id}, "
                       f"移动人脸数={len(face_ids_to_move)}, "
                       f"新名称={new_cluster_name}")
            
            if self.face_database is None:
                logger.warning("人脸数据库未初始化，无法拆分聚类")
                return {
                    'status': 'error',
                    'error': '人脸数据库未初始化'
                }
            
            # 获取原始聚类的所有人脸
            original_faces = await self.face_database.get_face_vectors_by_person_id(cluster_id)
            
            # 分离要移动和保留的人脸
            faces_to_move = [f for f in original_faces if f.get('vector_id') in face_ids_to_move]
            faces_to_keep = [f for f in original_faces if f.get('vector_id') not in face_ids_to_move]
            
            if not faces_to_move:
                return {
                    'status': 'error',
                    'error': '没有找到要移动的人脸'
                }
            
            # 创建新聚类
            new_cluster_id = await self.face_database.add_person(
                name=new_cluster_name,
                aliases=[],
                is_cluster=True
            )
            
            # 移动人脸到新聚类
            for face_data in faces_to_move:
                new_vector_id = f"split_face_{uuid.uuid4().hex[:8]}"
                await self.face_database.store_face_vector(
                    vector_id=new_vector_id,
                    person_id=new_cluster_id,
                    image_path=face_data.get('image_path', ''),
                    face_vector=face_data.get('vector', np.array([]))
                )
            
            # 保留原始聚类中剩余的人脸
            # 重新创建原始聚类的剩余部分
            if len(faces_to_keep) == 0:
                # 如果所有脸都移动了，删除原始聚类
                await self.face_database.delete_person(cluster_id)
            else:
                # 更新原始聚类名称(如果需要)
                await self.face_database.update_person_name(cluster_id, f"Remaining_{cluster_id}")
            
            return {
                'status': 'success',
                'original_cluster_id': cluster_id,
                'new_cluster_id': new_cluster_id,
                'moved_faces': [f['vector_id'] for f in faces_to_move],
                'remaining_faces_count': len(faces_to_keep)
            }
            
        except Exception as e:
            logger.error(f"拆分聚类失败: {e}", exc_info=True)
            return {
                'status': 'error',
                'error': str(e)
            }


# 全局人脸聚类管理器实例
_face_cluster_manager = None


def get_face_cluster_manager(config: Dict[str, Any] = None) -> FaceClusterManager:
    """
    获取全局人脸聚类管理器实例
    
    Args:
        config: 配置字典，首次调用时需要提供
        
    Returns:
        人脸聚类管理器实例
    """
    global _face_cluster_manager
    if _face_cluster_manager is None:
        if config is None:
            raise ValueError("首次调用get_face_cluster_manager时必须提供config参数")
        _face_cluster_manager = FaceClusterManager(config)
    return _face_cluster_manager


def set_face_cluster_manager_instance(instance: FaceClusterManager):
    """
    设置全局人脸聚类管理器实例(用于注入依赖)
    
    Args:
        instance: 人脸聚类管理器实例
    """
    global _face_cluster_manager
    _face_cluster_manager = instance


# 示例使用
if __name__ == "__main__":
    import asyncio
    
    # 配置示例
    config = {
        'face_clustering': {
            'method': 'dbscan',
            'similarity_threshold': 0.7,
            'min_samples': 2,
            'eps': 0.3
        }
    }
    
    # 创建聚类管理器实例(需要实际的数据库和嵌入引擎实例)
    # manager = FaceClusterManager(config, face_database, embedding_engine)
    
    # 聚类人脸(需要实际的图片文件列表)
    # result = asyncio.run(manager.cluster_faces(["face1.jpg", "face2.jpg"]))
    # print(result)