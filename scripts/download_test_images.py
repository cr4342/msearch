#!/usr/bin/env python3
"""
测试图片下载脚本
从网络下载测试图片到testdata目录
"""

import os
import requests
import time
from pathlib import Path
from urllib.parse import urlparse
from typing import List, Dict
import json

# 测试图片URL列表
TEST_IMAGES = [
    # 自然风景图片
    {
        "url": "https://picsum.photos/seed/sunset/800/600.jpg",
        "filename": "sunset_1.jpg",
        "description": "日落风景"
    },
    {
        "url": "https://picsum.photos/seed/mountain/800/600.jpg",
        "filename": "mountain_1.jpg", 
        "description": "山脉风景"
    },
    {
        "url": "https://picsum.photos/seed/ocean/800/600.jpg",
        "filename": "ocean_1.jpg",
        "description": "海洋风景"
    },
    {
        "url": "https://picsum.photos/seed/forest/800/600.jpg",
        "filename": "forest_1.jpg",
        "description": "森林风景"
    },
    {
        "url": "https://picsum.photos/seed/city/800/600.jpg",
        "filename": "city_1.jpg",
        "description": "城市风景"
    },
    # 动物图片
    {
        "url": "https://picsum.photos/seed/cat/800/600.jpg",
        "filename": "cat_1.jpg",
        "description": "猫咪"
    },
    {
        "url": "https://picsum.photos/seed/dog/800/600.jpg",
        "filename": "dog_1.jpg",
        "description": "狗狗"
    },
    {
        "url": "https://picsum.photos/seed/bird/800/600.jpg",
        "filename": "bird_1.jpg",
        "description": "鸟类"
    },
    {
        "url": "https://picsum.photos/seed/flower/800/600.jpg",
        "filename": "flower_1.jpg",
        "description": "花朵"
    },
    {
        "url": "https://picsum.photos/seed/food/800/600.jpg",
        "filename": "food_1.jpg",
        "description": "食物"
    },
    # 建筑图片
    {
        "url": "https://picsum.photos/seed/architecture/800/600.jpg",
        "filename": "architecture_1.jpg",
        "description": "建筑"
    },
    {
        "url": "https://picsum.photos/seed/house/800/600.jpg",
        "filename": "house_1.jpg",
        "description": "房屋"
    },
    {
        "url": "https://picsum.photos/seed/bridge/800/600.jpg",
        "filename": "bridge_1.jpg",
        "description": "桥梁"
    },
    {
        "url": "https://picsum.photos/seed/technology/800/600.jpg",
        "filename": "technology_1.jpg",
        "description": "科技"
    },
    # 抽象图片
    {
        "url": "https://picsum.photos/seed/abstract/800/600.jpg",
        "filename": "abstract_1.jpg",
        "description": "抽象图案"
    },
    {
        "url": "https://picsum.photos/seed/pattern/800/600.jpg",
        "filename": "pattern_1.jpg",
        "description": "纹理图案"
    },
    {
        "url": "https://picsum.photos/seed/texture/800/600.jpg",
        "filename": "texture_1.jpg",
        "description": "材质纹理"
    }
]

def download_image(url: str, filepath: str, timeout: int = 30) -> bool:
    """
    下载单个图片
    
    Args:
        url: 图片URL
        filepath: 保存路径
        timeout: 超时时间
        
    Returns:
        是否下载成功
    """
    try:
        print(f"下载图片: {url}")
        
        # 发送请求
        response = requests.get(url, timeout=timeout, stream=True)
        response.raise_for_status()
        
        # 检查内容类型
        content_type = response.headers.get('content-type', '')
        if not content_type.startswith('image/'):
            print(f"错误: URL返回的不是图片内容: {content_type}")
            return False
        
        # 检查内容长度
        content_length = response.headers.get('content-length', '0')
        if int(content_length) < 1000:  # 小于1KB可能不是有效图片
            print(f"错误: 文件太小，可能不是有效图片: {content_length} bytes")
            return False
        
        # 保存文件
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # 验证文件大小
        file_size = os.path.getsize(filepath)
        print(f"✅ 下载成功: {filepath} ({file_size} bytes)")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 下载失败: {url} - {e}")
        return False
    except Exception as e:
        print(f"❌ 下载异常: {url} - {e}")
        return False

def main():
    """主函数"""
    print("🌐 开始下载测试图片")
    print("=" * 50)
    
    # 确保目录存在
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    testdata_dir = project_root / "testdata"
    images_dir = testdata_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    
    # 下载统计
    success_count = 0
    fail_count = 0
    
    # 下载元数据
    metadata = []
    
    for i, image_info in enumerate(TEST_IMAGES):
        print(f"\n[{i+1}/{len(TEST_IMAGES)}] 下载: {image_info['description']}")
        
        filepath = images_dir / image_info['filename']
        
        if download_image(image_info['url'], str(filepath)):
            success_count += 1
            metadata.append({
                'filename': image_info['filename'],
                'url': image_info['url'],
                'description': image_info['description'],
                'filepath': str(filepath),
                'file_size': os.path.getsize(filepath),
                'download_time': time.time()
            })
        else:
            fail_count += 1
        
        # 添加延迟避免过于频繁的请求
        time.sleep(1)
    
    # 保存元数据
    metadata_file = testdata_dir / "images_metadata.json"
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 50)
    print("📊 下载统计:")
    print(f"   成功下载: {success_count} 张")
    print(f"   下载失败: {fail_count} 张")
    print(f"   元数据文件: {metadata_file}")
    print(f"   图片目录: {images_dir}")
    
    # 显示下载的图片列表
    print("\n📁 已下载的图片:")
    for item in metadata[:10]:  # 只显示前10个
        size_mb = item['file_size'] / 1024 / 1024
        print(f"   {item['filename']} ({size_mb:.2f}MB) - {item['description']}")
    
    if len(metadata) > 10:
        print(f"   ... 还有 {len(metadata) - 10} 张图片")

if __name__ == "__main__":
    main()