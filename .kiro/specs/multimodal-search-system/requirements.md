# Requirements Document

## Introduction

msearch 是一款**单机可运行**的跨平台多模态桌面检索软件，专为视频剪辑师设计，实现素材无需整理、无需标签的智能检索。该软件基于专业化多模型架构：使用 CLIP 模型进行文本-图像/视频检索、CLAP 模型进行文本-音乐检索、Whisper 模型进行语音转文本检索，结合 inaSpeechSegmenter 进行音频内容智能分类。系统采用 **michaelfeil/infinity** 作为高吞吐量、低延迟的多模型服务引擎，支持文本、图像、视频、音频四种模态的精准检索，通过实时监控和增量处理，为视频剪辑师提供高效、安全的多媒体内容检索体验。

## Glossary

- **MSearch系统**: 完整的多模态检索应用，包括用户界面、后台服务和数据存储（单机运行）
- **Infinity引擎**: michaelfeil/infinity 高吞吐量、低延迟的模型服务引擎
- **CLIP模型**: 对比语言-图像预训练模型，用于文本-图像检索
- **CLIP4Clip模型**: 基于CLIP的视频-文本检索模型，用于文本-视频片段检索和时序定位
- **CLAP模型**: 对比语言-音频预训练模型，用于文本-音乐检索
- **Whisper模型**: OpenAI 的语音识别模型，用于音频转录
- **向量数据库**: 用于存储和检索向量嵌入的本地 Milvus Lite 向量数据库
- **向量嵌入**: 多媒体内容在高维空间中的数值表示（用于相似度匹配）
- **时序定位**: 识别视频内容中特定时间位置的过程
- **场景检测**: 自动识别视频中场景转换的过程
- **InaSpeechSegmenter**: 用于区分语音、音乐和噪声的音频分类工具
- **关键帧**: 从视频中提取的用于索引的代表性帧
- **模态**: 数据类型（文本、图像、视频、音频）
- **跨模态检索**: 使用一种模态的查询检索另一种模态的内容

## Requirements

### 需求 1: 基于文本的多模态检索

**用户故事:** 作为视频剪辑师，我希望能够使用自然语言描述检索我的多媒体文件，以便快速找到相关素材而无需手动标记。

#### 验收标准

1. WHEN 用户输入文本查询时，THE MSearch系统 SHALL 使用CLIP4Clip模型、CLIP模型和CLAP模型生成向量嵌入
2. WHEN MSearch系统接收到文本查询时，THE MSearch系统 SHALL 在2秒内返回匹配结果，容差为正0.5秒
3. WHEN MSearch系统返回视频结果时，THE MSearch系统 SHALL 包含视频片段缩略图和时间戳信息，精度为正负5秒以内
4. WHEN MSearch系统执行文本到视频检索时，THE MSearch系统 SHALL 使用CLIP4Clip模型进行视频片段级检索和时序定位
5. WHEN MSearch系统显示检索结果时，THE MSearch系统 SHALL 显示按相似度分数排序的前20个最相关项目

### 需求 2: 基于图像的多模态检索

**用户故事:** 作为视频剪辑师，我希望能够使用参考图像进行检索，以便在我的媒体库中找到视觉相似的镜头或素材。

#### 验收标准

1. WHEN 用户上传参考图像时，THE MSearch系统 SHALL 使用CLIP模型提取特征
2. WHEN MSearch系统处理图像查询时，THE MSearch系统 SHALL 在2秒内检索视觉相似的图像和视频，容差为正0.5秒
3. WHEN MSearch系统找到匹配的视频时，THE MSearch系统 SHALL 标记视频片段位置和时间戳，精度为正负5秒以内
4. WHEN MSearch系统执行图像到视频检索时，THE MSearch系统 SHALL 使用CLIP4Clip模型进行视频片段级检索和时序定位
5. WHEN 用户拖拽图像文件到检索界面时，THE MSearch系统 SHALL 自动启动检索过程

### 需求 3: 基于音频的多模态检索

**用户故事:** 作为视频剪辑师，我希望能够使用音频样本进行检索，以便找到包含相似声音或音乐的文件。

#### 验收标准

1. WHEN 用户上传音频样本时，THE MSearch系统 SHALL 使用InaSpeechSegmenter对音频类型进行分类
2. WHEN InaSpeechSegmenter识别出音乐内容时，THE MSearch系统 SHALL 使用CLAP模型生成向量嵌入
3. WHEN InaSpeechSegmenter识别出语音内容时，THE MSearch系统 SHALL 使用Whisper模型转录并按文本检索
4. WHEN MSearch系统处理音频查询时，THE MSearch系统 SHALL 在2秒内返回匹配结果，容差为正0.5秒
5. WHEN MSearch系统找到包含音频的匹配视频时，THE MSearch系统 SHALL 指示音频片段的时间戳

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

**用户故事:** 作为视频剪辑师，我希望系统能够自动将视频文件优化为对AI模型友好的格式，并通过场景分割和片段级向量化降低计算时间和存储空间，以便检索高效且避免大模型处理时出现内存溢出，同时保持原始素材不变。

**核心目标:**
- **格式优化**: 将原始视频转换为CLIP4Clip模型的标准输入格式（H.264 MP4、RGB色彩空间）
- **内存保护**: 通过分辨率限制、场景分割、片段级向量化等策略，防止大模型处理时爆内存
- **性能优化**: 使用CLIP4Clip进行片段级向量化，替代逐帧向量化，大幅减少计算时间和向量存储量

#### 验收标准

1. WHEN MSearch系统处理短边超过960像素的视频时，THE MSearch系统 SHALL 按比例调整至短边约960像素（仅用于索引，不修改原始文件）
2. WHEN MSearch系统处理视频文件时，THE MSearch系统 SHALL 转换为H.264 8位MP4格式（仅用于索引）
3. WHEN MSearch系统处理超过120秒的视频时，THE MSearch系统 SHALL 使用FFmpeg工具的场景检测将其分割为120秒或更短的场景片段
4. WHEN MSearch系统完成视频分割时，THE MSearch系统 SHALL 使用CLIP4Clip模型对视频片段进行片段级向量化，而非逐帧向量化
5. WHEN MSearch系统对视频片段进行向量化时，THE MSearch系统 SHALL 优化内存使用，避免大模型处理时爆内存
6. WHEN MSearch系统处理带音频的视频时，THE MSearch系统 SHALL 使用InaSpeechSegmenter对音频内容进行分类
7. WHEN InaSpeechSegmenter仅检测到噪声或短于3秒的不清晰语音时，THE MSearch系统 SHALL 跳过该视频的音频向量化
8. WHEN MSearch系统处理4K及以上分辨率视频时，THE MSearch系统 SHALL 自动降采样至1080p或720p（仅用于索引），以优化模型处理效率

### 需求 8: 智能图像预处理

**用户故事:** 作为视频剪辑师，我希望系统能够自动将图像文件优化为对AI模型友好的格式，并通过分辨率限制和格式转换降低内存消耗，以便检索高效且避免大模型处理时出现内存溢出，同时保持原始素材不变。

**核心目标:**
- **格式优化**: 将原始图像转换为CLIP模型的标准输入格式（RGB色彩空间、标准化分辨率）
- **内存保护**: 通过分辨率限制（长边≤2048px）、超大文件分块处理等策略，防止大模型处理时爆内存

#### 验收标准

1. WHEN MSearch系统处理图像文件时，THE MSearch系统 SHALL 使用CLIP模型生成向量嵌入
2. WHEN MSearch系统处理图像文件时，THE MSearch系统 SHALL 自动调整图像分辨率，确保长边不超过2048像素（仅用于索引）
3. WHEN MSearch系统处理图像文件时，THE MSearch系统 SHALL 转换为RGB格式（仅用于索引）
4. WHEN MSearch系统处理图像文件时，THE MSearch系统 SHALL 生成缩略图用于UI显示
5. WHEN MSearch系统处理超大图像文件（超过50MB）时，THE MSearch系统 SHALL 预处理为对AI模型友好的格式规格（仅用于索引）
6. WHEN MSearch系统处理RAW格式图像时，THE MSearch系统 SHALL 自动转换为JPEG或PNG格式（仅用于索引），并调整至合适大小

### 需求 9: 智能音频预处理

**用户故事:** 作为视频剪辑师，我希望系统能够自动将音频文件优化为对AI模型友好的格式，并通过重采样和格式转换降低内存消耗，以便音频检索准确高效且避免大模型处理时出现内存溢出，同时保持原始素材不变。

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

**说明:** 系统使用CLIP4Clip模型进行视频片段级检索和时序定位，相比逐帧向量化大幅降低计算时间和存储空间，但时间定位精度从±2秒降低至±5秒。

#### 验收标准

1. WHEN MSearch系统检索视频内容时，THE MSearch系统 SHALL 返回包含时间戳信息的结果
2. WHEN MSearch系统执行时序定位时，THE MSearch系统 SHALL 达到正负5秒以内的精度，容差可达正负10秒
3. WHEN MSearch系统显示视频结果时，THE MSearch系统 SHALL 显示片段缩略图和时间位置
4. WHEN 用户点击视频结果时，THE MSearch系统 SHALL 提供选项在识别的时间戳处打开系统默认视频播放器
5. IF MSearch系统在一个视频中找到多个相似片段，THEN MSearch系统 SHALL 按相似度分数对结果进行排序
6. WHEN MSearch系统返回视频检索结果时，THE MSearch系统 SHALL 包含原始视频文件的完整路径和文件名
7. WHEN MSearch系统返回视频检索结果时，THE MSearch系统 SHALL 包含切片标识信息（segment_id、segment_index）以便区分同一视频的不同切片
8. WHEN MSearch系统返回视频检索结果时，THE MSearch系统 SHALL 包含切片在原始视频中的起止时间（start_time、end_time）
9. WHEN MSearch系统返回视频检索结果时，THE MSearch系统 SHALL 包含CLIP4Clip模型预测的片段中心时间戳（segment_center_timestamp）用于定位
10. IF MSearch系统对同一视频文件检索出多个切片结果，THEN MSearch系统 SHALL 能够按原始视频时间顺序聚合显示这些结果
11. WHEN MSearch系统显示视频检索结果时，THE MSearch系统 SHALL 明确标识结果来自切片文件还是完整文件
12. WHEN MSearch系统检索到视频切片结果时，THE MSearch系统 SHALL 提供从切片结果跳转到原始视频文件的完整路径和对应时间戳的功能

### 需求 11: 硬件自适应模型选择

**用户故事:** 作为视频剪辑师，我希望系统能够根据我的硬件自动选择最优模型，以便获得最佳性能配置。

#### 验收标准

1. WHEN MSearch系统启动时，THE MSearch系统 SHALL 检测GPU、CPU和内存配置
2. IF MSearch系统检测到CUDA兼容GPU，THEN Infinity引擎 SHALL 使用CUDA_INT8加速
3. IF MSearch系统仅检测到支持OpenVINO的CPU，THEN Infinity引擎 SHALL 使用OpenVINO后端
4. IF MSearch系统检测到低硬件配置，THEN MSearch系统 SHALL 选择轻量级模型：CLIP-base、CLAP-base和Whisper-base
5. WHEN 用户切换模型时，THE MSearch系统 SHALL 从配置文件加载配置而无需修改代码

### 需求 12: 高性能向量检索

**用户故事:** 作为视频剪辑师，我希望能够在我的媒体库中快速准确地检索，以便即使有数万文件也能快速找到内容。

#### 验收标准

1. WHEN 用户执行检索时，THE MSearch系统 SHALL 在2秒内返回前20个结果
2. WHEN 向量数据库包含超过10万条记录时，THE MSearch系统 SHALL 保持检索性能而无明显下降
3. WHEN 用户查询包含"音乐"或"歌曲"等关键词时，THE MSearch系统 SHALL 将CLAP模型权重提高1.5到2.0倍并将Whisper模型权重降低0.5到0.7倍
4. WHEN 用户查询包含"讲话"、"会议"或"语音"等关键词时，THE MSearch系统 SHALL 将Whisper模型权重提高1.5到2.0倍并将CLAP模型权重降低0.5到0.7倍

### 需求 13: 数据存储与管理

**用户故事:** 作为视频剪辑师，我希望能够可靠地存储我的文件索引和向量数据，以便数据安全且易于备份。

#### 验收标准

1. WHEN MSearch系统处理文件时，THE MSearch系统 SHALL 在本地SQLite数据库中存储元数据
2. WHEN MSearch系统生成向量嵌入时，THE MSearch系统 SHALL 在本地 Milvus Lite 向量数据库中存储向量
3. WHEN MSearch系统异常关闭时，THE MSearch系统 SHALL 保持所有已处理内容的数据完整性
4. WHEN 用户请求备份时，THE MSearch系统 SHALL 提供数据导出功能
5. IF 本地数据库损坏，THEN MSearch系统 SHALL 提供数据恢复机制

### 需求 14: 跨平台兼容性

**用户故事:** 作为视频剪辑师，我希望能够在Windows、macOS和Linux上使用相同的软件功能，以便在不同设备间无缝切换。

#### 验收标准

1. WHEN MSearch系统部署在Windows上时，THE MSearch系统 SHALL 正确执行所有功能
2. WHEN MSearch系统部署在macOS上时，THE MSearch系统 SHALL 正确执行所有功能
3. WHEN MSearch系统部署在Linux上时，THE MSearch系统 SHALL 正确执行所有功能
4. WHEN 用户在平台间迁移数据时，THE MSearch系统 SHALL 保持数据格式兼容性
5. IF MSearch系统遇到平台特定功能不可用，THEN MSearch系统 SHALL 提供替代方案或优雅降级

### 需求 15: 用户界面与交互

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

### 需求 16: 易用性与稳定性

**用户故事:** 作为视频剪辑师，我希望拥有一个简单易用、稳定可靠的工具，以便专注于我的创作工作。

#### 验收标准

1. WHEN 用户首次打开应用程序时，THE MSearch系统 SHALL 提供简洁的设置向导，引导用户完成基本配置
2. WHEN 用户使用应用程序时，THE MSearch系统 SHALL 提供清晰的操作指引和帮助信息
3. WHEN MSearch系统执行操作时，THE MSearch系统 SHALL 提供明确的反馈信息
4. WHEN MSearch系统遇到错误时，THE MSearch系统 SHALL 显示友好的错误信息，而非技术错误代码
5. WHEN 用户关闭应用程序时，THE MSearch系统 SHALL 安全保存所有数据和状态
6. WHEN MSearch系统运行时，THE MSearch系统 SHALL 保持稳定，崩溃率低于0.1%
7. WHEN MSearch系统处理大文件时，THE MSearch系统 SHALL 保持稳定，不会出现内存溢出或崩溃
8. WHEN 用户使用应用程序时，THE MSearch系统 SHALL 保持界面响应，不会出现卡顿或无响应

### 需求 17: 后端与前端UI分离

**用户故事:** 作为开发者，我希望系统能够保持后端与前端UI分离的结构，以便日后升级为服务化架构。

#### 验收标准

1. WHEN MSearch系统设计时，THE 后端 SHALL 与前端UI完全分离
2. WHEN MSearch系统提供接口时，THE 后端 SHALL 仅提供检索、修改配置等必要接口
3. WHEN MSearch系统运行时，THE 前端UI SHALL 通过标准API与后端通信
4. WHEN MSearch系统升级时，THE 后端与前端UI SHALL 能够独立升级
5. WHEN MSearch系统部署时，THE 后端与前端UI SHALL 能够独立部署

### 需求 18: 本地运行与数据安全

**用户故事:** 作为视频剪辑师，我希望工具能够在本地运行，不依赖互联网，以保证我的素材和项目的安全性。

#### 验收标准

1. WHEN MSearch系统运行时，THE MSearch系统 SHALL 完全在本地运行，不依赖互联网连接
2. WHEN MSearch系统存储数据时，THE MSearch系统 SHALL 将所有数据存储在本地，不发送到任何远程服务器
3. WHEN MSearch系统处理文件时，THE MSearch系统 SHALL 仅访问用户明确指定的目录
4. WHEN MSearch系统生成索引时，THE MSearch系统 SHALL 不修改原始文件
5. WHEN MSearch系统删除索引时，THE MSearch系统 SHALL 不影响原始文件
