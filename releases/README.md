# MSearch 发布包

这是 MSearch 多模态检索系统的发布包。

## 包内容

- `src/` - 源代码目录
- `config/` - 配置文件目录
- `scripts/` - 脚本文件目录
- `docs/` - 文档目录
- `examples/` - 示例代码目录
- `requirements.txt` - Python依赖列表
- `README.md` - 项目说明文件
- `IFLOW.md` - 项目上下文文档

## 安装依赖

```bash
pip install -r requirements.txt
```

## 运行程序

### 启动API服务
```bash
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

### 启动桌面GUI
```bash
python src/gui/main.py
```

## 配置

- 默认配置文件: `config/config.yml`
- 可根据需要修改配置参数