#!/usr/bin/env python3
# 修复配置文件，移除Qdrant相关配置，添加FAISS相关配置

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
SRC_DIR = PROJECT_ROOT / "src"


def fix_config_py():
    """修复config.py文件"""
    print("修复 src/core/config.py...")
    file_path = SRC_DIR / "core" / "config.py"
    
    # 读取文件内容
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    # 删除QdrantConfig类
    in_qdrant_config = False
    fixed_lines = []
    for line in lines:
        if '@dataclass' in line and 'QdrantConfig' in lines[lines.index(line) + 1]:
            in_qdrant_config = True
            continue
        if in_qdrant_config:
            if '@dataclass' in line and line.strip() == '@dataclass':
                in_qdrant_config = False
            continue
        fixed_lines.append(line)
    
    # 修复DatabaseConfig类
    fixed_content = ''.join(fixed_lines)
    fixed_content = fixed_content.replace('qdrant: QdrantConfig = None', 'faiss: Dict[str, Any] = None')
    fixed_content = fixed_content.replace('        if self.qdrant is None:\n            self.qdrant = QdrantConfig()', '        if self.faiss is None:\n            self.faiss = {}')
    
    # 添加必要的导入
    if 'from typing import' in fixed_content and 'Dict, Any' not in fixed_content:
        fixed_content = fixed_content.replace('from typing import', 'from typing import Dict, Any,')
    
    # 保存修复后的内容
    with open(file_path, 'w') as f:
        f.write(fixed_content)
    
    print("  ✅ src/core/config.py 修复完成")


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
        content = content.replace('                qdrant_point_id TEXT,', '                # qdrant_point_id TEXT, (removed, using FAISS)')
        content = content.replace('                            model_name, vector_type, qdrant_point_id, created_at', '                            model_name, vector_type, NULL, created_at')
        
        # 保存修复后的内容
        with open(full_path, 'w') as f:
            f.write(content)
        
        print(f"  ✅ {file_path} 修复完成")


def fix_orchestrator_py():
    """修复orchestrator.py文件"""
    print("修复 src/processing_service/orchestrator.py...")
    file_path = SRC_DIR / "processing_service" / "orchestrator.py"
    
    # 读取文件内容
    with open(file_path, 'r') as f:
        content = f.read()
    
    # 替换Qdrant相关的注释和描述
    content = content.replace('# 存储向量到Qdrant向量数据库', '# 存储向量到FAISS索引')
    content = content.replace('# 批量存储向量到Qdrant', '# 批量存储向量到FAISS')
    content = content.replace('self.logger.debug(f"向量存储到Qdrant成功: {len(vector_ids)}个向量")', 'self.logger.debug(f"向量存储到FAISS成功: {len(vector_ids)}个向量")')
    
    # 保存修复后的内容
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("  ✅ src/processing_service/orchestrator.py 修复完成")


def fix_vector_storage_manager_py():
    """修复vector_storage_manager.py文件"""
    print("修复 src/common/storage/vector_storage_manager.py...")
    file_path = SRC_DIR / "common" / "storage" / "vector_storage_manager.py"
    
    # 读取文件内容
    with open(file_path, 'r') as f:
        content = f.read()
    
    # 替换Qdrant相关的注释
    content = content.replace('使用Qdrant作为向量数据库后端，提供统一的接口进行向量操作。', '使用FAISS作为向量数据库后端，提供统一的接口进行向量操作。')
    content = content.replace('        qdrant_adapter: Qdrant数据库适配器', '        faiss_adapter: FAISS数据库适配器')
    
    # 保存修复后的内容
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("  ✅ src/common/storage/vector_storage_manager.py 修复完成")


def main():
    """修复所有配置文件"""
    print("开始修复配置文件...")
    
    fix_config_py()
    fix_database_adapter_files()
    fix_orchestrator_py()
    fix_vector_storage_manager_py()
    
    print("\n所有配置文件修复完成！")


if __name__ == "__main__":
    main()