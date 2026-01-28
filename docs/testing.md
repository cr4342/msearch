# 测试策略文档

**文档版本**：v1.0  
**最后更新**：2026-01-19  
**对应设计文档**：[design.md](./design.md)  

---

> **文档定位**：本文档是 [design.md](./design.md) 的补充文档，详细展开第 8 部分"测试与质量"的内容。

**相关文档**：
- [design.md](./design.md) - 主设计文档
- [deployment.md](./deployment.md) - 部署与运维文档

---

## 概述

本文档详细描述了 msearch 系统的测试策略、测试方法、测试用例和测试流程。

**测试目标**：
- 确保系统功能正确性
- 确保系统性能满足要求
- 确保系统稳定性和可靠性
- 确保代码质量和可维护性
- 提供测试覆盖度报告

**测试类型**：
- 单元测试（Unit Testing）
- 集成测试（Integration Testing）
- 端到端测试（E2E Testing）
- 性能测试（Performance Testing）
- 基准测试（Benchmark Testing）
- 回归测试（Regression Testing）

---

## 测试环境

### 2.1 硬件环境

**测试环境配置**：
- **CPU**：Intel Core i7-10700K（8核16线程）
- **内存**：32GB DDR4 3200MHz
- **GPU**：NVIDIA RTX 3080（10GB VRAM）
- **存储**：1TB NVMe SSD
- **网络**：1000Mbps 以太网

**最低测试配置**：
- **CPU**：Intel Core i5-8400（6核）
- **内存**：16GB RAM
- **GPU**：NVIDIA GTX 1080（8GB VRAM）
- **存储**：256GB SSD

### 2.2 软件环境

**操作系统**：
- **Windows**：Windows 10 22H2 64-bit
- **macOS**：macOS 13.0 Ventura
- **Linux**：Ubuntu 22.04 LTS 64-bit

**软件版本**：
- **Python**：3.10.12
- **PyTorch**：2.0.1（CUDA 11.8）
- **CUDA**：11.8
- **cuDNN**：8.7.0
- **FFmpeg**：5.1+

**测试框架**：
- **测试运行器**：pytest 7.4+
- **覆盖率工具**：pytest-cov 4.1+
- **基准测试**：pytest-benchmark 4.0+
- **Mock 工具**：unittest.mock
- **异步测试**：pytest-asyncio 0.21+

### 2.3 测试数据

**测试数据位置**：`tests/data/`  
**测试数据结构**：
```
tests/data/
├── msearch/
│   ├── v1/
│   │   ├── images/          # 测试图像（jpg, png, bmp）
│   │   ├── videos/          # 测试视频（mp4, avi, mov）
│   │   ├── audios/          # 测试音频（mp3, wav, aac）
│   │   ├── texts/           # 测试文本（txt, md）
│   │   └── fixtures/        # 测试 fixtures
│   └── v2/
│       └── ...              # 新版本测试数据
└── common/                  # 通用测试数据
    ├── configs/             # 测试配置文件
    ├── databases/           # 测试数据库
    └── models/              # 测试模型（小型模型）
```

**测试数据要求**：
- 图像：多种格式（jpg, png, bmp），多种尺寸（128x128 到 4K）
- 视频：多种格式（mp4, avi, mov），多种时长（10秒到5分钟）
- 音频：多种格式（mp3, wav, aac），多种时长（10秒到2分钟）
- 文本：多种语言（中文、英文），多种格式（txt, md）

**测试数据管理**：
- 测试数据应尽可能小（便于快速测试）
- 测试数据应覆盖各种场景（正常、边界、异常）
- 测试数据应定期更新
- 测试数据不应包含敏感信息

---

## 测试类型与方法

### 3.1 单元测试

**定义**：对单个函数、方法或类进行测试，验证其功能正确性。

**目标**：
- 验证单个函数的正确性
- 验证边界条件处理
- 验证错误处理
- 验证参数验证

**范围**：
- 所有工具函数
- 所有数据模型
- 所有业务逻辑函数
- 所有配置管理函数
- 所有工具类

**覆盖率要求**：
- 行覆盖率：≥ 80%
- 分支覆盖率：≥ 70%
- 函数覆盖率：≥ 85%

**测试文件命名**：`test_<模块名>.py`  
**测试文件位置**：`tests/unit/`  

**测试示例**：
```python
# tests/unit/test_config.py

import pytest
from src.core.config.config_manager import ConfigManager

class TestConfigManager:
    """配置管理器单元测试"""
    
    def test_load_config_success(self, tmp_path):
        """测试成功加载配置文件"""
        # Arrange
        config_content = """
version: "2.0"
data:
  data_dir: "data"
models:
  [配置驱动模型]:
    model_name: "[配置驱动模型]"
    device: "cuda"
"""
        config_file = tmp_path / "config.yml"
        config_file.write_text(config_content)
        
        # Act
        config_manager = ConfigManager(config_file_path=str(config_file))
        config = config_manager.load_config()
        
        # Assert
        assert config is not None
        assert config["version"] == "2.0"
        assert config["data"]["data_dir"] == "data"
        assert config["models"]["[配置驱动模型]"]["model_name"] == "[配置驱动模型]"
    
    def test_load_config_file_not_found(self):
        """测试加载不存在的配置文件"""
        # Arrange
        config_manager = ConfigManager(config_file_path="/path/to/nonexistent/config.yml")
        
        # Act & Assert
        with pytest.raises(FileNotFoundError):
            config_manager.load_config()
    
    def test_load_config_invalid_format(self, tmp_path):
        """测试加载格式错误的配置文件"""
        # Arrange
        config_file = tmp_path / "config.yml"
        config_file.write_text("invalid yaml content")
        
        config_manager = ConfigManager(config_file_path=str(config_file))
        
        # Act & Assert
        with pytest.raises(Exception):
            config_manager.load_config()
    
    def test_get_config_section(self, tmp_path):
        """测试获取配置节"""
        # Arrange
        config_content = """
models:
  [配置驱动模型]:
    model_name: "[配置驱动模型]"
    device: "cuda"
  [配置驱动模型]:
    model_name: "[配置驱动模型]"
    device: "cuda"
"""
        config_file = tmp_path / "config.yml"
        config_file.write_text(config_content)
        
        config_manager = ConfigManager(config_file_path=str(config_file))
        config = config_manager.load_config()
        
        # Act
        image_config = config_manager.get_config_section("models.[配置驱动模型]")
        audio_config = config_manager.get_config_section("models.[配置驱动模型]")
        
        # Assert
        assert image_config["model_name"] == "[配置驱动模型]"
        assert audio_config["model_name"] == "[配置驱动模型]"
```

**运行单元测试**：
```bash
# 运行所有单元测试
pytest tests/unit/ -v

# 运行特定模块测试
pytest tests/unit/test_config.py -v

# 运行特定测试类
pytest tests/unit/test_config.py::TestConfigManager -v

# 运行特定测试方法
pytest tests/unit/test_config.py::TestConfigManager::test_load_config_success -v

# 生成覆盖率报告
pytest tests/unit/ -v --cov=src --cov-report=html --cov-report=xml --cov-report=term-missing

# 查看覆盖率报告
# HTML：htmlcov/index.html
# XML：coverage.xml
```

### 3.2 集成测试

**定义**：测试多个模块或组件之间的交互，验证集成后的功能正确性。

**目标**：
- 验证模块之间的接口正确性
- 验证数据流转正确性
- 验证依赖关系正确性
- 验证异常处理正确性

**范围**：
- 配置管理与其他模块的集成
- 模型加载与推理的集成
- 数据库与其他模块的集成
- 任务调度器与执行器的集成
- API 服务器与核心模块的集成

**测试文件命名**：`it_<模块名>.py`  
**测试文件位置**：`tests/integration/`  

**测试示例**：
```python
# tests/integration/it_config_manager.py

import pytest
from src.core.config.config_manager import ConfigManager
from src.core.embedding.embedding_engine import EmbeddingEngine

class TestConfigEmbeddingIntegration:
    """配置管理与嵌入引擎集成测试"""
    
    def test_config_embedding_integration(self, tmp_path, config_fixture):
        """测试配置管理与嵌入引擎的集成"""
        # Arrange
        config_manager = ConfigManager(config_file_path=config_fixture)
        config = config_manager.load_config()
        
        # Act
        embedding_engine = EmbeddingEngine(config=config)
        
        # Assert
        assert embedding_engine is not None
        assert embedding_engine.[配置驱动模型]_config is not None
        assert embedding_engine.[配置驱动模型]_config is not None
        assert embedding_engine.[配置驱动模型]_config["model_name"] == config["models"]["[配置驱动模型]"]["model_name"]
        assert embedding_engine.[配置驱动模型]_config["model_name"] == config["models"]["[配置驱动模型]"]["model_name"]
    
    def test_embedding_engine_with_different_configs(self, tmp_path):
        """测试嵌入引擎使用不同配置"""
        # Arrange
        # 配置 1：使用 GPU
        config_content_1 = """
models:
  [配置驱动模型]:
    model_name: "[配置驱动模型]"
    device: "cuda"
    precision: "float16"
    batch_size: 16
  [配置驱动模型]:
    model_name: "[配置驱动模型]"
    device: "cuda"
"""
        config_file_1 = tmp_path / "config_gpu.yml"
        config_file_1.write_text(config_content_1)
        
        # 配置 2：使用 CPU
        config_content_2 = """
models:
  [配置驱动模型]:
    model_name: "[配置驱动模型]"
    device: "cpu"
    precision: "float32"
    batch_size: 8
  [配置驱动模型]:
    model_name: "[配置驱动模型]"
    device: "cpu"
"""
        config_file_2 = tmp_path / "config_cpu.yml"
        config_file_2.write_text(config_content_2)
        
        # Act
        config_manager_1 = ConfigManager(config_file_path=str(config_file_1))
        config_1 = config_manager_1.load_config()
        embedding_engine_1 = EmbeddingEngine(config=config_1)
        
        config_manager_2 = ConfigManager(config_file_path=str(config_file_2))
        config_2 = config_manager_2.load_config()
        embedding_engine_2 = EmbeddingEngine(config=config_2)
        
        # Assert
        assert embedding_engine_1.[配置驱动模型]_config["device"] == "cuda"
        assert embedding_engine_1.[配置驱动模型]_config["precision"] == "float16"
        assert embedding_engine_1.[配置驱动模型]_config["batch_size"] == 16
        
        assert embedding_engine_2.[配置驱动模型]_config["device"] == "cpu"
        assert embedding_engine_2.[配置驱动模型]_config["precision"] == "float32"
        assert embedding_engine_2.[配置驱动模型]_config["batch_size"] == 8
```

**运行集成测试**：
```bash
# 运行所有集成测试
pytest tests/integration/ -v

# 运行特定模块测试
pytest tests/integration/it_config_manager.py -v

# 生成覆盖率报告
pytest tests/integration/ -v --cov=src --cov-report=html --cov-report=xml
```

### 3.3 端到端测试

**定义**：测试整个系统的功能，从用户输入到系统输出的完整流程。

**目标**：
- 验证系统功能完整性
- 验证用户体验正确性
- 验证系统稳定性
- 验证系统性能

**范围**：
- 文件上传与处理
- 索引与检索
- 任务管理
- API 接口
- Web UI 功能

**测试文件命名**：`e2e_<模块名>.py`  
**测试文件位置**：`tests/e2e/`  

**测试示例**：
```python
# tests/e2e/e2e_database_architecture.py

import pytest
import requests
import time
from src.core.database.database_manager import DatabaseManager

class TestDatabaseArchitecture:
    """数据库架构端到端测试"""
    
    def test_database_connection_and_operations(self, tmp_path, config_fixture):
        """测试数据库连接和基本操作"""
        # Arrange
        db_path = tmp_path / "test.db"
        
        # Act
        db_manager = DatabaseManager(db_path=str(db_path))
        db_manager.connect()
        
        # 测试创建表
        db_manager.execute("""
        CREATE TABLE IF NOT EXISTS test_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT NOT NULL,
            file_name TEXT NOT NULL,
            file_type TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(file_path)
        )
        """)
        
        # 测试插入数据
        db_manager.execute(
            "INSERT INTO test_files (file_path, file_name, file_type, file_size) VALUES (?, ?, ?, ?)",
            ("/path/to/test.jpg", "test.jpg", "image", 102400)
        )
        db_manager.commit()
        
        # 测试查询数据
        result = db_manager.fetch_one("SELECT * FROM test_files WHERE file_name = ?", ("test.jpg",))
        
        # Assert
        assert result is not None
        assert result[1] == "/path/to/test.jpg"
        assert result[2] == "test.jpg"
        assert result[3] == "image"
        assert result[4] == 102400
        
        # Cleanup
        db_manager.close()
    
    def test_database_transaction_rollback(self, tmp_path):
        """测试数据库事务回滚"""
        # Arrange
        db_path = tmp_path / "test_transaction.db"
        db_manager = DatabaseManager(db_path=str(db_path))
        db_manager.connect()
        
        db_manager.execute("""
        CREATE TABLE IF NOT EXISTS test_transaction (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            value INTEGER NOT NULL
        )
        """)
        db_manager.commit()
        
        # Act
        try:
            db_manager.execute("INSERT INTO test_transaction (value) VALUES (1)")
            db_manager.execute("INSERT INTO test_transaction (value) VALUES (2)")
            # 触发错误
            db_manager.execute("INSERT INTO test_transaction (value) VALUES ('invalid')")
            db_manager.commit()
        except Exception as e:
            db_manager.rollback()
        
        # Assert
        result = db_manager.fetch_one("SELECT COUNT(*) FROM test_transaction")
        assert result[0] == 0  # 事务回滚，没有数据插入
        
        # Cleanup
        db_manager.close()
```

**运行端到端测试**：
```bash
# 运行所有端到端测试
pytest tests/e2e/ -v

# 运行特定模块测试
pytest tests/e2e/e2e_database_architecture.py -v

# 生成覆盖率报告
pytest tests/e2e/ -v --cov=src --cov-report=html --cov-report=xml
```

### 3.4 性能测试

**定义**：测试系统的性能指标，包括响应时间、吞吐量、资源使用率等。

**目标**：
- 验证系统性能满足要求
- 识别性能瓶颈
- 优化系统性能
- 建立性能基准

**范围**：
- 模型推理性能
- 检索性能
- 索引性能
- 数据库性能
- API 性能

**测试指标**：
| 指标 | 目标值 | 说明 |
|------|-------|------|
| 图像推理速度 | < 100ms/张 | 图像向量化时间 |
| 视频推理速度 | < 500ms/秒视频 | 视频向量化时间（每秒视频） |
| 音频推理速度 | < 1000ms/段音频 | 音频向量化时间（每段音频） |
| 文本检索速度 | < 500ms | 文本查询响应时间 |
| 图像检索速度 | < 1000ms | 图像查询响应时间 |
| 音频检索速度 | < 1500ms | 音频查询响应时间 |
| 图像索引速度 | < 1 秒/张 | 图像索引时间 |
| 视频索引速度 | < 30 秒/分钟视频 | 视频索引时间（每分钟视频） |
| 音频索引速度 | < 10 秒/分钟音频 | 音频索引时间（每分钟音频） |
| CPU 使用率 | < 80% | 系统 CPU 使用率 |
| 内存使用率 | < 80% | 系统内存使用率 |
| GPU 显存使用率 | < 90% | GPU 显存使用率 |

**测试文件位置**：`tests/performance/`  

**测试示例**：
```python
# tests/performance/test_embedding_performance.py

import pytest
import time
import numpy as np
from src.core.embedding.embedding_engine import EmbeddingEngine

class TestEmbeddingPerformance:
    """嵌入引擎性能测试"""
    
    def test_image_embedding_performance(self, embedding_engine, test_images):
        """测试图像嵌入性能"""
        # Arrange
        images = test_images  # 测试图像列表
        
        # Act
        start_time = time.time()
        for image_path in images:
            embedding_engine.embed_image(image_path=image_path)
        end_time = time.time()
        
        # Assert
        total_time = end_time - start_time
        avg_time_per_image = total_time / len(images)
        print(f"Image embedding performance: {len(images)} images in {total_time:.2f}s, avg {avg_time_per_image*1000:.2f}ms/image")
        
        assert avg_time_per_image < 0.1  # 平均每张图像 < 100ms
    
    def test_video_embedding_performance(self, embedding_engine, test_videos):
        """测试视频嵌入性能"""
        # Arrange
        videos = test_videos  # 测试视频列表
        
        # Act
        start_time = time.time()
        for video_path in videos:
            embedding_engine.embed_video(video_path=video_path)
        end_time = time.time()
        
        # Assert
        total_time = end_time - start_time
        # 假设测试视频总时长为 10 分钟
        total_duration = 10 * 60  # 秒
        avg_time_per_second = total_time / total_duration
        print(f"Video embedding performance: {total_duration}s video in {total_time:.2f}s, avg {avg_time_per_second:.2f}x realtime")
        
        assert avg_time_per_second < 0.5  # 每秒视频 < 500ms
    
    def test_batch_embedding_performance(self, embedding_engine, test_images):
        """测试批量嵌入性能"""
        # Arrange
        images = test_images[:32]  # 32 张图像
        
        # Act
        start_time = time.time()
        embeddings = embedding_engine.embed_images_batch(image_paths=images)
        end_time = time.time()
        
        # Assert
        total_time = end_time - start_time
        avg_time_per_image = total_time / len(images)
        print(f"Batch embedding performance: {len(images)} images in {total_time:.2f}s, avg {avg_time_per_image*1000:.2f}ms/image")
        
        assert len(embeddings) == len(images)
        assert avg_time_per_image < 0.05  # 批量嵌入 < 50ms/张
```

**运行性能测试**：
```bash
# 运行性能测试
pytest tests/performance/ -v

# 生成性能报告
pytest tests/performance/ -v --benchmark-autosave

# 查看性能报告
# 报告位置：.benchmarks/
```

### 3.5 基准测试

**定义**：测试系统的基准性能，建立性能基线，用于后续回归测试。

**目标**：
- 建立性能基准
- 监控性能变化
- 验证性能优化效果
- 识别性能退化

**范围**：
- 核心功能性能
- 关键路径性能
- 高频操作性能

**测试文件位置**：`tests/benchmark/`  
**输出报告**：`{模块}.benchmark.json` 和 `{模块}.benchmark.md`  

**测试示例**：
```python
# tests/benchmark/test_msearch_benchmark.py

import pytest
import json
import time
from datetime import datetime
from src.core.embedding.embedding_engine import EmbeddingEngine

class TestMsearchBenchmark:
    """msearch 基准测试"""
    
    def test_image_embedding_benchmark(self, embedding_engine, benchmark, test_images):
        """图像嵌入基准测试"""
        def embed_image():
            for image_path in test_images[:10]:
                embedding_engine.embed_image(image_path=image_path)
        
        result = benchmark(embed_image)
        
        # 保存基准结果
        self._save_benchmark_result(
            module="embedding_engine",
            test_name="image_embedding",
            result=result,
            unit="ms/image",
            value=result.stats['mean'] * 1000 / 10
        )
    
    def test_text_search_benchmark(self, embedding_engine, benchmark, vector_store, test_queries):
        """文本检索基准测试"""
        def search_text():
            for query in test_queries[:10]:
                vector_store.search_text(query=query, top_k=20)
        
        result = benchmark(search_text)
        
        # 保存基准结果
        self._save_benchmark_result(
            module="vector_store",
            test_name="text_search",
            result=result,
            unit="ms/query",
            value=result.stats['mean'] * 1000 / 10
        )
    
    def _save_benchmark_result(self, module, test_name, result, unit, value):
        """保存基准测试结果"""
        benchmark_data = {
            "module": module,
            "test_name": test_name,
            "timestamp": datetime.now().isoformat(),
            "unit": unit,
            "value": value,
            "stats": {
                "mean": result.stats['mean'],
                "stddev": result.stats['stddev'],
                "min": result.stats['min'],
                "max": result.stats['max'],
                "median": result.stats['median']
            },
            "params": {
                "iterations": result.stats['iterations'],
                "rounds": result.stats['rounds']
            }
        }
        
        # 保存 JSON 报告
        json_path = f"tests/benchmark/{module}.benchmark.json"
        with open(json_path, 'w') as f:
            json.dump(benchmark_data, f, indent=2)
        
        # 保存 Markdown 摘要
        md_path = f"tests/benchmark/{module}.benchmark.md"
        md_content = f"""# {module} 基准测试报告

**测试时间**：{benchmark_data['timestamp']}
**测试名称**：{test_name}

## 测试结果

| 指标 | 值 |
|------|-----|
| 平均值 | {value:.2f} {unit} |
| 标准差 | {benchmark_data['stats']['stddev']*1000:.2f} ms |
| 最小值 | {benchmark_data['stats']['min']*1000:.2f} ms |
| 最大值 | {benchmark_data['stats']['max']*1000:.2f} ms |
| 中位数 | {benchmark_data['stats']['median']*1000:.2f} ms |

## 测试参数

| 参数 | 值 |
|------|-----|
| 迭代次数 | {benchmark_data['params']['iterations']} |
| 轮数 | {benchmark_data['params']['rounds']} |
"""
        with open(md_path, 'w') as f:
            f.write(md_content)
```

**运行基准测试**：
```bash
# 运行基准测试
pytest tests/benchmark/ -v --benchmark-autosave

# 查看基准报告
cat tests/benchmark/embedding_engine.benchmark.json
cat tests/benchmark/embedding_engine.benchmark.md

# 比较基准结果
pytest tests/benchmark/ -v --benchmark-compare=0001
```

### 3.6 回归测试

**定义**：在代码变更后，运行所有测试用例，确保没有引入新的问题。

**目标**：
- 验证代码变更没有破坏现有功能
- 确保系统稳定性
- 提高代码质量

**范围**：
- 所有单元测试
- 所有集成测试
- 所有端到端测试
- 关键性能测试

**触发时机**：
- 代码提交前
- Pull Request 时
- 代码合并后
- 版本发布前

**运行回归测试**：
```bash
# 运行所有测试
pytest tests/ -v

# 运行所有测试并生成覆盖率报告
pytest tests/ -v --cov=src --cov-report=html --cov-report=xml --cov-report=term-missing

# 运行特定目录测试
pytest tests/unit/ tests/integration/ -v

# 运行标记为关键的测试
pytest tests/ -v -m "critical"
```

---

## 测试流程

### 4.1 开发阶段测试

**流程**：
1. **编写代码**：开发人员实现功能
2. **编写单元测试**：开发人员为新代码编写单元测试
3. **运行单元测试**：开发人员在本地运行单元测试
4. **检查覆盖率**：确保代码覆盖率达到要求
5. **提交代码**：提交代码到版本控制系统

**要求**：
- 新代码必须有单元测试
- 单元测试覆盖率 ≥ 80%
- 所有单元测试必须通过

### 4.2 代码审查阶段测试

**流程**：
1. **创建 Pull Request**：开发人员创建 PR
2. **自动运行测试**：CI/CD 系统自动运行所有测试
3. **代码审查**：审查人员审查代码和测试结果
4. **修复问题**：开发人员修复发现的问题
5. **合并代码**：代码审查通过后合并

**要求**：
- 所有测试必须通过
- 代码覆盖率不得下降
- 性能不得退化

### 4.3 预发布阶段测试

**流程**：
1. **创建发布分支**：创建发布分支
2. **运行完整测试**：运行所有测试（单元、集成、端到端、性能）
3. **生成测试报告**：生成测试报告和覆盖率报告
4. **验证功能**：手动验证关键功能
5. **性能测试**：运行性能测试和基准测试
6. **安全测试**：进行安全扫描和漏洞检测
7. **发布版本**：所有测试通过后发布版本

**要求**：
- 所有测试必须通过
- 代码覆盖率 ≥ 80%
- 性能满足要求
- 没有严重 Bug

### 4.4 发布后测试

**流程**：
1. **部署到生产环境**：部署新版本到生产环境
2. **监控系统**：监控系统运行状态
3. **收集反馈**：收集用户反馈
4. **修复问题**：修复发现的问题
5. **更新测试**：更新测试用例

**要求**：
- 系统稳定运行
- 性能满足要求
- 用户反馈良好

---

## 测试工具与配置

### 5.1 pytest 配置

**配置文件**：`tests/pytest.ini`  

**配置内容**：
```ini
[pytest]
# 测试目录
testpaths = tests

# 测试文件匹配
python_files = test_*.py it_*.py e2e_*.py
python_classes = Test*
python_functions = test_*

# 忽略目录
ignore = .git .tox .venv __pycache__ *.pyc *.pyo

# 覆盖率配置
addopts = 
    --cov=src
    --cov-report=html:tests/.coverage/html
    --cov-report=xml:tests/.coverage/coverage.xml
    --cov-report=term-missing
    --cov-config=tests/.coveragerc
    -v
    --tb=short

# 并发测试
# addopts += -n auto

# 基准测试
addopts += --benchmark-autosave

# 标记
markers =
    critical: 关键测试用例
    slow: 慢速测试用例
    integration: 集成测试
    e2e: 端到端测试
    performance: 性能测试
    benchmark: 基准测试

# 自定义 fixture 目录
pythonpath = src tests

# 异步测试
asyncio_mode = auto
```

### 5.2 覆盖率配置

**配置文件**：`tests/.coveragerc`  

**配置内容**：
```ini
[run]
# 源代码目录
source = src

# 忽略的文件
omit =
    src/**/__init__.py
    src/**/config.py
    src/**/version.py
    src/**/main.py
    src/api/**
    src/ui/**
    tests/**

# 分支覆盖率
branch = true

[report]
# 显示未覆盖的行
show_missing = true

# 跳过空行
skip_covered = false

# 跳过隐藏文件
skip_empty = true

# 排序方式
sort = Covered

# 最低覆盖率
fail_under = 80

[html]
# HTML 报告目录
directory = tests/.coverage/html

[xml]
# XML 报告输出
output = tests/.coverage/coverage.xml
```

### 5.3 测试 Fixtures

**Fixtures 位置**：`tests/fixtures/`  

**Fixtures 示例**：
```python
# tests/fixtures/path_factory.py

import pytest
import tempfile
import os
from pathlib import Path

@pytest.fixture(scope="session")
def test_data_dir():
    """测试数据目录"""
    return Path(__file__).parent.parent / "data" / "msearch" / "v1"

@pytest.fixture(scope="session")
def test_images(test_data_dir):
    """测试图像列表"""
    image_dir = test_data_dir / "images"
    if not image_dir.exists():
        return []
    
    image_extensions = [".jpg", ".jpeg", ".png", ".bmp", ".gif"]
    images = []
    for ext in image_extensions:
        images.extend(image_dir.glob(f"*{ext}"))
    
    return images[:10]  # 返回前 10 张图像

@pytest.fixture(scope="session")
def test_videos(test_data_dir):
    """测试视频列表"""
    video_dir = test_data_dir / "videos"
    if not video_dir.exists():
        return []
    
    video_extensions = [".mp4", ".avi", ".mov", ".mkv"]
    videos = []
    for ext in video_extensions:
        videos.extend(video_dir.glob(f"*{ext}"))
    
    return videos[:5]  # 返回前 5 个视频

@pytest.fixture(scope="session")
def test_audios(test_data_dir):
    """测试音频列表"""
    audio_dir = test_data_dir / "audios"
    if not audio_dir.exists():
        return []
    
    audio_extensions = [".mp3", ".wav", ".aac", ".flac"]
    audios = []
    for ext in audio_extensions:
        audios.extend(audio_dir.glob(f"*{ext}"))
    
    return audios[:5]  # 返回前 5 个音频

@pytest.fixture(scope="session")
def test_queries():
    """测试查询列表"""
    return [
        "海滩日落",
        "城市夜景",
        "山脉风景",
        "人物肖像",
        "动物世界",
        "美食烹饪",
        "运动健身",
        "科技产品",
        "自然风景",
        "建筑设计"
    ]

@pytest.fixture(scope="function")
def tmp_config(tmp_path):
    """临时配置文件"""
    config_content = """
version: "2.0"
data:
  data_dir: "data"
  model_cache_dir: "data/models"
  database_dir: "data/database"
models:
  [配置驱动模型]:
    model_name: "[配置驱动模型]"
    model_path: "data/models/[配置驱动模型]"
    embedding_dim: 512  # [配置驱动模型]的嵌入维度
    device: "cuda"
    precision: "float16"
    batch_size: 16
    input_resolution: 512
  [配置驱动模型]:
    model_name: "[配置驱动模型]"
    model_path: "[配置驱动模型]"
    vector_dim: 512
    device: "cuda"
    precision: "float16"
    batch_size: 8
    sample_rate: 44100
vector_store:
  type: "lancedb"
  path: "data/database/lancedb"
  table_name: "unified_vectors"
database:
  type: "sqlite"
  path: "data/database/sqlite/msearch.db"
task_scheduler:
  max_workers: 4
  queue_size: 1000
file_monitor:
  enabled: true
  watch_paths: []
  scan_interval: 60
api:
  host: "0.0.0.0"
  port: 8000
  workers: 1
logging:
  level: "INFO"
  format: "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"
  rotation: "1 day"
  retention: "7 days"
performance:
  video_processing:
    frame_interval: 10
    scene_threshold: 0.3
    max_segments_per_video: 100
    target_fps: 2
    min_segment_duration: 2.0
    max_segment_duration: 10.0
  image_processing:
    resize_method: "bilinear"
    normalize: true
  audio_processing:
    target_sample_rate: 44100
    target_channels: 2
    max_duration: 30.0
"""
    config_file = tmp_path / "config.yml"
    config_file.write_text(config_content)
    return str(config_file)
```

---

## 测试报告

### 5.1 单元测试报告

**报告内容**：
- 测试用例数量
- 通过数量
- 失败数量
- 跳过数量
- 测试时间
- 详细测试结果

**报告示例**：
```
============================= test session starts ==============================
platform linux -- Python 3.10.12, pytest-7.4.0, pluggy-1.2.0 -- /usr/bin/python3
cachedir: .pytest_cache
rootdir: /data/project/msearch
configfile: pytest.ini
plugins: cov-4.1.0, asyncio-0.21.1, benchmark-4.0.0
collected 125 items

tests/unit/test_config.py ........                                       [  6%]
tests/unit/test_embedding_engine.py .................................    [ 35%]
tests/unit/test_vector_store.py .............................           [ 59%]
tests/unit/test_database_manager.py .....................               [ 79%]
tests/unit/test_task_scheduler.py .......................               [ 95%]
tests/unit/test_file_monitor.py .....                                   [100%]

============================== 125 passed in 45.23s ==============================
```

### 5.2 覆盖率报告

**报告内容**：
- 总体覆盖率
- 各模块覆盖率
- 未覆盖的行
- 分支覆盖率

**报告示例**：
```
---------- coverage: platform linux, python 3.10.12-final-0 -----------
Name                                 Stmts   Miss Branch BrPart  Cover
----------------------------------------------------------------------
src/core/config/config.py              45      5      8      2    85%
src/core/embedding/embedding_engine.py 120     15     25      5    82%
src/core/vector/vector_store.py        95     10     20      3    88%
src/core/database/database_manager.py  80      8     15      2    89%
src/core/task/task_scheduler.py        75      6     12      1    91%
src/core/monitor/file_monitor.py       55      4      8      1    92%
----------------------------------------------------------------------
TOTAL                                 470     48     88     13    88%

Missing lines:
src/core/config/config.py: 25, 32, 45, 67, 89
src/core/embedding/embedding_engine.py: 45, 67, 89, 102, 115, 132, 145, 158, 172, 185, 198, 212, 225, 238, 252
```

### 5.3 性能测试报告

**报告内容**：
- 各测试用例的性能指标
- 平均值、标准差、最小值、最大值
- 与基准的比较
- 性能瓶颈分析

**报告示例**：
```
============================= Performance Test Report ==============================

Report generated: 2026-01-19 10:00:00

============================= Image Embedding Performance ==============================

Test: test_image_embedding_performance
Samples: 100 images

Statistics:
- Mean: 85.2 ms/image
- StdDev: 12.5 ms/image
- Min: 65.3 ms/image
- Max: 112.8 ms/image
- Median: 82.5 ms/image

Target: < 100 ms/image
Status: PASSED

============================= Text Search Performance ==============================

Test: test_text_search_performance
Samples: 100 queries

Statistics:
- Mean: 325.6 ms/query
- StdDev: 45.2 ms/query
- Min: 245.8 ms/query
- Max: 425.3 ms/query
- Median: 315.2 ms/query

Target: < 500 ms/query
Status: PASSED

============================= Video Indexing Performance ==============================

Test: test_video_indexing_performance
Samples: 10 videos (total 10 minutes)

Statistics:
- Mean: 25.3 s/minute video
- StdDev: 5.2 s/minute video
- Min: 18.5 s/minute video
- Max: 35.8 s/minute video
- Median: 24.2 s/minute video

Target: < 30 s/minute video
Status: PASSED

============================= Summary ==============================

Total Tests: 5
Passed: 5
Failed: 0

Overall Status: PASSED
```

---

## 质量标准

### 6.1 测试覆盖率标准

**单元测试覆盖率**：≥ 80%  
**集成测试覆盖率**：≥ 70%  
**端到端测试覆盖率**：≥ 60%  
**总体覆盖率**：≥ 80%  

### 6.2 性能标准

**模型推理性能**：
- 图像：< 100ms/张
- 视频：< 500ms/秒视频
- 音频：< 1000ms/段音频

**检索性能**：
- 文本检索：< 500ms
- 图像检索：< 1000ms
- 音频检索：< 1500ms

**索引性能**：
- 图像：< 1 秒/张
- 视频：< 30 秒/分钟视频
- 音频：< 10 秒/分钟音频

### 6.3 稳定性标准

**系统可用性**：≥ 99.9%  
**任务成功率**：≥ 99.5%  
**错误率**：< 0.1%  
**崩溃率**：< 0.01%  

---

## 附录

### A.1 测试命令参考

**常用测试命令**：
```bash
# 运行所有测试
pytest tests/ -v

# 运行单元测试
pytest tests/unit/ -v

# 运行集成测试
pytest tests/integration/ -v

# 运行端到端测试
pytest tests/e2e/ -v

# 运行性能测试
pytest tests/performance/ -v

# 运行基准测试
pytest tests/benchmark/ -v --benchmark-autosave

# 运行标记为 critical 的测试
pytest tests/ -v -m "critical"

# 运行标记为 slow 的测试
pytest tests/ -v -m "slow"

# 生成覆盖率报告
pytest tests/ -v --cov=src --cov-report=html --cov-report=xml --cov-report=term-missing

# 查看覆盖率报告
firefox tests/.coverage/html/index.html

# 运行特定模块测试
pytest tests/unit/test_config.py -v

# 运行特定测试类
pytest tests/unit/test_config.py::TestConfigManager -v

# 运行特定测试方法
pytest tests/unit/test_config.py::TestConfigManager::test_load_config_success -v

# 重新运行失败的测试
pytest tests/ -v --lf

# 只运行新的或修改的测试
pytest tests/ -v --ff

# 并行运行测试
pytest tests/ -v -n auto

# 生成 JUnit 格式报告
pytest tests/ -v --junitxml=tests/.reports/junit.xml

# 生成 HTML 报告
pytest tests/ -v --html=tests/.reports/report.html
```

### A.2 测试工具安装

**安装测试依赖**：
```bash
# 安装 pytest
pip install pytest

# 安装覆盖率工具
pip install pytest-cov

# 安装基准测试工具
pip install pytest-benchmark

# 安装异步测试工具
pip install pytest-asyncio

# 安装 HTML 报告工具
pip install pytest-html

# 安装并行测试工具
pip install pytest-xdist

# 安装所有测试依赖
pip install -r requirements-test.txt
```

**requirements-test.txt**：
```
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-benchmark>=4.0.0
pytest-asyncio>=0.21.1
pytest-html>=3.2.0
pytest-xdist>=3.3.1
pytest-mock>=3.11.1
requests>=2.31.0
numpy>=1.25.2
Pillow>=10.0.0
opencv-python>=4.8.0
```

### A.3 测试数据准备

**准备测试数据**：
```bash
# 创建测试数据目录
mkdir -p tests/data/msearch/v1/{images,videos,audios,texts}

# 下载测试图像
# 使用脚本下载或手动准备

# 下载测试视频
# 使用脚本下载或手动准备

# 下载测试音频
# 使用脚本下载或手动准备

# 准备测试文本
cat > tests/data/msearch/v1/texts/test_queries.txt << EOF
海滩日落
城市夜景
山脉风景
人物肖像
动物世界
美食烹饪
运动健身
科技产品
自然风景
建筑设计
EOF
```

**测试数据要求**：
- 图像：至少 10 张，格式包括 jpg, png, bmp
- 视频：至少 5 个，格式包括 mp4, avi, mov，时长 10-30 秒
- 音频：至少 5 个，格式包括 mp3, wav, aac，时长 10-60 秒
- 文本：至少 10 个查询词

---

**© 2026 msearch 技术团队**  
**本文档受团队内部保密协议保护**