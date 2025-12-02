# 安装指南

> **文档导航**: [需求文档](requirements.md) | [设计文档](design.md) | [开发计划](development_plan.md) | [API文档](api_documentation.md) | [测试策略](test_strategy.md) | [用户手册](user_manual.md) | [部署指南](deployment_guide.md)

## 1. 系统要求

### 1.1 硬件要求

| 组件 | 最低配置 | 推荐配置 |
|------|----------|----------|
| CPU | 4核处理器 | 8核处理器 |
| 内存 | 8GB RAM | 16GB RAM |
| 磁盘 | 50GB 可用空间 | 100GB 可用空间 |
| GPU | 无特殊要求 | NVIDIA GPU (8GB VRAM+) |
| 网络 | 100Mbps | 1Gbps |

### 1.2 软件要求

| 操作系统 | 支持版本 |
|----------|----------|
| Windows | Windows 10/11 (64位) |
| macOS | macOS 10.15+ |
| Linux | Ubuntu 20.04+, CentOS 7+, Debian 10+ |

| 依赖软件 | 版本要求 |
|----------|----------|
| Python | 3.10+ |
| FFmpeg | 4.4+ |
| Git | 2.20+ |
| CUDA | 11.7+ (仅GPU加速需要) |

## 2. 安装方法

### 2.1 在线自动安装 (推荐)

**Windows/Linux/macOS通用**:  
```bash
# 克隆仓库
git clone https://github.com/yourusername/msearch.git
cd msearch

# 运行自动安装脚本
chmod +x scripts/install_auto.sh
./scripts/install_auto.sh
```

**脚本功能**:  
- 自动检测操作系统
- 安装Python依赖
- 下载所需模型
- 配置环境变量
- 初始化数据库
- 启动服务

### 2.2 离线安装

**步骤1: 准备离线资源包**
1. 在有网络的环境下下载离线资源包
   ```bash
   ./scripts/download_all_resources.sh
   ```
2. 将生成的 `offline/` 目录复制到目标机器

**步骤2: 执行离线安装**
```bash
chmod +x scripts/install_offline.sh
./scripts/install_offline.sh
```

### 2.3 手动安装

**步骤1: 安装系统依赖**

- **Ubuntu/Debian**:
  ```bash
  sudo apt update
  sudo apt install -y python3-pip python3-venv ffmpeg git
  ```

- **CentOS/RHEL**:
  ```bash
  sudo yum install -y python3-pip python3-venv ffmpeg git
  ```

- **macOS** (使用Homebrew):
  ```bash
  brew install python3 ffmpeg git
  ```

- **Windows**:
  - 下载并安装 [Python 3.10+](https://www.python.org/downloads/)
  - 下载并安装 [FFmpeg](https://ffmpeg.org/download.html)，并添加到系统PATH
  - 下载并安装 [Git](https://git-scm.com/downloads)

**步骤2: 安装Python依赖**
```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

**步骤3: 下载模型文件**
```bash
./scripts/download_all_resources.sh
```

**步骤4: 初始化数据库**
```bash
python -c "from src.storage.database_manager import DatabaseManager; db = DatabaseManager(); db.init_database()"
```

## 3. 验证安装

### 3.1 检查服务状态

```bash
# 启动服务
python scripts/start_services.py

# 检查API是否可用
curl http://localhost:8000/api/health
```

预期输出:
```json
{"status": "ok", "message": "MSearch service is running"}
```

### 3.2 运行测试

```bash
# 运行单元测试
pytest tests/unit/

# 运行集成测试
pytest tests/integration/
```

## 4. 启动方式

### 4.1 命令行启动

```bash
# 启动所有服务
python scripts/start_services.py

# 仅启动API服务
python scripts/start_api.py

# 仅启动UI服务
python scripts/start_ui.py
```

### 4.2 系统服务启动 (Linux)

```bash
# 安装为系统服务
sudo cp scripts/msearch.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable msearch
sudo systemctl start msearch

# 检查服务状态
sudo systemctl status msearch
```

### 4.3 开机自启 (Windows)

1. 打开 `任务计划程序`
2. 创建基本任务
3. 设置触发器为"启动时"
4. 操作选择"启动程序"
5. 程序路径选择 `scripts/start_services.py`
6. 完成设置

## 5. 常见安装问题

### 5.1 Python版本不兼容

**问题**: 安装时提示Python版本过低
**解决**: 安装Python 3.10+版本，并确保使用正确的Python解释器

### 5.2 FFmpeg未找到

**问题**: 提示"ffmpeg not found"
**解决**: 确保FFmpeg已正确安装并添加到系统PATH

### 5.3 模型下载失败

**问题**: 模型下载超时或失败
**解决**: 检查网络连接，或手动下载模型文件到 `data/models/` 目录

### 5.4 端口被占用

**问题**: 提示"Address already in use"
**解决**: 修改配置文件 `config/config.yml` 中的端口设置

### 5.5 权限问题

**问题**: 提示"Permission denied"
**解决**: 确保脚本有执行权限，或使用sudo运行

## 6. 升级指南

### 6.1 在线升级

```bash
# 拉取最新代码
git pull origin main

# 升级依赖
pip install -r requirements.txt --upgrade

# 运行数据库迁移
python scripts/migrate_database.py

# 重启服务
python scripts/restart_services.py
```

### 6.2 离线升级

1. 在有网络的环境下下载最新代码和资源
2. 复制到目标机器
3. 执行离线安装脚本

## 7. 卸载方法

```bash
# 停止所有服务
python scripts/stop_services.py

# 删除虚拟环境
rm -rf venv

# 删除数据库和模型 (可选)
rm -rf data/

# 删除项目目录 (可选)
cd ..
rm -rf msearch/
```

## 8. 联系方式

- **官方文档**: https://docs.msearch.com
- **GitHub Issues**: https://github.com/yourusername/msearch/issues
- **社区论坛**: https://forum.msearch.com
- **技术支持**: support@msearch.com
