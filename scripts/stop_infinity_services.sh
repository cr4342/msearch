#!/bin/bash
# Infinity服务停止脚本

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}[INFO]${NC} 停止Infinity服务..."

# 停止各个服务
services=("clip" "clap" "whisper")

for service in "${services[@]}"; do
    pid_file="/tmp/infinity_${service}.pid"
    
    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null; then
            echo "停止${service^^}服务 (PID: $pid)..."
            kill "$pid" 2>/dev/null
            rm -f "$pid_file"
            echo -e "${GREEN}[INFO]${NC} ${service^^}服务已停止"
        else
            echo -e "${YELLOW}[WARNING]${NC} ${service^^}服务未运行 (PID文件存在但进程不存在)"
            rm -f "$pid_file"
        fi
    else
        echo -e "${YELLOW}[WARNING]${NC} ${service^^}服务PID文件不存在，可能未启动"
    fi

    # 额外检查：通过端口查找并终止进程
    case $service in
        "clip")
            port=7997
            ;;
        "clap")
            port=7998
            ;;
        "whisper")
            port=7999
            ;;
    esac
    
    # 查找监听指定端口的进程并终止
    lsof_pids=$(lsof -ti:$port 2>/dev/null || true)
    if [ -n "$lsof_pids" ]; then
        echo "发现监听端口$port的进程: $lsof_pids，正在终止..."
        kill $lsof_pids 2>/dev/null || true
    fi
    
    # 查找包含infinity_emb的进程并终止
    infinity_pids=$(pgrep -f "infinity_emb" 2>/dev/null || true)
    if [ -n "$infinity_pids" ]; then
        echo "发现infinity_emb进程: $infinity_pids，正在终止..."
        kill $infinity_pids 2>/dev/null || true
    fi
done

# 清理主服务PID文件
if [ -f /tmp/infinity_services.pid ]; then
    rm -f /tmp/infinity_services.pid
fi

# 强制清理（如果需要）
sleep 1

# 再次检查是否有残留进程
infinity_pids=$(pgrep -f "infinity_emb" 2>/dev/null || true)
if [ -n "$infinity_pids" ]; then
    echo -e "${YELLOW}[WARNING]${NC} 发现残留的infinity_emb进程，强制终止..."
    kill -9 $infinity_pids 2>/dev/null || true
fi

# 检查端口是否已释放
for port in 7997 7998 7999; do
    if lsof -ti:$port >/dev/null 2>&1; then
        echo -e "${RED}[ERROR]${NC} 端口$port仍然被占用"
    else
        echo -e "${GREEN}[INFO]${NC} 端口$port已释放"
    fi
done

echo -e "${GREEN}[INFO]${NC} Infinity服务停止完成！"
echo ""
echo "服务状态检查："
for port in 7997 7998 7999; do
    if nc -z localhost $port 2>/dev/null; then
        echo -e "端口$port: ${RED}运行中${NC}"
    else
        echo -e "端口$port: ${GREEN}已停止${NC}"
    fi
done