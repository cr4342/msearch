# msearch 项目上下文文档

## 项目概述

msearch 是一款跨平台的多模态检索系统，采用单体架构设计，专注于单机桌面应用场景。系统使用 michaelfeil/infinity 作为多模型服务引擎，支持文本、图像、视频、音频四种模态的精准检索，特别集成了人脸识别与人名检索融合机制。

### 核心特性

- **智能检索**: 无需手动整理、无需添加标签即可实现智能检索
- **跨模态搜索**: 支持用任意模态（文本、图像、音频）检索其他模态内容
- **高精度定位**: 支持毫秒级时间戳精确定位，时间戳精度±2秒要求
- **零配置**: 素材无需整理、无需标签
- **高性能本地推理**: 利用Infinity Python-native模式实现高效向量化
- **单体架构**: 简洁清晰的模块划分，易于理解和维护
- **人脸识别**: 支持人脸检测、识别以及基于人名的智能检索
- **完整API**: 提供全面的RESTful API接口，支持多模态搜索、任务管理、系统监控等功能

### 技术栈

- **语言**: Python 3.8+
- **向量化引擎**: infinity-emb[all]
- **向量数据库**: Milvus Lite
- **关系数据库**: SQLite
- **Web框架**: FastAPI
- **媒体处理**: FFmpeg, Librosa, OpenCV
- **文件监控**: Watchdog
- **任务队列**: persist-queue
- **人脸识别**: FaceNet/MTCNN
- **GUI框架**: PySide6
- **API文档**: OpenAPI/Swagger
- **数据验证**: Pydantic

## 架构设计

### 3大核心块架构

项目采用分层架构，通过统一数据访问层简化组件间依赖：

```
┌─────────────────────────────────────────────────────────┐
│                   主应用程序 (main.py)                    │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ 任务管理器   │  │ 向量化引擎   │  │ 向量存储     │ │
│  │ TaskManager  │  │EmbeddingEngine│ │ VectorStore  │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                        检索引擎                          │
├─────────────────────────────────────────────────────────┤
│                统一数据访问层 (UDAL)                     │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────┐                    ┌──────────────┐ │
│  │ 向量存储     │                    │ 数据库管理   │ │
│  │ VectorStore  │                    │ DatabaseMgmt │ │
│  └──────────────┘                    └──────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### 模块职责

#### 核心模块
- **TaskManager**: 任务进度跟踪和状态管理，使用persist-queue持久化任务
- **EmbeddingEngine**: 统一管理AI模型调用（CLIP/CLAP/Whisper/CLIP4Clip/FaceNet），现在通过infinity-emb进行Python-native模式集成
- **VectorStore**: 专注于Milvus Lite向量数据库操作
- **FaceManager**: 专门处理人脸检测、特征提取和人名关联

#### 统一数据访问层
- **UnifiedDataAccessLayer**: 协调向量检索和元数据查询，提供统一接口，支持人脸特征检索

#### 服务层组件
- **FileScanner**: 系统启动时的初始文件扫描
- **FileMonitor**: 实时监控文件变化（基于watchdog）
- **MediaProcessor**: 智能视频预处理
- **SearchEngine**: 多模态检索功能，集成人脸识别与人名检索融合机制

#### API层组件
- **APIServer**: FastAPI服务主入口
- **APIRoutes**: 定义所有API路由
- **APIHandlers**: 处理API业务逻辑
- **APISchemas**: 定义API数据模型

### 详细模块结构

```
src/
├── main.py              # 应用入口
├── api_server.py        # API服务入口
├── core/                # 核心功能模块
│   ├── config_manager.py        # 配置管理
│   ├── embedding_engine.py      # 向量化引擎
│   ├── vector_store.py          # 向量存储
│   ├── task_manager.py          # 任务管理
│   ├── database_adapter_optimized.py # 数据库适配器
│   ├── infinity_manager.py      # Infinity引擎管理
│   ├── retry.py                 # 重试机制
│   ├── performance_monitor.py   # 性能监控
│   ├── cache_manager.py         # 缓存管理
│   ├── batch_processor.py       # 批量处理器
│   ├── hardware/                # 硬件相关模块
│   ├── embedding/               # 向量化相关模块
│   ├── config/                  # 配置管理模块
│   ├── vector/                  # 向量存储模块
│   ├── task/                    # 任务管理模块
│   └── database/                # 数据库相关模块
├── services/            # 服务层模块
│   ├── file_services/           # 文件服务
│   ├── media_services/          # 媒体服务
│   ├── search_services/         # 搜索服务
│   ├── face_services/           # 人脸识别服务
│   ├── file/                    # 文件相关模块
│   ├── media/                   # 媒体相关模块
│   └── search/                  # 搜索相关模块
├── api/                 # API层
│   ├── handlers.py      # API处理器
│   ├── routes.py        # API路由
│   ├── schemas.py       # API数据模型
│   └── ...
├── ui/                  # 用户界面
│   ├── main_window.py   # 主窗口
│   └── ui_launcher.py   # UI启动器
└── utils/               # 工具类
```

## 项目结构

```
msearch/
├── IFLOW.md                 # 项目上下文文档
├── README.md                # 项目说明
├── requirements.txt         # Python依赖
├── config/
│   └── config.yml          # 主配置文件
├── data/
│   ├── database/           # 数据库文件
│   ├── models/             # AI模型文件
│   ├── logs/               # 日志文件
│   └── cache/              # 缓存数据
├── docs/                   # 文档
│   ├── api_documentation.md # API文档
│   ├── architecture.md     # 架构设计
│   ├── database.md         # 数据库设计
│   ├── deployment.md       # 部署文档
│   ├── extensibility.md    # 扩展性文档
│   ├── performance.md      # 性能文档
│   ├── security.md         # 安全文档
│   ├── technical_implementation.md # 技术实现
│   ├── test_strategy.md    # 测试策略
│   └── user_manual.md      # 用户手册
├── logs/                   # 运行时日志
├── scripts/                # 实用脚本
│   ├── install.sh          # Linux安装脚本
│   ├── install_windows.py  # Windows安装脚本
│   ├── download_models_only.py # 模型下载脚本
│   ├── start_all.sh        # 启动脚本
│   ├── stop_all.sh         # 停止脚本
│   ├── hardware_analysis.py # 硬件分析脚本
│   ├── linux/              # Linux专用脚本
│   ├── utils/              # 实用工具脚本
│   └── maintain_database.py # 数据库维护脚本
├── src/                    # 源代码
│   ├── main.py             # 应用入口
│   ├── api_server.py       # API服务入口
│   ├── core/               # 核心功能
│   │   ├── config_manager.py
│   │   ├── database_manager.py
│   │   ├── embedding_engine.py  # 已更新为使用infinity-emb
│   │   ├── hardware_detector.py # 硬件检测器
│   │   ├── infinity_manager.py  # Infinity管理器
│   │   ├── logging_config.py
│   │   ├── retry.py
│   │   ├── task_manager.py
│   │   ├── unified_data_access.py
│   │   ├── vector_store.py
│   │   ├── batch_processor.py
│   │   ├── cache_manager.py
│   │   ├── performance_monitor.py
│   │   └── ...
│   ├── services/           # 服务层
│   │   ├── face_services/  # 人脸识别服务
│   │   ├── file_services/  # 文件服务
│   │   ├── media_services/ # 媒体服务
│   │   └── search_services/ # 搜索服务
│   ├── api/                # API层
│   │   ├── handlers.py     # API处理器
│   │   ├── routes.py       # API路由
│   │   ├── schemas.py      # API数据模型
│   │   └── ...
│   ├── ui/                 # 用户界面
│   │   ├── main_window.py  # 主窗口
│   │   └── ui_launcher.py  # UI启动器
│   └── utils/              # 工具类
│       ├── config_validator.py
│       ├── error_handling.py
│       └── exceptions.py
├── webui/                  # Web界面
│   └── index.html
├── tests/                  # 测试文件
├── storage/                # 存储目录（Milvus集合数据）
└── temp/                   # 临时文件目录
```

## Infinity-emb集成架构

### Python-native模式集成

项目现在使用infinity-emb进行Python-native模式集成，取代了直接使用transformers库的方式：

- **EmbeddingEngine**: 现在通过InfinityManager调用infinity-emb引擎
- **InfinityManager**: 管理CLIP、CLAP、Whisper等模型的infinity-emb实例
- **向量化流程**: 所有向量化请求通过infinity-emb进行，提高性能和一致性

### 模型管理

- **CLIP模型**: 用于文本-图像/视频检索
- **CLAP模型**: 用于文本-音乐检索
- **Whisper模型**: 用于语音转文本检索
- **FaceNet模型**: 用于人脸识别（可选）

## 向量存储架构

### 统一向量表设计

项目采用统一向量表设计，将不同模态的向量存储在统一的表中，提高查询效率和管理便利性：

- **unified_vectors**: 统一向量表，支持多种模态（image, video, audio, text, face）
- **字段包含**: vector_id, file_uuid, segment_id, modality, vector, metadata等
- **索引优化**: 针对不同查询场景进行索引优化

### 模态类型
- **image**: 图像向量
- **video**: 视频向量
- **audio**: 音频向量
- **text**: 文本向量
- **face**: 人脸向量

## 人脸识别与人名检索融合机制

### 核心功能
- **人名检测**: 当用户检索词包含和人名完全一致的人名时，系统自动激活人脸识别检索
- **人脸特征提取**: 基于FaceNet模型提取人脸特征向量，生成标准化的人脸嵌入
- **权重调整**: 系统将人脸模态的检索权重提高1.5到2.0倍，同时适当降低其他模态的权重
- **结果融合**: 将人脸特征匹配结果与其他模态检索结果按调整后的权重进行加权融合

### 实现细节
1. **人名识别**: 检测查询中是否包含已注册的人名
2. **人脸检索**: 调用人脸特征库检索对应的人脸特征向量
3. **权重调整**: 人脸结果权重×1.8，其他结果权重×0.8
4. **结果融合**: 合并并重新排序结果

## 工作流程

### 文件处理流程
```
系统启动 → 初始扫描 → 任务创建 → 任务队列 → 媒体预处理 → 向量化 → 存储
    │          │           │           │          │          │        │
  (FileScanner) (TaskManager) (persist-queue) (MediaProcessor) (EmbeddingEngine) (VectorStore)
```

### 检索流程
```
用户查询 → 查询向量化 → 统一搜索 → 人名检测 → 人脸检索 → 结果丰富 → 结果聚合/去重 → 返回结果
    │           │           │          │          │          │          │
 (UI/API) (EmbeddingEngine) (UDAL) (SearchEngine) (FaceManager) (DatabaseManager) (SearchEngine) (UI/API)
```

### API调用流程
```
HTTP请求 → FastAPI路由 → API处理器 → 业务逻辑 → 统一数据访问层 → 数据库/向量存储 → 响应
    │           │            │           │              │              │         │
  (验证)    (分发)      (处理)    (协调)        (查询)      (存储)   (格式化)
```

## 部署和运行

### 环境要求
- Python 3.8+
- 支持CUDA的GPU（推荐，用于加速AI推理）
- 至少8GB内存（推荐16GB+，模型加载需要大量内存）
- 至少10GB可用存储空间（模型文件和数据库）

### 安装依赖
```bash
pip install -r requirements.txt
# 或使用分离的依赖文件
pip install -r requirements_core.txt
pip install -r requirements_dev.txt  # 开发依赖
```

### 启动应用
```bash
# 启动完整应用
python src/main.py

# 仅启动API服务
python src/api_server.py

# 启动桌面UI
python src/ui/ui_launcher.py
```

### 配置管理
系统使用 `config/config.yml` 进行配置，支持以下主要配置项：
- `system`: 系统级别配置
- `models`: AI模型配置
- `database`: 数据库配置（包括Milvus Lite和SQLite）
- `processing`: 媒体处理配置
- `retry`: 重试策略配置
- `face_recognition`: 人脸识别配置
- `api`: API服务配置

## 性能要求
- **检索响应**: ≤2秒返回前20个结果
- **视频定位精度**: ±2秒（相比原设计的±5秒有所提升）
- **人脸识别**: ≤3秒返回人脸匹配结果
- **API响应**: ≤1秒返回API响应
- **并发处理**: 支持4+个并发任务
- **内存使用**: 模型加载后≤4GB

## API特色功能

### 多模态融合搜索
支持文本、图像、音频的组合搜索，通过权重调整实现最优结果融合。

### 人脸与人名检索融合
当检测到人名查询时，自动激活人脸识别模块，提供更精确的检索结果。

### 时间线搜索
支持按时间范围搜索媒体内容，提供精确的时间戳定位。

### 批量操作
支持批量文件处理、批量搜索等操作，提高处理效率。

## 新增功能和改进

### 2026-01-07 更新
- **infinity-emb集成**: EmbeddingEngine已更新为使用infinity-emb进行Python-native模式集成
- **InfinityManager**: 新增Infinity管理器，专门管理infinity-emb引擎实例
- **统一向量表**: VectorStore支持统一向量表设计
- **人脸识别**: 新增人脸识别与人名检索融合机制
- **性能优化**: 通过infinity-emb提高了向量化性能
- **模块化改进**: 改进了组件间的依赖关系，使架构更清晰

### 脚本增强
- **硬件检测**: 新增`scripts/hardware_analysis.py`用于检测系统硬件
- **数据库维护**: 新增`scripts/maintain_database.py`用于数据库维护
- **启动脚本**: 新增`scripts/start_all.sh`和`scripts/stop_all.sh`用于一键启动/停止
- **模型下载**: 新增`scripts/download_models_only.py`用于快速下载模型

## 开发约定

### 代码规范
- 遵循Python PEP 8编码规范
- 使用类型注解提高代码可读性
- 模块化设计，单一职责原则
- 统一错误处理机制
- 结构化日志记录

### 配置管理
- 使用YAML格式配置文件
- 配置驱动设计，无硬编码参数
- 支持环境变量覆盖
- 配置热重载支持

### 测试策略
- 单元测试覆盖核心功能
- 集成测试验证模块间协作
- 性能测试确保系统响应时间
- 端到端测试验证用户流程

## 扩展性设计

### 模块化架构
- 低耦合设计，便于功能扩展
- 接口抽象，支持不同的实现
- 配置驱动，支持动态功能切换

### 服务化预留
- 为未来服务化架构预留接口
- 支持分布式部署选项
- 模块可独立部署和扩展

---
*最后更新: 2026-01-09*
*统一数据访问层架构: TaskManager + EmbeddingEngine + VectorStore + FaceManager + UnifiedDataAccessLayer + API层*