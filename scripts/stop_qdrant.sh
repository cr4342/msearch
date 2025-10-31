#!/bin/bash
# Qdrant服务停止脚本

echo "停止Qdrant服务..."

# 停止进程
if [ -f /tmp/qdrant.pid ]; then
    kill $(cat /tmp/qdrant.pid) 2>/dev/null && rm /tmp/qdrant.pid
    echo "Qdrant进程已停止"
fi

# 停止Docker容器
if command -v docker &> /dev/null; then
    if docker ps -q -f name=qdrant-msearch | grep -q .; then
        docker stop qdrant-msearch
        docker rm qdrant-msearch
        echo "Qdrant Docker容器已停止"
    fi
fi

echo "Qdrant服务已完全停止"