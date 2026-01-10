# MSearch 数据模型文档

## 概述

本文档详细描述了 MSearch 多模态搜索系统中使用的所有数据模型，包括字段定义、约束条件、关系图和使用示例。

**数据模型分类**：
- **核心数据模型**：文件、向量、任务等核心实体
- **媒体处理模型**：场景、音频分段等媒体相关实体
- **配置模型**：模型配置、硬件信息等配置实体
- **API模型**：请求和响应模型

## 1. 核心数据模型

### 1.1 FileMetadata - 文件元数据

**描述**：存储文件的基本信息和处理状态。

**字段定义**：

| 字段名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| id | str | 是 | - | 文件唯一ID（UUID v4） |
| file_path | str | 是 | - | 文件绝对路径 |
| file_name | str | 是 | - | 文件名（含扩展名） |
| file_type | str | 是 | - | 文件类型（image/video/audio） |
| file_size | int | 是 | - | 文件大小（字节） |
| file_hash | str | 是 | - | 文件SHA256哈希值 |
| created_at | float | 是 | - | 文件创建时间（Unix时间戳） |
| updated_at | float | 是 | - | 文件更新时间（Unix时间戳） |
| processed_at | float | 否 | null | 处理完成时间（Unix时间戳） |
| processing_status | str | 是 | pending | 处理状态（pending/processing/completed/failed） |
| metadata | Dict[str, Any] | 否 | {} | 扩展元数据（JSON格式） |

**约束条件**：
- `id`：必须符合UUID v4格式
- `file_path`：必须是有效的绝对路径
- `file_type`：必须是 image、video 或 audio 之一
- `file_size`：必须大于0
- `file_hash`：必须是64字符的十六进制字符串
- `processing_status`：必须是 pending、processing、completed 或 failed 之一

**索引设计**：
- 主键：`id`
- 唯一索引：`file_path`
- 唯一索引：`file_hash`
- 普通索引：`file_type`
- 普通索引：`processing_status`

**使用示例**：

```python
from datetime import datetime
import uuid

# 创建文件元数据
file_metadata = {
    "id": str(uuid.uuid4()),
    "file_path": "/path/to/video.mp4",
    "file_name": "video.mp4",
    "file_type": "video",
    "file_size": 1024000,
    "file_hash": "a1b2c3d4e5f6...（64字符）",
    "created_at": datetime.now().timestamp(),
    "updated_at": datetime.now().timestamp(),
    "processed_at": None,
    "processing_status": "pending",
    "metadata": {
        "duration": 120.5,
        "resolution": "1920x1080",
        "frame_rate": 30
    }
}

# 查询文件元数据
query = {
    "file_type": "video",
    "processing_status": "completed"
}
```

### 1.2 VectorData - 向量数据

**描述**：存储多模态向量数据和关联信息。

**字段定义**：

| 字段名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| id | str | 是 | - | 向量唯一ID（UUID v4或文件ID+模态） |
| vector | List[float] | 是 | - | 向量数据 |
| modality | str | 是 | - | 模态类型（image/video/audio/text/face） |
| file_id | str | 是 | - | 关联文件ID |
| segment_id | str | 否 | null | 视频片段ID（仅视频） |
| start_time | float | 否 | null | 视频片段开始时间（仅视频，精度±5秒） |
| end_time | float | 否 | null | 视频片段结束时间（仅视频，精度±5秒） |
| metadata | Dict[str, Any] | 否 | {} | 扩展元数据 |
| created_at | float | 是 | - | 创建时间戳 |

**约束条件**：
- `id`：必须唯一
- `vector`：维度必须一致（根据模型确定，如512维）
- `modality`：必须是 image、video、audio、text 或 face 之一
- `file_id`：必须关联到有效的 FileMetadata.id
- `segment_id`：当 modality 为 video 时必填
- `start_time`、`end_time`：当 modality 为 video 时必填，精度±5秒
- `start_time` < `end_time`

**索引设计**：
- 主键：`id`
- 普通索引：`file_id`
- 普通索引：`modality`
- 向量索引：`vector`（HNSW索引）

**使用示例**：

```python
import uuid

# 创建向量数据
vector_data = {
    "id": f"{file_id}_video",
    "vector": [0.1234, 0.5678, ...],  # 512维向量
    "modality": "video",
    "file_id": file_id,
    "segment_id": "seg_001",
    "start_time": 10.5,
    "end_time": 15.5,
    "metadata": {
        "frame_index": 315,
        "keyframe": True
    },
    "created_at": datetime.now().timestamp()
}

# 向量检索
query_vector = [0.2345, 0.6789, ...]  # 查询向量
results = vector_store.search_vectors(
    query_vector=query_vector,
    limit=20,
    filter={"modality": "video"}
)
```

### 1.3 Task - 任务数据

**描述**：存储异步任务的状态和执行信息。

**字段定义**：

| 字段名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| id | str | 是 | - | 任务唯一ID（UUID v4） |
| task_type | str | 是 | - | 任务类型（file_scan/file_embed/video_slice等） |
| task_data | Dict[str, Any] | 是 | - | 任务数据 |
| priority | int | 是 | 5 | 优先级（0-10，数字越小优先级越高） |
| status | str | 是 | pending | 状态（pending/running/completed/failed/cancelled/paused） |
| created_at | float | 是 | - | 创建时间戳 |
| updated_at | float | 是 | - | 更新时间戳 |
| started_at | float | 否 | null | 开始执行时间 |
| completed_at | float | 否 | null | 完成时间 |
| retry_count | int | 是 | 0 | 当前重试次数 |
| max_retries | int | 是 | 3 | 最大重试次数 |
| result | Any | 否 | null | 任务执行结果 |
| error | str | 否 | null | 错误信息（如果有） |
| progress | float | 是 | 0.0 | 任务进度（0.0-1.0） |

**约束条件**：
- `id`：必须符合UUID v4格式
- `task_type`：必须是预定义的任务类型之一
- `priority`：必须在0-10范围内
- `status`：必须是 pending、running、completed、failed、cancelled 或 paused 之一
- `retry_count` ≤ `max_retries`
- `progress`：必须在0.0-1.0范围内
- `started_at` ≥ `created_at`
- `completed_at` ≥ `started_at`（如果两者都存在）

**索引设计**：
- 主键：`id`
- 普通索引：`task_type`
- 普通索引：`status`
- 普通索引：`priority`
- 普通索引：`created_at`

**使用示例**：

```python
import uuid

# 创建任务
task = {
    "id": str(uuid.uuid4()),
    "task_type": "file_embed",
    "task_data": {
        "file_path": "/path/to/video.mp4",
        "file_id": file_id,
        "modality": "video"
    },
    "priority": 3,
    "status": "pending",
    "created_at": datetime.now().timestamp(),
    "updated_at": datetime.now().timestamp(),
    "started_at": None,
    "completed_at": None,
    "retry_count": 0,
    "max_retries": 3,
    "result": None,
    "error": None,
    "progress": 0.0
}

# 查询任务
query = {
    "status": "pending",
    "priority": {"$lte": 3}
}
```

## 2. 媒体处理模型

### 2.1 SceneSegment - 场景数据

**描述**：存储视频场景检测的结果。

**字段定义**：

| 字段名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| scene_id | str | 是 | - | 场景ID |
| start_time | float | 是 | - | 开始时间（秒） |
| end_time | float | 是 | - | 结束时间（秒） |
| duration | float | 是 | - | 时长（秒） |
| frame_count | int | 是 | - | 帧数 |
| is_key_transition | bool | 是 | false | 是否为关键转场点 |
| confidence | float | 是 | - | 场景检测置信度 |

**约束条件**：
- `scene_id`：必须唯一
- `start_time` ≥ 0
- `end_time` > `start_time`
- `duration` = `end_time` - `start_time`
- `frame_count` ≥ 1
- `confidence`：必须在0.0-1.0范围内

**使用示例**：

```python
# 创建场景数据
scene_segment = {
    "scene_id": "scene_001",
    "start_time": 0.0,
    "end_time": 5.0,
    "duration": 5.0,
    "frame_count": 150,
    "is_key_transition": True,
    "confidence": 0.95
}
```

### 2.2 AudioSegment - 音频分段数据

**描述**：存储音频分段和分类结果。

**字段定义**：

| 字段名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| segment_id | str | 是 | - | 分段ID |
| start_time | float | 是 | - | 开始时间（秒） |
| end_time | float | 是 | - | 结束时间（秒） |
| duration | float | 是 | - | 时长（秒） |
| content_type | str | 是 | - | 内容类型（speech/music/noise/silence/mixed/unknown） |
| confidence | float | 是 | - | 分类置信度 |
| recommended_model | str | 是 | - | 推荐使用的模型（clap/whisper） |
| features | Dict[str, Any] | 否 | {} | 音频特征 |
| quality_score | float | 是 | - | 质量评分 |

**约束条件**：
- `segment_id`：必须唯一
- `start_time` ≥ 0
- `end_time` > `start_time`
- `duration` = `end_time` - `start_time`
- `content_type`：必须是 speech、music、noise、silence、mixed 或 unknown 之一
- `confidence`：必须在0.0-1.0范围内
- `recommended_model`：必须是 clap 或 whisper 之一
- `quality_score`：必须在0.0-1.0范围内

**使用示例**：

```python
# 创建音频分段数据
audio_segment = {
    "segment_id": "audio_001",
    "start_time": 0.0,
    "end_time": 10.0,
    "duration": 10.0,
    "content_type": "speech",
    "confidence": 0.92,
    "recommended_model": "whisper",
    "features": {
        "spectral_centroid": 2500.5,
        "mfcc": [12.3, 45.6, ...],
        "zero_crossing_rate": 0.15
    },
    "quality_score": 0.88
}
```

## 3. 配置模型

### 3.1 ModelConfig - 模型配置

**描述**：存储AI模型的配置信息。

**字段定义**：

#### 图像/视频模型配置

| 字段名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| model_name | str | 是 | - | 模型名称/路径 |
| device | str | 是 | cpu | 设备类型（cuda/cpu） |
| batch_size | int | 是 | 16 | 批量大小 |
| precision | str | 是 | float32 | 模型精度（float32/float16/int8） |
| max_resolution | int | 是 | 224 | 最大输入分辨率 |

#### 音频模型配置

| 字段名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| model_name | str | 是 | - | 模型名称/路径 |
| device | str | 是 | cpu | 设备类型（cuda/cpu） |
| batch_size | int | 是 | 8 | 批量大小 |
| precision | str | 是 | float32 | 模型精度（float32/float16/int8） |

**约束条件**：
- `device`：必须是 cuda 或 cpu 之一
- `batch_size`：必须大于0
- `precision`：必须是 float32、float16 或 int8 之一
- `max_resolution`：必须大于0

**使用示例**：

```python
# 模型配置
model_config = {
    "image_video_model": {
        "model_name": "apple/mobileclip",
        "device": "cuda",
        "batch_size": 16,
        "precision": "float16",
        "max_resolution": 224
    },
    "clap": {
        "model_name": "laion/clap-htsat-unfused",
        "device": "cuda",
        "batch_size": 8,
        "precision": "float32"
    },
    "whisper": {
        "model_name": "openai/whisper-base",
        "device": "cpu",
        "precision": "float32"
    }
}
```

### 3.2 HardwareInfo - 硬件信息

**描述**：存储系统硬件配置信息。

**字段定义**：

#### CPU信息

| 字段名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| model | str | 是 | - | CPU型号 |
| cores | int | 是 | - | 物理核心数 |
| threads | int | 是 | - | 逻辑线程数 |
| frequency | float | 是 | - | 主频（GHz） |
| architecture | str | 是 | - | 架构类型（x86_64/arm64） |

#### GPU信息

| 字段名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| name | str | 是 | - | GPU名称 |
| memory_total | int | 是 | - | 显存总量（MB） |
| memory_free | int | 是 | - | 可用显存（MB） |
| cuda_version | str | 否 | null | CUDA版本 |
| driver_version | str | 否 | null | 驱动版本 |
| compute_capability | str | 否 | null | 计算能力 |

#### 内存信息

| 字段名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| total | int | 是 | - | 总内存（MB） |
| available | int | 是 | - | 可用内存（MB） |
| used | int | 是 | - | 已用内存（MB） |

#### 磁盘信息

| 字段名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| path | str | 是 | - | 路径 |
| total | int | 是 | - | 总空间（MB） |
| free | int | 是 | - | 可用空间（MB） |
| used | int | 是 | - | 已用空间（MB） |

**约束条件**：
- `cores`、`threads`：必须大于0
- `frequency`：必须大于0
- `memory_total`、`memory_free`：必须大于等于0
- `total`、`available`、`used`：必须大于等于0

**使用示例**：

```python
# 硬件信息
hardware_info = {
    "cpu": {
        "model": "Intel Core i7-9700K",
        "cores": 8,
        "threads": 8,
        "frequency": 3.6,
        "architecture": "x86_64"
    },
    "gpu": [
        {
            "name": "NVIDIA GeForce RTX 3080",
            "memory_total": 10240,
            "memory_free": 8192,
            "cuda_version": "11.8",
            "driver_version": "525.85.12",
            "compute_capability": "8.6"
        }
    ],
    "memory": {
        "total": 32768,
        "available": 16384,
        "used": 16384
    },
    "disk": {
        "path": "/data",
        "total": 1024000,
        "free": 512000,
        "used": 512000
    }
}
```

## 4. API模型

### 4.1 基础响应模型

#### BaseResponse

**描述**：所有API响应的基础模型。

**字段定义**：

| 字段名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| success | bool | 是 | true | 请求是否成功 |
| message | str | 是 | "" | 响应消息 |
| timestamp | datetime | 是 | 当前时间 | 时间戳 |
| request_id | str | 否 | null | 请求ID |

**使用示例**：

```python
from datetime import datetime

response = {
    "success": True,
    "message": "操作成功",
    "timestamp": datetime.now(),
    "request_id": "req_123456"
}
```

#### PaginationRequest

**描述**：分页请求模型。

**字段定义**：

| 字段名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| page | int | 是 | 1 | 页码（≥1） |
| page_size | int | 是 | 20 | 每页大小（1-100） |

**使用示例**：

```python
pagination_request = {
    "page": 1,
    "page_size": 20
}
```

#### PaginationResponse

**描述**：分页响应模型。

**字段定义**：

| 字段名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| page | int | 是 | - | 当前页码 |
| page_size | int | 是 | - | 每页大小 |
| total_count | int | 是 | - | 总记录数 |
| total_pages | int | 是 | - | 总页数 |
| has_next | bool | 是 | - | 是否有下一页 |
| has_prev | bool | 是 | - | 是否有上一页 |

**使用示例**：

```python
pagination_response = {
    "page": 1,
    "page_size": 20,
    "total_count": 100,
    "total_pages": 5,
    "has_next": True,
    "has_prev": False
}
```

### 4.2 搜索模型

#### SearchRequest

**描述**：搜索请求基础模型。

**字段定义**：

| 字段名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| query | str | 是 | - | 搜索查询（≥1字符） |
| modalities | List[str] | 否 | null | 指定模态类型 |
| file_types | List[str] | 否 | null | 文件类型过滤 |
| similarity_threshold | float | 是 | 0.7 | 相似度阈值（0.0-1.0） |
| limit | int | 是 | 20 | 结果数量限制（1-100） |
| ranking_strategy | str | 是 | hybrid | 排序策略 |
| include_metadata | bool | 是 | true | 是否包含元数据 |

**使用示例**：

```python
search_request = {
    "query": "海边日落",
    "modalities": ["image", "video"],
    "file_types": ["jpg", "mp4"],
    "similarity_threshold": 0.8,
    "limit": 20,
    "ranking_strategy": "hybrid",
    "include_metadata": True
}
```

#### SearchResultItem

**描述**：搜索结果项模型。

**字段定义**：

| 字段名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| id | str | 是 | - | 结果ID |
| file_id | str | 是 | - | 文件ID |
| file_path | str | 是 | - | 文件路径 |
| file_name | str | 是 | - | 文件名 |
| file_type | str | 是 | - | 文件类型 |
| similarity | float | 是 | - | 相似度（0.0-1.0） |
| modality | str | 是 | - | 模态类型 |
| segment_id | str | 否 | null | 片段ID |
| start_time | float | 否 | null | 开始时间 |
| end_time | float | 否 | null | 结束时间 |
| thumbnail_path | str | 否 | null | 缩略图路径 |
| metadata | Dict[str, Any] | 否 | {} | 元数据 |
| created_at | datetime | 是 | - | 创建时间 |

**使用示例**：

```python
from datetime import datetime

search_result_item = {
    "id": "result_001",
    "file_id": "file_001",
    "file_path": "/path/to/video.mp4",
    "file_name": "video.mp4",
    "file_type": "video",
    "similarity": 0.95,
    "modality": "video",
    "segment_id": "seg_001",
    "start_time": 10.5,
    "end_time": 15.5,
    "thumbnail_path": "/path/to/thumb.jpg",
    "metadata": {
        "duration": 120.5,
        "resolution": "1920x1080"
    },
    "created_at": datetime.now()
}
```

#### SearchResponse

**描述**：搜索响应模型。

**字段定义**：

| 字段名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| success | bool | 是 | true | 请求是否成功 |
| message | str | 是 | "" | 响应消息 |
| timestamp | datetime | 是 | 当前时间 | 时间戳 |
| request_id | str | 否 | null | 请求ID |
| results | List[SearchResultItem] | 是 | [] | 搜索结果 |
| total_count | int | 是 | - | 总结果数 |
| search_time | float | 是 | - | 搜索耗时（秒） |
| query_info | Dict[str, Any] | 是 | - | 查询信息 |
| pagination | PaginationResponse | 否 | null | 分页信息 |

**使用示例**：

```python
from datetime import datetime

search_response = {
    "success": True,
    "message": "搜索成功",
    "timestamp": datetime.now(),
    "request_id": "req_123456",
    "results": [search_result_item],
    "total_count": 100,
    "search_time": 0.5,
    "query_info": {
        "query": "海边日落",
        "modality": "video"
    },
    "pagination": pagination_response
}
```

### 4.3 任务模型

#### TaskCreateRequest

**描述**：创建任务请求模型。

**字段定义**：

| 字段名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| task_type | str | 是 | - | 任务类型 |
| input_data | Dict[str, Any] | 是 | - | 输入数据 |
| priority | int | 是 | 3 | 优先级（1-9） |
| max_retries | int | 是 | 3 | 最大重试次数（0-10） |
| dependencies | List[str] | 否 | [] | 依赖任务ID列表 |

**使用示例**：

```python
task_create_request = {
    "task_type": "file_embed",
    "input_data": {
        "file_path": "/path/to/video.mp4",
        "file_id": "file_001"
    },
    "priority": 3,
    "max_retries": 3,
    "dependencies": []
}
```

#### TaskResponse

**描述**：任务响应模型。

**字段定义**：

| 字段名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| success | bool | 是 | true | 请求是否成功 |
| message | str | 是 | "" | 响应消息 |
| timestamp | datetime | 是 | 当前时间 | 时间戳 |
| request_id | str | 否 | null | 请求ID |
| task_id | str | 是 | - | 任务ID |
| task_type | str | 是 | - | 任务类型 |
| status | str | 是 | - | 任务状态 |
| priority | int | 是 | - | 优先级 |
| progress | float | 是 | - | 任务进度（0.0-1.0） |
| created_at | datetime | 是 | - | 创建时间 |
| started_at | datetime | 否 | null | 开始时间 |
| completed_at | datetime | 否 | null | 完成时间 |
| estimated_duration | float | 否 | null | 预计耗时（秒） |
| output_data | Dict[str, Any] | 否 | null | 输出数据 |
| error_info | Dict[str, Any] | 否 | null | 错误信息 |

**使用示例**：

```python
from datetime import datetime

task_response = {
    "success": True,
    "message": "任务创建成功",
    "timestamp": datetime.now(),
    "request_id": "req_123456",
    "task_id": "task_001",
    "task_type": "file_embed",
    "status": "pending",
    "priority": 3,
    "progress": 0.0,
    "created_at": datetime.now(),
    "started_at": None,
    "completed_at": None,
    "estimated_duration": 30.0,
    "output_data": None,
    "error_info": None
}
```

### 4.4 文件模型

#### FileInfo

**描述**：文件信息模型。

**字段定义**：

| 字段名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| id | str | 是 | - | 文件ID |
| file_path | str | 是 | - | 文件路径 |
| file_name | str | 是 | - | 文件名 |
| file_type | str | 是 | - | 文件类型 |
| file_size | int | 是 | - | 文件大小（字节） |
| file_hash | str | 是 | - | 文件哈希 |
| created_at | datetime | 是 | - | 创建时间 |
| modified_at | datetime | 是 | - | 修改时间 |
| processing_status | str | 是 | - | 处理状态 |
| metadata | Dict[str, Any] | 否 | {} | 元数据 |

**使用示例**：

```python
from datetime import datetime

file_info = {
    "id": "file_001",
    "file_path": "/path/to/video.mp4",
    "file_name": "video.mp4",
    "file_type": "video",
    "file_size": 1024000,
    "file_hash": "a1b2c3d4...",
    "created_at": datetime.now(),
    "modified_at": datetime.now(),
    "processing_status": "completed",
    "metadata": {
        "duration": 120.5,
        "resolution": "1920x1080"
    }
}
```

#### ScanRequest

**描述**：扫描请求模型。

**字段定义**：

| 字段名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| directory_path | str | 是 | - | 目录路径 |
| recursive | bool | 是 | true | 是否递归扫描 |
| file_types | List[str] | 否 | null | 文件类型过滤 |
| force_reindex | bool | 是 | false | 是否强制重新索引 |

**使用示例**：

```python
scan_request = {
    "directory_path": "/path/to/media",
    "recursive": True,
    "file_types": ["mp4", "jpg", "mp3"],
    "force_reindex": False
}
```

### 4.5 系统模型

#### SystemStats

**描述**：系统统计信息模型。

**字段定义**：

| 字段名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| cpu_usage | float | 是 | - | CPU使用率（%） |
| memory_usage | float | 是 | - | 内存使用率（%） |
| disk_usage | float | 是 | - | 磁盘使用率（%） |
| gpu_usage | float | 否 | null | GPU使用率（%） |
| task_queue_size | int | 是 | - | 任务队列大小 |
| active_tasks | int | 是 | - | 活跃任务数 |
| total_files | int | 是 | - | 总文件数 |
| indexed_files | int | 是 | - | 已索引文件数 |
| total_vectors | int | 是 | - | 总向量数 |

**使用示例**：

```python
system_stats = {
    "cpu_usage": 45.5,
    "memory_usage": 62.3,
    "disk_usage": 55.8,
    "gpu_usage": 78.2,
    "task_queue_size": 10,
    "active_tasks": 3,
    "total_files": 1000,
    "indexed_files": 950,
    "total_vectors": 5000
}
```

#### ModelInfo

**描述**：模型信息模型。

**字段定义**：

| 字段名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| name | str | 是 | - | 模型名称 |
| type | str | 是 | - | 模型类型 |
| version | str | 是 | - | 模型版本 |
| device | str | 是 | - | 设备类型 |
| status | str | 是 | - | 模型状态 |
| loaded_at | datetime | 否 | null | 加载时间 |

**使用示例**：

```python
from datetime import datetime

model_info = {
    "name": "apple/mobileclip",
    "type": "image_video",
    "version": "1.0",
    "device": "cuda",
    "status": "loaded",
    "loaded_at": datetime.now()
}
```

#### HardwareInfo

**描述**：硬件信息模型（API版本）。

**字段定义**：

| 字段名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| cpu | Dict[str, Any] | 是 | - | CPU信息 |
| gpu | List[Dict[str, Any]] | 是 | - | GPU信息列表 |
| memory | Dict[str, Any] | 是 | - | 内存信息 |
| disk | Dict[str, Any] | 是 | - | 磁盘信息 |

**使用示例**：

```python
hardware_info = {
    "cpu": {
        "model": "Intel Core i7-9700K",
        "cores": 8,
        "threads": 8,
        "frequency": 3.6,
        "architecture": "x86_64"
    },
    "gpu": [
        {
            "name": "NVIDIA GeForce RTX 3080",
            "memory_total": 10240,
            "memory_free": 8192,
            "cuda_version": "11.8",
            "driver_version": "525.85.12",
            "compute_capability": "8.6"
        }
    ],
    "memory": {
        "total": 32768,
        "available": 16384,
        "used": 16384
    },
    "disk": {
        "path": "/data",
        "total": 1024000,
        "free": 512000,
        "used": 512000
    }
}
```

## 5. 数据关系图

### 5.1 核心实体关系

```
FileMetadata (1) ----< (N) VectorData
    |
    | (1)
    |
    v
(N) Task
```

**关系说明**：
- 一个 FileMetadata 可以关联多个 VectorData（不同模态）
- 一个 FileMetadata 可以关联多个 Task（索引、处理等）

### 5.2 媒体处理关系

```
FileMetadata (1) ----< (N) SceneSegment
    |
    | (1)
    |
    v
(N) AudioSegment
```

**关系说明**：
- 一个视频文件可以包含多个 SceneSegment
- 一个音频文件可以包含多个 AudioSegment

### 5.3 配置关系

```
HardwareInfo ----> ModelConfig
    |
    | (推荐)
    |
    v
EmbeddingEngine
```

**关系说明**：
- HardwareInfo 用于生成 ModelConfig
- ModelConfig 用于配置 EmbeddingEngine

## 6. 数据验证规则

### 6.1 文件验证

- 文件路径必须是绝对路径
- 文件大小必须大于0
- 文件哈希必须是64字符的十六进制字符串
- 文件类型必须是 image、video 或 audio 之一

### 6.2 向量验证

- 向量维度必须一致（根据模型确定）
- 向量值必须在合理范围内（通常-1.0到1.0）
- 模态类型必须是 image、video、audio、text 或 face 之一
- 视频片段必须包含时间信息

### 6.3 任务验证

- 任务类型必须是预定义的类型之一
- 优先级必须在0-10范围内
- 状态必须是 pending、running、completed、failed、cancelled 或 paused 之一
- 进度必须在0.0-1.0范围内
- 重试次数不能超过最大重试次数

### 6.4 API验证

- 查询字符串不能为空
- 相似度阈值必须在0.0-1.0范围内
- 结果数量限制必须在1-100范围内
- 分页参数必须符合约束

## 7. 数据迁移策略

### 7.1 版本升级

- 使用数据库迁移脚本处理数据模型变更
- 保持向后兼容性
- 提供数据备份和恢复机制

### 7.2 数据清理

- 定期清理孤儿记录
- 清理过期的任务记录
- 清理无效的向量数据

## 8. 性能优化建议

### 8.1 索引优化

- 为常用查询字段创建索引
- 使用复合索引优化复杂查询
- 定期重建索引以提高性能

### 8.2 查询优化

- 使用分页查询避免一次性加载大量数据
- 使用投影查询只返回需要的字段
- 使用缓存减少重复查询

### 8.3 存储优化

- 使用压缩减少存储空间
- 定期清理无用数据
- 使用分区表提高查询性能

## 9. 安全考虑

### 9.1 数据加密

- 敏感数据使用加密存储
- 使用HTTPS传输数据
- 使用安全的哈希算法

### 9.2 访问控制

- 实现基于角色的访问控制
- 使用API密钥认证
- 记录访问日志

### 9.3 数据备份

- 定期备份数据
- 实现灾难恢复机制
- 测试备份恢复流程

## 10. 附录

### 10.1 枚举值

#### 文件类型（file_type）
- image：图像
- video：视频
- audio：音频

#### 处理状态（processing_status）
- pending：待处理
- processing：处理中
- completed：已完成
- failed：失败

#### 模态类型（modality）
- image：图像
- video：视频
- audio：音频
- text：文本
- face：人脸

#### 任务状态（status）
- pending：待执行
- running：运行中
- completed：已完成
- failed：失败
- cancelled：已取消
- paused：已暂停

#### 音频内容类型（content_type）
- speech：语音
- music：音乐
- noise：噪声
- silence：静音
- mixed：混合
- unknown：未知

#### 设备类型（device）
- cpu：CPU
- cuda：CUDA（GPU）

#### 模型精度（precision）
- float32：32位浮点数
- float16：16位浮点数
- int8：8位整数

### 10.2 常量定义

```python
# 向量维度
VECTOR_DIMENSIONS = {
    "image": 512,
    "video": 512,
    "audio": 512,
    "text": 768,
    "face": 512
}

# 最大文件大小
MAX_FILE_SIZE = 10 * 1024 * 1024 * 1024  # 10GB

# 最大切片时长
MAX_SEGMENT_DURATION = 5.0  # 5秒

# 时间戳精度
TIMESTAMP_PRECISION = 5.0  # ±5秒

# 默认批量大小
DEFAULT_BATCH_SIZE = 16

# 最大并发任务数
MAX_CONCURRENT_TASKS = 4
```

### 10.3 错误码

| 错误码 | 描述 |
|--------|------|
| 1001 | 文件不存在 |
| 1002 | 文件格式不支持 |
| 1003 | 文件大小超过限制 |
| 2001 | 向量维度不匹配 |
| 2002 | 向量检索失败 |
| 3001 | 任务创建失败 |
| 3002 | 任务执行失败 |
| 3003 | 任务超时 |
| 4001 | 模型加载失败 |
| 4002 | 模型推理失败 |
| 5001 | 数据库连接失败 |
| 5002 | 数据库查询失败 |
| 6001 | 硬件检测失败 |
| 6002 | 资源不足 |
