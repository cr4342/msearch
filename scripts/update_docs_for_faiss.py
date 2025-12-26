#!/usr/bin/env python3
# 更新所有文档，将Qdrant相关内容替换为FAISS

import os
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DOCS_DIR = PROJECT_ROOT / "docs"

# 需要更新的文档
DOCS_TO_UPDATE = [
    "architecture.md",
    "DATABASE_SCHEMA.md",
    "api_documentation.md",
    "FAQ.md",
    "technical_implementation.md",
    "test_strategy.md"
]

# Qdrant到FAISS的替换映射
REPLACEMENTS = {
    # 向量数据库名称替换
    "Qdrant": "FAISS",
    "qdrant": "faiss",
    "QDRANT": "FAISS",
    
    # 特定术语替换
    "qdrant-client": "faiss",
    "qdrant_client": "faiss",
    "qdrant_url": "faiss_index_path",
    "QdrantClient": "FAISSIndex",
    "qdrant_point_id": "faiss_index_id",
    "qdrant_connected": "faiss_connected",
    "qdrant_version": "faiss_version",
    
    # 配置和路径替换
    "qdrant_simple.yaml": "faiss_config.yaml",
    "./data/database/qdrant": "./data/database/faiss_indices",
    "qdrant/": "faiss_indices/",
    
    # 脚本名称替换
    "start_qdrant_optimized.sh": "# start_qdrant_optimized.sh (removed)",
    "stop_qdrant.sh": "# stop_qdrant.sh (removed)",
    "backup_qdrant.py": "# backup_qdrant.py (removed)",
    "restore_qdrant.py": "# restore_qdrant.py (removed)",
    
    # 代码文件替换
    "vector_store.py     # Qdrant向量存储器": "vector_store.py     # FAISS向量存储器",
    
    # 功能描述替换
    "Qdrant向量数据库操作封装": "FAISS向量数据库操作封装",
    "同时将向量上传到Qdrant向量数据库": "同时将向量存储到FAISS索引",
    "同时从Qdrant向量数据库中删除对应的向量": "同时从FAISS索引中删除对应的向量",
    "使用查询向量在Qdrant中检索相似向量": "使用查询向量在FAISS中检索相似向量",
    "获取 `qdrant_point_id` 列表": "获取 `faiss_index_id` 列表",
    "根据 `qdrant_point_id` 在 `vectors` 表中查找对应的记录": "根据 `faiss_index_id` 在 `vectors` 表中查找对应的记录",
    
    # 命令替换
    "lsof -i :6333  # 检查Qdrant端口": "# lsof -i :6333  # 检查Qdrant端口 (removed)",
    "python scripts/backup_qdrant.py": "# python scripts/backup_qdrant.py (removed)",
    "python scripts/restore_qdrant.py --backup-file <backup_file>": "# python scripts/restore_qdrant.py --backup-file <backup_file> (removed)",
    
    # 其他替换
    "bash scripts/start_qdrant_optimized.sh": "# bash scripts/start_qdrant_optimized.sh (removed)",
    "bash scripts/stop_qdrant.sh": "# bash scripts/stop_qdrant.sh (removed)",
    "# config/qdrant_simple.yaml": "# config/faiss_config.yaml",
    "  storage_path: ./data/database/qdrant": "  storage_path: ./data/database/faiss_indices",
    
    # 技术栈替换
    "| 向量数据库 | Qdrant | ≥1.7.0 |": "| 向量数据库 | FAISS | ≥1.7.0 |",
    "在 msearch 系统中，我们采用分离式架构：**michaelfeil/infinity** 负责AI模型推理和向量生成，**Qdrant** 负责向量存储和相似性搜索：": "在 msearch 系统中，我们采用分离式架构：**michaelfeil/infinity** 负责AI模型推理和向量生成，**FAISS** 负责向量存储和相似性搜索：",
    "- **Qdrant**：专门的向量数据库，提供高性能的向量存储和相似性搜索": "- **FAISS**：专门的向量数据库，提供高性能的向量存储和相似性搜索",
    "| **技术栈验证** | 重点测试michaelfeil/infinity、Qdrant、SQLite、FastAPI集成 | 验证核心技术选型 |": "| **技术栈验证** | 重点测试michaelfeil/infinity、FAISS、SQLite、FastAPI集成 | 验证核心技术选型 |",
    
    # 问题解决替换
    "### 10.2 Qdrant启动问题解决": "### 10.2 FAISS索引维护问题解决",
    "- Qdrant服务启动失败或端口冲突": "- FAISS索引加载失败或损坏",
    "# 使用优化的Qdrant启动脚本": "# 使用优化的FAISS索引维护脚本",
    "2. **进程清理**：停止现有的Qdrant进程": "2. **索引检查**：检查FAISS索引完整性",
    "通过这些优化解决方案，可以有效解决Python 3.12兼容性、Qdrant启动和OpenCV依赖等问题，确保测试环境的稳定性和可靠性，提高测试执行的成功率和效率。": "通过这些优化解决方案，可以有效解决Python 3.12兼容性、FAISS索引维护和OpenCV依赖等问题，确保测试环境的稳定性和可靠性，提高测试执行的成功率和效率。"
}

def update_document(file_path):
    """更新单个文档，将Qdrant相关内容替换为FAISS"""
    print(f"更新文档: {file_path}")
    
    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 应用所有替换
    original_content = content
    for old, new in REPLACEMENTS.items():
        content = content.replace(old, new)
    
    # 保存更新后的内容
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✅ 更新完成")
    else:
        print(f"  ✅ 无需更新")

def main():
    """更新所有文档"""
    print("开始更新文档，将Qdrant相关内容替换为FAISS...")
    
    for doc_name in DOCS_TO_UPDATE:
        doc_path = DOCS_DIR / doc_name
        if doc_path.exists():
            update_document(doc_path)
        else:
            print(f"⚠️ 文档不存在: {doc_path}")
    
    print("\n所有文档更新完成！")

if __name__ == "__main__":
    main()