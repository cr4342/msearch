# msearch CLI 工具使用指南

## 简介

msearch CLI 工具是一个命令行界面，用于测试和调试 msearch 系统。它封装了所有 API 接口，提供方便的命令行访问方式。

## 安装

确保已安装 Python 3.8+ 和 requests 库：

```bash
pip install requests
```

## 使用方法

### 基本语法

```bash
python src/cli.py [选项] <命令> [子命令] [参数]
```

### 选项

- `--url`: API 服务器 URL（默认：http://localhost:8000）

### 命令

#### 1. 健康检查

检查系统各组件是否正常运行。

```bash
python src/cli.py health
```

**输出示例**：
```
============================================================
健康检查
============================================================
状态: healthy

组件状态:
  - database: ok
  - vector_store: ok
  - embedding_engine: ok
  - task_manager: ok

✓ 系统运行正常
```

#### 2. 系统信息

查看系统配置信息。

```bash
python src/cli.py info
```

**输出示例**：
```
============================================================
系统信息
============================================================
状态: ok

配置信息:
  - model: OFA-Sys/chinese-clip-vit-large-patch14-336px
  - device: cpu
  - embedding_dim: 768
```

#### 3. 向量统计

查看向量数据库统计信息。

```bash
python src/cli.py vector-stats
```

**输出示例**：
```
============================================================
向量统计
============================================================
表名: unified_vectors
总向量数: 14
向量维度: 768
索引类型: ivf
```

#### 4. 搜索

##### 4.1 文本搜索

使用文本查询搜索文件。

```bash
python src/cli.py search text "查询文本" [--top-k 数量]
```

**示例**：
```bash
python src/cli.py search text "老虎"
python src/cli.py search text "风景" --top-k 10
```

##### 4.2 图像搜索

使用图像文件搜索相似文件。

```bash
python src/cli.py search image <图像路径> [--top-k 数量]
```

**示例**：
```bash
python src/cli.py search image test.jpg
python src/cli.py search image /path/to/image.jpg --top-k 5
```

##### 4.3 音频搜索

使用音频文件搜索相似文件。

```bash
python src/cli.py search audio <音频路径> [--top-k 数量]
```

**示例**：
```bash
python src/cli.py search audio test.wav
python src/cli.py search audio /path/to/audio.wav --top-k 5
```

#### 5. 任务管理

##### 5.1 任务统计

查看任务统计信息。

```bash
python src/cli.py task stats
```

**输出示例**：
```
============================================================
任务统计
============================================================

总体统计:
  - 总任务数: 0
  - 待处理: 0
  - 运行中: 0
  - 已完成: 0
  - 失败: 0
  - 已取消: 0

并发数: 4

资源使用:
  - CPU: 10.2%
  - 内存: 69.4%
  - GPU: 0.0%
```

##### 5.2 列出任务

查看任务列表。

```bash
python src/cli.py task list [--status 状态] [--type 类型] [--limit 数量]
```

**示例**：
```bash
# 列出所有任务
python src/cli.py task list

# 只列出运行中的任务
python src/cli.py task list --status running

# 只列出图像预处理任务
python src/cli.py task list --type image_preprocess

# 限制返回数量
python src/cli.py task list --limit 10
```

##### 5.3 获取任务详情

查看特定任务的详细信息。

```bash
python src/cli.py task get <任务ID>
```

**示例**：
```bash
python src/cli.py task get abc123-def456
```

##### 5.4 取消任务

取消指定的任务。

```bash
python src/cli.py task cancel <任务ID>
```

**示例**：
```bash
python src/cli.py task cancel abc123-def456
```

##### 5.5 更新任务优先级

更新任务的优先级。

```bash
python src/cli.py task priority <任务ID> <优先级>
```

**示例**：
```bash
# 将任务优先级设置为最高（0）
python src/cli.py task priority abc123-def456 0
```

**优先级说明**：
- 0: 最高优先级
- 1-5: 高优先级
- 6-8: 中等优先级
- 9-11: 低优先级

##### 5.6 取消所有任务

取消所有待处理的任务。

```bash
python src/cli.py task cancel-all [--cancel-running]
```

**示例**：
```bash
# 只取消待处理的任务
python src/cli.py task cancel-all

# 同时取消正在运行的任务
python src/cli.py task cancel-all --cancel-running
```

##### 5.7 按类型取消任务

取消特定类型的所有任务。

```bash
python src/cli.py task cancel-by-type <任务类型> [--cancel-running]
```

**示例**：
```bash
# 取消所有图像预处理任务
python src/cli.py task cancel-by-type image_preprocess

# 取消所有视频预处理任务（包括正在运行的）
python src/cli.py task cancel-by-type video_preprocess --cancel-running
```

**常见任务类型**：
- `file_scan`: 文件扫描
- `image_preprocess`: 图像预处理
- `video_preprocess`: 视频预处理
- `audio_preprocess`: 音频预处理
- `file_embed_image`: 图像向量化
- `file_embed_video`: 视频向量化
- `file_embed_audio`: 音频向量化
- `thumbnail_generate`: 缩略图生成
- `preview_generate`: 预览生成

## 完整使用示例

### 场景 1: 系统健康检查

```bash
# 1. 检查系统健康状态
python src/cli.py health

# 2. 查看系统信息
python src/cli.py info

# 3. 查看向量统计
python src/cli.py vector-stats
```

### 场景 2: 搜索测试

```bash
# 1. 文本搜索
python src/cli.py search text "老虎"

# 2. 图像搜索
python src/cli.py search image testdata/test_image.jpg

# 3. 音频搜索
python src/cli.py search audio testdata/test_audio.wav
```

### 场景 3: 任务管理

```bash
# 1. 查看任务统计
python src/cli.py task stats

# 2. 列出所有任务
python src/cli.py task list

# 3. 列出运行中的任务
python src/cli.py task list --status running

# 4. 取消所有待处理任务
python src/cli.py task cancel-all

# 5. 取消特定类型的任务
python src/cli.py task cancel-by-type image_preprocess
```

### 场景 4: 任务优先级调整

```bash
# 1. 列出所有任务
python src/cli.py task list

# 2. 将重要任务提升到最高优先级
python src/cli.py task priority <任务ID> 0

# 3. 查看任务详情
python src/cli.py task get <任务ID>
```

## 常见问题

### 1. 连接失败

**错误信息**：
```
错误: 无法连接到API服务器 (http://localhost:8000)
请确保API服务器正在运行: python3 src/api_server.py
```

**解决方案**：
```bash
# 启动 API 服务器
python3 src/api_server.py

# 或使用自定义 URL
python src/cli.py health --url http://localhost:8080
```

### 2. 文件不存在

**错误信息**：
```
错误: 文件不存在: test.jpg
```

**解决方案**：
```bash
# 检查文件路径是否正确
ls -la test.jpg

# 使用绝对路径
python src/cli.py search image /full/path/to/image.jpg
```

### 3. 任务不存在

**错误信息**：
```
错误: HTTP 404
详情: 任务不存在
```

**解决方案**：
```bash
# 先列出所有任务，找到正确的任务 ID
python src/cli.py task list
```

## 高级用法

### 自定义 API 服务器 URL

如果 API 服务器运行在不同的端口或主机：

```bash
python src/cli.py --url http://192.168.1.100:8000 health
```

### 批量操作

结合 shell 脚本进行批量操作：

```bash
# 批量取消多种类型的任务
for type in image_preprocess video_preprocess audio_preprocess; do
    python src/cli.py task cancel-by-type $type
done

# 批量搜索多个关键词
for keyword in "老虎" "风景" "人物"; do
    python src/cli.py search text "$keyword"
done
```

### 日志记录

将输出保存到日志文件：

```bash
python src/cli.py task stats > task_stats.log
python src/cli.py search text "老虎" > search_results.log 2>&1
```

## 技术支持

如遇到问题，请检查：

1. API 服务器是否正在运行
2. 网络连接是否正常
3. 文件路径是否正确
4. 任务 ID 是否有效

更多帮助信息：

```bash
python src/cli.py --help
python src/cli.py <命令> --help
```