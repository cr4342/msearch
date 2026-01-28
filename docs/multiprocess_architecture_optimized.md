# msearch多进程架构说明（优化版）

## 架构概述

msearch采用多进程架构，将计算密集型任务与主应用解耦，提升系统稳定性和资源利用率。为了满足桌面应用"一键安装、零配置、100%离线运行"的核心需求，优化后的架构移除了Redis依赖，采用更适合桌面环境的进程间通信方案。

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
                    │        SQLite + Unix Socket      │
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

## 进程间通信（优化版）

### 通信方式
- **任务分发**: SQLite持久化队列 (可靠、持久化、支持优先级)
- **状态查询**: SQLite数据库 + 内存LRU缓存 (快速查询)
- **进程通信**: Unix Socket (Linux/macOS) / Named Pipe (Windows)
- **大文件传输**: 共享内存 (避免序列化开销)

### 任务队列替代方案 (基于persist-queue)

**实现原理**：
```python
# 使用基于SQLite的持久化队列
import persistqueue
import sqlite3
import json
import os

# 任务队列（持久化）
task_queue = persistqueue.SQLiteQueue(
    path='data/task_queue', 
    multithreading=True, 
    auto_commit=True
)

# 优先级队列（持久化）
high_priority_queue = persistqueue.SQLitePriorityQueue(
    path='data/priority_queue_high',
    multithreading=True
)
normal_priority_queue = persistqueue.SQLitePriorityQueue(
    path='data/priority_queue_normal',
    multithreading=True
)
low_priority_queue = persistqueue.SQLitePriorityQueue(
    path='data/priority_queue_low',
    multithreading=True
)
```

### 状态缓存替代方案 (SQLite + 内存LRU)

**实现原理**：
```python
from collections import OrderedDict
import sqlite3
import json
import threading

class LRUCache:
    """内存LRU缓存"""
    def __init__(self, capacity: int = 1000):
        self.capacity = capacity
        self.cache = OrderedDict()
        self.lock = threading.Lock()
    
    def get(self, key: str):
        with self.lock:
            if key in self.cache:
                # 移动到末尾，表示最近使用
                self.cache.move_to_end(key)
                return self.cache[key]
            return None
    
    def put(self, key: str, value):
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
            elif len(self.cache) >= self.capacity:
                # 删除最久未使用的项
                self.cache.popitem(last=False)
            self.cache[key] = value

class StateCache:
    """状态缓存管理器（双层设计）"""
    def __init__(self, db_path: str = 'data/state_cache.db'):
        self.db_path = db_path
        self.memory_cache = LRUCache(capacity=1000)
        self.lock = threading.Lock()
        self.init_db()
    
    def init_db(self):
        """初始化SQLite数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建状态表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS task_states (
                task_id TEXT PRIMARY KEY,
                state_data TEXT NOT NULL,
                last_updated REAL NOT NULL,
                accessed_count INTEGER DEFAULT 0
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS process_states (
                process_id TEXT PRIMARY KEY,
                state_data TEXT NOT NULL,
                last_updated REAL NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_task_state(self, task_id: str):
        """获取任务状态"""
        # 先查内存缓存
        cached = self.memory_cache.get(task_id)
        if cached:
            return cached
        
        # 内存中未找到，查数据库
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT state_data FROM task_states WHERE task_id = ?',
            (task_id,)
        )
        result = cursor.fetchone()
        
        conn.close()
        
        if result:
            state_data = json.loads(result[0])
            # 加入内存缓存
            self.memory_cache.put(task_id, state_data)
            return state_data
        
        return None
    
    def update_task_state(self, task_id: str, state_data: dict):
        """更新任务状态"""
        # 更新内存缓存
        self.memory_cache.put(task_id, state_data)
        
        # 更新数据库
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO task_states 
            (task_id, state_data, last_updated, accessed_count)
            VALUES (?, ?, ?, COALESCE((SELECT accessed_count FROM task_states WHERE task_id = ?), 0))
        ''', (task_id, json.dumps(state_data), time.time(), task_id))
        
        conn.commit()
        conn.close()
```

### 进程间通信替代方案 (Unix Socket/Named Pipe)

**实现原理**：
```python
import socket
import json
import os
import threading
from typing import Dict, Any, Optional

class LocalIPC:
    """本地进程间通信（Unix Socket/Named Pipe）"""
    
    def __init__(self, socket_path: str = '/tmp/msearch.sock'):
        self.socket_path = socket_path
        self.socket = None
        self.is_server = False
        self.lock = threading.Lock()
    
    def start_server(self):
        """启动服务器（主进程）"""
        if os.path.exists(self.socket_path):
            os.unlink(self.socket_path)
        
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.socket.bind(self.socket_path)
        self.socket.listen(5)
        self.is_server = True
        
        # 设置权限，只允许当前用户访问
        os.chmod(self.socket_path, 0o600)
    
    def connect_client(self):
        """连接服务器（子进程）"""
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.socket.connect(self.socket_path)
    
    def send_message(self, message: Dict[str, Any]) -> bool:
        """发送消息"""
        try:
            serialized = json.dumps(message) + '\n'
            self.socket.send(serialized.encode('utf-8'))
            return True
        except Exception as e:
            print(f"发送消息失败: {e}")
            return False
    
    def receive_message(self, timeout: int = 1) -> Optional[Dict[str, Any]]:
        """接收消息"""
        try:
            self.socket.settimeout(timeout)
            data = self.socket.recv(4096).decode('utf-8').strip()
            if data:
                return json.loads(data)
        except socket.timeout:
            return None
        except Exception as e:
            print(f"接收消息失败: {e}")
            return None
        return None
```

### SQLite数据结构设计

```
# 任务队列表
CREATE TABLE tasks (
    id TEXT PRIMARY KEY,
    data TEXT NOT NULL,
    priority INTEGER DEFAULT 0,
    status TEXT DEFAULT 'pending', -- pending, processing, completed, failed
    created_at REAL NOT NULL,
    started_at REAL,
    completed_at REAL,
    worker_id TEXT,
    result TEXT,
    error TEXT,
    sender TEXT,
    sender_type TEXT
);

# 进程状态表
CREATE TABLE process_states (
    process_id TEXT PRIMARY KEY,
    process_type TEXT NOT NULL,
    status TEXT DEFAULT 'running',
    pid INTEGER,
    heartbeat REAL,
    created_at REAL NOT NULL,
    last_updated REAL NOT NULL
);

# 任务状态缓存表（内存LRU缓存的持久化层）
CREATE TABLE task_states (
    task_id TEXT PRIMARY KEY,
    state_data TEXT NOT NULL,
    last_updated REAL NOT NULL,
    accessed_count INTEGER DEFAULT 0
);
```

## 启动服务

### 使用控制脚本
```bash
# 启动服务（优化版，无需Redis）
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
# 启动多进程架构（优化版）
python3 scripts/multiprocess_launcher.py
```

## 依赖要求（优化版）

### 系统依赖
- Python 3.8+ （无需Redis）

### Python依赖
- fastapi
- uvicorn
- persist-queue  # 替代Redis，基于SQLite的持久化队列
- python-multipart
- watchdog
- psutil  # 进程管理

## 配置项（优化版）

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

# IPC配置（优化版）
ipc:
  # 任务队列配置
  task_queue:
    path: "data/task_queue"  # SQLite队列路径
    max_size: 10000  # 最大队列长度
    auto_commit: true
  
  # 状态缓存配置
  state_cache:
    path: "data/state_cache.db"  # SQLite缓存路径
    memory_capacity: 1000  # 内存LRU缓存容量
    cleanup_interval: 3600  # 清理间隔（秒）
  
  # 本地通信配置
  local_ipc:
    socket_path: "/tmp/msearch.sock"  # Unix Socket路径
    timeout: 30  # 通信超时（秒）
```

## 性能优化

### 启动时间优化
- 移除Redis启动时间（2-3秒）
- 应用启动时间控制在3秒以内
- SQLite连接池复用

### 内存占用优化
- 移除Redis额外的150-200MB内存占用
- 内存LRU缓存容量可配置
- 数据库连接池大小可配置

### 离线运行优化
- 100%本地运行，无需网络依赖
- 一键安装，零配置
- 单点故障风险极低

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

## 升级指南

### 从旧版升级
1. 停止旧版服务
2. 安装备用依赖：`pip install persist-queue`
3. 迁移任务队列数据（可选）
4. 启动新版服务

### 兼容性
- 保持API接口不变
- 保持配置文件结构兼容
- 任务数据格式保持一致
