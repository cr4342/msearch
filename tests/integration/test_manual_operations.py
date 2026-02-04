#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试手动操作控制功能
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

from src.webui.app import MSearchWebUI

def test_manual_operations():
    """测试手动操作控制功能"""
    print("="*60)
    print("测试手动操作控制功能")
    print("="*60)
    
    # 初始化 WebUI
    print("\n[1/6] 初始化 WebUI...")
    webui = MSearchWebUI()
    print("✓ WebUI 初始化完成")
    
    # 测试全量扫描
    print("\n[2/6] 测试全量扫描...")
    test_dir = str(project_root / 'testdata')
    scan_result = webui.full_scan(test_dir)
    print(scan_result)
    
    # 测试启动向量化处理
    print("\n[3/6] 测试启动向量化处理...")
    vectorization_result = webui.start_vectorization(priority=5, max_concurrent=2)
    print(vectorization_result)
    
    # 测试获取任务列表
    print("\n[4/6] 测试获取任务列表...")
    task_list = webui.get_task_list()
    print(task_list)
    
    # 测试获取任务统计
    print("\n[5/6] 测试获取任务统计...")
    task_stats = webui.get_task_statistics()
    print(task_stats)
    
    # 测试获取处理进度
    print("\n[6/6] 测试获取处理进度...")
    progress = webui.get_processing_progress()
    print(progress)
    
    print("\n" + "="*60)
    print("所有测试完成")
    print("="*60)

if __name__ == '__main__':
    test_manual_operations()
