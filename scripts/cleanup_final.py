#!/usr/bin/env python3
# 最终清理脚本

import os
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

# 清理database_adapter.py文件
def cleanup_database_adapter():
    file_path = PROJECT_ROOT / "src" / "common" / "storage" / "database_adapter.py"
    print(f"清理 {file_path}...")
    
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    # 清理第109行的qdrant_point_id字段
    for i, line in enumerate(lines):
        if "qdrant_point_id TEXT," in line:
            lines[i] = line.replace("qdrant_point_id TEXT,", "-- qdrant_point_id TEXT, -- FAISS doesn't use point IDs\n")
            break
    
    # 清理第612行的qdrant_point_id引用
    for i, line in enumerate(lines):
        if "model_name, vector_type, qdrant_point_id, created_at" in line:
            lines[i] = line.replace("model_name, vector_type, qdrant_point_id, created_at", "model_name, vector_type, NULL, created_at")
            break
    
    # 保存修复后的文件
    with open(file_path, 'w') as f:
        f.writelines(lines)
    print("✅ database_adapter.py 清理完成")

# 清理database_adapter_optimized.py文件
def cleanup_database_adapter_optimized():
    file_path = PROJECT_ROOT / "src" / "core" / "database_adapter_optimized.py"
    print(f"清理 {file_path}...")
    
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    # 清理qdrant_point_id字段
    for i, line in enumerate(lines):
        if "qdrant_point_id TEXT," in line:
            lines[i] = line.replace("qdrant_point_id TEXT,", "-- qdrant_point_id TEXT, -- FAISS doesn't use point IDs\n")
            break
    
    # 保存修复后的文件
    with open(file_path, 'w') as f:
        f.writelines(lines)
    print("✅ database_adapter_optimized.py 清理完成")

# 清理orchestrator.py文件
def cleanup_orchestrator():
    file_path = PROJECT_ROOT / "src" / "processing_service" / "orchestrator.py"
    print(f"清理 {file_path}...")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # 替换Qdrant相关的注释和日志
    content = content.replace("存储向量到Qdrant向量数据库", "存储向量到FAISS索引")
    content = content.replace("批量存储向量到Qdrant", "批量存储向量到FAISS")
    content = content.replace("向量存储到Qdrant成功", "向量存储到FAISS成功")
    
    # 保存修复后的文件
    with open(file_path, 'w') as f:
        f.write(content)
    print("✅ orchestrator.py 清理完成")

# 清理vector_storage_manager.py文件
def cleanup_vector_storage_manager():
    file_path = PROJECT_ROOT / "src" / "common" / "storage" / "vector_storage_manager.py"
    print(f"清理 {file_path}...")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # 替换Qdrant相关的注释
    content = content.replace("使用Qdrant作为向量数据库后端，提供统一的接口进行向量操作。", "使用FAISS作为向量数据库后端，提供统一的接口进行向量操作。")
    content = content.replace("    qdrant_adapter: Qdrant数据库适配器", "    faiss_adapter: FAISS数据库适配器")
    
    # 保存修复后的文件
    with open(file_path, 'w') as f:
        f.write(content)
    print("✅ vector_storage_manager.py 清理完成")

# 主函数
def main():
    print("开始最终清理...")
    cleanup_database_adapter()
    cleanup_database_adapter_optimized()
    cleanup_orchestrator()
    cleanup_vector_storage_manager()
    print("\n所有清理操作完成！")

if __name__ == "__main__":
    main()