# MSearch 多模态检索系统 Windows部署指南

## 1. 系统要求

- **操作系统**: Windows 10 64位或以上
- **Python**: 3.9 - 3.11 版本 (推荐3.10)
- **内存**: 至少8GB RAM (推荐16GB以上)
- **存储空间**: 至少10GB可用空间 (用于安装依赖和模型)
- **GPU**: 可选，支持CUDA以加速AI模型

## 2. 快速开始

### 2.1 一键部署

MSearch提供了Windows一键部署脚本，可以自动完成所有安装和配置步骤：

1. 确保已安装Python 3.9-3.11版本
2. 打开Windows命令提示符 (cmd.exe) 或PowerShell
3. 进入项目根目录
4. 执行部署脚本：

```batch
scripts\install_and_configure_msearch.bat
```

该脚本会自动执行以下操作：
- 检查Python环境
- 创建虚拟环境
- 安装项目依赖
- 创建必要的目录结构
- 启动Qdrant向量数据库服务
- 启动MSearch主API服务

### 2.2 停止服务

要停止所有服务，请运行：

```batch
scripts\stop_all_services.bat
```

## 3. 部署流程详解

### 3.1 环境准备

1. **Python安装**
   - 从 [Python官网](https://www.python.org/downloads/) 下载Python 3.9-3.11版本
   - 安装时请勾选"Add Python to PATH"

2. **Git克隆项目** (如果尚未克隆)
   ```bash
   git clone <项目仓库地址>
   cd msearch
   ```

### 3.2 依赖安装

一键部署脚本会自动处理依赖安装，支持两种模式：
- **离线安装**：如果在`offline/packages/requirements`目录下有预下载的依赖包
- **在线安装**：如果没有离线包，将通过pip在线下载

### 3.3 服务启动

部署成功后，以下服务将自动启动：
- **Qdrant向量数据库**: http://localhost:6333
- **MSearch API服务**: http://localhost:8000
- **API文档**: http://localhost:8000/docs

## 4. 访问系统

### 4.1 API文档

部署完成后，可以通过浏览器访问以下地址查看API文档：
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 4.2 桌面应用

可以通过以下命令启动桌面应用：

```batch
# 先激活虚拟环境
venv\Scripts\activate
# 运行桌面应用
python src\gui\gui_main.py
```

### 4.3 健康检查

检查Qdrant服务状态：
```bash
curl http://localhost:6333/health
```

检查MSearch API服务状态：
```bash
curl http://localhost:8000/health
```

## 5. 自定义配置

### 5.1 修改默认配置

编辑`config/config.yml`文件可以自定义系统配置：
- 修改监控目录
- 调整模型参数
- 配置功能开关
- 设置并发任务数

### 5.2 环境变量覆盖

可以通过设置环境变量来覆盖配置文件中的设置：
```batch
set MSEARCH_LOG_LEVEL=DEBUG
set MSEARCH_DATA_DIR=C:\custom\data\path
```

## 6. 常见问题排查

### 6.1 端口冲突

如果8000或6333端口被占用，可以在启动前释放这些端口，或修改配置文件中的端口设置。

### 6.2 内存不足

如果系统内存不足，可以：
- 减少`max_concurrent_tasks`值
- 使用较小的模型版本
- 关闭不需要的功能模块

### 6.3 GPU支持

系统会自动检测并使用GPU（如果可用）。要强制使用CPU，可以在配置文件中设置：
```yaml
models:
  clip:
    device: "cpu"
  clap:
    device: "cpu"
```

## 7. 离线部署说明

对于完全离线环境，建议先在有网络的环境中运行：
```batch
scripts\download_model_resources.bat
```

该脚本会下载所有必要的依赖包和模型文件到`offline`目录，然后可以将整个项目复制到离线环境中进行部署。

## 8. 升级系统

要升级系统版本，请：
1. 停止当前运行的服务
2. 更新代码库
3. 重新运行部署脚本

```batch
scripts\stop_all_services.bat
git pull
scripts\install_and_configure_msearch.bat
```

## 9. 联系方式

如有任何问题或建议，请通过项目仓库的Issues功能反馈。

---

*文档版本: v1.0 | 更新日期: 2024年*