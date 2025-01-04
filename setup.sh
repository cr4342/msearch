#!/bin/bash

# 安装依赖
echo "Installing dependencies..."
pip install -r requirements.txt

# 初始化数据库
echo "Initializing database..."
python src/database/init_sql.py

# 启动 API
echo "Starting API..."
uvicorn src.api.main_api:app --reload