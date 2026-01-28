#!/usr/bin/env python3
"""
检查向量数据库列名
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))

from src.core.config.config_manager import ConfigManager
from src.core.vector.vector_store import VectorStore


def check_columns():
    """检查向量数据库列名"""
    print("="*60)
    print("向量数据库列名检查")
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
    
    try:
        import lancedb
        db = lancedb.connect(vector_store_config['data_dir'])
        table = db.open_table(vector_store_config['collection_name'])
        
        # 获取所有数据
        all_data = table.to_pandas()
        print(f"总记录数: {len(all_data)}")
        
        # 显示列名
        print("\n列名:")
        print("="*60)
        for col in all_data.columns:
            print(f"  - {col}")
        
        # 显示前3条记录的所有字段
        print("\n前3条记录的完整数据:")
        print("="*60)
        for i, row in all_data.head(3).iterrows():
            print(f"\n记录 {i+1}:")
            for col in all_data.columns:
                value = row[col]
                if isinstance(value, list) and len(value) > 0:
                    print(f"  {col}: [向量，长度={len(value)}]")
                else:
                    print(f"  {col}: {value}")
        
    except Exception as e:
        print(f"检查失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    check_columns()
