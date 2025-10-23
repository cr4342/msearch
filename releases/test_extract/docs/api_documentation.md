# MSearch API文档

## 1. API概述

### 1.1 基础信息

**API基础URL**: `http://localhost:8000/api/v1`

**认证方式**: 当前版本无需认证

**数据格式**: JSON

**字符编码**: UTF-8

### 1.2 技术架构

MSearch API基于以下技术栈构建：
- **后端框架**: FastAPI
- **AI推理引擎**: michaelfeil/infinity (集成CLIP、CLAP、Whisper等模型)
- **向量数据库**: Qdrant
- **多模态处理**: 支持文本、图像、视频、音频的向量化处理
- **时间定位机制**: 基于帧级时间戳的精确时间定位（±2秒精度）

### 1.3 通用响应格式

**成功响应**：
```json
{
  "success": true,
  "message": "操作成功",
  "data": {
    // 具体数据内容
  }
}
```

**错误响应**：
```json
{
  "success": false,
  "message": "错误信息",
  "error": "详细错误信息"
}
```

### 1.3 时间定位机制

MSearch系统实现了精确的时间定位机制，支持视频和音频内容的精确时间戳定位：

- **帧级时间戳计算**: 基于帧率的精确时间计算（±0.033s@30fps）
- **多模态时间同步**: 视觉、音频、语音统一时间基准
- **精确时间检索**: 支持±2秒精度保证的时间范围搜索
- **场景感知切片**: 避免在场景中间进行时间切分

在API响应中，时间相关信息通过以下字段表示：
- `start_time_ms`: 开始时间（毫秒）
- `end_time_ms`: 结束时间（毫秒）
- `frame_index`: 帧索引（视频内容）

### 1.4 HTTP状态码

| 状态码 | 说明 | 使用场景 |
|--------|------|---------|
| 200 | 成功 | 请求处理成功 |
| 400 | 请求错误 | 参数验证失败、格式错误 |
| 404 | 资源不存在 | 请求的资源未找到 |
| 500 | 服务器错误 | 内部处理异常 |
| 503 | 服务不可用 | 系统维护或过载 |

## 2. 搜索接口

### 2.1 智能搜索

**端点**: `POST /api/v1/search`

**描述**: 执行智能多模态搜索，系统会自动识别查询类型并动态调整权重

**请求参数**：
```json
{
  "query": "包含张三的会议照片",
  "limit": 10
}
```

**响应示例**：
```json
{
  "status": "success",
  "query": "包含张三的会议照片",
  "limit": 10,
  "results": [
    {
      "id": "point_1",
      "score": 0.95,
      "file_path": "/path/to/meeting.mp4",
      "file_type": "video",
      "start_time_ms": 10000,
      "end_time_ms": 15000,
      "metadata": {
        "duration": 120.5,
        "resolution": "1920x1080"
      }
    }
  ],
  "total": 1
}
```

### 2.2 文本搜索

**端点**: `POST /api/v1/search/text`

**描述**: 执行文本检索，支持跨模态检索

**请求参数**：
- `query`: 查询文本
- `limit`: 返回结果数量限制（默认20）

**响应示例**：
```json
{
  "success": true,
  "message": "文本检索完成",
  "data": {
    "query": "会议讨论",
    "results": [
      {
        "id": "point_1",
        "score": 0.87,
        "file_path": "/path/to/meeting.mp4",
        "file_type": "video",
        "start_time_ms": 25000,
        "end_time_ms": 30000,
        "metadata": {
          "file_id": "file_001",
          "vector_metadata": {
            "segment_type": "video"
          }
        }
      }
    ],
    "total": 1
  }
}
```

### 2.3 图像搜索

**端点**: `POST /api/v1/search/image`

**描述**: 通过上传图片进行相似图片/视频搜索

**请求格式**: `multipart/form-data`

**请求参数**：
- `file`: 图像文件
- `limit`: 返回结果数量限制（默认20）

**响应示例**：
```json
{
  "success": true,
  "message": "图像检索完成",
  "data": {
    "query_image": "search_image.jpg",
    "results": [
      {
        "id": "point_1",
        "score": 0.92,
        "file_path": "/path/to/similar_image.jpg",
        "file_type": "image",
        "start_time_ms": 0,
        "end_time_ms": 0,
        "metadata": {
          "segment_type": "image"
        }
      }
    ],
    "total": 1
  }
}
```

### 2.4 音频搜索

**端点**: `POST /api/v1/search/audio`

**描述**: 通过上传音频文件进行音频内容搜索

**请求格式**: `multipart/form-data`

**请求参数**：
- `file`: 音频文件
- `limit`: 返回结果数量限制（默认20）

**响应示例**：
```json
{
  "success": true,
  "message": "音频检索完成",
  "data": {
    "query_audio": "search_audio.mp3",
    "results": [
      {
        "id": "point_1",
        "score": 0.85,
        "file_path": "/path/to/similar_audio.mp3",
        "file_type": "audio_music",
        "segment_type": "audio_music",
        "start_time_ms": 30000,
        "end_time_ms": 40000,
        "transcribed_text": "",
        "metadata": {
          "segment_type": "audio_music"
        }
      }
    ],
    "total": 1
  }
}
```

### 2.5 视频搜索

**端点**: `POST /api/v1/search/video`

**描述**: 通过上传视频文件进行视频内容搜索

**请求格式**: `multipart/form-data`

**请求参数**：
- `file`: 视频文件
- `limit`: 返回结果数量限制（默认20）

**响应示例**：
```json
{
  "success": true,
  "message": "视频检索完成",
  "data": {
    "query_video": "search_video.mp4",
    "results": [
      {
        "id": "point_1",
        "score": 0.88,
        "file_path": "/path/to/similar_video.mp4",
        "file_type": "video",
        "start_time_ms": 15000,
        "end_time_ms": 20000,
        "frame_index": 0,
        "metadata": {
          "segment_type": "video"
        }
      }
    ],
    "total": 1
  }
}
```

### 2.6 多模态搜索

**端点**: `POST /api/v1/search/multimodal`

**描述**: 支持文本、图像、音频、视频混合查询

**请求格式**: `multipart/form-data`

**请求参数**：
- `query_text`: 查询文本（可选）
- `image_file`: 图像文件（可选）
- `audio_file`: 音频文件（可选）
- `video_file`: 视频文件（可选）
- `limit`: 返回结果数量限制（默认20）

**响应示例**：
```json
{
  "success": true,
  "message": "多模态检索完成",
  "data": {
    "query_text": "会议讨论",
    "query_image": null,
    "query_audio": null,
    "query_video": null,
    "results": [
      {
        "id": "point_1",
        "score": 0.91,
        "fused_score": 0.91,
        "modality_scores": {},
        "file_path": "/path/to/meeting.mp4",
        "file_type": "video",
        "start_time_ms": 25000,
        "end_time_ms": 30000,
        "metadata": {
          "file_id": "file_001",
          "vector_metadata": {
            "file_id": "file_001",
            "file_path": "/path/to/meeting.mp4",
            "segment_type": "video",
            "start_time_ms": 25000,
            "end_time_ms": 30000
          }
        }
      }
    ],
    "total": 1
  }
}
```

### 2.7 时间线搜索

**端点**: `POST /api/v1/search/timeline`

**描述**: 按时间范围搜索媒体文件，支持精确时间定位（±2秒精度）

**请求参数**：
```json
{
  "query": "会议",
  "time_range": {
    "start": "2024-01-01T00:00:00Z",
    "end": "2024-01-31T23:59:59Z",
    "start_time_ms": 25000,
    "end_time_ms": 30000
  },
  "file_types": ["video", "audio"],
  "limit": 20,
  "time_accurate": true
}
```

**请求参数说明**：
- `time_range.start`: 开始时间（ISO 8601格式）
- `time_range.end`: 结束时间（ISO 8601格式）
- `time_range.start_time_ms`: 媒体文件内开始时间（毫秒，可选）
- `time_range.end_time_ms`: 媒体文件内结束时间（毫秒，可选）
- `time_accurate`: 是否启用精确时间检索（默认true）

**响应示例**：
```json
{
  "success": true,
  "message": "时间线搜索完成",
  "data": {
    "query": "会议",
    "time_range": {
      "start": "2024-01-01T00:00:00Z",
      "end": "2024-01-31T23:59:59Z",
      "start_time_ms": 25000,
      "end_time_ms": 30000
    },
    "file_types": ["video", "audio"],
    "time_accurate": true,
    "results": [
      {
        "id": "point_1",
        "score": 0.89,
        "file_path": "/path/to/meeting.mp4",
        "file_type": "video",
        "created_at": "2024-01-15T10:00:00Z",
        "start_time_ms": 25000,
        "end_time_ms": 30000,
        "time_precision": "±2s",
        "metadata": {
          "file_id": "file_001",
          "file_path": "/path/to/meeting.mp4",
          "file_type": "video",
          "created_at": "2024-01-15T10:00:00Z",
          "vector_metadata": {
            "file_id": "file_001",
            "file_path": "/path/to/meeting.mp4",
            "file_type": "video",
            "created_at": "2024-01-15T10:00:00Z",
            "time_precision": "±2s"
          }
        }
      }
    ],
    "total": 1
  }
}
```

## 3. 人脸识别接口

### 3.1 添加人物到人脸库

**端点**: `POST /api/v1/face/persons`

**描述**: 添加新的人物到人脸库

**请求格式**: `multipart/form-data`

**请求参数**：
- `name`: 人物姓名
- `image_files`: 人物照片文件列表
- `aliases`: 人物别名（JSON数组字符串，可选）
- `description`: 人物描述（可选）

**响应示例**：
```json
{
  "success": true,
  "message": "人物 张三 添加成功",
  "data": {
    "person_id": 1
  }
}
```

### 3.2 获取所有人名列表

**端点**: `GET /api/v1/face/persons`

**描述**: 获取人脸库中的所有人物

**响应示例**：
```json
{
  "success": true,
  "message": "获取人名列表成功",
  "data": [
    {
      "id": 1,
      "name": "张三",
      "aliases": ["小张", "张总"],
      "description": "公司CEO"
    }
  ]
}
```

### 3.3 人脸搜索

**端点**: `POST /api/v1/face/search`

**描述**: 通过上传人脸图片进行人脸搜索

**请求格式**: `multipart/form-data`

**请求参数**：
- `image_file`: 人脸图片文件
- `limit`: 返回结果数量限制（默认10）

**响应示例**：
```json
{
  "success": true,
  "message": "人脸搜索完成",
  "data": {
    "query_image": "face.jpg",
    "matches": [
      {
        "person_id": 1,
        "person_name": "张三",
        "aliases": ["小张", "张总"],
        "similarity": 0.92,
        "confidence": 0.95
      }
    ]
  }
}
```

## 4. 文件处理接口

### 4.1 处理文件

**端点**: `POST /api/v1/files/process`

**描述**: 处理单个文件

**请求参数**：
```json
{
  "file_path": "/path/to/file.mp4",
  "file_id": 1
}
```

**响应示例**：
```json
{
  "success": true,
  "message": "文件处理完成",
  "data": {
    "status": "success",
    "file_id": "550e8400-e29b-41d4-a716-446655440000",
    "file_path": "/path/to/file.mp4",
    "file_type": "video",
    "processing_time": 12.5
  }
}
```

### 4.2 批量处理文件

**端点**: `POST /api/v1/files/batch-process`

**描述**: 批量处理文件

**请求参数**：
```json
{
  "file_list": [
    {
      "file_path": "/path/to/file1.mp4",
      "file_id": "1"
    },
    {
      "file_path": "/path/to/file2.jpg",
      "file_id": "2"
    }
  ]
}
```

**响应示例**：
```json
{
  "success": true,
  "message": "批量处理完成: 2/2 成功",
  "data": [
    {
      "status": "success",
      "file_id": "550e8400-e29b-41d4-a716-446655440000",
      "file_path": "/path/to/file1.mp4",
      "file_type": "video",
      "processing_time": 12.5
    },
    {
      "status": "success",
      "file_id": "550e8400-e29b-41d4-a716-446655440001",
      "file_path": "/path/to/file2.jpg",
      "file_type": "image",
      "processing_time": 2.3
    }
  ]
}
```

### 4.3 获取文件处理状态

**端点**: `GET /api/v1/files/process-status/{file_id}`

**描述**: 获取文件处理状态

**路径参数**：
- `file_id`: 文件ID

**响应示例**：
```json
{
  "success": true,
  "message": "状态获取成功",
  "data": {
    "file_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "completed",
    "progress": 100
  }
}
```

## 5. 配置管理接口

### 5.1 获取系统配置

**端点**: `GET /api/v1/config`

**描述**: 获取当前系统配置信息

**响应示例**：
```json
{
  "status": "success",
  "message": "系统配置获取成功",
  "data": {
    "hardware_mode": "cpu",
    "paths": {
      "watch_directories": ["/home/user/Pictures", "/home/user/Videos"],
      "sqlite_db_path": "./data/msearch.db",
      "log_file_path": "./data/logs/msearch.log"
    },
    "preprocessing": {},
    "system": {
      "log_level": "INFO",
      "data_dir": "./data",
      "temp_dir": "./temp",
      "max_workers": 4
    },
    "fastapi": {
      "host": "0.0.0.0",
      "port": 8000
    },
    "qdrant": {
      "host": "localhost",
      "port": 6333,
      "collections": {
        "visual_vectors": "visual_vectors",
        "audio_music_vectors": "audio_music_vectors",
        "audio_speech_vectors": "audio_speech_vectors"
      }
    }
  }
}
```

### 5.2 更新系统配置

**端点**: `PUT /api/v1/config`

**描述**: 更新系统配置信息

**请求参数**：
```json
{
  "system": {
    "log_level": "DEBUG"
  }
}
```

**响应示例**：
```json
{
  "status": "success",
  "message": "系统配置更新成功",
  "data": {
    // 更新后的完整配置
  }
}
```

## 6. 任务管理接口

### 6.1 启动任务

**端点**: `POST /api/v1/tasks/start`

**描述**: 启动任务

**请求参数**：
```json
{
  "task_type": "process_directory"
}
```

**响应示例**：
```json
{
  "message": "启动任务功能待实现",
  "task_type": "process_directory"
}
```

### 6.2 停止任务

**端点**: `POST /api/v1/tasks/stop`

**描述**: 停止任务

**请求参数**：
```json
{
  "task_type": "process_directory"
}
```

**响应示例**：
```json
{
  "message": "停止任务功能待实现",
  "task_type": "process_directory"
}
```

### 6.3 获取任务状态

**端点**: `GET /api/v1/tasks/status`

**描述**: 获取任务状态

**请求参数**：
```json
{
  "task_type": "process_directory"
}
```

**响应示例**：
```json
{
  "message": "获取任务状态功能待实现",
  "task_type": "process_directory"
}
```

### 6.4 重置系统

**端点**: `POST /api/v1/tasks/reset`

**描述**: 重置系统

**请求参数**：
```json
{
  "reset_type": "all"
}
```

**响应示例**：
```json
{
  "message": "重置系统功能待实现",
  "reset_type": "all"
}
```

## 7. 系统状态接口

### 7.1 获取系统状态

**端点**: `GET /api/v1/status`

**描述**: 获取系统状态

**响应示例**：
```json
{
  "message": "获取系统状态功能待实现"
}
```

### 7.2 健康检查

**端点**: `GET /api/v1/status/health`

**描述**: 健康检查

**响应示例**：
```json
{
  "status": "healthy",
  "message": "系统运行正常"
}
```

### 7.3 获取系统指标

**端点**: `GET /api/v1/status/metrics`

**描述**: 获取系统指标

**响应示例**：
```json
{
  "message": "获取系统指标功能待实现"
}
```

### 7.4 获取系统版本

**端点**: `GET /api/v1/status/version`

**描述**: 获取系统版本

**响应示例**：
```json
{
  "version": "0.1.0",
  "message": "版本信息获取成功"
}
```

## 8. 系统管理接口

### 8.1 健康检查

**端点**: `GET /health`

**描述**: 系统健康检查端点

**响应示例**：
```json
{
  "success": true,
  "message": "服务运行正常",
  "data": {
    "status": "healthy",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

### 8.2 获取系统版本

**端点**: `GET /api/v1/system/version`

**描述**: 获取系统版本信息

**响应示例**：
```json
{
  "success": true,
  "message": "版本信息获取成功",
  "data": {
    "version": "v0.1",
    "environment": "development"
  }
}
```

### 8.3 获取系统状态

**端点**: `GET /api/v1/system/status`

**描述**: 获取系统状态信息

**响应示例**：
```json
{
  "success": true,
  "message": "系统状态获取成功",
  "data": {
    "cpu_usage": "25.0%",
    "memory_usage": "68.0%",
    "memory_available": "8.00 GB",
    "disk_usage": "45.00%",
    "disk_available": "100.00 GB",
    "uptime": "3600 seconds"
  }
}
```

### 8.4 获取数据库状态

**端点**: `GET /api/v1/system/db-status`

**描述**: 获取数据库连接状态

**响应示例**：
```json
{
  "success": true,
  "message": "数据库状态检查完成",
  "data": {
    "sqlite_connected": true,
    "qdrant_connected": true,
    "sqlite_version": "3.35.0",
    "qdrant_version": "1.1.0"
  }
}
```

### 8.5 系统重置

**端点**: `POST /api/v1/system/reset`

**描述**: 系统重置

**请求参数**：
```json
{
  "reset_type": "all"
}
```

**响应示例**：
```json
{
  "success": true,
  "message": "系统重置成功: all",
  "data": {
    "reset_type": "all"
  }
}
```

## 9. 文件监控接口

### 9.1 获取文件监控状态

**端点**: `GET /api/v1/monitoring/status`

**描述**: 获取文件监控状态

**响应示例**：
```json
{
  "success": true,
  "message": "监控状态获取成功",
  "data": {
    // 监控状态信息
  }
}
```

### 9.2 启动文件监控

**端点**: `POST /api/v1/monitoring/start`

**描述**: 启动文件监控服务

**响应示例**：
```json
{
  "success": true,
  "message": "文件监控已启动",
  "data": {
    // 监控状态信息
  }
}
```

### 9.3 停止文件监控

**端点**: `POST /api/v1/monitoring/stop`

**描述**: 停止文件监控服务

**响应示例**：
```json
{
  "success": true,
  "message": "文件监控已停止",
  "data": {
    // 监控状态信息
  }
}
```

## 10. 错误码参考

### 10.1 通用错误码

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| INVALID_PARAMETER | 400 | 请求参数无效 |
| MISSING_PARAMETER | 400 | 缺少必需参数 |
| RESOURCE_NOT_FOUND | 404 | 资源不存在 |
| INTERNAL_ERROR | 500 | 内部服务器错误 |
| SERVICE_UNAVAILABLE | 503 | 服务不可用 |

### 10.2 业务错误码

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| FILE_NOT_FOUND | 404 | 文件不存在 |
| FILE_PROCESSING_FAILED | 500 | 文件处理失败 |
| UNSUPPORTED_FILE_TYPE | 400 | 不支持的文件类型 |
| SEARCH_TIMEOUT | 408 | 搜索超时 |
| FACE_DETECTION_FAILED | 500 | 人脸检测失败 |
| DUPLICATE_PERSON | 409 | 人物已存在 |

## 11. SDK使用示例

### 11.1 Python SDK示例

```python
import requests
import json

class MSearchClient:
    def __init__(self, base_url="http://localhost:8000/api/v1"):
        self.base_url = base_url
    
    def search(self, query, limit=10):
        """执行智能搜索"""
        url = f"{self.base_url}/search"
        data = {
            "query": query,
            "limit": limit
        }
        response = requests.post(url, json=data)
        return response.json()
    
    def upload_image_search(self, image_path, limit=10):
        """上传图片搜索"""
        url = f"{self.base_url}/search/image"
        with open(image_path, 'rb') as f:
            files = {'file': f}
            data = {'limit': limit}
            response = requests.post(url, files=files, data=data)
        return response.json()
    
    def add_person(self, name, image_paths, aliases=None):
        """添加人物到人脸库"""
        url = f"{self.base_url}/face/persons"
        files = [('image_files', open(path, 'rb')) for path in image_paths]
        data = {'name': name}
        if aliases:
            data['aliases'] = json.dumps(aliases)
        
        try:
            response = requests.post(url, files=files, data=data)
            return response.json()
        finally:
            for _, f in files:
                f.close()

# 使用示例
client = MSearchClient()

# 智能搜索
result = client.search("包含张三的会议照片")
print(f"找到 {len(result['results'])} 个结果")

# 图片搜索
result = client.upload_image_search("query_image.jpg")

# 添加人物
result = client.add_person("张三", ["face1.jpg", "face2.jpg"], ["小张", "张总"])
```

### 11.2 JavaScript SDK示例

```javascript
class MSearchClient {
    constructor(baseUrl = 'http://localhost:8000/api/v1') {
        this.baseUrl = baseUrl;
    }
    
    async search(query, limit = 10) {
        const response = await fetch(`${this.baseUrl}/search`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query: query,
                limit: limit
            })
        });
        return await response.json();
    }
    
    async uploadImageSearch(imageFile, limit = 10) {
        const formData = new FormData();
        formData.append('file', imageFile);
        formData.append('limit', limit);
        
        const response = await fetch(`${this.baseUrl}/search/image`, {
            method: 'POST',
            body: formData
        });
        return await response.json();
    }
    
    async getSystemStatus() {
        const response = await fetch(`${this.baseUrl}/status`);
        return await response.json();
    }
}

// 使用示例
const client = new MSearchClient();

// 执行搜索
client.search('会议场景')
    .then(result => {
        console.log(`找到 ${result.results.length} 个结果`);
    });
```