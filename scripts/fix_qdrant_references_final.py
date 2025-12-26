#!/usr/bin/env python3
# 最终清理所有代码中的Qdrant相关引用

import os
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
SRC_DIR = PROJECT_ROOT / "src"


def fix_database_adapter_files():
    """修复数据库适配器文件"""
    files_to_fix = [
        "src/common/storage/database_adapter.py",
        "src/core/database_adapter_optimized.py"
    ]
    
    for file_path in files_to_fix:
        full_path = PROJECT_ROOT / file_path
        if not full_path.exists():
            print(f"⚠️ 文件不存在: {full_path}")
            continue
        
        print(f"修复 {file_path}...")
        
        # 读取文件内容
        with open(full_path, 'r') as f:
            content = f.read()
        
        # 移除qdrant_point_id字段
        content = re.sub(r'\s*qdrant_point_id TEXT,', r'\s*-- qdrant_point_id TEXT, -- FAISS doesn\'t use point ids', content)
        content = re.sub(r'model_name, vector_type, qdrant_point_id, created_at', r'model_name, vector_type, NULL, created_at', content)
        
        # 保存修复后的内容
        with open(full_path, 'w') as f:
            f.write(content)
        
        print(f"  ✅ {file_path} 修复完成")


def fix_orchestrator_file():
    """修复orchestrator.py文件"""
    file_path = SRC_DIR / "processing_service" / "orchestrator.py"
    print(f"修复 {file_path}...")
    
    # 读取文件内容
    with open(file_path, 'r') as f:
        content = f.read()
    
    # 替换Qdrant相关的注释和日志
    content = content.replace('存储向量到Qdrant向量数据库', '存储向量到FAISS索引')
    content = content.replace('批量存储向量到Qdrant', '批量存储向量到FAISS')
    content = content.replace('向量存储到Qdrant成功', '向量存储到FAISS成功')
    
    # 保存修复后的内容
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"  ✅ {file_path} 修复完成")


def fix_vector_storage_manager():
    """修复vector_storage_manager.py文件"""
    file_path = SRC_DIR / "common" / "storage" / "vector_storage_manager.py"
    print(f"修复 {file_path}...")
    
    # 读取文件内容
    with open(file_path, 'r') as f:
        content = f.read()
    
    # 替换Qdrant相关的注释
    content = content.replace('使用Qdrant作为向量数据库后端，提供统一的接口进行向量操作。', '使用FAISS作为向量数据库后端，提供统一的接口进行向量操作。')
    content = content.replace('    qdrant_adapter: Qdrant数据库适配器', '    faiss_adapter: FAISS数据库适配器')
    
    # 保存修复后的内容
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"  ✅ {file_path} 修复完成")


def verify_fix():
    """验证修复结果"""
    print("\n验证修复结果...")
    
    # 检查所有Python文件中的Qdrant引用
    python_files = list(PROJECT_ROOT.glob("src/**/*.py"))
    qdrant_references = []
    
    for file_path in python_files:
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            if 'qdrant' in content.lower():
                qdrant_references.append(file_path)
        except Exception as e:
            print(f"⚠️ 读取文件失败: {file_path}")
    
    if qdrant_references:
        print(f"❌ 仍有 {len(qdrant_references)} 个文件包含Qdrant引用:")
        for file_path in qdrant_references:
            print(f"  - {file_path}")
    else:
        print("✅ 所有Python文件中的Qdrant引用已清理完毕！")


def main():
    """执行所有修复操作"""
    print("开始最终清理代码中的Qdrant引用...")
    
    fix_database_adapter_files()
    fix_orchestrator_file()
    fix_vector_storage_manager()
    
    verify_fix()
    
    print("\n所有修复操作已完成！")


if __name__ == "__main__":
    main()