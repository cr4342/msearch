"""
向量化引擎接口定义
定义向量化引擎的抽象接口
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class EmbeddingEngine(ABC):
    """向量化引擎接口"""

    @abstractmethod
    async def embed_text(self, text: str) -> List[float]:
        """
        文本向量化

        Args:
            text: 文本内容

        Returns:
            向量列表
        """
        pass

    @abstractmethod
    async def embed_image(self, image_path: str) -> List[float]:
        """
        图像向量化

        Args:
            image_path: 图像文件路径

        Returns:
            向量列表
        """
        pass

    @abstractmethod
    async def embed_audio(self, audio_path: str) -> List[float]:
        """
        音频向量化

        Args:
            audio_path: 音频文件路径

        Returns:
            向量列表
        """
        pass

    @abstractmethod
    async def embed_video_segment(
        self,
        video_path: str,
        start_time: float = 0.0,
        end_time: Optional[float] = None,
        aggregation: str = "mean",
    ) -> List[float]:
        """
        视频片段向量化

        Args:
            video_path: 视频文件路径
            start_time: 开始时间（秒）
            end_time: 结束时间（秒），None表示到视频结尾
            aggregation: 聚合方式（mean/max/avg）

        Returns:
            向量列表
        """
        pass

    @abstractmethod
    def get_embedding_dimension(self) -> int:
        """
        获取向量维度

        Returns:
            向量维度
        """
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息

        Returns:
            模型信息字典
        """
        pass
