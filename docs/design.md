# msearch 多模态搜索系统设计文档

## 目录

1. [第一部分：整体架构设计](#第一部分整体架构设计)
   - [1.1 项目概述](#11-项目概述)
   - [1.2 核心设计原则](#12-核心设计原则)
   - [1.3 系统架构图](#13-系统架构图)
   - [1.4 技术栈选型](#14-技术栈选型)
   - [1.5 数据流转总览](#15-数据流转总览)
   - [1.6 多进程架构设计](#16-多进程架构设计)

2. [第二部分：核心组件设计](#第二部分核心组件设计)
   - [2.1 配置管理系统](#21-配置管理系统)
   - [2.2 模型管理系统](#22-模型管理系统)
   - [2.3 文件扫描系统](#23-文件扫描系统)
   - [2.4 数据处理系统](#24-数据处理系统)
   - [2.5 任务管理系统](#25-任务管理系统)
   - [2.6 向量化引擎](#26-向量化引擎)
   - [2.7 向量存储系统](#27-向量存储系统)
   - [2.8 检索引擎](#28-检索引擎)
   - [2.9 WebUI 系统](#29-webui-系统)
   - [2.10 桌面 UI 系统](#210-桌面-ui-系统)

3. [第三部分：详细流程设计](#第三部分详细流程设计)
   - [3.1 数据处理流程](#31-数据处理流程)
   - [3.2 检索流程](#32-检索流程)
   - [3.3 任务调度流程](#33-任务调度流程)
   - [3.4 目录监控流程](#34-目录监控流程)

4. [第四部分：性能优化设计](#第四部分性能优化设计)
   - [4.1 内存管理](#41-内存管理)
   - [4.2 并行处理](#42-并行处理)
   - [4.3 缓存策略](#43-缓存策略)
   - [4.4 资源监控](#44-资源监控)

5. [第五部分：部署与运维](#第五部分部署与运维)
   - [5.1 安装流程](#51-安装流程)
   - [5.2 配置说明](#52-配置说明)
   - [5.3 离线模式](#53-离线模式)
   - [5.4 故障排查](#54-故障排查)

6. [第六部分：进程间通信设计](#第六部分进程间通信设计)
   - [6.1 进程边界划分](#61-进程边界划分)
   - [6.2 进程间通信机制](#62-进程间通信机制)
   - [6.3 进程接口定义](#63-进程接口定义)
   - [6.4 进程生命周期管理](#64-进程生命周期管理)

7. [第七部分：服务化演进（参考）](#第七部分服务化演进参考)
   - [7.1 演进路线图](#71-演进路线图)
   - [7.2 演进原则](#72-演进原则)

8. [第八部分：测试与质量](#第八部分测试与质量)
   - [8.1 测试策略](#81-测试策略)
   - [8.2 性能基准](#82-性能基准)
   - [8.3 质量标准](#83-质量标准)

---

## 相关文档索引

| 文档 | 说明 | 关联章节 |
|------|------|----------|
| [data_flow.md](./data_flow.md) | 数据流转详细设计 | 1.5, 3.1 |
| [file_scanner_design_refinement.md](./file_scanner_design_refinement.md) | 文件扫描器详细设计 | 2.3 |
| [pyside6_ui_design.md](./pyside6_ui_design.md) | 桌面UI详细设计 | 2.10 |
| [deployment.md](./deployment.md) | 部署与运维详细指南 | 5.0 |
| [requirements.md](./requirements.md) | 需求文档 | 1.1 |
| [INFINITY_MEMORY_MANAGEMENT.md](./INFINITY_MEMORY_MANAGEMENT.md) | Infinity内存管理 | 2.2, 4.1 |
| [INFINITY_MODEL_MANAGEMENT.md](./INFINITY_MODEL_MANAGEMENT.md) | Infinity模型管理 | 2.2 |

---

# 第一部分：整体架构设计

## 1.1 项目概述

msearch 是一款单机可运行的跨平台多模态桌面检索软件，专为视频剪辑师设计，实现素材无需整理、无需标签的智能检索。

**核心目标**：
- 提供跨模态的智能检索能力（文本、图像、视频、音频）
- 实现素材自动索引和向量化
- 支持本地化部署，无需网络依赖
- 提供简洁高效的用户界面
- 避免桌面环境过度工程化，保持架构演进的灵活性

**用户价值**：
- 视频剪辑师：快速找到素材，提升工作效率
- 内容创作者：管理和检索媒体素材库
- 普通用户：本地文件的智能检索

## 1.2 核心设计原则

### 1.2.1 独立性原则

每个代码文件应该能够独立运行，通过参数传递所有需要的配置、数据和依赖，而不是直接导入其他模块。

**优点**：
- 便于单元测试：每个模块可以独立测试
- 降低耦合度：模块之间通过清晰的接口通信
- 提高可维护性：修改一个模块不影响其他模块
- **多进程就绪**：清晰的接口边界便于拆分为独立进程

**实现要求**：
- 所有依赖通过构造函数参数传递
- 不在模块内部直接导入其他业务模块
- 使用数据类或字典传递配置和状态
- **定义抽象接口**：核心业务组件必须定义抽象接口（ABC）
- **进程通信无关**：业务逻辑不依赖特定的进程间通信方式

### 1.2.2 单一职责原则

每个模块专注于一个明确的功能领域，不承担过多职责。

**优点**：
- 职责清晰，易于理解
- 便于测试和调试
- 降低修改风险
- **进程边界清晰**：单一职责的模块天然适合作为独立进程边界

**实现要求**：
- 每个模块只负责一个功能领域
- 复杂逻辑通过组合多个简单模块实现
- 避免一个模块承担多个不相关的职责
- **进程内聚性**：拆分为独立进程时，每个进程应该是高内聚的独立单元

### 1.2.4 配置驱动原则

所有重要参数必须通过配置文件管理，避免硬编码到代码中。

**优点**：
- 便于配置调整，无需修改代码
- 支持不同环境的配置隔离
- 提高代码可维护性
- 便于统一管理和版本控制

**实现要求**：
- 使用 `ConfigManager` 类管理所有配置
- 配置文件采用 YAML 格式，清晰易读
- 所有默认配置集中在配置文件中，不分散在代码中
- 对于必须有默认值的参数，在配置管理器中统一设置
- 避免在业务代码中直接使用常量或魔法数字

### 1.2.5 配置驱动硬件选择原则

**核心原则**：程序运行时是否使用 GPU 应该由配置文件决定，硬件检测逻辑不应该在具体处理任务的代码中。

**设计要求**：
- **配置文件驱动**：GPU/CPU 的使用由配置文件（`config/config.yml`）中的 `device` 参数决定
- **安装时检测**：硬件检测逻辑在安装脚本（`scripts/install.sh`）中完成
- **静态配置**：安装脚本检测硬件后写入配置文件，程序启动时直接读取配置
- **无运行时检测**：程序代码不进行任何硬件检测，不调用 `hardware_detector`
- **无硬编码**：程序代码中不硬编码 GPU/CPU 选择逻辑

**代码实现要求**：
- ✅ 允许：`device = config.get('models.available_models.chinese_clip_large.device')`
- ✅ 允许：`if device == 'cuda': monitor_gpu()`
- ❌ 禁止：`device = 'cuda' if torch.cuda.is_available() else 'cpu'`（运行时检测）
- ❌ 禁止：`detector = HardwareDetector(); device = detector.get_device()`（运行时检测）
- ❌ 禁止：`os.environ['CUDA_VISIBLE_DEVICES'] = '-1'`（硬编码禁用 GPU）

### 1.2.6 多进程架构原则

**核心原则**：当前单机应用采用多进程架构，将计算密集型任务与主应用解耦。

**设计要求**：
- **分层架构**：严格区分接入层、业务层、数据层
- **接口抽象**：核心业务逻辑通过抽象接口定义，不依赖具体实现
- **通信无关**：业务代码不依赖特定的进程间通信方式
- **状态外置**：进程状态存储在外部存储（SQLite），便于进程重启恢复

**进程划分**：
| 进程名称 | 职责 | 资源需求 | 进程数 |
|---------|------|---------|--------|
| **Main Process** | API服务、WebUI、任务调度 | 中 CPU，低内存 | 1 |
| **Embedding Worker** | 向量化推理 | 高 GPU/CPU，高内存 | 1-N |
| **File Monitor** | 文件监控、扫描 | 低 CPU，低内存 | 1 |
| **Task Worker** | 任务执行（非推理类） | 中 CPU，中内存 | 1-N |

**代码组织要求**：
```
src/
├── interfaces/          # 抽象接口定义（进程边界）
│   ├── __init__.py
│   ├── task_interface.py      # 任务接口
│   ├── embedding_interface.py # 向量化接口
│   └── storage_interface.py   # 存储接口
├── core/               # 核心业务实现
│   ├── task/          # 任务管理
│   ├── embedding/     # 向量化引擎
│   └── ...
├── workers/           # 独立进程实现
│   ├── __init__.py
│   ├── embedding_worker.py    # 向量化工作进程
│   ├── file_monitor.py        # 文件监控进程
│   └── task_worker.py         # 任务工作进程
├── ipc/               # 进程间通信
│   ├── __init__.py
│   ├── message_queue.py       # 消息队列
│   ├── shared_memory.py       # 共享内存
│   └── rpc_client.py          # RPC客户端
└── api/               # 接入层（REST API）
    └── v1/
```

**进程间通信方式**：
- **消息队列**：SQLite（任务队列、状态通知）
- **共享内存**：大文件数据传输（视频帧、音频数据）
- **Unix Socket**：控制命令、状态查询（Linux/macOS）
- **Named Pipe**：控制命令、状态查询（Windows）

## 1.3 系统架构图

### 1.3.1 单机架构（当前）

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         msearch 单机架构图                                   │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                              接入层 (Presentation)                           │
├──────────────────┬──────────────────┬──────────────────┬────────────────────┤
│      WebUI       │    Desktop UI    │       CLI        │   Python SDK       │
│     (Gradio)     │    (PySide6)     │   (Click)        │   (API Client)     │
└────────┬─────────┴────────┬─────────┴────────┬─────────┴────────┬───────────┘
         │                  │                  │                  │
         └──────────────────┴──────────────────┴──────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              API 层 (FastAPI)                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Search    │  │    Index    │  │    Task     │  │      System         │ │
│  │    API      │  │    API      │  │    API      │  │      API            │ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘ │
└─────────┼────────────────┼────────────────┼────────────────────┼────────────┘
          │                │                │                    │
          └────────────────┴────────────────┴────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         服务层 (Services) - 进程内调用                        │
├──────────────┬──────────────┬──────────────┬──────────────┬─────────────────┤
│ FileScanner  │ TaskManager  │ SearchEngine │   Embedding  │ ResourceMonitor │
│  (FileSvc)   │  (TaskSvc)   │ (SearchSvc)  │    Engine    │   (ResourceSvc) │
└──────┬───────┴──────┬───────┴──────┬───────┴──────┬───────┴────────┬────────┘
       │              │              │              │                │
       └──────────────┴──────────────┴──────────────┴────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         存储层 (Storage)                                     │
├──────────────┬──────────────┬──────────────┬──────────────┬─────────────────┤
│ VectorStore  │  Database    │  FileCache   │  ModelCache  │ ConfigManager   │
│  (LanceDB)   │  (SQLite)    │  (Local FS)  │  (Local FS)  │  (YAML)         │
└──────────────┴──────────────┴──────────────┴──────────────┴─────────────────┘
```

### 1.3.2 多进程架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         msearch 多进程架构图                                 │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌─────────────────┐
                              │  Main Process   │
                              │  (主进程)        │
                              │                 │
                              │ • API Server    │
                              │ • WebUI (Gradio)│
                              │ • Task Scheduler│
                              └────────┬────────┘
                                       │
              ┌────────────────────────┼────────────────────────┐
              │                        │                        │
              ▼                        ▼                        ▼
    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
    │ File Monitor    │    │ Embedding Worker│    │  Task Worker    │
    │  (独立进程)      │    │   (独立进程)     │    │   (独立进程)     │
    │                 │    │                 │    │                 │
    │ • 文件监控       │    │ • 向量化推理     │    │ • 任务执行       │
    │ • 目录扫描       │    │ • GPU/CPU计算   │    │ • 媒体预处理     │
    │ • 事件通知       │    │ • 模型管理       │    │ • 数据转换       │
    └────────┬────────┘    └────────┬────────┘    └────────┬────────┘
             │                      │                      │
             └──────────────────────┼──────────────────────┘
                                    │
                                    ▼
                    ┌─────────────────────────────┐
                    │      SQLite (本地队列)        │
                    │                             │
                    │ • 任务队列 (Task Queue)      │
                    │ • 状态缓存 (Status Cache)    │
                    │ • 结果缓存 (Result Cache)    │
                    └─────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         存储层 (Storage)                                     │
├──────────────┬──────────────┬──────────────┬──────────────┬─────────────────┤
│ VectorStore  │  Database    │  FileCache   │  ModelCache  │ ConfigManager   │
│  (LanceDB)   │  (SQLite)    │  (Local FS)  │  (Local FS)  │  (YAML)         │
└──────────────┴──────────────┴──────────────┴──────────────┴─────────────────┘

进程间通信：
- 控制命令：Unix Socket / Named Pipe
- 任务分发：SQLite 消息队列（基于persist-queue）
- 大数据传输：共享内存 (Shared Memory)
- 状态同步：SQLite数据库 + 内存LRU缓存 + 文件锁
```

## 1.4 技术栈选型

### 1.4.1 模型管理框架

**michaelfeil/infinity**（统一模型运行时框架）

**核心优势**：
- **统一调用接口**：所有模型（文本、图像、视频、音频）都通过 Infinity 框架统一调用
- **配置驱动**：通过 YAML 配置文件管理所有模型，支持热切换
- **多引擎支持**：torch/optimum/ctranslate2/neuron，自动选择最佳后端
- **高效管理**：自动批处理优化、FlashAttention 加速、智能内存管理
- **统一接口**：所有模型使用相同的加载和推理接口（AsyncEmbeddingEngine）
- **离线支持**：完全支持离线模式，自动处理模型依赖
- **多模型部署**：同时管理多个模型，灵活切换
- **统一 API**：`embed()` 方法统一处理所有模态的向量化请求
- **资源控制**：CPU/内存使用率限制在 90% 以内，避免系统卡死

### 1.4.2 支持的模型

#### 图像/视频向量化模型

所有图像/视频模型支持文本、图像、视频的跨模态检索。

| 模型ID | 模型名称 | 硬件要求 | 模型大小 | 向量维度 | 批处理大小 | 适用场景 |
|--------|---------|---------|---------|---------|-----------|---------|
| chinese_clip_base | OFA-Sys/chinese-clip-vit-base-patch16 | CPU/4GB 内存或 GPU/2GB 显存 | ~500MB | 512 | 16 | 开发测试、低配置设备、快速原型 |
| chinese_clip_large | OFA-Sys/chinese-clip-vit-large-patch14-336px | CPU/8GB 内存或 GPU/4GB 显存 | ~1.2GB | 768 | 8 | 生产环境、平衡精度与速度 |
| colqwen3_turbo | VAGOsolutions/SauerkrautLM-ColQwen3-1.7b-Turbo-v0.1 | GPU/16GB+ 显存（推荐 GPU/24GB） | ~3.5GB | 512 | 4 | 高性能检索、多模态理解 |
| tomoro_colqwen3 | TomoroAI/tomoro-colqwen3-embed-4b | GPU/24GB+ 显存（推荐 GPU/32GB） | ~8GB | 512 | 2 | 大规模检索、企业级应用 |

#### 音频向量化模型

| 模型ID | 模型名称 | 硬件要求 | 模型大小 | 向量维度 | 批处理大小 | 适用场景 |
|--------|---------|---------|---------|---------|-----------|---------|
| audio_model | laion/clap-htsat-unfused | CPU/8GB 内存或 GPU/4GB 显存 | ~590MB | 512 | 8 | 文本-音频检索、音频分类 |

### 1.4.3 其他组件

- **LanceDB**：向量数据库（单一向量表设计）
- **SQLite**：元数据存储
- **Gradio**：WebUI 框架
- **Pydantic**：数据验证
- **APScheduler**：任务调度
- **Watchdog**：文件系统监控

## 1.5 数据流转总览

### 1.5.1 完整数据流转图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         msearch 数据流转架构                                 │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  文件监控器  │────▶│  文件扫描器  │────▶│  元数据提取器 │────▶│  任务调度器  │
│ FileMonitor │     │ FileScanner │     │MetadataExtractor│   │TaskScheduler│
└─────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
       │                   │                    │                    │
       ▼                   ▼                    ▼                    ▼
┌─────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  文件发现   │     │  文件识别   │     │  元数据提取   │     │  任务队列   │
│  (新增/修改) │     │  (类型/大小) │     │  (哈希/时间戳)│   │  (优先级)   │
└─────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
                                                          │
                                                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        任务执行器 (TaskExecutor)                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                                          │
                    ┌──────────────┬──────────────┬───────┴───────┬──────────────┐
                    ▼              ▼              ▼              ▼              ▼
           ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
           │  图像处理器   │ │  视频处理器   │ │  音频处理器   │ │  文本处理器   │
           │ImageProcessor│ │VideoProcessor│ │AudioProcessor│ │TextProcessor│
           └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
                    │              │              │              │
                    ▼              ▼              ▼              ▼
           ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
           │  图像预处理   │ │  视频预处理   │ │  音频预处理   │ │  文本预处理   │
           │              │ │  (切片/场景检测)│ │              │ │              │
           └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
                    │              │              │              │
                    ▼              ▼              ▼              ▼
           ┌────────────────────────────────────────────────────────────────┐
           │                    向量化引擎 (EmbeddingEngine)                 │
           └────────────────────────────────────────────────────────────────┘
                                                          │
                    ┌──────────────┬──────────────┬───────┴───────┬──────────────┐
                    ▼              ▼              ▼              ▼              ▼
           ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
           │ [配置驱动模型] │ │ [配置驱动模型] │ │   CLAP-HTSAT │ │ [配置驱动模型] │
           │  (图像向量)   │ │  (视频向量)   │ │  (音频向量)   │ │  (文本向量)   │
           └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
                    │              │              │              │
                    └──────────────┴──────────────┴──────────────┘
                                           │
                                           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          向量存储 (VectorStore - LanceDB)                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                           │
                                           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      元数据存储 (Database - SQLite)                           │
└─────────────────────────────────────────────────────────────────────────────┘
                                           │
                                           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          搜索引擎 (SearchEngine)                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                           │
                    ┌──────────────┬───────┴───────┬──────────────┐
                    ▼              ▼              ▼              ▼
           ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
           │  文本检索     │ │  图像检索     │ │  视频检索     │ │  音频检索     │
           │ Text Search  │ │ Image Search │ │ Video Search │ │ Audio Search │
           └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
                    │              │              │              │
                    └──────────────┴──────────────┴──────────────┘
                                           │
                                           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          结果排序与融合 (ResultRanker)                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                           │
                                           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          API 服务器 / Web UI                                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 1.6 多进程架构设计

### 1.6.1 进程划分

**设计目标**：将计算密集型任务与主应用解耦，提升系统稳定性和资源利用率。

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         msearch 进程架构                                     │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                              Main Process                                   │
│                              (主进程 - 1个)                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐ │
│  │  API Server  │  │  WebUI       │  │ Task Manager │  │ Config Manager │ │
│  │  (FastAPI)   │  │  (Gradio)    │  │ (调度器)      │  │ (配置管理)      │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
         ┌─────────────────────────────┼─────────────────────────────┐
         │                             │                             │
         ▼                             ▼                             ▼
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│ File Monitor        │    │ Embedding Worker    │    │ Task Worker         │
│ (文件监控进程 - 1个)  │    │ (向量化进程 - 1-N个) │    │ (任务执行进程 - 1-N) │
├─────────────────────┤    ├─────────────────────┤    ├─────────────────────┤
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
                    │      SQLite + Unix Socket (本地)     │
                    │  ┌─────────────┐ ┌───────────────┐ │
                    │  │ Task Queue  │ │ Status Cache  │ │
                    │  │ (任务队列)   │ │ (状态缓存)     │ │
                    │  └─────────────┘ └───────────────┘ │
                    └───────────────────────────────────┘
```

### 1.6.2 进程职责说明

#### Main Process (主进程)

**职责**：
- 提供 REST API 接口
- 运行 WebUI (Gradio)
- 任务调度与状态管理
- 配置管理
- 进程生命周期管理

**资源需求**：
- CPU：中等（1-2 核）
- 内存：低（500MB - 1GB）
- GPU：无

**启动顺序**：第 1 个启动

#### File Monitor (文件监控进程)

**职责**：
- 监控配置的目录变化
- 执行目录扫描
- 检测新增/修改/删除的文件
- 发送文件事件通知

**资源需求**：
- CPU：低
- 内存：低（100MB - 200MB）
- GPU：无

**启动顺序**：第 2 个启动（依赖 Main Process）

#### Embedding Worker (向量化工作进程)

**职责**：
- 加载 AI 模型
- 执行向量推理（图像、视频、音频）
- 管理 GPU/CPU 资源
- 批处理优化

**资源需求**：
- CPU：高（推理时使用）
- 内存：高（2GB - 8GB，取决于模型）
- GPU：可选（推荐，显存 4GB+）

**启动顺序**：第 3 个启动（依赖 SQLite）
- 可启动多个实例（多 GPU 场景）

#### Task Worker (任务执行进程)

**职责**：
- 执行非推理类任务
- 媒体预处理（视频切片、音频提取等）
- 文件格式转换
- 缩略图生成

**资源需求**：
- CPU：中等至高
- 内存：中等（1GB - 2GB）
- GPU：无

**启动顺序**：第 4 个启动（依赖 SQLite）
- 可启动多个实例（并行处理）

### 1.6.3 进程间通信机制

#### 通信方式选择

| 通信场景 | 通信方式 | 说明 |
|---------|---------|------|
| 任务分发 | SQLite 队列（persist-queue） | 可靠、持久化、支持优先级 |
| 状态查询 | Unix Socket / Named Pipe | 低延迟、双向通信 |
| 大文件传输 | 共享内存 | 零拷贝、高性能 |
| 配置同步 | 文件 + 信号 | 简单可靠 |
| 日志收集 | 文件 / SQLite | 异步、不阻塞 |

#### 为什么选择SQLite而不是Redis？

**桌面应用的核心需求**：
- **快速启动**：应用总启动时间需<3秒
- **低资源占用**：支持4GB RAM低配设备
- **零配置**：一键安装，无需额外配置
- **100%离线**：不依赖外部服务

**Redis与SQLite对比**：

| 指标 | Redis | SQLite (persist-queue) | 优势 |
|------|-------|------------------------|------|
| **启动时间** | 2-3秒 | <0.1秒 | SQLite快30倍 |
| **内存占用** | 150-200MB | <10MB | SQLite节省95% |
| **外部依赖** | 需单独安装 | 纯Python | SQLite零依赖 |
| **配置复杂度** | 需配置端口、密码等 | 零配置 | SQLite开箱即用 |
| **离线运行** | 需本地运行服务 | 文件级存储 | SQLite更可靠 |
| **分布式能力** | 强 | 无 | 桌面应用不需要 |

**结论**：对于单机桌面应用，SQLite方案完全满足需求，且更符合"轻量、快速、零配置"的设计原则。

#### SQLite任务队列和状态缓存设计

**任务队列（基于persist-queue）**：

```
# 任务队列表结构
CREATE TABLE tasks (
    id TEXT PRIMARY KEY,
    data TEXT NOT NULL,
    priority INTEGER DEFAULT 0,
    status TEXT DEFAULT 'pending', -- pending, processing, completed, failed
    created_at REAL NOT NULL,
    started_at REAL,
    completed_at REAL,
    worker_id TEXT,
    result TEXT,
    error TEXT,
    sender TEXT,
    sender_type TEXT
);

# 优先级队列（通过priority字段实现）
# 高优先级: priority = 10
# 普通优先级: priority = 5  
# 低优先级: priority = 1

# 进程状态表
CREATE TABLE process_states (
    process_id TEXT PRIMARY KEY,
    process_type TEXT NOT NULL,
    status TEXT DEFAULT 'running',
    pid INTEGER,
    heartbeat REAL,
    created_at REAL NOT NULL,
    last_updated REAL NOT NULL
);

# 任务状态缓存表（内存LRU缓存的持久化层）
CREATE TABLE task_states (
    task_id TEXT PRIMARY KEY,
    state_data TEXT NOT NULL,
    last_updated REAL NOT NULL,
    accessed_count INTEGER DEFAULT 0
);
```

**实现原理**：
```python
import persistqueue
import sqlite3
import json
from collections import OrderedDict
import threading
import time

class LRUCache:
    """内存LRU缓存"""
    def __init__(self, capacity: int = 1000):
        self.capacity = capacity
        self.cache = OrderedDict()
        self.lock = threading.Lock()
    
    def get(self, key: str):
        with self.lock:
            if key in self.cache:
                # 移动到末尾，表示最近使用
                self.cache.move_to_end(key)
                return self.cache[key]
            return None
    
    def put(self, key: str, value):
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
            elif len(self.cache) >= self.capacity:
                # 删除最久未使用的项
                self.cache.popitem(last=False)
            self.cache[key] = value

class StateCache:
    """状态缓存管理器（双层设计）"""
    def __init__(self, db_path: str = 'data/state_cache.db'):
        self.db_path = db_path
        self.memory_cache = LRUCache(capacity=1000)
        self.lock = threading.Lock()
        self.init_db()
    
    def init_db(self):
        """初始化SQLite数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建状态表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS task_states (
                task_id TEXT PRIMARY KEY,
                state_data TEXT NOT NULL,
                last_updated REAL NOT NULL,
                accessed_count INTEGER DEFAULT 0
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS process_states (
                process_id TEXT PRIMARY KEY,
                state_data TEXT NOT NULL,
                last_updated REAL NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_task_state(self, task_id: str):
        """获取任务状态"""
        # 先查内存缓存
        cached = self.memory_cache.get(task_id)
        if cached:
            return cached
        
        # 内存中未找到，查数据库
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT state_data FROM task_states WHERE task_id = ?',
            (task_id,)
        )
        result = cursor.fetchone()
        
        conn.close()
        
        if result:
            state_data = json.loads(result[0])
            # 加入内存缓存
            self.memory_cache.put(task_id, state_data)
            return state_data
        
        return None
    
    def update_task_state(self, task_id: str, state_data: dict):
        """更新任务状态"""
        # 更新内存缓存
        self.memory_cache.put(task_id, state_data)
        
        # 更新数据库
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO task_states 
            (task_id, state_data, last_updated, accessed_count)
            VALUES (?, ?, ?, COALESCE((SELECT accessed_count FROM task_states WHERE task_id = ?), 0))
        ''', (task_id, json.dumps(state_data), time.time(), task_id))
        
        conn.commit()
        conn.close()

# 任务队列（持久化）
task_queue = persistqueue.SQLiteQueue(
    path='data/task_queue', 
    multithreading=True, 
    auto_commit=True
)

# 优先级队列（持久化）
high_priority_queue = persistqueue.SQLitePriorityQueue(
    path='data/priority_queue_high',
    multithreading=True
)
normal_priority_queue = persistqueue.SQLitePriorityQueue(
    path='data/priority_queue_normal',
    multithreading=True
)
low_priority_queue = persistqueue.SQLitePriorityQueue(
    path='data/priority_queue_low',
    multithreading=True
)
```

#### 共享内存设计

**使用场景**：
- 大文件数据传输（视频帧、音频数据）
- 避免序列化/反序列化开销

**实现方案**：
```python
# src/ipc/shared_memory.py
import mmap
import os
import struct

class SharedMemoryManager:
    """共享内存管理器"""
    
    def __init__(self, name: str, size: int = 100 * 1024 * 1024):  # 100MB
        self.name = name
        self.size = size
        self.mm = None
    
    def create(self):
        """创建共享内存"""
        # Linux/macOS: /dev/shm/{name}
        # Windows: 使用 mmap
        pass
    
    def write(self, data: bytes, offset: int = 0) -> int:
        """写入数据，返回实际写入字节数"""
        pass
    
    def read(self, offset: int, size: int) -> bytes:
        """读取数据"""
        pass
    
    def close(self):
        """关闭共享内存"""
        pass
```

### 1.6.4 进程生命周期管理

#### 启动流程

```
1. Main Process 启动
   ├── 加载配置
   ├── 初始化日志
   ├── 初始化数据库连接（SQLite）
   ├── 初始化任务队列（persist-queue）
   ├── 初始化状态缓存（SQLite + 内存LRU）
   ├── 启动本地IPC服务（Unix Socket/Named Pipe）
   └── 启动 API Server 和 WebUI

2. File Monitor 启动
   ├── 连接本地IPC服务
   ├── 加载监控目录配置
   ├── 执行初始扫描
   └── 启动文件系统监控

3. Embedding Worker(s) 启动
   ├── 连接本地IPC服务
   ├── 加载模型配置
   ├── 初始化模型（延迟加载）
   └── 开始监听任务队列

4. Task Worker(s) 启动
   ├── 连接本地IPC服务
   ├── 注册处理能力
   └── 开始监听任务队列
```

#### 进程监控与重启

```python
# src/core/process/process_manager.py
class ProcessManager:
    """进程管理器"""
    
    def __init__(self):
        self.processes = {}
        self.heartbeat_timeout = 30  # 秒
    
    def start_process(self, name: str, target: callable, args: tuple = ()):
        """启动进程"""
        pass
    
    def monitor_processes(self):
        """监控所有进程状态"""
        # 检查心跳
        # 如果超时，标记为失败
        # 根据策略决定是否重启
        pass
    
    def restart_process(self, name: str):
        """重启进程"""
        pass
    
    def shutdown_all(self):
        """关闭所有进程"""
        pass
```

#### 优雅关闭

```
1. 接收关闭信号 (SIGTERM)
2. 停止接收新任务
3. 等待处理中任务完成（超时 30 秒）
4. 保存状态
5. 关闭连接
6. 退出进程
```

### 1.6.5 配置示例

```yaml
# config/process.yml

process:
  # 主进程配置
  main:
    auto_restart: true
    max_restart_attempts: 3
  
  # 文件监控进程
  file_monitor:
    enabled: true
    count: 1
    auto_restart: true
  
  # 向量化工作进程
  embedding_worker:
    enabled: true
    count: 1  # 根据 GPU 数量调整
    gpu_devices: [0]  # 使用的 GPU 设备
    auto_restart: true
    batch_size: 16
  
  # 任务工作进程
  task_worker:
    enabled: true
    count: 2  # 根据 CPU 核心数调整
    auto_restart: true
    max_concurrent_tasks: 4

# IPC配置（优化版）
ipc:
  # 任务队列配置
  task_queue:
    path: "data/task_queue"  # SQLite队列路径
    max_size: 10000  # 最大队列长度
    auto_commit: true
  
  # 状态缓存配置
  state_cache:
    path: "data/state_cache.db"  # SQLite缓存路径
    memory_capacity: 1000  # 内存LRU缓存容量
    cleanup_interval: 3600  # 清理间隔（秒）
  
  # 本地通信配置
  local_ipc:
    socket_path: "/tmp/msearch.sock"  # Unix Socket路径
    timeout: 30  # 通信超时（秒）
  
  # 共享内存配置
  shared_memory:
    enabled: true
    default_size: 104857600  # 100MB
    max_size: 1073741824     # 1GB
```

### 1.5.2 数据流转阶段说明

**阶段 1：文件发现与扫描**
```
用户添加文件到监控目录
    ↓
文件监控器 (FileMonitor) 检测到文件变化
    ↓
文件扫描器 (FileScanner) 扫描文件
    ↓
收集基本信息 (路径、大小、修改时间、类型)
    ↓
创建文件扫描任务 (task_type: file_scan)
```

**阶段 2：元数据提取**
```
任务调度器分配元数据提取任务
    ↓
元数据提取器 (MetadataExtractor) 执行
    ↓
计算文件哈希 (SHA256)
    ↓
提取文件元数据 (EXIF、视频时长、音频采样率等)
    ↓
检测文件是否重复 (通过哈希)
    ↓
如果重复：直接引用已存储向量
    ↓
如果不重复：创建预处理任务
```

**阶段 3：预处理**
```
任务调度器分配预处理任务
    ↓
根据文件类型选择处理器
    ↓
├─ 图像预处理 (ImagePreprocessor)
│  ├─ 调整大小 (resize to 512x512)
│  ├─ 格式转换 (convert to RGB)
│  └─ 归一化 (normalize)
│
├─ 视频预处理 (VideoPreprocessor)
│  ├─ 时长判断 (≤6秒 or >6秒)
│  ├─ 音频分离 (extract audio)
│  ├─ 场景检测 (scene detection)
│  ├─ 视频切片 (video slicing)
│  └─ 帧提取 (frame extraction)
│
└─ 音频预处理 (AudioPreprocessor)
   ├─ 价值判断 (≥3秒)
   ├─ 重采样 (resample to 44100Hz)
   ├─ 格式转换 (convert to mono/stereo)
   └─ 归一化 (normalize)
```

**阶段 4：向量化**
```
任务调度器分配向量化任务
    ↓
向量化引擎 (EmbeddingEngine) 加载模型
    ↓
├─ 图像向量化 (Image Embedding)
│  ├─ 使用模型: [配置驱动模型]-500M
│  ├─ 输入: 预处理后的图像 (batch_size=16)
│  ├─ 输出: [配置驱动模型]向量
│  └─ 精度: float16
│
├─ 视频向量化 (Video Embedding)
│  ├─ 使用模型: [配置驱动模型]-500M
│  ├─ 输入: 视频帧序列 (batch_size=16)
│  ├─ 输出: [配置驱动模型]向量 (每帧一个向量)
│  └─ 精度: float16
│
└─ 音频向量化 (Audio Embedding)
   ├─ 使用模型: [配置驱动模型]
   ├─ 输入: 预处理后的音频 (batch_size=8)
   ├─ 输出: [配置驱动模型]向量
   └─ 精度: float16
```

**阶段 5：存储**
```
向量数据准备
    ↓
├─ 向量存储 (LanceDB)
│  ├─ 表名: unified_vectors
│  ├─ 字段:
│  │  ├─ vector: 向量数据 ([配置驱动模型])
│  │  ├─ file_id: 文件ID
│  │  ├─ segment_id: 分段ID (视频专用)
│  │  ├─ timestamp: 时间戳 (视频帧时间)
│  │  ├─ modality: 模态类型 (image/video/audio)
│  │  └─ created_at: 创建时间
│  └─ 索引: IVF 索引
│
└─ 元数据存储 (SQLite)
   ├─ 表名: file_metadata
   ├─ 字段:
   │  ├─ id: 文件ID (UUID)
   │  ├─ file_path: 文件路径
   │  ├─ file_name: 文件名
   │  ├─ file_type: 文件类型
   │  ├─ file_size: 文件大小
   │  ├─ file_hash: 文件哈希
   │  ├─ created_at: 创建时间
   │  ├─ modified_at: 修改时间
   │  ├─ indexed_at: 索引时间
   │  └─ status: 状态
   ├─ 表名: video_segments
   ├─ 字段:
   │  ├─ id: 分段ID
   │  ├─ file_id: 文件ID
   │  ├─ start_time: 开始时间
   │  ├─ end_time: 结束时间
   │  ├─ thumbnail_path: 缩略图路径
   │  └─ frame_count: 帧数
   └─ 表名: vector_timestamp_map
      ├─ 字段:
      │  ├─ vector_id: 向量ID
      │  ├─ file_id: 文件ID
      │  ├─ segment_id: 分段ID
      │  └─ timestamp: 时间戳
```

**阶段 6：检索**
```
用户查询
    ↓
├─ 文本查询
│  ├─ 输入: 文本字符串
│  ├─ 处理: 使用 [配置驱动模型] 生成文本向量
│  └─ 输出: [配置驱动模型]文本向量
│
├─ 图像查询
│  ├─ 输入: 图像文件
│  ├─ 处理: 预处理 + [配置驱动模型] 生成图像向量
│  └─ 输出: [配置驱动模型]图像向量
│
├─ 音频查询
│  ├─ 输入: 音频文件
│  ├─ 处理: 预处理 + CLAP 生成音频向量
│  └─ 输出: [配置驱动模型]音频向量
│
└─ 视频查询
   ├─ 输入: 视频文件
   ├─ 处理: 预处理 + 帧提取 + [配置驱动模型] 生成视频向量
   └─ 输出: [配置驱动模型]视频向量 (多帧)
    ↓
向量检索 (LanceDB)
    ↓
├─ 查询向量与数据库中向量计算相似度
├─ 使用 IVF 索引加速检索
├─ 返回 top_k 个最相似结果
└─ 过滤低相似度结果 (< 0.7)
    ↓
结果排序与融合
    ↓
├─ 多模态结果融合
├─ 去重 (同一文件的多个分段)
├─ 排序 (相似度降序)
└─ 生成时间轴 (视频专用)
    ↓
返回结果给用户
```

---

# 第二部分：核心组件设计

## 2.1 配置管理系统

### 2.1.1 配置文件结构

```yaml
# config/config.yml

# 系统配置
system:
  name: "msearch"
  version: "1.0.0"
  log_level: "INFO"
  log_dir: "logs"
  cache_dir: "data/cache"
  model_dir: "data/models"
  database_dir: "data/database"

# 模型配置
models:
  available_models:
    chinese_clip_base:
      model_id: "chinese_clip_base"
      model_name: "OFA-Sys/chinese-clip-vit-base-patch16"
      local_path: "data/models/chinese-clip-vit-base-patch16"
      engine: "torch"
      device: "cpu"
      dtype: "float32"
      embedding_dim: 512
      trust_remote_code: true
      pooling_method: "mean"
      compile: false
      batch_size: 16

    chinese_clip_large:
      model_id: "chinese_clip_large"
      model_name: "OFA-Sys/chinese-clip-vit-large-patch14-336px"
      local_path: "data/models/chinese-clip-vit-large-patch14-336px"
      engine: "torch"
      device: "cpu"
      dtype: "float32"
      embedding_dim: 768
      trust_remote_code: true
      pooling_method: "mean"
      compile: false
      batch_size: 8

    audio_model:
      model_id: "audio_model"
      model_name: "laion/clap-htsat-unfused"
      local_path: "data/models/clap-htsat-unfused"
      engine: "torch"
      device: "cpu"
      dtype: "float32"
      embedding_dim: 512
      trust_remote_code: true
      pooling_method: "mean"
      compile: false
      batch_size: 8

  active_models:
    - chinese_clip_large
    - audio_model

# 向量存储配置
vector_store:
  type: "lancedb"
  path: "data/database/lancedb"
  table_name: "unified_vectors"
  embedding_dim: 768
  index_type: "ivf"
  nlist: 1024
  metric: "cosine"

# 数据库配置
database:
  type: "sqlite"
  path: "data/database/sqlite/msearch.db"
  timeout: 30
  check_same_thread: false

# 任务调度配置
task_scheduler:
  max_workers: 4
  queue_size: 1000
  retry_count: 3
  retry_delay: 5
  priority_levels: 5

# 文件扫描配置
file_scanner:
  scan_strategy: "incremental"
  max_concurrency: 4
  batch_size: 100
  supported_types:
    image: ["jpg", "jpeg", "png", "bmp", "gif", "webp", "tiff"]
    video: ["mp4", "avi", "mov", "mkv", "flv", "wmv", "webm"]
    audio: ["mp3", "wav", "aac", "flac", "ogg", "wma", "m4a"]
  filters:
    min_file_size: 10240
    min_video_duration: 0.5
    enable_hash_detection: true
  memory_limit_mb: 512
  cpu_usage_limit: 80
  hash_chunk_size: 65536
  exclude_paths:
    - "/tmp"
    - "/var/tmp"
    - "node_modules"

# WebUI 配置
webui:
  host: "0.0.0.0"
  port: 7860
  debug: false
  share: false
  enable_queue: true
  concurrency_count: 10

# 检索配置
search:
  top_k: 20
  min_score_threshold: 0.7
  enable_reranking: true
  rerank_top_k: 10
  max_results: 100

# 资源监控配置
resource_monitor:
  enabled: true
  check_interval: 1.0
  cpu_threshold: 90
  memory_threshold: 90
  gpu_threshold: 90
  auto_optimize: true
```

### 2.1.2 ConfigManager 类设计

```python
class ConfigManager:
    """
    配置管理器 - 负责加载、验证和管理所有配置
    """
    
    def __init__(self, config_path: str = "config/config.yml"):
        self.config_path = config_path
        self.config = {}
        self.defaults = {
            "system.log_level": "INFO",
            "system.log_dir": "logs",
            "task_scheduler.max_workers": 4,
            "search.top_k": 20,
        }
        
    def load(self) -> Dict:
        """加载配置文件"""
        pass
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值，支持点分隔符"""
        pass
    
    def set(self, key: str, value: Any) -> None:
        """设置配置值"""
        pass
    
    def validate(self) -> List[str]:
        """验证配置的完整性和正确性"""
        pass
    
    def save(self) -> None:
        """保存配置到文件"""
        pass
```

## 2.2 模型管理系统

### 2.2.1 统一模型调用架构

```
┌─────────────────────────────────────────────────────────────────┐
│                      EmbeddingEngine                             │
│                   （统一向量化接口）                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ModelManager                                  │
│                 （基于 Infinity 框架）                            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  async def embed_text(inputs, input_type="text")        │   │
│  │  async def embed_image(inputs, input_type="image")      │   │
│  │  async def embed_video(inputs, input_type="video")      │   │
│  │  async def embed_audio(inputs, input_type="audio")      │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
    ┌─────▼─────┐      ┌─────▼─────┐      ┌─────▼─────┐
    │ Infinity  │      │ Infinity  │      │ Infinity  │
    │   Client  │      │   Client  │      │   Client  │
    │  (Image)  │      │  (Video)  │      │  (Audio)  │
    └─────┬─────┘      └─────┬─────┘      └─────┬─────┘
          │                   │                   │
    ┌─────▼─────┐      ┌─────▼─────┐      ┌─────▼─────┐
    │ chinese-  │      │ chinese-  │      │ clap-     │
    │ clip-*    │      │ clip-*    │      │ htsat     │
    │ vit-*     │      │ vit-*     │      │ unfused   │
    └───────────┘      └───────────┘      └───────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   config.yml    │
                    │ （统一配置）     │
                    └─────────────────┘
```

### 2.2.2 ModelManager 类设计

```python
class ModelManager:
    """
    模型管理器 - 负责加载、管理和切换所有模型
    """
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.models: Dict[str, AsyncEmbeddingEngine] = {}
        self.active_models: List[str] = []
        
    async def load_model(self, model_id: str) -> AsyncEmbeddingEngine:
        """加载单个模型"""
        pass
    
    async def load_all_models(self) -> None:
        """加载所有配置的模型"""
        pass
    
    async def unload_model(self, model_id: str) -> None:
        """卸载模型"""
        pass
    
    async def switch_model(self, model_id: str) -> None:
        """切换到指定模型"""
        pass
    
    async def embed(self, inputs: List[str], input_type: str = "text") -> np.ndarray:
        """统一向量化接口"""
        pass
    
    def get_model_info(self, model_id: str) -> Dict:
        """获取模型信息"""
        pass
```

### 2.2.3 Infinity 框架集成示例

```python
from infinity_emb import AsyncEmbeddingEngine, EngineArgs

# 初始化 Infinity 客户端
async def initialize_model(model_config: Dict) -> AsyncEmbeddingEngine:
    engine_args = EngineArgs(
        model_name_or_path=model_config["local_path"],
        engine=model_config["engine"],
        device=model_config["device"],
        dtype=model_config["dtype"],
        trust_remote_code=model_config.get("trust_remote_code", False),
    )
    
    engine = AsyncEmbeddingEngine.from_args(engine_args)
    await engine.astart()
    
    return engine

# 使用模型进行向量化
async def embed_with_model(engine: AsyncEmbeddingEngine, inputs: List[str], input_type: str) -> np.ndarray:
    embeddings = await engine.embed(inputs, input_type=input_type)
    return embeddings
```

## 2.3 文件扫描系统

### 2.3.1 设计目标与核心原则

**设计目标**：
- **高效识别**：快速识别系统支持的媒体文件（图像、视频为主，未来扩展音频）
- **智能过滤**：初步过滤低价值内容，减少后续处理开销
- **元数据提取**：提取基本文件元数据，为后续处理提供基础
- **重复检测**：通过文件哈希检测重复内容，避免重复处理
- **可扩展架构**：支持未来扩展新的文件类型和扫描策略
- **资源友好**：在扫描过程中合理使用系统资源，避免系统过载

**核心设计原则**：
- **单一职责**：专注于文件识别和初步过滤，不承担后续处理任务
- **独立性**：通过清晰接口与其他模块通信，减少耦合
- **性能优先**：优化扫描速度和资源占用，确保用户体验流畅
- **可配置性**：支持通过配置文件调整扫描策略和参数
- **容错性**：优雅处理扫描过程中的异常情况

### 2.3.2 模块架构

```
┌─────────────────────┐
│   FileScanner       │
├─────────────────────┤
│  ┌─────────────────┐│
│  │  扫描策略层    ││
│  └─────────────────┘│
│  ┌─────────────────┐│
│  │  文件识别层    ││
│  └─────────────────┘│
│  ┌─────────────────┐│
│  │  元数据提取层  ││
│  └─────────────────┘│
│  ┌─────────────────┐│
│  │  过滤处理层    ││
│  └─────────────────┘│
│  ┌─────────────────┐│
│  │  结果输出层    ││
│  └─────────────────┘│
└─────────────────────┘
```

### 2.3.3 职责边界

| 层级 | 主要职责 | 核心组件 |
|------|----------|----------|
| **扫描策略层** | 决定如何扫描文件系统 | 扫描调度器、路径管理器、并发控制器 |
| **文件识别层** | 识别支持的媒体文件类型 | 文件类型检测器、扩展名匹配器、MIME类型识别器 |
| **元数据提取层** | 提取基本文件信息 | 元数据收集器、哈希计算器、时间戳提取器 |
| **过滤处理层** | 初步过滤低价值内容 | 大小过滤器、格式过滤器、噪音检测器 |
| **结果输出层** | 处理扫描结果 | 结果处理器、任务创建器、进度报告器 |

### 2.3.4 与其他模块的集成

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  TaskManager    │────▶│  FileScanner    │────▶│  DatabaseManager│
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                          │                      ▲
        ▼                          ▼                      │
┌─────────────────┐     ┌─────────────────┐     ┌─────────┴─────────┐
│                 │     │                 │     │                 │
│  ConfigManager  │     │  FilterSystem   │────▶│  MetadataExtractor│
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### 2.3.5 扫描策略设计

#### 深度优先扫描
- **适用场景**：需要完整扫描指定目录树
- **核心算法**：递归遍历目录结构，优先扫描子目录
- **性能特点**：内存占用较高，但能保证扫描完整性

#### 广度优先扫描
- **适用场景**：快速获取目录概览
- **核心算法**：按层级扫描目录，优先扫描当前目录下的文件
- **性能特点**：内存占用较低，适合大目录树的初步扫描

#### 增量扫描
- **适用场景**：定期更新索引，只扫描新增或修改的文件
- **核心算法**：
  1. 记录上次扫描时间戳
  2. 只处理修改时间晚于该时间戳的文件
  3. 支持文件系统事件监听（如 inotify）实现实时增量扫描
- **性能特点**：扫描速度快，资源占用低，适合日常维护

#### 并发扫描
- **适用场景**：多磁盘系统或高性能硬件环境
- **核心算法**：
  1. 将扫描任务拆分为多个子任务
  2. 使用线程池或进程池并行执行
  3. 动态调整并发数，避免系统过载
- **性能特点**：充分利用系统资源，提高扫描效率

### 2.3.6 文件识别机制

#### 扩展名匹配
- **快速识别**：通过文件扩展名初步识别文件类型
- **支持类型**：
  - 图像：jpg, jpeg, png, bmp, gif, webp, tiff
  - 视频：mp4, avi, mov, mkv, flv, wmv, webm, mpg, mpeg
  - 音频：mp3, wav, aac, flac, ogg, wma, m4a

#### MIME 类型识别
- **深度识别**：读取文件头信息，识别真实文件类型
- **实现方式**：通过文件魔术数字（Magic Number）识别
- **核心价值**：避免扩展名欺骗，提高识别准确性

#### 文件结构验证
- **精确识别**：对关键文件类型进行结构验证
- **验证内容**：
  - 图像：验证文件结构完整性
  - 视频：验证容器格式和编解码器信息
- **实现方式**：使用轻量级库进行快速验证

### 2.3.7 元数据提取

| 元数据字段 | 类型 | 描述 | 用途 |
|------------|------|------|------|
| `file_path` | String | 文件完整路径 | 唯一标识文件位置 |
| `file_name` | String | 文件名（不含路径） | 展示和搜索 |
| `file_ext` | String | 文件扩展名 | 类型识别 |
| `file_size` | Integer | 文件大小（字节） | 过滤和存储管理 |
| `file_hash` | String | 文件 SHA256 哈希 | 重复检测 |
| `mime_type` | String | 文件 MIME 类型 | 精确类型识别 |
| `created_at` | Timestamp | 文件创建时间 | 时间范围查询 |
| `modified_at` | Timestamp | 文件修改时间 | 增量扫描 |
| `accessed_at` | Timestamp | 文件访问时间 | 使用频率分析 |
| `basic_info` | JSON | 基本媒体信息 | 初步内容分析 |

### 2.3.8 重复文件处理

**检测算法**：
1. **快速过滤**：使用文件大小快速排除不可能重复的文件
2. **哈希计算**：对可能重复的文件计算 SHA256 哈希
3. **数据库比对**：将哈希值与数据库中已存储的文件进行比对

**处理策略**：
- **完全重复**：相同哈希值的文件直接引用已有记录
- **相似内容**：（未来扩展）通过相似性算法检测相似内容
- **保留策略**：根据配置决定保留哪些重复文件的元数据

### 2.3.9 低价值内容过滤

#### 基于文件属性的过滤
- **文件大小过滤**：过滤过小的文件（如 <10KB 的图像）
- **文件时长过滤**：过滤过短的视频（如 <1 秒的视频片段）
- **格式兼容性**：过滤系统不支持的编解码器

#### 基于内容的初步过滤
- **分辨率过滤**：过滤低分辨率图像/视频
- **文件完整性**：过滤损坏或不完整的文件
- **无意义内容**：（未来扩展）基于 AI 的初步内容分析

### 2.3.10 FileScanner 类设计

```python
class FileScanner:
    """
    文件扫描器 - 负责扫描文件系统，识别媒体文件
    """
    
    def __init__(self, config: ConfigManager, db_manager: DatabaseManager):
        self.config = config
        self.db_manager = db_manager
        self.scan_strategy: ScanStrategy = None
        self.file_detector: FileTypeDetector = None
        self.metadata_extractor: MetadataExtractor = None
        self.filter_system: FilterSystem = None
        
    def set_scan_strategy(self, strategy: ScanStrategy) -> None:
        """设置扫描策略"""
        pass
    
    async def scan(self, path: str) -> List[FileInfo]:
        """扫描指定路径"""
        pass
    
    async def scan_incremental(self, path: str, last_scan_time: float) -> List[FileInfo]:
        """增量扫描"""
        pass
    
    def get_scan_status(self) -> ScanStatus:
        """获取扫描状态"""
        pass
```

## 2.4 数据处理系统

### 2.4.1 图像处理器

```python
class ImageProcessor:
    """
    图像处理器 - 负责图像文件的预处理和向量化
    """
    
    def __init__(self, config: ConfigManager, model_manager: ModelManager):
        self.config = config
        self.model_manager = model_manager
        
    async def process(self, file_info: FileInfo) -> ImageProcessingResult:
        """处理图像文件"""
        pass
    
    def preprocess(self, image_path: str) -> np.ndarray:
        """图像预处理"""
        pass
    
    async def embed(self, image_tensor: np.ndarray) -> np.ndarray:
        """图像向量化"""
        pass
    
    def generate_thumbnail(self, image_path: str, size: Tuple[int, int] = (256, 256)) -> str:
        """生成缩略图"""
        pass
```

### 2.4.2 视频处理器

```python
class VideoProcessor:
    """
    视频处理器 - 负责视频文件的预处理和向量化
    """
    
    def __init__(self, config: ConfigManager, model_manager: ModelManager):
        self.config = config
        self.model_manager = model_manager
        
    async def process(self, file_info: FileInfo) -> VideoProcessingResult:
        """处理视频文件"""
        pass
    
    def preprocess(self, video_path: str) -> List[np.ndarray]:
        """视频预处理"""
        pass
    
    def extract_frames(self, video_path: str, fps: float = 1.0) -> List[np.ndarray]:
        """提取视频帧"""
        pass
    
    def detect_scenes(self, video_path: str) -> List[Tuple[float, float]]:
        """场景检测"""
        pass
    
    async def embed(self, frame_tensors: List[np.ndarray]) -> np.ndarray:
        """视频向量化"""
        pass
```

### 2.4.3 音频处理器

```python
class AudioProcessor:
    """
    音频处理器 - 负责音频文件的预处理和向量化
    """
    
    def __init__(self, config: ConfigManager, model_manager: ModelManager):
        self.config = config
        self.model_manager = model_manager
        
    async def process(self, file_info: FileInfo) -> AudioProcessingResult:
        """处理音频文件"""
        pass
    
    def preprocess(self, audio_path: str) -> np.ndarray:
        """音频预处理"""
        pass
    
    async def embed(self, audio_tensor: np.ndarray) -> np.ndarray:
        """音频向量化"""
        pass
```

## 2.5 任务管理系统

### 2.5.1 设计目标与核心原则

**设计目标**：
- **统一调度**：为所有数据处理任务提供统一的调度和管理接口
- **优先级管理**：支持基于任务类型、文件重要性、等待时间的优先级计算
- **并发控制**：根据系统负载动态调整并发任务数量
- **依赖管理**：支持任务间的依赖关系，确保任务按正确顺序执行
- **资源监控**：实时监控CPU、内存、GPU、磁盘IO使用情况
- **错误处理**：自动重试失败的任务，记录错误日志
- **进度跟踪**：实时跟踪任务进度和状态

**核心设计原则**：
- **组件化设计**：将任务管理拆分为多个独立组件，各司其职
- **依赖注入**：通过构造函数注入依赖，提高可测试性
- **配置驱动**：所有重要参数通过配置文件管理
- **异步执行**：支持异步任务执行，提高系统吞吐量
- **容错机制**：优雅处理任务执行过程中的异常情况

### 2.5.2 模块架构

```
┌─────────────────────────────────────────────────────────────────┐
│                      TaskManager                                │
│                   （任务管理器 - 主控制器）                        │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ TaskScheduler   │  │ TaskExecutor    │  │ TaskMonitor     │ │
│  │  任务调度器      │  │  任务执行器      │  │  任务监控器      │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ResourceManager  │  │ConcurrencyMgr   │  │TaskGroupManager │ │
│  │  资源管理器      │  │  并发管理器      │  │  任务组管理器    │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 2.5.3 组件职责边界

#### 2.5.3.0 职责划分原则

**设计原则**：每个组件有明确的单一职责，通过清晰的接口进行协作，避免职责重叠和调度逻辑分散。

| 组件 | 核心职责 | 不承担的职责 | 与其他组件的关系 |
|------|---------|-------------|-----------------|
| **TaskScheduler** | 任务优先级计算、任务队列管理、任务排序和选择 | 不直接执行任务、不管理任务组状态、不处理资源监控 | 向TaskManager提供待执行任务；接收ResourceManager的状态通知；查询TaskGroupManager的锁状态 |
| **TaskExecutor** | 任务执行、错误处理和重试、进度更新、任务状态变更 | 不决定执行顺序、不管理任务队列、不处理优先级 | 接收TaskManager分配的任务；向TaskMonitor报告进度；向TaskGroupManager报告锁释放 |
| **TaskGroupManager** | 任务组管理、任务流水线锁管理、文件级任务组织 | 不执行任务、不计算优先级、不管理资源 | 向TaskScheduler提供锁状态；接收TaskExecutor的锁释放通知；维护文件与任务的映射关系 |
| **ResourceManager** | 资源监控、OOM状态检测、资源预警 | 不直接控制任务执行、不管理任务队列 | 向TaskScheduler发送状态通知；提供资源使用数据供优先级调整参考 |
| **TaskMonitor** | 任务状态跟踪、任务统计、历史记录 | 不执行任务、不调度任务、不管理资源 | 接收所有组件的状态更新；提供查询接口 |

#### 2.5.3.1 组件协作流程

```
┌─────────────────────────────────────────────────────────────────┐
│                     任务调度协作流程                              │
└─────────────────────────────────────────────────────────────────┘

1. 任务创建流程
   TaskManager.create_task()
       ↓
   TaskGroupManager.create_group() / add_task_to_group()
       ↓
   TaskScheduler.enqueue_task() [计算优先级并入队]
       ↓
   TaskMonitor.add_task()

2. 任务调度流程
   TaskManager._schedule_next_task()
       ↓
   TaskScheduler.dequeue_task() [获取最高优先级任务]
       ↓
   TaskGroupManager.is_pipeline_locked() [检查流水线锁]
       ↓
   ResourceManager.check_oom_status() [检查资源状态]
       ↓
   TaskGroupManager.acquire_pipeline_lock() [获取锁 - 核心任务]
       ↓
   TaskExecutor.execute_task()

3. 任务执行完成流程
   TaskExecutor.execute_task() 完成
       ↓
   TaskMonitor.update_task_status()
       ↓
   TaskGroupManager.update_group_progress()
       ↓
   TaskGroupManager.release_pipeline_lock() [释放锁 - 核心任务完成]
       ↓
   TaskManager._schedule_next_task() [调度后续任务]

4. OOM处理流程
   ResourceManager.check_oom_status()
       ↓
   ResourceManager 状态变更 (normal → warning → critical)
       ↓
   TaskScheduler [接收状态通知，调整行为]
       ↓
   TaskScheduler [限制新任务入队 / 取消低优先级任务]
```

#### 2.5.3.2 TaskManager（任务管理器）

**职责**：
- 任务生命周期管理（创建、执行、取消）
- 组件协调和集成（ orchestrator 角色）
- 对外提供统一的任务管理接口
- 调度循环控制

**明确边界**：
- ✅ 负责任务的创建、取消、状态查询
- ✅ 协调各组件完成调度流程
- ✅ 维护调度循环，触发任务调度
- ❌ 不直接计算优先级（委托给TaskScheduler）
- ❌ 不直接执行任务（委托给TaskExecutor）
- ❌ 不直接管理任务组锁（委托给TaskGroupManager）

**类设计**：
```python
class TaskManager:
    """
    任务管理器 - 负责任务生命周期管理、任务调度、任务状态跟踪
    """
    
    def __init__(self, config: Dict[str, Any], device: str = 'cpu'):
        """
        初始化任务管理器
        
        Args:
            config: 配置字典
            device: 设备类型（cuda/cpu）
        """
        self.config = config
        self.device = device
        self.task_config = config.get('task_manager', {})
        
        # 创建组件
        self.task_scheduler = TaskScheduler(self.task_config)
        self.task_executor = TaskExecutor()
        self.resource_manager = ResourceManager(device)
        self.task_monitor = TaskMonitor()
        self.task_group_manager = TaskGroupManager()
        self.concurrency_manager = ConcurrencyManager(
            ConcurrencyConfig(**self.task_config), device
        )
        
        # 任务处理器
        self.task_handlers: Dict[str, Callable] = {}
        
        # 线程控制
        self.is_running = False
        self.worker_thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()
    
    def initialize(self) -> bool:
        """初始化任务管理器"""
        pass
    
    def shutdown(self) -> None:
        """关闭任务管理器"""
        pass
    
    def create_task(
        self,
        task_type: str,
        task_data: Dict[str, Any],
        priority: int = 5,
        file_id: Optional[str] = None,
        depends_on: Optional[List[str]] = None
    ) -> str:
        """
        创建任务
        
        Args:
            task_type: 任务类型
            task_data: 任务数据
            priority: 优先级
            file_id: 文件ID
            depends_on: 依赖的任务ID列表
        
        Returns:
            任务ID
        """
        pass
    
    def register_handler(self, task_type: str, handler: Callable) -> None:
        """注册任务处理器"""
        pass
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        pass
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        pass
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        pass
```

#### 2.5.3.3 TaskScheduler（任务调度器）

**职责**：
- 任务优先级计算（包括基础优先级、文件优先级、类型优先级和等待时间补偿）
- 任务队列管理（PriorityQueue）
- 动态优先级调整（根据资源使用情况和等待时间）
- 任务排序和选择（决定任务执行顺序）
- 响应OOM状态通知，调整调度行为

**明确边界**：
- ✅ 负责计算任务优先级，决定任务执行顺序
- ✅ 管理任务队列，提供入队/出队接口
- ✅ 根据资源状态调整调度策略
- ✅ 查询TaskGroupManager的锁状态，决定是否可调度
- ❌ 不直接执行任务
- ❌ 不直接管理任务组状态
- ❌ 不直接监控资源（接收ResourceManager通知）

**优先级计算公式**：
```
final_priority = base_priority * 1000 + file_priority * 100 + type_priority * 10 + wait_compensation
```

**优先级计算组件说明**：

| 组件 | 权重 | 说明 | 范围 | 作用 |
|------|------|------|------|------|
| base_priority | 1000 | 基础优先级，基于任务类型的重要性 | 0-9 | 决定任务的基本执行顺序 |
| file_priority | 100 | 文件级优先级，基于文件的重要性 | 1-10 | 确保重要文件的任务优先执行 |
| type_priority | 10 | 任务类型优先级，基于任务类型的处理顺序 | 0-9 | 确保同一文件的核心任务优先于辅助任务 |
| wait_compensation | 1 | 等待时间补偿因子，基于任务的等待时间 | 0-999 | 确保长时间等待的任务能够获得更高优先级 |

**等待时间补偿计算**：
```python
wait_time = current_time - task.created_at
wait_compensation = min(999, int(wait_time / 60))  # 每60秒增加1点补偿值
```

**优先级调整策略**：
1. **资源紧张时**：提高用户交互类任务的优先级，降低后台处理任务的优先级
2. **系统空闲时**：按照正常优先级执行所有任务
3. **任务积压时**：提高核心任务的优先级，确保系统能够尽快处理完积压任务

**类设计**：
```python
class TaskScheduler:
    """
    任务调度器 - 负责任务优先级计算和队列管理
    """
    
    def __init__(self, resource_manager=None):
        """初始化任务调度器"""
        self.task_queue = PriorityQueue()
        self.task_priorities: Dict[str, int] = {}
        self.resource_manager = resource_manager
        self._priority_cache: Dict[str, int] = {}
    
    def calculate_priority(self, task: Task, file_info: Dict = None, 
                          file_priority: int = 40) -> int:
        """
        计算任务优先级
        
        Args:
            task: 任务对象
            file_info: 文件信息
            file_priority: 文件级优先级
        
        Returns:
            优先级数值（数值越小优先级越高）
        """
        pass
    
    def enqueue_task(self, task: Task, file_info: Dict = None, 
                     file_priority: int = 40) -> None:
        """将任务加入队列"""
        pass
    
    def dequeue_task(self) -> Optional[Task]:
        """从队列中取出最高优先级的任务"""
        pass
    
    def adjust_priorities(self, tasks: Dict[str, Task]) -> None:
        """动态调整任务优先级"""
        pass
    
    def update_priority(self, task_id: str, new_priority: int) -> bool:
        """更新任务优先级"""
        pass
    
    def cancel_task(self, task_id: str) -> bool:
        """从队列中取消任务"""
        pass
```

**任务类型优先级映射**：
| 任务类型 | 基础优先级 | 类型优先级 | 说明 |
|---------|-----------|-----------|------|
| file_scan | 3 | 3 | 文件扫描 |
| image_preprocess | 1 | 4 | 图像预处理 |
| video_preprocess | 1 | 4 | 视频预处理 |
| audio_preprocess | 1 | 4 | 音频预处理 |
| file_embed_image | 1 | 1 | 图像向量化（高优先级） |
| file_embed_video | 3 | 2 | 视频向量化 |
| file_embed_audio | 4 | 3 | 音频向量化 |
| video_slice | 3 | 2 | 视频切片 |
| thumbnail_generate | 2 | 5 | 缩略图生成 |
| preview_generate | 2 | 6 | 预览生成 |

#### 2.5.3.4 TaskExecutor（任务执行器）

**职责**：
- 任务执行（调用具体的任务处理器）
- 错误处理和重试（处理执行过程中的异常）
- 进度更新（跟踪任务执行进度）
- 任务状态管理（更新任务的运行状态）
- 核心任务完成后通知TaskGroupManager释放流水线锁

**明确边界**：
- ✅ 负责执行具体的任务逻辑
- ✅ 处理任务执行过程中的错误和重试
- ✅ 更新任务执行进度和状态
- ✅ 核心任务完成后通知释放流水线锁
- ❌ 不决定任务执行顺序
- ❌ 不管理任务队列
- ❌ 不计算任务优先级
- ❌ 不直接管理任务组（通过回调通知）

**类设计**：
```python
class TaskExecutor:
    """
    任务执行器 - 负责任务执行和错误处理
    """
    
    def __init__(self):
        """初始化任务执行器"""
        self.handlers: Dict[str, Callable] = {}
    
    def register_handler(self, task_type: str, handler: Callable) -> None:
        """注册任务处理器"""
        pass
    
    def execute_task(self, task: Task) -> bool:
        """
        执行任务
        
        Args:
            task: 任务对象
            
        Returns:
            执行结果（True表示成功，False表示失败）
        """
        pass
    
    def retry_task(self, task: Task) -> bool:
        """重试任务"""
        pass
    
    def update_progress(self, task: Task, progress: float, 
                       current_step: str = None, step_progress: float = None) -> None:
        """更新任务进度"""
        pass
    
    def cancel_task(self, task: Task) -> bool:
        """取消任务执行"""
        pass
    
    def get_handler(self, task_type: str) -> Optional[Callable]:
        """获取任务处理器"""
        pass
```

#### 2.5.3.5 TaskMonitor（任务监控器）

**职责**：
- 任务进度跟踪
- 任务统计
- 任务历史记录
- 事件监听和通知

**明确边界**：
- ✅ 负责跟踪所有任务的状态变化
- ✅ 提供任务统计和历史查询接口
- ✅ 发送任务状态变更通知
- ❌ 不执行任务
- ❌ 不调度任务
- ❌ 不管理资源

**类设计**：
```python
class TaskMonitor:
    """
    任务监控器 - 负责任务进度跟踪和统计
    """
    
    def __init__(self):
        """初始化任务监控器"""
        self.tasks: Dict[str, Task] = {}
        self.task_history: List[Dict] = []
        self.task_statistics: Dict = {
            'total': 0, 'pending': 0, 'running': 0, 
            'completed': 0, 'failed': 0, 'cancelled': 0
        }
        self.task_type_statistics: Dict[str, Dict] = defaultdict(lambda: {
            'total': 0, 'completed': 0, 'failed': 0, 'avg_duration': 0.0
        })
        self.listeners: Dict[str, List] = defaultdict(list)
    
    def add_task(self, task: Task) -> None:
        """添加任务到监控器"""
        pass
    
    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """获取任务状态"""
        pass
    
    def update_task_status(self, task_id: str, status: str, **kwargs) -> bool:
        """更新任务状态"""
        pass
    
    def get_statistics(self) -> Dict:
        """获取任务统计"""
        pass
    
    def generate_report(self) -> Dict:
        """生成任务报告"""
        pass
```

#### 2.5.3.6 ConcurrencyManager（并发管理器）

**职责**：
- 动态并发控制
- 系统资源监控
- 并发数自适应调整

**明确边界**：
- ✅ 负责控制并发任务数量
- ✅ 根据系统负载动态调整并发数
- ✅ 提供并发统计信息
- ❌ 不直接调度任务
- ❌ 不管理任务队列
- ❌ 不处理OOM状态（由ResourceManager处理）

**并发模式**：
- **静态模式**：使用固定的并发数（`base_concurrent_tasks`）
- **动态模式**：根据系统负载动态调整并发数（`min_concurrent_tasks` ~ `max_concurrent_tasks`）

**类设计**：
```python
class ConcurrencyManager:
    """
    并发管理器 - 负责动态调整并发任务数量
    """
    
    def __init__(self, config: ConcurrencyConfig, device: str = 'cpu'):
        """
        初始化并发管理器
        
        Args:
            config: 并发配置
            device: 设备类型（cuda/cpu）
        """
        self.config = config
        self.device = device
        
        # 根据并发模式设置初始并发数
        if config.concurrency_mode == "static":
            self.current_concurrent = config.base_concurrent_tasks
            self.target_concurrent = config.base_concurrent_tasks
        else:
            self.current_concurrent = config.min_concurrent
            self.target_concurrent = config.min_concurrent
        
        # 资源监控
        self.last_resources: Optional[SystemResources] = None
        self.resource_history: list[SystemResources] = []
        
        # 控制线程
        self.is_running = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()
    
    def initialize(self) -> bool:
        """初始化并发管理器"""
        pass
    
    def shutdown(self) -> None:
        """关闭并发管理器"""
        pass
    
    def increment_concurrent(self) -> None:
        """增加并发计数"""
        pass
    
    def decrement_concurrent(self) -> None:
        """减少并发计数"""
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        pass
```

**并发配置参数**：
| 参数 | 说明 | 默认值 |
|------|------|--------|
| concurrency_mode | 并发模式（static/dynamic） | dynamic |
| min_concurrent_tasks | 最小并发数 | 4 |
| max_concurrent_tasks | 最大并发数 | 16 |
| base_concurrent_tasks | 基础并发数（静态模式） | 8 |
| target_cpu_percent | 目标CPU使用率 | 60.0 |
| target_memory_percent | 目标内存使用率 | 70.0 |
| target_gpu_memory_percent | 目标GPU显存使用率 | 80.0 |
| adjustment_interval | 调整间隔（秒） | 5.0 |
| adjustment_step | 调整步长 | 2 |

#### 2.5.3.7 ResourceManager（资源管理器）

**职责**：
- 系统资源监控
- 资源使用统计和历史记录
- 资源预警和OOM状态检测
- 向TaskScheduler发送状态通知

**明确边界**：
- ✅ 负责监控系统资源使用情况
- ✅ 检测OOM状态并发送通知
- ✅ 提供资源使用数据
- ❌ 不直接控制任务执行
- ❌ 不管理任务队列
- ❌ 不直接取消任务（通过通知TaskScheduler）

**监控指标**：
- CPU使用率
- 内存使用率
- GPU显存使用率
- 磁盘IO速率
- 进程内存使用

**OOM处理机制**（简化为2级）：

| 级别 | 内存阈值 | 动作 | 对TaskScheduler的通知 | 恢复条件 |
|------|---------|------|---------------------|---------|
| 正常 | < 85% | 正常执行 | `state: normal` | - |
| 警告 | 85% - 95% | 限制新任务入队，降低并发数 | `state: warning, action: throttle` | 内存使用率 < 80% 持续30秒 |
| 临界 | ≥ 95% | 取消低优先级任务，暂停非关键任务 | `state: critical, action: cancel_low_priority` | 内存使用率 < 85% 持续60秒 |

**与TaskScheduler的解耦设计**：

```python
# ResourceManager 只负责检测和通知
class ResourceManager:
    def check_oom_status(self) -> str:
        memory_usage = self.get_memory_usage()
        if memory_usage >= 95.0:
            return 'critical'
        elif memory_usage >= 85.0:
            return 'warning'
        return 'normal'
    
    def notify_scheduler(self, state: str):
        # 发送状态通知，不直接控制
        self._notify(TaskScheduler, {'oom_state': state})

# TaskScheduler 根据通知调整行为
class TaskScheduler:
    def on_oom_notification(self, notification: Dict):
        state = notification['oom_state']
        if state == 'warning':
            self.throttle_new_tasks()
        elif state == 'critical':
            self.cancel_low_priority_tasks()
```

**关键设计原则**：
1. **状态通知而非直接控制**：ResourceManager只发送状态通知，不直接操作任务队列
2. **调度器自主决策**：TaskScheduler根据通知自主决定如何调整调度策略
3. **降低耦合**：两个组件通过明确的消息接口通信，不直接依赖对方内部实现

**类设计**：
```python
class ResourceManager:
    """
    资源管理器 - 负责系统资源监控和OOM处理
    """
    
    def __init__(self, device: str = 'cpu', oom_config: Dict = None):
        """
        初始化资源管理器
        
        Args:
            device: 设备类型（cuda/cpu）
            oom_config: OOM处理配置
        """
        self.device = device
        self.has_gpu = (device == 'cuda')
        # 简化的2级OOM处理配置
        self.oom_config = oom_config or {
            'enabled': True,
            'warning_threshold': 85.0,  # 警告阈值（%）
            'critical_threshold': 95.0,  # 临界阈值（%）
            'action_warning': "throttle_new_tasks",  # 警告时动作
            'action_critical': "cancel_low_priority_tasks",  # 临界时动作
            'check_interval': 5.0,  # 检查间隔（秒）
            'recovery_timeout': 30.0,  # 恢复超时（秒）
            'max_concurrent_reduction': 0.5  # 警告时并发数减少比例
        }
        # 当前资源状态
        self.current_state = 'normal'  # normal, warning, critical
        self.last_state_change = time.time()
        # 资源历史
        self.resource_history = []
        self.max_history_size = 10
    
    def get_resource_usage(self) -> Dict[str, float]:
        """
        获取资源使用情况
        
        Returns:
            资源使用字典
        """
        pass
    
    def check_resource_available(self) -> bool:
        """检查资源是否可用"""
        pass
    
    def check_oom_status(self) -> str:
        """
        检查OOM状态
        
        Returns:
            当前OOM状态（normal, warning, critical）
        """
        pass
    
    def get_oom_action(self, state: str) -> str:
        """
        获取对应状态的OOM处理动作
        
        Args:
            state: OOM状态
        
        Returns:
            处理动作
        """
        pass
    
    def should_throttle_tasks(self) -> bool:
        """
        是否应该限制任务入队
        
        Returns:
            是否应该限制
        """
        pass
    
    def should_cancel_tasks(self) -> bool:
        """
        是否应该取消低优先级任务
        
        Returns:
            是否应该取消
        """
        pass
    
    def get_recommended_concurrent_reduction(self) -> float:
        """
        获取推荐的并发数减少比例
        
        Returns:
            减少比例（0.0-1.0）
        """
        pass
```

**OOM处理流程**：
1. 资源管理器定期检查系统资源使用情况
2. 根据内存使用率判断当前OOM状态
3. 当内存使用率达到警告阈值（85%）时：
   - 向任务调度器发送警告信号
   - 任务调度器限制新任务入队
   - 减少并发执行的任务数
4. 当内存使用率达到临界阈值（95%）时：
   - 向任务调度器发送临界信号
   - 任务调度器取消低优先级任务
   - 暂停所有非关键任务的执行
5. 当内存使用率恢复到正常水平时：
   - 向任务调度器发送恢复信号
   - 任务调度器恢复正常的任务入队和执行

**与任务调度器的交互**：
- 资源管理器通过状态通知与任务调度器交互，而非直接控制
- 任务调度器根据资源管理器的状态调整自身行为
- 两者之间通过明确的接口通信，降低耦合度

#### 2.5.3.8 TaskGroupManager（任务组管理器）

**职责**：
- 文件级任务组管理（为每个文件创建和管理任务组）
- 任务组进度跟踪（监控同一文件的所有任务进度）
- 任务流水线锁管理（保障同一文件的核心任务连续执行）
- 文件级优先级管理（确保文件级优先级的正确应用）

**明确边界**：
- ✅ 负责管理文件与任务的映射关系
- ✅ 管理任务流水线锁的获取和释放
- ✅ 跟踪任务组进度
- ❌ 不执行任务
- ❌ 不计算优先级
- ❌ 不管理资源
- ❌ 不直接调度任务（提供锁状态供调度器查询）

**任务流水线锁机制**：

**核心任务定义**：
| 任务类型 | 是否核心任务 | 说明 |
|---------|-------------|------|
| file_scan | 否 | 文件扫描，前置任务 |
| image_preprocess | 是 | 图像预处理 |
| video_preprocess | 是 | 视频预处理 |
| audio_preprocess | 是 | 音频预处理 |
| file_embed_image | 是 | 图像向量化 |
| file_embed_video | 是 | 视频向量化 |
| file_embed_audio | 是 | 音频向量化 |
| video_slice | 是 | 视频切片 |
| thumbnail_generate | 否 | 缩略图生成，辅助任务 |
| preview_generate | 否 | 预览生成，辅助任务 |

**锁状态定义**：
| 锁状态 | 含义 | 对核心任务的影响 | 对辅助任务的影响 |
|--------|------|-----------------|-----------------|
| 未锁定 | 无核心任务在执行 | 可获取锁并执行 | 可执行 |
| 锁定 | 有核心任务在执行 | 等待锁释放 | 等待锁释放 |

**锁获取策略**：
1. **首次获取**：当文件的第一个核心任务被调度时，TaskScheduler调用`acquire_pipeline_lock()`获取锁
2. **锁保持**：锁被获取后，同一文件的所有核心任务都可以执行（不阻塞同文件核心任务）
3. **锁释放**：当文件的最后一个核心任务完成时，TaskExecutor通知TaskGroupManager调用`release_pipeline_lock()`释放锁
4. **辅助任务执行**：锁释放后，辅助任务才能开始执行

**锁实现机制**：
```python
class TaskGroupManager:
    def __init__(self):
        self.task_groups: Dict[str, TaskGroup] = {}
        self.pipeline_locks: Dict[str, PipelineLock] = {}  # file_id -> lock
    
    def acquire_pipeline_lock(self, file_id: str, task_id: str) -> bool:
        """
        获取任务流水线锁
        
        策略：
        - 如果锁不存在，创建锁并获取
        - 如果锁存在且是同文件的核心任务，允许执行（不阻塞）
        - 如果锁存在且是其他文件的任务，阻塞等待
        """
        if file_id not in self.pipeline_locks:
            # 创建新锁
            self.pipeline_locks[file_id] = PipelineLock(
                owner_file=file_id,
                owner_task=task_id,
                acquired_at=time.time()
            )
            return True
        
        lock = self.pipeline_locks[file_id]
        if lock.owner_file == file_id:
            # 同文件的核心任务，允许执行
            return True
        
        # 其他文件的任务，需要等待
        return False
    
    def release_pipeline_lock(self, file_id: str, task_id: str) -> bool:
        """
        释放任务流水线锁
        
        策略：
        - 只有锁的拥有者可以释放锁
        - 释放时检查是否还有未完成的同文件核心任务
        - 如果没有，才真正释放锁
        """
        if file_id not in self.pipeline_locks:
            return False
        
        lock = self.pipeline_locks[file_id]
        if lock.owner_task != task_id:
            return False
        
        # 检查是否还有未完成的同文件核心任务
        group = self.task_groups.get(file_id)
        if group and group.has_pending_core_tasks():
            # 还有核心任务未完成，不释放锁
            return False
        
        # 释放锁
        del self.pipeline_locks[file_id]
        return True
    
    def is_pipeline_locked(self, file_id: str) -> bool:
        """检查文件的任务流水线是否被锁定"""
        return file_id in self.pipeline_locks
```

**任务流水线锁使用流程**：
```
场景：文件A的核心任务（预处理+向量化）执行过程中，文件B的任务到达

1. 文件A的第一个核心任务（preprocess）被调度
   TaskScheduler.dequeue_task() -> 文件A的preprocess任务
       ↓
   TaskGroupManager.acquire_pipeline_lock(file_id='A', task_id='preprocess_1')
       ↓
   锁获取成功，开始执行

2. 文件A的核心任务执行中，文件B的任务到达
   TaskScheduler.dequeue_task() -> 文件B的任务（优先级更高）
       ↓
   TaskGroupManager.is_pipeline_locked(file_id='A') -> True
       ↓
   TaskScheduler决定：文件B的任务重新入队等待
       ↓
   继续执行文件A的preprocess任务

3. 文件A的preprocess完成，开始执行embed任务
   TaskExecutor.execute_task() 完成
       ↓
   TaskGroupManager.update_group_progress() 
       ↓
   TaskGroupManager.has_pending_core_tasks(file_id='A') -> True
       ↓
   不释放锁，继续调度文件A的embed任务

4. 文件A的所有核心任务完成
   TaskExecutor.execute_task() 完成
       ↓
   TaskGroupManager.has_pending_core_tasks(file_id='A') -> False
       ↓
   TaskGroupManager.release_pipeline_lock(file_id='A', task_id='embed_1')
       ↓
   锁释放，可以调度其他文件的任务

5. 现在可以调度文件B的任务
   TaskScheduler.dequeue_task() -> 文件B的任务
       ↓
   TaskGroupManager.acquire_pipeline_lock(file_id='B', task_id='...')
       ↓
   开始执行文件B的任务
```

**任务组连续性保障效果**：
- ✅ 确保同一文件的核心任务（预处理+向量化）连续执行
- ✅ 避免其他文件的任务在核心任务执行过程中插入
- ✅ 确保辅助任务（缩略图生成）在核心任务完成后执行
- ✅ 提高文件处理的整体效率和一致性

**类设计**：
```python
class TaskGroupManager:
    """
    任务组管理器 - 负责文件级任务组管理
    """
    
    def __init__(self):
        """初始化任务组管理器"""
        self.task_groups: Dict[str, TaskGroup] = {}  # group_id -> TaskGroup
        self.file_to_group: Dict[str, str] = {}  # file_id -> group_id
        self.active_locks: Dict[str, threading.Lock] = {}  # 文件ID -> 锁对象
        self.lock_owners: Dict[str, str] = {}  # 文件ID -> 任务ID（锁拥有者）
    
    def create_group(self, file_id: str, file_path: str, priority: int = 40) -> str:
        """创建任务组"""
        pass
    
    def add_task_to_group(self, task: Task, file_id: str) -> None:
        """将任务添加到文件对应的任务组"""
        pass
    
    def update_group_progress(self, file_id: str, task_status: str) -> None:
        """更新任务组进度"""
        pass
    
    def get_group_progress(self, file_id: str) -> float:
        """获取任务组进度"""
        pass
    
    def get_group_statistics(self) -> Dict:
        """获取任务组统计"""
        pass
    
    def acquire_pipeline_lock(self, file_id: str, task_id: str) -> bool:
        """
        获取任务流水线锁
        
        Args:
            file_id: 文件ID
            task_id: 任务ID（锁拥有者）
        
        Returns:
            是否获取成功
        """
        pass
    
    def release_pipeline_lock(self, file_id: str, task_id: str) -> bool:
        """
        释放任务流水线锁
        
        Args:
            file_id: 文件ID
            task_id: 任务ID（锁拥有者）
        
        Returns:
            是否释放成功
        """
        pass
    
    def is_pipeline_locked(self, file_id: str) -> bool:
        """
        检查任务流水线是否被锁定
        
        Args:
            file_id: 文件ID
        
        Returns:
            是否被锁定
        """
        pass
    
    def get_lock_owner(self, file_id: str) -> Optional[str]:
        """
        获取锁拥有者
        
        Args:
            file_id: 文件ID
        
        Returns:
            锁拥有者的任务ID
        """
        pass
    
    def should_wait_for_lock(self, file_id: str, task_type: str) -> bool:
        """
        判断任务是否应该等待锁释放
        
        Args:
            file_id: 文件ID
            task_type: 任务类型
        
        Returns:
            是否应该等待
        """
        pass
    
    def get_group(self, file_id: str) -> Optional[TaskGroup]:
        """获取文件对应的任务组"""
        pass
    
    def clear_all_groups(self) -> None:
        """清除所有任务组"""
        pass
```

**任务流水线锁使用流程**：
1. 任务调度器准备执行任务时，检查任务所属的文件
2. 如果任务是核心任务（预处理或向量化）：
   a. 尝试获取任务流水线锁
   b. 如果获取成功，执行任务
   c. 如果获取失败，任务重新入队等待
3. 如果任务是辅助任务（如缩略图生成）：
   a. 检查文件的任务流水线是否被锁定
   b. 如果被锁定，任务重新入队等待
   c. 如果未被锁定，执行任务
4. 核心任务执行完成后，检查同一文件是否还有其他核心任务
5. 如果没有其他核心任务，释放任务流水线锁
6. 辅助任务开始执行

**任务组连续性保障效果**：
- 确保同一文件的核心任务（预处理+向量化）连续执行
- 避免其他文件的任务插入执行
- 确保辅助任务在核心任务完成后执行
- 提高文件处理的整体效率和一致性

### 2.5.4 任务类型定义

**任务分类**：

| 任务类型 | 任务类别 | 基础优先级 | 类型优先级 | 说明 | 依赖任务 |
|---------|---------|-----------|-----------|------|---------|
| file_scan | 前置任务 | 3 | 3 | 文件扫描 | 无 |
| image_preprocess | 核心任务 | 1 | 4 | 图像预处理 | file_scan |
| video_preprocess | 核心任务 | 1 | 4 | 视频预处理 | file_scan |
| audio_preprocess | 核心任务 | 1 | 4 | 音频预处理 | file_scan |
| video_slice | 核心任务 | 3 | 2 | 视频切片 | video_preprocess |
| file_embed_image | 核心任务 | 1 | 1 | 图像向量化 | image_preprocess |
| file_embed_video | 核心任务 | 3 | 2 | 视频向量化 | video_preprocess 或 video_slice |
| file_embed_audio | 核心任务 | 4 | 3 | 音频向量化 | audio_preprocess |
| thumbnail_generate | 辅助任务 | 2 | 5 | 缩略图生成 | file_embed_image, file_embed_video |
| preview_generate | 辅助任务 | 2 | 6 | 预览生成 | file_scan |

**任务类别说明**：
- **前置任务**：文件扫描，为后续任务提供基础信息
- **核心任务**：预处理和向量化任务，必须连续执行，受任务流水线锁保护
- **辅助任务**：缩略图生成、预览生成等，可在核心任务完成后执行

**MVP阶段任务优先级**：
- **P0（最高）**：config_load, database_init, vector_store_init
- **P1（高）**：file_embed_text, file_embed_image（文搜图功能）
- **P2（中高）**：file_scan
- **P3（中）**：video_slice, file_embed_video
- **P4（中低）**：audio_segment, file_embed_audio
- **P5（低）**：search, search_multimodal
- **P6（更低）**：rank_results, filter_results
- **P7（最低）**：thumbnail_generate, preview_generate

### 2.5.5 视频切片时序定位机制

#### 2.5.5.1 切片参数配置

**全局配置参数**（`config/config.yml`）：

```yaml
video_slicing:
  # 切片策略：fixed_duration, scene_based, keyframe_based, hybrid
  strategy: "hybrid"
  
  # 时长控制参数
  max_segment_duration: 5.0      # 最大切片时长（秒）
  min_segment_duration: 0.5      # 最小切片时长（秒）
  segment_overlap: 1.0           # 切片重叠时间（秒）
  short_video_threshold: 6.0     # 短视频阈值（秒）
  
  # 场景检测参数
  scene_detect:
    enabled: true
    threshold: 0.3               # 场景变化阈值（0.1-0.9）
    min_duration: 1.0            # 最小场景时长（秒）
    max_duration: 10.0           # 最大场景时长（秒）
  
  # 关键帧检测参数
  keyframe_detect:
    enabled: true
    interval: 2.0                # 关键帧间隔（秒）
    min_distance: 0.5            # 最小关键帧距离（秒）
  
  # 时间戳映射参数
  timestamp:
    precision: 0.1               # 时间戳精度（秒）
    format: "seconds"            # 时间格式：seconds, milliseconds, timecode
  
  # 输出配置
  output:
    save_thumbnails: true        # 是否保存切片缩略图
    thumbnail_size: [320, 180]   # 缩略图尺寸
    save_metadata: true          # 是否保存切片元数据
```

**参数详细说明**：

| 参数 | 说明 | 默认值 | 范围 | 作用 |
|------|------|--------|------|------|
| **时长控制参数** |
| max_segment_duration | 最大切片时长（秒） | 5.0 | 1.0-30.0 | 控制单个切片的最大长度，避免切片过长影响处理效率 |
| min_segment_duration | 最小切片时长（秒） | 0.5 | 0.1-5.0 | 控制单个切片的最小长度，避免切片过短导致处理开销增大 |
| segment_overlap | 切片重叠时间（秒） | 1.0 | 0.0-2.0 | 确保场景边界的连续性，避免关键信息丢失 |
| short_video_threshold | 短视频阈值（秒） | 6.0 | 3.0-10.0 | 区分短视频和长视频，短视频作为整体处理 |
| **场景检测参数** |
| scene_detect_threshold | 场景变化阈值 | 0.3 | 0.1-0.9 | 控制场景检测的敏感度，值越小检测越敏感 |
| scene_detect_min_duration | 最小场景时长（秒） | 1.0 | 0.5-3.0 | 过滤过短的场景，确保场景的语义完整性 |
| scene_detect_max_duration | 最大场景时长（秒） | 10.0 | 5.0-30.0 | 限制场景的最大长度，避免过长场景 |
| **关键帧检测参数** |
| keyframe_interval | 关键帧间隔（秒） | 2.0 | 0.5-5.0 | 基于关键帧切片时的关键帧间隔 |
| keyframe_min_distance | 最小关键帧距离（秒） | 0.5 | 0.1-2.0 | 避免关键帧过于密集 |
| **时间戳映射参数** |
| timestamp_precision | 时间戳精度（秒） | 0.1 | 0.01-0.5 | 控制时间戳映射的精度，影响时间定位的准确性 |
| timestamp_format | 时间格式 | "seconds" | seconds/milliseconds/timecode | 时间戳的输出格式 |

#### 2.5.5.2 切片策略详解

**1. 固定时长切片（fixed_duration）**

```python
def slice_by_fixed_duration(video_path: str, config: Dict) -> List[VideoSegment]:
    """
    基于固定时长切片
    
    算法：
    1. 获取视频总时长
    2. 如果总时长 <= short_video_threshold，作为单个切片
    3. 否则，按 max_segment_duration 切片，保留 segment_overlap 重叠
    """
    duration = get_video_duration(video_path)
    
    if duration <= config['short_video_threshold']:
        # 短视频，作为整体处理
        return [VideoSegment(
            segment_id=generate_id(),
            start_time=0.0,
            end_time=duration,
            duration=duration
        )]
    
    segments = []
    start_time = 0.0
    
    while start_time < duration:
        end_time = min(start_time + config['max_segment_duration'], duration)
        
        # 确保最后一段不短于 min_segment_duration
        if duration - end_time < config['min_segment_duration']:
            end_time = duration
        
        segment = VideoSegment(
            segment_id=generate_id(),
            start_time=start_time,
            end_time=end_time,
            duration=end_time - start_time
        )
        segments.append(segment)
        
        # 下一个切片的起始时间（考虑重叠）
        start_time = end_time - config['segment_overlap']
        
        if end_time >= duration:
            break
    
    return segments
```

**2. 场景检测切片（scene_based）**

```python
def slice_by_scene_detection(video_path: str, config: Dict) -> List[VideoSegment]:
    """
    基于场景检测切片
    
    算法：
    1. 使用场景检测算法（如pyscenedetect）检测场景边界
    2. 根据配置的阈值过滤场景
    3. 如果场景过长，使用固定时长进一步切片
    4. 如果场景过短，与相邻场景合并
    """
    # 检测场景边界
    scene_boundaries = detect_scenes(
        video_path, 
        threshold=config['scene_detect_threshold']
    )
    
    segments = []
    prev_boundary = 0.0
    
    for boundary in scene_boundaries:
        scene_duration = boundary - prev_boundary
        
        # 过滤过短的场景
        if scene_duration < config['scene_detect_min_duration']:
            continue
        
        # 如果场景过长，进一步切片
        if scene_duration > config['scene_detect_max_duration']:
            sub_segments = slice_long_scene(
                prev_boundary, boundary, config
            )
            segments.extend(sub_segments)
        else:
            segment = VideoSegment(
                segment_id=generate_id(),
                start_time=prev_boundary,
                end_time=boundary,
                duration=scene_duration
            )
            segment.add_scene_boundary(prev_boundary)
            segment.add_scene_boundary(boundary)
            segments.append(segment)
        
        prev_boundary = boundary
    
    # 处理最后一个场景
    duration = get_video_duration(video_path)
    if prev_boundary < duration:
        segment = VideoSegment(
            segment_id=generate_id(),
            start_time=prev_boundary,
            end_time=duration,
            duration=duration - prev_boundary
        )
        segments.append(segment)
    
    return segments
```

**3. 关键帧切片（keyframe_based）**

```python
def slice_by_keyframes(video_path: str, config: Dict) -> List[VideoSegment]:
    """
    基于关键帧切片
    
    算法：
    1. 提取视频的关键帧时间戳
    2. 根据关键帧间隔生成切片
    3. 确保切片在配置的时长范围内
    """
    keyframes = extract_keyframes(video_path)
    
    segments = []
    prev_keyframe = 0.0
    
    for keyframe in keyframes:
        if keyframe - prev_keyframe < config['keyframe_min_distance']:
            continue
        
        segment = VideoSegment(
            segment_id=generate_id(),
            start_time=prev_keyframe,
            end_time=keyframe,
            duration=keyframe - prev_keyframe
        )
        segment.add_key_frame(keyframe)
        segments.append(segment)
        
        prev_keyframe = keyframe
    
    return segments
```

**4. 混合策略（hybrid）**

```python
def slice_hybrid(video_path: str, config: Dict) -> List[VideoSegment]:
    """
    混合切片策略
    
    算法：
    1. 优先尝试场景检测
    2. 如果场景检测失败或场景数量过少，使用关键帧
    3. 如果关键帧也失败，使用固定时长
    4. 确保最终切片符合时长要求
    """
    # 尝试场景检测
    if config['scene_detect']['enabled']:
        segments = slice_by_scene_detection(video_path, config)
        if len(segments) >= 2:
            return segments
    
    # 尝试关键帧
    if config['keyframe_detect']['enabled']:
        segments = slice_by_keyframes(video_path, config)
        if len(segments) >= 2:
            return segments
    
    # 使用固定时长
    return slice_by_fixed_duration(video_path, config)
```

#### 2.5.5.3 时间映射设计

**时间映射原理**：

```
原始视频时间轴：
0s    5s    10s   15s   20s   25s   30s
|-----|-----|-----|-----|-----|-----|
[====Segment 1====][====Segment 2====][====Segment 3====]
0s-10s            10s-20s            20s-30s

切片内相对时间 -> 原始视频绝对时间映射：
Segment 1: relative_time 0s -> original_time 0s
           relative_time 5s -> original_time 5s
           relative_time 10s -> original_time 10s

Segment 2: relative_time 0s -> original_time 10s
           relative_time 5s -> original_time 15s
           relative_time 10s -> original_time 20s
```

**VideoSegment 类设计**：

```python
class VideoSegment:
    """
    视频切片信息
    """
    
    def __init__(self, segment_id: str, start_time: float, end_time: float, duration: float):
        """
        初始化视频切片
        
        Args:
            segment_id: 切片ID
            start_time: 切片在原始视频中的开始时间
            end_time: 切片在原始视频中的结束时间
            duration: 切片时长
        """
        self.segment_id = segment_id
        self.start_time = start_time  # 切片在原始视频中的开始时间
        self.end_time = end_time      # 切片在原始视频中的结束时间
        self.duration = duration      # 切片时长
        self.timestamp_map = {}       # 时间戳映射：切片内时间 -> 原始视频时间
        self.key_frames = []          # 关键帧时间戳（原始视频时间）
        self.scene_boundaries = []     # 场景边界时间戳（原始视频时间）
    
    def generate_timestamp_map(self, precision: float = 0.1):
        """
        生成时间戳映射
        
        Args:
            precision: 时间戳精度（秒）
        """
        current_time = 0.0
        while current_time < self.duration:
            # 切片内时间 -> 原始视频时间
            original_time = self.start_time + current_time
            self.timestamp_map[round(current_time, 2)] = round(original_time, 2)
            current_time += precision
    
    def add_key_frame(self, timestamp: float):
        """
        添加关键帧时间戳
        
        Args:
            timestamp: 关键帧在原始视频中的时间戳
        """
        if self.start_time <= timestamp <= self.end_time:
            self.key_frames.append(timestamp)
    
    def add_scene_boundary(self, timestamp: float):
        """
        添加场景边界时间戳
        
        Args:
            timestamp: 场景边界在原始视频中的时间戳
        """
        if self.start_time <= timestamp <= self.end_time:
            self.scene_boundaries.append(timestamp)
    
    def get_original_time(self, relative_time: float) -> float:
        """
        根据切片内相对时间获取原始视频时间
        
        Args:
            relative_time: 切片内的相对时间
        
        Returns:
            原始视频中的绝对时间
        """
        if relative_time in self.timestamp_map:
            return self.timestamp_map[relative_time]
        # 线性插值计算
        return self.start_time + relative_time
    
    def get_relative_time(self, original_time: float) -> float:
        """
        根据原始视频时间获取切片内相对时间
        
        Args:
            original_time: 原始视频中的绝对时间
        
        Returns:
            切片内的相对时间
        """
        if original_time < self.start_time or original_time > self.end_time:
            raise ValueError(f"Original time {original_time} out of segment bounds [{self.start_time}, {self.end_time}]")
        return original_time - self.start_time
    
    def to_dict(self):
        """
        转换为字典
        
        Returns:
            切片信息字典
        """
        return {
            'segment_id': self.segment_id,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration': self.duration,
            'timestamp_map': self.timestamp_map,
            'key_frames': self.key_frames,
            'scene_boundaries': self.scene_boundaries
        }
```

**切片策略**：
- **fixed_duration**：基于固定时长切片，适用于所有类型的视频，处理简单高效
- **scene_based**：基于场景检测切片，适用于场景变化明显的视频，保持场景的语义完整性
- **keyframe_based**：基于关键帧切片，适用于需要精确时间定位的场景，如视频编辑
- **hybrid**：混合策略（优先场景检测，失败后使用固定时长），适用于各种复杂场景

**时间映射使用流程**：

```
完整时间映射流程：

1. 视频切片阶段
   VideoSlicer.slice_video(video_path)
       ↓
   根据配置选择切片策略
       ↓
   生成 VideoSegment 列表
       ↓
   为每个 segment 生成时间戳映射
       ↓
   segment.generate_timestamp_map(precision=0.1)

2. 向量存储阶段
   将切片向量存入 LanceDB
       ↓
   存储字段：
   - vector: 向量数据
   - file_id: 文件ID
   - segment_id: 切片ID
   - start_time: 切片开始时间（原始视频时间）
   - end_time: 切片结束时间（原始视频时间）
   - timestamp_map: 时间戳映射（JSON格式）

3. 检索阶段
   用户查询 → 向量检索 → 返回匹配切片
       ↓
   根据 segment_id 获取时间映射
       ↓
   展示结果时显示原始视频时间
       ↓
   用户点击结果 → 跳转到原始视频的对应时间点
```

**时间映射使用示例**：

```python
# 示例：用户检索到视频片段，需要定位到原始视频

# 1. 从检索结果获取切片信息
segment_id = "seg_abc123"
segment_info = vector_store.get_segment(segment_id)

# 2. 获取原始视频路径和时间
video_path = segment_info['file_path']
start_time = segment_info['start_time']  # 原始视频开始时间
end_time = segment_info['end_time']      # 原始视频结束时间

# 3. 播放视频时跳转到对应时间点
video_player.play(video_path, start_time=start_time)

# 4. 如果需要精确定位到切片内的某一帧
# 假设用户在切片内看到第3秒的内容
relative_time = 3.0
original_time = segment_info['timestamp_map'][relative_time]
video_player.seek(original_time)
```

**时间映射存储格式**：

```json
{
  "segment_id": "seg_abc123",
  "file_id": "file_xyz789",
  "start_time": 10.0,
  "end_time": 20.0,
  "duration": 10.0,
  "timestamp_map": {
    "0.0": 10.0,
    "0.1": 10.1,
    "0.2": 10.2,
    "...": "...",
    "10.0": 20.0
  },
  "key_frames": [12.5, 15.0, 17.5],
  "scene_boundaries": [10.0, 20.0]
}
```

### 2.5.6 任务依赖管理

**依赖关系示例**：
```
file_scan (P2)
    ↓
├─→ image_preprocess (P1) → file_embed_image (P1) → thumbnail_generate (P7)
├─→ video_preprocess (P1) → video_slice (P3) → file_embed_video (P3) → thumbnail_generate (P7)
└─→ audio_preprocess (P1) → file_embed_audio (P4)
```

**依赖检查机制**：
```python
def check_dependencies(self, task_id: str) -> bool:
    """
    检查任务依赖是否满足
    
    Args:
        task_id: 任务ID
    
    Returns:
        依赖是否满足
    """
    task = self.task_monitor.tasks.get(task_id)
    if not task:
        return False
    
    for dep_id in task.depends_on:
        dep_task = self.task_monitor.tasks.get(dep_id)
        if not dep_task or dep_task.status != 'completed':
            return False
    return True
```

### 2.5.6 配置管理

**任务管理器配置**（`config/config.yml`）：
```yaml
task_manager:
  # 并发模式：static（静态）或 dynamic（动态）
  concurrency_mode: dynamic
  
  # 并发数配置
  min_concurrent_tasks: 4
  max_concurrent_tasks: 16
  base_concurrent_tasks: 8
  
  # 动态并发调整参数
  dynamic_concurrency_interval: 5.0
  dynamic_concurrency_step: 2
  dynamic_concurrency_target_cpu: 60.0
  dynamic_concurrency_target_memory: 70.0
  dynamic_concurrency_target_gpu: 80.0
  
  # 重试配置
  max_retries: 3
  retry_delay: 30
  
  # 任务队列配置
  task_queue_size: 1000
  
  # 文件级优先级配置
  file_priority:
    enabled: true
    default_file_priority: 5
    max_file_priority: 10
    priority_multiplier: 100
    priority_inheritance: true
  
  # OOM处理配置（简化为2级）
  oom_handling:
    enabled: true
    warning_threshold: 85.0  # 警告阈值（%）
    critical_threshold: 95.0  # 临界阈值（%）
    action_warning: "throttle_new_tasks"  # 警告时动作：限制新任务入队
    action_critical: "cancel_low_priority_tasks"  # 临界时动作：取消低优先级任务
    check_interval: 5.0  # 检查间隔（秒）
    recovery_timeout: 30.0  # 恢复超时（秒）
    max_concurrent_reduction: 0.5  # 警告时并发数减少比例
  
  # 按类型的最大并发任务数
  max_concurrent_by_type:
    file_scan: 2
    image_preprocess: 4
    video_preprocess: 2
    audio_preprocess: 2
    file_embed_image: 4
    file_embed_video: 2
    file_embed_audio: 2
    video_slice: 2
    audio_extract: 2
    thumbnail_generate: 4
    preview_generate: 4
```

### 2.5.7 与其他模块的集成

```
┌─────────────────────────────────────────────────────────────────┐
│                         应用层 (main.py)                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      TaskManager                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌──────────┐ │
│  │ TaskScheduler│ │ TaskExecutor│ │ TaskMonitor │ │ Concurrency│ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └──────────┘ │
└─────────────────────────────────────────────────────────────────┘
        │                  │                  │                  │
        ▼                  ▼                  ▼                  ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ ConfigManager│ │MediaProcessor│ │DatabaseMgr  │ │VectorStore  │
└─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘
        │                  │                  │                  │
        └──────────────────┴──────────────────┴──────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      EmbeddingEngine                             │
└─────────────────────────────────────────────────────────────────┘
```

### 2.5.8 任务执行流程

**完整任务执行流程**：
```
1. 任务创建
   ├─ 生成任务ID（UUID）
   ├─ 创建任务对象
   ├─ 设置任务状态为 "pending"
   └─ 记录创建时间

2. 任务入队
   ├─ 计算任务优先级
   ├─ 添加到优先级队列
   └─ 添加到任务监控器

3. 任务调度
   ├─ 从队列中取出最高优先级任务
   ├─ 检查任务依赖是否满足
   ├─ 检查并发限制
   ├─ 检查资源使用情况（OOM处理）
   ├─ 检查任务流水线锁（保障任务组连续性）
   └─ 分配执行资源

4. 任务执行
   ├─ 设置任务状态为 "running"
   ├─ 调用任务处理器执行任务
   ├─ 更新任务进度
   └─ 处理执行结果

5. 结果处理
   ├─ 成功：
   │  ├─ 设置任务状态为 "completed"
   │  ├─ 保存执行结果
   │  └─ 创建后续任务（如果有）
   └─ 失败：
      ├─ 记录错误信息
      ├─ 检查重试次数
      ├─ 未超限：重新入队
      └─ 超限：设置任务状态为 "failed"

6. 资源释放
   ├─ 释放执行资源
   ├─ 减少并发计数
   ├─ 释放任务流水线锁（如果有）
   └─ 更新任务统计
```

### 2.5.9 任务依赖可视化

#### 2.5.9.1 设计目标

- 提供直观的任务依赖关系可视化界面
- 支持查看任务执行顺序和依赖链条
- 帮助用户理解任务执行状态和进度
- 支持交互式操作，如缩放、拖拽、节点点击
- 提供任务执行历史的可视化追踪
- 支持多视图切换（全局视图、文件视图、时间轴视图）

#### 2.5.9.2 UI 布局设计

```
┌─────────────────────────────────────────────────────────────────┐
│                     任务依赖可视化界面                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌─────────────────────────────────────────┐  │
│  │   工具栏      │  │           主视图区域                     │  │
│  │              │  │                                         │  │
│  │ [全局视图]   │  │    ┌─────────────────────────────┐     │  │
│  │ [文件视图]   │  │    │                             │     │  │
│  │ [时间轴]     │  │    │    任务依赖图/时间轴视图      │     │  │
│  │              │  │    │                             │     │  │
│  │ ───────────  │  │    │    (力导向图/分层布局)        │     │  │
│  │              │  │    │                             │     │  │
│  │ 筛选器       │  │    └─────────────────────────────┘     │  │
│  │ □ pending    │  │                                         │  │
│  │ □ running    │  │  ┌─────────────────────────────────┐   │  │
│  │ □ completed  │  │  │        任务详情面板              │   │  │
│  │ □ failed     │  │  │  任务ID: task_123               │   │  │
│  │              │  │  │  类型: image_preprocess         │   │  │
│  │ 类型筛选     │  │  │  状态: running                  │   │  │
│  │ □ 核心任务   │  │  │  进度: 65%                      │   │  │
│  │ □ 辅助任务   │  │  │  依赖: task_001, task_002       │   │  │
│  │              │  │  └─────────────────────────────────┘   │  │
│  │ ───────────  │  │                                         │  │
│  │              │  │                                         │  │
│  │ 统计信息     │  │                                         │  │
│  │ 总任务: 100  │  │                                         │  │
│  │ 进行中: 10   │  │                                         │  │
│  │ 已完成: 80   │  │                                         │  │
│  │ 失败: 5      │  │                                         │  │
│  └──────────────┘  └─────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

#### 2.5.9.3 视图模式

**1. 全局视图（Global View）**

- **布局方式**：力导向图（Force-Directed Graph）
- **展示内容**：系统中所有任务的依赖关系
- **适用场景**：整体任务监控、系统负载查看
- **交互特性**：
  - 支持缩放和平移
  - 节点拖拽调整位置
  - 悬停显示任务概要
  - 点击显示任务详情

**2. 文件视图（File View）**

- **布局方式**：分层布局（Hierarchical Layout）
- **展示内容**：单个文件的所有任务及其依赖关系
- **适用场景**：查看特定文件的处理流程
- **交互特性**：
  - 按任务类型分组显示
  - 显示任务流水线锁状态
  - 突出显示当前执行的任务

**3. 时间轴视图（Timeline View）**

- **布局方式**：水平时间轴
- **展示内容**：任务执行的时间顺序和持续时间
- **适用场景**：性能分析、执行历史查看
- **交互特性**：
  - 时间范围缩放
  - 任务持续时间显示
  - 并发任务可视化

#### 2.5.9.4 依赖图数据结构

```python
class TaskDependencyGraph:
    """
    任务依赖图 - 负责生成和管理任务依赖关系图
    """
    
    def __init__(self, task_monitor: TaskMonitor, task_group_manager: TaskGroupManager):
        self.task_monitor = task_monitor
        self.task_group_manager = task_group_manager
        self.nodes: Dict[str, TaskNode] = {}
        self.edges: List[TaskEdge] = []
        self.groups: Dict[str, TaskGroup] = {}
    
    def add_task(self, task_id: str, task_info: Dict) -> TaskNode:
        """添加任务节点"""
        node = TaskNode(
            id=task_id,
            label=task_info['task_type'],
            type=task_info['task_type'],
            status=task_info['status'],
            priority=task_info['priority'],
            file_id=task_info.get('file_id'),
            created_at=task_info['created_at'],
            started_at=task_info.get('started_at'),
            completed_at=task_info.get('completed_at'),
            progress=task_info.get('progress', 0.0)
        )
        self.nodes[task_id] = node
        return node
    
    def add_dependency(self, from_task: str, to_task: str, dep_type: str = 'strong'):
        """添加依赖关系"""
        edge = TaskEdge(
            source=from_task,
            target=to_task,
            type=dep_type
        )
        self.edges.append(edge)
    
    def add_task_group(self, file_id: str, tasks: List[str]):
        """添加任务组"""
        self.groups[file_id] = TaskGroup(
            file_id=file_id,
            tasks=tasks,
            is_locked=self.task_group_manager.is_pipeline_locked(file_id)
        )
    
    def generate_global_graph(self, filters: Dict = None) -> Dict:
        """生成全局依赖图"""
        # 获取所有任务
        tasks = self.task_monitor.get_all_tasks(filters)
        
        # 构建节点和边
        for task in tasks:
            self.add_task(task['id'], task)
            for dep_id in task.get('depends_on', []):
                self.add_dependency(dep_id, task['id'])
        
        return self._to_graph_data()
    
    def generate_file_graph(self, file_id: str) -> Dict:
        """生成特定文件的依赖图"""
        # 获取文件的所有任务
        tasks = self.task_monitor.get_tasks_by_file(file_id)
        
        for task in tasks:
            self.add_task(task['id'], task)
            # 只添加同一文件内的依赖
            for dep_id in task.get('depends_on', []):
                dep_task = self.task_monitor.get_task(dep_id)
                if dep_task and dep_task.get('file_id') == file_id:
                    self.add_dependency(dep_id, task['id'])
        
        self.add_task_group(file_id, [t['id'] for t in tasks])
        return self._to_graph_data()
    
    def generate_task_chain(self, task_id: str, depth: int = 3) -> Dict:
        """生成特定任务的依赖链"""
        # 获取任务的前置依赖（向上追溯）
        upstream = self._get_upstream_tasks(task_id, depth)
        # 获取任务的后置依赖（向下追溯）
        downstream = self._get_downstream_tasks(task_id, depth)
        
        all_tasks = upstream + [task_id] + downstream
        
        for tid in all_tasks:
            task = self.task_monitor.get_task(tid)
            if task:
                self.add_task(tid, task)
        
        # 添加依赖边
        for tid in all_tasks:
            task = self.task_monitor.get_task(tid)
            if task:
                for dep_id in task.get('depends_on', []):
                    if dep_id in all_tasks:
                        self.add_dependency(dep_id, tid)
        
        return self._to_graph_data()
    
    def _to_graph_data(self) -> Dict:
        """转换为图数据格式"""
        return {
            'nodes': [node.to_dict() for node in self.nodes.values()],
            'edges': [edge.to_dict() for edge in self.edges],
            'groups': [group.to_dict() for group in self.groups.values()],
            'stats': self._calculate_stats()
        }
    
    def _calculate_stats(self) -> Dict:
        """计算统计信息"""
        status_count = defaultdict(int)
        for node in self.nodes.values():
            status_count[node.status] += 1
        
        return {
            'total_tasks': len(self.nodes),
            'pending_tasks': status_count.get('pending', 0),
            'running_tasks': status_count.get('running', 0),
            'completed_tasks': status_count.get('completed', 0),
            'failed_tasks': status_count.get('failed', 0),
            'cancelled_tasks': status_count.get('cancelled', 0)
        }
```

#### 2.5.9.5 前端可视化组件

**技术选型**：
- **图表库**：ECharts 或 D3.js
- **UI框架**：Vue.js 3 或 React
- **状态管理**：Pinia 或 Redux

**组件架构**：

```
src/components/task-visualization/
├── TaskDependencyGraph.vue      # 主组件
├── views/
│   ├── GlobalView.vue           # 全局视图
│   ├── FileView.vue             # 文件视图
│   └── TimelineView.vue         # 时间轴视图
├── components/
│   ├── GraphCanvas.vue          # 图形容器
│   ├── TaskNode.vue             # 任务节点
│   ├── TaskEdge.vue             # 依赖边
│   ├── TaskDetailPanel.vue      # 任务详情面板
│   ├── FilterPanel.vue          # 筛选面板
│   └── StatsPanel.vue           # 统计面板
├── composables/
│   ├── useGraphLayout.ts        # 图形布局逻辑
│   ├── useTaskFilters.ts        # 任务筛选逻辑
│   └── useGraphInteraction.ts   # 交互逻辑
└── types/
    └── graph.types.ts           # 类型定义
```

**视觉设计规范**：

| 元素 | 属性 | 值 | 说明 |
|------|------|-----|------|
| **节点颜色** | pending | #9E9E9E (灰色) | 待处理任务 |
| | running | #2196F3 (蓝色) | 运行中任务 |
| | completed | #4CAF50 (绿色) | 已完成任务 |
| | failed | #F44336 (红色) | 失败任务 |
| | cancelled | #FF9800 (橙色) | 已取消任务 |
| **节点大小** | 基础大小 | 40px | 普通任务 |
| | 高优先级 | 50px | 优先级 < 3 |
| | 低优先级 | 30px | 优先级 > 7 |
| **边样式** | 强依赖 | 实线, 2px, #666 | 必须完成的依赖 |
| | 弱依赖 | 虚线, 1px, #999 | 建议完成的依赖 |
| | 文件组边界 | 点线, 1px, #2196F3 | 同一文件的任务组 |
| **布局** | 全局视图 | 力导向布局 | 自动调整位置 |
| | 文件视图 | 分层布局 | 从上到下排列 |
| | 时间轴 | 水平布局 | 按时间顺序排列 |

#### 2.5.9.6 交互功能

**1. 基础交互**

| 操作 | 功能 | 触发方式 |
|------|------|---------|
| 缩放 | 放大/缩小视图 | 鼠标滚轮 / 捏合手势 |
| 平移 | 移动视图位置 | 拖拽空白区域 |
| 节点拖拽 | 调整节点位置 | 拖拽节点 |
| 悬停 | 显示任务概要 | 鼠标悬停 |
| 点击 | 显示任务详情 | 鼠标点击 |
| 双击 | 聚焦到任务链 | 鼠标双击 |

**2. 筛选功能**

```typescript
interface TaskFilters {
  status: ('pending' | 'running' | 'completed' | 'failed' | 'cancelled')[];
  taskType: ('core' | 'auxiliary' | 'all')[];
  fileId: string | null;
  timeRange: {
    start: Date | null;
    end: Date | null;
  };
  priorityRange: {
    min: number;
    max: number;
  };
}
```

**3. 任务详情面板**

点击任务节点后显示的信息：

```
┌─────────────────────────────────┐
│ 任务详情 - image_preprocess     │
├─────────────────────────────────┤
│ 基本信息                        │
│ ├─ 任务ID: task_img_001         │
│ ├─ 任务类型: 图像预处理          │
│ ├─ 所属文件: photo.jpg          │
│ ├─ 文件ID: file_abc123          │
│ └─ 优先级: 1 (高)               │
│                                 │
│ 状态信息                        │
│ ├─ 状态: 运行中 🟢              │
│ ├─ 进度: 65% [████████░░]       │
│ ├─ 创建时间: 2024-01-01 12:00   │
│ ├─ 开始时间: 2024-01-01 12:01   │
│ └─ 预计完成: 2024-01-01 12:03   │
│                                 │
│ 依赖关系                        │
│ ├─ 前置任务:                    │
│ │  ├─ file_scan (✅ 已完成)     │
│ └─ 后置任务:                    │
│    ├─ file_embed_image (⏳ 等待)│
│    └─ thumbnail_generate (⏳ 等待)│
│                                 │
│ 操作按钮                        │
│ [取消任务] [查看日志] [重试]    │
└─────────────────────────────────┘
```

#### 2.5.9.7 API 接口

**依赖图数据接口**：

```python
from fastapi import APIRouter, Query, Depends
from typing import Optional, List
from datetime import datetime

router = APIRouter(prefix="/api/tasks", tags=["task-visualization"])

@router.get("/dependency-graph")
async def get_task_dependency_graph(
    view_type: str = Query("global", description="视图类型: global, file, timeline"),
    file_id: Optional[str] = Query(None, description="文件ID（文件视图时使用）"),
    task_id: Optional[str] = Query(None, description="任务ID（任务链视图时使用）"),
    status: Optional[List[str]] = Query(None, description="任务状态筛选"),
    task_types: Optional[List[str]] = Query(None, description="任务类型筛选"),
    priority_min: Optional[int] = Query(None, description="最小优先级"),
    priority_max: Optional[int] = Query(None, description="最大优先级"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    graph_service: TaskGraphService = Depends(get_graph_service)
):
    """
    获取任务依赖图数据
    
    Args:
        view_type: 视图类型 (global/file/timeline)
        file_id: 文件ID（文件视图时使用）
        task_id: 任务ID（任务链视图时使用）
        status: 任务状态筛选列表
        task_types: 任务类型筛选列表
        priority_min: 最小优先级
        priority_max: 最大优先级
        start_time: 开始时间
        end_time: 结束时间
    
    Returns:
        依赖图数据，包含节点、边、组和统计信息
    """
    filters = TaskGraphFilter(
        status=status,
        task_types=task_types,
        priority_range=(priority_min, priority_max) if priority_min and priority_max else None,
        time_range=(start_time, end_time) if start_time and end_time else None
    )
    
    if view_type == "global":
        return await graph_service.generate_global_graph(filters)
    elif view_type == "file" and file_id:
        return await graph_service.generate_file_graph(file_id, filters)
    elif view_type == "timeline":
        return await graph_service.generate_timeline_graph(filters)
    else:
        raise HTTPException(status_code=400, detail="Invalid view_type or missing required parameters")

@router.get("/{task_id}/dependency-chain")
async def get_task_dependency_chain(
    task_id: str,
    upstream_depth: int = Query(3, ge=1, le=10, description="上游依赖深度"),
    downstream_depth: int = Query(3, ge=1, le=10, description="下游依赖深度"),
    graph_service: TaskGraphService = Depends(get_graph_service)
):
    """
    获取特定任务的依赖链
    
    Args:
        task_id: 任务ID
        upstream_depth: 上游依赖追溯深度
        downstream_depth: 下游依赖追溯深度
    
    Returns:
        依赖链数据，包含上游和下游任务
    """
    return await graph_service.generate_task_chain(
        task_id, 
        upstream_depth=upstream_depth,
        downstream_depth=downstream_depth
    )

@router.get("/groups/{file_id}/dependency-graph")
async def get_file_task_dependency_graph(
    file_id: str,
    include_auxiliary: bool = Query(True, description="是否包含辅助任务"),
    graph_service: TaskGraphService = Depends(get_graph_service)
):
    """
    获取特定文件的任务依赖图
    
    Args:
        file_id: 文件ID
        include_auxiliary: 是否包含辅助任务（缩略图生成等）
    
    Returns:
        文件任务依赖图数据
    """
    return await graph_service.generate_file_graph(file_id, include_auxiliary=include_auxiliary)

@router.get("/statistics")
async def get_task_statistics(
    time_range: Optional[str] = Query("24h", description="时间范围: 1h, 24h, 7d, 30d"),
    task_service: TaskService = Depends(get_task_service)
):
    """
    获取任务统计信息
    
    Args:
        time_range: 时间范围
    
    Returns:
        任务统计信息
    """
    return await task_service.get_statistics(time_range)

@router.get("/{task_id}/details")
async def get_task_details(
    task_id: str,
    include_logs: bool = Query(False, description="是否包含日志"),
    task_service: TaskService = Depends(get_task_service)
):
    """
    获取任务详细信息
    
    Args:
        task_id: 任务ID
        include_logs: 是否包含执行日志
    
    Returns:
        任务详细信息
    """
    return await task_service.get_task_details(task_id, include_logs=include_logs)
```

**WebSocket 实时更新接口**：

```python
@router.websocket("/ws/graph-updates")
async def graph_updates_websocket(
    websocket: WebSocket,
    graph_service: TaskGraphService = Depends(get_graph_service)
):
    """
    WebSocket 接口，实时推送任务图更新
    
    推送事件类型：
    - task_created: 新任务创建
    - task_started: 任务开始执行
    - task_completed: 任务完成
    - task_failed: 任务失败
    - task_cancelled: 任务取消
    - dependency_added: 添加依赖关系
    - graph_refresh: 强制刷新整个图
    """
    await websocket.accept()
    
    # 订阅任务更新事件
    subscription = await graph_service.subscribe_updates()
    
    try:
        while True:
            # 等待任务更新事件
            event = await subscription.get_event()
            
            # 推送更新到客户端
            await websocket.send_json({
                "event_type": event.type,
                "timestamp": event.timestamp,
                "data": event.data
            })
    except WebSocketDisconnect:
        await subscription.unsubscribe()
```

**数据模型**：

```python
from pydantic import BaseModel
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from enum import Enum

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskNode(BaseModel):
    """任务节点数据模型"""
    id: str
    label: str
    type: str
    status: TaskStatus
    priority: int
    file_id: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration: Optional[float]  # 执行时长（秒）
    progress: float  # 进度 0.0-1.0
    x: Optional[float]  # 布局坐标X
    y: Optional[float]  # 布局坐标Y
    
    def to_dict(self) -> Dict:
        return self.dict()

class TaskEdge(BaseModel):
    """任务边数据模型"""
    source: str  # 源任务ID
    target: str  # 目标任务ID
    type: str = "strong"  # 依赖类型: strong, weak
    label: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return self.dict()

class TaskGroup(BaseModel):
    """任务组数据模型"""
    file_id: str
    file_name: Optional[str]
    tasks: List[str]
    is_locked: bool
    lock_owner: Optional[str]
    
    def to_dict(self) -> Dict:
        return self.dict()

class GraphStatistics(BaseModel):
    """图统计信息"""
    total_tasks: int
    pending_tasks: int
    running_tasks: int
    completed_tasks: int
    failed_tasks: int
    cancelled_tasks: int
    avg_duration: Optional[float]
    total_duration: Optional[float]

class TaskDependencyGraphData(BaseModel):
    """任务依赖图完整数据"""
    nodes: List[TaskNode]
    edges: List[TaskEdge]
    groups: List[TaskGroup]
    stats: GraphStatistics
    generated_at: datetime
    view_type: str

class TaskGraphFilter(BaseModel):
    """任务图筛选条件"""
    status: Optional[List[str]] = None
    task_types: Optional[List[str]] = None
    priority_range: Optional[Tuple[int, int]] = None
    time_range: Optional[Tuple[datetime, datetime]] = None
    file_id: Optional[str] = None
```

4. **数据结构**：

**节点数据结构**：
```json
{
  "id": "task_123",
  "label": "image_preprocess",
  "type": "image_preprocess",
  "status": "completed",
  "priority": 1,
  "file_id": "file_456",
  "created_at": "2023-01-01T12:00:00",
  "started_at": "2023-01-01T12:01:00",
  "completed_at": "2023-01-01T12:02:00",
  "duration": 60,
  "progress": 1.0,
  "group_id": "group_456"
}
```

**边数据结构**：
```json
{
  "source": "task_123",
  "target": "task_789",
  "type": "strong",
  "label": "依赖"
}
```

**图数据结构**：
```json
{
  "nodes": [/* 节点数据 */],
  "edges": [/* 边数据 */],
  "groups": [/* 任务组数据 */],
  "stats": {
    "total_tasks": 100,
    "completed_tasks": 80,
    "running_tasks": 10,
    "failed_tasks": 5,
    "pending_tasks": 5
  }
}
```

#### 2.5.9.8 使用场景

**1. 任务监控场景**

```
场景：管理员需要查看当前系统任务执行情况

操作流程：
1. 打开任务依赖可视化界面
2. 选择"全局视图"模式
3. 查看任务统计面板
   - 总任务数、进行中、已完成、失败任务数
4. 观察依赖图
   - 蓝色节点：正在执行的任务
   - 绿色节点：已完成的任务
   - 红色节点：失败的任务
5. 点击红色节点查看失败原因
6. 根据依赖关系判断失败影响范围
```

**2. 问题排查场景**

```
场景：用户反馈某个文件处理失败，需要定位问题

操作流程：
1. 在搜索框输入文件名
2. 切换到"文件视图"模式
3. 查看该文件的所有任务
4. 识别失败的任务节点（红色）
5. 点击失败任务查看详情
   - 错误信息
   - 执行日志
   - 前置依赖任务状态
6. 如果前置任务失败，向上追溯直到找到根因
7. 根据依赖链确定需要重试的任务范围
```

**3. 性能分析场景**

```
场景：系统处理速度慢，需要找出性能瓶颈

操作流程：
1. 切换到"时间轴视图"模式
2. 选择较长的时间范围（如7天）
3. 观察任务执行时间分布
4. 识别执行时间较长的任务类型
5. 查看并发任务数量变化
6. 分析资源使用与任务执行的关系
7. 根据分析结果调整并发配置
```

**4. 资源规划场景**

```
场景：需要评估系统容量，规划资源扩容

操作流程：
1. 查看全局视图的统计信息
2. 分析任务队列积压情况
3. 观察不同任务类型的执行时间
4. 识别资源竞争严重的任务类型
5. 基于依赖关系优化任务调度策略
6. 估算增加并发数对系统的影响
```

**5. 用户交互场景**

```
场景：普通用户想了解自己的文件处理进度

操作流程：
1. 用户登录系统
2. 进入任务管理页面
3. 系统自动显示用户文件的任务依赖图
4. 用户可以看到：
   - 哪些文件正在处理
   - 每个文件的处理进度
   - 当前执行到哪个步骤
   - 预计完成时间
5. 点击具体任务可以查看详细信息
6. 如果任务失败，可以查看错误信息并选择重试
```

#### 2.5.9.9 性能优化

**前端性能优化**：
- **虚拟滚动**：当任务数量超过1000时，使用虚拟滚动只渲染可见区域
- **增量更新**：通过WebSocket接收增量更新，避免全量刷新
- **数据缓存**：客户端缓存任务数据，减少API请求
- **懒加载**：任务详情和日志采用懒加载策略

**后端性能优化**：
- **数据预计算**：定期预计算常用视图的图数据
- **缓存策略**：SQLite数据库 + 内存LRU缓存热点数据（如正在执行的任务图）
- **分页查询**：大量任务时分页返回，避免内存溢出
- **异步生成**：复杂依赖图异步生成，先返回简化版本

### 2.5.10 性能优化

**并发控制优化**：
- 动态调整并发数，根据系统负载自动优化
- 按任务类型限制并发数，避免资源竞争
- 支持静态和动态两种并发模式

**优先级优化**：
- 多维度优先级计算（任务类型、文件优先级、等待时间）
- 动态优先级调整，根据资源使用情况提升重要任务
- 优先级缓存，避免重复计算

**资源监控优化**：
- 定期采样系统资源使用情况
- 基于历史数据预测资源需求
- 资源预警机制，避免系统过载

**错误处理优化**：
- 自动重试失败任务（最多3次）
- 错误日志记录，便于问题排查
- 优雅降级，避免级联失败

## 2.6 向量化引擎

### 2.6.1 EmbeddingEngine 类设计

```python
class EmbeddingEngine:
    """
    向量化引擎 - 负责所有类型数据的向量化
    """
    
    def __init__(self, config: ConfigManager, model_manager: ModelManager):
        self.config = config
        self.model_manager = model_manager
        
    async def embed_text(self, texts: List[str]) -> np.ndarray:
        """文本向量化"""
        pass
    
    async def embed_image(self, images: List[str]) -> np.ndarray:
        """图像向量化"""
        pass
    
    async def embed_video(self, videos: List[str]) -> np.ndarray:
        """视频向量化"""
        pass
    
    async def embed_audio(self, audios: List[str]) -> np.ndarray:
        """音频向量化"""
        pass
    
    async def embed_multimodal(self, inputs: List[str], input_type: str) -> np.ndarray:
        """多模态向量化"""
        pass
```

## 2.7 向量存储系统

### 2.7.1 VectorStore 类设计

```python
class VectorStore:
    """
    向量存储 - 负责向量数据的存储和检索
    """
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.db: lancedb.DBConnection = None
        self.table: lancedb.table = None
        
    async def initialize(self) -> None:
        """初始化向量存储"""
        pass
    
    async def insert(self, vectors: np.ndarray, metadata: List[Dict]) -> None:
        """插入向量"""
        pass
    
    async def search(self, query_vector: np.ndarray, top_k: int = 20, filters: Dict = None) -> List[SearchResult]:
        """向量检索"""
        pass
    
    async def delete(self, file_id: str) -> None:
        """删除向量"""
        pass
    
    async def update(self, file_id: str, vectors: np.ndarray) -> None:
        """更新向量"""
        pass
    
    async def create_index(self) -> None:
        """创建向量索引"""
        pass
```

### ⚠️ 关键提示：相似度计算（重要）

**问题根源**：如果文字检索结果关联度不高，90%的情况是相似度计算公式错误。

**LanceDB距离类型**：
- LanceDB默认使用**余弦距离**（Cosine Distance）
- 公式：`distance = 1 - cosine_similarity`
- 范围：`[0, 2]`

**CLIP模型相似度**：
- CLIP模型使用**余弦相似度**（Cosine Similarity）
- 范围：`[-1, 1]`
- 1.0：完全相同，0.0：无关/正交，-1.0：完全相反

**正确的相似度转换公式**：

```python
# ✅ 正确：适用于余弦距离（CLIP模型）
similarity = 1.0 - float(row['_distance'])
similarity = max(0.0, min(1.0, similarity))  # 确保在[0,1]范围内

# ❌ 错误：适用于欧氏距离，不适用于余弦距离
similarity = 1.0 / (1.0 + float(row['_distance']))
```

**为什么不能使用欧氏距离公式？**
- 欧氏距离公式 `1/(1+distance)` 适用于欧氏距离（范围 `[0, +∞)`）
- 余弦距离的范围是 `[0, 2]`，使用欧氏距离公式会导致相似度值偏低
- 例如：距离0.3（高度相关）→ 欧氏公式给出0.77，实际应该是0.70

**相似度阈值配置**：

```yaml
search:
  similarity_threshold: 0.3  # 推荐值：0.3（使用正确的余弦距离转换后）
```

**阈值设置建议**：
- 使用正确的余弦距离转换后，推荐阈值为 **0.3**
- 距离0.3对应相似度0.7（高度相关）
- 距离0.5对应相似度0.5（中等相关）
- 距离0.7对应相似度0.3（低度相关）

**实现示例**（`src/core/vector/vector_store.py`）：

```python
def _results_to_dicts(self, results) -> List[Dict[str, Any]]:
    """将查询结果转换为字典列表"""
    result_list = []
    for _, row in results.iterrows():
        # 计算相似度（关键修复点）
        # LanceDB返回的是余弦距离（1 - cosine_similarity）
        # 所以需要用 1 - distance 转换为相似度
        similarity = 1.0 - float(row['_distance']) if '_distance' in row else 0.0
        # 确保相似度在[0, 1]范围内
        similarity = max(0.0, min(1.0, similarity))
        
        result = {
            'id': row['id'],
            'vector': row['vector'].tolist(),
            'modality': row['modality'],
            'file_id': row['file_id'],
            'similarity': similarity,  # 使用正确的相似度
            '_distance': float(row['_distance']),
            '_score': similarity  # 确保与similarity一致
        }
        result_list.append(result)
    
    return result_list
```

**验证方法**：
1. 检查相似度值是否在合理范围（0.0-1.0）
2. 高度相关结果（距离<0.3）应该有较高的相似度（>0.7）
3. 低度相关结果（距离>0.7）应该有较低的相似度（<0.3）

**常见错误**：
- ❌ 使用 `1/(1+distance)` 转换余弦距离
- ❌ 相似度阈值设置过高（如0.7）
- ❌ 忘记将 `_score` 字段与 `similarity` 保持一致

**故障排查清单**：
1. 检查相似度计算公式是否使用 `1.0 - distance`
2. 检查相似度阈值是否设置为0.3（而不是0.7）
3. 检查 `_score` 字段是否与 `similarity` 一致
4. 验证距离值是否在 `[0, 2]` 范围内（余弦距离）
5. 测试搜索结果的相关性是否提升

## 2.8 检索引擎

### 2.7.1 SearchEngine 类设计

```python
class SearchEngine:
    """
    搜索引擎 - 负责处理用户查询和返回检索结果
    """
    
    def __init__(self, config: ConfigManager, vector_store: VectorStore, model_manager: ModelManager):
        self.config = config
        self.vector_store = vector_store
        self.model_manager = model_manager
        
    async def search_text(self, query: str, top_k: int = 20) -> List[SearchResult]:
        """文本检索"""
        pass
    
    async def search_image(self, image_path: str, top_k: int = 20) -> List[SearchResult]:
        """图像检索"""
        pass
    
    async def search_video(self, video_path: str, top_k: int = 20) -> List[SearchResult]:
        """视频检索"""
        pass
    
    async def search_audio(self, audio_path: str, top_k: int = 20) -> List[SearchResult]:
        """音频检索"""
        pass
    
    async def rerank(self, query: str, results: List[SearchResult], top_k: int = 10) -> List[SearchResult]:
        """结果重排序"""
        pass
    
    def deduplicate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """结果去重"""
        pass
```

## 2.9 WebUI 系统

### 2.8.1 WebUI 架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         WebUI 架构图                                         │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   用户浏览器  │────▶│  Gradio 服务器 │────▶│  SearchEngine │────▶│  VectorStore │
│              │     │               │     │               │     │              │
└─────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
       │                   │                    │                    │
       ▼                   ▼                    ▼                    ▼
┌─────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  搜索界面   │     │  API 路由    │     │  向量化引擎   │     │  数据库      │
│              │     │               │     │               │     │              │
└─────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
       │                   │
       ▼                   ▼
┌─────────────┐     ┌──────────────┐
│  结果展示   │     │  任务队列    │
│              │     │               │
└─────────────┘     └──────────────┘
```

### 2.8.2 WebUI 组件设计

```python
class WebUI:
    """
    WebUI - 负责提供用户界面
    """
    
    def __init__(self, config: ConfigManager, search_engine: SearchEngine, task_manager: TaskManager):
        self.config = config
        self.search_engine = search_engine
        self.task_manager = task_manager
        self.demo: gr.Blocks = None
        
    def build(self) -> gr.Blocks:
        """构建 WebUI"""
        pass
    
    def build_search_tab(self) -> gr.Tab:
        """构建搜索标签页"""
        pass
    
    def build_index_tab(self) -> gr.Tab:
        """构建索引标签页"""
        pass
    
    def build_settings_tab(self) -> gr.Tab:
        """构建设置标签页"""
        pass
    
    async def launch(self) -> None:
        """启动 WebUI"""
        pass
```

---

## 2.10 桌面 UI 系统

### 2.9.1 桌面 UI 概述

桌面 UI 是 msearch 的原生客户端界面，基于 PySide6 框架开发，提供更流畅的用户体验和更丰富的功能。相比 WebUI，桌面 UI 具有以下优势：

**性能优势**：
- 原生性能，无需浏览器开销
- 更低的内存占用
- 更快的响应速度
- 更好的系统集成

**功能优势**：
- 系统托盘支持
- 全局快捷键
- 文件拖拽支持
- 更好的文件预览
- 离线工作模式

**用户体验**：
- 更自然的交互方式
- 自定义主题支持
- 多窗口管理
- 更好的高 DPI 支持

### 2.9.2 桌面 UI 架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          桌面 UI 架构图                                     │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                            MainWindow                                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  菜单栏      │  │  工具栏      │  │  状态栏      │  │  主内容区    │         │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
        ┌──────────────────────────┼──────────────────────────┐
        ▼                          ▼                          ▼
┌──────────────┐          ┌──────────────┐          ┌──────────────┐
│ SearchModule │          │  DataModule  │          │ ConfigModule │
│  搜索模块     │          │  数据管理模块  │          │  配置模块     │
└──────────────┘          └──────────────┘          └──────────────┘
        │                          │                          │
        ▼                          ▼                          ▼
┌──────────────┐          ┌──────────────┐          ┌──────────────┐
│  SearchBar   │          │  DataManager │          │  Settings    │
│  搜索栏       │          │  数据管理器   │          │  设置面板     │
└──────────────┘          └──────────────┘          └──────────────┘
        │                          │                          │
        ▼                          ▼                          ▼
┌──────────────┐          ┌──────────────┐          ┌──────────────┐
│ ResultPanel  │          │  TaskManager │          │  AboutDialog │
│ 结果展示面板   │          │  任务管理器   │          │  关于对话框   │
└──────────────┘          └──────────────┘          └──────────────┘
```

### 2.9.3 核心组件设计

**主窗口**：
- 顶部工具栏（Logo、功能按钮）
- 左侧面板（搜索栏、过滤面板、统计信息）
- 右侧面板（结果展示区）
- 底部状态栏（状态信息、资源监控）

**搜索模块**：
- 多模态搜索支持（文本、图像、视频、音频）
- 实时搜索建议
- 搜索历史记录
- 搜索过滤和排序

**数据管理模块**：
- 索引管理（添加、删除、扫描）
- 任务管理（任务列表、进度监控）
- 数据统计（文件数量、索引大小）
- 数据导出和备份

**配置模块**：
- 常规设置（语言、主题）
- 模型设置（模型路径、模型选择）
- 高级设置（性能优化、高级选项）
- 快捷键设置

### 2.9.4 设计特点

**现代扁平化设计**：
- 简洁的视觉风格
- 清晰的视觉层次
- 适当的留白和间距
- 柔和的阴影效果

**配色方案**：
- 主色调：深蓝色系（#165DFF）- 专业、可信赖
- 辅助色：橙色系（#FF7D00）- 活力、创新
- 中性色：深灰、中灰、浅灰
- 支持浅色和深色主题

**交互设计**：
- 直观的操作流程
- 实时状态反馈
- 流畅的动画效果
- 完善的错误处理

### 2.9.5 详细设计文档

完整的桌面 UI 设计文档请参考：
- [PySide6 桌面 UI 设计方案](pyside6_ui_design.md)

该文档包含：
- 完整的 UI 设计原则
- 详细的组件设计代码
- 样式管理和主题系统
- 性能优化策略
- 测试和部署方案

---

## 2.11 API服务设计

### 2.11.1 API设计原则

**RESTful API设计**：
- 遵循REST架构风格
- 使用标准HTTP方法（GET、POST、PUT、DELETE）
- 统一的响应格式
- 清晰的错误处理
- 完整的API文档

**分层架构**：
```
API层 (src/api/)
├── __init__.py
├── api_server.py          # API服务器主入口
└── v1/                   # API v1版本
    ├── __init__.py
    ├── routes.py           # 路由定义
    ├── handlers.py         # 请求处理器
    └── schemas.py          # 数据模型定义
```

**依赖注入**：
- 所有业务逻辑通过依赖注入获取
- 便于测试和模块解耦
- 支持多种部署方式

### 2.11.2 API端点设计

#### 搜索端点

**文本搜索**：
```http
POST /api/v1/search/text
Content-Type: application/json

{
  "query": "搜索查询文本",
  "top_k": 20,
  "modality": "all"
}

Response:
{
  "success": true,
  "query": "搜索查询文本",
  "total": 15,
  "results": [
    {
      "file_uuid": "uuid-1234",
      "file_name": "image.jpg",
      "file_path": "/path/to/image.jpg",
      "modality": "image",
      "score": 0.9543,
      "metadata": {...}
    }
  ]
}
```

**图像搜索**：
```http
POST /api/v1/search/image
Content-Type: multipart/form-data

image: <binary>

Response:
{
  "success": true,
  "image": "image.jpg",
  "total": 10,
  "results": [...]
}
```

**视频搜索**：
```http
POST /api/v1/search/video
Content-Type: application/json

{
  "query": "视频查询文本",
  "top_k": 20
}

Response:
{
  "success": true,
  "query": "视频查询文本",
  "total": 8,
  "results": [
    {
      "file_uuid": "uuid-5678",
      "file_name": "video.mp4",
      "file_path": "/path/to/video.mp4",
      "modality": "video",
      "score": 0.8765,
      "timestamp": {
        "start_time": 10.5,
        "end_time": 15.2,
        "segment_id": "seg_001"
      }
    }
  ]
}
```

**音频搜索**：
```http
POST /api/v1/search/audio
Content-Type: multipart/form-data

audio: <binary>

Response:
{
  "success": true,
  "audio": "audio.wav",
  "total": 5,
  "results": [...]
}
```

#### 索引端点

**索引单个文件**：
```http
POST /api/v1/index/file
Content-Type: application/x-www-form-urlencoded

file_path=/path/to/file.jpg

Response:
{
  "success": true,
  "message": "文件已添加到索引队列",
  "data": {
    "task_id": "task-1234"
  }
}
```

**索引目录**：
```http
POST /api/v1/index/directory
Content-Type: application/x-www-form-urlencoded

directory=/path/to/directory
recursive=true

Response:
{
  "success": true,
  "message": "目录索引任务已创建",
  "data": {
    "task_id": "task-5678",
    "stats": {
      "total_files": 150,
      "image_files": 80,
      "video_files": 50,
      "audio_files": 20
    }
  }
}
```

**重新索引所有文件**：
```http
POST /api/v1/index/reindex-all
Content-Type: application/json

Response:
{
  "success": true,
  "message": "重新索引任务已创建",
  "data": {
    "task_id": "task-9012"
  }
}
```

**获取索引状态**：
```http
GET /api/v1/index/status

Response:
{
  "success": true,
  "stats": {
    "total_files": 500,
    "indexed_files": 450,
    "pending_files": 50,
    "processing_files": 10,
    "failed_files": 5,
    "modality_counts": {
      "image": 300,
      "video": 120,
      "audio": 80
    }
  },
  "last_index_time": "2026-01-28T10:30:00Z",
  "current_tasks": [
    {
      "task_id": "task-1234",
      "task_type": "image_preprocess",
      "progress": 0.75,
      "status": "processing"
    }
  ]
}
```

#### 文件管理端点

**获取文件列表**：
```http
GET /api/v1/files/list?file_type=image&indexed_only=true&limit=20&offset=0

Response:
{
  "success": true,
  "total": 100,
  "files": [
    {
      "file_uuid": "uuid-1234",
      "file_name": "image.jpg",
      "file_path": "/path/to/image.jpg",
      "file_type": "image",
      "file_size": 1024000,
      "indexed": true,
      "indexed_at": "2026-01-28T10:00:00Z"
    }
  ]
}
```

**获取文件信息**：
```http
GET /api/v1/files/{file_uuid}

Response:
{
  "success": true,
  "file_uuid": "uuid-1234",
  "file_name": "image.jpg",
  "file_path": "/path/to/image.jpg",
  "file_type": "image",
  "file_size": 1024000,
  "indexed": true,
  "indexed_at": "2022026-01-28T10:00:00Z",
  "metadata": {
    "width": 1920,
    "height": 1080,
    "format": "JPEG",
    "created_at": "2026-01-28T09:00:00Z"
  }
}
```

**获取文件预览**：
```http
GET /api/v1/files/preview?path=/path/to/image.jpg

Response: <image/jpeg binary>
```

**获取文件缩略图**：
```http
GET /api/v1/files/thumbnail?path=/path/to/image.jpg

Response: <image/jpeg binary>
```

#### 任务管理端点

**获取任务列表**：
```http
GET /api/v1/tasks/list?task_type=image_preprocess&status=processing&limit=20&offset=0

Response:
{
  "success": true,
  "total": 50,
  "tasks": [
    {
      "id": "task-1234",
      "task_type": "image_preprocess",
      "status": "processing",
      "priority": 1,
      "progress": 0.75,
      "current_step": "向量化处理",
      "step_progress": 0.5,
      "created_at": "2026-01-28T10:00:00Z",
      "started_at": "2026-01-28T10:01:00Z",
      "task_data": {
        "file_path": "/path/to/image.jpg"
      }
    }
  ]
}
```

**获取任务详情**：
```http
GET /api/v1/tasks/{task_id}

Response:
{
  "success": true,
  "id": "task-1234",
  "task_type": "image_preprocess",
  "status": "processing",
  "priority": 1,
  "progress": 0.75,
  "current_step": "向量化处理",
  "step_progress": 0.5,
  "created_at": "2026-01-28T10:00:00Z",
  "started_at": "2026-01-28T10:01:00Z",
  "task_data": {
    "file_path": "/path/to/image.jpg"
  },
  "result": null,
  "error": null
}
```

**取消任务**：
```http
DELETE /api/v1/tasks/{task_id}

Response:
{
  "success": true,
  "message": "任务已取消"
}
```

**更新任务优先级**：
```http
POST /api/v1/tasks/{task_id}/priority
Content-Type: application/json

{
  "priority": 3
}

Response:
{
  "success": true,
  "message": "任务优先级已更新",
  "result": {
    "task_id": "task-1234",
    "old_priority": 5,
    "new_priority": 3
  }
}
```

**取消所有任务**：
```http
POST /api/v1/tasks/cancel-all
Content-Type: application/json

{
  "cancel_running": "false"
}

Response:
{
  "success": true,
  "message": "批量取消任务完成",
  "result": {
    "cancelled": 45,
    "failed": 5,
    "total": 50
  }
}
```

**按类型取消任务**：
```http
POST /api/v1/tasks/cancel-by-type
Content-Type: application/json

{
  "task_type": "image_preprocess",
  "cancel_running": "false"
}

Response:
{
  "success": true,
  "message": "批量取消任务完成",
  "result": {
    "task_type": "image_preprocess",
    "cancelled": 30,
    "failed": 2,
    "total": 32
  }
}
```

**获取任务统计**：
```http
GET /api/v1/tasks/stats

Response:
{
  "success": true,
  "task_stats": {
    "overall": {
      "total": 100,
      "pending": 20,
      "running": 5,
      "completed": 70,
      "failed": 3,
      "cancelled": 2
    },
    "by_type": {
      "image_preprocess": {
        "total": 30,
        "completed": 25,
        "failed": 2
      },
      "video_preprocess": {
        "total": 25,
        "completed": 20,
        "failed": 1
      }
    }
  },
  "concurrency": 4,
  "resource_usage": {
    "cpu_percent": 45.2,
    "memory_percent": 62.8,
    "gpu_percent": 78.5
  }
}
```

#### 系统信息端点

**获取系统信息**：
```http
GET /api/v1/system/info

Response:
{
  "success": true,
  "version": "1.0.0",
  "config": {
    "models": {
      "image_video_model": "chinese-clip-vit-base-patch16",
      "audio_model": "laion/clap-htsat-unfused"
    },
    "device": "cuda",
    "batch_size": 16
  }
}
```

**获取系统统计**：
```http
GET /api/v1/system/stats

Response:
{
  "success": true,
  "stats": {
    "total_files": 500,
    "indexed_files": 450,
    "total_vectors": 450,
    "database_size": "2.5GB",
    "vector_db_size": "1.8GB"
  }
}
```

**健康检查**：
```http
GET /api/v1/health

Response:
{
  "status": "healthy",
  "service": "msearch API",
  "version": "1.0.0"
}
```

### 2.11.3 API数据模型

#### 搜索相关模型

**TextSearchRequest**：
```python
class TextSearchRequest(BaseModel):
    query: str
    top_k: int = 20
    modality: str = "all"  # all, image, video, audio
```

**ImageSearchRequest**：
```python
class ImageSearchRequest(BaseModel):
    top_k: int = 20
```

**VideoSearchRequest**：
```python
class VideoSearchRequest(BaseModel):
    query: str
    top_k: int = 20
```

**AudioSearchRequest**：
```python
class AudioSearchRequest(BaseModel):
    top_k: int = 20
```

**SearchResponse**：
```python
class SearchResponse(BaseModel):
    success: bool
    query: Optional[str] = None
    image: Optional[str] = None
    audio: Optional[str] = None
    video: Optional[str] = None
    total: int
    results: List[SearchResult]
```

**SearchResult**：
```python
class SearchResult(BaseModel):
    file_uuid: str
    file_name: str
    file_path: str
    modality: str  # image, video, audio
    score: float
    metadata: Dict[str, Any]
    timestamp: Optional[Dict[str, Any]] = None  # 视频时间戳信息
```

#### 索引相关模型

**IndexAddRequest**：
```python
class IndexAddRequest(BaseModel):
    file_path: str
    priority: int = 5
```

**IndexRemoveRequest**：
```python
class IndexRemoveRequest(BaseModel):
    file_uuid: str
```

**IndexStatusResponse**：
```python
class IndexStatusResponse(BaseModel):
    success: bool
    stats: Dict[str, Any]
    last_index_time: Optional[str] = None
    current_tasks: List[Dict[str, Any]]
```

#### 文件相关模型

**FilesListRequest**：
```python
class FilesListRequest(BaseModel):
    file_type: Optional[str] = None
    indexed_only: bool = False
    limit: int = 100
    offset: int = 0
```

**FilesListResponse**：
```python
class FilesListResponse(BaseModel):
    success: bool
    total: int
    files: List[FileInfo]
```

**FileInfo**：
```python
class FileInfo(BaseModel):
    file_uuid: str
    file_name: str
    file_path: str
    file_type: str
    file_size: int
    indexed: bool
    indexed_at: Optional[str] = None
    metadata: Dict[str, Any]
```

#### 任务相关模型

**TasksListRequest**：
```python
class TasksListRequest(BaseModel):
    task_type: Optional[str] = None
    status: Optional[str] = None
    limit: int = 100
    offset: int = 0
```

**TasksListResponse**：
```python
class TasksListResponse(BaseModel):
    success: bool
    total: int
    tasks: List[TaskInfo]
```

**TaskStatusResponse**：
```python
class TaskStatusResponse(BaseModel):
    success: bool
    id: str
    task_type: str
    status: str
    priority: int
    progress: float
    current_step: Optional[str] = None
    step_progress: Optional[float] = None
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    task_data: Dict[str, Any]
    result: Optional[Any] = None
    error: Optional[str] = None
```

#### 系统相关模型

**SystemInfo**：
```python
class SystemInfo(BaseModel):
    success: bool
    version: str
    config: Dict[str, Any]
```

**SystemStats**：
```python
class SystemStats(BaseModel):
    success: bool
    stats: Dict[str, Any]
```

**ErrorResponse**：
```python
class ErrorResponse(BaseModel):
    success: bool
    error: str
    detail: Optional[str] = None
```

**SuccessResponse**：
```python
class SuccessResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
```

### 2.11.4 API错误处理

**统一错误响应格式**：
```json
{
  "success": false,
  "error": "错误类型",
  "detail": "详细错误信息"
}
```

**常见错误码**：
- 400: 请求参数错误
- 404: 资源不存在
- 500: 服务器内部错误

**错误处理示例**：
```python
@router.get("/files/{file_uuid}")
async def get_file_info(file_uuid: str):
    try:
        file_info = await handlers.handle_file_info(file_uuid)
        return file_info
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 2.11.5 API性能要求

根据需求文档的验收标准：

1. **响应时间**：所有API请求应在2秒内返回结果，容差为±0.5秒
2. **并发处理**：支持多个并发请求，不影响性能
3. **结果数量**：默认返回前20个最相关项目
4. **向量数据库性能**：超过10万条记录时保持检索性能无明显下降
5. **错误处理**：所有错误返回统一格式的错误响应

### 2.11.6 API安全考虑

**输入验证**：
- 所有输入参数必须经过验证
- 文件路径必须进行安全检查
- 防止路径遍历攻击

**访问控制**：
- 当前版本无需身份验证（单机应用）
- 未来可扩展为API Key认证

**资源限制**：
- 文件上传大小限制
- 请求频率限制（可选）
- 并发连接数限制

---

## 2.12 CLI设计

### 2.12.1 CLI设计原则

**命令行工具定位**：
- 用于测试和调试msearch系统
- 封装所有API接口，提供命令行访问方式
- 支持自动化脚本和批处理操作

**设计特点**：
- 直观的命令结构
- 清晰的帮助信息
- 友好的错误提示
- 丰富的输出格式

**依赖关系**：
- 依赖API服务器运行
- 使用requests库进行HTTP通信
- 支持多种输出格式（文本、JSON）

### 2.12.2 CLI命令结构

```
msearch-cli <command> [options] [arguments]

可用命令：
  health          健康检查
  info             系统信息
  vector-stats     向量统计
  search          搜索
  task            任务管理
  index           文件索引
  config          配置管理
  help            帮助信息
```

### 2.12.3 健康检查命令

**命令**：
```bash
python src/cli.py health
```

**功能**：
- 检查API服务器连接状态
- 验证所有组件运行状态
- 显示系统健康指标

**输出示例**：
```
============================================================
健康检查
============================================================
状态: healthy

组件状态:
  - API服务: running
  - 数据库: connected
  - 向量存储: ready
  - 任务管理器: active

✓ 系统运行正常
```

### 2.12.4 系统信息命令

**命令**：
```bash
python src/cli.py info
```

**功能**：
- 显示系统版本信息
- 显示当前配置信息
- 显示模型配置详情

**输出示例**：
```
============================================================
系统信息
============================================================
状态: true

配置信息:
  - 版本: 1.0.0
  - 设备: cuda
  - 批处理大小: 16
  - 图像/视频模型: chinese-clip-vit-base-patch16
  - 音频模型: laion/clap-htsat-unfused
```

### 2.12.5 向量统计命令

**命令**：
```bash
python src/cli.py vector-stats
```

**功能**：
- 显示向量数据库统计信息
- 显示各模态向量数量分布
- 显示向量维度信息

**输出示例**：
```
============================================================
向量统计
============================================================
表名: unified_vectors
总向量数: 450
向量维度: 512

模态分布:
  - image: 300
  - video: 120
  - audio: 30
```

### 2.12.6 搜索命令

#### 文本搜索

**命令**：
```bash
python src/cli.py search text "搜索文本" [--top-k 20]
```

**功能**：
- 使用文本查询搜索文件
- 支持多模态搜索
- 显示搜索结果和相似度分数

**输出示例**：
```
============================================================
文本搜索: 老虎
============================================================
查询: 老虎
结果数: 15

搜索结果:
  [1] 相似度: 0.9543
      文件名: tiger.jpg
      文件路径: /data/animals/tiger.jpg
      模态: image

  [2] 相似度: 0.9234
      文件名: wildlife_video.mp4
      文件路径: /data/videos/wildlife.mp4
      模态: video
      时间戳: 10.5-15.2秒
```

#### 图像搜索

**命令**：
```bash
python src/cli.py search image /path/to/image.jpg [--top-k 20]
```

**功能**：
- 使用图像文件搜索相似文件
- 支持图搜图和图搜视频
- 显示图像相似度分数

**输出示例**：
```
============================================================
图像搜索: /path/to/image.jpg
============================================================
图像: image.jpg
结果数: 10

搜索结果:
  [1] 相似度: 0.9123
      文件名: similar_image.jpg
      文件路径: /data/images/similar_image.jpg
      模态: image
```

#### 音频搜索

**命令**：
```bash
python src/cli.py search audio /path/to/audio.wav [--top-k 20]
```

**功能**：
- 使用音频文件搜索相似文件
- 支持音频找音频和音频找视频
- 显示音频相似度分数

**输出示例**：
```
============================================================
音频搜索: /path/to/audio.wav
============================================================
音频: audio.wav
结果数: 5

搜索结果:
  [1] 相似度: 0.8765
      文件名: similar_audio.wav
      文件路径: /data/audio/similar_audio.wav
      模态: audio
```

### 2.12.7 任务管理命令

#### 任务统计

**命令**：
```bash
python src/cli.py task stats
```

**功能**：
- 显示任务总体统计信息
- 显示各类型任务统计
- 显示资源使用情况

**输出示例**：
```
============================================================
任务统计
============================================================

总体统计:
  - 总任务数: 100
  - 待处理: 20
  - 运行中: 5
  - 已完成: 70
  - 失败: 3
  - 已取消: 2

按类型统计:
  - image_preprocess:
      总数: 30
      完成: 25
      失败: 2

并发数: 4

资源使用:
  - CPU: 45.2%
  - 内存: 62.8%
  - GPU: 78.5%
```

#### 列出任务

**命令**：
```bash
python src/cli.py task list [--status pending] [--type image_preprocess] [--limit 20]
```

**功能**：
- 列出所有任务
- 支持按状态和类型过滤
- 支持分页显示

**输出示例**：
```
============================================================
任务列表
============================================================
任务总数: 50

任务列表:
  [1] 任务ID: task-1234...
      类型: image_preprocess
      状态: processing
      优先级: 1
      进度: 75.0%
      当前步骤: 向量化处理
      创建时间: 2026-01-28 10:00:00
```

#### 获取任务详情

**命令**：
```bash
python src/cli.py task get <task_id>
```

**功能**：
- 显示任务详细信息
- 显示任务进度和状态
- 显示任务错误信息（如果有）

**输出示例**：
```
============================================================
任务详情: task-1234
============================================================
任务ID: task-1234
类型: image_preprocess
状态: processing
优先级: 1
进度: 75.0%
创建时间: 2026-01-28 10:00:00
开始时间: 2026-01-28 10:01:00
当前步骤: 向量化处理
步骤进度: 50.0%

任务数据:
  - file_path: /path/to/image.jpg
```

#### 取消任务

**命令**：
```bash
python src/cli.py task cancel <task_id>
```

**功能**：
- 取消指定任务
- 显示取消结果
- 支持取消运行中的任务

**输出示例**：
```
============================================================
取消任务: task-1234
============================================================
成功: true
消息: 任务已取消
```

#### 更新任务优先级

**命令**：
```bash
python src/cli.py task priority <task_id> <priority>
```

**功能**：
- 更新任务优先级（0-11）
- 支持动态调整任务优先级
- 显示更新结果

**输出示例**：
```
============================================================
更新任务优先级: task-1234
============================================================
成功: true
消息: 任务优先级已更新
新优先级: 3
```

#### 取消所有任务

**命令**：
```bash
python src/cli.py task cancel-all [--cancel-running]
```

**功能**：
- 取消所有待处理任务
- 可选同时取消正在运行的任务
- 显示取消统计信息

**输出示例**：
```
============================================================
取消所有任务
============================================================
成功: true
消息: 批量取消任务完成

取消统计:
  - 已取消: 45
  - 失败: 5
  - 总计: 50
```

#### 按类型取消任务

**命令**：
```bash
python src/cli.py task cancel-by-type <task_type> [--cancel-running]
```

**功能**：
- 按任务类型批量取消任务
- 可选同时取消正在运行的任务
- 显示按类型的取消统计

**输出示例**：
```
============================================================
取消image_preprocess类型任务
============================================================
成功: true
消息: 批量取消任务完成

取消统计:
  - 任务类型: image_preprocess
  - 已取消: 30
  - 失败: 2
  - 总计: 32
```

### 2.12.8 文件索引命令

#### 索引单个文件

**命令**：
```bash
python src/cli.py index file /path/to/file.jpg
```

**功能**：
- 将单个文件添加到索引队列
- 返回任务ID用于跟踪进度
- 支持所有文件类型

**输出示例**：
```
============================================================
索引文件: /path/to/file.jpg
============================================================
任务ID: task-1234
状态: true
消息: 文件已添加到索引队列

您可以使用以下命令查看任务进度:
  python src/cli.py task get task-1234
```

#### 索引目录

**命令**：
```bash
python src/cli.py index directory /path/to/directory [--no-recursive]
```

**功能**：
- 递归或非递归索引目录
- 显示扫描统计信息
- 返回任务ID用于跟踪进度

**输出示例**：
```
============================================================
索引目录: /path/to/directory
============================================================
任务ID: task-5678
状态: true
消息: 目录索引任务已创建

扫描统计:
  - 总文件数: 150
  - 图像文件: 80
  - 视频文件: 50
  - 音频文件: 20
  - 其他文件: 0

您可以使用以下命令查看任务进度:
  python src/cli.py task get task-5678
```

#### 重新索引所有文件

**命令**：
```bash
python src/cli.py index reindex-all
```

**功能**：
- 重新索引所有已注册文件
- 跳过已索引的文件
- 返回任务ID用于跟踪进度

**输出示例**：
```
============================================================
重新索引所有文件
============================================================
任务ID: task-9012
状态: true
消息: 重新索引任务已创建

您可以使用以下命令查看任务进度:
  python src/cli.py task get task-9012
```

#### 获取索引状态

**命令**：
```bash
python src/cli.py index status
```

**功能**：
- 显示索引统计信息
- 显示各模态文件数量
- 显示当前索引任务进度
- 显示最后索引时间

**输出示例**：
```
============================================================
索引状态
============================================================
状态: true

索引统计:
  - 总文件数: 500
  - 已索引: 450
  - 待处理: 50
  - 处理中: 10
  - 失败: 5

模态分布:
  - image: 300
  - video: 120
  - audio: 30

最后索引时间: 2026-01-28 10:30:00

当前索引任务:
  - task-1234 (image_preprocess) - 进度: 75.0% - 状态: processing
  - task-5678 (video_preprocess) - 进度: 30.0% - 状态: processing
```

### 2.12.9 CLI高级功能

#### 自定义API URL

**命令**：
```bash
python src/cli.py --url http://localhost:8080 search text "搜索文本"
```

**功能**：
- 支持自定义API服务器URL
- 用于连接远程API服务器
- 便于测试不同环境

#### JSON输出格式

**命令**：
```bash
python src/cli.py --format json search text "搜索文本"
```

**功能**：
- 支持JSON格式输出
- 便于脚本解析
- 支持自动化集成

#### 批处理操作

**命令**：
```bash
# 批量索引多个文件
for file in /path/to/images/*.jpg; do
    python src/cli.py index file "$file"
done

# 批量取消所有图像预处理任务
python src/cli.py task cancel-by-type image_preprocess
```

**功能**：
- 支持shell脚本集成
- 支持批处理操作
- 支持自动化流程

### 2.12.10 CLI使用示例

#### 完整工作流程示例

```bash
# 1. 健康检查
python src/cli.py health

# 2. 查看系统信息
python src/cli.py info

# 3. 索引测试数据目录
python src/cli.py index directory /data/testdata

# 4. 查看索引状态
python src/cli.py index status

# 5. 执行文本搜索
python src/cli.py search text "老虎"

# 6. 执行图像搜索
python src/cli.py search image /data/testdata/tiger.jpg

# 7. 执行音频搜索
python src/cli.py search audio /data/testdata/roar.wav

# 8. 查看任务统计
python src/cli.py task stats

# 9. 取消所有任务
python src/cli.py task cancel-all

# 10. 查看向量统计
python src/cli.py vector-stats
```

#### 自动化脚本示例

```bash
#!/bin/bash
# 自动化索引脚本

# 索引新文件
echo "开始索引新文件..."
python src/cli.py index directory /data/new_files

# 等待索引完成
sleep 5

# 查看索引状态
python src/cli.py index status

# 执行测试搜索
echo "执行测试搜索..."
python src/cli.py search text "测试"

echo "索引完成!"
```

### 2.12.11 CLI性能要求

根据需求文档的验收标准：

1. **响应时间**：所有CLI命令应在2秒内返回结果
2. **错误处理**：所有错误都有友好的错误提示
3. **帮助信息**：所有命令都有清晰的帮助说明
4. **进度跟踪**：长时间操作提供任务ID用于跟踪进度
5. **批量操作**：支持批处理和自动化脚本

### 2.12.12 CLI与API的关系

**CLI作为API的封装**：
- CLI工具封装了所有API端点
- 提供更友好的命令行界面
- 支持自动化脚本和批处理

**依赖关系**：
- CLI依赖API服务器运行
- 使用HTTP协议与API通信
- 错误处理与API保持一致

**使用场景**：
- 开发测试：快速测试API功能
- 调试问题：诊断系统问题
- 自动化：集成到CI/CD流程
- 运维管理：批量操作和监控

---

# 第三部分：详细流程设计

## 3.1 数据处理流程

### 3.1.1 图像文件处理流程

```
图像文件处理流程图

┌─────────────────────────────────────────────────────────────────────────────┐
│                         图像文件处理流程 (Image Processing)                   │
└─────────────────────────────────────────────────────────────────────────────┘

开始
  ↓
[1] 文件扫描
  ├─ 发现图像文件 (jpg, png, bmp, gif, webp)
  ├─ 收集基本信息 (路径、大小、修改时间)
  └─ 创建文件扫描任务
  ↓
[2] 元数据提取
  ├─ 计算 SHA256 哈希
  ├─ 提取 EXIF 信息 (分辨率、拍摄时间等)
  ├─ 检测文件是否重复
  └─ 如果重复: 直接引用向量 → 结束
  ↓
[3] 噪音过滤
  ├─ 检查文件大小 (≥ 1KB)
  ├─ 检查分辨率 (≥ 100x100)
  └─ 如果不符合: 跳过处理 → 结束
  ↓
[4] 图像预处理
  ├─ 读取图像文件
  ├─ 转换为 RGB 格式
  ├─ 调整大小到 512x512 (保持宽高比)
  ├─ 居中裁剪
  ├─ 归一化 (mean: [0.481, 0.457, 0.408], std: [0.268, 0.261, 0.275])
  └─ 转换为张量
  ↓
[5] 图像向量化
  ├─ 使用 [配置驱动模型]-500M 模型
  ├─ 批处理 (batch_size=16)
  ├─ 生成 512 维向量
  └─ 使用混合精度 (float16)
  ↓
[6] 向量存储
  ├─ 存储到 LanceDB
  ├─ 字段: vector, file_id, modality, created_at
  └─ 更新元数据状态为 "indexed"
  ↓
[7] 缩略图生成
  ├─ 生成 256x256 缩略图
  ├─ 保存到缓存目录
  └─ 更新元数据中的缩略图路径
  ↓
结束

处理时间估算:
- 文件扫描: < 10ms
- 元数据提取: < 50ms
- 噪音过滤: < 10ms
- 图像预处理: < 50ms
- 图像向量化: < 100ms
- 向量存储: < 10ms
- 缩略图生成: < 50ms
- 总计: < 320ms
```

**关键代码位置**：
- 文件扫描：`src/core/services/file/file_scanner.py`
- 元数据提取：`src/core/data/extractors/metadata_extractor.py`
- 噪音过滤：`src/core/data/filters/noise_filter.py`
- 图像预处理：`src/core/services/media/image_preprocessor.py`
- 图像向量化：`src/core/embedding/embedding_engine.py`
- 向量存储：`src/core/vector/vector_store.py`
- 缩略图生成：`src/core/data/generators/thumbnail_generator.py`

### 3.1.2 视频文件处理流程

```
视频文件处理流程图

┌─────────────────────────────────────────────────────────────────────────────┐
│                         视频文件处理流程 (Video Processing)                   │
└─────────────────────────────────────────────────────────────────────────────┘

开始
  ↓
[1] 文件扫描
  ├─ 发现视频文件 (mp4, avi, mov, mkv, webm)
  ├─ 收集基本信息 (路径、大小、修改时间)
  └─ 创建文件扫描任务
  ↓
[2] 元数据提取
  ├─ 计算 SHA256 哈希
  ├─ 提取视频信息 (时长、分辨率、帧率、码率)
  ├─ 检测文件是否重复
  └─ 如果重复: 直接引用向量 → 结束
  ↓
[3] 噪音过滤
  ├─ 检查文件大小 (≥ 100KB)
  ├─ 检查时长 (≥ 1秒)
  └─ 如果不符合: 跳过处理 → 结束
  ↓
[4] 时长判断
  ├─ 如果时长 ≤ 6秒: 短视频处理流程
  └─ 如果时长 > 6秒: 长视频处理流程
  ↓
[5] 视频预处理
  ├─ 短视频流程 (≤6秒)
  │  ├─ 提取所有帧
  │  └─ 选择关键帧 (每 0.5 秒一帧)
  │
  └─ 长视频流程 (>6秒)
     ├─ 场景检测 (scene detection)
     ├─ 视频切片 (每 5-10 秒一个片段)
     └─ 提取片段关键帧
  ↓
[6] 音频分离 (可选)
  ├─ 提取音频轨道
  ├─ 音频向量化 (使用 CLAP 模型)
  └─ 存储音频向量
  ↓
[7] 视频向量化
  ├─ 使用 [配置驱动模型]-500M 模型
  ├─ 批处理 (batch_size=16)
  ├─ 生成 512 维向量 (每帧一个向量)
  └─ 使用混合精度 (float16)
  ↓
[8] 向量存储
  ├─ 存储到 LanceDB
  ├─ 字段: vector, file_id, segment_id, timestamp, modality, created_at
  └─ 更新元数据状态为 "indexed"
  ↓
[9] 缩略图生成
  ├─ 生成视频缩略图 (第一帧或关键帧)
  ├─ 生成时间轴缩略图 (每 5 秒一帧)
  ├─ 保存到缓存目录
  └─ 更新元数据中的缩略图路径
  ↓
结束

处理时间估算 (10 秒 1080p 视频):
- 文件扫描: < 10ms
- 元数据提取: < 100ms
- 噪音过滤: < 10ms
- 时长判断: < 10ms
- 视频预处理: < 2000ms (场景检测 + 帧提取)
- 音频分离: < 500ms
- 视频向量化: < 1000ms (20 帧 × 50ms/帧)
- 向量存储: < 50ms
- 缩略图生成: < 100ms
- 总计: < 3780ms (~3.8 秒)
```

**关键代码位置**：
- 文件扫描：`src/core/services/file/file_scanner.py`
- 元数据提取：`src/core/data/extractors/metadata_extractor.py`
- 噪音过滤：`src/core/data/filters/noise_filter.py`
- 视频预处理：`src/core/services/media/video_preprocessor.py`
- 场景检测：`src/core/data/analyzers/scene_detector.py`
- 视频向量化：`src/core/embedding/embedding_engine.py`
- 向量存储：`src/core/vector/vector_store.py`
- 缩略图生成：`src/core/data/generators/thumbnail_generator.py`

### 3.1.3 音频文件处理流程

```
音频文件处理流程图

┌─────────────────────────────────────────────────────────────────────────────┐
│                         音频文件处理流程 (Audio Processing)                   │
└─────────────────────────────────────────────────────────────────────────────┘

开始
  ↓
[1] 文件扫描
  ├─ 发现音频文件 (mp3, wav, aac, flac)
  ├─ 收集基本信息 (路径、大小、修改时间)
  └─ 创建文件扫描任务
  ↓
[2] 元数据提取
  ├─ 计算 SHA256 哈希
  ├─ 提取音频信息 (时长、采样率、声道数、比特率)
  ├─ 检测文件是否重复
  └─ 如果重复: 直接引用向量 → 结束
  ↓
[3] 噪音过滤
  ├─ 检查文件大小 (≥ 10KB)
  ├─ 检查时长 (≥ 3秒)
  └─ 如果不符合: 跳过处理 → 结束
  ↓
[4] 音频预处理
  ├─ 读取音频文件
  ├─ 重采样到 44100Hz
  ├─ 转换为单声道或立体声
  ├─ 归一化 (normalization)
  └─ 转换为张量
  ↓
[5] 音频向量化
  ├─ 使用 CLAP-HTSAT 模型
  ├─ 批处理 (batch_size=8)
  ├─ 生成 512 维向量
  └─ 使用混合精度 (float16)
  ↓
[6] 向量存储
  ├─ 存储到 LanceDB
  ├─ 字段: vector, file_id, modality, created_at
  └─ 更新元数据状态为 "indexed"
  ↓
结束

处理时间估算 (30 秒音频):
- 文件扫描: < 10ms
- 元数据提取: < 50ms
- 噪音过滤: < 10ms
- 音频预处理: < 200ms
- 音频向量化: < 500ms
- 向量存储: < 10ms
- 总计: < 780ms

**关键代码位置**：
- 文件扫描：`src/core/services/file/file_scanner.py`
- 元数据提取：`src/core/data/extractors/metadata_extractor.py`
- 噪音过滤：`src/core/data/filters/noise_filter.py`
- 音频预处理：`src/core/services/media/audio_preprocessor.py`
- 音频向量化：`src/core/embedding/embedding_engine.py`
- 向量存储：`src/core/vector/vector_store.py`

## 3.2 检索流程

### 3.2.1 文本检索流程

```
文本检索流程图

用户输入文本查询
  ↓
[1] 查询解析
  ├─ 验证查询格式
  ├─ 提取关键词
  └─ 确定检索范围 (图像/视频/音频/全部)
  ↓
[2] 文本向量化
  ├─ 使用 [配置驱动模型] 模型
  ├─ 生成文本向量 (512/768 维)
  └─ 使用 float32 精度
  ↓
[3] 向量检索
  ├─ 查询 LanceDB 向量数据库
  ├─ 使用 IVF 索引加速
  ├─ 返回 top_k 个结果 (默认 20)
  └─ 过滤低相似度结果 (< 0.7)
  ↓
[4] 结果去重
  ├─ 去除同一文件的多个分段
  ├─ 保留最高相似度的分段
  └─ 生成去重后的结果列表
  ↓
[5] 结果重排序 (可选)
  ├─ 使用重排序模型
  ├─ 根据查询与结果的相关性重新排序
  └─ 返回前 10 个结果
  ↓
[6] 结果格式化
  ├─ 获取文件元数据
  ├─ 生成缩略图 URL
  ├─ 计算相似度分数
  └─ 组织结果结构
  ↓
[7] 返回结果
  ├─ 返回 JSON 格式结果
  ├─ 包含文件信息、相似度、缩略图等
  └─ 支持分页和排序

处理时间估算:
- 查询解析: < 10ms
- 文本向量化: < 50ms
- 向量检索: < 100ms
- 结果去重: < 10ms
- 结果重排序: < 50ms (可选)
- 结果格式化: < 50ms
- 返回结果: < 10ms
- 总计: < 280ms
```

### 3.2.2 图像检索流程

```
图像检索流程图

用户上传图像文件
  ↓
[1] 图像验证
  ├─ 检查文件格式
  ├─ 检查文件大小
  └─ 检查文件完整性
  ↓
[2] 图像预处理
  ├─ 调整大小到 512x512
  ├─ 转换为 RGB 格式
  ├─ 归一化
  └─ 转换为张量
  ↓
[3] 图像向量化
  ├─ 使用 [配置驱动模型] 模型
  ├─ 生成图像向量 (512/768 维)
  └─ 使用 float32 精度
  ↓
[4] 向量检索
  ├─ 查询 LanceDB 向量数据库
  ├─ 使用 IVF 索引加速
  ├─ 返回 top_k 个结果 (默认 20)
  └─ 过滤低相似度结果 (< 0.7)
  ↓
[5] 结果去重
  ├─ 去除同一文件的多个分段
  ├─ 保留最高相似度的分段
  └─ 生成去重后的结果列表
  ↓
[6] 结果格式化
  ├─ 获取文件元数据
  ├─ 生成缩略图 URL
  ├─ 计算相似度分数
  └─ 组织结果结构
  ↓
[7] 返回结果
  ├─ 返回 JSON 格式结果
  ├─ 包含文件信息、相似度、缩略图等
  └─ 支持分页和排序

处理时间估算:
- 图像验证: < 10ms
- 图像预处理: < 50ms
- 图像向量化: < 100ms
- 向量检索: < 100ms
- 结果去重: < 10ms
- 结果格式化: < 50ms
- 返回结果: < 10ms
- 总计: < 330ms
```

### 3.2.3 视频检索流程

```
视频检索流程图

用户上传视频文件
  ↓
[1] 视频验证
  ├─ 检查文件格式
  ├─ 检查文件大小
  ├─ 检查文件完整性
  └─ 检查时长 (≤ 60 秒)
  ↓
[2] 视频预处理
  ├─ 提取关键帧 (每 1 秒一帧)
  ├─ 调整大小到 512x512
  ├─ 转换为 RGB 格式
  ├─ 归一化
  └─ 转换为张量
  ↓
[3] 视频向量化
  ├─ 使用 [配置驱动模型] 模型
  ├─ 批处理 (batch_size=16)
  ├─ 生成视频向量 (每帧一个向量)
  └─ 使用 float32 精度
  ↓
[4] 向量融合
  ├─ 平均所有帧向量
  ├─ 生成视频级向量
  └─ 或使用关键帧向量
  ↓
[5] 向量检索
  ├─ 查询 LanceDB 向量数据库
  ├─ 使用 IVF 索引加速
  ├─ 返回 top_k 个结果 (默认 20)
  └─ 过滤低相似度结果 (< 0.7)
  ↓
[6] 结果去重
  ├─ 去除同一文件的多个分段
  ├─ 保留最高相似度的分段
  └─ 生成去重后的结果列表
  ↓
[7] 结果格式化
  ├─ 获取文件元数据
  ├─ 生成缩略图 URL
  ├─ 计算相似度分数
  └─ 组织结果结构
  ↓
[8] 返回结果
  ├─ 返回 JSON 格式结果
  ├─ 包含文件信息、相似度、缩略图等
  └─ 支持分页和排序

处理时间估算 (10 秒视频):
- 视频验证: < 10ms
- 视频预处理: < 500ms (帧提取)
- 视频向量化: < 500ms (10 帧 × 50ms/帧)
- 向量融合: < 10ms
- 向量检索: < 100ms
- 结果去重: < 10ms
- 结果格式化: < 50ms
- 返回结果: < 10ms
- 总计: < 1190ms (~1.2 秒)
```

### 3.2.4 音频检索流程

```
音频检索流程图

用户上传音频文件
  ↓
[1] 音频验证
  ├─ 检查文件格式
  ├─ 检查文件大小
  ├─ 检查文件完整性
  └─ 检查时长 (≤ 60 秒)
  ↓
[2] 音频预处理
  ├─ 重采样到 44100Hz
  ├─ 转换为单声道
  ├─ 归一化
  └─ 转换为张量
  ↓
[3] 音频向量化
  ├─ 使用 CLAP-HTSAT 模型
  ├─ 生成音频向量 (512 维)
  └─ 使用 float32 精度
  ↓
[4] 向量检索
  ├─ 查询 LanceDB 向量数据库
  ├─ 使用 IVF 索引加速
  ├─ 返回 top_k 个结果 (默认 20)
  └─ 过滤低相似度结果 (< 0.7)
  ↓
[5] 结果去重
  ├─ 去除同一文件的多个分段
  ├─ 保留最高相似度的分段
  └─ 生成去重后的结果列表
  ↓
[6] 结果格式化
  ├─ 获取文件元数据
  ├─ 生成缩略图 URL
  ├─ 计算相似度分数
  └─ 组织结果结构
  ↓
[7] 返回结果
  ├─ 返回 JSON 格式结果
  ├─ 包含文件信息、相似度、缩略图等
  └─ 支持分页和排序

处理时间估算 (30 秒音频):
- 音频验证: < 10ms
- 音频预处理: < 200ms
- 音频向量化: < 500ms
- 向量检索: < 100ms
- 结果去重: < 10ms
- 结果格式化: < 50ms
- 返回结果: < 10ms
- 总计: < 880ms
```

## 3.3 任务调度流程

### 3.3.1 任务创建流程

```
任务创建流程图

事件触发 (文件扫描/用户操作/系统事件)
  ↓
[1] 任务类型判断
  ├─ 文件扫描任务 (file_scan)
  ├─ 元数据提取任务 (metadata_extract)
  ├─ 预处理任务 (preprocess)
  ├─ 向量化任务 (embedding)
  ├─ 向量存储任务 (vector_store)
  ├─ 检索任务 (search)
  └─ 其他任务类型
  ↓
[2] 任务参数验证
  ├─ 验证参数完整性
  ├─ 验证参数格式
  └─ 验证参数有效性
  ↓
[3] 任务优先级计算
  ├─ 根据任务类型设置优先级
  ├─ 根据文件大小调整优先级
  ├─ 根据用户请求调整优先级
  └─ 计算最终优先级 (1-5)
  ↓
[4] 任务创建
  ├─ 生成任务 ID (UUID)
  ├─ 创建任务对象
  ├─ 设置任务状态为 "pending"
  └─ 记录创建时间
  ↓
[5] 任务入队
  ├─ 添加到任务队列
  ├─ 根据优先级排序
  └─ 等待调度器处理
  ↓
[6] 任务通知
  ├─ 记录任务日志
  ├─ 发送任务创建事件
  └─ 更新任务状态

处理时间估算:
- 任务类型判断: < 10ms
- 任务参数验证: < 10ms
- 任务优先级计算: < 10ms
- 任务创建: < 10ms
- 任务入队: < 10ms
- 任务通知: < 10ms
- 总计: < 60ms
```

### 3.3.2 任务执行流程

```
任务执行流程图

任务调度器从队列中取出任务
  ↓
[1] 任务状态检查
  ├─ 检查任务是否为 "pending" 状态
  ├─ 检查任务是否已过期
  └─ 检查任务是否被取消
  ↓
[2] 任务锁定
  ├─ 设置任务状态为 "running"
  ├─ 记录开始时间
  ├─ 分配执行资源
  └─ 生成执行日志
  ↓
[3] 任务执行
  ├─ 根据任务类型选择执行器
  ├─ 调用执行器执行任务
  ├─ 处理执行结果
  └─ 记录执行日志
  ↓
[4] 任务结果处理
  ├─ 如果执行成功:
  │  ├─ 设置任务状态为 "completed"
  │  ├─ 记录结束时间
  │  ├─ 保存执行结果
  │  └─ 创建后续任务 (如果有)
  │
  └─ 如果执行失败:
     ├─ 记录错误信息
     ├─ 检查重试次数
     ├─ 如果重试次数未超限: 重新入队
     └─ 如果重试次数超限: 设置任务状态为 "failed"
  ↓
[5] 任务解锁
  ├─ 释放执行资源
  ├─ 更新任务统计
  └─ 发送任务完成事件
  ↓
[6] 任务清理 (可选)
  ├─ 删除临时文件
  ├─ 清理缓存
  └─ 释放内存

处理时间估算 (取决于任务类型):
- 任务状态检查: < 10ms
- 任务锁定: < 10ms
- 任务执行: < 100ms - 10000ms (取决于任务类型)
- 任务结果处理: < 10ms
- 任务解锁: < 10ms
- 任务清理: < 10ms
- 总计: < 150ms - 10050ms
```

## 3.4 目录监控流程

### 3.4.1 目录监控启动流程

```
目录监控启动流程图

用户添加监控目录
  ↓
[1] 目录验证
  ├─ 检查目录是否存在
  ├─ 检查目录是否可访问
  ├─ 检查目录是否已监控
  └─ 检查目录权限
  ↓
[2] 监控配置
  ├─ 设置监控事件类型 (创建/修改/删除/移动)
  ├─ 设置监控文件类型 (图像/视频/音频/全部)
  ├─ 设置监控深度 (递归/非递归)
  └─ 设置监控延迟 (防抖)
  ↓
[3] 监控器初始化
  ├─ 创建 FileSystemEventHandler
  ├─ 创建 Observer
  ├─ 配置 Observer (线程数/事件队列大小)
  └─ 启动 Observer
  ↓
[4] 目录扫描
  ├─ 扫描目录下的所有文件
  ├─ 创建文件扫描任务
  ├─ 添加到任务队列
  └─ 记录扫描结果
  ↓
[5] 监控注册
  ├─ 将目录添加到监控器
  ├─ 注册事件处理器
  ├─ 记录监控信息
  └─ 更新监控状态
  ↓
[6] 监控通知
  ├─ 记录监控日志
  ├─ 发送监控启动事件
  └─ 返回监控结果

处理时间估算 (1000 个文件的目录):
- 目录验证: < 10ms
- 监控配置: < 10ms
- 监控器初始化: < 10ms
- 目录扫描: < 1000ms (1ms/文件)
- 监控注册: < 10ms
- 监控通知: < 10ms
- 总计: < 1050ms
```

### 3.4.2 文件事件处理流程

```
文件事件处理流程图

文件系统事件触发 (创建/修改/删除/移动)
  ↓
[1] 事件接收
  ├─ 接收文件系统事件
  ├─ 解析事件类型
  ├─ 解析事件路径
  └─ 记录事件日志
  ↓
[2] 事件过滤
  ├─ 检查事件类型是否监控
  ├─ 检查文件类型是否支持
  ├─ 检查文件大小是否符合
  └─ 检查是否为临时文件
  ↓
[3] 防抖处理
  ├─ 检查是否在防抖时间内
  ├─ 如果是: 忽略事件
  └─ 如果否: 继续处理
  ↓
[4] 事件类型判断
  ├─ 文件创建事件
  ├─ 文件修改事件
  ├─ 文件删除事件
  └─ 文件移动事件
  ↓
[5] 事件处理
  ├─ 如果是创建/修改事件:
  │  ├─ 创建文件扫描任务
  │  ├─ 添加到任务队列
  │  └─ 记录处理日志
  │
  └─ 如果是删除/移动事件:
     ├─ 创建文件删除任务
     ├─ 添加到任务队列
     └─ 记录处理日志
  ↓
[6] 事件通知
  ├─ 记录事件处理日志
  ├─ 发送事件处理完成事件
  └─ 更新事件统计

处理时间估算:
- 事件接收: < 10ms
- 事件过滤: < 10ms
- 防抖处理: < 10ms
- 事件类型判断: < 10ms
- 事件处理: < 10ms
- 事件通知: < 10ms
- 总计: < 60ms
```

---

# 第四部分：性能优化设计

## 4.1 内存管理

### 4.1.1 模型内存管理

**内存优化策略**：

1. **懒加载**：
   - 模型在需要时才加载
   - 避免启动时加载所有模型
   - 减少启动时间和内存占用

2. **动态卸载**：
   - 长时间未使用的模型自动卸载
   - 释放内存供其他模型使用
   - 下次使用时重新加载

3. **内存共享**：
   - 多个任务共享同一模型实例
   - 避免重复加载相同模型
   - 减少内存占用

4. **混合精度**：
   - GPU 环境使用 float16/bfloat16
   - CPU 环境使用 float32
   - 减少内存占用并提高速度

5. **模型分片**：
   - 大型模型分片加载
   - 减少峰值内存占用
   - 支持更大模型

### 4.1.2 数据内存管理

**内存优化策略**：

1. **流式处理**：
   - 数据流式读取
   - 避免一次性加载全部数据
   - 减少内存占用

2. **批量处理**：
   - 数据批量处理
   - 提高处理效率
   - 减少内存波动

3. **及时释放**：
   - 处理完成后及时释放数据
   - 避免内存泄漏
   - 保持内存稳定

4. **内存映射**：
   - 大文件使用内存映射
   - 减少内存占用
   - 提高访问速度

5. **缓存策略**：
   - 常用数据缓存
   - 减少重复计算
   - 提高响应速度

### 4.1.3 内存监控

**内存监控指标**：

1. **内存使用率**：
   - 实时监控内存使用情况
   - 设置内存阈值
   - 超过阈值时触发优化

2. **内存泄漏检测**：
   - 定期检查内存使用趋势
   - 检测内存泄漏
   - 及时报警和处理

3. **内存碎片整理**：
   - 定期整理内存碎片
   - 提高内存使用效率
   - 减少内存浪费

## 4.2 并行处理

### 4.2.1 任务并行

**并行策略**：

1. **多线程**：
   - CPU 密集型任务使用多线程
   - 提高 CPU 利用率
   - 减少处理时间

2. **多进程**：
   - 独立任务使用多进程
   - 避免 GIL 限制
   - 提高处理效率

3. **异步处理**：
   - IO 密集型任务使用异步
   - 提高 IO 利用率
   - 减少等待时间

4. **任务队列**：
   - 任务队列管理
   - 任务调度和分配
   - 负载均衡

### 4.2.2 批处理优化

**批处理策略**：

1. **动态批大小**：
   - 根据硬件配置调整批大小
   - GPU 环境使用较大批大小
   - CPU 环境使用较小批大小

2. **批合并**：
   - 合并多个小批
   - 提高处理效率
   - 减少启动开销

3. **批排序**：
   - 按数据大小排序
   - 减少内存波动
   - 提高处理效率

## 4.3 缓存策略

### 4.3.1 模型缓存

**缓存策略**：

1. **LRU 缓存**：
   - 最近最少使用缓存
   - 自动淘汰不常用模型
   - 保持常用模型在内存

2. **模型预热**：
   - 预加载常用模型
   - 减少首次使用延迟
   - 提高用户体验

3. **模型池**：
   - 模型池管理
   - 模型复用
   - 减少加载时间

### 4.3.2 数据缓存

**缓存策略**：

1. **缩略图缓存**：
   - 生成的缩略图缓存
   - 减少重复生成
   - 提高显示速度

2. **向量缓存**：
   - 常用向量缓存
   - 减少重复计算
   - 提高检索速度

3. **元数据缓存**：
   - 文件元数据缓存
   - 减少数据库查询
   - 提高响应速度

### 4.3.3 缓存管理

**缓存管理策略**：

1. **缓存过期**：
   - 设置缓存过期时间
   - 定期清理过期缓存
   - 保持缓存新鲜

2. **缓存更新**：
   - 文件变化时更新缓存
   - 保持缓存一致性
   - 避免返回过期数据

3. **缓存清理**：
   - 定期清理缓存
   - 释放磁盘空间
   - 保持系统稳定

## 4.4 资源监控

### 4.4.1 系统资源监控

**监控指标**：

1. **CPU 使用率**：
   - 实时监控 CPU 使用情况
   - 设置 CPU 阈值
   - 超过阈值时降频处理

2. **内存使用率**：
   - 实时监控内存使用情况
   - 设置内存阈值
   - 超过阈值时触发优化

3. **GPU 使用率**：
   - 实时监控 GPU 使用情况
   - 设置 GPU 阈值
   - 超过阈值时降频处理

4. **磁盘使用率**：
   - 实时监控磁盘使用情况
   - 设置磁盘阈值
   - 超过阈值时报警

### 4.4.2 应用性能监控

**监控指标**：

1. **任务处理时间**：
   - 记录每个任务的处理时间
   - 分析性能瓶颈
   - 优化关键路径

2. **队列长度**：
   - 监控任务队列长度
   - 设置队列阈值
   - 超过阈值时限流

3. **错误率**：
   - 记录任务错误率
   - 设置错误率阈值
   - 超过阈值时报警

4. **吞吐量**：
   - 记录系统吞吐量
   - 分析系统负载
   - 优化系统性能

### 4.4.3 自动优化

**优化策略**：

1. **动态调整**：
   - 根据资源使用情况动态调整
   - 自动优化性能
   - 保持系统稳定

2. **自动降级**：
   - 资源紧张时自动降级
   - 保证核心功能
   - 减少资源消耗

3. **自动恢复**：
   - 故障时自动恢复
   - 减少人工干预
   - 提高可用性

---

# 第五部分：部署与运维

## 5.1 安装流程

### 5.1.1 环境检查

**检查项**：

1. **操作系统**：
   - 支持 Windows/Linux/macOS
   - 检查操作系统版本
   - 检查系统架构 (x86_64/arm64)

2. **Python 环境**：
   - 检查 Python 版本 (≥ 3.9)
   - 检查 pip 版本
   - 检查虚拟环境

3. **硬件配置**：
   - 检查 CPU 核心数
   - 检查内存大小
   - 检查 GPU (可选)
   - 检查磁盘空间

4. **依赖项**：
   - 检查 Git
   - 检查 FFmpeg (视频处理)
   - 检查其他系统依赖

### 5.1.2 安装步骤

**安装命令**：

```bash
# 1. 克隆仓库
git clone https://github.com/your-repo/msearch.git
cd msearch

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 运行安装脚本
bash scripts/install.sh

# 5. 启动 WebUI
python src/webui/app.py
```

### 5.1.3 安装脚本说明

**脚本功能**：

1. **环境检测**：
   - 检测硬件配置
   - 检测系统依赖
   - 检测 Python 环境

2. **模型下载**：
   - 下载预训练模型
   - 验证模型完整性
   - 保存到本地目录

3. **配置生成**：
   - 根据硬件生成配置
   - 设置默认参数
   - 保存配置文件

4. **数据库初始化**：
   - 创建数据库文件
   - 创建表结构
   - 初始化数据

5. **测试验证**：
   - 运行单元测试
   - 验证功能完整性
   - 输出测试报告

## 5.2 配置说明

### 5.2.1 配置文件位置

**配置文件**：`config/config.yml`

**配置目录**：`config/`

### 5.2.2 配置参数说明

**系统配置**：

```yaml
system:
  name: "msearch"                    # 系统名称
  version: "1.0.0"                   # 系统版本
  log_level: "INFO"                  # 日志级别 (DEBUG/INFO/WARN/ERROR)
  log_dir: "logs"                    # 日志目录
  cache_dir: "data/cache"            # 缓存目录
  model_dir: "data/models"           # 模型目录
  database_dir: "data/database"      # 数据库目录
```

**模型配置**：

```yaml
models:
  available_models:
    chinese_clip_base:
      model_id: "chinese_clip_base"  # 模型 ID
      model_name: "OFA-Sys/chinese-clip-vit-base-patch16"  # 模型名称
      local_path: "data/models/chinese-clip-vit-base-patch16"  # 本地路径
      engine: "torch"                # 推理引擎
      device: "cpu"                  # 设备 (cpu/cuda)
      dtype: "float32"               # 数据类型
      embedding_dim: 512             # 向量维度
      trust_remote_code: true        # 是否信任远程代码
      pooling_method: "mean"         # 池化方法
      compile: false                 # 是否编译模型
      batch_size: 16                 # 批处理大小

  active_models:
    - chinese_clip_base              # 激活的模型
    - audio_model
```

**向量存储配置**：

```yaml
vector_store:
  type: "lancedb"                   # 向量存储类型
  path: "data/database/lancedb"     # 存储路径
  table_name: "unified_vectors"     # 表名
  embedding_dim: 512                # 向量维度
  index_type: "ivf"                 # 索引类型
  nlist: 1024                       # 索引参数
  metric: "cosine"                  # 相似度度量
```

**数据库配置**：

```yaml
database:
  type: "sqlite"                    # 数据库类型
  path: "data/database/sqlite/msearch.db"  # 数据库路径
  timeout: 30                       # 超时时间
  check_same_thread: false          # 是否检查线程
```

**任务调度配置**：

```yaml
task_scheduler:
  max_workers: 4                    # 最大工作线程数
  queue_size: 1000                  # 队列大小
  retry_count: 3                    # 重试次数
  retry_delay: 5                    # 重试延迟
  priority_levels: 5                # 优先级级别
```

**文件扫描配置**：

```yaml
file_scanner:
  scan_strategy: "incremental"      # 扫描策略
  max_concurrency: 4                # 最大并发数
  batch_size: 100                   # 批处理大小
  supported_types:
    image: ["jpg", "jpeg", "png", ...]  # 支持的图像类型
    video: ["mp4", "avi", "mov", ...]  # 支持的视频类型
    audio: ["mp3", "wav", "aac", ...]  # 支持的音频类型
  filters:
    min_file_size: 10240            # 最小文件大小
    min_video_duration: 0.5         # 最小视频时长
    enable_hash_detection: true     # 是否启用哈希检测
  memory_limit_mb: 512              # 内存限制
  cpu_usage_limit: 80               # CPU 使用率限制
  hash_chunk_size: 65536            # 哈希计算块大小
  exclude_paths:
    - "/tmp"                        # 排除路径
    - "/var/tmp"
    - "node_modules"
```

**WebUI 配置**：

```yaml
webui:
  host: "0.0.0.0"                   # 监听地址
  port: 7860                        # 监听端口
  debug: false                      # 调试模式
  share: false                      # 共享模式
  enable_queue: true                # 启用队列
  concurrency_count: 10             # 并发数
```

**检索配置**：

```yaml
search:
  top_k: 20                         # 返回结果数
  similarity_threshold: 0.3         # 最小相似度阈值（关键：使用正确的余弦距离转换后，推荐0.3）
  enable_reranking: true            # 是否启用重排序
  rerank_top_k: 10                  # 重排序结果数
  max_results: 100                  # 最大结果数
```

**⚠️ 重要提示**：
- `similarity_threshold` 必须设置为 **0.3**（不是0.7）
- 这是因为使用正确的余弦距离转换公式 `1.0 - distance` 后，距离0.7对应相似度0.3
- 如果使用错误的欧氏距离公式 `1/(1+distance)`，则需要将阈值设置为0.7
- **强烈建议使用正确的余弦距离转换公式，并将阈值设置为0.3**

**资源监控配置**：

```yaml
resource_monitor:
  enabled: true                     # 是否启用监控
  check_interval: 1.0               # 检查间隔
  cpu_threshold: 90                 # CPU 阈值
  memory_threshold: 90              # 内存阈值
  gpu_threshold: 90                 # GPU 阈值
  auto_optimize: true               # 是否自动优化
```

## 5.3 离线模式

### 5.3.1 离线模式配置

**环境变量**：

```bash
# 强制离线模式
# 必须在导入任何模型相关模块之前设置
export TRANSFORMERS_OFFLINE=1
export HF_DATASETS_OFFLINE=1
export HF_HUB_OFFLINE=1

# 禁用遥测和警告
export HF_HUB_DISABLE_TELEMETRY=1
export HF_HUB_DISABLE_EXPERIMENTAL_WARNING=1
export HF_HUB_DISABLE_IMPORT_ERROR=1

# 模型缓存目录
export HF_HOME="data/models"
export HUGGINGFACE_HUB_CACHE="data/models"

# 禁用网络请求
export NO_PROXY='*'
export no_proxy='*'
```

### 5.3.2 离线模式注意事项

**重要说明**：

1. **环境变量设置**：
   - 环境变量必须在**代码最开头、导入任何模块之前**设置
   - 否则可能会尝试连接网络

2. **模型路径**：
   - `model_name_or_path` 必须使用**本地绝对路径**
   - 不能使用 HuggingFace 模型 ID
   - 否则可能会尝试下载模型

3. **模型完整性**：
   - 确保模型文件已完整下载
   - 检查模型文件是否存在
   - 验证模型文件完整性

4. **依赖项**：
   - 确保所有依赖项已安装
   - 检查依赖项版本
   - 解决依赖冲突

### 5.3.3 常见问题

**问题 1：LocalEntryNotFoundError**

**原因**：模型文件未找到或路径错误

**解决方法**：
1. 检查模型文件是否完整下载
2. 检查路径是否为绝对路径
3. 检查路径是否正确
4. 重新下载模型

**问题 2：网络连接错误**

**原因**：代码尝试连接网络

**解决方法**：
1. 确保环境变量已正确设置
2. 确保环境变量在导入模块之前设置
3. 检查代码是否有硬编码的网络请求
4. 使用离线模式测试

**问题 3：模型加载失败**

**原因**：模型文件损坏或版本不兼容

**解决方法**：
1. 检查模型文件完整性
2. 重新下载模型
3. 检查模型版本
4. 检查依赖项版本

## 5.4 故障排查

### 5.4.1 常见错误

**错误 1：内存不足**

**症状**：
- 程序崩溃
- 内存错误
- 系统卡顿

**解决方法**：
1. 减少批处理大小
2. 关闭其他程序
3. 增加系统内存
4. 使用更轻量级的模型

**错误 2：GPU 不可用**

**症状**：
- GPU 未使用
- 模型加载到 CPU
- 性能缓慢

**解决方法**：
1. 检查 GPU 驱动
2. 检查 CUDA 版本
3. 检查 PyTorch 版本
4. 检查配置文件

**错误 3：模型下载失败**

**症状**：
- 模型下载超时
- 模型文件损坏
- 模型验证失败

**解决方法**：
1. 检查网络连接
2. 检查代理设置
3. 手动下载模型
4. 验证模型完整性

**错误 4：文件扫描失败**

**症状**：
- 文件未识别
- 扫描速度慢
- 扫描结果为空

**解决方法**：
1. 检查文件权限
2. 检查文件格式
3. 检查文件大小
4. 检查扫描配置

### 5.4.2 日志分析

**日志位置**：
- 主日志：`logs/msearch.log`
- WebUI 日志：`logs/webui.log`
- 任务日志：`logs/task.log`
- 错误日志：`logs/error.log`

**日志级别**：
- DEBUG：调试信息
- INFO：一般信息
- WARN：警告信息
- ERROR：错误信息

**日志分析方法**：
1. 查看错误日志
2. 搜索关键字 (ERROR/Exception)
3. 分析错误堆栈
4. 定位问题代码
5. 查找解决方案

### 5.4.3 性能分析

**性能指标**：
- CPU 使用率
- 内存使用率
- GPU 使用率
- 磁盘 IO
- 网络 IO
- 任务处理时间
- 队列长度
- 错误率
- 吞吐量

**性能分析工具**：
- Linux：top, htop, nvidia-smi, iostat
- Windows：任务管理器, Resource Monitor
- macOS：活动监视器
- 应用内置监控：WebUI 监控页面

**性能优化方法**：
1. 分析性能瓶颈
2. 优化关键路径
3. 调整配置参数
4. 升级硬件配置
5. 使用更高效的算法

---

# 第六部分：进程间通信设计

## 6.1 进程边界划分

### 6.1.1 进程职责定义

基于资源需求和业务内聚性，划分以下独立进程：

| 进程名称 | 职责描述 | 资源需求 | 进程数 |
|---------|---------|---------|--------|
| **Main Process** | API服务、WebUI、任务调度 | 中 CPU，低内存 | 1 |
| **File Monitor** | 文件监控、目录扫描 | 低 CPU，低内存 | 1 |
| **Embedding Worker** | 模型加载、向量化推理 | 高 GPU/CPU，高内存 | 1-N |
| **Task Worker** | 媒体预处理、任务执行 | 中 CPU，中内存 | 1-N |

### 6.1.2 进程间依赖关系

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         进程依赖关系图                                       │
└─────────────────────────────────────────────────────────────────────────────┘

                    ┌─────────────────┐
                    │  Main Process   │
                    │   (主进程)       │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  File Monitor   │  │ Embedding Worker│  │  Task Worker    │
│  (文件监控)      │  │  (向量化)        │  │  (任务执行)      │
└─────────────────┘  └─────────────────┘  └─────────────────┘
         │                   │                   │
         └───────────────────┼───────────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ SQLite (本地)    │
                    │  (消息队列)      │
                    └─────────────────┘

依赖规则：
- Main Process 管理所有子进程的生命周期
- 子进程之间不直接通信，通过 SQLite 队列 + 本地IPC中转
- 所有进程共享 SQLite + LanceDB 存储
```

## 6.2 进程间通信机制

### 6.2.1 通信方式选择

| 通信场景 | 通信方式 | 说明 |
|---------|---------|------|
| 任务分发 | SQLite 队列（persist-queue） | 可靠、持久化、支持优先级 |
| 状态查询 | Unix Socket / Named Pipe | 低延迟、双向通信 |
| 大文件传输 | 共享内存 | 零拷贝、高性能 |
| 配置同步 | 文件 + 信号 | 简单可靠 |
| 日志收集 | 文件 / SQLite | 异步、不阻塞 |

### 6.2.2 SQLite 数据结构设计

```
# 任务队列
queue:tasks:pending      # 待处理任务队列 (List)
queue:tasks:processing   # 处理中任务集合 (Set)
queue:tasks:completed    # 已完成任务队列 (List, 限制长度)
queue:tasks:failed       # 失败任务队列 (List)

# 任务优先级队列
queue:tasks:priority:high    # 高优先级 (LPUSH)
queue:tasks:priority:normal  # 普通优先级
queue:tasks:priority:low     # 低优先级

# 进程状态
process:main:status          # 主进程状态 (Hash)
process:file_monitor:status  # 文件监控进程状态
process:embedding_worker:*   # 向量化工作进程状态 (通配符)
process:task_worker:*        # 任务工作进程状态

# 任务状态
task:{task_id}:status        # 任务状态 (Hash)
task:{task_id}:result        # 任务结果 (String, JSON)
task:{task_id}:progress      # 任务进度 (String)

# 心跳检测
heartbeat:file_monitor       # 文件监控进程心跳 (String, TTL)
heartbeat:embedding_worker:* # 向量化工作进程心跳
heartbeat:task_worker:*      # 任务工作进程心跳
```

### 6.2.3 共享内存设计

**使用场景**：
- 大文件数据传输（视频帧、音频数据）
- 避免序列化/反序列化开销

**实现方案**：
```python
# src/ipc/shared_memory.py
import mmap
import os
import struct

class SharedMemoryManager:
    """共享内存管理器"""
    
    def __init__(self, name: str, size: int = 100 * 1024 * 1024):  # 100MB
        self.name = name
        self.size = size
        self.mm = None
    
    def create(self):
        """创建共享内存"""
        # Linux/macOS: /dev/shm/{name}
        # Windows: 使用 mmap
        pass
    
    def write(self, data: bytes, offset: int = 0) -> int:
        """写入数据，返回实际写入字节数"""
        pass
    
    def read(self, offset: int, size: int) -> bytes:
        """读取数据"""
        pass
    
    def close(self):
        """关闭共享内存"""
        pass
```

## 6.3 进程接口定义

### 6.3.1 抽象接口层

```python
# src/interfaces/task_interface.py
from typing import Protocol, Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class TaskResult:
    task_id: str
    status: TaskStatus
    progress: float
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

class ITaskProcessor(Protocol):
    """任务处理器接口"""
    
    async def process_task(self, task_data: Dict[str, Any]) -> TaskResult:
        """处理任务"""
        ...
    
    async def get_capabilities(self) -> List[str]:
        """获取支持的任务类型"""
        ...
```

### 6.3.2 本地进程适配器

```python
# src/ipc/local_process_adapter.py
import persistqueue
import sqlite3
import json
import time
from typing import Dict, Any, Optional
from pathlib import Path

class LocalProcessAdapter:
    """
    本地进程适配器
    
    封装进程间通信细节，提供统一的接口
    使用SQLite队列替代Redis，更适合桌面应用
    - 启动时间<0.1秒（vs Redis 2-3秒）
    - 内存占用<10MB（vs Redis 150-200MB）
    - 零外部依赖，纯Python实现
    """
    
    def __init__(self, process_name: str, data_dir: str = 'data/ipc'):
        self.process_name = process_name
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化任务队列（基于SQLite）
        self.task_queue = persistqueue.SQLiteQueue(
            path=str(self.data_dir / f"queue_{process_name}"),
            multithreading=True,
            auto_commit=True
        )
        
        # 初始化状态缓存数据库
        self.state_db_path = self.data_dir / "state_cache.db"
        self._init_state_db()
    
    def _init_state_db(self):
        """初始化状态数据库"""
        conn = sqlite3.connect(str(self.state_db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS task_states (
                task_id TEXT PRIMARY KEY,
                state_data TEXT NOT NULL,
                last_updated REAL NOT NULL
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_task_states_updated 
            ON task_states(last_updated)
        ''')
        
        conn.commit()
        conn.close()
    
    async def send_task(self, task_type: str, task_data: Dict[str, Any], 
                       priority: int = 5) -> str:
        """发送任务到指定进程"""
        task_id = f"{self.process_name}_{int(time.time() * 1000)}"
        task = {
            "id": task_id,
            "type": task_type,
            "data": task_data,
            "priority": priority,
            "created_at": time.time(),
            "sender": self.process_name,
            "status": "pending"
        }
        
        # 使用SQLite队列，支持优先级
        self.task_queue.put(task, priority=priority)
        
        # 初始化任务状态
        self._update_task_state(task_id, {
            "status": "pending",
            "progress": 0.0,
            "created_at": task["created_at"]
        })
        
        return task_id
    
    async def get_task(self, timeout: float = 1.0) -> Optional[Dict[str, Any]]:
        """获取任务（阻塞式）"""
        try:
            # 从SQLite队列获取任务
            task = self.task_queue.get(block=True, timeout=timeout)
            
            # 更新任务状态为运行中
            self._update_task_state(task["id"], {
                "status": "running",
                "started_at": time.time()
            })
            
            return task
        except persistqueue.Empty:
            return None
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        conn = sqlite3.connect(str(self.state_db_path))
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT state_data FROM task_states WHERE task_id = ?',
            (task_id,)
        )
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return json.loads(result[0])
        return None
    
    async def update_task_progress(self, task_id: str, progress: float, 
                                   result: Dict = None):
        """更新任务进度"""
        current_state = self.get_task_status(task_id) or {}
        current_state.update({
            "progress": progress,
            "updated_at": time.time()
        })
        if result:
            current_state["result"] = result
        
        self._update_task_state(task_id, current_state)
    
    async def complete_task(self, task_id: str, result: Dict = None, 
                           error: str = None):
        """完成任务"""
        state_data = {
            "status": "completed" if not error else "failed",
            "progress": 1.0 if not error else 0.0,
            "completed_at": time.time()
        }
        if result:
            state_data["result"] = result
        if error:
            state_data["error_message"] = error
        
        self._update_task_state(task_id, state_data)
        self.task_queue.task_done()
    
    def _update_task_state(self, task_id: str, state_data: Dict):
        """更新任务状态到SQLite"""
        conn = sqlite3.connect(str(self.state_db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO task_states (task_id, state_data, last_updated)
            VALUES (?, ?, ?)
        ''', (task_id, json.dumps(state_data), time.time()))
        
        conn.commit()
        conn.close()
```

## 6.4 进程生命周期管理

### 6.4.1 进程管理器

```python
# src/core/process/process_manager.py
import multiprocessing
import signal
from typing import Dict, Callable

class ProcessManager:
    """进程管理器"""
    
    def __init__(self):
        self.processes: Dict[str, multiprocessing.Process] = {}
        self.heartbeat_timeout = 30  # 秒
        self._shutdown_event = multiprocessing.Event()
    
    def start_process(
        self,
        name: str,
        target: Callable,
        args: tuple = (),
        kwargs: dict = None
    ) -> multiprocessing.Process:
        """启动进程"""
        process = multiprocessing.Process(
            name=name,
            target=target,
            args=args,
            kwargs=kwargs or {},
            daemon=True
        )
        process.start()
        self.processes[name] = process
        
        logger.info(f"Process {name} started with PID {process.pid}")
        return process
    
    def monitor_processes(self):
        """监控所有进程状态"""
        for name, process in list(self.processes.items()):
            if not process.is_alive():
                logger.error(f"Process {name} (PID {process.pid}) is not alive")
                # 根据策略决定是否重启
                self._handle_process_failure(name)
    
    def _handle_process_failure(self, name: str):
        """处理进程故障"""
        # 实现重启策略
        pass
    
    def shutdown_all(self, timeout: int = 30):
        """优雅关闭所有进程"""
        logger.info("Shutting down all processes...")
        
        # 设置关闭事件
        self._shutdown_event.set()
        
        # 发送终止信号
        for name, process in self.processes.items():
            logger.info(f"Terminating process {name} (PID {process.pid})")
            process.terminate()
        
        # 等待进程结束
        for name, process in self.processes.items():
            process.join(timeout=timeout)
            if process.is_alive():
                logger.warning(f"Force killing process {name}")
                process.kill()
        
        logger.info("All processes shutdown complete")
```

### 6.4.2 优雅关闭流程

```
1. 接收关闭信号 (SIGTERM)
2. 停止接收新任务
3. 等待处理中任务完成（超时 30 秒）
4. 保存状态
5. 关闭连接
6. 退出进程
```

**实现代码**：
```python
# src/workers/base_worker.py
import signal
import sys

class BaseWorker:
    """工作进程基类"""
    
    def __init__(self):
        self._shutdown_requested = False
        self._current_task = None
        
        # 注册信号处理器
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)
    
    def _handle_shutdown(self, signum, frame):
        """处理关闭信号"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self._shutdown_requested = True
        
        # 如果正在处理任务，等待完成
        if self._current_task:
            logger.info(f"Waiting for current task {self._current_task} to complete...")
    
    def run(self):
        """主循环"""
        while not self._shutdown_requested:
            try:
                # 获取任务
                task = self._get_task(timeout=1.0)
                if not task:
                    continue
                
                self._current_task = task["id"]
                
                # 处理任务
                self._process_task(task)
                
                self._current_task = None
                
            except Exception as e:
                logger.error(f"Error processing task: {e}")
        
        logger.info("Worker shutdown complete")
```

---

# 第七部分：服务化演进（参考）

## 7.1 演进路线图

本文档聚焦于**本地多进程单机应用**架构设计。关于未来向容器化、微服务集群演进的详细设计，请参考专用文档。

## 7.2 演进原则

**当前阶段（本地多进程）**：
- 保持架构简洁
- 进程间通过 SQLite队列 + 本地IPC + 共享内存通信
- 单机部署，易于维护

**未来演进（容器化/微服务）**：
- 复用现有接口定义
- 只需实现新的通信适配器
- 渐进式拆分，降低迁移成本

---

# 第七部分：测试与质量

## 6.1 测试策略

### 6.1.1 单元测试

**测试目标**：
- 测试单个函数/方法
- 测试边界条件
- 测试错误处理
- 测试性能

**测试框架**：
- pytest
- unittest
- coverage

**测试覆盖率**：
- 目标覆盖率：≥ 80%
- 关键模块：≥ 90%
- 核心功能：100%

**测试示例**：

```python
def test_image_preprocessor():
    """测试图像预处理"""
    preprocessor = ImagePreprocessor()
    
    # 测试正常图像
    image = preprocessor.preprocess("test.jpg")
    assert image.shape == (3, 512, 512)
    
    # 测试边界条件
    with pytest.raises(ValueError):
        preprocessor.preprocess("invalid.jpg")
    
    # 测试性能
    start_time = time.time()
    for _ in range(100):
        preprocessor.preprocess("test.jpg")
    elapsed_time = time.time() - start_time
    assert elapsed_time < 1.0  # 100 次处理 < 1 秒
```

### 6.1.2 集成测试

**测试目标**：
- 测试模块之间的交互
- 测试数据流
- 测试接口
- 测试异常处理

**测试方法**：
- 黑盒测试
- 灰盒测试
- 端到端测试

**测试示例**：

```python
async def test_image_processing_pipeline():
    """测试图像处理流程"""
    # 初始化模块
    config = ConfigManager()
    model_manager = ModelManager(config)
    image_processor = ImageProcessor(config, model_manager)
    
    # 加载模型
    await model_manager.load_model("chinese_clip_base")
    
    # 处理图像
    file_info = FileInfo(path="test.jpg", file_type="image")
    result = await image_processor.process(file_info)
    
    # 验证结果
    assert result.success
    assert result.embedding is not None
    assert len(result.embedding) == 512
    
    # 验证性能
    assert result.processing_time < 1.0  # 处理时间 < 1 秒
```

### 6.1.3 性能测试

**测试目标**：
- 测试系统性能
- 测试响应时间
- 测试吞吐量
- 测试资源消耗

**测试工具**：
- pytest-benchmark
- locust
- wrk
- ab

**性能基准**：
- 图像处理：< 500ms/张
- 视频处理：< 5秒/10秒视频
- 音频处理：< 1秒/30秒音频
- 文本检索：< 300ms/次
- 图像检索：< 400ms/次
- 视频检索：< 2秒/次
- 音频检索：< 1秒/次

**测试示例**：

```python
@pytest.mark.benchmark(group="image_processing")
def test_image_processing_performance(benchmark):
    """测试图像处理性能"""
    preprocessor = ImagePreprocessor()
    
    def process_image():
        preprocessor.preprocess("test.jpg")
    
    benchmark(process_image)
    
    # 验证性能
    stats = benchmark.stats
    assert stats.mean < 0.1  # 平均处理时间 < 100ms
    assert stats.stdev < 0.05  # 标准差 < 50ms
```

### 6.1.4 压力测试

**测试目标**：
- 测试系统稳定性
- 测试系统极限
- 测试故障恢复
- 测试资源管理

**测试方法**：
- 高并发测试
- 大数据量测试
- 长时间运行测试
- 故障注入测试

**测试示例**：

```python
async def test_high_concurrency():
    """测试高并发处理"""
    # 初始化模块
    config = ConfigManager()
    model_manager = ModelManager(config)
    image_processor = ImageProcessor(config, model_manager)
    
    # 加载模型
    await model_manager.load_model("chinese_clip_base")
    
    # 并发处理 100 个图像
    file_infos = [FileInfo(path=f"test_{i}.jpg", file_type="image") for i in range(100)]
    
    start_time = time.time()
    tasks = [image_processor.process(info) for info in file_infos]
    results = await asyncio.gather(*tasks)
    elapsed_time = time.time() - start_time
    
    # 验证结果
    success_count = sum(1 for r in results if r.success)
    assert success_count == 100  # 全部成功
    
    # 验证性能
    assert elapsed_time < 10.0  # 100 个图像 < 10 秒
    assert elapsed_time / 100 < 0.2  # 平均 < 200ms/张
```

## 6.2 性能基准

### 6.2.1 硬件配置

**测试环境**：
- CPU：Intel Core i7-10700K (8核16线程)
- 内存：32GB DDR4 3200MHz
- GPU：NVIDIA RTX 3080 (10GB VRAM)
- 存储：SSD 1TB
- 操作系统：Ubuntu 20.04 LTS

### 6.2.2 性能指标

**图像处理**：
- 预处理时间：< 50ms/张
- 向量化时间：< 100ms/张
- 总处理时间：< 200ms/张
- 吞吐量：> 5 张/秒

**视频处理**：
- 预处理时间：< 2000ms/10秒视频
- 向量化时间：< 1000ms/10秒视频
- 总处理时间：< 4000ms/10秒视频
- 吞吐量：> 0.25 个/秒

**音频处理**：
- 预处理时间：< 200ms/30秒音频
- 向量化时间：< 500ms/30秒音频
- 总处理时间：< 800ms/30秒音频
- 吞吐量：> 1.25 个/秒

**文本检索**：
- 向量化时间：< 50ms
- 向量检索时间：< 100ms
- 总检索时间：< 200ms
- 吞吐量：> 5 次/秒

**图像检索**：
- 预处理时间：< 50ms
- 向量化时间：< 100ms
- 向量检索时间：< 100ms
- 总检索时间：< 300ms
- 吞吐量：> 3 次/秒

**视频检索**：
- 预处理时间：< 500ms
- 向量化时间：< 500ms
- 向量检索时间：< 100ms
- 总检索时间：< 1500ms
- 吞吐量：> 0.67 次/秒

**音频检索**：
- 预处理时间：< 200ms
- 向量化时间：< 500ms
- 向量检索时间：< 100ms
- 总检索时间：< 1000ms
- 吞吐量：> 1 次/秒

### 6.2.3 资源消耗

**内存消耗**：
- 启动内存：< 1GB
- 运行内存：< 4GB
- 峰值内存：< 8GB

**CPU 消耗**：
- 空闲 CPU：< 10%
- 运行 CPU：< 80%
- 峰值 CPU：< 90%

**GPU 消耗**：
- 空闲 GPU：< 10%
- 运行 GPU：< 80%
- 峰值 GPU：< 90%

**磁盘消耗**：
- 模型存储：< 10GB
- 向量存储：< 1GB/10000 文件
- 元数据存储：< 100MB/10000 文件

## 6.3 质量标准

### 6.3.1 代码质量

**代码规范**：
- 遵循 PEP 8 规范
- 使用类型注解
- 编写文档字符串
- 保持代码简洁

**代码审查**：
- 所有代码必须经过审查
- 审查覆盖率：100%
- 审查标准：代码质量、性能、安全性

**代码质量工具**：
- pylint：代码规范检查
- mypy：类型检查
- black：代码格式化
- isort：导入排序

### 6.3.2 文档质量

**文档规范**：
- 编写详细的文档字符串
- 编写 API 文档
- 编写用户手册
- 编写部署指南

**文档覆盖率**：
- 公共 API：100%
- 核心模块：100%
- 工具函数：≥ 80%

**文档质量工具**：
- sphinx：文档生成
- pdoc：API 文档生成
- mkdocs：文档站点

### 6.3.3 测试质量

**测试覆盖率**：
- 单元测试覆盖率：≥ 80%
- 集成测试覆盖率：≥ 70%
- 端到端测试覆盖率：≥ 60%

**测试质量**：
- 测试用例清晰
- 测试边界条件
- 测试错误处理
- 测试性能

**测试质量工具**：
- coverage：覆盖率统计
- pytest-cov：覆盖率报告
- pytest-html：HTML 报告

### 6.3.4 安全性

**安全标准**：
- 遵循安全开发规范
- 输入验证
- 输出编码
- 错误处理
- 日志记录

**安全审查**：
- 定期安全审查
- 漏洞扫描
- 渗透测试
- 安全审计

**安全工具**：
- bandit：安全扫描
- safety：依赖安全检查
- snyk：漏洞扫描

---

# 附录

## A. 术语表

**多模态检索**：支持多种数据类型（文本、图像、视频、音频）的检索技术

**向量化**：将数据转换为向量表示的过程

**向量检索**：基于向量相似度的检索技术

**Embedding**：数据的向量表示

**LanceDB**：开源向量数据库

**Infinity**：统一模型运行时框架

**CLIP**：Contrastive Language-Image Pre-training，对比语言-图像预训练模型

**CLAP**：Contrastive Language-Audio Pre-training，对比语言-音频预训练模型

**GPU**：Graphics Processing Unit，图形处理器

**CPU**：Central Processing Unit，中央处理器

**CUDA**：Compute Unified Device Architecture，统一计算设备架构

**IVF**：Inverted File，倒排文件索引

**HNSW**：Hierarchical Navigable Small Worlds，分层导航小世界索引

## B. 参考文献

1. [michaelfeil/infinity](https://github.com/michaelfeil/infinity)
2. [LanceDB](https://github.com/lancedb/lancedb)
3. [OpenAI CLIP](https://github.com/openai/CLIP)
4. [LAION CLAP](https://github.com/LAION-AI/CLAP)
5. [Hugging Face Transformers](https://github.com/huggingface/transformers)
6. [PyTorch](https://pytorch.org/)
7. [Gradio](https://gradio.app/)
8. [SQLite](https://www.sqlite.org/)

## C. 更新日志

### v1.0 (2026-01-24)

**主要更新**：
- 重新组织设计文档结构
- 整合 data_flow.md 和 file_scanner_design_refinement.md
- 优化文档格式和可读性
- 补充详细流程设计
- 补充性能优化设计
- 补充部署与运维指南
- 补充测试与质量标准
- **新增任务控制功能**（2026-01-24更新）
  - 支持任务优先级动态调整
  - 支持取消单个任务
  - 支持批量取消所有任务
  - 支持按类型批量取消任务
  - 新增任务进度跟踪字段（current_step、step_progress）
  - 完善任务控制API接口
  - 添加任务控制API集成测试

### v1.0 (2026-01-19)

**初始版本**：
- 项目概述和核心设计原则
- 系统架构图和技术栈选型
- 数据流转总览
- 核心组件设计
- 详细流程设计

---

**文档维护者**：msearch 开发团队

**联系方式**：msearch@example.com

**最后更新**：2026-01-24

---

*本文档遵循 msearch 项目设计规范，如有疑问请联系开发团队。*