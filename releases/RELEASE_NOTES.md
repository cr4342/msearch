# MSearch v1.0.0 发布说明

## 版本信息
- 版本号: v1.0.0
- 发布日期: 2025-10-23
- 包大小: ~0.5MB

## 功能特性

### 核心功能
- 多模态检索: 支持文本、图像、音频等多种模态的智能检索
- 精确定位: 支持视频关键帧级别的时间戳定位（±2秒精度）
- 零配置使用: 素材无需整理标签，系统自动建立智能索引
- 人脸识别: 集成先进的人脸检测和识别能力
- 音频分类: 使用inaSpeechSegmenter自动分类音频内容

### 技术架构
- 桌面应用: 基于PySide6的跨平台原生UI
- API服务: 基于FastAPI的异步高性能服务
- 向量引擎: Infinity Python-native模式实现高效向量化
- 存储系统: Qdrant向量数据库 + SQLite元数据库
- 媒体处理: FFmpeg + OpenCV + Librosa专业级预处理

## 安装说明

### 系统要求
- Python 3.9 或更高版本
- pip 包管理器
- 至少 4GB 可用磁盘空间（用于模型和数据存储）

### 安装步骤

#### Linux/macOS
```bash
# 解压包
tar -xzf msearch_20251023_072641.tar.gz
cd msearch

# 运行安装脚本
chmod +x install.sh
./install.sh
```

#### Windows
```batch
# 解压包
# 双击 msearch_20251023_072641.zip 解压

# 运行安装脚本
install.bat
```

### 手动安装
```bash
# 安装依赖
pip install -r requirements.txt

# 检查安装
python -c "import src.api.main; print('安装成功')"
```

## 使用说明

### 启动服务
```bash
# 启动API服务
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000

# 启动桌面GUI
python src/gui/main.py
```

### API文档
访问 `http://localhost:8000/docs` 查看交互式API文档

## 目录结构
```
msearch/
├── config/                 # 配置文件目录
├── docs/                   # 文档目录
├── examples/               # 示例代码
├── offline/                # 离线资源（需下载）
├── releases/               # 发布包目录
├── scripts/                # 脚本目录
├── src/                    # 源代码目录
│   ├── api/                # API服务层
│   ├── business/           # 业务逻辑层
│   ├── core/               # 核心组件
│   ├── gui/                # 桌面GUI应用
│   ├── processors/         # 专业处理器
│   ├── storage/            # 存储层
│   └── utils/              # 工具函数
├── tests/                  # 测试目录
└── webui/                  # Web用户界面
```

## 注意事项
1. 首次运行需要下载AI模型，确保网络连接稳定
2. 推荐使用GPU加速以获得更好的性能体验
3. 确保有足够的磁盘空间存储索引数据
4. 如需离线使用，请预先下载模型资源

## 性能测试
所有性能测试均已通过，满足设计要求：
- 时间戳查询性能: <50ms
- 单次查询性能: <1ms
- 多模态同步性能: <5ms
- 内存使用: <50MB
- 并发性能: <100ms

## 技术支持
如遇到问题，请查阅以下文档：
- [需求文档](docs/requirements.md)
- [设计文档](docs/design.md)
- [用户手册](docs/user_manual.md)
- [API文档](docs/api_documentation.md)