# MSearch 测试策略文档

## 概述

本文档详细描述了 MSearch 多模态搜索系统的测试策略，包括测试目标、测试类型、测试工具、测试流程和测试覆盖率要求。

**测试目标**：
- 确保系统功能正确性和稳定性
- 提高代码质量和可维护性
- 降低线上故障风险
- 支持持续集成和持续部署（CI/CD）

**测试原则**：
- **测试驱动开发**：在编写功能代码前先编写测试
- **AAA模式**：所有测试用例遵循 Arrange-Act-Assert 模式
- **独立性**：测试用例之间相互独立，不依赖执行顺序
- **可重复性**：测试用例可以重复执行，结果一致
- **快速反馈**：测试执行时间尽可能短，快速发现问题

## 1. 测试目录结构

### 1.1 目录规范

```
tests/
├── __init__.py
├── pytest.ini                 # pytest配置文件
├── conftest.py                 # 全局conftest（可选）
├── conf.d/                     # 按域拆分的conftest
│   ├── __init__.py
│   ├── conftest_msearch.py     # msearch域conftest
│   ├── conftest_api.py         # API域conftest
│   └── conftest_media.py       # 媒体处理域conftest
├── .coverage/                  # 覆盖率报告目录（已gitignore）
│   ├── html/                   # HTML格式报告
│   ├── xml/                    # XML格式报告（供SonarQube）
│   └── csv/                    # CSV格式报告（供数据仓库）
├── .tmp/                       # 临时文件目录（已gitignore）
├── data/                       # 测试数据
│   ├── msearch/
│   │   └── v1/                 # msearch v1测试数据
│   │       ├── images/         # 测试图像
│   │       ├── videos/         # 测试视频
│   │       ├── audio/          # 测试音频
│   │       └── metadata/       # 测试元数据
│   └── api/
│       └── v2/                 # API v2测试数据
│           ├── requests/       # 测试请求
│           └── responses/      # 测试响应
├── fixtures/                   # 共享fixture
│   ├── __init__.py
│   ├── path_factory.py         # 路径生成器
│   ├── data_factory.py         # 数据生成器
│   └── mock_factory.py         # Mock对象工厂
├── unit/                       # 单元测试
│   ├── core/                   # 核心组件测试
│   │   ├── test_config_manager.py
│   │   ├── test_database_manager.py
│   │   ├── test_vector_store.py
│   │   ├── test_embedding_engine.py
│   │   ├── test_task_manager.py
│   │   └── test_hardware_detector.py
│   ├── data/                   # 数据层测试
│   │   ├── test_metadata_extractor.py
│   │   ├── test_thumbnail_generator.py
│   │   └── test_content_analyzer.py
│   ├── services/               # 服务层测试
│   │   ├── test_search_engine.py
│   │   ├── test_media_processor.py
│   │   ├── test_query_processor.py
│   │   └── test_result_ranker.py
│   ├── media/                  # 媒体处理测试
│   │   ├── test_video_processor.py
│   │   ├── test_audio_segmenter.py
│   │   └── test_file_indexer.py
│   ├── ui/                     # UI测试
│   │   └── test_main_window.py
│   └── utils/                  # 工具层测试
│       ├── test_error_handling.py
│       ├── test_file_utils.py
│       └── test_format_utils.py
├── integration/                # 集成测试
│   ├── it_multimodal_fusion.py
│   ├── it_config_manager.py
│   ├── it_database_architecture.py
│   └── it_api_endpoints.py
├── e2e/                        # 端到端测试
│   ├── e2e_database_architecture.py
│   ├── e2e_api_endpoints.py
│   └── e2e_user_workflow.py
└── benchmark/                  # 性能基准测试
    ├── test_msearch_benchmark.py
    ├── test_embedding_benchmark.py
    ├── test_search_benchmark.py
    ├── msearch.benchmark.json
    ├── msearch.benchmark.md
    ├── embedding.benchmark.json
    ├── embedding.benchmark.md
    ├── search.benchmark.json
    └── search.benchmark.md
```

### 1.2 命名规范

**测试文件命名**：
- 单元测试：`test_*.py`
- 集成测试：`it_*.py`
- 端到端测试：`e2e_*.py`
- 性能基准测试：`test_*_benchmark.py`

**测试函数命名**：
- 格式：`test_功能点_预期行为`
- 示例：
  - `test_config_manager_load_config_success`
  - `test_vector_store_insert_vector_success`
  - `test_embedding_engine_embed_image_invalid_path_raises_error`

**测试类命名**：
- 格式：`Test{模块名}`
- 示例：
  - `TestConfigManager`
  - `TestVectorStore`
  - `TestEmbeddingEngine`

## 2. 测试类型

### 2.1 单元测试

**目标**：测试单个函数或类的功能正确性

**范围**：
- 核心组件：config_manager、database_manager、vector_store、embedding_engine、task_manager、hardware_detector
- 数据层：metadata_extractor、thumbnail_generator、content_analyzer
- 服务层：search_engine、media_processor、query_processor、result_ranker
- 媒体处理：video_processor、audio_segmenter、file_indexer
- 工具层：error_handling、file_utils、format_utils

**编写规范**：

```python
def test_config_manager_load_config_success(tmp_path):
    """
    测试配置管理器加载配置成功
    
    Arrange:
        - 创建临时配置目录
        - 创建测试配置文件
    
    Act:
        - 加载配置
    
    Assert:
        - 配置加载成功
        - 配置值正确
    """
    # Arrange
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    config_file = config_dir / "config.json"
    config_file.write_text('{"test_key": "test_value"}')
    
    config_manager = ConfigManager(str(config_dir))
    
    # Act
    config_manager.initialize()
    config = config_manager.get_config()
    
    # Assert
    assert config is not None
    assert config["test_key"] == "test_value"
```

**覆盖率要求**：
- 核心组件：≥ 90%
- 数据层：≥ 85%
- 服务层：≥ 80%
- 工具层：≥ 85%

### 2.2 集成测试

**目标**：测试多个组件协同工作的正确性

**范围**：
- 多模态融合测试
- 配置管理集成测试
- 数据库架构集成测试
- API端点集成测试

**编写规范**：

```python
def it_multimodal_fusion_search_success(tmp_path):
    """
    集成测试：多模态融合搜索成功
    
    Arrange:
        - 初始化数据库和向量存储
        - 索引测试数据（图像、视频、音频）
        - 初始化搜索引擎
    
    Act:
        - 执行多模态搜索
    
    Assert:
        - 搜索结果正确
        - 结果排序合理
        - 性能满足要求
    """
    # Arrange
    config = {
        "data_dir": str(tmp_path / "data"),
        "vector_db_path": str(tmp_path / "vectors")
    }
    
    database_manager = DatabaseManager(config)
    database_manager.initialize()
    
    vector_store = VectorStore(str(tmp_path / "vectors"))
    vector_store.initialize()
    
    # 索引测试数据
    test_files = [
        {"path": "/test/image1.jpg", "type": "image"},
        {"path": "/test/video1.mp4", "type": "video"},
        {"path": "/test/audio1.mp3", "type": "audio"}
    ]
    
    for file_info in test_files:
        file_id = database_manager.add_file(file_info)
        vector = generate_test_vector(file_info["type"])
        vector_store.insert_vectors([{
            "id": f"{file_id}_{file_info['type']}",
            "vector": vector,
            "modality": file_info["type"],
            "file_id": file_id
        }])
    
    search_engine = SearchEngine(config, database_manager, vector_store)
    search_engine.initialize()
    
    # Act
    results = search_engine.search("测试查询", modalities=["image", "video", "audio"])
    
    # Assert
    assert len(results) > 0
    assert all(r["similarity"] > 0.7 for r in results)
    assert len(results) <= 20
```

**覆盖率要求**：
- 集成测试覆盖率：≥ 70%

### 2.3 端到端测试

**目标**：测试完整的用户工作流程

**范围**：
- 数据库架构端到端测试
- API端点端到端测试
- 用户工作流程端到端测试

**编写规范**：

```python
def e2e_user_workflow_index_and_search_success(tmp_path):
    """
    端到端测试：用户索引和搜索工作流程
    
    Arrange:
        - 启动API服务器
        - 准备测试文件
    
    Act:
        - 扫描目录
        - 索引文件
        - 执行搜索
    
    Assert:
        - 索引成功
        - 搜索结果正确
    """
    # Arrange
    from msearch.api_server import APIServer
    import requests
    
    api_server = APIServer(config={"data_dir": str(tmp_path)})
    api_server.start()
    
    base_url = "http://localhost:8000/api/v1"
    
    # 准备测试文件
    test_dir = tmp_path / "media"
    test_dir.mkdir()
    (test_dir / "test.jpg").write_bytes(b"fake_image_data")
    
    # Act
    # 扫描目录
    scan_response = requests.post(
        f"{base_url}/files/scan",
        json={"directory_path": str(test_dir), "recursive": True}
    )
    assert scan_response.status_code == 200
    
    # 等待索引完成
    time.sleep(5)
    
    # 执行搜索
    search_response = requests.post(
        f"{base_url}/search/multimodal",
        json={"query": "test", "limit": 10}
    )
    assert search_response.status_code == 200
    
    # Assert
    results = search_response.json()["data"]["results"]
    assert len(results) > 0
    assert results[0]["similarity"] > 0.7
    
    # Cleanup
    api_server.stop()
```

**覆盖率要求**：
- 端到端测试覆盖率：≥ 50%

### 2.4 性能基准测试

**目标**：测试系统性能和资源使用情况

**范围**：
- MSearch核心性能测试
- Embedding性能测试
- Search性能测试

**编写规范**：

```python
def test_msearch_benchmark_performance(tmp_path, benchmark):
    """
    性能基准测试：MSearch核心性能
    
    测试指标：
    - 文件扫描性能
    - 向量化性能
    - 搜索性能
    """
    config = {
        "data_dir": str(tmp_path / "data"),
        "vector_db_path": str(tmp_path / "vectors")
    }
    
    # 测试文件扫描性能
    def scan_files():
        file_indexer = FileIndexer(config)
        file_indexer.initialize()
        file_indexer.index_directory(str(tmp_path / "media"))
    
    scan_time = benchmark(scan_files)
    assert scan_time < 10.0  # 扫描100个文件应在10秒内完成
    
    # 测试向量化性能
    def embed_images():
        embedding_engine = EmbeddingEngine(config)
        embedding_engine.initialize()
        embedding_engine.embed_batch_images([
            str(tmp_path / f"media/image{i}.jpg")
            for i in range(100)
        ])
    
    embed_time = benchmark(embed_images)
    assert embed_time < 30.0  # 向量化100张图像应在30秒内完成
    
    # 测试搜索性能
    def search():
        search_engine = SearchEngine(config)
        search_engine.initialize()
        search_engine.search("test query", limit=20)
    
    search_time = benchmark(search)
    assert search_time < 1.0  # 搜索应在1秒内完成
```

**性能指标**：

| 指标 | 目标值 |
|------|--------|
| 文件扫描（100个文件） | < 10秒 |
| 图像向量化（100张） | < 30秒 |
| 视频向量化（10个，每个5秒） | < 60秒 |
| 音频向量化（10个，每个10秒） | < 60秒 |
| 搜索响应时间 | < 1秒 |
| 内存使用（空闲） | < 500MB |
| 内存使用（峰值） | < 4GB |

**报告格式**：

```json
{
  "module": "msearch",
  "version": "1.0.0",
  "timestamp": "2024-01-01T00:00:00Z",
  "environment": {
    "cpu": "Intel Core i7-9700K",
    "memory": "32GB",
    "gpu": "NVIDIA GeForce RTX 3080"
  },
  "benchmarks": [
    {
      "name": "file_scan",
      "iterations": 10,
      "mean": 8.5,
      "stddev": 0.5,
      "min": 7.8,
      "max": 9.2,
      "unit": "seconds"
    },
    {
      "name": "image_embedding",
      "iterations": 10,
      "mean": 25.3,
      "stddev": 2.1,
      "min": 23.5,
      "max": 28.1,
      "unit": "seconds"
    },
    {
      "name": "search",
      "iterations": 100,
      "mean": 0.8,
      "stddev": 0.1,
      "min": 0.6,
      "max": 1.2,
      "unit": "seconds"
    }
  ]
}
```

## 3. 测试工具

### 3.1 pytest

**配置文件**：`tests/pytest.ini`

```ini
[pytest]
# 测试目录
testpaths = .

# 测试文件模式
python_files = test_*.py it_*.py e2e_*.py

# 测试类模式
python_classes = Test*

# 测试函数模式
python_functions = test_*

# 标记
markers =
    unit: 单元测试
    integration: 集成测试
    e2e: 端到端测试
    benchmark: 性能基准测试
    slow: 慢速测试
    gpu: 需要GPU的测试

# 覆盖率配置
addopts =
    --strict-markers
    --verbose
    --tb=short
    --cov=../src
    --cov-report=html:.coverage/html
    --cov-report=xml:.coverage/xml/coverage.xml
    --cov-report=csv:.coverage/csv/coverage.csv
    --cov-fail-under=80

# 最小覆盖率
cov-fail-under = 80

# 排除的文件
norecursedirs = .git .tmp .coverage __pycache__ venv env

# 日志配置
log_cli = true
log_cli_level = INFO
log_cli_format = %(asctime)s [%(levelname)s] %(message)s
log_cli_date_format = %Y-%m-%d %H:%M:%S
```

### 3.2 pytest-cov

**覆盖率报告**：

```bash
# 生成HTML报告
pytest --cov=../src --cov-report=html:.coverage/html

# 生成XML报告（供SonarQube）
pytest --cov=../src --cov-report=xml:.coverage/xml/coverage.xml

# 生成CSV报告（供数据仓库）
pytest --cov=../src --cov-report=csv:.coverage/csv/coverage.csv

# 生成终端报告
pytest --cov=../src --cov-report=term-missing
```

**覆盖率目标**：

| 模块 | 目标覆盖率 |
|------|-----------|
| 核心组件 | ≥ 90% |
| 数据层 | ≥ 85% |
| 服务层 | ≥ 80% |
| 工具层 | ≥ 85% |
| 整体 | ≥ 80% |

### 3.3 pytest-benchmark

**性能基准测试**：

```bash
# 运行性能基准测试
pytest tests/benchmark/ --benchmark-only

# 生成性能报告
pytest tests/benchmark/ --benchmark-only --benchmark-json=.coverage/benchmark.json

# 比较性能
pytest tests/benchmark/ --benchmark-only --benchmark-compare
```

### 3.4 pytest-mock

**Mock对象**：

```python
from unittest.mock import Mock, patch, MagicMock

def test_with_mock():
    # 创建Mock对象
    mock_func = Mock(return_value="test_value")
    
    # 使用Mock对象
    result = mock_func("arg1", "arg2")
    
    # 验证调用
    mock_func.assert_called_once_with("arg1", "arg2")
    assert result == "test_value"

def test_with_patch():
    # 使用patch
    with patch('msearch.core.config_manager.load_config') as mock_load:
        mock_load.return_value = {"test": "value"}
        
        config_manager = ConfigManager("/path/to/config")
        config = config_manager.get_config()
        
        mock_load.assert_called_once()
        assert config == {"test": "value"}
```

### 3.5 pytest-asyncio

**异步测试**：

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result is not None
```

### 3.6 pytest-xdist

**并行测试**：

```bash
# 使用4个进程并行运行测试
pytest -n 4

# 自动检测CPU核心数
pytest -n auto
```

## 4. 测试Fixture

### 4.1 路径生成器

**文件**：`tests/fixtures/path_factory.py`

```python
import pytest
from pathlib import Path
from typing import Optional

class PathFactory:
    """路径生成器"""
    
    def __init__(self, tmp_path: Path):
        self.tmp_path = tmp_path
    
    def get_config_dir(self) -> Path:
        """获取配置目录"""
        config_dir = self.tmp_path / "config"
        config_dir.mkdir(exist_ok=True)
        return config_dir
    
    def get_data_dir(self) -> Path:
        """获取数据目录"""
        data_dir = self.tmp_path / "data"
        data_dir.mkdir(exist_ok=True)
        return data_dir
    
    def get_vector_db_dir(self) -> Path:
        """获取向量数据库目录"""
        vector_dir = self.tmp_path / "vectors"
        vector_dir.mkdir(exist_ok=True)
        return vector_dir
    
    def get_test_image_path(self, name: str = "test.jpg") -> Path:
        """获取测试图像路径"""
        image_dir = self.tmp_path / "images"
        image_dir.mkdir(exist_ok=True)
        image_path = image_dir / name
        if not image_path.exists():
            image_path.write_bytes(b"fake_image_data")
        return image_path
    
    def get_test_video_path(self, name: str = "test.mp4") -> Path:
        """获取测试视频路径"""
        video_dir = self.tmp_path / "videos"
        video_dir.mkdir(exist_ok=True)
        video_path = video_dir / name
        if not video_path.exists():
            video_path.write_bytes(b"fake_video_data")
        return video_path
    
    def get_test_audio_path(self, name: str = "test.mp3") -> Path:
        """获取测试音频路径"""
        audio_dir = self.tmp_path / "audio"
        audio_dir.mkdir(exist_ok=True)
        audio_path = audio_dir / name
        if not audio_path.exists():
            audio_path.write_bytes(b"fake_audio_data")
        return audio_path

@pytest.fixture
def path_factory(tmp_path):
    """路径生成器fixture"""
    return PathFactory(tmp_path)
```

### 4.2 数据生成器

**文件**：`tests/fixtures/data_factory.py`

```python
import pytest
import uuid
import numpy as np
from datetime import datetime
from typing import List, Dict, Any

class DataFactory:
    """数据生成器"""
    
    @staticmethod
    def generate_uuid() -> str:
        """生成UUID"""
        return str(uuid.uuid4())
    
    @staticmethod
    def generate_vector(dim: int = 512) -> List[float]:
        """生成测试向量"""
        return np.random.rand(dim).tolist()
    
    @staticmethod
    def generate_file_metadata(file_type: str = "image") -> Dict[str, Any]:
        """生成文件元数据"""
        return {
            "id": DataFactory.generate_uuid(),
            "file_path": f"/test/{file_type}_test.{file_type}",
            "file_name": f"{file_type}_test.{file_type}",
            "file_type": file_type,
            "file_size": 1024000,
            "file_hash": "a1b2c3d4e5f6" * 8,
            "created_at": datetime.now().timestamp(),
            "updated_at": datetime.now().timestamp(),
            "processed_at": None,
            "processing_status": "pending",
            "metadata": {}
        }
    
    @staticmethod
    def generate_vector_data(modality: str = "image") -> Dict[str, Any]:
        """生成向量数据"""
        return {
            "id": f"{DataFactory.generate_uuid()}_{modality}",
            "vector": DataFactory.generate_vector(),
            "modality": modality,
            "file_id": DataFactory.generate_uuid(),
            "segment_id": None,
            "start_time": None,
            "end_time": None,
            "metadata": {},
            "created_at": datetime.now().timestamp()
        }
    
    @staticmethod
    def generate_task(task_type: str = "file_embed") -> Dict[str, Any]:
        """生成任务数据"""
        return {
            "id": DataFactory.generate_uuid(),
            "task_type": task_type,
            "task_data": {},
            "priority": 5,
            "status": "pending",
            "created_at": datetime.now().timestamp(),
            "updated_at": datetime.now().timestamp(),
            "started_at": None,
            "completed_at": None,
            "retry_count": 0,
            "max_retries": 3,
            "result": None,
            "error": None,
            "progress": 0.0
        }

@pytest.fixture
def data_factory():
    """数据生成器fixture"""
    return DataFactory()
```

### 4.3 Mock对象工厂

**文件**：`tests/fixtures/mock_factory.py`

```python
import pytest
from unittest.mock import Mock, MagicMock
from typing import Dict, Any

class MockFactory:
    """Mock对象工厂"""
    
    @staticmethod
    def create_config_manager(config: Dict[str, Any] = None) -> Mock:
        """创建配置管理器Mock"""
        mock = Mock()
        mock.get_config.return_value = config or {"test": "value"}
        mock.initialize.return_value = True
        return mock
    
    @staticmethod
    def create_database_manager() -> Mock:
        """创建数据库管理器Mock"""
        mock = Mock()
        mock.add_file.return_value = "file_id"
        mock.get_file.return_value = {"id": "file_id", "file_path": "/test/file.jpg"}
        mock.update_file_status.return_value = True
        mock.initialize.return_value = True
        return mock
    
    @staticmethod
    def create_vector_store() -> Mock:
        """创建向量存储Mock"""
        mock = Mock()
        mock.insert_vectors.return_value = None
        mock.search_vectors.return_value = [
            {"id": "vec_1", "similarity": 0.95, "file_id": "file_1"}
        ]
        mock.initialize.return_value = True
        return mock
    
    @staticmethod
    def create_embedding_engine() -> Mock:
        """创建向量化引擎Mock"""
        mock = Mock()
        mock.embed_image.return_value = [0.1] * 512
        mock.embed_video_frame.return_value = [0.1] * 512
        mock.embed_audio.return_value = [0.1] * 512
        mock.embed_text.return_value = [0.1] * 512
        mock.initialize.return_value = True
        return mock

@pytest.fixture
def mock_factory():
    """Mock对象工厂fixture"""
    return MockFactory()
```

### 4.4 全局Fixture

**文件**：`tests/conftest_msearch.py`

```python
import pytest
from pathlib import Path
from msearch.core.config_manager import ConfigManager
from msearch.core.database_manager import DatabaseManager
from msearch.core.vector_store import VectorStore
from msearch.core.embedding_engine import EmbeddingEngine
from msearch.core.task_manager import TaskManager
from msearch.core.hardware_detector import HardwareDetector

@pytest.fixture
def config_manager(tmp_path):
    """配置管理器fixture"""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    
    config_file = config_dir / "config.json"
    config_file.write_text('{"test_key": "test_value"}')
    
    manager = ConfigManager(str(config_dir))
    manager.initialize()
    yield manager
    manager.close()

@pytest.fixture
def database_manager(tmp_path):
    """数据库管理器fixture"""
    db_path = tmp_path / "test.db"
    manager = DatabaseManager(str(db_path), wal_mode=True)
    manager.initialize()
    yield manager
    manager.close()

@pytest.fixture
def vector_store(tmp_path):
    """向量存储fixture"""
    vector_dir = tmp_path / "vectors"
    vector_dir.mkdir()
    store = VectorStore(str(vector_dir))
    store.initialize()
    yield store
    store.close()

@pytest.fixture
def embedding_engine(tmp_path):
    """向量化引擎fixture"""
    config = {
        "model_path": str(tmp_path / "models"),
        "device": "cpu"
    }
    engine = EmbeddingEngine(config)
    engine.initialize()
    yield engine
    engine.shutdown()
```

## 5. 测试流程

### 5.1 本地开发测试

**步骤**：

1. **编写测试**
   ```bash
   # 创建测试文件
   touch tests/unit/core/test_new_feature.py
   ```

2. **运行单元测试**
   ```bash
   # 运行所有单元测试
   pytest tests/unit/ -m unit
   
   # 运行特定测试文件
   pytest tests/unit/core/test_config_manager.py
   
   # 运行特定测试函数
   pytest tests/unit/core/test_config_manager.py::test_config_manager_load_config_success
   ```

3. **检查覆盖率**
   ```bash
   # 生成覆盖率报告
   pytest tests/unit/ --cov=../src --cov-report=html:.coverage/html
   
   # 查看HTML报告
   open .coverage/html/index.html
   ```

4. **修复问题**
   ```bash
   # 运行失败的测试
   pytest tests/unit/ -v --tb=short
   
   # 运行特定标记的测试
   pytest tests/unit/ -m "not slow"
   ```

### 5.2 持续集成测试

**CI流水线配置**：

```yaml
# .github/workflows/test.yml
name: Test

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    strategy:
      matrix:
        python-version: [3.8, 3.9, 3.10, 3.11]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov pytest-benchmark pytest-mock pytest-asyncio pytest-xdist
    
    - name: Run unit tests
      run: |
        pytest tests/unit/ -m unit --cov=src --cov-report=xml:.coverage/xml/coverage.xml --cov-report=html:.coverage/html
    
    - name: Run integration tests
      run: |
        pytest tests/integration/ -m integration
    
    - name: Run e2e tests
      run: |
        pytest tests/e2e/ -m e2e
    
    - name: Run benchmark tests
      run: |
        pytest tests/benchmark/ -m benchmark --benchmark-json=.coverage/benchmark.json
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: .coverage/xml/coverage.xml
        flags: unittests
        name: codecov-umbrella
    
    - name: Upload benchmark results
      uses: actions/upload-artifact@v3
      with:
        name: benchmark-results
        path: .coverage/benchmark.json
```

### 5.3 测试报告

**覆盖率报告**：

```bash
# 生成HTML报告
pytest --cov=src --cov-report=html:.coverage/html

# 生成XML报告（供SonarQube）
pytest --cov=src --cov-report=xml:.coverage/xml/coverage.xml

# 生成CSV报告（供数据仓库）
pytest --cov=src --cov-report=csv:.coverage/csv/coverage.csv
```

**性能报告**：

```bash
# 生成性能报告
pytest tests/benchmark/ --benchmark-only --benchmark-json=.coverage/benchmark.json

# 生成Markdown摘要
pytest tests/benchmark/ --benchmark-only --benchmark-json=.coverage/benchmark.json --benchmark-autosave
```

## 6. 测试最佳实践

### 6.1 AAA模式

**Arrange-Act-Assert模式**：

```python
def test_example():
    # Arrange：准备测试数据和环境
    test_data = {"key": "value"}
    expected_result = "expected"
    
    # Act：执行被测试的代码
    result = function_to_test(test_data)
    
    # Assert：验证结果是否符合预期
    assert result == expected_result
```

### 6.2 测试独立性

**避免测试依赖**：

```python
# 错误示例：测试之间有依赖
def test_create_file():
    global file_id
    file_id = create_file("test.txt")

def test_delete_file():
    delete_file(file_id)  # 依赖上一个测试

# 正确示例：测试独立
def test_create_file():
    file_id = create_file("test.txt")
    assert file_id is not None

def test_delete_file():
    file_id = create_file("test.txt")
    result = delete_file(file_id)
    assert result is True
```

### 6.3 测试可读性

**使用描述性的测试名称**：

```python
# 错误示例：名称不清晰
def test_1():
    pass

# 正确示例：名称清晰
def test_config_manager_load_config_success():
    pass

def test_config_manager_load_config_file_not_found_raises_error():
    pass
```

### 6.4 测试覆盖率

**避免为了覆盖率而测试**：

```python
# 错误示例：无意义的测试
def test_return_none():
    result = function_that_returns_none()
    assert result is None  # 只是为了提高覆盖率

# 正确示例：有意义的测试
def test_return_none_when_input_is_empty():
    result = function_that_returns_none("")
    assert result is None  # 测试边界条件
```

### 6.5 Mock使用

**合理使用Mock**：

```python
# 错误示例：过度Mock
def test_with_too_much_mock():
    with patch('module.function1'), \
         patch('module.function2'), \
         patch('module.function3'):
        result = function_to_test()
        assert result is not None

# 正确示例：只Mock外部依赖
def test_with_reasonable_mock():
    with patch('module.external_api_call') as mock_api:
        mock_api.return_value = {"data": "test"}
        result = function_to_test()
        assert result is not None
```

## 7. 测试维护

### 7.1 测试更新

**代码变更时更新测试**：

1. **添加新功能**
   - 先编写测试
   - 实现功能
   - 运行测试确保通过

2. **修改现有功能**
   - 先更新测试
   - 修改功能代码
   - 运行测试确保通过

3. **删除功能**
   - 删除相关测试
   - 运行测试确保没有失败

### 7.2 测试重构

**定期重构测试**：

1. **提取重复代码到fixture**
2. **合并相似的测试**
3. **删除过时的测试**
4. **优化慢速测试**

### 7.3 测试文档

**保持测试文档更新**：

1. **更新测试策略文档**
2. **更新测试用例说明**
3. **更新测试覆盖率目标**
4. **更新性能基准**

## 8. 测试问题排查

### 8.1 常见问题

**问题1：测试失败**

```bash
# 查看详细错误信息
pytest tests/unit/core/test_config_manager.py -v --tb=long

# 只运行失败的测试
pytest tests/unit/core/test_config_manager.py --lf

# 进入调试模式
pytest tests/unit/core/test_config_manager.py --pdb
```

**问题2：测试超时**

```bash
# 设置超时时间
pytest tests/unit/ --timeout=30

# 跳过慢速测试
pytest tests/unit/ -m "not slow"
```

**问题3：测试依赖**

```bash
# 随机化测试顺序
pytest tests/unit/ --random-order

# 重置测试环境
pytest tests/unit/ --forked
```

### 8.2 性能问题

**问题1：测试运行慢**

```bash
# 使用并行测试
pytest tests/unit/ -n 4

# 只运行快速测试
pytest tests/unit/ -m "not slow"

# 使用缓存
pytest tests/unit/ --cache-clear
```

**问题2：内存泄漏**

```bash
# 监控内存使用
pytest tests/unit/ --memprof

# 使用内存分析工具
pytest tests/unit/ --memprof-top=10
```

## 9. 附录

### 9.1 测试命令速查

```bash
# 运行所有测试
pytest

# 运行单元测试
pytest tests/unit/ -m unit

# 运行集成测试
pytest tests/integration/ -m integration

# 运行端到端测试
pytest tests/e2e/ -m e2e

# 运行性能测试
pytest tests/benchmark/ -m benchmark

# 生成覆盖率报告
pytest --cov=src --cov-report=html:.coverage/html

# 并行运行测试
pytest -n 4

# 只运行失败的测试
pytest --lf

# 只运行上次失败的测试
pytest --ff

# 显示测试输出
pytest -s

# 显示详细输出
pytest -v

# 进入调试模式
pytest --pdb

# 设置超时
pytest --timeout=30

# 跳过慢速测试
pytest -m "not slow"

# 随机化测试顺序
pytest --random-order
```

### 9.2 测试标记

```python
import pytest

# 单元测试
@pytest.mark.unit
def test_unit_example():
    pass

# 集成测试
@pytest.mark.integration
def test_integration_example():
    pass

# 端到端测试
@pytest.mark.e2e
def test_e2e_example():
    pass

# 性能测试
@pytest.mark.benchmark
def test_benchmark_example():
    pass

# 慢速测试
@pytest.mark.slow
def test_slow_example():
    pass

# 需要GPU的测试
@pytest.mark.gpu
def test_gpu_example():
    pass

# 跳过测试
@pytest.mark.skip(reason="Not implemented yet")
def test_skip_example():
    pass

# 条件跳过
@pytest.mark.skipif(sys.version_info < (3, 8), reason="Requires Python 3.8+")
def test_skipif_example():
    pass

# 预期失败
@pytest.mark.xfail
def test_xfail_example():
    pass
```

### 9.3 测试配置

**pytest.ini**：

```ini
[pytest]
testpaths = .
python_files = test_*.py it_*.py e2e_*.py
python_classes = Test*
python_functions = test_*

markers =
    unit: 单元测试
    integration: 集成测试
    e2e: 端到端测试
    benchmark: 性能基准测试
    slow: 慢速测试
    gpu: 需要GPU的测试

addopts =
    --strict-markers
    --verbose
    --tb=short
    --cov=../src
    --cov-report=html:.coverage/html
    --cov-report=xml:.coverage/xml/coverage.xml
    --cov-report=csv:.coverage/csv/coverage.csv
    --cov-fail-under=80

cov-fail-under = 80
norecursedirs = .git .tmp .coverage __pycache__ venv env

log_cli = true
log_cli_level = INFO
log_cli_format = %(asctime)s [%(levelname)s] %(message)s
log_cli_date_format = %Y-%m-%d %H:%M:%S
```

### 9.4 测试依赖

**requirements-test.txt**：

```
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-benchmark>=4.0.0
pytest-mock>=3.11.1
pytest-asyncio>=0.21.0
pytest-xdist>=3.3.1
pytest-timeout>=2.1.0
pytest-random-order>=3.12.0
pytest-memprof>=0.6.0
```

### 9.5 测试资源

**官方文档**：
- [pytest文档](https://docs.pytest.org/)
- [pytest-cov文档](https://pytest-cov.readthedocs.io/)
- [pytest-benchmark文档](https://pytest-benchmark.readthedocs.io/)

**最佳实践**：
- [Python测试最佳实践](https://docs.python-guide.org/writing/tests/)
- [测试驱动开发](https://en.wikipedia.org/wiki/Test-driven_development)
