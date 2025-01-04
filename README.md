# msearch

## 项目概述

开发一个基于内容理解的多模态搜索系统 msearch，旨在通过整合多种数据处理和存储技术，实现对文本、图片和视频的高效检索和管理。

## 技术栈

- 视频处理：Towhee、ffmpeg
- 向量存储：Qdrant
- 特征提取模型选项：Chinese-CLIP 或 mPLUG-Owl

## 运行项目

1. **使用 `setup.sh` 脚本**：
   ```bash
   ./setup.sh
   ```

2. 手动运行步骤：
   1. 安装依赖：
      ```bash
      pip install -r requirements.txt
      ```
   2. 初始化数据库：
      ```bash
      python src/database/init_sql.py
      ```
   3. 启动 API：
      ```bash
      uvicorn src.api.main_api:app --reload
      ```
   4. 启动 Flask 服务：
      ```bash
      python src/main.py
      ```

## 开发要求

1. 代码要符合 Python 最佳实践
2. 使用异步编程处理 I/O 密集操作
3. 实现优雅的错误处理
4. 提供清晰的文档注释
5. 包含必要的单元测试
6. 尽可能将参数放入配置文件中
7. 遵循 PEP 8 编码规范
8. 遵循 Git 版本控制规范
9. 遵循 Docker 容器化规范
10. 遵循 RESTful API 规范