# msearch 多模态检索系统开发任务列表

## 版本 v0.1 - 基于3核心块架构

根据最新的设计文档，项目架构已简化为3个核心块，所有开发任务将围绕这3个核心块展开。系统采用 [michaelfeil/infinity](https://github.com/michaelfeil/infinity) 框架统一管理模型，实现简单切换模型、高效管理模型运行：
- **简单切换模型**：配置文件驱动，无需修改代码即可切换不同模型
- **高效管理模型运行**：统一的模型生命周期管理（加载、卸载、缓存）
- **统一的模型加载接口**：所有模型使用相同的加载方式，简化代码
- **高性能推理**：动态批处理优化，FlashAttention 加速，多精度支持
- **内存优化**：自动内存管理，避免显存溢出，智能缓存策略
- **支持离线模式**：完全支持离线运行，无需网络连接

系统支持的模型：
- **chinese-clip-vit-base-patch16**：统一多模态模型，支持文本、图像、视频检索
- **clap-htsat-unfused**：音频模型，用于文本-音乐检索

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
- [x] 手动任务管理功能（重启任务、更新优先级、延后处理）
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
  - [x] chinese-clip-vit-base-patch16（统一多模态模型，支持文本、图像、视频检索）
- [x] clap-htsat-unfused集成（用于文本-音乐检索）
- [x] 硬件自适应模型选择实现
- [x] 向量化方法实现（使用路径作为输入）
  - [x] `embed_image_from_path(file_path)`
  - [x] `embed_video_segment(file_path)`
  - [x] `embed_video_segments_batch(file_paths)`
  - [x] `embed_text_query(text, target_modality)`
  - [x] `transcribe_audio_from_path(file_path)`
  - [x] `embed_audio_from_path(file_path)`
- [x] 批量处理支持
- [x] 模型预热机制
- [x] 健康检查端点
- [x] 统一错误码体系
- [x] 模型懒加载机制
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
- [x] 向量集合管理
- [x] 向量CRUD操作
- [x] 相似度检索功能
- [x] 批量操作支持
- [x] 时间定位机制实现
- [x] 向量元数据管理（包含时间戳信息）
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
  - [x] 基于文件哈希的去重和引用计数
    - [x] get_or_create_file_by_hash()方法实现
    - [x] add_file_reference()方法实现
    - [x] remove_file_reference()方法实现
    - [x] get_file_references()方法实现
    - [x] get_reference_count()方法实现
    - [x] cleanup_orphaned_files()方法实现
- [x] SearchEngine检索引擎
  - [x] 视频检索流程优化
  - [x] 检索结果聚合与排序（按视频聚合结果，收集相似度分数和时间戳列）
  - [x] 超大视频部分索引结果处理
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

### API接口
- [x] RESTful API实现
  - [x] 检索API（仅保留必要的查询API）
  - [x] 移除其他服务化接口

### 测试与功能验证
- [x] 单元测试
  - [x] test_task_manager.py
  - [x] test_embedding_engine.py
  - [x] test_vector_store.py
  - [x] test_media_processor.py
  - [x] test_config_manager.py
  - [x] test_database_manager.py
  - [x] test_timestamp_accuracy.py
  - [x] test_multimodal_fusion.py
- [x] 集成测试
  - [x] 端到端检索流程测试
  - [x] 多模态融合功能测试
  - [x] 性能基准测试
- [x] 功能验证
  - [x] 时间戳精度验证（±5秒）
  - [x] 跨模态检索验证
  - [x] 批量处理性能验证

### 部署与打包
- [x] 部署脚本实现
  - [x] install_auto.sh
  - [x] install_offline.sh
  - [x] download_all_resources.sh
- [ ] Nuitka打包配置

### 文档
- [x] 更新设计文档（design.md）
  - [x] 文件名生成策略从基于哈希改为基于UUID
  - [x] 添加预处理缓存与中间文件管理设计
  - [x] 更新缩略图和预览生成器设计
  - [x] 添加缓存清理策略设计
- [x] 更新任务列表（tasks.md）
- [x] 用户手册（user_manual.md）
- [x] API文档（api.md）
- [x] 技术实现文档（technical_implementation.md）
- [x] 测试策略文档（testing.md）
- [ ] 贡献指南（CONTRIBUTING.md）
- [x] 缓存管理使用指南
- [x] 中间文件管理使用指南

### 代码实现示例

本章节包含从设计文档中移动过来的代码实现示例，供开发参考。

#### 核心类接口示例

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
    def __init__(self, config: Dict[str, Any], thumbnail_generator: ThumbnailGenerator = None)
    def initialize(self) -> bool
    
    # 媒体处理
    def process_media(self, file_path: str) -> Dict[str, Any]
    def process_image(self, image_path: str) -> Dict[str, Any]
    def process_video(self, video_path: str) -> List[Dict[str, Any]]
    def process_audio(self, audio_path: str) -> Dict[str, Any]
    
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

**AudioExtractor类接口**：
```python
class AudioExtractor:
    def __init__(self, config: Dict[str, Any])
    def initialize(self) -> bool
    
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

**CacheManager类接口**：
```python
class CacheManager:
    def __init__(self, config: Dict[str, Any])
    def initialize(self) -> bool
    def shutdown(self) -> None
    
    # 缓存操作
    def get(self, key: str, cache_type: str = "default") -> Optional[Any]
    def set(self, key: str, value: Any, ttl: int = None, cache_type: str = "default") -> bool
    def delete(self, key: str, cache_type: str = "default") -> bool
    def exists(self, key: str, cache_type: str = "default") -> bool
    
    # 批量操作
    def get_many(self, keys: List[str], cache_type: str = "default") -> Dict[str, Any]
    def set_many(self, items: Dict[str, Any], ttl: int = None, cache_type: str = "default") -> bool
    def delete_many(self, keys: List[str], cache_type: str = "default") -> int
    
    # 缓存管理
    def clear_cache(self, cache_type: str = None) -> None
    def flush_expired(self, cache_type: str = None) -> int
    def optimize_cache(self, cache_type: str = None) -> None
    
    # 缓存策略
    def set_eviction_policy(self, policy: str, cache_type: str = "default") -> None
    def set_cache_size_limit(self, limit: int, cache_type: str = "default") -> None
    
    # 统计和监控
    def get_cache_stats(self, cache_type: str = None) -> Dict[str, Any]
    def get_hit_rate(self, cache_type: str = "default") -> float
    def get_memory_usage(self, cache_type: str = None) -> Dict[str, int]
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