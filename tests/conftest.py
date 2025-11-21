"""
msearch 测试配置文件
pytest配置和测试依赖管理
"""
import pytest
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

# 测试配置
def pytest_configure(config):
    """pytest配置"""
    # 添加自定义标记
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "gpu: marks tests that require GPU"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )

# 测试夹具
@pytest.fixture(scope="session")
def test_config():
    """测试配置夹具"""
    return {
        'device': 'cpu',
        'features': {
            'enable_clip': True,
            'enable_clap': False,
            'enable_whisper': False
        },
        'models': {
            'clip': {
                'device': 'cpu',
                'batch_size': 4,
                'local_path': './data/models/clip'
            }
        },
        'search': {
            'timestamp_retrieval': {
                'accuracy_requirement': 2.0,
                'enable_segment_merging': True,
                'merge_threshold': 2.0
            }
        },
        'database': {
            'sqlite': {
                'path': ':memory:'  # 使用内存数据库进行测试
            }
        }
    }

@pytest.fixture(scope="session")
def mock_image_data():
    """模拟图像数据夹具"""
    import numpy as np
    return np.random.rand(224, 224, 3).astype(np.float32)

@pytest.fixture(scope="session")
def mock_audio_data():
    """模拟音频数据夹具"""
    import numpy as np
    return np.random.rand(16000).astype(np.float32)  # 1秒16kHz音频

@pytest.fixture(scope="session")
def mock_text_data():
    """模拟文本数据夹具"""
    return "这是一个测试文本，用于验证文本向量化功能。"

# 测试收集钩子
def pytest_collection_modifyitems(config, items):
    """修改测试收集"""
    # 为没有标记的测试添加默认标记
    for item in items:
        if "slow" not in [mark.name for mark in item.iter_markers()]:
            if "performance" in item.nodeid or "integration" in item.nodeid:
                item.add_marker(pytest.mark.slow)
        
        if "gpu" not in [mark.name for mark in item.iter_markers()]:
            if "gpu" in item.nodeid.lower():
                item.add_marker(pytest.mark.gpu)

# 测试报告钩子（需要pytest-html插件）
# 注释掉HTML相关钩子以避免插件未安装错误
# try:
#     def pytest_html_report_title(report):
#         """自定义HTML报告标题"""
#         report.title = "msearch 多模态检索系统测试报告"
# 
#     def pytest_html_results_summary(prefix, summary, postfix):
#         """自定义HTML报告摘要"""
#         prefix.extend([
#             "<h2>测试环境信息</h2>",
#             "<p>Python版本: " + str(sys.version) + "</p>",
#             "<p>项目路径: " + str(project_root) + "</p>",
#             "<p>测试时间: " + str(pytest.__version__) + "</p>"
#         ])
# except:
#     pass  # pytest-html插件未安装

# 跳过条件
def pytest_runtest_setup(item):
    """测试运行前设置"""
    # GPU测试跳过条件
    if "gpu" in [mark.name for mark in item.iter_markers()]:
        try:
            import torch
            if not torch.cuda.is_available():
                pytest.skip("GPU不可用，跳过GPU测试")
        except ImportError:
            pytest.skip("PyTorch未安装，跳过GPU测试")
    
    # 集成测试跳过条件
    if "integration" in [mark.name for mark in item.iter_markers()]:
        # 检查是否有必要的外部依赖
        try:
            import qdrant_client
            import sqlalchemy
        except ImportError:
            pytest.skip("集成测试依赖未安装，跳过集成测试")

# 测试清理
def pytest_unconfigure(config):
    """测试清理"""
    # 清理临时文件
    import tempfile
    import shutil
    
    temp_dir = Path(tempfile.gettempdir()) / "msearch_test"
    if temp_dir.exists():
        shutil.rmtree(temp_dir, ignore_errors=True)