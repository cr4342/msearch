## WebUI API调用修复计划

### 问题分析
当前WebUI的文字检索、图像检索、任务管理功能报错，原因是WebUI直接调用内部方法，而不是按照设计通过HTTP API调用FastAPI服务器。

### 解决方案

#### 1. 实现APIClient类
- 创建`src/webui/api_client.py`文件
- 实现HTTP请求方法，调用FastAPI端点
- 包含所有需要的API调用：文本搜索、图像搜索、任务管理等
- 处理错误和异常情况

#### 2. 修改WebUI代码
- 更新`src/webui/app.py`中的`MSearchWebUI`类
- 将直接调用内部方法的代码改为调用APIClient
- 修改以下方法：
  - `search_text()` → 使用`api_client.search_text()`
  - `search_image()` → 使用`api_client.search_image()`
  - `refresh_task_manager()` → 使用`api_client.get_all_tasks()`
  - 其他相关方法

#### 3. 配置和启动
- 确保FastAPI服务器正确运行在端口8000
- 在WebUI初始化时配置API Client的基础URL
- 启动WebUI并验证所有功能

### 技术细节
- **API Client**：使用`requests`库发送HTTP请求
- **FastAPI服务器**：运行在`http://localhost:8000`
- **WebUI**：使用Gradio框架，通过API Client调用后端API

### 预期结果
- WebUI的文字检索功能正常工作
- WebUI的图像检索功能正常工作
- WebUI的任务管理功能正常工作
- 所有功能通过HTTP API调用，符合设计要求