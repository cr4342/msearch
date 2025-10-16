# 部署与运维指南

> **文档导航**: [文档索引](README.md) | [需求文档](requirements.md) | [设计文档](design.md) | [开发计划](development_plan.md) | [API文档](api_documentation.md) | [开发环境搭建](development_environment.md) | [技术实现指南](technical_implementation.md) | [故障排除指南](troubleshooting.md)

## 1. 配置文件管理

> **文档导航**: [文档索引](README.md) | [需求文档](requirements.md) | [设计文档](design.md) | [开发计划](development_plan.md) | [测试策略](test_strategy.md) | [部署指南](deployment_guide.md)

### 1.1 概述

msearch 系统采用统一的配置文件管理机制，所有配置文件统一存放在 `config/` 目录下，确保配置管理的规范性和可维护性。

### 1.2 配置文件结构

#### 主配置文件

**文件路径**：`config/config.yml`

**功能说明**：包含系统的核心配置，包括路径设置、预处理参数、向量引擎配置、数据库配置等。

**主要配置项**：
- **paths**: 监控目录、数据库路径、日志路径等基础路径配置
- **preprocessing**: 视频和音频预处理参数
- **infinity**: Infinity 向量引擎配置（多模型架构）
- **qdrant**: Qdrant 向量数据库配置（多集合架构）
- **smart_retrieval**: 智能检索策略配置
- **fastapi**: FastAPI 服务配置
- **hardware_mode**: 硬件模式选择（cpu/cuda/auto）
- **audio_weights**: 音频权重配置
- **system**: 系统限制和格式支持配置

#### 人脸检索配置文件

**文件路径**：`config/face_retrieval.yml`

**功能说明**：专门用于人脸检索功能的独立配置，支持热重载。

### 1.3 配置加载机制

#### 默认加载路径

系统默认从以下路径加载配置：
```python
config/config.yml  # 主配置文件
```

#### 自定义配置路径

支持通过以下方式指定自定义配置路径：

1. **函数参数**：在代码中调用配置加载函数时传入自定义路径
2. **环境变量**：通过环境变量指定配置路径

#### 配置生成机制

当配置文件不存在时，系统会自动生成默认配置：

1. **创建配置目录**：自动创建 `config/` 目录
2. **生成默认配置**：根据系统需求生成包含所有必要配置的默认文件
3. **路径自动设置**：自动设置合理的基础路径和参数

### 1.4 配置管理最佳实践

#### 配置文件组织

- 所有配置文件统一存放在 `config/` 目录下
- 按功能模块分离配置（如人脸检索独立配置）
- 使用清晰的配置项命名和层级结构

#### 配置版本管理

- 配置文件纳入版本控制（Git）
- 为不同环境创建配置模板（开发、测试、生产）
- 记录配置变更历史

#### 配置安全

- 敏感信息（如密码、密钥）使用环境变量
- 避免在配置文件中硬编码敏感数据
- 定期审查配置安全性

#### 配置优化

- 根据硬件环境调整性能参数
- 定期优化检索相关配置
- 监控配置变更对系统性能的影响

### 1.5 配置更新和维护

#### 配置重启加载

配置修改后需要重启服务才能生效：
- 修改配置文件后需要重启服务
- 系统启动时一次性加载所有配置
- 配置变更简单可靠，降低开发维护复杂度

#### 配置备份

建议定期备份配置文件：
- 备份重要配置到安全位置
- 记录配置变更时间和原因
- 建立配置回滚机制

### 1.6 故障排查

#### 常见配置问题

1. **配置文件缺失**：系统会自动生成默认配置
2. **配置路径错误**：检查路径是否存在且有读取权限
3. **配置格式错误**：使用 YAML 格式验证工具检查
4. **配置项冲突**：检查相同配置项的重复定义

#### 调试建议

1. **启用详细日志**：设置日志级别为 DEBUG
2. **检查配置加载**：确认配置文件被正确加载
3. **验证配置内容**：确保配置项值符合预期
4. **测试配置变更**：在小规模环境测试配置修改

## 2. 离线优先部署策略

### 2.1 部署流程概览

本项目采用**离线优先**的部署策略，所有依赖和模型优先从本地`offline`目录获取：

1. **离线资源准备** - 使用`download_model_resources.sh`脚本预先下载所有依赖
2. **本地依赖安装** - 优先从`offline/packages`目录安装Python依赖
3. **本地模型加载** - 优先从`offline/models`目录加载AI模型
4. **服务启动** - 使用离线脚本启动Qdrant和Infinity服务

### 2.2 离线资源目录结构

```
offline/
├── packages/          # Python依赖包
│   ├── requirements/  # 主要依赖包
│   └── pyside6/       # PySide6 GUI框架
├── models/            # AI模型文件
│   └── huggingface/   # HuggingFace模型
├── bin/               # 二进制工具
│   └── qdrant         # Qdrant向量数据库
├── github/            # GitHub下载的资源
│   └── ffmpeg.tar.xz  # FFmpeg静态构建
└── qdrant_data/       # Qdrant数据存储
```

### 2.3 多源下载机制

#### 自动检测与本地资源优先策略

部署脚本或安装程序启动时会执行以下自动检测流程：

1. **模型文件检测** - 检查指定目录（默认为`offline/models/`）是否存在所需模型文件
2. **依赖软件检测** - 验证关键依赖软件是否已安装
3. **本地资源优先使用** - 如检测到本地存在完整模型文件和已安装依赖，直接使用本地资源
4. **部分缺失处理** - 如仅缺失部分模型文件，优先下载缺失部分

#### 网络下载策略

当本地资源不完整或不存在时，系统会按以下顺序尝试从网络下载：

**国内网络优化策略**：
1. **HuggingFace镜像站** (hf-mirror.com) - 首选下载源
2. **GitClone/GitHub镜像站** - 代码和模型仓库加速
   - kkgithu.com（推荐，速度快，稳定性好）
   - github.com.cnpmjs.org（服务器位于香港）
   - https://gh-proxy.com/（GitHub代理加速）
3. **ModelScope** (modelscope.cn) - 国内备用源

**国际网络策略**：
1. **原始HuggingFace** - 当检测到非中国网络环境时使用
2. **原始GitHub** - 当镜像站不可用时的备选

#### 离线模式处理

当所有网络下载尝试失败时，系统将：
1. 自动切换到离线模式
2. 提示用户自行下载所需模型和依赖包
3. 提供详细的下载指南和指定放置目录
4. 列出所有必需文件的完整清单和MD5校验值

### 2.4 GitHub下载优化

**使用https://gh-proxy.com/代理**：
```bash
# 原始GitHub URL
https://github.com/owner/repo/releases/download/v1.0.0/file.tar.gz

# 使用代理加速的URL
https://gh-proxy.com/https://github.com/owner/repo/releases/download/v1.0.0/file.tar.gz
```

**Qdrant官方二进制下载**：
Qdrant向量数据库使用官方二进制文件部署，支持多架构：
```bash
# 下载脚本会自动检测系统架构并下载对应的Qdrant二进制文件
# 支持：Linux x86_64, Linux aarch64, macOS x86_64, macOS arm64

# 下载地址（通过代理加速）
https://gh-proxy.com/https://github.com/qdrant/qdrant/releases/latest/download/qdrant-x86_64-unknown-linux-gnu.tar.gz
```

### 2.5 离线模式处理

当所有网络下载尝试失败时，系统将：
1. 自动切换到离线模式
2. 提示用户自行下载所需模型和依赖包
3. 提供详细的下载指南和指定放置目录
4. 列出所有必需文件的完整清单和MD5校验值

## 3. 快速部署步骤

### 3.1 离线资源下载（推荐）

```bash
# 1. 下载所有离线资源（模型、依赖、工具）
./scripts/download_model_resources.sh

# 2. 安装Python依赖（优先使用离线包）
pip install --no-index --find-links=offline/packages -r requirements.txt

# 3. 安装PySide6（GUI框架）
pip install --no-index --find-links=offline/packages/pyside6 PySide6
```

### 3.2 服务启动

```bash
# 1. 启动Qdrant向量数据库（使用离线二进制文件）
./scripts/start_qdrant.sh

# 2. 启动Infinity AI推理服务
./scripts/start_infinity_services.sh

# 3. 启动主应用
python src/api/main.py
```

### 3.3 服务停止

```bash
# 停止所有服务
./scripts/stop_qdrant.sh
./scripts/stop_infinity_services.sh
```

## 4. 一键部署脚本

### 4.1 启动所有服务

```bash
# 一键启动所有服务（Qdrant + Infinity）
./scripts/start_all_services.sh
```

### 4.2 停止所有服务

```bash
# 一键停止所有服务
./scripts/stop_all_services.sh
```

### 4.3 服务状态检查

```bash
# 检查Qdrant服务状态
curl http://localhost:6333/health

# 检查Infinity服务状态
curl http://localhost:7997/health  # CLIP服务
curl http://localhost:7998/health  # CLAP服务  
curl http://localhost:7999/health  # Whisper服务
```

## 5. 环境配置

### 5.1 开发环境

**环境变量配置**：
```bash
# 开发环境配置
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG

# 数据库配置
QDRANT_HOST=localhost
QDRANT_PORT=6333
SQLITE_PATH=./data/msearch_dev.db

# Infinity服务配置
INFINITY_CLIP_PORT=7997
INFINITY_CLAP_PORT=7998
INFINITY_WHISPER_PORT=7999

# 硬件配置
HARDWARE_MODE=auto  # cpu, cuda, auto
CUDA_VISIBLE_DEVICES=0

# 开发工具配置
ENABLE_HOT_RELOAD=true
ENABLE_DEBUG_TOOLBAR=true
```

### 5.2 生产环境

**性能优化配置**：
```bash
# 生产环境配置
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# 高性能配置
WORKERS=4
MAX_REQUESTS=1000
TIMEOUT=300

# 安全配置
ENABLE_SSL=true
API_RATE_LIMIT=100/minute
```

## 6. 监控与维护

### 6.1 健康检查

**服务健康检查**：
```bash
# 检查所有服务状态
./scripts/check_services_health.sh

# 监控资源使用
./scripts/monitor_resources.sh
```

### 6.2 日志管理

**日志配置**：
```bash
# 日志目录
mkdir -p logs/{app,qdrant,infinity}

# 日志轮转
logrotate -f config/logrotate.conf
```

### 6.3 备份策略

**数据备份**：
```bash
# 备份Qdrant数据
cp -r offline/qdrant_data backup/qdrant_data_$(date +%Y%m%d)

# 备份配置文件
cp -r config backup/config_$(date +%Y%m%d)
```

## 7. 性能调优

### 7.1 系统优化

**内存优化**：
- 调整批处理大小
- 优化向量索引参数
- 配置内存回收策略

**CPU优化**：
- 调整工作进程数
- 优化并发处理参数
- 配置CPU亲和性

### 7.2 数据库优化

**Qdrant优化**：
- 调整索引参数
- 优化集合配置
- 配置内存使用策略

## 相关文档

- [开发环境搭建指南](development_environment.md) - 开发环境配置
- [技术实现指南](technical_implementation.md) - 技术架构详解
- [故障排除指南](troubleshooting.md) - 常见问题解决