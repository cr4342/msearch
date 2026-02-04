# 任务控制API文档

## 概述

本文档描述了msearch系统的任务控制API接口，这些接口允许用户手动控制任务的执行，包括取消任务、调整任务优先级等操作。

## API接口列表

### 1. 取消单个任务

**接口**: `POST /api/v1/tasks/{task_id}/cancel`

**描述**: 取消指定的任务

**参数**:
- `task_id` (路径参数): 任务ID

**响应示例**:
```json
{
  "success": true,
  "message": "任务已取消: task_12345"
}
```

**错误响应**:
```json
{
  "detail": "任务不存在或无法取消"
}
```

**使用示例**:
```bash
curl -X POST http://localhost:8000/api/v1/tasks/task_12345/cancel
```

---

### 2. 更新任务优先级

**接口**: `POST /api/v1/tasks/{task_id}/priority`

**描述**: 更新指定任务的优先级

**参数**:
- `task_id` (路径参数): 任务ID
- `priority` (表单参数): 新优先级（数值越小优先级越高）

**优先级说明**:
- 0-11级优先级，数值越小优先级越高
- 0: 最高优先级（搜索查询、手动操作）
- 1-5: 高优先级（向量化任务）
- 6-8: 中等优先级（预处理任务）
- 9-10: 低优先级（缩略图生成、预览生成）
- 11: 最低优先级

**响应示例**:
```json
{
  "success": true,
  "message": "任务优先级已更新: task_12345 -> 1"
}
```

**错误响应**:
```json
{
  "detail": "任务不存在"
}
```

**使用示例**:
```bash
# 将任务优先级提升到最高
curl -X POST http://localhost:8000/api/v1/tasks/task_12345/priority -d "priority=0"

# 将任务优先级降低
curl -X POST http://localhost:8000/api/v1/tasks/task_12345/priority -d "priority=10"
```

---

### 3. 取消所有任务

**接口**: `POST /api/v1/tasks/cancel-all`

**描述**: 取消所有待处理的任务

**参数**:
- `cancel_running` (表单参数, 可选): 是否取消正在运行的任务，默认为false

**响应示例**:
```json
{
  "success": true,
  "message": "已取消5个任务",
  "result": {
    "cancelled": 5,
    "failed": 0,
    "total": 5
  }
}
```

**使用示例**:
```bash
# 只取消待处理任务，不取消正在运行的任务
curl -X POST http://localhost:8000/api/v1/tasks/cancel-all -d "cancel_running=false"

# 取消所有任务，包括正在运行的任务
curl -X POST http://localhost:8000/api/v1/tasks/cancel-all -d "cancel_running=true"
```

---

### 4. 按类型取消任务

**接口**: `POST /api/v1/tasks/cancel-by-type`

**描述**: 取消指定类型的所有任务

**参数**:
- `task_type` (表单参数): 任务类型
- `cancel_running` (表单参数, 可选): 是否取消正在运行的任务，默认为false

**常见任务类型**:
- `file_scan`: 文件扫描
- `image_preprocess`: 图像预处理
- `video_preprocess`: 视频预处理
- `audio_preprocess`: 音频预处理
- `file_embed_image`: 图像向量化
- `file_embed_video`: 视频向量化
- `file_embed_audio`: 音频向量化
- `thumbnail_generate`: 缩略图生成
- `preview_generate`: 预览生成

**响应示例**:
```json
{
  "success": true,
  "message": "已取消3个image_preprocess任务",
  "result": {
    "cancelled": 3,
    "failed": 0,
    "total": 3,
    "task_type": "image_preprocess"
  }
}
```

**使用示例**:
```bash
# 取消所有图像预处理任务
curl -X POST http://localhost:8000/api/v1/tasks/cancel-by-type -d "task_type=image_preprocess"

# 取消所有视频向量化任务（包括正在运行的）
curl -X POST http://localhost:8000/api/v1/tasks/cancel-by-type -d "task_type=file_embed_video&cancel_running=true"
```

---

## 使用场景

### 场景1: 紧急停止所有任务

当系统资源紧张或需要紧急停止所有处理任务时：

```bash
curl -X POST http://localhost:8000/api/v1/tasks/cancel-all -d "cancel_running=true"
```

### 场景2: 优先处理重要文件

当需要优先处理某个重要文件时，可以将其任务的优先级提升：

```bash
# 1. 获取所有待处理任务
curl -s http://localhost:8000/api/v1/tasks?status=pending | python3 -m json.tool

# 2. 找到重要文件的任务ID，提升其优先级
curl -X POST http://localhost:8000/api/v1/tasks/task_important_file/priority -d "priority=0"
```

### 场景3: 取消特定类型的任务

当只需要取消某类任务（如缩略图生成）而不影响其他任务时：

```bash
curl -X POST http://localhost:8000/api/v1/tasks/cancel-by-type -d "task_type=thumbnail_generate"
```

---

### 5. 重试单个失败任务（新增功能 - 2024-02-04）

**接口**: `POST /api/v1/tasks/{task_id}/retry`

**描述**: 重试指定的失败任务，只有失败状态的任务才能重试

**参数**:
- `task_id` (路径参数): 要重试的任务ID

**重试逻辑**:
1. 检查任务是否存在
2. 验证任务状态必须为"failed"
3. 如果状态正确，创建新的任务实例
4. 复制原任务的配置（类型、数据、优先级等）
5. 返回新任务的ID和操作结果

**响应示例**:
```json
{
  "success": true,
  "message": "任务已重试: task_12345",
  "data": {
    "new_task_id": "task_67890"
  }
}
```

**错误响应**:
```json
{
  "detail": "任务不存在: task_12345"
}
```

```json
{
  "detail": "任务状态不是失败，无法重试: completed"
}
```

**使用示例**:
```bash
# 重试失败的任务
curl -X POST http://localhost:8000/api/v1/tasks/task_12345/retry
```

---

### 6. 批量重试失败任务（新增功能 - 2024-02-04）

**接口**: 通过WebUI界面的批量操作实现

**描述**: 重试多个选中的失败任务

**实现逻辑**:
1. 遍历选中的任务列表
2. 检查每个任务的状态，只处理失败状态的任务
3. 并行调用单个任务重试API
4. 统计成功和失败的数量
5. 生成详细的操作结果反馈

**使用场景**:
```bash
# 获取失败任务列表
curl -s "http://localhost:8000/api/v1/tasks?status=failed" | python3 -m json.tool

# 通过WebUI批量重试（推荐方式）
# 访问 http://localhost:8502 → 📋 任务管理器 → 选中失败任务 → 🔄 批量重试
```

---

## 更新日志

### 2024-02-04
- ✅ 新增任务重试功能（单个和批量）
- ✅ 新增实时进度显示功能
- ✅ 新增当前操作监控功能
- ✅ 完善任务管理器界面交互设计

### 场景4: 延后非关键任务

当需要延后非关键任务（如预览生成）以节省系统资源时：

```bash
# 降低预览生成任务的优先级
curl -X POST http://localhost:8000/api/v1/tasks/task_preview_123/priority -d "priority=10"
```

---

## 注意事项

1. **任务状态**: 只有`pending`状态的任务可以被取消。`running`状态的任务需要设置`cancel_running=true`才能取消。

2. **优先级范围**: 优先级数值范围为0-11，超出范围的值可能会被忽略。

3. **任务依赖**: 取消任务时，依赖该任务的其他任务可能会失败。建议使用`cancel-all`或`cancel-by-type`时谨慎操作。

4. **安全性**: 取消正在运行的任务可能会导致部分处理结果丢失。建议在任务完成后再取消。

5. **性能**: 批量取消任务可能会对系统性能产生短暂影响。

---

## 错误处理

所有API接口在出错时都会返回标准的HTTP错误响应：

- `404 Not Found`: 任务不存在
- `500 Internal Server Error`: 服务器内部错误

错误响应格式：
```json
{
  "detail": "错误描述信息"
}
```

---

## 相关API

以下API可以与任务控制API配合使用：

- `GET /api/v1/tasks/stats`: 获取任务统计信息
- `GET /api/v1/tasks`: 获取所有任务列表
- `GET /api/v1/tasks/{task_id}`: 获取单个任务详情

---

## 版本信息

- API版本: v1
- 文档版本: 1.0.0
- 最后更新: 2026-01-24