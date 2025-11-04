#!/usr/bin/env python3
"""
媒体预处理系统使用示例
展示如何使用简化的媒体预处理接口
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.processors.media_preprocessing_system import (
    preprocess_media_file,
    batch_preprocess_files,
    get_segment_mapping_manager,
    validate_file,
    get_supported_formats
)


def demo_single_file_processing():
    """演示单个文件处理"""
    print("=== 单个文件处理演示 ===")
    
    # 创建一个模拟的视频文件路径（实际使用时替换为真实路径）
    video_path = "demo_video.mp4"
    
    # 验证文件（在实际环境中）
    validation = validate_file(video_path)
    print(f"文件验证结果: {validation}")
    
    if not validation['valid']:
        print("文件验证失败，跳过处理")
        return
    
    # 预处理文件
    print(f"开始处理文件: {video_path}")
    result = preprocess_media_file(video_path)
    
    print(f"处理状态: {result.status}")
    print(f"原始文件ID: {result.original_file_id}")
    print(f"文件类型: {result.file_type}")
    print(f"切片数量: {len(result.segments)}")
    print(f"时间戳数量: {len(result.timestamp_infos)}")
    print(f"处理耗时: {result.processing_time:.2f}秒")
    
    if result.status == 'error':
        print(f"错误信息: {result.error_message}")
        return
    
    # 显示切片信息
    print("\n切片信息:")
    for i, segment in enumerate(result.segments):
        print(f"  切片 {i+1}:")
        print(f"    ID: {segment.segment_id}")
        print(f"    时间范围: {segment.start_time:.2f}s - {segment.end_time:.2f}s")
        print(f"    时长: {segment.duration:.2f}s")
        print(f"    模态: {segment.modality}")
        print(f"    路径: {segment.segment_path}")
    
    # 显示时间戳信息
    print(f"\n时间戳信息 (前5个):")
    for i, ts in enumerate(result.timestamp_infos[:5]):
        print(f"  时间戳 {i+1}:")
        print(f"    段ID: {ts.segment_id}")
        print(f"    模态: {ts.modality.value}")
        print(f"    时间: {ts.start_time:.2f}s - {ts.end_time:.2f}s")
        print(f"    置信度: {ts.confidence:.3f}")
    
    return result


def demo_batch_processing():
    """演示批量文件处理"""
    print("\n=== 批量文件处理演示 ===")
    
    # 模拟文件列表
    file_paths = [
        "demo_image.jpg",
        "demo_video.mp4",
        "demo_audio.mp3"
    ]
    
    print(f"批量处理 {len(file_paths)} 个文件")
    
    # 批量预处理
    results = batch_preprocess_files(file_paths)
    
    # 显示结果统计
    success_count = sum(1 for r in results if r.status == 'success')
    error_count = len(results) - success_count
    
    print(f"处理完成: 成功 {success_count} 个, 失败 {error_count} 个")
    
    # 显示每个文件的处理结果
    for result in results:
        print(f"\n文件: {result.original_file_path}")
        print(f"  状态: {result.status}")
        print(f"  文件ID: {result.original_file_id}")
        print(f"  切片数: {len(result.segments)}")
        if result.status == 'error':
            print(f"  错误: {result.error_message}")
    
    return results


def demo_segment_mapping():
    """演示切片映射功能"""
    print("\n=== 切片映射功能演示 ===")
    
    # 获取切片映射管理器
    segment_manager = get_segment_mapping_manager()
    
    # 显示统计信息
    stats = segment_manager.get_statistics()
    print(f"映射统计信息:")
    print(f"  总文件数: {stats['total_files']}")
    print(f"  总切片数: {stats['total_segments']}")
    print(f"  平均切片数: {stats['avg_segments_per_file']:.1f}")
    print(f"  模态分布: {stats['modality_distribution']}")
    
    # 如果有映射数据，演示时间戳转换
    if stats['total_files'] > 0:
        # 获取第一个文件的映射
        for original_file_id, segments in segment_manager.mappings.items():
            print(f"\n文件 {original_file_id} 的切片映射:")
            
            for segment in segments[:3]:  # 只显示前3个切片
                print(f"  切片: {segment.segment_id}")
                print(f"    时间范围: {segment.start_time:.2f}s - {segment.end_time:.2f}s")
                print(f"    模态: {segment.modality}")
            
            # 演示时间戳转换
            test_timestamps = [30.0, 65.0, 120.0]
            print(f"\n时间戳转换演示:")
            
            for original_timestamp in test_timestamps:
                result = segment_manager.find_segment_by_original_timestamp(
                    original_file_id, original_timestamp
                )
                
                if result:
                    segment_info, segment_timestamp = result
                    print(f"  原始时间 {original_timestamp:.1f}s -> "
                          f"切片 {segment_info.segment_index} 内时间 {segment_timestamp:.2f}s")
                else:
                    print(f"  原始时间 {original_timestamp:.1f}s -> 未找到对应切片")
            
            break  # 只演示第一个文件


def demo_time_position_calculation():
    """演示时间位置计算"""
    print("\n=== 时间位置计算演示 ===")
    
    segment_manager = get_segment_mapping_manager()
    
    # 模拟一个检索场景：用户检索到了某个切片的某个时间点
    # 需要反向计算在原始文件中的时间位置
    
    print("场景: 用户检索到切片内容，需要定位原始文件时间")
    
    # 假设检索到的切片信息
    found_segment_id = "demo_segment_123"
    found_timestamp_in_segment = 15.5  # 切片内的时间戳
    
    print(f"检索结果: 切片ID = {found_segment_id}, 切片内时间 = {found_timestamp_in_segment:.1f}s")
    
    # 计算原始文件时间戳
    original_timestamp = segment_manager.calculate_original_timestamp(
        found_segment_id, found_timestamp_in_segment
    )
    
    if original_timestamp is not None:
        print(f"原始文件时间戳: {original_timestamp:.1f}s")
        
        # 获取原始文件信息
        segment_info = segment_manager.get_original_file_info(found_segment_id)
        if segment_info:
            print(f"原始文件: {segment_info.original_file_path}")
            print(f"切片索引: {segment_info.segment_index}")
            print(f"切片时间范围: {segment_info.start_time:.1f}s - {segment_info.end_time:.1f}s")
    else:
        print("未找到对应的原始文件信息")


def demo_supported_formats():
    """演示支持的文件格式"""
    print("\n=== 支持的文件格式 ===")
    
    formats = get_supported_formats()
    
    for file_type, extensions in formats.items():
        print(f"{file_type.upper()} 文件:")
        print(f"  支持格式: {', '.join(extensions)}")


def main():
    """主演示函数"""
    print("媒体预处理系统使用演示")
    print("=" * 50)
    
    try:
        # 演示支持的格式
        demo_supported_formats()
        
        # 演示单个文件处理（模拟）
        print("\n注意: 以下演示使用模拟数据，实际使用时请提供真实文件路径")
        
        # 由于没有真实文件，我们只演示API调用方式
        print("\n=== API调用方式演示 ===")
        
        print("\n1. 单个文件处理:")
        print("   result = preprocess_media_file('path/to/video.mp4')")
        print("   print(f'状态: {result.status}')")
        print("   print(f'切片数: {len(result.segments)}')")
        
        print("\n2. 批量文件处理:")
        print("   results = batch_preprocess_files(['file1.mp4', 'file2.jpg'])")
        print("   for result in results:")
        print("       print(f'{result.original_file_path}: {result.status}')")
        
        print("\n3. 时间戳转换:")
        print("   segment_manager = get_segment_mapping_manager()")
        print("   original_time = segment_manager.calculate_original_timestamp(")
        print("       segment_id, segment_timestamp)")
        
        print("\n4. 切片查找:")
        print("   segment_info, segment_time = segment_manager.find_segment_by_original_timestamp(")
        print("       original_file_id, original_timestamp)")
        
        # 演示切片映射功能（如果有数据）
        demo_segment_mapping()
        
        print("\n" + "=" * 50)
        print("演示完成！")
        
        print("\n核心功能说明:")
        print("1. preprocess_media_file() - 处理单个媒体文件")
        print("2. batch_preprocess_files() - 批量处理文件")
        print("3. SegmentMappingManager - 管理文件切片映射关系")
        print("4. 支持自动时间戳转换，确保检索时时间定位准确")
        
    except Exception as e:
        print(f"演示过程中出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()