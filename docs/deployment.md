# 部署与运维文档

**文档版本**：v2.0  
**最后更新**：2026-01-23  
**对应设计文档**：[design.md](./design.md)  

---

> **文档定位**：本文档是 [design.md](./design.md) 的补充文档，详细展开第 5 部分"部署与运维"的内容。

**相关文档**：
- [design.md](./design.md) - 主设计文档
- [testing.md](./testing.md) - 测试策略文档
- [service_evolution.md](./service_evolution.md) - 服务化演进设计（容器化部署）

---

## 概述

本文档详细描述了 msearch 系统的部署、运维、监控和故障排查等内容。

**系统架构**：单机部署，所有服务在同一台机器上运行  
**部署模式**：本地部署（桌面应用）  
**运维复杂度**：低（单机运维）  

**快速开始**：  
- 一键安装：`bash scripts/install.sh`  
- 一键启动：`bash scripts/run.sh`  
- 详细指南：[QUICKSTART.md](../QUICKSTART.md)  

---

## 环境准备

### 2.1 硬件要求

**最低配置**：
- **CPU**：Intel Core i5-8400 / AMD Ryzen 5 2600（6核及以上）
- **内存**：16GB RAM
- **GPU**：NVIDIA GPU with 8GB VRAM（支持 CUDA 11.0+）
- **存储**：50GB 可用空间（SSD 推荐）
- **网络**：无特殊要求（首次安装需要下载模型）

**推荐配置**：
- **CPU**：Intel Core i7-10700K / AMD Ryzen 7 3700X（8核及以上）
- **内存**：32GB RAM
- **GPU**：NVIDIA RTX 3080 / RTX 4070（10GB+ VRAM）
- **存储**：200GB+ SSD（推荐 NVMe SSD）
- **网络**：100Mbps+ 带宽（用于模型下载）

**硬件检测**：
系统在安装时会自动检测硬件配置，根据硬件情况选择合适的模型。硬件检测脚本位于：`src/core/hardware/hardware_detector.py`

**硬件检测项**：
- CPU 核心数和频率
- 内存大小和可用内存
- GPU 型号、显存大小和 CUDA 支持情况
- 磁盘空间和类型
- 网络带宽（可选）

### 2.2 软件要求

**操作系统**：
- **Windows**：Windows 10 64-bit（1909+）或 Windows 11
- **macOS**：macOS 11.0+（Big Sur）或更高版本
- **Linux**：Ubuntu 20.04+ / Debian 11+ / CentOS 8+（64位）

**Python 环境**：
- **Python 版本**：3.9 - 3.11（推荐 3.10）
- **pip 版本**：21.0+（推荐 23.0+）
- **虚拟环境**：推荐使用 `venv` 或 `conda`

**依赖库**：
```bash
# 核心依赖
pip install torch torchvision torchaudio  # PyTorch（根据 CUDA 版本选择）
pip install infinity-emb  # Infinity 框架
pip install lancedb  # LanceDB 向量数据库
pip install sqlalchemy  # SQLite ORM
pip install fastapi uvicorn  # API 服务器
pip install python-multipart  # 文件上传支持
pip install watchdog  # 文件监控
pip install pillow  # 图像处理
pip install opencv-python  # 视频处理
pip install pydub  # 音频处理
pip install pyyaml  # YAML 配置文件
pip install loguru  # 日志库
pip install pydantic  # 数据验证
pip install tqdm  # 进度条

# 可选依赖（用于特定功能）
pip install ffmpeg-python  # FFmpeg 集成（视频处理）
pip install librosa  # 音频分析
pip install matplotlib  # 可视化（测试用）
```

**FFmpeg 安装**：
视频处理需要 FFmpeg，需单独安装：
- **Windows**：从 [FFmpeg 官网](https://ffmpeg.org/) 下载，添加到 PATH
- **macOS**：`brew install ffmpeg`
- **Linux**：`sudo apt install ffmpeg`（Ubuntu/Debian）或 `sudo dnf install ffmpeg`（CentOS/RHEL）

### 2.3 CUDA 环境配置

**CUDA 版本**：11.0 - 12.0（推荐 11.8）  
**cuDNN 版本**：8.0+（与 CUDA 版本匹配）  

**安装步骤**：
1. 下载并安装 NVIDIA 显卡驱动（版本 450.80.02+）
2. 下载并安装 CUDA Toolkit（推荐 11.8）
3. 下载并安装 cuDNN（与 CUDA 版本匹配）
4. 配置环境变量：
   ```bash
   # Linux/macOS
   export PATH=/usr/local/cuda-11.8/bin:$PATH
   export LD_LIBRARY_PATH=/usr/local/cuda-11.8/lib64:$LD_LIBRARY_PATH
   
   # Windows（系统环境变量）
   # PATH 添加：C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8\bin
   # PATH 添加：C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8\libnvvp
   ```

**验证 CUDA 安装**：
```bash
# 检查 CUDA 版本
nvcc --version

# 检查 GPU 状态
nvidia-smi

# 验证 PyTorch CUDA 支持
python -c "import torch; print(torch.cuda.is_available())"
```

---

## 安装步骤

### 3.1 快速安装（推荐）

**一键安装脚本**：
```bash
# 运行安装脚本（自动完成所有配置）
bash scripts/install.sh
```

安装脚本会自动完成：
1. ✅ 检查Python版本（需要3.8+）
2. ✅ 创建虚拟环境
3. ✅ 安装所有Python依赖
4. ✅ 检测硬件配置（CPU/GPU/内存）
5. ✅ 下载AI模型（自动使用国内镜像）
6. ✅ 配置离线模式
7. ✅ 运行单元测试

**安装完成后**：
```bash
# 一键启动应用
bash scripts/run.sh
```

### 3.2 手动安装

**克隆代码仓库**：
```bash
git clone https://github.com/your-username/msearch.git
cd msearch
```

**创建虚拟环境**：
```bash
# 使用 venv
python -m venv venv

# 激活虚拟环境
# Linux/macOS
source venv/bin/activate
# Windows
venv\Scripts\activate
```

**安装依赖**：
```bash
# 安装基础依赖
pip install -r requirements.txt

# 安装可选依赖（用于视频处理等功能）
pip install -r requirements/optional.txt
```

**下载模型**：
```bash
# 方法 1：通过安装脚本自动下载
python scripts/setup_models.py setup

# 方法 2：手动下载（使用国内镜像）
export HF_ENDPOINT=https://hf-mirror.com
python -m huggingface-cli download \
    --resume-download \
    --local-dir-use-symlinks False \
    OFA-Sys/chinese-clip-vit-base-patch16 \
    --local-dir data/models/chinese-clip-vit-base-patch16

python -m huggingface-cli download \
    --resume-download \
    --local-dir-use-symlinks False \
    laion/clap-htsat-unfused \
    --local-dir data/models/clap-htsat-unfused
```

**配置文件**：
```bash
# 复制配置文件模板
cp config/config.yml.example config/config.yml

# 编辑配置文件（根据实际情况修改）
```

### 3.4 Docker 部署（可选）

**构建 Docker 镜像**：
```bash
docker build -t msearch:latest .
```

**运行 Docker 容器**：
```bash
docker run -d \
  --name msearch \
  --gpus all \
  -p 8000:8000 \
  -p 5173:5173 \
  -v /path/to/data:/app/data \
  -v /path/to/models:/app/data/models \
  -v /path/to/monitor:/data/monitor \
  --restart unless-stopped \
  msearch:latest
```

**Docker Compose**：
```yaml
# docker-compose.yml
version: '3.8'

services:
  msearch:
    image: msearch:latest
    container_name: msearch
    restart: unless-stopped
    ports:
      - "8000:8000"  # API 端口
      - "5173:5173"  # Web UI 端口
    volumes:
      - ./data:/app/data
      - ./data/models:/app/data/models
      - /path/to/monitor:/data/monitor
    environment:
      - PYTHONUNBUFFERED=1
      - MSEARCH_CONFIG=/app/config/config.yml
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

**启动命令**：
```bash
docker-compose up -d
```

### 3.3 安装验证

**检查环境**：
```bash
# 检查 Python 版本
python --version

# 检查依赖版本
pip list | grep -E "torch|infinity|lancedb|fastapi"

# 检查 GPU 可用性
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}'); print(f'GPU count: {torch.cuda.device_count()}'); print(f'GPU name: {torch.cuda.get_device_name(0)}')"

# 检查 FFmpeg
ffmpeg -version
```

**检查模型**：
```bash
# 检查模型完整性
python scripts/setup_models.py check

# 预期输出：
# ✓ chinese-clip-vit-base-patch16: 1436.78 MB (完整)
# ✓ clap-htsat-unfused: 589.28 MB (完整)
```

**运行测试**：
```bash
# 运行单元测试
pytest tests/unit/ -v

# 运行集成测试
pytest tests/integration/ -v

# 运行特定测试
pytest tests/unit/test_config.py -v
pytest tests/unit/test_embedding_engine.py -v
```

**启动服务**：
```bash
# 启动 API 服务器
python src/api_server.py

# 或使用启动脚本
bash scripts/run.sh
```

**验证服务**：
```bash
# 检查 API 服务是否正常
curl http://localhost:8000/health

# 检查系统信息
curl http://localhost:8000/api/v1/system/info

# 检查模型信息
curl http://localhost:8000/api/v1/models/info
```

---

## 启动与停止

### 4.1 快速启动（推荐）

**一键启动脚本**：
```bash
# 启动完整应用（API服务 + WebUI）
bash scripts/run.sh
```

启动后：
- 🌐 浏览器会自动打开 WebUI: http://localhost:8080
- 📡 API服务运行在: http://localhost:8000
- 📚 API文档: http://localhost:8000/docs

### 4.2 手动启动

**启动顺序**：
1. 激活虚拟环境
2. 设置离线环境变量
3. 启动API服务
4. 启动WebUI（可选）

**启动命令**：
```bash
# 方式 1：启动完整服务（API + WebUI）
bash scripts/run.sh

# 方式 2：仅启动 API 服务器
source venv/bin/activate
export HF_HOME="data/models"
export TRANSFORMERS_OFFLINE=1
export HF_DATASETS_OFFLINE=1
export HF_HUB_OFFLINE=1
python src/api_server.py

# 方式 3：仅启动 PySide6 桌面UI
source venv/bin/activate
python src/ui/ui_launcher.py

# 方式 4：使用 uvicorn（生产环境）
source venv/bin/activate
uvicorn src.api_server:app --host 0.0.0.0 --port 8000 --workers 1 --log-level info

# 方式 5：使用 nohup（后台运行）
source venv/bin/activate
nohup python src/api_server.py > /dev/null 2>&1 &
```

### 4.3 停止服务

**停止命令**：
```bash
# 方式 1：Ctrl+C（前台运行）
Ctrl+C

# 方式 2：kill 命令（后台运行）
ps aux | grep "python src/api_server.py" | grep -v grep | awk '{print $2}' | xargs kill

# 方式 3：停止所有相关进程
pkill -f "python src/api_server.py"
pkill -f "python -m http.server"  # WebUI

# 方式 4：使用脚本停止（如果有）
bash scripts/stop.sh
```

**停止日志**：
```
2026-01-19 18:00:00 | INFO | api_server:shutdown:125 | Received shutdown signal
2026-01-19 18:00:00 | INFO | api_server:shutdown:128 | Stopping API server
2026-01-19 18:00:00 | INFO | file_monitor:stop:42 | Stopping file monitor
2026-01-19 18:00:00 | INFO | task_manager:stop:55 | Stopping task manager
2026-01-19 18:00:05 | INFO | task_manager:stop:62 | Task manager stopped (4 tasks completed, 0 pending)
2026-01-19 18:00:05 | INFO | embedding_engine:unload_model:92 | Unloading audio model
2026-01-19 18:00:05 | INFO | embedding_engine:unload_model:95 | Unloading image/video model
2026-01-19 18:00:05 | INFO | vector_store:close:45 | Closing LanceDB vector store
2026-01-19 18:00:05 | INFO | database_manager:close:45 | Closing SQLite database
2026-01-19 18:00:05 | INFO | api_server:shutdown:142 | msearch stopped successfully
```

---

## 模型管理

### 模型下载

**自动下载（推荐）**：
```bash
# 运行安装脚本时自动下载
bash scripts/install.sh
```

**手动下载**：
```bash
# 检查模型状态
python scripts/setup_models.py check

# 下载模型（跳过已存在的）
python scripts/setup_models.py setup

# 强制重新下载
python scripts/setup_models.py setup --force

# 清除模型
python scripts/setup_models.py clear
```

**使用国内镜像**：
```bash
# 设置HuggingFace镜像
export HF_ENDPOINT=https://hf-mirror.com

# 下载模型
python -m huggingface-cli download \
    --resume-download \
    --local-dir-use-symlinks False \
    OFA-Sys/chinese-clip-vit-base-patch16 \
    --local-dir data/models/chinese-clip-vit-base-patch16
```

### 模型检查

**检查模型完整性**：
```bash
python scripts/setup_models.py check
```

**输出示例**：
```
检查模型状态...
✓ chinese-clip-vit-base-patch16: 1436.78 MB (完整)
✓ clap-htsat-unfused: 589.28 MB (完整)

所有模型完整，无需下载
```

### 模型配置

**模型选择**：
```yaml
# config/config.yml
models:
  image_video_model:
    model_name: "OFA-Sys/chinese-clip-vit-base-patch16"  # 基础模型
    # model_name: "OFA-Sys/chinese-clip-vit-large-patch14-336px"  # 高精度模型
    # model_name: "SauerkrautLM/ColQwen3-1.7b-Turbo-v0.1"  # 高性能模型
    model_path: "data/models/chinese-clip-vit-base-patch16"
    embedding_dim: 512
    device: "cuda"  # cuda 或 cpu
    precision: "float16"  # float16 或 float32
    batch_size: 16
```

**硬件自适应**：
- 低配（CPU/4GB内存）：使用基础模型（512维）
- 中配（GPU/8GB内存）：使用高精度模型（1024维）
- 高配（GPU/16GB+内存）：使用高性能模型（2048维）

---

## 监控与日志

### 5.1 系统监控

**监控指标**：
- **系统资源**：CPU、内存、GPU、磁盘、网络使用情况
- **服务状态**：API 服务器、任务调度器、文件监控器状态
- **模型状态**：模型加载状态、推理速度、显存使用情况
- **数据库状态**：SQLite 和 LanceDB 连接数、查询性能
- **任务状态**：任务队列长度、执行速度、成功率
- **文件状态**：监控目录数量、文件数量、索引进度

**监控接口**：
```bash
# 系统信息
curl http://localhost:8000/api/v1/system/info

# 模型信息
curl http://localhost:8000/api/v1/models/info

# 数据库统计
curl http://localhost:8000/api/v1/database/stats

# 任务统计
curl http://localhost:8000/api/v1/tasks/stats

# 健康检查
curl http://localhost:8000/health
```

**监控脚本**：
```bash
# 实时监控 GPU 使用情况
watch -n 1 nvidia-smi

# 实时监控系统资源
htop

# 实时监控日志
tail -f data/logs/msearch.log

# 监控任务队列
watch -n 5 "curl -s http://localhost:8000/api/v1/tasks/stats | jq '.data.running'"
```

### 5.2 日志管理

**日志配置**：
```yaml
# config/config.yml
logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
  format: "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"
  rotation: "1 day"  # 日志轮转（每天）
  retention: "7 days"  # 日志保留（7天）
  compression: "zip"  # 压缩格式
```

**日志位置**：
- **主日志**：`data/logs/msearch.log`
- **错误日志**：`data/logs/msearch.error.log`
- **访问日志**：`data/logs/msearch.access.log`（API 请求日志）
- **轮转日志**：`data/logs/msearch.log.2026-01-19_10-00-00.zip`

**日志格式**：
```
2026-01-19 10:00:00 | INFO | msearch:main:12 | Starting msearch v2.0.0
2026-01-19 10:00:00 | DEBUG | config:load_config:45 | Loading configuration from config/config.yml
2026-01-19 10:00:00 | INFO | embedding_engine:load_model:65 | Loading image/video model: [配置驱动模型]
2026-01-19 10:00:15 | INFO | embedding_engine:load_model:72 | Image/video model loaded successfully
2026-01-19 10:00:23 | INFO | main:start_api:112 | Starting API server on http://0.0.0.0:8000
2026-01-19 10:00:25 | WARNING | file_monitor:on_created:78 | File too large, skipping: /path/to/large/file.mp4
2026-01-19 10:00:30 | ERROR | task_executor:execute:125 | Task failed: file_embed_video (file_id: file_123456)
```

**日志分析**：
```bash
# 查看错误日志
grep "ERROR" data/logs/msearch.log

# 查看警告日志
grep "WARNING" data/logs/msearch.log

# 查看特定模块日志
grep "embedding_engine" data/logs/msearch.log

# 查看特定时间段日志
sed -n '/2026-01-19 10:00:00/,/2026-01-19 11:00:00/p' data/logs/msearch.log

# 统计错误数量
grep -c "ERROR" data/logs/msearch.log

# 统计任务失败数量
grep -c "Task failed" data/logs/msearch.log
```

---

## 备份与恢复

### 6.1 数据备份

**备份内容**：
- **向量数据库**：`data/database/lancedb/`
- **元数据数据库**：`data/database/sqlite/msearch.db`
- **配置文件**：`config/config.yml`
- **模型文件**：`data/models/`（可选，可重新下载）
- **日志文件**：`data/logs/`（可选）

**备份脚本**：
```bash
#!/bin/bash
# scripts/backup.sh

BACKUP_DIR="/path/to/backup"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="msearch_backup_${TIMESTAMP}"

# 创建备份目录
mkdir -p ${BACKUP_DIR}

# 打包数据
tar -czf ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz \
  --exclude="*.tmp" \
  --exclude="*.temp" \
  --exclude="*.lock" \
  data/database/ \
  config/config.yml

# 可选：备份模型
# tar -czf ${BACKUP_DIR}/${BACKUP_NAME}_models.tar.gz data/models/

echo "Backup completed: ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
```

**自动备份**：
```bash
# 配置 crontab（每天凌晨 2 点备份）
0 2 * * * /path/to/msearch/scripts/backup.sh >> /var/log/msearch_backup.log 2>&1
```

### 6.2 数据恢复

**恢复步骤**：
```bash
# 1. 停止服务
python src/api/main.py stop

# 2. 备份当前数据（可选）
tar -czf data_backup_before_restore.tar.gz data/

# 3. 解压备份文件
tar -xzf /path/to/backup/msearch_backup_20260119_020000.tar.gz -C /

# 4. 验证数据
ls -la data/database/sqlite/
ls -la data/database/lancedb/

# 5. 启动服务
python src/api/main.py start
```

**恢复验证**：
```bash
# 检查数据库连接
curl http://localhost:8000/api/v1/database/stats

# 检查文件数量
curl http://localhost:8000/api/v1/files?page=1&page_size=1

# 执行测试检索
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "top_k": 5}'
```

---

## 性能优化

### 7.1 系统优化

**Linux 系统优化**：
```bash
# 1. 增加文件描述符限制
echo "* soft nofile 65536" >> /etc/security/limits.conf
echo "* hard nofile 65536" >> /etc/security/limits.conf

# 2. 增加内存映射限制
echo "vm.max_map_count=262144" >> /etc/sysctl.conf
sysctl -p

# 3. 优化磁盘 I/O
echo "vm.dirty_ratio=10" >> /etc/sysctl.conf
echo "vm.dirty_background_ratio=5" >> /etc/sysctl.conf
sysctl -p

# 4. 禁用 swap（如果有足够内存）
sudo swapoff -a
```

**Windows 系统优化**：
- 关闭虚拟内存（如果有足够内存）
- 优化 SSD（禁用磁盘碎片整理）
- 关闭不必要的后台程序
- 调整电源计划为高性能

**macOS 系统优化**：
- 关闭 Spotlight 索引（在监控目录）
- 禁用 Time Machine 自动备份（在监控目录）
- 调整电源设置为高性能

### 7.2 应用优化

**模型优化**：
```yaml
# config/config.yml
models:
  [配置驱动模型]:
    batch_size: 16  # 根据 GPU 显存调整（8-32）
    precision: "float16"  # 使用混合精度
    device: "cuda"  # 使用 GPU
  
  [配置驱动模型]:
    batch_size: 8  # 根据 GPU 显存调整（4-16）
    precision: "float16"
    device: "cuda"
```

**视频处理优化**：
```yaml
# config/config.yml
performance:
  video_processing:
    frame_interval: 10  # 增加采样间隔（减少处理时间）
    target_fps: 2  # 降低目标帧率
    max_segments_per_video: 50  # 减少最大分段数
    scene_threshold: 0.3  # 调整场景变化阈值
```

**数据库优化**：
```yaml
# config/config.yml
vector_store:
  index_type: "ivf"  # 使用 IVF 索引（适合大数据量）
  nlist: 1024  # 根据数据量调整（512-4096）

database:
  pool_size: 5  # 连接池大小
  max_overflow: 10
```

**任务调度优化**：
```yaml
# config/config.yml
task_scheduler:
  max_workers: 4  # 根据 CPU 核心数调整（2-8）
  queue_size: 1000
  retry_count: 3
  retry_delay: 5
```

### 7.3 性能监控

**性能指标**：
```bash
# 模型推理速度
# 图像：< 100ms/张
# 视频：< 500ms/秒视频
# 音频：< 1000ms/段音频

# 检索速度
# 文本检索：< 500ms
# 图像检索：< 1000ms
# 音频检索：< 1500ms

# 索引速度
# 图像：< 1 秒/张
# 视频：< 30 秒/分钟视频
# 音频：< 10 秒/分钟音频

# 内存使用
# 模型加载：< 10GB
# 运行时：< 16GB

# GPU 显存使用
# 模型：< 8GB
# 运行时：< 10GB
```

**性能测试**：
```bash
# 运行基准测试
pytest tests/benchmark/ -v

# 生成性能报告
python scripts/run_benchmark.py --output data/benchmark/report.json

# 查看性能报告
cat data/benchmark/report.json | jq '.performance'
```

---

## 故障排查

### 8.1 常见问题

**问题 1：模型加载失败**
```
ERROR | embedding_engine:load_model:75 | Failed to load model: [配置驱动模型]
Error: CUDA out of memory
```

**解决方案**：
- 降低 batch_size（配置文件）
- 使用 float32 精度（配置文件）
- 使用 CPU 推理（device: "cpu"）
- 关闭其他占用 GPU 的程序
- 增加 GPU 显存（硬件升级）

**问题 2：CUDA 不可用**
```
WARNING | embedding_engine:load_model:70 | CUDA not available, falling back to CPU
```

**解决方案**：
- 检查 NVIDIA 驱动是否安装
- 检查 CUDA 是否安装
- 检查 PyTorch 是否支持 CUDA
- 验证命令：`python -c "import torch; print(torch.cuda.is_available())"`

**问题 3：文件监控不工作**
```
WARNING | file_monitor:on_created:78 | File not found: /path/to/file.jpg
```

**解决方案**：
- 检查文件路径是否正确
- 检查文件权限
- 检查 ignore_patterns 配置
- 重启文件监控器

**问题 4：检索结果为空**
```json
{
    "code": 0,
    "message": "success",
    "data": {
        "query": "test",
        "total": 0,
        "results": []
    }
}
```

**解决方案**：
- 检查是否有已索引的文件
- 检查检索参数是否正确
- 检查相似度阈值是否过高
- 检查模型是否加载成功
- 重新索引文件

**问题 5：API 服务器无法启动**
```
ERROR | main:start_api:115 | Failed to start API server
Error: [Errno 98] Address already in use
```

**解决方案**：
- 检查端口是否被占用：`netstat -tlnp | grep 8000`
- 杀死占用端口的进程：`kill -9 <pid>`
- 修改 API 端口（配置文件）

**问题 6：数据库连接失败**
```
ERROR | database_manager:init_database:35 | Failed to initialize database
Error: unable to open database file
```

**解决方案**：
- 检查数据库目录是否存在：`ls -la data/database/sqlite/`
- 检查目录权限：`chmod -R 755 data/database/`
- 检查磁盘空间：`df -h`
- 重新初始化数据库：`python scripts/init_database.py`

### 8.2 日志分析

**错误日志模式**：
```bash
# 查找所有错误
grep "ERROR" data/logs/msearch.log | head -20

# 查找特定错误
grep "CUDA out of memory" data/logs/msearch.log
grep "Failed to load model" data/logs/msearch.log
grep "Task failed" data/logs/msearch.log

# 统计错误类型
grep "ERROR" data/logs/msearch.log | awk -F'|' '{print $4}' | sort | uniq -c | sort -rn

# 查看最近的错误
tail -100 data/logs/msearch.log | grep "ERROR"
```

**警告日志模式**：
```bash
# 查找所有警告
grep "WARNING" data/logs/msearch.log | head -20

# 查找特定警告
grep "CUDA not available" data/logs/msearch.log
grep "File not found" data/logs/msearch.log
```

### 8.3 诊断工具

**系统诊断**：
```bash
# 检查系统资源
htop
nvidia-smi
df -h
free -h

# 检查进程
ps aux | grep msearch
ps aux | grep python

# 检查端口
netstat -tlnp | grep 8000
netstat -tlnp | grep 5173

# 检查文件描述符
lsof -p <pid> | wc -l
```

**应用诊断**：
```bash
# 健康检查
curl http://localhost:8000/health

# 系统信息
curl http://localhost:8000/api/v1/system/info

# 模型信息
curl http://localhost:8000/api/v1/models/info

# 数据库统计
curl http://localhost:8000/api/v1/database/stats

# 任务统计
curl http://localhost:8000/api/v1/tasks/stats

# 测试检索
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "top_k": 5}'
```

### 8.4 恢复流程

**恢复步骤**：
1. **收集信息**：
   - 错误日志
   - 系统状态（CPU、内存、GPU、磁盘）
   - 配置文件
   - 最近的操作

2. **定位问题**：
   - 根据错误信息定位问题
   - 查看相关日志
   - 使用诊断工具

3. **尝试修复**：
   - 根据常见问题解决方案尝试修复
   - 修改配置文件
   - 重启服务

4. **验证修复**：
   - 运行测试
   - 检查日志
   - 验证功能

5. **记录问题**：
   - 记录问题描述
   - 记录解决方案
   - 记录预防措施

---

## 升级与维护

### 9.1 版本升级

**升级前准备**：
- 备份数据（数据库、配置文件）
- 查看版本说明（CHANGELOG.md）
- 检查升级注意事项
- 停止服务

**升级步骤**：
```bash
# 1. 备份数据
scripts/backup.sh

# 2. 拉取最新代码
git pull origin main

# 3. 安装依赖
pip install -r requirements.txt

# 4. 升级数据库（如果需要）
python scripts/migrate_database.py

# 5. 更新配置文件（如果需要）
cp config/config.yml.example config/config.yml.new
# 手动合并配置

# 6. 启动服务
python src/api/main.py

# 7. 验证升级
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/system/info
```

**版本回退**：
```bash
# 1. 停止服务
python src/api/main.py stop

# 2. 回退代码
git checkout <previous_version>

# 3. 恢复数据
# 解压备份文件

# 4. 启动服务
python src/api/main.py
```

### 9.2 日常维护

**每日检查**：
- 检查服务状态：`curl http://localhost:8000/health`
- 检查日志是否有错误：`grep "ERROR" data/logs/msearch.log | tail -10`
- 检查磁盘空间：`df -h`

**每周检查**：
- 运行性能测试：`pytest tests/benchmark/ -v`
- 清理日志文件：`find data/logs -name "*.log.*" -mtime +7 -delete`
- 检查任务成功率：`curl http://localhost:8000/api/v1/tasks/stats`

**每月检查**：
- 备份数据：`scripts/backup.sh`
- 检查模型更新
- 清理临时文件：`rm -rf data/temp/*`
- 检查系统更新

### 9.3 常见维护任务

**清理临时文件**：
```bash
# 清理临时文件
rm -rf data/temp/*

# 清理日志文件
find data/logs -name "*.log.*" -mtime +7 -delete

# 清理备份文件
find /path/to/backup -name "*.tar.gz" -mtime +30 -delete

# 清理缓存
rm -rf data/cache/preprocessing/*
```

**重新索引文件**：
```bash
# 删除所有索引（注意：这会删除所有向量数据）
python scripts/clear_database_vectors.py

# 重新索引
python src/api_server.py &
sleep 5
curl -X POST http://localhost:8000/api/v1/files/scan \
  -H "Content-Type: application/json" \
  -d '{"path": "/path/to/monitor"}'
```

**更新模型**：
```bash
# 检查模型状态
python scripts/setup_models.py check

# 强制重新下载
python scripts/setup_models.py setup --force

# 重启服务
bash scripts/run.sh
```

**数据库维护**：
```bash
# 备份数据库
cp data/database/sqlite/msearch.db data/database/sqlite/msearch.db.backup

# 清理向量数据库
rm -rf data/database/lancedb/unified_vectors

# 重新初始化
python src/api_server.py
```

---

## 附录

### A.1 配置参数参考

**完整配置文件**：`config/config.yml.example`

**常用配置参数**：
| 参数 | 说明 | 默认值 | 推荐值 |
|------|------|-------|-------|
| `models.[配置驱动模型].batch_size` | 图像/视频模型批处理大小 | 16 | 8-32 |
| `models.[配置驱动模型].precision` | 模型精度 | float16 | float16/float32 |
| `models.[配置驱动模型].device` | 模型设备 | cuda | cuda/cpu |
| `models.[配置驱动模型].batch_size` | 音频模型批处理大小 | 8 | 4-16 |
| `performance.video_processing.frame_interval` | 视频采样间隔 | 10 | 5-20 |
| `performance.video_processing.target_fps` | 视频目标帧率 | 2 | 1-5 |
| `performance.video_processing.max_segments_per_video` | 最大分段数 | 100 | 50-200 |
| `task_scheduler.max_workers` | 任务调度器工作线程数 | 4 | 2-8 |
| `api.port` | API 端口 | 8000 | 8000-8080 |
| `logging.level` | 日志级别 | INFO | DEBUG/INFO/WARNING |

### A.2 命令参考

**常用命令**：
```bash
# 安装部署
bash scripts/install.sh              # 一键安装
bash scripts/run.sh                  # 一键启动

# 模型管理
python scripts/setup_models.py check # 检查模型
python scripts/setup_models.py setup # 下载模型
python scripts/setup_models.py clear # 清除模型

# 服务管理
bash scripts/run.sh                  # 启动服务
pkill -f "python src/api_server.py"  # 停止服务

# 数据库管理
python scripts/clear_database_vectors.py  # 清除向量数据
cp data/database/sqlite/msearch.db data/database/sqlite/msearch.db.backup  # 备份数据库

# 日志查看
tail -f data/logs/msearch.log        # 查看主日志
tail -f data/logs/api.log            # 查看API日志

# 测试
pytest tests/unit/ -v                # 运行单元测试
pytest tests/integration/ -v         # 运行集成测试
```

**API命令**：
```bash
# 健康检查
curl http://localhost:8000/health

# 系统信息
curl http://localhost:8000/api/v1/system/info

# 模型信息
curl http://localhost:8000/api/v1/models/info

# 文本搜索
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query": "测试搜索", "top_k": 10}'

# 图像搜索
curl -X POST http://localhost:8000/api/v1/search/image \
  -F "image=@/path/to/image.jpg" \
  -F "top_k=10"

# 音频搜索
curl -X POST http://localhost:8000/api/v1/search/audio \
  -F "audio=@/path/to/audio.mp3" \
  -F "top_k=10"

# 文件扫描
curl -X POST http://localhost:8000/api/v1/files/scan \
  -H "Content-Type: application/json" \
  -d '{"path": "/path/to/monitor"}'
```

### A.3 故障排查流程图

```
用户报告问题
    ↓
收集信息（日志、系统状态、配置）
    ↓
查看常见问题
    ↓
是否找到解决方案？
    ↓ 是
尝试修复
    ↓
验证修复
    ↓
问题解决？
    ↓ 是
记录问题和解决方案
    ↓
结束
    
    ↓ 否（常见问题未找到）
查看详细日志
    ↓
使用诊断工具
    ↓
定位问题
    ↓
尝试修复
    ↓
验证修复
    ↓
问题解决？
    ↓ 是
记录问题和解决方案
    ↓
结束
    
    ↓ 否
联系技术支持
    ↓
提供详细信息
    ↓
等待支持
```

### A.4 支持与反馈

**获取帮助**：
- **快速开始**：[QUICKSTART.md](../QUICKSTART.md)
- **完整文档**：docs/ 目录下的文档
- **API文档**：http://localhost:8000/docs（启动后访问）
- **问题跟踪**：GitHub Issues

**反馈问题**：
- 提供详细的问题描述
- 提供错误日志（`data/logs/msearch.log`）
- 提供系统信息（CPU、内存、GPU、操作系统）
- 提供复现步骤
- 提供预期结果和实际结果

**常见问题**：
1. **模型下载失败**：使用国内镜像 `export HF_ENDPOINT=https://hf-mirror.com`
2. **CUDA不可用**：检查NVIDIA驱动和CUDA安装
3. **端口被占用**：修改 `config/config.yml` 中的端口配置
4. **内存不足**：降低 `batch_size` 或使用CPU推理
5. **检索结果为空**：检查是否有已索引的文件

**离线模式**：
```bash
# 设置离线环境变量
export TRANSFORMERS_OFFLINE=1
export HF_DATASETS_OFFLINE=1
export HF_HUB_OFFLINE=1
export HF_HOME="data/models"

# 启动离线模式
bash scripts/run_offline.sh
```

---

**© 2026 msearch 技术团队**  
**本文档受团队内部保密协议保护**

---

## 变更日志

### v2.0 (2026-01-23)
- 新增快速安装和启动脚本
- 新增模型管理和检查功能
- 新增PySide6桌面UI
- 新增离线模式支持
- 优化模型下载逻辑（支持国内镜像）
- 优化配置文件结构

### v1.0 (2026-01-19)
- 初始版本
- 完整的部署和运维文档