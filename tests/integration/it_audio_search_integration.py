"""
测试音频处理和检索流程
使用真实模型和testdata目录下的数据
"""

import os
import sys
import json
import time
from pathlib import Path
import shutil

# 设置matplotlib使用非交互式后端，避免ft2font错误
os.environ['MPLBACKEND'] = 'Agg'

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.config.config_manager import ConfigManager
from src.core.database.database_manager import DatabaseManager
from src.core.vector.vector_store import VectorStore
from src.core.embedding.embedding_engine import EmbeddingEngine
from src.services.media.media_processor import MediaProcessor
from src.data.extractors.noise_filter import NoiseFilterManager

def setup_test_environment():
    """设置测试环境"""
    # 创建临时目录
    test_dir = Path("test_temp")
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir()
    
    # 创建子目录
    (test_dir / "database").mkdir()
    (test_dir / "lancedb").mkdir()
    
    return test_dir

def get_test_audio_files():
    """获取testdata目录中的音频文件"""
    testdata_dir = Path("testdata")
    audio_extensions = ['.mp3', '.wav', '.aac', '.ogg', '.flac']
    
    audio_files = []
    for ext in audio_extensions:
        audio_files.extend(testdata_dir.glob(f"*{ext}"))
    
    print(f"找到 {len(audio_files)} 个测试音频")
    for i, audio_file in enumerate(audio_files, 1):
        file_size = audio_file.stat().st_size
        print(f"  - {audio_file.name} ({file_size} bytes)")
    
    return audio_files

def process_and_index_audios(audios, db_manager, vector_store, embedding_engine, media_processor, noise_filter):
    """处理和索引音频"""
    indexed_count = 0
    
    for i, audio_path in enumerate(audios):
        print(f"\n处理音频: {audio_path.name}")
        
        # 获取文件大小
        file_size = audio_path.stat().st_size
        
        # 噪音过滤
        media_info = {
            'duration': 0,  # 将由media_processor填充
            'file_size': file_size,
            'file_ext': audio_path.suffix.lstrip('.'),  # 去掉点号
            'bitrate': 128  # 设置一个合理的默认比特率
        }
        
        # 先获取音频时长
        try:
            import librosa
            audio_data, sr = librosa.load(str(audio_path), sr=None)
            duration = len(audio_data) / sr
            media_info['duration'] = duration
        except Exception as e:
            print(f"  获取音频时长失败: {e}")
            continue
        
        should_keep, reason = noise_filter.filter("audio", media_info)
        if not should_keep:
            print(f"  跳过: {reason}")
            continue
        
        # 音频预处理
        try:
            processed = media_processor.process_audio(str(audio_path))
            if not processed or processed.get('status') != 'success':
                print(f"  预处理失败: {processed.get('error', 'unknown')}")
                continue
            print(f"  预处理成功: 时长={processed.get('duration', 0):.2f}s")
        except Exception as e:
            print(f"  预处理异常: {e}")
            import traceback
            traceback.print_exc()
            continue
        
        # 音频向量化
        try:
            print(f"  正在向量化...")
            # 使用真实的CLAP模型进行音频向量化
            audio_vector = embedding_engine.embed_audio(str(audio_path))
            
            if not audio_vector:
                print(f"  向量化失败")
                continue
            print(f"  向量维度: {len(audio_vector)}")
        except Exception as e:
            print(f"  向量化异常: {e}")
            import traceback
            traceback.print_exc()
            continue
        
        # 存储到数据库
        file_uuid = f"audio_{file_size}_{indexed_count}"
        metadata = {
            "id": file_uuid,
            "file_path": str(audio_path),
            "file_name": audio_path.name,
            "file_size": file_size,
            "file_type": "audio",
            "file_hash": f"hash_{file_size}",
            "duration": processed.get('duration', 0),
            "audio_type": processed.get('audio_type', 'UNKNOWN')
        }
        
        try:
            db_manager.insert_file_metadata(metadata)
        except Exception as e:
            print(f"  数据库插入失败: {e}")
            continue
        
        # 存储到向量数据库
        vector_id = f"{file_uuid}_vector"
        vector_data = {
            "id": vector_id,
            "vector": audio_vector,
            "modality": "audio",
            "file_id": file_uuid,
            "segment_id": "",
            "start_time": 0.0,
            "end_time": processed.get('duration', 0),
            "is_full_video": False,
            "metadata": json.dumps(metadata),
            "created_at": time.time()
        }
        
        try:
            vector_store.add_vector(vector_data)
            print(f"  索引成功: {file_uuid}")
            indexed_count += 1
        except Exception as e:
            print(f"  向量存储失败: {e}")
            continue
    
    return indexed_count

def search_audios(query_text, vector_store, embedding_engine, limit=5):
    """搜索音频"""
    print(f"\n搜索查询: {query_text}")
    
    # 向量化查询文本（使用音频检索）
    try:
        # 使用真实的CLAP模型进行查询文本向量化
        query_vector = embedding_engine.embed_text(query_text)
        print(f"  查询向量维度: {len(query_vector)}")
    except Exception as e:
        print(f"  查询向量化失败: {e}")
        return []
    
    # 搜索向量
    try:
        results = vector_store.search_vectors(
            query_vector=query_vector,
            limit=limit,
            filter={'modality': 'audio'}
        )
        return results
    except Exception as e:
        print(f"  搜索失败: {e}")
        return []

def main():
    """主函数"""
    print("=" * 60)
    print("音频处理和检索流程测试")
    print("=" * 60)
    
    # 设置测试环境
    print("\n1. 设置测试环境...")
    test_dir = setup_test_environment()
    print(f"测试目录: {test_dir}")
    
    # 初始化配置管理器
    print("\n2. 初始化配置管理器...")
    config_manager = ConfigManager()
    print(f"配置加载成功")
    
    # 初始化数据库
    print("\n3. 初始化数据库...")
    db_path = str(test_dir / "database" / "msearch.db")
    db_manager = DatabaseManager(db_path=db_path, enable_wal=True)
    print(f"数据库初始化成功")
    
    # 初始化向量存储
    print("\n4. 初始化向量存储...")
    lancedb_path = str(test_dir / "lancedb")
    vector_store = VectorStore(config={
        'data_dir': lancedb_path,
        'collection_name': 'unified_vectors',
        'vector_dimension': 512
    })
    print(f"向量存储初始化成功")
    
    # 初始化向量化引擎
    print("\n5. 初始化向量化引擎...")
    embedding_engine = EmbeddingEngine(config_manager.config)
    print(f"向量化引擎初始化成功")
    
    # 初始化媒体处理器
    print("\n6. 初始化媒体处理器...")
    media_processor = MediaProcessor(config_manager.config)
    print(f"媒体处理器初始化成功")
    
    # 初始化噪音过滤器
    print("\n7. 初始化噪音过滤器...")
    noise_filter = NoiseFilterManager(config_manager.config.get('noise_filter', {}))
    print(f"噪音过滤器初始化成功")
    
    # 获取测试音频
    print("\n8. 获取测试音频...")
    audios = get_test_audio_files()
    if not audios:
        print("未找到测试音频文件")
        return
    
    # 处理和索引音频
    print("\n9. 处理和索引音频...")
    indexed_count = process_and_index_audios(
        audios, db_manager, vector_store, embedding_engine, media_processor, noise_filter
    )
    print(f"\n成功索引 {indexed_count} 个音频")
    
    # 搜索测试
    print("\n10. 搜索测试...")
    queries = ["音乐", "悲伤", "古典音乐", "乐器"]
    
    for query in queries:
        results = search_audios(query, vector_store, embedding_engine, limit=3)
        print(f"\n查询: {query}")
        if results:
            for i, result in enumerate(results[:3], 1):
                # 计算相似度（距离越小，相似度越高）
                distance = result.get('_distance', 1.0)
                score = 1.0 - distance  # 将距离转换为相似度
                file_id = result.get('file_id', 'N/A')
                print(f"  {i}. 文件ID: {file_id}, 相似度: {score:.4f}")
        else:
            print("  未找到结果")
    
    # 清理测试环境
    print("\n11. 清理测试环境...")
    db_manager.close()
    vector_store.close()
    shutil.rmtree(test_dir)
    print("清理完成")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)

if __name__ == "__main__":
    main()