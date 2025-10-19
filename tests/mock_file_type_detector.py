#!/usr/bin/env python3
"""
文件类型检测器的模拟实现
为测试环境提供文件类型检测功能，解决Windows路径问题
"""
import os
import sys
from pathlib import Path

# 强制将/tmp路径映射到Windows临时目录
def detect_file_type(file_path):
    """
    检测文件类型（模拟实现）
    返回包含mime_type和file_category的字典
    """
    # 处理/tmp路径
    file_path_str = str(file_path)  # 确保是字符串类型
    if file_path_str.startswith('/tmp/'):
        filename = os.path.basename(file_path_str)
        # 获取正确的临时目录路径
        temp_dir = os.environ.get('TEMP_TEST_DIR')
        if not temp_dir:
            project_root = Path(__file__).parent.parent
            temp_dir = project_root / "tests" / "temp"
        
        # 构建正确的文件路径
        file_path_str = os.path.join(str(temp_dir), filename)
    
    # 默认的文件类型映射
    mime_types = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.mp3': 'audio/mpeg',
        '.mp4': 'video/mp4'
    }
    
    file_categories = {
        '.jpg': 'image',
        '.jpeg': 'image',
        '.mp3': 'audio',
        '.mp4': 'video'
    }
    
    ext = os.path.splitext(file_path_str)[1].lower()
    
    # 返回与真实实现兼容的格式
    return {
        'mime_type': mime_types.get(ext, 'application/octet-stream'),
        'file_category': file_categories.get(ext, 'other'),
        'extension': ext
    }

# 获取测试文件路径
def get_test_file_path(filename):
    """
    获取测试文件的完整路径
    支持在Windows环境下自动找到正确的测试文件位置
    """
    # 首先检查TEMP_TEST_DIR环境变量
    temp_dir = os.environ.get('TEMP_TEST_DIR')
    if not temp_dir:
        # 如果没有设置环境变量，使用默认路径
        project_root = Path(__file__).parent.parent
        temp_dir = project_root / "tests" / "temp"
    
    # 构建完整路径
    file_path = os.path.join(str(temp_dir), filename)
    
    # 确保文件存在
    if not os.path.exists(file_path):
        print(f"警告：测试文件不存在: {file_path}")
    
    return file_path
        