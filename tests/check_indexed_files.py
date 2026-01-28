#!/usr/bin/env python3
"""
检查已索引的文件
"""

import sys
import json
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))

from src.core.config.config_manager import ConfigManager


def check_indexed_files():
    """检查已索引的文件"""
    print("="*60)
    print("已索引文件检查")
    print("="*60)
    
    # 加载配置
    config_manager = ConfigManager('config/config.yml')
    config = config_manager.get_all()
    
    # 连接到向量数据库
    import lancedb
    vector_store_config = {
        'data_dir': config.get('database.lancedb.data_dir', 'data/database/lancedb'),
        'collection_name': config.get('database.lancedb.collection_name', 'unified_vectors'),
    }
    
    try:
        db = lancedb.connect(vector_store_config['data_dir'])
        table = db.open_table(vector_store_config['collection_name'])
        
        # 获取所有数据
        all_data = table.to_pandas()
        
        print(f"\n总向量数: {len(all_data)}")
        
        # 统计模态
        modality_counts = all_data['modality'].value_counts()
        print("\n模态统计:")
        for modality, count in modality_counts.items():
            print(f"  - {modality}: {count}")
        
        # 显示音频文件
        audio_data = all_data[all_data['modality'] == 'audio']
        print(f"\n音频文件 ({len(audio_data)}):")
        print("="*60)
        
        for i, row in audio_data.iterrows():
            # 解析 metadata
            metadata_dict = {}
            if 'metadata' in row:
                if isinstance(row['metadata'], str):
                    try:
                        metadata_dict = json.loads(row['metadata']) if row['metadata'] else {}
                    except json.JSONDecodeError:
                        metadata_dict = {}
                elif isinstance(row['metadata'], dict):
                    metadata_dict = row['metadata']
            
            file_name = metadata_dict.get('file_name', 'N/A')
            file_path = metadata_dict.get('file_path', 'N/A')
            vector_dim = len(row['vector']) if 'vector' in row else 0
            
            print(f"\n[{i+1}]")
            print(f"  文件名: {file_name}")
            print(f"  文件路径: {file_path}")
            print(f"  向量维度: {vector_dim}")
        
        # 显示图像文件（包括熊猫）
        image_data = all_data[all_data['modality'] == 'image']
        print(f"\n图像文件 ({len(image_data)}):")
        print("="*60)
        
        # 查找熊猫图片
        panda_images = []
        for i, row in image_data.iterrows():
            metadata_dict = {}
            if 'metadata' in row:
                if isinstance(row['metadata'], str):
                    try:
                        metadata_dict = json.loads(row['metadata']) if row['metadata'] else {}
                    except json.JSONDecodeError:
                        metadata_dict = {}
                elif isinstance(row['metadata'], dict):
                    metadata_dict = row['metadata']
            
            file_name = metadata_dict.get('file_name', 'N/A')
            file_path = metadata_dict.get('file_path', 'N/A')
            
            # 检查是否包含"熊猫"
            if '熊猫' in file_name or 'panda' in file_name.lower():
                panda_images.append((file_name, file_path))
        
        if panda_images:
            print("\n熊猫图片:")
            for file_name, file_path in panda_images:
                print(f"  - {file_name}")
                print(f"    路径: {file_path}")
        else:
            print("\n未找到熊猫图片")
        
        # 显示最近的几个图像文件
        print(f"\n最近的图像文件 (前5个):")
        for i, row in image_data.head(5).iterrows():
            metadata_dict = {}
            if 'metadata' in row:
                if isinstance(row['metadata'], str):
                    try:
                        metadata_dict = json.loads(row['metadata']) if row['metadata'] else {}
                    except json.JSONDecodeError:
                        metadata_dict = {}
                elif isinstance(row['metadata'], dict):
                    metadata_dict = row['metadata']
            
            file_name = metadata_dict.get('file_name', 'N/A')
            file_path = metadata_dict.get('file_path', 'N/A')
            
            print(f"  - {file_name}")
    
    except Exception as e:
        print(f"检查失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    check_indexed_files()
