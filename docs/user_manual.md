# msearch 用户手册

## 目录

1. [快速开始](#快速开始)
2. [安装指南](#安装指南)
3. [配置说明](#配置说明)
4. [基本使用](#基本使用)
5. [高级功能](#高级功能)
6. [常见问题](#常见问题)
7. [故障排除](#故障排除)

---

## 快速开始

### 1. 系统要求

**最低配置**:
- 操作系统: Windows 10+, macOS 10.15+, Linux (Ubuntu 18.04+)
- CPU: 4核心及以上
- 内存: 8GB及以上
- 磁盘空间: 20GB可用空间

**推荐配置**:
- CPU: 8核心及以上
- 内存: 16GB及以上
- GPU: NVIDIA RTX 3060及以上（8GB显存）
- 磁盘空间: 50GB可用空间

### 2. 快速安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/msearch.git
cd msearch

# 安装依赖
pip install -r requirements.txt

# 启动应用
python src/main.py
```

### 3. 首次使用

1. 启动应用后，系统会自动检测硬件配置
2. 根据硬件配置自动选择合适的AI模型
3. 添加监控目录开始自动索引
4. 使用Web界面或API进行检索

---

## 安装指南

详细的安装指南请参考 [安装部署文档](./deployment.md)。

### 支持的平台

- **Windows**: 完整支持
- **macOS**: 完整支持（Intel和Apple Silicon）
- **Linux**: 完整支持（Ubuntu, Debian, CentOS等）

### 依赖项

- Python 3.8+
- PyTorch 2.8.0+
- CUDA 11.8+（GPU加速）
- FFmpeg（视频处理）

---

## 配置说明

### 配置文件位置

主配置文件位于: `config/config.yml`

其他配置文件:
- `config/config.yml`: 主配置文件
- `config/config.yml.backup`: 配置文件备份

### 基本配置

```yaml
system:
  debug: false
  data_dir: "data/"
  log_level: "INFO"
  check_interval: 5
  hardware_level: "auto"
  auto_model_selection: true
```

**参数说明**:
- `debug`: 调试模式
- `data_dir`: 数据存储目录
- `log_level`: 日志级别
- `check_interval`: 文件检查间隔（秒）
- `hardware_level`: 硬件级别（auto/low/mid/high/ultra）
- `auto_model_selection`: 自动选择模型

### 硬件级别说明

系统支持多级硬件自适应模型选择，使用 [michaelfeil/infinity](https://github.com/michaelfeil/infinity) 框架统一管理模型：

| 硬件级别 | GPU显存 | 系统内存 | 推荐模型 | 显存需求 |
|---------|---------|---------|---------|---------|
| entry | <2GB或CPU | ≥4GB | [配置驱动模型] | 2GB |
| low | <8GB或无GPU | ≥8GB | [配置驱动模型] | 4GB |
| mid | 8-16GB | ≥16GB | [配置驱动模型] | 4GB |
| high | 16-24GB | ≥32GB | [配置驱动模型] | 4GB |
| ultra | >24GB | ≥64GB | [配置驱动模型] | 4GB |

设置为 `auto` 时，系统会自动检测硬件并选择合适的模型。

**Infinity 框架特性**：
- **简单切换模型**：配置文件驱动，无需修改代码即可切换不同模型
- **高效管理模型运行**：统一的模型生命周期管理（加载、卸载、缓存）
- **统一的模型加载接口**：所有模型使用相同的加载方式，简化代码
- **高性能推理**：动态批处理优化，FlashAttention 加速，多精度支持
- **内存优化**：自动内存管理，避免显存溢出，智能缓存策略
- **支持离线模式**：完全支持离线运行，无需网络连接

### 监控配置

```yaml
monitoring:
  directories:
    - path: /path/to/media
      priority: 1
      recursive: true
  check_interval: 5
  debounce_delay: 500
```

**参数说明**:
- `directories`: 监控目录列表
- `check_interval`: 检查间隔（秒）
- `debounce_delay`: 防抖延迟（毫秒）

### 模型配置

系统会根据硬件配置自动选择模型，无需手动配置。

---

## 基本使用

### 1. 添加监控目录

**方法一：通过配置文件**
```yaml
monitoring:
  directories:
    - path: /path/to/your/media
      priority: 1
      recursive: true
```

**方法二：通过API**
```bash
curl -X POST http://localhost:8000/api/v1/monitor/add \
  -H "Content-Type: application/json" \
  -d '{"path": "/path/to/your/media", "recursive": true}'
```

### 2. 文本检索

**方法一：通过Web界面**
1. 打开浏览器访问 `http://localhost:8000`
2. 在搜索框输入关键词
3. 点击搜索按钮
4. 查看搜索结果

**方法二：通过API**
```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query": "海边日落", "modality": "text", "limit": 10}'
```

### 3. 图像检索

**方法一：通过Web界面**
1. 打开浏览器访问 `http://localhost:8000`
2. 点击图像检索按钮
3. 上传参考图像
4. 查看搜索结果

**方法二：通过API**
```bash
curl -X POST http://localhost:8000/api/v1/search/image \
  -H "Content-Type: application/json" \
  -d '{"image_path": "/path/to/image.jpg", "limit": 10}'
```

### 4. 音频检索

**方法一：通过Web界面**
1. 打开浏览器访问 `http://localhost:8000`
2. 点击音频检索按钮
3. 上传参考音频
4. 查看搜索结果

**方法二：通过API**
```bash
curl -X POST http://localhost:8000/api/v1/search/audio \
  -H "Content-Type: application/json" \
  -d '{"audio_path": "/path/to/audio.mp3", "limit": 10}'
```

---

## 高级功能

### 1. 时间线搜索

在视频搜索结果中，系统会显示时间轴信息，帮助您快速定位到视频中的特定片段。

**使用方法**:
1. 执行视频搜索
2. 在结果中查看时间轴
3. 点击时间轴上的标记点
4. 播放预览视频

### 2. 人脸识别检索

系统支持基于人名的智能检索，当搜索词包含人名时，会自动激活人脸识别功能。

**使用方法**:
```bash
# 搜索包含特定人名的视频
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query": "张三", "modality": "text", "limit": 10}'
```

### 3. 批量操作

系统支持批量添加文件、批量搜索等操作。

**批量添加文件**:
```bash
# 创建批量任务列表
cat > batch_files.json << EOF
{
  "files": [
    {"path": "/path/to/file1.mp4"},
    {"path": "/path/to/file2.mp4"},
    {"path": "/path/to/file3.mp4"}
  ]
}
EOF

# 执行批量添加
curl -X POST http://localhost:8000/api/v1/files/batch \
  -H "Content-Type: application/json" \
  -d @batch_files.json
```

### 4. 任务管理

查看和管理正在进行的任务。

**查看任务列表**:
```bash
curl http://localhost:8000/api/v1/tasks
```

**查看任务详情**:
```bash
curl http://localhost:8000/api/v1/tasks/{task_id}
```

**取消任务**:
```bash
curl -X POST http://localhost:8000/api/v1/tasks/{task_id}/cancel
```

### 5. 系统监控

实时监控系统运行状态和资源使用情况。

**查看系统状态**:
```bash
curl http://localhost:8000/api/v1/system/status
```

**查看硬件信息**:
```bash
curl http://localhost:8000/api/v1/system/hardware
```

**查看并发统计**:
```bash
curl http://localhost:8000/api/v1/system/concurrency
```

---

## 常见问题

### Q1: 如何提高搜索速度？

**A**: 
1. 使用更高配置的硬件
2. 减少向量数据库中的数据量
3. 使用更小的模型（牺牲精度换速度）
4. 启用GPU加速

### Q2: 如何降低内存使用？

**A**:
1. 使用统一多模态模型（[配置驱动模型]）
2. 减少并发任务数量
3. 定期清理缓存
4. 使用更小的批处理大小

### Q3: 如何处理大量文件？

**A**:
1. 分批添加文件
2. 使用优先级控制处理顺序
3. 在低峰期进行批量处理
4. 监控系统资源使用情况

### Q4: 如何备份和恢复数据？

**A**:
1. 备份 `data/` 目录
2. 导出向量数据库
3. 导出SQLite数据库
4. 详见 [安装部署文档](./deployment.md)

### Q5: 如何更新模型？

**A**:
1. 下载新模型到 `data/models/` 目录
2. 更新配置文件中的模型路径
3. 重启应用
4. 系统会自动加载新模型

---

## 故障排除

### 1. 应用无法启动

**症状**: 运行 `python src/main.py` 时报错

**可能原因**:
- 依赖未安装
- 配置文件错误
- 端口被占用

**解决方案**:
```bash
# 检查依赖
pip install -r requirements.txt

# 检查配置
python -c "from src.core.config import ConfigManager; ConfigManager()"

# 检查端口
lsof -i :8000  # Linux/macOS
netstat -ano | findstr :8000  # Windows
```

### 2. 检索速度慢

**症状**: 检索响应时间超过2秒

**可能原因**:
- 向量数据库数据量过大
- 硬件配置不足
- 索引未优化

**解决方案**:
```bash
# 查看系统状态
curl http://localhost:8000/api/v1/system/status

# 查看硬件信息
curl http://localhost:8000/api/v1/system/hardware

# 重建索引
# 需要在配置文件中启用索引重建选项
```

### 3. 文件处理失败

**症状**: 文件添加后一直处于 `processing` 状态

**可能原因**:
- 文件格式不支持
- 文件损坏
- 磁盘空间不足
- 模型加载失败

**解决方案**:
```bash
# 查看任务详情
curl http://localhost:8000/api/v1/tasks/{task_id}

# 查看日志
tail -f data/logs/msearch.log

# 检查磁盘空间
df -h  # Linux/macOS
wmic logicaldisk get size,freespace,caption  # Windows
```

### 4. 内存不足

**症状**: 应用崩溃或响应缓慢

**可能原因**:
- 处理大文件
- 并发任务过多
- 模型占用内存过大

**解决方案**:
```bash
# 查看内存使用
curl http://localhost:8000/api/v1/system/hardware

# 减少并发任务
# 在配置文件中设置 max_concurrent_tasks

# 使用更小的模型
# 在配置文件中设置 hardware_level 为 low
```

### 5. GPU不可用

**症状**: GPU未被使用，所有任务都在CPU上运行

**可能原因**:
- CUDA未安装
- PyTorch版本不兼容
- GPU驱动未安装

**解决方案**:
```bash
# 检查CUDA
nvcc --version

# 检查PyTorch
python -c "import torch; print(torch.cuda.is_available())"

# 检查GPU驱动
nvidia-smi

# 重新安装PyTorch
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

---

## 获取帮助

### 文档资源

- [API文档](./api.md)
- [安装部署文档](./deployment.md)
- [设计文档](./design.md)
- [需求文档](./requirements.md)

### 社区支持

- GitHub Issues: https://github.com/yourusername/msearch/issues
- 讨论区: https://github.com/yourusername/msearch/discussions

### 联系方式

- 邮件: support@msearch.example.com
- 官网: https://msearch.example.com

---

## 更新日志

### v1.0.0 (2026-01-13)
- 初始版本发布
- 支持文本、图像、音频多模态检索
- 自动硬件检测和模型选择
- 动态并发调整
- 可配置缓存策略