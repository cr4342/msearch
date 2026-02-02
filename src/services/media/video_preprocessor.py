import os
import sys
import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 导入媒体处理通用工具
from src.services.media.media_utils import MediaInfoHelper, calculate_file_hash

# 导入数据层组件
from src.data.extractors.metadata_extractor import MetadataExtractor
from src.data.extractors.frame_extractor import FrameExtractor
from src.data.extractors.audio_extractor import AudioExtractor
from src.data.extractors.scene_detector import SceneDetector


class VideoPreprocessor:
    """视频处理器类"""

    def __init__(
        self,
        config: Dict[str, Any] = None,
        metadata_extractor: Optional[MetadataExtractor] = None,
        frame_extractor: Optional[FrameExtractor] = None,
        audio_extractor: Optional[AudioExtractor] = None,
        scene_detector: Optional[SceneDetector] = None,
    ):
        """
        初始化视频处理器

        Args:
            config: 配置字典
            metadata_extractor: 元数据提取器（依赖注入）
            frame_extractor: 帧提取器（依赖注入）
            audio_extractor: 音频提取器（依赖注入）
            scene_detector: 场景检测器（依赖注入）
        """
        self.config = config or {}
        self.media_info_helper = MediaInfoHelper(self.config)

        # 依赖注入数据层组件
        self.metadata_extractor = metadata_extractor or MetadataExtractor()
        self.frame_extractor = frame_extractor or FrameExtractor()
        self.audio_extractor = audio_extractor or AudioExtractor()

        # 视频处理配置
        media_config = self.config.get("media", {}).get("video", {})
        indexing_config = self.config.get("indexing", {})
        self.short_video_threshold = media_config.get("short_video", {}).get(
            "threshold", indexing_config.get("short_video_threshold", 6.0)
        )
        self.segment_duration = media_config.get("large_video", {}).get(
            "segment_duration", indexing_config.get("video_segment_duration", 5.0)
        )
        scene_config = media_config.get("scene_detection", {})
        self.scene_detection_enabled = scene_config.get("enabled", False)
        self.scene_detection_method = scene_config.get("method", "histogram")
        self.scene_detection_threshold = scene_config.get("threshold", 30.0)
        self.scene_min_scene_length = scene_config.get("min_scene_length", 2.0)

        self.scene_detector = scene_detector or SceneDetector(
            threshold=self.scene_detection_threshold,
            min_scene_length=self.scene_min_scene_length,
        )

        logger.info("VideoPreprocessor initialized")

    def initialize(self) -> bool:
        """
        初始化视频处理器

        Returns:
            是否初始化成功
        """
        try:
            logger.info("VideoPreprocessor initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize VideoPreprocessor: {e}")
            return False

    def process_video(self, video_path: str) -> Dict[str, Any]:
        """
        处理视频文件

        Args:
            video_path: 视频文件路径

        Returns:
            处理结果
        """
        logger.info(f"Processing video: {video_path}")

        try:
            # 使用数据层提取器获取视频元数据
            metadata = self.metadata_extractor.extract(video_path)

            # 获取视频信息
            video_info = self.media_info_helper.get_media_info(video_path)
            duration = video_info.get("duration", 0.0)

            # 确定视频是否为短视频
            is_short_video = duration <= self.short_video_threshold

            # 处理视频：提取关键帧和分段
            segments = self._extract_video_segments(video_path, is_short_video)

            return {
                "status": "success",
                "file_path": video_path,
                "media_type": "video",
                "metadata": metadata,
                "is_short_video": is_short_video,
                "segments": segments,
                "processed_at": time.time(),
            }
        except Exception as e:
            logger.error(f"Failed to process video: {e}")
            return {"status": "error", "error": str(e), "file_path": video_path}

    def _extract_video_segments(
        self, video_path: str, is_short_video: bool
    ) -> List[Dict[str, Any]]:
        """
        提取视频分段

        Args:
            video_path: 视频文件路径
            is_short_video: 是否为短视频

        Returns:
            分段结果
        """
        try:
            # 获取视频信息
            video_info = self.media_info_helper.get_media_info(video_path)
            duration = video_info.get("duration", 0.0)

            segments = []

            if is_short_video:
                # 短视频：统一使用segment_id="full"
                segments.append(
                    {
                        "segment_id": "full",
                        "start_time": 0.0,
                        "end_time": duration,
                        "duration": duration,
                        "is_short_segment": True,
                    }
                )
            else:
                # 长视频：优先使用场景检测分段，否则按固定时长分段
                scene_ranges: List[Tuple[float, float]] = []
                if self.scene_detection_enabled:
                    try:
                        scene_ranges = self._detect_scene_ranges(video_path)
                    except Exception as e:
                        logger.warning(f"场景检测失败，回退到固定分段: {e}")

                if scene_ranges:
                    segments = self._build_segments_from_ranges(scene_ranges, duration)
                else:
                    time_ranges = self._build_time_ranges(duration)
                    segments = self._build_segments_from_ranges(time_ranges, duration)

            return segments
        except Exception as e:
            logger.error(f"Failed to extract video segments: {e}")
            return []

    def _detect_scene_ranges(self, video_path: str) -> List[Tuple[float, float]]:
        """
        使用场景检测器获取场景时间范围

        Args:
            video_path: 视频文件路径

        Returns:
            场景时间范围列表 [(start_time, end_time), ...]
        """
        scenes = self.scene_detector.detect(
            video_path, method=self.scene_detection_method
        )
        ranges: List[Tuple[float, float]] = []
        for scene in scenes:
            start_time, end_time = scene[0], scene[1]
            if end_time > start_time:
                ranges.append((max(0.0, float(start_time)), float(end_time)))
        return ranges

    def _build_time_ranges(self, duration: float) -> List[Tuple[float, float]]:
        """
        按固定时长生成时间范围

        Args:
            duration: 视频总时长

        Returns:
            时间范围列表
        """
        if duration <= 0:
            return []

        ranges: List[Tuple[float, float]] = []
        start_time = 0.0
        while start_time < duration:
            end_time = min(start_time + self.segment_duration, duration)
            ranges.append((start_time, end_time))
            start_time = end_time
        return ranges

    def _build_segments_from_ranges(
        self, ranges: List[Tuple[float, float]], duration: float
    ) -> List[Dict[str, Any]]:
        """
        将时间范围转换为分段结构

        Args:
            ranges: 时间范围列表
            duration: 视频总时长

        Returns:
            分段结果列表
        """
        segments: List[Dict[str, Any]] = []
        segment_index = 0

        for start_time, end_time in ranges:
            start_time = max(0.0, float(start_time))
            end_time = min(float(end_time), duration)
            if end_time <= start_time:
                continue

            current_start = start_time
            while end_time - current_start > self.segment_duration:
                current_end = current_start + self.segment_duration
                segments.append(
                    {
                        "segment_id": f"segment_{segment_index}",
                        "start_time": current_start,
                        "end_time": current_end,
                        "duration": current_end - current_start,
                        "is_short_segment": False,
                    }
                )
                segment_index += 1
                current_start = current_end

            segments.append(
                {
                    "segment_id": f"segment_{segment_index}",
                    "start_time": current_start,
                    "end_time": end_time,
                    "duration": end_time - current_start,
                    "is_short_segment": False,
                }
            )
            segment_index += 1

        return segments

    def extract_audio_from_video(self, video_path: str, output_path: str = None) -> str:
        """
        从视频中提取音频

        Args:
            video_path: 视频文件路径
            output_path: 音频输出路径

        Returns:
            音频文件路径
        """
        try:
            logger.info(f"Extracting audio from video: {video_path}")

            # 使用数据层的音频提取器
            audio_path = self.audio_extractor.extract(video_path, output_path)

            if audio_path:
                logger.info(f"Audio extracted to: {audio_path}")
            else:
                logger.error("Failed to extract audio")

            return audio_path
        except Exception as e:
            logger.error(f"Failed to extract audio from video: {e}")
            return ""

    def slice_video(
        self,
        video_path: str,
        start_time: float,
        end_time: float,
        output_path: str = None,
    ) -> str:
        """
        切片视频

        Args:
            video_path: 视频文件路径
            start_time: 开始时间（秒）
            end_time: 结束时间（秒）
            output_path: 输出路径

        Returns:
            切片后的视频路径
        """
        try:
            logger.info(
                f"Slicing video: {video_path} from {start_time}s to {end_time}s"
            )

            # 如果未指定输出路径，则使用视频路径生成
            if not output_path:
                video_name = Path(video_path).stem
                output_path = (
                    f"{video_name}_slice_{int(start_time)}_{int(end_time)}.mp4"
                )

            # 使用ffmpeg切片视频
            cmd = [
                "ffmpeg",
                "-i",
                video_path,
                "-ss",
                str(start_time),  # 开始时间
                "-t",
                str(end_time - start_time),  # 持续时间
                "-c:v",
                "libx264",  # 视频编码器
                "-c:a",
                "aac",  # 音频编码器
                "-y",  # 覆盖输出文件
                output_path,
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                logger.error(f"FFmpeg failed: {result.stderr}")
                return ""

            logger.info(f"Video sliced to: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Failed to slice video: {e}")
            return ""

    def has_media_value(self, file_path: str) -> bool:
        """
        判断视频文件是否有价值

        Args:
            file_path: 文件路径

        Returns:
            是否有价值
        """
        return self.media_info_helper.has_media_value(file_path)

    def get_media_info(self, file_path: str) -> Dict[str, Any]:
        """
        获取视频媒体信息

        Args:
            file_path: 文件路径

        Returns:
            媒体信息
        """
        return self.media_info_helper.get_media_info(file_path)

    def calculate_hash(self, file_path: str) -> str:
        """
        计算文件哈希值

        Args:
            file_path: 文件路径

        Returns:
            文件哈希值
        """
        return calculate_file_hash(file_path)

    def get_video_frames(self, video_path: str, max_frames: int = 3) -> List[Any]:
        """
        从视频中提取帧并返回PIL Images列表

        用于视频向量化，将视频帧转换为PIL Images传递给模型

        Args:
            video_path: 视频文件路径
            max_frames: 最大返回帧数，默认3帧

        Returns:
            PIL Images列表
        """
        import cv2
        from PIL import Image

        frames = []

        try:
            if not os.path.exists(video_path):
                logger.error(f"Video file not found: {video_path}")
                return frames

            # 获取视频信息
            video_info = self.media_info_helper.get_media_info(video_path)
            duration = video_info.get("duration", 0.0)

            # 处理视频获取分段
            is_short_video = duration <= self.short_video_threshold
            segments = self._extract_video_segments(video_path, is_short_video)

            cap = cv2.VideoCapture(video_path)

            # 从每个分段提取一帧（在中间位置）
            for segment in segments[:max_frames]:
                start_time = segment.get("start_time", 0)
                seg_duration = segment.get("duration", 0)
                frame_time = start_time + seg_duration / 2  # 分段中间位置

                # 定位到指定时间
                cap.set(cv2.CAP_PROP_POS_MSEC, frame_time * 1000)
                ret, frame = cap.read()

                if ret:
                    # 将BGR转换为RGB，然后转换为PIL Image
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    pil_image = Image.fromarray(frame_rgb)
                    frames.append(pil_image)
                    logger.debug(
                        f"Video frame extracted: {video_path} @ {frame_time:.2f}s"
                    )

            cap.release()

            if frames:
                logger.info(f"Extracted {len(frames)} frames from {video_path}")
            else:
                logger.warning(f"No frames extracted from {video_path}")

            return frames

        except Exception as e:
            logger.error(f"Failed to extract frames from video: {e}")
            return frames
