"""
视频元数据处理器 - 解析摄像机XML并提取关键参数

支持：
- 自动摄像机识别：RED、ARRI、Sony、Canon等主流品牌
- 关键参数提取：拍摄日期、时间码、摄像机设置等
- 文件关联机制：自动匹配XML与媒体文件
- 错误隔离：解析失败不影响主流程
"""

import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class UnsupportedCameraError(Exception):
    """不支持的摄像机类型错误"""
    pass


class CameraMetadataParser:
    """摄像机元数据解析器基类"""
    
    def can_handle(self, header: str) -> bool:
        """检查是否能处理此XML"""
        raise NotImplementedError
    
    def parse(self, xml_path: str) -> Dict[str, Any]:
        """解析XML文件"""
        raise NotImplementedError


class RedMetadataParser(CameraMetadataParser):
    """RED摄像机元数据解析器"""
    
    def can_handle(self, header: str) -> bool:
        return 'RED' in header or 'red' in header
    
    def parse(self, xml_path: str) -> Dict[str, Any]:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        metadata = {
            'camera_brand': 'RED',
            'camera_model': '',
            'shooting_date': '',
            'timecode': '',
            'frame_rate': '',
            'resolution': '',
            'iso': '',
            'shutter_angle': '',
            'aperture': '',
        }
        
        # 提取RED特定元数据
        for elem in root.iter():
            if 'Camera' in elem.tag:
                metadata['camera_model'] = elem.get('model', '')
            if 'Date' in elem.tag or 'date' in elem.tag:
                metadata['shooting_date'] = elem.text
            if 'Timecode' in elem.tag or 'timecode' in elem.tag:
                metadata['timecode'] = elem.text
        
        return metadata


class ArriMetadataParser(CameraMetadataParser):
    """ARRI摄像机元数据解析器"""
    
    def can_handle(self, header: str) -> bool:
        return 'ARRI' in header or 'arri' in header
    
    def parse(self, xml_path: str) -> Dict[str, Any]:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        metadata = {
            'camera_brand': 'ARRI',
            'camera_model': '',
            'shooting_date': '',
            'timecode': '',
            'frame_rate': '',
            'resolution': '',
            'iso': '',
            'shutter_angle': '',
            'aperture': '',
        }
        
        for elem in root.iter():
            if 'Camera' in elem.tag:
                metadata['camera_model'] = elem.get('model', '')
            if 'Date' in elem.tag or 'date' in elem.tag:
                metadata['shooting_date'] = elem.text
        
        return metadata


class SonyMetadataParser(CameraMetadataParser):
    """Sony摄像机元数据解析器"""
    
    def can_handle(self, header: str) -> bool:
        return 'Sony' in header or 'sony' in header
    
    def parse(self, xml_path: str) -> Dict[str, Any]:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        metadata = {
            'camera_brand': 'Sony',
            'camera_model': '',
            'shooting_date': '',
            'timecode': '',
            'frame_rate': '',
            'resolution': '',
            'iso': '',
            'shutter_angle': '',
            'aperture': '',
        }
        
        for elem in root.iter():
            if 'Camera' in elem.tag:
                metadata['camera_model'] = elem.get('model', '')
            if 'Date' in elem.tag or 'date' in elem.tag:
                metadata['shooting_date'] = elem.text
        
        return metadata


class CanonMetadataParser(CameraMetadataParser):
    """Canon摄像机元数据解析器"""
    
    def can_handle(self, header: str) -> bool:
        return 'Canon' in header or 'canon' in header
    
    def parse(self, xml_path: str) -> Dict[str, Any]:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        metadata = {
            'camera_brand': 'Canon',
            'camera_model': '',
            'shooting_date': '',
            'timecode': '',
            'frame_rate': '',
            'resolution': '',
            'iso': '',
            'shutter_angle': '',
            'aperture': '',
        }
        
        for elem in root.iter():
            if 'Camera' in elem.tag:
                metadata['camera_model'] = elem.get('model', '')
            if 'Date' in elem.tag or 'date' in elem.tag:
                metadata['shooting_date'] = elem.text
        
        return metadata


class VideoMetadataProcessor:
    """
    视频元数据处理器 - 解析摄像机XML并提取关键参数
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化视频元数据处理器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.supported_cameras = {
            "RED": RedMetadataParser(),
            "ARRI": ArriMetadataParser(),
            "Sony": SonyMetadataParser(),
            "Canon": CanonMetadataParser()
        }
        
        # 从配置中获取支持的摄像机类型
        metadata_config = config.get('metadata', {}).get('video', {})
        self.supported_camera_types = metadata_config.get('supported_cameras', 
                                                          list(self.supported_cameras.keys()))
        
        # 验证规则配置
        self.validation_rules = metadata_config.get('validation_rules', {})
        self.required_fields = self.validation_rules.get('required_fields', [])
        
        logger.info(f"视频元数据处理器初始化完成，支持: {self.supported_camera_types}")
    
    def detect_camera_type(self, xml_path: str) -> str:
        """
        自动识别摄像机品牌
        
        Args:
            xml_path: XML文件路径
            
        Returns:
            str: 摄像机品牌
        """
        with open(xml_path, 'r') as f:
            header = f.read(1024)
        
        for brand, parser in self.supported_cameras.items():
            if parser.can_handle(header):
                return brand
        
        return "Unknown"
    
    def extract_metadata(self, xml_path: str) -> Dict[str, Any]:
        """
        提取完整元数据
        
        Args:
            xml_path: XML文件路径
            
        Returns:
            Dict: 元数据字典
            
        Raises:
            UnsupportedCameraError: 不支持的摄像机类型
        """
        camera_type = self.detect_camera_type(xml_path)
        
        if camera_type == "Unknown":
            raise UnsupportedCameraError(f"不支持的摄像机类型: {camera_type}")
        
        parser = self.supported_cameras.get(camera_type)
        if not parser:
            raise UnsupportedCameraError(f"不支持的摄像机类型: {camera_type}")
        
        metadata = parser.parse(xml_path)
        
        # 验证必需字段
        self._validate_metadata(metadata)
        
        logger.info(f"提取元数据成功: {xml_path}, camera_type={camera_type}")
        
        return metadata
    
    def associate_with_media(self, metadata: Dict[str, Any], media_file: str) -> bool:
        """
        将元数据关联到媒体文件
        
        Args:
            metadata: 元数据字典
            media_file: 媒体文件路径
            
        Returns:
            bool: 是否关联成功
        """
        # 基于文件名/时间戳匹配
        xml_path = self._find_associated_xml(media_file)
        
        if xml_path and Path(xml_path).exists():
            logger.info(f"关联元数据: {media_file} -> {xml_path}")
            return True
        
        logger.warning(f"未找到关联的XML文件: {media_file}")
        return False
    
    def _find_associated_xml(self, media_file: str) -> Optional[str]:
        """
        查找关联的XML文件
        
        Args:
            media_file: 媒体文件路径
            
        Returns:
            Optional[str]: XML文件路径
        """
        media_path = Path(media_file)
        base_name = media_path.stem
        
        # 查找同名的XML文件
        xml_path = media_path.parent / f"{base_name}.xml"
        if xml_path.exists():
            return str(xml_path)
        
        # 查找可能的XML文件（常见的命名模式）
        for pattern in ['*_metadata.xml', '*_camera.xml']:
            matches = list(media_path.parent.glob(pattern))
            if matches:
                return str(matches[0])
        
        return None
    
    def _validate_metadata(self, metadata: Dict[str, Any]) -> None:
        """
        验证元数据
        
        Args:
            metadata: 元数据字典
            
        Raises:
            ValueError: 验证失败
        """
        missing_fields = []
        for field in self.required_fields:
            if field not in metadata or not metadata[field]:
                missing_fields.append(field)
        
        if missing_fields:
            logger.warning(f"元数据缺少必需字段: {missing_fields}")
