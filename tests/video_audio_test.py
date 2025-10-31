#!/usr/bin/env python3
"""
视频音频处理测试脚本
测试FFMPEG视频预处理和音频分离功能
"""

import os
import sys
import json
import time
import logging
import subprocess
import wave
import numpy as np
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_ffmpeg():
    """检查FFMPEG是否可用"""
    logger.info("🔍 检查FFMPEG...")
    
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            logger.info(f"✅ FFMPEG可用: {version_line}")
            return True
        else:
            logger.error("❌ FFMPEG不可用")
            return False
    except FileNotFoundError:
        logger.error("❌ FFMPEG未安装")
        return False
    except Exception as e:
        logger.error(f"❌ FFMPEG检查异常: {e}")
        return False

def create_test_video():
    """创建包含音频的测试视频"""
    logger.info("🎬 创建包含音频的测试视频...")
    
    testdata_dir = project_root / "testdata"
    testdata_dir.mkdir(exist_ok=True)
    
    if not check_ffmpeg():
        logger.error("FFMPEG不可用，无法创建测试视频")
        return None
    
    try:
        # 输出文件路径
        video_path = testdata_dir / "test_video_with_audio.mp4"
        
        # 使用FFMPEG生成测试视频（包含音频）
        cmd = [
            'ffmpeg', '-y',  # 覆盖输出文件
            '-f', 'lavfi',   # 使用lavfi输入格式
            '-i', 'testsrc2=duration=5:size=320x240:rate=10',  # 生成5秒测试视频
            '-f', 'lavfi',   # 音频输入
            '-i', 'sine=frequency=440:duration=5',  # 生成440Hz正弦波音频
            '-c:v', 'libx264',  # 视频编码
            '-c:a', 'aac',      # 音频编码
            '-shortest',        # 以最短流为准
            str(video_path)
        ]
        
        logger.info("执行FFMPEG命令生成测试视频...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0 and video_path.exists():
            file_size = video_path.stat().st_size
            logger.info(f"✅ 测试视频创建成功: {video_path} ({file_size} bytes)")
            return video_path
        else:
            logger.error(f"❌ 视频创建失败: {result.stderr}")
            return None
            
    except Exception as e:
        logger.error(f"❌ 视频创建异常: {e}")
        return None

def extract_audio_from_video(video_path):
    """从视频中提取音频"""
    logger.info(f"🎵 从视频中提取音频: {video_path.name}")
    
    if not video_path.exists():
        logger.error(f"视频文件不存在: {video_path}")
        return None
    
    try:
        # 输出音频文件路径
        audio_path = video_path.parent / f"{video_path.stem}_extracted.wav"
        
        # 使用FFMPEG提取音频
        cmd = [
            'ffmpeg', '-y',
            '-i', str(video_path),
            '-vn',  # 不要视频流
            '-acodec', 'pcm_s16le',  # 16位PCM编码
            '-ar', '16000',  # 16kHz采样率
            '-ac', '1',      # 单声道
            str(audio_path)
        ]
        
        logger.info("执行音频提取...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0 and audio_path.exists():
            file_size = audio_path.stat().st_size
            logger.info(f"✅ 音频提取成功: {audio_path} ({file_size} bytes)")
            return audio_path
        else:
            logger.error(f"❌ 音频提取失败: {result.stderr}")
            return None
            
    except Exception as e:
        logger.error(f"❌ 音频提取异常: {e}")
        return None

def test_video_audio_pipeline():
    """测试完整的视频音频处理流水线"""
    logger.info("🚀 开始视频音频处理测试...")
    logger.info("=" * 60)
    
    results = {
        "ffmpeg_available": False,
        "video_created": False,
        "audio_extracted": False,
        "tests": []
    }
    
    # 检查FFMPEG
    results["ffmpeg_available"] = check_ffmpeg()
    if not results["ffmpeg_available"]:
        logger.error("❌ FFMPEG不可用，跳过视频音频测试")
        return results
    
    # 创建测试视频
    video_path = create_test_video()
    results["video_created"] = video_path is not None
    
    if not video_path:
        logger.error("❌ 无法创建测试视频")
        return results
    
    # 提取音频
    audio_path = extract_audio_from_video(video_path)
    results["audio_extracted"] = audio_path is not None
    
    if not audio_path:
        logger.error("❌ 无法提取音频")
        return results
    
    # 分析音频文件
    try:
        with wave.open(str(audio_path), 'rb') as wav_file:
            sample_rate = wav_file.getframerate()
            channels = wav_file.getnchannels()
            frames = wav_file.getnframes()
            duration = frames / sample_rate
            
            logger.info(f"📊 音频分析结果:")
            logger.info(f"   采样率: {sample_rate} Hz")
            logger.info(f"   声道数: {channels}")
            logger.info(f"   时长: {duration:.2f} 秒")
            logger.info(f"   帧数: {frames}")
            
            results["audio_analysis"] = {
                "sample_rate": sample_rate,
                "channels": channels,
                "duration": duration,
                "frames": frames
            }
            
    except Exception as e:
        logger.error(f"❌ 音频分析失败: {e}")
        results["audio_analysis"] = {"error": str(e)}
    
    # 测试不同格式转换
    conversion_tests = []
    
    for target_rate in [8000, 22050, 44100]:
        try:
            converted_path = audio_path.parent / f"converted_{target_rate}hz.wav"
            
            cmd = [
                'ffmpeg', '-y',
                '-i', str(audio_path),
                '-ar', str(target_rate),
                str(converted_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and converted_path.exists():
                conversion_tests.append({
                    "target_rate": target_rate,
                    "success": True,
                    "file_size": converted_path.stat().st_size
                })
                logger.info(f"✅ 转换到 {target_rate}Hz 成功")
            else:
                conversion_tests.append({
                    "target_rate": target_rate,
                    "success": False,
                    "error": result.stderr
                })
                logger.warning(f"⚠️ 转换到 {target_rate}Hz 失败")
                
        except Exception as e:
            conversion_tests.append({
                "target_rate": target_rate,
                "success": False,
                "error": str(e)
            })
            logger.error(f"❌ 转换到 {target_rate}Hz 异常: {e}")
    
    results["conversion_tests"] = conversion_tests
    successful_conversions = len([t for t in conversion_tests if t["success"]])
    
    # 输出结果
    logger.info("=" * 60)
    logger.info("📊 视频音频处理测试结果汇总")
    logger.info("=" * 60)
    logger.info(f"FFMPEG状态: {'✅ 可用' if results['ffmpeg_available'] else '❌ 不可用'}")
    logger.info(f"视频创建: {'✅ 成功' if results['video_created'] else '❌ 失败'}")
    logger.info(f"音频提取: {'✅ 成功' if results['audio_extracted'] else '❌ 失败'}")
    logger.info(f"格式转换: {successful_conversions}/{len(conversion_tests)} 成功")
    
    # 保存结果
    output_dir = project_root / "tests" / "output"
    output_dir.mkdir(exist_ok=True)
    
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    results_file = output_dir / f"video_audio_test_{timestamp}.json"
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    logger.info(f"测试结果已保存到: {results_file}")
    
    return results

def main():
    """主函数"""
    results = test_video_audio_pipeline()
    
    # 判断测试结果
    if results["ffmpeg_available"] and results["video_created"] and results["audio_extracted"]:
        logger.info("🎉 视频音频处理测试全部通过！")
        return 0
    elif results["ffmpeg_available"]:
        logger.warning("⚠️ 视频音频处理测试部分通过")
        return 1
    else:
        logger.error("❌ 视频音频处理测试失败")
        return 2

if __name__ == "__main__":
    sys.exit(main())