#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试实时进度监控功能
"""

import sys
import os
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root))

from webui.app import MSearchWebUI

def test_realtime_progress():
    """测试实时进度获取功能"""
    print("=" * 60)
    print("测试实时进度监控功能")
    print("=" * 60)
    
    try:
        # 初始化WebUI
        webui = MSearchWebUI()
        print("✓ WebUI初始化成功")
        
        # 测试获取实时进度
        progress_display, current_operation = webui.get_realtime_progress()
        
        print("\n--- 实时进度显示 ---")
        print(progress_display)
        
        print("\n--- 当前操作显示 ---")
        print(current_operation)
        
        # 测试任务图标获取
        print("\n--- 测试任务图标 ---")
        task_types = [
            "file_embed_image",
            "file_embed_video", 
            "file_embed_audio",
            "search_query",
            "file_scan",
            "vectorization",
            "unknown_type"
        ]
        
        for task_type in task_types:
            icon = webui._get_task_icon(task_type)
            print(f"  {task_type}: {icon}")
        
        # 测试任务操作描述
        print("\n--- 测试任务操作描述 ---")
        statuses = ["running", "paused", "completed", "failed", "pending"]
        
        for task_type in ["file_embed_image", "file_embed_video"]:
            for status in statuses:
                icon, operation = webui._get_task_operation(task_type, status)
                print(f"  {task_type} + {status}: {icon} {operation}")
        
        print("\n" + "=" * 60)
        print("✓ 所有测试通过")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = test_realtime_progress()
    sys.exit(0 if success else 1)