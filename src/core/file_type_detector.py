"""
文件类型识别器模块
负责精确识别文件类型，为媒体处理提供准确的类型信息
"""

import os
import magic
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import logging
from functools import lru_cache

from src.core.config_manager import get_config_manager
from src.core.logging_config import get_logger

logger = get_logger(__name__)


class FileTypeDetector:
    """文件类型识别器 - 提供多种文件类型检测策略"""
    
    def __init__(self):
        """初始化文件类型识别器"""
        self.config_manager = get_config_manager()
        self._load_config()
        
        # 初始化libmagic用于基于文件内容的类型检测
        self.mime_magic = magic.Magic(mime=True)
        self.file_magic = magic.Magic()
        
        logger.info("文件类型识别器初始化完成")
    
    def _load_config(self) -> None:
        """从配置加载文件类型映射和检测策略"""
        # 从配置获取支持的文件类型映射
        self.file_extensions = self.config_manager.get('file_monitoring.file_extensions', {
            'image': ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp'],
            'video': ['.mp4', '.avi', '.mov', '.mkv', '.webm'],
            'audio': ['.mp3', '.wav', '.ogg', '.flac', '.aac'],
            'text': ['.txt', '.md', '.csv', '.json', '.xml']
        })
        
        # 从配置获取MIME类型映射
        self.mime_types = self.config_manager.get('file_monitoring.mime_types', {
            'image': ['image/jpeg', 'image/png', 'image/bmp', 'image/gif', 'image/webp'],
            'video': ['video/mp4', 'video/x-msvideo', 'video/quicktime', 'video/x-matroska', 'video/webm'],
            'audio': ['audio/mpeg', 'audio/wav', 'audio/ogg', 'audio/flac', 'audio/aac'],
            'text': ['text/plain', 'text/markdown', 'text/csv', 'application/json', 'application/xml']
        })
        
        # 监听配置变更
        self.config_manager.watch('file_monitoring', self._on_config_changed)
    
    def _on_config_changed(self, key: str, value: Any) -> None:
        """配置变更回调"""
        logger.info(f"文件监控配置已变更: {key}")
        self._load_config()
    
    @lru_cache(maxsize=1000)
    def detect_file_type(self, file_path: str) -> Dict[str, str]:
        """
        检测文件类型，返回综合检测结果
        
        Args:
            file_path: 文件路径
            
        Returns:
            包含文件类型信息的字典
        """
        if not os.path.exists(file_path):
            logger.error(f"文件不存在: {file_path}")
            return {
                'type': 'unknown',
                'subtype': 'unknown',
                'extension': '',
                'mime_type': '',
                'confidence': 0.0,
                'detect_method': 'none'
            }
        
        # 1. 基于文件扩展名检测
        extension_type = self._detect_by_extension(file_path)
        
        # 2. 基于文件内容(MIME类型)检测
        mime_type_info = self._detect_by_mime(file_path)
        
        # 3. 综合判断
        result = self._combine_detection_results(extension_type, mime_type_info)
        
        logger.debug(f"文件类型检测结果: {file_path} -> {result}")
        return result
    
    def _detect_by_extension(self, file_path: str) -> Dict[str, str]:
        """
        基于文件扩展名检测文件类型
        
        Args:
            file_path: 文件路径
            
        Returns:
            检测结果字典
        """
        file_extension = Path(file_path).suffix.lower()
        
        for file_type, extensions in self.file_extensions.items():
            if file_extension in extensions:
                return {
                    'type': file_type,
                    'subtype': file_extension.lstrip('.'),
                    'extension': file_extension,
                    'confidence': 0.7,
                    'detect_method': 'extension'
                }
        
        return {
            'type': 'unknown',
            'subtype': 'unknown',
            'extension': file_extension,
            'confidence': 0.3,
            'detect_method': 'extension'
        }
    
    def _detect_by_mime(self, file_path: str) -> Dict[str, str]:
        """
        基于文件内容(MIME类型)检测文件类型
        
        Args:
            file_path: 文件路径
            
        Returns:
            检测结果字典
        """
        try:
            mime_type = self.mime_magic.from_file(file_path)
            file_description = self.file_magic.from_file(file_path)
            
            # 映射MIME类型到文件类型
            file_type = 'unknown'
            for type_key, mime_list in self.mime_types.items():
                if mime_type in mime_list:
                    file_type = type_key
                    break
            
            # 从MIME类型提取子类型
            subtype = mime_type.split('/')[1] if '/' in mime_type else 'unknown'
            
            return {
                'type': file_type,
                'subtype': subtype,
                'mime_type': mime_type,
                'file_description': file_description,
                'confidence': 0.9,
                'detect_method': 'mime'
            }
        except Exception as e:
            logger.error(f"基于MIME类型检测文件失败: {file_path}, 错误: {e}")
            return {
                'type': 'unknown',
                'subtype': 'unknown',
                'mime_type': '',
                'confidence': 0.1,
                'detect_method': 'mime_error'
            }
    
    def _combine_detection_results(self, 
                                  extension_result: Dict[str, str], 
                                  mime_result: Dict[str, str]) -> Dict[str, str]:
        """
        综合多种检测结果，返回最终的文件类型判断
        
        Args:
            extension_result: 基于扩展名的检测结果
            mime_result: 基于MIME类型的检测结果
            
        Returns:
            综合后的检测结果
        """
        # 如果两种方法检测结果一致，直接返回
        if (extension_result['type'] != 'unknown' and 
           mime_result['type'] != 'unknown' and 
           extension_result['type'] == mime_result['type']):
            return {
                'type': extension_result['type'],
                'subtype': extension_result['subtype'],
                'extension': extension_result['extension'],
                'mime_type': mime_result.get('mime_type', ''),
                'file_description': mime_result.get('file_description', ''),
                'confidence': min(1.0, extension_result['confidence'] + mime_result['confidence'] * 0.3),
                'detect_method': 'combined'
            }
        
        # 优先信任MIME类型检测结果
        if mime_result['type'] != 'unknown':
            return {
                'type': mime_result['type'],
                'subtype': mime_result['subtype'],
                'extension': extension_result['extension'],
                'mime_type': mime_result.get('mime_type', ''),
                'file_description': mime_result.get('file_description', ''),
                'confidence': mime_result['confidence'],
                'detect_method': 'mime_priority'
            }
        
        # 否则返回扩展名检测结果
        return {
            'type': extension_result['type'],
            'subtype': extension_result['subtype'],
            'extension': extension_result['extension'],
            'mime_type': mime_result.get('mime_type', ''),
            'confidence': extension_result['confidence'],
            'detect_method': 'extension_fallback'
        }
    
    def get_processing_strategy(self, file_type: str) -> str:
        """
        根据文件类型获取对应的处理策略
        
        Args:
            file_type: 文件类型
            
        Returns:
            处理策略名称
        """
        strategy_mapping = {
            'image': 'image_processing',
            'video': 'video_processing',
            'audio': 'audio_processing',
            'text': 'text_processing'
        }
        
        return strategy_mapping.get(file_type, 'default_processing')
    
    def is_supported_file_type(self, file_path: str) -> bool:
        """
        检查文件类型是否受支持
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否支持该文件类型
        """
        file_info = self.detect_file_type(file_path)
        return file_info['type'] != 'unknown'
    
    def get_supported_extensions(self) -> Dict[str, List[str]]:
        """
        获取所有支持的文件扩展名
        
        Returns:
            文件类型到扩展名列表的映射
        """
        return self.file_extensions


# 全局文件类型识别器实例
_file_type_detector = None


def get_file_type_detector() -> FileTypeDetector:
    """
    获取全局文件类型识别器实例
    
    Returns:
        FileTypeDetector实例
    """
    global _file_type_detector
    if _file_type_detector is None:
        _file_type_detector = FileTypeDetector()
    return _file_type_detector