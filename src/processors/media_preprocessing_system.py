"""
媒体预处理系统 - 简化版本
提供可直接调用的媒体预处理方法，支持文件切片后的UUID关联管理
"""
import os
import uuid
import json
from typing import Dict, Any, List, Optional, Tuple
import logging
from pathlib import Path
from dataclasses import dataclass, asdict

from src.core.config_manager import get_config_manager
from src.processors.media_processor import MediaProcessor
from src.processors.timestamp_processor import TimestampProcessor, TimestampInfo, ModalityType

logger = logging.getLogger(__name__)


@dataclass
class FileSegmentMapping:
    """文件切片映射信息"""
    original_file_id: str  # 原始文件UUID
    original_file_path: str  # 原始文件路径
    segment_id: str  # 切片UUID
    segment_path: str  # 切片文件路径
    segment_index: int  # 切片索引
    start_time: float  # 切片开始时间
    end_time: float  # 切片结束时间
    duration: float  # 切片时长
    modality: str  # 模态类型
    created_at: float  # 创建时间戳


@dataclass
class PreprocessingResult:
    """预处理结果"""
    status: str  # 'success' or 'error'
    original_file_id: str  # 原始文件UUID
    original_file_path: str  # 原始文件路径
    file_type: str  # 文件类型
    segments: List[FileSegmentMapping]  # 切片映射列表
    metadata: Dict[str, Any]  # 文件元数据
    timestamp_infos: List[TimestampInfo]  # 时间戳信息
    processing_time: float  # 处理耗时
    error_message: Optional[str] = None  # 错误信息


class SegmentMappingManager:
    """切片映射管理器 - 管理文件切片后的UUID关联关系"""
    
    def __init__(self, storage_path: str = "data/segment_mappings.json"):
        """
        初始化切片映射管理器
        
        Args:
            storage_path: 映射数据存储路径
        """
        self.storage_path = storage_path
        self.mappings: Dict[str, List[FileSegmentMapping]] = {}
        self._load_mappings()
        
        logger.info(f"切片映射管理器初始化完成: {storage_path}")
    
    def _load_mappings(self):
        """从文件加载映射数据"""
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # 转换为FileSegmentMapping对象
                for original_file_id, segments_data in data.items():
                    segments = []
                    for segment_data in segments_data:
                        segment = FileSegmentMapping(**segment_data)
                        segments.append(segment)
                    self.mappings[original_file_id] = segments
                
                logger.info(f"加载了 {len(self.mappings)} 个文件的切片映射")
        except Exception as e:
            logger.error(f"加载切片映射失败: {e}")
            self.mappings = {}
    
    def _save_mappings(self):
        """保存映射数据到文件"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            
            # 转换为可序列化的字典
            data = {}
            for original_file_id, segments in self.mappings.items():
                data[original_file_id] = [asdict(segment) for segment in segments]
            
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            logger.debug(f"切片映射已保存: {len(self.mappings)} 个文件")
        except Exception as e:
            logger.error(f"保存切片映射失败: {e}")
    
    def add_segment_mapping(self, mapping: FileSegmentMapping):
        """添加切片映射"""
        if mapping.original_file_id not in self.mappings:
            self.mappings[mapping.original_file_id] = []
        
        self.mappings[mapping.original_file_id].append(mapping)
        self._save_mappings()
        
        logger.debug(f"添加切片映射: {mapping.original_file_id} -> {mapping.segment_id}")
    
    def get_segments_by_file_id(self, original_file_id: str) -> List[FileSegmentMapping]:
        """根据原始文件ID获取所有切片映射"""
        return self.mappings.get(original_file_id, [])
    
    def get_original_file_info(self, segment_id: str) -> Optional[FileSegmentMapping]:
        """根据切片ID获取原始文件信息"""
        for segments in self.mappings.values():
            for segment in segments:
                if segment.segment_id == segment_id:
                    return segment
        return None
    
    def calculate_original_timestamp(self, segment_id: str, segment_timestamp: float) -> Optional[float]:
        """
        根据切片时间戳计算原始文件中的时间戳
        
        Args:
            segment_id: 切片ID
            segment_timestamp: 切片内的时间戳
            
        Returns:
            原始文件中的时间戳，如果找不到则返回None
        """
        segment_info = self.get_original_file_info(segment_id)
        if segment_info:
            # 原始时间戳 = 切片开始时间 + 切片内时间戳
            return segment_info.start_time + segment_timestamp
        return None
    
    def find_segment_by_original_timestamp(self, original_file_id: str, 
                                         original_timestamp: float) -> Optional[Tuple[FileSegmentMapping, float]]:
        """
        根据原始文件时间戳找到对应的切片和切片内时间戳
        
        Args:
            original_file_id: 原始文件ID
            original_timestamp: 原始文件中的时间戳
            
        Returns:
            (切片映射, 切片内时间戳) 或 None
        """
        segments = self.get_segments_by_file_id(original_file_id)
        
        for segment in segments:
            if segment.start_time <= original_timestamp <= segment.end_time:
                segment_timestamp = original_timestamp - segment.start_time
                return segment, segment_timestamp
        
        return None
    
    def remove_file_mappings(self, original_file_id: str):
        """删除指定文件的所有切片映射"""
        if original_file_id in self.mappings:
            del self.mappings[original_file_id]
            self._save_mappings()
            logger.info(f"删除文件切片映射: {original_file_id}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取映射统计信息"""
        total_files = len(self.mappings)
        total_segments = sum(len(segments) for segments in self.mappings.values())
        
        modality_stats = {}
        for segments in self.mappings.values():
            for segment in segments:
                modality = segment.modality
                modality_stats[modality] = modality_stats.get(modality, 0) + 1
        
        return {
            'total_files': total_files,
            'total_segments': total_segments,
            'modality_distribution': modality_stats,
            'avg_segments_per_file': total_segments / total_files if total_files > 0 else 0
        }


def preprocess_media_file(file_path: str, config: Optional[Dict[str, Any]] = None) -> PreprocessingResult:
    """
    预处理媒体文件 - 简化的直接调用接口
    
    Args:
        file_path: 媒体文件路径
        config: 可选的配置字典，如果不提供则从配置文件读取
        
    Returns:
        预处理结果对象
    """
    import time
    start_time = time.time()
    
    try:
        # 生成原始文件UUID
        original_file_id = str(uuid.uuid4())
        
        # 加载配置
        if config is None:
            config_manager = get_config_manager()
            config = config_manager.config
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        # 检测文件类型
        file_type = _detect_file_type(file_path)
        if file_type == 'unknown':
            raise ValueError(f"不支持的文件类型: {file_path}")
        
        logger.info(f"开始预处理文件: {file_path} (ID: {original_file_id}, 类型: {file_type})")
        
        # 初始化处理器
        media_processor = MediaProcessor()
        timestamp_processor = TimestampProcessor(config)
        segment_manager = SegmentMappingManager()
        
        # 根据文件类型进行处理
        segments = []
        timestamp_infos = []
        metadata = {}
        
        if file_type == 'image':
            # 图片不需要切片，直接处理
            segment_mapping = FileSegmentMapping(
                original_file_id=original_file_id,
                original_file_path=file_path,
                segment_id=str(uuid.uuid4()),
                segment_path=file_path,  # 图片使用原始路径
                segment_index=0,
                start_time=0.0,
                end_time=0.0,
                duration=0.0,
                modality='visual',
                created_at=time.time()
            )
            segments.append(segment_mapping)
            segment_manager.add_segment_mapping(segment_mapping)
            
            # 提取图片元数据
            metadata = _extract_image_metadata(file_path)
            
        elif file_type == 'video':
            # 视频处理和切片
            video_result = media_processor.process_video_with_timestamps(file_path)
            
            if video_result['status'] == 'success':
                metadata = video_result.get('video_info', {})
                
                # 处理视频切片
                chunks = video_result.get('chunks', [])
                for i, chunk in enumerate(chunks):
                    segment_mapping = FileSegmentMapping(
                        original_file_id=original_file_id,
                        original_file_path=file_path,
                        segment_id=str(uuid.uuid4()),
                        segment_path=chunk.get('output_path', f"{file_path}_chunk_{i}.mp4"),
                        segment_index=i,
                        start_time=chunk['start_time'],
                        end_time=chunk['end_time'],
                        duration=chunk['duration'],
                        modality='visual',
                        created_at=time.time()
                    )
                    segments.append(segment_mapping)
                    segment_manager.add_segment_mapping(segment_mapping)
                
                # 处理时间戳信息
                video_timestamps = video_result.get('video_timestamps', [])
                for ts_data in video_timestamps:
                    timestamp_info = TimestampInfo(
                        file_id=original_file_id,
                        segment_id=ts_data['segment_id'],
                        modality=ModalityType(ts_data['modality']),
                        start_time=ts_data['start_time'],
                        end_time=ts_data['end_time'],
                        duration=ts_data['duration'],
                        frame_index=ts_data.get('frame_index'),
                        confidence=ts_data['confidence'],
                        scene_boundary=ts_data.get('scene_boundary', False)
                    )
                    timestamp_infos.append(timestamp_info)
                
                # 处理音频时间戳（如果有）
                audio_timestamps = video_result.get('audio_timestamps', [])
                for ts_data in audio_timestamps:
                    timestamp_info = TimestampInfo(
                        file_id=original_file_id,
                        segment_id=ts_data['segment_id'],
                        modality=ModalityType(ts_data['modality']),
                        start_time=ts_data['start_time'],
                        end_time=ts_data['end_time'],
                        duration=ts_data['duration'],
                        confidence=ts_data['confidence']
                    )
                    timestamp_infos.append(timestamp_info)
            else:
                raise RuntimeError(f"视频处理失败: {video_result.get('error', '未知错误')}")
                
        elif file_type == 'audio':
            # 音频处理和切片
            audio_result = media_processor.process_audio(file_path)
            
            if audio_result['status'] == 'success':
                metadata = audio_result.get('metadata', {})
                
                # 处理音频切片
                audio_segments = audio_result.get('segments', [])
                for i, segment in enumerate(audio_segments):
                    segment_mapping = FileSegmentMapping(
                        original_file_id=original_file_id,
                        original_file_path=file_path,
                        segment_id=str(uuid.uuid4()),
                        segment_path=segment.get('output_path', f"{file_path}_segment_{i}.wav"),
                        segment_index=i,
                        start_time=segment['start_time'],
                        end_time=segment['end_time'],
                        duration=segment['duration'],
                        modality=segment.get('type', 'audio_music'),
                        created_at=time.time()
                    )
                    segments.append(segment_mapping)
                    segment_manager.add_segment_mapping(segment_mapping)
                
                # 生成音频时间戳
                audio_segments_for_ts = [
                    {
                        'type': seg.modality,
                        'start_time': seg.start_time,
                        'end_time': seg.end_time,
                        'confidence': 1.0
                    }
                    for seg in segments
                ]
                
                audio_timestamps = timestamp_processor.process_audio_stream_timestamps(
                    file_path, audio_segments_for_ts
                )
                timestamp_infos.extend(audio_timestamps)
            else:
                raise RuntimeError(f"音频处理失败: {audio_result.get('error', '未知错误')}")
        
        else:
            raise ValueError(f"不支持的文件类型: {file_type}")
        
        # 创建预处理结果
        processing_time = time.time() - start_time
        
        result = PreprocessingResult(
            status='success',
            original_file_id=original_file_id,
            original_file_path=file_path,
            file_type=file_type,
            segments=segments,
            metadata=metadata,
            timestamp_infos=timestamp_infos,
            processing_time=processing_time
        )
        
        logger.info(f"文件预处理完成: {file_path}, 耗时: {processing_time:.2f}s, "
                   f"切片数: {len(segments)}, 时间戳数: {len(timestamp_infos)}")
        
        return result
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"文件预处理失败: {file_path}, 错误: {e}")
        
        return PreprocessingResult(
            status='error',
            original_file_id=original_file_id if 'original_file_id' in locals() else str(uuid.uuid4()),
            original_file_path=file_path,
            file_type=file_type if 'file_type' in locals() else 'unknown',
            segments=[],
            metadata={},
            timestamp_infos=[],
            processing_time=processing_time,
            error_message=str(e)
        )


def batch_preprocess_files(file_paths: List[str], config: Optional[Dict[str, Any]] = None) -> List[PreprocessingResult]:
    """
    批量预处理文件
    
    Args:
        file_paths: 文件路径列表
        config: 可选的配置字典
        
    Returns:
        预处理结果列表
    """
    logger.info(f"开始批量预处理 {len(file_paths)} 个文件")
    
    results = []
    for file_path in file_paths:
        result = preprocess_media_file(file_path, config)
        results.append(result)
    
    success_count = sum(1 for r in results if r.status == 'success')
    error_count = len(results) - success_count
    
    logger.info(f"批量预处理完成: 成功 {success_count} 个, 失败 {error_count} 个")
    
    return results


def get_segment_mapping_manager() -> SegmentMappingManager:
    """
    获取全局切片映射管理器实例
    
    Returns:
        切片映射管理器实例
    """
    global _segment_mapping_manager
    if '_segment_mapping_manager' not in globals():
        global _segment_mapping_manager
        _segment_mapping_manager = SegmentMappingManager()
    return _segment_mapping_manager


def _detect_file_type(file_path: str) -> str:
    """
    自动检测文件类型
    
    Args:
        file_path: 文件路径
        
    Returns:
        文件类型字符串
    """
    ext = Path(file_path).suffix.lower()
    
    # 文件扩展名映射
    type_mapping = {
        # 图像文件
        '.jpg': 'image', '.jpeg': 'image', '.png': 'image', '.bmp': 'image',
        '.gif': 'image', '.tiff': 'image', '.webp': 'image',
        # 视频文件
        '.mp4': 'video', '.avi': 'video', '.mov': 'video', '.mkv': 'video',
        '.wmv': 'video', '.flv': 'video', '.webm': 'video',
        # 音频文件
        '.mp3': 'audio', '.wav': 'audio', '.flac': 'audio', '.aac': 'audio',
        '.ogg': 'audio', '.m4a': 'audio',
        # 文本文件
        '.txt': 'text', '.md': 'text', '.doc': 'text', '.docx': 'text',
        '.pdf': 'text', '.rtf': 'text'
    }
    
    return type_mapping.get(ext, 'unknown')


def _extract_image_metadata(image_path: str) -> Dict[str, Any]:
    """
    提取图片元数据
    
    Args:
        image_path: 图片路径
        
    Returns:
        元数据字典
    """
    try:
        from PIL import Image
        
        with Image.open(image_path) as img:
            metadata = {
                'width': img.width,
                'height': img.height,
                'format': img.format,
                'mode': img.mode,
                'file_size': os.path.getsize(image_path)
            }
            
            # 提取EXIF信息（如果有）
            if hasattr(img, '_getexif') and img._getexif():
                metadata['exif'] = dict(img._getexif())
            
            return metadata
            
    except Exception as e:
        logger.error(f"提取图片元数据失败: {image_path}, 错误: {e}")
        return {
            'file_size': os.path.getsize(image_path),
            'error': str(e)
        }
    
def validate_file(file_path: str) -> Dict[str, Any]:
    """
    验证文件是否可以处理
    
    Args:
        file_path: 文件路径
        
    Returns:
        验证结果字典
    """
    result = {
        'valid': False,
        'file_path': file_path,
        'file_type': None,
        'errors': []
    }
    
    try:
        # 检查文件是否存在
        if not os.path.exists(file_path):
            result['errors'].append("文件不存在")
            return result
        
        # 检查文件是否可读
        if not os.access(file_path, os.R_OK):
            result['errors'].append("文件不可读")
            return result
        
        # 检测文件类型
        file_type = _detect_file_type(file_path)
        result['file_type'] = file_type
        
        # 检查文件类型是否支持
        if file_type == 'unknown':
            result['errors'].append("不支持的文件类型")
            return result
        
        # 检查文件大小
        file_size = os.path.getsize(file_path)
        max_size = 100 * 1024 * 1024  # 默认100MB
        if file_size > max_size:
            result['errors'].append(f"文件过大，最大支持 {max_size / (1024*1024):.1f}MB")
            return result
        
        # 所有检查通过
        result['valid'] = True
        
    except Exception as e:
        result['errors'].append(f"验证过程中出错: {str(e)}")
    
    return result


def get_supported_formats() -> Dict[str, List[str]]:
    """
    获取支持的文件格式
    
    Returns:
        支持的文件格式字典
    """
    return {
        'image': ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp'],
        'video': ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm'],
        'audio': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a'],
        'text': ['.txt', '.md', '.doc', '.docx', '.pdf', '.rtf']
    }


# 示例使用
if __name__ == "__main__":
    # 处理单个文件
    result = preprocess_media_file("path/to/video.mp4")
    print(f"处理结果: {result.status}")
    print(f"原始文件ID: {result.original_file_id}")
    print(f"切片数量: {len(result.segments)}")
    
    # 批量处理文件
    file_paths = ["path/to/file1.jpg", "path/to/file2.mp4", "path/to/file3.mp3"]
    results = batch_preprocess_files(file_paths)
    for result in results:
        print(f"{result.original_file_path}: {result.status}")
    
    # 使用切片映射管理器
    segment_manager = get_segment_mapping_manager()
    
    # 根据原始时间戳查找切片
    segment_info, segment_timestamp = segment_manager.find_segment_by_original_timestamp(
        result.original_file_id, 125.5
    )
    if segment_info:
        print(f"时间戳 125.5s 对应切片: {segment_info.segment_id}, 切片内时间: {segment_timestamp:.2f}s")
    
    # 获取统计信息
    stats = segment_manager.get_statistics()
    print(f"映射统计: {stats}")
    
    # 获取支持的格式
    formats = get_supported_formats()
    print(f"支持的格式: {formats}")