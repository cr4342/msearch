"""
视频切片管理器
改进时序定位，明确定义切片参数配置和时间映射
"""

import os
import subprocess
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class VideoSegmentConfig:
    """视频切片配置"""

    def __init__(self, config: Dict[str, Any]):
        # 基础切片参数
        self.max_segment_duration = config.get(
            "max_segment_duration", 5.0
        )  # 最大切片时长（秒）
        self.min_segment_duration = config.get(
            "min_segment_duration", 0.5
        )  # 最小切片时长（秒）
        self.segment_overlap = config.get("segment_overlap", 0.0)  # 切片重叠时长（秒）

        # 场景检测参数
        self.scene_detect_threshold = config.get(
            "scene_detect_threshold", 0.3
        )  # 场景变化阈值
        self.scene_detect_min_duration = config.get(
            "scene_detect_min_duration", 1.0
        )  # 最小场景时长

        # 时间映射参数
        self.timestamp_precision = config.get(
            "timestamp_precision", 0.1
        )  # 时间戳精度（秒）

        # 短视频处理
        self.short_video_threshold = config.get(
            "short_video_threshold", 6.0
        )  # 短视频阈值
        self.short_video_handling = config.get(
            "short_video_handling", "full_process"
        )  # 短视频处理方式

        # 分辑率和格式参数
        self.max_resolution_short_edge = config.get(
            "max_resolution_short_edge", 960
        )  # 短边最大分辑率
        self.output_format = config.get("output_format", "mp4")  # 输出格式
        self.video_codec = config.get("video_codec", "libx264")  # 视频编码器
        self.audio_codec = config.get("audio_codec", "aac")  # 音频编码器

        # 启用场景检测
        self.scene_detect_enabled = config.get("scene_detect_enabled", True)


class VideoSegmentManager:
    """视频切片管理器 - 改进时序定位"""

    def __init__(self, config: VideoSegmentConfig):
        self.config = config

    def segment_video(self, video_path: str) -> List[Dict[str, Any]]:
        """
        Video segmentation method, returns slice list with time mapping

        Args:
            video_path: Video file path

        Returns:
            Slice list, each slice contains time mapping information
        """
        try:
            video_duration = self._get_video_duration(video_path)
            logger.info(
                f"Start processing video: {video_path}, duration: {video_duration:.2f}s"
            )

            if video_duration <= self.config.short_video_threshold:
                # Short video processing: treat entire video as one segment
                segment = {
                    "start_time": 0.0,
                    "end_time": video_duration,
                    "duration": video_duration,
                    "segment_id": f"full_{os.path.basename(video_path)}",
                    "is_full_video": True,
                    "timestamp_map": self._generate_timestamp_map(0.0, video_duration),
                    "scene_info": None,
                }
                logger.info(f"Short video processing completed: {video_path}")
                return [segment]
            else:
                # Long video processing: slice based on configuration
                if self.config.scene_detect_enabled:
                    segments = self._scene_based_segmentation(video_path)
                else:
                    segments = self._time_based_segmentation(video_path, video_duration)

                logger.info(
                    f"Video segmentation completed: {video_path}, generated {len(segments)} segments"
                )
                return segments

        except Exception as e:
            logger.error(f"Video segmentation failed {video_path}: {e}")
            raise

    def _get_video_duration(self, video_path: str) -> float:
        """Get video duration"""
        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "quiet",
                    "-show_entries",
                    "format=duration",
                    "-of",
                    "csv=p=0",
                    video_path,
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            duration = float(result.stdout.strip())
            return duration
        except subprocess.CalledProcessError:
            # If ffprobe fails, try alternative method to get duration
            try:
                import cv2

                cap = cv2.VideoCapture(video_path)
                fps = cap.get(cv2.CAP_PROP_FPS)
                frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
                duration = frame_count / fps if fps > 0 else 0
                cap.release()
                return duration
            except:
                raise ValueError(f"Cannot get video duration: {video_path}")

    def _generate_timestamp_map(
        self, start_time: float, end_time: float
    ) -> Dict[str, float]:
        """
        Generate timestamp mapping for precise time positioning

        Args:
            start_time: Start time
            end_time: End time

        Returns:
            Timestamp mapping dictionary
        """
        timestamp_map = {}
        current_time = start_time

        while current_time <= end_time:
            # Generate mapping based on timestamp precision
            frame_time = round(current_time, 1)  # Use configured timestamp precision
            frame_key = f"frame_{int(frame_time * 10)}"  # Use 10x precision as key
            timestamp_map[frame_key] = frame_time
            current_time += self.config.timestamp_precision

        return timestamp_map

    def _scene_based_segmentation(self, video_path: str) -> List[Dict[str, Any]]:
        """Scene-based video segmentation"""
        try:
            # Use FFmpeg for scene detection
            scene_detect_cmd = [
                "ffmpeg",
                "-i",
                video_path,
                "-vf",
                f"scene_detect=threshold={self.config.scene_detect_threshold}",
                "-f",
                "csv",
                "-",
            ]

            result = subprocess.run(scene_detect_cmd, capture_output=True, text=True)

            # Parse scene detection results
            scenes = self._parse_scene_detection_result(result.stdout)

            # Create slices based on scene boundaries
            segments = []
            for i, (start_time, end_time) in enumerate(scenes):
                # Ensure slice duration is within reasonable range
                if end_time - start_time > self.config.max_segment_duration:
                    # If scene is too long, split by time
                    sub_segments = self._split_long_segment(start_time, end_time)
                    segments.extend(sub_segments)
                else:
                    segment = {
                        "start_time": start_time,
                        "end_time": end_time,
                        "duration": end_time - start_time,
                        "segment_id": f"scene_{i:04d}_{os.path.basename(video_path)}",
                        "is_full_video": False,
                        "timestamp_map": self._generate_timestamp_map(
                            start_time, end_time
                        ),
                        "scene_info": {"scene_index": i, "is_scene_boundary": True},
                    }
                    segments.append(segment)

            return segments

        except Exception as e:
            logger.warning(f"Scene detection failed, fallback to time slicing: {e}")
            # Fall back to time slicing
            video_duration = self._get_video_duration(video_path)
            return self._time_based_segmentation(video_path, video_duration)

    def _parse_scene_detection_result(self, result: str) -> List[tuple]:
        """Parse scene detection results"""
        scenes = []
        lines = result.strip().split("\n")

        for line in lines:
            if line.startswith("frame,"):
                continue  # Skip title row

            parts = line.split(",")
            if len(parts) >= 3:
                try:
                    frame_time = float(parts[1])  # Timestamp
                    scene_score = float(parts[2])  # Scene change score

                    # If scene score exceeds threshold, consider it a scene boundary
                    if scene_score > self.config.scene_detect_threshold:
                        if scenes:
                            # End previous scene
                            last_scene_end = scenes[-1][1]
                            if (
                                frame_time - last_scene_end
                                >= self.config.scene_detect_min_duration
                            ):
                                # Ensure previous scene reaches minimum duration
                                scenes[-1] = (scenes[-1][0], frame_time)
                            else:
                                # If too short, extend scene
                                scenes[-1] = (scenes[-1][0], frame_time)
                        else:
                            # First scene
                            scenes.append((0.0, frame_time))
                except (ValueError, IndexError):
                    continue

        # Add last scene to end of video
        if scenes:
            video_duration = self._get_video_duration(video_path)
            if scenes[-1][1] < video_duration:
                scenes[-1] = (scenes[-1][0], video_duration)
        else:
            # If no scene changes detected, use entire video
            video_duration = self._get_video_duration(video_path)
            scenes.append((0.0, video_duration))

        return scenes

    def _time_based_segmentation(
        self, video_path: str, video_duration: float
    ) -> List[Dict[str, Any]]:
        """Time-based video segmentation"""
        segments = []

        current_time = 0.0
        segment_index = 0

        while current_time < video_duration:
            # Calculate slice end time
            end_time = min(
                current_time + self.config.max_segment_duration, video_duration
            )

            # Ensure slice duration is not below minimum
            if (
                end_time - current_time < self.config.min_segment_duration
                and end_time < video_duration
            ):
                # If current slice is too short and not the last one, skip to next appropriate position
                current_time = end_time
                continue

            segment = {
                "start_time": current_time,
                "end_time": end_time,
                "duration": end_time - current_time,
                "segment_id": f"time_{segment_index:04d}_{os.path.basename(video_path)}",
                "is_full_video": False,
                "timestamp_map": self._generate_timestamp_map(current_time, end_time),
                "scene_info": {
                    "scene_index": segment_index,
                    "is_scene_boundary": False,
                },
            }

            segments.append(segment)
            current_time = end_time
            segment_index += 1

        return segments

    def _split_long_segment(
        self, start_time: float, end_time: float
    ) -> List[Dict[str, Any]]:
        """Split long segment by time"""
        sub_segments = []
        current_time = start_time
        sub_index = 0

        while current_time < end_time:
            sub_end_time = min(
                current_time + self.config.max_segment_duration, end_time
            )

            segment = {
                "start_time": current_time,
                "end_time": sub_end_time,
                "duration": sub_end_time - current_time,
                "segment_id": f"sub_{int(start_time * 1000):08d}_{sub_index:03d}",
                "is_full_video": False,
                "timestamp_map": self._generate_timestamp_map(
                    current_time, sub_end_time
                ),
                "scene_info": {
                    "scene_index": int(start_time * 1000),  # Original scene index
                    "is_sub_segment": True,
                    "sub_index": sub_index,
                },
            }

            sub_segments.append(segment)
            current_time = sub_end_time
            sub_index += 1

        return sub_segments

    def create_segment_file(
        self, video_path: str, start_time: float, end_time: float, output_path: str
    ) -> bool:
        """
        Create video slice file

        Args:
            video_path: Original video path
            start_time: Start time
            end_time: End time
            output_path: Output path

        Returns:
            Success or not
        """
        try:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Use FFmpeg to create video slice
            cmd = [
                "ffmpeg",
                "-ss",
                str(start_time),  # Start time
                "-to",
                str(end_time),  # End time
                "-i",
                video_path,  # Input file
                "-c:v",
                self.config.video_codec,  # Video encoder
                "-c:a",
                self.config.audio_codec,  # Audio encoder
                "-y",  # Overwrite output file
                output_path,
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0 and os.path.exists(output_path):
                logger.info(f"Video slice created successfully: {output_path}")
                return True
            else:
                logger.error(f"Video slice creation failed: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Error creating video slice: {e}")
            return False

    def get_segment_info(self, segment: Dict[str, Any]) -> Dict[str, Any]:
        """Get slice detailed information"""
        return {
            "segment_id": segment["segment_id"],
            "start_time": segment["start_time"],
            "end_time": segment["end_time"],
            "duration": segment["duration"],
            "is_full_video": segment.get("is_full_video", False),
            "timestamp_map_count": len(segment.get("timestamp_map", {})),
            "scene_info": segment.get("scene_info"),
        }

    def validate_config(self) -> bool:
        """Validate configuration validity"""
        if self.config.max_segment_duration <= 0:
            logger.error("Maximum slice duration must be greater than 0")
            return False

        if self.config.min_segment_duration <= 0:
            logger.error("Minimum slice duration must be greater than 0")
            return False

        if self.config.min_segment_duration > self.config.max_segment_duration:
            logger.error(
                "Minimum slice duration cannot be greater than maximum slice duration"
            )
            return False

        if self.config.timestamp_precision <= 0:
            logger.error("Timestamp precision must be greater than 0")
            return False

        if (
            self.config.scene_detect_threshold < 0
            or self.config.scene_detect_threshold > 1
        ):
            logger.error("Scene detection threshold must be between 0-1")
            return False

        return True
