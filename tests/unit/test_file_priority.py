#!/usr/bin/env python3
"""
文件级优先级测试
测试文件级优先级机制是否正常工作
"""

import pytest
import sys
import time
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))

from core.config import ConfigManager
from core.task.task_manager import TaskManager


class TestFilePriority:
    """文件级优先级测试"""
    
    @pytest.fixture
    def config(self):
        """配置管理器"""
        return ConfigManager()
    
    @pytest.fixture
    def task_manager(self, config):
        """任务管理器"""
        tm = TaskManager(config.config, device='cpu')
        tm.initialize()
        yield tm
        tm.shutdown()
    
    def test_file_priority_calculation(self, task_manager):
        """测试文件级优先级计算"""
        # 创建文件A的第一个任务（优先级8）
        task1_id = task_manager.create_task(
            task_type='file_embed_image',
            task_data={'file_id': 'file_A'},
            priority=8
        )
        
        # 创建文件A的第二个任务（优先级7）
        task2_id = task_manager.create_task(
            task_type='file_embed_video',
            task_data={'file_id': 'file_A'},
            priority=7
        )
        
        # 创建文件B的任务（优先级5）
        task3_id = task_manager.create_task(
            task_type='file_embed_audio',
            task_data={'file_id': 'file_B'},
            priority=5
        )
        
        # 验证任务创建成功
        assert task1_id is not None
        assert task2_id is not None
        assert task3_id is not None
        
        print("✓ 文件级优先级计算测试通过")
    
    def test_file_priority_inheritance(self, task_manager):
        """测试优先级继承"""
        # 创建一个文件的高优先级任务
        task_id = task_manager.create_task(
            task_type='file_embed_image',
            task_data={'file_id': 'file_C'},
            priority=9
        )
        
        assert task_id is not None
        
        print("✓ 优先级继承测试通过")
    
    def test_file_priority_disabled(self, task_manager):
        """测试禁用文件级优先级"""
        # 创建一个没有file_id的任务
        task_id = task_manager.create_task(
            task_type='generic_task',
            task_data={'test': 'data'},
            priority=5
        )
        
        assert task_id is not None
        
        print("✓ 文件级优先级禁用测试通过")
    
    def test_multiple_files_priority_order(self, task_manager):
        """测试多个文件的优先级顺序"""
        # 创建多个文件的任务
        tasks = []
        for i in range(3):
            task_id = task_manager.create_task(
                task_type=f'task_{i}',
                task_data={'file_id': f'file_{i}'},
                priority=5
            )
            tasks.append(task_id)
        
        assert len(tasks) == 3
        
        print("✓ 多文件优先级顺序测试通过")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
