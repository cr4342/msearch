# msearch 项目上下文文档

## 项目概述

msearch 是一款单机可运行的跨平台多模态桌面检索软件，专为视频剪辑师设计，实现素材无需整理、无需标签的智能检索。系统采用Python原生集成AI模型的方式，支持文本、图像、视频、音频四种模态的精准检索，通过实时监控和增量处理，为视频剪辑师提供高效、安全的多媒体内容检索体验。

### 核心特性

- **智能检索**: 无需手动整理、无需添加标签即可实现智能检索
- **跨模态搜索**: 支持用任意模态（文本、图像、音频）检索其他模态内容
- **高精度定位**: 支持视频片段级检索，时间戳精度±5秒
- **零配置**: 素材无需整理、无需标签
- **高性能本地推理**: Python原生集成AI模型，无需额外服务引擎
- **硬件自适应**: 根据硬件配置自动选择最优模型（低/中/高配）
- **单机运行**: 完全本地化，无需网络依赖
- **后端前端分离**: API服务与UI界面分离，便于扩展

### 技术栈

- **语言**: Python 3.8+
- **AI推理**: Python原生集成（直接模型调用、GPU自动调度）
- **图像/视频向量化**: 硬件自适应模型策略
  - 低配硬件: apple/mobileclip（轻量级，CPU友好）
  - 中配硬件: vidore/colSmol-500M（平衡性能）
  - 高配硬件: vidore/colqwen2.5-v0.2（高性能）
- **语音识别**: OpenAI Whisper（语音转文本）
- **音频检索**: CLAP模型（文本-音乐检索）
- **音频分类**: InaSpeechSegmenter（区分音乐/语音/噪音）
- **向量存储**: LanceDB（高性能本地向量数据库）
- **元数据存储**: SQLite（轻量级关系数据库）
- **任务管理**: persist-queue + SQLite（线程安全、磁盘持久化）
- **Web框架**: FastAPI（异步API服务）
- **GUI框架**: PySide6（跨平台桌面应用，开发中）
- **WebUI**: 原生HTML/CSS/JavaScript（快速验证界面）
- **媒体处理**: FFmpeg, OpenCV, Librosa（专业级预处理）
- **文件监控**: Watchdog（实时增量处理）
- **配置管理**: YAML + 环境变量（配置驱动、支持热重载）
- **日志系统**: Python logging（多级别日志、自动轮转）

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
- **EmbeddingEngine**: 统一管理AI模型调用（硬件自适应模型、Whisper、CLAP）
- **VectorStore**: 专注于LanceDB向量数据库操作（统一向量表设计）

#### 辅助组件
- **FileScanner**: 系统启动时的初始文件扫描
- **FileMonitor**: 实时监控文件变化（基于watchdog）
- **MediaProcessor**: 智能视频预处理（场景分割、切片向量化）
- **SearchEngine**: 多模态检索功能
- **DatabaseManager**: SQLite元数据库管理
- **HardwareDetector**: 硬件配置检测
- **ConfigManager**: 配置管理器

#### API层组件
- **APIServer**: FastAPI服务主入口
- **APIRoutes**: 定义所有API路由
- **APIHandlers**: 处理API业务逻辑
- **APISchemas**: 定义API数据模型

#### 用户界面
- **WebUI**: 原生HTML/CSS/JavaScript界面（webui/index.html），用于快速功能验证
- **PySide6 UI**: 跨平台桌面应用（开发中）

## 项目结构

```
msearch/
├── IFLOW.md                 # 项目上下文文档
├── requirements.txt         # Python依赖
├── config/
│   └── config.yml          # 主配置文件
├── data/
│   ├── database/           # 数据库文件
│   │   ├── sqlite/         # SQLite数据库
│   │   └── lancedb/        # LanceDB向量数据库
│   ├── logs/               # 日志文件
│   │   ├── application.log
│   │   ├── error.log
│   │   ├── performance.log
│   │   └── timestamp.log
│   ├── models/             # AI模型文件
│   │   ├── mobileclip/     # MobileCLIP模型
│   │   ├── colsmol/        # colSmol-500M模型
│   │   ├── colqwen/        # colqwen2.5-v0.2模型
│   │   ├── clap/           # CLAP模型
│   │   ├── whisper/        # Whisper模型
│   │   └── inaspeech/      # InaSpeechSegmenter模型
│   └── cache/              # 缓存目录
├── docs/                   # 文档目录（待补充）
├── tests/                  # 测试文件
│   ├── unit/               # 单元测试
│   │   ├── core/           # 核心组件测试
│   │   ├── data/           # 数据层测试
│   │   ├── services/       # 服务层测试
│   │   ├── ui/             # UI测试
│   │   └── utils/          # 工具层测试
│   ├── integration/        # 集成测试（待实现）
│   └── e2e/               # 端到端测试（待实现）
├── webui/                  # Web界面
│   └── index.html          # WebUI主界面
├── testdata/               # 测试数据
│   ├── audio/              # 测试音频
│   └── faces/              # 测试人脸图片
├── .kiro/                  # 项目规范
│   └── specs/
│       └── multimodal-search-system/
│           ├── requirements.md  # 需求文档
│           ├── design.md        # 设计文档
│           └── tasks.md         # 任务列表
└── src/                    # 源代码目录（待实现）
```

## 工作流程

### 文件处理流程
```
系统启动 → 初始扫描 → 任务创建 → 任务队列 → 媒体预处理 → 向量化 → 存储
    │          │           │           │          │          │        │
  (FileScanner) (TaskManager) (persist-queue) (MediaProcessor) (EmbeddingEngine) (VectorStore)
```

### 检索流程
```
用户查询 → 查询向量化 → 统一搜索 → 结果丰富 → 结果聚合/去重 → 返回结果
    │           │           │          │          │
 (UI/API) (EmbeddingEngine) (UDAL) (DatabaseManager) (SearchEngine)
```

### API调用流程
```
HTTP请求 → FastAPI路由 → API处理器 → 业务逻辑 → 统一数据访问层 → 数据库/向量存储 → 响应
    │           │            │           │              │              │         │
  (验证)    (分发)      (处理)    (协调)        (查询)      (存储)   (格式化)
```

## 专业AI模型架构

### 硬件自适应图像/视频向量化模型

系统根据硬件配置自动选择最优模型：

1. **apple/mobileclip**（轻量级模型）
   - 应用场景：低配硬件环境（CPU核心2-4，内存4-8GB，GPU显存0-2GB）
   - 向量维度：512维
   - 硬件要求：适配CPU和低端GPU，显存占用低（约2GB）
   - 批处理大小：16

2. **vidore/colSmol-500M**（平衡型模型）
   - 应用场景：中配硬件环境（CPU核心4-8，内存8-16GB，GPU显存2-6GB）
   - 向量维度：512维
   - 硬件要求：适用于中端GPU，提供较好的性能与资源平衡（约4GB）
   - 批处理大小：12

3. **vidore/colqwen2.5-v0.2**（高性能模型）
   - 应用场景：高配硬件环境（CPU核心8+，内存16GB+，GPU显存6GB+）
   - 向量维度：512维
   - 硬件要求：适用于高端GPU，提供最佳性能（约8GB）
   - 批处理大小：8

4. **vidore/colqwen-omni-v0.1**（服务化超高配）
   - 应用场景：专用服务器部署（服务化预留）
   - 向量维度：512维
   - 硬件要求：专用GPU服务器（约16GB）
   - 批处理大小：4

### 其他AI模型

- **Whisper**: 语音-文本转换（高精度多语言语音识别）
- **CLAP**: 文本-音乐检索（高质量文本-音乐匹配）
- **InaSpeechSegmenter**: 音频内容智能分类（精准区分音乐、语音、噪音）

## 配置管理

系统使用 `config/config.yml` 进行配置，支持以下主要配置项：

- **system**: 系统级别配置（日志级别、最大工作线程数、健康检查间隔）
- **monitoring**: 监控配置（监控目录、检查间隔、防抖延迟）
- **processing**: 媒体处理配置（图像、视频、音频处理参数）
- **models**: AI模型配置（模型选择、缓存目录、模型预热）
  - clip_model: 图像/视频向量化模型名称
  - clap_model: CLAP模型名称
  - whisper_model: Whisper模型名称
- **database**: 数据库配置（SQLite路径、Milvus Lite路径、向量索引参数）
- **retry**: 重试策略配置（初始延迟、重试倍数、最大重试次数）
- **logging**: 日志配置（日志级别、格式、轮转策略）
- **api**: API服务配置（主机、端口、CORS、速率限制）

## 智能媒体预处理

### 视频预处理策略

- **场景分割**: 使用FFmpeg场景检测将视频分割为片段
- **切片限制**: 最大切片时长120秒
- **分辨率优化**: 短边超过960像素时自动调整
- **格式转换**: 转换为H.264 MP4格式（仅用于索引）
- **音频处理**: 使用InaSpeechSegmenter分类音频内容
- **超大视频处理**: 超过3GB或30分钟的视频优先处理开头5分钟

### 图像预处理策略

- **分辨率限制**: 长边不超过2048像素
- **格式转换**: 转换为RGB格式
- **缩略图生成**: 自动生成缩略图用于UI显示

### 音频预处理策略

- **重采样**: 重采样为16kHz单声道64kbps AAC格式
- **内容分类**: 使用InaSpeechSegmenter区分音乐和语音
- **音乐处理**: 使用CLAP模型生成向量嵌入
- **语音处理**: 使用Whisper模型进行转录

## 部署和运行

### 环境要求
- Python 3.8+
- 支持CUDA的GPU（推荐，用于加速AI推理）
- 至少8GB内存（推荐16GB+）
- 至少10GB可用存储空间

### 安装依赖
```bash
pip install -r requirements.txt
```

### 启动应用
```bash
# 启动完整应用（待实现）
python src/main.py

# 仅启动API服务（待实现）
python src/api_server.py

# 启动桌面UI（待实现）
python src/ui/ui_launcher.py
```

### 使用WebUI
1. 启动API服务后，在浏览器中打开 `webui/index.html`
2. 选择搜索类型（文本/图像/音频）
3. 输入查询或上传文件
4. 查看搜索结果

## 性能要求

- **检索响应**: ≤2秒返回前20个结果
- **视频定位精度**: ±5秒
- **并发处理**: 支持4+个并发任务
- **内存使用**: 模型加载后≤4GB
- **系统稳定性**: 崩溃率低于0.1%

## 开发实践

### 代码规范
- 使用类型注解（Type Hints）
- 遵循PEP 8代码风格
- 使用异步编程（async/await）
- 完善的错误处理和日志记录
- 遵循独立性原则和单一职责原则

### 测试策略
- 单元测试：测试各个模块的核心功能
- 集成测试：测试模块间的协作
- 端到端测试：测试完整的用户流程
- 性能测试：测试系统性能指标

### 测试工具
- pytest: 测试框架
- pytest-asyncio: 异步测试支持
- pytest-cov: 代码覆盖率
- pytest-benchmark: 性能测试

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

### HuggingFace镜像站
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

## 项目状态

### 已完成
- [x] 项目需求文档（requirements.md）
- [x] 项目设计文档（design.md）
- [x] 项目任务列表（tasks.md）
- [x] 配置文件（config/config.yml）
- [x] 依赖文件（requirements.txt）
- [x] WebUI界面（webui/index.html）
- [x] 测试目录结构

### 进行中
- [ ] 核心模块实现（TaskManager、EmbeddingEngine、VectorStore）
- [ ] 辅助组件实现
- [ ] API接口实现
- [ ] 单元测试编写

### 待开发
- [ ] 集成测试
- [ ] 端到端测试
- [ ] 部署脚本
- [ ] PySide6桌面UI
- [ ] 用户文档
- [ ] API文档

---

*最后更新: 2026-01-10*
*架构: TaskManager + EmbeddingEngine + VectorStore + 辅助组件 + API层*
*状态: 设计阶段完成，开发进行中*