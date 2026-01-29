# msearch 多模态检索系统开发任务列表

## 版本 v0.1 - 单进程多线程架构

根据最新的设计文档，项目采用**单进程多线程架构**，使用线程池处理并发任务，SQLite作为任务队列和状态存储。系统采用 [michaelfeil/infinity](https://github.com/michaelfeil/infinity) 框架统一管理模型，实现简单切换模型、高效管理模型运行：

### 核心架构特点
- **单进程架构**：所有组件运行在同一进程中，避免进程间通信开销
- **线程池并发**：使用线程池处理I/O密集型和计算密集型任务
- **SQLite队列**：任务队列、状态通知统一使用SQLite实现
- **状态外置**：任务状态存储在外部存储（SQLite），便于恢复
- **独立性原则**：每个代码文件能够独立运行，通过参数传递所有需要的配置、数据和依赖
- **配置驱动**：所有可变参数通过配置文件管理，代码中不出现硬编码的配置值

### 线程池划分
| 线程池名称 | 职责 | 资源需求 | 线程数 |
|-----------|------|---------|--------|
| **Embedding Pool** | 向量化推理 | 高 GPU/CPU，高内存 | 1-4 |
| **I/O Pool** | 文件I/O、网络I/O | 低 CPU，低内存 | 4-8 |
| **Task Pool** | 任务执行（非推理类） | 中 CPU，中内存 | 4-8 |

### 系统支持的模型
- **chinese-clip-vit-base-patch16**：统一多模态模型，支持文本、图像、视频检索（512维）
- **clap-htsat-unfused**：音频模型，用于文本-音乐检索（512维，48kHz）

### 开发顺序说明
1. **核心功能开发**：优先完成线程池、任务队列和3大核心块的实现
2. **辅助组件开发**：完成配置管理、日志系统等辅助组件
3. **API接口开发**：提供RESTful API供WebUI调用
4. **测试与功能验证**：通过完整的测试套件验证所有功能
5. **部署与打包**：实现部署脚本和Nuitka打包
6. **文档编写**：完善各类文档
7. **WebUI快速验证**：基于现有WebUI界面快速验证功能
8. **PySide6桌面UI**：在完成所有功能验证后，最后开发桌面版用户界面

---

## 已完成功能（v0.1）

### 核心架构
- [x] 单进程多线程架构实现
- [x] ThreadPoolManager线程池管理器实现
  - [x] Embedding Pool（向量化线程池）
  - [x] I/O Pool（文件I/O线程池）
  - [x] Task Pool（任务执行线程池）
- [x] SQLiteTaskQueue任务队列实现
  - [x] 任务持久化存储
  - [x] 任务状态管理（PENDING, PROCESSING, COMPLETED, FAILED, RETRYING）
  - [x] 任务优先级系统
  - [x] 失败重试机制
  - [x] 任务去重机制
- [x] 接口定义（interfaces/目录）
  - [x] task_interface.py
  - [x] embedding_interface.py
  - [x] search_interface.py
  - [x] storage_interface.py
  - [x] indexer_interface.py

### 核心块1: 任务管理器 (TaskManager)
- [x] CentralTaskManager中央任务管理器实现
  - [x] 任务生命周期管理（创建、取消、状态查询）
  - [x] 组件协调（调度器、执行器、组管理器）
  - [x] 调度循环控制
- [x] TaskScheduler任务调度器实现
  - [x] 优先级计算（基础优先级+文件优先级+类型优先级+等待时间补偿）
  - [x] 任务队列管理
  - [x] 动态优先级调整
  - [x] 任务排序和选择
- [x] TaskExecutor任务执行器实现
  - [x] 任务执行逻辑
  - [x] 错误处理和重试
  - [x] 进度更新
  - [x] 任务状态管理
- [x] TaskGroupManager任务组管理器实现
  - [x] 文件级任务组管理
  - [x] 任务流水线锁管理
  - [x] 文件级任务组织
  - [x] 任务组进度跟踪
- [x] PriorityCalculator优先级计算器实现
- [x] ResourceManager资源管理器实现
- [x] TaskMonitor任务监控器实现
- [x] 手动操作支持（全量扫描、增量扫描、重新向量化）
- [x] 手动任务管理功能（重启任务、更新优先级、延后处理）
- [x] 任务进度展示
- [x] FileMonitor文件监控组件
  - [x] 实时文件监控（基于watchdog）
  - [x] 防抖延迟（500ms）
  - [x] 批量处理（100个文件/批次）
- [x] MediaProcessor媒体处理组件
- [x] 健康检查端点
- [x] 统一错误码体系

### 核心块2: 向量化引擎 (EmbeddingEngine)
- [x] EmbeddingEngine基础类实现
  - [x] 统一模型管理接口（使用Infinity框架）
  - [x] 模型懒加载机制
  - [x] 模型预热机制
  - [x] 健康检查端点
  - [x] 统一错误码体系
- [x] EmbeddingService向量化服务实现
  - [x] 统一向量化接口
  - [x] 批量处理支持
  - [x] 动态向量维度支持（模型默认值，不强制512维）
- [x] ModelManager模型管理器实现
  - [x] 图像/视频向量化模型集成
    - [x] chinese-clip-vit-base-patch16（统一多模态模型，512维）
  - [x] clap-htsat-unfused集成（用于文本-音乐检索，512维，48kHz）
  - [x] 硬件自适应模型选择实现
  - [x] 模型生命周期管理（加载、卸载、缓存）
  - [x] 高性能推理（动态批处理、FlashAttention加速）
  - [x] 内存优化（自动内存管理、智能缓存策略）
  - [x] 离线模式支持
- [x] 向量化方法实现（使用路径作为输入）
  - [x] `embed_image_from_path(file_path)`
  - [x] `embed_video_segment(file_path)`
  - [x] `embed_video_segments_batch(file_paths)`
  - [x] `embed_text_query(text, target_modality)`
  - [x] `transcribe_audio_from_path(file_path)`
  - [x] `embed_audio_from_path(file_path)`
- [x] 任务优先级系统（视觉任务优先）
  - [x] 11级优先级定义（0-10）
  - [x] 优先级计算机制（基础优先级+模态调整+任务类型调整+等待时间补偿）
  - [x] 任务依赖关系管理
  - [x] 向量化任务优先于预处理任务
  - [x] 视觉模态优先于音频模态
  - [x] 音频分离优先于视频切片

### 核心块3: 向量存储 (VectorStore)
- [x] VectorStore基础类实现
  - [x] LanceDB集成
  - [x] 动态向量维度支持（模型默认值）
  - [x] 向量集合管理
  - [x] 向量CRUD操作
  - [x] 相似度检索功能
  - [x] 批量操作支持
  - [x] 健康检查端点
  - [x] 统一错误码体系
- [x] 时间定位机制实现
  - [x] 向量元数据管理（包含时间戳信息）
  - [x] 简化时序定位（≤6秒视频统一使用segment_id="full"）
  - [x] 关键帧精确时间戳生成（仅用于>6秒视频）
  - [x] 向量与时间映射实现
  - [x] 切片与时间定位结合机制
- [x] DatabaseManager数据库管理组件
  - [x] SQLite元数据库管理
  - [x] 基于文件哈希的去重和引用计数
  - [x] 健康检查端点
  - [x] 统一错误码体系

### 辅助组件
- [x] ConfigManager配置管理器
  - [x] 配置加载和验证
  - [x] 配置热更新支持
  - [x] 配置持久化
- [x] DatabaseManager数据库管理器
  - [x] SQLite元数据库管理
  - [x] 时间定位数据结构实现
    - [x] VIDEO_METADATA表创建
    - [x] VIDEO_SEGMENTS表创建
    - [x] VECTOR_TIMESTAMP_MAP表创建
    - [x] 表间关联关系实现
  - [x] 基于文件哈希的去重和引用计数
    - [x] get_or_create_file_by_hash()方法实现
    - [x] add_file_reference()方法实现
    - [x] remove_file_reference()方法实现
    - [x] get_file_references()方法实现
    - [x] get_reference_count()方法实现
    - [x] cleanup_orphaned_files()方法实现
- [x] SearchEngine检索引擎
  - [x] 文本搜索（search）
  - [x] 图像搜索（image_search）
  - [x] 音频搜索（audio_search）
  - [x] 视频检索流程优化
  - [x] 检索结果聚合与排序（按视频聚合结果，收集相似度分数和时间戳列）
  - [x] 超大视频部分索引结果处理
  - [x] 去重服务集成（services/deduplication/）
- [x] FileIndexer文件索引器
  - [x] 基于文件哈希的去重和引用计数
    - [x] calculate_file_hash()方法实现
    - [x] check_duplicate_file()方法实现
    - [x] handle_duplicate_file()方法实现
    - [x] deduplicate_index()方法实现
- [x] MediaProcessor媒体处理器
  - [x] 视频时长判断机制实现
    - [x] is_short_video()方法实现（≤6秒判断）
    - [x] 视频时长获取方法
  - [x] 音频价值判断机制实现
    - [x] has_audio_value()方法实现（<3秒判断）
    - [x] get_min_audio_value_duration()方法实现（3秒阈值）
  - [x] 音频分离功能实现
    - [x] extract_audio_from_video()方法实现
    - [x] 音频分离优先级设置（优先级3）
  - [x] 视频切片功能实现
    - [x] video_slice()方法实现
    - [x] 视频切片优先级设置（优先级5）
  - [ ] 图片预处理优化
    - [x] 图片预处理和缩略图生成合并执行
    - [ ] 减少IO操作实现
  - [ ] 视频预处理优化
    - [ ] 视频缩略图和预览生成合并执行
    - [ ] 一次解码完成实现
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
      - [x] 音频价值阈值过滤（仅处理>3秒的音频片段）
  - [x] 时间定位功能
    - [x] 简化时序定位（≤6秒视频统一使用segment_id="full"）
    - [x] 关键帧精确时间戳生成（仅用于>6秒视频）
    - [x] 向量与时间映射实现
    - [x] 切片与时间定位结合机制（向量存储时结合切片重计算时间）
  - [x] 媒体价值判断（前置过滤）
    - [x] has_media_value()方法实现
    - [x] get_min_media_value_duration()方法实现
  - [x] 音频分离器优化
    - [x] has_audio_value()方法实现
    - [x] get_min_audio_value_duration()方法实现
- [x] 日志系统实现（多级别、分类存储、自动轮转）
- [x] 统一错误码体系
- [x] 文件名生成策略更新
  - [x] 缩略图命名策略从基于哈希改为基于UUID
  - [x] 预览命名策略从基于哈希改为基于UUID
  - [x] 确保所有文件ID生成机制统一使用UUID v4
- [x] 预处理缓存与中间文件管理
  - [x] PreprocessingCache类实现
    - [x] get_cache_path()方法实现
    - [x] save_cache()方法实现
    - [x] load_cache()方法实现
    - [x] delete_cache()方法实现
    - [x] cleanup_expired_cache()方法实现
    - [x] cleanup_by_size()方法实现
    - [x] get_cache_stats()方法实现
  - [x] 缓存目录结构创建
    - [x] 主缓存目录
    - [x] 预处理缓存子目录
    - [x] 临时文件目录
  - [x] 缓存配置参数实现
    - [x] 缓存大小限制
    - [x] 缓存过期时间
    - [x] 缓存清理间隔
  - [x] 中间文件管理实现
    - [x] 临时文件自动清理
    - [x] 中间文件生命周期管理
  - [x] 缓存与原始文件关联性验证
    - [x] 文件删除时自动清理相关缓存
    - [x] 文件修改时自动清理旧缓存
    - [x] 定期验证缓存文件完整性
- [x] 缓存性能优化
  - [x] 缓存命中率统计
  - [x] 缓存预加载机制
  - [x] 缓存压缩与优化
- [x] 去重服务实现（services/deduplication/）
  - [x] 重复文件检测
  - [x] 去重策略管理

### API接口
- [x] RESTful API实现（FastAPI）
  - [x] 检索API（文本、图像、音频搜索）
  - [x] 文件管理API
  - [x] 任务管理API
  - [x] 系统信息API
  - [x] 健康检查API
  - [x] API服务器实现（api_server.py，使用依赖注入）
  - [x] API服务器工厂（api_server_factory.py）
- [x] WebUI实现
  - [x] 原生HTML/CSS/JavaScript界面
  - [x] 搜索面板
  - [x] 结果展示面板
  - [x] API客户端集成

### 测试与功能验证
- [x] 单元测试（tests/unit/）
  - [x] test_task_manager.py
  - [x] test_embedding_engine.py
  - [x] test_vector_store.py
  - [x] test_media_processor.py
  - [x] test_config_manager.py
  - [x] test_database_manager.py
  - [x] test_timestamp_accuracy.py
  - [x] test_multimodal_fusion.py
  - [x] test_search_simple.py
  - [x] test_semantic_search.py
  - [x] test_vector_search_simple.py
  - [x] test_retrieval_accuracy.py
- [x] 集成测试（tests/integration/）
  - [x] 端到端检索流程测试
  - [x] 多模态融合功能测试
  - [x] 性能基准测试
  - [x] test_data_processing.py
  - [x] test_search.py
  - [x] test_search_cli.py
  - [x] test_search_with_embedding.py
  - [x] test_webui_search.py
- [x] 端到端测试（tests/e2e/）
  - [x] e2e_full_workflow.py
  - [x] e2e_api_server.py
  - [x] e2e_webui.py
  - [x] test_comprehensive.py
  - [x] test_other_features.py
  - [x] test_requirements_comprehensive.py
- [x] 性能基准测试（tests/benchmark/）
  - [x] test_embedding_benchmark.py
  - [x] test_search_accuracy.py
  - [x] test_search_accuracy_improved.py
  - [x] test_search_accuracy_real.py
- [x] 功能验证
  - [x] 时间戳精度验证（±5秒）
  - [x] 跨模态检索验证
  - [x] 批量处理性能验证

### 部署与打包
- [x] 部署脚本实现
  - [x] install_auto.sh
  - [x] install_offline.sh
  - [x] download_all_resources.sh
  - [x] run.sh（主程序启动脚本）
  - [x] run_api.sh（API服务启动脚本）
  - [x] run_webui.sh（WebUI启动脚本）
  - [x] run_offline.sh（离线模式启动脚本）
  - [x] setup_models.py（模型设置脚本）
- [ ] Nuitka打包配置

### 文档
- [x] 更新设计文档（design.md）
  - [x] 单进程多线程架构设计
  - [x] 线程池管理设计
  - [x] SQLite任务队列设计
  - [x] 文件名生成策略从基于哈希改为基于UUID
  - [x] 添加预处理缓存与中间文件管理设计
  - [x] 更新缩略图和预览生成器设计
  - [x] 添加缓存清理策略设计
  - [x] 音频预处理48kHz配置
  - [x] 动态向量维度支持
- [x] 更新任务列表（tasks.md）
- [x] 用户手册（user_manual.md）
- [x] API文档（api.md）
- [x] 技术实现文档（technical_implementation.md）
- [x] 测试策略文档（testing.md）
- [x] 数据流转文档（data_flow.md）
- [x] 文件扫描器设计文档（file_scanner_design_refinement.md）
- [x] PySide6 UI设计文档（pyside6_ui_design.md）
- [x] 部署文档（deployment.md）
- [x] 任务控制API文档（task_control_api.md）
- [x] CLI使用文档（cli_usage.md）
- [x] Infinity内存管理文档（INFINITY_MEMORY_MANAGEMENT.md）
- [x] Infinity模型管理文档（INFINITY_MODEL_MANAGEMENT.md）
- [x] 使用标准数据集文档（USING_STANDARD_DATASETS.md）
- [x] 多进程架构文档（multiprocess_architecture.md）- 参考文档
- [ ] 贡献指南（CONTRIBUTING.md）
- [x] 缓存管理使用指南
- [x] 中间文件管理使用指南

### 代码实现示例

本章节包含从设计文档中移动过来的代码实现示例，供开发参考。

#### 核心类接口示例

**ThreadPoolManager类接口**：
```python
class ThreadPoolManager:
    """
    线程池管理器 - 管理三个专用线程池
    """
    def __init__(self, config: Dict[str, Any]):
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
```

**SQLiteTaskQueue类接口**：
```python
class SQLiteTaskQueue:
    """
    SQLite任务队列 - 持久化任务队列实现
    """
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()
        
    def enqueue(self, task: Task) -> bool:
        """将任务加入队列"""
        pass
        
    def dequeue(self, worker_id: str) -> Optional[Task]:
        """从队列取出任务"""
        pass
        
    def update_status(self, task_id: str, status: TaskStatus, result: Any = None):
        """更新任务状态"""
        pass
        
    def get_pending_tasks(self, limit: int = 10) -> List[Task]:
        """获取待处理任务"""
        pass
```

**CentralTaskManager类接口**：
```python
class CentralTaskManager:
    """
    中央任务管理器 - 任务生命周期管理、组件协调、调度循环控制
    """
    def __init__(self, config: Dict[str, Any], thread_pool_manager: ThreadPoolManager,
                 task_queue: SQLiteTaskQueue, file_monitor: FileMonitor):
        self.config = config
        self.thread_pool_manager = thread_pool_manager
        self.task_queue = task_queue
        self.file_monitor = file_monitor
        
        # 子组件
        self.scheduler = TaskScheduler(config)
        self.executor = TaskExecutor(thread_pool_manager)
        self.group_manager = TaskGroupManager()
        
    async def start(self):
        """启动任务管理器"""
        # 启动调度循环
        await self._start_scheduler_loop()
        
    async def stop(self):
        """停止任务管理器"""
        pass
        
    def submit_task(self, task: Task) -> str:
        """提交任务"""
        return self.task_queue.enqueue(task)
        
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        pass
        
    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """获取任务状态"""
        pass
```

**SearchEngine类接口**：
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

**SearchOptions类定义**：
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

**MediaProcessor类接口**：
```python
class MediaProcessor:
    """
    媒体处理器 - 负责媒体文件的预处理和向量化
    """
    def __init__(self, config: ConfigManager, model_manager: ModelManager,
                 thread_pool_manager: ThreadPoolManager):
        self.config = config
        self.model_manager = model_manager
        self.thread_pool_manager = thread_pool_manager
        
    async def process(self, file_info: FileInfo) -> ProcessingResult:
        """处理媒体文件"""
        pass
    
    def process_image(self, image_path: str) -> Dict[str, Any]:
        """处理图像文件"""
        pass
    
    def process_video(self, video_path: str) -> List[Dict[str, Any]]:
        """处理视频文件"""
        pass
    
    def process_audio(self, audio_path: str) -> Dict[str, Any]:
        """处理音频文件"""
        # 1. 检查音频时长（≥3秒）
        # 2. 重采样到48kHz
        # 3. 转换为单声道
        # 4. 归一化
        # 5. 向量化
        pass
    
    def get_supported_media_types(self) -> List[str]
    def is_supported_media_type(self, file_path: str) -> bool
    def get_media_info(self, file_path: str) -> Dict[str, Any]
```

**FrameExtractor类接口**：
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

**AudioProcessor类接口**：
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
    
    # 音频价值判断
    def has_audio_value(self, audio_path: str) -> bool
    def get_min_audio_value_duration(self) -> float
    
    # 音频分离（从视频中提取音频）
    def extract_audio_from_video(self, video_path: str, output_path: str = None) -> str
    def extract_audio_segment(self, video_path: str, start_time: float, end_time: float) -> np.ndarray
    
    # 特征提取
    def extract_audio_features(self, audio_segment: np.ndarray) -> Dict[str, Any]
    def extract_spectral_features(self, audio_segment: np.ndarray) -> Dict[str, float]
    def extract_temporal_features(self, audio_segment: np.ndarray) -> Dict[str, float]
    
    # 质量评估
    def assess_audio_quality(self, audio_path: str) -> float
    def filter_low_quality_audio(self, audio_paths: List[str], quality_threshold: float = 0.5) -> List[str]
```

**FileIndexer类接口**：
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

**PreprocessingCache类接口**：
```python
class PreprocessingCache:
    def __init__(self, config: Dict[str, Any])
    def initialize(self) -> bool
    def shutdown(self) -> None
    
    # 缓存操作
    def get(self, key: str) -> Optional[Any]
    def set(self, key: str, value: Any, ttl: int = None) -> bool
    def delete(self, key: str) -> bool
    def exists(self, key: str) -> bool
    
    # 缓存管理
    def clear_cache(self) -> None
    def flush_expired(self) -> int
    def optimize_cache(self) -> None
    
    # 统计和监控
    def get_cache_stats(self) -> Dict[str, Any]
    def get_hit_rate(self) -> float
    def get_memory_usage(self) -> Dict[str, int]
    
    # 预处理缓存特定方法
    def get_cache_path(self, cache_type: str, key: str) -> str
    def save_cache(self, cache_type: str, key: str, data: Any) -> bool
    def load_cache(self, cache_type: str, key: str) -> Optional[Any]
    def delete_cache(self, cache_type: str, key: str) -> bool
    def cleanup_expired_cache(self) -> int
    def cleanup_by_size(self, max_size: int) -> int
```

**ContentAnalyzer类接口**：
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

#### 数据模型定义

**SceneSegment数据模型**：
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

**ShortVideoSegment数据模型**：
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

**AudioContentType枚举**：
```python
class AudioContentType:
    SPEECH = "speech"          # 语音
    MUSIC = "music"           # 音乐
    NOISE = "noise"           # 噪声
    SILENCE = "silence"       # 静音
    MIXED = "mixed"           # 混合
    UNKNOWN = "unknown"       # 未知
```

**AudioSegment数据模型**：
```python
class AudioSegment:
    segment_id: str           # 分段ID
    start_time: float         # 开始时间（秒）
    end_time: float           # 结束时间（秒）
    duration: float           # 时长（秒）
    content_type: str         # 内容类型（speech/music/noise/silence/mixed/unknown）
    confidence: float         # 分类置信度
    recommended_model: str    # 推荐使用的模型（clap）
    features: Dict[str, Any]  # 音频特征
    quality_score: float      # 质量评分
```

**IndexStatus枚举**：
```python
class IndexStatus:
    PENDING = "pending"        # 待索引
    INDEXING = "indexing"     # 索引中
    INDEXED = "indexed"       # 已索引
    FAILED = "failed"         # 索引失败
    OUTDATED = "outdated"     # 需要更新
    REMOVED = "removed"       # 已移除
```

**CacheType枚举**：
```python
class CacheType:
    EMBEDDING = "embedding"      # 向量缓存
    THUMBNAIL = "thumbnail"      # 缩略图缓存
    METADATA = "metadata"        # 元数据缓存
    SEARCH_RESULT = "search"     # 搜索结果缓存
    MODEL = "model"             # 模型缓存
    PROCESSED_MEDIA = "media"    # 处理后媒体缓存
```

**EvictionPolicy枚举**：
```python
class EvictionPolicy:
    LRU = "lru"                 # 最近最少使用
    LFU = "lfu"                 # 最少使用频率
    FIFO = "fifo"               # 先进先出
    TTL = "ttl"                 # 基于时间
    ADAPTIVE = "adaptive"        # 自适应策略
```

**ContentFeatures数据模型**：
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
```

### 用户界面（已完成）

> **重要说明**：用户界面开发在完成所有核心功能、API接口、测试验证和文档编写后进行。

#### 阶段1: WebUI快速验证（已完成）
- [x] 集成现有WebUI界面（webui/index.html）
- [x] 连接后端API服务
- [x] 功能快速验证和测试
- [x] 用户反馈收集
- [x] WebUI应用实现（webui/app.py）
- [x] 搜索面板
- [x] 结果展示面板
- [x] API客户端集成
- [x] 缩略图显示
- [x] 时间轴展示

#### 阶段2: PySide6桌面UI（已完成）
- [x] PySide6用户界面实现
  - [x] 主窗口（main_window.py）
  - [x] UI启动器（ui_launcher.py）
  - [x] 搜索功能界面（search_panel.py）
  - [x] 结果展示界面（result_panel.py）
  - [x] 配置管理界面（settings_panel.py）
  - [x] 任务控制面板界面
  - [x] 进度对话框（progress_dialog.py）
- [x] 异步任务集成
- [x] 本地文件系统集成
- [x] 跨平台兼容性测试
- [x] 依赖注入架构

---

## 技术栈更新

### 核心技术栈
- **语言**: Python 3.8+
- **AI推理**: Python原生集成（直接模型调用、GPU/CPU由配置文件决定）
- **PyTorch版本**: torch>=2.8.0
- **模型管理框架**: [michaelfeil/infinity](https://github.com/michaelfeil/infinity)
- **架构模式**: 单进程多线程
- **并发模型**: 线程池（Embedding Pool、I/O Pool、Task Pool）
- **任务队列**: SQLite
- **向量存储**: LanceDB
- **元数据存储**: SQLite
- **Web框架**: FastAPI
- **GUI框架**: PySide6
- **媒体处理**: FFmpeg, OpenCV, Librosa
- **文件监控**: Watchdog
- **配置管理**: YAML

### 架构优化
- **简化架构**: 单进程多线程架构，消除进程间通信开销
- **动态向量维度**: 模型默认值，不强制512维
- **48kHz音频预处理**: CLAP模型要求48kHz采样率
- **增量索引**: 500ms防抖延迟，100文件/批次
- **配置驱动**: 所有配置通过YAML管理
- **独立性原则**: 模块独立运行，参数传递依赖

---

## 配置更新

### 线程池配置（新增）
```yaml
thread_pools:
  embedding:
    min_workers: 1
    max_workers: 4
    queue_size: 100
    task_timeout: 300
  io:
    min_workers: 4
    max_workers: 8
    queue_size: 200
    task_timeout: 60
  task:
    min_workers: 4
    max_workers: 8
    queue_size: 200
    task_timeout: 120
```

### 任务队列配置（新增）
```yaml
task_queue:
  database_path: "data/task_queue/tasks.db"
  max_pending_tasks: 1000
  max_processing_tasks: 100
  cleanup_interval: 300
  retry_interval: 60
  max_retries: 3
```

### 音频预处理配置（更新）
```yaml
processing:
  audio:
    sample_rate: 48000  # 从44100更新到48000
    channels: 1
    quality: high
    format: aac
    bitrate: 128000
    min_duration: 5.0  # 从3秒更新到5秒
```

### 文件监控配置（更新）
```yaml
file_monitor:
  watch_directories:
    - "testdata"
  scan_interval: 60
  debounce_delay: 500  # 500ms防抖延迟
  batch_size: 100      # 100文件/批次
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
```

### 模型配置（更新）
```yaml
models:
  available_models:
    chinese_clip_base:
      embedding_dim: 512  # 模型默认值，不强制
      ...
    clap_htsat:
      embedding_dim: 512  # 模型默认值，不强制
      sample_rate: 48000  # 48kHz
      ...
```