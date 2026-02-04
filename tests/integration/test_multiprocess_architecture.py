#!/usr/bin/env python3
"""
测试多进程架构功能
"""
import os
import sys
import time
import subprocess
import json
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_multiprocess_launcher():
    """测试多进程启动器"""
    print("测试多进程启动器...")
    
    # 检查启动脚本是否存在
    launcher_path = project_root / "scripts" / "multiprocess_launcher.py"
    assert launcher_path.exists(), f"启动脚本不存在: {launcher_path}"
    
    # 检查Redis是否可用
    print("检查Redis服务...")
    try:
        result = subprocess.run(['redis-cli', 'ping'], capture_output=True, text=True)
        redis_available = result.stdout.strip() == 'PONG'
        print(f"Redis状态: {'可用' if redis_available else '不可用'}")
    except Exception as e:
        print(f"Redis检查失败: {e}")
        redis_available = False
    
    # 如果Redis不可用，尝试启动
    if not redis_available:
        print("尝试启动Redis服务...")
        try:
            subprocess.run(['redis-server', '--daemonize', 'yes'], check=True)
            time.sleep(2)
            result = subprocess.run(['redis-cli', 'ping'], capture_output=True, text=True)
            redis_available = result.stdout.strip() == 'PONG'
            print(f"Redis启动状态: {'成功' if redis_available else '失败'}")
        except Exception as e:
            print(f"启动Redis失败: {e}")
            redis_available = False
    
    if not redis_available:
        print("警告: Redis不可用，将跳过部分测试")
    
    # 测试启动器帮助信息
    print("测试启动器帮助信息...")
    result = subprocess.run