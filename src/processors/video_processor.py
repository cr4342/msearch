"""
视频处理器 - 处理视频文件的场景检测、关键帧提取和时间戳管理
"""
import os
import cv2
import numpy as np
from typing import Dict, Any, List, Tuple
import logging
from src.processors.timestamp_processor import TimestampProcessor

logger = logging.getLogger(__name__)


class VideoProcessor:
    """视频处理器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化视频处理器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.target_size = config.get('processing.video.target_size', 224)  # CLIP模型标准输入尺寸
        self.max_resolution = config.get('processing.video.max_resolution', (1280, 720))
        self.scene_threshold = config.get('processing.video.scene_threshold', 0.3)
        self.frame_interval = config.get('processing.video.frame_interval', 2.0)  # 秒
        self.timestamp_processor = TimestampProcessor()
    
    async def process_video(self, video_path: str) -> Dict[str, Any]:
        """
        处理视频文件
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            处理结果字典
        """
        try:
            logger.debug(f"开始处理视频: {video_path}")
            
            # 1. 提取视频元数据
            metadata = self._extract_metadata(video_path)
            
            # 2. 场景检测
            scenes = self._detect_scenes(video_path, metadata)
            
            # 3. 关键帧提取
            keyframes = self._extract_keyframes(video_path, scenes, metadata)
            
            # 4. 音频流分离（如果需要）
            # audio_segments = self._extract_audio(video_path)
            
            logger.debug(f"视频处理完成: {video_path}, 提取关键帧数: {len(keyframes)}")
            
            return {
                'status': 'success',
                'metadata': metadata,
                'scenes': scenes,
                'keyframes': keyframes,
                'file_path': video_path
            }
            
        except Exception as e:
            logger.error(f"视频处理失败: {video_path}, 错误: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'file_path': video_path
            }
    
    def _extract_metadata(self, video_path: str) -> Dict[str, Any]:
        """
        提取视频元数据
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            元数据字典
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"视频文件不存在: {video_path}")
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"无法打开视频文件: {video_path}")
        
        # 获取视频属性
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        cap.release()
        
        duration = frame_count / fps if fps > 0 else 0
        
        return {
            'width': width,
            'height': height,
            'fps': fps,
            'frame_count': frame_count,
            'duration': duration,
            'resolution': f"{width}x{height}"
        }
    
    def _detect_scenes(self, video_path: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        检测视频场景变化
        
        Args:
            video_path: 视频文件路径
            metadata: 视频元数据
            
        Returns:
            场景列表
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"无法打开视频文件: {video_path}")
        
        scenes = []
        prev_frame = None
        scene_start_frame = 0
        fps = metadata['fps']
        
        frame_idx = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # 每隔一定帧数进行场景检测以提高性能
            if frame_idx % int(fps/2) == 0:  # 每0.5秒检测一次
                # 转换为灰度图并计算直方图
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                if prev_frame is not None:
                    # 计算帧间差异
                    diff = cv2.absdiff(prev_frame, gray)
                    diff_score = np.mean(diff) / 255.0
                    
                    # 如果差异超过阈值，认为是场景变化
                    if diff_score > self.scene_threshold:
                        scene_end_frame = frame_idx
                        scene_duration = (scene_end_frame - scene_start_frame) / fps
                        
                        scenes.append({
                            'start_frame': scene_start_frame,
                            'end_frame': scene_end_frame,
                            'start_time': scene_start_frame / fps,
                            'end_time': scene_end_frame / fps,
                            'duration': scene_duration,
                            'confidence': diff_score
                        })
                        
                        scene_start_frame = frame_idx
                
                prev_frame = gray.copy()
            
            frame_idx += 1
        
        # 添加最后一个场景
        if scene_start_frame < frame_idx:
            scene_duration = (frame_idx - scene_start_frame) / fps
            scenes.append({
                'start_frame': scene_start_frame,
                'end_frame': frame_idx,
                'start_time': scene_start_frame / fps,
                'end_time': frame_idx / fps,
                'duration': scene_duration,
                'confidence': 0.5  # 默认置信度
            })
        
        cap.release()
        return scenes
    
    def _extract_keyframes(self, video_path: str, scenes: List[Dict[str, Any]], 
                          metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        从场景中提取关键帧
        
        Args:
            video_path: 视频文件路径
            scenes: 场景列表
            metadata: 视频元数据
            
        Returns:
            关键帧列表
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"无法打开视频文件: {video_path}")
        
        keyframes = []
        fps = metadata['fps']
        
        for scene in scenes:
            start_frame = scene['start_frame']
            end_frame = scene['end_frame']
            
            # 计算抽帧间隔（基于配置的秒数）
            frame_interval_frames = int(self.frame_interval * fps)
            if frame_interval_frames < 1:
                frame_interval_frames = 1
            
            # 在场景内按间隔抽帧
            for frame_idx in range(start_frame, min(end_frame, metadata['frame_count']), frame_interval_frames):
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                if ret:
                    # 处理帧
                    processed_frame = self._process_frame(frame)
                    
                    # 计算时间戳
                    timestamp = frame_idx / fps
                    
                    keyframes.append({
                        'frame_index': frame_idx,
                        'timestamp': timestamp,
                        'frame_data': processed_frame,
                        'scene_id': scenes.index(scene),
                        'resolution': processed_frame.shape[:2]
                    })
        
        cap.release()
        return keyframes
    
    def _process_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        处理单个视频帧
        
        Args:
            frame: 原始帧数据
            
        Returns:
            处理后的帧数据
        """
        # 调整尺寸
        height, width = frame.shape[:2]
        max_width, max_height = self.max_resolution
        
        if width > max_width or height > max_height:
            scale_x = max_width / width
            scale_y = max_height / height
            scale = min(scale_x, scale_y)
            
            new_width = int(width * scale)
            new_height = int(height * scale)
            frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)
        
        # 调整到目标尺寸 (224x224)
        processed_frame = cv2.resize(frame, (self.target_size, self.target_size), interpolation=cv2.INTER_LINEAR)
        
        # 转换为RGB格式
        rgb_frame = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
        
        # 归一化到[0, 1]范围
        normalized_frame = rgb_frame.astype(np.float32) / 255.0
        
        return normalized_frame
    
    def _extract_audio(self, video_path: str) -> List[Dict[str, Any]]:
        """
        从视频中提取音频流（占位方法）
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            音频片段列表
        """
        # 这里应该调用音频处理器来处理音频流
        # 暂时返回空列表
        return []


# 示例使用
if __name__ == "__main__":
    # 配置示例
    config = {
        'processing.video.target_size': 224,
        'processing.video.max_resolution': (1280, 720),
        'processing.video.scene_threshold': 0.3,
        'processing.video.frame_interval': 2.0
    }
    
    # 创建处理器实例
    processor = VideoProcessor(config)
    
    # 处理视频 (需要实际的视频文件路径)
    # result = processor.process_video("path/to/video.mp4")
    # print(result)