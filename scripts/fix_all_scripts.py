#!/usr/bin/env python3
# 修复所有脚本，确保它们与FAISS兼容

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

def fix_download_all_resources():
    """修复download_all_resources.sh脚本，移除Qdrant相关代码"""
    print("修复 download_all_resources.sh...")
    file_path = SCRIPTS_DIR / "download_all_resources.sh"
    
    # 读取文件内容
    with open(file_path, 'r') as f:
        content = f.read()
    
    # 移除Qdrant相关代码
    content = content.replace('            QDRANT_FILENAME="qdrant-${ARCH}-unknown-linux-gnu.${FILE_EXT}"', '            # Qdrant support removed, using FAISS instead')
    content = content.replace('            QDRANT_FILENAME="qdrant-${ARCH}-${OS}.${FILE_EXT}"', '            # Qdrant support removed, using FAISS instead')
    content = content.replace('    key_packages=("torch" "transformers" "fastapi" "qdrant-client" "inaspeechsegmenter" "infinity_emb")', '    key_packages=("torch" "transformers" "fastapi" "inaspeechsegmenter" "infinity_emb")')
    content = content.replace('            "qdrant-client"', '            # "qdrant-client" removed, using FAISS instead')
    content = content.replace('        "qdrant_client"', '        # "qdrant_client" removed, using FAISS instead')
    content = content.replace('    echo "1. 启动Qdrant服务: ./scripts/start_qdrant.sh"', '')
    
    # 保存修改后的内容
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("  ✅ download_all_resources.sh 修复完成")

def fix_hardware_analysis():
    """修复hardware_analysis.py脚本，移除Qdrant相关代码"""
    print("修复 hardware_analysis.py...")
    file_path = SCRIPTS_DIR / "hardware_analysis.py"
    
    # 读取文件内容
    with open(file_path, 'r') as f:
        content = f.read()
    
    # 移除Qdrant相关代码
    content = content.replace('qdrant_memory_limit', 'faiss_memory_limit')
    content = content.replace('"qdrant": {', '# "qdrant": {')
    content = content.replace('    "memory_limit": f"{qdrant_memory_limit}MB",', '#    "memory_limit": f"{faiss_memory_limit}MB",')
    content = content.replace('    "service": {', '#    "service": {')
    content = content.replace('        "enabled": True', '#        "enabled": True')
    content = content.replace('    }', '#    }')
    content = content.replace('}', '}')
    
    # 保存修改后的内容
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("  ✅ hardware_analysis.py 修复完成")

def main():
    """修复所有脚本"""
    print("开始修复所有脚本...")
    
    # 修复各个脚本
    fix_download_all_resources()
    fix_hardware_analysis()
    
    print("\n所有脚本修复完成！")

if __name__ == "__main__":
    main()