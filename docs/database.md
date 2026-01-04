# 数据库设计文档

本文档详细描述 msearch 多模态检索系统的数据库设计，包括 Schema 定义、表结构、索引设计和使用示例。

## 1. 概述

系统使用 SQLite 作为元数据库，用于存储文件元数据和任务状态。数据库设计遵循以下原则：
- **类型安全**: 使用 Pydantic Schema 提供类型安全和数据验证
- **数据完整性**: 使用约束确保数据一致性
- **查询性能**: 使用索引优化查询性能
- **可扩展性**: 设计支持未来功能扩展

## 2. DatabaseManager 组件

### 2.1 职责

DatabaseManager 专注于 SQLite 数据库的操作和管理，为任务管理器提供元数据存储支持。

### 2.2 核心功能

1. **元数据存储**: 存储文件元数据（UUID、hash、路径等）
2. **任务状态跟踪**: 记录任务处理状态和进度信息
3. **批量操作**: 支持批量插入、更新、查询元数据
4. **事务管理**: 确保数据一致性
5. **健康检查**: 提供数据库连接状态检查

## 3. Schema 设计

使用 Pydantic Schema 规范数据库操作，提供类型安全和数据验证。

### 3.1 FileMetadata Schema

文件元数据模型，存储所有文件的元数据，包括原始文件和预处理生成的派生文件。

```python
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
from enum import Enum

class FileType(str, Enum):
    VIDEO = "video"
    AUDIO = "audio"
    IMAGE = "image"
    DERIVED = "derived"

class ModalityType(str, Enum):
    VIDEO = "video"
    AUDIO = "audio"
    IMAGE = "image"
    TEXT = "text"

class DerivedType(str, Enum):
    SEPARATED_AUDIO = "separated_audio"
    VIDEO_SEGMENT = "video_segment"
    THUMBNAIL = "thumbnail"

class FileMetadata(BaseModel):
    file_uuid: str = Field(..., description="文件唯一标识")
    file_path: str = Field(..., description="文件完整路径")
    file_name: str = Field(..., description="文件名")
    file_type: FileType = Field(..., description="文件类型")
    modality: ModalityType = Field(..., description="模态类型")
    file_hash: str = Field(..., description="文件内容哈希（SHA256）")
    file_size: int = Field(..., description="文件大小（字节）")
    source_file_uuid: Optional[str] = Field(None, description="源文件UUID（派生文件关联到原始文件）")
    derived_type: Optional[DerivedType] = Field(None, description="派生类型")
    total_duration: Optional[float] = Field(None, description="视频/音频总时长（秒）")
    frame_rate: Optional[float] = Field(None, description="视频帧率")
    resolution: Optional[str] = Field(None, description="视频/图像分辨率")
    width: Optional[int] = Field(None, description="图像宽度")
    height: Optional[int] = Field(None, description="图像高度")
    sample_rate: Optional[int] = Field(None, description="音频采样率")
    channels: Optional[int] = Field(None, description="音频声道数")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="记录创建时间")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="记录更新时间")
    
    @validator('file_size')
    def validate_file_size(cls, v):
        if v < 0:
            raise ValueError('file_size must be non-negative')
        return v
    
    @validator('total_duration', 'frame_rate')
    def validate_positive_float(cls, v):
        if v is not None and v < 0:
            raise ValueError('value must be non-negative')
        return v
    
    @validator('width', 'height', 'sample_rate', 'channels')
    def validate_positive_int(cls, v):
        if v is not None and v < 0:
            raise ValueError('value must be non-negative')
        return v
    
    @validator('derived_type')
    def validate_derived_type(cls, v, values):
        if v is not None and values.get('file_type') != FileType.DERIVED:
            raise ValueError('derived_type can only be set for derived files')
        return v
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
```

### 3.2 TaskProgress Schema

任务进度跟踪模型，记录任务处理状态和进度信息。

```python
from typing import Optional
from datetime import datetime

class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskProgress(BaseModel):
    task_id: str = Field(..., description="任务唯一标识")
    file_uuid: str = Field(..., description="关联的文件UUID")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="任务状态")
    progress: int = Field(default=0, ge=0, le=100, description="任务进度（0-100）")
    error_message: Optional[str] = Field(None, description="错误消息")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="任务创建时间")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="任务更新时间")
    retry_count: int = Field(default=0, ge=0, description="重试次数")
    
    @validator('progress')
    def validate_progress(cls, v):
        if v < 0 or v > 100:
            raise ValueError('progress must be between 0 and 100')
        return v
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
```

### 3.3 VideoSegment Schema

视频切片模型，存储视频场景检测切片的元数据。

```python
from typing import Optional
from datetime import datetime

class VideoSegment(BaseModel):
    segment_id: str = Field(..., description="切片唯一标识")
    file_uuid: str = Field(..., description="原始视频唯一标识")
    segment_index: int = Field(..., ge=0, description="按原始视频时序的片段序号（从0开始）")
    start_time: float = Field(..., ge=0, description="在原始视频中的起始时间(秒)")
    end_time: float = Field(..., ge=0, description="在原始视频中的结束时间(秒)")
    duration: float = Field(..., ge=0, description="片段时长(秒)")
    scene_boundary: bool = Field(default=False, description="是否为场景边界切片")
    
    @validator('end_time')
    def validate_end_time(cls, v, values):
        if 'start_time' in values and v < values['start_time']:
            raise ValueError('end_time must be greater than or equal to start_time')
        return v
    
    @validator('duration')
    def validate_duration(cls, v, values):
        if 'start_time' in values and 'end_time' in values:
            expected_duration = values['end_time'] - values['start_time']
            if abs(v - expected_duration) > 0.01:
                raise ValueError(f'duration must equal end_time - start_time (expected {expected_duration})')
        return v
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
```

### 3.4 VideoVectorPayload Schema

视频向量载荷模型，存储向量数据库中的元数据。

```python
from typing import Optional

class VideoVectorPayload(BaseModel):
    file_uuid: str = Field(..., description="原始视频唯一标识")
    segment_id: str = Field(..., description="切片唯一标识")
    segment_center_timestamp: float = Field(..., ge=0, description="片段中心时间戳(秒，CLIP4Clip预测)")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
```

## 4. DatabaseManager 接口

```python
from typing import List, Dict, Optional

class DatabaseManager:
    # 元数据管理（使用Schema）
    async def insert_file_metadata(self, metadata: FileMetadata) -> str
    async def get_file_metadata(self, file_uuid: str) -> Optional[FileMetadata]
    async def update_file_metadata(self, file_uuid: str, metadata: FileMetadata) -> None
    async def get_file_by_path(self, file_path: str) -> Optional[FileMetadata]
    
    # 批量操作（使用Schema）
    async def batch_insert_files(self, files: List[FileMetadata]) -> List[str]
    async def batch_update_files(self, file_uuids: List[str], metadata: FileMetadata) -> None
    
    # 视频切片管理（使用Schema）
    async def insert_video_segment(self, segment: VideoSegment) -> str
    async def get_video_segment(self, segment_id: str) -> Optional[VideoSegment]
    async def get_video_segments(self, file_uuid: str) -> List[VideoSegment]
    async def batch_insert_video_segments(self, segments: List[VideoSegment]) -> List[str]
    
    # 任务状态跟踪（使用Schema）
    async def update_task_progress(self, task_id: str, progress: TaskProgress) -> None
    async def get_task_status(self, task_id: str) -> Optional[TaskProgress]
    
    # 健康检查
    async def health_check(self) -> Dict
```

## 5. 数据库表设计

### 5.1 files 表

存储所有文件的元数据，包括原始文件和预处理生成的派生文件。

```sql
CREATE TABLE files (
    file_uuid TEXT PRIMARY KEY,
    file_path TEXT NOT NULL UNIQUE,
    file_name TEXT NOT NULL,
    file_type TEXT NOT NULL CHECK(file_type IN ('video', 'audio', 'image', 'derived')),
    modality TEXT NOT NULL CHECK(modality IN ('video', 'audio', 'image', 'text')),
    file_hash TEXT NOT NULL,
    file_size INTEGER NOT NULL CHECK(file_size >= 0),
    source_file_uuid TEXT,
    derived_type TEXT CHECK(derived_type IN ('separated_audio', 'video_segment', 'thumbnail')),
    total_duration REAL CHECK(total_duration >= 0),
    frame_rate REAL CHECK(frame_rate >= 0),
    resolution TEXT,
    width INTEGER CHECK(width >= 0),
    height INTEGER CHECK(height >= 0),
    sample_rate INTEGER CHECK(sample_rate >= 0),
    channels INTEGER CHECK(channels >= 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_file_uuid) REFERENCES files(file_uuid)
);
```

#### 字段说明

| 字段名 | 类型 | 说明 | 示例值 |
|-------|------|------|--------|
| file_uuid | UUID | 文件唯一标识（主键） | "video-abc123" |
| file_path | String | 文件完整路径 | "/home/user/videos/interview.mp4" |
| file_name | String | 文件名 | "interview.mp4" |
| file_type | FileType | 文件类型（video/audio/image/derived） | "video" |
| modality | ModalityType | 模态类型（video/audio/image/text） | "video" |
| file_hash | String | 文件内容哈希（SHA256） | "a1b2c3d4..." |
| file_size | Integer | 文件大小（字节） | 104857600 |
| source_file_uuid | UUID | **源文件UUID（派生文件关联到原始文件）** | "video-abc123" 或 NULL |
| derived_type | DerivedType | 派生类型（separated_audio/video_segment/thumbnail） | "separated_audio" 或 NULL |
| total_duration | Float | 视频/音频总时长（秒） | 360.0 |
| frame_rate | Float | 视频帧率 | 30.0 |
| resolution | String | 视频/图像分辨率 | "1920x1080" |
| width | Integer | 图像宽度 | 1920 |
| height | Integer | 图像高度 | 1080 |
| sample_rate | Integer | 音频采样率 | 16000 |
| channels | Integer | 音频声道数 | 1 |
| created_at | Timestamp | 记录创建时间 | 2024-01-01 10:00:00 |
| updated_at | Timestamp | 记录更新时间 | 2024-01-01 10:05:00 |

#### 重要说明

- **原始文件**: `source_file_uuid` 为 NULL，`derived_type` 为 NULL
- **派生文件**: `source_file_uuid` 指向原始文件的 `file_uuid`，`derived_type` 标识派生类型
- **文件类型**: `file_type` 区分原始文件（video/audio/image）和派生文件（derived）
- **关联查询**: 通过 `source_file_uuid` 可以从派生文件追溯到原始文件

#### 派生类型说明

| derived_type | 说明 | 示例 |
|-------------|------|------|
| separated_audio | 从视频中分离的音频 | video.mp4 → audio.wav |
| video_segment | 视频场景检测切片 | video.mp4 → segment_001.mp4 |
| thumbnail | 生成的缩略图 | video.mp4 → thumb.jpg |

### 5.2 video_segments 表

存储视频场景检测切片的元数据。

```sql
CREATE TABLE video_segments (
    segment_id TEXT PRIMARY KEY,
    file_uuid TEXT NOT NULL,
    segment_index INTEGER NOT NULL CHECK(segment_index >= 0),
    start_time REAL NOT NULL CHECK(start_time >= 0),
    end_time REAL NOT NULL CHECK(end_time >= 0),
    duration REAL NOT NULL CHECK(duration >= 0),
    scene_boundary BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (file_uuid) REFERENCES files(file_uuid),
    CHECK(end_time >= start_time),
    CHECK(duration = end_time - start_time)
);
```

#### 字段说明

| 字段名 | 类型 | 说明 | 示例值 |
|-------|------|------|--------|
| segment_id | UUID | 切片唯一标识 | "seg-001" |
| file_uuid | UUID | 原始视频唯一标识 | "video-abc123" |
| segment_index | Integer | 按原始视频时序的片段序号（从0开始） | 0, 1, 2... |
| start_time | Float | 在原始视频中的起始时间(秒) | 0.0, 120.5, 245.3 |
| end_time | Float | 在原始视频中的结束时间(秒) | 120.5, 245.3, 360.0 |
| duration | Float | 片段时长(秒) = end_time - start_time | 120.5, 124.8, 114.7 |
| scene_boundary | Boolean | 是否为场景边界切片 | true/false |

#### 重要约束

1. **切片时间连续性**: 相邻切片的时间必须连续，即前一切片的结束时间必须等于后一切片的开始时间
2. **切片时长准确性**: 切片时长必须等于结束时间减去开始时间的差值
3. **切片序号完整性**: 切片序号必须按时序连续递增，从0开始编号

### 5.3 task_progress 表

存储任务处理状态和进度信息。

```sql
CREATE TABLE task_progress (
    task_id TEXT PRIMARY KEY,
    file_uuid TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('pending', 'processing', 'completed', 'failed', 'cancelled')),
    progress INTEGER DEFAULT 0 CHECK(progress >= 0 AND progress <= 100),
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    retry_count INTEGER DEFAULT 0 CHECK(retry_count >= 0),
    FOREIGN KEY (file_uuid) REFERENCES files(file_uuid)
);
```

## 6. 索引设计

为优化查询性能，创建以下索引：

```sql
-- files 表索引
CREATE INDEX idx_files_path ON files(file_path);
CREATE INDEX idx_files_type ON files(file_type);
CREATE INDEX idx_files_source_uuid ON files(source_file_uuid);

-- video_segments 表索引
CREATE INDEX idx_video_segments_file_uuid ON video_segments(file_uuid);
CREATE INDEX idx_video_segments_segment_index ON video_segments(segment_index);

-- task_progress 表索引
CREATE INDEX idx_task_progress_status ON task_progress(status);
CREATE INDEX idx_task_progress_created_at ON task_progress(created_at);
```

## 7. Schema 使用示例

### 7.1 文件元数据操作

```python
# 创建文件元数据
file_metadata = FileMetadata(
    file_uuid="video-abc123",
    file_path="/home/user/videos/interview.mp4",
    file_name="interview.mp4",
    file_type=FileType.VIDEO,
    modality=ModalityType.VIDEO,
    file_hash="a1b2c3d4...",
    file_size=104857600,
    total_duration=360.0,
    frame_rate=30.0,
    resolution="1920x1080",
    width=1920,
    height=1080
)

# 插入数据库
file_uuid = await database_manager.insert_file_metadata(file_metadata)

# 查询文件元数据
metadata = await database_manager.get_file_metadata(file_uuid)
if metadata:
    print(f"File: {metadata.file_name}, Size: {metadata.file_size}")

# 批量插入文件
files = [
    FileMetadata(file_uuid="video-001", file_path="/path/to/video1.mp4", ...),
    FileMetadata(file_uuid="video-002", file_path="/path/to/video2.mp4", ...),
]
file_uuids = await database_manager.batch_insert_files(files)
```

### 7.2 视频切片操作

```python
# 创建视频切片
segment = VideoSegment(
    segment_id="seg-001",
    file_uuid="video-abc123",
    segment_index=0,
    start_time=0.0,
    end_time=120.5,
    duration=120.5,
    scene_boundary=True
)

# 插入数据库
segment_id = await database_manager.insert_video_segment(segment)

# 批量插入切片
segments = [
    VideoSegment(segment_id="seg-001", file_uuid="video-abc123", segment_index=0, start_time=0.0, end_time=120.5, duration=120.5, scene_boundary=True),
    VideoSegment(segment_id="seg-002", file_uuid="video-abc123", segment_index=1, start_time=120.5, end_time=245.3, duration=124.8, scene_boundary=False),
    VideoSegment(segment_id="seg-003", file_uuid="video-abc123", segment_index=2, start_time=245.3, end_time=360.0, duration=114.7, scene_boundary=True)
]
segment_ids = await database_manager.batch_insert_video_segments(segments)

# 查询视频的所有切片
segments = await database_manager.get_video_segments("video-abc123")
```

### 7.3 任务进度操作

```python
# 创建任务进度
task_progress = TaskProgress(
    task_id="task-001",
    file_uuid="video-abc123",
    status=TaskStatus.PROCESSING,
    progress=50
)

# 更新任务进度
await database_manager.update_task_progress("task-001", task_progress)

# 查询任务状态
status = await database_manager.get_task_status("task-001")
if status:
    print(f"Task {status.task_id}: {status.status} ({status.progress}%)")
```

### 7.4 向量存储操作

```python
# 创建向量Payload
payload = VideoVectorPayload(
    file_uuid="video-abc123",
    segment_id="seg-001",
    segment_center_timestamp=60.25
)

# 存储向量时使用Payload
metadata = payload.dict()
vector_store.insert_vectors(collection="video_vectors", vectors=[vector], ids=["vec-001"], metadata=[metadata])
```

## 8. 设计说明

### 8.1 Schema 优势

使用 Pydantic Schema 提供以下优势：
- **类型安全**: 编译时类型检查，减少运行时错误
- **数据验证**: 自动验证数据格式和约束
- **自动文档生成**: 自动生成 API 文档
- **IDE 支持**: 提供代码补全和类型提示

### 8.2 任务队列管理

- **任务队列管理**由 persist-queue 负责，提供线程安全的磁盘持久化队列
- **DatabaseManager** 只负责元数据存储和任务状态跟踪，不负责任务队列管理
- persist-queue 自动处理任务队列的存储和加载，无需手动管理

### 8.3 数据完整性

- 使用 CHECK 约束确保数据有效性
- 使用 FOREIGN KEY 约束维护关系完整性
- 使用 UNIQUE 约束防止重复数据

### 8.4 查询性能

- 为常用查询字段创建索引
- 批量操作减少数据库访问次数
- 使用事务确保数据一致性

## 9. 扩展性

数据库设计支持以下扩展：
- 添加新的文件类型和派生类型
- 添加新的任务状态
- 添加新的元数据字段
- 添加新的索引优化查询性能
