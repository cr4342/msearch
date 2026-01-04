# msearch - 多模态检索系统

msearch 是一款跨平台的多模态检索系统，采用单体架构设计，专注于单机桌面应用场景。系统使用 michaelfeil/infinity 作为多模型服务引擎，支持文本、图像、视频、音频四种模态的精准检索。

## 核心特性

- **智能检索**: 无需手动整理、无需添加标签即可实现智能检索
- **跨模态搜索**: 支持用任意模态（文本、图像、音频）检索其他模态内容
- **高精度定位**: 支持毫秒级时间戳精确定位，时间戳精度±2秒要求
- **零配置**: 素材无需整理、无需标签
- **高性能本地推理**: 利用Infinity Python-native模式实现高效向量化
- **单体架构**: 简洁清晰的模块划分，易于理解和维护

## 技术架构

### 3大核心块

1. **核心块1: 任务管理器 (TaskManager)**
   - 为用户提供直观的任务进度展示和手动管理界面
   - 统一管理所有文件处理任务
   - 支持全量扫描、增量扫描、重新向量化等手动操作

2. **核心块2: 向量化引擎 (EmbeddingEngine)**
   - 专注于AI模型管理和向量化处理
   - 提供统一的向量化接口
   - 集成CLIP、CLAP、Whisper等多模态模型

3. **核心块3: 向量存储 (VectorStore)**
   - 专注于 Milvus Lite 向量数据库的操作和管理
   - 提供向量集合管理、CRUD操作、相似度检索等功能

### 辅助组件

- **检索引擎 (SearchEngine)**: 实现多模态检索功能
- **数据库管理器 (DatabaseManager)**: SQLite数据库操作
- **配置管理器 (ConfigManager)**: YAML配置管理
- **Infinity管理器 (InfinityManager)**: AI模型服务管理

## 快速开始

### 环境要求

- Python 3.8+
- 支持CUDA的GPU（推荐，用于加速AI推理）

### 安装依赖

```bash
pip install -r requirements.txt
```

### 启动应用

```bash
python src/main.py
```

## 架构图

```
用户界面 <---> 任务管理器 <---> 媒体处理器
                ↓              ↓
            检索引擎 <---> 向量化引擎 <---> Infinity管理器
                ↓              ↓              ↓
            数据库管理器 <--> 向量存储器 <---> Milvus Lite
                                        ↓
                                    SQLite
```

## 项目结构

```
msearch/
├── config/                    # 配置文件
│   └── config.yml
├── data/                      # 数据目录
│   └── models/                # AI模型文件
├── src/                       # 源代码
│   ├── main.py               # 应用入口
│   ├── core/                 # 3大核心块
│   │   ├── task_manager.py   # 任务管理器
│   │   ├── embedding_engine.py # 向量化引擎
│   │   └── vector_store.py   # 向量存储
│   └── components/           # 辅助组件
│       ├── database_manager.py
│       ├── config_manager.py
│       ├── search_engine.py
│       └── infinity_manager.py
├── tests/                     # 测试
└── docs/                      # 文档
```

## 工作流程

### 文件处理与向量化

1. 文件监控器检测到新文件
2. 任务管理器创建处理任务
3. 向量化引擎进行AI向量化
4. 向量存储保存向量和元数据

### 检索流程

1. 用户输入查询（文本/图像/音频）
2. 向量化引擎向量化查询
3. 向量存储执行相似度检索
4. 检索引擎返回排序结果

## 配置

系统使用 `config/config.yml` 进行配置，支持以下主要配置项：

- `system`: 系统级别配置
- `models`: AI模型配置
- `database`: 数据库配置
- `processing`: 媒体处理配置
- `retry`: 重试策略配置

## 许可证

[MIT License](LICENSE)