"""
视频场景检测器
使用FFmpeg进行视频场景变化检测
"""

import subprocess
import re
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class VideoSceneDetector:
    """视频场景检测器：使用FFmpeg检测视频场景变化"""
    
    def __init__(self, scene_threshold: float = 0.3):
        """
        初始化场景检测器
        
        Args:
            scene_threshold: 场景检测阈值（0-1），值越大检测越严格
        """
        self.scene_threshold = scene_threshold
        
        logger.info(f"VideoSceneDetector initialized with threshold {scene_threshold}")
    
    def detect_scenes(self, video_path: str) -> List[Tuple[int, float, float]]:
        """
        检测视频场景变化点
        
        Args:
            video_path: 视频文件路径
        
        Returns:
            场景变化点列表，每个元素为 (帧号, 时间戳, 场景分数)
        """
        logger.info(f"Detecting scenes in video: {video_path}")
        
        # 构建FFmpeg命令
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-vf', f'select=\'gt(scene,{self.scene_threshold})\',metadata=print:file=pipe:1',
            '-f', 'null',
            '-'
        ]
        
        try:
            # 执行FFmpeg命令
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            
            # 解析输出
            scenes = self._parse_scene_output(result.stderr)
            
            logger.info(f"Detected {len(scenes)} scenes in video: {video_path}")
            return scenes
            
        except Exception as e:
            logger.error(f"Error detecting scenes in video {video_path}: {e}")
            return []
    
    def _parse_scene_output(self, output: str) -> List[Tuple[int, float, float]]:
        """
        解析场景检测输出
        
        Args:
            output: FFmpeg输出
        
        Returns:
            场景变化点列表
        """
        scenes = []
        
        # 正则表达式匹配场景信息
        pattern = r'frame:(\d+)\s+pts:(\d+)\s+pts_time:([\d.]+)\s+tag:lavfi.scene_score=([\d.]+)'
        
        for match in re.finditer(pattern, output):
            frame_num = int(match.group(1))
            pts = int(match.group(2))
            pts_time = float(match.group(3))
            scene_score = float(match.group(4))
            
            scenes.append((frame_num, pts_time, scene_score))
        
        return scenes
    
    def get_scene_segments(self, video_path: str, max_duration: float = 5.0) -> List[Tuple[float, float]]:
        """
        获取视频场景片段
        
        Args:
            video_path: 视频文件路径
            max_duration: 最大片段时长（秒）
        
        Returns:
            片段列表，每个元素为 (开始时间, 结束时间)
        """
        logger.info(f"Getting scene segments for video: {video_path}")
        
        # 检测场景变化点
        scenes = self.detect_scenes(video_path)
        
        # 获取视频总时长
        duration = self._get_video_duration(video_path)
        
        # 提取时间戳
        timestamps = [0.0] + [scene[1] for scene in scenes] + [duration]
        
        # 生成片段
        segments = []
        for i in range(len(timestamps) - 1):
            start_time = timestamps[i]
            end_time = timestamps[i + 1]
            
            # 如果片段时长超过最大时长，进行分割
            while end_time - start_time > max_duration:
                split_time = start_time + max_duration
                segments.append((start_time, split_time))
                start_time = split_time
            
            segments.append((start_time, end_time))
        
        logger.info(f"Generated {len(segments)} segments for video: {video_path}")
        return segments
    
    def _get_video_duration(self, video_path: str) -> float:
        """
        获取视频总时长
        
        Args:
            video_path: 视频文件路径
        
        Returns:
            视频时长（秒）
        """
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            video_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            duration = float(result.stdout.strip())
            return duration
        except Exception as e:
            logger.error(f"Error getting video duration for {video_path}: {e}")
            return 0.0
    
    def get_keyframes(self, video_path: str) -> List[float]:
        """
        获取关键帧时间戳
        
        Args:
            video_path: 视频文件路径
        
        Returns:
            关键帧时间戳列表
        """
        logger.info(f"Getting keyframes for video: {video_path}")
        
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'frame=pkt_pts_time,key_frame',
            '-of', 'csv=p=0',
            video_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # 解析关键帧
            keyframes = []
            for line in result.stdout.split('\n'):
                if not line:
                    continue
                parts = line.split(',')
                if len(parts) >= 2 and parts[1].strip() == '1':
                    keyframes.append(float(parts[0]))
            
            logger.info(f"Found {len(keyframes)} keyframes in video: {video_path}")
            return keyframes
            
        except Exception as e:
            logger.error(f"Error getting keyframes for video {video_path}: {e}")
            return []
    
    def set_scene_threshold(self, threshold: float) -> None:
        """
        设置场景检测阈值
        
        Args:
            threshold: 场景检测阈值（0-1）
        """
        if 0 <= threshold <= 1:
            self.scene_threshold = threshold
            logger.info(f"Scene threshold set to {threshold}")
        else:
            logger.warning(f"Invalid scene threshold: {threshold}. Must be between 0 and 1.")