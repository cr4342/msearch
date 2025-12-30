import pytest
import asyncio
from src.core.config_manager import get_config_manager

@pytest.fixture
def config_manager():
    """配置管理器夹具"""
    return get_config_manager()

@pytest.fixture
def event_loop():
    """事件循环夹具，用于异步测试"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


def pytest_configure(config):
    """Pytest配置"""
    config.addinivalue_line(
        "markers", "asyncio: mark test as asyncio test"
    )
