"""
音频处理器 - 处理音频文件的内容分类、格式转换和分段处理
"""
import os
import librosa
import numpy as np
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class AudioProcessor:
    """音频处理器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化音频处理器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.target_sample_rate = config.get('processing.audio.target_sample_rate', 16000)
        self.target_channels = config.get('processing.audio.target_channels', 1)  # 单声道
        self.segment_duration = config.get('processing.audio.segment_duration', 10.0)  # 秒
        self.quality_threshold = config.get('processing.audio.quality_threshold', 0.5)
    
    async def process_audio(self, audio_path: str) -> Dict[str, Any]:
        """
        处理音频文件
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            处理结果字典
        """
        try:
            logger.debug(f"开始处理音频: {audio_path}")            
            # 使用异步执行器处理CPU密集型操作
            import asyncio
            loop = asyncio.get_event_loop()
            
            # 1. 提取音频元数据（异步执行）
            metadata = await loop.run_in_executor(None, self._extract_metadata, audio_path)
            
            # 2. 音频内容分类（异步执行）
            classification = await loop.run_in_executor(None, self._classify_audio_content, audio_path, metadata)
            
            # 3. 格式标准化（异步执行）
            standardized_audio = await loop.run_in_executor(None, self._standardize_format, audio_path)
            
            # 4. 音频分段（异步执行）
            segments = await loop.run_in_executor(None, self._segment_audio, standardized_audio, metadata)
            
            # 5. 质量评估（异步执行）
            quality_scores = []
            for segment in segments:
                quality_score = await loop.run_in_executor(None, self._assess_quality, segment['audio_data'])
                quality_scores.append(quality_score)
            
            logger.debug(f"音频处理完成: {audio_path}, 分段数: {len(segments)}")
            
            return {
                'status': 'success',
                'metadata': metadata,
                'classification': classification,
                'segments': segments,
                'quality_scores': quality_scores,
                'file_path': audio_path
            }
            
        except Exception as e:
            logger.error(f"音频处理失败: {audio_path}, 错误: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'file_path': audio_path
            }
    
    def _extract_metadata(self, audio_path: str) -> Dict[str, Any]:
        """
        提取音频元数据
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            元数据字典
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"音频文件不存在: {audio_path}")
        
        # 使用librosa获取音频信息
        try:
            duration = librosa.get_duration(filename=audio_path)
            sample_rate = librosa.get_samplerate(audio_path)
            
            # 加载一小段音频来获取声道数
            y, _ = librosa.load(audio_path, duration=1.0)
            channels = 1 if y.ndim == 1 else y.shape[0]
            
            return {
                'duration': duration,
                'sample_rate': sample_rate,
                'channels': channels,
                'file_size': os.path.getsize(audio_path)
            }
        except Exception as e:
            raise ValueError(f"无法提取音频元数据: {audio_path}, 错误: {e}")
    
    def _classify_audio_content(self, audio_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        分类音频内容（音乐/语音/噪音）
        
        Args:
            audio_path: 音频文件路径
            metadata: 音频元数据
            
        Returns:
            分类结果字典
        """
        try:
            # 使用inaSpeechSegmenter进行音频分类
            from src.processors.audio_classifier import AudioClassifier
            classifier = AudioClassifier()
            segments = classifier.classify_audio(audio_path)
            
            if segments:
                # 统计各类别的时间占比
                total_duration = sum(seg['duration'] for seg in segments)
                type_durations = {}
                
                for segment in segments:
                    seg_type = segment['type']
                    if seg_type not in type_durations:
                        type_durations[seg_type] = 0
                    type_durations[seg_type] += segment['duration']
                
                # 计算各类别的占比
                type_ratios = {k: v / total_duration for k, v in type_durations.items()}
                
                # 确定主要类型
                primary_type = max(type_ratios, key=type_ratios.get)
                confidence = type_ratios[primary_type]
                
                return {
                    'primary_type': primary_type,
                    'confidence': confidence,
                    'details': type_ratios,
                    'segments': segments
                }
            else:
                # 如果分类失败，使用启发式方法
                duration = metadata['duration']
                
                if duration < 5:
                    primary_type = 'noise'
                    confidence = 0.7
                elif duration > 30:
                    primary_type = 'music'
                    confidence = 0.8
                else:
                    primary_type = 'speech'
                    confidence = 0.6
                
                return {
                    'primary_type': primary_type,
                    'confidence': confidence,
                    'details': {
                        'music': 0.3 if primary_type != 'music' else 0.8,
                        'speech': 0.3 if primary_type != 'speech' else 0.8,
                        'noise': 0.3 if primary_type != 'noise' else 0.8
                    }
                }
        except Exception as e:
            logger.error(f"音频分类失败: {e}")
            # 使用启发式方法作为回退
            duration = metadata['duration']
            
            if duration < 5:
                primary_type = 'noise'
                confidence = 0.7
            elif duration > 30:
                primary_type = 'music'
                confidence = 0.8
            else:
                primary_type = 'speech'
                confidence = 0.6
            
            return {
                'primary_type': primary_type,
                'confidence': confidence,
                'details': {
                    'music': 0.3 if primary_type != 'music' else 0.8,
                    'speech': 0.3 if primary_type != 'speech' else 0.8,
                    'noise': 0.3 if primary_type != 'noise' else 0.8
                }
            }
    
    def _standardize_format(self, audio_path: str) -> np.ndarray:
        """
        标准化音频格式
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            标准化后的音频数据
        """
        # 加载音频并转换为标准格式
        y, sr = librosa.load(
            audio_path,
            sr=self.target_sample_rate,
            mono=(self.target_channels == 1)
        )
        
        return y
    
    def _segment_audio(self, audio_data: np.ndarray, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        将音频分割成固定长度的片段
        
        Args:
            audio_data: 音频数据
            metadata: 音频元数据
            
        Returns:
            音频片段列表
        """
        sample_rate = self.target_sample_rate
        segment_samples = int(self.segment_duration * sample_rate)
        
        segments = []
        total_samples = len(audio_data)
        
        # 计算需要的片段数
        num_segments = int(np.ceil(total_samples / segment_samples))
        
        for i in range(num_segments):
            start_sample = i * segment_samples
            end_sample = min((i + 1) * segment_samples, total_samples)
            
            # 提取片段
            segment_data = audio_data[start_sample:end_sample]
            
            # 如果片段太短，可以选择跳过或填充
            if len(segment_data) < sample_rate:  # 小于1秒的片段
                continue
            
            # 计算时间戳
            start_time = start_sample / sample_rate
            end_time = end_sample / sample_rate
            
            segments.append({
                'segment_id': i,
                'start_time': start_time,
                'end_time': end_time,
                'duration': end_time - start_time,
                'audio_data': segment_data,
                'sample_rate': sample_rate
            })
        
        return segments
    
    def _assess_quality(self, audio_data: np.ndarray) -> float:
        """
        评估音频质量
        
        Args:
            audio_data: 音频数据
            
        Returns:
            质量评分 (0-1)
        """
        # 简单的质量评估：基于音频能量和信噪比
        if len(audio_data) == 0:
            return 0.0
        
        # 计算音频能量（均方根）
        rms = np.sqrt(np.mean(audio_data**2))
        
        # 计算零交叉率
        zero_crossings = np.sum(np.abs(np.diff(np.sign(audio_data)))) / (2 * len(audio_data))
        
        # 组合质量评分
        # 高能量和适中的零交叉率表示高质量音频
        energy_score = min(rms * 10, 1.0)  # 调整比例
        zero_crossing_score = 1.0 - abs(zero_crossings - 0.1)  # 0.1是理想零交叉率
        zero_crossing_score = max(0.0, min(zero_crossing_score, 1.0))
        
        quality_score = (energy_score + zero_crossing_score) / 2.0
        
        return quality_score
    
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
            import librosa
            
            # 加载音频数据
            loop = asyncio.get_event_loop()
            # 修复librosa.load调用
            audio_data, sample_rate = await loop.run_in_executor(
                None, lambda: librosa.load(audio_path, sr=self.target_sample_rate)
            )
            
            # 使用嵌入引擎进行语音转文本
            from src.business.embedding_engine import get_embedding_engine
            from src.core.config_manager import get_config_manager
            
            # 获取配置
            config = get_config_manager().config
            engine = get_embedding_engine(config)
            
            # 确保Whisper模型可用
            if not engine.is_model_available('whisper'):
                raise RuntimeError("Whisper模型不可用")
            
            # 进行语音转文本
            transcribed_text = await engine.transcribe_speech(audio_data)
            
            return transcribed_text
            
        except Exception as e:
            logger.error(f"语音转文本失败: {audio_path}, 错误: {e}")
            return ""
    
    def get_audio_segments_by_type(self, audio_path: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        获取按类型分类的音频段
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            按类型分类的音频段字典
        """
        try:
            # 使用inaSpeechSegmenter进行音频分类
            from src.processors.audio_classifier import AudioClassifier
            classifier = AudioClassifier()
            segments = classifier.classify_audio(audio_path)
            
            # 按类型分组
            segments_by_type = {}
            for segment in segments:
                seg_type = segment['type']
                if seg_type not in segments_by_type:
                    segments_by_type[seg_type] = []
                segments_by_type[seg_type].append(segment)
            
            return segments_by_type
        except Exception as e:
            logger.error(f"获取音频段失败: {e}")
            return {}


# 示例使用
if __name__ == "__main__":
    # 配置示例
    config = {
        'processing.audio.target_sample_rate': 16000,
        'processing.audio.target_channels': 1,
        'processing.audio.segment_duration': 10.0,
        'processing.audio.quality_threshold': 0.5
    }
    
    # 创建处理器实例
    processor = AudioProcessor(config)
    
    # 处理音频 (需要实际的音频文件路径)
    # result = processor.process_audio("path/to/audio.wav")
    # print(result)