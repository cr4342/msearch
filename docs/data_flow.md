# 数据流转与处理流程

**文档版本**：v1.0  
**最后更新**：2026-01-19  
**对应设计文档**：[design.md](./design.md)  

---

## 概述

本文档详细描述了 msearch 系统的数据流转和处理流程，包括文件从扫描到检索的完整生命周期。

> **文档定位**：本文档是 [design.md](./design.md) 的补充文档，详细展开第 1.5 节"数据流转总览"和第 3.1 节"数据处理流程"的内容。

**数据流转阶段**：
1. **文件发现阶段**：文件扫描与监控
2. **元数据提取阶段**：文件信息收集
3. **预处理阶段**：媒体预处理和优化
4. **向量化阶段**：使用AI模型生成向量
5. **存储阶段**：向量和元数据存储
6. **检索阶段**：多模态检索和结果返回

**相关文档**：
- [design.md](./design.md) - 主设计文档
- [file_scanner_design_refinement.md](./file_scanner_design_refinement.md) - 文件扫描器详细设计
- [task_management_optimization.md](./task_management_optimization.md) - 任务管理优化设计

---

## 完整数据流转图

### 2.1 数据流转架构图

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

### 2.2 数据流转阶段说明

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

## 详细处理流程

### 3.1 图像文件处理流程

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

### 3.2 视频文件处理流程

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

┌─────────────────────────────────────────────────────────────────────────────┐
│                    短视频处理流程 (Duration ≤ 6秒)                           │
└─────────────────────────────────────────────────────────────────────────────┘

[5] 视频预处理
  ├─ 读取视频文件
  ├─ 提取关键帧 (fps=2)
  ├─ 调整大小到 512x512
  ├─ 归一化
  └─ 转换为张量
  ↓
[6] 视频向量化
  ├─ 使用 [配置驱动模型]-500M 模型
  ├─ 批处理 (batch_size=16)
  ├─ 生成 512 维向量 (每帧一个)
  └─ 使用混合精度 (float16)
  ↓
[7] 向量存储
  ├─ 存储到 LanceDB
  ├─ 字段: vector, file_id, timestamp, modality, created_at
  └─ 更新元数据状态为 "indexed"
  ↓
[8] 缩略图与预览生成
  ├─ 生成 256x256 缩略图
  ├─ 生成 5秒预览视频
  ├─ 保存到缓存目录
  └─ 更新元数据中的路径
  ↓
结束

处理时间估算 (6秒视频):
- 文件扫描: < 10ms
- 元数据提取: < 100ms
- 噪音过滤: < 10ms
- 视频预处理: < 500ms
- 视频向量化: < 500ms (12帧 × 40ms)
- 向量存储: < 100ms (12个向量)
- 缩略图生成: < 100ms
- 预览生成: < 2000ms
- 总计: < 3820ms (~4秒)

┌─────────────────────────────────────────────────────────────────────────────┐
│                    长视频处理流程 (Duration > 6秒)                           │
└─────────────────────────────────────────────────────────────────────────────┘

[5] 音频分离
  ├─ 从视频中提取音频轨道
  ├─ 保存为临时文件
  └─ 创建音频向量化任务
  ↓
[6] 场景检测
  ├─ 使用场景检测算法
  ├─ 检测场景变化点
  └─ 生成场景列表
  ↓
[7] 视频切片
  ├─ 根据场景列表分割视频
  ├─ 每个分段 2-10 秒
  ├─ 最大分段数: 100
  └─ 生成分段列表
  ↓
[8] 分段处理 (并行)
  对于每个分段:
  ├─ 提取关键帧 (fps=2)
  ├─ 调整大小到 512x512
  ├─ 归一化
  ├─ 使用 [配置驱动模型]-500M 生成向量
  └─ 存储向量
  ↓
[9] 音频向量化
  ├─ 音频预处理 (重采样、归一化)
  ├─ 使用 [配置驱动模型] 模型
  ├─ 生成 512 维向量
  └─ 存储向量
  ↓
[10] 缩略图与预览生成
  ├─ 为每个分段生成缩略图
  ├─ 生成 5秒预览视频
  ├─ 保存到缓存目录
  └─ 更新元数据中的路径
  ↓
结束

处理时间估算 (60秒视频，10个分段):
- 文件扫描: < 10ms
- 元数据提取: < 100ms
- 噪音过滤: < 10ms
- 音频分离: < 500ms
- 场景检测: < 1000ms
- 视频切片: < 500ms
- 分段处理: < 5000ms (10分段 × 500ms)
- 音频向量化: < 1000ms
- 向量存储: < 1000ms (100个向量)
- 缩略图生成: < 1000ms
- 预览生成: < 5000ms
- 总计: < 15120ms (~15秒)
```

**关键代码位置**：
- 文件扫描：`src/core/services/file/file_scanner.py`
- 元数据提取：`src/core/data/extractors/metadata_extractor.py`
- 噪音过滤：`src/core/data/filters/noise_filter.py`
- 音频分离：`src/core/services/media/audio_extractor.py`
- 场景检测：`src/core/services/media/scene_detector.py`
- 视频切片：`src/core/services/media/video_preprocessor.py`
- 视频向量化：`src/core/embedding/embedding_engine.py`
- 音频向量化：`src/core/embedding/embedding_engine.py`
- 向量存储：`src/core/vector/vector_store.py`
- 缩略图生成：`src/core/data/generators/thumbnail_generator.py`
- 预览生成：`src/core/data/generators/preview_generator.py`

### 3.3 音频文件处理流程

```
音频文件处理流程图

┌─────────────────────────────────────────────────────────────────────────────┐
│                         音频文件处理流程 (Audio Processing)                   │
└─────────────────────────────────────────────────────────────────────────────┘

开始
  ↓
[1] 文件扫描
  ├─ 发现音频文件 (mp3, wav, aac, flac, ogg)
  ├─ 收集基本信息 (路径、大小、修改时间)
  └─ 创建文件扫描任务
  ↓
[2] 元数据提取
  ├─ 计算 SHA256 哈希
  ├─ 提取音频信息 (时长、采样率、声道数、码率)
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
  ├─ 归一化
  └─ 转换为张量
  ↓
[5] 音频向量化
  ├─ 使用 [配置驱动模型] 模型
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

处理时间估算 (60秒音频):
- 文件扫描: < 10ms
- 元数据提取: < 50ms
- 噪音过滤: < 10ms
- 音频预处理: < 500ms
- 音频向量化: < 1000ms
- 向量存储: < 10ms
- 总计: < 1580ms (~2秒)
```

**关键代码位置**：
- 文件扫描：`src/core/services/file/file_scanner.py`
- 元数据提取：`src/core/data/extractors/metadata_extractor.py`
- 噪音过滤：`src/core/data/filters/noise_filter.py`
- 音频预处理：`src/core/services/media/audio_preprocessor.py`
- 音频向量化：`src/core/embedding/embedding_engine.py`
- 向量存储：`src/core/vector/vector_store.py`

### 3.4 检索流程

```
检索流程图

┌─────────────────────────────────────────────────────────────────────────────┐
│                         多模态检索流程 (Multimodal Search)                   │
└─────────────────────────────────────────────────────────────────────────────┘

开始
  ↓
[1] 用户查询
  ├─ 文本查询: 用户输入文本字符串
  ├─ 图像查询: 用户上传图像文件
  ├─ 音频查询: 用户上传音频文件
  └─ 视频查询: 用户上传视频文件
  ↓
[2] 查询预处理
  ├─ 文本查询:
  │  └─ 文本清洗和标准化
  ├─ 图像查询:
  │  ├─ 读取图像文件
  │  ├─ 调整大小到 512x512
  │  └─ 归一化
  ├─ 音频查询:
  │  ├─ 读取音频文件
  │  ├─ 重采样到 44100Hz
  │  └─ 归一化
  └─ 视频查询:
     ├─ 读取视频文件
     ├─ 提取关键帧 (fps=2)
     └─ 归一化
  ↓
[3] 查询向量化
  ├─ 文本查询:
  │  └─ 使用 [配置驱动模型]-500M 生成 512 维向量
  ├─ 图像查询:
  │  └─ 使用 [配置驱动模型]-500M 生成 512 维向量
  ├─ 音频查询:
  │  └─ 使用 [配置驱动模型] 生成 512 维向量
  └─ 视频查询:
     └─ 使用 [配置驱动模型]-500M 生成 512 维向量 (多帧)
  ↓
[4] 向量检索
  ├─ 连接 LanceDB
  ├─ 使用 IVF 索引加速
  ├─ 计算查询向量与数据库向量的余弦相似度
  ├─ 返回 top_k 个最相似结果 (默认 20)
  └─ 过滤低相似度结果 (相似度 < 0.7)
  ↓
[5] 结果去重
  ├─ 同一文件的多个分段去重
  ├─ 保留最高相似度的分段
  └─ 保留时间戳信息 (视频专用)
  ↓
[6] 元数据查询
  ├─ 查询 SQLite 数据库
  ├─ 获取文件元数据 (路径、大小、类型等)
  ├─ 获取缩略图路径
  └─ 获取视频分段信息
  ↓
[7] 结果排序
  ├─ 按相似度降序排序
  ├─ 多模态结果融合
  └─ 生成最终结果列表
  ↓
[8] 时间轴生成 (视频专用)
  ├─ 为视频结果生成时间轴
  ├─ 显示关键帧和时间戳
  └─ 支持时间戳跳转
  ↓
[9] 结果返回
  ├─ 返回 JSON 格式结果
  ├─ 包含文件信息、相似度、缩略图等
  └─ 支持分页
  ↓
结束

处理时间估算:
- 查询预处理: < 100ms
- 查询向量化: < 200ms
- 向量检索: < 100ms
- 结果去重: < 10ms
- 元数据查询: < 50ms
- 结果排序: < 10ms
- 时间轴生成: < 50ms
- 总计: < 520ms
```

**关键代码位置**：
- 查询预处理：`src/core/services/search/query_processor.py`
- 查询向量化：`src/core/embedding/embedding_engine.py`
- 向量检索：`src/core/vector/vector_store.py`
- 结果去重：`src/core/services/search/result_ranker.py`
- 元数据查询：`src/core/database/database_manager.py`
- 结果排序：`src/core/services/search/result_ranker.py`
- 时间轴生成：`src/core/services/search/timeline.py`

---

## 数据流转优化策略

### 4.1 重复文件处理

**问题**：相同文件多次添加会导致重复处理和存储浪费。

**解决方案**：使用 SHA256 哈希检测重复文件。

```python
# 重复文件检测流程

def process_file(file_path):
    # 1. 计算文件哈希
    file_hash = calculate_sha256(file_path)
    
    # 2. 检查数据库中是否已存在
    existing_file = db.query("SELECT * FROM file_metadata WHERE file_hash = ?", (file_hash,))
    
    if existing_file:
        # 3. 如果已存在，直接引用向量
        print(f"文件已存在，直接引用向量: {file_path}")
        
        # 4. 更新文件引用关系
        db.execute(
            "INSERT INTO file_references (file_id, file_path) VALUES (?, ?)",
            (existing_file['id'], file_path)
        )
        db.commit()
        
        return existing_file['id']
    else:
        # 5. 如果不存在，正常处理
        print(f"新文件，开始处理: {file_path}")
        file_id = process_new_file(file_path, file_hash)
        return file_id
```

**优化效果**：
- 避免重复处理，节省计算资源
- 避免重复存储，节省存储空间
- 提高处理速度

### 4.2 批处理优化

**问题**：单文件处理效率低，尤其是大量小文件。

**解决方案**：使用批处理技术。

```python
# 批处理优化

def process_files_batch(file_paths, batch_size=16):
    """批处理文件"""
    
    # 1. 分批处理
    for i in range(0, len(file_paths), batch_size):
        batch = file_paths[i:i+batch_size]
        
        # 2. 批量预处理
        preprocessed_data = []
        for file_path in batch:
            data = preprocess_file(file_path)
            preprocessed_data.append(data)
        
        # 3. 批量向量化
        embeddings = embedding_engine.embed_batch(preprocessed_data)
        
        # 4. 批量存储
        vector_store.insert_batch(embeddings)
        
        print(f"处理了 {len(batch)} 个文件，进度: {i+len(batch)}/{len(file_paths)}")
```

**优化效果**：
- 提高 GPU 利用率
- 减少 IO 操作
- 提高处理速度 2-4 倍

### 4.3 预处理与向量化合并

**问题**：预处理和向量化分开执行会导致重复解码。

**解决方案**：合并预处理和向量化步骤。

```python
# 预处理与向量化合并

def process_media_optimized(file_path, file_type):
    """优化的媒体处理流程"""
    
    if file_type == 'image':
        # 图像：预处理和向量化一次完成
        image = load_image(file_path)
        image = preprocess_image(image)
        
        # 同时生成向量和缩略图
        vector = embedding_engine.embed_image(image)
        thumbnail = generate_thumbnail(image)
        
        return vector, thumbnail
    
    elif file_type == 'video':
        # 视频：一次解码，多次使用
        video = load_video(file_path)
        
        # 预处理（一次解码）
        frames = extract_frames(video, fps=2)
        frames = preprocess_frames(frames)
        
        # 向量化（使用预处理后的帧）
        vectors = embedding_engine.embed_video_frames(frames)
        
        # 缩略图和预览（使用预处理后的帧）
        thumbnail = generate_thumbnail(frames[0])
        preview = generate_preview(frames)
        
        return vectors, thumbnail, preview
```

**优化效果**：
- 减少视频解码次数
- 提高处理速度 30-50%
- 降低 CPU 和 GPU 使用率

### 4.4 优先级调度

**问题**：任务执行顺序不合理会影响用户体验。

**解决方案**：使用优先级调度。

```python
# 优先级调度

TASK_PRIORITIES = {
    # 基础任务（最高优先级）
    'config_load': 10,
    'database_init': 10,
    'vector_store_init': 10,
    
    # 核心功能（高优先级）
    'file_embed_text': 9,
    'file_embed_image': 8,
    'file_embed_video': 7,
    'file_embed_audio': 6,
    
    # 辅助功能（中优先级）
    'file_scan': 5,
    'video_process': 4,
    'audio_preprocess': 4,
    
    # 后台任务（低优先级）
    'video_slice': 3,
    'thumbnail_generate': 2,
    'preview_generate': 2,
}

class PriorityTaskQueue:
    """优先级任务队列"""
    
    def __init__(self):
        self.queue = []
    
    def add_task(self, task):
        """添加任务到队列"""
        priority = TASK_PRIORITIES.get(task['type'], 5)
        heapq.heappush(self.queue, (-priority, task))  # 使用负数值实现最大堆
    
    def get_task(self):
        """获取最高优先级任务"""
        if self.queue:
            _, task = heapq.heappop(self.queue)
            return task
        return None
```

**优化效果**：
- 核心任务优先执行
- 提高用户体验
- 合理利用系统资源

---

## 数据流转监控

### 5.1 监控指标

**处理阶段监控**：
```python
class ProcessingMetrics:
    """处理阶段监控指标"""
    
    def __init__(self):
        self.metrics = {
            'file_scan': {
                'count': 0,
                'total_time': 0,
                'avg_time': 0,
            },
            'metadata_extraction': {
                'count': 0,
                'total_time': 0,
                'avg_time': 0,
            },
            'noise_filter': {
                'count': 0,
                'total_time': 0,
                'avg_time': 0,
                'filtered_count': 0,
            },
            'preprocessing': {
                'count': 0,
                'total_time': 0,
                'avg_time': 0,
            },
            'embedding': {
                'count': 0,
                'total_time': 0,
                'avg_time': 0,
            },
            'storage': {
                'count': 0,
                'total_time': 0,
                'avg_time': 0,
            },
            'thumbnail_generation': {
                'count': 0,
                'total_time': 0,
                'avg_time': 0,
            },
        }
    
    def record_metric(self, stage, duration):
        """记录阶段指标"""
        if stage in self.metrics:
            self.metrics[stage]['count'] += 1
            self.metrics[stage]['total_time'] += duration
            self.metrics[stage]['avg_time'] = (
                self.metrics[stage]['total_time'] / 
                self.metrics[stage]['count']
            )
    
    def get_report(self):
        """生成监控报告"""
        report = "处理阶段监控报告:\n"
        report += "-" * 60 + "\n"
        
        for stage, data in self.metrics.items():
            report += f"{stage}:\n"
            report += f"  数量: {data['count']}\n"
            report += f"  总时间: {data['total_time']:.2f}s\n"
            report += f"  平均时间: {data['avg_time']*1000:.2f}ms\n"
            if 'filtered_count' in data:
                report += f"  过滤数量: {data['filtered_count']}\n"
            report += "\n"
        
        return report
```

### 5.2 性能监控

**性能监控指标**：
```python
class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.start_time = time.time()
        self.processed_files = 0
        self.failed_files = 0
        self.total_vectors = 0
        self.total_storage = 0
    
    def record_file_processed(self, file_size, vector_count):
        """记录文件处理"""
        self.processed_files += 1
        self.total_vectors += vector_count
        self.total_storage += file_size
    
    def record_file_failed(self):
        """记录文件处理失败"""
        self.failed_files += 1
    
    def get_performance_report(self):
        """生成性能报告"""
        elapsed_time = time.time() - self.start_time
        throughput = self.processed_files / elapsed_time if elapsed_time > 0 else 0
        
        report = {
            'uptime': elapsed_time,
            'processed_files': self.processed_files,
            'failed_files': self.failed_files,
            'success_rate': (self.processed_files / (self.processed_files + self.failed_files)) * 100 
                if (self.processed_files + self.failed_files) > 0 else 0,
            'total_vectors': self.total_vectors,
            'total_storage_gb': self.total_storage / (1024 ** 3),
            'throughput_files_per_second': throughput,
            'avg_time_per_file_seconds': elapsed_time / self.processed_files 
                if self.processed_files > 0 else 0,
        }
        
        return report
```

---

## 数据流转异常处理

### 6.1 异常处理策略

```python
class DataFlowExceptionHandler:
    """数据流转异常处理器"""
    
    def __init__(self):
        self.error_count = 0
        self.error_types = {}
    
    def handle_exception(self, stage, file_path, exception):
        """处理异常"""
        self.error_count += 1
        error_type = type(exception).__name__
        
        if error_type not in self.error_types:
            self.error_types[error_type] = []
        
        self.error_types[error_type].append({
            'stage': stage,
            'file_path': file_path,
            'error_message': str(exception),
            'timestamp': time.time(),
        })
        
        # 根据异常类型采取不同策略
        if error_type in ['FileNotFoundError', 'PermissionError']:
            # 文件错误：跳过文件
            self._skip_file(file_path, exception)
        elif error_type in ['CUDAError', 'OutOfMemoryError']:
            # GPU 错误：重试或降级到 CPU
            self._retry_or_fallback(stage, file_path, exception)
        elif error_type in ['InvalidDataError', 'CodecError']:
            # 数据错误：记录并跳过
            self._log_and_skip(stage, file_path, exception)
        else:
            # 其他错误：重试
            self._retry(stage, file_path, exception)
    
    def _skip_file(self, file_path, exception):
        """跳过文件"""
        logger.warning(f"跳过文件 {file_path}: {exception}")
        # 更新文件状态为 "failed"
    
    def _retry_or_fallback(self, stage, file_path, exception):
        """重试或降级"""
        logger.warning(f"GPU 错误，尝试重试或降级: {exception}")
        # 重试逻辑或降级到 CPU
    
    def _log_and_skip(self, stage, file_path, exception):
        """记录并跳过"""
        logger.error(f"数据错误 {stage} {file_path}: {exception}")
        # 更新文件状态为 "failed"
    
    def _retry(self, stage, file_path, exception):
        """重试"""
        logger.warning(f"重试 {stage} {file_path}: {exception}")
        # 重试逻辑
```

### 6.2 重试机制

```python
class RetryMechanism:
    """重试机制"""
    
    def __init__(self, max_retries=3, retry_delay=5):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
    
    def execute_with_retry(self, func, *args, **kwargs):
        """带重试的执行"""
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                logger.warning(f"尝试 {attempt + 1} 失败: {e}")
                
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))  # 指数退避
        
        logger.error(f"所有 {self.max_retries} 次尝试都失败: {last_exception}")
        raise last_exception
```

---

## 附录

### A.1 数据库表结构

**SQLite 表结构**：
```sql
-- 文件元数据表
CREATE TABLE IF NOT EXISTS file_metadata (
    id TEXT PRIMARY KEY,  -- 文件ID (UUID)
    file_path TEXT NOT NULL,  -- 文件路径
    file_name TEXT NOT NULL,  -- 文件名
    file_type TEXT NOT NULL,  -- 文件类型 (image/video/audio/text)
    file_size INTEGER NOT NULL,  -- 文件大小
    file_hash TEXT NOT NULL,  -- 文件哈希 (SHA256)
    created_at TIMESTAMP NOT NULL,  -- 创建时间
    modified_at TIMESTAMP NOT NULL,  -- 修改时间
    indexed_at TIMESTAMP,  -- 索引时间
    status TEXT NOT NULL DEFAULT 'pending',  -- 状态 (pending/indexing/indexed/failed)
    thumbnail_path TEXT,  -- 缩略图路径
    preview_path TEXT,  -- 预览路径
    metadata JSON,  -- 元数据 (JSON)
    UNIQUE(file_path),
    UNIQUE(file_hash)
);

-- 文件引用表（处理重复文件）
CREATE TABLE IF NOT EXISTS file_references (
    id TEXT PRIMARY KEY,  -- 引用ID
    file_id TEXT NOT NULL,  -- 文件ID
    file_path TEXT NOT NULL,  -- 文件路径
    created_at TIMESTAMP NOT NULL,  -- 创建时间
    FOREIGN KEY (file_id) REFERENCES file_metadata(id)
);

-- 视频分段表
CREATE TABLE IF NOT EXISTS video_segments (
    id TEXT PRIMARY KEY,  -- 分段ID
    file_id TEXT NOT NULL,  -- 文件ID
    start_time REAL NOT NULL,  -- 开始时间 (秒)
    end_time REAL NOT NULL,  -- 结束时间 (秒)
    thumbnail_path TEXT,  -- 缩略图路径
    frame_count INTEGER NOT NULL,  -- 帧数
    created_at TIMESTAMP NOT NULL,  -- 创建时间
    FOREIGN KEY (file_id) REFERENCES file_metadata(id)
);

-- 向量时间戳映射表
CREATE TABLE IF NOT EXISTS vector_timestamp_map (
    id INTEGER PRIMARY KEY AUTOINCREMENT,  -- 映射ID
    vector_id TEXT NOT NULL,  -- 向量ID
    file_id TEXT NOT NULL,  -- 文件ID
    segment_id TEXT,  -- 分段ID (视频专用)
    timestamp REAL NOT NULL,  -- 时间戳 (秒)
    created_at TIMESTAMP NOT NULL,  -- 创建时间
    FOREIGN KEY (file_id) REFERENCES file_metadata(id),
    FOREIGN KEY (segment_id) REFERENCES video_segments(id)
);

-- 任务表
CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,  -- 任务ID
    type TEXT NOT NULL,  -- 任务类型
    file_id TEXT,  -- 文件ID
    file_path TEXT,  -- 文件路径
    status TEXT NOT NULL DEFAULT 'pending',  -- 状态 (pending/running/completed/failed/cancelled)
    priority INTEGER NOT NULL DEFAULT 5,  -- 优先级 (1-10)
    progress REAL NOT NULL DEFAULT 0,  -- 进度 (0-100)
    current_step TEXT,  -- 当前步骤
    error_message TEXT,  -- 错误信息
    created_at TIMESTAMP NOT NULL,  -- 创建时间
    started_at TIMESTAMP,  -- 开始时间
    completed_at TIMESTAMP,  -- 完成时间
    FOREIGN KEY (file_id) REFERENCES file_metadata(id)
);

-- 任务步骤表
CREATE TABLE IF NOT EXISTS task_steps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,  -- 步骤ID
    task_id TEXT NOT NULL,  -- 任务ID
    step_name TEXT NOT NULL,  -- 步骤名称
    step_id TEXT NOT NULL,  -- 步骤ID
    status TEXT NOT NULL DEFAULT 'pending',  -- 状态 (pending/running/completed/failed)
    progress REAL NOT NULL DEFAULT 0,  -- 进度 (0-100)
    started_at TIMESTAMP,  -- 开始时间
    completed_at TIMESTAMP,  -- 完成时间
    duration_ms INTEGER,  -- 持续时间 (毫秒)
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_file_metadata_file_hash ON file_metadata(file_hash);
CREATE INDEX IF NOT EXISTS idx_file_metadata_status ON file_metadata(status);
CREATE INDEX IF NOT EXISTS idx_file_metadata_created_at ON file_metadata(created_at);
CREATE INDEX IF NOT EXISTS idx_video_segments_file_id ON video_segments(file_id);
CREATE INDEX IF NOT EXISTS idx_vector_timestamp_map_file_id ON vector_timestamp_map(file_id);
CREATE INDEX IF NOT EXISTS idx_vector_timestamp_map_segment_id ON vector_timestamp_map(segment_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_type ON tasks(type);
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority);
CREATE INDEX IF NOT EXISTS idx_task_steps_task_id ON task_steps(task_id);
CREATE INDEX IF NOT EXISTS idx_task_steps_status ON task_steps(status);
```

**LanceDB 表结构**：
```python
# LanceDB 向量表结构

# 表名: unified_vectors
# 字段:
# - vector: 向量数据 ([配置驱动模型] float32)
# - file_id: 文件ID (字符串)
# - segment_id: 分段ID (字符串，可选)
# - timestamp: 时间戳 (float，视频帧时间，可选)
# - modality: 模态类型 (字符串: 'image'/'video'/'audio')
# - created_at: 创建时间 (timestamp)

# 索引:
# - IVF 索引 (nlist=1024)
# - 向量索引用于相似度搜索
```

### A.2 数据流转 API

**数据流转 API**：
```python
# 文件扫描 API
POST /api/v1/files/scan
Request:
{
    "paths": ["/path/to/directory1", "/path/to/directory2"],
    "recursive": true,
    "file_types": ["image", "video", "audio"]
}
Response:
{
    "code": 0,
    "message": "扫描完成",
    "data": {
        "files_found": 156,
        "files_new": 120,
        "files_existing": 36,
        "tasks_created": 120
    }
}

# 文件处理状态 API
GET /api/v1/files/{file_id}/status
Response:
{
    "code": 0,
    "message": "success",
    "data": {
        "file_id": "file_123456",
        "file_path": "/path/to/file.jpg",
        "status": "indexed",
        "progress": 100.0,
        "current_stage": "completed",
        "created_at": "2023-09-10T08:00:00Z",
        "started_at": "2023-09-10T08:00:05Z",
        "completed_at": "2023-09-10T08:00:30Z",
        "processing_time_ms": 25000
    }
}

# 系统处理状态 API
GET /api/v1/system/processing-status
Response:
{
    "code": 0,
    "message": "success",
    "data": {
        "total_files": 1256,
        "files_pending": 156,
        "files_indexing": 24,
        "files_indexed": 1058,
        "files_failed": 18,
        "total_tasks": 2512,
        "tasks_pending": 312,
        "tasks_running": 48,
        "tasks_completed": 2124,
        "tasks_failed": 28,
        "processing_speed": {
            "files_per_second": 0.5,
            "vectors_per_second": 10,
            "avg_time_per_file_seconds": 2.0
        }
    }
}

# 数据流转监控 API
GET /api/v1/system/metrics/data-flow
Response:
{
    "code": 0,
    "message": "success",
    "data": {
        "stages": {
            "file_scan": {
                "count": 1256,
                "total_time_seconds": 12.56,
                "avg_time_ms": 10.0
            },
            "metadata_extraction": {
                "count": 1256,
                "total_time_seconds": 62.8,
                "avg_time_ms": 50.0
            },
            "noise_filter": {
                "count": 1256,
                "total_time_seconds": 12.56,
                "avg_time_ms": 10.0,
                "filtered_count": 50
            },
            "preprocessing": {
                "count": 1206,
                "total_time_seconds": 120.6,
                "avg_time_ms": 100.0
            },
            "embedding": {
                "count": 1206,
                "total_time_seconds": 241.2,
                "avg_time_ms": 200.0
            },
            "storage": {
                "count": 1206,
                "total_time_seconds": 12.06,
                "avg_time_ms": 10.0
            },
            "thumbnail_generation": {
                "count": 1206,
                "total_time_seconds": 60.3,
                "avg_time_ms": 50.0
            }
        },
        "performance": {
            "success_rate": 96.0,
            "total_vectors": 15680,
            "total_storage_gb": 2.5,
            "throughput_files_per_second": 0.5,
            "avg_time_per_file_seconds": 2.0
        }
    }
}
```

---

**© 2026 msearch 技术团队**  
**本文档受团队内部保密协议保护**