# 部署指南

> **文档导航**: [文档索引](README.md) | [需求文档](requirements.md) | [设计文档](design.md) | [开发计划](development_plan.md) | [测试策略](test_strategy.md)

## 1. 部署概述

### 1.1 系统要求

**硬件要求**：
- **CPU**: 4核心以上，推荐8核心
- **内存**: 最低8GB，推荐16GB以上
- **存储**: 可用空间50GB以上（用于模型文件和数据存储）
- **GPU**: 可选，支持CUDA的NVIDIA显卡可显著提升性能

**软件要求**：
- **操作系统**: Windows 10/11, Ubuntu 18.04+, macOS 10.15+
- **Python**: 3.9-3.11
- **依赖库**: 详见requirements.txt

### 1.2 部署模式

| 部署模式 | 适用场景 | 优势 | 限制 |
|---------|---------|------|------|
| **单机部署** | 个人用户、小团队 | 简单易用、零配置 | 性能受限于单机 |
| **离线部署** | 内网环境、安全要求高 | 完全离线、数据安全 | 需要预下载模型 |
| **容器部署** | 云环境、微服务架构 | 标准化、易扩展 | 需要容器技术 |

## 2. 快速开始

### 2.1 一键安装脚本

**Windows用户**：
```batch
# 克隆项目
git clone https://github.com/cr4342/msearch.git
cd msearch

# 运行一键部署脚本
scripts\install_and_configure_msearch.bat
```

**Linux/macOS用户**：
```bash
# 克隆项目
git clone https://github.com/cr4342/msearch.git
cd msearch

# 创建虚拟环境并激活
python3 -m venv venv
source venv/bin/activate  # Linux/macOS

# 运行一键部署脚本
bash scripts/deploy_msearch.sh
```

### 2.2 手动安装步骤

#### 2.2.1 环境准备

**1. 克隆项目**：
```bash
git clone https://github.com/cr4342/msearch.git
cd msearch
```

**2. 创建虚拟环境**：
```bash
# 使用venv
python3 -m venv venv

# Windows激活
venv\Scripts\activate

# Linux/macOS激活
source venv/bin/activate
```

**3. 安装依赖**：
```bash
pip install -r requirements.txt
```

#### 2.2.2 配置初始化

**1. 复制配置文件**：
```bash
cp config/config.yml config/config.local.yml
```

**2. 编辑配置文件**：
```yaml
# config/config.local.yml
general:
  log_level: INFO
  data_dir: ./data
  watch_directories:
    - ~/Pictures      # 修改为你的图片目录
    - ~/Videos        # 修改为你的视频目录
    - ~/Documents     # 修改为你的文档目录

features:
  enable_face_recognition: true
  enable_audio_processing: true
  enable_video_processing: true
```

#### 2.2.3 启动服务

**1. 下载模型文件**：
```bash
# Linux/macOS
bash scripts/download_model_resources.sh

# Windows
scripts\download_model_resources.bat
```

**2. 初始化数据库**：
```bash
# 数据库会自动初始化，无需手动操作
```

**3. 启动应用**：
```bash
# Linux/macOS
bash scripts/start_qdrant.sh
bash scripts/start_infinity_services.sh
python3 src/api/main.py

# Windows
scripts\start_qdrant.bat
scripts\start_infinity_services.bat
python src\api\main.py
```

**4. 验证安装**：
访问 http://localhost:8000 查看API文档，或运行健康检查：
```bash
curl http://localhost:8000/health
```

## 3. 离线部署

### 3.1 离线部署准备

**1. 下载离线资源包**：
```bash
# 在有网络的环境中执行
bash scripts/download_model_resources.sh
```

**2. 打包离线部署包**：
```bash
# 创建完整的离线部署包
tar -czf msearch-offline.tar.gz msearch/ offline/
```

### 3.2 离线环境部署

**1. 解压部署包**：
```bash
tar -xzf msearch-offline.tar.gz
cd msearch/
```

**2. 设置离线模式**：
```bash
# 设置环境变量指向本地模型目录
export HF_HOME="$(pwd)/offline/models/huggingface"
export TRANSFORMERS_CACHE="$HF_HOME"
```

**3. 安装离线依赖**：
```bash
# 使用离线包安装依赖
pip install --no-index --find-links=offline/packages -r requirements.txt
```

**4. 启动离线服务**：
```bash
bash scripts/start_qdrant.sh
bash scripts/start_infinity_services.sh
python3 src/api/main.py
```

### 3.3 离线部署验证

**验证模型加载**：
```bash
python3 -c "
from src.business.embedding_engine import get_embedding_engine
engine = get_embedding_engine()
print('离线模型加载成功')
"
```

## 4. 配置详解

### 4.1 核心配置项

**基础配置**：
```yaml
general:
  log_level: INFO                    # 日志级别
  data_dir: ./data                   # 数据存储目录
  max_concurrent_tasks: 4            # 最大并发任务数
  watch_directories:                 # 监控目录列表
    - ~/Pictures
    - ~/Videos
```

**功能开关**：
```yaml
features:
  enable_face_recognition: true      # 人脸识别功能
  enable_audio_processing: true      # 音频处理功能
  enable_video_processing: true      # 视频处理功能
  enable_file_monitoring: true       # 文件监控功能
```

**模型配置**：
```yaml
models:
  clip:
    model_name: "openai/clip-vit-base-patch32"
    device: "auto"                   # auto, cpu, cuda
    batch_size: 16
  clap:
    model_name: "laion/clap-htsat-fused"
    device: "auto"
    batch_size: 8
  whisper:
    model_name: "openai/whisper-base"
    device: "auto"
    batch_size: 4
```

### 4.2 性能优化配置

**处理参数优化**：
```yaml
processing:
  # 图像处理配置
  image:
    batch_size: 32
    preprocessing:
      max_resolution: 1920           # 4K图片降采样到1080p
      output_format: "jpeg"
      jpeg_quality: 85
    model_input:
      resize_width: 224
      resize_height: 224
  
  # 视频处理配置
  video:
    batch_size: 16
    preprocessing:
      resolution_conversion:
        "4k_to_720p": true           # 4K视频转720p
        "hd_to_720p": true           # HD视频转720p
        target_resolution: 720
      encoding:
        target_codec: "h264"
        target_bitrate: 2.0
        max_fps: 30
    frame_extraction:
      short_video_interval: 2        # 短视频2秒间隔抽帧
      long_video_interval: 5         # 长视频5秒间隔抽帧
      long_video_threshold: 120      # 长短视频分界线(秒)
```

**硬件优化配置**：
```yaml
performance:
  # GPU内存管理
  gpu_memory:
    model_loading: "lazy"            # lazy(按需加载) 或 eager(预加载)
    cleanup_strategy: "auto"
    max_gpu_memory_fraction: 0.8
  
  # 批处理优化
  batch_processing:
    dynamic_batch_size: true         # 动态批大小调整
    memory_monitoring: true
  
  # 缓存配置
  cache:
    vector_cache_size: 1024          # 向量缓存大小(MB)
    model_cache_strategy: "lru"
```

### 4.3 日志配置

**多级别日志配置**：
```yaml
logging:
  level: INFO                        # 全局日志级别
  
  handlers:
    console:
      enabled: true
      level: INFO
      format: standard
    
    file:
      enabled: true
      level: DEBUG
      path: "./data/logs/msearch.log"
      max_size: "100MB"
      backup_count: 5
    
    error_file:
      enabled: true
      level: ERROR
      path: "./data/logs/error.log"
      max_size: "50MB"
      backup_count: 10
  
  # 组件特定日志级别
  loggers:
    "msearch.processors": WARNING    # 处理器日志级别
    "msearch.models": WARNING        # 模型日志级别
    "transformers": ERROR            # 第三方库日志级别
```

## 5. 数据库配置

### 5.1 SQLite配置

**基础配置**：
```yaml
database:
  sqlite:
    path: "./data/database/msearch.db"
    connection_pool_size: 10
    
    # 时间戳索引配置
    timestamp_indexing:
      enable_time_range_index: true
      enable_vector_id_index: true
      enable_modality_time_index: true
```

**数据库初始化**：
```bash
# 创建数据库表结构
# 数据库会自动初始化，无需手动操作
```

### 5.2 Qdrant配置

**嵌入式模式**：
```yaml
database:
  qdrant:
    mode: "embedded"
    embedded:
      path: "./data/database/qdrant"
      collections:
        image_collection:
          vector_size: 512
          distance: "cosine"
        video_collection:
          vector_size: 512
          distance: "cosine"
        audio_collection:
          vector_size: 512
          distance: "cosine"
        face_collection:
          vector_size: 512
          distance: "cosine"
```

**服务器模式**（可选）：
```yaml
database:
  qdrant:
    mode: "server"
    server:
      host: "localhost"
      port: 6333
      api_key: null
```

## 6. 服务管理

### 6.1 系统服务配置

**Linux systemd服务**：
```ini
# /etc/systemd/system/msearch.service
[Unit]
Description=MSearch Multimodal Search Service
After=network.target

[Service]
Type=simple
User=msearch
WorkingDirectory=/opt/msearch
Environment=PATH=/opt/msearch/venv/bin
ExecStart=/opt/msearch/venv/bin/python scripts/start_all_services.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**启用和管理服务**：
```bash
# 启用服务
sudo systemctl enable msearch
sudo systemctl start msearch

# 查看状态
sudo systemctl status msearch

# 查看日志
sudo journalctl -u msearch -f
```

**Windows服务**：
```batch
# 使用NSSM安装Windows服务
nssm install MSearch "C:\msearch\venv\Scripts\python.exe"
nssm set MSearch Arguments "C:\msearch\scripts\start_all_services.py"
nssm set MSearch AppDirectory "C:\msearch"
nssm start MSearch
```

### 6.2 进程监控

**健康检查脚本**：
```bash
#!/bin/bash
# scripts/health_check.sh

# 检查API服务
if curl -f http://localhost:8000/api/v1/status > /dev/null 2>&1; then
    echo "API服务正常"
else
    echo "API服务异常"
    exit 1
fi

# 检查数据库连接
python3 -c "
from src.storage.database import DatabaseManager
from src.storage.vector_store import VectorStore

try:
    db_manager = DatabaseManager()
    vector_store = VectorStore()
    print('数据库连接正常')
except Exception as e:
    print(f'数据库连接异常: {e}')
    exit(1)
"

echo "系统健康检查通过"
```

## 7. 性能调优

### 7.1 硬件优化

**GPU配置**：
```yaml
# 启用GPU加速
models:
  clip:
    device: "cuda"
  clap:
    device: "cuda"
  whisper:
    device: "cuda"

performance:
  gpu_memory:
    max_gpu_memory_fraction: 0.8     # 限制GPU内存使用
```

**CPU优化**：
```yaml
# CPU模式优化
general:
  max_concurrent_tasks: 8            # 根据CPU核心数调整

processing:
  image:
    batch_size: 16                   # CPU模式减小批大小
  video:
    batch_size: 8
  audio:
    batch_size: 4
```

### 7.2 内存优化

**内存使用监控**：
```python
# 内存使用监控脚本
import psutil
import time

def monitor_memory():
    process = psutil.Process()
    while True:
        memory_info = process.memory_info()
        memory_percent = process.memory_percent()
        
        print(f"内存使用: {memory_info.rss / 1024 / 1024:.1f}MB ({memory_percent:.1f}%)")
        
        if memory_percent > 80:
            print("警告: 内存使用率过高")
        
        time.sleep(60

)

if __name__ == "__main__":
    monitor_memory()
```

**内存优化配置**：
```yaml
performance:
  cache:
    vector_cache_size: 512           # 减少缓存大小
  
  batch_processing:
    dynamic_batch_size: true         # 启用动态批大小
    memory_monitoring: true          # 启用内存监控
```

## 8. 故障排除

### 8.1 常见问题

**问题1：模型下载失败**
```bash
# 症状：模型下载超时或失败
# 解决方案：
export HF_ENDPOINT=https://hf-mirror.com  # 使用镜像源
bash scripts/download_model_resources.sh --force
```

**问题2：GPU内存不足**
```yaml
# 症状：CUDA out of memory
# 解决方案：调整批大小
processing:
  image:
    batch_size: 8      # 减小批大小
  video:
    batch_size: 4
```

**问题3：时间戳精度问题**
```yaml
# 症状：时间戳精度超出±2秒要求
# 解决方案：调整时间戳配置
video:
  timestamp_processing:
    accuracy_requirement: 2.0
    overlap_buffer: 1.0
    enable_drift_correction: true
```

### 8.2 日志分析

**查看错误日志**：
```bash
# 查看最近的错误
tail -f data/logs/error.log

# 搜索特定错误
grep "timestamp" data/logs/error.log

# 分析性能日志
grep "PERF" data/logs/performance.log | tail -20
```

**日志级别调整**：
```bash
# 临时启用DEBUG日志
curl -X POST "http://localhost:8000/api/v1/config/logging" \
  -H "Content-Type: application/json" \
  -d '{"logger_name": "msearch.processors.timestamp_processor", "level": "DEBUG"}'
```

### 8.3 性能诊断

**系统资源监控**：
```bash
# CPU和内存使用
top -p $(pgrep -f "python.*main.py")

# GPU使用情况（如果有GPU）
nvidia-smi

# 磁盘使用情况
df -h data/
```

**数据库性能检查**：
```bash
# SQLite数据库大小
ls -lh data/database/msearch.db

# Qdrant集合信息
curl http://localhost:6333/collections
```

## 9. 备份和恢复

### 9.1 数据备份

**备份脚本**：
```bash
#!/bin/bash
# scripts/backup.sh

BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# 备份配置文件
cp -r config/ "$BACKUP_DIR/"

# 备份数据库
cp -r data/database/ "$BACKUP_DIR/"

# 备份日志（最近7天）
find data/logs/ -name "*.log" -mtime -7 -exec cp {} "$BACKUP_DIR/" \;

echo "备份完成: $BACKUP_DIR"
```

### 9.2 数据恢复

**恢复脚本**：
```bash
#!/bin/bash
# scripts/restore.sh

if [ -z "$1" ]; then
    echo "用法: $0 <备份目录>"
    exit 1
fi

BACKUP_DIR="$1"

# 停止服务
bash scripts/stop_all_services.sh

# 恢复配置
cp -r "$BACKUP_DIR/config/" ./

# 恢复数据库
cp -r "$BACKUP_DIR/database/" data/

# 重启服务
bash scripts/deploy_msearch.sh

echo "恢复完成"
```

## 10. 安全配置

### 10.1 访问控制

**API访问限制**：
```yaml
api:
  # 绑定地址（生产环境建议使用127.0.0.1）
  host: "127.0.0.1"
  port: 8000
  
  # CORS配置
  cors:
    allow_origins: ["http://localhost:3000"]  # 限制允许的源
    allow_methods: ["GET", "POST"]
    allow_headers: ["Content-Type", "Authorization"]
```

**文件系统权限**：
```bash
# 设置适当的文件权限
chmod 750 data/
chmod 640 config/config.yml
chmod 600 data/logs/*.log
```

### 10.2 数据安全

**敏感数据处理**：
```yaml
# 配置文件中避免明文密码
database:
  qdrant:
    server:
      api_key: "${QDRANT_API_KEY}"  # 使用环境变量
```

**数据加密**：
```bash
# 数据库文件加密（可选）
gpg --cipher-algo AES256 --compress-algo 1 --s2k-cipher-algo AES256 \
    --s2k-digest-algo SHA512 --s2k-mode 3 --s2k-count 65536 \
    --symmetric data/database/msearch.db
```

这个部署指南提供了完整的部署流程，包括快速安装、离线部署、配置优化、故障排除等各个方面，确保用户能够顺利部署和运行msearch系统。