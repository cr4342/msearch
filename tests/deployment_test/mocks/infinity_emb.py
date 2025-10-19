
"""模拟的infinity_emb模块"""
import logging
import numpy as np
from typing import List, Union

logger = logging.getLogger(__name__)

class EngineArgs:
    """模拟的EngineArgs"""
    def __init__(self, **kwargs):
        self.model_name_or_path = kwargs.get('model_name_or_path', '')
        self.device = kwargs.get('device', 'cpu')

class AsyncEngineArray:
    """模拟的AsyncEngineArray"""
    def __init__(self, args):
        self.args = args
        logger.info(f"创建模拟AsyncEngineArray: {args.model_name_or_path}")
    
    async def encode(self, sentences: List[str]) -> np.ndarray:
        """模拟编码"""
        # 返回随机向量
        return np.random.rand(len(sentences), 512).astype(np.float32)

class AsyncEmbeddingEngine:
    """模拟的AsyncEmbeddingEngine"""
    def __init__(self, args):
        self.args = args
        logger.info(f"创建模拟AsyncEmbeddingEngine: {args.model_name_or_path}")
