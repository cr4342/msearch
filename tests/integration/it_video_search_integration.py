"""
测试视频处理和检索流程
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
from src.services.media.media_utils import MediaInfoHelper

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
    (test_dir / "frames").mkdir()
    (test_dir / "audio").mkdir()
    
    return test_dir

def cleanup_test_environment(test_dir):
    """清理测试环境"""
    if test_dir.exists():
        shutil.rmtree(test_dir)
    print("清理完成")

def get_test_videos():
    """获取测试视频"""
    testdata_dir = Path("testdata")
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv']
    
    videos = []
    for ext in video_extensions:
        videos.extend(testdata_dir.glob(f"*{ext}"))
    
    return videos

def process_and_index_videos(videos, db_manager, vector_store, embedding_engine, media_processor, noise_filter):
    """处理和索引视频"""
    indexed_count = 0
    media_info_helper = MediaInfoHelper()
    
    for video_path in videos:
        print(f"\n处理视频: {video_path.name}")
        
        # 获取文件大小和媒体信息
        file_size = video_path.stat().st_size
        video_info = media_info_helper.get_media_info(str(video_path))
        
        # 使用opencv获取视频分辨率
        import cv2
        cap = cv2.VideoCapture(str(video_path))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
        
        # 噪音过滤
        file_ext = video_path.suffix.lower().lstrip('.')  # 去掉点号
        media_info = {
            'file_path': str(video_path),
            'file_name': video_path.name,
            'file_size': file_size,
            'file_ext': file_ext,  # 不包含点号
            'duration': video_info.get('duration', 0.0),
            'width': width,
            'height': height
        }
        
        should_keep, reason = noise_filter.filter('video', media_info)
        if not should_keep:
            print(f"  跳过: {reason}")
            continue
        
        # 视频预处理
        try:
            print(f"  正在预处理...")
            processed = media_processor.process_video(str(video_path))
            if not processed or processed.get('status') != 'success':
                print(f"  预处理失败")
                continue
            
            duration = video_info.get('duration', 0.0)
            is_short_video = processed.get('is_short_video', True)
            segments = processed.get('segments', [])
            
            print(f"  预处理成功: 时长={duration:.2f}s, 短视频={is_short_video}, 片段数={len(segments)}")
        except Exception as e:
            print(f"  预处理异常: {e}")
            continue
        
        # 视频向量化
        try:
            print(f"  正在向量化...")
            
            # 简化实现：只向量化第一个片段
            if segments:
                segment = segments[0]
                video_vector = embedding_engine.embed_video_segment(
                    str(video_path),
                    start_time=segment['start_time'],
                    end_time=segment['end_time'],
                    aggregation='mean'
                )
            else:
                # 如果没有片段，向量化整个视频
                video_vector = embedding_engine.embed_video_segment(str(video_path))
            
            if not video_vector:
                print(f"  向量化失败")
                continue
            
            print(f"  向量维度: {len(video_vector)}")
        except Exception as e:
            print(f"  向量化异常: {e}")
            import traceback
            traceback.print_exc()
            continue
        
        # 存储到数据库
        file_uuid = f"video_{file_size}_{indexed_count}"
        metadata = {
            "id": file_uuid,
            "file_path": str(video_path),
            "file_name": video_path.name,
            "file_size": file_size,
            "file_type": "video",
            "file_hash": f"hash_{file_size}",
            "duration": duration,
            "is_short_video": is_short_video
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
            "vector": video_vector,
            "modality": "video",
            "file_id": file_uuid,
            "segment_id": segments[0]['segment_id'] if segments else "full",
            "start_time": segments[0]['start_time'] if segments else 0.0,
            "end_time": segments[0]['end_time'] if segments else duration,
            "is_full_video": is_short_video,
            "metadata": json.dumps({
                "file_uuid": file_uuid,
                "file_path": str(video_path),
                "file_name": video_path.name
            }),
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

def search_videos(query_text, vector_store, embedding_engine, limit=5):
    """搜索视频"""
    print(f"\n搜索查询: {query_text}")
    
    # 向量化查询文本
    try:
        query_vector = embedding_engine.embed_text(query_text)
        print(f"查询向量维度: {len(query_vector)}")
    except Exception as e:
        print(f"查询向量化失败: {e}")
        return []
    
    # 搜索向量
    try:
        results = vector_store.search_vectors(
            query_vector=query_vector,
            limit=limit,
            filter={"modality": "video"}
        )
        return results
    except Exception as e:
        print(f"搜索失败: {e}")
        return []

def main():
    """主函数"""
    print("=" * 60)
    print("视频处理和检索流程测试")
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
        'index_type': 'ivf_pq',
        'num_partitions': 128,
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
    noise_filter = NoiseFilterManager(config_manager.config)
    print(f"噪音过滤器初始化成功")
    
    # 获取测试视频
    print("\n8. 获取测试视频...")
    videos = get_test_videos()
    print(f"找到 {len(videos)} 个测试视频")
    for video in videos:
        print(f"  - {video.name} ({video.stat().st_size} bytes)")
    
    if not videos:
        print("\n没有找到测试视频，测试结束")
        cleanup_test_environment(test_dir)
        return
    
    # 处理和索引视频
    print("\n9. 处理和索引视频...")
    indexed_count = process_and_index_videos(
        videos, db_manager, vector_store, embedding_engine, media_processor, noise_filter
    )
    print(f"\n成功索引 {indexed_count} 个视频")
    
    # 搜索测试
    print("\n10. 搜索测试...")
    queries = ["风景", "人物", "建筑", "自然"]
    
    for query in queries:
        results = search_videos(query, vector_store, embedding_engine, limit=3)
        print(f"\n查询: {query}")
        if results:
            for i, result in enumerate(results[:3], 1):
                score = result.get('_distance', 0.0)
                print(f"  {i}. 文件ID: {result.get('file_id', 'N/A')}, 相似度: {score:.4f}")
        else:
            print("  未找到结果")
    
    # 清理测试环境
    print("\n11. 清理测试环境...")
    cleanup_test_environment(test_dir)
    
    # 关闭数据库连接
    print("\n关闭数据库连接...")
    db_manager.close()
    vector_store.close()
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)

if __name__ == "__main__":
    main()