# -*- coding: utf-8 -*-
"""
查询处理器模块

提供查询预处理功能，包括查询解析、查询优化和查询转换。
"""

from typing import Optional, Dict, Any, List
import re

from ...data.constants import ModalityType
from ...data.models.search_models import SearchQuery


class QueryProcessor:
    """查询处理器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化查询处理器
        
        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.logger = None
        
        # 查询配置
        self.max_query_length = self.config.get("max_query_length", 1000)
        self.min_query_length = self.config.get("min_query_length", 1)
        self.default_top_k = self.config.get("default_top_k", 20)
        self.default_threshold = self.config.get("default_threshold", 0.5)
    
    def process_query(self, query: SearchQuery) -> SearchQuery:
        """
        处理查询
        
        Args:
            query: 搜索查询对象
            
        Returns:
            处理后的搜索查询对象
        """
        try:
            # 验证查询
            if not self._validate_query(query):
                if self.logger:
                    self.logger.warning("查询验证失败，使用默认值")
                return self._get_default_query()
            
            # 解析查询
            self._parse_query(query)
            
            # 优化查询
            self._optimize_query(query)
            
            # 设置默认值
            self._set_defaults(query)
            
            return query
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"处理查询失败: {e}")
            return self._get_default_query()
    
    def _validate_query(self, query: SearchQuery) -> bool:
        """
        验证查询
        
        Args:
            query: 搜索查询对象
            
        Returns:
            是否有效
        """
        # 检查查询内容是否为空
        if not query.query_text and not query.query_image and not query.query_audio and not query.query_vector:
            return False
        
        # 检查文本查询长度
        if query.query_text:
            if len(query.query_text) < self.min_query_length or len(query.query_text) > self.max_query_length:
                return False
        
        # 检查模态类型
        if query.modality not in [m.value for m in ModalityType]:
            return False
        
        # 检查top_k
        if query.top_k <= 0 or query.top_k > 1000:
            return False
        
        # 检查阈值
        if query.threshold < 0 or query.threshold > 1:
            return False
        
        return True
    
    def _parse_query(self, query: SearchQuery) -> None:
        """
        解析查询
        
        Args:
            query: 搜索查询对象
        """
        # 解析文本查询中的特殊语法
        if query.query_text:
            query.query_text = self._parse_text_query(query.query_text)
        
        # 解析过滤条件
        if query.filters:
            query.filters = self._parse_filters(query.filters)
        
        # 解析时间范围
        if query.time_range:
            query.time_range = self._parse_time_range(query.time_range)
    
    def _parse_text_query(self, text: str) -> str:
        """
        解析文本查询
        
        Args:
            text: 文本查询
            
        Returns:
            解析后的文本
        """
        # 去除多余空格
        text = re.sub(r'\s+', ' ', text).strip()
        
        # 去除特殊字符（保留中文、英文、数字、标点）
        text = re.sub(r'[^\w\s\u4e00-\u9fff\u3000-\u303f\uff00-\uffef.,!?;:()""''【】《》]', '', text)
        
        return text
    
    def _parse_filters(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析过滤条件
        
        Args:
            filters: 过滤条件字典
            
        Returns:
            解析后的过滤条件字典
        """
        parsed_filters = {}
        
        # 文件类型过滤
        if "file_type" in filters:
            file_type = filters["file_type"]
            if isinstance(file_type, str):
                parsed_filters["file_type"] = [file_type]
            elif isinstance(file_type, list):
                parsed_filters["file_type"] = file_type
        
        # 日期范围过滤
        if "date_range" in filters:
            date_range = filters["date_range"]
            if isinstance(date_range, dict):
                parsed_filters["date_range"] = date_range
        
        # 大小范围过滤
        if "size_range" in filters:
            size_range = filters["size_range"]
            if isinstance(size_range, dict):
                parsed_filters["size_range"] = size_range
        
        # 自定义过滤
        for key, value in filters.items():
            if key not in parsed_filters:
                parsed_filters[key] = value
        
        return parsed_filters
    
    def _parse_time_range(self, time_range: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析时间范围
        
        Args:
            time_range: 时间范围字典
            
        Returns:
            解析后的时间范围字典
        """
        parsed = {}
        
        if "start" in time_range:
            parsed["start"] = float(time_range["start"])
        
        if "end" in time_range:
            parsed["end"] = float(time_range["end"])
        
        return parsed
    
    def _optimize_query(self, query: SearchQuery) -> None:
        """
        优化查询
        
        Args:
            query: 搜索查询对象
        """
        # 根据查询类型设置最优参数
        if query.query_image:
            # 图像查询：提高阈值，减少结果数量
            query.threshold = max(query.threshold, 0.6)
            query.top_k = min(query.top_k, 50)
        
        elif query.query_audio:
            # 音频查询：使用中等阈值
            query.threshold = max(query.threshold, 0.5)
            query.top_k = min(query.top_k, 30)
        
        elif query.query_text:
            # 文本查询：使用默认阈值
            query.threshold = max(query.threshold, 0.4)
            query.top_k = min(query.top_k, 100)
        
        # 根据过滤条件调整参数
        if query.filters and len(query.filters) > 0:
            # 有过滤条件时，可以降低阈值
            query.threshold = max(0.3, query.threshold - 0.1)
    
    def _set_defaults(self, query: SearchQuery) -> None:
        """
        设置默认值
        
        Args:
            query: 搜索查询对象
        """
        # 设置默认top_k
        if query.top_k <= 0:
            query.top_k = self.default_top_k
        
        # 设置默认阈值
        if query.threshold < 0 or query.threshold > 1:
            query.threshold = self.default_threshold
        
        # 设置默认模态
        if not query.modality:
            if query.query_text:
                query.modality = ModalityType.TEXT.value
            elif query.query_image:
                query.modality = ModalityType.IMAGE.value
            elif query.query_audio:
                query.modality = ModalityType.AUDIO.value
            else:
                query.modality = ModalityType.TEXT.value
    
    def _get_default_query(self) -> SearchQuery:
        """
        获取默认查询
        
        Returns:
            默认搜索查询对象
        """
        return SearchQuery(
            query_text="",
            modality=ModalityType.TEXT.value,
            top_k=self.default_top_k,
            threshold=self.default_threshold
        )
    
    def extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """
        从文本中提取关键词
        
        Args:
            text: 文本内容
            max_keywords: 最大关键词数量
            
        Returns:
            关键词列表
        """
        try:
            # 简单的关键词提取：基于词频
            words = re.findall(r'[\w\u4e00-\u9fff]+', text)
            
            # 统计词频
            word_freq = {}
            for word in words:
                if len(word) > 1:  # 过滤单字
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            # 按频率排序
            sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
            
            # 返回前N个关键词
            keywords = [word for word, freq in sorted_words[:max_keywords]]
            
            return keywords
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"提取关键词失败: {e}")
            return []
    
    def detect_query_type(self, query: SearchQuery) -> str:
        """
        检测查询类型
        
        Args:
            query: 搜索查询对象
            
        Returns:
            查询类型（semantic/exact/fuzzy）
        """
        # 如果有图像或音频查询，使用语义搜索
        if query.query_image or query.query_audio:
            return "semantic"
        
        # 如果有向量查询，使用语义搜索
        if query.query_vector:
            return "semantic"
        
        # 检查文本查询是否包含引号（精确匹配）
        if query.query_text and ('"' in query.query_text or "'" in query.query_text):
            return "exact"
        
        # 默认使用模糊搜索
        return "fuzzy"
    
    def normalize_query(self, query: SearchQuery) -> SearchQuery:
        """
        标准化查询
        
        Args:
            query: 搜索查询对象
            
        Returns:
            标准化后的搜索查询对象
        """
        # 转小写
        if query.query_text:
            query.query_text = query.query_text.lower()
        
        # 标准化过滤条件
        if query.filters:
            for key, value in query.filters.items():
                if isinstance(value, str):
                    query.filters[key] = value.lower()
        
        return query