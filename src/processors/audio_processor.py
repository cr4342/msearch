"""
音频处理器 - 处理音频文件的内容分类、特征提取和时间戳管理
实现音频流处理、内容分类和多模态时间同步
"""
import os
import librosa
import numpy as np
import subprocess
import json
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import logging
from dataclasses import dataclass
from enum import Enum

from src.processors.timestamp_processor import (
    TimestampProcessor, TimestampInfo, ModalityType
)

logger = logging.getLogger(__name__)


class AudioContentType(Enum):
    """音频内容类型"""
    MUSIC = "music"
    SPEECH = "speech"
    NOISE = "noise"
    MIXED = "mixed"


@dataclass
class AudioMetadata:
    """音频元数据"""
    duration: float
    sample_rate: int
    channels: int
    bitrate: int
    format: str
    has_speech: bool
    has_music: bool


@dataclass
class AudioSegment:
    """音频段信息"""
    segment_id: int
    start_time: float
    end_time: float
    duration: float
    content_type: AudioContentType
    confidence: float
    data: np.ndarray
    sample_rate: int
    timestamp_info: TimestampInfo


class AudioProcessor:
    """音频处理器 - 实现音频流处理和时间戳管理"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化音频处理器
        
        Args:
            config: 配置字典
        """
        self.config = config
        
        # 从配置获取音频处理参数
        audio_config = config.get('processing', {}).get('audio', {})
        
        # 预处理配置
        preprocessing_config = audio_config.get('preprocessing', {})
        self.target_sample_rate = preprocessing_config.get('target_sample_rate', 16000)
        self.target_channels = preprocessing_config.get('target_channels', 1)
        self.output_format = preprocessing_config.get('output_format', 'wav')
        self.bit_depth = preprocessing_config.get('bit_depth', 16)
        
        # 分段处理配置
        segmentation_config = audio_config.get('segmentation', {})
        self.music_segment_duration = segmentation_config.get('music_segment_duration', 30)
        self.speech_segment_duration = segmentation_config.get('speech_segment_duration', 10)
        self.min_duration = segmentation_config.get('min_duration', 3)
        
        # 内容分类配置
        classification_config = audio_config.get('content_classification', {})
        self.enable_classification = classification_config.get('enable', True)
        self.music_threshold = classification_config.get('music_threshold', 0.7)
        self.speech_threshold = classification_config.get('speech_threshold', 0.6)
        
        # 质量过滤配置
        quality_config = classification_config.get('quality_filter', {})
        self.min_snr = quality_config.get('min_snr', 10)
        self.max_silence_ratio = quality_config.get('max_silence_ratio', 0.8)
        
        # 处理限制
        self.max_file_size = audio_config.get('max_file_size', 100) * 1024 * 1024  # MB转字节
        
        # 初始化时间戳处理器
        self.timestamp_processor = TimestampProcessor(config)
        
        logger.info("音频处理器初始化完成")
    
    async def process_audio(self, audio_path: str) -> Dict[str, Any]:
        """
        处理音频文件 - 完整的音频处理流程
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            处理结果字典
        """
        try:
            logger.info(f"开始处理音频: {audio_path}")
            
            # 验证文件
            if not os.path.exists(audio_path):
                raise FileNotFoundError(f"音频文件不存在: {audio_path}")
            
            file_size = os.path.getsize(audio_path)
            if file_size > self.max_file_size:
                raise ValueError(f"音频文件过大: {file_size / (1024*1024):.1f}MB > {self.max_file_size / (1024*1024):.1f}MB")
            
            # 使用异步执行器处理CPU密集型操作
            import asyncio
            loop = asyncio.get_event_loop()
            
            # 1. 提取音频元数据
            metadata = await loop.run_in_executor(None, self._extract_metadata, audio_path)
            
            # 2. 预处理音频(格式标准化)
            preprocessed_path = await loop.run_in_executor(None, self._preprocess_audio, audio_path, metadata)
            
            # 3. 加载预处理后的音频数据
            audio_data, sample_rate = await loop.run_in_executor(None, self._load_audio, preprocessed_path)
            
            # 4. 音频内容分类
            content_classification = await loop.run_in_executor(None, self._classify_audio_content, audio_data, sample_rate)
            
            # 5. 音频分段
            segments = await loop.run_in_executor(None, self._segment_audio, audio_data, sample_rate, content_classification)
            
            # 6. 质量过滤
            filtered_segments = await loop.run_in_executor(None, self._filter_segments_by_quality, segments)
            
            # 7. 创建时间戳信息
            timestamp_infos = self._create_timestamp_infos(filtered_segments, audio_path)
            
            # 8. 应用时间戳校正
            corrected_timestamps = self.timestamp_processor.correct_timestamp_drift(timestamp_infos)
            
            logger.info(f"音频处理完成: {audio_path}, 有效段数: {len(filtered_segments)}")
            
            return {
                'status': 'success',
                'metadata': metadata.__dict__,
                'content_classification': content_classification,
                'segments': [self._segment_to_dict(seg) for seg in filtered_segments],
                'timestamp_infos': [ts.__dict__ for ts in corrected_timestamps],
                'preprocessed_path': preprocessed_path,
                'file_path': audio_path,
                'processing_stats': {
                    'original_duration': metadata.duration,
                    'original_sample_rate': metadata.sample_rate,
                    'target_sample_rate': self.target_sample_rate,
                    'segments_extracted': len(filtered_segments),
                    'content_types': list(set(seg.content_type.value for seg in filtered_segments)),
                    'timestamp_accuracy': f"±{self.timestamp_processor.accuracy_requirement}s"
                }
            }
            
        except Exception as e:
            logger.error(f"音频处理失败: {audio_path}, 错误: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'file_path': audio_path
            }
    
    def _extract_metadata(self, audio_path: str) -> AudioMetadata:
        """
        提取音频元数据
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            音频元数据对象
        """
        try:
            # 使用ffprobe提取元数据
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                audio_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            metadata = json.loads(result.stdout)
            
            # 提取音频流信息
            audio_stream = None
            for stream in metadata.get('streams', []):
                if stream['codec_type'] == 'audio':
                    audio_stream = stream
                    break
            
            if not audio_stream:
                raise ValueError("未找到音频流")
            
            # 解析音频信息
            duration = float(metadata['format'].get('duration', 0))
            sample_rate = int(audio_stream.get('sample_rate', 0))
            channels = int(audio_stream.get('channels', 0))
            bitrate = int(metadata['format'].get('bit_rate', 0))
            format_name = metadata['format'].get('format_name', 'unknown')
            
            # 简单的内容类型预判断
            has_speech = duration > 10  # 简单启发式：长音频可能包含语音
            has_music = True  # 默认假设包含音乐
            
            return AudioMetadata(
                duration=duration,
                sample_rate=sample_rate,
                channels=channels,
                bitrate=bitrate,
                format=format_name,
                has_speech=has_speech,
                has_music=has_music
            )
            
        except subprocess.CalledProcessError as e:
            logger.error(f"ffprobe执行失败: {e}")
            raise ValueError(f"无法提取音频元数据: {e}")
        except Exception as e:
            logger.error(f"元数据提取失败: {e}")
            raise
    
    def _preprocess_audio(self, audio_path: str, metadata: AudioMetadata) -> str:
        """
        预处理音频：格式标准化
        
        Args:
            audio_path: 原始音频路径
            metadata: 音频元数据
            
        Returns:
            预处理后的音频路径
        """
        try:
            # 检查是否需要预处理
            needs_preprocessing = (
                metadata.sample_rate != self.target_sample_rate or
                metadata.channels != self.target_channels or
                metadata.format not in ['wav', 'wave']
            )
            
            if not needs_preprocessing:
                logger.debug(f"音频无需预处理: {audio_path}")
                return audio_path
            
            # 创建临时输出文件
            output_dir = Path(audio_path).parent / "preprocessed"
            output_dir.mkdir(exist_ok=True)
            
            output_path = output_dir / f"preprocessed_{Path(audio_path).stem}.wav"
            
            # 构建ffmpeg命令
            cmd = [
                'ffmpeg',
                '-i', audio_path,
                '-ar', str(self.target_sample_rate),  # 采样率
                '-ac', str(self.target_channels),     # 声道数
                '-acodec', 'pcm_s16le',               # 编码格式
                '-y',  # 覆盖输出文件
                str(output_path)
            ]
            
            logger.debug(f"开始音频预处理: {metadata.sample_rate}Hz -> {self.target_sample_rate}Hz")
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            logger.info(f"音频预处理完成: {output_path}")
            return str(output_path)
            
        except subprocess.CalledProcessError as e:
            logger.error(f"音频预处理失败: {e.stderr}")
            raise ValueError(f"音频预处理失败: {e}")
        except Exception as e:
            logger.error(f"预处理过程出错: {e}")
            return audio_path  # 返回原始路径作为备选
    
    def _load_audio(self, audio_path: str) -> Tuple[np.ndarray, int]:
        """
        加载音频文件
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            (音频数据, 采样率)
        """
        try:
            # 使用librosa加载音频
            audio_data, sample_rate = librosa.load(
                audio_path, 
                sr=self.target_sample_rate,
                mono=(self.target_channels == 1)
            )
            
            # 归一化
            audio_data = librosa.util.normalize(audio_data)
            
            return audio_data, sample_rate
            
        except Exception as e:
            logger.error(f"音频加载失败: {audio_path}, 错误: {e}")
            raise
    
    def _classify_audio_content(self, audio_data: np.ndarray, sample_rate: int) -> Dict[str, Any]:
        """
        音频内容分类
        
        Args:
            audio_data: 音频数据
            sample_rate: 采样率
            
        Returns:
            分类结果字典
        """
        try:
            if not self.enable_classification:
                return {
                    'overall_type': AudioContentType.MIXED,
                    'music_confidence': 0.5,
                    'speech_confidence': 0.5,
                    'segments': []
                }
            
            # 简化的内容分类(基于音频特征)
            # 在实际实现中，这里应该集成inaSpeechSegmenter或其他专业分类器
            
            # 计算音频特征
            # 1. 零交叉率 (Zero Crossing Rate) - 语音通常有更高的零交叉率
            zcr = librosa.feature.zero_crossing_rate(audio_data)[0]
            avg_zcr = np.mean(zcr)
            
            # 2. 频谱质心 (Spectral Centroid) - 音乐通常有更丰富的频谱
            spectral_centroids = librosa.feature.spectral_centroid(y=audio_data, sr=sample_rate)[0]
            avg_spectral_centroid = np.mean(spectral_centroids)
            
            # 3. MFCC特征
            mfccs = librosa.feature.mfcc(y=audio_data, sr=sample_rate, n_mfcc=13)
            mfcc_mean = np.mean(mfccs, axis=1)
            
            # 简单的启发式分类
            # 这是一个简化的实现，实际应该使用训练好的分类模型
            speech_score = 0.0
            music_score = 0.0
            
            # 基于零交叉率的判断
            if avg_zcr > 0.1:
                speech_score += 0.3
            else:
                music_score += 0.3
            
            # 基于频谱质心的判断
            if avg_spectral_centroid > 2000:
                speech_score += 0.3
            else:
                music_score += 0.3
            
            # 基于MFCC的判断(简化)
            if np.std(mfcc_mean) > 10:
                speech_score += 0.4
            else:
                music_score += 0.4
            
            # 归一化分数
            total_score = speech_score + music_score
            if total_score > 0:
                speech_confidence = speech_score / total_score
                music_confidence = music_score / total_score
            else:
                speech_confidence = 0.5
                music_confidence = 0.5
            
            # 确定整体类型
            if music_confidence > self.music_threshold:
                overall_type = AudioContentType.MUSIC
            elif speech_confidence > self.speech_threshold:
                overall_type = AudioContentType.SPEECH
            else:
                overall_type = AudioContentType.MIXED
            
            return {
                'overall_type': overall_type,
                'music_confidence': music_confidence,
                'speech_confidence': speech_confidence,
                'features': {
                    'avg_zcr': avg_zcr,
                    'avg_spectral_centroid': avg_spectral_centroid,
                    'mfcc_std': np.std(mfcc_mean)
                }
            }
            
        except Exception as e:
            logger.error(f"音频内容分类失败: {e}")
            return {
                'overall_type': AudioContentType.MIXED,
                'music_confidence': 0.5,
                'speech_confidence': 0.5,
                'error': str(e)
            }
    
    def _segment_audio(self, audio_data: np.ndarray, sample_rate: int, 
                      content_classification: Dict[str, Any]) -> List[AudioSegment]:
        """
        音频分段处理
        
        Args:
            audio_data: 音频数据
            sample_rate: 采样率
            content_classification: 内容分类结果
            
        Returns:
            音频段列表
        """
        try:
            segments = []
            
            # 根据内容类型确定分段时长
            overall_type = content_classification.get('overall_type', AudioContentType.MIXED)
            if overall_type == AudioContentType.MUSIC:
                segment_duration = self.music_segment_duration
                modality_type = ModalityType.AUDIO_MUSIC
            elif overall_type == AudioContentType.SPEECH:
                segment_duration = self.speech_segment_duration
                modality_type = ModalityType.AUDIO_SPEECH
            else:
                # 混合内容，使用较短的分段
                segment_duration = min(self.music_segment_duration, self.speech_segment_duration)
                modality_type = ModalityType.AUDIO_MUSIC  # 默认为音乐模态
            
            # 计算分段参数
            segment_samples = int(segment_duration * sample_rate)
            total_samples = len(audio_data)
            
            segment_id = 0
            for start_sample in range(0, total_samples, segment_samples):
                end_sample = min(start_sample + segment_samples, total_samples)
                
                # 检查段长度
                actual_duration = (end_sample - start_sample) / sample_rate
                if actual_duration < self.min_duration:
                    continue
                
                # 提取音频段数据
                segment_data = audio_data[start_sample:end_sample]
                start_time = start_sample / sample_rate
                end_time = end_sample / sample_rate
                
                # 创建时间戳信息
                timestamp_info = TimestampInfo(
                    file_id="",  # 将在外部设置
                    segment_id=f"audio_segment_{segment_id}",
                    modality=modality_type,
                    start_time=start_time,
                    end_time=end_time,
                    duration=actual_duration,
                    frame_index=None,
                    vector_id=None,
                    confidence=content_classification.get('music_confidence', 0.5),
                    scene_boundary=False
                )
                
                # 创建音频段对象
                audio_segment = AudioSegment(
                    segment_id=segment_id,
                    start_time=start_time,
                    end_time=end_time,
                    duration=actual_duration,
                    content_type=overall_type,
                    confidence=content_classification.get('music_confidence', 0.5),
                    data=segment_data,
                    sample_rate=sample_rate,
                    timestamp_info=timestamp_info
                )
                
                segments.append(audio_segment)
                segment_id += 1
            
            logger.debug(f"音频分段完成: 生成{len(segments)}个段")
            return segments
            
        except Exception as e:
            logger.error(f"音频分段失败: {e}")
            return []
    
    def _filter_segments_by_quality(self, segments: List[AudioSegment]) -> List[AudioSegment]:
        """
        根据质量过滤音频段
        
        Args:
            segments: 原始音频段列表
            
        Returns:
            过滤后的音频段列表
        """
        try:
            filtered_segments = []
            
            for segment in segments:
                # 计算音频质量指标
                quality_score = self._calculate_audio_quality(segment.data)
                
                # 检查静音比例
                silence_ratio = self._calculate_silence_ratio(segment.data)
                
                # 应用质量过滤
                if quality_score > 0.3 and silence_ratio < self.max_silence_ratio:
                    # 更新置信度
                    segment.confidence = segment.confidence * quality_score
                    filtered_segments.append(segment)
                else:
                    logger.debug(f"过滤低质量音频段: segment_id={segment.segment_id}, "
                               f"quality={quality_score:.3f}, silence_ratio={silence_ratio:.3f}")
            
            logger.info(f"质量过滤完成: {len(segments)} -> {len(filtered_segments)} 段")
            return filtered_segments
            
        except Exception as e:
            logger.error(f"质量过滤失败: {e}")
            return segments  # 返回原始段作为备选
    
    def _calculate_audio_quality(self, audio_data: np.ndarray) -> float:
        """
        计算音频质量评分
        
        Args:
            audio_data: 音频数据
            
        Returns:
            质量评分 (0-1)
        """
        if len(audio_data) == 0:
            return 0.0
        
        # 计算RMS能量
        rms = np.sqrt(np.mean(audio_data**2))
        
        # 计算动态范围
        dynamic_range = np.max(audio_data) - np.min(audio_data)
        
        # 计算频谱平坦度(衡量频谱分布的均匀性)
        fft = np.fft.fft(audio_data)
        magnitude = np.abs(fft[:len(fft)//2])
        spectral_flatness = np.exp(np.mean(np.log(magnitude + 1e-10))) / (np.mean(magnitude) + 1e-10)
        
        # 综合质量评分
        energy_score = min(rms * 5, 1.0)  # 能量评分
        dynamic_score = min(dynamic_range * 2, 1.0)  # 动态范围评分
        spectral_score = min(spectral_flatness * 2, 1.0)  # 频谱评分
        
        quality_score = (energy_score + dynamic_score + spectral_score) / 3.0
        return quality_score
    
    def _calculate_silence_ratio(self, audio_data: np.ndarray, threshold: float = 0.01) -> float:
        """
        计算静音比例
        
        Args:
            audio_data: 音频数据
            threshold: 静音阈值
            
        Returns:
            静音比例 (0-1)
        """
        if len(audio_data) == 0:
            return 1.0
        
        # 计算每个样本的绝对值
        abs_audio = np.abs(audio_data)
        
        # 统计低于阈值的样本数
        silence_samples = np.sum(abs_audio < threshold)
        
        # 计算静音比例
        silence_ratio = silence_samples / len(audio_data)
        return silence_ratio
    
    def _create_timestamp_infos(self, segments: List[AudioSegment], audio_path: str) -> List[TimestampInfo]:
        """
        为音频段创建时间戳信息
        
        Args:
            segments: 音频段列表
            audio_path: 音频文件路径
            
        Returns:
            时间戳信息列表
        """
        timestamp_infos = []
        
        for segment in segments:
            # 更新文件ID
            segment.timestamp_info.file_id = audio_path
            
            # 应用重叠时间窗口
            overlapping_ts = self.timestamp_processor.create_overlapping_time_windows([segment.timestamp_info])
            timestamp_infos.extend(overlapping_ts)
        
        return timestamp_infos
    
    def _segment_to_dict(self, segment: AudioSegment) -> Dict[str, Any]:
        """
        将音频段对象转换为字典(用于JSON序列化)
        
        Args:
            segment: 音频段对象
            
        Returns:
            音频段字典
        """
        return {
            'segment_id': segment.segment_id,
            'start_time': segment.start_time,
            'end_time': segment.end_time,
            'duration': segment.duration,
            'content_type': segment.content_type.value,
            'confidence': segment.confidence,
            'sample_rate': segment.sample_rate,
            'data_shape': segment.data.shape if segment.data is not None else None,
            'timestamp_info': segment.timestamp_info.__dict__
        }
    
    async def transcribe_speech(self, audio_path: str) -> str:
        """
        使用Whisper模型将语音转换为文本
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            转录文本
        """
        try:
            import asyncio
            
            # 加载音频数据
            loop = asyncio.get_event_loop()
            audio_data, sample_rate = await loop.run_in_executor(
                None, lambda: librosa.load(audio_path, sr=self.target_sample_rate)
            )
            
            # 使用嵌入引擎进行语音转文本
            from src.business.embedding_engine import EmbeddingEngine
            
            # 获取配置
            config = self.config
            engine = EmbeddingEngine(config)
            
            # 进行语音转文本
            transcribed_text = await engine.transcribe_audio(audio_data)
            
            return transcribed_text
            
        except Exception as e:
            logger.error(f"语音转文本失败: {audio_path}, 错误: {e}")
            return ""
    
    def validate_processing_result(self, result: Dict[str, Any]) -> bool:
        """
        验证处理结果的完整性和正确性
        
        Args:
            result: 处理结果字典
            
        Returns:
            验证是否通过
        """
        try:
            if result.get('status') != 'success':
                return False
            
            # 验证必要字段
            required_fields = ['metadata', 'content_classification', 'segments', 'timestamp_infos']
            for field in required_fields:
                if field not in result:
                    logger.error(f"处理结果缺少必要字段: {field}")
                    return False
            
            # 验证时间戳精度
            timestamp_infos = result.get('timestamp_infos', [])
            for ts_dict in timestamp_infos:
                duration = ts_dict.get('duration', 0)
                if not self.timestamp_processor.validate_timestamp_accuracy(0, duration):
                    logger.warning(f"时间戳精度不满足要求: {duration}s")
            
            # 验证音频段数量的合理性
            segments_count = len(result.get('segments', []))
            
            if segments_count == 0:
                logger.error("未提取到任何音频段")
                return False
            
            logger.info(f"处理结果验证通过: 音频段数={segments_count}")
            return True
            
        except Exception as e:
            logger.error(f"处理结果验证失败: {e}")
            return False