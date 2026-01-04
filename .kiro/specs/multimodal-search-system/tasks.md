# 实现计划 (简化架构版)

## 概述

本实现计划基于简化后的单体架构设计，专注于单机桌面应用场景。

## 架构简化要点

1. **任务管理器职责明确**: 专注于为用户提供直观的任务进度展示和手动管理界面
2. **向量存储专业化**: `vector_store.py` 专注于 Milvus Lite 向量数据库操作
3. **模型文件存储**: `data/models/` 目录存放 AI 模型文件（CLIP/CLAP/Whisper/FaceNet）
4. **简化目录结构**: 
   - `src/core/` - 3大核心块（任务管理器、向量化引擎、向量存储）
   - `src/components/` - 辅助组件
   - `src/ui/` - 用户界面

## 开发策略

按照以下顺序进行增量开发：
1. **阶段一：基础架构** - 搭建简化的项目结构、配置管理、日志系统
2. **阶段二：核心存储** - 实现数据库管理器和向量存储器（直接使用 Milvus Lite）
3. **阶段三：索引引擎** - 实现完整的文件处理到向量化流程
4. **阶段四：检索引擎** - 实现多模态检索功能
5. **阶段五：用户界面** - 实现 PySide6 界面
6. **阶段六：优化与测试** - 性能优化和完整测试

---

## 阶段一：基础架构搭建

### 1.1 简化项目目录结构
- [ ] 1.1.1 创建简化的目录结构
  - 创建 `src/core/`、`src/components/`、`src/ui/` 目录
  - 创建 `data/models/` 目录用于存放AI模型文件
  - 初始化所有 `__init__.py` 文件
  - _需求映射: 2.3_

- [ ] 1.1.2 创建配置文件
  - 创建 `config/config.yml` 主配置文件
  - 包含系统、监控、处理、模型、数据库配置
  - _需求映射: 6.1_

### 1.2 配置管理器实现
- [ ] 1.2.1 实现 `src/components/config_manager.py`
  - 支持 YAML 配置文件加载
  - 支持配置热重载
  - 支持配置验证
  - _需求映射: 6.1_

### 1.3 日志系统实现
- [ ] 1.3.1 实现 `src/components/logging_config.py`
  - 配置多级别日志（DEBUG/INFO/WARNING/ERROR）
  - 配置日志轮转和归档
  - 支持按模块分离日志
  - _需求映射: 7.1, 7.2, 7.3_

---

## 阶段二：核心存储层

### 2.1 数据库管理器实现
- [ ] 2.1.1 实现 `src/components/database_manager.py`
  - 直接使用 SQLite API
  - 实现文件元数据 CRUD 操作
  - 实现任务状态管理
  - 实现配置持久化
  - _需求映射: 3.4, 8.2_

### 2.2 向量存储器实现
- [ ] 2.2.1 实现 `src/core/vector_store.py`
  - 专注于 Milvus Lite 向量数据库操作
  - 实现向量集合管理（创建/删除/检查）
  - 实现向量 CRUD 操作
  - 实现批量向量插入
  - 实现相似度检索
  - _需求映射: 3.3, 13.2, 13.3_

### 2.3 创建数据库 Schema
- [ ] 2.3.1 设计数据库表结构
  - `files` 表：文件元数据
  - `video_segments` 表：视频切片信息
  - `tasks` 表：处理任务
  - `persons` 表：人物信息
  - `file_faces` 表：人脸检测结果
  - _需求映射: 3.4_

---

## 阶段三：索引引擎

### 3.1 Infinity 管理器实现
- [ ] 3.1.1 实现 `src/components/infinity_manager.py`
  - 初始化 AsyncEngineArray
  - 加载 CLIP/CLAP/Whisper 模型（从 data/models/ 目录）
  - 实现模型预热和 GPU 内存管理
  - 支持 CPU/GPU 自动切换
  - _需求映射: 1.3.4, 1.3.5_

### 3.2 向量化引擎实现
- [ ] 3.2.1 实现 `src/core/embedding_engine.py`
  - `embed_image_from_path(file_path)` - 从文件路径CLIP图像向量化
  - `embed_video_frame_from_path(file_path)` - 从文件路径CLIP视频帧向量化
  - `embed_audio_from_path(file_path)` - 从文件路径CLAP音频向量化
  - `embed_text_for_visual(text)` - CLIP文本向量化（用于视觉检索）
  - `embed_text_for_music(text)` - CLAP文本向量化（用于音乐检索）
  - `transcribe_audio_from_path(file_path)` - 从文件路径Whisper语音转录
  - `transcribe_and_embed_from_path(file_path)` - 从文件路径转录并向量化
  - `embed_face_from_path(file_path)` - 从文件路径人脸向量化
  - _需求映射: 3.2, 1.3.2, 1.3.3_

### 3.3 媒体处理器实现
- [ ] 3.3.1 实现 `src/components/media_processor.py`
  - 图像预处理：分辨率调整、格式转换
  - 视频预处理：场景检测、切片、音频分离
  - 音频预处理：格式转换、内容分类
  - 使用 inaSpeechSegmenter 进行音频分类
  - _需求映射: 2.4.12, 2.13_

### 3.4 文件监控器实现
- [ ] 3.4.1 实现 `src/components/file_monitor.py`
  - 使用 Watchdog 监控目录
  - 实现文件事件监听（创建/修改/删除）
  - 实现文件类型过滤
  - 实现防抖处理
  - _需求映射: 2.4.1, 4.1_

### 3.5 任务管理器实现
- [ ] 3.5.1 实现 `src/core/task_manager.py`
  - 为用户提供直观的任务进度展示
  - 支持用户手动启动、暂停、取消任务
  - 实现任务状态管理和进度跟踪
  - 支持手动操作：全量扫描、增量扫描、重新向量化
  - 实现任务队列管理
  - 实现失败重试机制
  - _需求映射: 2.4.3, 4.1_

---

## 阶段四：检索引擎

### 4.1 检索引擎核心实现
- [ ] 4.1.1 实现 `src/components/search_engine.py`
  - `search_by_text()` - 文本检索
  - `search_by_image_from_path()` - 从文件路径图像检索
  - `search_by_audio_from_path()` - 从文件路径音频检索
  - `hybrid_search()` - 混合检索
  - 实现查询类型识别
  - 实现动态权重分配
  - 实现结果融合和排序
  - _需求映射: 2.4.6, 4.2_

### 4.2 人脸管理器实现
- [ ] 4.2.1 实现 `src/components/face_manager.py`
  - 人脸注册功能
  - 人脸检测功能
  - 人脸匹配功能
  - 按人名检索功能
  - _需求映射: 2.4.9_

### 4.3 视频时序定位实现
- [ ] 4.3.1 实现时序定位功能
  - 返回精确时间戳（±2秒）
  - 支持多片段结果排序
  - 实现时间戳计算和验证
  - _需求映射: 2.4.13, 5.1, 5.2_

---

## 阶段五：用户界面

### 5.1 PySide6 主窗口实现
- [ ] 5.1.1 实现 `src/ui/main_window.py`
  - 主窗口布局
  - 系统托盘集成
  - 应用生命周期管理
  - _需求映射: 2.1_

### 5.2 检索界面实现
- [ ] 5.2.1 实现 `src/ui/search_widget.py`
  - 文本检索输入框
  - 图像/音频拖拽上传
  - 结果网格展示
  - 缩略图预览
  - 结果过滤和排序
  - _需求映射: 2.1_

### 5.3 配置界面实现
- [ ] 5.3.1 实现 `src/ui/config_widget.py`
  - 监控目录管理
  - 模型配置选择
  - 性能参数调优
  - _需求映射: 2.4.16_

### 5.4 任务管理控制面板实现
- [ ] 5.4.1 实现 `src/ui/task_control_widget.py`
  - 任务进度实时展示
  - 手动启动/暂停/取消任务按钮
  - 全量扫描和增量扫描控制
  - 处理历史查看
  - _需求映射: 2.4.3, 2.4.15_

---

## 阶段六：优化与测试

### 6.1 性能优化
- [ ] 6.1.1 批处理优化
  - 批量向量插入
  - 批量文件处理
  - _需求映射: 1.3.4_

- [ ] 6.1.2 缓存优化
  - 查询结果缓存
  - 模型推理缓存
  - _需求映射: 1.3.4_

### 6.2 测试实现
- [ ] 6.2.1 单元测试
  - `tests/test_task_manager.py`
  - `tests/test_embedding_engine.py`
  - `tests/test_vector_store.py`
  - `tests/test_media_processor.py`
  - `tests/test_config_manager.py`
  - `tests/test_database_manager.py`
  - `tests/test_search_engine.py`

- [ ] 6.2.2 集成测试
  - `tests/test_timestamp_accuracy.py` - 时间戳精度测试
  - `tests/test_multimodal_fusion.py` - 多模态融合测试

### 6.3 文档完善
- [ ] 6.3.1 更新文档
  - 更新 `docs/architecture.md` 匹配简化架构
  - 更新 `docs/api_documentation.md`
  - 更新 `docs/user_manual.md`
  - _需求映射: 2.2_

---

## 里程碑

- **M1**: 完成阶段一至阶段二 - 基础架构和存储层就绪
- **M2**: 完成阶段三 - 任务管理器和向量化引擎可用，文件可被处理和向量化
- **M3**: 完成阶段四 - 检索引擎可用，支持多模态检索
- **M4**: 完成阶段五 - UI 可用，用户可通过界面操作和管理任务
- **M5**: 完成阶段六 - 系统优化完成，测试通过，可正式发布

## 简化架构对比

| 原概念 | 简化后 | 说明 |
|-------|--------|------|
| 复杂的管理器层次 | `TaskManager` | 专注用户任务进度展示和手动管理 |
| `VectorStorageAdapter` | `VectorStore` | 专注 Milvus Lite 向量数据库操作 |
| `src/models/` 数据模型 | `data/models/` AI模型文件 | 存放 CLIP/CLAP/Whisper/FaceNet 模型文件 |
| 微服务架构 | 3核心块架构 | TaskManager + EmbeddingEngine + VectorStore |
| 复杂目录结构 | 简化结构 | core/ + components/ + ui/ |