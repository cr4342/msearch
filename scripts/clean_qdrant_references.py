#!/usr/bin/env python3
# 清理所有脚本中的Qdrant相关引用

import os
import re
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

# 需要清理的文件
FILES_TO_CLEAN = [
    "download_all_resources.sh",
    "install.sh",
    "hardware_analysis.py",
    "build_with_nuitka.sh"
]

# Qdrant相关的模式
QDRANT_PATTERNS = [
    # 移除QDRANT_FILENAME相关代码
    r'\s*QDRANT_FILENAME="qdrant-[^"]+".*',
    # 移除qdrant-client从依赖列表中
    r'\s*["\']qdrant-client["\'],?',
    r'\s*["\']qdrant_client["\'],?',
    # 移除启动Qdrant的提示
    r'\s*1\. 启动Qdrant服务: ./scripts/start_qdrant.sh\n',
    # 移除Qdrant相关的注释
    r'\s*#.*Qdrant.*',
]

def clean_file(file_path):
    """清理单个文件中的Qdrant引用"""
    print(f"清理文件: {file_path}")
    
    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 应用所有清理模式
    original_content = content
    for pattern in QDRANT_PATTERNS:
        content = re.sub(pattern, '', content, flags=re.IGNORECASE)
    
    # 移除空行
    lines = content.splitlines()
    cleaned_lines = [line for line in lines if line.strip()]
    content = '\n'.join(cleaned_lines) + '\n'
    
    # 保存清理后的内容
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✅ 清理完成")
    else:
        print(f"  ✅ 无需清理")

def main():
    """清理所有脚本中的Qdrant引用"""
    print("开始清理脚本中的Qdrant引用...")
    
    for file_name in FILES_TO_CLEAN:
        file_path = SCRIPTS_DIR / file_name
        if file_path.exists():
            clean_file(file_path)
        else:
            print(f"⚠️ 文件不存在: {file_path}")
    
    print("\n所有清理操作已完成！")

if __name__ == "__main__":
    main()