# msearch多进程架构说明

## 架构概述

msearch采用多进程架构，将计算密集型任务与主应用解耦，提升系统稳定性和资源利用率。

## 进程结构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Main Process                                   │
│                              (主进程 - 1个)                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐ │
│  │  API Server  │  │  WebUI       │  │ Task Manager │  │ Config Manager │ │
│  │  (FastAPI)   │  │  (Gradio)    │  │ (调度器)      │  │ (配置管理)      │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
         ┌─────────────────────────────┼─────────────────────────────┐
         │                             │                             │
         ▼                             ▼                             ▼
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│ File Monitor        │    │ Embedding Worker    │    │ Task Worker         │
│ (文件监控进程 - 1个)  │    │ (向量化进程 - 1-N个) │    │ (任务执行进程 - 1-N) │
├─────────────────────┤    ├─────────────────────┤    ├─────────────────────┤
│ • 文件系统监控       │    │ • 模型加载/卸载      │    │ • 媒体预处理        │
│ • 目录扫描          │    │ • 向量推理          │    │ • 数据转换          │
│ • 事件通知          │    │ • 批处理优化        │    │ • 文件格式处理      │
│ • 增量更新          │    │ • GPU/CPU 管理      │    │ • 缩略图生成        │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
         │                             │                             │
         └─────────────────────────────┼─────────────────────────────┘
                                       │
                                       ▼
                    ┌───────────────────────────────────┐
                    │         Redis (本地)               │
                    │  ┌─────────────┐ ┌───────────────┐ │
                    │  │ Task Queue  │ │ Status Cache  │ │
                    │  └─────────────┘ └───────────────┘ │
                    └───────────────────────────────────┘
```

## 进程职责

### 1. 主进程 (Main Process)
- 提供 REST API 接口
- 运行 WebUI (Gradio)
- 任务调度与状态管理
- 配置管理
- 进程生命周期管理

### 2. 文件监控进程 (File Monitor Process)
- 监控配置的目录变化
- 执行目录扫描
- 检测新增/修改/删除的文件
- 发送文件事件通知

### 3. 向量化工作进程 (Embedding Worker Process)
- 加载 AI 模型
- 执行向量推理（图像、视频、音频）
- 管理 GPU/CPU 资源
- 批处理优化

### 4. 任务执行进程 (Task Worker Process)
- 执行非推理类任务
- 媒体预处理（视频切片、音频提取等）
- 文件格式转换
- 缩略图生成

## 进程间通信

### 通信方式
- **任务分发**: Redis 队列 (可靠、持久化、支持优先级)
- **状态查询**: Redis Hash (快速查询)
- **心跳检测**: Redis Key with TTL

### Redis 数据结构

```
# 任务队列
queue:tasks:pending        # 待处理任务队列 (List)
queue:tasks:processing     # 处理中任务集合 (Set)
queue:tasks:completed      # 已完成任务队列 (List, 限制长度)
queue:tasks:failed         # 失败任务队列 (List)

# 任务优先级队列
queue:tasks:priority:high    # 高优先级
queue:tasks:priority:normal  # 普通优先级  
queue:tasks:priority:low     # 低优先级

# 进程状态
process:main:status          # 主进程状态 (Hash)
process:file_monitor:status  # 文件监控进程状态
process:embedding_worker:*   # 向量化工作进程状态 (通配符)
process:task_worker:*        # 任务工作进程状态

# 任务状态
task:{task_id}:status        # 任务状态 (Hash)
task:{task_id}:result        # 任务结果 (String, JSON)
task:{task_id}:progress      # 任务进度 (String)

# 心跳检测
heartbeat:main              # 主进程心跳 (String, TTL)
heartbeat:file_monitor      # 文件监控进程心跳
heartbeat:embedding_worker:* # 向量化工作进程心跳
heartbeat:task_worker:*      # 任务工作进程心跳
```

## 启动服务

### 使用控制脚本
```bash
# 启动服务
./scripts/msearchctl start

# 停止服务
./scripts/msearchctl stop

# 重启服务
./scripts/msearchctl restart

# 查看状态
./scripts/msearchctl status
```

### 使用启动器
```bash
# 启动多进程架构
python3 scripts/multiprocess_launcher.py
```

## 依赖要求

### 系统依赖
- Python 3.8+
- Redis server

### Python依赖
- fastapi
- uvicorn
- redis
- python-multipart
- watchdog

## 配置项

### 主配置文件 (config/config.yml)
```yaml
# 进程配置
processes:
  file_monitor:
    watched_dirs: ["./testdata"]
    supported_extensions: [".jpg", ".jpeg", ".png", ".mp4", ".mp3"]
    recursive: true
    scan_interval: 300  # 秒
  embedding_worker:
    device: "cpu"  # 或 "cuda"
    batch_size: 8
    num_instances: 1  # 向量化工作进程数量
  task_worker:
    num_instances: 2  # 任务工作进程数量

# Redis配置
redis:
  host: "localhost"
  port: 6379
  db: 0
```

## 监控与调试

### 查看进程状态
```bash
# 通过CLI查看任务状态
python3 src/cli.py task stats

# 查看索引状态
python3 src/cli.py index status
```

### 日志文件
- 主进程日志: `logs/main_process.log`
- API服务日志: `logs/api_server.log`
- 子进程日志: `logs/subprocesses/`