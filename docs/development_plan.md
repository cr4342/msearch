# MSearch 开发计划

> 本文档描述MSearch系统的开发计划，包含各阶段的功能实现、技术选型和实施优先级。

## 文档导航

- [设计文档](design.md) - 系统整体设计和技术架构
- [需求文档](requirements.md) - 软件需求规范
- [技术实现文档](technical_implementation.md) - 技术实现细节
- [API文档](api_documentation.md) - API接口说明
- [测试策略](test_strategy.md) - 测试方案和策略
- [用户手册](user_manual.md) - 用户操作指南

## 项目概述

MSearch是一个基于michaelfeil/infinity的多模态内容检索系统，支持文本、图像、视频和音频的智能搜索。本开发计划按照功能模块和优先级，将项目分为11个阶段逐步实施。

## ⚠️ 重要架构调整说明

**v2.0架构调整**：基于AI模型对输入格式的严格要求，本版本开发计划进行了重要调整：

1. **新增阶段0**：模型资源准备阶段，解决所有测试验证对本地模型的依赖问题
2. **媒体预处理前置**：将媒体预处理系统从阶段3调整到阶段2，为AI模型提供标准化输入
3. **依赖关系明确**：明确标注各阶段间的依赖关系，避免开发过程中的阻塞问题

**调整原因**：
- AI模型（CLIP、CLAP、Whisper）对输入格式有严格要求
- 所有功能测试都需要本地模型支持
- 媒体预处理是AI模型调用的前置条件

## 技术架构

### 核心组件
- **michaelfeil/infinity**: 多模型服务引擎，提供统一的AI推理能力
- **向量存储层**: 基于Qdrant的向量数据库，存储多模态向量数据
- **多模态处理器**: 支持文本、图像、视频、音频的向量化处理
- **时间定位机制**: 基于帧级时间戳的精确时间定位（±2秒精度）

### 技术栈
- **后端**: Python + FastAPI + SQLAlchemy
- **AI推理**: michaelfeil/infinity (集成CLIP、CLAP、Whisper等模型)
- **向量数据库**: Qdrant (本地二进制部署)
- **桌面应用**: PySide6（主要用户界面） 

## 实施策略概述

根据功能导向的迭代开发原则，本开发计划将按照十一个主要阶段组织，每个阶段围绕具体功能展开，从基础架构到完整的多模态搜索系统：

**⚠️ 重要提醒：本项目的所有测试和验证都严重依赖本地AI模型，必须在开发前完成模型准备工作！**

**⚠️ 架构调整说明：由于AI模型对文件格式有严格要求，媒体预处理必须在模型调用之前完成！**

0. **阶段0（模型资源准备）**：**[必须优先完成]** 下载和部署所有AI模型，建立离线开发环境，确保后续开发测试可以正常进行
1. **阶段1（基础架构与存储）**：建立系统基础架构，实现配置管理、日志系统、存储层和AI模型集成
2. **阶段2（媒体预处理系统）**：**[重新调整]** 实现媒体文件预处理框架，为AI模型提供标准化输入格式
3. **阶段3（图片处理与基础多模态）**：基于预处理框架实现图片处理和向量化，建立第一个多模态搜索能力
4. **阶段4（视频处理与搜索）**：基于预处理框架实现视频处理器和视频搜索，支持场景检测和时间定位
5. **阶段5（音频处理与搜索）**：基于预处理框架实现音频处理器和音频搜索，支持语音转录和音频特征检索
6. **阶段6（人脸识别与智能检索）**：实现人脸识别、智能检索策略、动态权重分配
7. **阶段7（高级搜索与融合）**：多模态融合、时间线搜索、高级配置管理
8. **阶段8（PySide6桌面应用）**：开发PySide6桌面应用，提供原生用户体验
9. **阶段9（系统优化与部署）**：Python-native优化、性能调优、系统稳定性、生产环境部署
10. **阶段10（Web用户界面）**：可选的Web界面，提供跨平台访问能力（可选功能）

## 阶段0（模型资源准备 - 必须优先完成）

### 0.1 核心功能：AI模型资源下载与部署

**⚠️ 关键提醒**：这是整个项目的前置依赖阶段，必须100%完成才能进行后续开发！

**目标**：建立完整的离线AI模型环境，确保所有后续开发和测试都能正常进行

**模型依赖分析**：
- **阶段1验证**：需要CLIP模型进行EmbeddingEngine测试
- **阶段2图片处理**：需要CLIP模型进行图片向量化
- **阶段4视频处理**：需要CLIP模型进行视频帧向量化
- **阶段5音频处理**：需要CLAP和Whisper模型进行音频处理
- **阶段6人脸识别**：需要额外的人脸识别模型（FaceNet/ArcFace）

**技术实现**：
- [x] [p0] **模型下载脚本执行**
  - 执行 `scripts/download_all_resources.sh` 下载所有AI模型
  - 下载CLIP模型：openai/clip-vit-base-patch32 到 `offline/models/clip-vit-base-patch32/`
  - 下载CLAP模型：laion/clap-htsat-fused 到 `offline/models/clap-htsat-fused/`
  - 下载Whisper模型：openai/whisper-base 到 `offline/models/whisper-base/`
  - 验证模型文件完整性和格式正确性
  - _需求：离线部署方案_

- [x] [p0] **模型部署与环境配置**
  - 执行 `scripts/install_auto.sh` 将模型从offline/复制到data/models/
  - 配置HF_HOME环境变量指向本地模型目录
  - 设置offline_mode: true和force_local: true确保不尝试在线下载
  - 验证config/config.yml中的模型路径配置正确
  - _需求：本地模型配置_

- [x] [p0] **人脸识别模型准备**
  - 下载人脸检测模型（MTCNN/RetinaFace）
  - 下载人脸识别模型（FaceNet/ArcFace）
  - 配置人脸模型的本地路径
  - _需求：2.1, 2.2 人脸识别系统_

**验证方式**：
```bash
# 1. 验证模型下载完成
ls -la offline/models/
# 应该看到：clip-vit-base-patch32/, clap-htsat-fused/, whisper-base/

# 2. 验证模型部署完成  
ls -la data/models/
# 应该看到：clip-vit-base-patch32/, clap-htsat-fused/, whisper-base/

# 3. 验证模型可以正常加载（这是关键测试）
python -c "
import os
os.environ['HF_HOME'] = './data/models'
from transformers import CLIPModel
model = CLIPModel.from_pretrained('./data/models/clip-vit-base-patch32', local_files_only=True)
print('CLIP模型加载成功')
"

# 4. 验证配置文件正确
python -c "
from src.core.config_manager import ConfigManager
config = ConfigManager()
print(f'CLIP模型路径: {config.get(\"embedding.clip.model_name\")}')
print(f'离线模式: {config.get(\"models_storage.offline_mode\")}')
"
```

**用户价值**：✅ 建立完整的离线AI模型环境，为所有后续开发提供必要的模型依赖

**⚠️ 阻塞警告**：如果此阶段未完成，后续所有阶段的测试都将失败！

---

## 阶段1（MVP - 基础架构与存储）

### 1.1 核心功能：基础架构搭建

**目标**：建立完整的系统基础架构，为后续功能开发奠定基础

**技术实现**：
- [x] [p0] 项目基础搭建
  - 创建项目结构：按照设计文档8.2节的目录结构组织代码
  - 实现核心组件：ConfigManager、LoggerManager、FileTypeDetector
  - 建立基础的错误处理和日志记录机制
  - _需求：系统架构基础_

- [x] [p0] 配置驱动架构实现
  - 实现ConfigManager统一配置管理器（src/core/config_manager.py）
  - 支持单一配置文件config/config.yml管理所有系统参数
  - 实现LoggerManager多级别日志系统（src/core/logger_manager.py）
  - 支持环境变量覆盖配置文件参数，便于容器化部署
  - 实现配置验证和默认配置生成，确保配置完整性和类型安全
  - 配置修改后重启生效，简化维护复杂度
  - _需求：系统架构要求_

- [x] [p0] 存储层基础实现
  - 实现SQLiteManager元数据管理器（src/storage/sqlite_manager.py）
  - 实现QdrantClient向量数据库客户端（src/storage/qdrant_client.py）
  - 建立基础的数据模型和表结构
  - 实现数据库初始化和迁移机制
  - _需求：存储层设计_

**验证方式**：
```bash
# ⚠️ 前置检查：确保阶段0已完成
if [ ! -d "data/models/clip-vit-base-patch32" ]; then
    echo "错误：请先完成阶段0的模型准备工作！"
    exit 1
fi

# 验证配置系统
python -c "from src.core.config_manager import ConfigManager; print('配置系统正常')"

# 验证数据库连接
python scripts/database_init.py

# 验证日志系统
python -c "from src.core.logger_manager import LoggerManager; LoggerManager().get_logger('test').info('日志系统正常')"
```

**用户价值**：✅ 建立稳定的系统基础，为后续功能开发提供可靠支撑

### 1.2 核心功能：Python-native EmbeddingEngine

**目标**：实现高性能的AI模型集成，为多模态搜索提供核心能力

**技术实现**：
- [x] [p0] Python-native EmbeddingEngine
  - 实现EmbeddingEngine集成 michaelfeil/infinity Python-native模式
  - 直接在Python中管理CLIP、CLAP、Whisper等模型
  - 消除HTTP通信开销，提升20-30%性能
  - 统一GPU内存管理和批处理优化
  - _需求：AI推理层设计_

- [x] [p0] 模型管理与健康检查
  - 实现模型加载和初始化机制
  - 支持模型健康检查和性能监控
  - 实现错误处理和自动重试机制
  - 支持硬件自适应配置（CPU/GPU）
  - _需求：模型管理_

**验证方式**：
```python
# ⚠️ 前置检查：确保模型已部署
import os
if not os.path.exists('./data/models/clip-vit-base-patch32'):
    raise RuntimeError("错误：请先完成阶段0的模型准备工作！")

# 验证模型加载（这是关键测试，依赖本地模型）
from src.business.embedding_engine import EmbeddingEngine
engine = EmbeddingEngine()
result = await engine.embed_content("test text", "text")
print(f"向量维度: {len(result)}")  # 应该输出512

# 验证模型健康状态
health = engine.get_model_health()
print(f"模型健康状态: {health}")  # 应该显示所有模型为True
```

**用户价值**：✅ 提供高性能的AI模型服务，为多模态搜索奠定技术基础

### 1.3 核心功能：基础文本搜索API

**目标**：实现最基本的文本内容搜索功能，验证整个技术栈

**功能演示**：
```bash
# 用户操作
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "机器学习算法", "type": "text"}'

# 系统返回
{
  "results": [
    {"file": "notes.txt", "content": "...机器学习算法...", "score": 0.95},
    {"file": "paper.pdf", "content": "...深度学习算法...", "score": 0.87}
  ]
}
```

**技术实现**：
- [x] [p0] FastAPI基础框架
  - 实现FastAPI应用入口（src/api/main.py）
  - 创建基础路由和中间件
  - 实现统一的错误处理和响应格式
  - _需求：API服务层_

- [x] [p0] 基础搜索API
  - 实现 `/search` 端点，支持文本查询
  - 基于CLIP模型的文本向量化和相似度匹配
  - 返回匹配的文件列表和相似度分数
  - _需求：1.3, 6.2_

**用户价值**：✅ 可以搜索文本文件内容，验证系统核心功能正常

## 阶段2（媒体预处理系统 - 为AI模型提供标准化输入）

### 2.1 核心功能：媒体文件预处理框架

**目标**：建立完整的媒体预处理框架，为AI模型提供标准化的输入格式

**⚠️ 架构重要性**：AI模型对输入格式有严格要求，预处理是所有后续功能的基础！

**AI模型格式要求分析**：
- **CLIP模型**：需要RGB格式、224×224尺寸、标准化的图片输入
- **Whisper模型**：需要16kHz单声道WAV格式音频
- **CLAP模型**：需要特定采样率的音频片段
- **视频处理**：需要场景检测、关键帧提取、时间戳同步

**技术实现**：
- [x] [p0] 配置驱动的MediaProcessor框架
  - 实现MediaProcessor（src/business/media_processor.py）
  - 实现完全配置驱动的媒体预处理器，所有参数从config.yml读取
  - 支持格式标准化：4K→720p (1280×720) 降采样，减少60-80%显存占用
  - 创建多阶段预处理流水线：格式转换→尺寸标准化→向量化准备
  - 实现配置验证机制，确保处理参数在合理范围内
  - _需求：媒体处理策略设计_

- [x] [p0] FileTypeDetector组件实现
  - 实现FileTypeDetector（src/core/file_type_detector.py）
  - 实现多层次文件类型检测（扩展名、MIME类型、文件头分析）
  - 支持配置驱动的文件类型映射和处理策略路由
  - 集成libmagic库进行精确的文件内容分析
  - 提供置信度评分机制，处理类型冲突
  - _需求：文件处理基础功能_

- [x] [p0] ProcessingOrchestrator处理编排器
  - 实现ProcessingOrchestrator（src/business/orchestrator.py）
  - 实现策略路由：根据文件类型和内容特征选择处理策略
  - 实现流程编排：管理预处理→向量化→存储的调用顺序
  - 支持状态管理：跟踪处理进度、状态转换和错误恢复
  - 实现资源协调：协调CPU/GPU资源分配，避免资源竞争
  - _需求：ProcessingOrchestrator设计_

**验证方式**：
```bash
# ⚠️ 前置检查：确保阶段0已完成
if [ ! -d "data/models/clip-vit-base-patch32" ]; then
    echo "错误：请先完成阶段0的模型准备工作！"
    exit 1
fi

# 验证文件类型检测
python -c "
from src.core.file_type_detector import FileTypeDetector
detector = FileTypeDetector()
result = detector.detect_file_type('test.mp4')
print(f'文件类型: {result}')
"

# 验证媒体预处理（为AI模型准备标准化输入）
python -c "
from src.business.media_processor import MediaProcessor
processor = MediaProcessor()
result = processor.preprocess_file('test.jpg')  # 输出应该是CLIP可接受的格式
print(f'预处理结果: {result}')
"

# 验证预处理输出格式符合AI模型要求
python -c "
from src.business.media_processor import MediaProcessor
import numpy as np
processor = MediaProcessor()
processed_image = processor.preprocess_image('test.jpg')
print(f'图片尺寸: {processed_image.shape}')  # 应该是 (224, 224, 3)
print(f'数据类型: {processed_image.dtype}')   # 应该是 float32
print(f'数值范围: [{processed_image.min():.3f}, {processed_image.max():.3f}]')  # 应该是标准化范围
"
```

**用户价值**：✅ 建立媒体预处理基础设施，为所有AI模型提供标准化输入，确保后续功能正常运行

### 2.2 核心功能：时间戳处理机制

**目标**：实现±2秒精度的时间戳处理，支持多模态时间同步

**技术实现**：
- [x] [p0] TimestampProcessor时间戳处理器
  - 实现TimestampProcessor（src/processors/timestamp_processor.py）
  - 实现帧级时间戳计算：基于帧率的精确时间计算（±0.033s@30fps）
  - 实现多模态时间同步验证：视觉、音频、语音统一时间基准
  - 支持±2秒精度保证：重叠时间窗口+精确边界检测
  - 实现场景感知切片：避免在场景中间进行时间切分
  - _需求：时间戳处理机制设计_

- [x] [p0] TimeAccurateRetrieval精确时间检索
  - 实现时间戳索引查询：向量相似度检索→时间戳查询→精度验证
  - 支持时间段合并与去重：重叠时间段智能合并
  - 实现连续性检测：判断时间段是否连续（考虑±2秒精度）
  - 优化查询性能：时间戳查询延迟<10ms，批量查询<50ms
  - _需求：精确时间检索算法_

- [x] [p0] 时间戳数据库设计
  - 实现video_timestamps表：存储文件ID、向量ID、时间戳、模态类型
  - 创建时间范围查询索引：优化时间戳查询性能
  - 支持多模态时间戳存储：视觉、音频、语音分别记录
  - 实现时间戳漂移校正：确保多模态时间同步
  - _需求：时间戳数据库设计_

**验证方式**：
```python
# 验证时间戳计算精度
from src.processors.timestamp_processor import TimestampProcessor
processor = TimestampProcessor(fps=30.0)
timestamp = processor.calculate_frame_timestamp(60)
print(f"帧60的时间戳: {timestamp}s")  # 应该是2.0s

# 验证精度要求
accuracy = processor.validate_timestamp_accuracy(10.0, 3.0)
print(f"精度验证: {accuracy}")  # 应该是True（3s < 4s）
```

**用户价值**：✅ 为视频和音频搜索提供精确的时间定位能力

### 2.3 核心功能：文件监控与自动处理

**目标**：实现智能文件监控系统，自动发现并处理新增的媒体文件

**功能演示**：
```bash
# 查看文件处理状态
curl -X GET "http://localhost:8000/files/status"

# 系统返回当前处理队列
{
  "queue_size": 5,
  "processing_files": [
    {"file": "vacation.jpg", "status": "processing", "progress": 45},
    {"file": "meeting.png", "status": "queued", "progress": 0}
  ]
}
```

**技术实现**：
- [x] [p0] 文件系统监控服务
  - 实现FileMonitor（src/business/file_monitor.py）
  - 创建基于watchdog的文件监控器，支持多目录监控
  - 实现文件事件处理：创建、删除、修改、移动
  - 创建文件过滤机制，支持扩展名和模式匹配
  - _需求：3.1, 3.2, 3.3, 3.4, 3.5_

- [x] [p0] 异步处理队列系统
  - 实现TaskManager（src/business/task_manager.py）
  - 创建优先级任务队列，支持文件处理任务调度
  - 实现任务重试机制和错误处理策略
  - 创建任务状态跟踪和进度报告
  - _需求：3.2, 3.5, 7.1_

**用户价值**：✅ 文件自动发现和排队处理，无需手动操作

## 阶段3（图片处理与基础多模态 - 基于预处理框架）

### 3.1 核心功能：图片处理与向量化

**目标**：基于阶段2的预处理框架，实现图片文件的处理和向量化，建立第一个多模态搜索能力

**⚠️ 依赖关系**：此阶段严重依赖阶段2的MediaProcessor提供标准化图片输入！

**功能演示**：
```bash
# 文搜图 - 用文字搜索图片
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "夕阳下的海滩", "type": "text_to_image"}'

# 图搜图 - 用图片搜索相似图片  
curl -X POST "http://localhost:8000/search" \
  -F "image=@vacation.jpg" \
  -F 'type=image_to_image'
```

**技术实现**：
- [x] [p0] 图片处理器实现（基于预处理框架）
  - 实现ImageProcessor（src/processors/image_processor.py）
  - **依赖MediaProcessor**：使用预处理框架提供的标准化图片输入
  - 支持多格式图片处理（JPEG、PNG、WEBP、TIFF等）
  - 实现格式标准化：4K→720p降采样，减少显存压力
  - 集成EXIF元数据提取和处理
  - _需求：图片处理策略_

- [x] [p0] 图片向量化与存储
  - 集成Python-native CLIP模型处理**预处理后的**图片内容
  - 实现批处理优化，批处理大小32（根据GPU显存动态调整）
  - 实现图片特征提取和Qdrant向量存储
  - 建立image_vectors集合和相关索引
  - _需求：2.1, 2.2, 2.3_

- [x] [p0] 图片搜索API
  - 扩展 `/search` 端点支持跨模态图片查询
  - 实现文搜图（CLIP文本→图像）和图搜图功能
  - 支持多图片格式上传和实时处理
  - 集成向量相似度搜索和结果排序
  - _需求：2.4, 6.3_

**验证方式**：
```bash
# ⚠️ 前置检查：确保阶段0和阶段2已完成
if [ ! -d "data/models/clip-vit-base-patch32" ]; then
    echo "错误：请先完成阶段0的模型准备工作！"
    exit 1
fi

# 验证预处理框架可用
python -c "
from src.business.media_processor import MediaProcessor
processor = MediaProcessor()
print('预处理框架可用')
"

# 验证图片处理（使用预处理框架）
python -c "
from src.processors.image_processor import ImageProcessor
processor = ImageProcessor()
result = processor.process_image('test.jpg')
print(f'处理结果: {result}')
print(f'输出格式符合CLIP要求: {result[\"format_valid\"]}')
"

# 验证图片搜索
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "测试图片", "type": "text_to_image"}'
```

**用户价值**：✅ 可以通过文字或图片搜索图片库，解决图片管理和查找问题

## 阶段4（视频处理与搜索 - 基于预处理框架）

### 4.1 核心功能：视频处理器实现

**目标**：基于阶段2的预处理框架，实现视频文件的智能处理，支持场景检测和关键帧提取

**⚠️ 依赖关系**：此阶段严重依赖阶段2的MediaProcessor和TimestampProcessor！

**技术实现**：
- [x] [p0] VideoProcessor视频处理器（基于预处理框架）
  - 实现VideoProcessor（src/processors/video_processor.py）
  - **依赖MediaProcessor**：使用预处理框架提供的标准化视频输入
  - **依赖TimestampProcessor**：使用阶段2的时间戳处理机制
  - 实现智能视频预处理：4K/HD→720p (1280×720) 转换，减少70-80%显存占用
  - 集成FFmpeg进行格式转换和场景检测
  - 实现动态抽帧策略：短视频2秒间隔，长视频场景感知切片
  - 支持多种视频格式的精确识别和差异化处理
  - _需求：视频处理策略设计_

- [x] [p0] 视频时间戳处理集成
  - **使用阶段2的TimestampProcessor**进行帧级时间戳计算
  - 支持多模态时间同步：视觉、音频、语音统一时间基准
  - 实现±2秒精度保证：重叠时间窗口+精确边界检测
  - 创建时间戳数据库索引，支持毫秒级时间查询
  - _需求：视频时间戳处理机制_

- [x] [p0] 视频向量化与存储
  - 集成Python-native CLIP模型处理**预处理后的**视频帧
  - 实现批处理优化，批处理大小16（720p预处理后可增加批处理大小）
  - 建立video_vectors集合，存储帧向量和时间戳
  - 实现MaxSim聚合算法，优化显存占用
  - _需求：视频向量化策略_

**验证方式**：
```python
# ⚠️ 前置检查：确保阶段0和阶段2已完成
import os
if not os.path.exists('./data/models/clip-vit-base-patch32'):
    raise RuntimeError("错误：请先完成阶段0的模型准备工作！")

# 验证预处理框架和时间戳处理器可用
from src.business.media_processor import MediaProcessor
from src.processors.timestamp_processor import TimestampProcessor
media_processor = MediaProcessor()
timestamp_processor = TimestampProcessor(fps=30.0)
print('预处理框架和时间戳处理器可用')

# 验证视频处理（使用预处理框架）
from src.processors.video_processor import VideoProcessor
processor = VideoProcessor()
result = processor.process_video('test.mp4')
print(f"处理结果: 提取{len(result['frames'])}帧")
print(f"预处理格式符合CLIP要求: {result['format_valid']}")

# 验证时间戳精度（使用阶段2的时间戳处理器）
for frame in result['frames'][:3]:
    print(f"帧{frame['index']}: {frame['timestamp']:.3f}s")
    print(f"时间戳精度验证: {timestamp_processor.validate_timestamp_accuracy(frame['timestamp'], 2.0)}")
```

**用户价值**：✅ 智能视频预处理，为视频搜索提供高质量的特征数据

### 4.2 核心功能：视频搜索与时间定位

**目标**：实现视频场景检测与内容搜索，用户可以用文字描述搜索视频片段并定位时间戳

**功能演示**：
```bash
# 搜索包含特定场景的视频片段
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "会议开始场景", "type": "text_to_video"}'

# 系统返回匹配的视频片段
{
  "results": [
    {"file": "meeting_2024.mp4", "timestamp": "00:02:15", "score": 0.89},
    {"file": "team_sync.mp4", "timestamp": "00:05:30", "score": 0.82}
  ]
}
```

**技术实现**：
- [x] [p0] TimeAccurateRetrieval精确时间检索
  - 实现TimeAccurateRetrieval（src/business/search_engine.py）
  - 实现时间戳索引查询：向量相似度检索→时间戳查询→精度验证
  - 支持时间段合并与去重：重叠时间段智能合并
  - 实现连续性检测：判断时间段是否连续（考虑±2秒精度）
  - 优化查询性能：时间戳查询延迟<10ms，批量查询<50ms
  - _需求：精确时间检索算法_

- [x] [p0] 视频搜索API
  - 扩展 `/search` 端点支持视频内容查询
  - 实现基于CLIP的视频帧检索和时间戳定位
  - 返回精确的时间戳信息（±2秒精度）
  - 支持场景边界感知的结果合并
  - _需求：2.5, 2.6, 2.7, 2.8_

**验证方式**：
```bash
# 验证视频搜索
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "测试场景", "type": "text_to_video"}'

# 验证时间戳精度
python -c "
from src.business.search_engine import TimeAccurateRetrieval
retrieval = TimeAccurateRetrieval()
# 测试时间戳精度验证
result = retrieval.validate_time_accuracy({'duration': 3.0})
print(f'时间戳精度验证: {result}')  # 应该是True
"
```

**用户价值**：✅ 可以搜索视频内容并定位到具体场景和时间点，大幅提升视频查找效率

## 阶段5（音频处理与搜索 - 基于预处理框架）

### 5.1 核心功能：音频处理器实现

**目标**：基于阶段2的预处理框架，实现音频文件的智能处理，支持内容分类和特征提取

**⚠️ 依赖关系**：此阶段严重依赖阶段2的MediaProcessor提供标准化音频输入！

**技术实现**：
- [x] [p0] AudioProcessor音频处理器（基于预处理框架）
  - 实现AudioProcessor（src/processors/audio_processor.py）
  - **依赖MediaProcessor**：使用预处理框架提供的标准化音频输入
  - 实现格式标准化：统一转换为16kHz单声道，减少60-70%数据量
  - 集成FFmpeg进行音频格式转换和质量优化
  - 实现质量过滤：过滤低质量、过短或纯噪音片段
  - 支持多种音频格式的精确识别和差异化处理
  - _需求：音频处理策略设计_

- [x] [p0] AudioClassifier音频分类器
  - 实现AudioClassifier（src/processors/audio_classifier.py）
  - 集成inaSpeechSegmenter进行智能音频分类（音乐、语音、噪音）
  - 实现分段处理：音乐30秒片段，语音3-10秒片段
  - 支持音频内容类型的自动识别和路由
  - _需求：音频内容分类_

- [x] [p0] 音频向量化与存储
  - 集成Python-native Whisper模型进行语音转文字（处理**预处理后的**音频）
  - 集成Python-native CLAP模型提取音频特征（处理**预处理后的**音频）
  - 建立audio_vectors集合，存储音频特征和时间戳
  - 支持批处理优化，批处理大小8
  - _需求：3.1, 3.2, 3.3, 3.4_

**验证方式**：
```python
# ⚠️ 前置检查：确保阶段0和阶段2已完成
import os
if not os.path.exists('./data/models/whisper-base'):
    raise RuntimeError("错误：请先完成阶段0的模型准备工作！")
if not os.path.exists('./data/models/clap-htsat-fused'):
    raise RuntimeError("错误：请先完成阶段0的模型准备工作！")

# 验证预处理框架可用
from src.business.media_processor import MediaProcessor
media_processor = MediaProcessor()
print('预处理框架可用')

# 验证音频处理（使用预处理框架）
from src.processors.audio_processor import AudioProcessor
processor = AudioProcessor()
result = processor.process_audio('test.wav')
print(f"音频处理结果: {result}")
print(f"输出格式符合Whisper/CLAP要求: {result['format_valid']}")

# 验证音频分类
from src.processors.audio_classifier import AudioClassifier
classifier = AudioClassifier()
segments = classifier.classify_audio('test.wav')
for seg in segments:
    print(f"{seg['type']}: {seg['start_time']:.1f}s - {seg['end_time']:.1f}s")
```

**用户价值**：✅ 智能音频预处理，为音频搜索提供高质量的特征数据

### 5.2 核心功能：音频内容转录与搜索

**目标**：实现音频内容转录与搜索，支持语音转文字和音频相似度匹配

**功能演示**：
```bash
# 用文字搜索音频内容（基于语音转录）
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "项目计划讨论", "type": "text_to_audio"}'

# 系统返回包含相关语音的音频文件
{
  "results": [
    {"file": "meeting_audio.wav", "transcript": "...项目计划讨论...", "score": 0.91},
    {"file": "interview.mp3", "transcript": "...讨论项目进展...", "score": 0.83}
  ]
}
```

**技术实现**：
- [x] [p0] 音频搜索API
  - 扩展 `/search` 端点支持音频内容查询
  - 实现基于转录文本的语音搜索（Whisper→CLIP）
  - 实现基于音频特征的音乐搜索（CLAP）
  - 支持时间戳精确定位（±0.1秒音频精度）
  - _需求：3.5, 6.4_

- [x] [p0] 多模态音频处理集成
  - 实现音频内容的多模态向量化（CLAP + Whisper）
  - 支持语音内容的文本检索能力
  - 实现音乐内容的音频特征检索
  - 集成时间戳处理，支持音频片段精确定位
  - _需求：多模态音频处理_

**验证方式**：
```bash
# 验证音频搜索
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "测试语音", "type": "text_to_audio"}'

# 验证语音转录
python -c "
from src.business.embedding_engine import EmbeddingEngine
engine = EmbeddingEngine()
result = engine.transcribe_audio('test_speech.wav')
print(f'转录结果: {result}')
"
```

**用户价值**：✅ 可以搜索音频文件中的语音内容，解决录音文件难以查找的问题

## 阶段6（人脸识别与智能检索）

### 6.1 核心功能：人脸识别系统

**目标**：实现需求2中的人脸识别功能，支持预定义人脸照片+名字的关联检索

**功能演示**：
```bash
# 添加人脸到库
curl -X POST "http://localhost:8000/faces/persons" \
  -F "name=张三" \
  -F "aliases=小张,张总" \
  -F "images=@zhangsan_1.jpg" \
  -F "images=@zhangsan_2.jpg"

# 搜索包含指定人物的文件
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "张三在会议室", "type": "text"}'

# 系统返回包含张三的文件，并优先排序
{
  "results": [
    {"file": "meeting_2024.mp4", "timestamp": "00:05:30", "person": "张三", "confidence": 0.95},
    {"file": "team_photo.jpg", "person": "张三", "confidence": 0.92}
  ]
}
```

**技术实现**：
- [x] [p1] FaceManager人脸管理器
  - 集成专业人脸识别模型（FaceNet/ArcFace）进行特征提取
  - 实现人脸检测器（MTCNN/RetinaFace）和512维特征向量生成
  - 支持预定义人脸库管理：存储人脸照片和对应名字关联
  - 实现人脸聚类和相似度计算，支持动态添加新人脸
  - _需求：2.1, 2.2, 2.4, FaceManager设计_

- [x] [p1] 混合存储架构
  - 实现SQLite存储人物信息：persons表（姓名、别名）、face_images表、file_faces表
  - 实现Qdrant存储人脸特征向量：face_vectors集合（512维向量）
  - 支持人脸-名字关联管理和别名系统
  - 实现数据一致性保障：向量-元数据同步、事务性操作
  - _需求：2.1, 2.5, 存储架构设计_

- [x] [p1] 人脸索引与检测
  - 为图片和视频建立人脸索引，自动检测和特征提取
  - 视频每5秒采样一帧进行人脸检测和人物匹配
  - 存储人脸位置（bbox）、时间戳和置信度信息
  - 实现人脸质量评估和过滤机制
  - _需求：2.2, 2.7_

- [x] [p1] 人脸检索API
  - 实现基于人脸特征的相似度搜索和人名匹配
  - 支持人名查询生成文件白名单，提升检索效率30-50%
  - 集成动态权重调整：人名检索时自动提升人脸相关权重
  - 实现人脸数据库维护和管理接口
  - _需求：2.3, 2.6_

**用户价值**：✅ 可以通过人名精确检索包含特定人物的图片和视频

### 6.2 核心功能：智能检索策略

**目标**：实现SmartRetrievalEngine，支持查询类型识别和动态权重分配

**功能演示**：
```bash
# 人名查询 - 自动启用人脸预检索
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "张三在讲话", "type": "smart"}'

# 音乐查询 - 自动提升CLAP权重
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "轻音乐背景", "type": "smart"}'
```

**技术实现**：
- [x] [p1] SmartRetrievalEngine智能检索引擎
  - 实现查询类型自动识别：人名、音频、视觉、通用查询
  - 集成人名识别器：智能识别查询中的预设人名（从SQLite查询）
  - 实现配置驱动的关键词检测：音频、视觉关键词从config.yml读取
  - 配置修改后重启生效，简化开发维护复杂度
  - _需求：8.6, 8.7, 8.8, SmartRetrievalEngine设计_

- [x] [p1] MultiModalFusionEngine融合引擎
  - 实现动态权重融合：检测查询中的人名，自动提升人脸相关权重
  - 实现权重计算器：基于人名匹配度动态调整各模态权重
  - 支持配置驱动的权重分配策略，所有参数从config.yml读取
  - 实现多模态结果聚合，按文件ID智能合并和重排序
  - _需求：8.6, 8.7, 8.8, MultiModalFusionEngine设计_

- [x] [p1] 分层检索优化策略
  - 实现人脸预检索→文件白名单生成→精确检索流程
  - 分层检索优化：缩小搜索范围，提升效率30-50%
  - 实现时间序列融合，支持视频时间戳精确匹配
  - 集成置信度评分，提供结果可信度评估
  - _需求：2.3, 2.6, 8.5_

**用户价值**：✅ 智能识别查询意图，自动优化检索策略，提升检索精度

## 阶段7（高级搜索与融合）

### 7.1 核心功能：多模态融合搜索

**目标**：实现跨模态融合搜索，用户可以同时使用文字、图片、音频进行组合查询

**功能演示**：
```bash
# 多模态融合搜索
curl -X POST "http://localhost:8000/search/fusion" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "会议讨论要点",
    "image_path": "./meeting_screenshot.jpg",
    "query_type": "fusion",
    "weights": {"text": 0.5, "image": 0.3, "audio": 0.2},
    "max_results": 10
  }'
```

**技术实现**：
- [x] [p2] 多模态融合算法
  - 实现权重可调节的融合搜索算法
  - 支持多模态特征融合和相似度计算
  - 创建融合结果重排序机制
  - _需求：7.1, 7.2, 7.3_

- [x] [p2] 融合搜索API
  - 创建 `/search/fusion` 专用端点
  - 实现动态权重配置
  - 支持多模态查询组合
  - _需求：2.9, 2.10, 6.5_

**用户价值**：✅ 提供更智能、更精准的跨模态搜索体验

### 7.2 核心功能：时间线搜索与定位

**目标**：实现基于时间线的搜索和定位功能，支持媒体文件的时间维度检索

**功能演示**：
```bash
# 按时间范围搜索
curl -X POST "http://localhost:8000/search/timeline" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "项目讨论",
    "time_range": {
      "start": "2024-01-01T00:00:00Z",
      "end": "2024-01-31T23:59:59Z"
    },
    "file_types": ["video", "audio"],
    "max_results": 10
  }'
```

**技术实现**：
- [x] [p2] 时间线搜索系统
  - 实现基于时间戳的搜索过滤
  - 支持时间范围查询和排序
  - 创建时间线可视化数据接口
  - _需求：5.1, 5.2, 5.3_

- [x] [p2] 时间定位API
  - 创建 `/search/timeline` 专用端点
  - 实现时间维度搜索和过滤
  - 支持时间线数据导出
  - _需求：2.11, 2.12, 6.6_

**用户价值**：✅ 可以按时间维度搜索媒体内容，适合会议记录、监控录像等场景

### 7.3 辅助功能：高级配置管理

**目标**：实现高级配置管理，支持模型参数调优和搜索策略配置

**功能演示**：
```bash
# 获取高级配置
curl -X GET "http://localhost:8000/config/advanced"

# 更新模型参数
curl -X PUT "http://localhost:8000/config/models" \
  -H "Content-Type: application/json" \
  -d '{
    "colpali_model": "colpali-v1.2",
    "embedding_dim": 128,
    "batch_size": 32,
    "similarity_threshold": 0.75
  }'
```

**技术实现**：
- [x] [p2] 高级配置系统
  - 实现模型参数动态配置
  - 支持搜索策略和算法调优
  - 创建配置版本管理和回滚
  - _需求：8.4, 8.5, 8.6_

**用户价值**：✅ 支持高级用户进行模型调优和性能优化

## 阶段8（PySide6桌面应用）

### 8.1 核心功能：PySide6桌面应用开发

**目标**：实现桌面应用程序，提供本地化的多模态搜索体验

**核心功能**：
- 本地文件系统搜索和管理
- 离线模式支持（无需网络连接）
- 系统托盘集成和快速访问
- 高级文件预览和编辑功能

**技术实现**：
- [x] [p0] PySide6桌面应用开发
  - 使用PySide6构建跨平台桌面应用
  - 实现本地数据库和文件索引
  - 支持离线模式和数据同步
  - _需求：10.1, 10.2, 10.3_

- [x] [p0] 系统集成和优化
  - 实现系统托盘集成
  - 支持全局快捷键和快速搜索
  - 优化内存使用和性能表现
  - _需求：10.4, 10.5, 10.6_

**用户价值**：✅ 提供本地化、高性能的桌面搜索体验，支持离线使用

### 8.2 辅助功能：桌面应用界面组件

**技术实现**：
- [x] [p0] 实现PySide6桌面应用框架
  - 创建主窗口和应用程序生命周期管理
  - 实现系统托盘集成和后台运行支持
  - 创建应用程序配置和主题管理
  - _需求：9.1, 9.2, 9.3, 10.1, 6.3_

- [x] [p0] 实现搜索界面组件
  - 创建多模态搜索输入界面（文本框、文件拖放区域）
  - 实现搜索类型选择和高级过滤选项
  - 创建实时搜索建议和自动完成功能
  - _需求：10.2, 10.5, 1.4_

- [x] [p0] 实现结果展示与时间定位交互
  - 创建搜索结果列表和网格视图
  - 实现缩略图生成和懒加载显示
  - 实现视频时间轴可视化，包含热图和最佳匹配标记
  - 实现可点击的时间戳注释，跳转到特定视频位置
  - _需求：4.1, 4.2, 4.3, 4.4, 4.5, 10.3, 10.4, 1.5_

## 阶段9（系统优化与部署）

### 9.1 核心功能：Python-native michaelfeil/infinity 集成优化

**目标**：优化 Python-native michaelfeil/infinity 模式，实现生产级性能和稳定性

**技术实现**：
- [x] [p0] Python-native EmbeddingEngine优化（基于 michaelfeil/infinity）
  - 优化AsyncEngineArray统一管理CLIP、CLAP、Whisper等模型
  - 实现统一GPU内存池管理，提升资源利用率
  - 集成智能批处理优化，提升GPU利用率
  - 实现模型热加载和动态切换机制
  - _需求：Python-native架构优化_

- [x] [p0] 性能监控与资源管理
  - 实现EmbeddingEngine健康检查：模型加载状态、推理性能测试
  - 集成GPU/CPU/内存使用监控和自动清理机制
  - 实现批处理大小动态调整，根据硬件条件优化
  - 支持硬件自适应配置：CPU/GPU自动检测和参数调整
  - _需求：6.1, 6.2, 性能优化_

- [x] [p0] 错误处理与稳定性
  - 实现Python原生异常机制，简化错误处理逻辑
  - 支持模型加载失败的自动重试和降级机制
  - 实现向量质量验证：维度检查、范数验证、质量评估
  - 集成内存泄漏防护和资源竞争解决方案
  - _需求：6.2, 6.5, 系统稳定性_

**用户价值**：✅ 提供高性能、稳定可靠的AI模型服务，简化部署和维护

### 9.2 核心功能：系统性能优化

**目标**：实现系统性能优化、稳定性提升和生产环境部署

**核心功能**：
- 性能优化和内存管理
- 系统监控和日志管理
- 容器化部署和自动化运维
- 高可用性和负载均衡

**技术实现**：
- [x] [p3] 性能优化
  - 实现内存池管理和资源回收
  - 优化向量搜索算法和索引结构
  - 支持分布式部署和负载均衡
  - _需求：11.1, 11.2, 11.3_

- [x] [p3] 系统监控和运维
  - 实现系统健康检查和监控告警
  - 支持日志聚合和分析
  - 实现自动化部署和回滚
  - _需求：11.4, 11.5, 11.6_

**用户价值**：✅ 提供稳定、高效、可扩展的生产级多模态搜索系统

### 9.3 核心功能：时间戳处理系统

**目标**：实现±2秒精度的时间戳处理，支持多模态时间同步和精确检索

**技术实现**：
- [x] [p0] TimestampProcessor时间戳处理器
  - 实现帧级时间戳计算：基于帧率的精确时间计算（±0.033s@30fps）
  - 实现多模态时间同步验证：视觉、音频、语音统一时间基准
  - 支持±2秒精度保证：重叠时间窗口+精确边界检测
  - 实现场景感知切片：避免在场景中间进行时间切分
  - _需求：时间戳处理机制设计_

- [x] [p0] TimeAccurateRetrieval精确时间检索
  - 实现时间戳索引查询：向量相似度检索→时间戳查询→精度验证
  - 支持时间段合并与去重：重叠时间段智能合并
  - 实现连续性检测：判断时间段是否连续（考虑±2秒精度）
  - 优化查询性能：时间戳查询延迟<10ms，批量查询<50ms
  - _需求：5.1, 5.2, 5.3, 精确时间检索算法_

- [x] [p0] 时间戳数据库设计
  - 实现video_timestamps表：存储文件ID、向量ID、时间戳、模态类型
  - 创建时间范围查询索引：优化时间戳查询性能
  - 支持多模态时间戳存储：视觉、音频、语音分别记录
  - 实现时间戳漂移校正：确保多模态时间同步
  - _需求：时间戳数据库设计_

### 9.4 核心功能：ProcessingOrchestrator处理编排

**目标**：实现统一的处理流程编排，协调各专业处理模块的调用顺序和数据流转

**技术实现**：
- [x] [p0] ProcessingOrchestrator处理编排器
  - 实现策略路由：根据文件类型和内容特征选择处理策略
  - 实现流程编排：管理预处理→向量化→存储的调用顺序
  - 支持状态管理：跟踪处理进度、状态转换和错误恢复
  - 实现资源协调：协调CPU/GPU资源分配，避免资源竞争
  - _需求：ProcessingOrchestrator设计_

- [x] [p0] TaskManager任务队列管理器
  - 实现SQLite持久化任务队列，支持任务状态追踪
  - 支持优先级队列管理，支持紧急任务插队
  - 实现并发控制，防止系统资源过度占用
  - 集成失败重试机制，支持指数退避算法
  - _需求：TaskManager设计_

- [x] [p1] FileMonitor文件监控服务
  - 实现跨平台文件系统事件监控（基于watchdog）
  - 支持增量更新机制，只处理新增或修改的文件
  - 实现文件类型过滤，支持自定义扩展名规则
  - 集成防抖处理，避免频繁文件操作导致的重复触发
  - _需求：4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

### 9.5 系统稳定性与部署优化

**技术实现**：
- [x] [p2] 系统稳定性与部署优化
  - 实现内存泄漏防护和资源竞争解决方案
  - 集成高级错误处理：Python原生异常机制，简化错误处理
  - 创建数据一致性检查：向量-元数据同步验证
  - 实现系统状态监控和告警机制
  - _需求：3.5, 5.2, 5.3, 8.3, 8.5_

- [x] [p2] 离线部署与服务管理
  - 创建Python-native模式启动脚本：无需独立服务进程管理
  - 实现本地模型目录支持：HF_HOME环境变量配置
  - 支持完全离线部署：预下载模型文件，零网络依赖
  - 集成硬件自适应配置：CPU/GPU自动检测和参数调整
  - _需求：离线部署方案_

- [x] [p2] QdrantClient抽象层与扩展性
  - 保留QdrantClient抽象层，便于未来微服务化演进
  - 当前使用本地二进制Qdrant，零配置部署
  - 预留远程Qdrant、集群部署的扩展接口
  - 实现统一向量操作接口，支持不同部署模式
  - _需求：单机版vs微服务架构权衡_

### 9.6 测试与质量保证

**技术实现**：
- [x] [p2] Python-native模式测试套件
  - 创建EmbeddingEngine测试：验证CLIP、CLAP、Whisper等模型Python-native集成
  - 实现时间戳处理测试：验证±2秒精度、多模态同步、帧级计算
  - 实现配置驱动测试：验证config.yml参数加载、验证、热重载
  - 集成性能测试：验证Python-native模式20-30%性能提升
  - _需求：Python-native架构测试_

- [x] [p2] 时间戳精度验证测试
  - 实现帧级时间戳精度测试：验证帧级精度(±0.033s@30fps)
  - 实现多模态同步测试：验证视觉-音频时间对齐容差
  - 实现检索时间精度测试：验证±2秒精度要求100%满足
  - 实现性能测试：验证时间戳查询延迟<10ms，批量查询<50ms
  - _需求：时间戳处理测试要求_

- [x] [p2] 集成测试和端到端验证
  - 创建多模态搜索工作流测试：文搜图、图搜图、视频时间戳定位
  - 实现大文件处理测试：4K视频处理、内存使用监控、批处理优化
  - 实现人脸识别集成测试：人名检索、动态权重、分层检索优化
  - 创建离线部署测试：本地模型加载、零网络依赖验证
  - _需求：7.1, 7.2, 9.1, 9.2, 9.3, 10.1_

### 9.7 文档与部署准备

**技术实现**：
- [x] [p2] 创建用户文档和部署指南
  - 编写安装和配置指南，支持不同硬件配置
  - 创建用户操作手册和功能文档
  - 实现系统需求检查和兼容性验证工具
  - _需求：5.5, 9.4, 9.5_

- [x] [p2] 实现统一部署脚本系统
  - 创建智能部署脚本，优先从offline目录获取依赖和模型文件
  - 实现本地资源检测机制，支持完全离线部署
  - 创建资源完整性验证和自动补全功能
  - 实现一键部署流程，简化测试和离线环境部署
  - _需求：9.6, 11.7_

- [x] [p2] 实现打包和分发系统
  - 创建跨平台打包脚本（PyInstaller或类似工具）
  - 实现自动化构建和版本管理
  - 创建容器化部署配置（Docker/Kubernetes）
  - _需求：9.6, 11.7_

## 阶段10（Web用户界面）

### 10.1 核心功能：Web前端界面开发（可选）

**目标**：实现可选的Web用户界面，提供跨平台访问能力

**核心功能**：
- 基础多模态搜索界面
- 简化的搜索结果展示
- 基础配置管理
- 系统状态监控

**技术实现**：
- [x] [p3] 前端界面开发（可选）
  - 使用Vue.js构建轻量级Web界面
  - 实现基础的响应式设计
  - 集成基础文件上传功能
  - _需求：可选功能_

- [x] [p3] Web API完善（可选）
  - 完善Web专用API接口
  - 实现基础的实时通信
  - 支持简化的文件处理
  - _需求：可选功能_

**用户价值**：✅ 提供可选的跨平台访问能力，适合远程使用场景

### 10.2 辅助功能：配置管理界面

**技术实现**：
- [x] [p2] 实现配置管理界面
  - 创建系统设置面板：监控目录、模型选择、硬件配置
  - 实现人物库管理界面：添加、删除、编辑人物标签
  - 创建处理队列监控和任务管理界面
  - _需求：2.1, 2.5, 3.1, 8.4_

## 实施优先级说明

### 优先级定义
- **[p0]**：核心功能，必须实现
- **[p1]**：重要功能，建议实现
- **[p2]**：增强功能，根据资源情况实现
- **[p3]**：可选功能，仅在需要时实现

### 开发建议

1. **⚠️ 阶段0必须优先**：按照阶段0→1→2→3→4→5→6→7→8→9→10的顺序实施，**阶段0是所有后续开发的前置依赖**
2. **模型依赖检查**：每个阶段开始前都必须检查所需模型是否已部署，避免开发过程中的阻塞
3. **预处理框架优先**：阶段2的媒体预处理框架是阶段3-5的基础，必须稳固实现
4. **基础架构稳固**：阶段1-2建立系统基础架构和预处理能力，必须100%完成
5. **核心功能优先**：阶段6的人脸识别和智能检索是核心差异化功能，必须实现
6. **桌面UI优先**：优先完成PySide6桌面应用（阶段8），提供完整的用户体验
7. **Web UI可选**：Web用户界面（阶段10）为可选功能，适合远程访问场景
8. **原生体验**：PySide6提供更好的系统集成和离线使用体验
9. **测试驱动**：每个阶段都包含验证方式，确保功能正确性后再进入下一阶段
10. **离线开发**：确保开发环境完全离线，避免网络依赖导致的开发中断

### 技术选型理由

- **PySide6**：主要用户界面，提供原生桌面体验、离线功能和深度系统集成
- **FastAPI**：现代、快速、易用的Web框架，适合构建RESTful API
- **Vue.js**：可选Web界面，轻量级前端框架，适合简单的远程访问场景
