# MSearch API 文档

## 概述

本文档详细描述了 MSearch 多模态搜索系统的 RESTful API 接口。

**API 基础信息**：
- **基础URL**: `http://localhost:8000/api/v1`
- **协议**: HTTP/HTTPS
- **数据格式**: JSON
- **字符编码**: UTF-8
- **API版本**: v1

## 认证方式

### API密钥认证

在请求头中添加 API 密钥：

```http
Authorization: Bearer YOUR_API_KEY
```

### 获取API密钥

```bash
curl -X POST http://localhost:8000/api/v1/auth/api-key \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

**响应示例**：

```json
{
  "success": true,
  "data": {
    "api_key": "sk-1234567890abcdef",
    "expires_at": "2025-12-31T23:59:59Z"
  }
}
```

## 通用响应格式

所有API响应遵循统一格式：

```json
{
  "success": true,
  "data": {},
  "message": "操作成功",
  "error": null,
  "timestamp": 1704067200.0
}
```

**字段说明**：
- `success`: 操作是否成功（布尔值）
- `data`: 返回的数据（成功时）
- `message`: 操作消息（字符串）
- `error`: 错误信息（失败时）
- `timestamp`: 响应时间戳（Unix时间戳）

## 错误码

| 错误码 | 说明 | HTTP状态码 |
|--------|------|-----------|
| 1000 | 成功 | 200 |
| 1001 | 参数错误 | 400 |
| 1002 | 认证失败 | 401 |
| 1003 | 权限不足 | 403 |
| 1004 | 资源不存在 | 404 |
| 1005 | 服务器错误 | 500 |
| 1006 | 任务不存在 | 404 |
| 1007 | 文件不存在 | 404 |
| 1008 | 数据库错误 | 500 |
| 1009 | 向量化失败 | 500 |
| 1010 | 检索失败 | 500 |

**错误响应示例**：

```json
{
  "success": false,
  "data": null,
  "message": "参数错误",
  "error": {
    "code": 1001,
    "message": "参数错误",
    "details": "缺少必需参数: query"
  },
  "timestamp": 1704067200.0
}
```

## API端点

### 1. 搜索相关

#### 1.1 多模态搜索

搜索多媒体内容（文本、图像、视频、音频）。

**请求**：

```http
POST /api/v1/search/multimodal
```

**请求参数**：

```json
{
  "query": "搜索关键词",
  "modality": "all",
  "limit": 20,
  "offset": 0,
  "filters": {
    "file_type": ["image", "video"],
    "date_range": {
      "start": "2024-01-01",
      "end": "2024-12-31"
    }
  }
}
```

**参数说明**：
- `query`: 搜索查询（字符串，必需）
- `modality`: 模态类型（字符串，可选，默认"all"）
  - `all`: 所有模态
  - `image`: 仅图像
  - `video`: 仅视频
  - `audio`: 仅音频
  - `text`: 仅文本
- `limit`: 返回结果数量（整数，可选，默认20，最大100）
- `offset`: 偏移量（整数，可选，默认0）
- `filters`: 过滤条件（对象，可选）
  - `file_type`: 文件类型列表（数组）
  - `date_range`: 日期范围（对象）

**响应示例**：

```json
{
  "success": true,
  "data": {
    "results": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "file_path": "/path/to/file.mp4",
        "file_name": "file.mp4",
        "file_type": "video",
        "file_size": 1024000,
        "modality": "video",
        "score": 0.95,
        "metadata": {
          "duration": 120.5,
          "resolution": "1920x1080",
          "frame_rate": 30
        },
        "segments": [
          {
            "segment_id": "seg_001",
            "start_time": 10.5,
            "end_time": 15.5,
            "score": 0.95
          }
        ]
      }
    ],
    "total": 100,
    "limit": 20,
    "offset": 0
  },
  "message": "搜索成功",
  "error": null,
  "timestamp": 1704067200.0
}
```

#### 1.2 图像搜索

使用图像进行相似度搜索。

**请求**：

```http
POST /api/v1/search/image
```

**请求参数**：

```json
{
  "image": "base64_encoded_image_data",
  "limit": 20,
  "offset": 0
}
```

**参数说明**：
- `image`: 图像数据（Base64编码字符串，必需）
- `limit`: 返回结果数量（整数，可选，默认20）
- `offset`: 偏移量（整数，可选，默认0）

**响应示例**：

```json
{
  "success": true,
  "data": {
    "results": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "file_path": "/path/to/image.jpg",
        "file_name": "image.jpg",
        "file_type": "image",
        "file_size": 512000,
        "modality": "image",
        "score": 0.92,
        "metadata": {
          "width": 1920,
          "height": 1080,
          "format": "JPEG"
        }
      }
    ],
    "total": 50,
    "limit": 20,
    "offset": 0
  },
  "message": "图像搜索成功",
  "error": null,
  "timestamp": 1704067200.0
}
```

#### 1.3 音频搜索

使用音频进行相似度搜索。

**请求**：

```http
POST /api/v1/search/audio
```

**请求参数**：

```json
{
  "audio": "base64_encoded_audio_data",
  "limit": 20,
  "offset": 0
}
```

**参数说明**：
- `audio`: 音频数据（Base64编码字符串，必需）
- `limit`: 返回结果数量（整数，可选，默认20）
- `offset`: 偏移量（整数，可选，默认0）

**响应示例**：

```json
{
  "success": true,
  "data": {
    "results": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "file_path": "/path/to/audio.mp3",
        "file_name": "audio.mp3",
        "file_type": "audio",
        "file_size": 256000,
        "modality": "audio",
        "score": 0.88,
        "metadata": {
          "duration": 180.5,
          "format": "MP3",
          "sample_rate": 44100
        }
      }
    ],
    "total": 30,
    "limit": 20,
    "offset": 0
  },
  "message": "音频搜索成功",
  "error": null,
  "timestamp": 1704067200.0
}
```

### 2. 文件管理

#### 2.1 添加文件

添加文件到索引。

**请求**：

```http
POST /api/v1/files/add
```

**请求参数**：

```json
{
  "file_paths": [
    "/path/to/file1.mp4",
    "/path/to/file2.jpg"
  ],
  "priority": 5,
  "background": false
}
```

**参数说明**：
- `file_paths`: 文件路径列表（数组，必需）
- `priority`: 任务优先级（整数，可选，默认5，范围0-10）
- `background`: 是否后台处理（布尔值，可选，默认false）

**响应示例**：

```json
{
  "success": true,
  "data": {
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "pending",
    "files_added": 2,
    "files": [
      {
        "file_path": "/path/to/file1.mp4",
        "file_id": "550e8400-e29b-41d4-a716-446655440001",
        "status": "pending"
      },
      {
        "file_path": "/path/to/file2.jpg",
        "file_id": "550e8400-e29b-41d4-a716-446655440002",
        "status": "pending"
      }
    ]
  },
  "message": "文件添加成功",
  "error": null,
  "timestamp": 1704067200.0
}
```

#### 2.2 删除文件

从索引中删除文件。

**请求**：

```http
DELETE /api/v1/files/{file_id}
```

**路径参数**：
- `file_id`: 文件ID（字符串，必需）

**响应示例**：

```json
{
  "success": true,
  "data": {
    "file_id": "550e8400-e29b-41d4-a716-446655440000",
    "deleted": true
  },
  "message": "文件删除成功",
  "error": null,
  "timestamp": 1704067200.0
}
```

#### 2.3 获取文件信息

获取文件的详细信息。

**请求**：

```http
GET /api/v1/files/{file_id}
```

**路径参数**：
- `file_id`: 文件ID（字符串，必需）

**响应示例**：

```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "file_path": "/path/to/file.mp4",
    "file_name": "file.mp4",
    "file_type": "video",
    "file_size": 1024000,
    "file_hash": "a1b2c3d4e5f6...",
    "created_at": 1704067200.0,
    "updated_at": 1704067200.0,
    "processed_at": 1704067300.0,
    "processing_status": "completed",
    "metadata": {
      "duration": 120.5,
      "resolution": "1920x1080",
      "frame_rate": 30,
      "codec": "h264"
    }
  },
  "message": "获取文件信息成功",
  "error": null,
  "timestamp": 1704067200.0
}
```

#### 2.4 列出文件

列出所有文件。

**请求**：

```http
GET /api/v1/files
```

**查询参数**：
- `status`: 处理状态（字符串，可选）
- `file_type`: 文件类型（字符串，可选）
- `limit`: 返回结果数量（整数，可选，默认20）
- `offset`: 偏移量（整数，可选，默认0）

**响应示例**：

```json
{
  "success": true,
  "data": {
    "files": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "file_path": "/path/to/file.mp4",
        "file_name": "file.mp4",
        "file_type": "video",
        "file_size": 1024000,
        "processing_status": "completed",
        "created_at": 1704067200.0
      }
    ],
    "total": 100,
    "limit": 20,
    "offset": 0
  },
  "message": "获取文件列表成功",
  "error": null,
  "timestamp": 1704067200.0
}
```

### 3. 任务管理

#### 3.1 获取任务信息

获取任务的详细信息。

**请求**：

```http
GET /api/v1/tasks/{task_id}
```

**路径参数**：
- `task_id`: 任务ID（字符串，必需）

**响应示例**：

```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "task_type": "file_embed",
    "task_data": {
      "file_id": "550e8400-e29b-41d4-a716-446655440001"
    },
    "priority": 5,
    "status": "completed",
    "created_at": 1704067200.0,
    "updated_at": 1704067300.0,
    "started_at": 1704067205.0,
    "completed_at": 1704067300.0,
    "retry_count": 0,
    "max_retries": 3,
    "result": {
      "success": true,
      "vector_id": "vec_001"
    },
    "error": null,
    "progress": 1.0
  },
  "message": "获取任务信息成功",
  "error": null,
  "timestamp": 1704067200.0
}
```

#### 3.2 取消任务

取消正在执行的任务。

**请求**：

```http
POST /api/v1/tasks/{task_id}/cancel
```

**路径参数**：
- `task_id`: 任务ID（字符串，必需）

**响应示例**：

```json
{
  "success": true,
  "data": {
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "cancelled": true
  },
  "message": "任务取消成功",
  "error": null,
  "timestamp": 1704067200.0
}
```

#### 3.3 暂停任务

暂停正在执行的任务。

**请求**：

```http
POST /api/v1/tasks/{task_id}/pause
```

**路径参数**：
- `task_id`: 任务ID（字符串，必需）

**响应示例**：

```json
{
  "success": true,
  "data": {
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "paused": true
  },
  "message": "任务暂停成功",
  "error": null,
  "timestamp": 1704067200.0
}
```

#### 3.4 恢复任务

恢复已暂停的任务。

**请求**：

```http
POST /api/v1/tasks/{task_id}/resume
```

**路径参数**：
- `task_id`: 任务ID（字符串，必需）

**响应示例**：

```json
{
  "success": true,
  "data": {
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "resumed": true
  },
  "message": "任务恢复成功",
  "error": null,
  "timestamp": 1704067200.0
}
```

#### 3.5 列出任务

列出所有任务。

**请求**：

```http
GET /api/v1/tasks
```

**查询参数**：
- `status`: 任务状态（字符串，可选）
- `task_type`: 任务类型（字符串，可选）
- `limit`: 返回结果数量（整数，可选，默认20）
- `offset`: 偏移量（整数，可选，默认0）

**响应示例**：

```json
{
  "success": true,
  "data": {
    "tasks": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "task_type": "file_embed",
        "priority": 5,
        "status": "completed",
        "created_at": 1704067200.0,
        "progress": 1.0
      }
    ],
    "total": 50,
    "limit": 20,
    "offset": 0
  },
  "message": "获取任务列表成功",
  "error": null,
  "timestamp": 1704067200.0
}
```

### 4. 系统管理

#### 4.1 获取系统状态

获取系统运行状态。

**请求**：

```http
GET /api/v1/system/status
```

**响应示例**：

```json
{
  "success": true,
  "data": {
    "status": "running",
    "uptime": 86400.0,
    "version": "1.0.0",
    "database": {
      "status": "connected",
      "total_files": 1000,
      "indexed_files": 950,
      "pending_files": 50
    },
    "tasks": {
      "total": 50,
      "pending": 10,
      "running": 5,
      "completed": 30,
      "failed": 5
    },
    "hardware": {
      "cpu_usage": 45.5,
      "memory_usage": 60.2,
      "gpu_usage": 30.0
    }
  },
  "message": "获取系统状态成功",
  "error": null,
  "timestamp": 1704067200.0
}
```

#### 4.2 获取配置

获取系统配置。

**请求**：

```http
GET /api/v1/system/config
```

**响应示例**：

```json
{
  "success": true,
  "data": {
    "system": {
      "debug": false,
      "data_dir": "/path/to/data"
    },
    "models": {
      "clip": {
        "model_name": "apple/mobileclip",
        "device": "cpu",
        "batch_size": 8
      }
    },
    "media_processing": {
      "video": {
        "use_scene_detect": true,
        "max_segment_duration": 5
      }
    }
  },
  "message": "获取配置成功",
  "error": null,
  "timestamp": 1704067200.0
}
```

#### 4.3 更新配置

更新系统配置。

**请求**：

```http
PUT /api/v1/system/config
```

**请求参数**：

```json
{
  "system": {
    "debug": true
  },
  "models": {
    "clip": {
      "batch_size": 16
    }
  }
}
```

**响应示例**：

```json
{
  "success": true,
  "data": {
    "updated": true,
    "config": {
      "system": {
        "debug": true,
        "data_dir": "/path/to/data"
      },
      "models": {
        "clip": {
          "model_name": "apple/mobileclip",
          "device": "cpu",
          "batch_size": 16
        }
      }
    }
  },
  "message": "配置更新成功",
  "error": null,
  "timestamp": 1704067200.0
}
```

#### 4.4 重新加载配置

重新加载配置文件。

**请求**：

```http
POST /api/v1/system/reload-config
```

**响应示例**：

```json
{
  "success": true,
  "data": {
    "reloaded": true,
    "timestamp": 1704067200.0
  },
  "message": "配置重新加载成功",
  "error": null,
  "timestamp": 1704067200.0
}
```

#### 4.5 获取性能指标

获取系统性能指标。

**请求**：

```http
GET /api/v1/system/metrics
```

**查询参数**：
- `start_time`: 开始时间戳（浮点数，可选）
- `end_time`: 结束时间戳（浮点数，可选）

**响应示例**：

```json
{
  "success": true,
  "data": {
    "search_performance": {
      "avg_response_time": 0.5,
      "max_response_time": 1.2,
      "min_response_time": 0.3,
      "total_requests": 1000
    },
    "embedding_performance": {
      "avg_processing_time": 2.5,
      "max_processing_time": 5.0,
      "min_processing_time": 1.0,
      "total_processed": 500
    },
    "system_performance": {
      "cpu_usage": 45.5,
      "memory_usage": 60.2,
      "disk_usage": 30.0
    }
  },
  "message": "获取性能指标成功",
  "error": null,
  "timestamp": 1704067200.0
}
```

### 5. 数据库管理

#### 5.1 获取数据库统计信息

获取数据库统计信息。

**请求**：

```http
GET /api/v1/database/stats
```

**响应示例**：

```json
{
  "success": true,
  "data": {
    "total_files": 1000,
    "indexed_files": 950,
    "pending_files": 50,
    "total_vectors": 5000,
    "vector_dimensions": 512,
    "database_size": 1073741824,
    "last_updated": 1704067200.0
  },
  "message": "获取数据库统计信息成功",
  "error": null,
  "timestamp": 1704067200.0
}
```

#### 5.2 清理数据库

清理数据库中的过期数据。

**请求**：

```http
POST /api/v1/database/cleanup
```

**请求参数**：

```json
{
  "retention_days": 30,
  "dry_run": false
}
```

**参数说明**：
- `retention_days`: 保留天数（整数，必需）
- `dry_run`: 是否模拟运行（布尔值，可选，默认false）

**响应示例**：

```json
{
  "success": true,
  "data": {
    "deleted_files": 10,
    "deleted_vectors": 50,
    "freed_space": 536870912,
    "dry_run": false
  },
  "message": "数据库清理成功",
  "error": null,
  "timestamp": 1704067200.0
}
```

## API版本管理

### 版本策略

- **URL版本控制**: 通过URL路径指定API版本（如 `/api/v1/`）
- **向后兼容**: 新版本保持向后兼容，不破坏现有客户端
- **弃用策略**: 旧版本至少保留6个月，弃用前提前通知
- **版本头**: 响应头中包含API版本信息

### 版本信息

**请求**：

```http
GET /api/v1/version
```

**响应示例**：

```json
{
  "success": true,
  "data": {
    "version": "1.0.0",
    "api_version": "v1",
    "supported_versions": ["v1"],
    "deprecated_versions": [],
    "latest_version": "v1"
  },
  "message": "获取版本信息成功",
  "error": null,
  "timestamp": 1704067200.0
}
```

## 限流策略

### 请求频率限制

- **默认限制**: 每分钟100次请求
- **认证用户**: 每分钟200次请求
- **管理员**: 无限制

### 限流响应

当超过限流阈值时，返回以下响应：

```json
{
  "success": false,
  "data": null,
  "message": "请求频率过高",
  "error": {
    "code": 429,
    "message": "Too Many Requests",
    "details": "每分钟最多100次请求",
    "retry_after": 30
  },
  "timestamp": 1704067200.0
}
```

**响应头**：
- `X-RateLimit-Limit`: 限制次数
- `X-RateLimit-Remaining`: 剩余次数
- `X-RateLimit-Reset`: 重置时间

## WebSocket支持

### 连接WebSocket

```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws');

ws.onopen = () => {
  console.log('WebSocket连接已建立');
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('收到消息:', message);
};

ws.onclose = () => {
  console.log('WebSocket连接已关闭');
};

ws.onerror = (error) => {
  console.error('WebSocket错误:', error);
};
```

### 消息格式

**订阅任务更新**：

```json
{
  "action": "subscribe",
  "topic": "task_updates",
  "task_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**任务更新通知**：

```json
{
  "action": "notify",
  "topic": "task_updates",
  "data": {
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "completed",
    "progress": 1.0,
    "result": {
      "success": true
    }
  },
  "timestamp": 1704067200.0
}
```

## SDK和客户端

### Python SDK

```python
from msearch_client import MSearchClient

client = MSearchClient(
    base_url="http://localhost:8000/api/v1",
    api_key="your_api_key"
)

# 多模态搜索
results = client.search.multimodal(
    query="搜索关键词",
    modality="all",
    limit=20
)

# 添加文件
task = client.files.add(
    file_paths=["/path/to/file.mp4"],
    priority=5
)

# 获取任务信息
task_info = client.tasks.get(task.task_id)
```

### JavaScript SDK

```javascript
import { MSearchClient } from 'msearch-client';

const client = new MSearchClient({
  baseUrl: 'http://localhost:8000/api/v1',
  apiKey: 'your_api_key'
});

// 多模态搜索
const results = await client.search.multimodal({
  query: '搜索关键词',
  modality: 'all',
  limit: 20
});

// 添加文件
const task = await client.files.add({
  filePaths: ['/path/to/file.mp4'],
  priority: 5
});

// 获取任务信息
const taskInfo = await client.tasks.get(task.taskId);
```

## 最佳实践

### 1. 错误处理

始终检查响应中的 `success` 字段：

```python
response = client.search.multimodal(query="test")

if response['success']:
    results = response['data']['results']
else:
    error = response['error']
    print(f"错误: {error['code']} - {error['message']}")
```

### 2. 分页处理

使用 `limit` 和 `offset` 参数进行分页：

```python
limit = 20
offset = 0

while True:
    response = client.files.list(limit=limit, offset=offset)
    
    if not response['success']:
        break
    
    files = response['data']['files']
    if not files:
        break
    
    # 处理文件
    for file in files:
        process_file(file)
    
    offset += limit
```

### 3. 异步任务处理

对于耗时操作，使用异步任务：

```python
# 添加文件
task = client.files.add(file_paths=["/path/to/file.mp4"])

# 轮询任务状态
while True:
    task_info = client.tasks.get(task.task_id)
    
    if task_info['data']['status'] in ['completed', 'failed', 'cancelled']:
        break
    
    time.sleep(1)
```

### 4. WebSocket监听

使用WebSocket监听任务更新：

```python
from msearch_client import WebSocketClient

ws = WebSocketClient('ws://localhost:8000/api/v1/ws')

@ws.on('task_updates')
def handle_task_update(message):
    task_id = message['data']['task_id']
    status = message['data']['status']
    print(f"任务 {task_id} 状态更新: {status}")

ws.connect()
ws.subscribe('task_updates', task_id='your_task_id')
```

## 附录

### A. 完整错误码列表

| 错误码 | 说明 | HTTP状态码 |
|--------|------|-----------|
| 1000 | 成功 | 200 |
| 1001 | 参数错误 | 400 |
| 1002 | 认证失败 | 401 |
| 1003 | 权限不足 | 403 |
| 1004 | 资源不存在 | 404 |
| 1005 | 服务器错误 | 500 |
| 1006 | 任务不存在 | 404 |
| 1007 | 文件不存在 | 404 |
| 1008 | 数据库错误 | 500 |
| 1009 | 向量化失败 | 500 |
| 1010 | 检索失败 | 500 |
| 1011 | 请求频率过高 | 429 |
| 1012 | 配置错误 | 400 |
| 1013 | 文件格式不支持 | 400 |
| 1014 | 磁盘空间不足 | 500 |
| 1015 | 内存不足 | 500 |

### B. 数据类型定义

#### 文件类型

- `image`: 图像文件
- `video`: 视频文件
- `audio`: 音频文件
- `text`: 文本文件

#### 任务类型

- `file_scan`: 文件扫描
- `file_embed`: 文件向量化
- `video_slice`: 视频切片
- `audio_segment`: 音频分段

#### 任务状态

- `pending`: 等待中
- `running`: 运行中
- `completed`: 已完成
- `failed`: 失败
- `cancelled`: 已取消
- `paused`: 已暂停

#### 处理状态

- `pending`: 等待处理
- `processing`: 处理中
- `completed`: 处理完成
- `failed`: 处理失败

### C. 配置参数参考

详见 [design.md](../specs/multimodal-search-system/design.md) 中的配置章节。

### D. 更新日志

#### v1.0.0 (2024-01-01)
- 初始版本发布
- 支持多模态搜索
- 支持文件管理
- 支持任务管理
- 支持系统管理
- 支持WebSocket
