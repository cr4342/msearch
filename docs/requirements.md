# Requirements Document

## Introduction

msearch 是一款**单机可运行**的跨平台多模态桌面检索软件，专为视频剪辑师设计，实现素材无需整理、无需标签的智能检索。该软件基于专业化多模型架构，结合 inaSpeechSegmenter 进行音频内容智能分类，支持文本、图像、视频、音频四种模态的精准检索，通过实时监控和增量处理，为视频剪辑师提供高效、安全的多媒体内容检索体验。

## Requirements

### 需求 1: 文字混合检索

**用户故事:** 作为视频剪辑师，我希望能够使用自然语言描述检索我的多媒体文件，以便快速找到相关素材而无需手动标记。

**检索策略:**
- **默认模式**: 文字查询默认以"文搜图"和"文搜视频（纯视觉）"为主，音频权重占比为0
- **音频检索**: 当查询文字包含"音乐"、"歌曲"、"BGM"、"背景音乐"、"讲话"、"会议"、"语音"、"对话"、"演讲"等关键词时，根据配置调整模型权重比例
- **混合检索**: 支持同时检索图像、视频和音频，根据查询关键词动态调整各模态权重比例

#### 验收标准

1. WHEN 用户输入文本查询时，THE MSearch系统 SHALL 根据目标媒体类型选择对应的模型将检索输入转换为向量嵌入，确保向量维度与媒体处理对齐
2. WHEN MSearch系统执行文本到图像或文本到视频视觉检索时，THE MSearch系统 SHALL 使用多模态向量嵌入模型（基于Infinity框架，支持文本、图像、视频检索）进行文本向量化
   - 具体模型规格和硬件适配请参阅设计文档
3. WHEN MSearch系统执行文本到音频检索时，THE MSearch系统 SHALL 使用laion/clap-htsat-unfused模型进行文本向量化
4. WHEN 用户查询包含音频相关关键词时，THE MSearch系统 SHALL 根据配置调整模型权重比例
7. WHEN MSearch系统接收到文本查询时，THE MSearch系统 SHALL 在2秒内返回匹配结果，容差为正0.5秒
8. WHEN MSearch系统返回视频结果时，THE MSearch系统 SHALL 包含视频文件路径、缩略图和时间戳等信息
9. WHEN MSearch系统执行文本到视频检索时，THE MSearch系统 SHALL 使用硬件自适应多模态模型进行视频片段级检索和时序定位
10. WHEN MSearch系统显示检索结果时，THE MSearch系统 SHALL 显示按相似度分数排序的前20个最相关项目
11. WHEN 向量数据库包含超过10万条记录时，THE MSearch系统 SHALL 保持检索性能而无明显下降

### 需求 2: 图搜图、图搜视频

**用户故事:** 作为视频剪辑师，我希望能够使用参考图像进行检索，以便在我的媒体库中找到视觉相似的镜头或素材。

**检索策略:**
- **图搜图**: 使用参考图像检索视觉相似的静态图像
- **图搜视频**: 使用参考图像检索视频中视觉相似的片段，返回时间戳信息
- **视觉相似度**: 基于颜色、纹理、构图等视觉特征进行相似度匹配

#### 验收标准

1. WHEN 用户上传参考图像时，THE MSearch系统 SHALL 使用多模态向量嵌入模型（基于Infinity框架）提取特征
   - 具体模型规格和硬件适配请参阅设计文档
2. WHEN MSearch系统执行图搜图检索时，THE MSearch系统 SHALL 返回视觉相似的图像结果，按相似度分数排序
3. WHEN MSearch系统执行图搜视频检索时，THE MSearch系统 SHALL 使用多模态向量嵌入模型（基于Infinity框架）进行视频片段级检索和时序定位
4. WHEN MSearch系统找到匹配的视频时，THE MSearch系统 SHALL 标记视频片段位置和时间戳，精度为正负5秒以内
5. WHEN 用户拖拽图像文件到检索界面时，THE MSearch系统 SHALL 自动启动检索过程
6. WHEN MSearch系统处理图像查询时，THE MSearch系统 SHALL 在2秒内返回匹配结果，容差为正0.5秒

### 需求 3: 音频找相似音频、找包含相似音频的视频

**用户故事:** 作为视频剪辑师，我希望能够使用音频样本进行检索，以便找到包含相似声音或音乐的文件。

**检索策略:**
- **音频找音频**: 使用laion/clap-htsat-unfused模型检索音频相似的音频文件
- **音频找视频**: 使用laion/clap-htsat-unfused模型检索包含相似音频的视频片段，返回时间戳信息

#### 验收标准

1. WHEN 用户上传音频样本时，THE MSearch系统 SHALL 使用laion/clap-htsat-unfused模型生成向量嵌入
2. WHEN MSearch系统执行音频找音频检索时，THE MSearch系统 SHALL 返回音频相似的音频文件，按相似度分数排序
3. WHEN MSearch系统执行音频找视频检索时，THE MSearch系统 SHALL 使用laion/clap-htsat-unfused模型进行视频音频片段级检索和时序定位
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

### 需求 5: 目录监控与可视化

**用户故事:** 作为视频剪辑师，我希望能够直观地看到程序正在监控哪些目录、已扫描到多少文件、当前处理进度如何，并能够控制监控状态，以便实时了解系统运行状态并管理监控目录。

**核心目标:**
- **直观的可视化界面**: 用户打开任务管理器时，应能一目了然地看到所有监控目录的状态
- **实时数据更新**: 所有统计信息（文件数量、处理进度）应实时更新，无需刷新页面
- **完整的监控控制**: 用户可以随时添加、删除、暂停、恢复任何监控目录
- **清晰的错误提示**: 监控出现错误时，应有明确的错误提示信息

**用户体验要求:**
1. 用户打开任务管理器时，应能立即看到：
   - 程序正在监视哪些目录（路径列表）
   - 每个目录的监控状态（监控中🟢/暂停🟡/错误🔴/初始化中🔵）
   - 每个目录的文件统计（总数、图像数、视频数、音频数）
   - 新文件数量（自上次扫描以来的新增文件）
   - 处理中文件数量

2. 用户应能实时看到：
   - 总计已扫描文件数
   - 按类型分类的统计（图像/视频/音频）
   - 当前处理进度（已完成数量/总数）
   - 预计完成时间（基于当前处理速度）
   - 当前正在处理的文件名和处理状态

#### 验收标准

**基础功能:**
1. WHEN 用户通过UI配置监控目录时，THE MSearch系统 SHALL 为该目录启动Watchdog监控器
2. WHEN Watchdog监控器检测到新文件时，THE MSearch系统 SHALL 自动将文件元数据记录到本地数据库
3. WHEN Watchdog监控器检测到新文件时，THE MSearch系统 SHALL 在后台自动执行向量化处理
4. WHEN Watchdog监控器检测到文件删除或移动时，THE MSearch系统 SHALL 更新本地数据库并从向量数据库中移除对应的向量
5. WHEN MSearch系统重启时，THE MSearch系统 SHALL 自动恢复所有已配置目录的监控状态
6. IF MSearch系统遇到处理错误，THEN MSearch系统 SHALL 记录错误日志并继续处理其他文件
7. WHEN 用户通过UI调整监控配置时，THE MSearch系统 SHALL 实时更新监控状态

**可视化功能:**
8. WHEN 用户打开任务管理器界面时，THE MSearch系统 SHALL 显示所有正在监控的目录列表，包括目录路径和监控状态
9. WHEN 目录监控状态变化时，THE MSearch系统 SHALL 实时更新UI上的状态指示器（监控中🟢/暂停🟡/错误🔴/初始化中🔵）
10. WHEN 文件扫描完成后，THE MSearch系统 SHALL 在UI上显示已扫描文件总数
11. WHEN 文件扫描完成后，THE MSearch系统 SHALL 在UI上显示按类型分类的统计（图像数量/视频数量/音频数量）
12. WHEN 文件正在处理时，THE MSearch系统 SHALL 在UI上显示当前处理进度（已完成数量/总数）
13. WHEN 文件正在处理时，THE MSearch系统 SHALL 在UI上显示预计完成时间
14. WHEN 文件正在处理时，THE MSearch系统 SHALL 在UI上显示当前正在处理的文件名和处理状态
15. WHEN 文件处理完成或失败时，THE MSearch系统 SHALL 在UI上实时更新进度信息和统计数字

**控制功能:**
16. WHEN 用户点击目录列表中的暂停按钮时，THE MSearch系统 SHALL 暂停该目录的监控，但保留已扫描的文件数据
17. WHEN 用户点击目录列表中的恢复按钮时，THE MSearch系统 SHALL 恢复该目录的监控，并继续处理新文件
18. WHEN 用户通过UI添加新的监控目录时，THE MSearch系统 SHALL 立即启动该目录的监控
19. WHEN 用户通过UI删除监控目录时，THE MSearch系统 SHALL 停止该目录的监控，并询问是否删除已索引的数据

**实时更新要求:**
20. WHEN 文件统计数据变化时，THE MSearch系统 SHALL 在1秒内更新UI显示
21. WHEN 处理进度变化时，THE MSearch系统 SHALL 在1秒内更新进度条和百分比
22. WHEN 监控目录状态变化时，THE MSearch系统 SHALL 在1秒内更新状态指示器
23. WHEN 新文件添加到监控目录时，THE MSearch系统 SHALL 立即在UI上显示新文件通知

### 需求 5.5: 重复文件检测与引用

**用户故事:** 作为视频剪辑师，我希望系统能够自动检测重复文件并复用已存储的向量，以便避免重复处理，节省计算资源和存储空间。

**核心功能:**
- **基于SHA256哈希的重复检测**: 文件扫描时计算SHA256哈希值，检测重复文件
- **向量复用**: 对于重复文件，直接引用已存储的向量，避免重复向量化
- **引用计数**: 维护文件的引用计数，支持多路径引用同一文件
- **引用关系管理**: 更新文件引用关系，确保向量与文件的正确关联

#### 验收标准

1. WHEN MSearch系统扫描文件时，THE MSearch系统 SHALL 计算文件的SHA256哈希值
2. WHEN MSearch系统检测到已存在相同哈希的文件时，THE MSearch系统 SHALL 直接引用已存储的向量
3. WHEN MSearch系统引用已存储向量时，THE MSearch系统 SHALL 更新文件引用关系
4. WHEN MSearch系统引用已存储向量时，THE MSearch系统 SHALL 增加文件的引用计数
5. WHEN MSearch系统删除文件时，THE MSearch系统 SHALL 减少文件的引用计数
6. WHEN 文件引用计数降为0时，THE MSearch系统 SHALL 清理孤立的向量数据
7. WHEN MSearch系统处理重复文件时，THE MSearch系统 SHALL 不重复执行向量化操作
8. WHEN MSearch系统处理重复文件时，THE MSearch系统 SHALL 记录重复文件检测日志

### 需求 6: 手动操作控制与进度管理

**用户故事:** 作为视频剪辑师，我希望能够手动控制全量扫描和向量化处理，以便根据需要管理系统资源和处理进度。我希望能够实时看到系统已扫描到多少文件、当前处理到什么进度、预计还需要多长时间完成，并能够随时暂停或取消处理。

**核心功能:**
- **手动触发扫描**: 用户可以手动触发全量扫描，扫描所有已配置监控目录
- **手动触发向量化**: 用户可以手动触发向量化处理，对所有未向量化文件执行处理
- **实时进度显示**: 实时显示当前处理的进度，包括已完成数量、总数、百分比
- **预计完成时间**: 根据当前处理速度，动态计算并显示预计完成时间
- **当前处理文件**: 显示当前正在处理的文件名和处理状态
- **处理速度统计**: 显示处理速度（文件/分钟）和剩余时间估计
- **暂停/恢复控制**: 用户可以暂停当前处理，稍后恢复继续
- **取消处理**: 用户可以取消正在进行的处理，系统安全停止并保留已处理结果
- **资源控制**: 用户可以指定处理时使用的资源（如最大并发数、GPU使用等）

#### 验收标准

**扫描功能:**
1. WHEN 用户通过UI触发全量扫描时，THE MSearch系统 SHALL 扫描所有已配置监控目录的文件
2. WHEN 用户通过UI触发全量扫描时，THE MSearch系统 SHALL 为未入库文件创建元数据记录
3. WHEN 用户通过UI触发扫描指定目录时，THE MSearch系统 SHALL 仅扫描该目录的文件

**向量化功能:**
4. WHEN 用户通过UI启动已入库文件的向量化时，THE MSearch系统 SHALL 对所有未向量化文件执行向量化处理
5. WHEN 用户通过UI选择特定文件类型进行向量化时，THE MSearch系统 SHALL 仅处理该类型的文件（图像/视频/音频）

**进度显示功能:**
6. WHEN 用户通过UI启动向量化处理时，THE MSearch系统 SHALL 显示处理进度条（已完成数量/总数/百分比）
7. WHEN 文件正在处理时，THE MSearch系统 SHALL 在UI上显示当前正在处理的文件名
8. WHEN 文件正在处理时，THE MSearch系统 SHALL 在UI上显示预计完成时间
9. WHEN 文件正在处理时，THE MSearch系统 SHALL 在UI上显示处理速度（文件/分钟）和剩余时间估计
10. WHEN 文件处理完成时，THE MSearch系统 SHALL 在UI上更新最终统计信息（总文件数、成功数、失败数、跳过数）

**控制功能:**
11. WHEN 用户点击暂停按钮时，THE MSearch系统 SHALL 暂停当前处理，完成当前任务后不再启动新任务
12. WHEN 用户点击恢复按钮时，THE MSearch系统 SHALL 恢复处理，继续执行剩余任务
13. WHEN 用户通过UI取消正在进行的处理时，THE MSearch系统 SHALL 安全停止处理并保留已处理结果
14. WHEN 处理被取消时，THE MSearch系统 SHALL 在UI上显示取消原因和已完成的统计信息

**资源控制功能:**
15. WHEN 用户设置最大并发数时，THE MSearch系统 SHALL 限制同时处理的任务数量不超过用户指定的值
16. WHEN 用户设置GPU使用模式时，THE MSearch系统 SHALL 根据用户配置使用GPU或CPU
17. WHEN MSearch系统执行手动操作时，THE MSearch系统 SHALL 优先使用用户指定的资源配置

### 需求 7: 智能视频预处理

**用户故事:** 作为视频剪辑师，我希望系统能够自动将视频文件优化为对AI模型友好的格式，并根据视频时长采用不同的处理策略，以便优化程序运行效率并降低内存开销，同时保持原始素材不变。

**核心目标:**
- **格式优化**: 将原始视频转换为标准输入格式（H.264 MP4、RGB色彩空间）
- **内存保护**: 通过分辨率限制、场景分割、片段级向量化等策略，防止大模型处理时爆内存
- **性能优化**: 使用硬件自适应模型进行片段级向量化，替代逐帧向量化，大幅减少计算时间和向量存储量
- **时长判断**: 根据视频时长（≤6秒 vs >6秒）采用不同的处理策略
- **音频分离**: 对于长视频（>6秒），分离音频并进行向量化
- **视频切片**: 对于长视频（>6秒），进行视频切片并分别向量化
- **IO优化**: 缩略图和预览生成一次解码完成，减少IO操作
- **时序定位**: 视频预处理与视频时序定位紧密耦合，场景分割为时序定位提供基础切片和时间戳信息

#### 验收标准

1. WHEN MSearch系统处理视频文件时，THE MSearch系统 SHALL 判断视频时长
2. WHEN MSearch系统处理时长≤6秒的视频时，THE MSearch系统 SHALL 直接进行视频向量化
3. WHEN MSearch系统处理时长≤6秒的视频时，THE MSearch系统 SHALL 在向量化完成后生成缩略图和预览（一次解码完成）
4. WHEN MSearch系统处理时长>6秒的视频时，THE MSearch系统 SHALL 同时执行音频分离和视频切片
5. WHEN MSearch系统处理时长>6秒的视频时，THE MSearch系统 SHALL 将分离的音频进行向量化
6. WHEN MSearch系统处理时长>6秒的视频时，THE MSearch系统 SHALL 将切片的视频进行向量化
7. WHEN MSearch系统处理时长>6秒的视频时，THE MSearch系统 SHALL 在向量化完成后生成缩略图和预览（一次解码完成）
8. WHEN MSearch系统处理短边超过960像素的视频时，THE MSearch系统 SHALL 按比例调整至短边约960像素（仅用于索引，不修改原始文件）
9. WHEN MSearch系统处理视频文件时，THE MSearch系统 SHALL 转换为H.264 8位MP4格式（仅用于索引）
10. WHEN MSearch系统处理超过120秒的视频时，THE MSearch系统 SHALL 使用FFmpeg工具的场景检测将其分割为120秒或更短的场景片段
11. WHEN MSearch系统完成视频分割时，THE MSearch系统 SHALL 使用硬件自适应模型对视频片段进行片段级向量化，而非逐帧向量化
12. WHEN MSearch系统对视频片段进行向量化时，THE MSearch系统 SHALL 优化内存使用，避免大模型处理时爆内存
13. WHEN MSearch系统处理4K及以上分辨率视频时，THE MSearch系统 SHALL 自动降采样至1080p或720p（仅用于索引），以优化模型处理效率
14. WHEN MSearch系统完成视频场景分割时，THE MSearch系统 SHALL 为每个切片记录在原始视频中的起止时间（start_time、end_time）和切片标识（segment_id、segment_index）
15. WHEN MSearch系统对视频片段进行向量化时，THE MSearch系统 SHALL 将切片时间戳信息与向量嵌入一起存储，为视频时序定位提供基础数据
16. WHEN MSearch系统执行视频预处理时，THE MSearch系统 SHALL 确保切片时间戳精度在正负5秒以内，满足视频时序定位的需求
17. WHEN MSearch系统处理视频文件时，THE MSearch系统 SHALL 优先执行向量化任务，延后执行缩略图和预览生成任务

### 需求 8: 智能图像预处理

**用户故事:** 作为视频剪辑师，我希望系统能够自动将图像文件优化为对AI模型友好的格式，并通过分辨率限制和格式转换降低内存消耗，同时将预处理和缩略图生成合并执行以减少IO操作，以便优化程序运行效率并降低内存开销，同时保持原始素材不变。

**核心目标:**
- **格式优化**: 将原始图像转换为标准输入格式（RGB色彩空间、标准化分辨率）
- **内存保护**: 通过分辨率限制（长边≤2048px）、超大文件分块处理等策略，防止大模型处理时爆内存
- **IO优化**: 图像预处理和缩略图生成合并执行，减少IO操作

#### 验收标准

1. WHEN MSearch系统处理图像文件时，THE MSearch系统 SHALL 使用硬件自适应模型生成向量嵌入
2. WHEN MSearch系统处理图像文件时，THE MSearch系统 SHALL 自动调整图像分辨率，确保长边不超过2048像素（仅用于索引）
3. WHEN MSearch系统处理图像文件时，THE MSearch系统 SHALL 转换为RGB格式（仅用于索引）
4. WHEN MSearch系统处理图像文件时，THE MSearch系统 SHALL 将图像预处理和缩略图生成合并执行（一次解码完成）
5. WHEN MSearch系统处理超大图像文件（超过50MB）时，THE MSearch系统 SHALL 预处理为对AI模型友好的格式规格（仅用于索引）
6. WHEN MSearch系统处理RAW格式图像时，THE MSearch系统 SHALL 自动转换为JPEG或PNG格式（仅用于索引），并调整至合适大小

### 需求 9: 智能音频预处理

**用户故事:** 作为视频剪辑师，我希望系统能够自动将音频文件优化为对AI模型友好的格式，并通过重采样和格式转换降低内存消耗，同时过滤低价值音频（<3秒），以便优化程序运行效率并降低内存开销，同时保持原始素材不变。

**核心目标:**
- **格式优化**: 将原始音频转换为laion/clap-htsat-unfused模型的标准输入格式（48kHz单声道WAV）
- **内存保护**: 通过重采样、无损格式转换、超大文件分块处理等策略，防止大模型处理时爆内存
- **音频价值判断**: 过滤低价值音频（<3秒），避免不必要的处理

#### 验收标准

1. WHEN MSearch系统处理音频文件时，THE MSearch系统 SHALL 判断音频时长
2. WHEN MSearch系统处理时长<3秒的音频时，THE MSearch系统 SHALL 跳过低价值音频，不执行向量化
3. WHEN MSearch系统处理时长≥3秒的音频时，THE MSearch系统 SHALL 进行音频预处理
4. WHEN MSearch系统处理音频文件时，THE MSearch系统 SHALL 将音频转换为laion/clap-htsat-unfused模型的标准输入格式（重采样为48 kHz单声道WAV格式）
5. WHEN MSearch系统处理超大音频文件（超过100MB）时，THE MSearch系统 SHALL 预处理为对AI模型友好的格式规格（仅用于索引）
6. WHEN MSearch系统处理无损音频格式（如FLAC、WAV）时，THE MSearch系统 SHALL 自动转换为压缩格式（仅用于索引）并调整至合适大小

### 需求 10: 视频时序定位

**用户故事:** 作为视频剪辑师，我希望在检索视频时能够快速找到相关片段和大致时间位置，以便直接跳转到所需内容。

**说明:** 系统使用硬件自适应多模态模型进行视频片段级检索和时序定位，相比逐帧向量化大幅降低计算时间和存储空间，但时间定位精度从±2秒降低至±5秒。

#### 验收标准

1. WHEN MSearch系统检索视频内容时，THE MSearch系统 SHALL 返回包含时间戳信息的结果
2. WHEN MSearch系统执行时序定位时，THE MSearch系统 SHALL 达到正负5秒以内的精度，容差可达正负10秒
3. WHEN MSearch系统显示视频结果时，THE MSearch系统 SHALL 显示片段缩略图和时间位置
4. WHEN 用户点击视频结果时，THE MSearch系统 SHALL 提供选项在识别的时间戳处打开系统默认视频播放器
5. IF MSearch系统在一个视频中找到多个相似片段，THEN MSearch系统 SHALL 按相似度分数对结果进行排序
6. WHEN MSearch系统返回视频检索结果时，THE MSearch系统 SHALL 包含原始视频文件的完整路径和文件名
7. WHEN MSearch系统返回视频检索结果时，THE MSearch系统 SHALL 包含切片标识信息（segment_id、segment_index）以便区分同一视频的不同切片
8. WHEN MSearch系统返回视频检索结果时，THE MSearch系统 SHALL 包含切片在原始视频中的起止时间（start_time、end_time）
9. WHEN MSearch系统返回视频检索结果时，THE MSearch系统 SHALL 包含模型预测的片段中心时间戳（segment_center_timestamp）用于定位
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
5. WHEN 用户点击音频结果时，THE MSearch系统 SHALL 显示音频波形和播放控制
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

1. WHEN 用户安装MSearch系统时，THE 安装脚本 SHALL 检测GPU、CPU和内存配置，并生成匹配的配置文件
2. IF 安装脚本检测到CUDA兼容GPU，THEN 配置文件 SHALL 配置使用CUDA加速
3. IF 安装脚本仅检测到CPU，THEN 配置文件 SHALL 配置使用CPU
4. IF 安装脚本检测到低硬件配置，THEN 配置文件 SHALL 配置使用轻量级模型
5. IF 安装脚本检测到中配以上硬件配置，THEN 配置文件 SHALL 配置使用标准模型
5. WHEN 用户首次打开应用程序时，THE MSearch系统 SHALL 提供简洁的设置向导，引导用户完成基本配置
6. WHEN 用户使用应用程序时，THE MSearch系统 SHALL 提供清晰的操作指引和帮助信息
7. WHEN MSearch系统执行操作时，THE MSearch系统 SHALL 提供明确的反馈信息
8. WHEN MSearch系统遇到错误时，THE MSearch系统 SHALL 显示友好的错误信息，而非技术错误代码
9. WHEN 用户切换模型时，THEN 用户 SHALL 修改配置文件选择不同模型（使用 [michaelfeil/infinity](https://github.com/michaelfeil/infinity) 框架）
10. WHEN 用户关闭应用程序时，THE MSearch系统 SHALL 安全保存所有数据和状态
11. WHEN MSearch系统运行时，THE MSearch系统 SHALL 保持稳定，崩溃率低于0.1%
12. WHEN MSearch系统处理大文件时，THE MSearch系统 SHALL 保持稳定，不会出现内存溢出或崩溃
13. WHEN 用户使用应用程序时，THE MSearch系统 SHALL 保持界面响应，不会出现卡顿或无响应

**Infinity 框架特性**：
- **简单切换模型**：配置文件驱动，无需修改代码即可切换不同模型
- **高效管理模型运行**：统一的模型生命周期管理（加载、卸载、缓存）
- **统一的模型加载接口**：所有模型使用相同的加载方式，简化代码
- **高性能推理**：动态批处理优化，FlashAttention 加速，多精度支持
- **内存优化**：自动内存管理，避免显存溢出，智能缓存策略
- **支持离线模式**：完全支持离线运行，无需网络连接

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

### 需求 17: 任务优先级与调度

**用户故事:** 作为视频剪辑师，我希望系统能够根据任务类型和重要性自动调度任务，优先执行关键操作（如向量化），延后执行辅助操作（如缩略图生成），以便优化系统性能和响应速度。同时，我希望能够手动控制任务优先级，让程序优先处理我需要的文件类型，并能在UI中看到当前任务队列和执行情况。

**核心功能:**
- **任务优先级系统**: 支持0-11级任务优先级，数值越小优先级越高
- **向量化任务优先**: 向量化任务优先级最高（1-5级），确保核心功能快速完成
- **预处理任务次之**: 预处理任务优先级中等（6-8级），为向量化做准备
- **辅助任务延后**: 缩略图生成、预览生成等辅助任务优先级较低（9-10级），在核心任务完成后执行
- **任务依赖管理**: 自动管理任务依赖关系，确保前置任务完成后才执行后续任务
- **用户控制优先级**: 用户可以手动设置文件类型优先级，让程序优先处理特定类型的文件
- **任务队列可视化**: 用户可以在UI中看到当前任务队列、等待中的任务、正在执行的任务
- **任务统计信息**: 实时显示任务统计（等待/执行/完成/失败数量）

#### 验收标准

**自动优先级分配:**
1. WHEN MSearch系统创建任务时，THE MSearch系统 SHALL 根据任务类型分配优先级（0-11级）
2. WHEN MSearch系统执行任务时，THE MSearch系统 SHALL 优先执行高优先级任务
3. WHEN MSearch系统执行向量化任务时，THE MSearch系统 SHALL 分配最高优先级（1-5级）
4. WHEN MSearch系统执行预处理任务时，THE MSearch系统 SHALL 分配中等优先级（6-8级）
5. WHEN MSearch系统执行缩略图生成任务时，THE MSearch系统 SHALL 分配较低优先级（9-10级）
6. WHEN MSearch系统执行预览生成任务时，THE MSearch系统 SHALL 分配较低优先级（9-10级）
7. WHEN MSearch系统调度任务时，THE MSearch系统 SHALL 确保前置任务完成后才执行依赖任务
8. WHEN MSearch系统处理视频文件时，THE MSearch系统 SHALL 优先执行向量化任务，延后执行缩略图和预览生成任务
9. WHEN MSearch系统处理图像文件时，THE MSearch系统 SHALL 将预处理和缩略图生成合并执行（一次解码完成）
10. WHEN MSearch系统处理音频文件时，THE MSearch系统 SHALL 优先执行向量化任务

**用户控制优先级:**
11. WHEN 用户在UI中设置文件类型优先级时，THE MSearch系统 SHALL 根据用户设置的优先级调整相关任务的执行顺序
12. WHEN 用户将"视频"设置为最高优先级时，THE MSearch系统 SHALL 优先处理所有视频相关任务
13. WHEN 用户将"音频"设置为最高优先级时，THE MSearch系统 SHALL 优先处理所有音频相关任务
14. WHEN 用户将"图像"设置为最高优先级时，THE MSearch系统 SHALL 优先处理所有图像相关任务
15. WHEN 用户调整优先级时，THE MSearch系统 SHALL 立即更新任务队列的排序

**任务队列可视化:**
16. WHEN 用户打开任务管理器界面时，THE MSearch系统 SHALL 显示当前任务队列中等待中的任务列表
17. WHEN 用户打开任务管理器界面时，THE MSearch系统 SHALL 显示当前正在执行的任务列表
18. WHEN 任务状态变化时，THE MSearch系统 SHALL 实时更新UI上的任务列表
19. WHEN 用户查看任务列表时，THE MSearch系统 SHALL 显示每个任务的优先级、文件名、任务类型、创建时间
20. WHEN 用户查看任务列表时，THE MSearch系统 SHALL 使用颜色或图标区分不同优先级的任务

**任务统计信息:**
21. WHEN 用户查看任务管理器时，THE MSearch系统 SHALL 显示任务统计信息（等待数量/执行数量/完成数量/失败数量）
22. WHEN 用户查看任务管理器时，THE MSearch系统 SHALL 显示线程池使用情况（活跃线程数/空闲线程数）
23. WHEN 任务完成时，THE MSearch系统 SHALL 实时更新统计信息

**任务控制功能:**
24. WHEN 用户点击某个等待中的任务时，THE MSearch系统 SHALL 显示该任务的详细信息（文件信息、任务类型、优先级、依赖任务）
25. WHEN用户点击某个正在执行的任务时，THE MSearch系统 SHALL 显示该任务的详细信息（文件信息、进度、已用时间、预计剩余时间）
26. WHEN 用户选择多个等待中的任务并点击提升优先级时，THE MSearch系统 SHALL 将这些任务的优先级提高一级
27. WHEN 用户选择多个等待中的任务并点击降低优先级时，THE MSearch系统 SHALL 将这些任务的优先级降低一级
28. WHEN 用户选择多个等待中的任务并点击取消时，THE MSearch系统 SHALL 从任务队列中移除这些任务
29. WHEN 用户点击某个正在执行的任务并点击取消时，THE MSearch系统 SHALL 安全停止该任务并标记为已取消

---

## 附录：项目架构与技术说明

### 项目结构

msearch 采用分层架构设计，主要包含以下模块：

#### 核心组件层 (src/core/)
- **config/**: 配置管理（config.py - 合并了配置加载、验证和查询功能）
- **database/**: 数据库管理（database_manager.py）
- **vector/**: 向量存储（vector_store.py）
- **embedding/**: 向量化引擎（embedding_engine.py, model_manager.py）
- **task/**: 任务管理（task_manager.py, task_scheduler.py）
- **hardware/**: 硬件检测（hardware_detector.py）
- **logging/**: 日志配置（logging_config.py）

#### 服务层 (src/services/)
- **search/**: 检索服务（search_engine.py, query_processor.py, result_ranker.py）
- **media/**: 媒体处理服务（media_processor.py）
- **file/**: 文件处理服务（file_monitor.py, file_scanner.py）
- **face/**: 人脸识别服务（可选）
- **cache/**: 缓存服务（cache_manager.py）

#### 数据层 (src/data/)
- **extractors/**: 数据提取器（metadata_extractor.py, noise_filter.py）
- **generators/**: 数据生成器（thumbnail_generator.py, preview_generator.py）
- **models/**: 数据模型定义
- **validators/**: 数据验证器

#### 工具层 (src/utils/)
- **error_handling.py**: 错误处理
- **exceptions.py**: 异常定义
- **retry.py**: 重试策略
- **helpers.py**: 辅助函数
- **file_utils.py**: 文件操作工具

#### API层 (src/api/)
- **v1/**: API v1版本（routes.py, handlers.py, schemas.py, dependencies.py）
- **middlewares.py**: API中间件

### 配置管理

系统采用 YAML 格式的配置文件，支持多环境配置：

- **configs/config.yaml**: 主配置文件
- **configs/default.yaml**: 默认配置
- **configs/development.yaml**: 开发环境配置
- **configs/production.yaml**: 生产环境配置
- **configs/schema.json**: 配置验证 Schema

配置管理器提供以下功能：
- 配置加载和验证
- 配置热更新
- 配置导入导出
- 类型转换和默认值管理

### 数据库架构

系统使用两种数据库：

1. **SQLite** (data/database/sqlite/msearch.db)
   - 存储文件元数据
   - 支持事务和全文搜索
   - 文件型数据库，易于备份

2. **LanceDB** (data/database/lancedb/)
   - 存储向量数据
   - 单一向量表设计（unified_vectors）
   - 支持IVF、HNSW等索引算法

### 硬件自适应模型策略

系统支持多级硬件配置，使用 [michaelfeil/infinity](https://github.com/michaelfeil/infinity) 框架统一管理模型：

| 硬件级别 | GPU显存 | 系统内存 | 模型类型 | 显存需求 |
|---------|---------|---------|---------|---------|
| 入门硬件 | <2GB或CPU | ≥4GB | 轻量级模型 | 参考设计文档 |
| 通用硬件 | ≥4GB | ≥8GB | 标准模型 | 参考设计文档 |
| 中配硬件 | 8-16GB | ≥16GB | 标准模型 | 参考设计文档 |
| 高配硬件 | 16-24GB | ≥32GB | 高性能模型 | 参考设计文档 |
| 超高配硬件 | >24GB | ≥64GB | 高性能模型 | 参考设计文档 |

**说明**: 具体模型规格、显存需求和硬件适配详情请参阅设计文档。

**Infinity 框架特性**：
- **简单切换模型**：配置文件驱动，无需修改代码即可切换不同模型
- **高效管理模型运行**：统一的模型生命周期管理（加载、卸载、缓存）
- **统一的模型加载接口**：所有模型使用相同的加载方式，简化代码
- **高性能推理**：动态批处理优化，FlashAttention 加速，多精度支持
- **内存优化**：自动内存管理，避免显存溢出，智能缓存策略
- **支持离线模式**：完全支持离线运行，无需网络连接

### 任务调度机制

系统采用智能任务调度机制：

- **12级优先级** (0-11，数值越小优先级越高)
- **动态并发控制**：根据系统负载自动调整并发数
- **任务依赖管理**：自动管理任务依赖关系
- **任务持久化**：使用 persist-queue 持久化任务

### 缓存策略

系统支持多种缓存策略：

- **LRU** (最近最少使用)
- **LFU** (最不经常使用)
- **TTL** (生存时间)
- 热冷数据分离
- 自动清理和优化

### 噪音过滤机制

系统提供低价值噪音过滤机制，提高系统效率：

- **图像过滤**：基于分辨率、文件大小等
- **视频过滤**：基于时长、分辨率、文件大小等
- **音频过滤**：基于时长（<3秒跳过）、比特率等
- **文本过滤**：基于长度等

### Python原生集成

系统采用Python原生集成模型，不使用任何外部服务引擎：

- **轻量级**：无需额外的模型服务引擎
- **灵活性**：直接调用模型API
- **易于维护**：避免引入额外的第三方依赖
- **可扩展性**：设计预留服务化接口
