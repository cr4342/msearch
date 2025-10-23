#!/bin/bash
# Qdrant服务停止脚本

echo "停止Qdrant服务..."

if [ -f /tmp/qdrant.pid ]; then
    kill $(cat /tmp/qdrant.pid) 2>/dev/null && rm /tmp/qdrant.pid
    echo "Qdrant服务已停止"
else
    echo "Qdrant服务未运行"
fi