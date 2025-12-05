# 需求文档

## 介绍

msearch 是一款跨平台多模态桌面检索软件，旨在打造"用户的第二大脑"，实现素材无需整理、无需标签的智能检索。该软件基于专业化多模型架构：使用 CLIP 模型进行文本-图像/视频检索、CLAP 模型进行文本-音乐检索、Whisper 模型进行语音转文本检索，结合 inaSpeechSegmenter 进行音频内容智能分类。系统采用 **michaelfeil/infinity** 作为高吞吐量、低延迟的多模型服务引擎，支持文本、图像、视频、音频四种模态的精准检索，通过实时监控和增量处理，为用户提供无缝的多媒体内容检索体验。

## 术语表

- **MSearch系统**: 完整的多模态检索应用，包括用户界面、后台服务和数据存储
- **Infinity引擎**: michaelfeil/infinity 高吞吐量、低延迟的模型服务引擎
- **CLIP模型**: 对比语言-图像预训练模型，用于文本-图像/视频检索
- **CLAP模型**: 对比语言-音频预训练模型，用于文本-音乐检索
- **Whisper模型**: OpenAI 的语音识别模型，用于音频转录
- **Qdrant数据库**: 用于存储和检索向量嵌入的向量数据库
- **向量嵌入**: 多媒体内容在高维空间中的数值表示
- **时序定位**: 识别视频内容中特定时间位置的过程
- **场景检测**: 自动识别视频中场景转换的过程
- **InaSpeechSegmenter**: 用于区分语音、音乐和噪声的音频分类工具
- **ANN检索**: 近似最近邻检索，用于高效向量相似度计算
- **MaxSim聚合**: 视频片段向量的最大相似度聚合方法
- **关键帧**: 从视频中提取的用于索引的代表性帧
- **模态**: 数据类型（文本、图像、视频、音频）
- **跨模态检索**: 使用一种模态的查询检索另一种模态的内容
- **人脸特征库**: 存储人脸嵌入和关联人名的数据库
- **FaceNet模型**: 用于人脸识别和嵌入生成的深度学习模型
- **Watchdog监控器**: 用于检测文件变化的文件系统监控服务
- **SQLite数据库**: 用于存储文件元数据的关系型数据库
- **REST接口**: 用于后端通信的RESTful应用程序编程接口
- **PySide6界面**: 基于Qt的桌面用户界面框架
- **FastAPI后端**: 用于后台服务的高性能Web框架
- **CUDA_INT8加速**: 使用8位整数量化的GPU加速
- **OpenVINO后端**: Intel的CPU推理优化工具包
- **FFmpeg工具**: 用于视频/音频处理的多媒体框架
- **场景片段**: 检测到的场景转换之间的视频部分（≤120秒）
- **缩略图**: 表示视频内容的小型预览图像
- **相似度分数**: 内容相关性的数值度量（0-1范围）

## 需求

### 需求 1: 基于文本的多模态检索

**用户故事:** 作为用户，我希望能够使用文本查询检索我的多媒体文件，以便快速找到相关内容而无需手动标记。

#### 验收标准

1. WHEN 用户输入文本查询时，THE MSearch系统 SHALL 使用CLIP模型和CLAP模型生成向量嵌入
2. WHEN MSearch系统接收到文本查询时，THE MSearch系统 SHALL 在2秒内返回匹配结果，容差为正0.5秒
3. WHEN MSearch系统返回视频结果时，THE MSearch系统 SHALL 包含关键帧缩略图和时间戳信息，精度为正负2秒以内
4. WHEN MSearch系统执行文本到视频检索时，THE MSearch系统 SHALL 应用时序定位来识别最相似的时间位置
5. WHEN MSearch系统显示检索结果时，THE MSearch系统 SHALL 显示按相似度分数排序的前20个最相关项目

### 需求 2: 基于图像的多模态检索

**用户故事:** 作为用户，我希望能够使用参考图像进行检索，以便在我的媒体库中找到视觉相似的内容。

#### 验收标准

1. WHEN 用户上传参考图像时，THE MSearch系统 SHALL 使用CLIP模型提取特征
2. WHEN MSearch系统处理图像查询时，THE MSearch系统 SHALL 在2秒内检索视觉相似的图像和视频，容差为正0.5秒
3. WHEN MSearch系统找到匹配的视频时，THE MSearch系统 SHALL 标记关键帧位置和时间戳，精度为正负2秒以内
4. WHEN MSearch系统执行图像到视频检索时，THE MSearch系统 SHALL 应用时序定位来识别匹配的时间位置
5. WHEN 用户拖拽图像文件到检索界面时，THE MSearch系统 SHALL 自动启动检索过程

### 需求 3: 基于音频的多模态检索

**用户故事:** 作为用户，我希望能够使用音频样本进行检索，以便找到包含相似声音或音乐的文件。

#### 验收标准

1. WHEN 用户上传音频样本时，THE MSearch系统 SHALL 使用InaSpeechSegmenter对音频类型进行分类
2. WHEN InaSpeechSegmenter识别出音乐内容时，THE MSearch系统 SHALL 使用CLAP模型生成向量嵌入
3. WHEN InaSpeechSegmenter识别出语音内容时，THE MSearch系统 SHALL 使用Whisper模型转录并按文本检索
4. WHEN MSearch系统处理音频查询时，THE MSearch系统 SHALL 在2秒内返回匹配结果，容差为正0.5秒
5. WHEN MSearch系统找到包含音频的匹配视频时，THE MSearch系统 SHALL 指示音频片段的时间戳

### 需求 4: 人脸识别与基于人名的检索

**用户故事:** 作为用户，我希望能够注册人脸和姓名并按人名检索，以便高精度地找到包含特定个人的所有媒体。

#### 验收标准

1. WHEN 用户上传人脸照片和人名时，THE MSearch系统 SHALL 使用FaceNet模型创建人脸特征库条目
2. WHEN MSearch系统处理新的图像或视频时，THE MSearch系统 SHALL 对人脸特征库进行检测和匹配，准确率达到95%或更高
3. WHEN 用户在查询中输入已注册的人名时，THE MSearch系统 SHALL 检索对应的人脸嵌入并将人脸模态权重提高1.5到2.0倍
4. WHEN MSearch系统检测到未知人脸时，THE MSearch系统 SHALL 提示用户将人脸添加到人脸特征库
5. WHEN MSearch系统执行人脸匹配时，THE MSearch系统 SHALL 在不同角度和光照条件下识别人脸，准确率达到95%或更高

### 需求 5: 目录监控与自动处理

**用户故事:** 作为用户，我希望能够通过UI配置要监控的目录，并让系统自动处理新文件，以便无需手动触发索引更新。

#### 验收标准

1. WHEN 用户通过UI配置监控目录时，THE MSearch系统 SHALL 为该目录启动Watchdog监控器
2. WHEN Watchdog监控器检测到新文件时，THE MSearch系统 SHALL 自动将文件元数据记录到SQLite数据库
3. WHEN Watchdog监控器检测到新文件时，THE MSearch系统 SHALL 在后台自动执行向量化处理
4. WHEN Watchdog监控器检测到文件删除或移动时，THE MSearch系统 SHALL 更新SQLite数据库并从Qdrant数据库中移除对应的向量
5. WHEN MSearch系统重启时，THE MSearch系统 SHALL 自动恢复所有已配置目录的监控状态
6. IF MSearch系统遇到处理错误，THEN MSearch系统 SHALL 记录错误日志并继续处理其他文件
7. WHEN 用户通过UI调整监控配置时，THE MSearch系统 SHALL 实时更新监控状态

### 需求 6: 手动操作控制

**用户故事:** 作为用户，我希望能够手动控制全量扫描和向量化处理，以便根据需要管理系统资源和处理进度。

#### 验收标准

1. WHEN 用户通过UI触发全量扫描时，THE MSearch系统 SHALL 扫描所有已配置监控目录的文件
2. WHEN 用户通过UI触发全量扫描时，THE MSearch系统 SHALL 为未入库文件创建元数据记录
3. WHEN 用户通过UI启动已入库文件的向量化时，THE MSearch系统 SHALL 对所有未向量化文件执行向量化处理
4. WHEN 用户通过UI启动向量化处理时，THE MSearch系统 SHALL 显示处理进度和预计完成时间
5. WHEN 用户通过UI取消正在进行的处理时，THE MSearch系统 SHALL 安全停止处理并保留已处理结果
6. WHEN MSearch系统执行手动操作时，THE MSearch系统 SHALL 优先使用用户指定的资源配置

### 需求 7: 智能图像预处理

**用户故事:** 作为用户，我希望系统能够自动优化图像文件，以便检索高效且存储优化。

#### 验收标准

1. WHEN MSearch系统处理图像文件时，THE MSearch系统 SHALL 使用CLIP模型生成向量嵌入
2. WHEN MSearch系统处理图像文件时，THE MSearch系统 SHALL 自动调整图像分辨率，确保长边不超过2048像素
3. WHEN MSearch系统处理图像文件时，THE MSearch系统 SHALL 转换为RGB格式
4. WHEN MSearch系统处理图像文件时，THE MSearch系统 SHALL 压缩图像质量，确保文件大小不超过10MB
5. WHEN MSearch系统处理图像文件时，THE MSearch系统 SHALL 提取图像元数据，包括拍摄时间、分辨率和格式
6. WHEN MSearch系统处理图像文件时，THE MSearch系统 SHALL 生成缩略图用于UI显示
7. WHEN MSearch系统处理超大图像文件（超过50MB）时，THE MSearch系统 SHALL 预处理为对AI大模型友好的格式规格，包括分辨率调整、质量压缩和格式转换
8. WHEN MSearch系统处理RAW格式图像时，THE MSearch系统 SHALL 自动转换为JPEG或PNG格式，并调整至合适大小，以优化模型处理效率

### 需求 8: 智能视频预处理

**用户故事:** 作为用户，我希望系统能够自动优化视频文件，以便检索高效且存储优化。

#### 验收标准

1. WHEN MSearch系统处理短边超过960像素的视频时，THE MSearch系统 SHALL 按比例调整至短边约960像素
2. WHEN MSearch系统处理视频文件时，THE MSearch系统 SHALL 转换为8帧每秒的H.264 8位MP4格式
3. WHEN MSearch系统处理超过120秒的视频时，THE MSearch系统 SHALL 使用FFmpeg工具的场景检测将其分割为120秒或更短的场景片段
4. WHEN MSearch系统完成视频分割时，THE MSearch系统 SHALL 以2秒间隔提取关键帧并使用CLIP模型进行向量化
5. WHEN MSearch系统对视频片段进行向量化时，THE MSearch系统 SHALL 应用MaxSim聚合来优化内存使用
6. WHEN MSearch系统处理带音频的视频时，THE MSearch系统 SHALL 使用InaSpeechSegmenter对音频内容进行分类
7. WHEN InaSpeechSegmenter仅检测到噪声或短于3秒的不清晰语音时，THE MSearch系统 SHALL 跳过该视频的音频向量化
8. WHEN MSearch系统处理超大视频文件（超过1GB）时，THE MSearch系统 SHALL 预处理为对AI大模型友好的格式规格，包括分辨率调整、帧率降低和分段处理
9. WHEN MSearch系统处理4K及以上分辨率视频时，THE MSearch系统 SHALL 自动降采样至1080p或720p，以优化模型处理效率

### 需求 9: 智能音频预处理

**用户故事:** 作为用户，我希望系统能够自动分类和优化音频文件，以便音频检索准确高效。

#### 验收标准

1. WHEN MSearch系统处理音频文件时，THE MSearch系统 SHALL 使用InaSpeechSegmenter区分音乐和语音内容
2. WHEN MSearch系统处理音频文件时，THE MSearch系统 SHALL 重采样为16 kHz单声道64 kbps AAC格式
3. WHEN InaSpeechSegmenter识别出音乐片段时，THE MSearch系统 SHALL 使用CLAP模型生成向量嵌入
4. WHEN InaSpeechSegmenter识别出语音片段时，THE MSearch系统 SHALL 使用Whisper模型进行转录
5. WHEN 用户配置音频处理策略时，THE MSearch系统 SHALL 通过配置文件提供视频音频流处理选项
6. WHEN MSearch系统处理超大音频文件（超过100MB）时，THE MSearch系统 SHALL 预处理为对AI大模型友好的格式规格，包括格式转换、采样率调整和分段处理
7. WHEN MSearch系统处理无损音频格式（如FLAC、WAV）时，THE MSearch系统 SHALL 自动转换为压缩格式并调整至合适大小，以优化模型处理效率

### 需求 10: 视频时序定位

**用户故事:** 作为视频剪辑人员，我希望在检索视频时能够快速找到相关片段和大致时间位置，以便直接跳转到所需内容。

#### 验收标准

1. WHEN MSearch系统检索视频内容时，THE MSearch系统 SHALL 返回包含时间戳信息的结果
2. WHEN MSearch系统执行时序定位时，THE MSearch系统 SHALL 达到正负2秒以内的精度，容差可达正负4秒
3. WHEN MSearch系统显示视频结果时，THE MSearch系统 SHALL 显示片段缩略图和时间位置
4. WHEN 用户点击视频结果时，THE MSearch系统 SHALL 在识别的时间戳处打开视频播放器
5. IF MSearch系统在一个视频中找到多个相似片段，THEN MSearch系统 SHALL 按相似度分数对结果进行排序

### 需求 11: 硬件自适应模型选择

**用户故事:** 作为用户，我希望系统能够根据我的硬件自动选择最优模型，以便获得最佳性能配置。

#### 验收标准

1. WHEN MSearch系统启动时，THE MSearch系统 SHALL 检测GPU、CPU和内存配置
2. IF MSearch系统检测到CUDA兼容GPU，THEN Infinity引擎 SHALL 使用CUDA_INT8加速
3. IF MSearch系统仅检测到支持OpenVINO的CPU，THEN Infinity引擎 SHALL 使用OpenVINO后端
4. IF MSearch系统检测到低硬件配置，THEN MSearch系统 SHALL 选择轻量级模型：CLIP-base、CLAP-base和Whisper-base
5. WHEN 用户切换模型时，THE MSearch系统 SHALL 从配置文件加载配置而无需修改代码

### 需求 12: 后端与界面分离

**用户故事:** 作为开发者，我希望桌面界面与后端逻辑完全分离，以便独立更新界面或拆分为微服务。

#### 验收标准

1. WHEN MSearch系统架构设计时，THE PySide6界面 SHALL 通过REST接口与FastAPI后端通信
2. WHEN FastAPI后端运行时，THE FastAPI后端 SHALL 为所有操作提供完整的REST接口端点
3. WHEN PySide6界面启动时，THE PySide6界面 SHALL 在没有后端连接的情况下独立运行基本界面操作
4. WHEN 开发者更新界面时，THE 开发者 SHALL 在不修改FastAPI后端代码的情况下进行更改
5. IF 系统需要微服务部署，THEN MSearch系统 SHALL 支持功能模块的独立部署

### 需求 13: 高性能向量检索

**用户故事:** 作为用户，我希望能够在大型多媒体集合中快速准确地检索，以便即使有数百万文件也能快速找到内容。

#### 验收标准

1. WHEN 用户执行检索时，THE MSearch系统 SHALL 在2秒内返回前20个结果
2. WHEN Qdrant数据库包含超过100万条记录时，THE MSearch系统 SHALL 保持检索性能而无明显下降
3. WHEN MSearch系统执行ANN检索时，THE Qdrant数据库 SHALL 高效计算向量相似度
4. WHEN 用户查询包含"音乐"或"歌曲"等关键词时，THE MSearch系统 SHALL 将CLAP模型权重提高1.5到2.0倍并将Whisper模型权重降低0.5到0.7倍
5. WHEN 用户查询包含"讲话"、"会议"或"语音"等关键词时，THE MSearch系统 SHALL 将Whisper模型权重提高1.5到2.0倍并将CLAP模型权重降低0.5到0.7倍
6. WHEN MSearch系统处理其他音频相关查询时，THE MSearch系统 SHALL 智能调整音频模型权重并优先使用Whisper模型

### 需求 14: 数据存储与管理

**用户故事:** 作为用户，我希望能够可靠地存储我的文件索引和向量数据，以便数据安全且易于备份。

#### 验收标准

1. WHEN MSearch系统处理文件时，THE MSearch系统 SHALL 在SQLite数据库中存储元数据
2. WHEN MSearch系统生成向量嵌入时，THE MSearch系统 SHALL 在Qdrant数据库中存储向量
3. WHEN MSearch系统异常关闭时，THE MSearch系统 SHALL 保持所有已处理内容的数据完整性
4. WHEN 用户请求备份时，THE MSearch系统 SHALL 提供数据导出功能
5. IF SQLite数据库或Qdrant数据库损坏，THEN MSearch系统 SHALL 提供数据恢复机制

### 需求 15: 跨平台兼容性

**用户故事:** 作为用户，我希望能够在Windows、macOS和Linux上使用相同的软件功能，以便在不同设备间无缝切换。

#### 验收标准

1. WHEN MSearch系统部署在Windows上时，THE MSearch系统 SHALL 正确执行所有功能
2. WHEN MSearch系统部署在macOS上时，THE MSearch系统 SHALL 正确执行所有功能
3. WHEN MSearch系统部署在Linux上时，THE MSearch系统 SHALL 正确执行所有功能
4. WHEN 用户在平台间迁移数据时，THE MSearch系统 SHALL 保持数据格式兼容性
5. IF MSearch系统遇到平台特定功能不可用，THEN MSearch系统 SHALL 提供替代方案或优雅降级

### 需求 16: 用户界面与交互

**用户故事:** 作为用户，我希望拥有直观响应的界面来进行检索操作和结果浏览，以便高效完成任务。

#### 验收标准

1. WHEN 用户打开应用程序时，THE PySide6界面 SHALL 在3秒内完全加载
2. WHEN 用户拖拽文件到检索框时，THE MSearch系统 SHALL 自动识别文件类型并启动检索
3. WHEN MSearch系统显示检索结果时，THE PySide6界面 SHALL 显示缩略图、文件路径和相似度分数
4. WHEN 用户点击视频结果时，THE MSearch系统 SHALL 打开视频播放器并跳转到关键帧位置
5. WHILE MSearch系统正在执行检索时，THE PySide6界面 SHALL 显示进度指示器和预计完成时间
6. WHEN 用户通过UI配置系统时，THE MSearch系统 SHALL 提供实时反馈和验证
7. WHEN 用户查看处理历史时，THE MSearch系统 SHALL 显示详细的处理日志和状态
