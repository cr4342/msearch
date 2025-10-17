"""
文件类型检测器 - 精确识别文件类型，为媒体处理提供准确的类型信息
"""
import os
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    logger.warning("python-magic未安装，将使用简化文件类型检测")


class FileTypeDetector:
    """文件类型检测器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化文件类型检测器
        
        Args:
            config: 配置字典
        """
        self.config = config
        
        # 从配置加载文件类型映射
        self.file_extensions = config.get('file_monitoring.file_extensions', {
            'image': ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp'],
            'video': ['.mp4', '.avi', '.mov', '.mkv', '.webm'],
            'audio': ['.mp3', '.wav', '.ogg', '.flac', '.aac'],
            'text': ['.txt', '.md', '.csv', '.json', '.xml']
        })
        
        self.mime_types = config.get('file_monitoring.mime_types', {
            'image': ['image/jpeg', 'image/png', 'image/bmp', 'image/gif', 'image/webp'],
            'video': ['video/mp4', 'video/x-msvideo', 'video/quicktime', 'video/x-matroska', 'video/webm'],
            'audio': ['audio/mpeg', 'audio/wav', 'audio/ogg', 'audio/flac', 'audio/aac'],
            'text': ['text/plain', 'text/markdown', 'text/csv', 'application/json', 'application/xml']
        })
        
        logger.info("文件类型检测器初始化完成")
    
    def detect_file_type(self, file_path: str) -> Dict[str, Any]:
        """
        检测文件类型
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件类型信息字典
        """
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"文件不存在: {file_path}")
            
            # 1. 基于扩展名的检测
            extension_result = self._detect_by_extension(file_path)
            
            # 2. 基于MIME类型的检测
            mime_result = self._detect_by_mime(file_path)
            
            # 3. 综合两种检测结果
            final_result = self._combine_detection_results(extension_result, mime_result)
            
            logger.debug(f"文件类型检测完成: {file_path} -> {final_result}")
            return final_result
            
        except Exception as e:
            logger.error(f"文件类型检测失败: {file_path}, 错误: {e}")
            return {
                'type': 'unknown',
                'subtype': 'unknown',
                'extension': os.path.splitext(file_path)[1],
                'confidence': 0.1,
                'detect_method': 'error',
                'error': str(e)
            }
    
    def _detect_by_extension(self, file_path: str) -> Dict[str, Any]:
        """
        基于文件扩展名检测文件类型
        
        Args:
            file_path: 文件路径
            
        Returns:
            检测结果字典
        """
        extension = os.path.splitext(file_path)[1].lower()
        
        # 查找匹配的文件类型
        for file_type, extensions in self.file_extensions.items():
            if extension in extensions:
                return {
                    'type': file_type,
                    'subtype': extension.lstrip('.'),
                    'extension': extension,
                    'confidence': 0.7,
                    'detect_method': 'extension'
                }
        
        # 未知类型
        return {
            'type': 'unknown',
            'subtype': 'unknown',
            'extension': extension,
            'confidence': 0.3,
            'detect_method': 'extension'
        }
    
    def _detect_by_mime(self, file_path: str) -> Dict[str, Any]:
        """
        基于MIME类型检测文件类型
        
        Args:
            file_path: 文件路径
            
        Returns:
            检测结果字典
        """
        if not MAGIC_AVAILABLE:
            # 如果magic不可用，返回默认结果
            return {
                'type': 'unknown',
                'subtype': 'octet-stream',
                'mime_type': 'application/octet-stream',
                'file_description': 'Magic library not available',
                'confidence': 0.1,
                'detect_method': 'mime_unavailable'
            }
        
        try:
            # 使用magic库检测MIME类型
            mime_magic = magic.Magic(mime=True)
            mime_type = mime_magic.from_file(file_path)
            
            # 获取文件描述
            file_magic = magic.Magic()
            file_description = file_magic.from_file(file_path)
            
            # 查找匹配的文件类型
            for file_type, mime_types in self.mime_types.items():
                if mime_type in mime_types:
                    return {
                        'type': file_type,
                        'subtype': mime_type.split('/')[-1],
                        'mime_type': mime_type,
                        'file_description': file_description,
                        'confidence': 0.9,
                        'detect_method': 'mime'
                    }
            
            # 未知类型
            return {
                'type': 'unknown',
                'subtype': mime_type.split('/')[-1] if '/' in mime_type else 'unknown',
                'mime_type': mime_type,
                'file_description': file_description,
                'confidence': 0.5,
                'detect_method': 'mime'
            }
            
        except Exception as e:
            logger.warning(f"MIME类型检测失败: {file_path}, 错误: {e}")
            return {
                'type': 'unknown',
                'subtype': 'error',
                'mime_type': 'error',
                'file_description': f'Error: {e}',
                'confidence': 0.1,
                'detect_method': 'mime_error'
            }
    
    def _combine_detection_results(self, extension_result: Dict[str, Any], 
                                  mime_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        综合扩展名和MIME类型检测结果
        
        Args:
            extension_result: 扩展名检测结果
            mime_result: MIME类型检测结果
            
        Returns:
            综合检测结果
        """
        # 如果两个结果一致，增加置信度
        if (extension_result['type'] == mime_result['type'] and 
            extension_result['type'] != 'unknown'):
            combined_result = extension_result.copy()
            combined_result['confidence'] = min(0.95, extension_result['confidence'] + 0.2)
            combined_result['detect_method'] = 'combined'
            combined_result['mime_type'] = mime_result.get('mime_type')
            combined_result['file_description'] = mime_result.get('file_description')
            return combined_result
        
        # 如果MIME类型检测成功且不是未知类型，优先使用MIME结果
        if (mime_result['type'] != 'unknown' and 
            mime_result['detect_method'] not in ['mime_unavailable', 'mime_error']):
            mime_result['detect_method'] = 'mime_priority'
            return mime_result
        
        # 如果扩展名检测成功且不是未知类型，使用扩展名结果
        if extension_result['type'] != 'unknown':
            extension_result['detect_method'] = 'extension_fallback'
            return extension_result
        
        # 如果都失败，返回MIME结果
        return mime_result
    
    def is_supported_file_type(self, file_path: str) -> bool:
        """
        检查文件类型是否受支持
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否受支持
        """
        detection_result = self.detect_file_type(file_path)
        return detection_result['type'] != 'unknown'


# 全局单例实例
_file_type_detector = None


def get_file_type_detector(config: Dict[str, Any] = None) -> FileTypeDetector:
    """
    获取文件类型检测器单例实例
    
    Args:
        config: 配置字典
        
    Returns:
        文件类型检测器实例
    """
    global _file_type_detector
    if _file_type_detector is None:
        _file_type_detector = FileTypeDetector(config or {})
    return _file_type_detector


# 示例使用
if __name__ == "__main__":
    # 配置示例
    config = {
        'file_monitoring.file_extensions': {
            'image': ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp'],
            'video': ['.mp4', '.avi', '.mov', '.mkv', '.webm'],
            'audio': ['.mp3', '.wav', '.ogg', '.flac', '.aac'],
            'text': ['.txt', '.md', '.csv', '.json', '.xml']
        },
        'file_monitoring.mime_types': {
            'image': ['image/jpeg', 'image/png', 'image/bmp', 'image/gif', 'image/webp'],
            'video': ['video/mp4', 'video/x-msvideo', 'video/quicktime', 'video/x-matroska', 'video/webm'],
            'audio': ['audio/mpeg', 'audio/wav', 'audio/ogg', 'audio/flac', 'audio/aac'],
            'text': ['text/plain', 'text/markdown', 'text/csv', 'application/json', 'application/xml']
        }
    }
    
    # 获取检测器实例
    detector = get_file_type_detector(config)
    
    # 检测文件类型 (需要实际的文件路径)
    # result = detector.detect_file_type("path/to/file.jpg")
    # print(result)
    # 
    # is_supported = detector.is_supported_file_type("path/to/file.jpg")
    # print(f"文件类型是否受支持: {is_supported}")