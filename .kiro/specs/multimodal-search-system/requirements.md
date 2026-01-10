# Requirements Document

## Introduction

msearch 是一款**单机可运行**的跨平台多模态桌面检索软件，专为视频剪辑师设计，实现素材无需整理、无需标签的智能检索。该软件基于专业化多模型架构，结合 inaSpeechSegmenter 进行音频内容智能分类，支持文本、图像、视频、音频四种模态的精准检索，通过实时监控和增量处理，为视频剪辑师提供高效、安全的多媒体内容检索体验。

## Requirements

### 需求 1: 文字混合检索

**用户故事:** 作为视频剪辑师，我希望能够使用自然语言描述检索我的多媒体文件，以便快速找到相关素材而无需手动标记。

**检索策略:**
- **默认模式**: 文字查询默认以"文搜图"和"文搜视频（纯视觉）"为主，音频权重占比为0
- **音乐检索**: 当查询文字包含"音乐"、"歌曲"、"BGM"、"背景音乐"等关键词时，根据配置调整CLAP模型权重比例
- **讲话检索**: 当查询文字包含"讲话"、"会议"、"语音"、"对话"、"演讲"等关键词时，根据配置调整Whisper模型权重比例
- **混合检索**: 支持同时检索图像、视频和音频，根据查询关键词动态调整各模态权重比例

#### 验收标准

1. WHEN 用户输入文本查询时，THE MSearch系统 SHALL 根据目标媒体类型选择对应的模型将检索输入转换为向量嵌入，确保向量维度与媒体处理对齐
2. WHEN MSearch系统执行文本到图像或文本到视频视觉检索时，THE MSearch系统 SHALL 使用apple/mobileclip、vidore/colSmol-500M或vidore/colqwen2.5-v0.2等硬件自适应模型进行文本向量化
3. WHEN MSearch系统执行文本到音乐音频检索时，THE MSearch系统 SHALL 使用CLAP模型进行文本向量化
4. WHEN MSearch系统执行文本到讲话音频检索时，THE MSearch系统 SHALL 使用与讲话音频处理相同的模型进行文本向量化
5. WHEN 用户查询包含"音乐"或"歌曲"等关键词时，THE MSearch系统 SHALL 根据配置将CLAP模型权重提高并将Whisper模型权重降低
6. WHEN 用户查询包含"讲话"、"会议"或"语音"等关键词时，THE MSearch系统 SHALL 根据配置将Whisper模型权重提高并将CLAP模型权重降低
7. WHEN MSearch系统接收到文本查询时，THE MSearch系统 SHALL 在2秒内返回匹配结果，容差为正0.5秒
8. WHEN MSearch系统返回视频结果时，THE MSearch系统 SHALL 包含视频文件路径、缩略图和时间戳等信息
9. WHEN MSearch系统执行文本到视频检索时，THE MSearch系统 SHALL 使用apple/mobileclip、vidore/colSmol-500M或vidore/colqwen2.5-v0.2等模型进行视频片段级检索和时序定位
10. WHEN MSearch系统显示检索结果时，THE MSearch系统 SHALL 显示按相似度分数排序的前20个最相关项目
11. WHEN 向量数据库包含超过10万条记录时，THE MSearch系统 SHALL 保持检索性能而无明显下降

### 需求 2: 图搜图、图搜视频

**用户故事:** 作为视频剪辑师，我希望能够使用参考图像进行检索，以便在我的媒体库中找到视觉相似的镜头或素材。

**检索策略:**
- **图搜图**: 使用参考图像检索视觉相似的静态图像
- **图搜视频**: 使用参考图像检索视频中视觉相似的片段，返回时间戳信息
- **视觉相似度**: 基于颜色、纹理、构图等视觉特征进行相似度匹配

#### 验收标准

1. WHEN 用户上传参考图像时，THE MSearch系统 SHALL 使用硬件自适应模型（apple/mobileclip、vidore/colSmol-500M或vidore/colqwen2.5-v0.2）提取特征
2. WHEN MSearch系统执行图搜图检索时，THE MSearch系统 SHALL 返回视觉相似的图像结果，按相似度分数排序
3. WHEN MSearch系统执行图搜视频检索时，THE MSearch系统 SHALL 使用硬件自适应模型（apple/mobileclip、vidore/colSmol-500M或vidore/colqwen2.5-v0.2）进行视频片段级检索和时序定位
4. WHEN MSearch系统找到匹配的视频时，THE MSearch系统 SHALL 标记视频片段位置和时间戳，精度为正负5秒以内
5. WHEN 用户拖拽图像文件到检索界面时，THE MSearch系统 SHALL 自动启动检索过程
6. WHEN MSearch系统处理图像查询时，THE MSearch系统 SHALL 在2秒内返回匹配结果，容差为正0.5秒

### 需求 3: 音频找相似音频、找包含相似音频的视频

**用户故事:** 作为视频剪辑师，我希望能够使用音频样本进行检索，以便找到包含相似声音或音乐的文件。

**检索策略:**
- **音频找音频**: 使用CLAP模型检索音频相似的音频文件
- **音频找视频**: 使用CLAP模型检索包含相似音频的视频片段，返回时间戳信息
- **音频分类**: 使用InaSpeechSegmenter区分音乐和语音内容，优化检索精度

#### 验收标准

1. WHEN 用户上传音频样本时，THE MSearch系统 SHALL 使用CLAP模型生成向量嵌入
2. WHEN MSearch系统执行音频找音频检索时，THE MSearch系统 SHALL 返回音频相似的音频文件，按相似度分数排序
3. WHEN MSearch系统执行音频找视频检索时，THE MSearch系统 SHALL 使用CLAP模型进行视频音频片段级检索和时序定位
4. WHEN MSearch系统找到包含音频的匹配视频时，THE MSearch系统 SHALL 指示音频片段的时间戳
5. WHEN MSearch系统处理音频查询时，THE MSearch系统 SHALL 在2秒内返回匹配结果，容差为正0.5秒
6. WHEN 用户拖拽音频文件到检索界面时，THE MSearch系统 SHALL 自动启动检索过程

### 需求 4: 人脸识别与基于人名的检索（可选功能）

**用户故事:** 作为视频剪辑师，我希望能够选择性地注册人脸和姓名并按人名检索，以便高精度地找到包含特定个人的所有媒体。

#### 验收标准

1. WHEN 用户选择启用人脸识别功能时，THE MSearch系统 SHALL 提供人脸注册界面
2. WHEN 用户上传人脸照片和人名时，THE MSearch系统 SHALL 使用FaceNet模型创建人脸特征库条目
3. WHEN MSearch系统处理新的图像或视频时，THE MSearch系统 SHALL 对人脸特征库进行检测和匹配，准确率达到95%或更高
4. WHEN 用户在查询中输入已注册的人名时，THE MSearch系统 SHALL 检索对应的人脸嵌入并将人脸模态权重提高1.5到2.0倍
5. WHEN MSearch系统检测到未知人脸时，THE MSearch系统 SHALL 可选提示用户将人脸添加到人脸特征库

### 需求 5: 目录监控与自动处理

**用户故事:** 作为视频剪辑师，我希望能够通过UI配置要监控的目录，并让系统自动处理新文件，以便无需手动触发索引更新。

#### 验收标准

1. WHEN 用户通过UI配置监控目录时，THE MSearch系统 SHALL 为该目录启动Watchdog监控器
2. WHEN Watchdog监控器检测到新文件时，THE MSearch系统 SHALL 自动将文件元数据记录到本地数据库
3. WHEN Watchdog监控器检测到新文件时，THE MSearch系统 SHALL 在后台自动执行向量化处理
4. WHEN Watchdog监控器检测到文件删除或移动时，THE MSearch系统 SHALL 更新本地数据库并从向量数据库中移除对应的向量
5. WHEN MSearch系统重启时，THE MSearch系统 SHALL 自动恢复所有已配置目录的监控状态
6. IF MSearch系统遇到处理错误，THEN MSearch系统 SHALL 记录错误日志并继续处理其他文件
7. WHEN 用户通过UI调整监控配置时，THE MSearch系统 SHALL 实时更新监控状态

### 需求 6: 手动操作控制

**用户故事:** 作为视频剪辑师，我希望能够手动控制全量扫描和向量化处理，以便根据需要管理系统资源和处理进度。

#### 验收标准

1. WHEN 用户通过UI触发全量扫描时，THE MSearch系统 SHALL 扫描所有已配置监控目录的文件
2. WHEN 用户通过UI触发全量扫描时，THE MSearch系统 SHALL 为未入库文件创建元数据记录
3. WHEN 用户通过UI启动已入库文件的向量化时，THE MSearch系统 SHALL 对所有未向量化文件执行向量化处理
4. WHEN 用户通过UI启动向量化处理时，THE MSearch系统 SHALL 显示处理进度和预计完成时间
5. WHEN 用户通过UI取消正在进行的处理时，THE MSearch系统 SHALL 安全停止处理并保留已处理结果
6. WHEN MSearch系统执行手动操作时，THE MSearch系统 SHALL 优先使用用户指定的资源配置

### 需求 7: 智能视频预处理

**用户故事:** 作为视频剪辑师，我希望系统能够自动将视频文件优化为对AI模型友好的格式，并通过场景分割和片段级向量化降低计算时间和存储空间，以便优化程序运行效率并降低内存开销，同时保持原始素材不变。

**核心目标:**
- **格式优化**: 将原始视频转换为硬件自适应模型（apple/mobileclip、vidore/colSmol-500M或vidore/colqwen2.5-v0.2）的标准输入格式（H.264 MP4、RGB色彩空间）
- **内存保护**: 通过分辨率限制、场景分割、片段级向量化等策略，防止大模型处理时爆内存
- **性能优化**: 使用硬件自适应模型进行片段级向量化，替代逐帧向量化，大幅减少计算时间和向量存储量
- **时序定位**: 视频预处理与视频时序定位紧密耦合，场景分割为时序定位提供基础切片和时间戳信息

#### 验收标准

1. WHEN MSearch系统处理短边超过960像素的视频时，THE MSearch系统 SHALL 按比例调整至短边约960像素（仅用于索引，不修改原始文件）
2. WHEN MSearch系统处理视频文件时，THE MSearch系统 SHALL 转换为H.264 8位MP4格式（仅用于索引）
3. WHEN MSearch系统处理超过120秒的视频时，THE MSearch系统 SHALL 使用FFmpeg工具的场景检测将其分割为120秒或更短的场景片段
4. WHEN MSearch系统完成视频分割时，THE MSearch系统 SHALL 使用硬件自适应模型（apple/mobileclip、vidore/colSmol-500M或vidore/colqwen2.5-v0.2）对视频片段进行片段级向量化，而非逐帧向量化
5. WHEN MSearch系统对视频片段进行向量化时，THE MSearch系统 SHALL 优化内存使用，避免大模型处理时爆内存
6. WHEN MSearch系统处理带音频的视频时，THE MSearch系统 SHALL 使用InaSpeechSegmenter对音频内容进行分类
7. WHEN InaSpeechSegmenter仅检测到噪声或短于3秒的不清晰语音时，THE MSearch系统 SHALL 跳过该视频的音频向量化
8. WHEN MSearch系统处理4K及以上分辨率视频时，THE MSearch系统 SHALL 自动降采样至1080p或720p（仅用于索引），以优化模型处理效率
9. WHEN MSearch系统完成视频场景分割时，THE MSearch系统 SHALL 为每个切片记录在原始视频中的起止时间（start_time、end_time）和切片标识（segment_id、segment_index）
10. WHEN MSearch系统对视频片段进行向量化时，THE MSearch系统 SHALL 将切片时间戳信息与向量嵌入一起存储，为视频时序定位提供基础数据
11. WHEN MSearch系统执行视频预处理时，THE MSearch系统 SHALL 确保切片时间戳精度在正负5秒以内，满足视频时序定位的需求

### 需求 8: 智能图像预处理

**用户故事:** 作为视频剪辑师，我希望系统能够自动将图像文件优化为对AI模型友好的格式，并通过分辨率限制和格式转换降低内存消耗，以便优化程序运行效率并降低内存开销，同时保持原始素材不变。

**核心目标:**
- **格式优化**: 将原始图像转换为硬件自适应模型（apple/mobileclip、vidore/colSmol-500M或vidore/colqwen2.5-v0.2）的标准输入格式（RGB色彩空间、标准化分辨率）
- **内存保护**: 通过分辨率限制（长边≤2048px）、超大文件分块处理等策略，防止大模型处理时爆内存

#### 验收标准

1. WHEN MSearch系统处理图像文件时，THE MSearch系统 SHALL 使用硬件自适应模型（apple/mobileclip、vidore/colSmol-500M或vidore/colqwen2.5-v0.2）生成向量嵌入
2. WHEN MSearch系统处理图像文件时，THE MSearch系统 SHALL 自动调整图像分辨率，确保长边不超过2048像素（仅用于索引）
3. WHEN MSearch系统处理图像文件时，THE MSearch系统 SHALL 转换为RGB格式（仅用于索引）
4. WHEN MSearch系统处理图像文件时，THE MSearch系统 SHALL 生成缩略图用于UI显示
5. WHEN MSearch系统处理超大图像文件（超过50MB）时，THE MSearch系统 SHALL 预处理为对AI模型友好的格式规格（仅用于索引）
6. WHEN MSearch系统处理RAW格式图像时，THE MSearch系统 SHALL 自动转换为JPEG或PNG格式（仅用于索引），并调整至合适大小

### 需求 9: 智能音频预处理

**用户故事:** 作为视频剪辑师，我希望系统能够自动将音频文件优化为对AI模型友好的格式，并通过重采样和格式转换降低内存消耗，以便优化程序运行效率并降低内存开销，同时保持原始素材不变。

**核心目标:**
- **格式优化**: 将原始音频转换为CLAP/Whisper模型的标准输入格式（16kHz单声道AAC）
- **内存保护**: 通过重采样、无损格式转换、超大文件分块处理等策略，防止大模型处理时爆内存

#### 验收标准

1. WHEN MSearch系统处理音频文件时，THE MSearch系统 SHALL 使用InaSpeechSegmenter区分音乐和语音内容
2. WHEN MSearch系统处理音频文件时，THE MSearch系统 SHALL 重采样为16 kHz单声道64 kbps AAC格式（仅用于索引）
3. WHEN InaSpeechSegmenter识别出音乐片段时，THE MSearch系统 SHALL 使用CLAP模型生成向量嵌入
4. WHEN InaSpeechSegmenter识别出语音片段时，THE MSearch系统 SHALL 使用Whisper模型进行转录
5. WHEN MSearch系统处理超大音频文件（超过100MB）时，THE MSearch系统 SHALL 预处理为对AI模型友好的格式规格（仅用于索引）
6. WHEN MSearch系统处理无损音频格式（如FLAC、WAV）时，THE MSearch系统 SHALL 自动转换为压缩格式（仅用于索引）并调整至合适大小

### 需求 10: 视频时序定位

**用户故事:** 作为视频剪辑师，我希望在检索视频时能够快速找到相关片段和大致时间位置，以便直接跳转到所需内容。

**说明:** 系统使用硬件自适应模型（apple/mobileclip、vidore/colSmol-500M或vidore/colqwen2.5-v0.2）进行视频片段级检索和时序定位，相比逐帧向量化大幅降低计算时间和存储空间，但时间定位精度从±2秒降低至±5秒。

#### 验收标准

1. WHEN MSearch系统检索视频内容时，THE MSearch系统 SHALL 返回包含时间戳信息的结果
2. WHEN MSearch系统执行时序定位时，THE MSearch系统 SHALL 达到正负5秒以内的精度，容差可达正负10秒
3. WHEN MSearch系统显示视频结果时，THE MSearch系统 SHALL 显示片段缩略图和时间位置
4. WHEN 用户点击视频结果时，THE MSearch系统 SHALL 提供选项在识别的时间戳处打开系统默认视频播放器
5. IF MSearch系统在一个视频中找到多个相似片段，THEN MSearch系统 SHALL 按相似度分数对结果进行排序
6. WHEN MSearch系统返回视频检索结果时，THE MSearch系统 SHALL 包含原始视频文件的完整路径和文件名
7. WHEN MSearch系统返回视频检索结果时，THE MSearch系统 SHALL 包含切片标识信息（segment_id、segment_index）以便区分同一视频的不同切片
8. WHEN MSearch系统返回视频检索结果时，THE MSearch系统 SHALL 包含切片在原始视频中的起止时间（start_time、end_time）
9. WHEN MSearch系统返回视频检索结果时，THE MSearch系统 SHALL 包含硬件自适应模型（apple/mobileclip、vidore/colSmol-500M或vidore/colqwen2.5-v0.2）预测的片段中心时间戳（segment_center_timestamp）用于定位
10. IF MSearch系统对同一视频文件检索出多个切片结果，THEN MSearch系统 SHALL 能够按原始视频时间顺序聚合显示这些结果
11. WHEN MSearch系统显示视频检索结果时，THE MSearch系统 SHALL 明确标识结果来自切片文件还是完整文件
12. WHEN MSearch系统检索到视频切片结果时，THE MSearch系统 SHALL 提供从切片结果跳转到原始视频文件的完整路径和对应时间戳的功能

### 需求 11: 数据存储与管理

**用户故事:** 作为视频剪辑师，我希望能够可靠地存储我的文件索引和向量数据，以便数据安全且易于备份。

#### 验收标准

1. WHEN MSearch系统处理文件时，THE MSearch系统 SHALL 在本地SQLite数据库中存储元数据
2. WHEN MSearch系统生成向量嵌入时，THE MSearch系统 SHALL 在本地 LanceDB 向量数据库中存储向量
3. WHEN MSearch系统异常关闭时，THE MSearch系统 SHALL 保持所有已处理内容的数据完整性
4. WHEN 用户请求备份时，THE MSearch系统 SHALL 提供数据导出功能
5. IF 本地数据库损坏，THEN MSearch系统 SHALL 提供数据恢复机制

### 需求 12: 跨平台兼容性

**用户故事:** 作为视频剪辑师，我希望能够在Windows、macOS和Linux上使用相同的软件功能，以便在不同设备间无缝切换。

#### 验收标准

1. WHEN MSearch系统部署在Windows上时，THE MSearch系统 SHALL 正确执行所有功能
2. WHEN MSearch系统部署在macOS上时，THE MSearch系统 SHALL 正确执行所有功能
3. WHEN MSearch系统部署在Linux上时，THE MSearch系统 SHALL 正确执行所有功能
4. WHEN 用户在平台间迁移数据时，THE MSearch系统 SHALL 保持数据格式兼容性
5. IF MSearch系统遇到平台特定功能不可用，THEN MSearch系统 SHALL 提供替代方案或优雅降级

### 需求 13: 用户界面与交互

**用户故事:** 作为视频剪辑师，我希望拥有直观响应的界面来进行检索操作和结果浏览，以便高效完成任务。

#### 验收标准

1. WHEN 用户打开应用程序时，THE MSearch系统 SHALL 在3秒内完全加载界面
2. WHEN 用户拖拽文件到检索框时，THE MSearch系统 SHALL 自动识别文件类型并启动检索
3. WHEN MSearch系统显示检索结果时，THE MSearch系统 SHALL 显示缩略图、文件路径、相似度分数和时间戳（如果是视频/音频）
4. WHEN 用户点击视频结果时，THE MSearch系统 SHALL 提供选项在系统默认视频播放器中打开视频并跳转到关键帧位置
5. WHEN 用户点击音频结果时，THE MSearch系统 SHALL 提供选项在系统默认音频播放器中打开音频
6. WHILE MSearch系统正在执行检索时，THE MSearch系统 SHALL 显示进度指示器和预计完成时间
7. WHEN 用户通过UI配置系统时，THE MSearch系统 SHALL 提供实时反馈和验证
8. WHEN 用户查看处理历史时，THE MSearch系统 SHALL 显示详细的处理日志和状态
9. WHEN 用户浏览检索结果时，THE MSearch系统 SHALL 支持按媒体类型（视频、音频、图像）过滤
10. WHEN 用户浏览检索结果时，THE MSearch系统 SHALL 支持按相似度分数、文件大小、创建时间等排序
11. WHEN 用户预览视频结果时，THE MSearch系统 SHALL 提供视频预览功能，支持播放、暂停和进度拖动
12. WHEN 用户预览音频结果时，THE MSearch系统 SHALL 显示音频波形和播放控制
13. WHEN 用户选择检索结果时，THE MSearch系统 SHALL 提供选项将素材直接导入到常用剪辑软件（如Premiere Pro、Final Cut Pro）
14. WHEN 用户处理大量素材时，THE MSearch系统 SHALL 支持批量选择和操作检索结果

### 需求 14: 易用性与稳定性

**用户故事:** 作为视频剪辑师，我希望在安装系统时能够自动检测我的硬件配置并选择最优模型，安装完成后能够通过设置向导完成基本配置，以便拥有一个简单易用、稳定可靠的工具，专注于我的创作工作。

**核心功能:**
- **硬件自适应模型选择**: 安装时自动检测GPU、CPU和内存配置，根据硬件选择最优模型
- **设置向导**: 首次启动时提供简洁的设置向导，引导用户完成基本配置
- **模型配置**: 支持用户在设置中切换模型，从配置文件加载配置而无需修改代码

#### 验收标准

1. WHEN 用户安装MSearch系统时，THE MSearch系统 SHALL 检测GPU、CPU和内存配置
2. IF MSearch系统检测到CUDA兼容GPU，THEN 模型 SHALL 使用CUDA_INT8加速
3. IF MSearch系统仅检测到支持OpenVINO的CPU，THEN 模型 SHALL 使用OpenVINO后端
4. IF MSearch系统检测到低硬件配置，THEN MSearch系统 SHALL 选择轻量级模型：apple/mobileclip、CLAP-base和Whisper-base
5. WHEN 用户首次打开应用程序时，THE MSearch系统 SHALL 提供简洁的设置向导，引导用户完成基本配置
6. WHEN 用户使用应用程序时，THE MSearch系统 SHALL 提供清晰的操作指引和帮助信息
7. WHEN MSearch系统执行操作时，THE MSearch系统 SHALL 提供明确的反馈信息
8. WHEN MSearch系统遇到错误时，THE MSearch系统 SHALL 显示友好的错误信息，而非技术错误代码
9. WHEN 用户切换模型时，THE MSearch系统 SHALL 从配置文件加载配置而无需修改代码
10. WHEN 用户关闭应用程序时，THE MSearch系统 SHALL 安全保存所有数据和状态
11. WHEN MSearch系统运行时，THE MSearch系统 SHALL 保持稳定，崩溃率低于0.1%
12. WHEN MSearch系统处理大文件时，THE MSearch系统 SHALL 保持稳定，不会出现内存溢出或崩溃
13. WHEN 用户使用应用程序时，THE MSearch系统 SHALL 保持界面响应，不会出现卡顿或无响应

### 需求 15: 后端与前端UI分离

**用户故事:** 作为开发者，我希望系统能够保持后端与前端UI分离的结构，降低代码耦合，确保后端逻辑与前端分离，同时为日后升级为服务化架构提供基础。

#### 验收标准

1. WHEN MSearch系统设计时，THE 后端 SHALL 与前端UI完全分离
2. WHEN MSearch系统提供接口时，THE 后端 SHALL 仅提供检索、修改配置等必要接口
3. WHEN MSearch系统运行时，THE 前端UI SHALL 通过标准API与后端通信
4. WHEN MSearch系统升级时，THE 后端与前端UI SHALL 能够独立升级
5. WHEN MSearch系统部署时，THE 后端与前端UI SHALL 能够独立部署

### 需求 16: 本地运行与数据安全

**用户故事:** 做为一款桌面应用，MSearch系统能够在本地运行，不依赖互联网，以保证我的素材和项目的安全性。

#### 验收标准

1. WHEN MSearch系统运行时，THE MSearch系统 SHALL 完全在本地运行，不依赖互联网连接
2. WHEN MSearch系统存储数据时，THE MSearch系统 SHALL 将所有数据存储在本地，不发送到任何远程服务器
3. WHEN MSearch系统处理文件时，THE MSearch系统 SHALL 仅访问用户明确指定的目录
4. WHEN MSearch系统生成索引时，THE MSearch系统 SHALL 不修改原始文件
5. WHEN MSearch系统删除索引时，THE MSearch系统 SHALL 不影响原始文件
