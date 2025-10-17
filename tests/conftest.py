"""
测试配置文件
"""

import os
import sys
from pathlib import Path

# 将src目录添加到Python路径中
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))