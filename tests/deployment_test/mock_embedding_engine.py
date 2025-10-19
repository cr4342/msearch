#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模拟嵌入引擎 - 用于测试
"""

import numpy as np
import logging
from typing import Dict, Any, List, Union
import sys
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent.parent.parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

logger = logging.getLogger(__name__)

class MockEmbeddingEngine:
    """模拟嵌入引擎"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化嵌入引擎
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 模型映射 - 根据内容类型选择对应的模型
        self.model_mapping = {
            'image': 'clip',
            'text': 'clip',
            'audio_music': 'clap',
            'audio_speech': 'whisper'
        }
        
        # 模型健康状态
        self.model_health = {
            'clip': True,
            'clap': True,
            'whisper': True
        }
        
        self.logger.info("模拟嵌入引擎初始化成功")
    
    async def encode_text(self, text: str, model_name: str = 'clip') -> np.ndarray:
        """编码文本"""
        # 返回固定大小的随机向量
        return np.random.rand(512).astype(np.float32)
    
    async def encode_image(self, image_path: str, model_name: str = 'clip') -> np.ndarray:
        """编码图像"""
        # 返回固定大小的随机向量
        return np.random.rand(512).astype(np.float32)
    
    async def encode_audio(self, audio_path: str, model_name: str = 'clap') -> np.ndarray:
        """编码音频"""
        # 返回固定大小的随机向量
        return np.random.rand(512).astype(np.float32)
    
    def get_model_health(self, model_name: str) -> bool:
        """获取模型健康状态"""
        return self.model_health.get(model_name, False)
    
    def is_model_available(self, model_name: str) -> bool:
        """检查模型是否可用"""
        return model_name in self.model_health

# 替换原始的EmbeddingEngine
import src.business.embedding_engine
src.business.embedding_engine.EmbeddingEngine = MockEmbeddingEngine

print("模拟嵌入引擎已替换原始引擎")