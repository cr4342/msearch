#!/usr/bin/env python3
# 清理Qdrant引用的简单脚本

import os

# 修复database_adapter.py文件
def fix_database_adapter():
    print("修复 database_adapter.py...")
    with open("src/common/storage/database_adapter.py", "r") as f:
        content = f.read()
    
    content = content.replace("qdrant_point_id TEXT", "-- qdrant_point_id TEXT -- FAISS doesn't use point IDs")
    content = content.replace("model_name, vector_type, qdrant_point_id, created_at", "model_name, vector_type, NULL, created_at")
    
    with open("src/common/storage/database_adapter.py", "w") as f:
        f.write(content)
    print("✅ 完成")

# 修复database_adapter_optimized.py文件
def fix_database_adapter_optimized():
    print("修复 database_adapter_optimized.py...")
    with open("src/core/database_adapter_optimized.py", "r") as f:
        content = f.read()
    
    content = content.replace("qdrant_point_id TEXT", "-- qdrant_point_id TEXT -- FAISS doesn't use point IDs")
    
    with open("src/core/database_adapter_optimized.py", "w") as f:
        f.write(content)
    print("✅ 完成")

# 修复orchestrator.py文件
def fix_orchestrator():
    print("修复 orchestrator.py...")
    with open("src/processing_service/orchestrator.py", "r") as f:
        content = f.read()
    
    content = content.replace("存储向量到Qdrant向量数据库", "存储向量到FAISS索引")
    content = content.replace("批量存储向量到Qdrant", "批量存储向量到FAISS")
    content = content.replace("向量存储到Qdrant成功", "向量存储到FAISS成功")
    
    with open("src/processing_service/orchestrator.py", "w") as f:
        f.write(content)
    print("✅ 完成")

# 修复vector_storage_manager.py文件
def fix_vector_storage_manager():
    print("修复 vector_storage_manager.py...")
    with open("src/common/storage/vector_storage_manager.py", "r") as f:
        content = f.read()
    
    content = content.replace("使用Qdrant作为向量数据库后端", "使用FAISS作为向量数据库后端")
    content = content.replace("qdrant_adapter: Qdrant数据库适配器", "faiss_adapter: FAISS数据库适配器")
    
    with open("src/common/storage/vector_storage_manager.py", "w") as f:
        f.write(content)
    print("✅ 完成")

# 运行所有修复
if __name__ == "__main__":
    fix_database_adapter()
    fix_database_adapter_optimized()
    fix_orchestrator()
    fix_vector_storage_manager()
    print("\n所有修复完成！")
