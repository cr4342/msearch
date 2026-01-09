# msearch 多模态检索系统开发任务列表

## 版本 v0.1 - 基于3核心块架构

根据最新的设计文档，项目架构已简化为3个核心块，所有开发任务将围绕这3个核心块展开。系统采用硬件自适应模型策略，仅使用apple/mobileclip、vidore/colSmol-500M和vidore/colqwen2.5-v0.2进行图像/视频向量化。

### 开发顺序说明
1. **核心功能开发**：优先完成3大核心块的实现
2. **辅助组件开发**：完成配置管理、日志系统等辅助组件
3. **API接口开发**：提供RESTful API供WebUI调用
4. **测试与功能验证**：通过完整的测试套件验证所有功能
5. **部署与打包**：实现部署脚本和Nuitka打包
6. **文档编写**：完善各类文档
7. **WebUI快速验证**：基于现有WebUI界面快速验证功能
8. **PySide6桌面UI**：在完成所有功能验证后，最后开发桌面版用户界面

### 核心块1: 任务管理器 (TaskManager)
- [x] TaskManager基础类实现
- [x] 任务状态管理（PENDING, PROCESSING, COMPLETED, FAILED, RETRY）
- [x] 任务队列管理
- [x] 手动操作支持（全量扫描、增量扫描、重新向量化）
- [x] 任务进度展示
- [x] FileMonitor文件监控组件
- [x] MediaProcessor媒体处理组件
- [x] 任务持久化存储（SQLite）
- [x] 失败重试机制
- [x] 健康检查端点
- [x] 统一错误码体系

### 核心块2: 向量化引擎 (EmbeddingEngine)
- [x] EmbeddingEngine基础类实现
- [x] 图像/视频向量化模型集成
  - [x] apple/mobileclip（低配硬件）
  - [x] vidore/colSmol-500M（中配硬件）
  - [x] vidore/colqwen2.5-v0.2（高配硬件）
- [x] Whisper模型集成（用于语音转录）
- [x] 硬件自适应模型选择实现
- [x] 向量化方法实现（使用路径作为输入）
  - [x] `embed_image_from_path(file_path)`
  - [x] `embed_video_segment(file_path)`
  - [x] `embed_video_segments_batch(file_paths)`
  - [x] `embed_text_query(text, target_modality)`
  - [x] `transcribe_audio_from_path(file_path)`
- [x] 批量处理支持
- [x] 模型预热机制
- [x] 健康检查端点
- [x] 统一错误码体系

### 核心块3: 向量存储 (VectorStore)
- [x] VectorStore基础类实现
- [x] Milvus Lite集成
- [x] 向量集合管理
- [x] 向量CRUD操作
- [x] 相似度检索功能
- [x] 批量操作支持
- [ ] 时间定位机制实现
- [ ] 向量元数据管理（包含时间戳信息）
- [x] DatabaseManager数据库管理组件
- [x] 健康检查端点
- [x] 统一错误码体系

### 辅助组件
- [x] ConfigManager配置管理器
- [x] DatabaseManager数据库管理器
  - [ ] 时间定位数据结构实现
    - [ ] VIDEO_METADATA表创建
    - [ ] VIDEO_SEGMENTS表创建
    - [ ] VECTOR_TIMESTAMP_MAP表创建
    - [ ] 表间关联关系实现
- [x] SearchEngine检索引擎
  - [ ] 视频检索流程优化
  - [ ] 检索结果聚合与排序（按视频聚合结果，收集相似度分数和时间戳列）
  - [ ] 超大视频部分索引结果处理
- [ ] MediaProcessor媒体处理器
  - [ ] 智能视频切片机制实现
    - [ ] 两阶段切片策略（FFMPEG场景检测+关键帧提取）
      - [ ] FFMPEG场景检测功能集成（scene detection）
      - [ ] 视觉变化阈值设置（scene=0.3）
      - [ ] 切片最大时长限制（5秒）
      - [ ] 关键帧提取（每切片1-3个关键帧）
    - [ ] 超大视频特殊处理策略（>3GB或>30分钟）
      - [ ] 优先处理开头5分钟内容
      - [ ] 关键场景和转场点识别
      - [ ] 后台逐步处理剩余内容
      - [ ] 实时返回部分结果
    - [ ] 长时固定场景处理（如监控录像）
      - [ ] 每120秒强制提取1帧
      - [ ] 音频活跃时段优先处理
      - [ ] 运动检测算法实现
      - [ ] 静止段跳过机制
    - [ ] 音频辅助切片优化
      - [ ] 视频开头10秒音频预提取
      - [ ] InaSpeechSegmenter音频分类
      - [ ] 根据音频类型调整场景检测阈值
  - [ ] 时间定位功能
    - [ ] 关键帧精确时间戳生成
    - [ ] 向量与时间映射实现
    - [ ] 切片与时间定位结合机制（向量存储时结合切片重计算时间）
- [x] 日志系统实现（多级别、分类存储、自动轮转）
- [x] 统一错误码体系

### API接口
- [ ] RESTful API实现
  - [x] 检索API（仅保留必要的查询API）
  - [ ] 移除其他服务化接口

### 测试与功能验证
- [ ] 单元测试
  - [x] test_task_manager.py
  - [x] test_embedding_engine.py
  - [x] test_vector_store.py
  - [ ] test_media_processor.py
  - [ ] test_config_manager.py
  - [ ] test_database_manager.py
  - [x] test_timestamp_accuracy.py
  - [x] test_multimodal_fusion.py
- [ ] 集成测试
  - [ ] 端到端检索流程测试
  - [ ] 多模态融合功能测试
  - [ ] 性能基准测试
- [ ] 功能验证
  - [ ] 时间戳精度验证（±5秒）
  - [ ] 跨模态检索验证
  - [ ] 批量处理性能验证

### 部署与打包
- [ ] 部署脚本实现
  - [ ] install_auto.sh
  - [ ] install_offline.sh
  - [ ] download_all_resources.sh
- [ ] Nuitka打包配置

### 文档
- [x] 更新设计文档（design.md）
- [x] 更新任务列表（tasks.md）
- [ ] 用户手册（user_manual.md）
- [ ] API文档（api_documentation.md）
- [ ] 技术实现文档（technical_implementation.md）
- [ ] 测试策略文档（test_strategy.md）
- [ ] 贡献指南（CONTRIBUTING.md）

### 用户界面（最后阶段开发）

> **重要说明**：用户界面开发在完成所有核心功能、API接口、测试验证和文档编写后进行。

#### 阶段1: WebUI快速验证
- [ ] 集成现有WebUI界面（webui/index.html）
- [ ] 连接后端API服务
- [ ] 功能快速验证和测试
- [ ] 用户反馈收集

#### 阶段2: PySide6桌面UI
- [ ] PySide6用户界面实现
  - [ ] 主窗口
  - [ ] 搜索功能界面
  - [ ] 配置管理界面
  - [ ] 任务控制面板界面
- [ ] 异步任务集成
- [ ] 本地文件系统集成
- [ ] 跨平台兼容性测试