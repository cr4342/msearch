"""
测试脚本：使用真实模型处理testdata目录中的数据（离线模式）
"""
import sys
import os
import asyncio
from pathlib import Path

# 设置离线模式环境变量
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.config.config_manager import ConfigManager
from src.core.embedding.embedding_engine import EmbeddingEngine
from src.core.vector.vector_store import VectorStore
from src.core.database.database_manager import DatabaseManager
from src.services.media.media_processor import MediaProcessor


async def process_testdata():
    """处理testdata目录中的数据"""
    print("=" * 60)
    print("使用真实模型处理testdata数据（离线模式）")
    print("=" * 60)
    
    # 1. 初始化配置管理器
    print("\n1. 初始化配置...")
    config_manager = ConfigManager()
    print(f"   配置加载成功")
    
    # 2. 初始化向量化引擎
    print("\n2. 初始化向量化引擎...")
    embedding_engine = EmbeddingEngine(config=config_manager.config)
    print(f"   向量化引擎初始化完成，配置驱动模式")
    
    # 3. 初始化向量存储
    print("\n3. 初始化向量存储...")
    vector_store = VectorStore(config={
        'data_dir': 'data/database/lancedb',
        'collection_name': 'unified_vectors',
        'vector_dimension': 512
    })
    print(f"   向量存储初始化成功")
    
    # 4. 初始化数据库管理器
    print("\n4. 初始化数据库...")
    db_manager = DatabaseManager(db_path='data/database/sqlite/msearch.db')
    print(f"   数据库初始化成功")
    
    # 5. 初始化媒体处理器
    print("\n5. 初始化媒体处理器...")
    media_processor = MediaProcessor(config=config_manager.config)
    print(f"   媒体处理器初始化完成")
    
    # 6. 获取testdata目录中的文件
    testdata_dir = Path('testdata')
    if not testdata_dir.exists():
        print(f"\n错误: testdata目录不存在")
        return False
    
    image_files = list(testdata_dir.glob('*.jpg')) + list(testdata_dir.glob('*.jpeg')) + list(testdata_dir.glob('*.png'))
    print(f"\n6. 找到 {len(image_files)} 个图像文件")
    
    if len(image_files) == 0:
        print("   没有找到图像文件，跳过处理")
        return True
    
    # 7. 处理每个图像文件
    print("\n7. 处理图像文件...")
    processed_count = 0
    failed_count = 0
    
    for image_file in image_files:
        print(f"\n   处理文件: {image_file.name}")
        try:
            # 7.1 预处理图像
            processed_image = media_processor.process_image(str(image_file))
            if processed_image is None:
                print(f"   警告: 图像预处理失败")
                failed_count += 1
                continue
            
            # 7.2 生成向量
            vector = await embedding_engine.embed_image(str(image_file))
            if vector is None or len(vector) == 0:
                print(f"   警告: 向量化失败")
                failed_count += 1
                continue
            
            print(f"   向量生成成功，维度: {len(vector)}")
            
            # 7.3 存储到向量数据库
            vector_id = f"image_{image_file.stem}"
            vector_store.add_vector({
                "id": vector_id,
                "vector": vector,
                "modality": "image",
                "file_id": image_file.stem,
                "metadata": {
                    "file_name": image_file.name,
                    "file_path": str(image_file)
                }
            })
            print(f"   向量存储成功")
            
            # 7.4 存储元数据到数据库
            db_manager.insert_file_metadata({
                'id': image_file.stem,
                'file_path': str(image_file),
                'file_name': image_file.name,
                'file_size': image_file.stat().st_size,
                'file_type': 'image',
                'metadata': {'modality': 'image'}
            })
            print(f"   元数据存储成功")
            
            processed_count += 1
            
        except Exception as e:
            print(f"   错误: 处理失败 - {e}")
            import traceback
            traceback.print_exc()
            failed_count += 1
    
    # 8. 输出处理结果
    print("\n" + "=" * 60)
    print("处理完成")
    print("=" * 60)
    print(f"总文件数: {len(image_files)}")
    print(f"成功处理: {processed_count}")
    print(f"处理失败: {failed_count}")
    print("=" * 60)
    
    return processed_count > 0


if __name__ == "__main__":
    try:
        success = asyncio.run(process_testdata())
        if success:
            print("\n处理完成!")
        else:
            print("\n没有成功处理任何文件")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
