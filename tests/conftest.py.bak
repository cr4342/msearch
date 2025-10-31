"""
测试配置和日志设置
为所有测试提供统一的日志配置和mock环境
"""
import pytest
import logging
import sys
import os
from unittest.mock import patch

# 导入测试配置和mock
from tests.test_config import get_test_config, patch_config_for_testing
from tests.mock_models import patch_models_for_testing, setup_test_environment

# 配置测试日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('tests/test.log', mode='w', encoding='utf-8')
    ]
)

# 创建测试日志记录器
test_logger = logging.getLogger('msearch_tests')

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """为所有测试设置环境"""
    # 设置测试环境
    setup_test_environment()
    
    test_logger.info("=" * 60)
    test_logger.info("开始测试套件执行")
    test_logger.info("=" * 60)
    yield
    test_logger.info("=" * 60)
    test_logger.info("测试套件执行完成")
    test_logger.info("=" * 60)

@pytest.fixture(autouse=True)
def log_test_start_end(request):
    """为每个测试记录开始和结束"""
    test_name = request.node.name
    test_logger.info(f"开始测试: {test_name}")
    yield
    test_logger.info(f"完成测试: {test_name}")

@pytest.fixture
def test_logger():
    """提供测试日志记录器"""
    return test_logger

@pytest.fixture
def test_config():
    """提供测试配置"""
    return get_test_config()

@pytest.fixture(autouse=True)
def mock_models():
    """自动mock模型依赖"""
    patches = patch_models_for_testing()
    
    # 启动所有补丁
    for p in patches:
        p.start()
    
    yield
    
    # 停止所有补丁
    for p in patches:
        p.stop()

@pytest.fixture(autouse=True)
def mock_config():
    """自动mock配置"""
    with patch('src.core.config_manager.ConfigManager._load_config', return_value=get_test_config()):
        yield