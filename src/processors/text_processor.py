"""
文本处理器 - 处理文本文件的编码检测、内容清理和结构化提取
"""
import os
import chardet
import re
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class TextProcessor:
    """文本处理器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化文本处理器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.max_file_size = config.get('processing.text.max_file_size', 10 * 1024 * 1024)  # 10MB
        self.encoding_priority = config.get('processing.text.encoding_priority', 
                                          ['utf-8', 'gbk', 'gb2312', 'latin-1'])
    
    async def process_text(self, text_path: str) -> Dict[str, Any]:
        """
        处理文本文件
        
        Args:
            text_path: 文本文件路径
            
        Returns:
            处理结果字典
        """
        try:
            logger.debug(f"开始处理文本: {text_path}")
            
            # 1. 检查文件大小
            file_size = os.path.getsize(text_path)
            if file_size > self.max_file_size:
                raise ValueError(f"文件过大: {file_size} bytes > {self.max_file_size} bytes")
            
            # 2. 检测文件编码
            detected_encoding = self._detect_encoding(text_path)
            
            # 3. 读取文本内容
            text_content = self._read_text_file(text_path, detected_encoding)
            
            # 4. 内容清理
            cleaned_content = self._clean_content(text_content)
            
            # 5. 结构化提取
            structured_content = self._extract_structured_content(cleaned_content)
            
            logger.debug(f"文本处理完成: {text_path}, 原始长度={len(text_content)}, "
                        f"清理后长度={len(cleaned_content)}")
            
            return {
                'status': 'success',
                'original_content': text_content,
                'cleaned_content': cleaned_content,
                'structured_content': structured_content,
                'encoding': detected_encoding,
                'file_path': text_path,
                'file_size': file_size
            }
            
        except Exception as e:
            logger.error(f"文本处理失败: {text_path}, 错误: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'file_path': text_path
            }
    
    def _detect_encoding(self, file_path: str) -> str:
        """
        检测文件编码
        
        Args:
            file_path: 文件路径
            
        Returns:
            检测到的编码
        """
        # 首先尝试使用chardet检测
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read(10000)  # 读取前10KB用于编码检测
                detected = chardet.detect(raw_data)
                detected_encoding = detected['encoding']
                
                if detected_encoding:
                    logger.debug(f"chardet检测编码: {detected_encoding} (置信度: {detected['confidence']:.2f})")
                    if detected['confidence'] > 0.7:  # 置信度阈值
                        return detected_encoding
        except Exception as e:
            logger.warning(f"chardet编码检测失败: {e}")
        
        # 如果chardet失败，尝试使用配置中的编码列表
        for encoding in self.encoding_priority:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    f.read(1000)  # 尝试读取部分文件
                logger.debug(f"使用配置编码: {encoding}")
                return encoding
            except UnicodeDecodeError:
                continue
        
        # 如果都失败，使用默认编码
        logger.warning("所有编码检测方法都失败，使用默认编码utf-8")
        return 'utf-8'
    
    def _read_text_file(self, file_path: str, encoding: str) -> str:
        """
        读取文本文件
        
        Args:
            file_path: 文件路径
            encoding: 文件编码
            
        Returns:
            文本内容
        """
        with open(file_path, 'r', encoding=encoding) as f:
            content = f.read()
        return content
    
    def _clean_content(self, content: str) -> str:
        """
        清理文本内容
        
        Args:
            content: 原始文本内容
            
        Returns:
            清理后的文本内容
        """
        # 移除多余的空白字符和换行符
        cleaned = content.strip()
        
        # 标准化空白字符
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # 移除控制字符
        cleaned = ''.join(char for char in cleaned if ord(char) >= 32 or char in '\n\r\t')
        
        return cleaned
    
    def _extract_structured_content(self, content: str) -> Dict[str, Any]:
        """
        提取结构化内容
        
        Args:
            content: 清理后的文本内容
            
        Returns:
            结构化内容字典
        """
        # 简单的结构化提取
        lines = content.split('\n')
        
        return {
            'total_lines': len(lines),
            'total_chars': len(content),
            'total_words': len(content.split()),
            'sample_lines': lines[:10],  # 前10行作为样本
            'is_plain_text': True,  # 标记为纯文本
            'language': self._detect_language(content)
        }
    
    def _detect_language(self, content: str) -> str:
        """
        检测文本语言（简化版）
        
        Args:
            content: 文本内容
            
        Returns:
            语言代码
        """
        # 简单的语言检测：基于字符范围
        chinese_chars = len([c for c in content if '\u4e00' <= c <= '\u9fff'])
        total_chars = len([c for c in content if c.isalpha()])
        
        if total_chars > 0 and chinese_chars / total_chars > 0.3:
            return 'zh'
        else:
            return 'en'


# 示例使用
if __name__ == "__main__":
    # 配置示例
    config = {
        'processing.text.max_file_size': 10 * 1024 * 1024,  # 10MB
        'processing.text.encoding_priority': ['utf-8', 'gbk', 'gb2312', 'latin-1']
    }
    
    # 创建处理器实例
    processor = TextProcessor(config)
    
    # 处理文本 (需要实际的文本文件路径)
    # result = processor.process_text("path/to/text.txt")
    # print(result)