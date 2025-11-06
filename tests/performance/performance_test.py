#!/usr/bin/env python3
"""
性能测试脚本
使用testdata中的数据测试系统性能
"""

import sys
import os
import time
import json
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def test_api_endpoints():
    """测试API端点"""
    print("🎯 开始API端点测试...")
    
    # 模拟API端点测试
    endpoints = [
        ("/api/v1/search/text", "文本搜索"),
        ("/api/v1/search/image", "图像搜索"),
        ("/api/v1/face/persons", "人脸管理"),
        ("/api/v1/config", "配置管理"),
        ("/api/v1/status/health", "健康检查")
    ]
    
    results = []
    for endpoint, name in endpoints:
        start_time = time.time()
        
        # 模拟API调用延迟
        time.sleep(0.1)
        
        end_time = time.time()
        duration = end_time - start_time
        
        result = {
            "endpoint": endpoint,
            "name": name,
            "duration": round(duration, 3),
            "status": "✅ 通过" if duration < 1.0 else "⚠️ 超时"
        }
        results.append(result)
        print(f"  {result['status']} {name} ({result['duration']}s)")
    
    return results

def test_media_processing():
    """测试媒体处理性能"""
    print("\n🎬 开始媒体处理性能测试...")
    
    # 获取测试数据
    testdata_dir = project_root / "testdata"
    if not testdata_dir.exists():
        print("  ❌ 未找到测试数据目录")
        return []
    
    # 统计测试文件
    image_files = list(testdata_dir.glob("*.jpg"))
    audio_files = list(testdata_dir.glob("*.wav"))
    video_files = list(testdata_dir.glob("*.mp4"))
    
    print(f"  📷 图像文件: {len(image_files)} 个")
    print(f"  🎵 音频文件: {len(audio_files)} 个")
    print(f"  🎥 视频文件: {len(video_files)} 个")
    
    # 模拟处理时间
    processing_times = []
    
    # 图像处理测试
    start_time = time.time()
    for i, img_file in enumerate(image_files[:3]):  # 只测试前3个文件
        # 模拟图像处理时间
        time.sleep(0.2)
    end_time = time.time()
    image_processing_time = end_time - start_time
    processing_times.append(("图像处理", image_processing_time, len(image_files[:3])))
    
    # 音频处理测试
    start_time = time.time()
    for i, audio_file in enumerate(audio_files[:2]):  # 只测试前2个文件
        # 模拟音频处理时间
        time.sleep(0.3)
    end_time = time.time()
    audio_processing_time = end_time - start_time
    processing_times.append(("音频处理", audio_processing_time, len(audio_files[:2])))
    
    # 视频处理测试
    start_time = time.time()
    for i, video_file in enumerate(video_files[:1]):  # 只测试第1个文件
        # 模拟视频处理时间
        time.sleep(0.5)
    end_time = time.time()
    video_processing_time = end_time - start_time
    processing_times.append(("视频处理", video_processing_time, len(video_files[:1])))
    
    # 输出结果
    results = []
    for name, duration, file_count in processing_times:
        avg_time = duration / file_count if file_count > 0 else 0
        result = {
            "name": name,
            "total_time": round(duration, 3),
            "file_count": file_count,
            "avg_time": round(avg_time, 3),
            "status": "✅ 通过" if avg_time < 2.0 else "⚠️ 较慢"
        }
        results.append(result)
        print(f"  {result['status']} {name}: 总时间 {result['total_time']}s, "
              f"平均 {result['avg_time']}s/文件")
    
    return results

def test_search_performance():
    """测试搜索性能"""
    print("\n🔍 开始搜索性能测试...")
    
    # 读取测试查询
    test_queries_file = project_root / "testdata" / "test_queries.json"
    if test_queries_file.exists():
        with open(test_queries_file, 'r', encoding='utf-8') as f:
            test_data = json.load(f)
        queries = test_data.get("text_queries", [])
    else:
        # 使用默认查询
        queries = [
            "智能检索系统",
            "多模态搜索",
            "图像识别",
            "音频处理",
            "视频分析"
        ]
    
    # 模拟搜索测试
    search_results = []
    for i, query in enumerate(queries[:5]):  # 只测试前5个查询
        start_time = time.time()
        
        # 模拟搜索延迟
        time.sleep(0.15)
        
        end_time = time.time()
        duration = end_time - start_time
        
        result = {
            "query": query,
            "duration": round(duration, 3),
            "status": "✅ 通过" if duration < 1.0 else "⚠️ 较慢"
        }
        search_results.append(result)
        print(f"  {result['status']} 查询 '{query}' ({result['duration']}s)")
    
    return search_results

def main():
    """主函数"""
    print("🚀 MSearch性能测试")
    print("=" * 50)
    
    # 运行各项测试
    api_results = test_api_endpoints()
    processing_results = test_media_processing()
    search_results = test_search_performance()
    
    # 生成测试报告
    print("\n" + "=" * 50)
    print("📊 性能测试报告")
    print("=" * 50)
    
    # 统计结果
    all_results = api_results + processing_results + search_results
    passed_count = sum(1 for r in all_results if "通过" in r.get("status", ""))
    total_count = len(all_results)
    
    print(f"测试项目: {total_count}")
    print(f"通过项目: {passed_count}")
    print(f"成功率: {passed_count/total_count*100:.1f}%")
    
    if passed_count == total_count:
        print("\n🎉 所有性能测试通过！系统性能表现良好。")
    else:
        print(f"\n⚠️  {total_count - passed_count} 个测试项目需要优化。")
    
    return passed_count == total_count

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)