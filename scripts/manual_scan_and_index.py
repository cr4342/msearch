#!/usr/bin/env python3
"""
手动扫描和索引文件脚本
用于修复WebUI扫描后无法向量化的问题
"""

import os
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
src_root = project_root / "src"
sys.path.insert(0, str(src_root))
sys.path.insert(0, str(project_root))

os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['HF_DATASETS_OFFLINE'] = '1'
os.environ['HF_HUB_OFFLINE'] = '1'

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from core.config.config_manager import ConfigManager
from core.database.database_manager import DatabaseManager
from services.file.file_scanner import FileScanner
from services.file.file_indexer import FileIndexer
from data.constants import ProcessingStatus


def scan_and_index_directory(directory: str):
    """
    扫描目录并索引文件到数据库
    
    Args:
        directory: 要扫描的目录路径
    """
    print("\n" + "="*70)
    print(f"扫描并索引目录: {directory}")
    print("="*70)
    
    # 加载配置
    config_manager = ConfigManager()
    config = config_manager.get_all()
    
    # 初始化数据库
    db_path = config.get('database', {}).get('db_path', 'data/database/sqlite/msearch.db')
    db = DatabaseManager(db_path)
    db.initialize()
    
    # 初始化文件扫描器
    supported_extensions = config.get('file_monitor', {}).get('supported_extensions', [])
    file_scanner = FileScanner(supported_extensions)
    
    # 初始化文件索引器
    file_indexer = FileIndexer(config)
    
    # 扫描目录
    print(f"\n扫描目录: {directory}")
    file_paths = file_scanner.scan_directory(directory)
    print(f"找到 {len(file_paths)} 个文件")
    
    if not file_paths:
        print("没有找到文件")
        return
    
    # 显示找到的文件
    print("\n找到的文件:")
    for i, fp in enumerate(file_paths[:10], 1):
        print(f"  {i}. {Path(fp).name}")
    if len(file_paths) > 10:
        print(f"  ... 还有 {len(file_paths) - 10} 个文件")
    
    # 索引文件
    print(f"\n开始索引文件...")
    indexed_count = 0
    skipped_count = 0
    error_count = 0
    
    for file_path in file_paths:
        try:
            # 检查文件是否已存在
            existing = db.get_file_by_path(file_path)
            if existing:
                print(f"  跳过(已存在): {Path(file_path).name}")
                skipped_count += 1
                continue
            
            # 索引文件
            metadata = file_indexer.index_file(file_path, submit_task=False)
            
            if metadata:
                # 保存到数据库
                db.insert_file_metadata({
                    'id': metadata.id,
                    'file_path': metadata.file_path,
                    'file_name': metadata.file_name,
                    'file_type': metadata.file_type.value if hasattr(metadata.file_type, 'value') else str(metadata.file_type),
                    'file_size': metadata.file_size,
                    'file_hash': metadata.file_hash,
                    'created_at': metadata.created_at,
                    'updated_at': metadata.updated_at,
                    'processing_status': ProcessingStatus.PENDING.value
                })
                print(f"  ✓ 索引成功: {metadata.file_name}")
                indexed_count += 1
            else:
                print(f"  ✗ 索引失败: {Path(file_path).name}")
                error_count += 1
                
        except Exception as e:
            print(f"  ✗ 错误: {Path(file_path).name} - {e}")
            error_count += 1
    
    # 统计结果
    print("\n" + "="*70)
    print("索引结果统计")
    print("="*70)
    print(f"  总文件数: {len(file_paths)}")
    print(f"  成功索引: {indexed_count}")
    print(f"  跳过(已存在): {skipped_count}")
    print(f"  失败/错误: {error_count}")
    
    # 检查待处理文件
    pending_files = db.get_files_by_status(ProcessingStatus.PENDING.value, limit=1000)
    print(f"\n  待处理文件数: {len(pending_files)}")
    
    if pending_files:
        print("\n  待处理文件列表:")
        for f in pending_files[:10]:
            print(f"    - {f.get('file_name')} ({f.get('file_type')})")
        if len(pending_files) > 10:
            print(f"    ... 还有 {len(pending_files) - 10} 个文件")
    
    print("="*70)
    
    # 关闭数据库
    db.close()
    
    return indexed_count


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='手动扫描和索引文件')
    parser.add_argument('directory', nargs='?', default='/data/project/msearch/testdata',
                        help='要扫描的目录路径 (默认: /data/project/msearch/testdata)')
    
    args = parser.parse_args()
    
    # 检查目录是否存在
    if not Path(args.directory).exists():
        print(f"错误: 目录不存在: {args.directory}")
        sys.exit(1)
    
    # 执行扫描和索引
    count = scan_and_index_directory(args.directory)
    
    if count > 0:
        print(f"\n✓ 成功索引 {count} 个文件")
        print('\n现在可以在WebUI中点击"启动向量化处理"来处理这些文件')
    else:
        print("\n没有新文件被索引")


if __name__ == '__main__':
    main()
