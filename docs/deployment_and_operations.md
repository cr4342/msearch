# msearch 部署配置指南

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

**Linux/macOS用户**：
```bash
# 克隆项目
git clone https://github.com/cr4342/msearch.git
cd msearch

# 创建虚拟环境并激活
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate  # Windows

# 运行一键部署脚本
bash scripts/deploy_msearch.sh
```

**Windows用户**：
```batch
# 克隆项目
git clone https://github.com/cr4342/msearch.git
cd msearch

# 运行一键部署脚本
scripts\install_and_configure_msearch.bat
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

# Linux/macOS激活
source venv/bin/activate

# Windows激活
venv\Scripts\activate
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
# 启动Qdrant服务
bash scripts/start_qdrant.sh

# 启动Infinity服务
bash scripts/start_infinity_services.sh

# 启动API服务
python3 src/api/main.py
```

**4. 验证安装**：
访问 http://localhost:8000 查看API文档，或运行健康检查：
```bash
curl http://localhost:8000/health
```

## 3. 离线部署

### 3.1 离线部署准备

**1. 下载离线资源**：
```bash
# 在有网络的环境中执行
bash scripts/download_model_resources.sh
```

### 3.2 离线环境部署

**1. 传输部署包**：
将整个项目目录传输到离线环境。

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
# 启动Qdrant服务
bash scripts/start_qdrant.sh

# 启动Infinity服务
bash scripts/start_infinity_services.sh

# 启动API服务
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
  enable_face_recognition: true      # 启用人脸识别
  enable_audio_processing: true      # 启用音频处理
  enable_video_processing: true      # 启用视频处理
  enable_file_monitoring: true       # 启用文件监控
```

### 4.2 AI模型配置

**CLIP模型配置**：
```yaml
models:
  clip:
    model_name: "sentence-transformers/clip-ViT-B-32"
    device: "auto"  # auto, cpu, cuda
    batch_size: 16
```

**CLAP模型配置**：
```yaml
  clap:
    model_name: "sentence-transformers/clap-htsat-unfused"
    device: "auto"
    batch_size: 8
```

**Whisper模型配置**：
```yaml
  whisper:
    model_name: "sentence-transformers/all-MiniLM-L6-v2"
    device: "auto"
    batch_size: 4
```

### 4.3 数据库配置

**SQLite配置**：
```yaml
database:
  sqlite:
    path: "./data/database/msearch.db"
    connection_pool_size: 10
```

**Qdrant配置**：
```yaml
  qdrant:
    host: "localhost"
    port: 6333
    mode: "embedded"
    embedded:
      path: "./data/database/qdrant"
```

### 4.4 性能优化配置

**GPU内存管理**：
```yaml
performance:
  gpu_memory:
    model_loading: "lazy"
    max_gpu_memory_fraction: 0.8
```

**批处理优化**：
```yaml
  batch_processing:
    dynamic_batch_size: true
    memory_monitoring: true
```

## 5. 服务管理

### 5.1 启动服务

```bash
# 启动所有服务
bash scripts/deploy_msearch.sh

# 启动单个服务
bash scripts/start_qdrant.sh
bash scripts/start_infinity_services.sh
python3 src/api/main.py
```

### 5.2 停止服务

```bash
# 停止所有服务
bash scripts/stop_all_services.sh

# 停止单个服务
bash scripts/stop_qdrant.sh
bash scripts/stop_infinity_services.sh
# Ctrl+C 停止API服务
```

### 5.3 服务健康检查

```bash
# 检查Qdrant服务
curl http://localhost:6333/health

# 检查Infinity服务
curl http://localhost:7997/health
curl http://localhost:7998/health
curl http://localhost:7999/health

# 检查API服务
curl http://localhost:8000/health
```

## 6. 故障排除

### 6.1 常见问题

**1. 模型加载失败**：
```bash
# 检查模型文件是否存在
ls -la offline/models/

# 重新下载模型
bash scripts/download_model_resources.sh --force
```

**2. 服务启动失败**：
```bash
# 检查端口占用
lsof -i :6333
lsof -i :7997
lsof -i :8000

# 杀死占用进程
kill -9 <PID>
```

**3. 内存不足**：
```bash
# 降低并发任务数
# 在 config.yml 中设置:
general:
  max_concurrent_tasks: 2
```

### 6.2 日志查看

```bash
# 查看主日志
tail -f data/logs/msearch.log

# 查看错误日志
tail -f data/logs/error.log

# 查看性能日志
tail -f data/logs/performance.log
```

## 7. 安全配置

### 7.1 API安全

```yaml
api:
  # CORS配置
  cors:
    allow_origins: ["http://localhost:3000"]  # 限制来源
    allow_methods: ["GET", "POST"]
    allow_headers: ["Authorization", "Content-Type"]
```

### 7.2 数据安全

```yaml
# 数据库加密配置
database:
  sqlite:
    path: "./data/database/msearch.db"
    encryption_key: "your-secret-key"  # 数据库加密密钥
```

## 8. 性能调优

### 8.1 硬件优化

**GPU配置**：
```yaml
models:
  clip:
    device: "cuda:0"  # 指定GPU设备
    batch_size: 32    # 增大批处理大小
```

**内存优化**：
```yaml
performance:
  gpu_memory:
    max_gpu_memory_fraction: 0.7  # 限制GPU内存使用率
```

### 8.2 并发配置

```yaml
general:
  max_concurrent_tasks: 8  # 增加并发任务数
```

## 9. 监控和维护

### 9.1 系统监控

```bash
# 查看系统资源使用情况
htop
nvidia-smi
```

### 9.2 日志轮转

```yaml
logging:
  handlers:
    file:
      max_size: "100MB"    # 日志文件最大大小
      backup_count: 5      # 保留备份数量
```

### 9.3 数据备份

```bash
# 备份数据库
cp data/database/msearch.db data/database/msearch.db.backup.$(date +%Y%m%d)

# 备份向量数据库
cp -r data/database/qdrant data/database/qdrant.backup.$(date +%Y%m%d)
```

## 10. 升级指南

### 10.1 版本升级

```bash
# 拉取最新代码
git pull origin main

# 更新依赖
pip install -r requirements.txt

# 重启服务
bash scripts/stop_all_services.sh
bash scripts/deploy_msearch.sh
```

### 10.2 配置迁移

```bash
# 备份当前配置
cp config/config.yml config/config.yml.backup.$(date +%Y%m%d)

# 合并新配置
# 手动对比新旧配置文件，合并必要的更改
```

## 11. 常用命令

### 11.1 开发命令

```bash
# 运行测试
python3 tests/run_tests.py

# 生成API文档
python3 -m pydoc src.api.main > docs/api_reference.md

# 代码格式化
black src/
```

### 11.2 运维命令

```bash
# 查看服务状态
ps aux | grep msearch

# 查看端口监听
netstat -tlnp | grep :8000

# 清理临时文件
rm -rf data/temp/*
```

## 12. 联系支持

如遇到部署问题，请通过以下方式联系技术支持：

- GitHub Issues: https://github.com/cr4342/msearch/issues
- 邮件支持: support@msearch.example.com
- 社区论坛: https://community.msearch.example.com