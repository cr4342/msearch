"""
测试配置文件
"""

import os
import sys
import pytest
from pathlib import Path

# 将src目录添加到Python路径中
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# 为pytest-asyncio配置默认的事件循环
@pytest.fixture(scope="session")
def event_loop():
    """创建一个会话范围的事件循环"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()

# 确保导入asyncio
import asyncio