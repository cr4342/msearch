# 部署和测试指南

## 环境准备

### 1. 安装Python
确保系统中安装了Python 3.8或更高版本：

```bash
# 检查Python版本
python --version

# 如果没有安装Python，请从 https://www.python.org/downloads/ 下载并安装
```

### 2. 安装依赖
```bash
# 进入项目根目录
cd msearch

# 安装项目依赖
pip install -r requirements.txt
```

## 运行测试

### 1. 运行单元测试
```bash
# 运行所有单元测试
python -m pytest tests/unit/ -v

# 运行特定测试文件
python -m pytest tests/unit/test_processing_orchestrator.py -v
```

### 2. 运行集成测试
```bash
# 运行集成测试
python -m pytest tests/integration/ -v
```

### 3. 运行所有测试
```bash
# 运行所有测试并生成覆盖率报告
python tests/run_tests.py --coverage
```

## 启动服务

### 1. 启动API服务
```bash
# 启动FastAPI服务
python src/api/main.py
```

默认情况下，服务将在 `http://localhost:8000` 上运行。

### 2. 访问API文档
启动服务后，可以通过以下URL访问API文档：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API使用示例

### 1. 文本搜索
```bash
curl -X POST "http://localhost:8000/api/v1/search/text" \
  -H "Content-Type: application/json" \
  -d '{"query": "人工智能技术", "limit": 10}'
```

### 2. 图像搜索
```bash
curl -X POST "http://localhost:8000/api/v1/search/image" \
  -F "file=@image.jpg"
```

### 3. 多模态搜索
```bash
curl -X POST "http://localhost:8000/api/v1/search/multimodal" \
  -F "query_text=风景照片"
```

## 离线部署

### 1. 下载离线资源
```bash
# 下载模型和其他离线资源
bash scripts/download_model_resources.sh
```

### 2. 绿色安装
项目支持绿色安装部署，所有依赖和资源都可以离线安装。

## 常见问题

### 1. 依赖安装问题
如果遇到依赖安装问题，可以尝试使用国内镜像源：
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 2. 模型下载问题
如果遇到模型下载问题，可以手动下载模型文件并放置到相应目录。

### 3. GPU支持
如果系统有NVIDIA GPU，可以安装CUDA支持以提升性能：
```bash
# 安装CUDA支持的PyTorch
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

## 性能优化建议

1. **硬件配置**：
   - 推荐使用具有CUDA支持的NVIDIA GPU
   - 至少16GB内存
   - SSD存储以提升I/O性能

2. **配置调优**：
   - 根据硬件性能调整 `max_concurrent_tasks` 参数
   - 根据GPU内存调整批处理大小

3. **模型选择**：
   - 根据硬件配置选择合适的模型版本
   - 在性能和精度之间找到平衡点

## 监控和日志

### 1. 日志查看
```bash
# 查看主日志
tail -f data/logs/msearch.log

# 查看错误日志
tail -f data/logs/error.log
```

### 2. 性能监控
系统会自动记录性能日志，可以通过以下命令查看：
```bash
# 查看性能日志
tail -f data/logs/performance.log
```
