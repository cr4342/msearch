# API文档

> **文档导航**: [文档索引](README.md) | [需求文档](requirements.md) | [设计文档](design.md) | [开发计划](development_plan.md) | [测试策略](test_strategy.md) | [部署指南](deployment_guide.md)

## 1. API概述

### 1.1 基础信息

**API基础URL**: `http://localhost:8000/api/v1`

**认证方式**: 当前版本无需认证（后续版本将支持API Key认证）

**数据格式**: JSON

**字符编码**: UTF-8

### 1.2 通用响应格式

**成功响应**：
```json
{
  "status": "success",
  "data": {
    // 具体数据内容
  },
  "message": "操作成功",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**错误响应**：
```json
{
  "status": "error",
  "error": {
    "code": "INVALID_PARAMETER",
    "message": "参数验证失败",
    "details": "query参数不能为空"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 1.3 HTTP状态码

| 状态码 | 说明 | 使用场景 |
|--------|------|---------|
| 200 | 成功 | 请求处理成功 |
| 400 | 请求错误 | 参数验证失败、格式错误 |
| 404 | 资源不存在 | 请求的资源未找到 |
| 500 | 服务器错误 | 内部处理异常 |
| 503 | 服务不可用 | 系统维护或过载 |

## 2. 搜索接口

### 2.1 多模态搜索

**端点**: `POST /api/v1/search`

**描述**: 执行多模态搜索，支持文本、图片、音频等多种查询方式

**请求参数**：
```json
{
  "query": "美丽的风景照片",           // 查询文本
  "modality": "text_to_image",        // 搜索模态
  "top_k": 10,                        // 返回结果数量
  "similarity_threshold": 0.3,        // 相似度阈值
  "filters": {                        // 可选过滤条件
    "file_types": ["image", "video"],
    "date_range": {
      "start": "2024-01-01T00:00:00Z",
      "end": "2024-01-31T23:59:59Z"
    }
  }
}
```

**支持的搜索模态**：
- `text_to_image`: 文本搜索图片
- `text_to_video`: 文本搜索视频
- `text_to_audio`: 文本搜索音频
- `image_to_image`: 图片搜索相似图片
- `smart`: 智能搜索（自动识别查询类型）

**响应示例**：
```json
{
  "status": "success",
  "data": {
    "results": [
      {
        "file_id": "img_001",
        "file_path": "/home/user/photos/sunset.jpg",
        "file_name": "sunset.jpg",
        "file_type": "image",
        "similarity_score": 0.92,
        "metadata": {
          "width": 1920,
          "height": 1080,
          "format": "jpeg",
          "size_mb": 2.5
        },
        "timestamp": null
      },
      {
        "file_id": "vid_002",
        "file_path": "/home/user/videos/vacation.mp4",
        "file_name": "vacation.mp4",
        "file_type": "video",
        "similarity_score": 0.87,
        "metadata": {
          "duration": 120.5,
          "resolution": "1920x1080",
          "format": "mp4",
          "size_mb": 45.2
        },
        "timestamp": {
          "start_time": 25.5,
          "end_time": 27.5,
          "duration": 2.0
        }
      }
    ],
    "total_results": 2,
    "query_time_ms": 156,
    "search_metadata": {
      "query_type": "visual",
      "models_used": ["clip"],
      "collections_searched": ["image_vectors", "video_vectors"]
    }
  }
}
```

### 2.2 图片上传搜索

**端点**: `POST /api/v1/search/image`

**描述**: 通过上传图片进行相似图片搜索

**请求格式**: `multipart/form-data`

**请求参数**：
- `image`: 图片文件（支持JPG、PNG、GIF等格式）
- `top_k`: 返回结果数量（可选，默认10）
- `similarity_threshold`: 相似度阈值（可选，默认0.3）

**cURL示例**：
```bash
curl -X POST "http://localhost:8000/api/v1/search/image" \
  -F "image=@/path/to/query_image.jpg" \
  -F "top_k=5" \
  -F "similarity_threshold=0.5"
```

### 2.3 融合搜索

**端点**: `POST /api/v1/search/fusion`

**描述**: 多模态融合搜索，支持文本、图片、音频的组合查询

**请求参数**：
```json
{
  "text_query": "会议讨论场景",
  "image_file": "base64_encoded_image_data",  // 可选
  "audio_file": "base64_encoded_audio_data",  // 可选
  "weights": {                                // 模态权重
    "text": 0.5,
    "image": 0.3,
    "audio": 0.2
  },
  "top_k": 10,
  "fusion_strategy": "weighted_sum"           // 融合策略
}
```

## 3. 文件管理接口

### 3.1 获取文件列表

**端点**: `GET /api/v1/files`

**描述**: 获取系统中已索引的文件列表

**查询参数**：
- `page`: 页码（默认1）
- `page_size`: 每页数量（默认20）
- `file_type`: 文件类型过滤（image/video/audio）
- `status`: 处理状态过滤（pending/processing/completed/failed）

**响应示例**：
```json
{
  "status": "success",
  "data": {
    "files": [
      {
        "file_id": "file_001",
        "file_path": "/home/user/photos/image1.jpg",
        "file_name": "image1.jpg",
        "file_type": "image",
        "file_size": 2048576,
        "status": "completed",
        "created_at": "2024-01-15T10:00:00Z",
        "updated_at": "2024-01-15T10:05:00Z",
        "metadata": {
          "width": 1920,
          "height": 1080,
          "format": "jpeg"
        }
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total_pages": 5,
      "total_items": 100
    }
  }
}
```

### 3.2 获取文件详情

**端点**: `GET /api/v1/files/{file_id}`

**描述**: 获取指定文件的详细信息

**路径参数**：
- `file_id`: 文件ID

**响应示例**：
```json
{
  "status": "success",
  "data": {
    "file_id": "file_001",
    "file_path": "/home/user/videos/meeting.mp4",
    "file_name": "meeting.mp4",
    "file_type": "video",
    "file_size": 104857600,
    "status": "completed",
    "processing_info": {
      "total_frames": 3600,
      "keyframes_extracted": 180,
      "scenes_detected": 8,
      "audio_segments": 12,
      "faces_detected": 3
    },
    "vectors_info": {
      "visual_vectors": 180,
      "audio_vectors": 12,
      "face_vectors": 15
    },
    "metadata": {
      "duration": 120.0,
      "resolution": "1920x1080",
      "fps": 30.0,
      "format": "mp4",
      "codec": "h264"
    },
    "created_at": "2024-01-15T10:00:00Z",
    "updated_at": "2024-01-15T10:15:00Z"
  }
}
```

### 3.3 删除文件

**端点**: `DELETE /api/v1/files/{file_id}`

**描述**: 从系统中删除指定文件的索引信息

**路径参数**：
- `file_id`: 文件ID

**响应示例**：
```json
{
  "status": "success",
  "data": {
    "file_id": "file_001",
    "deleted": true
  },
  "message": "文件索引删除成功"
}
```

## 4. 任务管理接口

### 4.1 获取任务状态

**端点**: `GET /api/v1/tasks`

**描述**: 获取当前处理任务的状态信息

**查询参数**：
- `status`: 任务状态过滤（pending/processing/completed/failed）
- `limit`: 返回数量限制（默认50）

**响应示例**：
```json
{
  "status": "success",
  "data": {
    "tasks": [
      {
        "task_id": "task_001",
        "file_id": "file_001",
        "file_path": "/home/user/videos/new_video.mp4",
        "task_type": "process_video",
        "status": "processing",
        "progress": 65,
        "started_at": "2024-01-15T10:20:00Z",
        "estimated_completion": "2024-01-15T10:25:00Z",
        "error_message": null
      }
    ],
    "queue_info": {
      "pending_tasks": 3,
      "processing_tasks": 2,
      "completed_tasks": 45,
      "failed_tasks": 1
    }
  }
}
```

### 4.2 启动处理任务

**端点**: `POST /api/v1/tasks/start`

**描述**: 启动文件处理任务

**请求参数**：
```json
{
  "task_type": "process_directory",  // 任务类型
  "parameters": {
    "directory_path": "/home/user/new_photos",
    "recursive": true,
    "file_types": ["image", "video"]
  }
}
```

**任务类型**：
- `process_file`: 处理单个文件
- `process_directory`: 处理目录
- `reindex_all`: 重新索引所有文件
- `cleanup_orphaned`: 清理孤立数据

### 4.3 停止处理任务

**端点**: `POST /api/v1/tasks/stop`

**描述**: 停止指定的处理任务

**请求参数**：
```json
{
  "task_id": "task_001"  // 可选，不指定则停止所有任务
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
  "data": {
    "general": {
      "log_level": "INFO",
      "max_concurrent_tasks": 4,
      "watch_directories": [
        "/home/user/Pictures",
        "/home/user/Videos"
      ]
    },
    "features": {
      "enable_face_recognition": true,
      "enable_audio_processing": true,
      "enable_video_processing": true
    },
    "models": {
      "clip": {
        "model_name": "openai/clip-vit-base-patch32",
        "device": "cuda",
        "batch_size": 16
      }
    }
  }
}
```

### 5.2 更新系统配置

**端点**: `PUT /api/v1/config`

**描述**: 更新系统配置（需要重启服务生效）

**请求参数**：
```json
{
  "general": {
    "log_level": "DEBUG",
    "max_concurrent_tasks": 8
  },
  "features": {
    "enable_face_recognition": false
  }
}
```

### 5.3 获取搜索配置

**端点**: `GET /api/v1/config/search`

**描述**: 获取搜索相关配置

**响应示例**：
```json
{
  "status": "success",
  "data": {
    "weights": {
      "default": {
        "clip": 0.4,
        "clap": 0.3,
        "whisper": 0.3
      },
      "visual_query": {
        "clip": 0.7,
        "clap": 0.15,
        "whisper": 0.15
      }
    },
    "results": {
      "max_results": 50,
      "similarity_threshold": 0.3,
      "enable_reranking": true
    }
  }
}
```

## 6. 人脸管理接口

### 6.1 添加人物

**端点**: `POST /api/v1/faces/persons`

**描述**: 添加新的人物到人脸库

**请求格式**: `multipart/form-data`

**请求参数**：
- `name`: 人物姓名
- `aliases`: 别名列表（JSON数组字符串，可选）
- `images`: 人脸图片文件（支持多个）

**cURL示例**：
```bash
curl -X POST "http://localhost:8000/api/v1/faces/persons" \
  -F "name=张三" \
  -F "aliases=[\"小张\", \"张总\"]" \
  -F "images=@zhangsan_1.jpg" \
  -F "images=@zhangsan_2.jpg"
```

**响应示例**：
```json
{
  "status": "success",
  "data": {
    "person_id": 1,
    "name": "张三",
    "aliases": ["小张", "张总"],
    "face_images": [
      {
        "image_id": 1,
        "image_path": "faces/zhangsan_1.jpg",
        "vector_id": "face_person_001_img_001",
        "confidence": 0.95
      }
    ]
  },
  "message": "人物添加成功"
}
```

### 6.2 获取人物列表

**端点**: `GET /api/v1/faces/persons`

**描述**: 获取人脸库中的所有人物

**查询参数**：
- `page`: 页码（默认1）
- `page_size`: 每页数量（默认20）
- `search`: 搜索关键词（可选）

**响应示例**：
```json
{
  "status": "success",
  "data": {
    "persons": [
      {
        "person_id": 1,
        "name": "张三",
        "aliases": ["小张", "张总"],
        "face_count": 3,
        "created_at": "2024-01-15T10:00:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total_pages": 1,
      "total_items": 1
    }
  }
}
```

### 6.3 删除人物

**端点**: `DELETE /api/v1/faces/persons/{person_id}`

**描述**: 从人脸库中删除指定人物

**路径参数**：
- `person_id`: 人物ID

**响应示例**：
```json
{
  "status": "success",
  "data": {
    "person_id": 1,
    "deleted": true
  },
  "message": "人物删除成功"
}
```

## 7. 监控目录接口

### 7.1 添加监控目录

**端点**: `POST /api/v1/monitoring/directories`

**描述**: 添加新的文件监控目录

**请求参数**：
```json
{
  "directory_path": "/home/user/new_photos",
  "recursive": true,
  "file_types": ["image", "video", "audio"]
}
```

**响应示例**：
```json
{
  "status": "success",
  "data": {
    "directory_id": "dir_001",
    "directory_path": "/home/user/new_photos",
    "recursive": true,
    "file_types": ["image", "video", "audio"],
    "status": "active"
  },
  "message": "监控目录添加成功"
}
```

### 7.2 获取监控目录

**端点**: `GET /api/v1/monitoring/directories`

**描述**: 获取当前所有监控目录

**响应示例**：
```json
{
  "status": "success",
  "data": {
    "directories": [
      {
        "directory_id": "dir_001",
        "directory_path": "/home/user/Pictures",
        "recursive": true,
        "file_types": ["image", "video"],
        "status": "active",
        "files_count": 1250,
        "last_scan": "2024-01-15T10:00:00Z"
      }
    ]
  }
}
```

### 7.3 删除监控目录

**端点**: `DELETE /api/v1/monitoring/directories/{directory_id}`

**描述**: 停止监控指定目录

**路径参数**：
- `directory_id`: 目录ID

## 8. 系统状态接口

### 8.1 获取系统状态

**端点**: `GET /api/v1/status`

**描述**: 获取系统整体运行状态

**响应示例**：
```json
{
  "status": "success",
  "data": {
    "system": {
      "status": "healthy",
      "uptime": "2 days, 5 hours, 30 minutes",
      "version": "1.0.0"
    },
    "services": {
      "api_server": "running",
      "embedding_engine": "running",
      "file_monitor": "running",
      "task_queue": "running"
    },
    "database": {
      "sqlite": {
        "status": "connected",
        "file_count": 1250,
        "db_size_mb": 45.2
      },
      "qdrant": {
        "status": "connected",
        "collections": {
          "image_vectors": 850,
          "video_vectors": 320,
          "audio_vectors": 180,
          "face_vectors": 45
        }
      }
    },
    "resources": {
      "cpu_usage": 25.5,
      "memory_usage": 68.2,
      "disk_usage": 45.8,
      "gpu_usage": 15.3
    },
    "statistics": {
      "total_files": 1250,
      "processed_files": 1180,
      "pending_files": 70,
      "failed_files": 0
    }
  }
}
```

### 8.2 获取性能统计

**端点**: `GET /api/v1/status/performance`

**描述**: 获取系统性能统计信息

**查询参数**：
- `period`: 统计周期（hour/day/week，默认day）

**响应示例**：
```json
{
  "status": "success",
  "data": {
    "period": "day",
    "statistics": {
      "search_requests": 156,
      "avg_search_time_ms": 245,
      "files_processed": 45,
      "avg_processing_time_s": 12.5,
      "error_rate": 0.02
    },
    "timeline": [
      {
        "timestamp": "2024-01-15T00:00:00Z",
        "search_requests": 12,
        "avg_search_time_ms": 230
      }
    ]
  }
}
```

## 9. 错误码参考

### 9.1 通用错误码

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| INVALID_PARAMETER | 400 | 请求参数无效 |
| MISSING_PARAMETER | 400 | 缺少必需参数 |
| RESOURCE_NOT_FOUND | 404 | 资源不存在 |
| INTERNAL_ERROR | 500 | 内部服务器错误 |
| SERVICE_UNAVAILABLE | 503 | 服务不可用 |

### 9.2 业务错误码

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| FILE_NOT_FOUND | 404 | 文件不存在 |
| FILE_PROCESSING_FAILED | 500 | 文件处理失败 |
| UNSUPPORTED_FILE_TYPE | 400 | 不支持的文件类型 |
| SEARCH_TIMEOUT | 408 | 搜索超时 |
| FACE_DETECTION_FAILED | 500 | 人脸检测失败 |
| DUPLICATE_PERSON | 409 | 人物已存在 |

## 10. SDK和示例

### 10.1 Python SDK示例

```python
import requests
import json

class MSearchClient:
    def __init__(self, base_url="http://localhost:8000/api/v1"):
        self.base_url = base_url
    
    def search(self, query, modality="smart", top_k=10):
        """执行搜索"""
        url = f"{self.base_url}/search"
        data = {
            "query": query,
            "modality": modality,
            "top_k": top_k
        }
        response = requests.post(url, json=data)
        return response.json()
    
    def upload_image_search(self, image_path, top_k=10):
        """上传图片搜索"""
        url = f"{self.base_url}/search/image"
        with open(image_path, 'rb') as f:
            files = {'image': f}
            data = {'top_k': top_k}
            response = requests.post(url, files=files, data=data)
        return response.json()
    
    def add_person(self, name, image_paths, aliases=None):
        """添加人物到人脸库"""
        url = f"{self.base_url}/faces/persons"
        files = [('images', open(path, 'rb')) for path in image_paths]
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

# 文本搜索
result = client.search("美丽的风景", "text_to_image")
print(f"找到 {len(result['data']['results'])} 个结果")

# 图片搜索
result = client.upload_image_search("query_image.jpg")

# 添加人物
result = client.add_person("张三", ["face1.jpg", "face2.jpg"], ["小张", "张总"])
```

### 10.2 JavaScript SDK示例

```javascript
class MSearchClient {
    constructor(baseUrl = 'http://localhost:8000/api/v1') {
        this.baseUrl = baseUrl;
    }
    
    async search(query, modality = 'smart', topK = 10) {
        const response = await fetch(`${this.baseUrl}/search`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query: query,
                modality: modality,
                top_k: topK
            })
        });
        return await response.json();
    }
    
    async uploadImageSearch(imageFile, topK = 10) {
        const formData = new FormData();
        formData.append('image', imageFile);
        formData.append('top_k', topK);
        
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
client.search('会议场景', 'text_to_video')
    .then(result => {
        console.log(`找到 ${result.data.results.length} 个结果`);
    });
```

这个API文档提供了完整的接口说明，包括请求格式、响应格式、错误处理和使用示例，方便开发者集成和使用msearch系统。