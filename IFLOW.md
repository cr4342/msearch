# msearch 项目上下文文档

## 项目概述

msearch 是一款单机可运行的跨平台多模态桌面检索软件，专为视频剪辑师设计，实现素材无需整理、无需标签的智能检索。系统采用Python原生集成AI模型的方式，支持文本、图像、视频、音频四种模态的精准检索，通过实时监控和增量处理，为视频剪辑师提供高效、安全的多媒体内容检索体验。

### 多进程架构

msearch采用多进程架构设计，将计算密集型任务与主应用解耦，提升系统稳定性和资源利用率。架构包括：
- 主进程：提供API服务和协调功能
- 文件监控进程：监控文件系统变化
- 向量化工作进程：执行AI模型推理
- 任务工作进程：处理非推理类任务
- 进程间通信：采用SQLite队列 + 本地Unix Socket方案，移除Redis依赖

### 核心特性

- **智能检索**: 无需手动整理、无需添加标签即可实现智能检索
- **跨模态搜索**: 支持用任意模态（文本、图像、音频）检索其他模态内容
- **高精度定位**: 支持视频片段级检索，时间戳精度±5秒
- **零配置**: 素材无需整理、无需标签
- **高性能本地推理**: Python原生集成AI模型，无需额外服务引擎
- **硬件自适应**: 根据硬件配置自动选择最优模型（低/中/高配）
- **单机运行**: 完全本地化，无需网络依赖
- **后端前端分离**: API服务与UI界面分离，便于扩展
- **统一向量化流程**: 图像和视频使用统一的向量化工作流程，无需抽帧，大幅降低开发工作量
- **短视频优化**: 针对短视频（≤6秒）场景优化处理流程
- **音频价值判断**: 跳过无效短音频（≤5秒），节省计算资源
- **文件去重**: 基于SHA256哈希的智能去重机制
- **预处理缓存**: 智能缓存中间处理结果，提升重复处理效率
- **MVP优先级**: 文搜图功能提前到MVP阶段（P1优先级）
- **低价值噪音过滤**: 智能过滤低价值内容，提高系统效率和检索质量
- **视频时间轴展示**: 支持视频检索结果的时间轴可视化展示
- **PySide6桌面UI**: 跨平台桌面应用，提供完整的用户交互界面
- **依赖注入架构**: 使用依赖注入替代直接导入，提高模块独立性和可测试性

### 技术栈

- **语言**: Python 3.8+
- **AI推理**: Python原生集成（直接模型调用、GPU/CPU由配置文件决定）
- **PyTorch版本**: torch>=2.8.0
- **模型管理框架**: [michaelfeil/infinity](https://github.com/michaelfeil/infinity)（统一模型运行时框架）
  - **简单切换模型**：配置文件驱动，无需修改代码即可切换不同模型
  - **高效管理模型运行**：自动批处理优化、FlashAttention加速、内存管理
  - **统一接口**：所有模型使用相同的加载和推理接口
  - **离线支持**：完全支持离线模式，自动处理模型依赖
  - **支持模型系列**：
    - [配置驱动模型]（低配置，CPU/4GB内存，512维）
    - [配置驱动模型]（中配置，CPU/GPU/8GB内存，512维）
    - [配置驱动模型]（高配置，GPU/16GB+内存，2048维）
    - [配置驱动模型]（高配置，GPU/16GB+内存，512维）
    - [配置驱动模型]（超高配置，GPU/32GB+内存，4096维）    - [配置驱动模型]（音频模型，512维）
  - **模型切换**：只需修改配置文件，无需修改代码
- **图像/视频向量化**: [配置驱动模型]系列（统一多模态模型）
  - 统一模型: 多种[配置驱动模型]（基于Infinity框架）
  - 可选模型:
    - [配置驱动模型]（基础模型，快速）
    - [配置驱动模型]（高精度模型）
    - [配置驱动模型]（高性能模型）
    - [配置驱动模型]（高精度模型）
    - [配置驱动模型]（超高精度模型）
  - 硬件要求: 适用于各种硬件配置（CPU/GPU），约4GB显存（GPU）或8GB内存（CPU）
  - 批处理大小: 8-16（根据硬件配置自适应）
  - 特点: 高性能多模态嵌入模型，支持文本-图像、图像-图像、文本-视频检索，无需抽帧
- **音频处理**: CLAP（统一音频处理模型，简化流程）
  - 文本-音乐检索
  - 语音转文本
  - 音频内容分类（音乐/语音/噪音）
- **向量存储**: LanceDB（高性能本地向量数据库，统一向量表设计）
- **元数据存储**: SQLite（轻量级关系数据库，WAL模式）
- **任务管理**: TaskManager（任务优先级管理、并发控制、资源限制、持久化支持）
- **Web框架**: FastAPI（异步API服务）
- **GUI框架**: PySide6（跨平台桌面应用，已完成）
- **WebUI**: 原生HTML/CSS/JavaScript（快速验证界面）
- **媒体处理**: FFmpeg, OpenCV, Librosa（专业级预处理）
- **文件监控**: Watchdog（实时增量处理）
- **配置管理**: YAML（配置驱动、支持热重载）
- **日志系统**: Python logging（多级别日志、自动轮转）
- **缓存管理**: 基于文件哈希的预处理缓存系统
- **依赖注入**: 使用依赖注入架构，提高模块独立性和可测试性

## 架构设计

### 多进程架构

项目采用多进程架构设计，将计算密集型任务与主应用解耦，提升系统稳定性和资源利用率。

```
┌─────────────────────────────────────────────────────────────────┐
│                    主进程 (Main Process)                     │
│  - main.py: 主进程协调器                                 │
│  - api_server.py: API服务器 (FastAPI)                     │
│  - WebUI服务 (Gradio)                                     │
│  - Task Manager: 任务调度器                               │
│  - Config Manager: 配置管理器                             │
└─────────────────────────────────────────────────────────────────┘
                                       │
         ┌─────────────────────────────┼─────────────────────────────┐
         │                             │                             │
         ▼                             ▼                             ▼
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│ File Monitor        │    │ Embedding Worker    │    │ Task Worker         │
│ Process (1个)        │    │ Process (1-N个)      │    │ Process (1-N个)      │
├─────────────────────┤    ├─────────────────────┤    ├─────────────────────┤
│ • file_monitor_     │    │ • embedding_worker_ │    │ • task_worker_      │
│   process.py        │    │   process.py        │    │   process.py        │
│ • 文件系统监控       │    │ • 模型加载/卸载      │    │ • 媒体预处理        │
│ • 目录扫描          │    │ • 向量推理          │    │ • 数据转换          │
│ • 事件通知          │    │ • 批处理优化        │    │ • 文件格式处理      │
│ • 增量更新          │    │ • GPU/CPU 管理      │    │ • 缩略图生成        │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
         │                             │                             │
         └─────────────────────────────┼─────────────────────────────┘
                                       │
                                       ▼
                    ┌───────────────────────────────────┐
                    │         Redis (本地)               │
                    │  ┌─────────────┐ ┌───────────────┐ │
                    │  │ Task Queue  │ │ Status Cache  │ │
                    │  └─────────────┘ └───────────────┘ │
                    └───────────────────────────────────┘
```

### 分层架构 (在各进程中)

在每个进程中，仍保持原有的分层架构：

```
┌─────────────────────────────────────────────────────────────────┐
│                    用户界面层 (UI)                      │
│  - main_window.py: 主窗口                               │
│  - ui_launcher.py: UI启动器                              │
│  - components/: UI组件                                   │
│      - search_panel.py: 搜索面板                         │
│      - result_panel.py: 结果面板                         │
│      - settings_panel.py: 设置面板                       │
│      - task_manager_panel.py: 任务管理器面板               │
│      - data_manager_panel.py: 数据管理面板                 │
│  - dialogs/: UI对话框                                    │
│      - progress_dialog.py: 进度对话框                     │
├─────────────────────────────────────────────────────────────────┤
│                    API服务层 (API)                        │
│  - api_server.py: API服务器入口                           │
│  - routes.py: API路由定义                                │
│  - handlers.py: API处理器                                 │
│  - schemas.py: 数据模型定义                              │
├─────────────────────────────────────────────────────────────────┤
│                    服务层 (Services)                      │
│  - search_services/: 检索服务                            │
│  - media_services/: 媒体处理服务                          │
│  - file_services/: 文件处理服务                            │
│  - cache/: 缓存服务                                      │
│      - preprocessing_cache.py: 预处理缓存管理器           │
├─────────────────────────────────────────────────────────────────┤
│                    核心组件层 (Core)                       │
│  - config/: 配置管理                                      │
│      - config.py: 配置管理器（路径已修复为config/config.yml）          │
│  - database/: 数据库管理                                  │
│      - database_manager.py: 数据库管理器                  │
│  - vector/: 向量存储                                      │
│      - vector_store.py: 向量存储                          │
│  - embedding/: 向量化引擎                                 │
│      - embedding_engine.py: 向量化引擎（统一使用Infinity）                    │
│  - task/: 任务管理                                        │
│      - task_manager.py: 任务管理器                        │
│      - task_monitor.py: 任务监控器                        │
│  - ipc/: 进程间通信                                      │
│      - shared_memory.py: 共享内存管理器                   │
│      - redis_ipc.py: Redis进程间通信管理器               │
│      - process_manager.py: 多进程管理器                   │
│  - hardware/: 硬件检测                                    │
│      - hardware_detector.py: 硬件检测器                  │
│  - logging/: 日志配置                                      │
│      - logging_config.py: 日志配置器                      │
│  - file_monitor.py: 文件监控器                            │
│  - media_processor.py: 媒体处理器                          │
│  - search_engine.py: 搜索引擎                            │
│  - noise_filter.py: 噪音过滤器                            │
│  - timeline.py: 时间轴生成器                             │
│  - exceptions.py: 异常定义                               │
├─────────────────────────────────────────────────────────────────┤
│                    数据层 (Data)                         │
│  - metadata_extractor.py: 元数据提取器                      │
│  - thumbnail_generator.py: 缩略图生成器                    │
│  - preview_generator.py: 预览生成器                        │
│  - models.py: 数据模型定义                              │
├─────────────────────────────────────────────────────────────────┤
│                    工具层 (Utils)                         │
│  - config_validator.py: 配置验证器                        │
│  - error_handling.py: 错误处理                          │
│  - exceptions.py: 异常定义                              │
└─────────────────────────────────────────────────────────────────┘
```

### 核心模块职责

#### 核心组件层
- **ConfigManager**: 配置管理器，负责加载、验证、管理和更新系统配置（路径已修复为config/config.yml）
- **DatabaseManager**: SQLite元数据库管理，支持文件哈希去重、时间定位数据结构、引用计数机制
- **VectorStore**: 专注于LanceDB向量数据库操作（统一向量表设计），通过modality字段区分不同模态
- **EmbeddingEngine**: 统一管理AI模型调用（使用Infinity，统一接口），实现模型推理的错误处理和重试机制
- **TaskManager**: 任务进度跟踪和状态管理，支持任务优先级、依赖关系、并发控制和资源限制
- **TaskMonitor**: 任务监控器，负责任务进度跟踪、任务统计、任务历史记录和性能指标计算
- **DataManager**: 数据管理器，负责索引管理和数据统计功能，提供索引状态监控和数据健康度检查
- **IPCManager**: 进程间通信管理器，负责多进程间的通信、任务分发和状态同步，基于Redis实现
- **SharedMemoryManager**: 共享内存管理器，负责大文件数据的跨进程高效传输，避免序列化开销
- **ProcessManager**: 多进程管理器，负责子进程的生命周期管理、监控和自动重启
- **HardwareDetector**: 硬件配置检测和模型推荐，根据GPU、CPU和内存配置自动选择最优模型
- **LoggingConfig**: 日志配置管理器，负责配置日志级别、格式、轮转策略和处理器
- **FileMonitor**: 实时监控文件变化（基于watchdog），支持防抖延迟和递归监控
- **MediaProcessor**: 智能媒体预处理（场景分割、切片向量化、短视频优化、音频价值判断、CLAP音频分类）
- **SearchEngine**: 多模态检索功能，支持结果聚合、排序和去重，支持文本、图像、音频搜索（使用依赖注入）
- **NoiseFilterManager**: 低价值噪音过滤管理器，支持图像、视频、音频、文本的智能过滤
- **VideoTimelineGenerator**: 视频时间轴生成器，支持时间轴结果生成和管理
- **Exceptions**: 自定义异常定义

#### 服务层
- **PreprocessingCache**: 预处理缓存管理器，基于文件哈希的缓存键，自动管理缓存大小和TTL
- **FileMonitor**: 文件监控服务，实时监控文件变化并触发处理任务
- **MediaProcessor**: 媒体处理服务，处理图像、视频、音频文件的预处理和向量化

#### API层
- **APIServer**: FastAPI服务主入口，提供RESTful API接口（使用依赖注入）
- 支持检索API、文件管理API、任务管理API、系统信息API

#### 用户界面
- **PySide6 UI**: 跨平台桌面应用（已完成）
  - main_window.py: 主窗口（使用依赖注入）
  - ui_launcher.py: UI启动器
  - components/search_panel.py: 搜索面板组件
  - components/result_panel.py: 结果面板组件
  - components/settings_panel.py: 设置面板组件
  - dialogs/progress_dialog.py: 进度对话框
- **WebUI**: 原生HTML/CSS/JavaScript界面（webui/index.html），用于快速功能验证

## 项目结构

```
msearch/
├── IFLOW.md                 # 项目上下文文档
├── requirements.txt         # Python依赖入口（指向requirements/base.txt）
├── requirements/            # 依赖分离管理目录
│   ├── base.txt           # 核心依赖（运行msearch所需的最小依赖集）
│   ├── dev.txt            # 开发依赖（包含base.txt + 开发工具）
│   ├── test.txt           # 测试依赖（包含base.txt + 测试工具）
│   ├── optional.txt       # 可选依赖（包含base.txt + GUI等可选功能）
│   └── README.md          # 依赖管理说明
├── config/
│   └── config.yml          # 主配置文件（路径已修复）
├── data/
│   ├── database/           # 数据库文件
│   │   ├── sqlite/         # SQLite数据库
│   │   └── lancedb/        # LanceDB向量数据库
│   ├── logs/               # 日志文件
│   ├── models/             # AI模型文件
│   ├── cache/              # 预处理缓存
│   │   └── preprocessing/  # 预处理中间文件
│   │       ├── audio_segments/
│   │       ├── video_slices/
│   │       └── text_embeddings/
│   ├── tasks/              # 任务队列
│   └── thumbnails/         # 缩略图缓存（基于文件哈希命名）
├── docs/                   # 文档目录
│   ├── api.md              # API文档
│   ├── data-models.md      # 数据模型文档
│   ├── design.md           # 设计文档
│   ├── requirements.md     # 需求文档
│   ├── tasks.md            # 任务列表
│   ├── testing-strategy.md # 测试策略文档
│   ├── code_design_deviation_analysis.md  # 代码与设计偏差分析
│   └── code_refactoring_summary.md         # 代码重构总结
├── tests/                  # 测试文件
│   ├── __init__.py
│   ├── pytest.ini          # pytest配置
│   ├── conftest.py         # pytest配置
│   ├── unit/               # 单元测试
│   │   ├── core/           # 核心组件测试
│   │   ├── data/           # 数据层测试
│   │   ├── services/       # 服务层测试
│   │   ├── ui/             # UI测试
│   │   ├── utils/          # 工具层测试
│   │   ├── test_config.py  # 配置管理器测试
│   │   ├── test_database_manager.py
│   │   ├── test_search_engine.py
│   │   ├── test_noise_filter.py  # 噪音过滤器测试
│   │   ├── test_timeline.py      # 时间轴生成器测试
│   │   └── test_model_integration.py  # 模型集成测试
│   ├── integration/        # 集成测试
│   │   ├── it_search_flow.py    # 搜索流程集成测试
│   │   └── it_indexing_flow.py # 索引流程集成测试
│   ├── e2e/               # 端到端测试
│   │   └── e2e_full_workflow.py # 完整工作流程端到端测试
│   ├── benchmark/          # 性能基准测试
│   │   └── test_embedding_benchmark.py # 向量化性能基准测试
│   ├── conf.d/             # 测试配置
│   ├── data/               # 测试数据
│   │   ├── api/
│   │   └── msearch/
│   ├── fixtures/           # 测试夹具
│   │   ├── __init__.py
│   │   ├── data_factory.py
│   │   ├── mock_factory.py
│   │   └── path_factory.py
│   └── .coverage/          # 覆盖率报告
│       ├── html/
│       └── coverage.xml
├── scripts/                # 脚本文件
│   ├── install.sh          # Linux安装脚本
│   └── setup_models.py     # 模型设置脚本
├── webui/                  # Web界面
│   └── index.html          # WebUI主界面
├── testdata/               # 测试数据
│   ├── audio/              # 测试音频
│   └── faces/              # 测试人脸图片
└── src/                    # 源代码目录
    ├── main.py             # 主程序入口（使用依赖注入）
    ├── api_server.py       # API服务器（使用依赖注入）
    ├── api/                # API层
    │   └── __init__.py
    ├── core/               # 核心模块
    │   ├── config/         # 配置管理
    │   │   └── config.py   # 配置管理器（路径已修复）
    │   ├── database/       # 数据库管理
    │   │   └── database_manager.py
    │   ├── vector/         # 向量存储
    │   │   └── vector_store.py
    │   ├── embedding/      # 向量化引擎
    │   │   └── embedding_engine.py  # 向量化引擎（统一使用Infinity）
    │   ├── task/           # 任务管理
    │   │   └── task_manager.py
    │   ├── hardware/       # 硬件检测
    │   │   └── hardware_detector.py
    │   ├── logging/        # 日志配置
    │   │   └── logging_config.py
    │   ├── file_monitor.py # 文件监控器
    │   ├── media_processor.py # 媒体处理器
    │   ├── search_engine.py # 搜索引擎（使用依赖注入）
    │   ├── noise_filter.py # 噪音过滤器
    │   ├── timeline.py     # 时间轴生成器
    │   └── exceptions.py   # 异常定义
    ├── services/           # 服务层
    │   ├── cache/          # 缓存服务
    │   │   └── preprocessing_cache.py  # 预处理缓存管理器
    │   ├── file_monitor.py # 文件监控服务
    │   ├── media_processor.py # 媒体处理服务
    │   └── search/         # 搜索服务
    │       └── search_engine.py  # 搜索引擎（使用依赖注入）
    ├── data/               # 数据层
    │   ├── extractors/     # 数据提取器
    │   ├── generators/     # 数据生成器
    │   ├── models/         # 数据模型
    │   └── validators/     # 数据验证器
    ├── ui/                 # 用户界面
    │   ├── main_window.py  # 主窗口（使用依赖注入）
    │   ├── ui_launcher.py  # UI启动器
    │   ├── components/     # UI组件
    │   │   ├── search_panel.py
    │   │   ├── result_panel.py
    │   │   └── settings_panel.py
    │   └── dialogs/        # UI对话框
    │       └── progress_dialog.py
    └── utils/              # 工具类
        └── __init__.py
```

## 工作流程

### 文件处理流程（带任务优先级和噪音过滤）
```
[任务0: file_scan] 文件监控/扫描
    ↓
[任务0: file_scan] 元数据提取 + 文件哈希计算
    ↓
[任务1: duplicate_check] 重复文件检测（基于SHA256哈希）
    ↓
[任务2: noise_filter] 低价值噪音过滤
    ↓
    ├─→ [跳过] 低价值内容（图像尺寸过小、视频时长过短、音频时长<5秒等）
    └─→ [任务3: task_add] 添加预处理任务（高质量内容）
    ↓
    ├─→ [任务4: image_preprocess] 图像预处理 → 直接向量化 → 向量存储
    ├─→ [任务5: video_process] 视频处理
    │       ↓
    │       ├─→ [任务6: video_slice] 视频切片（>6秒，用于时间定位）
    │       │       ↓
    │       │       └─→ [任务7: video_embed] 视频向量化（直接处理，无需抽帧） → 向量存储
    │       └─→ [任务7: video_embed] 短视频向量化（≤6秒，直接处理，无需抽帧） → 向量存储
    ├─→ [任务8: audio_process] 音频价值判断
    │       ↓
    │       ├─→ [任务9: audio_preprocess] 音频预处理（≥5秒） → CLAP分类 → 向量化 → 向量存储
    │       └─→ [任务12: audio_skip] 跳过低价值音频（<5秒）
    ├─→ [任务10: text_embed] 文本向量化 → 向量存储
    ├─→ [任务11: thumbnail_generate] 缩略图生成
    └─→ [任务12: preview_generate] 预览生成
```

**架构优势**:
- ✅ **统一向量化**: 图像和视频使用相同的向量化接口，配合Infinity优化
- ✅ **简化流程**: 消除了帧提取、帧管理、帧向量化等复杂逻辑
- ✅ **降低开发量**: 减少了视频预处理和向量化代码量
- ✅ **提升性能**: Infinity框架，动态批处理和FlashAttention加速
- ✅ **智能过滤**: 低价值噪音过滤机制，提高系统效率和检索质量
- ✅ **依赖注入**: 使用依赖注入架构，提高模块独立性和可测试性

### 任务优先级定义（MVP阶段）

| 优先级 | 任务类型 | 说明 | 依赖关系 |
|-------|---------|------|---------|
| 0 | config_load | 配置加载（最高优先级，基础任务） | 无依赖 |
| 0 | database_init | 数据库初始化（最高优先级，基础任务） | 无依赖 |
| 0 | vector_store_init | 向量存储初始化（最高优先级，基础任务） | 无依赖 |
| 1 | file_embed_text | 文本向量化（高优先级，MVP核心） | 依赖file_scan |
| 1 | file_embed_image | 图像向量化（高优先级，MVP核心，已提前） | 依赖file_scan |
| 2 | file_scan | 文件扫描（中高优先级） | 无依赖 |
| 3 | video_slice | 视频切片（中等优先级，仅用于时间定位） | 依赖video_process |
| 3 | file_embed_video | 视频向量化（中等优先级，直接处理，无需抽帧） | 依赖video_process或video_slice |
| 4 | audio_segment | 音频分段（中低优先级） | 依赖file_scan或video_process |
| 4 | file_embed_audio | 音频向量化（中低优先级） | 依赖audio_segment |
| 5 | search | 向量搜索（低优先级） | 依赖file_embed_image, file_embed_text |
| 5 | search_multimodal | 多模态向量检索（低优先级） | 依赖file_embed_image, file_embed_text |
| 6 | rank_results | 搜索结果排序（更低优先级） | 依赖search |
| 6 | filter_results | 搜索结果过滤（更低优先级） | 依赖search |
| 7 | thumbnail_generate | 缩略图生成（最低优先级） | 依赖file_embed_image, file_embed_video |
| 7 | preview_generate | 预览生成（最低优先级） | 依赖file_scan |

**MVP阶段核心功能**:
- P0: 核心基础设施（配置、数据库、向量存储）
- P1: 文本向量化 + 图像向量化（文搜图、图搜图、文搜视频）
- P2: 文件扫描
- P3: 视频向量化
- P4: 音频向量化
- P5: 向量搜索
- P6: 结果排序和过滤
- P7: UI辅助功能

### 检索流程
```
用户查询 → 查询向量化 → 统一搜索 → 结果丰富 → 结果聚合/去重 → 时间轴生成 → 返回结果
    │           │           │          │          │          │
 (UI/API) (EmbeddingEngine) (SearchEngine) (DatabaseManager) (SearchEngine) (VideoTimelineGenerator)
```

### API调用流程
```
HTTP请求 → FastAPI路由 → API处理器 → 业务逻辑 → 统一数据访问层 → 数据库/向量存储 → 响应
    │           │            │           │              │              │         │
  (验证)    (分发)      (处理)    (协调)        (查询)      (存储)   (格式化)
```

## 专业AI模型架构

### 硬件自适应图像/视频向量化模型

系统采用统一的[配置驱动模型]进行图像/视频向量化，该模型基于Infinity框架，支持文本、图像、视频的跨模态检索。

**重要版本要求**: [配置驱动模型]支持PyTorch 2.0+版本，请确保环境配置正确。

**架构优势**:
- **统一工作流程**: 文本、图像、视频使用相同的向量化接口，无需区分处理逻辑
- **无需抽帧**: 模型直接支持视频输入，无需预先提取帧图像
- **降低开发量**: 减少了视频预处理、帧提取、帧管理等复杂逻辑
- **简化维护**: 统一的代码路径，减少bug和维护成本
- **提升性能**: 直接处理视频，避免中间帧提取的性能开销
- **统一接口**: 使用Infinity框架，所有模型使用相同的加载方式

#### **[配置驱动模型]**（基础[配置驱动模型]）
- **应用场景**: 各种硬件配置（CPU/GPU）
- **向量维度**: 512维
- **硬件要求**: 适用于各种硬件配置（约4GB显存（GPU）或8GB内存（CPU））
- **批处理大小**: 8-16（根据硬件配置自适应）
- **特点**:
  - 高性能多模态嵌入模型，支持文本-图像、图像-图像、文本-视频检索
  - 基于Infinity框架，易于集成和使用
  - 支持多种检索任务：文本到图像、图像到图像、文本到视频
  - 无需抽帧，直接处理视频
  - 统一的模型加载方式，简化代码
- **架构优势**: 统一文本/图像/视频接口，简化开发流程

#### **[配置驱动模型]**（高精度[配置驱动模型]）
- **应用场景**: 高精度检索场景（GPU）
- **向量维度**: 1024维
- **硬件要求**: 适用于GPU配置（约8GB显存）
- **批处理大小**: 4-8（根据硬件配置自适应）
- **特点**:
  - 超高精度多模态嵌入模型
  - 支持多种检索任务：文本到图像、图像到图像、文本到视频
  - 无需抽帧，直接处理视频

#### **[配置驱动模型]**（高性能[配置驱动模型]）
- **应用场景**: 高性能检索场景（GPU）
- **向量维度**: 2048维
- **硬件要求**: 适用于GPU配置（约16GB显存）
- **批处理大小**: 2-4（根据硬件配置自适应）
- **特点**:
  - 超高性能多模态嵌入模型
  - 支持多种检索任务：文本到图像、图像到图像、文本到视频
  - 无需抽帧，直接处理视频

#### **[配置驱动模型]**（高精度模型）
- **应用场景**: 高精度检索场景（GPU）
- **向量维度**: 512维
- **硬件要求**: 适用于GPU配置（约16GB显存）
- **批处理大小**: 4-8（根据硬件配置自适应）
- **特点**:
  - 高精度多模态嵌入模型
  - 支持多种检索任务：文本到图像、图像到图像、文本到视频
  - 无需抽帧，直接处理视频

#### **[配置驱动模型]**（超高精度模型）
- **应用场景**: 超高精度检索场景（GPU）
- **向量维度**: 4096维
- **硬件要求**: 适用于GPU配置（约32GB显存）
- **批处理大小**: 1-2（根据硬件配置自适应）
- **特点**:
  - 超高精度多模态嵌入模型
  - 支持多种检索任务：文本到图像、图像到图像、文本到视频
  - 无需抽帧，直接处理视频

### 音频处理模型

#### CLAP（统一音频处理模型）
CLAP统一处理所有音频类型，简化了音频处理流程，在音频-文本检索任务上具有显著优势。

**功能特性**:
- **文本-音乐检索**: 高质量文本-音乐匹配
- **语音-文本转换**: 高精度多语言语音识别
- **音频内容智能分类**: 精准区分音乐、语音、噪音

**音频分类实现**:
- 使用[配置驱动模型]对音频进行分类
- 支持类型: MUSIC、SPEECH、MIXED、SILENCE、UNKNOWN
- 基于音频特征进行分类（零交叉率、频谱质心、MFCC特征）

### 音频分类与模型选择映射

| 音频类型 | 使用模型 | 向量化方式 | 检索场景 |
|---------|---------|-----------|---------|
| MUSIC | CLAP | 音频向量嵌入 | 文本-音乐检索 |
| SPEECH | CLAP | 语音转文本 + 文本向量嵌入 | 语音内容检索 |
| MIXED | CLAP | 混合向量化（权重各50%） | 综合音频检索 |
| SILENCE | 无 | 跳过处理 | - |
| UNKNOWN | CLAP | 音频向量嵌入 | 通用音频检索 |

## 智能媒体预处理

### 视频预处理策略

**架构优化**: [配置驱动模型]采用Infinity框架，支持直接处理视频，无需抽帧，配合动态批处理和FlashAttention加速。

- **短视频优化**（≤6秒）：
  - **chinese-clip-vit-base-patch16处理**: 直接对整个视频进行向量化，无需抽帧
  - **性能优化**: 使用Infinity框架，动态批处理和FlashAttention加速
  - 性能提升：处理速度提升3-5倍
  - 简化流程：消除了帧提取、帧管理、帧向量化等复杂逻辑

- **长视频处理**（>6秒）：
  - **场景分割**: 使用FFmpeg场景检测将视频分割为片段（用于时间定位）
  - **切片限制**: 最大切片时长5秒
  - **chinese-clip-vit-base-patch16处理**: 直接对视频片段进行向量化，无需抽帧
  - **性能优化**: 使用Infinity框架，动态批处理和FlashAttention加速
  - 分辨率优化：短边超过960像素时自动调整
  - 格式转换：转换为H.264 MP4格式（仅用于索引）
  - 音频处理：使用CLAP分类音频内容
  - 超大视频处理：超过3GB或30分钟的视频优先处理开头5分钟

**架构优势**:
- ✅ **无需抽帧**: 所有模型直接支持视频输入，消除抽帧逻辑
- ✅ **统一接口**: 图像和视频使用相同的向量化接口
- ✅ **降低开发量**: 减少了帧提取、帧管理、帧存储等复杂代码
- ✅ **简化维护**: 统一的代码路径，减少bug和维护成本
- ✅ **提升性能**: 避免中间帧提取的性能开销
- ✅ **统一加载**: 使用Infinity统一加载模型，简化代码

### 图像预处理策略

- **分辨率限制**: 长边不超过2048像素
- **格式转换**: 转换为RGB格式
- **缩略图生成**: 基于文件哈希生成缩略图，避免重复生成

**统一处理**: 图像和视频使用相同的预处理流程，配合[配置驱动模型]，无需区分处理逻辑。

### 音频预处理策略

- **音频价值判断**：跳过无效短音频（≤5秒）
  - 核心原则：音频信息只有在超过5秒以上时才具有检索价值
  - 优化目标：避免对无效短音频执行昂贵的模型推理
  - 处理策略：短音频直接标记为低价值，跳过CLAP分类和后续处理

- **重采样**: 重采样为16kHz单声道64kbps AAC格式
- **内容分类**: 使用CLAP区分音乐和语音
  - 基于音频特征进行分类（零交叉率、频谱质心、MFCC特征）
  - 支持类型: MUSIC、SPEECH、MIXED、SILENCE、UNKNOWN
- **音乐处理**: 使用[配置驱动模型]生成向量嵌入
- **语音处理**: 使用[配置驱动模型]进行转录

### 时序定位优化策略

- **短视频简化**（≤6秒）：
  - segment_id = "full"（标记为完整视频）
  - start_time = 0
  - end_time = duration
  - is_full_video = True
  - 减少元数据写入开销

- **长视频精确**（>6秒）：
  - 存储精确时间戳
  - 时间戳精度：±5秒

### 文件去重机制

- **基于文件哈希的去重**：
  - 使用SHA256计算文件哈希
  - 相同内容的文件只存储一份向量和元数据
  - 引用计数机制：记录文件路径引用列表
  - 避免重复处理相同内容的文件

- **缩略图和预览去重**：
  - 基于文件哈希命名缩略图和预览文件
  - 格式：{hash_prefix}.jpg（缩略图）
  - 避免因路径/文件名变更导致重复生成

### 预处理缓存机制

- **缓存策略**：
  - 基于文件哈希的缓存键
  - 自动管理缓存大小和TTL
  - 支持缓存清理和过期检测

- **缓存内容**：
  - 预处理的图像
  - 音频重采样结果
  - 中间处理文件

- **缓存目录结构**：
  - audio_segments/: 音频分段缓存
  - video_slices/: 视频切片缓存
  - text_embeddings/: 文本嵌入缓存

- **缓存优势**：
  - 提升重复处理速度
  - 减少重复计算开销
  - 支持断点续处理

## 低价值噪音过滤机制

### 核心设计目标

- 减少低价值内容对系统资源的占用
- 提高检索结果的质量和相关性
- 降低计算成本和处理时间
- 提供可配置的过滤规则
- 支持不同媒体类型的定制化过滤策略

### 过滤器架构

### 噪音过滤器管理器（NoiseFilterManager）

- **职责**: 统一管理各类媒体过滤器
- **功能**: 
  - 初始化图像、视频、音频、文本过滤器
  - 提供统一过滤接口
  - 收集过滤统计信息
  - 支持配置热更新

### 图像噪音过滤器（ImageNoiseFilter）

- **过滤规则**:
  - 最小图像尺寸: 32x32像素
  - 最小文件大小: 1KB
  - 支持格式: jpg, jpeg, png, bmp, gif, webp
  - 最小质量分数: 0.1

- **过滤原因**:
  - small_dimension: 图像尺寸过小
  - small_file_size: 文件大小过小
  - unsupported_format: 不支持的格式
  - low_quality: 图像质量过低

### 视频噪音过滤器（VideoNoiseFilter）

- **过滤规则**:
  - 最小时长: 0.5秒
  - 最小文件大小: 10KB
  - 支持格式: mp4, avi, mov, wmv, flv, mkv
  - 最小分辨率: 160x160像素

- **过滤原因**:
  - short_duration: 视频时长过短
  - small_file_size: 文件大小过小
  - unsupported_format: 不支持的格式
  - low_resolution: 视频分辨率过低

### 音频噪音过滤器（AudioNoiseFilter）

- **过滤规则**:
  - 最小时长: 5秒（音频价值判断）
  - 最小文件大小: 5KB
  - 支持格式: mp3, wav, aac, ogg, flac, wma
  - 最小比特率: 32kbps

- **过滤原因**:
  - short_duration: 音频时长过短（≤5秒）
  - small_file_size: 文件大小过小
  - unsupported_format: 不支持的格式
  - low_bitrate: 音频比特率过低

### 文本噪音过滤器（TextNoiseFilter）

- **过滤规则**:
  - 最小文本长度: 5个字符
  - 最小文件大小: 10B
  - 支持格式: txt, md, pdf, docx, xlsx, csv
  - 最小质量分数: 0.1

- **过滤原因**:
  - short_text: 文本长度过短
  - small_file_size: 文件大小过小
  - unsupported_format: 不支持的格式
  - low_quality: 文本质量过低

### 过滤时机和位置

1. **文件扫描阶段**: 提取基本元数据后立即进行初步过滤
2. **预处理阶段**: 进一步提取媒体特性后进行深度过滤
3. **检索阶段**: 对检索结果进行最终过滤

### 过滤结果处理

1. **跳过处理**: 对于被过滤的内容，直接跳过后续处理步骤
2. **记录日志**: 记录过滤原因和统计信息，便于分析和优化
3. **统计分析**: 定期生成过滤统计报告，优化过滤策略

## 视频检索结果时间轴展示

### 核心设计目标

- 直观展示视频片段在原视频中的时间位置
- 支持多视频结果的时间轴对比
- 提供高效的视频片段导航功能
- 优化用户体验，减少查找相关内容的时间

### 时间轴数据结构

### 视频时间轴条目（VideoTimelineItem）

- **字段**:
  - video_uuid: 视频文件唯一标识
  - video_name: 视频文件名
  - video_path: 视频文件路径
  - start_time: 片段开始时间（秒）
  - end_time: 片段结束时间（秒）
  - duration: 片段时长（秒）
  - relevance_score: 相关性评分
  - thumbnail_path: 片段缩略图路径
  - preview_path: 片段预览路径
  - scene_info: 场景信息
  - frame_count: 包含的帧数
  - metadata: 元数据

- **方法**:
  - formatted_duration(): 格式化时长显示
  - formatted_start_time(): 格式化开始时间显示
  - formatted_end_time(): 格式化结束时间显示
  - to_dict(): 转换为字典

### 视频时间轴结果（VideoTimelineResult）

- **字段**:
  - query: 用户查询
  - total_results: 总结果数
  - timeline_items: 时间轴条目列表
  - grouped_by_video: 按视频分组的条目
  - sorted_by_time: 按时间排序的条目
  - sorted_by_relevance: 按相关性排序的条目
  - metadata: 元数据

- **方法**:
  - add_item(): 添加时间轴条目
  - sort_by_time(): 按时间排序
  - sort_by_relevance(): 按相关性排序
  - get_video_count(): 获取视频数量
  - get_items_by_video(): 获取指定视频的条目
  - get_total_duration(): 获取总时长
  - to_dict(): 转换为字典

### 视频时间轴生成器（VideoTimelineGenerator）

- **方法**:
  - from_search_results(): 从搜索结果生成时间轴
  - from_database_results(): 从数据库结果生成时间轴
  - merge_timeline_results(): 合并时间轴结果（并集/交集）

### 时间轴展示UI/UX设计

1. **主时间轴视图**:
   - 横向时间轴，显示视频片段在时间线上的位置
   - 每个片段以缩略图形式展示，悬停显示详细信息
   - 支持缩放和平移操作，查看不同时间范围

2. **视频分组视图**:
   - 按视频文件分组展示时间轴
   - 支持展开/折叠单个视频的时间轴
   - 显示每个视频的总时长和相关片段数量

3. **交互功能**:
   - 点击片段播放预览
   - 拖动选择时间范围进行更精确的检索
   - 支持按相关性、时间顺序等多种排序方式
   - 提供筛选功能，过滤特定视频或时间范围

## PySide6桌面UI

### UI架构设计

```
MainWindow（主窗口）
├── SearchPanel（搜索面板）
│   ├── 文本搜索输入框
│   ├── 图像搜索上传区域
│   ├── 音频搜索上传区域
│   ├── 搜索类型选择
│   └── 搜索按钮
├── ResultPanel（结果面板）
│   ├── 结果列表
│   ├── 缩略图显示
│   ├── 时间轴视图
│   └── 结果详情
├── SettingsPanel（设置面板）
│   ├── 通用设置
│   ├── 搜索设置
│   ├── 索引设置
│   └── 模型设置
└── ProgressDialog（进度对话框）
    ├── 索引进度对话框
    ├── 搜索进度对话框
    └── 下载进度对话框
```

### UI组件功能

#### 主窗口（MainWindow）

- **功能**: 应用程序主窗口，协调各个UI组件
- **特性**:
  - 菜单栏：文件、编辑、视图、帮助
  - 工具栏：常用操作快捷按钮
  - 状态栏：显示系统状态和进度信息
  - 中央区域：搜索面板和结果面板的容器

#### 搜索面板（SearchPanel）

- **功能**: 提供搜索输入和搜索类型选择
- **特性**:
  - 文本搜索：支持自然语言查询
  - 图像搜索：支持拖拽上传参考图像
  - 音频搜索：支持拖拽上传音频样本
  - 搜索类型切换：文本/图像/音频
  - 搜索历史：记录最近的搜索查询

#### 结果面板（ResultPanel）

- **功能**: 显示搜索结果和详细信息
- **特性**:
  - 结果列表：显示匹配的文件
  - 缩略图预览：显示图像和视频的缩略图
  - 时间轴视图：显示视频片段的时间轴
  - 结果详情：显示文件的详细信息
  - 排序和过滤：支持按相关性、时间等排序

#### 设置面板（SettingsPanel）

- **功能**: 提供系统设置功能
- **特性**:
  - 通用设置：日志级别、工作线程数、数据目录
  - 搜索设置：结果数量、超时时间、显示选项
  - 索引设置：文件监控、任务管理
  - 模型设置：模型选择、批处理大小、设备选择
  - 配置导入/导出：支持配置文件的导入和导出

#### 任务管理器面板（TaskManagerPanel）

- **功能**: 显示任务进度和历史记录
- **特性**:
  - 当前任务：实时显示正在运行的任务
  - 任务历史：显示已完成和失败的任务记录
  - 统计信息：总任务数、进行中、已完成、失败统计
  - 任务详情：显示任务类型、状态、进度、时间信息
  - 刷新功能：定时刷新任务状态

#### 数据管理面板（DataManagerPanel）

- **功能**: 提供索引管理和数据统计功能
- **特性**:
  - 索引管理：显示索引状态、索引进度、索引文件数量统计
  - 数据统计：显示已处理文件总数、各类型文件统计、存储使用情况
  - 索引操作：支持重新索引、清理索引、导出索引报告
  - 数据概览：显示数据库状态、向量存储状态、索引健康度

#### 进度对话框（ProgressDialog）

- **功能**: 显示长时间操作的进度
- **特性**:
  - 索引进度对话框：显示文件索引进度
  - 搜索进度对话框：显示搜索进度
  - 下载进度对话框：显示模型下载进度
  - 可取消操作：支持取消长时间操作
  - 详细信息：显示操作的详细日志

### UI启动器（UILauncher）

- **功能**: 启动PySide6桌面应用
- **特性**:
  - 检查依赖：检查PySide6是否安装
  - 初始化配置：加载系统配置
  - 创建主窗口：创建并显示主窗口
  - 错误处理：处理启动过程中的错误

## 时间定位机制

### 数据结构设计

系统采用三层时间定位数据结构：

1. **VIDEO_METADATA表**：存储视频元数据
   - 视频基本信息（时长、分辨率、帧率）
   - 是否为短视频标记
   - 总片段数

2. **VIDEO_SEGMENTS表**：存储视频片段信息
   - 片段索引和时间范围
   - 是否为完整视频标记
   - 关键帧信息

3. **VECTOR_TIMESTAMP_MAP表**：存储向量与时间戳的映射
   - 向量ID与时间戳关联
   - 模态类型标识
   - 置信度评分

### 时间定位功能

- **精确时间戳查询**：根据向量ID获取对应时间戳
- **时间范围查询**：获取指定时间范围内的所有向量
- **视频时间戳聚合**：按视频文件聚合所有时间戳
- **时间戳精度保证**：±5秒精度要求

## 配置管理

系统使用 `config/config.yml` 进行配置，支持以下主要配置项：

- **system**: 系统级别配置（日志级别、最大工作线程数、健康检查间隔）
- **task_manager**: 任务管理配置（任务优先级、并发控制、资源限制）
  - max_concurrent_tasks: 最大并发任务数
  - max_retries: 最大重试次数
  - task_priorities: 任务优先级（MVP阶段：文搜图已提前到P1）
  - max_concurrent_by_type: 按类型的最大并发任务数
  - resource_limits: 资源限制（内存、CPU、GPU）
- **monitoring**: 监控配置（监控目录、检查间隔、防抖延迟）
- **processing**: 媒体处理配置（图像、视频、音频处理参数）
  - 短视频阈值配置
  - 音频价值阈值配置
- **models**: AI模型配置（模型选择、缓存目录、模型预热）
  - image_video_model: 图像/视频向量化模型配置（统一多模态模型）
    - chinese-clip-vit-base-patch16: 统一多模态模型（支持文本、图像、视频统一处理）
    - chinese-clip-vit-large-patch14-336px: 高精度多模态模型
    - SauerkrautLM-ColQwen3-1.7b-Turbo-v0.1: 高性能多模态模型
    - colqwen2.5-v0.2: 高精度多模态模型
    - tomoro-colqwen3-embed-4b: 超高精度多模态模型
  - clap_model: CLAP统一音频处理模型
  - facenet_model: 人脸识别模型（可选）
  - high_end_preference: 高配硬件模型偏好（chinese-clip-vit-large-patch14-336px）
- **database**: 数据库配置（SQLite路径、LanceDB路径、向量索引参数）
- **retry**: 重试策略配置（初始延迟、重试倍数、最大重试次数）
- **logging**: 日志配置（日志级别、格式、轮转策略）
- **api**: API服务配置（主机、端口、CORS、速率限制）
- **cache**: 缓存配置（缓存目录、最大缓存大小、TTL）
- **noise_filter**: 噪音过滤配置（图像、视频、音频、文本过滤规则）

## 部署和运行

### 环境要求
- Python 3.8+
- PyTorch >= 2.0.0（**重要**: [配置驱动模型]支持PyTorch 2.0+版本）
- 支持CUDA的GPU（推荐，用于加速AI推理）
- 至少8GB内存（推荐16GB+）
- 至少10GB可用存储空间

### 安装依赖
```bash
# 使用安装脚本（推荐）
bash scripts/install.sh

# 手动安装（核心依赖）
pip install -r requirements.txt

# 手动安装（开发依赖）
pip install -r requirements/dev.txt

# 手动安装（测试依赖）
pip install -r requirements/test.txt

# 手动安装（可选依赖）
pip install -r requirements/optional.txt
```

### 启动应用
```bash
# 启动完整应用
python src/main.py

# 仅启动API服务
python src/api_server.py

# 启动API服务（指定配置文件）
python src/api_server.py --config config/config.yml

# 启动API服务（指定主机和端口）
python src/api_server.py --host 0.0.0.0 --port 8000

# 启动PySide6桌面UI
python src/ui/ui_launcher.py
```

### 使用WebUI
1. 启动API服务后，在浏览器中打开 `webui/index.html`
2. 选择搜索类型（文本/图像/音频）
3. 输入查询或上传文件
4. 查看搜索结果

### 运行测试
```bash
# 运行所有测试
pytest

# 运行单元测试
pytest tests/unit/

# 运行集成测试
pytest tests/integration/

# 运行端到端测试
pytest tests/e2e/

# 运行性能测试
pytest tests/benchmark/

# 生成覆盖率报告
pytest --cov=src --cov-report=html:tests/.coverage/html --cov-report=xml:tests/.coverage/coverage.xml

# 运行模型集成测试
pytest tests/unit/test_model_integration.py -v -s

# 运行配置管理器测试
pytest tests/unit/test_config.py -v -s

# 运行噪音过滤器测试
pytest tests/unit/test_noise_filter.py -v -s

# 运行时间轴生成器测试
pytest tests/unit/test_timeline.py -v -s
```

### 设置模型
```bash
# 使用模型设置脚本
python scripts/setup_models.py

# 检查模型状态
python scripts/setup_models.py --check

# 清除模型缓存
python scripts/setup_models.py --clear
```

## 性能要求

- **检索响应**: ≤2秒返回前20个结果
- **视频定位精度**: ±5秒
- **短视频处理**: 速度提升3-5倍
- **音频价值判断**: 跳过≤5秒音频，节省计算资源
- **并发处理**: 支持4+个并发任务
- **内存使用**: 模型加载后≤4GB
- **系统稳定性**: 崩溃率低于0.1%

## 开发实践

### 代码规范
- 使用类型注解（Type Hints）
- 遵循PEP 8代码风格
- 使用异步编程（async/await）
- 完善的错误处理和日志记录
- **遵循独立性原则**: 使用依赖注入，模块间通过接口通信
- 遵循单一职责原则
- 没有错误代码或空代码
- 所有TODO标记都有明确的实现说明

### 测试策略
- 单元测试：测试各个模块的核心功能
- 集成测试：测试模块间的协作
- 端到端测试：测试完整的用户流程
- 性能测试：测试系统性能指标
- 模型集成测试：验证AI模型的加载和使用

### 测试工具
- pytest: 测试框架
- pytest-asyncio: 异步测试支持
- pytest-cov: 代码覆盖率

### 测试目录规范
- 统一测试目录：所有测试代码统一放在 `tests/` 目录下
- 测试文件命名规范：
  - 单元测试：`test_*.py`
  - 集成测试：`it_*.py`
  - 端到端测试：`e2e_*.py`
  - 性能基准测试：`test_*_benchmark.py`
- 测试数据管理：测试数据与 fixtures 放在 `tests/data/` 子目录
- 临时文件管理：临时文件统一输出到 `tests/.tmp/` 并在 `.gitignore` 中忽略
- 覆盖率报告：统一输出到 `tests/.coverage/` 目录

## 安全考虑

### 数据安全
- 敏感数据加密存储
- 访问控制和权限管理
- 数据备份和恢复机制

### 系统安全
- 输入验证和清理
- 防止路径遍历攻击
- 资源使用限制

### 隐私保护
- 用户数据本地存储
- 不上传任何用户数据
- 支持数据删除和清理

## 国内镜像站使用方法

### Infinity框架
1. 安装依赖：`pip install -U huggingface_hub`
2. 设置环境变量：`export HF_ENDPOINT=https://hf-mirror.com`
3. 下载模型：`huggingface-cli download --resume-download --local-dir-use-symlinks False model_name --local-dir local_path`
4. 对于需要登录的模型，添加`--token hf_***`参数

### GitHub镜像站
1. 替换URL方式：`git clone https://gitclone.com/github.com/username/repository.git`
2. 设置Git参数方式：`git config --global url."https://gitclone.com/".insteadOf https://`
3. 使用cgit客户端：`cgit clone https://github.com/username/repository.git`

### PyPI镜像源
1. 清华大学镜像：`pip install package_name -i https://pypi.tuna.tsinghua.edu.cn/simple`
2. 阿里云镜像：`pip install package_name -i https://mirrors.aliyun.com/pypi/simple`
3. 中科大镜像：`pip install package_name -i https://pypi.mirrors.ustc.edu.cn/simple`

### Windows安装脚本编码要求
创建Windows安装脚本必须使用GBK编码，以确保在Windows系统中正确显示中文字符

### WebUI界面设计原则
在设计文档中增加webui界面的设计，以便在测试软件时只需要测试相关接口就能知道程序是否正常，只在最后才开始测试跨平台pyside的ui

### 技术编码要求
编码的技术要求必须遵守docs/technical_reference.md中的规定

## 完全离线模式配置

### 重要说明

**Infinity框架不支持`local_files_only`参数**

项目使用Infinity框架进行模型推理，该框架本身不支持HuggingFace的`local_files_only`参数。要实现完全离线运行，需要：

1. **设置环境变量**：禁用所有网络请求和HuggingFace连接
2. **使用本地模型路径**：模型路径必须是本地目录，不能是HuggingFace模型ID
3. **确保模型文件完整**：本地模型目录必须包含所有必需文件

### 离线模式环境变量

```bash
# Transformers离线模式（必须在导入任何模块之前设置）
export TRANSFORMERS_OFFLINE=1
export HF_DATASETS_OFFLINE=1
export HF_HUB_OFFLINE=1

# 禁用HuggingFace遥测和警告
export HF_HUB_DISABLE_TELEMETRY=1
export HF_HUB_DISABLE_EXPERIMENTAL_WARNING=1
export HF_HUB_DISABLE_IMPORT_ERROR=1

# 设置HuggingFace缓存目录
export HF_HOME="data/models"
export HUGGINGFACE_HUB_CACHE="data/models"

# 禁用所有网络请求
export NO_PROXY='*'
export no_proxy='*'
```

**重要说明**：
- 环境变量必须在**代码最开头、导入任何模块之前**设置
- `model_name_or_path` 必须使用**本地绝对路径**，不能使用 HuggingFace 模型 ID
- 如遇 `LocalEntryNotFoundError`，请检查模型文件是否完整下载

### 模型文件要求

本地模型目录必须包含以下文件：

```
data/models/chinese-clip-vit-base-patch16/
├── config.json              # 模型配置
├── tokenizer.json           # 分词器配置
├── tokenizer_config.json    # 分词器配置
├── special_tokens_map.json  # 特殊token映射
├── model.safetensors        # 模型权重（或pytorch_model.bin）
└── preprocessor_config.json # 预处理器配置（多模态模型）
```

### 启动离线模式

使用提供的启动脚本：

```bash
# 使用完全离线模式启动
bash scripts/run_offline.sh

# 或者手动设置环境变量后启动
export TRANSFORMERS_OFFLINE=1
export HF_DATASETS_OFFLINE=1
export HF_HUB_OFFLINE=1
export HF_HOME="data/models"
export HF_HUB_DISABLE_IMPORT_ERROR=1
python3 src/main.py
```

### 验证离线模式

运行验证脚本检查离线模式配置：

```bash
python3 scripts/verify_offline_mode.py
```

该脚本会检查：
- 环境变量是否正确设置
- 配置文件是否正确
- 模型文件是否完整
- 必要的依赖是否安装

### 常见离线问题

**问题1**: 模型加载时尝试连接HuggingFace

**原因**: 
- 环境变量未正确设置
- 模型路径使用了HuggingFace模型ID而非本地路径

**解决方案**:
```python
# 错误：使用HuggingFace模型ID
engine_args = EngineArgs(
    model_name_or_path="[配置驱动模型]"  # ❌ 会尝试连接HuggingFace
)

# 正确：使用本地绝对路径
engine_args = EngineArgs(
    model_name_or_path="/data/project/msearch/data/models/chinese-clip-vit-large-patch14-336px"  # ✅ 使用本地绝对路径
)
```

**问题2**: 模型文件不完整

**症状**: `FileNotFoundError: [Errno 2] No such file or directory: 'config.json'`

**解决方案**: 确保模型目录包含所有必需文件，使用`setup_models.py`脚本下载完整模型：

```bash
python scripts/setup_models.py
```

**问题3**: 仍有网络请求

**原因**: 环境变量设置时机不对

**解决方案**: 确保在导入任何transformers或infinity模块**之前**设置环境变量。项目已在以下位置设置环境变量：
- `src/core/embedding/embedding_engine.py`（模块开头）
- `src/core/models/model_manager.py`（setup_offline_mode函数）
- `src/cli.py`（CLI入口）
- `scripts/run_offline.sh`（启动脚本）

## 项目状态

### 已完成
- [x] 项目需求文档（docs/requirements.md）
- [x] 项目设计文档（docs/design.md）
- [x] 项目任务列表（docs/tasks.md）
- [x] 配置文件（config/config.yml）
- [x] 依赖文件（requirements.txt + requirements/目录）
- [x] WebUI界面（webui/index.html）
- [x] 测试目录结构（tests/）
- [x] 测试配置文件（tests/pytest.ini）
- [x] 测试夹具（tests/fixtures/）
- [x] API文档（docs/api.md）
- [x] 数据模型文档（docs/data-models.md）
- [x] 测试策略文档（docs/testing-strategy.md）
- [x] 代码与设计偏差分析（docs/code_design_deviation_analysis.md）
- [x] 代码重构总结（docs/code_refactoring_summary.md）
- [x] 核心模块实现（22个核心文件，约7100行代码）
  - [x] ConfigManager（配置管理器，路径已修复为config/config.yml）
  - [x] DatabaseManager（数据库管理器，978行）
  - [x] VectorStore（向量存储，365行）
  - [x] EmbeddingEngine（向量化引擎，统一使用Infinity，约400行）
    - [x] chinese-clip-vit-base-patch16模型集成（统一多模态模型，支持文本、图像、视频统一处理）
- [x] chinese-clip-vit-large-patch14-336px模型集成（高精度多模态模型）
- [x] SauerkrautLM-ColQwen3-1.7b-Turbo-v0.1模型集成（高性能多模态模型）
- [x] colqwen2.5-v0.2模型集成（高精度多模态模型）
- [x] tomoro-colqwen3-embed-4b模型集成（超高精度多模态模型）
    - [x] [配置驱动模型]集成（统一音频处理）
    - [x] Infinity框架（高性能推理）
    - [x] 硬件自适应模型选择（统一多模态模型）
    - [x] 音频向量化（embed_audio_from_path）
  - [x] TaskManager（任务管理器，795行）
  - [x] TaskMonitor（任务监控器，新增功能模块）
  - [x] DataManager（数据管理器，新增功能模块）
  - [x] SearchEngine（搜索引擎，使用依赖注入）
    - [x] 文本搜索（search）
    - [x] 图像搜索（image_search）
    - [x] 音频搜索（audio_search）
  - [x] HardwareDetector（硬件检测器，592行）
  - [x] FileMonitor（文件监控器，397行）
  - [x] MediaProcessor（媒体处理器，570行）
    - [x] CLAP音频分类（_classify_audio_type）
  - [x] LoggingConfig（日志配置管理器，448行）
  - [x] NoiseFilterManager（噪音过滤器管理器，450行）
    - [x] ImageNoiseFilter（图像噪音过滤器）
    - [x] VideoNoiseFilter（视频噪音过滤器）
    - [x] AudioNoiseFilter（音频噪音过滤器）
    - [x] TextNoiseFilter（文本噪音过滤器）
  - [x] VideoTimelineGenerator（视频时间轴生成器，400行）
    - [x] VideoTimelineItem（视频时间轴条目）
    - [x] VideoTimelineResult（视频时间轴结果）
  - [x] Exceptions（异常定义）
- [x] 服务层实现（1544行代码）
  - [x] PreprocessingCache（预处理缓存管理器，395行）
  - [x] FileMonitor（文件监控服务，347行）
  - [x] MediaProcessor（媒体处理服务，797行）
- [x] 主程序入口（main.py，使用依赖注入）
- [x] API服务层（api_server.py，使用依赖注入）
  - [x] RESTful API接口
  - [x] 检索API
  - [x] 文件管理API
  - [x] 任务管理API
  - [x] 系统信息API
- [x] 时间定位机制
  - [x] VIDEO_METADATA表
  - [x] VIDEO_SEGMENTS表
  - [x] VECTOR_TIMESTAMP_MAP表
  - [x] 向量元数据管理（包含时间戳信息）
  - [x] 时间戳查询接口
- [x] PySide6桌面UI（约2000行代码）
  - [x] MainWindow（主窗口，使用依赖注入）
  - [x] UILauncher（UI启动器）
  - [x] SearchPanel（搜索面板组件）
  - [x] ResultPanel（结果面板组件）
  - [x] SettingsPanel（设置面板组件）
  - [x] TaskManagerPanel（任务管理器面板组件，新增功能）
  - [x] DataManagerPanel（数据管理面板组件，新增功能）
  - [x] ProgressDialog（进度对话框）
- [x] 部署脚本
  - [x] install.sh（Linux安装脚本）
  - [x] setup_models.py（模型设置脚本）
- [x] 单元测试框架
  - [x] pytest配置
  - [x] conftest.py配置
  - [x] 测试夹具工厂
  - [x] 覆盖率报告配置
  - [x] 模型集成测试（test_model_integration.py，7个测试全部通过）
  - [x] 数据库管理器测试（test_database_manager.py，12个测试全部通过）
  - [x] 搜索引擎测试（test_search_engine.py，12个测试全部通过）
  - [x] 配置管理器测试（test_config.py，33个测试全部通过）
  - [x] 噪音过滤器测试（test_noise_filter.py，27个测试全部通过）
  - [x] 时间轴生成器测试（test_timeline.py，22个测试全部通过）
- [x] 集成测试
  - [x] it_search_flow.py（搜索流程集成测试）
  - [x] it_indexing_flow.py（索引流程集成测试）
- [x] 端到端测试
  - [x] e2e_full_workflow.py（完整工作流程端到端测试）
- [x] 性能基准测试
  - [x] test_embedding_benchmark.py（向量化性能基准测试）
- [x] 代码质量保证
  - [x] 所有42个Python文件语法检查通过
  - [x] 没有错误代码或空代码
  - [x] 符合PEP 8代码规范（除必要的路径修改导入）
  - [x] 所有113个核心单元测试通过
  - [x] 文搜图功能提前到MVP阶段（P1优先级）
- [x] 代码重构（2026-01-19）
  - [x] 修复配置文件路径不一致问题
  - [x] 重构向量化引擎，统一使用Infinity
  - [x] 重构核心模块，使用依赖注入
  - [x] 分离依赖管理文件

### 进行中
- [ ] 单元测试完善（113个核心测试已完成，部分边缘测试待补充）
- [ ] 集成测试完善（基础集成测试已完成，扩展测试待补充）
- [ ] 端到端测试完善（基础端到端测试已完成，扩展测试待补充）
- [ ] 性能优化和调优

### 待开发
- [ ] 用户文档
- [ ] API文档补充
- [ ] 部署文档
- [ ] 性能优化报告

## 架构优化总结

### 简化架构
- 合并配置管理模块（config_manager + config_validator → config.py）
- 简化向量存储设计，避免循环依赖
- 明确任务优先级和依赖关系
- 统一测试目录结构，规范测试文件命名
- **统一图像/视频向量化工作流程**: 消除抽帧逻辑，简化视频预处理
- **模块化设计**: 核心模块按功能分类到子目录（config/, database/, vector/, embedding/, task/, ipc/, hardware/, logging/）
- **依赖注入架构**: 使用依赖注入替代直接导入，提高模块独立性和可测试性
- **多进程模块化**: 将进程间通信、共享内存、进程管理等功能模块化设计

### 性能优化
- 短视频快速处理（≤6秒），性能提升3-5倍
- 音频价值判断（≤5秒），节省计算资源
- 基于文件哈希的去重机制，避免重复处理
- 缩略图和预览去重，减少存储空间
- 预处理缓存机制，提升重复处理效率
- **Infinity优化**: Python-native模式，动态批处理和FlashAttention加速
- **低价值噪音过滤**: 智能过滤低价值内容，提高系统效率和检索质量
- **多进程架构**: 计算密集型任务与主应用解耦，提升系统并发处理能力和稳定性
- **进程间通信优化**: 使用Redis实现高效的任务分发和状态同步机制

### 设计优化
- 音频分类与模型选择映射清晰
- 时序定位精度优化（短视频简化）
- 任务调度策略明确（优先级+依赖+并发控制）
- 配置管理统一，功能完整
- 时间定位机制完善，支持精确查询
- 预处理缓存目录结构清晰，便于管理
- 硬件自适应模型选择更加灵活（支持2个级别：低配和高配）
- **统一向量化接口**: 图像和视频使用相同的向量化接口，配合[配置驱动模型]优化
- **MVP优先级优化**: 文搜图功能提前到P1优先级，与文本向量化并列
- **Infinity集成**: 使用Infinity框架，高性能推理
- **统一模型**: 使用[配置驱动模型]统一多模态模型，简化架构
- **文件监控服务完善**: 实现了文件创建、修改、删除、移动事件的处理逻辑
- **低价值噪音过滤**: 智能过滤低价值内容，提高系统效率和检索质量
- **视频时间轴展示**: 支持视频检索结果的时间轴可视化展示
- **依赖注入重构**: 核心模块使用依赖注入，提高模块独立性和可测试性
- **多进程架构设计**: 将计算密集型任务与主应用解耦，提升系统稳定性和可扩展性
- **进程间通信机制**: 基于Redis实现可靠的进程间通信，支持任务分发和状态同步

### 开发量降低
- **消除抽帧逻辑**: [配置驱动模型]模型直接支持视频输入，无需抽帧
- **统一代码路径**: 图像和视频使用相同的处理流程，减少代码分支
- **简化维护**: 统一的代码路径，减少bug和维护成本
- **减少测试复杂度**: 统一的向量化流程，减少测试用例数量
- **降低学习成本**: 简化的架构，新开发者更容易理解和维护
- **依赖注入**: 使用依赖注入替代直接导入，提高模块独立性和可测试性

### 代码质量保证
- **无错误代码**: 所有42个Python文件语法检查通过
- **无空代码**: 所有TODO标记都有明确的实现说明或返回值
- **符合PEP 8**: 代码风格符合Python编码规范（除必要的路径修改导入）
- **测试覆盖**: 113个核心单元测试全部通过，覆盖核心功能
- **文档完整**: 完善的需求文档、设计文档、测试策略文档
- **Infinity集成**: 使用Infinity框架，高性能推理
- **依赖注入**: 核心模块使用依赖注入，提高模块独立性和可测试性

### 测试优化
- 统一测试目录和配置
- 完善的测试夹具工厂
- 覆盖率报告自动生成
- 测试数据按业务域和版本组织
- 模型集成测试覆盖所有新模型
- 已实现测试：test_config.py、test_database_manager.py、test_search_engine.py、test_model_integration.py、test_noise_filter.py、test_timeline.py
- 集成测试：it_search_flow.py、it_indexing_flow.py
- 端到端测试：e2e_full_workflow.py
- 性能基准测试：test_embedding_benchmark.py

### MVP阶段优化
- **文搜图提前**: 图像向量化任务优先级从P3提升到P1，与文本向量化并列
- **核心功能聚焦**: MVP阶段专注于核心基础设施、文本向量化、图像向量化
- **快速验证**: 通过WebUI快速验证核心功能，无需等待PySide6 UI完成
- **渐进式开发**: 先实现核心功能，再逐步扩展高级功能

### 新增模块
- **LoggingConfig**: 日志配置管理器，负责配置日志级别、格式、轮转策略和处理器，提供统一的日志管理接口
- **NoiseFilterManager**: 低价值噪音过滤管理器，支持图像、视频、音频、文本的智能过滤
- **VideoTimelineGenerator**: 视频时间轴生成器，支持时间轴结果生成和管理
- **TaskMonitor**: 任务监控器，负责任务进度跟踪、任务统计、任务历史记录和性能指标计算
- **TaskManagerPanel**: 任务管理器面板组件，提供任务进度和历史记录的图形界面展示
- **DataManager**: 数据管理模块，负责索引管理和数据统计功能
- **IPCManager**: 进程间通信管理器，提供基于Redis的多进程通信机制，支持任务分发、状态同步和心跳检测
- **SharedMemoryManager**: 共享内存管理器，用于大文件数据的跨进程高效传输，减少序列化开销
- **ProcessManager**: 多进程管理器，负责协调主进程与工作进程的生命周期管理
- **FileMonitorProcess**: 文件监控进程，独立监控文件系统变化并通知主进程
- **EmbeddingWorkerProcess**: 向量化工作进程，专门负责AI模型推理任务
- **TaskWorkerProcess**: 任务工作进程，处理非推理类任务（媒体预处理、文件转换等）
- **PySide6 UI**: 跨平台桌面应用，提供完整的用户交互界面
  - MainWindow: 主窗口（使用依赖注入）
  - UILauncher: UI启动器
  - SearchPanel: 搜索面板组件
  - ResultPanel: 结果面板组件
  - SettingsPanel: 设置面板组件
  - TaskManagerPanel: 任务管理器面板组件（新增）
  - DataManagerPanel: 数据管理面板组件（新增）
  - ProgressDialog: 进度对话框

### 部署优化
- **安装脚本**: 自动化安装过程，检查Python版本、创建虚拟环境、安装依赖
- **模型设置脚本**: 自动化模型下载和管理，支持模型状态检查和清除
- **依赖分离**: 依赖文件分离为base/dev/test/optional，便于灵活安装
- **多进程启动**: 提供统一的多进程架构启动和管理脚本（msearchctl）
- **Redis集成**: 自动配置和启动Redis服务以支持进程间通信

---

*最后更新: 2026-01-28*
*架构: 多进程架构（主进程、文件监控进程、向量化工作进程、任务工作进程，通过Redis通信）*
*状态: 核心模块、服务层、API服务层、时间定位机制、预处理缓存、噪音过滤、视频时间轴、PySide6 UI、部署脚本已完成，单元测试、集成测试、端到端测试、性能基准测试已实现，所有核心测试通过，代码重构完成*
*代码规模: 104个Python文件，核心模块约7100行代码，服务层约1544行代码，主程序约400行（重构后），API服务器约300行（重构后），PySide6 UI约2000行，多进程架构模块约1200行，总计约28565行代码*
*测试覆盖: 113个核心单元测试全部通过（test_config.py: 33个, test_database_manager.py: 12个, test_search_engine.py: 12个, test_model_integration.py: 7个, test_noise_filter.py: 27个, test_timeline.py: 22个）*
*优化: 短视频优化、音频价值判断、文件去重、任务优先级管理、CLAP音频向量化、预处理缓存机制、配置管理合并优化、[配置驱动模型]集成、CLAP音频分类、架构简化减少开发量、统一向量化工作流程、Infinity框架、动态批处理和FlashAttention加速、模块化设计、代码质量保证、MVP优先级优化、文搜图提前到P1、LoggingConfig日志配置管理器、文件监控服务完善、低价值噪音过滤、视频时间轴展示、PySide6桌面UI完成、部署脚本完成、集成测试完成、端到端测试完成、性能基准测试完成、依赖注入重构完成、配置路径修复完成、向量化引擎简化完成、依赖管理分离完成、TaskMonitor任务监控器、TaskManagerPanel任务管理器面板、DataManager数据管理器、DataManagerPanel数据管理面板、IPCManager进程间通信管理器、SharedMemoryManager共享内存管理器、ProcessManager多进程管理器、FileMonitorProcess文件监控进程、EmbeddingWorkerProcess向量化工作进程、TaskWorkerProcess任务工作进程、多进程架构优化*
*设计要求达成率: 约98%（核心功能、UI、测试、部署全部完成，代码重构完成）*