"""
测试配置文件
"""
import sys
from pathlib import Path

# 添加src目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root))

import pytest
from unittest.mock import patch
import os


@pytest.fixture(autouse=True)
def setup_test_environment():
    """自动设置测试环境"""
    # 设置环境变量
    os.environ['ENVIRONMENT'] = 'test'
    
    # 模拟某些可能需要的环境设置
    with patch('src.core.config.load_config'):
        yield