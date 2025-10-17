# 测试策略文档

> **文档导航**: [文档索引](README.md) | [需求文档](requirements.md) | [设计文档](design.md) | [开发计划](development_plan.md) | [部署指南](deployment_guide.md)

## 1. 测试策略概述

### 1.1 测试目标

本测试策略旨在确保msearch智能多模态检索系统的质量、性能和可靠性，重点关注：

- **功能正确性**：验证所有功能模块按需求正确工作
- **性能指标**：确保系统满足性能要求，特别是时间戳精度（±2秒）
- **稳定性保证**：验证系统在各种条件下的稳定运行
- **用户体验**：确保用户界面友好、操作流畅

### 1.2 测试原则

| 测试原则 | 具体要求 | 实现价值 |
|---------|---------|---------|
| **分层测试** | 单元测试→集成测试→系统测试 | 确保各层次质量 |
| **自动化优先** | 核心功能自动化测试覆盖率≥80% | 提高测试效率 |
| **性能导向** | 关键路径性能测试必须通过 | 保证用户体验 |
| **持续集成** | 每次代码提交触发自动测试 | 及早发现问题 |

### 1.3 测试环境

**测试环境配置**：
- **开发环境**：本地开发机器，用于单元测试和快速验证
- **集成环境**：模拟生产环境，用于集成测试和性能测试
- **部署测试环境**：deploy_test/目录，用于真实部署测试

## 2. 测试分类与策略

### 2.1 单元测试

#### 2.1.1 测试范围

**核心组件测试**：
- `src/core/config_manager.py` - 配置管理器测试
- `src/core/logger_manager.py` - 日志管理器测试
- `src/core/file_type_detector.py` - 文件类型检测器测试

**业务逻辑测试**：
- `src/business/embedding_engine.py` - 向量化引擎测试
- `src/business/search_engine.py` - 检索引擎测试
- `src/business/smart_retrieval.py` - 智能检索测试

**处理器测试**：
- `src/processors/timestamp_processor.py` - 时间戳处理器测试
- `src/processors/image_processor.py` - 图片处理器测试
- `src/processors/video_processor.py` - 视频处理器测试

#### 2.1.2 测试标准

**覆盖率要求**：
- 核心业务逻辑测试覆盖率不低于80%
- 关键路径必须100%覆盖
- 边界条件和异常情况需要充分测试

**测试结构**：
```python
# 测试文件结构示例
tests/unit/
├── test_config_manager.py      # 配置管理器测试
├── test_logger_manager.py      # 日志管理器测试
├── test_embedding_engine.py    # 向量化引擎测试
├── test_search_engine.py       # 检索引擎测试
├── test_timestamp_processor.py # 时间戳处理器测试
└── test_face_manager.py        # 人脸管理器测试
```

#### 2.1.3 关键测试用例

**时间戳处理精度测试**：
```python
class TestTimestampAccuracy:
    def test_frame_level_precision(self):
        """测试帧级时间戳精度"""
        processor = TimestampProcessor(fps=30.0)
        
        # 测试连续帧的时间戳精度
        for frame_idx in range(100):
            timestamp = processor.calculate_frame_timestamp(frame_idx)
            expected = frame_idx / 30.0
            assert abs(timestamp - expected) < 0.001  # 1ms精度
    
    def test_multimodal_sync_tolerance(self):
        """测试多模态同步容差"""
        sync_validator = MultiModalTimeSyncValidator()
        
        # 测试视觉-音频同步
        visual_time = 10.0
        audio_time = 10.05  # 50ms偏差
        
        assert sync_validator.validate_multimodal_sync(
            visual_time, audio_time, 'audio_music'
        )  # 应该在容差范围内
```

**配置管理器测试**：
```python
class TestConfigManager:
    def test_config_loading(self):
        """测试配置加载"""
        config_manager = ConfigManager('tests/fixtures/test_config.yml')
        
        # 测试基本配置读取
        assert config_manager.get('general.log_level') == 'DEBUG'
        assert config_manager.get('models.clip.model_name') == 'openai/clip-vit-base-patch32'
    
    def test_default_values(self):
        """测试默认值机制"""
        config_manager = ConfigManager()
        
        # 测试不存在的配置项返回默认值
        assert config_manager.get('nonexistent.key', 'default') == 'default'
```

### 2.2 集成测试

#### 2.2.1 测试范围

**API端点测试**：
- 检索API功能完整性测试
- 配置API参数验证测试
- 任务控制API状态管理测试

**工作流测试**：
- 文件处理完整流程测试
- 多模态检索工作流测试
- 时间戳精度端到端测试

#### 2.2.2 测试结构

```python
# 集成测试文件结构
tests/integration/
├── test_api_endpoints.py       # API端点测试
├── test_search_workflow.py     # 检索流程测试
├── test_processing_pipeline.py # 处理流程测试
└── test_multimodal_integration.py # 多模态集成测试
```

#### 2.2.3 关键集成测试

**视频处理流程测试**：
```python
class TestVideoProcessingPipeline:
    async def test_video_processing_with_timestamp_accuracy(self):
        """测试视频处理流程的时间戳精度"""
        # Arrange
        test_video_path = "tests/fixtures/test_video.mp4"
        processor = VideoProcessor()
        
        # Act
        results = await processor.process_video(test_video_path)
        
        # Assert - 验证时间戳精度
        for result in results['visual_vectors']:
            assert result['timestamp_accuracy'] <= 2.0
            assert result['start_time'] >= 0
            assert result['end_time'] > result['start_time']
```

**API端点集成测试**：
```python
class TestSearchAPI:
    async def test_multimodal_search_endpoint(self):
        """测试多模态搜索API"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # 测试文本搜索
            response = await ac.post("/api/v1/search", json={
                "query": "美丽的风景",
                "modality": "text_to_image",
                "top_k": 10
            })
            
            assert response.status_code == 200
            data = response.json()
            assert "results" in data
            assert len(data["results"]) <= 10
```

### 2.3 性能测试

#### 2.3.1 性能指标

**时间戳查询性能**：
- 单次时间戳查询延迟必须<10ms
- 批量查询(50个向量)延迟必须<50ms
- 时间范围查询必须使用索引优化

**多模态处理性能**：
- 视频预处理性能：720p视频处理速度>2x实时
- 时间戳计算性能：帧级计算延迟<1ms
- 同步验证性能：多模态同步检查<5ms

#### 2.3.2 性能测试用例

```python
class TestPerformance:
    async def test_timestamp_query_performance(self):
        """测试时间戳查询性能"""
        import time
        
        retrieval_engine = TimeAccurateRetrieval()
        vector_ids = [f"vector_{i}" for i in range(50)]
        
        start_time = time.time()
        
        # 批量查询时间戳
        for vector_id in vector_ids:
            await retrieval_engine.get_timestamp_info(vector_id, 'visual')
        
        end_time = time.time()
        query_time = (end_time - start_time) * 1000  # 转换为毫秒
        
        # 验证性能要求：50个查询<50ms
        assert query_time < 50, f"查询时间过长: {query_time}ms"
    
    def test_video_processing_performance(self):
        """测试视频处理性能"""
        processor = VideoProcessor()
        
        # 测试720p视频处理速度
        start_time = time.time()
        result = processor.process_video("tests/fixtures/720p_test.mp4")
        processing_time = time.time() - start_time
        
        # 验证处理速度 > 2x实时
        video_duration = result['metadata']['duration']
        speed_ratio = video_duration / processing_time
        assert speed_ratio > 2.0, f"处理速度不足: {speed_ratio}x"
```

### 2.4 系统测试

#### 2.4.1 功能测试

**多模态检索功能**：
- 文本搜索图片功能测试
- 图片搜索相似图片功能测试
- 视频时间戳定位功能测试
- 人脸识别检索功能测试

**系统稳定性测试**：
- 长时间运行稳定性测试
- 大文件处理压力测试
- 并发用户访问测试

#### 2.4.2 兼容性测试

**硬件兼容性**：
- CPU模式运行测试
- GPU加速模式测试
- 不同内存配置测试

**操作系统兼容性**：
- Windows系统部署测试
- Linux系统部署测试
- macOS系统部署测试

## 3. 测试数据管理

### 3.1 测试数据结构

```
tests/fixtures/
├── images/                    # 测试图片
│   ├── landscape_1.jpg        # 风景图片
│   ├── portrait_1.jpg         # 人物图片
│   └── object_1.jpg           # 物体图片
├── videos/                    # 测试视频
│   ├── short_video.mp4        # 短视频(<120s)
│   ├── long_video.mp4         # 长视频(>120s)
│   └── 720p_test.mp4          # 720p测试视频
├── audios/                    # 测试音频
│   ├── music_sample.mp3       # 音乐样本
│   ├── speech_sample.wav      # 语音样本
│   └── mixed_content.m4a      # 混合内容
└── configs/                   # 测试配置
    ├── test_config.yml        # 测试配置文件
    └── minimal_config.yml     # 最小配置文件
```

### 3.2 测试数据要求

**数据质量标准**：
- 图片：分辨率不低于720p，格式多样化
- 视频：包含不同时长、分辨率、编码格式
- 音频：包含音乐、语音、混合内容样本
- 配置：覆盖各种配置场景和边界情况

**数据管理原则**：
- 测试数据版本控制，确保测试一致性
- 敏感数据脱敏处理，保护隐私安全
- 数据大小控制，避免仓库过大

## 4. 测试自动化

### 4.1 持续集成配置

**GitHub Actions配置示例**：
```yaml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v3
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov pytest-asyncio
    
    - name: Run unit tests
      run: |
        pytest tests/unit/ -v --cov=src --cov-report=xml
    
    - name: Run integration tests
      run: |
        pytest tests/integration/ -v
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

### 4.2 测试执行策略

**本地开发测试**：
```bash
# 快速单元测试
pytest tests/unit/ -v

# 完整测试套件
pytest tests/ -v --cov=src

# 性能测试
pytest tests/performance/ -v --benchmark-only
```

**CI/CD测试**：
- 每次提交触发单元测试和集成测试
- 每日定时执行完整测试套件
- 发布前执行性能测试和系统测试

## 5. 测试工具和框架

### 5.1 测试框架选择

**主要测试框架**：
- **pytest**: 主要测试框架，支持丰富的插件生态
- **pytest-asyncio**: 异步测试支持
- **pytest-cov**: 测试覆盖率统计
- **pytest-benchmark**: 性能基准测试

**Mock和Stub工具**：
- **unittest.mock**: Python标准库Mock工具
- **pytest-mock**: pytest集成的Mock工具
- **responses**: HTTP请求Mock工具

### 5.2 测试配置

**pytest配置文件**：
```ini
# pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --strict-markers
    --disable-warnings
    --cov=src
    --cov-report=term-missing
    --cov-report=html:htmlcov
markers =
    unit: Unit tests
    integration: Integration tests
    performance: Performance tests
    slow: Slow running tests
```

**conftest.py配置**：
```python
# tests/conftest.py
import pytest
import asyncio
from pathlib import Path

@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def test_config():
    """测试配置"""
    return {
        "general": {
            "log_level": "DEBUG",
            "data_dir": "./test_data"
        },
        "models": {
            "clip": {"model_name": "openai/clip-vit-base-patch32"}
        }
    }

@pytest.fixture
def test_files():
    """测试文件路径"""
    fixtures_dir = Path(__file__).parent / "fixtures"
    return {
        "image": fixtures_dir / "images" / "test_image.jpg",
        "video": fixtures_dir / "videos" / "test_video.mp4",
        "audio": fixtures_dir / "audios" / "test_audio.wav"
    }
```

## 6. 质量保证流程

### 6.1 代码审查检查清单

**功能正确性**：
- [ ] 功能实现符合需求规范
- [ ] 边界条件处理正确
- [ ] 异常情况处理完善
- [ ] 返回值类型和格式正确

**性能要求**：
- [ ] 时间戳精度满足±2秒要求
- [ ] 查询响应时间符合性能指标
- [ ] 内存使用合理，无明显泄漏
- [ ] 并发处理能力满足要求

**代码质量**：
- [ ] 代码符合编码规范
- [ ] 函数和类有适当的文档字符串
- [ ] 测试覆盖率达到要求
- [ ] 无明显的代码异味

### 6.2 发布前测试检查清单

**功能验证**：
- [ ] 所有单元测试通过
- [ ] 所有集成测试通过
- [ ] 关键功能手动验证通过
- [ ] 性能测试指标达标

**部署验证**：
- [ ] 部署测试环境验证通过
- [ ] 配置文件格式正确
- [ ] 依赖项安装正常
- [ ] 服务启动和停止正常

**文档完整性**：
- [ ] API文档更新完整
- [ ] 用户手册更新及时
- [ ] 部署指南准确有效
- [ ] 变更日志记录完整

## 7. 测试报告和度量

### 7.1 测试度量指标

**覆盖率指标**：
- 代码覆盖率：目标≥80%
- 分支覆盖率：目标≥70%
- 功能覆盖率：目标≥95%

**质量指标**：
- 缺陷密度：<1个/KLOC
- 测试通过率：≥95%
- 性能达标率：100%

### 7.2 测试报告模板

**测试执行报告**：
```markdown
# 测试执行报告

## 测试概要
- 测试版本：v1.0.0
- 测试时间：2024-01-15
- 测试环境：集成测试环境
- 测试负责人：开发团队

## 测试结果
- 单元测试：通过率 98% (196/200)
- 集成测试：通过率 95% (38/40)
- 性能测试：通过率 100% (25/25)

## 覆盖率统计
- 代码覆盖率：85%
- 分支覆盖率：78%
- 功能覆盖率：96%

## 发现问题
1. 时间戳精度在特定条件下超出±2秒要求
2. 大文件处理时内存使用过高
3. 并发搜索时偶现响应超时

## 风险评估
- 高风险：0个
- 中风险：2个
- 低风险：1个

## 建议
1. 优化时间戳计算算法
2. 实现内存使用监控和清理
3. 增加并发处理的超时处理机制
```

这个测试策略文档提供了完整的测试框架，确保系统质量和可靠性，特别关注了时间戳精度等关键技术要求。