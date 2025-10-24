"""
人脸数据库模块
负责管理人脸特征的存储和检索
"""

import sqlite3
import json
import numpy as np
from typing import List, Dict, Any, Optional
import logging

from src.core.config_manager import get_config_manager
from src.core.logging_config import get_logger

logger = get_logger(__name__)


class FaceDatabase:
    """人脸数据库管理 - 基于SQLite"""
    
    def __init__(self, db_path: str = None):
        self.config_manager = get_config_manager()
        self.config = self.config_manager.config
        
        if db_path is None:
            db_path = self.config_manager.get('database.sqlite.path', './data/msearch.db')
        
        self.db_path = db_path
        self._init_database()
        
        # 监听配置变更
        self.config_manager.watch('database', self._reload_config)
    
    def _reload_config(self, key: str, value: Any) -> None:
        """重新加载配置"""
        if 'database.sqlite.path' in key:
            self.db_path = self.config_manager.get('database.sqlite.path', './data/msearch.db')
            self._init_database()
        
        logger.info(f"人脸数据库配置已更新: {key}")
    
    def _init_database(self) -> None:
        """初始化数据库表结构"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 创建人物信息表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS persons (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name VARCHAR(100) NOT NULL UNIQUE,
                        aliases TEXT,  -- JSON数组存储别名 ["小张", "张总"]
                        description TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # 创建人脸特征表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS face_features (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        person_id INTEGER NOT NULL,
                        image_path VARCHAR(500) NOT NULL,
                        feature_vector BLOB NOT NULL,  -- 512维向量的二进制存储
                        confidence REAL DEFAULT 1.0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (person_id) REFERENCES persons(id) ON DELETE CASCADE
                    )
                """)
                
                # 创建文件人脸检测结果表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS file_faces (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        file_id VARCHAR(100) NOT NULL,
                        person_id INTEGER,  -- 匹配到的人物ID，NULL表示未知人脸
                        bbox_x INTEGER NOT NULL,
                        bbox_y INTEGER NOT NULL,
                        bbox_width INTEGER NOT NULL,
                        bbox_height INTEGER NOT NULL,
                        timestamp REAL,  -- 视频中的时间戳，图片为NULL
                        confidence REAL NOT NULL,
                        feature_vector BLOB NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (person_id) REFERENCES persons(id) ON DELETE SET NULL
                    )
                """)
                
                # 创建索引
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_file_faces_file_id 
                    ON file_faces (file_id)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_file_faces_person_id 
                    ON file_faces (person_id)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_file_faces_timestamp 
                    ON file_faces (timestamp)
                """)
                
                # 创建人脸匹配缓存表（可选，用于性能优化）
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS face_match_cache (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        query_hash VARCHAR(64) NOT NULL UNIQUE,  -- 查询向量的哈希
                        matched_person_ids TEXT,  -- JSON数组存储匹配的人物ID
                        similarities TEXT,  -- JSON数组存储相似度分数
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMP NOT NULL
                    )
                """)
                
                # 创建缓存表索引
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_face_match_cache_expires 
                    ON face_match_cache (expires_at)
                """)
                
                conn.commit()
                logger.info("人脸数据库表结构初始化完成")
                
        except Exception as e:
            logger.error(f"人脸数据库初始化失败: {e}")
            raise
    
    def add_person(self, name: str, image_paths: List[str], 
                   aliases: List[str] = None, description: str = None) -> int:
        """添加新人物到数据库"""
        # 导入人脸模型管理器
        from src.models.face_model_manager import get_face_model_manager
        face_model_manager = get_face_model_manager()
        
        with sqlite3.connect(self.db_path) as conn:
            # 1. 插入人物信息
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO persons (name, aliases, description)
                VALUES (?, ?, ?)
            """, (name, json.dumps(aliases or []), description))
            
            person_id = cursor.lastrowid
            
            # 2. 处理人脸图片（实际检测人脸并提取特征）
            for image_path in image_paths:
                # 检测并提取人脸特征
                face_features = face_model_manager.detect_and_extract_faces(image_path)
                
                if face_features:
                    # 使用第一个人脸的特征（假设是主要人物）
                    main_face = face_features[0]
                    feature_vector = np.array(main_face['features'], dtype=np.float32)
                    confidence = main_face['confidence']
                    
                    # 存储特征向量
                    cursor.execute("""
                        INSERT INTO face_features (person_id, image_path, feature_vector, confidence)
                        VALUES (?, ?, ?, ?)
                    """, (person_id, image_path, feature_vector.tobytes(), confidence))
                    
                    logger.info(f"为人物 {name} 添加人脸特征，置信度: {confidence}")
                else:
                    logger.warning(f"在图片 {image_path} 中未检测到人脸")
            
            conn.commit()
            logger.info(f"人物 {name} 添加成功，ID: {person_id}")
            return person_id
    
    def search_similar_faces(self, query_vector: np.ndarray, 
                            top_k: int = None) -> List[Dict[str, Any]]:
        """搜索相似人脸"""
        top_k = top_k or self.config_manager.get('face_recognition.matching.max_matches', 10)
        threshold = self.config_manager.get('face_recognition.matching.similarity_threshold', 0.6)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 获取所有人脸特征
            cursor.execute("""
                SELECT ff.id, ff.person_id, ff.feature_vector, ff.confidence,
                       p.name, p.aliases
                FROM face_features ff
                JOIN persons p ON ff.person_id = p.id
            """)
            
            matches = []
            for row in cursor.fetchall():
                feature_id, person_id, vector_bytes, confidence, name, aliases = row
                
                # 反序列化向量
                stored_vector = np.frombuffer(vector_bytes, dtype=np.float32)
                
                # 计算相似度
                similarity = self._cosine_similarity(query_vector, stored_vector)
                
                if similarity >= threshold:
                    matches.append({
                        'person_id': person_id,
                        'person_name': name,
                        'aliases': json.loads(aliases or '[]'),
                        'similarity': similarity,
                        'confidence': confidence
                    })
            
            # 按相似度排序并返回前K个
            matches.sort(key=lambda x: x['similarity'], reverse=True)
            return matches[:top_k]
    
    def get_person_by_name(self, person_name: str) -> Dict[str, Any]:
        """根据人名获取人物信息"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 支持别名匹配
            cursor.execute("""
                SELECT id, name, aliases, description
                FROM persons
                WHERE name = ? OR aliases LIKE ?
            """, (person_name, f'%"{person_name}"%'))
            
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'name': row[1],
                    'aliases': json.loads(row[2] or '[]'),
                    'description': row[3]
                }
            return None
    
    def get_person_files(self, person_name: str) -> List[str]:
        """获取包含指定人物的所有文件ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 支持别名匹配
            cursor.execute("""
                SELECT DISTINCT ff.file_id
                FROM file_faces ff
                JOIN persons p ON ff.person_id = p.id
                WHERE p.name = ? OR p.aliases LIKE ?
            """, (person_name, f'%"{person_name}"%'))
            
            return [row[0] for row in cursor.fetchall()]
    
    def index_file_faces(self, file_id: str, image_path: str):
        """为文件建立人脸索引"""
        # 导入人脸模型管理器
        from src.models.face_model_manager import get_face_model_manager
        face_model_manager = get_face_model_manager()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 检测并提取人脸特征
            face_features = face_model_manager.detect_and_extract_faces(image_path)
            
            for face in face_features:
                # 提取特征向量
                feature_vector = np.array(face['features'], dtype=np.float32)
                confidence = face['confidence']
                bbox = face['bbox']
                
                # 查找匹配的人物
                matches = self.search_similar_faces(feature_vector, top_k=1)
                person_id = matches[0]['person_id'] if matches else None
                
                # 存储检测结果
                cursor.execute("""
                    INSERT INTO file_faces 
                    (file_id, person_id, bbox_x, bbox_y, bbox_width, bbox_height, 
                     timestamp, confidence, feature_vector)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    file_id, person_id, 
                    bbox['x'], bbox['y'], bbox['width'], bbox['height'],
                    None, confidence, feature_vector.tobytes()
                ))
            
            conn.commit()
            logger.info(f"文件 {file_id} 的人脸索引建立完成，检测到 {len(face_features)} 个人脸")
    
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """计算余弦相似度"""
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


# 全局人脸数据库实例
_face_database = None


def get_face_database() -> FaceDatabase:
    """获取全局人脸数据库实例"""
    global _face_database
    if _face_database is None:
        _face_database = FaceDatabase()
    return _face_database