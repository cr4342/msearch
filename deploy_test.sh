#!/bin/bash

# 用于测试部署的脚本
set -e

# 颜色定义
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${GREEN}[INFO]${NC} 开始部署测试..."

# 复制项目文件到deploy_test目录
echo -e "${GREEN}[INFO]${NC} 复制项目文件..."
cp -r src config scripts requirements.txt README.md IFLOW.md .gitignore /tmp/msearch_test/
cd /tmp/msearch_test

# 创建必要目录
mkdir -p data/database logs

# 运行部署脚本
echo -e "${GREEN}[INFO]${NC} 运行部署脚本..."
bash scripts/deploy_msearch.sh

echo -e "${GREEN}[INFO]${NC} 部署测试完成！"
