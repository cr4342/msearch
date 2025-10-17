# 需求文档

> **文档导航**: [文档索引](README.md) | [设计文档](design.md) | [开发计划](development_plan.md) | [测试策略](test_strategy.md) | [部署指南](deployment_guide.md)

## 介绍

msearch 是一款跨平台多模态桌面检索软件，旨在打造"用户的第二大脑"，实现素材无需整理、无需标签的智能检索。该软件基于专业化多模型架构：使用 CLIP 模型进行文本-图像/视频检索、CLAP 模型进行文本-音乐检索、Whisper 模型进行语音转文本检索，结合 inaSpeechSegmenter 进行音频内容智能分类。系统采用 **michaelfeil/infinity** 作为高吞吐量、低延迟的多模型服务引擎，支持文本、图像、视频、音频四种模态的精准检索，通过实时监控和增量处理，为用户提供无缝的多媒体内容检索体验。

> **重要说明**：本项目中的 Infinity 特指 **michaelfeil/infinity** 项目 (https://github.com/michaelfeil/infinity)，这是一个专为文本嵌入、重排序模型、CLIP、CLAP 和 ColPali 设计的高吞吐量、低延迟服务引擎。

## 需求

### 需求 1: 多模态内容检索

**用户故事:** 作为用户，我希望能够使用文本、图像、音频等不同方式检索我的多媒体文件，以便快速找到相关内容。

#### 验收标准

1. WHEN 用户输入文本查询（如"科比进球瞬间"）THEN 系统 SHALL 返回相关的视频片段、图片和音频文件
2. WHEN 用户上传参考图片 THEN 系统 SHALL 检索出视觉相似的图片和视频，并标记关键帧位置
3. WHEN 用户上传音频样本 THEN 系统 SHALL 检索出包含相似音效的音频文件和视频
4. WHEN 用户进行跨模态检索 THEN 系统 SHALL 在2秒内返回检索结果
5. WHEN 检索结果包含视频 THEN 系统 SHALL 显示关键帧缩略图和精确时间戳定位
6. WHEN 进行文本搜索视频 THEN 系统 SHALL 通过时序定位算法标注出与描述最相似的具体时间点
7. WHEN 进行图像搜索视频 THEN 系统 SHALL 通过时序定位算法标注出与参考图像最相似的具体时间点

### 需求 2: 人脸识别与聚类

**用户故事:** 作为用户，我希望系统能够通过预定义的人脸照片+名字方式，在以之后检索中如果出现指定人名则重点检索包含人脸的片段，以增加人名检索时的精度。

#### 验收标准

1. WHEN 用户上传人脸照片并设置人名 THEN 系统 SHALL 使用专业人脸识别模型（FaceNet/ArcFace）创建高精度人脸特征库条目
2. WHEN 系统处理新的图片或视频 THEN 系统 SHALL 自动检测并匹配已知人脸，匹配准确率≥95%
3. WHEN 用户输入已预设的人名 THEN 系统 SHALL 自动调用对应人脸图片进行精确检索，并动态提升人脸相关权重
4. WHEN 进行人脸匹配 THEN 系统 SHALL 达到95%以上的准确率，支持多角度、不同光照条件下的人脸识别
5. IF 检测到未知人脸 THEN 系统 SHALL 提示用户是否添加到人脸库，并支持批量人脸导入
6. WHEN 系统进行动态权重融合 THEN 检测到预设人名时自动提升人脸模态权重（权重系数1.5-2.0）
7. WHEN 用户检索包含预设人名的查询 THEN 系统 SHALL 优先返回包含该人脸的视频片段和图片

### 需求 3: 实时文件监控与增量处理

**用户故事:** 作为用户，我希望系统能够自动监控指定目录的文件变化，并实时处理新增文件，以便无需手动触发索引更新。

#### 验收标准

1. WHEN 用户配置监控目录 THEN 系统 SHALL 使用 watchdog 开始实时监控
2. WHEN 监控目录中有新文件添加 THEN 系统 SHALL 在30秒内开始处理该文件
3. WHEN 文件被删除或移动 THEN 系统 SHALL 更新索引并移除对应向量数据
4. WHEN 系统重启 THEN 系统 SHALL 自动恢复监控状态
5. IF 处理过程中出现错误 THEN 系统 SHALL 记录错误日志并继续处理其他文件

### 需求 4: 精确时序定位

**用户故事:** 作为用户，我希望在检索视频时能够获得精确的时间点定位，以便快速跳转到最相关的视频片段。

#### 验收标准

1. WHEN 用户使用文本检索视频 THEN 系统 SHALL 通过时序定位算法计算出与查询最匹配的时间点
2. WHEN 用户使用图像检索视频 THEN 系统 SHALL 通过时序定位算法找到视觉最相似的时间点
3. WHEN 系统进行时序定位 THEN 定位精度 SHALL 达到秒级别（±2秒以内）
4. WHEN 检索结果显示视频 THEN 系统 SHALL 在视频下方标注最相似时间点的时间轴位置
5. WHEN 用户点击时间轴标注 THEN 视频播放器 SHALL 自动跳转到对应时间点
6. IF 视频中有多个相似片段 THEN 系统 SHALL 按相似度排序显示前3个最佳时间点

### 需求 5: 智能文件预处理

**用户故事:** 作为用户，我希望系统能够自动优化多媒体文件格式，以便提高检索效率和节省存储空间。

#### 验收标准

1. WHEN 处理视频文件且短边超过960px THEN 系统 SHALL 等比例缩放至短边约960px
2. WHEN 处理视频文件 THEN 系统 SHALL 统一转换为8 FPS的H.264 8-bit mp4格式
3. WHEN 处理音频文件 THEN 系统 SHALL 使用inaSpeechSegmenter区分音乐和语音内容，并重采样为16 kHz mono的64 kbps AAC格式
4. WHEN 视频长度超过2分钟 THEN 系统 SHALL 使用FFmpeg scene detection检测转场并切片为120秒以内片段
5. WHEN 视频切片完成 THEN 系统 SHALL 使用CLIP模型对视频帧进行向量化，并对片段向量进行MaxSim聚合以优化显存占用
6. WHEN 处理带音频的视频文件 THEN 系统 SHALL 使用inaSpeechSegmenter区分音乐和讲话内容，并根据配置决定是否进行音频向量化
7. WHEN 检测到只有杂声或讲话时长过短、不清晰的视频音频 THEN 系统 SHALL 跳过该视频的音频向量化流程，节约资源
8. WHEN 用户配置音频处理策略 THEN 系统 SHALL 通过配置文件提供是否处理视频音频流的选择权

### 需求 6: 硬件自适应与模型选择

**用户故事:** 作为用户，我希望系统能够根据我的硬件配置自动选择最适合的模型和加速方案，以便获得最佳性能。

#### 验收标准

1. WHEN 系统启动 THEN 系统 SHALL 自动检测GPU、CPU和内存配置
2. IF 检测到CUDA兼容GPU THEN 系统 SHALL 优先使用 michaelfeil/infinity 的 CUDA-INT8 加速
3. IF 仅有CPU可用且支持OpenVINO THEN 系统 SHALL 使用 michaelfeil/infinity 的 CPU-OpenVINO 后端
4. IF 硬件配置较低 THEN 系统 SHALL 自动选择轻量级模型：CLIP-base、CLAP-base、Whisper-base
5. WHEN 模型切换 THEN 系统 SHALL 通过配置文件驱动，无需修改核心代码

### 需求 7: 桌面应用与后台服务分离

**用户故事:** 作为开发者，我希望桌面UI与后台处理逻辑完全分离，以便未来可以独立更新UI或进行微服务拆分。

#### 验收标准

1. WHEN 设计系统架构 THEN 桌面应用 SHALL 通过API与后台服务通信
2. WHEN 后台服务运行 THEN 系统 SHALL 提供完整的REST API接口
3. WHEN 桌面应用启动 THEN 系统 SHALL 能够独立于后台服务运行基本UI功能
4. WHEN 进行UI更新 THEN 开发者 SHALL 无需修改后台处理代码
5. IF 需要微服务拆分 THEN 各功能模块 SHALL 具备独立部署能力

### 需求 8: 高性能向量检索

**用户故事:** 作为用户，我希望系统能够快速准确地检索大量多媒体文件，以便在海量数据中快速找到目标内容。

#### 验收标准

1. WHEN 用户进行检索 THEN 系统 SHALL 在2秒内返回前20个最相关结果
2. WHEN 向量数据库包含超过100万条记录 THEN 检索性能 SHALL 不明显下降
3. WHEN 进行ANN召回 THEN 系统 SHALL 使用Qdrant进行高效向量相似度计算
4. WHEN 处理音频模态 THEN 系统 SHALL 根据音频类型选择合适模型：音乐使用CLAP模型，语音使用Whisper模型转文本后检索
5. IF 检索结果需要重排序 THEN 系统 SHALL 基于多模态相似度进行智能排序
6. WHEN 用户输入包含"音乐"、"歌曲"等关键词 THEN 系统 SHALL 动态提升CLAP音频权重，降低Whisper权重
7. WHEN 用户输入包含"讲话"、"会议"、"语音"等关键词 THEN 系统 SHALL 动态提升Whisper权重，降低CLAP权重
8. WHEN 处理其他音频相关查询 THEN 系统 SHALL 根据查询内容智能调整音频模型权重，优先使用Whisper模型

### 需求 9: 数据存储与管理

**用户故事:** 作为用户，我希望系统能够安全可靠地存储我的文件索引和向量数据，以便数据不会丢失且易于备份。

#### 验收标准

1. WHEN 系统处理文件 THEN 元数据 SHALL 存储在SQLite数据库中
2. WHEN 生成向量数据 THEN 向量 SHALL 存储在Qdrant向量数据库中
3. WHEN 系统异常关闭 THEN 已处理的数据 SHALL 保持完整性
4. WHEN 用户需要备份 THEN 系统 SHALL 提供数据导出功能
5. IF 数据库损坏 THEN 系统 SHALL 提供数据恢复机制

### 需求 10: 跨平台兼容性

**用户故事:** 作为用户，我希望能够在Windows、macOS和Linux系统上使用相同的软件功能，以便在不同设备间无缝切换。

#### 验收标准

1. WHEN 在Windows系统部署 THEN 所有功能 SHALL 正常运行
2. WHEN 在macOS系统部署 THEN 所有功能 SHALL 正常运行  
3. WHEN 在Linux系统部署 THEN 所有功能 SHALL 正常运行
4. WHEN 在不同平台间迁移数据 THEN 数据格式 SHALL 保持兼容
5. IF 平台特定功能不可用 THEN 系统 SHALL 提供替代方案或优雅降级

### 需求 11: 用户界面与交互体验

**用户故事:** 作为用户，我希望拥有直观易用的界面来进行检索操作和结果浏览，以便高效完成检索任务。

#### 验收标准

1. WHEN 用户打开应用 THEN 界面 SHALL 在3秒内完全加载
2. WHEN 用户拖拽文件到检索框 THEN 系统 SHALL 自动识别文件类型并开始检索
3. WHEN 显示检索结果 THEN 界面 SHALL 提供缩略图、文件路径和相似度评分
4. WHEN 用户点击视频结果 THEN 系统 SHALL 自动跳转到关键帧位置播放
5. IF 检索正在进行 THEN 界面 SHALL 显示进度指示器和预估完成时间

## 架构要求
- 采用Python 3.10+编写
- 使用PySide6 开发桌面UI
- 使用专业化多模型架构：CLIP (文本-图像/视频)、CLAP (文本-音乐)、Whisper (语音-文本)
- 使用 **michaelfeil/infinity** 作为多模型服务引擎，提供高吞吐量、低延迟的嵌入模型服务
- 使用inaSpeechSegmenter进行音频内容智能分类
- 使用Qdrant作为向量数据库
- 使用FastAPI作为后台服务，实现后端核心程序与UI分离，确保UI变更不需要改核心程序
- 支持单机非docker安装

