# msearch 多模态搜索系统设计文档

## 第一部分：项目逻辑和关键设计

### 1.1 项目概述

msearch 是一款单机可运行的跨平台多模态桌面检索软件，专为视频剪辑师设计，实现素材无需整理、无需标签的智能检索。

**核心目标**：
- 提供跨模态的智能检索能力（文本、图像、视频、音频）
- 实现素材自动索引和向量化
- 支持本地化部署，无需网络依赖
- 提供简洁高效的用户界面
- 避免桌面环境过度工程化，保持架构演进的灵活性

**技术栈**：
- **图像/视频向量化模型**（硬件自适应）：参见 [1.6.1 分级硬件自适应模型策略](#161-分级硬件自适应模型策略)
- **音频模型**（CLAP/Whisper/InaSpeechSegmenter）：参见 [1.6.2 音频模型集成与分类策略](#162-音频模型集成与分类策略)
- **Python 原生集成模型**：直接使用transformers、torch等库调用各AI模型进行推理，不引入任何额外服务引擎
- **LanceDB**：向量数据库（单一向量表设计），参见 [1.6.3 数据库技术选型](#163-数据库技术选型)
- **SQLite**：元数据存储，参见 [1.6.3 数据库技术选型](#163-数据库技术选型)

**架构原则**：
- **单机优先**：所有功能在单机环境运行，无需网络依赖
- **简洁设计**：避免过度工程化，保持桌面版架构简洁性
- **Python原生**：直接集成模型，不使用任何外部服务引擎

### 1.2 核心设计原则

#### 1.2.1 独立性原则
每个代码文件应该能够独立运行，通过参数传递所有需要的配置、数据和依赖，而不是直接导入其他模块。

**优点**：
- 便于单元测试：每个模块可以独立测试
- 降低耦合度：模块之间通过清晰的接口通信
- 提高可维护性：修改一个模块不影响其他模块

**实现要求**：
- 所有依赖通过构造函数参数传递
- 不在模块内部直接导入其他业务模块
- 使用数据类或字典传递配置和状态

#### 1.2.2 单一职责原则
每个模块专注于一个明确的功能领域，不承担过多职责。

**优点**：
- 职责清晰，易于理解
- 便于测试和调试
- 降低修改风险

**实现要求**：
- 每个模块只负责一个功能领域
- 复杂逻辑通过组合多个简单模块实现
- 避免一个模块承担多个不相关的职责

#### 1.2.3 MVP迭代原则
先实现核心功能（MVP），再逐步扩展高级功能。

**优点**：
- 快速验证核心价值
- 降低开发风险
- 便于用户反馈驱动迭代

**MVP交付清单**：
1. **文本搜图像/视频**（MobileCLIP，±5秒精度）
2. **图像搜图像/视频**（MobileCLIP）
3. **目录监控与自动索引**
4. **基础UI**

**优先级定义（P0-P10）**：

| 优先级 | 功能模块 | 任务类型 | 说明 |
|--------|----------|----------|------|
| **P0** | 核心基础设施 | - | 配置管理、数据库管理、向量存储基础 |
| **P1** | 文本向量化 | file_embed_text | 使用各模型处理文字向量化 |
| **P2** | 文件扫描 | file_scan | 扫描目录，识别文件类型 |
| **P3** | 图像向量化 | file_embed_image | 图像特征提取和向量化 |
| **P4** | 视频向量化 | file_embed_video | 视频切片、关键帧提取、向量化 |
| **P5** | 音频向量化 | file_embed_audio | 音频特征提取和向量化 |
| **P6** | 向量搜索 | search | 多模态向量检索 |
| **P7** | 结果排序 | rank | 搜索结果排序和过滤 |
| **P8** | 目录监控 | directory_watch | 实时监控目录变化 |
| **P9** | 自动索引 | auto_index | 自动触发索引任务 |
| **P10** | 基础UI | ui | 用户界面和交互 |

**任务优先级映射**：

```python
# TaskManager任务优先级配置
TASK_PRIORITIES = {
    # P0: 核心基础设施
    "config_load": 0,
    "database_init": 0,
    "vector_store_init": 0,
    
    # P1: 文本向量化
    "file_embed_text": 1,
    
    # P2: 文件扫描
    "file_scan": 2,
    
    # P3: 图像向量化
    "file_embed_image": 3,
    
    # P4: 视频向量化
    "video_slice": 4,
    "file_embed_video": 4,
    
    # P5: 音频向量化
    "audio_segment": 5,
    "file_embed_audio": 5,
    
    # P6: 向量搜索
    "search": 6,
    "search_multimodal": 6,
    
    # P7: 结果排序
    "rank_results": 7,
    "filter_results": 7,
    
    # P8: 目录监控
    "directory_watch": 8,
    
    # P9: 自动索引
    "auto_index": 9,
    
    # P10: 基础UI
    "ui_render": 10,
    "ui_update": 10
}
```

**MVP实现路径**：

**第一阶段（P0-P3）**：核心基础设施和基础向量化
- P0: 配置管理、数据库管理、向量存储
- P1: 文本向量化（支持文本搜索）
- P2: 文件扫描（识别图像、视频文件）
- P3: 图像向量化（支持图像搜索）

**第二阶段（P4-P7）**：多模态检索
- P4: 视频向量化（支持视频搜索）
- P5: 音频向量化（支持音频搜索）
- P6: 向量搜索（多模态检索）
- P7: 结果排序（搜索结果优化）

**第三阶段（P8-P10）**：自动化和UI
- P8: 目录监控（实时监控文件变化）
- P9: 自动索引（自动触发索引任务）
- P10: 基础UI（用户界面）

**实现要求**：
- 第一阶段（MVP核心）：实现基本的文件索引和检索功能（P0-P3）
- 第二阶段（MVP完整）：添加多模态检索和权重融合（P4-P7）
- 第三阶段（MVP增强）：添加高级功能（P8-P10）

### 1.3 总体架构

#### 1.3.1 架构分层

```
┌─────────────────────────────────────────────────────────────────┐
│                    用户界面层 (UI)                      │
│  - main_window.py: 主窗口                               │
│  - ui_launcher.py: UI启动器                              │
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
│  - face_services/: 人脸识别服务（可选）                     │
├─────────────────────────────────────────────────────────────────┤
│                    核心组件层 (Core)                       │
│  - config_manager.py: 配置管理                          │
│  - database_manager.py: 数据库管理                        │
│  - vector_store.py: 向量存储                            │
│  - embedding_engine.py: 向量化引擎                          │
│  - task_manager.py: 任务管理                            │
│  - hardware_detector.py: 硬件检测                        │
│  - unified_data_access.py: 统一数据访问层                    │
├─────────────────────────────────────────────────────────────────┤
│                    数据层 (Data)                         │
│  - metadata_extractor.py: 元数据提取器                      │
│  - thumbnail_generator.py: 缩略图生成器                    │
│  - models.py: 数据模型定义                              │
├─────────────────────────────────────────────────────────────────┤
│                    工具层 (Utils)                         │
│  - config_validator.py: 配置验证器                        │
│  - error_handling.py: 错误处理                          │
│  - exceptions.py: 异常定义                              │
└─────────────────────────────────────────────────────────────────┘
```

#### 1.3.2 数据流转逻辑

**文件处理完整流程（带任务优先级）**：

```
[任务0: file_scan] 文件监控/扫描
    ↓
[任务1: file_scan] 元数据提取 + 文件哈希计算
    ↓
    ├─→ [任务1: file_embed_image] 图像预处理 → 图像向量化 → 向量存储
    ├─→ [任务2: video_slice] 视频预处理（短视频快速处理/长视频切片）
    │       ↓
    │       └─→ [任务1: file_embed_video] 视频向量化 → 向量存储
    ├─→ [任务3: file_embed_text] 文本向量化 → 向量存储
    ├─→ [任务4: audio_segment] 音频分段（价值检查 > 5秒）
    │       ↓
    │       └─→ [任务5: file_embed_audio] 音频向量化 → 向量存储
    ├─→ [任务6: thumbnail_generate] 缩略图生成（基于文件哈希）
    └─→ [任务7: preview_generate] 预览生成（基于文件哈希）
```

**任务执行优先级说明**：

1. **P0 - file_scan（文件扫描）**
   - 优先级：0（最高）
   - 说明：基础任务，必须首先完成
   - 无依赖
   - 执行：扫描目录，提取文件元数据，计算文件哈希

2. **P1 - file_embed_image（图像向量化）**
   - 优先级：1（高）
   - 说明：图像检索是核心功能，优先处理
   - 依赖：file_scan
   - 执行：图像预处理 → 向量化 → 存储

3. **P1 - file_embed_video（视频向量化）**
   - 优先级：1（高）
   - 说明：视频检索是核心功能，优先处理
   - 依赖：file_scan + video_slice
   - 执行：视频预处理 → 向量化 → 存储

4. **P2 - video_slice（视频切片）**
   - 优先级：2（中高）
   - 说明：视频预处理任务，为向量化做准备
   - 依赖：file_scan
   - 执行：短视频快速处理（≤6秒）或长视频切片（>6秒）

5. **P3 - file_embed_text（文本向量化）**
   - 优先级：3（中）
   - 说明：文本检索功能，中等优先级
   - 依赖：file_scan
   - 执行：文本预处理 → 向量化 → 存储

6. **P4 - audio_segment（音频分段）**
   - 优先级：4（中低）
   - 说明：音频预处理任务，较低优先级
   - 依赖：file_scan
   - 执行：音频价值检查（>5秒）→ InaSpeechSegmenter分类

7. **P5 - file_embed_audio（音频向量化）**
   - 优先级：5（低）
   - 说明：音频检索功能，较低优先级
   - 依赖：file_scan + audio_segment
   - 执行：音频向量化（CLAP/Whisper）→ 存储

8. **P6 - thumbnail_generate（缩略图生成）**
   - 优先级：6（低）
   - 说明：UI辅助功能，低优先级
   - 依赖：file_scan
   - 执行：基于文件哈希生成缩略图

9. **P7 - preview_generate（预览生成）**
   - 优先级：7（最低）
   - 说明：UI辅助功能，最低优先级
   - 依赖：file_scan
   - 执行：基于文件哈希生成预览

**检索流程**：
```
用户查询 → 查询向量化 → 向量检索 → 结果排序与融合 → 结果返回
```

**任务调度策略**：

1. **优先级调度**：按优先级从高到低执行任务
2. **依赖检查**：执行前检查依赖任务是否完成
3. **并发控制**：根据任务类型限制并发数
   - file_scan: 1（串行执行）
   - file_embed: 2（最多2个并发）
   - video_slice: 2（最多2个并发）
   - audio_segment: 2（最多2个并发）
4. **资源限制**：监控CPU、内存、GPU使用，避免资源耗尽

### 1.4 项目结构

```
msearch/
├── src/                    # 源代码目录
│   ├── main.py            # 主程序入口
│   ├── api_server.py       # API服务器入口
│   ├── core/              # 核心组件层
│   │   ├── config/         # 配置管理
│   │   │   ├── config_manager.py
│   │   │   └── config_validator.py
│   │   ├── database/       # 数据库管理
│   │   │   ├── database_manager.py
│   │   │   └── unified_data_access.py
│   │   ├── vector/         # 向量存储
│   │   │   └── vector_store.py
│   │   ├── embedding/      # 向量化引擎
│   │   │   ├── embedding_engine.py
│   │   │   └── model_manager.py        # 模型管理器
│   │   ├── task/           # 任务管理
│   │   │   ├── task_manager.py
│   │   │   └── task_scheduler.py
│   │   ├── hardware/       # 硬件检测
│   │   │   └── hardware_detector.py
│   │   ├── config/         # 配置管理
│   │   │   └── config.py    # 配置管理器（合并验证、加载、查询）
│   │   └── logging/        # 日志配置
│   │       └── logging_config.py
│   ├── data/              # 数据层
│   │   ├── extractors/     # 数据提取器
│   │   │   ├── metadata_extractor.py
│   │   │   └── content_analyzer.py
│   │   ├── generators/     # 数据生成器
│   │   │   ├── thumbnail_generator.py
│   │   │   └── preview_generator.py
│   │   ├── models/         # 数据模型
│   │   │   ├── base_models.py
│   │   │   ├── search_models.py
│   │   │   └── task_models.py
│   │   ├── validators/     # 数据验证器
│   │   │   ├── file_validator.py
│   │   │   └── content_validator.py
│   │   └── constants.py
│   ├── services/          # 服务层
│   │   ├── search/         # 检索服务
│   │   │   ├── search_engine.py
│   │   │   ├── query_processor.py
│   │   │   └── result_ranker.py
│   │   ├── media/          # 媒体处理服务
│   │   │   ├── media_processor.py
│   │   │   ├── video/      # 视频处理
│   │   │   │   ├── video_processor.py
│   │   │   │   ├── scene_detector.py
│   │   │   │   └── frame_extractor.py
│   │   │   ├── image_processor.py  
│   │   │   └── audio/      # 音频处理
│   │   │       ├── audio_processor.py
│   │   │       └── audio_segmenter.py
│   │   ├── file/           # 文件处理服务
│   │   │   ├── file_monitor.py
│   │   │   ├── file_scanner.py
│   │   │   └── file_indexer.py
│   │   ├── face/           # 人脸识别服务（可选）
│   │   │   ├── face_manager.py
│   │   │   └── face_recognizer.py
│   │   └── cache/          # 缓存服务
│   │       └── cache_manager.py
│   ├── ui/                # 用户界面层
│   │   ├── main_window.py
│   │   ├── ui_launcher.py
│   │   ├── components/     # UI组件
│   │   │   ├── search_panel.py
│   │   │   ├── result_panel.py
│   │   │   └── settings_panel.py
│   │   └── dialogs/        # 对话框
│   │       ├── progress_dialog.py
│   │       └── settings_dialog.py
│   ├── utils/             # 工具层
│   │   ├── error_handling.py
│   │   ├── exceptions.py
│   │   ├── retry.py
│   │   ├── helpers.py
│   │   └── file_utils.py
│   └── api/              # API服务层（服务化预留）
│       ├── __init__.py
│       ├── v1/             # API v1版本
│       │   ├── routes.py
│       │   ├── handlers.py
│       │   ├── schemas.py
│       │   └── dependencies.py
│       └── middlewares.py  # API中间件
├── tests/               # 测试目录
│   ├── __init__.py
│   ├── pytest.ini       # pytest配置文件
│   ├── conf.d/          # 按域拆分的conftest
│   │   ├── conftest_msearch.py
│   │   └── conftest_api.py
│   ├── .coverage/       # 覆盖率报告（HTML/XML/CSV）
│   ├── .tmp/            # 临时文件（已gitignore）
│   ├── data/            # 测试数据
│   │   ├── msearch/
│   │   │   └── v1/
│   │   └── api/
│   │       └── v2/
│   ├── benchmark/       # 性能基准
│   │   ├── msearch.benchmark.json
│   │   ├── msearch.benchmark.md
│   │   ├── embedding.benchmark.json
│   │   ├── embedding.benchmark.md
│   │   ├── search.benchmark.json
│   │   ├── search.benchmark.md
│   │   ├── test_msearch_benchmark.py
│   │   ├── test_embedding_benchmark.py
│   │   └── test_search_benchmark.py
│   ├── fixtures/        # 共享fixture
│   │   ├── __init__.py
│   │   └── path_factory.py
│   ├── unit/            # 单元测试
│   │   ├── core/        # 核心组件测试
│   │   │   ├── test_config_manager.py
│   │   │   ├── test_embedding_engine.py
│   │   │   ├── test_model_manager.py
│   │   │   └── test_hardware_detector.py
│   │   ├── data/        # 数据层测试
│   │   │   ├── test_metadata_extractor.py
│   │   │   ├── test_thumbnail_generator.py
│   │   │   └── test_content_analyzer.py
│   │   ├── services/    # 服务层测试
│   │   │   ├── test_search_engine.py
│   │   │   ├── test_media_processor.py
│   │   │   ├── test_query_processor.py
│   │   │   └── test_result_ranker.py
│   │   ├── ui/          # UI测试
│   │   │   └── test_main_window.py
│   │   └── utils/       # 工具层测试
│   │       ├── test_error_handling.py
│   │       ├── test_file_utils.py
│   │       └── test_format_utils.py
│   ├── integration/     # 集成测试
│   │   ├── it_search_flow.py
│   │   ├── it_indexing_flow.py
│   │   ├── it_multimodal_fusion.py
│   │   └── it_config_manager.py
│   └── e2e/            # 端到端测试
│       ├── e2e_full_workflow.py
│       ├── e2e_ui_interaction.py
│       └── e2e_database_architecture.py
├── data/                # 数据目录
│   ├── database/         # 数据库文件
│   │   ├── sqlite/       # SQLite数据库
│   │   └── lancedb/      # LanceDB向量数据库
│   ├── models/           # AI模型缓存
│   │   ├── mobileclip/   # MobileCLIP模型
│   │   ├── colsmol/      # colSmol-500M模型
│   │   ├── colqwen/      # colqwen2.5-v0.2模型
│   │   ├── clap/         # CLAP模型
│   │   ├── whisper/      # Whisper模型
│   │   └── inaspeech/    # InaSpeechSegmenter模型
│   ├── cache/            # 缓存目录
│   │   ├── embeddings/   # 向量缓存
│   │   └── processed/    # 处理结果缓存
│   ├── logs/             # 日志文件
│   │   ├── application.log
│   │   ├── error.log
│   │   └── performance.log
│   └── thumbnails/       # 缩略图缓存
├── configs/             # 配置文件目录
│   ├── default.yaml      # 默认配置
│   ├── development.yaml  # 开发环境配置
│   ├── production.yaml   # 生产环境配置
│   └── schema.json       # 配置 schema
├── scripts/             # 脚本目录
│   ├── install.sh        # 安装脚本
│   ├── setup_models.py   # 模型设置脚本
│   ├── migrate_data.py   # 数据迁移脚本
│   └── benchmark.py      # 性能测试脚本
├── docs/                # 文档目录
│   ├── api.md           # API文档
│   ├── deployment.md    # 部署文档
│   └── development.md   # 开发文档
├── requirements/        # 依赖文件目录
│   ├── base.txt         # 基础依赖
│   ├── dev.txt          # 开发依赖
│   ├── test.txt         # 测试依赖
│   └── optional.txt     # 可选依赖
├── requirements.txt      # 核心依赖（指向requirements/base.txt）
├── requirements-dev.txt  # 开发依赖（指向requirements/dev.txt）
├── pyproject.toml       # 项目配置
├── setup.py             # 安装配置
└── README.md           # 项目说明
```

### 1.5 关键技术决策

#### 1.5.1 为什么选择Python原生集成模型
- **轻量级**：无需额外的模型服务引擎，降低系统复杂度，避免桌面环境过度工程化
- **灵活性**：直接调用模型API，便于定制和优化
- **易于维护**：避免引入额外的第三方依赖，减少兼容性问题
- **可扩展性**：设计预留服务化接口，未来可无缝迁移到API服务模式

#### 1.5.2 为什么采用分级硬件自适应模型策略
- **统一架构**：避免维护多个不同的模型框架，简化系统复杂度
- **硬件自适应**：根据硬件配置自动选择最优模型，详见 [1.6.1 分级硬件自适应模型策略](#161-分级硬件自适应模型策略)
- **性能优化**：统一的向量化流程，便于批量处理和缓存优化
- **服务化预留**：统一的模型接口便于未来迁移到专用Docker服务

#### 1.5.3 为什么选择LanceDB
详见 [1.6.3 数据库技术选型](#163-数据库技术选型)

#### 1.5.4 为什么选择SQLite
详见 [1.6.3 数据库技术选型](#163-数据库技术选型)

#### 1.5.5 测试目录规范
- **统一测试目录**：所有测试代码统一放在 `tests/` 目录下，禁止在业务源码目录内嵌测试文件
- **测试文件命名规范**：
  - 单元测试：`test_*.py`
  - 集成测试：`it_*.py`
  - 端到端测试：`e2e_*.py`
  - 性能基准测试：`test_*_benchmark.py`
- **测试数据管理**：测试数据与 fixtures 放在 `tests/data/` 子目录，按"业务域/版本"再分二级目录
- **性能基准测试**：输出报告统一为 `{模块}.benchmark.json`，并同步生成 `*.benchmark.md` 摘要
- **临时文件管理**：临时文件统一输出到 `tests/.tmp/` 并在 `.gitignore` 中忽略，CI 流水线每次自动清空
- **pytest配置**：运行入口统一使用 `pytest`，配置文件 `pytest.ini` 置于 `tests/` 下；`conftest.py` 按业务域拆分，放在 `tests/conf.d/` 中
- **覆盖率报告**：统一输出到 `tests/.coverage/` 目录，HTML、XML、CSV 三种格式均需生成
- **测试用例规范**：所有测试用例必须遵循 Arrange-Act-Assert（AAA）模式；函数名使用 `test_功能点_预期行为` 的蛇形命名
- **路径管理**：禁止在测试代码中硬编码绝对路径；统一通过 `pytest` 的 `tmp_path`、`monkeypatch` 或自定义 `fixture` 获取临时路径
- **路径生成器**：路径生成器统一封装在 `tests/fixtures/path_factory.py`

### 1.6 核心技术详细说明

#### 1.6.1 分级硬件自适应模型策略

**概述**：根据硬件配置自动选择最优模型，实现性能与资源的最佳平衡。

**硬件分级**：
- **低配硬件**（纯CPU，<8GB内存）
  - 模型：apple/mobileclip
  - 特点：CPU友好，内存占用小
  - 适用场景：资源受限环境
  
- **中配硬件**（CPU或低端GPU，8-16GB内存）
  - 模型：vidore/colSmol-500M
  - 特点：GPU加速，平衡性能
  - 适用场景：一般桌面环境
  
- **高配硬件**（高端GPU，>16GB内存）
  - 模型：vidore/colqwen2.5-v0.2
  - 特点：高性能，支持复杂场景
  - 适用场景：高性能工作站

**模型选择逻辑**：
```python
def select_model(hardware_info: Dict[str, Any]) -> str:
    if hardware_info['gpu_available']:
        if hardware_info['gpu_memory'] >= 16:
            return "vidore/colqwen2.5-v0.2"
        elif hardware_info['gpu_memory'] >= 8:
            return "vidore/colSmol-500M"
    return "apple/mobileclip"
```

**配置示例**：
```yaml
# 低配硬件模型（CPU友好）
models:
  clip:
    model_name: "apple/mobileclip"
    device: "cpu"
    batch_size: 8

# 中配硬件模型（平衡性能）
models:
  clip:
    model_name: "vidore/colSmol-500M"
    device: "cuda"
    batch_size: 16

# 高配硬件模型（高性能）
models:
  clip:
    model_name: "vidore/colqwen2.5-v0.2"
    device: "cuda"
    batch_size: 32
```

#### 1.6.2 音频模型集成与分类策略

**概述**：使用 InaSpeechSegmenter 对音频内容进行分类，根据分类结果动态选择 CLAP 或 Whisper 模型。引入音频价值阈值判断，避免对无效短音频进行模型推理。

**音频价值阈值原则**：
- **核心原则**：音频信息只有在超过5秒以上时才具有检索价值
- **优化目标**：避免对无效短音频（≤5秒）执行昂贵的模型推理，节省计算资源
- **处理策略**：短音频直接标记为低价值，跳过InaSpeechSegmenter分类和后续处理

**音频模型说明**：
- **CLAP**（Contrastive Language-Audio Pre-training）
  - 用途：文本-音频检索
  - 适用场景：音乐检索、环境音识别
  - 何时使用：音频分类为MUSIC类型或UNKNOWN类型时
  
- **Whisper**（OpenAI语音识别）
  - 用途：语音转文本
  - 适用场景：语音搜索、语音转文字
  - 何时使用：音频分类为SPEECH类型时
  
- **InaSpeechSegmenter**
  - 用途：音频内容分类
  - 分类类型：语音（SPEECH）、音乐（MUSIC）、混合（MIXED）、静音（SILENCE）、未知（UNKNOWN）

**音频价值判断逻辑**：
```python
def is_audio_valuable(audio_path: str, threshold: float = 5.0) -> bool:
    """
    判断音频是否具有检索价值
    
    Args:
        audio_path: 音频文件路径
        threshold: 音频价值阈值（秒），默认5秒
    
    Returns:
        是否具有检索价值
    """
    # 1. 获取音频信息
    audio_info = get_audio_info(audio_path)
    duration = audio_info.get('duration', 0)
    
    # 2. 判断时长
    return duration > threshold

def process_audio_with_value_check(audio_path: str) -> Dict[str, Any]:
    """
    带价值检查的音频处理流程
    
    Args:
        audio_path: 音频文件路径
    
    Returns:
        处理结果
    """
    # 1. 音频价值检查
    if not is_audio_valuable(audio_path):
        return {
            'status': 'skipped',
            'reason': 'audio_too_short',
            'duration': get_audio_info(audio_path)['duration'],
            'message': '音频时长≤5秒，跳过处理'
        }
    
    # 2. 执行InaSpeechSegmenter分类
    segments = classify_audio_content(audio_path)
    
    # 3. 根据分类结果选择模型并执行向量化
    for segment in segments:
        models = select_audio_model(segment['content_type'])
        # 执行模型推理和向量化...
    
    return {
        'status': 'processed',
        'segments': segments
    }
```

**分类结果与模型选择映射**：

| 音频类型 | 使用模型 | 向量化方式 | 检索场景 |
|---------|---------|-----------|---------|
| MUSIC | CLAP | 音频向量嵌入 | 文本-音乐检索 |
| SPEECH | Whisper | 语音转文本 + 文本向量嵌入 | 语音内容检索 |
| MIXED | CLAP + Whisper | 混合向量化（权重各50%） | 综合音频检索 |
| SILENCE | 无 | 跳过处理 | - |
| UNKNOWN | CLAP | 音频向量嵌入 | 通用音频检索 |

**模型选择逻辑**：
```python
def select_audio_model(audio_type: str) -> List[str]:
    """
    根据音频分类结果选择模型
    
    明确何时选择CLAP或Whisper：
    - MUSIC → CLAP：用于音乐检索
    - SPEECH → Whisper：用于语音转文本检索
    - MIXED → CLAP + Whisper：混合处理
    - SILENCE → 无：跳过处理
    - UNKNOWN → CLAP：默认使用CLAP
    
    Args:
        audio_type: 音频分类类型
    
    Returns:
        使用的模型列表
    """
    if audio_type == AudioType.MUSIC:
        # 音乐类型：使用CLAP进行文本-音乐检索
        return ["clap"]
    elif audio_type == AudioType.SPEECH:
        # 语音类型：使用Whisper进行语音转文本检索
        return ["whisper"]
    elif audio_type == AudioType.MIXED:
        # 混合类型：同时使用CLAP和Whisper
        return ["clap", "whisper"]
    elif audio_type == AudioType.SILENCE:
        # 静音类型：跳过处理
        return []
    else:
        # 未知类型：默认使用CLAP
        return ["clap"]
```

**音频价值阈值配置**：
```python
AUDIO_VALUE_CONFIG = {
    # 音频价值阈值（秒）
    'value_threshold': 5.0,
    
    # 极短音频阈值（秒），直接跳过
    'very_short_threshold': 2.0,
    
    # 是否启用音频价值检查
    'enable_value_check': True,
    
    # 跳过短音频时是否记录日志
    'log_skipped_audio': True
}
```

**音频价值阈值配置**：
```python
AUDIO_VALUE_CONFIG = {
    # 音频价值阈值（秒）
    'value_threshold': 5.0,
    
    # 极短音频阈值（秒），直接跳过
    'very_short_threshold': 2.0,
    
    # 是否启用音频价值检查
    'enable_value_check': True,
    
    # 跳过短音频时是否记录日志
    'log_skipped_audio': True
}
```

**配置示例**：
```yaml
models:
  clap:
    model_name: "laion/clap-htsat-unfused"
    device: "cuda"
  
  whisper:
    model_name: "openai/whisper-base"
    device: "cuda"
  
  inaspeech:
    model_name: "anasynth82/InaSpeechSegmenter"
    device: "cpu"

media:
  audio:
    # 音频价值阈值
    value_threshold: 5.0       # 音频价值阈值（秒）
    enable_value_check: true   # 是否启用音频价值检查
    log_skipped_audio: true    # 是否记录跳过的音频
```

#### 1.6.3 数据库技术选型

**LanceDB（向量数据库）**：
- **选型理由**：
  - 高性能：专为向量检索优化
  - 易用性：Python原生支持，无需额外服务
  - 可扩展：支持大规模向量存储
  - 本地化：完全本地运行，无需网络
  
- **设计特点**：
  - 单一向量表设计：所有模态的向量存储在同一个LanceDB表中
  - modality字段：通过modality字段区分不同模态的向量
  - 索引优化：支持IVF、HNSW等索引算法

**SQLite（元数据存储）**：
- **选型理由**：
  - 轻量级：无需额外服务
  - 可靠性：成熟稳定，支持事务
  - 易用性：Python原生支持
  - 本地化：完全本地运行

- **设计特点**：
  - 文件型数据库：单文件存储，易于备份和迁移
  - 事务支持：保证数据一致性
  - 全文搜索：支持FTS5全文搜索

**协同工作**：
```python
# 数据库与向量存储的协同操作
def save_file_with_vector(file_info: Dict[str, Any], vector: List[float]):
    # 1. 保存元数据到SQLite
    file_id = database_manager.save_file(file_info)
    
    # 2. 保存向量到LanceDB
    vector_store.insert_vector({
        "id": file_id,
        "vector": vector,
        "modality": file_info["modality"]
    })
```

#### 1.6.4 视频处理优化策略

**概述**：基于FFMPEG场景检测的视频切片和帧提取优化，采用短视频快速处理和长视频两阶段切片策略，平衡处理效率和检索精度。

**短视频快速处理策略**：

针对短视频场景（≤6秒），采用快速处理流程，避免不必要的场景检测开销：

```python
def is_short_video(video_path: str, threshold: float = 6.0) -> bool:
    """
    判断是否为短视频
    
    Args:
        video_path: 视频文件路径
        threshold: 短视频时长阈值（秒），默认6秒
    
    Returns:
        是否为短视频
    """
    # 1. 获取视频信息
    video_info = get_video_info(video_path)
    duration = video_info.get('duration', 0)
    
    # 2. 判断时长
    return duration <= threshold

def process_short_video(video_path: str) -> List[Dict[str, Any]]:
    """
    短视频快速处理流程
    
    适用于≤6秒的视频，跳过场景检测，直接提取关键帧
    
    Args:
        video_path: 视频文件路径
    
    Returns:
        处理结果列表
    """
    # 1. 获取视频信息
    video_info = get_video_info(video_path)
    duration = video_info['duration']
    
    # 2. 根据时长决定提取策略
    if duration <= 2.0:
        # 极短视频（≤2秒）：提取1帧（中间帧）
        timestamp = duration / 2
        frames = extract_frames_by_time(video_path, [timestamp])
        
    elif duration <= 4.0:
        # 短视频（2-4秒）：提取2帧（均匀分布）
        timestamps = [duration * 0.33, duration * 0.67]
        frames = extract_frames_by_time(video_path, timestamps)
        
    else:
        # 中短视频（4-6秒）：提取3帧（均匀分布）
        timestamps = [duration * 0.25, duration * 0.5, duration * 0.75]
        frames = extract_frames_by_time(video_path, timestamps)
    
    # 3. 创建单个场景（整个视频作为一个场景）
    scene = {
        'scene_id': generate_uuid(),
        'start_time': 0.0,
        'end_time': duration,
        'duration': duration,
        'frame_count': len(frames),
        'is_key_transition': False,
        'confidence': 1.0,  # 短视频置信度为1.0
        'is_short_video': True  # 标记为短视频
    }
    
    # 4. 返回结果
    return [{
        'scene': scene,
        'frames': frames,
        'processing_mode': 'fast'  # 标记为快速处理模式
    }]
```

**短视频处理优势**：
- **性能提升**：跳过FFMPEG场景检测，处理速度提升3-5倍
- **资源节省**：减少CPU和内存消耗，降低系统负载
- **简化逻辑**：短视频通常为单一场景，无需复杂分割
- **用户体验**：短视频处理更快，索引延迟更低

**短视频配置参数**：
```python
SHORT_VIDEO_PARAMS = {
    # 短视频时长阈值（秒）
    'short_video_threshold': 6.0,
    
    # 极短视频阈值（秒）
    'very_short_threshold': 2.0,
    
    # 短视频分段阈值（秒）
    'short_segment_threshold': 4.0,
    
    # 极短视频提取帧数
    'very_short_frames': 1,
    
    # 短视频提取帧数
    'short_frames': 2,
    
    # 中短视频提取帧数
    'medium_short_frames': 3,
    
    # 是否启用短视频快速处理
    'enable_fast_processing': True
}
```

**两阶段切片策略**（适用于长视频 > 6秒）：
1. **第一阶段（粗粒度切片）**：使用FFMPEG场景检测进行初步场景分割，最大切片时长≤5秒
2. **第二阶段（细粒度提取）**：根据场景内容特征，智能选择关键帧提取策略

**FFMPEG场景检测参数**：
```python
SCENE_DETECT_PARAMS = {
    # 场景检测算法选择
    'detect_mode': 'scene',  # scene: 场景检测, content: 内容检测
    
    # 场景变化阈值（0-1，越小越敏感）
    'scene_threshold': 0.3,   # 推荐值：0.3-0.5
    
    # 最大切片时长（秒）
    'max_segment_duration': 5,
    
    # 最小切片时长（秒）
    'min_segment_duration': 0.5,
    
    # 场景检测置信度
    'confidence': 0.7,
    
    # 视频预处理参数
    'video_filter': 'scale=640:360',  # 降采样以提高检测速度
    
    # 关键帧提取策略
    'keyframe_strategy': 'smart',  # smart: 智能选择, uniform: 均匀分布, first: 首帧
    
    # 时间戳精度
    'timestamp_precision': 0.1,  # ±0.1秒精度
}
```

**关键帧提取算法伪代码**：
```python
def extract_keyframes(video_path: str, scenes: List[Scene]) -> List[Frame]:
    """
    关键帧提取算法
    
    Args:
        video_path: 视频文件路径
        scenes: 场景列表，每个场景包含时间范围和特征
    
    Returns:
        关键帧列表
    """
    keyframes = []
    
    for scene in scenes:
        # 根据场景特征选择提取策略
        if scene.is_static:
            # 静态场景：提取中间帧
            timestamp = scene.start + (scene.duration / 2)
            frame = extract_frame_at_timestamp(video_path, timestamp)
            keyframes.append(frame)
            
        elif scene.is_dynamic:
            # 动态场景：提取多帧（最多3帧）
            num_frames = min(3, int(scene.duration / 2))
            for i in range(num_frames):
                progress = (i + 1) / (num_frames + 1)
                timestamp = scene.start + (scene.duration * progress)
                frame = extract_frame_at_timestamp(video_path, timestamp)
                keyframes.append(frame)
                
        else:
            # 混合场景：智能选择
            # 1. 计算场景运动强度
            motion_score = calculate_motion_score(scene)
            
            # 2. 根据运动强度决定帧数
            if motion_score < 0.3:
                # 低运动：提取1帧
                timestamp = scene.start + (scene.duration / 2)
                frame = extract_frame_at_timestamp(video_path, timestamp)
                keyframes.append(frame)
            elif motion_score < 0.7:
                # 中等运动：提取2帧
                for i in range(2):
                    progress = (i + 1) / 3
                    timestamp = scene.start + (scene.duration * progress)
                    frame = extract_frame_at_timestamp(video_path, timestamp)
                    keyframes.append(frame)
            else:
                # 高运动：提取3帧
                for i in range(3):
                    progress = (i + 1) / 4
                    timestamp = scene.start + (scene.duration * progress)
                    frame = extract_frame_at_timestamp(video_path, timestamp)
                    keyframes.append(frame)
    
    return keyframes

def calculate_motion_score(scene: Scene) -> float:
    """
    计算场景运动强度
    
    Args:
        scene: 场景对象
    
    Returns:
        运动强度分数（0-1）
    """
    # 1. 提取场景中的多个帧
    frames = extract_sample_frames(scene, num_samples=5)
    
    # 2. 计算帧间差异
    motion_scores = []
    for i in range(len(frames) - 1):
        diff = calculate_frame_difference(frames[i], frames[i+1])
        motion_scores.append(diff)
    
    # 3. 返回平均运动强度
    return sum(motion_scores) / len(motion_scores)

def extract_frame_at_timestamp(video_path: str, timestamp: float) -> Frame:
    """
    在指定时间戳提取帧，保证时间戳精度
    
    Args:
        video_path: 视频文件路径
        timestamp: 时间戳（秒）
    
    Returns:
        提取的帧对象
    """
    # 1. 使用FFMPEG精确提取
    cmd = [
        'ffmpeg',
        '-ss', str(timestamp),
        '-i', video_path,
        '-vframes', '1',
        '-q:v', '2',  # 高质量
        '-f', 'image2pipe',
        '-'
    ]
    
    # 2. 执行提取
    frame_data = execute_ffmpeg(cmd)
    
    # 3. 验证时间戳精度
    actual_timestamp = verify_timestamp(video_path, frame_data)
    if abs(actual_timestamp - timestamp) > 0.1:
        # 精度不足，重试
        return extract_frame_at_timestamp(video_path, timestamp)
    
    return Frame(data=frame_data, timestamp=actual_timestamp)
```

**超大视频处理流程**（>3GB或>30分钟）：

```python
def process_large_video(video_path: str) -> List[Dict[str, Any]]:
    """
    超大视频处理流程
    
    Args:
        video_path: 视频文件路径
    
    Returns:
        处理结果列表
    """
    # 1. 获取视频信息
    video_info = get_video_info(video_path)
    
    # 2. 阶段1：初始处理（开头5分钟）
    initial_results = process_video_segment(
        video_path,
        start_time=0,
        end_time=300,  # 5分钟
        priority='high'
    )
    
    # 3. 阶段2：关键转场检测
    transition_points = detect_key_transitions(video_path)
    transition_results = []
    for transition in transition_points:
        result = process_video_segment(
            video_path,
            start_time=transition['start'] - 5,
            end_time=transition['end'] + 5,
            priority='medium'
        )
        transition_results.append(result)
    
    # 4. 阶段3：后台渐进处理
    background_task = create_background_task(
        target=process_remaining_video,
        args=(video_path, 300),  # 从5分钟后开始
        priority='low',
        max_retries=3
    )
    
    # 5. 合并结果
    all_results = initial_results + transition_results
    
    # 6. 返回初始结果，后台任务继续执行
    return all_results

def detect_key_transitions(video_path: str) -> List[Dict[str, Any]]:
    """
    检测关键转场点
    
    Args:
        video_path: 视频文件路径
    
    Returns:
        关键转场点列表
    """
    # 1. 使用FFMPEG检测场景变化
    scenes = detect_scenes(video_path, max_duration=30)
    
    # 2. 计算场景变化强度
    transition_scores = []
    for i in range(len(scenes) - 1):
        score = calculate_transition_score(scenes[i], scenes[i+1])
        transition_scores.append({
            'start': scenes[i]['end'],
            'end': scenes[i+1]['start'],
            'score': score
        })
    
    # 3. 选择高评分的转场点（前20%）
    threshold = np.percentile([t['score'] for t in transition_scores], 80)
    key_transitions = [t for t in transition_scores if t['score'] >= threshold]
    
    return key_transitions

def process_remaining_video(video_path: str, start_time: float) -> List[Dict[str, Any]]:
    """
    后台渐进处理剩余视频
    
    Args:
        video_path: 视频文件路径
        start_time: 开始时间（秒）
    
    Returns:
        处理结果列表
    """
    video_info = get_video_info(video_path)
    total_duration = video_info['duration']
    
    # 1. 分批处理（每10分钟一批）
    batch_size = 600  # 10分钟
    results = []
    
    for batch_start in range(int(start_time), int(total_duration), batch_size):
        batch_end = min(batch_start + batch_size, total_duration)
        
        # 2. 处理当前批次
        batch_results = process_video_segment(
            video_path,
            start_time=batch_start,
            end_time=batch_end,
            priority='low'
        )
        results.extend(batch_results)
        
        # 3. 更新进度
        progress = (batch_end - start_time) / (total_duration - start_time)
        update_task_progress(progress)
    
    return results
```

**时间戳精度保证机制**：

```python
class TimestampPrecisionGuarantee:
    """
    时间戳精度保证机制
    
    确保提取的帧时间戳与请求时间戳的误差在±0.1秒以内
    """
    
    def __init__(self, video_path: str):
        self.video_path = video_path
        self.ffmpeg_instance = None
        self.timestamp_map = {}  # 缓存时间戳映射
    
    def extract_frame_with_precision(
        self,
        timestamp: float,
        max_retries: int = 3,
        tolerance: float = 0.1
    ) -> Frame:
        """
        精确提取帧
        
        Args:
            timestamp: 目标时间戳（秒）
            max_retries: 最大重试次数
            tolerance: 容忍误差（秒）
        
        Returns:
            提取的帧对象
        """
        for attempt in range(max_retries):
            # 1. 提取帧
            frame = self._extract_frame(timestamp)
            
            # 2. 验证时间戳
            actual_timestamp = self._verify_timestamp(frame)
            
            # 3. 检查精度
            if abs(actual_timestamp - timestamp) <= tolerance:
                # 精度满足要求
                return frame
            
            # 4. 精度不足，调整时间戳重试
            adjustment = timestamp - actual_timestamp
            timestamp += adjustment
        
        # 重试次数用尽，返回最后一次结果
        return frame
    
    def _extract_frame(self, timestamp: float) -> Frame:
        """
        使用FFMPEG提取帧
        
        Args:
            timestamp: 时间戳（秒）
        
        Returns:
            提取的帧对象
        """
        # 检查缓存
        if timestamp in self.timestamp_map:
            return self.timestamp_map[timestamp]
        
        # 使用-ss参数精确定位
        cmd = [
            'ffmpeg',
            '-ss', str(timestamp),
            '-i', self.video_path,
            '-vframes', '1',
            '-q:v', '2',
            '-f', 'image2pipe',
            '-'
        ]
        
        # 执行命令
        frame_data = execute_ffmpeg(cmd)
        
        # 创建帧对象
        frame = Frame(
            data=frame_data,
            timestamp=timestamp,
            video_path=self.video_path
        )
        
        # 缓存结果
        self.timestamp_map[timestamp] = frame
        
        return frame
    
    def _verify_timestamp(self, frame: Frame) -> float:
        """
        验证帧的实际时间戳
        
        Args:
            frame: 帧对象
        
        Returns:
            实际时间戳
        """
        # 1. 使用ffprobe获取帧的PTS（Presentation Timestamp）
        cmd = [
            'ffprobe',
            '-select_streams', 'v:0',
            '-show_frames',
            '-show_entries', 'frame=pkt_pts_time,best_effort_timestamp_time',
            '-of', 'csv=p=0',
            self.video_path
        ]
        
        # 2. 执行命令并解析输出
        output = execute_ffprobe(cmd)
        timestamps = [float(t) for t in output.split('\n') if t]
        
        # 3. 找到最接近的时间戳
        closest_timestamp = min(timestamps, key=lambda t: abs(t - frame.timestamp))
        
        return closest_timestamp
```

**固定场景处理**：

```python
def process_fixed_scenes(video_path: str, fixed_scenes: List[Dict[str, Any]]) -> List[Frame]:
    """
    固定场景处理
    
    不对源视频切片，直接对每个固定场景强制提取1帧
    
    Args:
        video_path: 视频文件路径
        fixed_scenes: 固定场景列表，每个场景包含时间范围
    
    Returns:
        提取的帧列表
    """
    frames = []
    
    for scene in fixed_scenes:
        # 1. 计算场景中心时间戳
        center_timestamp = (scene['start'] + scene['end']) / 2
        
        # 2. 使用精度保证机制提取帧
        precision_guarantee = TimestampPrecisionGuarantee(video_path)
        frame = precision_guarantee.extract_frame_with_precision(
            timestamp=center_timestamp,
            tolerance=0.1  # ±0.1秒精度
        )
        
        # 3. 添加场景元数据
        frame.metadata = {
            'scene_id': scene['id'],
            'scene_name': scene['name'],
            'scene_start': scene['start'],
            'scene_end': scene['end'],
            'scene_duration': scene['end'] - scene['start']
        }
        
        frames.append(frame)
    
    return frames
```

**配置示例**：
```yaml
media_processing:
  video:
    # 场景检测配置
    use_scene_detect: true
    scene_detect:
      detect_mode: scene
      scene_threshold: 0.3
      max_segment_duration: 5
      min_segment_duration: 0.5
      confidence: 0.7
      video_filter: scale=640:360
    
    # 关键帧提取配置
    keyframe_strategy: smart  # smart, uniform, first
    max_frames_per_scene: 3
    motion_threshold_low: 0.3
    motion_threshold_high: 0.7
    
    # 超大视频配置
    large_video_threshold:
      size_gb: 3
      duration_minutes: 30
    initial_processing_duration: 300  # 5分钟
    batch_processing_size: 600  # 10分钟
    
    # 时间戳精度配置
    timestamp_precision: 0.1
    max_timestamp_retries: 3
    
    # 固定场景配置
    fixed_scenes:
      - id: "intro"
        name: "片头"
        start: 0
        end: 30
      - id: "outro"
        name: "片尾"
        start: -30
        end: -1
```

**性能优化建议**：
1. **并行处理**：对多个场景使用多线程并行提取帧
2. **缓存机制**：缓存已提取的帧，避免重复处理
3. **渐进式加载**：对超大视频采用渐进式加载，优先处理关键部分
4. **GPU加速**：使用GPU加速视频解码和帧提取
5. **内存管理**：及时释放已处理帧的内存，避免内存溢出

---

## 第二部分：各模块详细说明（开发指导）

### 2.1 核心组件层

#### 2.1.1 config/config.py - 配置管理器（合并优化）

**模块职责**：
- 加载和管理系统配置
- 提供统一的配置查询接口
- 支持配置热更新
- 验证配置完整性和正确性
- 提供配置默认值和类型转换

**接口设计**：
```python
class ConfigManager:
    def __init__(config_dir: str, schema_path: str = None)
    def initialize(self) -> bool
    def get(self, key_path: str, default: Any = None) -> Any
    def set(self, key_path: str, value: Any) -> None
    def get_all(self) -> Dict[str, Any]
    def reload(self) -> bool
    def validate(self) -> Tuple[bool, List[str]]
    
    # 配置验证
    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, List[str]]
    def get_schema(self) -> Dict[str, Any]
    def apply_schema(self, config: Dict[str, Any]) -> Dict[str, Any]
    
    # 配置转换
    def convert_types(self, config: Dict[str, Any]) -> Dict[str, Any]
    def get_default_config(self) -> Dict[str, Any]
    
    # 配置导出
    def export_config(self, output_path: str) -> bool
    def import_config(self, input_path: str) -> bool
```

**依赖注入**：
- 构造函数接收配置目录和可选的schema路径
- 不依赖其他业务模块

**配置参数**：
```yaml
system:
  debug: false
  data_dir: "data/"
  log_level: "INFO"
  check_interval: 5

database:
  sqlite:
    path: "data/database/sqlite/msearch.db"
  lancedb:
    data_dir: "data/database/lancedb"

models:
  cache_dir: "data/models"
  image_video:
    model_name: "apple/mobileclip"  # 硬件自适应选择
    device: "auto"
    batch_size: 16
  clap:
    model_name: "laion/clap-htsat-unfused"
    device: "auto"
    batch_size: 8
  whisper:
    model_name: "openai/whisper-base"
    device: "auto"
```

**设计说明**：
- **合并优化**：将config_manager.py和config_validator.py合并为config.py
- **简化依赖**：不依赖其他业务模块，保持独立性
- **功能完整**：包含验证、加载、查询、导出等所有配置功能

**开发测试指南**：
1. 创建临时配置目录和文件进行测试
2. 测试配置加载和嵌套查询功能
3. 测试配置热更新和验证功能
4. 测试默认值和类型转换
5. 测试配置schema验证
6. 测试配置导入导出功能

#### 2.1.2 database/database_manager.py - 数据库管理器

**模块职责**：
- 管理SQLite数据库连接
- 提供元数据CRUD操作
- 支持事务管理
- 维护数据库完整性

**接口设计**：
```python
class DatabaseManager:
    def __init__(db_path: str, enable_wal: bool = True)
    def initialize(self) -> bool
    def create_tables(self) -> None
    def begin_transaction(self) -> None
    def commit(self) -> None
    def rollback(self) -> None
    def insert_file_metadata(self, metadata: Dict[str, Any]) -> str
    def get_file_metadata(self, file_id: str) -> Optional[Dict[str, Any]]
    def update_file_metadata(self, file_id: str, updates: Dict[str, Any]) -> bool
    def delete_file_metadata(self, file_id: str) -> bool
    def search_file_metadata(self, query: str, limit: int = 100) -> List[Dict[str, Any]]
    def get_file_by_hash(self, file_hash: str) -> Optional[Dict[str, Any]]
    def get_files_by_status(self, status: str, limit: int = 100) -> List[Dict[str, Any]]
    def update_file_status(self, file_id: str, status: str) -> bool
    def get_database_stats(self) -> Dict[str, Any]
    def close(self) -> None
    
    # 基于文件哈希的去重和引用计数
    def get_or_create_file_by_hash(self, file_hash: str, file_path: str, metadata: Dict[str, Any]) -> str
    def add_file_reference(self, file_hash: str, file_path: str) -> bool
    def remove_file_reference(self, file_hash: str, file_path: str) -> bool
    def get_file_references(self, file_hash: str) -> List[str]
    def get_reference_count(self, file_hash: str) -> int
    def cleanup_orphaned_files(self) -> int
```

**依赖注入**：
- 构造函数接收数据库路径和WAL模式开关
- 不依赖其他业务模块

**数据模型**：
```python
class FileMetadata:
    id: str                    # 文件唯一ID（UUID v4）
    file_path: str              # 文件路径
    file_name: str              # 文件名
    file_type: str              # 文件类型（image/video/audio）
    file_size: int              # 文件大小（字节）
    file_hash: str             # 文件SHA256哈希
    created_at: float           # 创建时间（Unix时间戳）
    updated_at: float           # 更新时间（Unix时间戳）
    processed_at: Optional[float] # 处理完成时间
    processing_status: str      # 处理状态（pending/processing/completed/failed）
    metadata: Dict[str, Any]   # 扩展元数据（JSON格式）
    reference_count: int = 1   # 引用计数（新增，用于去重）

class FileReference:
    id: str                    # 引用记录ID（UUID v4）
    file_hash: str             # 文件SHA256哈希
    file_path: str              # 文件路径
    file_id: str               # 关联的文件ID
    created_at: float           # 创建时间（Unix时间戳）
```

**基于文件哈希的去重逻辑**：
```python
def get_or_create_file_by_hash(self, file_hash: str, file_path: str, metadata: Dict[str, Any]) -> str:
    """
    根据文件哈希获取或创建文件记录
    
    如果文件哈希已存在，增加引用计数并添加新的路径引用
    如果文件哈希不存在，创建新的文件记录
    
    Args:
        file_hash: 文件SHA256哈希
        file_path: 文件路径
        metadata: 文件元数据
    
    Returns:
        文件ID
    """
    # 1. 检查文件哈希是否已存在
    existing_file = self.get_file_by_hash(file_hash)
    
    if existing_file:
        # 2. 文件已存在，增加引用计数
        file_id = existing_file['id']
        self.add_file_reference(file_hash, file_path)
        self.increment_reference_count(file_id)
        return file_id
    else:
        # 3. 文件不存在，创建新记录
        metadata['file_hash'] = file_hash
        metadata['reference_count'] = 1
        file_id = self.insert_file_metadata(metadata)
        self.add_file_reference(file_hash, file_path)
        return file_id

def add_file_reference(self, file_hash: str, file_path: str) -> bool:
    """
    添加文件路径引用
    
    Args:
        file_hash: 文件SHA256哈希
        file_path: 文件路径
    
    Returns:
        是否成功添加
    """
    # 检查路径是否已存在
    existing_refs = self.get_file_references(file_hash)
    if file_path in existing_refs:
        return False
    
    # 添加新的引用记录
    file_id = self.get_file_by_hash(file_hash)['id']
    ref_data = {
        'file_hash': file_hash,
        'file_path': file_path,
        'file_id': file_id
    }
    self.insert_file_reference(ref_data)
    return True

def cleanup_orphaned_files(self) -> int:
    """
    清理无引用的文件
    
    当引用计数为0时，删除文件记录和向量数据
    
    Returns:
        清理的文件数量
    """
    # 1. 查找引用计数为0的文件
    orphaned_files = self.get_files_with_zero_reference()
    
    # 2. 删除这些文件的记录和向量
    count = 0
    for file_id in orphaned_files:
        # 删除向量数据
        vector_store.delete_vectors_by_file_id(file_id)
        # 删除文件记录
        self.delete_file_metadata(file_id)
        count += 1
    
    return count
```

**去重优势**：
- **存储优化**：相同内容的文件只存储一份向量和元数据
- **性能提升**：避免重复处理相同内容的文件
- **空间节省**：减少向量数据库和元数据库的存储空间
- **一致性保证**：确保相同内容的文件检索结果一致

**开发测试指南**：
1. 创建临时数据库进行测试
2. 测试CRUD操作的正确性
3. 测试事务管理和回滚功能
4. 测试并发访问安全性
5. 测试数据库初始化和关闭
6. 测试不同状态的文件查询

#### 2.1.3 vector/vector_store.py - 向量存储

**模块职责**：
- 管理LanceDB向量数据库（单一向量表设计）
- 提供向量插入、检索、更新和删除接口
- 支持批量操作和事务
- 维护向量索引性能
- 通过modality字段区分不同模态的向量，而非使用多个独立集合

**接口设计**：
```python
class VectorStore:
    def __init__(data_dir: str)
    def initialize(self) -> bool
    def insert_vectors(self, vectors: List[Dict[str, Any]]) -> None
    def search_vectors(self, query_vector: List[float], limit: int = 20, filter: Optional[Dict] = None) -> List[Dict[str, Any]]
    def delete_vectors(self, vector_ids: List[str]) -> None
    def update_vector(self, vector_id: str, updates: Dict[str, Any]) -> bool
    def get_vector(self, vector_id: str) -> Optional[Dict[str, Any]]
    def get_collection_stats(self) -> Dict[str, Any]
    def close(self) -> None
```

**依赖注入**：
- 构造函数接收数据目录
- 不依赖其他业务模块

**向量数据模型**：
```python
class VectorData:
    id: str                    # 向量唯一ID（UUID v4或文件ID+模态）
    vector: List[float]        # 向量数据
    modality: str              # 模态类型（image/video/audio/text/face）
    file_id: str               # 关联文件ID
    segment_id: Optional[str]   # 视频片段ID（仅视频）
    start_time: Optional[float]  # 视频片段开始时间（仅视频，精度±5秒）
    end_time: Optional[float]    # 视频片段结束时间（仅视频，精度±5秒）
    is_full_video: Optional[bool]  # 是否为完整视频（短视频优化，仅视频）
    metadata: Dict[str, Any]   # 扩展元数据
    created_at: float           # 创建时间戳
```

**时序定位优化策略**：
- **短视频简化**：对于≤6秒的短视频，无需存储精确时间戳
  - segment_id = "full"（标记为完整视频）
  - start_time = 0
  - end_time = duration
  - is_full_video = True
- **长视频精确**：对于>6秒的长视频，存储精确时间戳
  - segment_id = 唯一片段ID
  - start_time/end_time = 实际切片时间
  - is_full_video = False
- **性能优化**：减少短视频的元数据写入开销，降低向量表存储压力

**设计说明**：
- **单一向量表**：所有模态的向量存储在同一个LanceDB表中，通过modality字段区分
- **简化管理**：避免维护多个独立集合，降低系统复杂度
- **统一查询**：支持跨模态查询，通过filter参数指定modality
- **时序定位**：视频片段的时间戳精度为±5秒，满足需求10的要求
- **短视频优化**：短视频简化时序定位，减少元数据开销

**开发测试指南**：
1. 创建临时向量数据库进行测试
2. 测试向量插入和检索性能
3. 测试批量操作和事务
4. 测试不同向量维度的兼容性
5. 测试向量更新和删除功能
6. 测试通过modality字段过滤查询

#### 2.1.4 embedding/embedding_engine.py - 向量化引擎

**模块职责**：
- 执行AI模型加载和推理
- 提供统一的多模态向量化接口
- 实现模型推理的错误处理和重试机制
- 管理模型生命周期（加载、卸载、推理）

**核心原则**：
- **纯执行层**：不负责模型选择和配置，只负责加载和推理
- **配置驱动**：通过配置参数接收模型路径和设备配置
- **无状态**：不维护模型切换状态，由外部配置控制

**接口设计**：
```python
class EmbeddingEngine:
    def __init__(config: Dict[str, Any])
    def initialize(self) -> bool
    def shutdown(self) -> None
    
    # 统一的图像/视频向量化接口
    def embed_image(self, image_path: str) -> List[float]
    def embed_video_frame(self, frame_data: np.ndarray) -> List[float]
    def embed_video_segment(self, video_path: str, start_time: float, end_time: float) -> List[float]
    
    # 其他模态向量化接口
    def embed_text(self, text: str) -> List[float]
    def embed_audio(self, audio_path: str, audio_type: str = 'auto') -> List[float]
    
    # 批量处理接口
    def embed_batch_images(self, image_paths: List[str]) -> List[List[float]]
    def embed_batch_video_segments(self, segments: List[Dict[str, Any]]) -> List[List[float]]
    
    # 模型预热（仅推理预热，不涉及模型选择）
    def warmup_models(self) -> None
    
    # 获取模型状态（只读，不涉及切换）
    def get_model_status(self) -> Dict[str, Any]
    
    # 懒加载机制
    def load_model_if_needed(self, modality: str) -> bool
    def unload_model(self, modality: str) -> bool
    def preload_models(self, modalities: List[str]) -> None
```

**懒加载机制**：
- **按需加载**：首次需要某模态时才加载对应模型，避免启动时加载全部模型
- **内存优化**：若用户主要使用视觉检索，音频模型不会常驻内存
- **预加载支持**：提供 `preload_models()` 方法支持主动预加载常用模态
- **模型卸载**：提供 `unload_model()` 方法支持手动卸载不常用模型释放内存

**懒加载实现**：
```python
def load_model_if_needed(self, modality: str) -> bool:
    """
    按需加载模型
    
    Args:
        modality: 模态类型（image/video/audio/text）
    
    Returns:
        是否成功加载
    """
    if modality in self.loaded_models:
        return True
    
    model_config = self.config.get(f"{modality}_model")
    if not model_config:
        raise ValueError(f"No model config found for modality: {modality}")
    
    model = self._load_model(model_config)
    self.loaded_models[modality] = model
    return True
```

**依赖注入**：
- 构造函数接收配置字典
- 配置包含模型路径、设备类型、精度等参数
- 不依赖其他业务模块

**模型配置**：
```python
class ModelConfig:
    # 统一的图像/视频向量化模型配置
    image_video_model:
        # 模型配置（由hardware_detector.py推荐）
        model_name: str = "apple/mobileclip"  # 模型名称/路径
        device: str = "cpu"        # 设备类型（cuda/cpu）
        batch_size: int = 16        # 批量大小
        precision: str = "float32"  # 模型精度（float32/float16/int8）
        max_resolution: int = 224   # 最大输入分辨率
    
    # 音频模型配置
    clap:
        model_name: str = "laion/clap-htsat-unfused"
        device: str = "cpu"
        batch_size: int = 8
        precision: str = "float32"
    
    # 语音转文本模型配置
    whisper:
        model_name: str = "openai/whisper-base"
        device: str = "cpu"
        precision: str = "float32"
```

**职责边界**：
- **不负责**：模型选择、硬件检测、性能优化、配置生成
- **负责**：模型加载、向量推理、错误处理、资源管理

**开发测试指南**：
1. 使用本地模型路径进行测试
2. 测试统一的图像/视频向量化功能
3. 测试批量处理性能和并发能力
4. 测试错误处理和重试机制
5. 测试不同设备配置下的性能
6. 测试模型加载和卸载机制

#### 2.1.5 hardware/hardware_detector.py - 硬件检测器

**模块职责**：
- 检测系统硬件配置（CPU、GPU、内存、磁盘）
- 根据硬件配置推荐最优模型和参数
- 提供硬件信息查询和监控
- 首次安装/启动时自动执行并生成配置文件
- 为安装器提供模型推荐和配置建议

**核心原则**：
- **安装时推荐**：在首次安装时根据硬件配置推荐模型供安装器使用
- **配置生成**：生成最优配置文件，供EmbeddingEngine等组件使用
- **只读检测**：不参与运行时的模型切换和推理决策
- **离线友好**：支持离线环境下的硬件检测和配置生成

**接口设计**：
```python
class HardwareDetector:
    def __init__(config: Dict[str, Any])
    def detect_hardware(self) -> Dict[str, Any]
    def get_hardware_info(self) -> Dict[str, Any]
    def get_recommended_models(self) -> Dict[str, Dict[str, Any]]
    def get_optimal_batch_size(self, model_type: str) -> int
    def get_optimal_precision(self, model_type: str) -> str
    def get_optimal_device(self, model_type: str = None) -> str
    def get_gpu_info(self) -> List[Dict[str, Any]]
    def get_cpu_info(self) -> Dict[str, Any]
    def get_memory_info(self) -> Dict[str, Any]
    def get_disk_info(self, path: str) -> Dict[str, Any]
    def is_gpu_available(self) -> bool
    def is_cuda_available(self) -> bool
    def is_mps_available(self) -> bool
    def is_openvino_available(self) -> bool
    
    # 配置文件生成（安装时使用）
    def generate_config_file(self, config_path: str) -> bool
    def update_config_file(self, config_path: str) -> bool
    def load_config_file(self, config_path: str) -> Dict[str, Any]
    
    # 首次启动检测
    def is_first_run(self) -> bool
    def run_initial_setup(self, config_path: str) -> bool
```

**依赖注入**：
- 构造函数接收配置字典
- 不依赖其他业务模块

**硬件信息模型**：
```python
class HardwareInfo:
    cpu_count: int            # CPU核心数
    cpu_name: str             # CPU名称
    cpu_memory_gb: float      # CPU内存（GB）
    gpu_available: bool        # 是否有GPU
    gpus: List[Dict[str, Any]] # GPU列表
        - name: str           # GPU名称
        - memory_gb: float    # GPU内存（GB）
        - device_type: str    # 设备类型（cuda/mps/opencl）
        - compute_capability: float # 计算能力
    disk_space_gb: float      # 可用磁盘空间（GB）
    total_disk_gb: float      # 总磁盘空间（GB）
    hardware_level: str       # 硬件级别（low/mid/high/ultra）
    recommended_models: Dict[str, Dict[str, Any]] # 推荐模型配置
        - image_video_model:  # 图片和视频向量化模型
            model_type: str     # 模型类型（mobileclip/colsmol_500m/colqwen2_5_v0_2）
            model_name: str     # 推荐模型名称
            batch_size: int     # 推荐批量大小
            precision: str      # 推荐精度
            device: str         # 推荐设备
            memory_requirement: str  # 内存需求
        - audio_model:         # 音频向量化模型
            model_type: str     # 模型类型（clap）
            model_name: str     # 推荐模型名称
            batch_size: int     # 推荐批量大小
            precision: str      # 推荐精度
            device: str         # 推荐设备
        - speech_model:        # 语音转文本模型
            model_type: str     # 模型类型（whisper）
            model_name: str     # 推荐模型名称
            precision: str      # 推荐精度
            device: str         # 推荐设备
```

**首次启动流程**：
```python
# 应用启动时自动执行
def on_app_startup():
    hardware_detector = HardwareDetector(config)
    
    # 检查是否首次运行
    if hardware_detector.is_first_run():
        # 自动检测硬件
        hardware_info = hardware_detector.detect_hardware()
        
        # 生成配置文件
        config_path = get_config_path()
        hardware_detector.run_initial_setup(config_path)
        
        # 保存硬件信息
        save_hardware_info(hardware_info)
    else:
        # 加载已有配置
        config = hardware_detector.load_config_file(config_path)
```

**硬件级别与模型映射**：
详见 [1.6.1 分级硬件自适应模型策略](#161-分级硬件自适应模型策略)

**职责边界**：
- **负责**：硬件检测、模型推荐、配置生成、安装时建议
- **不负责**：模型加载、向量推理、运行时模型切换、性能监控

**开发测试指南**：
1. 测试不同硬件环境的检测准确性
2. 测试模型推荐逻辑的合理性
3. 测试参数优化建议的有效性
4. 测试异常硬件环境处理
5. 测试GPU类型检测（CUDA/MPS/OpenVINO）
6. 测试内存和磁盘信息检测
7. 测试首次启动自动配置生成
8. 测试配置文件加载和更新

#### 2.1.6 task/task_scheduler.py - 任务调度器

**模块职责**：
- 实现智能任务调度算法
- 管理任务优先级和依赖关系
- 优化资源利用率
- 支持任务负载均衡

**接口设计**：
```python
class TaskScheduler:
    def __init__(self, config: Dict[str, Any])
    def initialize(self) -> bool
    
    # 调度算法
    def schedule_tasks(self, pending_tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]
    def calculate_task_priority(self, task: Dict[str, Any]) -> float
    def estimate_task_duration(self, task: Dict[str, Any]) -> float
    
    # 资源管理
    def check_resource_availability(self, task: Dict[str, Any]) -> bool
    def allocate_resources(self, task: Dict[str, Any]) -> Dict[str, Any]
    def release_resources(self, task: Dict[str, Any]) -> None
    
    # 负载均衡
    def balance_workload(self, tasks: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]
    def get_optimal_batch_size(self, task_type: str) -> int
    
    # 调度策略
    def set_scheduling_strategy(self, strategy: str) -> None  # FIFO, Priority, SJF, Round-Robin
    def get_scheduling_metrics(self) -> Dict[str, float]
```

**调度策略**：
- **FIFO**：先进先出，适合简单场景
- **Priority**：基于优先级调度，适合有紧急任务的场景
- **SJF**：短作业优先，适合提高整体吞吐量
- **Round-Robin**：轮询调度，适合公平性要求高的场景

**任务优先级设计**：
- **视觉任务优先**：为 image/video 类型任务赋予更高默认优先级，符合"优先通过视觉信息检索"的偏好
- **模态优先级**：image/video > text > audio > 其他
- **任务类型优先级**：
  - file_scan: 优先级 2（文件扫描，基础任务）
  - file_embed_image: 优先级 1（图像向量化，最高优先级）
  - file_embed_video: 优先级 1（视频向量化，最高优先级）
  - file_embed_audio: 优先级 5（音频向量化，较低优先级）
  - file_embed_text: 优先级 3（文本向量化，中等优先级）
  - video_slice: 优先级 2（视频切片，基础任务）
  - audio_segment: 优先级 4（音频分段，较低优先级）

**优先级计算实现**：
```python
def calculate_task_priority(self, task: Dict[str, Any]) -> float:
    """
    计算任务优先级
    
    Args:
        task: 任务数据
    
    Returns:
        优先级分数（越小优先级越高）
    """
    task_type = task.get("task_type")
    
    # 基础优先级（根据任务类型）
    base_priority = self.task_type_priorities.get(task_type, 5)
    
    # 模态优先级调整
    modality = task.get("modality", "")
    if modality in ["image", "video"]:
        base_priority -= 1  # 视觉任务优先级提升
    elif modality == "audio":
        base_priority += 1  # 音频任务优先级降低
    
    # 用户指定优先级（如果存在）
    user_priority = task.get("priority")
    if user_priority is not None:
        base_priority = min(base_priority, user_priority)
    
    # 任务等待时间调整（等待越久优先级越高）
    wait_time = time.time() - task.get("created_at", time.time())
    wait_bonus = int(wait_time / 60)  # 每等待1分钟优先级提升1
    
    return max(0, base_priority - wait_bonus)
```

**开发测试指南**：
1. 测试不同调度策略的效果
2. 测试任务优先级计算算法
3. 测试资源分配和释放机制
4. 测试负载均衡算法
5. 测试调度性能指标

#### 2.1.7 hardware/performance_monitor.py - 性能监控器（新增）

**模块职责**：
- 实时监控系统性能指标
- 收集和分析性能数据
- 提供性能告警机制
- 生成性能报告

**接口设计**：
```python
class PerformanceMonitor:
    def __init__(self, config: Dict[str, Any])
    def initialize(self) -> bool
    def start_monitoring(self) -> None
    def stop_monitoring(self) -> None
    
    # 性能指标收集
    def collect_cpu_metrics(self) -> Dict[str, float]
    def collect_memory_metrics(self) -> Dict[str, float]
    def collect_gpu_metrics(self) -> Dict[str, float]
    def collect_disk_metrics(self) -> Dict[str, float]
    def collect_model_metrics(self, model_type: str) -> Dict[str, float]
    
    # 性能分析
    def analyze_performance_trends(self, time_window: int = 3600) -> Dict[str, Any]
    def detect_performance_anomalies(self) -> List[Dict[str, Any]]
    def calculate_performance_score(self) -> float
    
    # 告警机制
    def set_performance_thresholds(self, thresholds: Dict[str, float]) -> None
    def check_performance_alerts(self) -> List[Dict[str, Any]]
    def send_performance_alert(self, alert: Dict[str, Any]) -> None
    
    # 报告生成
    def generate_performance_report(self, time_range: Tuple[float, float]) -> Dict[str, Any]
    def export_metrics_data(self, format: str = "json") -> str
```

**性能指标定义**：
```python
class PerformanceMetrics:
    # 系统指标
    cpu_usage: float           # CPU使用率 (0-100%)
    memory_usage: float        # 内存使用率 (0-100%)
    gpu_usage: float          # GPU使用率 (0-100%)
    disk_io_rate: float       # 磁盘IO速率 (MB/s)
    
    # 模型指标
    inference_latency: float   # 推理延迟 (ms)
    throughput: float         # 吞吐量 (requests/s)
    model_accuracy: float     # 模型准确率 (0-1)
    
    # 应用指标
    search_response_time: float  # 搜索响应时间 (ms)
    indexing_speed: float       # 索引速度 (files/s)
    error_rate: float          # 错误率 (0-1)
```

**开发测试指南**：
1. 测试各种性能指标的收集准确性
2. 测试性能趋势分析算法
3. 测试异常检测机制
4. 测试告警功能
5. 测试报告生成和导出功能

#### 2.1.5 task/task_manager.py - 任务管理器

**模块职责**：
- 管理任务队列和调度
- 支持任务优先级和依赖关系
- 提供任务状态查询和监控
- 实现任务重试和错误处理
- 支持任务暂停、恢复和取消

**接口设计**：
```python
class TaskManager:
    def __init__(config: Dict[str, Any])
    def initialize(self) -> bool
    def shutdown(self) -> None
    def create_task(self, task_type: str, task_data: Dict[str, Any], priority: int = 5, max_retries: int = 3, depends_on: List[str] = None) -> str
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]
    def update_task_status(self, task_id: str, status: str, result: Optional[Any] = None) -> bool
    def get_pending_tasks(self, limit: int = 100) -> List[Dict[str, Any]]
    def get_running_tasks(self, limit: int = 100) -> List[Dict[str, Any]]
    def get_completed_tasks(self, limit: int = 100) -> List[Dict[str, Any]]
    def get_failed_tasks(self, limit: int = 100) -> List[Dict[str, Any]]
    def cancel_task(self, task_id: str) -> bool
    def pause_task(self, task_id: str) -> bool
    def resume_task(self, task_id: str) -> bool
    def get_task_stats(self) -> Dict[str, Any]
    def add_task_listener(self, event_type: str, callback: Callable) -> None
    def remove_task_listener(self, event_type: str, callback: Callable) -> None
    
    # 任务依赖管理
    def add_task_dependency(self, task_id: str, depends_on: str) -> bool
    def check_dependencies(self, task_id: str) -> bool
    def get_dependent_tasks(self, task_id: str) -> List[str]
```

**依赖注入**：
- 构造函数接收配置字典
- 通过回调函数或任务处理器执行任务，不直接调用业务模块

**任务数据模型**：
```python
class Task:
    id: str                    # 任务唯一ID（UUID v4）
    task_type: str              # 任务类型（file_scan/file_embed/video_slice等）
    task_data: Dict[str, Any]   # 任务数据
    priority: int              # 优先级（0-10，数字越小优先级越高）
    status: str                # 状态（pending/running/completed/failed/cancelled/paused）
    created_at: float           # 创建时间戳
    updated_at: float           # 更新时间戳
    started_at: Optional[float]  # 开始执行时间
    completed_at: Optional[float] # 完成时间
    retry_count: int           # 当前重试次数
    max_retries: int           # 最大重试次数
    result: Optional[Any]      # 任务执行结果
    error: Optional[str]       # 错误信息（如果有）
    progress: float            # 任务进度（0.0-1.0）
    depends_on: List[str] = []  # 依赖的任务ID列表（新增）
    blocking_for: List[str] = []  # 被此任务阻塞的任务ID列表（新增）
```

**任务优先级定义**：

| 优先级 | 任务类型 | 说明 | 依赖关系 |
|-------|---------|------|---------|
| 0 | file_scan | 文件扫描（最高优先级，基础任务） | 无依赖 |
| 1 | file_embed_image | 图像向量化（最高优先级） | 依赖file_scan |
| 1 | file_embed_video | 视频向量化（最高优先级） | 依赖file_scan + video_slice |
| 2 | video_slice | 视频切片（高优先级） | 依赖file_scan |
| 3 | file_embed_text | 文本向量化（中等优先级） | 依赖file_scan |
| 4 | audio_segment | 音频分段（较低优先级） | 依赖file_scan |
| 5 | file_embed_audio | 音频向量化（较低优先级） | 依赖file_scan + audio_segment |
| 6 | thumbnail_generate | 缩略图生成（低优先级） | 依赖file_scan |
| 7 | preview_generate | 预览生成（最低优先级） | 依赖file_scan |

**任务依赖关系图**：

```
file_scan (优先级0)
    ├─→ file_embed_image (优先级1)
    ├─→ video_slice (优先级2)
    │       └─→ file_embed_video (优先级1)
    ├─→ file_embed_text (优先级3)
    ├─→ audio_segment (优先级4)
    │       └─→ file_embed_audio (优先级5)
    ├─→ thumbnail_generate (优先级6)
    └─→ preview_generate (优先级7)
```

**任务依赖管理逻辑**：
```python
def check_dependencies(self, task_id: str) -> bool:
    """
    检查任务依赖是否满足
    
    Args:
        task_id: 任务ID
    
    Returns:
        依赖是否满足（所有依赖任务都已完成）
    """
    task = self.get_task(task_id)
    if not task or not task.depends_on:
        return True
    
    # 检查所有依赖任务是否已完成
    for dep_task_id in task.depends_on:
        dep_task = self.get_task(dep_task_id)
        if not dep_task or dep_task.status != 'completed':
            return False
    
    return True

def add_task_dependency(self, task_id: str, depends_on: str) -> bool:
    """
    添加任务依赖
    
    Args:
        task_id: 任务ID
        depends_on: 依赖的任务ID
    
    Returns:
        是否成功添加
    """
    task = self.get_task(task_id)
    dep_task = self.get_task(depends_on)
    
    if not task or not dep_task:
        return False
    
    # 避免循环依赖
    if self._would_create_cycle(task_id, depends_on):
        return False
    
    # 添加依赖
    if depends_on not in task.depends_on:
        task.depends_on.append(depends_on)
    
    # 更新阻塞关系
    if task_id not in dep_task.blocking_for:
        dep_task.blocking_for.append(task_id)
    
    return True

def _would_create_cycle(self, task_id: str, depends_on: str) -> bool:
    """
    检查是否会创建循环依赖
    
    Args:
        task_id: 任务ID
        depends_on: 依赖的任务ID
    
    Returns:
        是否会创建循环依赖
    """
    # 使用DFS检测循环
    visited = set()
    def dfs(current_id: str) -> bool:
        if current_id in visited:
            return False
        if current_id == task_id:
            return True
        visited.add(current_id)
        
        task = self.get_task(current_id)
        if task:
            for dep_id in task.depends_on:
                if dfs(dep_id):
                    return True
        return False
    
    return dfs(depends_on)
```

**并发控制和资源限制**：

```python
class ConcurrencyControl:
    """
    并发控制和资源限制机制
    
    确保系统资源合理分配，防止资源耗尽和任务饥饿
    """
    
    def __init__(self, config: Dict[str, Any]):
        # 并发数限制
        self.max_concurrent_tasks = config.get('max_concurrent_tasks', 4)
        self.max_concurrent_by_type = config.get('max_concurrent_by_type', {
            'file_scan': 1,
            'file_embed': 2,
            'video_slice': 2,
            'audio_segment': 2
        })
        
        # 资源限制
        self.max_memory_usage = config.get('max_memory_usage', 8 * 1024 * 1024 * 1024)  # 8GB
        self.max_cpu_usage = config.get('max_cpu_usage', 80)  # 80%
        self.max_gpu_usage = config.get('max_gpu_usage', 90)  # 90%
        
        # 任务队列
        self.task_queue = PriorityQueue()
        self.running_tasks = {}  # task_id -> Task
        self.waiting_tasks = {}  # task_id -> Task
        
        # 资源监控
        self.resource_monitor = ResourceMonitor()
        
        # 锁机制
        self.queue_lock = threading.Lock()
        self.resource_lock = threading.Lock()
    
    def can_start_task(self, task: Task) -> bool:
        """
        检查是否可以启动任务
        
        Args:
            task: 待启动的任务
        
        Returns:
            是否可以启动
        """
        # 1. 检查并发数限制
        if len(self.running_tasks) >= self.max_concurrent_tasks:
            return False
        
        # 2. 检查任务类型并发数限制
        task_type = task.task_type
        type_count = sum(1 for t in self.running_tasks.values() if t.task_type == task_type)
        if type_count >= self.max_concurrent_by_type.get(task_type, 2):
            return False
        
        # 3. 检查资源使用情况
        if not self.check_resource_availability(task):
            return False
        
        return True
    
    def check_resource_availability(self, task: Task) -> bool:
        """
        检查资源可用性
        
        Args:
            task: 待检查的任务
        
        Returns:
            资源是否可用
        """
        # 获取当前资源使用情况
        current_usage = self.resource_monitor.get_current_usage()
        
        # 检查内存
        if current_usage['memory'] + self.estimate_task_memory(task) > self.max_memory_usage:
            return False
        
        # 检查CPU
        if current_usage['cpu'] > self.max_cpu_usage:
            return False
        
        # 检查GPU（如果任务需要GPU）
        if task.task_data.get('requires_gpu', False):
            if current_usage['gpu'] > self.max_gpu_usage:
                return False
        
        return True
    
    def estimate_task_memory(self, task: Task) -> int:
        """
        估算任务内存需求
        
        Args:
            task: 任务对象
        
        Returns:
            估算的内存需求（字节）
        """
        # 根据任务类型估算内存需求
        memory_requirements = {
            'file_scan': 100 * 1024 * 1024,  # 100MB
            'file_embed': 500 * 1024 * 1024,  # 500MB
            'video_slice': 200 * 1024 * 1024,  # 200MB
            'audio_segment': 150 * 1024 * 1024  # 150MB
        }
        
        return memory_requirements.get(task.task_type, 100 * 1024 * 1024)
    
    def acquire_resources(self, task: Task) -> bool:
        """
        获取任务所需资源
        
        Args:
            task: 任务对象
        
        Returns:
            是否成功获取资源
        """
        with self.resource_lock:
            if not self.check_resource_availability(task):
                return False
            
            # 标记资源占用
            self.resource_monitor.mark_resource_usage(task, self.estimate_task_memory(task))
            return True
    
    def release_resources(self, task: Task) -> None:
        """
        释放任务占用的资源
        
        Args:
            task: 任务对象
        """
        with self.resource_lock:
            self.resource_monitor.release_resource_usage(task)


class ResourceMonitor:
    """
    资源监控器
    
    实时监控系统资源使用情况
    """
    
    def __init__(self):
        self.resource_usage = {
            'memory': 0,
            'cpu': 0,
            'gpu': 0
        }
        self.task_resource_map = {}  # task_id -> resource_usage
    
    def get_current_usage(self) -> Dict[str, float]:
        """
        获取当前资源使用情况
        
        Returns:
            资源使用情况字典
        """
        # 获取系统实际资源使用情况
        import psutil
        import torch
        
        # CPU使用率
        self.resource_usage['cpu'] = psutil.cpu_percent(interval=0.1)
        
        # 内存使用情况
        memory = psutil.virtual_memory()
        self.resource_usage['memory'] = memory.used
        
        # GPU使用情况（如果有）
        if torch.cuda.is_available():
            self.resource_usage['gpu'] = torch.cuda.memory_allocated() / torch.cuda.max_memory_allocated()
        else:
            self.resource_usage['gpu'] = 0
        
        return self.resource_usage.copy()
    
    def mark_resource_usage(self, task: Task, memory: int) -> None:
        """
        标记任务资源占用
        
        Args:
            task: 任务对象
            memory: 内存占用（字节）
        """
        self.task_resource_map[task.id] = {
            'memory': memory,
            'cpu': task.task_data.get('cpu_requirement', 10),
            'gpu': task.task_data.get('gpu_requirement', 0)
        }
    
    def release_resource_usage(self, task: Task) -> None:
        """
        释放任务资源占用
        
        Args:
            task: 任务对象
        """
        if task.id in self.task_resource_map:
            del self.task_resource_map[task.id]
```

**任务优先级调度算法**：

```python
class TaskScheduler:
    """
    任务调度器
    
    实现多优先级任务调度算法
    """
    
    def __init__(self, concurrency_control: ConcurrencyControl):
        self.concurrency_control = concurrency_control
        self.priority_queues = {
            0: [],  # 最高优先级
            1: [],
            2: [],
            3: [],
            4: [],
            5: [],  # 默认优先级
            6: [],
            7: [],
            8: [],
            9: [],
            10: []  # 最低优先级
        }
        self.queue_lock = threading.Lock()
    
    def add_task(self, task: Task) -> None:
        """
        添加任务到调度队列
        
        Args:
            task: 任务对象
        """
        with self.queue_lock:
            priority = task.priority
            self.priority_queues[priority].append(task)
    
    def get_next_task(self) -> Optional[Task]:
        """
        获取下一个待执行任务
        
        Returns:
            下一个任务对象，如果没有则返回None
        """
        with self.queue_lock:
            # 按优先级从高到低查找
            for priority in range(11):
                if self.priority_queues[priority]:
                    task = self.priority_queues[priority].pop(0)
                    
                    # 检查是否可以启动
                    if self.concurrency_control.can_start_task(task):
                        return task
                    else:
                        # 不能启动，放回队列
                        self.priority_queues[priority].insert(0, task)
                        continue
            
            return None
    
    def calculate_priority(self, task_type: str, task_data: Dict[str, Any]) -> int:
        """
        计算任务优先级
        
        Args:
            task_type: 任务类型
            task_data: 任务数据
        
        Returns:
            优先级（0-10）
        """
        # 基础优先级
        base_priority = {
            'file_scan': 3,
            'file_embed': 5,
            'video_slice': 4,
            'audio_segment': 5
        }
        
        priority = base_priority.get(task_type, 5)
        
        # 根据任务数据调整优先级
        if task_data.get('is_user_initiated', False):
            # 用户发起的任务优先级更高
            priority = max(0, priority - 2)
        
        if task_data.get('is_background', False):
            # 后台任务优先级更低
            priority = min(10, priority + 2)
        
        if task_data.get('is_urgent', False):
            # 紧急任务优先级最高
            priority = 0
        
        return priority
```

**任务超时和取消机制**：

```python
class TaskTimeoutManager:
    """
    任务超时管理器
    
    监控任务执行时间，超时自动取消
    """
    
    def __init__(self, task_manager: 'TaskManager'):
        self.task_manager = task_manager
        self.timeout_configs = {
            'file_scan': 3600,  # 1小时
            'file_embed': 1800,  # 30分钟
            'video_slice': 600,  # 10分钟
            'audio_segment': 300  # 5分钟
        }
        self.monitor_thread = None
        self.running = False
    
    def start_monitoring(self) -> None:
        """
        启动超时监控线程
        """
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
    
    def stop_monitoring(self) -> None:
        """
        停止超时监控线程
        """
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join()
    
    def _monitor_loop(self) -> None:
        """
        监控循环
        """
        while self.running:
            try:
                # 获取所有运行中的任务
                running_tasks = self.task_manager.get_running_tasks()
                
                current_time = time.time()
                
                for task in running_tasks:
                    # 检查任务是否超时
                    timeout = self.timeout_configs.get(task.task_type, 600)
                    elapsed = current_time - task.started_at
                    
                    if elapsed > timeout:
                        # 任务超时，取消任务
                        self.task_manager.cancel_task(task.id)
                        logger.warning(f"Task {task.id} timed out after {elapsed:.2f}s")
                
                # 休眠1秒
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in timeout monitor: {e}")
    
    def set_timeout(self, task_type: str, timeout: int) -> None:
        """
        设置任务类型超时时间
        
        Args:
            task_type: 任务类型
            timeout: 超时时间（秒）
        """
        self.timeout_configs[task_type] = timeout
```

**任务队列持久化和恢复策略**：

```python
class TaskPersistence:
    """
    任务持久化
    
    将任务队列持久化到磁盘，支持系统崩溃后恢复
    """
    
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.persistence_file = os.path.join(data_dir, 'tasks.json')
        self.backup_file = os.path.join(data_dir, 'tasks.backup.json')
        self.lock = threading.Lock()
    
    def save_tasks(self, tasks: List[Task]) -> bool:
        """
        保存任务到磁盘
        
        Args:
            tasks: 任务列表
        
        Returns:
            是否保存成功
        """
        with self.lock:
            try:
                # 创建备份
                if os.path.exists(self.persistence_file):
                    shutil.copy2(self.persistence_file, self.backup_file)
                
                # 序列化任务
                tasks_data = [task.__dict__ for task in tasks]
                
                # 写入文件
                with open(self.persistence_file, 'w', encoding='utf-8') as f:
                    json.dump(tasks_data, f, indent=2, ensure_ascii=False)
                
                return True
                
            except Exception as e:
                logger.error(f"Failed to save tasks: {e}")
                return False
    
    def load_tasks(self) -> List[Task]:
        """
        从磁盘加载任务
        
        Returns:
            任务列表
        """
        with self.lock:
            try:
                # 检查文件是否存在
                if not os.path.exists(self.persistence_file):
                    return []
                
                # 读取文件
                with open(self.persistence_file, 'r', encoding='utf-8') as f:
                    tasks_data = json.load(f)
                
                # 反序列化任务
                tasks = []
                for task_data in tasks_data:
                    task = Task(**task_data)
                    
                    # 恢复运行中的任务状态
                    if task.status == 'running':
                        task.status = 'pending'
                        task.retry_count = 0
                    
                    tasks.append(task)
                
                return tasks
                
            except Exception as e:
                logger.error(f"Failed to load tasks: {e}")
                
                # 尝试从备份恢复
                if os.path.exists(self.backup_file):
                    try:
                        shutil.copy2(self.backup_file, self.persistence_file)
                        return self.load_tasks()
                    except:
                        pass
                
                return []
    
    def clear_tasks(self) -> bool:
        """
        清空持久化的任务
        
        Returns:
            是否清空成功
        """
        with self.lock:
            try:
                if os.path.exists(self.persistence_file):
                    os.remove(self.persistence_file)
                if os.path.exists(self.backup_file):
                    os.remove(self.backup_file)
                return True
            except Exception as e:
                logger.error(f"Failed to clear tasks: {e}")
                return False
```

**配置示例**：
```yaml
task_manager:
  # 并发控制配置
  max_concurrent_tasks: 4
  max_concurrent_by_type:
    file_scan: 1
    file_embed: 2
    video_slice: 2
    audio_segment: 2
  
  # 资源限制配置
  max_memory_usage: 8589934592  # 8GB
  max_cpu_usage: 80  # 80%
  max_gpu_usage: 90  # 90%
  
  # 任务超时配置（秒）
  task_timeouts:
    file_scan: 3600  # 1小时
    file_embed: 1800  # 30分钟
    video_slice: 600  # 10分钟
    audio_segment: 300  # 5分钟
  
  # 持久化配置
  enable_persistence: true
  persistence_interval: 60  # 每60秒持久化一次
  
  # 任务队列配置
  queue_size_limit: 1000  # 队列最大任务数
  task_retention_days: 7  # 已完成任务保留天数
```

**开发测试指南**：
1. 测试任务创建和调度机制
2. 测试优先级排序和任务执行顺序
3. 测试任务状态更新和查询
4. 测试并发任务处理能力
5. 测试任务重试和错误处理
6. 测试任务暂停、恢复和取消功能
7. 测试任务监听器功能
8. 测试并发控制机制
9. 测试资源限制和监控
10. 测试任务超时和取消
11. 测试任务队列持久化和恢复

#### 2.1.6 hardware/hardware_detector.py - 硬件检测器

**模块职责**：
- 检测系统硬件配置（CPU、GPU、内存、磁盘）
- 推荐合适的模型和参数配置
- 提供硬件信息查询和监控
- 动态调整资源使用策略
- 首次安装/启动时自动执行并生成配置文件

**接口设计**：
```python
class HardwareDetector:
    def __init__(config: Dict[str, Any])
    def detect_hardware(self) -> Dict[str, Any]
    def get_hardware_info(self) -> Dict[str, Any]
    def get_recommended_models(self) -> Dict[str, Dict[str, Any]]
    def get_optimal_batch_size(self, model_type: str) -> int
    def get_optimal_precision(self, model_type: str) -> str
    def get_optimal_device(self, model_type: str = None) -> str
    def get_gpu_info(self) -> List[Dict[str, Any]]
    def get_cpu_info(self) -> Dict[str, Any]
    def get_memory_info(self) -> Dict[str, Any]
    def get_disk_info(self, path: str) -> Dict[str, Any]
    def is_gpu_available(self) -> bool
    def is_cuda_available(self) -> bool
    def is_mps_available(self) -> bool
    def is_openvino_available(self) -> bool
    
    # 配置文件生成
    def generate_config_file(self, config_path: str) -> bool
    def update_config_file(self, config_path: str) -> bool
    def load_config_file(self, config_path: str) -> Dict[str, Any]
    
    # 首次启动检测
    def is_first_run(self) -> bool
    def run_initial_setup(self, config_path: str) -> bool
```

**依赖注入**：
- 构造函数接收配置字典
- 不依赖其他业务模块

**硬件信息模型**：
```python
class HardwareInfo:
    cpu_count: int            # CPU核心数
    cpu_name: str             # CPU名称
    cpu_memory_gb: float      # CPU内存（GB）
    gpu_available: bool        # 是否有GPU
    gpus: List[Dict[str, Any]] # GPU列表
        - name: str           # GPU名称
        - memory_gb: float    # GPU内存（GB）
        - device_type: str    # 设备类型（cuda/mps/opencl）
        - compute_capability: float # 计算能力
    disk_space_gb: float      # 可用磁盘空间（GB）
    total_disk_gb: float      # 总磁盘空间（GB）
    hardware_level: str       # 硬件级别（low/mid/high/ultra）
    recommended_models: Dict[str, Dict[str, Any]] # 推荐模型配置
        - image_video_model:  # 图片和视频向量化模型
            model_type: str     # 模型类型（mobileclip/colsmol_500m/colqwen2_5_v0_2）
            model_name: str     # 推荐模型名称
            batch_size: int     # 推荐批量大小
            precision: str      # 推荐精度
            device: str         # 推荐设备
            memory_requirement: str  # 内存需求
        - audio_model:         # 音频向量化模型
            model_type: str     # 模型类型（clap）
            model_name: str     # 推荐模型名称
            batch_size: int     # 推荐批量大小
            precision: str      # 推荐精度
            device: str         # 推荐设备
        - speech_model:        # 语音转文本模型
            model_type: str     # 模型类型（whisper）
            model_name: str     # 推荐模型名称
            precision: str      # 推荐精度
            device: str         # 推荐设备
```

**首次启动流程**：
```python
# 应用启动时自动执行
def on_app_startup():
    hardware_detector = HardwareDetector(config)
    
    # 检查是否首次运行
    if hardware_detector.is_first_run():
        # 自动检测硬件
        hardware_info = hardware_detector.detect_hardware()
        
        # 生成配置文件
        config_path = get_config_path()
        hardware_detector.run_initial_setup(config_path)
        
        # 保存硬件信息
        save_hardware_info(hardware_info)
    else:
        # 加载已有配置
        config = hardware_detector.load_config_file(config_path)
```

**设计说明**：
- **自动检测**：首次安装/启动时自动执行硬件检测
- **配置生成**：根据检测结果自动生成最优配置文件
- **硬件级别**：根据硬件能力分为low/mid/high/ultra四个级别
- **模型推荐**：根据硬件级别推荐最优模型和参数
- **配置持久化**：将检测结果和推荐配置保存到配置文件

**开发测试指南**：
1. 测试不同硬件环境的检测准确性
2. 测试模型推荐逻辑的合理性
3. 测试参数优化建议的有效性
4. 测试异常硬件环境处理
5. 测试GPU类型检测（CUDA/MPS/OpenVINO）
6. 测试内存和磁盘信息检测
7. 测试首次启动自动配置生成
8. 测试配置文件加载和更新

#### 2.1.7 database/unified_data_access.py - 统一数据访问层

**模块职责**：
- 提供统一的数据访问接口，整合数据库和向量存储操作
- 支持事务管理和数据一致性
- 实现复杂查询和数据关联
- 提供数据统计和分析功能

**接口设计**：
```python
class UnifiedDataAccessLayer:
    def __init__(database_manager: DatabaseManager, vector_store: VectorStore)
    def initialize(self) -> bool
    def begin_transaction(self) -> None
    def commit(self) -> None
    def rollback(self) -> None
    
    def add_file(self, file_metadata: Dict[str, Any]) -> str
    def add_file_vectors(self, file_id: str, vectors: List[Dict[str, Any]]) -> None
    def update_file_metadata(self, file_id: str, updates: Dict[str, Any]) -> bool
    def update_file_status(self, file_id: str, status: str) -> bool
    
    def get_file(self, file_id: str, include_vectors: bool = False) -> Optional[Dict[str, Any]]
    def get_file_by_path(self, file_path: str) -> Optional[Dict[str, Any]]
    def get_files_by_status(self, status: str, limit: int = 100) -> List[Dict[str, Any]]
    
    def search_files(self, query_vector: List[float], modality: str = None, limit: int = 20) -> List[Dict[str, Any]]
    def search_files_by_text(self, text: str, limit: int = 20) -> List[Dict[str, Any]]
    def search_files_by_metadata(self, filters: Dict[str, Any], limit: int = 100) -> List[Dict[str, Any]]
    
    def delete_file(self, file_id: str, delete_vectors: bool = True) -> bool
    def delete_file_vectors(self, file_id: str) -> bool
    
    def get_total_file_count(self) -> int
    def get_file_count_by_type(self) -> Dict[str, int]
    def get_file_count_by_status(self) -> Dict[str, int]
    def get_vector_count(self) -> int
    def get_statistics(self) -> Dict[str, Any]
```

**设计原则**：
- **单一职责**：UnifiedDataAccessLayer仅负责协调DatabaseManager和VectorStore的操作
- **避免循环依赖**：不直接回写元数据到DatabaseManager，通过明确的接口调用
- **简化向量存储**：使用单一向量表设计，不使用create_collection等复杂操作
- **清晰的数据流**：文件元数据 → DatabaseManager，向量数据 → VectorStore，通过UDAL协调

**依赖关系**：
```
UnifiedDataAccessLayer
├── DatabaseManager (元数据存储)
└── VectorStore (向量存储)

# 数据流向
文件 → UDAL.add_file() → DatabaseManager.insert_file_metadata()
     → UDAL.add_file_vectors() → VectorStore.insert_vectors()

# 检索流向
查询 → UDAL.search_files() → VectorStore.search_vectors()
     → UDAL.get_file() → DatabaseManager.get_file_metadata()
```

**开发测试指南**：
1. 测试文件添加和向量关联操作
2. 测试多模态文件检索功能
3. 测试事务管理和数据一致性
4. 测试错误处理和回滚机制
5. 测试复杂查询和过滤功能
6. 测试数据统计和分析功能
7. 测试避免循环依赖的设计

### 2.2 服务层

#### 2.2.1 search/query_processor.py - 查询处理器（新增）

**模块职责**：
- 处理和优化用户查询
- 实现查询语法解析
- 支持多模态查询融合
- 提供查询建议和自动完成

**接口设计**：
```python
class QueryProcessor:
    def __init__(self, config: Dict[str, Any])
    def initialize(self) -> bool
    
    # 查询处理
    def process_text_query(self, query: str) -> Dict[str, Any]
    def process_image_query(self, image_path: str) -> Dict[str, Any]
    def process_audio_query(self, audio_path: str) -> Dict[str, Any]
    def process_video_query(self, video_path: str) -> Dict[str, Any]
    
    # 查询优化
    def optimize_query(self, query: Dict[str, Any]) -> Dict[str, Any]
    def expand_query(self, query: str) -> List[str]
    def suggest_corrections(self, query: str) -> List[str]
    
    # 多模态融合
    def fuse_multimodal_queries(self, queries: List[Dict[str, Any]]) -> Dict[str, Any]
    def calculate_query_weights(self, queries: List[Dict[str, Any]]) -> List[float]
    
    # 查询分析
    def analyze_query_intent(self, query: str) -> Dict[str, Any]
    def extract_query_features(self, query: Dict[str, Any]) -> Dict[str, Any]
```

**查询类型定义**：
```python
class QueryType:
    TEXT = "text"              # 文本查询
    IMAGE = "image"            # 图像查询
    AUDIO = "audio"            # 音频查询
    VIDEO = "video"            # 视频查询
    MULTIMODAL = "multimodal"  # 多模态查询
    SEMANTIC = "semantic"      # 语义查询
    SIMILARITY = "similarity"  # 相似度查询
```

**开发测试指南**：
1. 测试不同类型查询的处理逻辑
2. 测试查询优化算法
3. 测试多模态查询融合
4. 测试查询建议功能
5. 测试查询意图分析

#### 2.2.2 search/result_ranker.py - 结果排序器（新增）

**模块职责**：
- 实现多种结果排序算法
- 支持个性化排序
- 提供结果去重和过滤
- 优化结果展示顺序
- 计算结果的相关性评分

**核心原则**：
- **纯排序逻辑**：只负责排序算法的实现，不涉及检索流程
- **算法独立**：每种排序算法独立实现，易于扩展和测试
- **可配置**：支持通过配置选择不同的排序策略

**接口设计**：
```python
class ResultRanker:
    def __init__(self, config: Dict[str, Any])
    def initialize(self) -> bool
    
    # 排序算法
    def rank_by_similarity(self, results: List[Dict[str, Any]], query_vector: List[float]) -> List[Dict[str, Any]]
    def rank_by_relevance(self, results: List[Dict[str, Any]], query: Dict[str, Any]) -> List[Dict[str, Any]]
    def rank_by_popularity(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]
    def rank_by_recency(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]
    
    # 个性化排序
    def personalized_ranking(self, results: List[Dict[str, Any]], user_profile: Dict[str, Any]) -> List[Dict[str, Any]]
    def learn_user_preferences(self, user_interactions: List[Dict[str, Any]]) -> Dict[str, Any]
    
    # 结果处理
    def deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]
    def filter_results(self, results: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]
    def diversify_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]
    
    # 评分机制
    def calculate_relevance_score(self, result: Dict[str, Any], query: Dict[str, Any]) -> float
    def combine_scores(self, scores: Dict[str, float], weights: Dict[str, float]) -> float
```

**排序策略**：
```python
class RankingStrategy:
    SIMILARITY = "similarity"      # 基于相似度排序
    RELEVANCE = "relevance"       # 基于相关性排序
    POPULARITY = "popularity"     # 基于流行度排序
    RECENCY = "recency"          # 基于时间排序
    HYBRID = "hybrid"            # 混合排序
    PERSONALIZED = "personalized" # 个性化排序
```

**职责边界**：
- **负责**：排序算法实现、评分计算、结果去重、结果过滤
- **不负责**：检索流程管理、查询处理、向量检索、结果获取

**开发测试指南**：
1. 测试不同排序算法的效果
2. 测试个性化排序功能
3. 测试结果去重和过滤
4. 测试评分机制的准确性
5. 测试排序性能和稳定性

#### 2.2.3 search/search_engine.py - 搜索引擎（优化）

**模块职责**：
- 提供统一的多模态检索入口
- 管理检索流程（查询处理、向量检索、结果获取）
- 实现搜索缓存和优化
- 提供搜索分析和统计
- 协调QueryProcessor和ResultRanker完成完整搜索流程

**核心原则**：
- **流程管理**：专注于检索流程的编排和管理
- **职责分离**：查询处理委托给QueryProcessor，排序委托给ResultRanker
- **统一接口**：提供统一的搜索接口，屏蔽底层实现细节

**接口设计**：
```python
class SearchEngine:
    def __init__(self, embedding_engine: EmbeddingEngine, data_access: UnifiedDataAccessLayer, 
                 query_processor: QueryProcessor, result_ranker: ResultRanker)
    def initialize(self) -> bool
    
    # 核心搜索接口
    def search(self, query: Dict[str, Any], options: Dict[str, Any] = None) -> Dict[str, Any]
    def search_by_text(self, text: str, **kwargs) -> List[Dict[str, Any]]
    def search_by_image(self, image_path: str, **kwargs) -> List[Dict[str, Any]]
    def search_by_audio(self, audio_path: str, **kwargs) -> List[Dict[str, Any]]
    def search_by_video(self, video_path: str, **kwargs) -> List[Dict[str, Any]]
    def search_multimodal(self, queries: List[Dict[str, Any]], **kwargs) -> List[Dict[str, Any]]
    
    # 高级搜索
    def advanced_search(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]
    def semantic_search(self, concept: str, **kwargs) -> List[Dict[str, Any]]
    def similarity_search(self, reference_item: str, **kwargs) -> List[Dict[str, Any]]
    
    # 搜索优化
    def optimize_search_performance(self) -> None
    def warm_up_search_cache(self, common_queries: List[str]) -> None
    def clear_search_cache(self) -> None
    
    # 搜索分析
    def get_search_analytics(self, time_range: Tuple[float, float]) -> Dict[str, Any]
    def get_popular_queries(self, limit: int = 10) -> List[Dict[str, Any]]
    def get_search_performance_metrics(self) -> Dict[str, float]
```

**搜索流程**：
```python
# SearchEngine的典型搜索流程
def search_by_text(self, text: str, **kwargs):
    # 1. 查询处理（委托给QueryProcessor）
    processed_query = self.query_processor.process_text_query(text)
    
    # 2. 向量化（委托给EmbeddingEngine）
    query_vector = self.embedding_engine.embed_text(text)
    
    # 3. 向量检索（委托给UnifiedDataAccessLayer）
    raw_results = self.data_access.search_files(query_vector, **kwargs)
    
    # 4. 结果排序（委托给ResultRanker）
    ranked_results = self.result_ranker.rank_by_similarity(raw_results, query_vector)
    
    # 5. 返回结果
    return ranked_results
```

**搜索选项**：
```python
class SearchOptions:
    limit: int = 20                    # 结果数量限制
    offset: int = 0                    # 结果偏移量
    modalities: List[str] = None       # 指定模态类型
    file_types: List[str] = None       # 指定文件类型
    date_range: Tuple[float, float] = None  # 时间范围
    similarity_threshold: float = 0.7   # 相似度阈值
    ranking_strategy: str = "hybrid"    # 排序策略
    enable_cache: bool = True          # 是否启用缓存
    include_metadata: bool = True      # 是否包含元数据
```

**职责边界**：
- **负责**：检索流程管理、组件协调、缓存管理、搜索统计
- **不负责**：查询处理逻辑（委托给QueryProcessor）、排序算法（委托给ResultRanker）、向量推理（委托给EmbeddingEngine）

**开发测试指南**：
1. 测试各种搜索接口的功能
2. 测试搜索性能和缓存效果
3. 测试高级搜索功能
4. 测试搜索分析和统计
5. 测试多模态搜索融合
3. 测试高级搜索功能
4. 测试搜索分析和统计
5. 测试多模态搜索融合

#### 2.2.2 media/media_processor.py - 媒体处理器

**模块职责**：
- 提供统一的媒体文件处理入口
- 协调各媒体类型的处理流程
- 管理媒体预处理和后处理
- 集成视频分段、图像缩放和音频处理

**接口设计**：
```python
class MediaProcessor:
    def __init__(config: Dict[str, Any], thumbnail_generator: Optional[ThumbnailGenerator] = None)
    def initialize(self) -> bool
    
    # 媒体价值判断（前置过滤）
    def has_media_value(self, file_path: str) -> bool
    def get_min_media_value_duration(self, media_type: str) -> float
    
    def process_file(self, file_path: str) -> Dict[str, Any]
    def process_image(self, image_path: str) -> Dict[str, Any]
    def process_video(self, video_path: str) -> List[Dict[str, Any]]
    def process_audio(self, audio_path: str) -> Dict[str, Any]
    
    def get_supported_media_types(self) -> List[str]
    def is_supported_media_type(self, file_path: str) -> bool
    def get_media_info(self, file_path: str) -> Dict[str, Any]
```

**依赖注入**：
- 构造函数接收配置字典和可选的ThumbnailGenerator实例
- 内部创建或使用外部提供的媒体处理组件

**开发测试指南**：
1. 测试不同类型媒体文件的处理流程
2. 测试媒体信息提取准确性
3. 测试媒体类型检测功能
4. 测试与视频、图像、音频子处理器的集成
5. 测试异常媒体文件处理

#### 2.2.4 media/video/frame_extractor.py - 帧提取器（优化）

**模块职责**：
- 从视频中提取关键帧
- 实现基于FFMPEG场景检测的切片
- 支持短视频快速处理（≤6秒）
- 支持超大视频的渐进处理
- 优化帧提取性能

**接口设计**：
```python
class FrameExtractor:
    def __init__(self, config: Dict[str, Any])
    def initialize(self) -> bool
    
    # 短视频快速处理
    def is_short_video(self, video_path: str, threshold: float = 6.0) -> bool
    def process_short_video(self, video_path: str) -> List[Dict[str, Any]]
    def extract_frames_for_short_video(self, video_path: str, duration: float) -> List[Dict[str, Any]]
    
    # 场景检测和切片（长视频）
    def detect_scenes(self, video_path: str, max_segment_duration: float = 5.0) -> List[Dict[str, Any]]
    def extract_frames_by_scenes(self, video_path: str, scenes: List[Dict[str, Any]], frames_per_scene: int = 1) -> List[Dict[str, Any]]
    
    # 超大视频处理
    def process_large_video(self, video_path: str, initial_duration: float = 300.0) -> Dict[str, Any]
    def extract_key_transitions(self, video_path: str, num_transitions: int = 10) -> List[Dict[str, Any]]
    
    # 帧提取方法
    def extract_frames_by_interval(self, video_path: str, interval: float) -> List[Dict[str, Any]]
    def extract_frames_by_time(self, video_path: str, timestamps: List[float]) -> List[Dict[str, Any]]
    
    # 帧预处理
    def preprocess_frame(self, frame: np.ndarray, target_size: Tuple[int, int] = None) -> np.ndarray
    def batch_preprocess_frames(self, frames: List[np.ndarray], target_size: Tuple[int, int] = None) -> List[np.ndarray]
    
    # 统一处理入口
    def process_video(self, video_path: str) -> List[Dict[str, Any]]:
        """
        统一视频处理入口
        
        根据视频时长自动选择处理策略：
        - ≤6秒：短视频快速处理（简化时序定位）
        - >6秒：长视频场景检测切片
        
        Args:
            video_path: 视频文件路径
        
        Returns:
            处理结果列表
        """
        if self.is_short_video(video_path):
            return self.process_short_video(video_path)
        else:
            scenes = self.detect_scenes(video_path)
            return self.extract_frames_by_scenes(video_path, scenes)
```

**场景数据模型**：
```python
class SceneSegment:
    scene_id: str              # 场景ID
    start_time: float          # 开始时间（秒）
    end_time: float            # 结束时间（秒）
    duration: float            # 时长（秒）
    frame_count: int           # 帧数
    is_key_transition: bool    # 是否为关键转场点
    confidence: float          # 场景检测置信度
    is_short_video: bool       # 是否为短视频（新增）
    processing_mode: str       # 处理模式（fast/normal）- 新增
```

**短视频处理数据模型**：
```python
class ShortVideoSegment:
    segment_id: str            # 片段ID
    start_time: float          # 开始时间（秒）
    end_time: float            # 结束时间（秒）
    duration: float            # 时长（秒）
    frame_count: int           # 提取的帧数
    frames: List[Frame]        # 提取的帧列表
    is_short_video: bool       # 标记为短视频
    processing_mode: str       # 处理模式（fast）
    confidence: float          # 置信度（短视频为1.0）
```

**设计说明**：
详见 [1.6.4 视频处理优化策略](#164-视频处理优化策略)
- **性能优化**：专注于基本功能，避免过度工程化
- **短视频优化**：针对短视频场景（≤6秒）采用快速处理流程

**开发测试指南**：
1. 测试短视频判断逻辑（is_short_video）
2. 测试短视频快速处理流程（process_short_video）
3. 测试短视频帧提取策略（不同时长提取不同帧数）
4. 测试FFMPEG场景检测准确性
5. 测试最大切片时长限制（≤5秒）
6. 测试超大视频的渐进处理策略
7. 测试关键转场点提取效果
8. 测试时间戳精度（±5秒）
9. 测试统一处理入口（process_video）的路由逻辑
10. 性能测试：对比短视频和长视频的处理速度

#### 2.2.5 media/audio/audio_segmenter.py - 音频分段器（优化）

**模块职责**：
- 实现音频基础分段
- 使用InaSpeechSegmenter区分音乐和语音
- 提供音频特征提取
- 优化音频处理流程
- 根据分类结果影响CLAP/Whisper模型选择

**接口设计**：
```python
class AudioSegmenter:
    def __init__(self, config: Dict[str, Any])
    def initialize(self) -> bool
    
    # 音频价值判断
    def has_audio_value(self, audio_path: str) -> bool
    def get_min_audio_value_duration(self) -> float
    
    # 音频分段
    def segment_by_silence(self, audio_path: str, silence_threshold: float = -40.0) -> List[Dict[str, Any]]
    def segment_by_duration(self, audio_path: str, duration: float = 30.0) -> List[Dict[str, Any]]
    
    # InaSpeechSegmenter集成
    def classify_audio_content(self, audio_path: str) -> List[Dict[str, Any]]
    def get_audio_segments_with_classification(self, audio_path: str) -> List[Dict[str, Any]]
    
    # 模型选择建议
    def recommend_model_for_segment(self, segment: Dict[str, Any]) -> str
    def get_model_selection_strategy(self, segments: List[Dict[str, Any]]) -> Dict[str, Any]
    
    # 特征提取
    def extract_audio_features(self, audio_segment: np.ndarray) -> Dict[str, Any]
    def extract_spectral_features(self, audio_segment: np.ndarray) -> Dict[str, float]
    def extract_temporal_features(self, audio_segment: np.ndarray) -> Dict[str, float]
    
    # 质量评估
    def assess_segment_quality(self, segment: Dict[str, Any]) -> float
    def filter_low_quality_segments(self, segments: List[Dict[str, Any]], quality_threshold: float = 0.5) -> List[Dict[str, Any]]
```

**音频分类类型**：
```python
class AudioContentType:
    SPEECH = "speech"          # 语音
    MUSIC = "music"           # 音乐
    NOISE = "noise"           # 噪声
    SILENCE = "silence"       # 静音
    MIXED = "mixed"           # 混合
    UNKNOWN = "unknown"       # 未知
```

**音频分段数据模型**：
```python
class AudioSegment:
    segment_id: str           # 分段ID
    start_time: float         # 开始时间（秒）
    end_time: float           # 结束时间（秒）
    duration: float           # 时长（秒）
    content_type: str         # 内容类型（speech/music/noise/silence/mixed/unknown）
    confidence: float         # 分类置信度
    recommended_model: str    # 推荐使用的模型（clap/whisper）
    features: Dict[str, Any]  # 音频特征
    quality_score: float      # 质量评分
```

**模型选择逻辑**：
详见 [1.6.2 音频模型集成与分类策略](#162-音频模型集成与分类策略)

**设计说明**：

**开发测试指南**：
1. 测试InaSpeechSegmenter分类准确性
2. 测试模型选择逻辑的正确性
3. 测试音频分段算法
4. 测试特征提取准确性
5. 测试分段质量评估
6. 测试长音频文件处理性能

#### 2.2.7 file/file_indexer.py - 文件索引器

**模块职责**：
- 管理文件索引流程
- 实现增量索引更新
- 优化索引性能
- 提供索引状态管理

**接口设计**：
```python
class FileIndexer:
    def __init__(self, config: Dict[str, Any], metadata_extractor: MetadataExtractor, 
                 embedding_engine: EmbeddingEngine, data_access: UnifiedDataAccessLayer)
    def initialize(self) -> bool
    
    # 索引管理
    def index_file(self, file_path: str, force_reindex: bool = False) -> Dict[str, Any]
    def index_directory(self, directory_path: str, recursive: bool = True) -> Dict[str, Any]
    def batch_index_files(self, file_paths: List[str]) -> Dict[str, Any]
    
    # 增量索引
    def update_index(self, file_path: str) -> Dict[str, Any]
    def remove_from_index(self, file_path: str) -> bool
    def rebuild_index(self, directory_path: str = None) -> Dict[str, Any]
    
    # 索引状态
    def get_index_status(self, file_path: str = None) -> Dict[str, Any]
    def get_indexing_progress(self) -> Dict[str, Any]
    def is_file_indexed(self, file_path: str) -> bool
    def get_index_statistics(self) -> Dict[str, Any]
    
    # 基于文件哈希的去重和引用计数
    def calculate_file_hash(self, file_path: str) -> str
    def check_duplicate_file(self, file_path: str) -> Optional[Dict[str, Any]]
    def handle_duplicate_file(self, file_path: str, existing_file: Dict[str, Any]) -> Dict[str, Any]
    
    # 索引优化
    def optimize_index(self) -> Dict[str, Any]
    def cleanup_orphaned_entries(self) -> int
    def validate_index_integrity(self) -> Dict[str, Any]
    def deduplicate_index(self) -> Dict[str, Any]
    
    # 并发控制
    def set_indexing_concurrency(self, max_workers: int) -> None
    def pause_indexing(self) -> None
    def resume_indexing(self) -> None
    def cancel_indexing(self) -> None
```

**索引状态定义**：
```python
class IndexStatus:
    PENDING = "pending"        # 待索引
    INDEXING = "indexing"     # 索引中
    INDEXED = "indexed"       # 已索引
    FAILED = "failed"         # 索引失败
    OUTDATED = "outdated"     # 需要更新
    REMOVED = "removed"       # 已移除
```

**开发测试指南**：
1. 测试文件索引流程
2. 测试增量索引更新
3. 测试批量索引性能
4. 测试索引状态管理
5. 测试并发索引控制
6. 测试索引完整性验证

#### 2.2.8 cache/cache_manager.py - 缓存管理器（新增）

**模块职责**：
- 管理多级缓存系统
- 实现缓存策略和淘汰算法
- 优化缓存性能
- 提供缓存统计和监控

**接口设计**：
```python
class CacheManager:
    def __init__(self, config: Dict[str, Any])
    def initialize(self) -> bool
    def shutdown(self) -> None
    
    # 缓存操作
    def get(self, key: str, cache_type: str = "default") -> Optional[Any]
    def set(self, key: str, value: Any, ttl: int = None, cache_type: str = "default") -> bool
    def delete(self, key: str, cache_type: str = "default") -> bool
    def exists(self, key: str, cache_type: str = "default") -> bool
    
    # 批量操作
    def get_many(self, keys: List[str], cache_type: str = "default") -> Dict[str, Any]
    def set_many(self, items: Dict[str, Any], ttl: int = None, cache_type: str = "default") -> bool
    def delete_many(self, keys: List[str], cache_type: str = "default") -> int
    
    # 缓存管理
    def clear_cache(self, cache_type: str = None) -> None
    def flush_expired(self, cache_type: str = None) -> int
    def optimize_cache(self, cache_type: str = None) -> None
    
    # 缓存策略
    def set_eviction_policy(self, policy: str, cache_type: str = "default") -> None
    def set_cache_size_limit(self, limit: int, cache_type: str = "default") -> None
    
    # 统计和监控
    def get_cache_stats(self, cache_type: str = None) -> Dict[str, Any]
    def get_hit_rate(self, cache_type: str = "default") -> float
    def get_memory_usage(self, cache_type: str = None) -> Dict[str, int]
```

**缓存类型定义**：
```python
class CacheType:
    EMBEDDING = "embedding"      # 向量缓存
    THUMBNAIL = "thumbnail"      # 缩略图缓存
    METADATA = "metadata"        # 元数据缓存
    SEARCH_RESULT = "search"     # 搜索结果缓存
    MODEL = "model"             # 模型缓存
    PROCESSED_MEDIA = "media"    # 处理后媒体缓存
```

**缓存策略**：
```python
class EvictionPolicy:
    LRU = "lru"                 # 最近最少使用
    LFU = "lfu"                 # 最少使用频率
    FIFO = "fifo"               # 先进先出
    TTL = "ttl"                 # 基于时间
    ADAPTIVE = "adaptive"        # 自适应策略
```

**开发测试指南**：
1. 测试不同缓存策略的效果
2. 测试缓存淘汰算法
3. 测试缓存性能和命中率
4. 测试内存使用优化
5. 测试缓存统计和监控功能

### 2.3 数据层

#### 2.3.1 data/extractors/content_analyzer.py - 内容分析器（新增）

**模块职责**：
- 分析媒体内容特征
- 提取语义信息
- 检测内容类型和主题
- 提供内容质量评估

**接口设计**：
```python
class ContentAnalyzer:
    def __init__(self, config: Dict[str, Any])
    def initialize(self) -> bool
    
    # 内容分析
    def analyze_image_content(self, image_path: str) -> Dict[str, Any]
    def analyze_video_content(self, video_path: str) -> Dict[str, Any]
    def analyze_audio_content(self, audio_path: str) -> Dict[str, Any]
    def analyze_text_content(self, text: str) -> Dict[str, Any]
    
    # 特征提取
    def extract_visual_features(self, image: np.ndarray) -> Dict[str, Any]
    def extract_audio_features(self, audio: np.ndarray) -> Dict[str, Any]
    def extract_semantic_features(self, content: Any) -> Dict[str, Any]
    
    # 内容分类
    def classify_content_type(self, file_path: str) -> Dict[str, float]
    def detect_content_themes(self, content_features: Dict[str, Any]) -> List[Dict[str, Any]]
    def identify_content_objects(self, image: np.ndarray) -> List[Dict[str, Any]]
    
    # 质量评估
    def assess_content_quality(self, file_path: str) -> Dict[str, float]
    def detect_content_issues(self, file_path: str) -> List[Dict[str, Any]]
    def calculate_content_complexity(self, content_features: Dict[str, Any]) -> float
    
    # 相似度计算
    def calculate_content_similarity(self, content1: Dict[str, Any], content2: Dict[str, Any]) -> float
    def find_similar_content(self, reference_content: Dict[str, Any], candidate_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]
```

**内容特征定义**：
```python
class ContentFeatures:
    # 视觉特征
    color_histogram: np.ndarray    # 颜色直方图
    texture_features: Dict[str, float]  # 纹理特征
    edge_features: Dict[str, float]     # 边缘特征
    shape_features: Dict[str, float]    # 形状特征
    
    # 音频特征
    spectral_features: Dict[str, float]  # 频谱特征
    temporal_features: Dict[str, float]  # 时域特征
    rhythm_features: Dict[str, float]    # 节奏特征
    
    # 语义特征
    objects: List[Dict[str, Any]]       # 检测到的对象
    scenes: List[Dict[str, Any]]        # 场景信息
    emotions: Dict[str, float]          # 情感分析
    concepts: List[Dict[str, Any]]      # 概念标签
```

**开发测试指南**：
1. 测试不同媒体类型的内容分析
2. 测试特征提取的准确性
3. 测试内容分类和主题检测
4. 测试质量评估算法
5. 测试相似度计算性能

#### 2.3.1 data/generators/thumbnail_generator.py - 缩略图生成器

**模块职责**：
- 生成媒体文件缩略图
- 优化缩略图质量和文件大小
- 管理缩略图缓存
- 基于文件哈希的缩略图命名（避免重复生成）

**接口设计**：
```python
class ThumbnailGenerator:
    def __init__(self, config: Dict[str, Any])
    def initialize(self) -> bool
    
    # 缩略图生成
    def generate_image_thumbnail(self, image_path: str, size: int = 256) -> str
    def generate_video_thumbnail(self, video_path: str, time_offset: float = 0.3, size: int = 256) -> str
    def generate_audio_thumbnail(self, audio_path: str, size: int = 256) -> str
    
    # 批量生成
    def batch_generate_thumbnails(self, file_paths: List[str]) -> Dict[str, str]
    
    # 缩略图管理
    def get_thumbnail_path(self, file_path: str) -> Optional[str]
    def has_thumbnail(self, file_path: str) -> bool
    def delete_thumbnail(self, file_path: str) -> bool
    
    # 基于文件哈希的缩略图命名
    def get_thumbnail_filename(self, file_hash: str) -> str
    def get_thumbnail_path_by_hash(self, file_hash: str) -> str
    def has_thumbnail_by_hash(self, file_hash: str) -> bool
    
    # 缩略图优化
    def optimize_thumbnail(self, thumbnail_path: str, target_size: int = 50) -> str  # KB
    def compress_thumbnail(self, thumbnail_path: str, quality: int = 85) -> str
    
    # 缓存管理
    def clear_thumbnail_cache(self, older_than_days: int = 30) -> int
    def get_cache_usage(self) -> Dict[str, Any]
```

**基于UUID的缩略图命名策略**：
```python
def get_thumbnail_filename(self, file_id: str) -> str:
    """
    生成基于UUID的缩略图文件名
    
    使用文件ID（UUID v4）作为文件名，确保唯一性
    
    Args:
        file_id: 文件ID（UUID v4）
    
    Returns:
        缩略图文件名（格式：{file_id}.jpg）
    """
    return f"{file_id}.jpg"

def get_thumbnail_path(self, file_id: str) -> str:
    """
    获取基于UUID的缩略图文件路径
    
    Args:
        file_id: 文件ID（UUID v4）
    
    Returns:
        缩略图文件完整路径
    """
    filename = self.get_thumbnail_filename(file_id)
    return os.path.join(self.config["cache_dir"], "thumbnails", filename)

def has_thumbnail(self, file_id: str) -> bool:
    """
    检查是否存在基于UUID的缩略图
    
    Args:
        file_id: 文件ID（UUID v4）
    
    Returns:
        是否存在缩略图
    """
    thumbnail_path = self.get_thumbnail_path(file_id)
    return os.path.exists(thumbnail_path)

def get_thumbnail_path_by_file_path(self, file_path: str) -> Optional[str]:
    """
    根据文件路径获取缩略图路径
    
    Args:
        file_path: 文件路径
    
    Returns:
        缩略图文件路径
    """
    # 通过文件路径获取文件ID
    file_info = self.database_manager.get_file_by_path(file_path)
    if file_info:
        return self.get_thumbnail_path(file_info["id"])
    return None
```

**缩略图命名优势**：
- **唯一性**：使用UUID确保文件名唯一
- **一致性**：与系统其他文件ID生成机制保持一致
- **可追溯性**：通过文件名可直接关联到原始文件
- **安全性**：避免因文件哈希泄露导致的安全问题
- **扩展性**：便于未来扩展缓存管理功能

**缩略图缓存管理**：
- 缓存目录：`{cache_dir}/thumbnails/`
- 缓存格式：JPEG（质量85%）
- 缓存大小：默认256x256像素
- 缓存清理：支持按时间（30天）和大小（1GB）自动清理
- 缓存验证：定期验证缓存文件与原始文件的关联性

**开发测试指南**：
1. 测试不同类型媒体的缩略图生成
2. 测试缩略图质量和文件大小优化
3. 测试批量缩略图生成性能
4. 测试缩略图缓存管理
5. 测试缩略图格式兼容性
6. 测试基于文件哈希的缩略图命名策略
7. 测试缩略图去重和共享机制

#### 2.3.2 data/generators/preview_generator.py - 预览生成器（新增）

**模块职责**：
- 生成媒体文件预览
- 支持多种预览格式
- 优化预览生成性能
- 管理预览缓存
- 基于文件哈希的预览命名（避免重复生成）

**接口设计**：
```python
class PreviewGenerator:
    def __init__(self, config: Dict[str, Any])
    def initialize(self) -> bool
    
    # 预览生成
    def generate_image_preview(self, image_path: str, size: Tuple[int, int] = (512, 512)) -> str
    def generate_video_preview(self, video_path: str, duration: float = 10.0, size: Tuple[int, int] = (512, 288)) -> str
    def generate_audio_preview(self, audio_path: str, duration: float = 30.0) -> str
    def generate_gif_preview(self, video_path: str, start_time: float = 0.0, duration: float = 3.0) -> str
    
    # 批量生成
    def batch_generate_previews(self, file_paths: List[str], preview_config: Dict[str, Any]) -> Dict[str, str]
    def generate_preview_grid(self, file_paths: List[str], grid_size: Tuple[int, int] = (3, 3)) -> str
    
    # 预览管理
    def get_preview_path(self, file_path: str, preview_type: str = "thumbnail") -> Optional[str]
    def has_preview(self, file_path: str, preview_type: str = "thumbnail") -> bool
    def delete_preview(self, file_path: str, preview_type: str = None) -> bool
    
    # 基于文件哈希的预览命名
    def get_preview_filename(self, file_hash: str, preview_type: str = "thumbnail") -> str
    def get_preview_path_by_hash(self, file_hash: str, preview_type: str = "thumbnail") -> str
    def has_preview_by_hash(self, file_hash: str, preview_type: str = "thumbnail") -> bool
    
    # 预览优化
    def optimize_preview_quality(self, preview_path: str, target_size: int = 100) -> str  # KB
    def compress_preview(self, preview_path: str, quality: int = 85) -> str
    
    # 缓存管理
    def clear_preview_cache(self, older_than_days: int = 30) -> int
    def get_cache_usage(self) -> Dict[str, Any]
```

**预览类型定义**：
```python
class PreviewType:
    THUMBNAIL = "thumbnail"        # 缩略图
    SMALL_PREVIEW = "small"       # 小预览图
    MEDIUM_PREVIEW = "medium"     # 中等预览图
    LARGE_PREVIEW = "large"       # 大预览图
    GIF_PREVIEW = "gif"           # GIF动图预览
    VIDEO_PREVIEW = "video"       # 视频预览
    AUDIO_WAVEFORM = "waveform"   # 音频波形图
```

**基于文件哈希的预览命名策略**：
```python
def get_preview_filename(self, file_hash: str, preview_type: str = "thumbnail") -> str:
    """
    生成基于文件哈希的预览文件名
    
    使用文件SHA256哈希作为文件名，避免因路径/文件名变更导致重复生成
    
    Args:
        file_hash: 文件SHA256哈希
        preview_type: 预览类型
    
    Returns:
        预览文件名
    """
    # 使用文件哈希的前16位作为文件名
    hash_prefix = file_hash[:16]
    
    # 根据预览类型选择扩展名
    ext_map = {
        'thumbnail': '.jpg',
        'small': '.jpg',
        'medium': '.jpg',
        'large': '.jpg',
        'gif': '.gif',
        'video': '.mp4',
        'waveform': '.png'
    }
    
    ext = ext_map.get(preview_type, '.jpg')
    return f"{hash_prefix}{ext}"

def get_preview_path_by_hash(self, file_hash: str, preview_type: str = "thumbnail") -> str:
    """
    获取基于文件哈希的预览文件路径
    
    Args:
        file_hash: 文件SHA256哈希
        preview_type: 预览类型
    
    Returns:
        预览文件完整路径
    """
    filename = self.get_preview_filename(file_hash, preview_type)
    return os.path.join(self.config['cache_dir'], preview_type, filename)

def has_preview_by_hash(self, file_hash: str, preview_type: str = "thumbnail") -> bool:
    """
    检查是否存在基于文件哈希的预览
    
    Args:
        file_hash: 文件SHA256哈希
        preview_type: 预览类型
    
    Returns:
        是否存在预览
    """
    preview_path = self.get_preview_path_by_hash(file_hash, preview_type)
    return os.path.exists(preview_path)
```

**预览命名优势**：
- **避免重复生成**：相同内容的文件共享同一个预览文件
- **路径无关性**：文件移动或重命名不影响预览文件
- **缓存高效**：基于哈希的缓存管理更高效
- **存储优化**：减少重复预览文件的存储空间
- **去重支持**：与文件哈希去重机制完美配合

**开发测试指南**：
1. 测试不同类型媒体的预览生成
2. 测试预览质量和文件大小优化
3. 测试批量预览生成性能
4. 测试预览缓存管理
5. 测试预览格式兼容性
6. 测试基于文件哈希的预览命名策略
7. 测试预览去重和共享机制

#### 2.3.3 data/validators/file_validator.py - 文件验证器（新增）

**模块职责**：
- 验证文件完整性和有效性
- 检测文件格式和编码
- 提供文件安全检查
- 实现文件修复建议

**接口设计**：
```python
class FileValidator:
    def __init__(self, config: Dict[str, Any])
    def initialize(self) -> bool
    
    # 基础验证
    def validate_file_exists(self, file_path: str) -> bool
    def validate_file_readable(self, file_path: str) -> bool
    def validate_file_size(self, file_path: str, min_size: int = 0, max_size: int = None) -> bool
    def validate_file_extension(self, file_path: str, allowed_extensions: List[str]) -> bool
    
    # 格式验证
    def validate_image_format(self, image_path: str) -> Dict[str, Any]
    def validate_video_format(self, video_path: str) -> Dict[str, Any]
    def validate_audio_format(self, audio_path: str) -> Dict[str, Any]
    
    # 完整性验证
    def validate_file_integrity(self, file_path: str) -> Dict[str, Any]
    def validate_media_playability(self, media_path: str) -> Dict[str, Any]
    def detect_file_corruption(self, file_path: str) -> Dict[str, Any]
    
    # 安全检查
    def scan_for_malware(self, file_path: str) -> Dict[str, Any]
    def check_file_permissions(self, file_path: str) -> Dict[str, Any]
    def validate_file_metadata(self, file_path: str) -> Dict[str, Any]
    
    # 修复建议
    def suggest_file_repairs(self, file_path: str, issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]
    def attempt_file_repair(self, file_path: str, repair_type: str) -> Dict[str, Any]
    
    # 批量验证
    def batch_validate_files(self, file_paths: List[str]) -> Dict[str, Dict[str, Any]]
    def generate_validation_report(self, validation_results: Dict[str, Any]) -> str
```

**验证结果定义**：
```python
class ValidationResult:
    is_valid: bool                    # 是否有效
    file_path: str                   # 文件路径
    file_type: str                   # 文件类型
    issues: List[Dict[str, Any]]     # 发现的问题
    warnings: List[Dict[str, Any]]   # 警告信息
    suggestions: List[Dict[str, Any]] # 修复建议
    metadata: Dict[str, Any]         # 验证元数据
    validation_time: float           # 验证耗时
```

**开发测试指南**：
1. 测试各种文件格式的验证
2. 测试文件完整性检查
3. 测试安全扫描功能
4. 测试修复建议的准确性
5. 测试批量验证性能

#### 2.3.4 data/models/task_models.py - 任务模型（新增）

**模块职责**：
- 定义任务相关的数据模型
- 提供任务状态管理
- 实现任务序列化和反序列化
- 支持任务关系建模

**数据模型定义**：
```python
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
import uuid
from datetime import datetime

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"

class TaskPriority(Enum):
    LOW = 1
    NORMAL = 3
    HIGH = 5
    URGENT = 7
    CRITICAL = 9

class TaskType(Enum):
    FILE_SCAN = "file_scan"
    FILE_INDEX = "file_index"
    MEDIA_PROCESS = "media_process"
    VECTOR_EMBED = "vector_embed"
    THUMBNAIL_GENERATE = "thumbnail_generate"
    CACHE_CLEANUP = "cache_cleanup"

@dataclass
class Task:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_type: TaskType = TaskType.FILE_SCAN
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.NORMAL
    
    # 任务数据
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Optional[Dict[str, Any]] = None
    error_info: Optional[Dict[str, Any]] = None
    
    # 时间信息
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    updated_at: datetime = field(default_factory=datetime.now)
    
    # 执行信息
    retry_count: int = 0
    max_retries: int = 3
    progress: float = 0.0
    estimated_duration: Optional[float] = None
    
    # 依赖关系
    dependencies: List[str] = field(default_factory=list)
    dependents: List[str] = field(default_factory=list)
    
    # 资源需求
    resource_requirements: Dict[str, Any] = field(default_factory=dict)
    allocated_resources: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'task_type': self.task_type.value,
            'status': self.status.value,
            'priority': self.priority.value,
            'input_data': self.input_data,
            'output_data': self.output_data,
            'error_info': self.error_info,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'updated_at': self.updated_at.isoformat(),
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'progress': self.progress,
            'estimated_duration': self.estimated_duration,
            'dependencies': self.dependencies,
            'dependents': self.dependents,
            'resource_requirements': self.resource_requirements,
            'allocated_resources': self.allocated_resources
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """从字典创建任务对象"""
        task = cls()
        task.id = data.get('id', task.id)
        task.task_type = TaskType(data.get('task_type', TaskType.FILE_SCAN.value))
        task.status = TaskStatus(data.get('status', TaskStatus.PENDING.value))
        task.priority = TaskPriority(data.get('priority', TaskPriority.NORMAL.value))
        task.input_data = data.get('input_data', {})
        task.output_data = data.get('output_data')
        task.error_info = data.get('error_info')
        
        # 解析时间字段
        if data.get('created_at'):
            task.created_at = datetime.fromisoformat(data['created_at'])
        if data.get('started_at'):
            task.started_at = datetime.fromisoformat(data['started_at'])
        if data.get('completed_at'):
            task.completed_at = datetime.fromisoformat(data['completed_at'])
        if data.get('updated_at'):
            task.updated_at = datetime.fromisoformat(data['updated_at'])
        
        task.retry_count = data.get('retry_count', 0)
        task.max_retries = data.get('max_retries', 3)
        task.progress = data.get('progress', 0.0)
        task.estimated_duration = data.get('estimated_duration')
        task.dependencies = data.get('dependencies', [])
        task.dependents = data.get('dependents', [])
        task.resource_requirements = data.get('resource_requirements', {})
        task.allocated_resources = data.get('allocated_resources')
        
        return task

@dataclass
class TaskBatch:
    """任务批次模型"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    tasks: List[str] = field(default_factory=list)  # 任务ID列表
    created_at: datetime = field(default_factory=datetime.now)
    status: TaskStatus = TaskStatus.PENDING
    progress: float = 0.0
    
    def calculate_progress(self, task_statuses: Dict[str, TaskStatus]) -> float:
        """计算批次进度"""
        if not self.tasks:
            return 0.0
        
        completed_count = sum(1 for task_id in self.tasks 
                            if task_statuses.get(task_id) == TaskStatus.COMPLETED)
        return completed_count / len(self.tasks)

@dataclass
class TaskMetrics:
    """任务执行指标"""
    task_id: str
    execution_time: float
    memory_usage: float
    cpu_usage: float
    success_rate: float
    error_count: int
    retry_count: int
    throughput: float
    timestamp: datetime = field(default_factory=datetime.now)
```

**开发测试指南**：
1. 测试任务模型的序列化和反序列化
2. 测试任务状态转换逻辑
3. 测试任务依赖关系管理
4. 测试任务批次功能
5. 测试任务指标收集

### 2.4 用户界面层

#### 2.4.1 ui/components/search_panel.py - 搜索面板组件（新增）

**模块职责**：
- 提供统一的搜索界面组件
- 支持多模态查询输入
- 实现搜索历史和建议
- 提供高级搜索选项

**接口设计**：
```python
class SearchPanel(QWidget):
    # 信号定义
    search_requested = pyqtSignal(dict)  # 搜索请求信号
    query_changed = pyqtSignal(str)      # 查询变化信号
    
    def __init__(self, config: Dict[str, Any], parent: QWidget = None)
    def setup_ui(self) -> None
    
    # UI组件设置
    def setup_search_input(self) -> None
    def setup_search_buttons(self) -> None
    def setup_filter_options(self) -> None
    def setup_advanced_options(self) -> None
    
    # 搜索功能
    def set_query(self, query: str) -> None
    def get_query(self) -> str
    def clear_query(self) -> None
    def add_query_to_history(self, query: str) -> None
    
    # 多模态输入
    def handle_text_input(self, text: str) -> None
    def handle_image_drop(self, image_path: str) -> None
    def handle_audio_drop(self, audio_path: str) -> None
    def handle_video_drop(self, video_path: str) -> None
    
    # 搜索建议
    def show_search_suggestions(self, suggestions: List[str]) -> None
    def hide_search_suggestions(self) -> None
    def update_search_history(self, history: List[str]) -> None
    
    # 过滤选项
    def set_file_type_filter(self, file_types: List[str]) -> None
    def set_date_range_filter(self, start_date: QDate, end_date: QDate) -> None
    def set_similarity_threshold(self, threshold: float) -> None
    
    # 状态管理
    def set_search_enabled(self, enabled: bool) -> None
    def show_search_progress(self, progress: float) -> None
    def hide_search_progress(self) -> None
```

**UI组件结构**：
```python
class SearchPanelComponents:
    # 主搜索区域
    search_input: QLineEdit           # 搜索输入框
    search_button: QPushButton        # 搜索按钮
    voice_search_button: QPushButton  # 语音搜索按钮
    
    # 多模态输入区域
    image_drop_area: QLabel          # 图像拖放区域
    audio_drop_area: QLabel          # 音频拖放区域
    video_drop_area: QLabel          # 视频拖放区域
    
    # 过滤选项
    file_type_combo: QComboBox       # 文件类型选择
    date_range_widget: QDateRangeEdit # 日期范围选择
    similarity_slider: QSlider        # 相似度阈值滑块
    
    # 高级选项
    advanced_button: QPushButton      # 高级选项按钮
    advanced_panel: QWidget          # 高级选项面板
    
    # 搜索建议
    suggestions_list: QListWidget     # 搜索建议列表
    history_list: QListWidget        # 搜索历史列表
```

**开发测试指南**：
1. 测试各种输入方式的响应
2. 测试拖放功能的兼容性
3. 测试搜索建议和历史功能
4. 测试过滤选项的交互
5. 测试界面响应性和用户体验

#### 2.4.2 ui/components/result_panel.py - 结果面板组件

**模块职责**：
- 展示搜索结果
- 支持多种显示模式
- 提供结果交互功能
- 实现结果分页和排序

**接口设计**：
```python
class ResultPanel(QWidget):
    # 信号定义
    item_selected = pyqtSignal(dict)     # 项目选择信号
    item_double_clicked = pyqtSignal(dict) # 项目双击信号
    page_changed = pyqtSignal(int)       # 页面变化信号
    
    def __init__(self, config: Dict[str, Any], parent: QWidget = None)
    def setup_ui(self) -> None
    
    # 结果显示
    def display_results(self, results: List[Dict[str, Any]]) -> None
    def clear_results(self) -> None
    def update_result_count(self, count: int) -> None
    
    # 显示模式
    def set_view_mode(self, mode: str) -> None  # grid, list, detail
    def get_view_mode(self) -> str
    
    # 结果操作
    def select_result(self, index: int) -> None
    def get_selected_results(self) -> List[Dict[str, Any]]
    def export_results(self, format: str = "json") -> str
    
    # 分页功能
    def set_page_size(self, size: int) -> None
    def go_to_page(self, page: int) -> None
    def get_current_page(self) -> int
    def get_total_pages(self) -> int
    
    # 排序功能
    def sort_results(self, key: str, reverse: bool = False) -> None
    def get_sort_options(self) -> List[str]
    
    # 过滤功能
    def filter_results(self, filters: Dict[str, Any]) -> None
    def clear_filters(self) -> None
    
    # 预览功能
    def show_preview(self, result: Dict[str, Any]) -> None
    def hide_preview(self) -> None
    def toggle_preview_panel(self) -> None
```

**显示模式定义**：
```python
class ViewMode:
    GRID = "grid"           # 网格视图
    LIST = "list"           # 列表视图
    DETAIL = "detail"       # 详细视图
    TIMELINE = "timeline"   # 时间线视图
    THUMBNAIL = "thumbnail" # 缩略图视图
```

**结果项组件**：
```python
class ResultItem(QWidget):
    def __init__(self, result_data: Dict[str, Any], parent: QWidget = None)
    
    # UI设置
    def setup_thumbnail(self) -> None
    def setup_metadata(self) -> None
    def setup_actions(self) -> None
    
    # 数据更新
    def update_result_data(self, data: Dict[str, Any]) -> None
    def refresh_thumbnail(self) -> None
    def update_similarity_score(self, score: float) -> None
    
    # 交互功能
    def handle_click(self) -> None
    def handle_double_click(self) -> None
    def show_context_menu(self, position: QPoint) -> None
    
    # 状态管理
    def set_selected(self, selected: bool) -> None
    def set_highlighted(self, highlighted: bool) -> None
```

**开发测试指南**：
1. 测试不同显示模式的切换
2. 测试结果分页和排序功能
3. 测试结果选择和交互
4. 测试预览功能
5. 测试大量结果的性能

#### 2.4.3 ui/components/settings_panel.py - 设置面板组件（新增）

**模块职责**：
- 提供系统设置界面
- 管理用户偏好设置
- 支持配置实时预览
- 实现设置导入导出

**接口设计**：
```python
class SettingsPanel(QWidget):
    # 信号定义
    settings_changed = pyqtSignal(dict)  # 设置变化信号
    settings_applied = pyqtSignal()      # 设置应用信号
    
    def __init__(self, config: Dict[str, Any], parent: QWidget = None)
    def setup_ui(self) -> None
    
    # 设置分类
    def setup_general_settings(self) -> None
    def setup_search_settings(self) -> None
    def setup_model_settings(self) -> None
    def setup_performance_settings(self) -> None
    def setup_ui_settings(self) -> None
    
    # 设置管理
    def load_settings(self, settings: Dict[str, Any]) -> None
    def save_settings(self) -> Dict[str, Any]
    def reset_to_defaults(self) -> None
    def apply_settings(self) -> None
    
    # 导入导出
    def export_settings(self, file_path: str) -> bool
    def import_settings(self, file_path: str) -> bool
    
    # 验证功能
    def validate_settings(self) -> Tuple[bool, List[str]]
    def show_validation_errors(self, errors: List[str]) -> None
    
    # 预览功能
    def preview_changes(self) -> None
    def cancel_preview(self) -> None
```

**设置分类定义**：
```python
class SettingsCategory:
    GENERAL = "general"           # 常规设置
    SEARCH = "search"            # 搜索设置
    MODELS = "models"            # 模型设置
    PERFORMANCE = "performance"   # 性能设置
    UI = "ui"                    # 界面设置
    ADVANCED = "advanced"        # 高级设置
```

**开发测试指南**：
1. 测试各设置分类的功能
2. 测试设置验证和错误处理
3. 测试设置导入导出功能
4. 测试实时预览功能
5. 测试设置持久化

#### 2.4.4 ui/dialogs/progress_dialog.py - 进度对话框（新增）

**模块职责**：
- 显示长时间操作的进度
- 支持任务取消功能
- 提供详细的进度信息
- 实现进度动画效果

**接口设计**：
```python
class ProgressDialog(QDialog):
    # 信号定义
    cancelled = pyqtSignal()             # 取消信号
    details_requested = pyqtSignal()     # 详情请求信号
    
    def __init__(self, title: str = "Processing", parent: QWidget = None)
    def setup_ui(self) -> None
    
    # 进度控制
    def set_progress(self, value: int, maximum: int = 100) -> None
    def set_progress_text(self, text: str) -> None
    def set_detail_text(self, text: str) -> None
    def set_estimated_time(self, seconds: int) -> None
    
    # 状态管理
    def start_progress(self) -> None
    def finish_progress(self) -> None
    def pause_progress(self) -> None
    def resume_progress(self) -> None
    
    # 取消功能
    def set_cancellable(self, cancellable: bool) -> None
    def handle_cancel(self) -> None
    
    # 详情显示
    def show_details(self) -> None
    def hide_details(self) -> None
    def add_log_message(self, message: str, level: str = "info") -> None
    
    # 动画效果
    def start_spinner(self) -> None
    def stop_spinner(self) -> None
    def pulse_progress_bar(self) -> None
```

**进度类型定义**：
```python
class ProgressType:
    DETERMINATE = "determinate"     # 确定进度
    INDETERMINATE = "indeterminate" # 不确定进度
    PULSING = "pulsing"            # 脉冲进度
```

**开发测试指南**：
1. 测试不同类型进度的显示
2. 测试取消功能的响应
3. 测试详情面板的展开收缩
4. 测试动画效果的流畅性
5. 测试长时间操作的用户体验

### 2.5 API服务层（服务化预留）

#### 2.5.1 api/v1/dependencies.py - 依赖注入管理器

**模块职责**：
- 管理API依赖注入
- 提供服务实例创建和管理
- 实现依赖生命周期管理
- 支持依赖配置和切换

**接口设计**：
```python
class DependencyManager:
    def __init__(self, config: Dict[str, Any])
    def initialize(self) -> bool
    def shutdown(self) -> None
    
    # 服务创建
    def create_search_engine(self) -> SearchEngine
    def create_embedding_engine(self) -> EmbeddingEngine
    def create_task_manager(self) -> TaskManager
    def create_file_monitor(self) -> FileMonitor
    def create_data_access(self) -> UnifiedDataAccessLayer
    
    # 依赖管理
    def get_dependency(self, dependency_type: str) -> Any
    def register_dependency(self, dependency_type: str, instance: Any) -> None
    def unregister_dependency(self, dependency_type: str) -> None
    
    # 生命周期管理
    def start_services(self) -> None
    def stop_services(self) -> None
    def restart_service(self, service_type: str) -> None
    
    # 健康检查
    def check_dependencies_health(self) -> Dict[str, bool]
    def get_dependency_status(self, dependency_type: str) -> Dict[str, Any]

# FastAPI依赖函数
async def get_search_engine() -> SearchEngine:
    """获取搜索引擎实例"""
    return dependency_manager.get_dependency("search_engine")

async def get_embedding_engine() -> EmbeddingEngine:
    """获取向量化引擎实例"""
    return dependency_manager.get_dependency("embedding_engine")

async def get_task_manager() -> TaskManager:
    """获取任务管理器实例"""
    return dependency_manager.get_dependency("task_manager")

async def get_data_access() -> UnifiedDataAccessLayer:
    """获取数据访问层实例"""
    return dependency_manager.get_dependency("data_access")
```

**依赖类型定义**：
```python
class DependencyType:
    SEARCH_ENGINE = "search_engine"
    EMBEDDING_ENGINE = "embedding_engine"
    TASK_MANAGER = "task_manager"
    FILE_MONITOR = "file_monitor"
    DATA_ACCESS = "data_access"
    CACHE_MANAGER = "cache_manager"
    CONFIG_MANAGER = "config_manager"
```

**开发测试指南**：
1. 测试依赖创建和注册
2. 测试依赖生命周期管理
3. 测试健康检查功能
4. 测试依赖切换和重启
5. 测试FastAPI集成

#### 2.5.2 api/auth/auth_manager.py - 认证管理器（新增）

**模块职责**：
- 管理API认证和授权
- 支持多种认证方式
- 实现令牌管理
- 提供权限控制

**接口设计**：
```python
class AuthManager:
    def __init__(self, config: Dict[str, Any])
    def initialize(self) -> bool
    
    # 认证方法
    def authenticate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]
    def authenticate_jwt_token(self, token: str) -> Optional[Dict[str, Any]]
    def authenticate_basic_auth(self, username: str, password: str) -> Optional[Dict[str, Any]]
    
    # 令牌管理
    def generate_access_token(self, user_info: Dict[str, Any]) -> str
    def generate_refresh_token(self, user_info: Dict[str, Any]) -> str
    def refresh_access_token(self, refresh_token: str) -> Optional[str]
    def revoke_token(self, token: str) -> bool
    
    # 权限检查
    def check_permission(self, user_info: Dict[str, Any], resource: str, action: str) -> bool
    def get_user_permissions(self, user_info: Dict[str, Any]) -> List[str]
    
    # 用户管理
    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]
    def update_user(self, user_id: str, user_data: Dict[str, Any]) -> bool
    def delete_user(self, user_id: str) -> bool
    def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]

# FastAPI认证依赖
async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """获取当前用户信息"""
    user_info = auth_manager.authenticate_jwt_token(token)
    if not user_info:
        raise HTTPException(status_code=401, detail="Invalid authentication")
    return user_info

async def require_permission(permission: str):
    """权限检查装饰器"""
    def permission_checker(current_user: Dict[str, Any] = Depends(get_current_user)):
        if not auth_manager.check_permission(current_user, permission, "access"):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return permission_checker
```

**认证方式定义**：
```python
class AuthMethod:
    API_KEY = "api_key"         # API密钥认证
    JWT_TOKEN = "jwt_token"     # JWT令牌认证
    BASIC_AUTH = "basic_auth"   # 基础认证
    OAUTH2 = "oauth2"          # OAuth2认证
    NONE = "none"              # 无认证
```

**权限定义**：
```python
class Permission:
    SEARCH_READ = "search:read"           # 搜索读取权限
    SEARCH_WRITE = "search:write"         # 搜索写入权限
    FILE_READ = "file:read"               # 文件读取权限
    FILE_WRITE = "file:write"             # 文件写入权限
    TASK_READ = "task:read"               # 任务读取权限
    TASK_WRITE = "task:write"             # 任务写入权限
    SYSTEM_READ = "system:read"           # 系统读取权限
    SYSTEM_WRITE = "system:write"         # 系统写入权限
    ADMIN = "admin"                       # 管理员权限
```

**开发测试指南**：
1. 测试不同认证方式的实现
2. 测试令牌生成和验证
3. 测试权限检查机制
4. 测试用户管理功能
5. 测试FastAPI集成

#### 2.5.3 api/v1/schemas.py - API数据模型（优化）

**模块职责**：
- 定义API请求和响应模型
- 提供数据验证和序列化
- 实现模型转换和映射
- 支持API版本兼容性

**数据模型定义**：
```python
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum

# 基础模型
class BaseResponse(BaseModel):
    success: bool = True
    message: str = ""
    timestamp: datetime = Field(default_factory=datetime.now)
    request_id: Optional[str] = None

class PaginationRequest(BaseModel):
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页大小")
    
class PaginationResponse(BaseModel):
    page: int
    page_size: int
    total_count: int
    total_pages: int
    has_next: bool
    has_prev: bool

# 搜索相关模型
class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="搜索查询")
    modalities: Optional[List[str]] = Field(None, description="指定模态类型")
    file_types: Optional[List[str]] = Field(None, description="文件类型过滤")
    similarity_threshold: float = Field(0.7, ge=0.0, le=1.0, description="相似度阈值")
    limit: int = Field(20, ge=1, le=100, description="结果数量限制")
    ranking_strategy: str = Field("hybrid", description="排序策略")
    include_metadata: bool = Field(True, description="是否包含元数据")

class TextSearchRequest(SearchRequest):
    query_expansion: bool = Field(False, description="是否启用查询扩展")
    semantic_search: bool = Field(True, description="是否启用语义搜索")

class ImageSearchRequest(BaseModel):
    image_data: str = Field(..., description="Base64编码的图像数据")
    image_path: Optional[str] = Field(None, description="图像文件路径")
    similarity_threshold: float = Field(0.7, ge=0.0, le=1.0)
    limit: int = Field(20, ge=1, le=100)
    modalities: Optional[List[str]] = None

class AudioSearchRequest(BaseModel):
    audio_data: Optional[str] = Field(None, description="Base64编码的音频数据")
    audio_path: Optional[str] = Field(None, description="音频文件路径")
    audio_type: str = Field("auto", description="音频类型检测")
    similarity_threshold: float = Field(0.7, ge=0.0, le=1.0)
    limit: int = Field(20, ge=1, le=100)

class VideoSearchRequest(BaseModel):
    video_data: Optional[str] = Field(None, description="Base64编码的视频数据")
    video_path: Optional[str] = Field(None, description="视频文件路径")
    frame_sampling: str = Field("auto", description="帧采样策略")
    similarity_threshold: float = Field(0.7, ge=0.0, le=1.0)
    limit: int = Field(20, ge=1, le=100)

class MultimodalSearchRequest(BaseModel):
    queries: List[Dict[str, Any]] = Field(..., description="多模态查询列表")
    fusion_strategy: str = Field("weighted", description="融合策略")
    weights: Optional[Dict[str, float]] = Field(None, description="模态权重")
    limit: int = Field(20, ge=1, le=100)

# 搜索结果模型
class SearchResultItem(BaseModel):
    id: str
    file_id: str
    file_path: str
    file_name: str
    file_type: str
    similarity: float = Field(..., ge=0.0, le=1.0)
    modality: str
    segment_id: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    thumbnail_path: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

class SearchResponse(BaseResponse):
    results: List[SearchResultItem]
    total_count: int
    search_time: float
    query_info: Dict[str, Any]
    pagination: Optional[PaginationResponse] = None

# 任务相关模型
class TaskCreateRequest(BaseModel):
    task_type: str = Field(..., description="任务类型")
    input_data: Dict[str, Any] = Field(..., description="输入数据")
    priority: int = Field(3, ge=1, le=9, description="任务优先级")
    max_retries: int = Field(3, ge=0, le=10, description="最大重试次数")
    dependencies: List[str] = Field(default_factory=list, description="依赖任务ID")

class TaskResponse(BaseResponse):
    task_id: str
    task_type: str
    status: str
    priority: int
    progress: float = Field(..., ge=0.0, le=1.0)
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_duration: Optional[float] = None
    output_data: Optional[Dict[str, Any]] = None
    error_info: Optional[Dict[str, Any]] = None

class TaskListRequest(PaginationRequest):
    status_filter: Optional[str] = Field(None, description="状态过滤")
    task_type_filter: Optional[str] = Field(None, description="任务类型过滤")
    priority_filter: Optional[int] = Field(None, description="优先级过滤")

class TaskListResponse(BaseResponse):
    tasks: List[TaskResponse]
    pagination: PaginationResponse

# 文件相关模型
class FileInfo(BaseModel):
    id: str
    file_path: str
    file_name: str
    file_type: str
    file_size: int
    file_hash: str
    created_at: datetime
    modified_at: datetime
    processing_status: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class FileResponse(BaseResponse):
    file_info: FileInfo

class ScanRequest(BaseModel):
    directory_path: str = Field(..., description="扫描目录路径")
    recursive: bool = Field(True, description="是否递归扫描")
    file_types: Optional[List[str]] = Field(None, description="文件类型过滤")
    force_rescan: bool = Field(False, description="是否强制重新扫描")

class ScanResponse(BaseResponse):
    scan_id: str
    directory_path: str
    files_found: int
    files_processed: int
    scan_status: str
    started_at: datetime
    estimated_completion: Optional[datetime] = None

# 系统相关模型
class SystemStats(BaseModel):
    total_files: int
    indexed_files: int
    total_vectors: int
    database_size: int
    cache_size: int
    uptime: float
    cpu_usage: float
    memory_usage: float
    disk_usage: float

class SystemStatsResponse(BaseResponse):
    stats: SystemStats

class ModelInfo(BaseModel):
    model_type: str
    model_name: str
    model_status: str
    memory_usage: int
    device: str
    precision: str
    loaded_at: Optional[datetime] = None

class ModelsResponse(BaseResponse):
    models: List[ModelInfo]

class HardwareInfo(BaseModel):
    cpu_count: int
    cpu_name: str
    total_memory: int
    available_memory: int
    gpu_available: bool
    gpus: List[Dict[str, Any]]
    hardware_level: str
    recommended_models: Dict[str, Dict[str, Any]]

class HardwareInfoResponse(BaseResponse):
    hardware_info: HardwareInfo

# 错误响应模型
class ErrorResponse(BaseResponse):
    success: bool = False
    error_code: str
    error_details: Optional[Dict[str, Any]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "success": False,
                "message": "Validation error",
                "error_code": "VALIDATION_ERROR",
                "error_details": {
                    "field": "query",
                    "issue": "Field required"
                },
                "timestamp": "2024-01-01T00:00:00Z",
                "request_id": "req_123456"
            }
        }
```

**模型验证器**：
```python
class ModelValidators:
    @validator('file_types')
    def validate_file_types(cls, v):
        if v is not None:
            allowed_types = ['image', 'video', 'audio', 'document']
            for file_type in v:
                if file_type not in allowed_types:
                    raise ValueError(f'Invalid file type: {file_type}')
        return v
    
    @validator('modalities')
    def validate_modalities(cls, v):
        if v is not None:
            allowed_modalities = ['text', 'image', 'video', 'audio']
            for modality in v:
                if modality not in allowed_modalities:
                    raise ValueError(f'Invalid modality: {modality}')
        return v
```

**开发测试指南**：
1. 测试模型验证和序列化
2. 测试数据转换和映射
3. 测试错误处理和响应格式
4. 测试API版本兼容性
5. 测试模型文档生成

### 2.6 工具层

#### 2.6.1 core/config/config_validator.py - 配置验证器

**模块职责**：
- 验证配置文件格式和内容
- 检查配置项有效性和类型
- 验证配置值的范围和约束
- 提供详细的配置错误信息
- 支持配置schema验证

**接口设计**：
```python
class ConfigValidator:
    def __init__(config_schema: Optional[Dict[str, Any]] = None, schema_path: Optional[str] = None)
    def initialize(self) -> bool
    
    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, List[str]]
    def validate_config_type(self, key_path: str, value: Any, expected_type: Union[type, List[type]]) -> Tuple[bool, Optional[str]]
    def validate_config_range(self, key_path: str, value: Any, min_val: Any = None, max_val: Any = None) -> Tuple[bool, Optional[str]]
    def validate_config_path(self, key_path: str, path: str, exists: bool = True, is_dir: bool = False) -> Tuple[bool, Optional[str]]
    def validate_config_choice(self, key_path: str, value: Any, choices: List[Any]) -> Tuple[bool, Optional[str]]
    
    def load_schema(self, schema_path: str) -> bool
    def get_schema(self) -> Optional[Dict[str, Any]]
    def validate_schema(self, schema: Dict[str, Any]) -> Tuple[bool, List[str]]
```

**依赖注入**：
- 构造函数接收配置schema或schema文件路径
- 不依赖其他业务模块
- 支持JSON Schema验证

**开发测试指南**：
1. 测试配置验证功能
2. 测试类型检查和范围验证
3. 测试路径验证和文件存在性检查
4. 测试配置选项验证
5. 测试schema加载和验证
6. 测试详细错误信息生成

#### 2.6.2 utils/error_handling.py - 错误处理

**模块职责**：
- 定义统一的错误处理策略
- 提供错误分类和管理
- 实现错误日志记录和格式化
- 支持错误重试机制
- 提供错误恢复和降级策略
- 实现异常转换和包装

**接口设计**：
```python
# 自定义异常基类
class MSearchError(Exception):
    def __init__(self, message: str, error_code: str, context: Optional[Dict[str, Any]] = None)
        pass

# 错误处理类
class ErrorHandler:
    def __init__(config: Dict[str, Any])
    def initialize(self) -> bool
    
    def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> None
    def log_error(self, error: Exception, level: str = "ERROR", context: Optional[Dict[str, Any]] = None) -> None
    def format_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]
    
    def should_retry(self, error: Exception, attempt: int = 0) -> bool
    def get_retry_delay(self, error: Exception, attempt: int = 0) -> float
    def is_retryable_error(self, error: Exception) -> bool
    
    def convert_exception(self, exception: Exception, context: Optional[Dict[str, Any]] = None) -> MSearchError
    def get_error_code(self, exception: Exception) -> str
    
    def register_error_handler(self, exception_type: type, handler: Callable) -> None
    def unregister_error_handler(self, exception_type: type) -> None
```

**依赖注入**：
- 构造函数接收配置字典
- 不依赖其他业务模块
- 集成日志系统

**开发测试指南**：
1. 测试错误处理和日志记录
2. 测试不同类型异常的处理
3. 测试重试逻辑和延迟计算
4. 测试错误格式化和转换
5. 测试自定义错误处理注册
6. 测试异常包装和错误代码生成

### 2.7 开发工作流程

#### 2.7.1 单模块开发流程

1. **理解模块职责**：阅读设计文档，明确模块的核心职责和边界
2. **设计接口**：根据职责设计清晰的接口，定义输入输出和数据结构
3. **实现核心逻辑**：专注于核心功能，遵循单一职责原则，避免过度设计
4. **编写单元测试**：为每个接口编写测试用例，覆盖正常流程和异常情况
5. **集成测试**：在模拟环境中测试模块与其他模块的交互
6. **代码审查**：检查代码质量、设计一致性和遵循开发规范
7. **文档更新**：更新模块文档和设计文档（如果需要）

#### 2.7.2 MVP迭代策略

**第一阶段（MVP）**：
- 实现基本的文件索引和监控功能
- 集成MobileCLIP模型实现文本-图像检索
- 实现基本的用户界面
- 支持Windows、macOS和Linux平台

**第二阶段**：
- 添加音频检索功能（CLAP模型）
- 实现图像-图像检索
- 支持批量文件处理
- 优化检索性能

**第三阶段**：
- 添加视频检索功能（基于colpali-small模型，适配高配硬件）
- 实现视频分段功能（±5秒时间精度）
- 支持多模态融合检索
- 优化模型加载和推理性能

**第四阶段**：
- 添加人脸识别功能（可选）
- 实现高级搜索功能（过滤、排序、高级查询）
- 添加配置管理界面
- 实现性能监控和优化

**第五阶段**：
- 实现服务化架构（API模式）
- 支持分布式部署
- 优化大规模数据集处理
- 添加高级分析功能

---

## 第三部分：配置参数说明

### 3.1 系统配置

```yaml
system:
  debug: false                    # 调试模式开关
  data_dir: "data/"              # 数据存储目录
  log_level: "INFO"             # 日志级别
  check_interval: 5              # 健康检查间隔（秒）
  hardware_level: "auto"         # 硬件级别（auto/low/mid/high）
  auto_model_selection: true      # 是否自动选择模型

# 任务管理配置
task_manager:
  max_concurrent_tasks: 4        # 最大并发任务数
  max_retries: 3                 # 最大重试次数
  retry_delay: 1.0               # 重试延迟（秒）
  task_timeout: 300              # 任务超时时间（秒）
  enable_persistence: true       # 是否启用任务持久化
  persistence_file: "data/tasks/task_queue.json"  # 任务持久化文件
  
  # 任务类型并发限制
  max_concurrent_by_type:
    file_scan: 1                 # 文件扫描并发数
    file_embed: 2                # 向量化并发数
    video_slice: 2               # 视频切片并发数
    audio_segment: 2             # 音频分段并发数
  
  # 任务优先级配置
  task_priorities:
    file_scan: 0                 # 文件扫描优先级
    file_embed_image: 1          # 图像向量化优先级
    file_embed_video: 1          # 视频向量化优先级
    video_slice: 2               # 视频切片优先级
    file_embed_text: 3           # 文本向量化优先级
    audio_segment: 4             # 音频分段优先级
    file_embed_audio: 5          # 音频向量化优先级
    thumbnail_generate: 6        # 缩略图生成优先级
    preview_generate: 7          # 预览生成优先级
  
  # 资源限制
  resource_limits:
    max_memory_usage: 8589934592 # 最大内存使用（8GB）
    max_cpu_usage: 80            # 最大CPU使用率（%）
    max_gpu_usage: 90            # 最大GPU使用率（%）
```

### 3.2 数据库配置

```yaml
database:
  sqlite:
    path: "data/database/sqlite/msearch.db"     # SQLite数据库路径
    enable_wal: true                           # 是否启用WAL模式
  lancedb:
    data_dir: "data/database/lancedb"          # LanceDB数据目录
    index_type: "ivf_pq"                      # 索引类型
    num_partitions: 128                        # 索引分区数
```

### 3.3 模型配置

```yaml
models:
  cache_dir: "data/models"                     # 模型缓存目录
  
  # 统一的图像/视频向量化模型配置
  image_video_model:
    auto_select: true                          # 是否自动选择模型
    
    # 低配硬件模型（CPU友好）
    mobileclip:
      model_name: "apple/mobileclip"           # MobileCLIP模型名称/路径
      device: "auto"                           # 设备类型（cuda/cpu/auto）
      batch_size: 16                           # 批量大小
      precision: "float16"                     # 模型精度
      max_resolution: 224                      # 最大输入分辨率
      memory_requirement: "2GB"                # 内存需求
      enable_cache: true                       # 是否启用模型缓存
    
    # 中配硬件模型（平衡性能）
    colsmol_500m:
      model_name: "vidore/colSmol-500M"        # colSmol-500M模型名称/路径
      device: "auto"                           # 设备类型
      batch_size: 12                           # 批量大小
      precision: "float16"                     # 模型精度
      max_resolution: 336                      # 最大输入分辨率
      max_frames: 16                           # 视频最大帧数
      frame_interval: 2                        # 帧采样间隔
      memory_requirement: "4GB"                # 内存需求
      enable_cache: true                       # 是否启用模型缓存
    
    # 高配硬件模型（高性能）
    colqwen2_5_v0_2:
      model_name: "vidore/colqwen2.5-v0.2"     # colqwen2.5-v0.2模型名称/路径
      device: "auto"                           # 设备类型
      batch_size: 8                            # 批量大小
      precision: "float16"                     # 模型精度
      max_resolution: 448                      # 最大输入分辨率
      max_frames: 32                           # 视频最大帧数
      frame_interval: 1                        # 帧采样间隔
      memory_requirement: "8GB"                # 内存需求
      enable_cache: true                       # 是否启用模型缓存
  
  # 音频模型配置
  clap:
    model_name: "laion/clap-htsat-unfused"     # CLAP模型名称
    device: "auto"                             # 设备类型
    batch_size: 8                              # 批量大小
    precision: "float16"                       # 模型精度
    memory_requirement: "2GB"                  # 内存需求
  
  # 语音转文本模型配置
  whisper:
    model_name: "openai/whisper-base"          # Whisper模型名称
    device: "auto"                             # 设备类型
    precision: "float16"                       # 模型精度
    memory_requirement: "1GB"                  # 内存需求
  
  # 音频内容分类配置
  inaspeech_segmenter:
    model_name: "anasynth82/InaSpeechSegmenter"  # InaSpeechSegmenter模型名称
    device: "auto"                             # 设备类型
    enable_segmentation: true                  # 是否启用音频分段
    confidence_threshold: 0.7                   # 分类置信度阈值
    memory_requirement: "1GB"                  # 内存需求
  
  # 硬件自适应配置
  hardware_adaptive:
    enable_benchmarking: true                  # 是否启用性能基准测试
    benchmark_duration: 30                     # 基准测试时长（秒）
    auto_switch_threshold: 0.8                 # 自动切换阈值
    performance_monitoring: true               # 是否启用性能监控
  
  # 服务化配置（预留）
  service_mode:
    enabled: false                             # 是否启用服务化模式
    embedding_service_url: ""                  # 向量化服务URL
    preprocessing_service_url: ""              # 预处理服务URL
    vector_storage_service_url: ""             # 向量存储服务URL
    timeout: 30                                # 请求超时时间
    retry_count: 3                             # 重试次数
    
    # 服务化超高配模型（未来专用）
    colqwen_omni_v0_1:
      model_name: "vidore/colqwen-omni-v0.1"   # 服务化专用超高配模型
      device: "cuda"                           # 专用GPU设备
      batch_size: 4                            # 批量大小
      precision: "float16"                     # 模型精度
      max_resolution: 512                      # 最大输入分辨率
      max_frames: 64                           # 视频最大帧数
      memory_requirement: "16GB"               # 内存需求
```

### 3.4 检索配置

```yaml
search:
  max_results: 20                  # 最大返回结果数
  default_threshold: 0.7          # 默认相似度阈值
  top_n_per_modality: 50          # 各模态返回Top-N结果
  similarity_metric: "cosine"     # 相似度计算方式（cosine/dot/euclidean）
  result_fusion_method: "weighted" # 结果融合方式（weighted/rank/score）
```

### 3.5 媒体处理配置

```yaml
media:
  image:
    max_width: 2048              # 图像最大宽度
    max_height: 2048             # 图像最大高度
    thumbnail_size: 256          # 缩略图尺寸
  
  video:
    # 短视频快速处理配置
    short_video:
      enabled: true              # 是否启用短视频快速处理
      threshold: 6.0             # 短视频时长阈值（秒）
      very_short_threshold: 2.0  # 极短视频阈值（秒）
      short_segment_threshold: 4.0  # 短视频分段阈值（秒）
      very_short_frames: 1       # 极短视频提取帧数（≤2秒）
      short_frames: 2            # 短视频提取帧数（2-4秒）
      medium_short_frames: 3     # 中短视频提取帧数（4-6秒）
      frame_distribution: "uniform"  # 帧分布策略（uniform/smart）
    
    # 长视频场景检测配置
    segment:
      max_duration: 5.0           # 最大切片时长（秒），确保时间定位精度±5秒
      use_scene_detect: true     # 是否使用FFMPEG场景检测
      frames_per_scene: 1        # 每个场景提取的帧数
      scene_threshold: 0.3       # 场景变化阈值（0-1）
      min_segment_duration: 0.5  # 最小切片时长（秒）
      keyframe_strategy: "smart" # 关键帧提取策略（smart/uniform/first）
    
    # 超大视频处理配置
    large_video:
      size_threshold_gb: 3.0     # 超大视频文件大小阈值（GB）
      duration_threshold_min: 30.0  # 超大视频时长阈值（分钟）
      initial_duration: 300.0    # 初始处理时长（秒，5分钟）
      key_transitions: 10        # 提取的关键转场点数量
      batch_size: 600            # 后台批处理大小（秒，10分钟）
    
    # 缩略图配置
    thumbnail:
      time_offset: 0.3            # 缩略图提取时间偏移比例
      size: 256                   # 缩略图尺寸
  
  audio:
    sample_rate: 16000           # 音频采样率
    channels: 1                  # 音频通道数
    format: "wav"                # 音频格式
```

### 3.6 文件监控配置

```yaml
file_monitor:
  enabled: true                   # 是否启用文件监控
  watch_directories: []           # 监控目录列表
  recursive: true                 # 是否递归监控
  debounce_interval: 1000         # 防抖间隔（毫秒）
  ignore_patterns:                # 忽略文件模式
    - ".*"                        # 隐藏文件
    - "*.tmp"
    - "*.temp"
```

---

## 第四部分：部署和运维

### 4.1 安装流程

#### 4.1.1 自动安装

1. **运行安装脚本**：`./install.sh`
2. **硬件检测**：自动检测系统硬件配置（CPU/GPU/内存）
3. **依赖安装**：根据硬件配置安装相应的Python依赖和系统依赖
4. **模型预下载**：根据硬件配置自动下载推荐的AI模型
5. **配置初始化**：生成默认配置文件到`configs/`目录
6. **目录创建**：创建必要的数据目录结构

**硬件配置与模型映射**：
详见 [1.6.1 分级硬件自适应模型策略](#161-分级硬件自适应模型策略)

#### 4.1.2 手动安装

1. **安装系统依赖**：根据操作系统安装必要的系统依赖
2. **创建虚拟环境**：`python -m venv venv`
3. **激活虚拟环境**：`source venv/bin/activate`（Linux/macOS）或`venv\Scripts\activate`（Windows）
4. **选择安装模式**：
   - **纯CPU模式**：`pip install -r requirements-cpu.txt`
   - **GPU模式**：`pip install -r requirements-gpu.txt`
   - **完整模式**：`pip install -r requirements.txt`
5. **可选：安装开发依赖**：`pip install -r requirements-dev.txt`
6. **初始化配置**：`cp configs/default.yaml configs/config.yaml`
7. **下载模型**：运行`python src/utils/download_models.py --mode auto`

#### 4.1.3 离线安装包

**离线安装包结构**：
```
msearch-offline-package/
├── install.sh                    # 离线安装脚本
├── requirements/                 # 依赖文件目录
│   ├── requirements-cpu.txt      # 纯CPU依赖
│   ├── requirements-gpu.txt      # GPU依赖（含CUDA）
│   └── requirements.txt          # 完整依赖
├── wheels/                       # 预编译的wheel包
│   ├── cpu/                      # CPU版本wheel
│   └── gpu/                      # GPU版本wheel
├── models/                       # 预下载的模型文件
│   ├── mobileclip/               # 低配模型
│   ├── colsmol-500m/             # 中配模型
│   ├── colqwen2.5-v0.2/          # 高配模型
│   ├── clap-htsat-unfused/       # 音频模型
│   └── whisper/                  # 语音模型
├── configs/                      # 配置文件
│   ├── default.yaml
│   └── cpu-only.yaml             # 纯CPU配置模板
└── data/                         # 初始数据目录
```

**离线安装流程**：
```bash
# 1. 解压离线安装包
tar -xzf msearch-offline-package.tar.gz
cd msearch-offline-package

# 2. 运行离线安装脚本
./install.sh --offline --mode auto

# 3. 安装脚本自动执行：
#    - 检测硬件配置
#    - 从wheels/目录安装依赖（无需网络）
#    - 从models/目录复制模型文件（无需下载）
#    - 生成最优配置文件
```

**离线安装脚本核心逻辑**：
```python
def offline_install(hardware_level: str):
    # 1. 检测硬件
    hardware_info = detect_hardware()
    
    # 2. 选择依赖包
    if hardware_info['gpu_available']:
        install_from_wheels('wheels/gpu/')
    else:
        install_from_wheels('wheels/cpu/')
    
    # 3. 复制模型文件
    model_map = {
        'low': ['mobileclip', 'whisper-base'],
        'mid': ['colsmol-500m', 'whisper-small'],
        'high': ['colqwen2.5-v0.2', 'whisper-medium']
    }
    for model_name in model_map[hardware_level]:
        copy_model(f'models/{model_name}', 'data/models/')
    
    # 4. 生成配置
    generate_config(hardware_info)
```

#### 4.1.4 纯CPU模式安装

**CPU模式特点**：
- 不强制安装CUDA依赖
- 所有模型使用CPU推理
- 降低内存和磁盘需求
- 适合无GPU环境

**CPU模式依赖**：
```txt
# requirements-cpu.txt
torch>=2.0.0+cpu
torchvision>=0.15.0+cpu
transformers>=4.30.0
sentence-transformers>=2.2.0
lancedb>=0.5.0
ffmpeg-python>=0.2.0
pillow>=9.5.0
numpy>=1.24.0
pandas>=2.0.0
pyyaml>=6.0
fastapi>=0.100.0
uvicorn>=0.22.0
```

**CPU模式配置**：
```yaml
# configs/cpu-only.yaml
hardware:
  device: "cpu"
  precision: "float32"
  batch_size: 8
  max_workers: 2

models:
  image_video:
    model_name: "apple/mobileclip"
    device: "cpu"
    precision: "float32"
    batch_size: 8
  
  audio:
    model_name: "laion/clap-htsat-unfused"
    device: "cpu"
    precision: "float32"
    batch_size: 4
  
  speech:
    model_name: "openai/whisper-base"
    device: "cpu"
    precision: "float32"
```

#### 4.1.5 模型预下载策略

**预下载触发条件**：
1. 首次安装时自动触发
2. 硬件配置变更时重新下载
3. 手动运行下载脚本时

**预下载流程**：
```python
def download_models_by_hardware(hardware_info: Dict[str, Any]):
    # 1. 确定硬件级别
    hardware_level = determine_hardware_level(hardware_info)
    
    # 2. 获取推荐模型列表
    model_list = get_recommended_models(hardware_level)
    
    # 3. 检查本地缓存
    for model in model_list:
        if not model_exists_locally(model):
            download_model(model)
    
    # 4. 验证模型完整性
    validate_models(model_list)
    
    # 5. 更新配置文件
    update_config_with_models(model_list)
```

**下载优化**：
- 并行下载多个模型
- 支持断点续传
- 下载进度显示
- 自动重试机制
- 校验模型完整性

### 4.2 启动流程

1. **配置加载**：读取`configs/config.yaml`配置文件
2. **硬件检测**：检测系统硬件配置，自动选择合适的模型
3. **组件初始化**：按顺序初始化各个核心组件
4. **服务启动**：启动API服务和文件监控（如果启用）
5. **目录扫描**：扫描监控目录中已存在的文件（如果配置）
6. **UI启动**：启动用户界面（桌面应用模式）

### 4.3 运行模式

#### 4.3.1 桌面应用模式
```bash
# Linux/macOS
python src/main.py

# Windows
python src\main.py
```

#### 4.3.2 API服务模式（开发）
```bash
uvicorn src.api_server:app --host 0.0.0.0 --port 8000 --reload
```

#### 4.3.3 API服务模式（生产）
```bash
uvicorn src.api_server:app --host 0.0.0.0 --port 8000 --workers 4
```

#### 4.3.4 命令行模式
```bash
# 执行单次扫描
python src/utils/scan_directory.py --dir /path/to/media

# 执行搜索
python src/utils/search_cli.py --query "cat" --type text
```

### 4.4 监控和日志

#### 4.4.1 日志管理
- **日志级别**：DEBUG、INFO、WARN、ERROR
- **日志文件**：按模块分文件存储到`data/logs/`目录
- **日志轮转**：按大小（100MB）和时间（7天）轮转
- **日志格式**：JSON格式（生产）或文本格式（开发）

#### 4.4.2 性能监控
- **响应时间**：记录每个API请求的处理时间
- **资源使用**：监控CPU、内存、磁盘使用情况
- **错误率**：统计系统错误和崩溃率
- **模型性能**：记录模型推理时间和吞吐量
- **监控指标输出**：支持Prometheus格式指标输出

#### 4.4.3 健康检查
- **健康检查端点**：`/api/v1/system/health`
- **检查内容**：数据库连接、模型加载状态、磁盘空间
- **自动恢复**：部分组件支持自动恢复机制

### 4.5 配置管理

#### 4.5.1 配置文件
- **主配置文件**：`configs/config.yaml`
- **默认配置**：`configs/default.yaml`
- **配置schema**：`configs/schema.json`

#### 4.5.2 配置重载
- **动态重载**：支持运行时配置重载
- **重载命令**：通过API端点`/api/v1/system/reload-config`
- **重载机制**：安全重载，不影响正在运行的请求

### 4.6 模型管理

#### 4.6.1 模型下载
- **自动下载**：安装时自动下载推荐模型
- **手动下载**：使用`src/utils/download_models.py`脚本
- **模型缓存**：模型存储在`data/models/`目录

#### 4.6.2 模型切换
- **配置切换**：修改`configs/config.yaml`中的模型配置
- **动态切换**：支持运行时模型切换
- **模型验证**：切换前自动验证模型完整性

### 4.7 数据管理

#### 4.7.1 数据备份
- **备份命令**：`python src/utils/backup_data.py --output backup.zip`
- **备份内容**：数据库、配置文件、缩略图
- **自动备份**：支持配置自动定期备份

#### 4.7.2 数据恢复
- **恢复命令**：`python src/utils/restore_data.py --input backup.zip`
- **恢复验证**：恢复后自动验证数据完整性

#### 4.7.3 数据清理
- **清理命令**：`python src/utils/clean_data.py --older-than 30`
- **清理内容**：旧日志、临时文件、过期缩略图
- **自动清理**：支持配置自动定期清理

---

## 第五部分：测试策略

### 5.1 测试策略概述

遵循项目测试目录规范，采用分层测试策略，确保系统的质量和可靠性：

| 测试类型 | 测试范围 | 测试文件位置 | 命名规范 | 测试目标 |
|---------|---------|-------------|---------|---------|
| 单元测试 | 单个模块的独立功能 | `tests/unit/` | `test_*.py` | 验证模块内部逻辑正确性 |
| 集成测试 | 模块间的交互 | `tests/integration/` | `it_*.py` | 验证模块协同工作能力 |
| 端到端测试 | 完整用户流程 | `tests/e2e/` | `e2e_*.py` | 验证系统整体功能完整性 |
| 性能测试 | 系统性能指标 | `tests/benchmark/` | `*_benchmark.py` | 验证系统性能和扩展性 |

### 5.2 单元测试

#### 5.2.1 测试范围
- 核心组件层（config、database、vector、embedding等）
- 服务层（search、media、file等）
- 数据层（extractors、generators等）
- 工具层（error_handling、helpers等）

#### 5.2.2 测试策略
- **测试框架**：pytest
- **覆盖率目标**：核心模块90%以上，其他模块85%以上
- **测试隔离**：使用mock和fixture隔离依赖
- **测试模式**：Arrange-Act-Assert（AAA）模式
- **命名规范**：`test_功能点_预期行为`

#### 5.2.3 测试示例
```python
# tests/unit/core/embedding/test_embedding_engine.py
def test_embedding_engine_initialize_success(config):
    # Arrange
    engine = EmbeddingEngine(config)
    
    # Act
    result = engine.initialize()
    
    # Assert
    assert result is True
    assert engine.is_initialized
```

### 5.3 集成测试

#### 5.3.1 测试范围
- 核心组件间的交互（如EmbeddingEngine与VectorStore）
- 服务层与核心组件的交互（如SearchEngine与EmbeddingEngine）
- 数据库与向量存储的协同操作
- API接口与后端服务的集成

#### 5.3.2 测试策略
- **测试环境**：使用测试数据库和测试数据（位于`tests/data/`）
- **测试数据**：按业务域和版本组织，如`tests/data/msearch/v1/`
- **测试场景**：正常流程、异常流程、边界情况
- **命名规范**：`it_模块交互_预期行为`

#### 5.3.3 测试示例
```python
# tests/integration/search/test_search_engine_integration.py
def test_search_engine_integration_with_embedding(embedding_engine, vector_store, test_data):
    # Arrange
    data_access = UnifiedDataAccessLayer(None, vector_store)
    search_engine = SearchEngine(embedding_engine, data_access)
    
    # Act
    results = search_engine.search_by_text("test query", limit=5)
    
    # Assert
    assert isinstance(results, list)
    assert len(results) <= 5
```

### 5.4 端到端测试

#### 5.4.1 测试范围
- 完整的文件索引流程
- 多模态搜索功能
- 用户界面与后端服务的交互
- 不同运行模式的功能验证

#### 5.4.2 测试策略
- **测试环境**：模拟真实用户环境
- **测试工具**：pytest + 浏览器自动化工具（如Playwright/Selenium）
- **测试场景**：完整的用户操作流程
- **命名规范**：`e2e_功能流程_预期行为`

#### 5.4.3 测试示例
```python
# tests/e2e/test_full_search_flow.py
def test_full_search_flow(ui_launcher, test_media_files):
    # Arrange
    ui_launcher.start()
    
    # Act - 完整的搜索流程
    ui_launcher.add_directory(test_media_files.directory)
    ui_launcher.wait_for_indexing_complete()
    results = ui_launcher.search("cat")
    
    # Assert
    assert len(results) > 0
    assert all(result.similarity > 0.5 for result in results)
```

### 5.5 性能测试

#### 5.5.1 测试范围
- 向量化性能（不同模型和硬件配置）
- 搜索响应时间（不同数据规模）
- 内存使用和资源消耗
- 并发处理能力
- 大规模数据集处理性能

#### 5.5.2 测试策略
- **基准测试**：建立性能基线
- **压力测试**：测试系统极限
- **负载测试**：测试正常负载下的性能
- **命名规范**：`*_benchmark.py`

#### 5.5.3 测试示例
```python
# tests/benchmark/embedding_benchmark.py
def benchmark_embedding_performance(embedding_engine, test_images):
    # Arrange
    batch_sizes = [1, 4, 8, 16, 32]
    
    # Act & Assert
    for batch_size in batch_sizes:
        start_time = time.time()
        embedding_engine.embed_batch_images(test_images[:batch_size])
        duration = time.time() - start_time
        
        throughput = batch_size / duration
        assert throughput > expected_throughput[batch_size]
```

### 5.6 测试数据管理

#### 5.6.1 测试数据组织
```
tests/
├── data/                    # 测试数据目录
│   ├── msearch/            # 按项目组织
│   │   └── v1/             # 按版本组织
│   │       ├── images/     # 测试图片
│   │       ├── videos/     # 测试视频
│   │       ├── audio/      # 测试音频
│   │       └── configs/    # 测试配置
│   └── fixtures/           # 测试夹具
├── unit/                   # 单元测试
├── integration/            # 集成测试
├── e2e/                    # 端到端测试
├── benchmark/              # 性能测试
└── conf.d/                 # 测试配置
    └── pytest.ini
```

#### 5.6.2 测试配置
- 配置文件`pytest.ini`置于`tests/`目录

### 5.files):
    # Arrange
    ui = ui_launcher()
    
    # Act
    ui.add_watch_directory("/path/to/test/files")
    ui.wait_for_indexing_complete()
    results = ui.search("test image", search_type="text")
    
    # Assert
    assert len(results) > 0
    assert any("test" in result.file_name for result in results)
```

### 5.5 性能测试

#### 5.5.1 测试范围
- 模型推理性能
- 向量检索性能
- 文件索引吞吐量
- 系统资源使用情况

#### 5.5.2 测试策略
- **测试工具**：pytest-benchmark + 自定义性能测试脚本
- **测试数据**：大规模测试数据集（位于`tests/data/benchmark/`）
- **测试指标**：
  - 响应时间（P50、P95、P99）
  - 吞吐量（QPS）
  - 资源使用率（CPU、内存、GPU）
  - 模型推理延迟
- **报告格式**：生成`*.benchmark.json`和`*.benchmark.md`报告

#### 5.5.3 测试示例
```python
# tests/benchmark/test_embedding_performance.py
def test_embedding_performance(benchmark, embedding_engine, test_images):
    # Arrange
    def embed_images():
        for image_path in test_images:
            embedding_engine.embed_image(image_path)
    
    # Act & Assert
    benchmark(embed_images)
```

### 5.6 测试数据管理

#### 5.6.1 测试数据组织
```
tests/data/
├── msearch/              # 业务域
│   └── v1/              # 版本
│       ├── test_images/  # 测试图像
│       ├── test_videos/  # 测试视频
│       └── test_audio/   # 测试音频
└── benchmark/            # 性能测试数据
    └── large_dataset/    # 大规模测试数据集
```

#### 5.6.2 测试Fixtures
- 共享fixtures放在`tests/fixtures/`目录
- 按业务域拆分conftest.py，放在`tests/conf.d/`目录
- 配置文件`pytest.ini`置于`tests/`目录

### 5.7 测试执行和报告

#### 5.7.1 测试执行命令
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
pytest --cov=src --cov-report=html:tests/.coverage/html --cov-report=xml:tests/.coverage/coverage.xml --cov-report=csv:tests/.coverage/coverage.csv
```

#### 5.7.2 测试报告
- **覆盖率报告**：生成HTML、XML、CSV三种格式，位于`tests/.coverage/`目录
- **性能报告**：生成JSON和Markdown格式，位于`tests/benchmark/`目录
- **测试结果**：JUnit格式，用于CI/CD集成

### 5.8 CI/CD集成

- 每次代码提交自动运行单元测试和集成测试
- 每日构建运行完整测试套件
- 性能测试定期运行，监控系统性能变化
- 测试覆盖率低于目标值时构建失败
- 生成SonarQube兼容的XML覆盖率报告

---

## 第六部分：安全考虑

### 6.1 数据安全

#### 6.1.1 数据存储安全
- **本地存储**：所有数据（包括数据库、向量、模型和日志）完全存储在本地，不发送到任何远程服务器
- **文件权限**：严格设置文件和目录权限，确保只有授权用户可以访问
- **数据加密**：敏感配置和数据支持加密存储（可选）
- **数据备份**：支持手动和自动定期备份重要数据
- **数据恢复**：提供完整的数据恢复机制

#### 6.1.2 数据访问控制
- **最小权限原则**：进程运行时使用最小必要权限
- **文件系统访问限制**：仅访问用户明确指定的目录
- **数据库访问控制**：使用安全的数据库连接配置
- **敏感数据保护**：不在日志中记录敏感信息

### 6.2 系统安全

#### 6.2.1 输入验证和净化
- **全面输入验证**：所有用户输入、API请求和配置参数进行严格验证
- **路径遍历防护**：防止路径遍历攻击
- **SQL注入防护**：使用参数化查询和ORM框架
- **命令注入防护**：严格验证和净化外部命令参数

#### 6.2.2 错误处理和日志安全
- **安全错误处理**：不向用户暴露敏感错误信息
- **结构化日志记录**：使用结构化日志，便于分析和监控
- **日志脱敏**：自动脱敏日志中的敏感信息
- **日志访问控制**：限制日志文件的访问权限

#### 6.2.3 资源限制和防护
- **资源使用限制**：限制CPU、内存和磁盘使用
- **连接限制**：限制API请求频率和并发连接数
- **超时处理**：所有外部调用设置合理超时
- **异常恢复机制**：支持从异常状态自动恢复

### 6.3 模型安全

#### 6.3.1 模型下载和验证
- **安全模型下载**：从可信源下载模型，支持模型完整性验证
- **模型签名验证**：支持模型签名验证，防止模型篡改
- **模型隔离**：每个模型在独立环境中运行，防止模型间干扰

#### 6.3.2 模型推理安全
- **输入数据验证**：严格验证模型输入数据格式和内容
- **推理资源限制**：限制模型推理的资源使用
- **对抗样本防护**：实施基本的对抗样本防护措施

### 6.4 API安全

#### 6.4.1 API访问控制
- **API密钥认证**：支持API密钥认证（可选）
- **CORS配置**：严格配置CORS策略
- **请求限流**：实现API请求限流机制
- **HTTPS支持**：支持HTTPS协议（可选）

#### 6.4.2 API安全最佳实践
- **最小暴露原则**：仅暴露必要的API端点
- **请求验证**：验证所有API请求的参数和格式
- **响应净化**：净化API响应，不包含敏感信息
- **安全头部**：设置适当的安全HTTP头部

### 6.5 安装和更新安全

#### 6.5.1 安装安全
- **安全安装脚本**：安装脚本经过安全审查
- **依赖验证**：验证依赖包的完整性和签名
- **系统依赖检查**：检查系统依赖的安全性

#### 6.5.2 更新安全
- **安全更新机制**：支持安全的软件更新机制
- **更新验证**：验证更新包的完整性和签名
- **回滚机制**：支持更新失败时的回滚

### 6.6 安全审计和监控

#### 6.6.1 安全审计
- **审计日志**：记录所有安全相关事件
- **定期安全审计**：定期进行安全审计
- **漏洞扫描**：支持定期漏洞扫描

#### 6.6.2 安全监控
- **实时安全监控**：监控系统安全状态
- **异常检测**：检测异常行为和攻击模式
- **安全告警**：配置安全告警机制

---

## 第七部分：扩展性考虑

### 7.1 模块化设计

#### 7.1.1 组件化架构
- **松耦合设计**：各组件之间通过明确的接口通信，降低耦合度
- **插件式扩展**：支持通过插件机制扩展功能
- **可替换组件**：核心组件支持替换，便于技术栈升级

#### 7.1.2 服务化升级支持
- **API优先设计**：核心功能通过API暴露，便于未来服务化
- **服务发现支持**：预留服务发现机制，便于分布式部署
- **容器化支持**：支持Docker容器化部署
- **微服务架构预留**：设计考虑未来拆分为微服务的可能性

### 7.2 水平扩展

#### 7.2.1 多实例部署
- **无状态设计**：核心服务支持无状态部署，便于水平扩展
- **负载均衡**：支持API请求负载均衡
- **分布式任务调度**：支持分布式任务调度和执行
- **数据分片**：支持数据库和向量存储的数据分片

#### 7.2.2 分布式存储
- **分布式向量存储**：支持LanceDB或其他分布式向量数据库
- **共享存储支持**：支持NFS、S3等共享存储
- **数据一致性**：实现数据一致性保证机制

### 7.3 垂直扩展

#### 7.3.1 硬件扩展
- **GPU扩展**：支持多GPU并行处理
- **内存扩展**：支持大内存配置优化
- **存储扩展**：支持高性能存储设备

#### 7.3.2 模型扩展
- **模型升级**：支持无缝升级到更大、更先进的模型
- **多模型支持**：支持同时运行多个模型版本
- **模型并行**：支持模型并行和流水线并行

### 7.4 功能扩展

#### 7.4.1 新模态支持
- **模块化模态设计**：便于添加新的模态支持（如3D、文档等）
- **统一向量化接口**：新模态可复用现有向量化框架

#### 7.4.2 新功能插件
- **插件系统**：支持通过插件扩展功能
- **扩展点设计**：在关键位置设计扩展点
- **第三方集成**：支持与第三方工具和服务集成

### 7.5 性能扩展

#### 7.5.1 缓存优化
- **多级缓存设计**：支持内存缓存、磁盘缓存等多级缓存
- **智能缓存策略**：基于使用频率和访问模式的智能缓存
- **分布式缓存支持**：支持Redis等分布式缓存

#### 7.5.2 异步处理
- **异步API**：支持异步API设计
- **消息队列支持**：支持RabbitMQ、Kafka等消息队列
- **异步任务处理**：支持大规模异步任务处理

### 7.6 跨平台扩展

#### 7.6.1 多平台支持
- **跨平台设计**：支持Windows、macOS和Linux
- **平台特定优化**：针对不同平台进行特定优化
- **移动平台预留**：设计考虑未来移动平台支持

#### 7.6.2 多语言支持
- **API多语言客户端**：支持生成多种语言的API客户端
- **国际化支持**：支持多语言界面和文档

### 7.7 监控和管理扩展

#### 7.7.1 监控扩展
- **可扩展监控指标**：支持自定义监控指标
- **多种监控系统集成**：支持Prometheus、Grafana等监控系统
- **分布式跟踪**：支持OpenTelemetry等分布式跟踪系统

#### 7.7.2 管理扩展
- **配置中心支持**：支持Consul、etcd等配置中心
- **服务网格支持**：预留服务网格集成能力
- **自动化运维**：支持CI/CD自动化部署和运维

---

## 第八部分：维护和升级

### 8.1 日常维护

#### 8.1.1 日志管理
- **日志清理**：自动清理超过保留期的日志文件
- **日志压缩**：支持日志压缩存储，节省磁盘空间
- **日志分析**：提供日志分析工具和脚本
- **异常监控**：自动监控和告警关键错误日志

#### 8.1.2 数据管理
- **数据清理**：自动清理过期数据和临时文件
- **缓存优化**：定期优化缓存，提高访问性能
- **数据库维护**：定期进行数据库优化和备份
- **向量存储优化**：定期优化向量索引，提高检索性能

#### 8.1.3 系统监控
- **健康检查**：定期执行系统健康检查
- **性能监控**：监控系统性能指标
- **资源监控**：监控CPU、内存、磁盘等资源使用情况
- **告警机制**：配置关键指标告警

### 8.2 版本升级

#### 8.2.1 升级策略
- **语义化版本**：遵循语义化版本规范（MAJOR.MINOR.PATCH）
- **向后兼容**：尽量保持向后兼容性
- **升级文档**：提供详细的升级指南
- **回滚机制**：支持升级失败时的回滚

#### 8.2.2 配置迁移
- **配置版本管理**：支持配置文件版本管理
- **自动迁移工具**：提供配置自动迁移工具
- **配置验证**：迁移后自动验证配置完整性

#### 8.2.3 数据迁移
- **数据库迁移**：支持数据库结构和数据迁移
- **向量数据迁移**：支持向量数据的迁移和转换
- **迁移脚本**：提供自动迁移脚本
- **迁移验证**：迁移后自动验证数据完整性

#### 8.2.4 模型升级
- **模型版本管理**：支持多版本模型共存
- **模型迁移工具**：提供模型迁移工具
- **模型验证**：升级后自动验证模型功能

### 8.3 故障诊断和恢复

#### 8.3.1 故障诊断
- **诊断工具**：提供系统诊断工具
- **日志分析**：自动分析日志，定位故障原因
- **性能分析**：提供性能分析工具
- **监控告警**：实时监控系统状态，及时发现故障

#### 8.3.2 故障恢复
- **自动恢复**：部分组件支持自动恢复
- **恢复脚本**：提供故障恢复脚本
- **恢复指南**：提供详细的故障恢复指南
- **备份恢复**：支持从备份恢复系统

### 8.4 技术支持

#### 8.4.1 支持渠道
- **文档支持**：提供详细的用户文档和开发文档
- **社区支持**：建立用户社区，提供社区支持
- **商业支持**：提供商业支持选项（可选）

#### 8.4.2 问题反馈
- **反馈渠道**：提供多种问题反馈渠道
- **bug跟踪**：使用bug跟踪系统管理问题
- **版本发布**：定期发布版本，修复已知问题

### 8.5 安全更新

- **安全漏洞管理**：建立安全漏洞管理流程
- **紧急更新**：提供安全漏洞紧急更新机制
- **安全公告**：及时发布安全公告和更新指南
- **渗透测试**：定期进行安全渗透测试

---

## 附录

### A. 术语表

- **MSearch**：多模态检索系统，用于多媒体内容的智能检索
- **MobileCLIP**：苹果开发的轻量级CLIP模型，适配低配硬件，用于图像和视频向量化，详见 [1.6.1 分级硬件自适应模型策略](#161-分级硬件自适应模型策略)
- **colSmol-500M**：vidore开发的中等规模多模态模型，适配中配硬件，详见 [1.6.1 分级硬件自适应模型策略](#161-分级硬件自适应模型策略)
- **colqwen2.5-v0.2**：vidore开发的高性能多模态模型，适配高配硬件，详见 [1.6.1 分级硬件自适应模型策略](#161-分级硬件自适应模型策略)
- **colqwen-omni-v0.1**：vidore开发的超高性能全能模型，专用于服务化部署
- **CLAP**：Contrastive Language-Audio Pre-training，用于文本-音频检索，详见 [1.6.2 音频模型集成与分类策略](#162-音频模型集成与分类策略)
- **Whisper**：OpenAI的语音识别模型，用于语音转文本，详见 [1.6.2 音频模型集成与分类策略](#162-音频模型集成与分类策略)
- **InaSpeechSegmenter**：音频内容分类模型，用于区分音乐/语音，详见 [1.6.2 音频模型集成与分类策略](#162-音频模型集成与分类策略)
- **LanceDB**：高性能向量数据库，用于存储和检索向量嵌入，详见 [1.6.3 数据库技术选型](#163-数据库技术选型)
- **SQLite**：轻量级关系型数据库，用于元数据存储，详见 [1.6.3 数据库技术选型](#163-数据库技术选型)
- **MVP**：Minimum Viable Product，最小可行产品
- **向量嵌入**：多媒体内容在高维空间中的数值表示，用于相似度匹配
- **跨模态检索**：使用一种模态的查询检索另一种模态的内容
- **视频分段**：将视频按时间间隔分段，时间戳精度为±5秒，详见 [1.6.4 视频处理优化策略](#164-视频处理优化策略)
- **向量检索**：基于向量相似度的检索方法
- **API优先**：设计时优先考虑API接口，便于服务化和集成
- **服务化**：将系统功能以服务方式提供，支持网络访问和分布式部署
- **服务化预留**：为未来微服务化部署预留的API接口和架构设计
- **硬件自适应**：根据硬件配置自动选择最优模型和参数的机制，详见 [1.6.1 分级硬件自适应模型策略](#161-分级硬件自适应模型策略)
- **内容分析**：对媒体内容进行深度分析，提取语义和特征信息
- **任务调度**：智能分配和管理系统任务执行的机制
- **缓存策略**：优化数据访问性能的多级缓存管理策略

### B. 参考资料

- [LanceDB文档](https://lancedb.github.io/lance/)
- [FastAPI文档](https://fastapi.tiangolo.com/)
- [PySide6文档](https://doc.qt.io/qtforpython/6/)
- [Hugging Face Transformers](https://huggingface.co/docs/transformers/index)
- [PyTorch文档](https://pytorch.org/docs/stable/)
- [TensorFlow文档](https://www.tensorflow.org/api_docs)

### C. 国内镜像站使用方法

#### C.1 HuggingFace镜像站

HuggingFace是国内用户访问最困难的平台之一，使用镜像站可以大幅提升下载速度。

**使用方法：**

1. **安装依赖**
   ```bash
   pip install -U huggingface_hub
   ```

2. **设置环境变量**
   ```bash
   export HF_ENDPOINT=https://hf-mirror.com
   ```

   为了永久生效，可以将此命令添加到 `~/.bashrc` 或 `~/.zshrc` 文件中：
   ```bash
   echo 'export HF_ENDPOINT=https://hf-mirror.com' >> ~/.bashrc
   source ~/.bashrc
   ```

3. **下载模型**
   ```bash
   huggingface-cli download --resume-download --local-dir-use-symlinks False model_name --local-dir local_path
   ```

   **示例：**
   ```bash
   # 下载MobileCLIP模型
   huggingface-cli download --resume-download --local-dir-use-symlinks False apple/mobileclip-quickfer-16 --local-dir data/models/mobileclip
   
   # 下载Whisper模型
   huggingface-cli download --resume-download --local-dir-use-symlinks False openai/whisper-base --local-dir data/models/whisper
   
   # 下载CLAP模型
   huggingface-cli download --resume-download --local-dir-use-symlinks False laion/clap-htsat-unfused --local-dir data/models/clap
   ```

4. **需要登录的模型**
   
   对于需要登录才能下载的模型，添加 `--token` 参数：
   ```bash
   huggingface-cli download --resume-download --local-dir-use-symlinks False model_name --local-dir local_path --token hf_***
   ```

**在代码中使用：**

在Python代码中，也可以通过设置环境变量来使用镜像站：

```python
import os
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

from transformers import AutoModel, AutoTokenizer
model = AutoModel.from_pretrained('apple/mobileclip-quickfer-16')
```

#### C.2 GitHub镜像站

GitHub在国内访问速度较慢，使用镜像站可以加速克隆仓库。

**方法1：替换URL方式**

直接将GitHub URL替换为镜像站URL：

```bash
# 原始URL
git clone https://github.com/username/repository.git

# 使用镜像站
git clone https://gitclone.com/github.com/username/repository.git
```

**方法2：设置Git参数方式（推荐）**

全局设置Git使用镜像站：

```bash
git config --global url."https://gitclone.com/".insteadOf https://
```

设置后，所有 `git clone https://github.com/...` 命令都会自动使用镜像站。

**取消镜像站设置：**

```bash
git config --global --unset url."https://gitclone.com/".insteadOf
```

**方法3：使用cgit客户端**

```bash
cgit clone https://github.com/username/repository.git
```

**其他GitHub镜像站：**

- `https://github.com.cnpmjs.org/` - cnpmjs镜像
- `https://hub.fastgit.xyz/` - FastGit镜像
- `https://github.moeyy.xyz/` - Moeyy镜像

#### C.3 PyPI镜像源

PyPI是Python包的官方仓库，国内访问速度较慢，使用镜像源可以大幅提升下载速度。

**临时使用镜像源：**

在安装包时指定镜像源：

```bash
# 清华大学镜像
pip install package_name -i https://pypi.tuna.tsinghua.edu.cn/simple

# 阿里云镜像
pip install package_name -i https://mirrors.aliyun.com/pypi/simple

# 中科大镜像
pip install package_name -i https://pypi.mirrors.ustc.edu.cn/simple

# 豆瓣镜像
pip install package_name -i https://pypi.douban.com/simple

# 华为云镜像
pip install package_name -i https://repo.huaweicloud.com/repository/pypi/simple
```

**永久配置镜像源（推荐）：**

创建或修改 `~/.pip/pip.conf` 文件：

```ini
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
trusted-host = pypi.tuna.tsinghua.edu.cn
```

或使用阿里云镜像：

```ini
[global]
index-url = https://mirrors.aliyun.com/pypi/simple
trusted-host = mirrors.aliyun.com
```

**使用pip命令配置：**

```bash
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

**升级pip：**

```bash
pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
```

#### C.4 Windows安装脚本编码要求

在Windows系统中，批处理脚本（.bat文件）必须使用GBK编码，以确保中文字符能够正确显示。

**创建GBK编码的批处理脚本：**

1. **使用记事本创建**
   - 打开记事本
   - 输入脚本内容
   - 点击"文件" → "另存为"
   - 在"编码"下拉菜单中选择"ANSI"（即GBK编码）
   - 保存为.bat文件

2. **使用VS Code创建**
   - 打开VS Code
   - 创建新文件
   - 点击右下角的编码显示（如"UTF-8"）
   - 选择"通过编码保存"
   - 选择"GBK"或"Chinese Simplified (GBK)"
   - 保存为.bat文件

3. **使用Python创建GBK编码文件**

```python
# 创建GBK编码的批处理脚本
content = """
@echo off
echo 正在安装msearch...
pip install -r requirements.txt
echo 安装完成！
"""

with open('install.bat', 'w', encoding='gbk') as f:
    f.write(content)
```

**验证编码：**

```python
# 读取并验证编码
with open('install.bat', 'r', encoding='gbk') as f:
    print(f.read())
```

#### C.5 WebUI界面设计原则

为了提高开发效率和测试便捷性，项目采用"WebUI优先"的开发策略：

**设计原则：**

1. **快速验证功能**
   - 在开发核心功能时，优先使用WebUI进行功能验证
   - WebUI可以快速测试API接口的正确性
   - 避免在PySide6 UI开发上花费过多时间

2. **接口测试优先**
   - 通过WebUI测试所有API接口
   - 确保后端逻辑正确后再开发桌面UI
   - 减少UI开发与后端开发的耦合

3. **最后开发PySide6 UI**
   - 在所有核心功能、API接口、测试验证完成后
   - 最后才开发跨平台PySide6桌面UI
   - 此时后端已经稳定，UI开发更加顺畅

**实施策略：**

- **阶段1**: 开发核心模块 + WebUI测试
- **阶段2**: 完善API接口 + WebUI功能验证
- **阶段3**: 编写完整测试套件
- **阶段4**: 开发PySide6桌面UI

**WebUI优势：**

- 无需安装额外依赖
- 跨平台兼容性好
- 开发迭代速度快
- 便于远程访问和测试
- 可以快速验证API设计

#### C.6 技术编码要求

项目编码的技术要求必须遵守 `docs/technical_reference.md` 中的规定。

**核心编码规范：**

1. **代码风格**
   - 遵循PEP 8规范
   - 使用4个空格缩进
   - 行长度不超过88字符（Black默认）
   - 使用类型提示（Type Hints）

2. **命名规范**
   - 变量名：蛇形命名法（snake_case）
   - 类名：帕斯卡命名法（PascalCase）
   - 常量：全大写蛇形命名法（UPPER_SNAKE_CASE）
   - 私有成员：单下划线前缀（_private）

3. **注释规范**
   - 使用docstring注释函数和类
   - 复杂逻辑添加行内注释
   - 注释说明"为什么"而非"是什么"

4. **异常处理**
   - 使用自定义异常类
   - 捕获具体异常而非宽泛异常
   - 提供有意义的错误信息
   - 使用日志记录异常

5. **日志规范**
   - 使用标准logging模块
   - 根据严重程度选择日志级别
   - 关键操作必须记录日志
   - 敏感信息不要记录到日志

6. **测试规范**
   - 单元测试覆盖率不低于80%
   - 测试命名清晰描述测试意图
   - 使用pytest框架
   - 异步函数使用pytest-asyncio

7. **性能规范**
   - 避免不必要的循环嵌套
   - 合理使用生成器
   - 大数据量使用批量操作
   - 关键路径进行性能优化

**代码审查清单：**

- [ ] 代码符合PEP 8规范
- [ ] 所有公共函数都有类型提示
- [ ] 所有公共函数都有docstring
- [ ] 异常处理完整且合理
- [ ] 日志记录适当
- [ ] 没有硬编码的配置值
- [ ] 没有注释掉的代码
- [ ] 变量命名清晰有意义
- [ ] 函数职责单一
- [ ] 没有性能瓶颈

### D. 开发规范

- 代码风格：遵循PEP 8规范
- 命名规范：使用蛇形命名法
- 注释规范：使用docstring注释
- 类型提示：使用Python类型提示

### D. 版本历史
- v1.0.0：初始版本，实现基本功能
- v1.1.0：添加多模态检索
- v1.2.0：添加视频分段功能（±5秒时间精度）
- v2.0.0：重构架构，优化性能




## 预处理缓存与中间文件设计

系统在处理媒体文件过程中会产生大量中间文件和预处理结果，为了提高性能和避免重复处理，设计了完整的缓存管理机制。

### 1. 缓存目录结构

```
data/
├── cache/                  # 主缓存目录
│   ├── models/             # 模型缓存
│   ├── thumbnails/         # 缩略图缓存
│   ├── previews/           # 预览文件缓存
│   └── preprocessing/      # 预处理中间结果缓存
│       ├── frame_extraction/  # 视频帧提取结果
│       ├── audio_segments/    # 音频分段结果
│       ├── video_slices/      # 视频切片结果
│       └── text_embeddings/   # 文本向量化结果
```

### 2. 缓存管理组件

#### 2.1 PreprocessingCache 类

```python
class PreprocessingCache:
    """
    预处理缓存管理器
    
    负责管理预处理过程中产生的中间文件和缓存
    """
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.cache_dir = os.path.join(config['cache_dir'], 'preprocessing')
        self.max_cache_size = config.get('preprocessing', {}).get('max_cache_size', 5 * 1024 * 1024 * 1024)  # 5GB
        self.cache_ttl = config.get('preprocessing', {}).get('cache_ttl', 7 * 24 * 3600)  # 7天
    
    def get_cache_path(self, file_id: str, cache_type: str) -> str:
        """
        获取缓存文件路径
        
        Args:
            file_id: 文件ID（UUID v4）
            cache_type: 缓存类型（frame_extraction, audio_segments, etc.）
        
        Returns:
            缓存文件路径
        """
        cache_subdir = os.path.join(self.cache_dir, cache_type)
        os.makedirs(cache_subdir, exist_ok=True)
        return os.path.join(cache_subdir, f"{file_id}.json")
    
    def save_cache(self, file_id: str, cache_type: str, data: Any) -> bool:
        """
        保存缓存数据
        
        Args:
            file_id: 文件ID（UUID v4）
            cache_type: 缓存类型
            data: 缓存数据
        
        Returns:
            是否保存成功
        """
        try:
            cache_path = self.get_cache_path(file_id, cache_type)
            with open(cache_path, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
            return False
    
    def load_cache(self, file_id: str, cache_type: str) -> Optional[Any]:
        """
        加载缓存数据
        
        Args:
            file_id: 文件ID（UUID v4）
            cache_type: 缓存类型
        
        Returns:
            缓存数据
        """
        try:
            cache_path = self.get_cache_path(file_id, cache_type)
            if os.path.exists(cache_path):
                # 检查缓存是否过期
                if time.time() - os.path.getmtime(cache_path) > self.cache_ttl:
                    self.delete_cache(file_id, cache_type)
                    return None
                
                with open(cache_path, 'r') as f:
                    return json.load(f)
            return None
        except Exception as e:
            logger.error(f"Failed to load cache: {e}")
            return None
    
    def delete_cache(self, file_id: str, cache_type: Optional[str] = None) -> bool:
        """
        删除缓存数据
        
        Args:
            file_id: 文件ID（UUID v4）
            cache_type: 缓存类型（None表示删除所有类型）
        
        Returns:
            是否删除成功
        """
        try:
            if cache_type:
                # 删除特定类型的缓存
                cache_path = self.get_cache_path(file_id, cache_type)
                if os.path.exists(cache_path):
                    os.remove(cache_path)
            else:
                # 删除所有类型的缓存
                for cache_type in ['frame_extraction', 'audio_segments', 'video_slices', 'text_embeddings']:
                    cache_path = self.get_cache_path(file_id, cache_type)
                    if os.path.exists(cache_path):
                        os.remove(cache_path)
            return True
        except Exception as e:
            logger.error(f"Failed to delete cache: {e}")
            return False
    
    def cleanup_expired_cache(self) -> int:
        """
        清理过期缓存
        
        Returns:
            清理的缓存文件数量
        """
        try:
            count = 0
            current_time = time.time()
            
            for root, dirs, files in os.walk(self.cache_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    if current_time - os.path.getmtime(file_path) > self.cache_ttl:
                        os.remove(file_path)
                        count += 1
            
            return count
        except Exception as e:
            logger.error(f"Failed to cleanup expired cache: {e}")
            return 0
    
    def cleanup_by_size(self) -> int:
        """
        按大小清理缓存
        
        Returns:
            清理的缓存文件数量
        """
        try:
            # 计算当前缓存大小
            total_size = 0
            cache_files = []
            
            for root, dirs, files in os.walk(self.cache_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    file_size = os.path.getsize(file_path)
                    total_size += file_size
                    cache_files.append((file_path, file_size, os.path.getmtime(file_path)))
            
            # 如果缓存大小超过限制，按时间排序并删除最旧的文件
            count = 0
            if total_size > self.max_cache_size:
                # 按修改时间排序（最旧的先删除）
                cache_files.sort(key=lambda x: x[2])
                
                while total_size > self.max_cache_size and cache_files:
                    file_path, file_size, mtime = cache_files.pop(0)
                    os.remove(file_path)
                    total_size -= file_size
                    count += 1
            
            return count
        except Exception as e:
            logger.error(f"Failed to cleanup cache by size: {e}")
            return 0
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            缓存统计信息
        """
        try:
            total_size = 0
            file_count = 0
            type_counts = {}
            
            for root, dirs, files in os.walk(self.cache_dir):
                cache_type = os.path.basename(root)
                if cache_type == 'preprocessing':
                    continue
                
                type_counts[cache_type] = len(files)
                file_count += len(files)
                
                for file in files:
                    file_path = os.path.join(root, file)
                    total_size += os.path.getsize(file_path)
            
            return {
                'total_size': total_size,
                'file_count': file_count,
                'type_counts': type_counts,
                'max_cache_size': self.max_cache_size,
                'cache_ttl': self.cache_ttl
            }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {}
```

### 3. 缓存使用流程

#### 3.1 视频处理缓存流程

```python
def process_video(self, video_path: str) -> List[Dict[str, Any]]:
    """
    处理视频文件
    
    Args:
        video_path: 视频文件路径
    
    Returns:
        处理结果
    """
    # 1. 获取文件ID
    file_info = self.database_manager.get_or_create_file(video_path)
    file_id = file_info['id']
    
    # 2. 检查缓存
    cached_result = self.preprocessing_cache.load_cache(file_id, 'frame_extraction')
    if cached_result:
        logger.info(f"Using cached result for video {video_path}")
        return cached_result
    
    # 3. 执行实际处理
    # ... 视频处理逻辑 ...
    result = processed_segments
    
    # 4. 保存缓存
    self.preprocessing_cache.save_cache(file_id, 'frame_extraction', result)
    
    return result
```

### 4. 缓存清理策略

系统采用两种缓存清理策略：

1. **按时间清理**：
   - 默认缓存有效期为7天
   - 定期（每天）清理过期缓存
   - 支持手动触发清理

2. **按大小清理**：
   - 默认最大缓存大小为5GB
   - 当缓存大小超过限制时，按时间顺序删除最旧的文件
   - 支持配置最大缓存大小

3. **关联性清理**：
   - 当原始文件被删除时，自动清理相关缓存
   - 当原始文件被修改时，自动清理旧缓存
   - 定期验证缓存文件与原始文件的关联性

### 5. 中间文件管理

除了缓存文件外，系统还会产生一些临时中间文件，这些文件会被自动管理：

1. **临时文件目录**：`{cache_dir}/tmp/`
2. **自动清理**：程序退出时自动清理临时文件
3. **定期清理**：每小时清理一次临时文件
4. **最大生命周期**：临时文件最大生命周期为24小时

### 6. 缓存配置参数

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `cache_dir` | `data/cache` | 主缓存目录 |
| `preprocessing.max_cache_size` | `5GB` | 预处理缓存最大大小 |
| `preprocessing.cache_ttl` | `7天` | 预处理缓存有效期 |
| `preprocessing.cleanup_interval` | `3600` | 缓存清理间隔（秒） |
| `preprocessing.enable_cache` | `true` | 是否启用预处理缓存 |

### 7. 开发测试指南

1. **测试缓存功能**：
   - 测试缓存的保存和加载功能
   - 测试缓存过期清理功能
   - 测试缓存大小限制功能

2. **测试中间文件管理**：
   - 测试临时文件的自动清理
   - 测试程序异常退出时的临时文件清理

3. **性能测试**：
   - 测试缓存对处理性能的提升
   - 测试缓存清理对系统性能的影响

4. **边界测试**：
   - 测试空文件的缓存处理
   - 测试超大文件的缓存处理
   - 测试频繁修改文件的缓存处理

通过以上设计，系统实现了高效、可靠的预处理缓存和中间文件管理机制，能够显著提高系统性能，减少重复处理，同时保持系统的稳定性和可靠性。
