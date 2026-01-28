# msearch - 多模态桌面检索系统

一款单机可运行的跨平台多模态桌面检索软件，专为视频剪辑师设计，实现素材无需整理、无需标签的智能检索。系统采用Python原生集成AI模型的方式，支持文本、图像、视频、音频四种模态的精准检索。

## 核心特性

- **智能检索**: 无需手动整理、无需添加标签即可实现智能检索
- **跨模态搜索**: 支持用任意模态（文本、图像、音频）检索其他模态内容
- **高精度定位**: 支持视频片段级检索，时间戳精度±5秒
- **零配置**: 素材无需整理、无需标签
- **高性能本地推理**: Python原生集成AI模型，无需额外服务引擎
- **硬件自适应**: 根据硬件配置自动选择最优模型
- **单机运行**: 完全本地化，无需网络依赖
- **跨平台桌面UI**: PySide6桌面应用，提供完整的用户交互界面

## 快速开始

### 一键安装部署

```bash
# 运行安装脚本（自动检测硬件、安装依赖、下载模型）
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

### 一键启动

```bash
# 启动完整应用（包含WebUI和API服务）
bash scripts/run.sh
```

启动脚本会自动完成：
1. ✅ 设置离线环境变量
2. ✅ 激活虚拟环境
3. ✅ 启动API服务
4. ✅ 启动WebUI界面
5. ✅ 打开浏览器访问

### 其他启动方式

```bash
# 1. 激活虚拟环境
source venv/bin/activate

# 2. 启动完整应用
python src/main.py

# 3. 仅启动API服务
python src/api_server.py

# 4. 仅启动PySide6桌面UI
python src/ui/ui_launcher.py

# 5. 仅启动WebUI（需要先启动API）
bash scripts/run_webui.sh

# 6. 使用离线模式启动
bash scripts/run_offline.sh
```

## 使用说明

### Web界面使用

1. 启动应用后，浏览器会自动打开WebUI界面
2. 选择搜索类型：
   - **文本搜索**: 输入关键词进行检索
   - **图像搜索**: 上传参考图像进行检索
   - **音频搜索**: 上传音频样本进行检索
3. 点击"搜索"按钮查看结果
4. 结果支持：
   - 缩略图预览
   - 相似度排序
   - 类型过滤（图像/视频/音频）
   - 时间轴展示（视频结果）

### PySide6桌面UI使用

```bash
python src/ui/ui_launcher.py
```

桌面UI功能：
- **拖拽检索**: 直接拖拽文件到搜索框自动检索
- **结果列表**: 网格/列表视图切换
- **时间轴展示**: 视频片段时间轴可视化
- **类型过滤**: 按媒体类型过滤结果
- **预览功能**: 在系统播放器中打开视频

### CLI命令行使用

```bash
# 索引测试数据
python src/cli.py index testdata

# 文本搜索
python src/cli.py search "测试查询"

# 图像搜索
python src/cli.py search --image /path/to/image.jpg

# 音频搜索
python src/cli.py search --audio /path/to/audio.mp3
```

## 目录结构

```
msearch/
├── README.md                 # 本文件
├── requirements.txt         # Python依赖
├── config/
│   └── config.yml          # 主配置文件
├── src/
│   ├── main.py             # 主程序入口
│   ├── api_server.py       # API服务器
│   ├── core/               # 核心模块
│   ├── services/           # 服务层
│   ├── ui/                 # PySide6桌面UI
│   └── webui/              # Web界面
├── scripts/
│   ├── install.sh          # 一键安装脚本
│   ├── run.sh              # 一键启动脚本
│   └── setup_models.py     # 模型管理脚本
├── tests/                  # 测试文件
└── testdata/               # 测试数据
```

## 配置说明

### 模型配置

系统支持多种AI模型，根据硬件自动选择：

| 硬件配置 | 推荐模型 | 向量维度 | 设备 |
|---------|---------|---------|------|
| 低配（CPU/4GB） | chinese-clip-base | 512 | CPU |
| 中配（CPU/8GB或GPU/4GB） | chinese-clip-large | 768 | CPU/GPU |
| 高配（GPU/16GB+） | colqwen3-turbo | 512 | GPU |

### 离线模式配置

系统默认配置为完全离线模式：

```bash
# 离线模式环境变量（自动设置）
export HF_HOME="data/models"
export TRANSFORMERS_OFFLINE=1
export HF_DATASETS_OFFLINE=1
export HF_HUB_OFFLINE=1
```

## 故障排除

### 模型下载失败

```bash
# 使用国内镜像重新下载
export HF_ENDPOINT=https://hf-mirror.com
python scripts/setup_models.py setup

# 或者强制重新下载
python scripts/setup_models.py setup --force
```

### 模型加载错误

```bash
# 检查模型完整性
python scripts/setup_models.py check

# 检查环境变量
echo $HF_HOME
echo $TRANSFORMERS_OFFLINE
```

### 端口冲突

```bash
# 修改API端口（编辑config/config.yml）
# api:
#   host: 0.0.0.0
#   port: 8001  # 修改为其他端口
```

## 技术栈

- **语言**: Python 3.8+
- **AI推理**: Python原生集成（直接模型调用）
- **PyTorch**: torch>=2.8.0
- **模型框架**: [michaelfeil/infinity](https://github.com/michaelfeil/infinity)
- **图像/视频模型**: OFA-Sys/chinese-clip-vit-* 系列
- **音频模型**: CLAP
- **向量存储**: LanceDB
- **元数据存储**: SQLite
- **Web框架**: FastAPI
- **桌面UI**: PySide6
- **媒体处理**: FFmpeg, OpenCV, Librosa

## 文档

- [设计文档](docs/design.md) - 系统架构和设计说明
- [API文档](docs/api.md) - RESTful API接口文档
- [任务列表](docs/tasks.md) - 开发任务列表

## 许可证

MIT License

## 联系方式

- 问题反馈: GitHub Issues
- 技术支持: 查看文档或提交Issue