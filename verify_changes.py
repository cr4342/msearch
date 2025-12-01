#!/usr/bin/env python3
"""
验证代码修改脚本
通过检查文件内容验证我们的修改是否正确
"""

import sys
import re
from pathlib import Path

def check_file_content(file_path, checks):
    """检查文件内容是否符合要求"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        for check_name, pattern, should_exist in checks:
            matches = re.search(pattern, content, re.MULTILINE)
            if should_exist and not matches:
                print(f"❌ {file_path}: {check_name} - 未找到匹配内容")
                return False
            elif not should_exist and matches:
                print(f"❌ {file_path}: {check_name} - 找到了不应存在的内容")
                return False
        
        print(f"✓ {file_path} 验证通过")
        return True
    except Exception as e:
        print(f"❌ 读取文件失败 {file_path}: {e}")
        return False

# 定义文件路径
project_root = Path(__file__).parent
engine_file = project_root / "src" / "common" / "embedding" / "embedding_engine.py"
optimized_file = project_root / "src" / "common" / "embedding" / "embedding_engine_optimized.py"

# 定义embedding_engine.py的检查项
engine_checks = [
    ("移除了embed_image_async", r"def embed_image_async", False),
    ("移除了embed_audio_music_async", r"def embed_audio_music_async", False),
    ("保留了embed_image", r"def embed_image", True),
    ("保留了embed_audio_music", r"def embed_audio_music", True),
    ("重命名为transcribe_and_embed", r"def transcribe_and_embed", True),
    ("移除了transcribe_and_embed_async", r"def transcribe_and_embed_async", False),
]

# 定义embedding_engine_optimized.py的检查项
optimized_checks = [
    ("添加了transcribe_and_embed方法", r"def transcribe_and_embed", True),
    ("包含缓存检查", r"cache_key", True),
    ("调用了transcribe_audio", r"transcribe_audio", True),
    ("调用了embed_text_for_visual", r"embed_text_for_visual", True),
]

print("开始验证代码修改...\n")

# 执行检查
engine_result = check_file_content(engine_file, engine_checks)
print()
optimized_result = check_file_content(optimized_file, optimized_checks)

# 输出结果
if engine_result and optimized_result:
    print("\n🎉 所有代码修改验证通过！")
    sys.exit(0)
else:
    print("\n❌ 验证失败，请检查上述错误。")
    sys.exit(1)
