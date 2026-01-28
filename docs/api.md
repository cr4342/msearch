# API 文档

**文档版本**：v1.0  
**最后更新**：2026-01-19  
**对应设计文档**：[design.md](./design.md)  

---

> **文档定位**：本文档是 [design.md](./design.md) 的补充文档，详细展开第 2.9 节"WebUI 系统"和第 3.2 节"检索流程"的 API 接口定义。

**相关文档**：
- [design.md](./design.md) - 主设计文档
- [pyside6_ui_design.md](./pyside6_ui_design.md) - 桌面UI详细设计
- [task_control_api.md](./task_control_api.md) - 任务控制 API 文档

---

## 概述

本文档详细描述了 msearch 系统的 RESTful API 接口设计。所有 API 接口遵循 REST 规范，使用 JSON 格式进行数据交互。

**基础 URL**：`http://localhost:8000/api/v1`  
**API 版本**：v1  
**认证方式**：暂无（后续支持 API Key 认证）  
**请求格式**：JSON  
**响应格式**：JSON  
**字符编码**：UTF-8  

---

## 通用约定

### 状态码

| 状态码 | 含义 | 说明 |
|-------|------|------|
| 200 | OK | 请求成功 |
| 201 | Created | 资源创建成功 |
| 400 | Bad Request | 请求参数错误 |
| 401 | Unauthorized | 未授权 |
| 403 | Forbidden | 禁止访问 |
| 404 | Not Found | 资源不存在 |
| 500 | Internal Server Error | 服务器内部错误 |
| 503 | Service Unavailable | 服务不可用 |

### 通用响应格式

**成功响应**：
```json
{
    "code": 0,
    "message": "success",
    "data": {},
    "timestamp": 1640000000
}
```

**错误响应**：
```json
{
    "code": -1,
    "message": "错误信息",
    "error": {
        "type": "ErrorType",
        "details": "详细错误描述"
    },
    "timestamp": 1640000000
}
```

**分页响应**：
```json
{
    "code": 0,
    "message": "success",
    "data": {
        "items": [],
        "total": 100,
        "page": 1,
        "page_size": 20,
        "total_pages": 5
    },
    "timestamp": 1640000000
}
```

---

## 检索接口

### 2.1 文本检索

**接口地址**：`POST /search`  
**接口描述**：使用文本查询检索相关的图像、视频、音频等媒体文件  
**请求频率**：无限制（建议客户端控制在 1 次/秒以内）  

**请求参数**：
```json
{
    "query": "海滩日落",
    "modalities": ["image", "video", "audio"],
    "top_k": 20,
    "similarity_threshold": 0.7,
    "filters": {
        "file_type": ["image", "video"],
        "min_size": 1024,
        "max_size": 104857600,
        "created_after": "2023-01-01T00:00:00Z",
        "created_before": "2024-12-31T23:59:59Z"
    },
    "re_rank": true
}
```

**参数说明**：
| 参数 | 类型 | 必填 | 说明 | 默认值 |
|------|------|------|------|-------|
| query | string | 是 | 文本查询词 | - |
| modalities | array | 否 | 检索的媒体类型 | ["image", "video", "audio"] |
| top_k | integer | 否 | 返回结果数量 | 20 |
| similarity_threshold | float | 否 | 相似度阈值 | 0.7 |
| filters | object | 否 | 过滤条件 | null |
| filters.file_type | array | 否 | 文件类型过滤 | null |
| filters.min_size | integer | 否 | 最小文件大小（字节） | null |
| filters.max_size | integer | 否 | 最大文件大小（字节） | null |
| filters.created_after | string | 否 | 文件创建时间范围（开始） | null |
| filters.created_before | string | 否 | 文件创建时间范围（结束） | null |
| re_rank | boolean | 否 | 是否启用结果重排序 | true |

**响应示例**：
```json
{
    "code": 0,
    "message": "success",
    "data": {
        "query": "海滩日落",
        "total": 15,
        "took_ms": 125,
        "results": [
            {
                "id": "file_123456",
                "file_path": "/path/to/image.jpg",
                "file_name": "image.jpg",
                "file_type": "image",
                "file_size": 102400,
                "similarity": 0.92,
                "thumbnail": "/api/v1/files/file_123456/thumbnail",
                "metadata": {
                    "width": 1920,
                    "height": 1080,
                    "created_at": "2023-06-15T10:30:00Z",
                    "modified_at": "2023-06-15T10:30:00Z"
                }
            },
            {
                "id": "file_123457",
                "file_path": "/path/to/video.mp4",
                "file_name": "video.mp4",
                "file_type": "video",
                "file_size": 52428800,
                "similarity": 0.88,
                "thumbnail": "/api/v1/files/file_123457/thumbnail",
                "preview": "/api/v1/files/file_123457/preview",
                "metadata": {
                    "duration": 120.5,
                    "width": 1920,
                    "height": 1080,
                    "created_at": "2023-07-20T14:20:00Z",
                    "segments": [
                        {
                            "start_time": 0.0,
                            "end_time": 5.0,
                            "similarity": 0.88,
                            "thumbnail": "/api/v1/files/file_123457/segments/0/thumbnail"
                        }
                    ]
                }
            }
        ]
    },
    "timestamp": 1640000000
}
```

**错误响应**：
```json
{
    "code": -1,
    "message": "查询参数错误",
    "error": {
        "type": "ValidationError",
        "details": "query 参数不能为空"
    },
    "timestamp": 1640000000
}
```

### 2.2 图像检索

**接口地址**：`POST /search/image`  
**接口描述**：使用图像作为查询，检索相似的图像和视频  
**请求频率**：无限制（建议客户端控制在 1 次/2 秒以内）  

**请求参数**（Multipart Form Data）：
```
image: <文件> (必填) - 查询图像文件
modalities: image,video (可选) - 检索的媒体类型，默认 ["image", "video"]
top_k: 20 (可选) - 返回结果数量，默认 20
similarity_threshold: 0.7 (可选) - 相似度阈值，默认 0.7
re_rank: true (可选) - 是否启用结果重排序，默认 true
```

**请求示例**（cURL）：
```bash
curl -X POST http://localhost:8000/api/v1/search/image \
  -F "image=@query.jpg" \
  -F "modalities=image,video" \
  -F "top_k=20"
```

**响应示例**：
```json
{
    "code": 0,
    "message": "success",
    "data": {
        "total": 12,
        "took_ms": 250,
        "results": [
            {
                "id": "file_789012",
                "file_path": "/path/to/similar_image.jpg",
                "file_name": "similar_image.jpg",
                "file_type": "image",
                "file_size": 153600,
                "similarity": 0.95,
                "thumbnail": "/api/v1/files/file_789012/thumbnail",
                "metadata": {
                    "width": 1920,
                    "height": 1080,
                    "created_at": "2023-05-10T09:15:00Z"
                }
            }
        ]
    },
    "timestamp": 1640000000
}
```

**错误响应**：
```json
{
    "code": -1,
    "message": "图像处理失败",
    "error": {
        "type": "ImageProcessingError",
        "details": "不支持的图像格式"
    },
    "timestamp": 1640000000
}
```

### 2.3 音频检索

**接口地址**：`POST /search/audio`  
**接口描述**：使用音频作为查询，检索相似的音频和视频  
**请求频率**：无限制（建议客户端控制在 1 次/3 秒以内）  

**请求参数**（Multipart Form Data）：
```
audio: <文件> (必填) - 查询音频文件
modalities: audio,video (可选) - 检索的媒体类型，默认 ["audio", "video"]
top_k: 20 (可选) - 返回结果数量，默认 20
similarity_threshold: 0.6 (可选) - 相似度阈值，默认 0.6
re_rank: true (可选) - 是否启用结果重排序，默认 true
```

**请求示例**（cURL）：
```bash
curl -X POST http://localhost:8000/api/v1/search/audio \
  -F "audio=@query.mp3" \
  -F "modalities=audio,video" \
  -F "top_k=20"
```

**响应示例**：
```json
{
    "code": 0,
    "message": "success",
    "data": {
        "total": 8,
        "took_ms": 350,
        "results": [
            {
                "id": "file_345678",
                "file_path": "/path/to/similar_audio.mp3",
                "file_name": "similar_audio.mp3",
                "file_type": "audio",
                "file_size": 2048000,
                "similarity": 0.89,
                "metadata": {
                    "duration": 30.0,
                    "sample_rate": 44100,
                    "channels": 2,
                    "created_at": "2023-08-05T16:45:00Z"
                }
            }
        ]
    },
    "timestamp": 1640000000
}
```

**错误响应**：
```json
{
    "code": -1,
    "message": "音频处理失败",
    "error": {
        "type": "AudioProcessingError",
        "details": "音频文件损坏或格式不支持"
    },
    "timestamp": 1640000000
}
```

---

## 任务管理接口

### 3.1 获取任务列表

**接口地址**：`GET /tasks`  
**接口描述**：获取系统中所有任务的列表，支持分页和筛选  
**请求频率**：无限制（建议客户端控制在 1 次/5 秒以内）  

**请求参数**（Query String）：
```
page: 1 (可选) - 页码，默认 1
page_size: 20 (可选) - 每页数量，默认 20，最大 100
status: running (可选) - 任务状态筛选，可选值：pending, running, completed, failed
file_type: image (可选) - 文件类型筛选，可选值：image, video, audio, text
sort_by: created_at (可选) - 排序字段，可选值：created_at, started_at, completed_at
sort_order: desc (可选) - 排序顺序，可选值：asc, desc
```

**请求示例**：
```bash
curl "http://localhost:8000/api/v1/tasks?page=1&page_size=20&status=running&sort_by=created_at&sort_order=desc"
```

**响应示例**：
```json
{
    "code": 0,
    "message": "success",
    "data": {
        "page": 1,
        "page_size": 20,
        "total": 156,
        "total_pages": 8,
        "tasks": [
            {
                "id": "task_123456",
                "type": "file_embed_video",
                "file_id": "file_789012",
                "file_path": "/path/to/video.mp4",
                "file_name": "video.mp4",
                "file_type": "video",
                "status": "running",
                "progress": 65.0,
                "priority": 2,
                "created_at": "2023-09-10T08:00:00Z",
                "started_at": "2023-09-10T08:00:05Z",
                "current_step": "video_embedding",
                "steps": [
                    {
                        "name": "文件扫描",
                        "status": "completed",
                        "progress": 100.0,
                        "duration_ms": 150
                    },
                    {
                        "name": "元数据提取",
                        "status": "completed",
                        "progress": 100.0,
                        "duration_ms": 200
                    },
                    {
                        "name": "视频向量化",
                        "status": "running",
                        "progress": 65.0,
                        "duration_ms": 15000
                    }
                ]
            }
        ]
    },
    "timestamp": 1640000000
}
```

### 3.2 获取任务详情

**接口地址**：`GET /tasks/{task_id}`  
**接口描述**：获取指定任务的详细信息  

**请求参数**：
| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| task_id | path | string | 是 | 任务ID |

**请求示例**：
```bash
curl "http://localhost:8000/api/v1/tasks/task_123456"
```

**响应示例**：
```json
{
    "code": 0,
    "message": "success",
    "data": {
        "id": "task_123456",
        "type": "file_embed_video",
        "file_id": "file_789012",
        "file_path": "/path/to/video.mp4",
        "file_name": "video.mp4",
        "file_type": "video",
        "file_size": 104857600,
        "status": "completed",
        "progress": 100.0,
        "priority": 2,
        "created_at": "2023-09-10T08:00:00Z",
        "started_at": "2023-09-10T08:00:05Z",
        "completed_at": "2023-09-10T08:02:30Z",
        "duration_ms": 145000,
        "steps": [
            {
                "name": "文件扫描",
                "status": "completed",
                "progress": 100.0,
                "started_at": "2023-09-10T08:00:05Z",
                "completed_at": "2023-09-10T08:00:05Z",
                "duration_ms": 150
            },
            {
                "name": "元数据提取",
                "status": "completed",
                "progress": 100.0,
                "started_at": "2023-09-10T08:00:05Z",
                "completed_at": "2023-09-10T08:00:05Z",
                "duration_ms": 200
            },
            {
                "name": "视频预处理",
                "status": "completed",
                "progress": 100.0,
                "started_at": "2023-09-10T08:00:06Z",
                "completed_at": "2023-09-10T08:00:10Z",
                "duration_ms": 4000
            },
            {
                "name": "视频向量化",
                "status": "completed",
                "progress": 100.0,
                "started_at": "2023-09-10T08:00:10Z",
                "completed_at": "2023-09-10T08:02:25Z",
                "duration_ms": 135000
            },
            {
                "name": "向量存储",
                "status": "completed",
                "progress": 100.0,
                "started_at": "2023-09-10T08:02:25Z",
                "completed_at": "2023-09-10T08:02:26Z",
                "duration_ms": 1000
            },
            {
                "name": "缩略图生成",
                "status": "completed",
                "progress": 100.0,
                "started_at": "2023-09-10T08:02:26Z",
                "completed_at": "2023-09-10T08:02:30Z",
                "duration_ms": 4000
            }
        ],
        "metadata": {
            "duration": 120.5,
            "width": 1920,
            "height": 1080,
            "segments_count": 24
        }
    },
    "timestamp": 1640000000
}
```

**错误响应**：
```json
{
    "code": -1,
    "message": "任务不存在",
    "error": {
        "type": "NotFoundError",
        "details": "任务 task_999999 不存在"
    },
    "timestamp": 1640000000
}
```

### 3.3 获取任务统计

**接口地址**：`GET /tasks/stats`  
**接口描述**：获取任务的统计信息  

**请求示例**：
```bash
curl "http://localhost:8000/api/v1/tasks/stats"
```

**响应示例**：
```json
{
    "code": 0,
    "message": "success",
    "data": {
        "total": 1256,
        "pending": 156,
        "running": 24,
        "completed": 1058,
        "failed": 18,
        "by_type": {
            "file_scan": {"total": 200, "completed": 200},
            "file_embed_image": {"total": 450, "completed": 420},
            "file_embed_video": {"total": 380, "completed": 320},
            "file_embed_audio": {"total": 226, "completed": 218},
            "thumbnail_generate": {"total": 1256, "completed": 1058}
        },
        "by_status": {
            "pending": 156,
            "running": 24,
            "completed": 1058,
            "failed": 18
        },
        "avg_duration_ms": {
            "file_embed_image": 2500,
            "file_embed_video": 150000,
            "file_embed_audio": 8000
        }
    },
    "timestamp": 1640000000
}
```

### 3.4 取消任务

**接口地址**：`POST /tasks/{task_id}/cancel`  
**接口描述**：取消指定的任务  

**请求参数**：
| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| task_id | path | string | 是 | 任务ID |

**请求示例**：
```bash
curl -X POST "http://localhost:8000/api/v1/tasks/task_123456/cancel"
```

**响应示例**：
```json
{
    "code": 0,
    "message": "任务已取消",
    "data": {
        "task_id": "task_123456",
        "status": "cancelled",
        "cancelled_at": "2023-09-10T08:01:00Z"
    },
    "timestamp": 1640000000
}
```

**错误响应**：
```json
{
    "code": -1,
    "message": "无法取消任务",
    "error": {
        "type": "OperationError",
        "details": "任务已完成，无法取消"
    },
    "timestamp": 1640000000
}
```

### 3.5 重试失败任务

**接口地址**：`POST /tasks/{task_id}/retry`  
**接口描述**：重试指定的失败任务  

**请求参数**：
| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| task_id | path | string | 是 | 任务ID |

**请求示例**：
```bash
curl -X POST "http://localhost:8000/api/v1/tasks/task_123456/retry"
```

**响应示例**：
```json
{
    "code": 0,
    "message": "任务已重新加入队列",
    "data": {
        "task_id": "task_123456",
        "new_task_id": "task_123457",
        "status": "pending",
        "created_at": "2023-09-10T09:00:00Z"
    },
    "timestamp": 1640000000
}
```

---

## 文件管理接口

### 4.1 获取文件列表

**接口地址**：`GET /files`  
**接口描述**：获取已索引的文件列表，支持分页和筛选  

**请求参数**（Query String）：
```
page: 1 (可选) - 页码，默认 1
page_size: 20 (可选) - 每页数量，默认 20，最大 100
file_type: image (可选) - 文件类型筛选，可选值：image, video, audio, text
status: indexed (可选) - 文件状态筛选，可选值：pending, indexing, indexed, failed
min_size: 1024 (可选) - 最小文件大小（字节）
max_size: 104857600 (可选) - 最大文件大小（字节）
sort_by: created_at (可选) - 排序字段，可选值：created_at, modified_at, file_size, file_name
sort_order: desc (可选) - 排序顺序，可选值：asc, desc
```

**请求示例**：
```bash
curl "http://localhost:8000/api/v1/files?page=1&page_size=20&file_type=video&status=indexed&sort_by=created_at&sort_order=desc"
```

**响应示例**：
```json
{
    "code": 0,
    "message": "success",
    "data": {
        "page": 1,
        "page_size": 20,
        "total": 526,
        "total_pages": 27,
        "files": [
            {
                "id": "file_123456",
                "file_path": "/path/to/video.mp4",
                "file_name": "video.mp4",
                "file_type": "video",
                "file_size": 104857600,
                "file_hash": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6",
                "status": "indexed",
                "created_at": "2023-09-10T08:00:00Z",
                "modified_at": "2023-09-10T08:00:00Z",
                "indexed_at": "2023-09-10T08:02:30Z",
                "thumbnail": "/api/v1/files/file_123456/thumbnail",
                "metadata": {
                    "duration": 120.5,
                    "width": 1920,
                    "height": 1080,
                    "frame_rate": 30.0,
                    "codec": "h264",
                    "segments_count": 24
                }
            },
            {
                "id": "file_123457",
                "file_path": "/path/to/image.jpg",
                "file_name": "image.jpg",
                "file_type": "image",
                "file_size": 102400,
                "file_hash": "b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6",
                "status": "indexed",
                "created_at": "2023-09-09T14:30:00Z",
                "modified_at": "2023-09-09T14:30:00Z",
                "indexed_at": "2023-09-09T14:31:00Z",
                "thumbnail": "/api/v1/files/file_123457/thumbnail",
                "metadata": {
                    "width": 1920,
                    "height": 1080,
                    "format": "jpeg",
                    "color_mode": "rgb"
                }
            }
        ]
    },
    "timestamp": 1640000000
}
```

### 4.2 获取文件详情

**接口地址**：`GET /files/{file_id}`  
**接口描述**：获取指定文件的详细信息  

**请求参数**：
| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| file_id | path | string | 是 | 文件ID |

**请求示例**：
```bash
curl "http://localhost:8000/api/v1/files/file_123456"
```

**响应示例**：
```json
{
    "code": 0,
    "message": "success",
    "data": {
        "id": "file_123456",
        "file_path": "/path/to/video.mp4",
        "file_name": "video.mp4",
        "file_type": "video",
        "file_size": 104857600,
        "file_hash": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6",
        "status": "indexed",
        "created_at": "2023-09-10T08:00:00Z",
        "modified_at": "2023-09-10T08:00:00Z",
        "indexed_at": "2023-09-10T08:02:30Z",
        "thumbnail": "/api/v1/files/file_123456/thumbnail",
        "preview": "/api/v1/files/file_123456/preview",
        "metadata": {
            "duration": 120.5,
            "width": 1920,
            "height": 1080,
            "frame_rate": 30.0,
            "codec": "h264",
            "bitrate": 6990507,
            "audio_codec": "aac",
            "audio_sample_rate": 44100,
            "audio_channels": 2,
            "segments": [
                {
                    "id": "segment_001",
                    "start_time": 0.0,
                    "end_time": 5.0,
                    "thumbnail": "/api/v1/files/file_123456/segments/0/thumbnail",
                    "similarity": 0.95
                },
                {
                    "id": "segment_002",
                    "start_time": 5.0,
                    "end_time": 10.0,
                    "thumbnail": "/api/v1/files/file_123456/segments/1/thumbnail",
                    "similarity": 0.92
                }
            ]
        },
        "tasks": [
            {
                "id": "task_789012",
                "type": "file_embed_video",
                "status": "completed",
                "completed_at": "2023-09-10T08:02:30Z"
            }
        ]
    },
    "timestamp": 1640000000
}
```

**错误响应**：
```json
{
    "code": -1,
    "message": "文件不存在",
    "error": {
        "type": "NotFoundError",
        "details": "文件 file_999999 不存在"
    },
    "timestamp": 1640000000
}
```

### 4.3 获取文件缩略图

**接口地址**：`GET /files/{file_id}/thumbnail`  
**接口描述**：获取指定文件的缩略图  

**请求参数**：
| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| file_id | path | string | 是 | 文件ID |
| width | query | integer | 否 | 缩略图宽度，默认 256 |
| height | query | integer | 否 | 缩略图高度，默认 256 |

**请求示例**：
```bash
curl "http://localhost:8000/api/v1/files/file_123456/thumbnail?width=256&height=256"
```

**响应**：
- **成功**：返回 JPEG 格式的缩略图图片（Content-Type: image/jpeg）
- **失败**：返回 JSON 格式的错误信息

**错误响应**：
```json
{
    "code": -1,
    "message": "缩略图生成失败",
    "error": {
        "type": "ThumbnailError",
        "details": "文件 file_123456 的缩略图尚未生成"
    },
    "timestamp": 1640000000
}
```

### 4.4 获取文件预览

**接口地址**：`GET /files/{file_id}/preview`  
**接口描述**：获取指定视频文件的预览片段（仅支持视频文件）  

**请求参数**：
| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| file_id | path | string | 是 | 文件ID |
| duration | query | integer | 否 | 预览时长（秒），默认 5 |
| start_time | query | float | 否 | 预览开始时间（秒），默认 0 |

**请求示例**：
```bash
curl "http://localhost:8000/api/v1/files/file_123456/preview?duration=5&start_time=0"
```

**响应**：
- **成功**：返回 MP4 格式的预览视频（Content-Type: video/mp4）
- **失败**：返回 JSON 格式的错误信息

**错误响应**：
```json
{
    "code": -1,
    "message": "预览生成失败",
    "error": {
        "type": "PreviewError",
        "details": "文件 file_123456 不是视频文件"
    },
    "timestamp": 1640000000
}
```

### 4.5 删除文件索引

**接口地址**：`DELETE /files/{file_id}`  
**接口描述**：删除指定文件的索引（不会删除源文件）  

**请求参数**：
| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| file_id | path | string | 是 | 文件ID |

**请求示例**：
```bash
curl -X DELETE "http://localhost:8000/api/v1/files/file_123456"
```

**响应示例**：
```json
{
    "code": 0,
    "message": "文件索引已删除",
    "data": {
        "file_id": "file_123456",
        "file_path": "/path/to/video.mp4",
        "deleted_at": "2023-09-10T10:00:00Z",
        "deleted_vector_count": 24
    },
    "timestamp": 1640000000
}
```

**错误响应**：
```json
{
    "code": -1,
    "message": "删除失败",
    "error": {
        "type": "DeleteError",
        "details": "文件 file_123456 正在处理中，无法删除"
    },
    "timestamp": 1640000000
}
```

---

## 系统监控接口

### 5.1 获取系统信息

**接口地址**：`GET /system/info`  
**接口描述**：获取系统的基本信息  

**请求示例**：
```bash
curl "http://localhost:8000/api/v1/system/info"
```

**响应示例**：
```json
{
    "code": 0,
    "message": "success",
    "data": {
        "version": "2.0.0",
        "platform": "Linux",
        "python_version": "3.10.12",
        "cpu_count": 8,
        "memory_total_gb": 15.5,
        "memory_used_gb": 8.2,
        "memory_percent": 52.9,
        "gpu_info": {
            "available": true,
            "name": "NVIDIA GeForce RTX 3080",
            "memory_total_gb": 10.0,
            "memory_used_gb": 4.5,
            "memory_percent": 45.0
        },
        "start_time": "2023-09-10T07:00:00Z",
        "uptime_seconds": 3600,
        "config": {
            "data_dir": "/data/project/msearch/data",
            "model_cache_dir": "/data/project/msearch/data/models",
            "log_level": "INFO"
        }
    },
    "timestamp": 1640000000
}
```

### 5.2 获取模型信息

**接口地址**：`GET /models/info`  
**接口描述**：获取已加载的模型信息  

**请求示例**：
```bash
curl "http://localhost:8000/api/v1/models/info"
```

**响应示例**：
```json
{
    "code": 0,
    "message": "success",
    "data": {
        "[配置驱动模型]": {
            "name": "[配置驱动模型]",
            "path": "/data/project/msearch/data/models/[配置驱动模型]",
            "embedding_dim": 512,  # [配置驱动模型]的嵌入维度
            "device": "cuda",
            "precision": "float16",
            "batch_size": 16,
            "input_resolution": 512,
            "loaded": true,
            "load_time_seconds": 15.2
        },
        "[配置驱动模型]": {
            "name": "[配置驱动模型]",
            "path": "/data/project/msearch/[配置驱动模型]",
            "vector_dim": 512,
            "device": "cuda",
            "precision": "float16",
            "batch_size": 8,
            "sample_rate": 44100,
            "loaded": true,
            "load_time_seconds": 8.5
        }
    },
    "timestamp": 1640000000
}
```

### 5.3 获取数据库统计

**接口地址**：`GET /database/stats`  
**接口描述**：获取数据库的统计信息  

**请求示例**：
```bash
curl "http://localhost:8000/api/v1/database/stats"
```

**响应示例**：
```json
{
    "code": 0,
    "message": "success",
    "data": {
        "sqlite": {
            "path": "/data/project/msearch/data/database/sqlite/msearch.db",
            "size_mb": 125.5,
            "tables": {
                "file_metadata": {"count": 1256},
                "file_references": {"count": 1256},
                "video_metadata": {"count": 380},
                "video_segments": {"count": 9120},
                "vector_timestamp_map": {"count": 9120}
            }
        },
        "lancedb": {
            "path": "/data/project/msearch/data/database/lancedb",
            "size_mb": 2560.8,
            "tables": {
                "unified_vectors": {
                    "count": 15680,
                    "vector_dim": 512,
                    "index_type": "ivf",
                    "index_build_time_seconds": 120.5
                }
            }
        }
    },
    "timestamp": 1640000000
}
```

### 5.4 健康检查

**接口地址**：`GET /health`  
**接口描述**：检查系统的健康状态  

**请求示例**：
```bash
curl "http://localhost:8000/health"
```

**响应示例**：
```json
{
    "status": "healthy",
    "timestamp": 1640000000,
    "checks": {
        "database": {
            "status": "healthy",
            "message": "SQLite and LanceDB are accessible"
        },
        "models": {
            "status": "healthy",
            "message": "All models are loaded"
        },
        "task_manager": {
            "status": "healthy",
            "message": "Task manager is running"
        },
        "file_monitor": {
            "status": "healthy",
            "message": "File monitor is running"
        }
    }
}
```

**错误响应**：
```json
{
    "status": "unhealthy",
    "timestamp": 1640000000,
    "checks": {
        "database": {
            "status": "healthy",
            "message": "SQLite and LanceDB are accessible"
        },
        "models": {
            "status": "unhealthy",
            "message": "Image/video model failed to load: CUDA out of memory"
        },
        "task_manager": {
            "status": "healthy",
            "message": "Task manager is running"
        },
        "file_monitor": {
            "status": "healthy",
            "message": "File monitor is running"
        }
    }
}
```

---

## 配置管理接口

### 6.1 获取配置

**接口地址**：`GET /config`  
**接口描述**：获取系统的配置信息  

**请求参数**（Query String）：
```
section: models (可选) - 配置节名称，返回指定节的配置
```

**请求示例**：
```bash
curl "http://localhost:8000/api/v1/config?section=models"
```

**响应示例**：
```json
{
    "code": 0,
    "message": "success",
    "data": {
        "models": {
            "model_cache_dir": "data/models",
            "[配置驱动模型]": {
                "model_name": "[配置驱动模型]",
                "model_path": "data/models/[配置驱动模型]",
                "embedding_dim": 512,
                "device": "cuda",
                "precision": "float16",
                "batch_size": 16,
                "input_resolution": 512
            },
            "[配置驱动模型]": {
                "model_name": "[配置驱动模型]",
                "model_path": "[配置驱动模型]",
                "vector_dim": 512,
                "device": "cuda",
                "precision": "float16",
                "batch_size": 8,
                "sample_rate": 44100
            }
        }
    },
    "timestamp": 1640000000
}
```

### 6.2 更新配置

**接口地址**：`PUT /config`  
**接口描述**：更新系统的配置（需要重启生效）  

**请求参数**：
```json
{
    "section": "models",
    "config": {
        "[配置驱动模型]": {
            "batch_size": 8,
            "precision": "float32"
        }
    }
}
```

**参数说明**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| section | string | 是 | 配置节名称 |
| config | object | 是 | 配置内容 |

**请求示例**：
```bash
curl -X PUT "http://localhost:8000/api/v1/config" \
  -H "Content-Type: application/json" \
  -d '{
    "section": "models",
    "config": {
      "[配置驱动模型]": {
        "batch_size": 8,
        "precision": "float32"
      }
    }
  }'
```

**响应示例**：
```json
{
    "code": 0,
    "message": "配置已更新",
    "data": {
        "section": "models",
        "updated": true,
        "restart_required": true,
        "message": "配置已保存，需要重启服务生效"
    },
    "timestamp": 1640000000
}
```

**错误响应**：
```json
{
    "code": -1,
    "message": "配置更新失败",
    "error": {
        "type": "ValidationError",
        "details": "batch_size 参数必须是正整数"
    },
    "timestamp": 1640000000
}
```

---

## 附录

### A.1 数据类型定义

**文件类型**：
- `image` - 图像文件（jpg, jpeg, png, bmp, gif, webm, tiff）
- `video` - 视频文件（mp4, avi, mov, wmv, flv, mkv, webm）
- `audio` - 音频文件（mp3, wav, aac, ogg, flac, wma, m4a）
- `text` - 文本文件（txt, md, pdf, docx, xlsx, csv）

**任务状态**：
- `pending` - 待执行
- `running` - 执行中
- `completed` - 已完成
- `failed` - 执行失败
- `cancelled` - 已取消

**文件状态**：
- `pending` - 待索引
- `indexing` - 索引中
- `indexed` - 已索引
- `failed` - 索引失败
- `outdated` - 需要更新
- `removed` - 已移除

### A.2 错误码

| 错误码 | 含义 | 说明 |
|-------|------|------|
| 0 | Success | 请求成功 |
| -1 | General Error | 通用错误 |
| -2 | Validation Error | 参数验证错误 |
| -3 | Not Found | 资源不存在 |
| -4 | Operation Error | 操作失败 |
| -5 | Permission Error | 权限不足 |
| -6 | Database Error | 数据库错误 |
| -7 | Model Error | 模型加载或推理错误 |
| -8 | File Error | 文件处理错误 |
| -9 | Task Error | 任务执行错误 |
| -10 | System Error | 系统错误 |

### A.3 限流说明

当前版本暂未实现 API 限流，但建议客户端遵守以下频率限制：
- 检索接口：1 次/秒
- 图像检索：1 次/2 秒
- 音频检索：1 次/3 秒
- 任务查询：1 次/5 秒
- 系统监控：1 次/10 秒

后续版本将实现基于令牌桶的限流机制。

### A.4 版本历史

**v1.0.0** (2026-01-19)
- ✅ 初始版本发布
- ✅ 基础检索接口（文本、图像、音频）
- ✅ 文件管理接口
- ✅ 任务管理接口
- ✅ 系统监控接口
- ✅ 配置管理接口

---

**© 2026 msearch 技术团队**  
**本文档受团队内部保密协议保护**