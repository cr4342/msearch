# msearch 依赖管理说明

## 依赖文件说明

msearch 项目采用分离式依赖管理，将依赖按类型分为多个文件：

### 依赖文件

- **base.txt**: 核心依赖
  - 运行 msearch 系统所需的最小依赖集
  - 包含：numpy, pandas, fastapi, lancedb, infinity-emb, sentence-transformers 等
  - 适用于：生产环境、最小化安装

- **dev.txt**: 开发依赖
  - 包含 base.txt + 开发工具
  - 包含：black, mypy, flake8, ipython, jupyter 等
  - 适用于：开发环境、代码调试

- **test.txt**: 测试依赖
  - 包含 base.txt + 测试工具
  - 包含：pytest, pytest-asyncio, pytest-cov, faker 等
  - 适用于：测试环境、CI/CD

- **optional.txt**: 可选依赖
  - 包含 base.txt + GUI 等可选功能
  - 包含：PySide6（桌面UI）等
  - 适用于：需要完整功能的场景

## 安装方式

### 1. 核心依赖（最小化安装）

```bash
pip install -r requirements.txt
# 或
pip install -r requirements/base.txt
```

### 2. 开发依赖（开发环境）

```bash
pip install -r requirements/dev.txt
```

### 3. 测试依赖（测试环境）

```bash
pip install -r requirements/test.txt
```

### 4. 可选依赖（完整功能）

```bash
pip install -r requirements/optional.txt
```

### 5. 所有依赖（完整开发环境）

```bash
pip install -r requirements/dev.txt -r requirements/test.txt -r requirements/optional.txt
```

## 国内镜像加速

使用国内 PyPI 镜像加速安装：

```bash
# 清华大学镜像
pip install -r requirements/base.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 阿里云镜像
pip install -r requirements/base.txt -i https://mirrors.aliyun.com/pypi/simple

# 中科大镜像
pip install -r requirements/base.txt -i https://pypi.mirrors.ustc.edu.cn/simple
```

## 虚拟环境建议

建议使用虚拟环境进行开发：

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 安装依赖
pip install -r requirements/dev.txt -r requirements/test.txt -r requirements/optional.txt
```

## 依赖版本管理

- 所有依赖都指定了最低版本要求（>=）
- 建议定期更新依赖版本：
  ```bash
  pip list --outdated
  pip install --upgrade package_name
  ```
- 生产环境建议锁定依赖版本：
  ```bash
  pip freeze > requirements.lock
  ```

## 常见问题

### Q: 如何只安装核心依赖？

A: 使用 `pip install -r requirements/base.txt` 或 `pip install -r requirements.txt`

### Q: 如何安装所有依赖？

A: 使用 `pip install -r requirements/dev.txt -r requirements/test.txt -r requirements/optional.txt`

### Q: 如何更新依赖？

A: 使用 `pip install --upgrade -r requirements/base.txt`（或其他依赖文件）

### Q: 如何检查依赖冲突？

A: 使用 `pip check` 命令检查依赖冲突

## 依赖说明

### 核心依赖（base.txt）

- **numpy, pandas**: 数据处理
- **infinity-emb, colpali-engine**: 高性能模型运行时
- **fastapi, uvicorn**: Web框架
- **lancedb**: 向量数据库
- **sentence-transformers**: AI模型加载
- **pillow, opencv-python, librosa**: 媒体处理

### 开发依赖（dev.txt）

- **black, mypy, flake8**: 代码格式化和检查
- **ipython, jupyter**: 交互式开发

### 测试依赖（test.txt）

- **pytest, pytest-asyncio**: 测试框架
- **pytest-cov**: 覆盖率测试

### 可选依赖（optional.txt）

- **PySide6**: 桌面UI（Qt for Python）

## 注意事项

1. Python 版本要求：Python 3.8+
2. PyTorch 版本要求：torch>=2.0.0（Infinity 和 ColPali 的基础依赖）
3. GPU 支持：推荐使用 CUDA 支持的 GPU（可选）
4. 内存要求：至少 8GB 内存（推荐 16GB+）
5. 存储空间：至少 10GB 可用存储空间

## 联系方式

如有问题，请参考项目文档或提交 Issue。