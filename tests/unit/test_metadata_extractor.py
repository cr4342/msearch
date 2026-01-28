#!/usr/bin/env python3
"""
测试元数据提取器
"""

import pytest
import sys
import tempfile
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data.extractors.metadata_extractor import MetadataExtractor


class TestMetadataExtractor:
    """元数据提取器测试"""
    
    @pytest.fixture
    def extractor(self):
        """创建提取器"""
        return MetadataExtractor()
    
    def test_extractor_initialization(self, extractor):
        """测试提取器初始化"""
        assert extractor is not None
        print("✓ 元数据提取器初始化测试通过")
    
    def test_extract_image_metadata(self, extractor):
        """测试提取图像元数据"""
        # 创建一个临时图像文件
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            temp_path = Path(f.name)
        
        try:
            # 写入一个简单的JPEG文件头
            with open(temp_path, 'wb') as f:
                f.write(b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00')
            
            result = extractor.extract(str(temp_path))
            
            assert result is not None
            assert 'file_path' in result
            assert 'file_name' in result
            print("✓ 图像元数据提取测试通过")
        finally:
            temp_path.unlink(missing_ok=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])