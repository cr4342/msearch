"""
音频内容分类器 - 使用inaSpeechSegmenter区分音乐、语音和噪音
"""
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

try:
    from inaSpeechSegmenter import Segmenter
    INA_SPEECH_SEGMENTER_AVAILABLE = True
except ImportError:
    INA_SPEECH_SEGMENTER_AVAILABLE = False
    logger.warning("inaSpeechSegmenter未安装，将使用简化分类方法")


class AudioClassifier:
    """音频内容分类器"""
    
    def __init__(self):
        """初始化音频分类器"""
        if INA_SPEECH_SEGMENTER_AVAILABLE:
            try:
                self.segmenter = Segmenter(vad_engine='sm')
            except Exception as e:
                logger.warning(f"初始化inaSpeechSegmenter失败: {e}")
                self.segmenter = None
        else:
            self.segmenter = None
    
    def classify_audio(self, audio_path: str) -> List[Dict[str, Any]]:
        """
        分类音频内容，返回分类结果
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            分类结果列表，每个元素包含类型、起始时间、结束时间
        """
        if self.segmenter is not None:
            try:
                # 使用inaSpeechSegmenter进行分类
                segmentation = self.segmenter(audio_path)
                
                results = []
                for segment_type, start_time, end_time in segmentation:
                    results.append({
                        'type': segment_type,  # 'music', 'speech', or 'noise'
                        'start_time': start_time,
                        'end_time': end_time,
                        'duration': end_time - start_time
                    })
                
                return results
            except Exception as e:
                logger.error(f"使用inaSpeechSegmenter分类音频失败: {e}")
                return self._simple_classification(audio_path)
        else:
            # 如果inaSpeechSegmenter不可用，使用简化分类方法
            return self._simple_classification(audio_path)
    
    def _simple_classification(self, audio_path: str) -> List[Dict[str, Any]]:
        """
        简化的音频分类方法
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            简化的分类结果
        """
        # 这里可以实现基于音频特征的简单分类逻辑
        # 暂时返回默认分类
        
        try:
            import librosa
            # 获取音频时长
            duration = librosa.get_duration(filename=audio_path)
            
            # 基于时长的简单分类
            if duration < 5:
                audio_type = 'noise'
            elif duration < 30:
                audio_type = 'speech'
            else:
                audio_type = 'music'
            
            return [{
                'type': audio_type,
                'start_time': 0.0,
                'end_time': duration,
                'duration': duration
            }]
        except Exception as e:
            logger.error(f"简化音频分类失败: {e}")
            # 返回默认值
            return [{
                'type': 'unknown',
                'start_time': 0.0,
                'end_time': 1.0,
                'duration': 1.0
            }]
    
    def has_speech_content(self, audio_path: str) -> bool:
        """
        检查音频是否包含语音内容
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            是否包含语音内容
        """
        segments = self.classify_audio(audio_path)
        
        # 检查是否有语音段，且语音段总时长超过阈值
        speech_duration = sum(seg['duration'] for seg in segments if seg['type'] == 'speech')
        total_duration = sum(seg['duration'] for seg in segments)
        
        # 如果语音占比超过10%，则认为包含语音内容
        return speech_duration / total_duration > 0.1 if total_duration > 0 else False


# 示例使用
if __name__ == "__main__":
    # 创建分类器实例
    classifier = AudioClassifier()
    
    # 分类音频 (需要实际的音频文件路径)
    # results = classifier.classify_audio("path/to/audio.wav")
    # print(results)
    # 
    # has_speech = classifier.has_speech_content("path/to/audio.wav")
    # print(f"包含语音内容: {has_speech}")