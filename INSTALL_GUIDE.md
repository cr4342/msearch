# MSearch 安装指南

## 快速开始

### 环境要求
- Python 3.9-3.11
- Git
- 足够的磁盘空间（推荐至少10GB）
- 对于Linux系统：gcc, build-essential, libssl-dev, libffi-dev, python3-dev
- 对于Windows系统：Visual C++ Build Tools

### 安装步骤

1. **环境准备**
   ```bash
   # Linux
   # 安装系统依赖
   sudo apt-get update
   sudo apt-get install -y gcc build-essential libssl-dev libffi-dev python3-dev
   
   # 检查Python版本
   python --version
   
   # 克隆项目（如果需要）
   git clone <项目仓库地址>
   cd msearch
   ```
   
   ```batch
   :: Windows
   :: 请确保已安装Visual C++ Build Tools
   :: 检查Python版本
   python --version
   ```

2. **安装依赖和启动服务**
   ```bash
   # 自动检测模式（推荐）
   cd scripts
   chmod +x install.sh
   ./install.sh
   
   # 在线模式安装
   ./install.sh --online
   
   # 离线模式安装（需先准备离线资源）
   ./install.sh --offline
   
   # 仅下载离线资源
   ./install.sh --download-only
   ```

3. **启动服务**
   ```bash
   # 启动Qdrant服务
   ./start_qdrant.sh
   
   # 启动API服务（前台运行）
   ./start_api.sh
   
   # 启动所有服务（后台运行）
   ./start_all.sh
   ```

## 功能说明

- **自动检测模式**：优先使用离线资源，否则自动下载，适合大多数场景
- **在线模式**：自动下载依赖和模型，适合有网络环境
- **离线模式**：使用预下载的资源安装，适合无网络环境
- **虚拟环境**：离线模式默认创建虚拟环境，在线模式可选
- **自动配置**：自动生成配置文件和启动脚本
- **支持多种系统**：兼容Linux和Windows系统

## 使用说明

### API服务
- API地址：http://localhost:8000
- API文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health

### Qdrant服务
- 服务地址：http://localhost:6333
- Web UI：http://localhost:6333/dashboard
- 健康检查：http://localhost:6333/health

### 日志查看
```bash
# 查看API日志
tail -f logs/api.log

# 查看应用日志
tail -f logs/msearch.log
```

### 停止服务
```bash
# 停止前台运行的服务
Ctrl + C

# 停止后台运行的服务
pkill -f "uvicorn src.api.main:app"

# 停止Qdrant服务
./stop_qdrant.sh
```

## 常见问题

1. **端口被占用**
   - 修改配置文件中的端口号
   - 或停止占用端口的进程：`lsof -i :8000` 然后 `kill <PID>`

2. **模型下载失败**
   - 检查网络连接
   - 设置HuggingFace镜像：`export HF_ENDPOINT=https://hf-mirror.com`
   - 手动下载模型并放入`data/models/`目录

3. **依赖安装问题**
   - 确保pip版本较新：`pip install --upgrade pip`
   - 尝试使用虚拟环境：`python -m venv venv && source venv/bin/activate`

4. **Python环境问题**
   - 确保使用Python 3.9-3.11版本
   - 对于CUDA支持，需要安装对应版本的PyTorch

## 离线安装准备

1. **在有网络的环境下准备离线资源**
   ```bash
   ./install.sh --download-only
   ```

2. **复制离线资源到目标机器**
   - 将整个项目目录复制到目标机器
   - 确保`offline/`目录包含所有必要的资源

3. **在目标机器上执行离线安装**
   ```bash
   ./install.sh --offline
   ```

## 注意事项

- 首次运行时会下载大量模型，需要较长时间和稳定的网络
- 确保磁盘空间充足，尤其是模型存储目录
- 生产环境部署时请修改配置文件中的相关设置
- 离线模式需要先在有网络环境下准备离线资源
