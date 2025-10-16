"""
智能检索策略引擎
负责查询类型识别、文件白名单生成和动态权重分配
"""

from typing import Dict, List, Any, Optional
import re
import logging

from src.core.config_manager import get_config_manager
from src.core.logging_config import get_logger
from src.models.face_database import get_face_database

logger = get_logger(__name__)


class SmartRetrievalEngine:
    """智能检索引擎 - 集成人脸检索"""
    
    def __init__(self):
        self.config_manager = get_config_manager()
        self.config = self.config_manager.config
        self.face_db = get_face_database()
        
        # 监听配置变更
        self.config_manager.watch('smart_retrieval', self._reload_config)
        self.config_manager.watch('face_recognition', self._reload_config)
    
    def _reload_config(self, key: str, value: Any) -> None:
        """重新加载配置"""
        logger.info(f"智能检索引擎配置已更新: {key}")
    
    def detect_query_type(self, query: str) -> str:
        """检测查询类型"""
        # 1. 人名识别
        person_name = self._detect_person_name(query)
        if person_name:
            return "person_name"
        
        # 2. 音频关键词检测
        if self._detect_audio_keywords(query):
            return "audio"
        
        # 3. 视觉关键词检测
        if self._detect_visual_keywords(query):
            return "visual"
        
        # 4. 默认综合检索
        return "mixed"
    
    def _detect_person_name(self, query: str) -> Optional[str]:
        """检测查询中的人名"""
        try:
            # 获取所有人名
            person_names = self._get_all_person_names()
            
            # 在查询中查找匹配的人名
            query_lower = query.lower()
            for name in person_names:
                # 直接匹配
                if name.lower() in query_lower:
                    return name
                
                # 别名匹配
                aliases = self._get_person_aliases(name)
                for alias in aliases:
                    if alias.lower() in query_lower:
                        return name
            
            return None
        except Exception as e:
            logger.error(f"人名检测失败: {e}")
            return None
    
    def _get_all_person_names(self) -> List[str]:
        """获取所有人名"""
        try:
            import sqlite3
            with sqlite3.connect(self.face_db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM persons")
                names = [row[0] for row in cursor.fetchall()]
                return names
        except Exception as e:
            logger.error(f"获取人名列表失败: {e}")
            return []
    
    def _get_person_aliases(self, person_name: str) -> List[str]:
        """获取人名的别名"""
        try:
            import sqlite3
            import json
            with sqlite3.connect(self.face_db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT aliases FROM persons WHERE name = ?", (person_name,))
                row = cursor.fetchone()
                if row and row[0]:
                    return json.loads(row[0])
                return []
        except Exception as e:
            logger.error(f"获取人名别名失败: {e}")
            return []
    
    def _detect_audio_keywords(self, query: str) -> bool:
        """检测音频相关关键词"""
        music_keywords = self.config_manager.get('smart_retrieval.keywords.music', [])
        speech_keywords = self.config_manager.get('smart_retrieval.keywords.speech', [])
        
        # 检查查询中是否包含音频关键词
        cleaned_query = self._preprocess_query(query)
        
        for keyword in music_keywords + speech_keywords:
            if keyword in cleaned_query:
                return True
        
        return False
    
    def _detect_visual_keywords(self, query: str) -> bool:
        """检测视觉相关关键词"""
        visual_keywords = self.config_manager.get('smart_retrieval.keywords.visual', [])
        
        # 检查查询中是否包含视觉关键词
        cleaned_query = self._preprocess_query(query)
        
        for keyword in visual_keywords:
            if keyword in cleaned_query:
                return True
        
        return False
    
    def _preprocess_query(self, query: str) -> str:
        """预处理查询文本"""
        # 清理标点符号和多余空格
        cleaned = re.sub(r'[^\w\s]', '', query)
        # 转换为小写
        cleaned = cleaned.lower()
        # 去除多余空格
        cleaned = ' '.join(cleaned.split())
        return cleaned
    
    def calculate_weights(self, query_type: str, query: str) -> Dict[str, float]:
        """计算动态权重"""
        if query_type == "person_name":
            # 人名查询：视觉模态主导，音频模态辅助
            return self.config_manager.get('smart_retrieval.person_weights', {
                "clip": 0.5, "clap": 0.25, "whisper": 0.25
            })
        
        elif query_type == "audio":
            # 音频查询：根据关键词类型动态调整音频内部权重
            music_keywords = self.config_manager.get('smart_retrieval.keywords.music', [])
            speech_keywords = self.config_manager.get('smart_retrieval.keywords.speech', [])
            
            cleaned_query = self._preprocess_query(query)
            
            if any(keyword in cleaned_query for keyword in music_keywords):
                # 音乐类查询：CLAP主导
                return self.config_manager.get('smart_retrieval.audio_weights.music', {
                    "clip": 0.2, "clap": 0.7, "whisper": 0.1
                })
            elif any(keyword in cleaned_query for keyword in speech_keywords):
                # 语音类查询：Whisper主导
                return self.config_manager.get('smart_retrieval.audio_weights.speech', {
                    "clip": 0.2, "clap": 0.1, "whisper": 0.7
                })
            else:
                # 通用音频查询：保持相对均衡
                return {
                    "clip": 0.2, "clap": 0.5, "whisper": 0.3
                }
        
        elif query_type == "visual":
            # 视觉查询：视觉模态绝对主导
            return self.config_manager.get('smart_retrieval.visual_weights', {
                "clip": 0.7, "clap": 0.15, "whisper": 0.15
            })
        
        else:  # mixed
            # 默认综合检索权重
            return self.config_manager.get('smart_retrieval.default_weights', {
                "clip": 0.4, "clap": 0.3, "whisper": 0.3
            })
    
    def generate_file_whitelist(self, query: str) -> Optional[List[str]]:
        """生成文件白名单"""
        # 1. 人名识别
        person_name = self._detect_person_name(query)
        
        if person_name:
            # 2. 人脸预检索 - 生成文件白名单
            file_whitelist = self.face_db.get_person_files(person_name)
            return file_whitelist
        
        # 对于其他查询类型，不使用白名单
        return None
    
    def search(self, query: str) -> Dict[str, Any]:
        """执行智能检索"""
        # 1. 检测查询类型
        query_type = self.detect_query_type(query)
        logger.info(f"查询类型识别: {query_type}")
        
        # 2. 计算动态权重
        weights = self.calculate_weights(query_type, query)
        logger.info(f"动态权重分配: {weights}")
        
        # 3. 生成文件白名单（如果需要）
        file_whitelist = self.generate_file_whitelist(query)
        logger.info(f"文件白名单生成: {len(file_whitelist) if file_whitelist else 0} 个文件")
        
        # 4. 返回检索配置
        return {
            "query_type": query_type,
            "weights": weights,
            "file_whitelist": file_whitelist
        }


# 全局智能检索引擎实例
_smart_retrieval_engine = None


def get_smart_retrieval_engine() -> SmartRetrievalEngine:
    """获取全局智能检索引擎实例"""
    global _smart_retrieval_engine
    if _smart_retrieval_engine is None:
        _smart_retrieval_engine = SmartRetrievalEngine()
    return _smart_retrieval_engine