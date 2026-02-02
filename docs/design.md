# msearch 多模态搜索系统设计文档

## 目录

1. [第一部分：整体架构设计](#第一部分整体架构设计)
   - [1.1 项目概述](#11-项目概述)
   - [1.2 核心设计原则](#12-核心设计原则)
   - [1.3 系统架构图](#13-系统架构图)
   - [1.4 技术栈选型](#14-技术栈选型)
   - [1.5 数据流转总览](#15-数据流转总览)
   - [1.6 单进程多线程架构设计](#16-单进程多线程架构设计)

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
   - [3.4 目录监控与增量索引流程](#34-目录监控与增量索引流程)

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

6. [第六部分：任务队列与通信设计](#第六部分任务队列与通信设计)
   - [6.1 任务队列设计](#61-任务队列设计)
   - [6.2 SQLite队列实现](#62-sqlite队列实现)
   - [6.3 组件通信机制](#63-组件通信机制)

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
- 支持灵活组合：可以根据需要组合不同的模块

**实现方式**：
```python
# ❌ 不推荐：直接导入其他模块
from core.config import ConfigManager
config = ConfigManager()

# ✅ 推荐：通过参数传递
class MyComponent:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
```

### 1.2.2 配置驱动原则

所有可变参数都通过配置文件管理，代码中不出现硬编码的配置值。

**核心原则**：
- 程序代码不进行任何硬件检测
- 硬件检测在安装脚本中完成
- 程序启动时直接读取配置

**允许**：
```python
# ✅ 允许：从配置读取
device = config.get('models.available_models.chinese_clip_large.device')

# ✅ 允许：运行时监控GPU内存使用（资源监控）
if gpu_memory > threshold:
    logger.warning("GPU内存不足")
```

**禁止**：
```python
# ❌ 禁止：运行时检测硬件并选择设备
if torch.cuda.is_available():
    device = 'cuda'
else:
    device = 'cpu'

# ❌ 禁止：硬编码设备选择
device = 'cuda:0'

# ❌ 禁止：硬编码禁用 GPU
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
```

### 1.2.3 单进程多线程架构原则

**核心原则**：采用单进程架构，使用线程池处理并发任务，简化架构复杂度。

**设计要求**：
- **单进程架构**：所有组件运行在同一进程中，避免进程间通信开销
- **线程池并发**：使用线程池处理I/O密集型和计算密集型任务
- **SQLite队列**：任务队列、状态通知统一使用SQLite实现
- **状态外置**：任务状态存储在外部存储（SQLite），便于恢复

**线程池划分**：
| 线程池名称 | 职责 | 资源需求 | 线程数 |
|-----------|------|---------|--------|
| **Embedding Pool** | 向量化推理 | 高 GPU/CPU，高内存 | 1-4 |
| **I/O Pool** | 文件I/O、网络I/O | 低 CPU，低内存 | 4-8 |
| **Task Pool** | 任务执行（非推理类） | 中 CPU，中内存 | 4-8 |

**代码组织要求**：
```
src/
├── interfaces/          # 抽象接口定义
│   ├── __init__.py
│   ├── task_interface.py      # 任务接口
│   ├── embedding_interface.py # 向量化接口
│   └── storage_interface.py   # 存储接口
├── core/               # 核心业务实现
│   ├── task/          # 任务管理
│   ├── embedding/     # 向量化引擎
│   └── ...
├── workers/           # 线程池实现
│   ├── __init__.py
│   ├── embedding_worker.py    # 向量化线程池
│   ├── file_monitor.py        # 文件监控线程
│   └── task_worker.py         # 任务执行线程
└── api/               # 接入层（REST API）
    └── v1/
```

**任务队列方式**：
- **SQLite 队列**：任务队列、状态通知统一使用SQLite实现
- **内存队列**：任务快速传递（小数据）
- **文件共享**：大文件数据传输（视频帧、音频数据）

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
│                         服务层 (Services) - 线程池调用                        │
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

### 1.3.2 单进程多线程架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         msearch 单进程多线程架构图                             │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌─────────────────┐
                              │  Python Process │
                              │   (主进程)       │
                              └────────┬────────┘
                                       │
    ┌──────────────────────────────────┼──────────────────────────────────┐
    │                                  │                                  │
    ▼                                  ▼                                  ▼
┌─────────────────┐          ┌─────────────────┐          ┌─────────────────┐
│  Main Thread    │          │  Thread Pool    │          │  Thread Pool    │
│  (主线程)        │          │  (Embedding)    │          │  (I/O Tasks)    │
│                 │          │                 │          │                 │
│ ┌─────────────┐ │          │ ┌─────────────┐ │          │ ┌─────────────┐ │
│ │  API Server │ │          │ │ Model Load  │ │          │ │ File I/O    │ │
│ │  (FastAPI)  │ │          │ │ Inference   │ │          │ │ Task Exec   │ │
│ └─────────────┘ │          │ └─────────────┘ │          │ └─────────────┘ │
│                 │          │                 │          │                 │
│ ┌─────────────┐ │          │ Thread-1 to N   │          │ Thread-1 to N   │
│ │ Task Queue  │ │          │ (GPU/CPU计算)   │          │ (I/O密集型)     │
│ │ (SQLite)    │ │          │                 │          │                 │
│ └─────────────┘ │          └─────────────────┘          └─────────────────┘
│                 │
│ ┌─────────────┐ │
│ │ File Monitor│ │  ◄── 独立线程监控文件变化
│ │  (Thread)   │ │
│ └─────────────┘ │
└─────────────────┘

通信机制：
- 组件间通过 SQLite 队列通信
- 线程间通过内存队列传递数据
- 大文件通过文件系统共享
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

**注意**：向量维度按照模型默认值，不强制统一为512维。chinese_clip_base为512维，chinese_clip_large为768维。

#### 音频向量化模型

| 模型ID | 模型名称 | 硬件要求 | 模型大小 | 向量维度 | 批处理大小 | 适用场景 |
|--------|---------|---------|---------|---------|-----------|---------|
| audio_model | laion/clap-htsat-unfused | CPU/8GB 内存或 GPU/4GB 显存 | ~590MB | 512 | 8 | 文本-音频检索、音频分类 |

### 1.4.3 其他组件

- **LanceDB**：向量数据库（单一向量表设计）
- **SQLite**：元数据存储、任务队列
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
           │  ┌──────────────────────────────────────────────────────────┐  │
           │  │  - 图像向量化 (Image Embedding)                          │  │
           │  │  - 视频向量化 (Video Embedding)                          │  │
           │  │  - 音频向量化 (Audio Embedding)                          │  │
           │  │  - 文本向量化 (Text Embedding)                           │  │
           │  └──────────────────────────────────────────────────────────┘  │
           └────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
           ┌────────────────────────────────────────────────────────────────┐
           │                    向量存储 (VectorStore)                       │
           │  ┌──────────────────────────────────────────────────────────┐  │
           │  │  表名: unified_vectors                                   │  │
           │  │  - 向量维度: 按模型默认值 (512/768等)                      │  │
           │  │  - 支持多模态统一存储                                     │  │
           │  └──────────────────────────────────────────────────────────┘  │
           └────────────────────────────────────────────────────────────────┘
```

## 1.6 单进程多线程架构设计

### 1.6.1 线程池划分

**设计目标**：使用线程池处理并发任务，简化架构复杂度，避免进程间通信开销。

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         msearch 单进程多线程架构图                             │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌─────────────────┐
                              │  Python Process │
                              │   (主进程)       │
                              └────────┬────────┘
                                       │
    ┌──────────────────────────────────┼──────────────────────────────────┐
    │                                  │                                  │
    ▼                                  ▼                                  ▼
┌─────────────────┐          ┌─────────────────┐          ┌─────────────────┐
│  Main Thread    │          │  Thread Pool    │          │  Thread Pool    │
│  (主线程)        │          │  (Embedding)    │          │  (I/O Tasks)    │
│                 │          │                 │          │                 │
│ ┌─────────────┐ │          │ ┌─────────────┐ │          │ ┌─────────────┐ │
│ │  API Server │ │          │ │ Model Load  │ │          │ │ File I/O    │ │
│ │  (FastAPI)  │ │          │ │ Inference   │ │          │ │ Task Exec   │ │
│ └─────────────┘ │          │ └─────────────┘ │          │ └─────────────┘ │
│                 │          │                 │          │                 │
│ ┌─────────────┐ │          │ Thread-1 to N   │          │ Thread-1 to N   │
│ │ Task Queue  │ │          │ (GPU/CPU计算)   │          │ (I/O密集型)     │
│ │ (SQLite)    │ │          │                 │          │                 │
│ └─────────────┘ │          └─────────────────┘          └─────────────────┘
│                 │
│ ┌─────────────┐ │
│ │ File Monitor│ │  ◄── 独立线程监控文件变化
│ │  (Thread)   │ │
│ └─────────────┘ │
└─────────────────┘
```

### 1.6.2 线程池职责说明

#### Embedding Pool (向量化线程池)

**职责**：
- 模型加载和推理
- 图像/视频/音频向量化
- GPU/CPU计算任务

**线程数**：1-4（根据GPU数量和显存配置）

**特点**：
- 计算密集型任务
- 需要访问GPU资源
- 线程数不宜过多，避免GPU资源竞争

#### I/O Pool (I/O线程池)

**职责**：
- 文件读写操作
- 网络请求
- 数据库操作

**线程数**：4-8

**特点**：
- I/O密集型任务
- 不会阻塞主线程
- 可以处理大量并发I/O操作

#### Task Pool (任务线程池)

**职责**：
- 媒体预处理（非推理类）
- 视频切片
- 音频分离
- 缩略图生成

**线程数**：4-8

**特点**：
- CPU密集型但非GPU任务
- 可以并行处理多个文件
- 避免阻塞向量化线程池

### 1.6.3 线程池配置

```yaml
# config/config.yml

thread_pools:
  # 向量化线程池
  embedding:
    max_workers: 2
    thread_name_prefix: "embedding_"
    
  # I/O线程池
  io:
    max_workers: 4
    thread_name_prefix: "io_"
    
  # 任务线程池
  task:
    max_workers: 4
    thread_name_prefix: "task_"
```

**线程池实现**：

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

class ThreadPoolManager:
    """线程池管理器"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.pools: Dict[str, ThreadPoolExecutor] = {}
        
    def initialize(self):
        """初始化线程池"""
        # 向量化线程池
        self.pools['embedding'] = ThreadPoolExecutor(
            max_workers=self.config['embedding']['max_workers'],
            thread_name_prefix=self.config['embedding']['thread_name_prefix']
        )
        
        # I/O线程池
        self.pools['io'] = ThreadPoolExecutor(
            max_workers=self.config['io']['max_workers'],
            thread_name_prefix=self.config['io']['thread_name_prefix']
        )
        
        # 任务线程池
        self.pools['task'] = ThreadPoolExecutor(
            max_workers=self.config['task']['max_workers'],
            thread_name_prefix=self.config['task']['thread_name_prefix']
        )
        
    def submit(self, pool_name: str, fn, *args, **kwargs):
        """提交任务到指定线程池"""
        if pool_name not in self.pools:
            raise ValueError(f"未知的线程池: {pool_name}")
        return self.pools[pool_name].submit(fn, *args, **kwargs)
        
    def shutdown(self):
        """关闭所有线程池"""
        for pool in self.pools.values():
            pool.shutdown(wait=True)

# 线程池配置
thread_pool_manager = ThreadPoolManager(config['thread_pools'])
thread_pool_manager.initialize()

# 提交任务到向量化线程池
future = thread_pool_manager.submit('embedding', embed_image, image_path)
result = future.result()
```

---

# 第二部分：核心组件设计

## 2.1 配置管理系统

### 2.1.1 配置结构

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
      device: "cpu"  # 由安装脚本检测并配置
      dtype: "float32"
      embedding_dim: 512  # 按模型默认值
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
      embedding_dim: 768  # 按模型默认值，不强制512维
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
    - chinese_clip_base
    - audio_model

# 线程池配置
thread_pools:
  embedding:
    max_workers: 2
    thread_name_prefix: "embedding_"
  io:
    max_workers: 4
    thread_name_prefix: "io_"
  task:
    max_workers: 4
    thread_name_prefix: "task_"

# 文件监控配置
file_monitor:
  watch_directories:
    - "testdata"
  scan_interval: 60
  supported_extensions:
    - ".jpg"
    - ".jpeg"
    - ".png"
    - ".mp4"
    - ".avi"
    - ".mov"
    - ".mp3"
    - ".wav"
    - ".flac"

# 音频预处理配置
processing:
  audio:
    sample_rate: 48000  # CLAP模型要求48kHz
    channels: 1  # 单声道
    format: wav
    min_duration: 3.0

# 视频预处理配置
media:
  video:
    short_video:
      threshold: 6.0  # 短视频阈值（秒）
    large_video:
      segment_duration: 5.0
    scene_detection:
      enabled: true
      method: histogram
      threshold: 30.0
      min_scene_length: 2.0

# 向量存储配置
vector_store:
  data_dir: "data/database/lancedb"
  collection_name: "unified_vectors"
  index_type: "ivf_pq"
  num_partitions: 128
  # 注意：向量维度按模型默认值，不强制统一

# 数据库配置
database:
  db_path: "data/database/sqlite/msearch.db"
  check_same_thread: false
  max_workers: 4

# 任务队列配置（SQLite队列）
task_queue:
  db_path: "data/database/sqlite/task_queue.db"
  max_retries: 3
  retry_delay: 5.0
  default_priority: 5
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

class InfinityModelManager:
    """Infinity 模型管理器"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.engines: Dict[str, AsyncEmbeddingEngine] = {}
        
    async def load_model(self, model_config: Dict) -> AsyncEmbeddingEngine:
        """加载模型"""
        engine_args = EngineArgs(
            model_name_or_path=model_config['local_path'],
            engine=model_config.get('engine', 'torch'),
            device=model_config.get('device', 'cpu'),
            batch_size=model_config.get('batch_size', 16),
        )
        
        engine = AsyncEmbeddingEngine.from_args(engine_args)
        await engine.astart()
        
        return engine
        
    async def embed(self, model_id: str, inputs: List[str], input_type: str = "text") -> np.ndarray:
        """向量化"""
        engine = self.engines.get(model_id)
        if not engine:
            raise ValueError(f"模型 {model_id} 未加载")
            
        embeddings = await engine.embed(
            sentences=inputs,
            input_type=input_type
        )
        
        return embeddings
```

## 2.3 文件扫描系统

### 2.3.1 文件扫描器设计

```python
class FileScanner:
    """
    文件扫描器 - 负责扫描目录并识别支持的文件
    """
    
    def __init__(self, supported_extensions: List[str]):
        self.supported_extensions = supported_extensions
        
    def scan_directory(self, directory: str) -> List[str]:
        """
        扫描目录，返回支持的文件列表
        
        Args:
            directory: 目录路径
            
        Returns:
            文件路径列表
        """
        file_paths = []
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                if any(file.lower().endswith(ext) for ext in self.supported_extensions):
                    file_paths.append(os.path.join(root, file))
                    
        return file_paths
```

### 2.3.2 文件监控器设计

```python
class FileMonitor:
    """
    文件监控器 - 负责监控目录变化
    
    运行方式：独立线程运行
    通信方式：通过SQLite队列发送文件事件
    """
    
    def __init__(self, config: Dict, queue_manager: QueueManager):
        self.config = config
        self.queue_manager = queue_manager
        self.watch_directories = config.get('watch_directories', [])
        self.scan_interval = config.get('scan_interval', 60)
        self.observer = Observer()
        
    def start(self):
        """启动文件监控"""
        for directory in self.watch_directories:
            handler = FileChangeHandler(self.queue_manager)
            self.observer.schedule(handler, directory, recursive=True)
        self.observer.start()
        
    def stop(self):
        """停止文件监控"""
        self.observer.stop()
        self.observer.join()

class FileChangeHandler(FileSystemEventHandler):
    """文件变化处理器"""
    
    def __init__(self, queue_manager: QueueManager):
        self.queue_manager = queue_manager
        
    def on_created(self, event):
        """文件创建事件"""
        if not event.is_directory:
            self.queue_manager.put('file_events', {
                'event_type': 'created',
                'file_path': event.src_path,
                'timestamp': time.time()
            })
            
    def on_modified(self, event):
        """文件修改事件"""
        if not event.is_directory:
            self.queue_manager.put('file_events', {
                'event_type': 'modified',
                'file_path': event.src_path,
                'timestamp': time.time()
            })
            
    def on_deleted(self, event):
        """文件删除事件"""
        if not event.is_directory:
            self.queue_manager.put('file_events', {
                'event_type': 'deleted',
                'file_path': event.src_path,
                'timestamp': time.time()
            })
```

## 2.4 数据处理系统

### 2.4.1 数据处理器架构

```
┌─────────────────────────────────────────────────────────────────┐
│                      DataProcessor                               │
│                     （数据处理协调器）                            │
└─────────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
    ┌─────▼─────┐      ┌─────▼─────┐      ┌─────▼─────┐
    │  Image    │      │  Video    │      │  Audio    │
    │ Processor │      │ Processor │      │ Processor │
    └─────┬─────┘      └─────┬─────┘      └─────┬─────┘
          │                   │                   │
          ▼                   ▼                   ▼
    ┌───────────┐      ┌───────────┐      ┌───────────┐
    │ 预处理     │      │ 预处理     │      │ 预处理     │
    │ 向量化     │      │ 切片/抽帧  │      │ 重采样     │
    │           │      │ 向量化     │      │ 向量化     │
    └───────────┘      └───────────┘      └───────────┘
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
    
    预处理流程：
    1. 价值判断（≥3秒）
    2. 重采样到 48kHz（CLAP模型要求）
    3. 转换为单声道
    4. 归一化
    """
    
    def __init__(self, config: ConfigManager, model_manager: ModelManager):
        self.config = config
        self.model_manager = model_manager
        # 目标采样率 48kHz（CLAP模型要求）
        self.target_sample_rate = 48000
        self.target_channels = 1
        
    async def process(self, file_info: FileInfo) -> AudioProcessingResult:
        """处理音频文件"""
        # 1. 检查音频时长
        duration = self.get_audio_duration(file_info.file_path)
        if duration < 3.0:
            return AudioProcessingResult(
                success=False,
                error="音频时长不足3秒"
            )
        
        # 2. 预处理
        audio_data = self.preprocess(file_info.file_path)
        
        # 3. 向量化
        embedding = await self.embed(audio_data)
        
        return AudioProcessingResult(
            success=True,
            embedding=embedding,
            duration=duration
        )
    
    def preprocess(self, audio_path: str) -> np.ndarray:
        """
        音频预处理
        
        处理流程：
        1. 加载音频
        2. 重采样到 48kHz
        3. 转换为单声道
        4. 归一化
        """
        # 加载音频
        audio, sr = librosa.load(audio_path, sr=None, mono=False)
        
        # 重采样到 48kHz
        if sr != self.target_sample_rate:
            audio = librosa.resample(
                audio, 
                orig_sr=sr, 
                target_sr=self.target_sample_rate
            )
        
        # 转换为单声道
        if audio.ndim > 1:
            audio = librosa.to_mono(audio)
        
        # 归一化
        audio = librosa.util.normalize(audio)
        
        return audio
    
    async def embed(self, audio_data: np.ndarray) -> np.ndarray:
        """音频向量化"""
        pass
```

## 2.5 任务管理系统

### 2.5.1 任务管理架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    CentralTaskManager                            │
│                   （中央任务管理器）                              │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  职责：任务生命周期管理、组件协调、调度循环控制              │  │
│  │  明确边界：                                                 │  │
│  │  ✅ 负责任务的创建、取消、状态查询                          │  │
│  │  ✅ 协调各组件完成调度流程                                  │  │
│  │  ✅ 维护调度循环，触发任务调度                              │  │
│  │  ❌ 不直接计算优先级（委托给TaskScheduler）                 │  │
│  │  ❌ 不直接执行任务（委托给TaskExecutor）                    │  │
│  │  ❌ 不直接管理任务组锁（委托给TaskGroupManager）            │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
    ┌─────▼─────┐      ┌─────▼─────┐      ┌─────▼─────┐
    │  Task     │      │  Task     │      │  Task     │
    │ Scheduler │      │ Executor  │      │  Monitor  │
    │           │      │           │      │           │
    │ 优先级计算 │      │ 任务执行   │      │ 状态跟踪   │
    │ 队列管理   │      │ 错误处理   │      │ 统计记录   │
    └───────────┘      └───────────┘      └───────────┘
```

### 2.5.2 CentralTaskManager 类设计

```python
class CentralTaskManager:
    """
    中央任务管理器：统一协调所有任务管理功能
    
    职责：
    - 任务生命周期管理（创建、执行、取消）
    - 组件协调和集成（orchestrator 角色）
    - 对外提供统一的任务管理接口
    - 调度循环控制
    
    明确边界：
    - ✅ 负责任务的创建、取消、状态查询
    - ✅ 协调各组件完成调度流程
    - ✅ 维护调度循环，触发任务调度
    - ❌ 不直接计算优先级（委托给TaskScheduler）
    - ❌ 不直接执行任务（委托给TaskExecutor）
    - ❌ 不直接管理任务组锁（委托给TaskGroupManager）
    """
    
    def __init__(
        self,
        config: Dict[str, Any],
        task_scheduler: TaskScheduler,
        task_executor: TaskExecutor,
        task_monitor: TaskMonitor,
        task_group_manager: TaskGroupManager,
        device: str = 'cpu'
    ):
        """
        初始化中央任务管理器
        
        Args:
            config: 配置字典
            task_scheduler: 任务调度器
            task_executor: 任务执行器
            task_monitor: 任务监控器
            task_group_manager: 任务组管理器
            device: 设备类型（cuda/cpu）
        """
        self.config = config
        self.device = device
        
        # 任务配置
        self.task_config = config.get('task_manager', {})
        
        # 依赖注入：通过构造函数参数接收组件
        self.task_scheduler = task_scheduler
        self.task_executor = task_executor
        self.task_monitor = task_monitor
        self.group_manager = task_group_manager
        
        # 任务处理器
        self.task_handlers: Dict[str, Callable] = {}
        
        # 线程控制
        self.is_running = False
        self.worker_thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()
        
        # 统计信息
        self.stats = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'cancelled_tasks': 0,
            'retried_tasks': 0
        }
        
        logger.info("中央任务管理器初始化完成（依赖注入模式）")
```

## 2.6 向量化引擎

### 2.6.1 向量化流程

```
┌─────────────────────────────────────────────────────────────────┐
│                      EmbeddingEngine                             │
│                     （向量化引擎）                                │
└─────────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
    ┌─────▼─────┐      ┌─────▼─────┐      ┌─────▼─────┐
    │   Text    │      │   Image   │      │   Audio   │
    │ Embedding │      │ Embedding │      │ Embedding │
    └───────────┘      └───────────┘      └───────────┘
          │                   │                   │
          ▼                   ▼                   ▼
    ┌───────────┐      ┌───────────┐      ┌───────────┐
    │ chinese-  │      │ chinese-  │      │   CLAP    │
    │ clip-*    │      │ clip-*    │      │  htsat    │
    └───────────┘      └───────────┘      └───────────┘
          │                   │                   │
          └───────────────────┼───────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  Unified Vector │
                    │  (多维度支持)    │
                    │  - 512 dim      │
                    │  - 768 dim      │
                    │  - etc.         │
                    └─────────────────┘
```

### 2.6.2 EmbeddingEngine 类设计

```python
class EmbeddingEngine:
    """
    向量化引擎 - 负责所有类型数据的向量化
    
    支持多种向量维度（按模型默认值）：
    - chinese_clip_base: 512维
    - chinese_clip_large: 768维
    - audio_model: 512维
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.model_manager = None
        
    async def initialize(self):
        """初始化向量化引擎"""
        self.model_manager = ModelManager(self.config)
        await self.model_manager.load_all_models()
        
    async def embed_text(self, texts: Union[str, List[str]]) -> np.ndarray:
        """文本向量化"""
        if isinstance(texts, str):
            texts = [texts]
        return await self.model_manager.embed(
            self.config['active_models'][0],
            texts,
            input_type="text"
        )
        
    async def embed_image(self, images: Union[str, List[str]]) -> np.ndarray:
        """图像向量化"""
        if isinstance(images, str):
            images = [images]
        return await self.model_manager.embed(
            self.config['active_models'][0],
            images,
            input_type="image"
        )
        
    async def embed_video(self, videos: Union[str, List[str]]) -> np.ndarray:
        """视频向量化"""
        # 视频向量化：提取帧后进行图像向量化
        pass
        
    async def embed_audio(self, audios: Union[str, List[str]]) -> np.ndarray:
        """音频向量化"""
        if isinstance(audios, str):
            audios = [audios]
        return await self.model_manager.embed(
            'audio_model',
            audios,
            input_type="audio"
        )
```

## 2.7 向量存储系统

### 2.7.1 统一向量表设计

```python
{
    "vector": "vector",           # 向量数据（维度按模型默认值，不强制统一）
    "file_id": "string",           # 文件唯一标识
    "file_name": "string",         # 文件名
    "file_path": "string",         # 文件路径
    "file_type": "string",         # 文件类型
    "modality": "string",          # 模态类型 (image/video/audio)
    "model_id": "string",          # 使用的模型ID
    "embedding_dim": "int",        # 向量维度 (512/768等)
    "segment_id": "int",           # 片段ID
    "start_time": "float",         # 开始时间
    "end_time": "float",           # 结束时间
    "frame_index": "int",          # 帧索引
    "created_at": "timestamp"      # 创建时间
}
```

### 2.7.2 VectorStore 类设计

```python
class VectorStore:
    """
    向量存储 - 基于 LanceDB 的实现
    
    支持多种向量维度，不强制统一为512维
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.data_dir = config.get('data_dir', 'data/lancedb')
        self.collection_name = config.get('collection_name', 'unified_vectors')
        self.db = None
        self.table = None
        
    def initialize(self):
        """初始化向量存储"""
        import lancedb
        self.db = lancedb.connect(self.data_dir)
        
        # 检查表是否存在
        if self.collection_name in self.db.table_names():
            self.table = self.db.open_table(self.collection_name)
        else:
            # 创建表（不指定固定维度，支持多种维度）
            import pyarrow as pa
            schema = pa.schema([
                ("vector", pa.list_(pa.float32())),  # 动态维度
                ("file_id", pa.string()),
                ("file_name", pa.string()),
                ("file_path", pa.string()),
                ("file_type", pa.string()),
                ("modality", pa.string()),
                ("model_id", pa.string()),
                ("embedding_dim", pa.int32()),
                ("segment_id", pa.int32()),
                ("start_time", pa.float32()),
                ("end_time", pa.float32()),
                ("frame_index", pa.int32()),
                ("created_at", pa.timestamp('us'))
            ])
            self.table = self.db.create_table(self.collection_name, schema=schema)
            
    def insert(self, vectors: np.ndarray, metadata: List[Dict]) -> bool:
        """插入向量"""
        import pandas as pd
        
        data = []
        for i, meta in enumerate(metadata):
            row = {
                'vector': vectors[i].tolist(),
                'embedding_dim': len(vectors[i]),  # 记录实际维度
                **meta
            }
            data.append(row)
            
        df = pd.DataFrame(data)
        self.table.add(df)
        return True
```

## 2.8 检索引擎

### 2.8.1 检索流程

```
┌─────────────────────────────────────────────────────────────────┐
│                        SearchEngine                              │
│                       （检索引擎）                                │
└─────────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
    ┌─────▼─────┐      ┌─────▼─────┐      ┌─────▼─────┐
    │   Text    │      │   Image   │      │   Audio   │
    │   Search  │      │   Search  │      │   Search  │
    └───────────┘      └───────────┘      └───────────┘
          │                   │                   │
          ▼                   ▼                   ▼
    ┌───────────┐      ┌───────────┐      ┌───────────┐
    │  Query    │      │  Query    │      │  Query    │
    │ Embedding │      │ Embedding │      │ Embedding │
    └───────────┘      └───────────┘      └───────────┘
          │                   │                   │
          └───────────────────┼───────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  Vector Search  │
                    │  (LanceDB)      │
                    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  Result Merge   │
                    │  & Ranking      │
                    └─────────────────┘
```

### 2.8.2 SearchEngine 类设计

```python
class SearchEngine:
    """
    检索引擎 - 负责多模态检索
    """
    
    def __init__(
        self,
        config: Dict,
        embedding_engine: EmbeddingEngine,
        vector_store: VectorStore
    ):
        self.config = config
        self.embedding_engine = embedding_engine
        self.vector_store = vector_store
        
    async def search(
        self,
        query: Union[str, np.ndarray],
        query_type: str = "text",
        top_k: int = 20,
        filters: Optional[Dict] = None
    ) -> List[SearchResult]:
        """
        多模态检索
        
        Args:
            query: 查询（文本、图像路径或向量）
            query_type: 查询类型 (text/image/audio)
            top_k: 返回结果数量
            filters: 过滤条件
            
        Returns:
            搜索结果列表
        """
        # 1. 生成查询向量
        if isinstance(query, str):
            if query_type == "text":
                query_vector = await self.embedding_engine.embed_text(query)
            elif query_type == "image":
                query_vector = await self.embedding_engine.embed_image(query)
            elif query_type == "audio":
                query_vector = await self.embedding_engine.embed_audio(query)
            else:
                raise ValueError(f"不支持的查询类型: {query_type}")
        else:
            query_vector = query
            
        # 2. 向量检索
        results = self.vector_store.search(
            query_vector,
            top_k=top_k,
            filters=filters
        )
        
        # 3. 后处理
        return self._post_process_results(results)
```

**模态权重策略**：
- **默认文本查询**：以文搜图/文搜视频（纯视觉）为主，音频权重默认设置为 0
- **音频关键词触发**：当查询包含音频相关关键词时，按配置提升音频权重并适度降低视觉权重
- **配置来源**：`config.yml -> search.default_modality_weights / audio_keywords / audio_weight_multiplier / visual_weight_multiplier`

## 2.9 WebUI 系统

### 2.9.1 WebUI 架构

```
┌─────────────────────────────────────────────────────────────────┐
│                         WebUI (Gradio)                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   Search    │  │    Index    │  │    Task     │             │
│  │    Page     │  │    Page     │  │    Page     │             │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘             │
│         │                │                │                     │
│         └────────────────┼────────────────┘                     │
│                          │                                      │
│                          ▼                                      │
│              ┌─────────────────────┐                           │
│              │    API Client       │                           │
│              │  (HTTP Requests)    │                           │
│              └─────────────────────┘                           │
└─────────────────────────────────────────────────────────────────┘
```

### 2.9.2 任务管理器设计

#### 2.9.2.1 任务管理器架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      任务管理器界面架构                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  顶部工具栏                                            │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────┐ │    │
│  │  │ 任务搜索 │ │ 状态过滤 │ │ 优先级   │ │ 时间范围 │ │ 刷新  │ │    │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────┘ │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────┐ │    │
│  │  │ 类型过滤 │ │ 排序方式 │ │ 导出数据 │ │ 批量操作 │ │ 帮助  │ │    │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────┘ │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                          │                                      │
│                          ▼                                      │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  任务统计面板                                          │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────┐ │    │
│  │  │ 总任务数 │ │ 待处理   │ │ 运行中   │ │ 完成    │ │ 失败 │ │    │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────┘ │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────┐ │    │
│  │  │ 成功率   │ │ 平均耗时  │ │ 吞吐量   │ │ 队列深度│ │ 负载 │ │    │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────┘ │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                          │                                      │
│                          ▼                                      │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  任务列表（表格）                                       │    │
│  │  ┌─────────────────────────────────────────────────────┐   │    │
│  │  │ ☐ │ ID │ 类型 │ 状态 │ 进度 │ 优先级 │ 创建时间 │ 操作 │   │    │
│  │  ├─────────────────────────────────────────────────────┤   │    │
│  │  │ ☐ │ 001│ 图像 │ 待处理│  0%   │  5     │ 10:30:15│ [取消]│   │    │
│  │  ├─────────────────────────────────────────────────────┤   │    │
│  │  │ ☑ │ 002│ 视频 │ 运行中│ 45%   │  8     │ 10:31:20│ [暂停]│   │    │
│  │  ├─────────────────────────────────────────────────────┤   │    │
│  │  │ ☐ │ 003│ 音频 │ 完成  │ 100%  │  3     │ 10:32:45│ [重试]│   │    │
│  │  └─────────────────────────────────────────────────────┘   │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                          │                                      │
│                          ▼                                      │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  批量操作栏                                          │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────┐ │    │
│  │  │ 全选     │ │ 批量取消 │ │ 批量重试 │ │ 批量删除 │ │ 导出 │ │    │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────┘ │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────┐ │    │
│  │  │ 暂停选中 │ │ 恢复选中 │ │ 调整优先级│ │ 设置标签 │ │ 归档 │ │    │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────┘ │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                          │                                      │
│                          ▼                                      │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  任务详情面板                                        │    │
│  │  ┌─────────────────────────────────────────────────────┐   │    │
│  │  │ 基本信息 │ 进度详情 │ 日志输出 │ 依赖关系 │ 标签管理 │   │    │
│  │  └─────────────────────────────────────────────────────┘   │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 2.9.2.2 任务列表表格设计

| 列名 | 说明 | 数据类型 | 示例 | 可排序 | 可过滤 |
|--------|------|---------|------|--------|--------|
| **选择** | 多选框 | checkbox | `☑` | 否 | 否 |
| **任务ID** | 唯一标识符 | string | `550e8400-e29b-41d4-a716-446655440000` | 是 | 否 |
| **任务类型** | 任务类型 | string | `file_embed_image` | 是 | 是 |
| **文件路径** | 处理的文件路径 | string | `/data/testdata/image.jpg` | 否 | 否 |
| **状态** | 任务状态 | string | `pending` / `running` / `completed` / `failed` / `cancelled` | 是 | 是 |
| **进度** | 处理进度 | float | `0.0` - `1.0` | 是 | 否 |
| **优先级** | 任务优先级 | integer | `1-10` | 是 | 是 |
| **创建时间** | 任务创建时间 | timestamp | `1706524800.0` | 是 | 是 |
| **更新时间** | 最后更新时间 | timestamp | `1706524900.0` | 是 | 是 |
| **耗时** | 任务执行耗时(秒) | float | `12.5` | 是 | 是 |
| **错误信息** | 失败时的错误信息 | string | `Model not loaded` | 否 | 否 |
| **标签** | 任务标签 | array | `["urgent", "batch"]` | 否 | 是 |
| **依赖** | 依赖的任务ID | array | `["task_id_1", "task_id_2"]` | 否 | 否 |
| **操作** | 可执行的操作 | buttons | `[取消] [重试] [查看详情]` | 否 | 否 |

#### 2.9.2.3 任务状态可视化

```
状态颜色编码：
┌─────────────────────────────────────────────────────────┐
│  🟢 pending   - 待处理（灰色）               │
│  🔵 running   - 运行中（蓝色）               │
│  ⏸️ paused    - 已暂停（橙色）               │
│  ✅ completed - 已完成（绿色）               │
│  ❌ failed    - 失败（红色）                 │
│  ⚠️ cancelled - 已取消（黄色）             │
│  🔄 retrying  - 重试中（紫色）               │
└─────────────────────────────────────────────────────────┘

进度条可视化：
┌─────────────────────────────────────────────────────────┐
│  [████████████░░░░░░░░░░░░░░░░] 45%        │
│  [██████████████████████████████████] 100%       │
│  [░░░░░░░░░░░░░░░░░░░░░░░░░] 0%         │
│  [████████████████████░░░░░░░░░░] 67%        │
└─────────────────────────────────────────────────────────┘

优先级指示器：
┌─────────────────────────────────────────────────────────┐
│  🔴 高优先级 (1-3)    - 红色标记                │
│  🟡 中优先级 (4-7)    - 黄色标记                │
│  🟢 低优先级 (8-10)   - 绿色标记                │
└─────────────────────────────────────────────────────────┘
```

#### 2.9.2.4 任务操作功能

| 操作 | 说明 | 触发条件 | 权限要求 |
|------|------|---------|---------|
| **取消任务** | 停止正在运行或待处理的任务 | 状态为 `pending` 或 `running` | 用户 |
| **暂停任务** | 暂停正在运行的任务 | 状态为 `running` | 用户 |
| **恢复任务** | 恢复暂停的任务 | 状态为 `paused` | 用户 |
| **重试任务** | 重新提交失败的任务 | 状态为 `failed` | 用户 |
| **删除任务** | 从历史记录中删除任务 | 任意状态 | 管理员 |
| **查看详情** | 显示任务的详细信息 | 任意状态 | 用户 |
| **调整优先级** | 修改任务优先级 | 状态为 `pending` | 用户 |
| **添加标签** | 为任务添加标签 | 任意状态 | 用户 |
| **设置依赖** | 设置任务间的依赖关系 | 状态为 `pending` | 用户 |
| **批量取消** | 取消多个选中的任务 | 选中多个任务 | 用户 |
| **批量重试** | 重试多个失败的任务 | 选中多个失败任务 | 用户 |
| **批量暂停** | 暂停多个运行中的任务 | 选中多个运行中任务 | 用户 |
| **批量恢复** | 恢复多个暂停的任务 | 选中多个暂停任务 | 用户 |
| **导出数据** | 导出任务数据为CSV/JSON | 选中任务 | 用户 |
| **归档任务** | 将任务归档到历史记录 | 状态为 `completed` 或 `failed` | 用户 |

#### 2.9.2.5 高级过滤功能

```
过滤条件组合：
┌─────────────────────────────────────────────────────────┐
│  状态过滤: [✓] pending [✓] running [✓] completed       │
│           [✓] failed [✓] cancelled [✓] paused          │
│                                                         │
│  优先级过滤: [✓] 高(1-3) [✓] 中(4-7) [✓] 低(8-10)    │
│                                                         │
│  类型过滤: [✓] file_embed_image [✓] file_embed_video  │
│           [✓] file_embed_audio [✓] search_query       │
│                                                         │
│  时间范围: [开始时间] ──── [结束时间]                   │
│           预设: [最近1小时] [今天] [本周] [本月]        │
│                                                         │
│  标签过滤: [urgent] [batch] [manual] [+添加标签]      │
│                                                         │
│  文件路径: /data/testdata/*image*                       │
│                                                         │
│  [应用过滤] [重置过滤] [保存过滤方案]                    │
└─────────────────────────────────────────────────────────┘
```

#### 2.9.2.6 任务排序功能

```
排序选项：
┌─────────────────────────────────────────────────────────┐
│  主排序: [创建时间 ▼] [优先级 ▲] [状态 ▼] [进度 ▼]     │
│                                                         │
│  次排序: [更新时间 ▼] [耗时 ▲] [文件名 ▼] [类型 ▼]     │
│                                                         │
│  排序方式: [升序 ▲] [降序 ▼]                            │
│                                                         │
│  [应用排序] [重置排序] [保存排序方案]                    │
└─────────────────────────────────────────────────────────┘
```

#### 2.9.2.7 任务依赖管理

```
任务依赖关系图：
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  Task A (completed)                                     │
│       │                                                 │
│       ├─→ Task B (running)                             │
│       │       │                                         │
│       │       ├─→ Task D (pending)                     │
│       │       │                                         │
│       │       └─→ Task E (pending)                     │
│       │                                                 │
│       └─→ Task C (failed)                              │
│               │                                         │
│               └─→ Task F (blocked)                     │
│                                                         │
│  图例:                                                  │
│  ━━━━ 完成    ━━━━ 运行中    ━━━━ 待处理               │
│  ━━━━ 失败    ━━━━ 阻塞    ━━━━ 暂停                  │
│                                                         │
│  [查看依赖详情] [编辑依赖关系] [删除依赖]                │
└─────────────────────────────────────────────────────────┘
```

#### 2.9.2.8 任务标签系统

```
标签管理：
┌─────────────────────────────────────────────────────────┐
│  系统标签:                                              │
│  [urgent] [batch] [manual] [scheduled] [high-priority] │
│                                                         │
│  自定义标签:                                            │
│  [project-a] [test] [review] [+添加标签]                │
│                                                         │
│  标签颜色:                                              │
│  [urgent: 🔴] [batch: 🟡] [manual: 🟢] [+设置颜色]     │
│                                                         │
│  [保存标签配置] [导出标签] [导入标签]                    │
└─────────────────────────────────────────────────────────┘
```

#### 2.9.2.9 任务归档与清理

```
归档管理：
┌─────────────────────────────────────────────────────────┐
│  自动归档规则:                                          │
│  ☑ 完成超过30天的任务自动归档                           │
│  ☑ 失败超过7天的任务自动归档                            │
│  ☑ 已取消的任务立即归档                                 │
│                                                         │
│  手动归档:                                              │
│  [归档选中任务] [归档所有已完成] [归档所有失败]         │
│                                                         │
│  清理规则:                                              │
│  ☑ 归档超过90天的任务自动删除                           │
│  ☑ 删除前确认                                           │
│                                                         │
│  [清理归档任务] [查看归档历史] [恢复归档任务]            │
└─────────────────────────────────────────────────────────┘
```

### 2.9.3 Gradio 界面设计

```python
import gradio as gr
from typing import Dict, List, Any
import pandas as pd
from datetime import datetime, timedelta

class WebUI:
    """WebUI 实现"""
    
    def __init__(self, config: Dict, api_client: APIClient):
        self.config = config
        self.api_client = api_client
        self.selected_tasks = []
        self.filter_presets = {}
        self.sort_presets = {}
        
    def create_task_manager_page(self) -> gr.Blocks:
        """创建任务管理器页面"""
        with gr.Blocks(title="msearch - 任务管理器") as page:
            gr.Markdown("# 📋 任务管理器")
            
            # 顶部工具栏 - 第一行
            with gr.Row():
                task_search = gr.Textbox(
                    label="搜索任务",
                    placeholder="输入任务ID或文件路径...",
                    scale=3
                )
                status_filter = gr.CheckboxGroup(
                    label="状态过滤",
                    choices=["pending", "running", "paused", "completed", "failed", "cancelled"],
                    value=["pending", "running", "paused", "completed", "failed", "cancelled"],
                    scale=2
                )
                priority_filter = gr.CheckboxGroup(
                    label="优先级过滤",
                    choices=["高(1-3)", "中(4-7)", "低(8-10)"],
                    value=["高(1-3)", "中(4-7)", "低(8-10)"],
                    scale=2
                )
                refresh_btn = gr.Button("🔄 刷新", variant="primary", scale=1)
            
            # 顶部工具栏 - 第二行
            with gr.Row():
                type_filter = gr.CheckboxGroup(
                    label="类型过滤",
                    choices=["file_embed_image", "file_embed_video", "file_embed_audio", "search_query"],
                    value=["file_embed_image", "file_embed_video", "file_embed_audio", "search_query"],
                    scale=3
                )
                time_range = gr.Radio(
                    label="时间范围",
                    choices=["全部", "最近1小时", "今天", "本周", "本月"],
                    value="全部",
                    scale=2
                )
                sort_by = gr.Dropdown(
                    label="排序方式",
                    choices=["创建时间(降序)", "创建时间(升序)", "优先级(降序)", "优先级(升序)", 
                             "状态", "进度(降序)", "进度(升序)", "耗时(降序)", "耗时(升序)"],
                    value="创建时间(降序)",
                    scale=2
                )
                export_btn = gr.Button("📥 导出", variant="secondary", scale=1)
            
            # 任务统计面板
            with gr.Row():
                with gr.Column(scale=1):
                    total_tasks = gr.Number(label="总任务数", value=0, interactive=False)
                with gr.Column(scale=1):
                    pending_tasks = gr.Number(label="待处理", value=0, interactive=False)
                with gr.Column(scale=1):
                    running_tasks = gr.Number(label="运行中", value=0, interactive=False)
                with gr.Column(scale=1):
                    completed_tasks = gr.Number(label="已完成", value=0, interactive=False)
                with gr.Column(scale=1):
                    failed_tasks = gr.Number(label="失败", value=0, interactive=False)
                with gr.Column(scale=1):
                    paused_tasks = gr.Number(label="已暂停", value=0, interactive=False)
            
            # 任务统计面板 - 第二行
            with gr.Row():
                with gr.Column(scale=1):
                    success_rate = gr.Textbox(label="成功率", value="0%", interactive=False)
                with gr.Column(scale=1):
                    avg_duration = gr.Textbox(label="平均耗时", value="0s", interactive=False)
                with gr.Column(scale=1):
                    throughput = gr.Textbox(label="吞吐量", value="0/min", interactive=False)
                with gr.Column(scale=1):
                    queue_depth = gr.Number(label="队列深度", value=0, interactive=False)
                with gr.Column(scale=1):
                    system_load = gr.Textbox(label="系统负载", value="0%", interactive=False)
            
            # 任务列表
            task_list = gr.Dataframe(
                label="任务列表",
                headers=["选择", "任务ID", "类型", "文件路径", "状态", "进度", "优先级", "创建时间", "耗时", "标签", "操作"],
                datatype=["checkbox", "str", "str", "str", "str", "number", "number", "str", "str", "str", "buttons"],
                interactive=True,
                wrap=True,
                max_rows=20
            )
            
            # 批量操作栏 - 第一行
            with gr.Row():
                select_all_btn = gr.Button("☑️ 全选", variant="secondary")
                deselect_all_btn = gr.Button("⬜ 取消全选", variant="secondary")
                cancel_selected_btn = gr.Button("❌ 批量取消", variant="stop")
                pause_selected_btn = gr.Button("⏸️ 批量暂停", variant="secondary")
                resume_selected_btn = gr.Button("▶️ 批量恢复", variant="secondary")
            
            # 批量操作栏 - 第二行
            with gr.Row():
                retry_selected_btn = gr.Button("🔄 批量重试", variant="secondary")
                delete_selected_btn = gr.Button("🗑️ 批量删除", variant="stop")
                archive_selected_btn = gr.Button("📦 批量归档", variant="secondary")
                set_priority_btn = gr.Button("⚡ 调整优先级", variant="secondary")
                add_tags_btn = gr.Button("🏷️ 添加标签", variant="secondary")
            
            # 任务详情面板
            with gr.Accordion("任务详情", open=False):
                with gr.Tabs():
                    with gr.Tab("基本信息"):
                        task_info = gr.JSON(label="任务信息", visible=False)
                    with gr.Tab("进度详情"):
                        progress_details = gr.JSON(label="进度详情", visible=False)
                    with gr.Tab("日志输出"):
                        task_logs = gr.Textbox(label="任务日志", lines=10, interactive=False)
                    with gr.Tab("依赖关系"):
                        dependency_graph = gr.JSON(label="依赖关系", visible=False)
                    with gr.Tab("标签管理"):
                        tag_manager = gr.JSON(label="标签管理", visible=False)
            
            # 事件绑定
            refresh_btn.click(
                fn=self.refresh_task_list,
                inputs=[task_search, status_filter, priority_filter, type_filter, time_range, sort_by],
                outputs=[task_list, total_tasks, pending_tasks, running_tasks, completed_tasks, 
                         failed_tasks, paused_tasks, success_rate, avg_duration, throughput, 
                         queue_depth, system_load]
            )
            
            select_all_btn.click(
                fn=self.select_all_tasks,
                outputs=task_list
            )
            
            deselect_all_btn.click(
                fn=self.deselect_all_tasks,
                outputs=task_list
            )
            
            cancel_selected_btn.click(
                fn=self.cancel_selected_tasks,
                inputs=task_list,
                outputs=[task_list, gr.Textbox(label="操作结果")]
            )
            
            pause_selected_btn.click(
                fn=self.pause_selected_tasks,
                inputs=task_list,
                outputs=[task_list, gr.Textbox(label="操作结果")]
            )
            
            resume_selected_btn.click(
                fn=self.resume_selected_tasks,
                inputs=task_list,
                outputs=[task_list, gr.Textbox(label="操作结果")]
            )
            
            retry_selected_btn.click(
                fn=self.retry_selected_tasks,
                inputs=task_list,
                outputs=[task_list, gr.Textbox(label="操作结果")]
            )
            
            delete_selected_btn.click(
                fn=self.delete_selected_tasks,
                inputs=task_list,
                outputs=[task_list, gr.Textbox(label="操作结果")]
            )
            
            archive_selected_btn.click(
                fn=self.archive_selected_tasks,
                inputs=task_list,
                outputs=[task_list, gr.Textbox(label="操作结果")]
            )
            
            set_priority_btn.click(
                fn=self.set_task_priority,
                inputs=[task_list, gr.Number(label="新优先级", minimum=1, maximum=10)],
                outputs=[task_list, gr.Textbox(label="操作结果")]
            )
            
            add_tags_btn.click(
                fn=self.add_task_tags,
                inputs=[task_list, gr.Textbox(label="标签(逗号分隔)")],
                outputs=[task_list, gr.Textbox(label="操作结果")]
            )
            
            export_btn.click(
                fn=self.export_tasks,
                inputs=[task_list, gr.Dropdown(label="导出格式", choices=["CSV", "JSON"], value="CSV")],
                outputs=gr.File(label="下载文件")
            )
            
            # 任务列表点击事件
            task_list.select(
                fn=self.show_task_details,
                outputs=[task_info, progress_details, task_logs, dependency_graph, tag_manager]
            )
            
            # 自动刷新
            page.load(
                fn=self.refresh_task_list,
                inputs=[task_search, status_filter, priority_filter, type_filter, time_range, sort_by],
                outputs=[task_list, total_tasks, pending_tasks, running_tasks, completed_tasks, 
                         failed_tasks, paused_tasks, success_rate, avg_duration, throughput, 
                         queue_depth, system_load]
            )
        
        return page
    
    def refresh_task_list(
        self, 
        search_query: str, 
        status_filter: List[str], 
        priority_filter: List[str],
        type_filter: List[str],
        time_range: str,
        sort_by: str
    ) -> tuple:
        """刷新任务列表"""
        # 获取所有任务
        all_tasks = self.api_client.get_all_tasks()
        
        # 应用过滤器
        filtered_tasks = self._filter_tasks(
            all_tasks, search_query, status_filter, 
            priority_filter, type_filter, time_range
        )
        
        # 应用排序
        sorted_tasks = self._sort_tasks(filtered_tasks, sort_by)
        
        # 转换为DataFrame格式
        df_data = []
        for task in sorted_tasks:
            df_data.append([
                False,  # 选择框
                task['id'][:8] + '...',  # 截断ID
                task['task_type'],
                task.get('file_path', '')[-40:],  # 截断路径
                task['status'],
                f"{task.get('progress', 0) * 100:.1f}%",
                task['priority'],
                self._format_timestamp(task['created_at']),
                f"{task.get('duration', 0):.1f}s",
                ','.join(task.get('tags', [])),
                "查看详情"  # 操作按钮
            ])
        
        # 计算统计
        stats = self._calculate_stats(sorted_tasks)
        
        return (
            df_data,
            stats['total'],
            stats['pending'],
            stats['running'],
            stats['completed'],
            stats['failed'],
            stats['paused'],
            stats['success_rate'],
            stats['avg_duration'],
            stats['throughput'],
            stats['queue_depth'],
            stats['system_load']
        )
    
    def _filter_tasks(
        self, 
        tasks: List[Dict], 
        search_query: str, 
        status_filter: List[str],
        priority_filter: List[str],
        type_filter: List[str],
        time_range: str
    ) -> List[Dict]:
        """过滤任务"""
        filtered = tasks
        
        # 搜索过滤
        if search_query:
            search_lower = search_query.lower()
            filtered = [
                t for t in filtered 
                if search_lower in t['id'].lower() 
                or search_lower in t.get('file_path', '').lower()
                or any(search_lower in tag.lower() for tag in t.get('tags', []))
            ]
        
        # 状态过滤
        if status_filter:
            filtered = [t for t in filtered if t['status'] in status_filter]
        
        # 优先级过滤
        if priority_filter:
            priority_filtered = []
            for task in filtered:
                priority = task['priority']
                if "高(1-3)" in priority_filter and 1 <= priority <= 3:
                    priority_filtered.append(task)
                elif "中(4-7)" in priority_filter and 4 <= priority <= 7:
                    priority_filtered.append(task)
                elif "低(8-10)" in priority_filter and 8 <= priority <= 10:
                    priority_filtered.append(task)
            filtered = priority_filtered
        
        # 类型过滤
        if type_filter:
            filtered = [t for t in filtered if t['task_type'] in type_filter]
        
        # 时间范围过滤
        if time_range != "全部":
            now = datetime.now()
            if time_range == "最近1小时":
                cutoff = now - timedelta(hours=1)
            elif time_range == "今天":
                cutoff = now.replace(hour=0, minute=0, second=0, microsecond=0)
            elif time_range == "本周":
                cutoff = now - timedelta(days=now.weekday())
                cutoff = cutoff.replace(hour=0, minute=0, second=0, microsecond=0)
            elif time_range == "本月":
                cutoff = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            else:
                cutoff = None
            
            if cutoff:
                filtered = [
                    t for t in filtered 
                    if datetime.fromtimestamp(t['created_at']) >= cutoff
                ]
        
        return filtered
    
    def _sort_tasks(self, tasks: List[Dict], sort_by: str) -> List[Dict]:
        """排序任务"""
        if not tasks:
            return tasks
        
        reverse = True
        
        if sort_by == "创建时间(降序)":
            key = 'created_at'
            reverse = True
        elif sort_by == "创建时间(升序)":
            key = 'created_at'
            reverse = False
        elif sort_by == "优先级(降序)":
            key = 'priority'
            reverse = False  # 优先级越小越高
        elif sort_by == "优先级(升序)":
            key = 'priority'
            reverse = True
        elif sort_by == "状态":
            key = 'status'
            reverse = True
        elif sort_by == "进度(降序)":
            key = 'progress'
            reverse = True
        elif sort_by == "进度(升序)":
            key = 'progress'
            reverse = False
        elif sort_by == "耗时(降序)":
            key = 'duration'
            reverse = True
        elif sort_by == "耗时(升序)":
            key = 'duration'
            reverse = False
        else:
            key = 'created_at'
            reverse = True
        
        return sorted(tasks, key=lambda x: x.get(key, 0), reverse=reverse)
    
    def _calculate_stats(self, tasks: List[Dict]) -> Dict[str, Any]:
        """计算任务统计"""
        stats = {
            'total': len(tasks),
            'pending': 0,
            'running': 0,
            'completed': 0,
            'failed': 0,
            'paused': 0,
            'success_rate': '0%',
            'avg_duration': '0s',
            'throughput': '0/min',
            'queue_depth': 0,
            'system_load': '0%'
        }
        
        completed_count = 0
        failed_count = 0
        total_duration = 0
        completed_duration_count = 0
        
        for task in tasks:
            status = task['status']
            if status in stats:
                stats[status] += 1
            
            if status == 'completed':
                completed_count += 1
                duration = task.get('duration', 0)
                if duration > 0:
                    total_duration += duration
                    completed_duration_count += 1
            elif status == 'failed':
                failed_count += 1
        
        # 计算成功率
        total_finished = completed_count + failed_count
        if total_finished > 0:
            success_rate = (completed_count / total_finished) * 100
            stats['success_rate'] = f"{success_rate:.1f}%"
        
        # 计算平均耗时
        if completed_duration_count > 0:
            avg_duration = total_duration / completed_duration_count
            stats['avg_duration'] = f"{avg_duration:.1f}s"
        
        # 计算吞吐量（最近1小时完成的任务数）
        now = datetime.now()
        one_hour_ago = now - timedelta(hours=1)
        recent_completed = [
            t for t in tasks 
            if t['status'] == 'completed' 
            and datetime.fromtimestamp(t['updated_at']) >= one_hour_ago
        ]
        stats['throughput'] = f"{len(recent_completed)}/min"
        
        # 队列深度（待处理+运行中）
        stats['queue_depth'] = stats['pending'] + stats['running']
        
        # 系统负载（运行中任务数 / 总任务数）
        if stats['total'] > 0:
            load = (stats['running'] / stats['total']) * 100
            stats['system_load'] = f"{load:.1f}%"
        
        return stats
    
    def _format_timestamp(self, timestamp: float) -> str:
        """格式化时间戳"""
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    
    def select_all_tasks(self) -> List[List]:
        """全选任务"""
        all_tasks = self.api_client.get_all_tasks()
        return [[True] + [t['id'][:8] + '...' for t in all_tasks]]
    
    def deselect_all_tasks(self) -> List[List]:
        """取消全选"""
        all_tasks = self.api_client.get_all_tasks()
        return [[False] + [t['id'][:8] + '...' for t in all_tasks]]
    
    def cancel_selected_tasks(self, task_list: List[List]) -> tuple:
        """取消选中的任务"""
        selected_count = 0
        for row in task_list:
            if row[0]:  # 第一列是选择框
                task_id = row[1]
                self.api_client.cancel_task(task_id)
                selected_count += 1
        
        return task_list, f"已取消 {selected_count} 个任务"
    
    def pause_selected_tasks(self, task_list: List[List]) -> tuple:
        """暂停选中的任务"""
        selected_count = 0
        for row in task_list:
            if row[0]:
                task_id = row[1]
                self.api_client.pause_task(task_id)
                selected_count += 1
        
        return task_list, f"已暂停 {selected_count} 个任务"
    
    def resume_selected_tasks(self, task_list: List[List]) -> tuple:
        """恢复选中的任务"""
        selected_count = 0
        for row in task_list:
            if row[0]:
                task_id = row[1]
                self.api_client.resume_task(task_id)
                selected_count += 1
        
        return task_list, f"已恢复 {selected_count} 个任务"
    
    def retry_selected_tasks(self, task_list: List[List]) -> tuple:
        """重试选中的任务"""
        selected_count = 0
        for row in task_list:
            if row[0]:
                task_id = row[1]
                self.api_client.retry_task(task_id)
                selected_count += 1
        
        return task_list, f"已重试 {selected_count} 个任务"
    
    def delete_selected_tasks(self, task_list: List[List]) -> tuple:
        """删除选中的任务"""
        selected_count = 0
        for row in task_list:
            if row[0]:
                task_id = row[1]
                self.api_client.delete_task(task_id)
                selected_count += 1
        
        return task_list, f"已删除 {selected_count} 个任务"
    
    def archive_selected_tasks(self, task_list: List[List]) -> tuple:
        """归档选中的任务"""
        selected_count = 0
        for row in task_list:
            if row[0]:
                task_id = row[1]
                self.api_client.archive_task(task_id)
                selected_count += 1
        
        return task_list, f"已归档 {selected_count} 个任务"
    
    def set_task_priority(self, task_list: List[List], new_priority: int) -> tuple:
        """设置任务优先级"""
        selected_count = 0
        for row in task_list:
            if row[0]:
                task_id = row[1]
                self.api_client.set_task_priority(task_id, new_priority)
                selected_count += 1
        
        return task_list, f"已为 {selected_count} 个任务设置优先级为 {new_priority}"
    
    def add_task_tags(self, task_list: List[List], tags: str) -> tuple:
        """添加任务标签"""
        tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
        selected_count = 0
        for row in task_list:
            if row[0]:
                task_id = row[1]
                self.api_client.add_task_tags(task_id, tag_list)
                selected_count += 1
        
        return task_list, f"已为 {selected_count} 个任务添加标签: {', '.join(tag_list)}"
    
    def export_tasks(self, task_list: List[List], format: str) -> str:
        """导出任务数据"""
        import json
        import csv
        import tempfile
        import os
        
        # 获取选中的任务
        selected_tasks = []
        for row in task_list:
            if row[0]:
                task_id = row[1]
                task = self.api_client.get_task(task_id)
                selected_tasks.append(task)
        
        if not selected_tasks:
            return None
        
        # 创建临时文件
        temp_dir = tempfile.gettempdir()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format == "CSV":
            filename = f"tasks_export_{timestamp}.csv"
            filepath = os.path.join(temp_dir, filename)
            
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=selected_tasks[0].keys())
                writer.writeheader()
                writer.writerows(selected_tasks)
        else:  # JSON
            filename = f"tasks_export_{timestamp}.json"
            filepath = os.path.join(temp_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(selected_tasks, f, indent=2, ensure_ascii=False)
        
        return filepath
    
    def show_task_details(self, selection: gr.SelectData) -> tuple:
        """显示任务详情"""
        task_list = selection.parent.value
        row = task_list[selection.index[0]]
        task_id = row[1]
        
        task = self.api_client.get_task(task_id)
        
        task_info = {
            "任务ID": task['id'],
            "任务类型": task['task_type'],
            "文件路径": task.get('file_path', ''),
            "状态": task['status'],
            "优先级": task['priority'],
            "创建时间": self._format_timestamp(task['created_at']),
            "更新时间": self._format_timestamp(task['updated_at']),
            "耗时": f"{task.get('duration', 0):.1f}s",
            "标签": task.get('tags', []),
            "错误信息": task.get('error', '')
        }
        
        progress_details = {
            "进度": f"{task.get('progress', 0) * 100:.1f}%",
            "当前步骤": task.get('current_step', ''),
            "总步骤": task.get('total_steps', 0),
            "已完成步骤": task.get('completed_steps', 0)
        }
        
        logs = self.api_client.get_task_logs(task_id)
        
        dependencies = self.api_client.get_task_dependencies(task_id)
        
        tags = task.get('tags', [])
        
        return task_info, progress_details, logs, dependencies, tags
```

### 2.9.4 实时进度监控

```python
class RealTimeProgressMonitor:
    """实时进度监控器"""
    
    def __init__(self, task_manager):
        self.task_manager = task_manager
        self.progress_cache = {}
    
    def get_progress_updates(self) -> Dict[str, Any]:
        """获取进度更新"""
        # 获取所有运行中的任务
        running_tasks = self.task_manager.get_tasks_by_status('running')
        
        updates = []
        for task in running_tasks:
            task_id = task['id']
            current_progress = task.get('progress', 0)
            
            # 检查进度是否变化
            if task_id not in self.progress_cache or self.progress_cache[task_id] != current_progress:
                updates.append({
                    'task_id': task_id,
                    'progress': current_progress,
                    'status': task['status'],
                    'file_path': task.get('file_path', '')
                })
                self.progress_cache[task_id] = current_progress
        
        return {
            'updates': updates,
            'running_count': len(running_tasks)
        }
    
    def get_task_progress_bar(self, task: Dict) -> str:
        """获取任务进度条HTML"""
        progress = task.get('progress', 0) * 100
        status = task.get('status', 'unknown')
        
        # 根据状态选择颜色
        if status == 'running':
            color = '#3b82f6'  # 蓝色
        elif status == 'completed':
            color = '#28a745'  # 绿色
        elif status == 'failed':
            color = '#dc3545'  # 红色
        else:
            color = '#6c757d'  # 灰色
        
        # 生成进度条HTML
        bar_width = progress
        bar_html = f"""
        <div style="width: 100%; background-color: #f0f0f0; border-radius: 4px; overflow: hidden;">
            <div style="width: {bar_width}%; background-color: {color}; height: 20px; 
                        border-radius: 4px; display: flex; align-items: center; 
                        justify-content: center; color: white; font-size: 12px;">
                {progress:.1f}%
            </div>
        </div>
        """
        return bar_html
```

### 2.9.5 任务组管理

```python
class TaskGroupManagerUI:
    """任务组管理器UI"""
    
    def create_task_group_page(self) -> gr.Blocks:
        """创建任务组管理页面"""
        with gr.Blocks(title="msearch - 任务组管理") as page:
            gr.Markdown("# 📁 任务组管理")
            
            # 任务组列表
            with gr.Row():
                group_list = gr.Dataframe(
                    label="任务组列表",
                    headers=["组ID", "文件ID", "状态", "任务数", "完成数", "进度"],
                    datatype=["str", "str", "str", "number", "number", "number"],
                    interactive=False
                )
                refresh_groups_btn = gr.Button("🔄 刷新", variant="primary")
            
            # 任务组详情
            with gr.Accordion("任务组详情", open=False):
                group_tasks = gr.Dataframe(
                    label="组内任务",
                    headers=["任务ID", "类型", "状态", "优先级"],
                    datatype=["str", "str", "str", "number"],
                    interactive=False
                )
            
            # 操作按钮
            with gr.Row():
                cancel_group_btn = gr.Button("❌ 取消任务组", variant="stop")
                retry_group_btn = gr.Button("🔄 重试任务组", variant="secondary")
            
            # 事件绑定
            refresh_groups_btn.click(
                fn=self.refresh_task_groups,
                outputs=[group_list]
            )
            
            group_list.select(
                fn=self.show_group_details,
                outputs=[group_tasks]
            )
            
            cancel_group_btn.click(
                fn=self.cancel_task_group,
                inputs=group_list,
                outputs=group_list
            )
        
        return page
    
    def refresh_task_groups(self) -> List[List]:
        """刷新任务组列表"""
        groups = self.api_client.get_all_task_groups()
        
        group_data = []
        for group in groups:
            group_data.append([
                group['id'],
                group['file_id'],
                group['status'],
                group['total_tasks'],
                group['completed_tasks'],
                f"{group['completed_tasks'] / group['total_tasks'] * 100:.1f}%"
            ])
        
        return [group_data]
```

### 2.9.6 搜索页面设计

```python
    def create_search_page(self) -> gr.Blocks:
        """创建搜索页面"""
        with gr.Blocks(title="msearch - 多模态搜索") as interface:
            gr.Markdown("# 🔍 多模态智能搜索")
            
            with gr.Tab("📝 文本搜索"):
                with gr.Row():
                    with gr.Column(scale=3):
                        text_input = gr.Textbox(
                            label="输入搜索文本",
                            placeholder="描述你想找的内容...",
                            lines=3
                        )
                        with gr.Row():
                            top_k = gr.Slider(
                                label="返回结果数",
                                minimum=1,
                                maximum=50,
                                value=10,
                                step=1
                            )
                            threshold = gr.Slider(
                                label="相似度阈值",
                                minimum=0.0,
                                maximum=1.0,
                                value=0.0,
                                step=0.05
                            )
                        search_btn = gr.Button("🔍 搜索", variant="primary", size="lg")
                    
                    with gr.Column(scale=7):
                        results_gallery = gr.Gallery(
                            label="搜索结果",
                            columns=3,
                            height="auto",
                            object_fit="contain"
                        )
                
                search_btn.click(
                    fn=self.search_by_text,
                    inputs=[text_input, top_k, threshold],
                    outputs=results_gallery
                )
            
            with gr.Tab("🖼️ 图像搜索"):
                with gr.Row():
                    with gr.Column(scale=3):
                        image_input = gr.Image(
                            label="上传图像",
                            type="filepath"
                        )
                        with gr.Row():
                            top_k = gr.Slider(
                                label="返回结果数",
                                minimum=1,
                                maximum=50,
                                value=10,
                                step=1
                            )
                            threshold = gr.Slider(
                                label="相似度阈值",
                                minimum=0.0,
                                maximum=1.0,
                                value=0.0,
                                step=0.05
                            )
                        search_btn = gr.Button("🔍 搜索相似图像", variant="primary", size="lg")
                    
                    with gr.Column(scale=7):
                        results_gallery = gr.Gallery(
                            label="搜索结果",
                            columns=3,
                            height="auto",
                            object_fit="contain"
                        )
                
                search_btn.click(
                    fn=self.search_by_image,
                    inputs=[image_input, top_k, threshold],
                    outputs=results_gallery
                )
            
            with gr.Tab("🎵 音频搜索"):
                with gr.Row():
                    with gr.Column(scale=3):
                        audio_input = gr.Audio(
                            label="上传音频",
                            type="filepath"
                        )
                        with gr.Row():
                            top_k = gr.Slider(
                                label="返回结果数",
                                minimum=1,
                                maximum=50,
                                value=10,
                                step=1
                            )
                            threshold = gr.Slider(
                                label="相似度阈值",
                                minimum=0.0,
                                maximum=1.0,
                                value=0.0,
                                step=0.05
                            )
                        search_btn = gr.Button("🔍 搜索相似音频", variant="primary", size="lg")
                    
                    with gr.Column(scale=7):
                        results_gallery = gr.Gallery(
                            label="搜索结果",
                            columns=3,
                            height="auto",
                            object_fit="contain"
                        )
                
                search_btn.click(
                    fn=self.search_by_audio,
                    inputs=[audio_input, top_k, threshold],
                    outputs=results_gallery
                )
        
        return interface
```

### 2.9.7 系统状态页面

```python
    def create_system_status_page(self) -> gr.Blocks:
        """创建系统状态页面"""
        with gr.Blocks(title="msearch - 系统状态") as page:
            gr.Markdown("# 📊 系统状态")
            
            # 资源使用
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### 💻 CPU使用")
                    cpu_usage = gr.Textbox(label="CPU使用率", interactive=False)
                with gr.Column():
                    gr.Markdown("### 🧠 内存使用")
                    memory_usage = gr.Textbox(label="内存使用率", interactive=False)
                with gr.Column():
                    gr.Markdown("### 🎮 GPU使用")
                    gpu_usage = gr.Textbox(label="GPU使用率", interactive=False)
            
            # 向量存储状态
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### 📦 向量数据库")
                    vector_count = gr.Number(label="向量数量", interactive=False)
                    vector_size = gr.Textbox(label="向量大小", interactive=False)
                with gr.Column():
                    gr.Markdown("### 🗄️ 元数据库")
                    file_count = gr.Number(label="文件数量", interactive=False)
                    db_size = gr.Textbox(label="数据库大小", interactive=False)
            
            # 文件监控状态
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### 👁️ 文件监控")
                    monitored_dirs = gr.Textbox(label="监控目录", interactive=False)
                    event_count = gr.Number(label="事件计数", interactive=False)
                with gr.Column():
                    gr.Markdown("### 🔄 任务队列")
                    queue_size = gr.Number(label="队列大小", interactive=False)
                    throughput = gr.Textbox(label="吞吐量", interactive=False)
            
            # 刷新按钮
            refresh_btn = gr.Button("🔄 刷新状态", variant="primary")
            
            # 事件绑定
            refresh_btn.click(
                fn=self.get_system_status,
                outputs=[cpu_usage, memory_usage, gpu_usage, vector_count, vector_size, 
                         file_count, db_size, monitored_dirs, event_count, queue_size, throughput]
            )
            
            # 自动刷新（每5秒）
            page.load(
                fn=self.get_system_status,
                outputs=[cpu_usage, memory_usage, gpu_usage, vector_count, vector_size, 
                         file_count, db_size, monitored_dirs, event_count, queue_size, throughput]
            )
        
        return page
```

### 2.9.8 配置管理页面

```python
    def create_config_page(self) -> gr.Blocks:
        """创建配置管理页面"""
        with gr.Blocks(title="msearch - 配置管理") as page:
            gr.Markdown("# ⚙️ 配置管理")
            
            # 文件监控配置
            with gr.Accordion("📁 文件监控配置", open=True):
                with gr.Row():
                    watch_dirs = gr.Textbox(
                        label="监控目录",
                        placeholder="/path/to/dir1,/path/to/dir2",
                        value=",".join(self.config.get('file_monitor', {}).get('watch_directories', []))
                    )
                    monitor_enabled = gr.Checkbox(
                        label="启用文件监控",
                        value=self.config.get('file_monitor', {}).get('enabled', True)
                    )
                    recursive = gr.Checkbox(
                        label="递归监控子目录",
                        value=self.config.get('file_monitor', {}).get('recursive', True)
                    )
            
            # 去重配置
            with gr.Accordion("🔁 去重配置"):
                with gr.Row():
                    dedup_enabled = gr.Checkbox(
                        label="启用内容哈希去重",
                        value=self.config.get('deduplication', {}).get('enabled', True)
                    )
                    hash_algorithm = gr.Dropdown(
                        label="哈希算法",
                        choices=["md5", "sha256"],
                        value=self.config.get('deduplication', {}).get('hash_algorithm', 'md5')
                    )
                    video_sample_size = gr.Number(
                        label="视频采样大小(MB)",
                        value=self.config.get('deduplication', {}).get('video_sample_size', 1)
                    )
                with gr.Row():
                    cache_size = gr.Number(
                        label="哈希缓存大小",
                        value=self.config.get('deduplication', {}).get('cache_size', 1000)
                    )
                    cache_ttl = gr.Number(
                        label="缓存过期时间(秒)",
                        value=self.config.get('deduplication', {}).get('cache_ttl', 3600)
                    )
            
            # 模型配置
            with gr.Accordion("🤖 模型配置"):
                with gr.Row():
                    image_model = gr.Dropdown(
                        label="图像/视频模型",
                        choices=["chinese_clip_base", "chinese_clip_large", "colqwen3_turbo", "tomoro_colqwen3"],
                        value=self.config.get('models', {}).get('image_model', 'chinese_clip_base')
                    )
                    audio_model = gr.Dropdown(
                        label="音频模型",
                        choices=["audio_model"],
                        value=self.config.get('models', {}).get('audio_model', 'audio_model')
                    )
                with gr.Row():
                    device = gr.Dropdown(
                        label="设备",
                        choices=["cpu", "cuda"],
                        value=self.config.get('models', {}).get('device', 'cpu')
                    )
                    batch_size = gr.Number(
                        label="批处理大小",
                        value=self.config.get('models', {}).get('batch_size', 32)
                    )
            
            # 保存按钮
            with gr.Row():
                save_btn = gr.Button("💾 保存配置", variant="primary", size="lg")
                reset_btn = gr.Button("🔄 重置为默认", variant="secondary")
            
            # 事件绑定
            save_btn.click(
                fn=self.save_config,
                inputs=[watch_dirs, monitor_enabled, recursive, dedup_enabled, hash_algorithm, 
                         video_sample_size, cache_size, cache_ttl, image_model, 
                         audio_model, device, batch_size],
                outputs=gr.Textbox(label="保存结果", interactive=False)
            )
            
            reset_btn.click(
                fn=self.reset_config,
                outputs=gr.Textbox(label="重置结果", interactive=False)
            )
        
        return page
```

### 2.9.9 主界面集成

```python
    def create_interface(self) -> gr.Blocks:
        """创建主界面"""
        with gr.Blocks(title="msearch - 多模态搜索", theme=gr.themes.Soft()) as interface:
            gr.Markdown("""
            # 🔍 msearch - 多模态智能搜索系统
            
            基于深度学习的多模态内容检索系统，支持文本、图像、音频搜索。
            """)
            
            # 顶部导航
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### 📌 快速导航")
                with gr.Column(scale=3):
                    nav_links = gr.Radio(
                        choices=["🔍 搜索", "📋 任务管理", "📊 系统状态", "⚙️ 配置管理"],
                        value="🔍 搜索",
                        interactive=False
                    )
            
            # 页面容器
            with gr.Row():
                # 搜索页面
                with gr.Column(visible=True) as search_page:
                    search_interface = self.create_search_page()
                
                # 任务管理页面
                with gr.Column(visible=False) as task_page:
                    task_interface = self.create_task_manager_page()
                
                # 系统状态页面
                with gr.Column(visible=False) as status_page:
                    status_interface = self.create_system_status_page()
                
                # 配置管理页面
                with gr.Column(visible=False) as config_page:
                    config_interface = self.create_config_page()
            
            # 导航事件
            nav_links.change(
                fn=self.switch_page,
                inputs=nav_links,
                outputs=[search_page, task_page, status_page, config_page]
            )
        
        return interface
    
    def switch_page(self, page_name: str) -> tuple:
        """切换页面"""
        search_visible = page_name == "🔍 搜索"
        task_visible = page_name == "📋 任务管理"
        status_visible = page_name == "📊 系统状态"
        config_visible = page_name == "⚙️ 配置管理"
        
        return search_visible, task_visible, status_visible, config_visible
```

## 2.10 桌面 UI 系统

### 2.10.1 PySide6 架构

```
┌─────────────────────────────────────────────────────────────────┐
│                      Desktop UI (PySide6)                        │
├─────────────────────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                      MainWindow                            │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │  │
│  │  │ SearchPanel │  │ ResultPanel │  │  TaskPanel  │       │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘       │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                  │
│                              ▼                                  │
│                  ┌─────────────────────┐                       │
│                  │    API Client       │                       │
│                  │  (HTTP/Local)       │                       │
│                  └─────────────────────┘                       │
└─────────────────────────────────────────────────────────────────┘
```

### 2.10.2 PySide6 实现

```python
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QListWidget, QLabel
)
from PySide6.QtCore import Qt, QThread, Signal

class SearchWorker(QThread):
    """搜索工作线程"""
    finished = Signal(list)
    
    def __init__(self, api_client, query):
        super().__init__()
        self.api_client = api_client
        self.query = query
        
    def run(self):
        results = self.api_client.search(self.query)
        self.finished.emit(results)

class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self, config: Dict, api_client: APIClient):
        super().__init__()
        self.config = config
        self.api_client = api_client
        self.setup_ui()
        
    def setup_ui(self):
        """设置UI"""
        self.setWindowTitle("msearch - 多模态搜索")
        self.setMinimumSize(1200, 800)
        
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout(central_widget)
        
        # 左侧面板 - 搜索和任务管理
        left_panel = self._create_left_panel()
        main_layout.addWidget(left_panel, 1)
        
        # 右侧面板 - 结果
        right_panel = self._create_result_panel()
        main_layout.addWidget(right_panel, 3)
        
    def _create_left_panel(self) -> QWidget:
        """创建左侧面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 搜索区域
        layout.addWidget(QLabel("🔍 搜索"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入搜索内容...")
        layout.addWidget(self.search_input)
        
        # 搜索按钮
        search_btn = QPushButton("搜索")
        search_btn.clicked.connect(self._on_search)
        layout.addWidget(search_btn)
        
        # 分隔线
        layout.addWidget(self._create_separator())
        
        # 监控目录区域
        layout.addWidget(QLabel("📁 监控目录"))
        self.monitored_directories_panel = self._create_monitored_directories_panel()
        layout.addWidget(self.monitored_directories_panel)
        
        # 分隔线
        layout.addWidget(self._create_separator())
        
        # 任务队列区域
        layout.addWidget(QLabel("📋 任务队列"))
        self.task_list = self._create_task_list()
        layout.addWidget(self.task_list)
        
        layout.addStretch()
        return panel
        
    def _create_monitored_directories_panel(self) -> QWidget:
        """创建监控目录面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 目录列表
        self.directory_list = QListWidget()
        self.directory_list.setAlternatingRowColors(True)
        self.directory_list.setSelectionMode(QListWidget.NoSelection)
        layout.addWidget(self.directory_list)
        
        # 控制按钮
        controls_layout = QHBoxLayout()
        add_btn = QPushButton("+ 添加")
        add_btn.clicked.connect(self._add_directory)
        remove_btn = QPushButton("- 移除")
        remove_btn.clicked.connect(self._remove_directory)
        controls_layout.addWidget(add_btn)
        controls_layout.addWidget(remove_btn)
        layout.addLayout(controls_layout)
        
        # 文件统计
        self.stats_label = QLabel("总文件: 0 | 图像: 0 | 视频: 0 | 音频: 0")
        layout.addWidget(self.stats_label)
        
        return panel
        
    def _create_task_list(self) -> QWidget:
        """创建任务列表"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 任务过滤和排序
        filter_layout = QHBoxLayout()
        self.task_filter = QListWidget()
        self.task_filter.setFlow(QListWidget.LeftToRight)
        self.task_filter.setMaximumHeight(40)
        self.task_filter.addItem("全部")
        self.task_filter.addItem("待处理")
        self.task_filter.addItem("运行中")
        self.task_filter.addItem("已完成")
        self.task_filter.addItem("失败")
        layout.addWidget(self.task_filter)
        
        # 任务优先级控制
        priority_layout = QHBoxLayout()
        priority_layout.addWidget(QLabel("优先级:"))
        self.video_priority = QComboBox()
        self.video_priority.addItems(["高", "中", "低"])
        self.video_priority.setCurrentText("中")
        self.audio_priority = QComboBox()
        self.audio_priority.addItems(["高", "中", "低"])
        self.audio_priority.setCurrentText("中")
        self.image_priority = QComboBox()
        self.image_priority.addItems(["高", "中", "低"])
        self.image_priority.setCurrentText("中")
        priority_layout.addWidget(QLabel("视频:"))
        priority_layout.addWidget(self.video_priority)
        priority_layout.addWidget(QLabel("音频:"))
        priority_layout.addWidget(self.audio_priority)
        priority_layout.addWidget(QLabel("图像:"))
        priority_layout.addWidget(self.image_priority)
        apply_btn = QPushButton("应用")
        apply_btn.clicked.connect(self._apply_priority_settings)
        priority_layout.addWidget(apply_btn)
        layout.addLayout(priority_layout)
        
        # 任务列表
        self.task_list_widget = QListWidget()
        self.task_list_widget.setAlternatingRowColors(True)
        layout.addWidget(self.task_list_widget)
        
        # 进度信息
        self.progress_label = QLabel("处理中: 0/0 | 预计剩余: 计算中...")
        layout.addWidget(self.progress_label)
        
        # 控制按钮
        controls_layout = QHBoxLayout()
        self.pause_btn = QPushButton("暂停")
        self.pause_btn.clicked.connect(self._pause_tasks)
        self.resume_btn = QPushButton("恢复")
        self.resume_btn.clicked.connect(self._resume_tasks)
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self._cancel_tasks)
        controls_layout.addWidget(self.pause_btn)
        controls_layout.addWidget(self.resume_btn)
        controls_layout.addWidget(self.cancel_btn)
        layout.addLayout(controls_layout)
        
        return panel
        
    def _create_result_panel(self) -> QWidget:
        """创建结果面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        layout.addWidget(QLabel("搜索结果:"))
        self.result_list = QListWidget()
        layout.addWidget(self.result_list)
        
        return panel
        
    def _create_separator(self) -> QWidget:
        """创建分隔线"""
        line = QWidget()
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: #cccccc;")
        return line
        
    def _on_search(self):
        """搜索按钮点击事件"""
        query = self.search_input.text()
        if not query:
            return
            
        # 启动搜索线程
        self.search_worker = SearchWorker(self.api_client, query)
        self.search_worker.finished.connect(self._on_search_finished)
        self.search_worker.start()
        
    def _on_search_finished(self, results: List[Dict]):
        """搜索完成回调"""
        self.result_list.clear()
        for result in results:
            self.result_list.addItem(result['file_name'])
            
    def _add_directory(self):
        """添加监控目录"""
        directory = QFileDialog.getExistingDirectory(self, "选择要监控的目录")
        if directory:
            # 调用API添加监控目录
            self.api_client.add_monitored_directory(directory)
            # 刷新目录列表
            self._refresh_directories()
            
    def _remove_directory(self):
        """移除监控目录"""
        # 调用API移除监控目录
        # 刷新目录列表
        self._refresh_directories()
        
    def _refresh_directories(self):
        """刷新监控目录列表"""
        self.directory_list.clear()
        # 调用API获取监控目录列表
        directories = self.api_client.get_monitored_directories()
        for dir_info in directories:
            # 添加目录项，包含路径和状态
            status_icon = "🟢" if dir_info['status'] == 'monitoring' else "🔴"
            item_text = f"{status_icon} {dir_info['path']}"
            self.directory_list.addItem(item_text)
        # 更新文件统计
        self._refresh_stats()
        
    def _refresh_stats(self):
        """刷新文件统计信息"""
        # 调用API获取文件统计
        stats = self.api_client.get_file_stats()
        self.stats_label.setText(
            f"总文件: {stats['total']} | "
            f"图像: {stats['image']} | "
            f"视频: {stats['video']} | "
            f"音频: {stats['audio']}"
        )
        
    def _apply_priority_settings(self):
        """应用优先级设置"""
        # 调用API设置文件类型优先级
        priority_settings = {
            'video': self.video_priority.currentText(),
            'audio': self.audio_priority.currentText(),
            'image': self.image_priority.currentText()
        }
        self.api_client.set_priority_settings(priority_settings)
        
    def _pause_tasks(self):
        """暂停任务"""
        # 调用API暂停任务
        self.api_client.pause_tasks()
        
    def _resume_tasks(self):
        """恢复任务"""
        # 调用API恢复任务
        self.api_client.resume_tasks()
        
    def _cancel_tasks(self):
        """取消任务"""
        # 调用API取消任务
        self.api_client.cancel_tasks()
```

### 2.10.3 监控目录可视化设计

#### 2.10.3.1 监控目录面板UI布局

```
┌─────────────────────────────────────────────────────────┐
│  📁 监控目录                                              │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 🟢 /data/project/msearch/testdata              │   │
│  │   文件: 125 | 图像: 80 | 视频: 30 | 音频: 15     │   │
│  │   [暂停] [删除]                                │   │
│  ├─────────────────────────────────────────────────┤   │
│  │ 🟢 /home/user/MediaLibrary                     │   │
│  │   文件: 342 | 图像: 200 | 视频: 100 | 音频: 42    │   │
│  │   [暂停] [删除]                                │   │
│  ├─────────────────────────────────────────────────┤   │
│  │ 🔴 /home/user/TempFiles                       │   │
│  │   文件: 0 | 图像: 0 | 视频: 0 | 音频: 0          │   │
│  │   状态: 错误 - 目录不可访问                     │   │
│  │   [恢复] [删除]                                │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  [+ 添加目录]                                           │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 总计: 467 | 图像: 280 | 视频: 130 | 音频: 57       │   │
│  │ 新文件: 5 | 处理中: 12 | 待处理: 450               │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

#### 2.10.3.2 目录状态指示器

| 状态 | 图标 | 说明 |
|------|------|------|
| 监控中 | 🟢 | 目录正在正常监控 |
| 暂停 | 🟡 | 目录监控已暂停 |
| 错误 | 🔴 | 目录监控出错（不可访问、权限问题等） |
| 初始化中 | 🔵 | 目录监控正在初始化 |

### 2.10.4 任务优先级控制设计

#### 2.10.4.1 任务优先级控制UI

```
┌─────────────────────────────────────────────────────────┐
│  📋 任务优先级控制                                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  文件类型优先级:                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 视频: [高 ▼] [中] [低]                           │   │
│  │ 音频: [高] [中 ▼] [低]                           │   │
│  │ 图像: [高] [中 ▼] [低]                           │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  [应用设置] [恢复默认]                                 │
│                                                         │
│  当前优先级队列:                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 1. video_embed (优先级: 2)                     │   │
│  │ 2. audio_embed (优先级: 3)                     │   │
│  │ 3. image_embed (优先级: 5)                     │   │
│  │ 4. thumbnail_gen (优先级: 9)                   │   │
│  │ 5. preview_gen (优先级: 10)                    │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

#### 2.10.4.2 优先级调整规则

| 优先级 | 高 | 中 | 低 |
|--------|-----|-----|-----|
| 视频 | 1-2 | 4-5 | 8-9 |
| 音频 | 1-2 | 4-5 | 8-9 |
| 图像 | 1-2 | 4-5 | 8-9 |
| 缩略图 | 8-9 | 9-10 | 10-11 |
| 预览 | 8-9 | 9-10 | 10-11 |

### 2.10.5 处理进度可视化设计

#### 2.10.5.1 进度显示UI

```
┌─────────────────────────────────────────────────────────┐
│  📊 处理进度                                            │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  总体进度:                                               │
│  ┌─────────────────────────────────────────────────┐   │
│  │ [██████████░░░░░░░░░░░░░░] 35%                  │   │
│  │ 450/1280 文件                                     │   │
│  │ 预计剩余时间: 00:45:23                           │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  当前处理:                                               │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 🎬 video_project_01.mp4                         │   │
│  │ 类型: 视频 | 状态: 处理中                        │   │
│  │ 进度: [███████████░░░░] 67%                      │   │
│  │ 已用: 12.5s | 预计剩余: 6.2s                     │   │
│  │ 任务: 向量化 (优先级: 2)                         │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  队列状态:                                               │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 等待: 435 | 运行中: 3 | 完成: 842 | 失败: 0        │   │
│  │ 速度: 12.5 文件/分钟 | 并发数: 4/8                │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  [暂停] [恢复] [取消]                                 │
└─────────────────────────────────────────────────────────┘
```

#### 2.10.5.2 进度更新规则

- **实时更新**: 进度信息每秒更新一次
- **预计剩余时间**: 基于最近处理的平均速度计算
- **处理速度**: 显示最近60秒的平均处理速度
- **并发数**: 显示当前活跃任务数和最大并发数

---

# 第三部分：详细流程设计

## 3.1 数据处理流程

### 3.1.1 完整数据处理流程

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         数据处理流程图                                       │
└─────────────────────────────────────────────────────────────────────────────┘

阶段 1：文件发现
┌─────────────────────────────────────────────────────────────────────────────┐
│ 文件监控器 (FileMonitor) ──▶ 检测到新文件/修改文件                              │
│                              ↓                                               │
│                         写入 SQLite 队列 (file_events)                         │
└─────────────────────────────────────────────────────────────────────────────┘

阶段 2：文件扫描
┌─────────────────────────────────────────────────────────────────────────────┐
│ 任务调度器 ──▶ 从 SQLite 队列读取文件事件                                       │
│                  ↓                                                           │
│              文件扫描器 (FileScanner) ──▶ 扫描文件                              │
│                  ↓                                                           │
│              元数据提取器 (MetadataExtractor) ──▶ 提取元数据                     │
│                  ↓                                                           │
│              写入 SQLite 数据库 (files表)                                       │
└─────────────────────────────────────────────────────────────────────────────┘

阶段 3：预处理
┌─────────────────────────────────────────────────────────────────────────────┐
│ 任务调度器 ──▶ 创建预处理任务                                                   │
│                  ↓                                                           │
│              任务执行器 ──▶ 根据文件类型选择处理器                                │
│                  ↓                                                           │
│              ├─ 图像预处理 (ImagePreprocessor)                                  │
│              │   ├─ 调整大小 (resize to 512x512)                               │
│              │   ├─ 格式转换 (convert to RGB)                                  │
│              │   └─ 归一化 (normalize)                                         │
│              │                                                                 │
│              ├─ 视频预处理 (VideoPreprocessor)                                  │
│              │   ├─ 时长判断 (≤6秒 or >6秒)                                     │
│              │   ├─ 音频分离 (extract audio)                                    │
│              │   ├─ 场景检测 (scene detection)                                  │
│              │   ├─ 视频切片 (video slicing)                                    │
│              │   └─ 帧提取 (frame extraction)                                   │
│              │                                                                 │
│              └─ 音频预处理 (AudioPreprocessor)                                  │
│                  ├─ 价值判断 (≥3秒)                                             │
│                  ├─ 重采样 (resample to 48000Hz)  ◄── CLAP模型要求48kHz          │
│                  ├─ 格式转换 (convert to mono)                                  │
│                  └─ 归一化 (normalize)                                         │
└─────────────────────────────────────────────────────────────────────────────┘

阶段 4：向量化
┌─────────────────────────────────────────────────────────────────────────────┐
│ 任务调度器 ──▶ 创建向量化任务                                                   │
│                  ↓                                                           │
│              向量化引擎 (EmbeddingEngine) ──▶ 加载模型                           │
│                  ↓                                                           │
│              ├─ 图像向量化 (Image Embedding)                                    │
│              │   ├─ 使用模型: chinese_clip_*                                   │
│              │   ├─ 输入: 预处理后的图像 (batch_size=16)                         │
│              │   ├─ 输出: 向量 (维度按模型默认值: 512/768)                        │
│              │   └─ 精度: float16                                              │
│              │                                                                 │
│              ├─ 视频向量化 (Video Embedding)                                    │
│              │   ├─ 使用模型: chinese_clip_*                                   │
│              │   ├─ 输入: 视频帧序列 (batch_size=16)                             │
│              │   ├─ 输出: 向量 (每帧一个向量，维度按模型默认值)                    │
│              │   └─ 精度: float16                                              │
│              │                                                                 │
│              └─ 音频向量化 (Audio Embedding)                                    │
│                  ├─ 使用模型: audio_model (CLAP)                               │
│                  ├─ 输入: 预处理后的音频 (batch_size=8)                          │
│                  ├─ 输出: 向量 (维度: 512)                                       │
│                  └─ 精度: float16                                              │
└─────────────────────────────────────────────────────────────────────────────┘

阶段 5：存储
┌─────────────────────────────────────────────────────────────────────────────┐
│ 向量数据准备                                                                  │
│     ↓                                                                        │
│ ├─ 向量存储 (LanceDB)                                                         │
│ │  ├─ 表名: unified_vectors                                                   │
│ │  ├─ 支持多种向量维度 (512/768等，按模型默认值)                                 │
│ │  └─ 字段: vector, file_id, file_name, file_path, file_type, modality,        │
│ │          model_id, embedding_dim, segment_id, start_time, end_time,          │
│ │          frame_index, created_at                                             │
│ │                                                                             │
│ └─ 元数据存储 (SQLite)                                                        │
│    ├─ 表名: files                                                             │
│    └─ 字段: id, file_path, file_name, file_type, file_size, file_hash,         │
│             processing_status, created_at, updated_at                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 3.2 检索流程

### 3.2.1 检索流程图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         检索流程图                                           │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   用户输入   │────▶│  查询处理    │────▶│  向量化      │────▶│  向量检索    │
│  (文本/图像) │     │  (预处理)    │     │  (Embedding) │     │  (LanceDB)   │
└─────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
                                                                     │
                                                                     ▼
┌─────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   结果展示   │◀────│  结果排序    │◀────│  相似度计算  │◀────│  候选集      │
│  (Gallery)  │     │  (Ranking)   │     │  (1-distance)│     │  (Top-K)     │
└─────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

### 3.2.2 相似度计算

```python
def calculate_similarity(distance: float) -> float:
    """
    计算相似度
    
    公式：similarity = 1.0 - distance
    
    Args:
        distance: 距离值 (0-2)
        
    Returns:
        相似度 (0-1)
    """
    similarity = 1.0 - distance
    # 确保在[0, 1]范围内
    return max(0.0, min(1.0, similarity))
```

## 3.3 任务调度流程

### 3.3.1 任务调度流程图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         任务调度流程图                                       │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   任务创建   │────▶│  优先级计算  │────▶│  任务入队    │────▶│  SQLite队列  │
│  (Create)   │     │  (Priority)  │     │  (Enqueue)   │     │  (Queue)     │
└─────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
                                                                     │
                                                                     ▼
┌─────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   任务完成   │◀────│  状态更新    │◀────│  任务执行    │◀────│  任务出队    │
│  (Complete) │     │  (Status)    │     │  (Execute)   │     │  (Dequeue)   │
└─────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

## 3.4 目录监控与增量索引流程

### 3.4.1 文件监控与增量索引流程

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    目录监控与增量索引流程图                                   │
└─────────────────────────────────────────────────────────────────────────────┘

阶段 1：文件监控
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│  ┌─────────────────┐                                                         │
│  │  Watchdog       │  ◄── 文件系统事件监控                                    │
│  │  (Observer)     │                                                         │
│  └────────┬────────┘                                                         │
│           │                                                                  │
│           ▼                                                                  │
│  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐        │
│  │  on_created()   │     │  on_modified()  │     │  on_deleted()   │        │
│  │  (文件创建)      │     │  (文件修改)      │     │  (文件删除)      │        │
│  └────────┬────────┘     └────────┬────────┘     └────────┬────────┘        │
│           │                       │                       │                  │
│           └───────────────────────┼───────────────────────┘                  │
│                                   │                                          │
│                                   ▼                                          │
│                          ┌─────────────────┐                                 │
│                          │  SQLite队列     │                                 │
│                          │  file_events    │                                 │
│                          │  ─────────────  │                                 │
│                          │  event_type     │  (created/modified/deleted)    │
│                          │  file_path      │  (文件路径)                     │
│                          │  timestamp      │  (时间戳)                       │
│                          │  file_hash      │  (文件哈希，用于去重)            │
│                          └─────────────────┘                                 │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

阶段 2：增量索引处理
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│  ┌─────────────────┐                                                         │
│  │  任务调度器      │  ◄── 定期扫描SQLite队列                                  │
│  │  (TaskScheduler)│                                                         │
│  └────────┬────────┘                                                         │
│           │                                                                  │
│           ▼                                                                  │
│  ┌─────────────────┐                                                         │
│  │  读取文件事件    │                                                         │
│  └────────┬────────┘                                                         │
│           │                                                                  │
│           ▼                                                                  │
│  ┌─────────────────────────────────────────────────────────────────┐        │
│  │  事件类型判断                                                    │        │
│  │  ├─ created (新文件)  ──▶  完整处理流程 (扫描→预处理→向量化→存储)  │        │
│  │  ├─ modified (修改)   ──▶  增量更新流程 (对比哈希→更新向量→更新元数据)│        │
│  │  └─ deleted (删除)    ──▶  删除流程 (删除向量→删除元数据→清理缓存)   │        │
│  └─────────────────────────────────────────────────────────────────┘        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

阶段 3：新文件处理流程 (created)
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│  文件创建事件                                                                │
│       │                                                                      │
│       ▼                                                                      │
│  ┌─────────────────┐                                                         │
│  │  1. 文件扫描     │  ◄── 提取文件元数据 (大小、类型、哈希)                   │
│  └────────┬────────┘                                                         │
│           │                                                                  │
│           ▼                                                                  │
│  ┌─────────────────┐                                                         │
│  │  2. 重复检查     │  ◄── 对比文件哈希，检查是否已存在                        │
│  └────────┬────────┘                                                         │
│           │                                                                  │
│           ▼                                                                  │
│  ┌─────────────────┐                                                         │
│  │  3. 创建索引记录 │  ◄── 写入SQLite (status=pending)                        │
│  └────────┬────────┘                                                         │
│           │                                                                  │
│           ▼                                                                  │
│  ┌─────────────────┐                                                         │
│  │  4. 提交处理任务 │  ◄── 提交到SQLite任务队列                                │
│  │     file_embed_*│                                                         │
│  └────────┬────────┘                                                         │
│           │                                                                  │
│           ▼                                                                  │
│  ┌─────────────────┐                                                         │
│  │  5. 异步处理     │  ◄── 线程池执行：预处理 → 向量化 → 存储                   │
│  └────────┬────────┘                                                         │
│           │                                                                  │
│           ▼                                                                  │
│  ┌─────────────────┐                                                         │
│  │  6. 状态更新     │  ◄── 更新SQLite (status=completed/failed)               │
│  └─────────────────┘                                                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

阶段 4：文件修改处理流程 (modified)
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│  文件修改事件                                                                │
│       │                                                                      │
│       ▼                                                                      │
│  ┌─────────────────┐                                                         │
│  │  1. 计算新哈希   │  ◄── 重新计算文件哈希                                    │
│  └────────┬────────┘                                                         │
│           │                                                                  │
│           ▼                                                                  │
│  ┌─────────────────┐                                                         │
│  │  2. 哈希对比     │  ◄── 与数据库中的旧哈希对比                              │
│  └────────┬────────┘                                                         │
│           │                                                                  │
│     ┌─────┴─────┐                                                            │
│     ▼           ▼                                                            │
│  相同          不同                                                           │
│   │             │                                                            │
│   ▼             ▼                                                            │
│  跳过    ┌─────────────────┐                                                 │
│         │  3. 删除旧向量   │  ◄── 从LanceDB删除旧向量                          │
│         └────────┬────────┘                                                 │
│                  │                                                           │
│                  ▼                                                           │
│         ┌─────────────────┐                                                 │
│         │  4. 重新向量化   │  ◄── 重新执行预处理→向量化→存储                   │
│         └────────┬────────┘                                                 │
│                  │                                                           │
│                  ▼                                                           │
│         ┌─────────────────┐                                                 │
│         │  5. 更新元数据   │  ◄── 更新SQLite中的文件信息                        │
│         └─────────────────┘                                                 │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

阶段 5：文件删除处理流程 (deleted)
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│  文件删除事件                                                                │
│       │                                                                      │
│       ▼                                                                      │
│  ┌─────────────────┐                                                         │
│  │  1. 查询文件记录 │  ◄── 从SQLite查询文件信息                                │
│  └────────┬────────┘                                                         │
│           │                                                                  │
│           ▼                                                                  │
│  ┌─────────────────┐                                                         │
│  │  2. 删除向量     │  ◄── 从LanceDB删除该文件的所有向量                        │
│  └────────┬────────┘                                                         │
│           │                                                                  │
│           ▼                                                                  │
│  ┌─────────────────┐                                                         │
│  │  3. 删除元数据   │  ◄── 从SQLite删除文件记录                                │
│  └────────┬────────┘                                                         │
│           │                                                                  │
│           ▼                                                                  │
│  ┌─────────────────┐                                                         │
│  │  4. 清理缓存     │  ◄── 清理相关缓存数据                                    │
│  └─────────────────┘                                                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.4.2 增量索引实现

```python
class IncrementalIndexer:
    """
    增量索引器 - 处理文件变化的增量索引
    """
    
    def __init__(
        self,
        config: Dict,
        queue_manager: QueueManager,
        file_scanner: FileScanner,
        task_manager: TaskManager
    ):
        self.config = config
        self.queue_manager = queue_manager
        self.file_scanner = file_scanner
        self.task_manager = task_manager
        self.db = DatabaseManager(config['database']['db_path'])
        
    def process_file_events(self):
        """处理文件事件队列"""
        while True:
            # 从SQLite队列读取文件事件
            event = self.queue_manager.get('file_events', timeout=1.0)
            if event is None:
                continue
                
            event_type = event.get('event_type')
            file_path = event.get('file_path')
            
            # 根据事件类型处理
            if event_type == 'created':
                self._handle_file_created(file_path)
            elif event_type == 'modified':
                self._handle_file_modified(file_path)
            elif event_type == 'deleted':
                self._handle_file_deleted(file_path)
                
    def _handle_file_created(self, file_path: str):
        """处理文件创建事件"""
        logger.info(f"处理新文件: {file_path}")
        
        # 1. 检查文件是否支持
        if not self._is_supported_file(file_path):
            return
            
        # 2. 提取元数据
        metadata = self.file_scanner.extract_metadata(file_path)
        
        # 3. 检查是否已存在（通过哈希）
        existing = self.db.get_file_by_hash(metadata['file_hash'])
        if existing:
            logger.info(f"文件已存在，跳过: {file_path}")
            return
            
        # 4. 创建文件记录
        file_id = str(uuid.uuid4())
        self.db.insert_file({
            'id': file_id,
            'file_path': file_path,
            'file_name': os.path.basename(file_path),
            'file_type': metadata['file_type'],
            'file_size': metadata['file_size'],
            'file_hash': metadata['file_hash'],
            'processing_status': 'pending',
            'created_at': time.time()
        })
        
        # 5. 提交处理任务
        self._submit_processing_task(file_id, file_path, metadata['file_type'])
        
    def _handle_file_modified(self, file_path: str):
        """处理文件修改事件"""
        logger.info(f"处理文件修改: {file_path}")
        
        # 1. 查找文件记录
        file_record = self.db.get_file_by_path(file_path)
        if not file_record:
            # 文件不存在，按新文件处理
            self._handle_file_created(file_path)
            return
            
        # 2. 计算新哈希
        new_hash = self.file_scanner.calculate_hash(file_path)
        
        # 3. 对比哈希
        if new_hash == file_record['file_hash']:
            logger.info(f"文件内容未变化，跳过: {file_path}")
            return
            
        # 4. 删除旧向量
        self._delete_vectors(file_record['id'])
        
        # 5. 重新提交处理任务
        self._submit_processing_task(
            file_record['id'],
            file_path,
            file_record['file_type']
        )
        
    def _handle_file_deleted(self, file_path: str):
        """处理文件删除事件"""
        logger.info(f"处理文件删除: {file_path}")
        
        # 1. 查找文件记录
        file_record = self.db.get_file_by_path(file_path)
        if not file_record:
            return
            
        # 2. 删除向量
        self._delete_vectors(file_record['id'])
        
        # 3. 删除文件记录
        self.db.delete_file(file_record['id'])
        
    def _submit_processing_task(self, file_id: str, file_path: str, file_type: str):
        """提交处理任务"""
        # 根据文件类型选择任务类型
        task_type_map = {
            'image': 'file_embed_image',
            'video': 'file_embed_video',
            'audio': 'file_embed_audio'
        }
        task_type = task_type_map.get(file_type)
        
        if task_type:
            self.task_manager.create_task(
                task_type=task_type,
                task_data={'file_path': file_path, 'file_id': file_id},
                priority=5,
                file_id=file_id,
                file_path=file_path
            )
            
    def _delete_vectors(self, file_id: str):
        """删除文件的所有向量"""
        # 从LanceDB删除向量
        vector_store = VectorStore(self.config['vector_store'])
        vector_store.initialize()
        vector_store.delete(file_id)
        vector_store.close()
```

### 3.4.3 基于内容哈希的任务去重机制

#### 3.4.3.1 设计目标

- **基于内容去重**：使用文件内容哈希（而非文件名）识别重复文件
- **避免重复处理**：相同内容的文件只处理一次，节省计算资源
- **支持文件移动**：文件重命名或移动后不会重复处理
- **检测内容变化**：文件内容修改后能重新处理

#### 3.4.3.2 去重架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      基于内容哈希的任务去重架构                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  文件事件 (created/modified)                                                  │
│       │                                                                      │
│       ▼                                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐        │
│  │  1. 计算内容哈希                                                  │        │
│  │     ├─ 图像: MD5(文件内容)                                        │        │
│  │     ├─ 视频: MD5(前1MB + 后1MB)                                   │        │
│  │     └─ 音频: MD5(文件内容)                                        │        │
│  └────────────────────────┬────────────────────────────────────────┘        │
│                           │                                                  │
│                           ▼                                                  │
│  ┌─────────────────────────────────────────────────────────────────┐        │
│  │  2. 查询哈希索引                                                  │        │
│  │     ├─ 查询SQLite: SELECT * FROM files WHERE file_hash = ?        │        │
│  │     └─ 检查状态: pending/completed/failed                         │        │
│  └────────────────────────┬────────────────────────────────────────┘        │
│                           │                                                  │
│           ┌───────────────┼───────────────┐                                │
│           ▼               ▼               ▼                                │
│        不存在          已存在(完成)      已存在(失败)                        │
│           │               │               │                                │
│           ▼               ▼               ▼                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                        │
│  │ 创建新任务   │  │ 跳过处理    │  │ 重新提交    │                        │
│  │ (正常流程)   │  │ (去重)      │  │ (重试)      │                        │
│  └─────────────┘  └─────────────┘  └─────────────┘                        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 3.4.3.3 哈希计算策略

| 文件类型 | 哈希算法 | 计算方式 | 说明 |
|---------|---------|---------|------|
| **图像** | MD5 | 完整文件内容 | 图像文件通常较小，计算完整哈希 |
| **视频** | MD5 | 前1MB + 后1MB | 大视频文件采样计算，平衡性能和准确性 |
| **音频** | MD5 | 完整文件内容 | 音频文件通常较小，计算完整哈希 |
| **文档** | MD5 | 完整文件内容 | 文档文件计算完整哈希 |

#### 3.4.3.4 数据库表设计

```sql
-- 文件表（已存在，添加哈希索引）
CREATE TABLE files (
    id TEXT PRIMARY KEY,
    file_path TEXT UNIQUE NOT NULL,
    file_name TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    file_hash TEXT NOT NULL,          -- 内容哈希
    processing_status TEXT DEFAULT 'pending',
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);

-- 哈希索引（加速去重查询）
CREATE INDEX idx_files_hash ON files(file_hash);

-- 复合索引（哈希+状态，用于检查是否存在）
CREATE INDEX idx_files_hash_status ON files(file_hash, processing_status);
```

#### 3.4.3.5 去重管理器实现

```python
class ContentHashDeduplicator:
    """
    基于内容哈希的任务去重管理器
    
    职责：
    - 计算文件内容哈希
    - 检查文件是否已存在
    - 管理哈希索引
    - 处理重复文件事件
    """
    
    def __init__(self, db_manager: DatabaseManager):
        """
        初始化去重管理器
        
        Args:
            db_manager: 数据库管理器
        """
        self.db = db_manager
        self._hash_cache: Dict[str, str] = {}  # 内存缓存: file_path -> hash
        self._cache_lock = threading.Lock()
        
    def calculate_file_hash(self, file_path: str, file_type: str) -> str:
        """
        计算文件内容哈希
        
        Args:
            file_path: 文件路径
            file_type: 文件类型 (image/video/audio)
            
        Returns:
            文件内容哈希 (MD5)
        """
        # 检查缓存
        with self._cache_lock:
            if file_path in self._hash_cache:
                return self._hash_cache[file_path]
        
        # 根据文件类型选择哈希策略
        if file_type == 'video':
            hash_value = self._calculate_video_hash(file_path)
        else:
            hash_value = self._calculate_full_hash(file_path)
        
        # 更新缓存
        with self._cache_lock:
            self._hash_cache[file_path] = hash_value
        
        return hash_value
    
    def _calculate_full_hash(self, file_path: str) -> str:
        """计算完整文件哈希"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _calculate_video_hash(self, file_path: str) -> str:
        """计算视频文件哈希（采样）"""
        file_size = os.path.getsize(file_path)
        hash_md5 = hashlib.md5()
        
        with open(file_path, "rb") as f:
            # 读取前1MB
            hash_md5.update(f.read(1024 * 1024))
            
            # 如果文件大于2MB，读取后1MB
            if file_size > 2 * 1024 * 1024:
                f.seek(-1024 * 1024, 2)
                hash_md5.update(f.read())
        
        return hash_md5.hexdigest()
    
    def check_duplicate(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """
        检查文件是否已存在
        
        Args:
            file_hash: 文件内容哈希
            
        Returns:
            已存在的文件记录，如果不存在返回None
        """
        return self.db.get_file_by_hash(file_hash)
    
    def handle_duplicate(
        self,
        file_path: str,
        file_hash: str,
        existing_record: Dict[str, Any]
    ) -> str:
        """
        处理重复文件
        
        Args:
            file_path: 新文件路径
            file_hash: 文件哈希
            existing_record: 已存在的文件记录
            
        Returns:
            处理结果: 'skipped' | 'retry' | 'update_path'
        """
        existing_status = existing_record.get('processing_status')
        existing_path = existing_record.get('file_path')
        
        # 情况1: 已存在且处理完成
        if existing_status == 'completed':
            if existing_path != file_path:
                # 文件移动，更新路径
                logger.info(f"文件移动 detected: {existing_path} -> {file_path}")
                self.db.update_file_path(existing_record['id'], file_path)
                return 'update_path'
            else:
                # 完全重复，跳过
                logger.info(f"重复文件，跳过: {file_path}")
                return 'skipped'
        
        # 情况2: 已存在但处理失败
        elif existing_status == 'failed':
            logger.info(f"文件之前处理失败，重新提交: {file_path}")
            self.db.update_file_status(existing_record['id'], 'pending')
            return 'retry'
        
        # 情况3: 正在处理中
        elif existing_status == 'pending':
            logger.info(f"文件正在处理中，跳过: {file_path}")
            return 'skipped'
        
        # 情况4: 其他状态
        else:
            logger.warning(f"未知状态 {existing_status}，跳过: {file_path}")
            return 'skipped'
    
    def process_new_file(
        self,
        file_path: str,
        file_type: str
    ) -> Tuple[bool, Optional[str]]:
        """
        处理新文件（带去重检查）
        
        Args:
            file_path: 文件路径
            file_type: 文件类型
            
        Returns:
            (是否为新文件, 文件ID或None)
        """
        # 1. 计算文件哈希
        file_hash = self.calculate_file_hash(file_path, file_type)
        
        # 2. 检查是否已存在
        existing = self.check_duplicate(file_hash)
        
        if existing:
            # 3. 处理重复
            result = self.handle_duplicate(file_path, file_hash, existing)
            
            if result == 'skipped':
                return False, None
            elif result == 'retry':
                return True, existing['id']
            elif result == 'update_path':
                return True, existing['id']
        
        # 4. 新文件，创建记录
        file_id = str(uuid.uuid4())
        self.db.insert_file({
            'id': file_id,
            'file_path': file_path,
            'file_name': os.path.basename(file_path),
            'file_type': file_type,
            'file_size': os.path.getsize(file_path),
            'file_hash': file_hash,
            'processing_status': 'pending',
            'created_at': time.time(),
            'updated_at': time.time()
        })
        
        return True, file_id
    
    def clear_cache(self):
        """清空哈希缓存"""
        with self._cache_lock:
            self._hash_cache.clear()
```

#### 3.4.3.6 去重流程集成

```python
class FileProcessor:
    """文件处理器（集成去重机制）"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.db = DatabaseManager(config['database']['db_path'])
        self.deduplicator = ContentHashDeduplicator(self.db)
        self.task_manager = CentralTaskManager(config)
        
    def process_file_event(self, event_type: str, file_path: str):
        """处理文件事件"""
        # 1. 获取文件类型
        file_type = self._get_file_type(file_path)
        if not file_type:
            return
        
        if event_type == 'created':
            self._handle_created(file_path, file_type)
        elif event_type == 'modified':
            self._handle_modified(file_path, file_type)
        elif event_type == 'deleted':
            self._handle_deleted(file_path)
    
    def _handle_created(self, file_path: str, file_type: str):
        """处理文件创建事件（带去重）"""
        # 使用去重管理器处理
        is_new, file_id = self.deduplicator.process_new_file(file_path, file_type)
        
        if is_new and file_id:
            # 新文件，提交处理任务
            self._submit_task(file_id, file_path, file_type)
        # 否则已处理（跳过或重试）
    
    def _handle_modified(self, file_path: str, file_type: str):
        """处理文件修改事件（带哈希对比）"""
        # 1. 查找现有记录
        existing = self.db.get_file_by_path(file_path)
        if not existing:
            # 按新文件处理
            self._handle_created(file_path, file_type)
            return
        
        # 2. 计算新哈希
        new_hash = self.deduplicator.calculate_file_hash(file_path, file_type)
        
        # 3. 对比哈希
        if new_hash == existing['file_hash']:
            logger.info(f"文件内容未变化: {file_path}")
            return
        
        # 4. 内容变化，更新哈希并重新处理
        logger.info(f"文件内容变化，重新处理: {file_path}")
        self.db.update_file_hash(existing['id'], new_hash)
        self._delete_vectors(existing['id'])
        self._submit_task(existing['id'], file_path, file_type)
```

#### 3.4.3.7 性能优化

| 优化策略 | 实现方式 | 效果 |
|---------|---------|------|
| **哈希缓存** | 内存缓存最近计算的哈希 | 减少重复计算 |
| **数据库索引** | 哈希字段索引 | 加速去重查询 |
| **采样哈希** | 大视频文件采样计算 | 减少大文件处理时间 |
| **批量处理** | 批量查询哈希 | 减少数据库往返 |

#### 3.4.3.8 配置选项

```yaml
# config/config.yml
deduplication:
  enabled: true                    # 启用去重
  hash_algorithm: md5             # 哈希算法
  video_sample_size: 1048576      # 视频采样大小 (1MB)
  cache_size: 1000                # 哈希缓存大小
  cache_ttl: 3600                 # 缓存过期时间 (秒)
```

---

# 第四部分：性能优化设计

## 4.1 内存管理

### 4.1.1 内存使用预估

```
内存使用预估：
├─ 模型加载
│  ├─ chinese_clip_base: ~500MB
│  ├─ chinese_clip_large: ~1.2GB
│  └─ audio_model: ~590MB
│
├─ 向量缓存: ~100MB (10万向量)
├─ 任务队列: ~50MB
└─ 系统开销: ~200MB

总计: 1.5-3GB (取决于加载的模型)
```

### 4.1.2 内存优化策略

```python
class MemoryManager:
    """内存管理器"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.max_memory_percent = config.get('max_memory_percent', 90)
        
    def check_memory(self) -> bool:
        """检查内存使用情况"""
        import psutil
        memory = psutil.virtual_memory()
        return memory.percent < self.max_memory_percent
        
    def cleanup(self):
        """清理内存"""
        import gc
        gc.collect()
        
        # 清理GPU缓存
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
```

## 4.2 并行处理

### 4.2.1 线程池并行策略

```python
class ParallelProcessor:
    """并行处理器"""
    
    def __init__(self, thread_pool_manager: ThreadPoolManager):
        self.thread_pool_manager = thread_pool_manager
        
    async def process_batch(
        self,
        items: List[Any],
        process_func: Callable,
        pool_name: str = 'task'
    ) -> List[Any]:
        """
        批量并行处理
        
        Args:
            items: 待处理项列表
            process_func: 处理函数
            pool_name: 线程池名称
            
        Returns:
            处理结果列表
        """
        # 提交所有任务
        futures = [
            self.thread_pool_manager.submit(pool_name, process_func, item)
            for item in items
        ]
        
        # 等待所有任务完成
        results = [future.result() for future in futures]
        
        return results
```

## 4.3 缓存策略

### 4.3.1 多级缓存设计

```
┌─────────────────────────────────────────────────────────────────┐
│                        多级缓存架构                              │
├─────────────────────────────────────────────────────────────────┤
│  L1: 内存缓存 (LRU)                                             │
│  ├── 向量结果缓存                                                │
│  └── 元数据缓存                                                  │
│                                                                 │
│  L2: SQLite缓存                                                 │
│  ├── 文件元数据                                                  │
│  └── 任务状态                                                    │
│                                                                 │
│  L3: 文件系统缓存                                               │
│  ├── 缩略图                                                      │
│  └── 预处理后的媒体文件                                          │
└─────────────────────────────────────────────────────────────────┘
```

### 4.3.2 缓存实现

```python
class CacheManager:
    """缓存管理器"""
    
    def __init__(self, config: Dict):
        self.config = config
        
        # L1: 内存缓存
        self.memory_cache = LRUCache(
            maxsize=config.get('memory_cache_size', 1000)
        )
        
        # L2: SQLite缓存
        self.db_cache = SQLiteCache(
            db_path=config.get('cache_db_path', 'data/cache.db')
        )
        
    def get(self, key: str, level: str = 'all') -> Any:
        """获取缓存"""
        # L1
        if level in ['all', 'memory']:
            value = self.memory_cache.get(key)
            if value is not None:
                return value
                
        # L2
        if level in ['all', 'db']:
            value = self.db_cache.get(key)
            if value is not None:
                # 回填L1
                self.memory_cache[key] = value
                return value
                
        return None
        
    def set(self, key: str, value: Any, level: str = 'all'):
        """设置缓存"""
        # L1
        if level in ['all', 'memory']:
            self.memory_cache[key] = value
            
        # L2
        if level in ['all', 'db']:
            self.db_cache.set(key, value)
```

## 4.4 资源监控

### 4.4.1 资源监控器

```python
class ResourceMonitor:
    """资源监控器"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.monitoring = False
        self.monitor_thread = None
        
    def start(self):
        """启动监控"""
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.start()
        
    def _monitor_loop(self):
        """监控循环"""
        while self.monitoring:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 内存使用率
            memory = psutil.virtual_memory()
            
            # GPU使用率
            if torch.cuda.is_available():
                gpu_memory = torch.cuda.memory_allocated() / 1024**3
                gpu_memory_total = torch.cuda.get_device_properties(0).total_memory / 1024**3
                
            # 记录日志
            logger.debug(
                f"CPU: {cpu_percent}%, "
                f"Memory: {memory.percent}%, "
                f"GPU: {gpu_memory:.2f}/{gpu_memory_total:.2f}GB"
            )
            
            # 检查是否超过阈值
            if memory.percent > 90:
                logger.warning("内存使用率超过90%，触发清理")
                self._cleanup()
                
            time.sleep(5)
            
    def _cleanup(self):
        """清理资源"""
        import gc
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
```

---

# 第五部分：部署与运维

## 5.1 安装流程

### 5.1.1 安装脚本

```bash
#!/bin/bash
# install.sh

echo "=== msearch 安装脚本 ==="

# 1. 检测硬件
python3 scripts/detect_hardware.py

# 2. 安装依赖
pip install -r requirements.txt

# 3. 下载模型
python3 scripts/download_models.py

# 4. 初始化数据库
python3 scripts/init_database.py

# 5. 生成配置文件
python3 scripts/generate_config.py

echo "=== 安装完成 ==="
```

### 5.1.2 硬件检测

```python
# scripts/detect_hardware.py

def detect_hardware():
    """检测硬件并生成配置"""
    config = {}
    
    # 检测GPU
    if torch.cuda.is_available():
        gpu_count = torch.cuda.device_count()
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
        
        config['device'] = 'cuda'
        config['gpu_count'] = gpu_count
        config['gpu_memory'] = gpu_memory
        
        # 根据显存选择模型
        if gpu_memory >= 8:
            config['active_models'] = ['chinese_clip_large', 'audio_model']
        else:
            config['active_models'] = ['chinese_clip_base', 'audio_model']
    else:
        config['device'] = 'cpu'
        config['active_models'] = ['chinese_clip_base', 'audio_model']
        
    # 保存配置
    with open('config/hardware.yml', 'w') as f:
        yaml.dump(config, f)
        
    return config
```

## 5.2 配置说明

### 5.2.1 配置文件结构

```
config/
├── config.yml          # 主配置
├── hardware.yml        # 硬件配置（自动生成）
└── models.yml          # 模型配置
```

### 5.2.2 配置加载

```python
class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_dir: str = 'config'):
        self.config_dir = config_dir
        self.config = {}
        
    def load(self):
        """加载配置"""
        # 加载主配置
        with open(f'{self.config_dir}/config.yml', 'r') as f:
            self.config = yaml.safe_load(f)
            
        # 加载硬件配置
        with open(f'{self.config_dir}/hardware.yml', 'r') as f:
            hardware_config = yaml.safe_load(f)
            self.config.update(hardware_config)
            
    def get(self, key: str, default=None):
        """获取配置项"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            value = value.get(k, default)
            if value is None:
                return default
        return value
```

## 5.3 离线模式

### 5.3.1 离线模式配置

```yaml
# config/config.yml

system:
  offline_mode: true  # 启用离线模式
  
models:
  download_on_demand: false  # 禁止自动下载
  local_only: true  # 只使用本地模型
```

### 5.3.2 离线模式实现

```python
class OfflineModeManager:
    """离线模式管理器"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.offline_mode = config.get('offline_mode', True)
        
    def check_connectivity(self) -> bool:
        """检查网络连接"""
        if self.offline_mode:
            return False
            
        try:
            import urllib.request
            urllib.request.urlopen('https://www.google.com', timeout=1)
            return True
        except:
            return False
            
    def ensure_models_available(self) -> bool:
        """确保模型已下载"""
        model_dir = self.config.get('model_dir', 'data/models')
        
        for model_id in self.config.get('active_models', []):
            model_path = os.path.join(model_dir, model_id)
            if not os.path.exists(model_path):
                logger.error(f"模型 {model_id} 未下载")
                return False
                
        return True
```

## 5.4 故障排查

### 5.4.1 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| 模型加载失败 | 模型文件损坏 | 重新下载模型 |
| 内存不足 | 同时加载多个大模型 | 减少同时加载的模型数量 |
| GPU显存不足 | 批处理大小过大 | 减小batch_size |
| 检索速度慢 | 向量数量过多 | 创建索引或增加内存 |

### 5.4.2 日志系统

```python
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/msearch.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
```

---

# 第六部分：任务队列与通信设计

## 6.1 任务队列设计

### 6.1.1 队列架构

```
┌─────────────────────────────────────────────────────────────────┐
│                      任务队列架构                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    SQLite 任务队列                         │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │ 表: task_queue                                       │  │  │
│  │  │  ─────────────────────────────────────────────────  │  │  │
│  │  │  id: TEXT PRIMARY KEY                               │  │  │
│  │  │  task_type: TEXT                                    │  │  │
│  │  │  task_data: JSON                                    │  │  │
│  │  │  priority: INTEGER                                  │  │  │
│  │  │  status: TEXT (pending/running/completed/failed)    │  │  │
│  │  │  file_id: TEXT                                      │  │  │
│  │  │  file_path: TEXT                                    │  │  │
│  │  │  created_at: TIMESTAMP                              │  │  │
│  │  │  updated_at: TIMESTAMP                              │  │  │
│  │  │  retry_count: INTEGER                               │  │  │
│  │  │  error_message: TEXT                                │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    文件事件队列                            │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │ 表: file_events                                      │  │  │
│  │  │  ─────────────────────────────────────────────────  │  │  │
│  │  │  id: INTEGER PRIMARY KEY AUTOINCREMENT              │  │  │
│  │  │  event_type: TEXT (created/modified/deleted)        │  │  │
│  │  │  file_path: TEXT                                    │  │  │
│  │  │  file_hash: TEXT                                    │  │  │
│  │  │  timestamp: TIMESTAMP                               │  │  │
│  │  │  processed: BOOLEAN                                 │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    内存队列（运行时）                       │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │ Queue: task_submit                                   │  │  │
│  │  │ Queue: task_result                                   │  │  │
│  │  │ Queue: file_events                                   │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## 6.2 SQLite队列实现

### 6.2.1 SQLiteTaskQueue类

```python
class SQLiteTaskQueue:
    """
    SQLite任务队列管理器
    
    使用SQLite实现持久化任务队列，支持：
    - 任务持久化
    - 任务优先级
    - 任务状态跟踪
    - 任务依赖关系
    - 重试机制
    """
    
    def __init__(self, db_path: str, max_size: int = 10000):
        """
        初始化任务队列
        
        Args:
            db_path: SQLite数据库文件路径
            max_size: 队列最大长度
        """
        self.db_path = db_path
        self.max_size = max_size
        self._lock = threading.Lock()
        self._init_db()
        
    def _init_db(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建任务队列表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS task_queue (
                id TEXT PRIMARY KEY,
                task_type TEXT NOT NULL,
                task_data TEXT NOT NULL,
                priority INTEGER NOT NULL,
                status TEXT NOT NULL,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                file_id TEXT,
                file_path TEXT,
                retry_count INTEGER DEFAULT 0,
                error_message TEXT
            )
        ''')
        
        # 创建文件事件表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_hash TEXT,
                timestamp REAL NOT NULL,
                processed BOOLEAN DEFAULT 0
            )
        ''')
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_task_status ON task_queue(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_task_priority ON task_queue(priority)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_file_events_processed ON file_events(processed)')
        
        conn.commit()
        conn.close()
```

### 6.2.2 任务操作接口

```python
    def enqueue_task(self, task: Dict[str, Any]) -> bool:
        """
        添加任务到队列
        
        Args:
            task: 任务字典
            
        Returns:
            是否添加成功
        """
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 检查队列大小
            cursor.execute('SELECT COUNT(*) FROM task_queue WHERE status = ?', ('pending',))
            count = cursor.fetchone()[0]
            
            if count >= self.max_size:
                conn.close()
                logger.warning(f"任务队列已满: {self.max_size}")
                return False
            
            # 插入任务
            cursor.execute('''
                INSERT INTO task_queue 
                (id, task_type, task_data, priority, status, created_at, updated_at, file_id, file_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                task['id'],
                task['task_type'],
                json.dumps(task['task_data']),
                task.get('priority', 5),
                'pending',
                time.time(),
                time.time(),
                task.get('file_id'),
                task.get('file_path')
            ))
            
            conn.commit()
            conn.close()
            
            logger.debug(f"任务已添加到队列: {task['id']}")
            return True
    
    def dequeue_task(self) -> Optional[Dict[str, Any]]:
        """
        从队列获取任务
        
        Returns:
            任务字典，如果没有任务返回None
        """
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 获取优先级最高的待处理任务
            cursor.execute('''
                SELECT * FROM task_queue 
                WHERE status = ? 
                ORDER BY priority DESC, created_at ASC 
                LIMIT 1
            ''', ('pending',))
            
            row = cursor.fetchone()
            
            if row is None:
                conn.close()
                return None
            
            # 更新任务状态为处理中
            task_id = row[0]
            cursor.execute('''
                UPDATE task_queue 
                SET status = ?, updated_at = ? 
                WHERE id = ?
            ''', ('processing', time.time(), task_id))
            
            conn.commit()
            conn.close()
            
            # 构建任务字典
            task = {
                'id': row[0],
                'task_type': row[1],
                'task_data': json.loads(row[2]),
                'priority': row[3],
                'status': row[4],
                'created_at': row[5],
                'updated_at': row[6],
                'file_id': row[7],
                'file_path': row[8],
                'retry_count': row[9],
                'error_message': row[10]
            }
            
            return task
    
    def update_task_status(self, task_id: str, status: str, error_message: str = None) -> bool:
        """
        更新任务状态
        
        Args:
            task_id: 任务ID
            status: 新状态
            error_message: 错误信息
            
        Returns:
            是否更新成功
        """
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if error_message:
                cursor.execute('''
                    UPDATE task_queue 
                    SET status = ?, updated_at = ?, error_message = ? 
                    WHERE id = ?
                ''', (status, time.time(), error_message, task_id))
            else:
                cursor.execute('''
                    UPDATE task_queue 
                    SET status = ?, updated_at = ? 
                    WHERE id = ?
                ''', (status, time.time(), task_id))
            
            conn.commit()
            conn.close()
            
            logger.debug(f"任务状态已更新: {task_id} -> {status}")
            return True
```

## 6.3 组件通信机制

### 6.3.1 单进程内通信

在单进程架构下，组件间通信方式：

| 通信场景 | 通信方式 | 说明 |
|---------|---------|------|
| 任务提交 | SQLite队列 | 持久化、支持优先级 |
| 文件事件 | SQLite队列 + 内存事件 | 实时通知 |
| 状态查询 | 直接方法调用 | 低延迟 |
| 配置共享 | 内存对象 | 高效访问 |

### 6.3.2 文件事件处理流程

```
文件监控器检测到变化
        │
        ▼
┌─────────────────┐
│  写入SQLite队列  │
│  file_events表  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  发送内存事件    │
│  (可选，实时通知)│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  任务调度器处理  │
│  增量索引任务    │
└─────────────────┘
```

---

# 第七部分：服务化演进（参考）

## 7.1 演进路线图

### 7.1.1 当前阶段（单机单进程）

```
┌─────────────────────────────────────┐
│         单机单进程架构               │
│  ┌─────────┐ ┌─────────┐ ┌────────┐ │
│  │  WebUI  │ │ Desktop │ │  CLI   │ │
│  └────┬────┘ └────┬────┘ └───┬────┘ │
│       └─────────────┴─────────┘      │
│                   │                  │
│                   ▼                  │
│           ┌───────────┐              │
│           │  FastAPI  │              │
│           └─────┬─────┘              │
│                 │                    │
│                 ▼                    │
│     ┌───────────────────────┐        │
│     │   线程池（单进程内）   │        │
│     │  ┌─────┐┌─────┐┌────┐ │       │
│     │  │Embed││ I/O ││Task│ │       │
│     │  └─────┘└─────┘└────┘ │       │
│     └───────────────────────┘        │
└─────────────────────────────────────┘
```

### 7.1.2 未来演进方向

**阶段2：单机多进程（可选）**
- 当单进程无法满足性能需求时
- 将Embedding Worker拆分为独立进程
- 使用SQLite队列 + 共享内存通信

**阶段3：容器化部署**
- Docker容器化
- Docker Compose编排
- 适合中小规模部署

**阶段4：微服务集群**
- Kubernetes编排
- 服务发现和负载均衡
- 适合大规模企业部署

## 7.2 演进原则

### 7.2.1 架构演进原则

1. **渐进式演进**
   - 保持向后兼容
   - 逐步替换组件
   - 避免大规模重构

2. **接口稳定性**
   - 抽象接口层保持不变
   - 实现可以替换
   - 客户端无感知

3. **数据兼容性**
   - 向量数据库格式兼容
   - 元数据结构兼容
   - 配置格式兼容

### 7.2.2 演进触发条件

| 条件 | 当前架构 | 演进方向 |
|------|---------|---------|
| 向量数量 < 100万 | 单机单进程 | 无需演进 |
| 向量数量 > 100万 | 单机单进程 | 考虑多进程 |
| 并发用户 > 100 | 单机单进程 | 考虑多进程 |
| 需要高可用 | 单机 | 考虑容器化 |
| 多机部署 | 单机 | 考虑微服务 |

---

# 第八部分：测试与质量

## 8.1 测试策略

### 8.1.1 测试金字塔

```
                    ┌─────────┐
                    │  E2E测试 │  ← 用户场景验证
                    │  (10%)  │
                   ┌┴─────────┴┐
                   │  集成测试  │  ← 组件交互验证
                   │   (20%)   │
                  ┌┴───────────┴┐
                  │   单元测试    │  ← 函数逻辑验证
                  │    (70%)    │
                  └─────────────┘
```

### 8.1.2 测试覆盖要求

| 模块 | 单元测试覆盖率 | 集成测试 | E2E测试 |
|------|--------------|---------|---------|
| 任务管理 | ≥80% | 必需 | 必需 |
| 向量化引擎 | ≥70% | 必需 | 必需 |
| 向量存储 | ≥80% | 必需 | 可选 |
| 文件监控 | ≥70% | 必需 | 必需 |
| 检索引擎 | ≥80% | 必需 | 必需 |

### 8.1.3 关键测试场景

**向量化测试**：
- 图像向量化准确性
- 视频帧提取和向量化
- 音频向量化一致性
- 批处理性能

**检索测试**：
- 文本检索准确性
- 图像检索准确性
- 跨模态检索（文本搜图像/视频）
- 相似度阈值调优

**任务管理测试**：
- 任务优先级调度
- 任务失败重试
- 任务取消
- 并发任务处理

## 8.2 性能基准

### 8.2.1 性能指标

| 指标 | 目标值 | 测试方法 |
|------|--------|---------|
| 图像向量化延迟 | < 200ms | 单张图片 |
| 视频预处理延迟 | < 2000ms | 1分钟视频 |
| 音频向量化延迟 | < 500ms | 10秒音频 |
| 向量检索延迟 | < 100ms | 10万向量 |
| 并发任务处理 | > 10任务/秒 | 混合任务 |
| 内存占用 | < 4GB | 正常运行 |

### 8.2.2 性能测试工具

```python
# 性能测试示例
import time
import statistics

def benchmark_image_embedding():
    """图像向量化性能测试"""
    times = []
    
    for _ in range(100):
        start = time.time()
        result = embedding_engine.embed_image("test.jpg")
        elapsed = time.time() - start
        times.append(elapsed)
    
    print(f"平均延迟: {statistics.mean(times)*1000:.2f}ms")
    print(f"P99延迟: {statistics.quantiles(times, n=100)[98]*1000:.2f}ms")
```

## 8.3 质量标准

### 8.3.1 代码质量

- **代码风格**：遵循PEP 8
- **类型注解**：关键函数必须添加类型注解
- **文档字符串**：公共API必须添加docstring
- **复杂度**：圈复杂度 ≤ 10

### 8.3.2 代码审查清单

- [ ] 功能实现正确
- [ ] 单元测试通过
- [ ] 代码风格符合规范
- [ ] 性能影响评估
- [ ] 错误处理完善
- [ ] 日志记录适当
- [ ] 文档已更新

---

# 附录

## A.1 术语表

| 术语 | 说明 |
|------|------|
| CLIP | Contrastive Language-Image Pre-training，对比语言-图像预训练模型 |
| CLAP | Contrastive Language-Audio Pre-training，对比语言-音频预训练模型 |
| ANN | Approximate Nearest Neighbor，近似最近邻搜索 |
| IVF-PQ | Inverted File Product Quantization，倒排文件乘积量化 |
| mAP | mean Average Precision，平均精度均值 |
| 跨模态检索 | 使用一种模态（如文本）检索另一种模态（如图像） |

## A.2 参考资料

- [LanceDB Documentation](https://lancedb.github.io/lancedb/)
- [Infinity Documentation](https://github.com/michaelfeil/infinity)
- [SQLite Documentation](https://www.sqlite.org/docs.html)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

## A.3 版本历史

| 版本 | 日期 | 修改内容 |
|------|------|---------|
| 1.0 | 2025-01-29 | 初始版本，单进程多线程架构 |

---

**文档结束**