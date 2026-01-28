#!/usr/bin/env python3
"""
检查向量数据库内容
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))

from src.core.config.config_manager import ConfigManager
from src.core.vector.vector_store import VectorStore


def check_vector_db():
    """检查向量数据库内容"""
    print("="*60)
    print("向量数据库内容检查")
    print("="*60)
    
    # 加载配置
    config_manager = ConfigManager('config/config.yml')
    config = config_manager.get_all()
    
    # 初始化向量存储
    vector_store_config = {
        'data_dir': config.get('database.lancedb.data_dir', 'data/database/lancedb'),
        'collection_name': config.get('database.lancedb.collection_name', 'unified_vectors'),
        'index_type': config.get('database.lancedb.index_type', 'ivf_pq'),
        'num_partitions': config.get('database.lancedb.num_partitions', 128),
        'vector_dimension': config.get('database.lancedb.vector_dimension', 512)
    }
    vector_store = VectorStore(vector_store_config)
    
    # 获取所有向量
    print("\n获取所有向量数据...")
    try:
        import lancedb
        db = lancedb.connect(vector_store_config['data_dir'])
        table = db.open_table(vector_store_config['collection_name'])
        
        # 获取所有数据
        all_data = table.to_pandas()
        print(f"总记录数: {len(all_data)}")
        
        # 显示前10条记录
        print("\n前10条记录:")
        print("="*60)
        for i, row in all_data.head(10).iterrows():
            print(f"\n记录 {i+1}:")
            print(f"  ID: {row.get('id', 'N/A')}")
            print(f"  文件名: {row.get('file_name', 'N/A')}")
            print(f"  文件路径: {row.get('file_path', 'N/A')}")
            print(f"  媒体类型: {row.get('media_type', 'N/A')}")
            print(f"  模态: {row.get('modality', 'N/A')}")
            print(f"  向量维度: {len(row.get('embedding', []))}")
        
        # 统计媒体类型
        print("\n媒体类型统计:")
        print("="*60)
        media_types = all_data['media_type'].value_counts()
        for media_type, count in media_types.items():
            print(f"  {media_type}: {count}")
        
        # 统计模态
        print("\n模态统计:")
        print("="*60)
        modalities = all_data['modality'].value_counts()
        for modality, count in modalities.items():
            print(f"  {modality}: {count}")
        
        # 检查缺失的文件名
        missing_names = all_data[all_data['file_name'].isna() | (all_data['file_name'] == '')]
        print(f"\n缺失文件名的记录数: {len(missing_names)}")
        
        # 检查缺失的路径
        missing_paths = all_data[all_data['file_path'].isna() | (all_data['file_path'] == '')]
        print(f"缺失文件路径的记录数: {len(missing_paths)}")
        
    except Exception as e:
        print(f"检查失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    check_vector_db()
