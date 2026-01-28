# msearch WebUI

msearch 多模态检索系统的 Web 用户界面。

## 功能

- **多模态搜索**: 支持文本、图像、音频搜索
- **任务管理**: 查看和管理后台任务
- **文件管理**: 查看已索引的文件
- **系统状态**: 查看系统运行状态

## 使用方法

1. 启动 API 服务器: `python3 src/api_server.py`
2. 打开浏览器访问: `http://localhost:8000`
3. 或直接访问: `http://localhost:8000/webui/index.html`

## 文件说明

- `index.html`: 主页面
- `styles.css`: 样式文件
- `app.js`: 前端交互逻辑
