import os
import sys
import logging
import time
import librosa
import soundfile as sf
import numpy as np
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 导入媒体处理通用工具
from src.services.media.media_utils import MediaInfoHelper, calculate_file_hash


class AudioPreprocessor:
    """音频处理器类"""

    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化音频处理器

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.media_info_helper = MediaInfoHelper(self.config)

        processing_audio = self.config.get("processing", {}).get("audio", {})
        self.target_sample_rate = processing_audio.get("sample_rate", 48000)
        self.target_channels = processing_audio.get("channels", 1)
        self.target_format = processing_audio.get("format", "wav")
        self.min_duration = processing_audio.get("min_duration", 3.0)

        if str(self.target_format).lower() != "wav":
            logger.warning("CLAP输入要求WAV格式，已强制使用wav输出")
            self.target_format = "wav"

        logger.info("AudioPreprocessor initialized")

    def initialize(self) -> bool:
        """
        初始化音频处理器

        Returns:
            是否初始化成功
        """
        try:
            logger.info("AudioPreprocessor initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize AudioPreprocessor: {e}")
            return False

    def process_audio(
        self, audio_path: str, output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        处理音频文件

        按照设计文档要求：
        1. 价值判断：音频时长超过3秒才具有检索价值
        2. 音频预处理：统一采样率48kHz，转换为单声道，保存为WAV格式

        Args:
            audio_path: 音频文件路径
            output_path: 可选的输出路径，如果不提供则使用临时文件

        Returns:
            处理结果字典
        """
        logger.info(f"Processing audio: {audio_path}")

        try:
            # 检查文件是否存在
            if not os.path.exists(audio_path):
                return {
                    "status": "error",
                    "error": f"File not found: {audio_path}",
                    "file_path": audio_path,
                }

            # 1. 价值判断：获取音频时长
            try:
                audio_info = self.media_info_helper.get_media_info(audio_path)
                duration = audio_info.get("duration", 0)

                if duration < self.min_duration:
                    logger.info(
                        f"Audio too short ({duration}s < {self.min_duration}s), skipping"
                    )
                    return {
                        "status": "skipped",
                        "reason": "audio_too_short",
                        "file_path": audio_path,
                        "duration": duration,
                    }
            except Exception as e:
                logger.error(f"Failed to get audio info: {e}")
                return {
                    "status": "error",
                    "error": f"Failed to get audio info: {e}",
                    "file_path": audio_path,
                }

            # 2. 音频预处理
            try:
                processed_audio_path = self._preprocess_audio(audio_path, output_path)
                if not processed_audio_path:
                    return {
                        "status": "error",
                        "error": "Audio preprocessing failed",
                        "file_path": audio_path,
                    }
            except Exception as e:
                logger.error(f"Audio preprocessing failed: {e}")
                return {
                    "status": "error",
                    "error": f"Audio preprocessing failed: {e}",
                    "file_path": audio_path,
                }

            # 3. 使用CLAP进行音频分类（MUSIC、SPEECH、MIXED、SILENCE、UNKNOWN）
            try:
                audio_type = self._classify_audio_type(processed_audio_path)
            except Exception as e:
                logger.error(f"Audio classification failed: {e}")
                audio_type = "UNKNOWN"

            return {
                "status": "success",
                "file_path": audio_path,
                "processed_path": processed_audio_path,
                "media_type": "audio",
                "audio_type": audio_type,  # MUSIC、SPEECH、MIXED、SILENCE、UNKNOWN
                "duration": duration,
                "sample_rate": self.target_sample_rate,
                "channels": self.target_channels,
                "format": self.target_format,
                "metadata": audio_info,
                "processed_at": time.time(),
            }
        except Exception as e:
            logger.error(f"Failed to process audio: {e}")
            import traceback

            traceback.print_exc()
            return {"status": "error", "error": str(e), "file_path": audio_path}

    def _preprocess_audio(
        self, audio_path: str, output_path: Optional[str] = None
    ) -> Optional[str]:
        """
        音频预处理

        按照设计文档要求：
        - 统一采样率为48kHz（CLAP要求）
        - 转换为单声道
        - 保存为WAV格式

        Args:
            audio_path: 原始音频文件路径
            output_path: 输出文件路径

        Returns:
            处理后的音频文件路径
        """
        try:
            # 如果未指定输出路径，生成临时文件
            if not output_path:
                import tempfile

                temp_dir = tempfile.gettempdir()
                file_name = Path(audio_path).stem
                output_ext = str(self.target_format).lower()
                output_path = os.path.join(
                    temp_dir, f"{file_name}_processed.{output_ext}"
                )

            # 加载音频（使用librosa）
            audio_data, sr = librosa.load(audio_path, sr=None, mono=False)

            # 转换为单声道
            if self.target_channels == 1 and len(audio_data.shape) > 1:
                audio_data = librosa.to_mono(audio_data)

            # 重采样到48kHz
            if sr != self.target_sample_rate:
                audio_data = librosa.resample(
                    audio_data, orig_sr=sr, target_sr=self.target_sample_rate
                )

            # 保存为WAV格式
            sf.write(output_path, audio_data, self.target_sample_rate)

            logger.info(f"Audio preprocessed: {audio_path} -> {output_path}")
            logger.info(
                f"  Original: {sr}Hz, {audio_data.shape if len(audio_data.shape) > 1 else 'mono'}"
            )
            logger.info(f"  Processed: {self.target_sample_rate}Hz, mono, WAV")

            return output_path
        except Exception as e:
            logger.error(f"Failed to preprocess audio: {e}")
            return None

    def _classify_audio_type(self, audio_path: str) -> str:
        """
        使用音频特征对音频进行分类

        Args:
            audio_path: 音频文件路径

        Returns:
            音频类型: 'MUSIC', 'SPEECH', 'MIXED', 'SILENCE', 'UNKNOWN'
        """
        try:
            # 加载音频
            y, sr = librosa.load(audio_path, sr=22050)

            # 计算音频特征
            # 1. 零交叉率（Zero Crossing Rate）
            zcr = librosa.feature.zero_crossing_rate(y)[0]
            mean_zcr = zcr.mean()

            # 2. 频谱质心（Spectral Centroid）
            spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            mean_centroid = spectral_centroid.mean()

            # 3. MFCC特征
            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            mfcc_mean = mfccs.mean(axis=1)

            # 4. 频谱带宽（Spectral Bandwidth）
            spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]
            mean_bandwidth = spectral_bandwidth.mean()

            # 基于特征进行简单分类
            # 语音通常具有较高的零交叉率和较低的频谱质心
            # 音乐通常具有较低的零交叉率和较高的频谱质心

            if mean_zcr < 0.01:
                # 极低零交叉率，可能是静音
                return "SILENCE"
            elif mean_zcr > 0.15 and mean_centroid < 2000:
                # 高零交叉率，低频谱质心，可能是语音
                return "SPEECH"
            elif mean_zcr < 0.05 and mean_centroid > 3000 and mean_bandwidth > 1500:
                # 低零交叉率，高频谱质心，高频谱带宽，可能是音乐
                return "MUSIC"
            elif mean_zcr > 0.05 and mean_zcr < 0.15 and mean_centroid > 2000:
                # 中等特征，可能是混合音频
                return "MIXED"
            else:
                # 其他情况
                return "UNKNOWN"

        except Exception as e:
            logger.error(f"Failed to classify audio type: {e}")
            return "UNKNOWN"

    def has_media_value(self, file_path: str) -> bool:
        """
        判断音频文件是否有价值

        Args:
            file_path: 文件路径

        Returns:
            是否有价值
        """
        try:
            audio_info = self.media_info_helper.get_media_info(file_path)
            duration = audio_info.get("duration", 0)
            return duration >= self.min_duration
        except Exception as e:
            logger.error(f"Failed to check media value: {e}")
            return False

    def get_media_info(self, file_path: str) -> Dict[str, Any]:
        """
        获取音频媒体信息

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

    def get_preprocessed_audio_bytes(self, audio_path: str) -> Optional[bytes]:
        """
        获取预处理后的音频数据（bytes格式）

        用于直接传递给模型的audio_embed方法

        Args:
            audio_path: 原始音频文件路径

        Returns:
            预处理后的音频bytes，失败返回None
        """
        try:
            processed_path = self._preprocess_audio(audio_path, None)
            if processed_path:
                with open(processed_path, "rb") as f:
                    return f.read()
            return None
        except Exception as e:
            logger.error(f"Failed to get preprocessed audio bytes: {e}")
            return None
