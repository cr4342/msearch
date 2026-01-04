# msearch 项目架构文档

## 1. 项目概述

msearch 是一款跨平台的多模态检索系统，采用单体架构设计，专注于单机桌面应用场景。系统使用 michaelfeil/infinity 作为多模型服务引擎，支持文本、图像、视频、音频四种模态的精准检索。

### 1.1 核心特性

- **智能检索**: 无需手动整理、无需添加标签即可实现智能检索
- **跨模态搜索**: 支持用任意模态（文本、图像、音频）检索其他模态内容
- **高精度定位**: 支持毫秒级时间戳精确定位，视频时序定位精度±5秒
- **零配置**: 素材无需整理、无需标签
- **高性能本地推理**: 利用Infinity Python-native模式实现高效向量化
- **单体架构**: 简洁清晰的模块划分，易于理解和维护

### 1.2 技术栈

| 技术层级 | 技术选择 | 核心特性 | 选型理由 |
|---------|---------|---------|---------|
| **任务管理** | **persist-queue + SQLite** | 线程安全、磁盘持久化、基于SQLite的队列 | 防止任务丢失，自动持久化，支持故障恢复 |
| **异步处理** | **asyncio** | 基于asyncio的高性能异步处理 | 高并发，低延迟 |
| **AI推理层** | **michaelfeil/infinity** | 多模型服务引擎，高吞吐量低延迟 | 零配置部署，GPU自动调度 |
| **向量存储层** | **Milvus Lite** | 高性能本地向量数据库，CPU/GPU加速，支持分布式扩展 | 单机运行，无需额外服务，低延迟，支持更多向量索引类型 |
| **元数据层** | **SQLite** | 轻量级关系数据库，零配置，文件级便携 | 零配置，文件级数据便携性 |
| **配置管理** | **YAML + 环境变量** | 配置驱动设计，支持热重载 | 灵活配置，动态调整 |
| **日志系统** | **Python logging** | 多级别日志，自动轮转，分类存储 | 完善的日志管理 |
| **多模态模型** | **CLIP/CLIP4Clip/CLAP/Whisper** | 专业化模型架构，针对不同模态优化 | 高精度多模态理解 |
| **媒体处理** | **FFmpeg + OpenCV + Librosa** | 专业级预处理，场景检测+智能切片 | 专业级媒体处理能力 |
| **文件监控** | **Watchdog** | 实时增量处理，跨平台文件系统事件 | 实时文件监控 |
| **文件扫描** | **os.walk + pathlib** | 递归目录遍历，跨平台路径处理 | 初始文件扫描 |
| **测试框架** | **pytest + pytest-asyncio** | 异步测试支持，覆盖率报告 | 完整的测试体系 |

## 2. 项目目录结构

```
msearch/
├── .gitignore
├── IFLOW.md
├── README.md
├── requirements.txt
├── requirements-test.txt
├── .git/
├── .kiro/
│   └── specs/
│       └── multimodal-search-system/
│           ├── design.md
│           ├── requirements.md
│           └── tasks.md
├── config/
│   └── config.yml          # 主配置文件
├── data/
│   ├── database/           # 数据库文件
│   ├── logs/               # 日志文件
│   └── models/             # AI模型文件
├── docs/
│   ├── api_documentation.md
│   ├── design.md
│   ├── development_plan.md
│   ├── requirements.md
│   ├── technical_implementation.md
│   ├── test_strategy.md
│   └── user_manual.md
├── examples/
│   ├── media_preprocessing_example.py
│   └── time_accurate_retrieval_demo.py
├── scripts/
│   ├── download_all_resources.sh
│   ├── install_auto.sh
│   └── install_offline.sh
├── src/                    # 源代码目录
│   ├── __init__.py
│   ├── main.py             # 应用入口
│   │
│   ├── core/               # 3大核心块
│   │   ├── __init__.py
│   │   ├── task_manager.py        # 任务管理器（用户任务进度展示和手动管理）
│   │   ├── embedding_engine.py    # 向量化引擎（直接集成Infinity和CLIP4Clip）
│   │   └── vector_store.py        # 向量存储（专注Milvus Lite）
│   │
│   ├── components/         # 辅助组件
│   │   ├── __init__.py
│   │   ├── file_scanner.py        # 文件扫描（初始扫描）
│   │   ├── file_monitor.py        # 文件监控（实时监控）
│   │   ├── media_processor.py     # 媒体处理（视频切片、音频提取等）
│   │   ├── database_manager.py   # 数据库管理（SQLite）
│   │   ├── config_manager.py      # 配置管理
│   │   ├── config_generator.py    # 配置生成器（硬件自适应）
│   │   ├── hardware_detector.py   # 硬件检测器
│   │   ├── model_selector.py      # 模型选择器
│   │   └── search_engine.py       # 检索引擎
│   │
│   ├── ui/                 # 用户界面
│   │   ├── __init__.py
│   │   ├── main_window.py
│   │   ├── search_widget.py
│   │   ├── config_widget.py
│   │   ├── task_control_widget.py # 任务管理控制面板
│   │   └── setup_wizard.py        # 初次启动设置向导
│
├── tests/                   # 测试目录
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_task_manager.py
│   ├── test_embedding_engine.py
│   ├── test_vector_store.py
│   ├── test_media_processor.py
│   ├── test_config_manager.py
│   ├── test_database_manager.py
│   ├── test_timestamp_accuracy.py
│   └── test_multimodal_fusion.py
├── logs/                    # 日志目录（项目根目录）
│   ├── msearch.log
│   ├── error.log
│   ├── performance.log
│   └── timestamp.log
├── temp/                   # 临时文件目录
├── testdata/               # 测试数据
└── venv/                   # 虚拟环境
```

## 3. 开发优先级说明

### 3.1 核心功能优先

根据项目需求，开发应按以下优先级进行：

**P0 - 最高优先级（核心后端功能）**:
1. 配置管理系统 (core/config_manager.py)
2. 日志系统 (core/logger.py)
3. 数据库管理器 (storage/database_manager.py)
4. 向量存储器 (storage/vector_store.py)
5. 文件监控器 (core/file_monitor.py)
6. 向量化引擎 (business/embedding_engine.py)
7. 媒体处理器 (processors/)
8. 调度器 (business/processing_orchestrator.py)
9. 任务管理器 (business/task_manager.py)
10. 智能检索引擎 (business/smart_retrieval.py)

**P1 - 高优先级（API服务）**:
1. FastAPI应用 (api/app.py)
2. API路由 (api/routes/)
3. 请求/响应模型 (api/models/)
4. 中间件 (api/middleware/)

**P2 - 中优先级（高级功能）**:
1. 人脸管理器 (business/face_manager.py)
2. 多模态融合优化
3. 性能优化
4. 错误处理完善

**P3 - 低优先级（用户界面）**:
1. PySide6主窗口 (gui/main_window.py)
2. 检索界面 (gui/search_widget.py)
3. 配置界面 (gui/config_widget.py)
4. 进度监控界面 (gui/progress_widget.py)

**说明**:
- GUI开发可以在核心后端功能完成后进行
- 所有业务逻辑通过REST API暴露，GUI只是一个客户端
- 可以先使用curl、Postman或简单的命令行工具测试API
- GUI的开发不会阻塞核心功能的实现和测试

### 3.2 模块间依赖关系

```
┌─────────────────────────────────────────────────────────┐
│                    GUI层（可选，后期开发）                  │
│                    gui/main_window.py                    │
└────────────────────────┬────────────────────────────────┘
                         │ REST API调用
┌────────────────────────┴────────────────────────────────┐
│                      API服务层                            │
│                    api/app.py                            │
└────────────────────────┬────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ↓                ↓                ↓
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ 调度器        │  │ 检索引擎      │  │ 任务管理器    │
│ orchestrator │  │ smart_retrieval│ │ task_manager │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │
       ├─────────────────┼─────────────────┤
       │                 │                 │
       ↓                 ↓                 ↓
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ 媒体处理器    │  │ 向量化引擎    │  │ 文件监控器    │
│ processors/  │  │ embedding    │  │ file_monitor │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │
       └─────────────────┼─────────────────┘
                         │
        ┌────────────────┼────────────────┐
        ↓                ↓                ↓
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ 数据库管理器  │  │ 向量存储器    │  │ 配置管理器    │
│ database     │  │ vector_store │  │ config       │
└──────────────┘  └──────────────┘  └──────────────┘
```

## 4. 核心模块详细说明

### 4.1 API服务层 (src/api/)

#### 4.1.1 app.py - FastAPI应用主文件

**职责**: 
- 初始化FastAPI应用
- 配置CORS、中间件
- 注册路由
- 配置异常处理器

**核心功能**:
```python
# 主要接口
def create_app(config: Dict) -> FastAPI
def setup_middleware(app: FastAPI)
def register_routes(app: FastAPI)
def configure_exception_handlers(app: FastAPI)
```

**依赖关系**:
- 依赖: config_manager, logger_manager
- 被依赖: main.py

#### 4.1.2 routes/search.py - 检索接口

**职责**:
- 处理多模态检索请求
- 验证查询参数
- 调用智能检索引擎
- 格式化返回结果

**核心接口**:
```python
POST /api/search
- 输入: SearchRequest (query, filters, limit)
- 输出: SearchResponse (results, total, processing_time)
- 功能: 多模态混合检索
```

**依赖关系**:
- 依赖: smart_retrieval.SmartRetrievalEngine
- 被依赖: app.py

#### 4.1.3 routes/config.py - 配置接口

**职责**:
- 获取系统配置
- 更新配置参数
- 验证配置有效性
- 触发配置热重载

**核心接口**:
```python
GET /api/config
- 输出: 当前系统配置

PUT /api/config
- 输入: 配置键值对
- 输出: 更新结果
```

**依赖关系**:
- 依赖: config_manager.ConfigManager
- 被依赖: app.py

#### 4.1.4 routes/tasks.py - 任务管理接口

**职责**:
- 启动/停止处理任务
- 查询任务状态
- 获取任务进度
- 重试失败任务

**核心接口**:
```python
POST /api/tasks/start
- 输入: 任务类型、目录列表
- 输出: 任务ID

GET /api/tasks/{task_id}
- 输出: 任务详细信息

POST /api/tasks/{task_id}/stop
- 输出: 停止结果
```

**依赖关系**:
- 依赖: task_manager.TaskManager
- 被依赖: app.py

#### 4.1.5 routes/status.py - 状态查询接口

**职责**:
- 获取系统运行状态
- 查询资源使用情况
- 获取处理队列状态
- 健康检查

**核心接口**:
```python
GET /api/status
- 输出: 系统状态信息

GET /api/health
- 输出: 健康检查结果
```

**依赖关系**:
- 依赖: 各核心组件
- 被依赖: app.py

### 4.2 业务逻辑层 (src/business/)

#### 4.2.1 processing_orchestrator.py - 调度器

**职责**:
- 协调文件处理流程
- 策略路由（根据文件类型选择处理策略）
- 流程编排（预处理→向量化→存储）
- 状态管理和错误处理

**核心功能**:
```python
class ProcessingOrchestrator:
    async def submit_file(file_path: str) -> str
    async def process_file(file_id: str) -> Dict
    def select_processing_strategy(file_type: str) -> Dict
    async def coordinate_preprocessing(file_id: str)
    async def coordinate_vectorization(file_id: str)
    def handle_processing_error(file_id: str, error: Exception)
```

**处理策略决策**:
- 图像: 分辨率调整 → CLIP向量化 → 可选人脸检测
- 视频: 音频分离 → 场景检测切片 → CLIP向量化 → 音频处理
- 音频: 内容分类 → CLAP/Whisper向量化

**依赖关系**:
- 依赖: task_manager, media_processor, embedding_engine
- 被依赖: API层、UI层

#### 4.2.2 task_manager.py - 任务管理器

**职责**:
- 管理任务生命周期
- 维护任务队列（持久化到SQLite）
- 优先级调度
- 失败重试机制

**核心功能**:
```python
class TaskManager:
    def create_task(file_id: str, task_type: str) -> str
    def get_task(task_id: str) -> Task
    def update_task_status(task_id: str, status: str)
    def get_pending_tasks(limit: int) -> List[Task]
    def retry_failed_task(task_id: str)
    def get_task_statistics() -> Dict
```

**任务状态机**:
```
PENDING → PROCESSING → COMPLETED
                    ↓
                  FAILED → RETRY
```

**依赖关系**:
- 依赖: database_manager
- 被依赖: processing_orchestrator

#### 4.2.3 media_processor.py - 媒体处理器

**注意**: 在新的目录结构中，媒体处理器被拆分为独立的处理器模块 (src/processors/)，包括：
- base_processor.py: 处理器基类
- image_processor.py: 图像处理器
- video_processor.py: 视频处理器  
- audio_processor.py: 音频处理器

这里的说明适用于整个媒体处理器模块。

**职责**:
- 执行具体的媒体预处理
- 格式标准化和转换
- 分辨率降采样
- 视频场景检测和切片
- 音频分离和分类

**核心功能**:
```python
class MediaProcessor:
    async def process_image_async(file_path: str, task_id: str) -> Dict
    async def process_video_async(file_path: str, task_id: str) -> Dict
    async def process_audio_async(file_path: str, task_id: str) -> Dict
    
    # 视频处理
    def detect_scene_boundaries(video_path: str, threshold: float) -> List[float]
    def extract_audio_from_video(video_path: str) -> str
    def slice_video_by_scenes(video_path: str, boundaries: List[float]) -> List[Dict]
    
    # 音频处理
    def classify_audio_content(audio_path: str) -> str  # music/speech/mixed
    def extract_audio_features(audio_path: str) -> Dict
```

**处理参数**（默认值）:
- 图像目标分辨率: 720p (1280×720)
- 视频目标分辨率: 720p
- 视频目标帧率: 8 FPS
- 场景检测阈值: 0.15（严格模式）
- 最大切片时长: 5秒
- 每片段提取帧数: 1帧（中间帧）

**依赖关系**:
- 依赖: file_utils, video_utils, audio_utils
- 被依赖: processing_orchestrator

#### 4.2.4 embedding_engine.py - 向量化引擎

**职责**:
- 封装Infinity引擎
- 提供统一的向量化接口
- 管理多个AI模型（CLIP、CLAP、Whisper、FaceNet）
- 批处理优化

**核心功能**:
```python
class EmbeddingEngine:
    # 初始化
    def __init__(config: Dict)
    def load_models()
    
    # 图像向量化（CLIP）
    def embed_image(image_data: bytes) -> np.ndarray
    async def embed_image_async(image_data: bytes) -> np.ndarray
    def embed_image_batch(images: List[bytes]) -> List[np.ndarray]
    
    # 文本向量化
    def embed_text_for_visual(text: str) -> np.ndarray  # CLIP
    def embed_text_for_music(text: str) -> np.ndarray   # CLAP
    
    # 音频向量化
    def embed_audio_music(audio_data: bytes) -> np.ndarray  # CLAP
    async def embed_audio_music_async(audio_data: bytes) -> np.ndarray
    
    # 语音转录（Whisper）
    def transcribe_audio(audio_data: bytes) -> str
    async def transcribe_and_embed_async(audio_data: bytes) -> np.ndarray
    
    # 人脸向量化（FaceNet）
    def embed_face(face_data: bytes) -> np.ndarray
```

**模型配置**:
- CLIP: openai/clip-vit-base-patch32 (512维)
- CLAP: laion/clap-htsat-fused (512维)
- Whisper: openai/whisper-base
- FaceNet: facenet-pytorch (512维)

**依赖关系**:
- 依赖: infinity_manager, config_manager
- 被依赖: processing_orchestrator, smart_retrieval

#### 4.2.5 smart_retrieval.py - 智能检索引擎

**职责**:
- 识别查询类型（人名/音乐/语音/通用）
- 动态权重分配
- 执行多模态检索
- 结果融合和排序
- UUID换算（切片→源文件）

**核心功能**:
```python
class SmartRetrievalEngine:
    def smart_search(query: str, filters: Dict) -> List[Dict]
    def identify_query_type(query: str) -> str
    def calculate_dynamic_weights(query_type: str) -> Dict
    
    # 多模态检索
    async def search_text_to_visual(query: str, limit: int) -> List[Dict]
    async def search_text_to_audio(query: str, limit: int) -> List[Dict]
    async def search_image_to_visual(image: bytes, limit: int) -> List[Dict]
    async def search_audio_to_audio(audio: bytes, limit: int) -> List[Dict]
    
    # 结果处理
    def merge_multimodal_results(results: List[Dict]) -> List[Dict]
    def resolve_to_source_file(matched_id: str) -> str
    def resolve_video_location(segment_id: str, timestamp: float) -> Dict
```

**查询类型权重**:
| 查询类型 | 人脸权重 | 视觉权重 | CLAP权重 | Whisper权重 |
|---------|---------|---------|---------|------------|
| 人名查询 | 2.0 | 1.0 | 0.5 | 0.5 |
| 音乐查询 | 0.5 | 1.0 | 2.0 | 0.5 |
| 语音查询 | 0.5 | 1.0 | 0.5 | 2.0 |
| 通用查询 | 1.0 | 1.0 | 1.0 | 1.0 |

**依赖关系**:
- 依赖: embedding_engine, vector_store, database_manager
- 被依赖: API层

#### 4.2.6 face_manager.py - 人脸管理器

**职责**:
- 人脸检测和识别
- 人物信息管理
- 人脸向量存储
- 人名检索优化（分层检索）

**核心功能**:
```python
class FaceManager:
    def detect_faces(image: bytes) -> List[Dict]
    def recognize_face(face_data: bytes) -> Optional[str]
    def register_person(name: str, face_samples: List[bytes]) -> str
    def update_person(person_id: str, info: Dict)
    def search_by_person(person_id: str) -> List[str]  # 返回文件ID列表
```

**依赖关系**:
- 依赖: embedding_engine, vector_store, database_manager
- 被依赖: smart_retrieval

#### 4.2.7 file_monitor.py - 文件监控器

**注意**: 在新的目录结构中，file_monitor.py 位于 src/core/ 目录下，作为核心组件之一。

**职责**:
- 实时监控指定目录
- 检测文件变化（新增/删除/修改）
- 提取基础元数据
- 通知调度器处理

**核心功能**:
```python
class FileMonitor:
    def __init__(watch_directories: List[str])
    def start_monitoring()
    def stop_monitoring()
    
    # 事件处理
    def on_file_created(file_path: str)
    def on_file_deleted(file_path: str)
    def on_file_modified(file_path: str)
    
    # 元数据提取
    def extract_basic_metadata(file_path: str) -> Dict
```

**依赖关系**:
- 依赖: database_manager, file_utils
- 被依赖: processing_orchestrator

### 4.3 核心组件层 (src/core/)

**说明**: 核心组件层提供系统的基础功能，是最先需要实现的模块。

#### 4.3.1 config_manager.py - 配置管理器

**职责**:
- 加载和解析YAML配置文件
- 提供配置访问接口（支持点号路径）
- 配置验证
- 配置热重载
- 环境特定配置支持

**核心功能**:
```python
class ConfigManager:
    def __init__(config_path: str)
    def load_config() -> Dict
    def get(key_path: str, default: Any) -> Any
    def set(key_path: str, value: Any)
    def save()
    def reload()
    def validate_config() -> bool
```

**配置文件结构**:
- system: 系统基础配置
- file_monitoring: 文件监控配置
- media_processing: 媒体处理参数
- models: AI模型配置
- vector_storage: 向量存储配置
- database: 数据库配置
- task_management: 任务管理配置
- search: 检索配置
- api: API服务配置
- ui: UI配置

**依赖关系**:
- 依赖: 无
- 被依赖: 所有组件

### 4.4 数据存储层 (src/storage/)

**说明**: 数据存储层抽象化数据访问，为业务逻辑层提供统一的数据接口。

#### 4.4.1 database_manager.py - 数据库管理器

**职责**:
- SQLite数据库连接管理
- 提供统一的数据访问接口
- 事务管理
- 连接池管理
- 数据库维护（VACUUM、ANALYZE）

**核心功能**:
```python
class DatabaseManager:
    def __init__(db_path: str)
    def connect() -> Connection
    def execute(query: str, params: Tuple) -> Any
    def query(query: str, params: Tuple) -> List[Dict]
    def transaction() -> ContextManager
    
    # 文件操作
    def insert_file(file_info: Dict) -> str
    def get_file(file_id: str) -> Dict
    def update_file_status(file_id: str, status: str)
    def delete_file(file_id: str)
    def get_unprocessed_files() -> List[Dict]
    
    # 任务操作
    def create_task(task_info: Dict) -> str
    def get_task(task_id: str) -> Dict
    def update_task(task_id: str, updates: Dict)
    
    # 维护操作
    def vacuum()
    def analyze()
    def check_integrity() -> bool
```

**核心表结构**:
- files: 文件元数据
- video_segments: 视频切片信息
- file_relationships: 文件关联关系
- tasks: 处理任务
- persons: 人物信息
- file_faces: 人脸检测结果

**依赖关系**:
- 依赖: config_manager
- 被依赖: 所有业务组件

#### 4.4.2 vector_store.py - 向量存储器

**职责**:
- Milvus Lite向量数据库操作封装
- 向量集合管理
- 向量插入、检索、删除
- 批量操作优化
- 索引优化

**核心功能**:
```python
class VectorStore:
    def __init__(milvus_config: dict)
    def connect() -> MilvusClient
    
    # 集合管理
    def create_collection(name: str, vector_size: int, distance: str)
    def delete_collection(name: str)
    def list_collections() -> List[str]
    
    # 向量操作
    def insert_vector(collection: str, vector: np.ndarray, payload: Dict) -> str
    def insert_vectors_batch(collection: str, vectors: List, payloads: List)
    def delete_vector(collection: str, vector_id: str)
    def delete_vectors_by_filter(collection: str, filter: Dict)
    
    # 检索操作
    def search_vectors(collection: str, query_vector: np.ndarray, 
                      limit: int, filter: Dict) -> List[Dict]
    def search_batch(collection: str, query_vectors: List, limit: int) -> List[List[Dict]]
```

**向量集合设计**:
- image_vectors: 图像向量（512维，Cosine）
- video_vectors: 视频帧向量（512维，Cosine）
- audio_vectors: 音频向量（512维，Cosine）
- face_vectors: 人脸向量（512维，Cosine）

**依赖关系**:
- 依赖: config_manager
- 被依赖: embedding_engine, smart_retrieval

#### 4.3.2 logger.py - 日志系统

**注意**: 在新的目录结构中，日志系统简化为 logger.py，位于 src/core/ 目录下。

**职责**:
- 配置多级别日志系统
- 管理日志处理器（控制台、文件、错误文件）
- 日志轮转
- 组件特定日志级别

**核心功能**:
```python
class LoggerManager:
    def __init__(config: Dict)
    def setup_logging()
    def get_logger(name: str) -> logging.Logger
    def set_level(logger_name: str, level: str)
    def add_handler(handler: logging.Handler)
```

**日志级别**:
- DEBUG: 详细调试信息
- INFO: 关键操作记录
- WARNING: 潜在问题警告
- ERROR: 错误信息
- CRITICAL: 致命错误

**日志处理器**:
- console: 控制台输出（INFO级别）
- file: 详细日志文件（DEBUG级别，10MB轮转）
- error_file: 错误日志文件（ERROR级别，10MB轮转）
- performance: 性能日志（INFO级别，5MB轮转）

**依赖关系**:
- 依赖: config_manager
- 被依赖: 所有组件

#### 4.2.8 Infinity引擎管理

**注意**: 在新的目录结构中，Infinity引擎的管理集成在 embedding_engine.py 中，不再作为独立模块。

**职责**:
- 管理Infinity引擎生命周期
- 模型加载和卸载
- 后端选择（CUDA/CPU/OpenVINO）
- 批处理优化
- 模型预热

**核心功能**:
```python
class InfinityManager:
    def __init__(config: Dict)
    def initialize_engine()
    def load_model(model_type: str, model_path: str)
    def unload_model(model_type: str)
    def get_model(model_type: str) -> Model
    def select_backend() -> str
    def warmup_models()
```

**支持的模型类型**:
- clip: CLIP模型（文本-图像）
- clap: CLAP模型（文本-音频）
- whisper: Whisper模型（语音-文本）
- facenet: FaceNet模型（人脸识别）

**依赖关系**:
- 依赖: config_manager
- 被依赖: embedding_engine

#### 4.3.4 文件类型检测

**说明**: 文件类型检测功能集成在 file_monitor.py 中，不再作为独立模块。

**核心功能**:
- 基于扩展名检测文件类型
- 验证文件有效性
- 支持的文件类型：
  - 图像: jpg, jpeg, png, bmp, gif, webp
  - 视频: mp4, avi, mov, mkv, flv, wmv
  - 音频: mp3, wav, flac, aac, ogg, m4a

#### 4.3.3 exceptions.py - 自定义异常

**职责**: 定义系统的自定义异常类

**核心异常类**:
```python
class MSearchException(Exception):
    """基础异常类"""
    pass

class FileProcessingError(MSearchException):
    """文件处理错误"""
    pass

class VectorizationError(MSearchException):
    """向量化错误"""
    pass

class DatabaseError(MSearchException):
    """数据库错误"""
    pass

class ConfigurationError(MSearchException):
    """配置错误"""
    pass
```

**依赖关系**:
- 依赖: 无
- 被依赖: 所有组件

### 4.5 媒体处理器层 (src/processors/)

**说明**: 媒体处理器专门负责不同类型文件的预处理，采用基类+子类的设计模式。

#### 4.5.1 base_processor.py - 处理器基类

**职责**: 定义处理器的通用接口和共享功能

**核心接口**:
```python
class BaseProcessor:
    def __init__(config: Dict)
    async def process_async(file_path: str, task_id: str) -> Dict
    def validate_file(file_path: str) -> bool
    def extract_metadata(file_path: str) -> Dict
```

#### 4.5.2 image_processor.py - 图像处理器

**职责**: 处理图像文件的预处理

**核心功能**: 参见 4.2.3 节中的图像处理部分

#### 4.5.3 video_processor.py - 视频处理器

**职责**: 处理视频文件的预处理

**核心功能**: 参见 4.2.3 节中的视频处理部分

#### 4.5.4 audio_processor.py - 音频处理器

**职责**: 处理音频文件的预处理

**核心功能**: 参见 4.2.3 节中的音频处理部分

### 4.6 数据模型层 (api/models/)

**说明**: 数据模型层定义API的请求和响应模型，使用Pydantic进行数据验证。

#### 4.6.1 request.py - 请求模型

**职责**: 定义文件相关的数据结构

**核心类**:
```python
@dataclass
class FileMetadata:
    id: str                    # UUID
    file_path: str
    file_name: str
    file_type: str             # image/video/audio
    file_category: str         # source/processed/derived
    source_file_id: Optional[str]
    file_size: int
    file_hash: str
    created_at: datetime
    modified_at: datetime
    indexed_at: Optional[datetime]
    status: str                # pending/processing/completed/failed
    can_delete: bool

@dataclass
class VideoSegment:
    segment_id: str
    file_uuid: str
    segment_index: int
    start_time: float
    end_time: float
    duration: float
    scene_boundary: bool
    has_audio: bool
    frame_count: int
```

#### 4.6.2 response.py - 响应模型

**职责**: 定义任务相关的数据结构

**核心类**:
```python
@dataclass
class Task:
    id: str
    file_id: str
    task_type: str             # preprocess/vectorize
    status: str                # pending/processing/completed/failed
    progress: float            # 0-100
    priority: int
    retry_count: int
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
```

**说明**: 在新的架构中，数据模型主要用于API层的请求和响应验证。业务逻辑层使用字典和数据类来传递数据。

### 4.7 GUI层 (src/gui/) - 低优先级

**重要说明**: 
- GUI开发优先级最低，应在核心后端功能完成后再进行
- 所有业务逻辑通过REST API暴露，GUI只是一个客户端
- 可以先使用curl、Postman或命令行工具测试API
- GUI的开发不会阻塞核心功能的实现和测试

#### 4.7.1 main_window.py - 主窗口

**职责**: 应用主窗口和生命周期管理

**核心功能**:
- 窗口初始化和布局
- 系统托盘集成
- 子窗口管理
- 应用退出处理

#### 4.7.2 search_widget.py - 检索界面

**职责**: 多模态检索输入界面

**核心功能**:
- 文本输入框
- 图像/音频文件上传
- 拖拽文件支持
- 调用 /api/search 接口

#### 4.7.3 config_widget.py - 配置界面

**职责**: 系统配置管理界面

**核心功能**:
- 监控目录管理
- 模型选择
- 性能参数调整
- 调用 /api/config 接口

#### 4.7.4 progress_widget.py - 进度监控界面

**职责**: 处理进度实时监控

**核心功能**:
- 任务队列状态显示
- 资源使用情况显示
- 日志查看
- 调用 /api/status 接口
