# msearch 项目上下文文档

## 项目概述

msearch 是一款跨平台的多模态检索系统，采用单体架构设计，专注于单机桌面应用场景。系统使用 michaelfeil/infinity 作为多模型服务引擎，支持文本、图像、视频、音频四种模态的精准检索。

### 核心特性

- **智能检索**: 无需手动整理、无需添加标签即可实现智能检索
- **跨模态搜索**: 支持用任意模态（文本、图像、音频）检索其他模态内容
- **时序定位**: 支持视频片段级时序定位，时间戳精度±5秒
- **零配置**: 素材无需整理、无需标签
- **高性能本地推理**: 利用Infinity Python-native模式实现高效向量化
- **单体架构**: 模块化设计，易于理解和维护

### 技术栈

- **语言**: Python 3.8+
- **AI模型框架**: PyTorch, Transformers
- **向量化引擎**: infinity-emb[all]
- **向量数据库**: Milvus Lite
- **关系数据库**: SQLite
- **Web框架**: FastAPI (用于API服务)
- **GUI**: PySide6 (可选，用于桌面界面)
- **媒体处理**: OpenCV, FFmpeg, Librosa
- **文件监控**: Watchdog

## 架构设计

### 简化架构概述

基于实际项目状态和分析，推荐采用以下简化架构：

#### 1. 核心服务层（5个核心模块）
```
┌─────────────────────────────────────────────────────────┐
│                   主应用程序 (main.py)                    │
├─────────────────────────────────────────────────────────┤
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐   │
│  │ 文件服务 │  │ 向量化  │  │ 存储服务 │  │ 检索服务 │   │
│  │  (合并) │  │  服务   │  │  (合并) │  │         │   │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘   │
└─────────────────────────────────────────────────────────┘
```

#### 2. 实际实现模块（当前状态）
```
src/
├── main.py              # 应用入口
├── api_server.py        # FastAPI服务
├── core/                # 核心功能模块
│   ├── task_manager.py       # 任务管理
│   ├── embedding_engine.py   # 向量化引擎（统一调用Infinity和CLIP4Clip）
│   ├── vector_store.py       # 向量存储（Milvus Lite操作）
│   ├── config_manager.py     # 配置管理
│   ├── infinity_manager.py   # Infinity引擎封装
│   └── ... 其他辅助模块
├── components/          # 辅助组件
│   ├── database_manager.py   # SQLite数据库管理
│   └── search_engine.py      # 多模态检索引擎
├── ui/                  # PySide6用户界面
└── utils/               # 工具类
```

### 模块职责说明

#### 核心模块
1. **任务管理器 (TaskManager)**
   - 负责任务进度跟踪和状态管理
   - 支持手动操作（全量扫描、增量扫描、重新向量化）
   - 使用内存队列管理任务（简化设计）

2. **向量化引擎 (EmbeddingEngine)**
   - 统一管理所有AI模型调用
   - 集成Infinity引擎（CLIP/CLAP/Whisper）
   - 直接调用CLIP4Clip进行视频片段级向量化
   - 提供统一的向量化接口

3. **向量存储 (VectorStore)**
   - 管理Milvus Lite向量数据库
   - 负责向量CRUD操作和相似度检索
   - 与SQLite元数据库协同工作

#### 辅助模块
4. **配置管理器 (ConfigManager)**
   - 管理YAML配置文件
   - 支持硬件自适应配置生成
   - 提供配置验证和热重载

5. **检索引擎 (SearchEngine)**
   - 实现多模态检索功能
   - 支持文本、图像、音频查询
   - 融合不同模态的检索结果
   - 提供结果排序和丰富功能

#### 扩展模块（根据需求可选）
- **批量处理器 (BatchProcessor)**: 批量任务处理优化
- **缓存管理器 (CacheManager)**: 临时数据和模型缓存
- **性能监控器 (PerformanceMonitor)**: 系统性能监控
- **文件类型检测器 (FileTypeDetector)**: 智能媒体文件识别

### 架构优势
- **简化维护**: 模块职责清晰，减少依赖复杂度
- **快速开发**: 避免过度设计，聚焦核心功能
- **易于扩展**: 插件式设计支持功能扩展
- **跨平台**: 全Python实现，支持Windows/macOS/Linux

## 项目结构

```
msearch/
├── config/                    # 配置文件
│   └── config.yml            # 主配置文件
├── data/                      # 数据目录
│   ├── cache/                 # 缓存数据
│   ├── database/              # 数据库文件（SQLite + Milvus Lite）
│   ├── models/                # AI模型文件
│   └── logs/                  # 日志文件
├── docs/                      # 项目文档
│   ├── api_documentation.md   # API文档
│   ├── architecture.md        # 架构设计
│   ├── INSTALL.md             # 安装指南
│   ├── user_manual.md         # 用户手册
│   └── technical_implementation.md # 技术实现
├── logs/                      # 运行时日志
├── scripts/                   # 实用脚本
│   ├── install.sh             # Linux安装脚本
│   ├── install_windows.py     # Windows安装脚本（GBK编码）
│   ├── download_models_only.py # 模型下载脚本
│   ├── start_all.sh           # 启动脚本
│   ├── stop_all.sh            # 停止脚本
│   └── hardware_analysis.py   # 硬件分析脚本
├── src/                       # 源代码
│   ├── main.py               # 应用入口
│   ├── api_server.py         # FastAPI服务
│   ├── core/                 # 核心模块
│   ├── components/           # 辅助组件
│   ├── ui/                   # 用户界面（PySide6）
│   └── utils/                # 工具类
├── storage/                  # 存储目录（Milvus集合数据）
├── tests/                    # 测试代码
├── webui/                    # Web界面（开发测试用）
│   └── index.html
└── requirements.txt          # Python依赖
```

## 开发约定

### 代码规范
- 遵循Python PEP 8编码规范
- 使用类型注解提高代码可读性
- 所有异步函数使用`async/await`
- 模块化设计，单一职责原则

### 配置管理
- 使用YAML格式配置文件
- 配置驱动设计，无硬编码参数
- 支持环境变量覆盖
- 配置热重载支持

### 错误处理
- 使用Python异常类进行错误处理
- 提供友好的错误消息
- 详细的错误日志记录
- 支持错误重试机制

### 日志系统
- 多级别日志管理（DEBUG/INFO/WARNING/ERROR/CRITICAL）
- 分类存储（主日志、错误日志、性能日志）
- 自动日志轮转，防止日志文件过大
- 结构化日志便于分析

## 构建和运行

### 环境要求
- **Python**: 3.8+
- **内存**: 最低8GB，推荐16GB+
- **GPU**: 支持CUDA的GPU（推荐，用于加速AI推理）
- **磁盘空间**: 至少10GB（用于模型文件和数据）

### 安装依赖
```bash
# 使用pip安装
pip install -r requirements.txt

# 使用uv加速安装（推荐）
pip install uv
uv pip install -r requirements.txt
```

### 启动应用
```bash
# 启动完整应用（包含UI和后台服务）
python src/main.py

# 仅启动API服务
python src/api_server.py

# 使用脚本启动
bash scripts/start_all.sh
```

### 配置文件说明
系统使用`config/config.yml`进行配置，主要配置项：

```yaml
system:
  log_level: INFO
  max_workers: 4

monitoring:
  directories: []  # 监控目录列表
  check_interval: 5  # 检查间隔（秒）

processing:
  image:
    max_resolution: 2048  # 图像最大分辨率
  video:
    target_resolution: 720  # 视频目标分辨率
    max_segment_duration: 5  # 最大片段时长（秒）

models:
  clip_model: openai/clip-vit-base-patch32
  clap_model: laion/clap-htsat-fused
  whisper_model: openai/whisper-base
  clip4clip_model: clip4clip/ViT-B-16
```

## 工作流程

### 1. 文件处理与向量化流程
```
文件监控 → 任务创建 → 媒体预处理 → 向量化 → 存储
    │           │           │          │        │
 (Watchdog) (TaskManager) (MediaProcessor) (EmbeddingEngine) (VectorStore)
```

**详细步骤**：
1. **文件监控**: Watchdog实时监控配置目录，检测新文件
2. **任务创建**: TaskManager创建处理任务，跟踪进度状态
3. **媒体预处理**: 
   - 图像：分辨率调整，格式转换
   - 视频：场景检测切片，音频分离
   - 音频：格式转换，内容分类
4. **向量化**: EmbeddingEngine调用相应模型生成向量
5. **存储**: VectorStore保存向量，DatabaseManager保存元数据

### 2. 检索流程
```
用户查询 → 查询向量化 → 向量检索 → 结果融合 → 返回结果
    │           │           │          │          │
 (UI/API) (EmbeddingEngine) (VectorStore) (SearchEngine) (UI/API)
```

**详细步骤**：
1. **用户查询**: 接收文本、图像或音频查询
2. **查询向量化**: 使用相应模型将查询转换为向量
3. **向量检索**: 在Milvus Lite中执行相似度搜索
4. **结果融合**: SearchEngine融合多模态结果，排序
5. **返回结果**: 返回包含时间戳、相似度分数的结果

## 关键组件实现状态

### 已实现功能
- ✅ **基础架构**: 主应用框架、配置管理、日志系统
- ✅ **向量化引擎**: Infinity引擎集成、基础模型调用
- ✅ **存储系统**: SQLite元数据管理、Milvus Lite向量存储
- ✅ **任务管理**: 基础任务跟踪和状态管理
- ✅ **API服务**: FastAPI基础接口

### 待完善功能
- 🔄 **文件监控**: Watchdog集成需要完善
- 🔄 **视频处理**: CLIP4Clip视频片段级向量化
- 🔄 **UI界面**: PySide6用户界面需要完善
- 🔄 **硬件自适应**: 自动硬件检测和模型选择

### 性能要求
- **检索响应**: ≤2秒返回前20个结果
- **视频定位精度**: ±5秒（CLIP4Clip片段级）
- **并发处理**: 支持4+个并发任务
- **内存使用**: 模型加载后≤4GB内存占用

## 开发指南

### 添加新功能
1. **确定需求**: 参考`docs/requirements.md`需求文档
2. **设计接口**: 保持模块化，定义清晰接口
3. **实现功能**: 遵循现有代码风格和规范
4. **编写测试**: 添加单元测试和集成测试
5. **更新文档**: 更新相关文档和示例

### 调试技巧
```bash
# 启用调试日志
python src/main.py --log-level DEBUG

# 运行特定测试
pytest tests/test_task_manager.py -v

# 检查配置
python -c "from src.core.config_manager import ConfigManager; cm = ConfigManager('config/config.yml'); print(cm.config)"
```

### 性能优化
- **批量处理**: 使用BatchProcessor进行批量向量化
- **缓存策略**: 使用CacheManager缓存常用数据
- **异步处理**: 所有I/O操作使用异步处理
- **资源管理**: 监控GPU/CPU使用，动态调整批处理大小

## 部署说明

### 桌面应用打包
```bash
# 使用Nuitka打包（跨平台）
python -m nuitka --standalone --onefile src/main.py

# 使用PyInstaller打包
pyinstaller --onefile --windowed src/main.py
```

### 模型部署
```bash
# 下载所有AI模型
python scripts/download_models_only.py

# 国内用户使用镜像
export HF_ENDPOINT=https://hf-mirror.com
export HF_HUB_ENABLE_HF_TRANSFER=1
```

### 数据备份
```bash
# 备份数据库
cp data/database/msearch.db backup/msearch_$(date +%Y%m%d).db

# 备份配置
cp config/config.yml backup/config_$(date +%Y%m%d).yml
```

## 故障排除

### 常见问题
1. **模型加载失败**
   - 检查网络连接
   - 验证模型路径权限
   - 使用国内镜像源

2. **内存不足**
   - 降低批处理大小
   - 使用轻量级模型
   - 增加系统内存

3. **GPU相关错误**
   - 检查CUDA驱动版本
   - 验证GPU内存是否充足
   - 降级到CPU模式

### 日志分析
```bash
# 查看错误日志
tail -f logs/error.log

# 查看性能日志
tail -f logs/performance.log

# 搜索特定错误
grep -r "ERROR" logs/
```

## 扩展开发

### 添加新模型
1. 在`EmbeddingEngine`中添加模型调用接口
2. 更新配置管理器支持新模型配置
3. 添加对应的测试用例
4. 更新文档说明

### 添加新文件类型
1. 在`FileTypeDetector`中添加类型识别
2. 在`MediaProcessor`中添加相应处理逻辑
3. 更新数据库schema支持新类型
4. 测试完整处理流程

### 插件系统（未来扩展）
- 支持动态加载功能插件
- 插件生命周期管理
- 插件间通信机制
- 插件配置管理

## 版本信息

### 当前版本
- **架构版本**: 2.3（简化单体架构）
- **Python版本**: 3.8+
- **核心模型**: CLIP、CLAP、Whisper、CLIP4Clip
- **数据库**: SQLite + Milvus Lite

### 更新历史
- **2026-01-04**: 简化架构设计，聚焦核心功能
- **2026-01-04**: 更新项目结构，优化模块划分
- **2025-01-04**: 初始版本，微服务架构

## 贡献指南

请参考`docs/CONTRIBUTING.md`了解详细的贡献指南，包括：
- 代码提交规范
- 测试要求
- 文档更新
- 问题反馈流程

## 许可证

本项目采用MIT许可证，详见LICENSE文件。

---
*最后更新: 2026-01-04*
*基于实际项目状态和分析优化的上下文文档*