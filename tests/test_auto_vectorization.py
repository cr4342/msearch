#!/usr/bin/env python3
"""
测试自动向量化流程：下载图片到监控目录，验证自动向量化
"""

import os
import sys
import logging
import time
import requests
from pathlib import Path
import uuid

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 监控目录（从配置文件中获取）
MONITORED_DIR = Path("./testdata")

def download_random_image():
    """下载随机图片到监控目录"""
    logger.info(f"下载随机图片到监控目录: {MONITORED_DIR}")
    
    try:
        # 确保监控目录存在
        MONITORED_DIR.mkdir(parents=True, exist_ok=True)
        
        # 生成随机文件名
        image_name = f"test_download_{uuid.uuid4().hex[:8]}.jpg"
        image_path = MONITORED_DIR / image_name
        
        # 下载随机图片
        # 使用picsum.photos获取随机图片
        image_url = "https://picsum.photos/800/600"
        response = requests.get(image_url, stream=True)
        response.raise_for_status()
        
        with open(image_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logger.info(f"成功下载图片: {image_path}")
        return image_path
        
    except Exception as e:
        logger.error(f"下载图片失败: {e}")
        import traceback
        logger.error(f"错误堆栈: {traceback.format_exc()}")
        return None

def check_file_processed(image_path):
    """检查文件是否已被处理"""
    logger.info(f"检查文件是否已被处理: {image_path}")
    
    # 等待一段时间让系统处理
    wait_time = 10
    logger.info(f"等待 {wait_time} 秒让系统处理文件...")
    time.sleep(wait_time)
    
    # 检查数据库中是否有该文件的记录
    try:
        import sqlite3
        db_path = Path("./data/msearch.db")
        if not db_path.exists():
            logger.error(f"数据库文件不存在: {db_path}")
            return False
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 查询文件是否存在
        cursor.execute("SELECT id, status FROM files WHERE file_path = ?", (str(image_path),))
        result = cursor.fetchone()
        
        if result:
            file_id, status = result
            logger.info(f"文件在数据库中找到，ID: {file_id}, 状态: {status}")
            
            # 检查是否有对应的向量记录
            cursor.execute("SELECT COUNT(*) FROM vectors WHERE file_id = ?", (file_id,))
            vector_count = cursor.fetchone()[0]
            logger.info(f"文件对应的向量数量: {vector_count}")
            
            conn.close()
            
            # 如果状态是completed且有向量，则认为处理成功
            if status == 'completed' and vector_count > 0:
                logger.info(f"文件 {image_path} 已成功处理并生成向量！")
                return True
            else:
                logger.warning(f"文件 {image_path} 状态: {status}, 向量数量: {vector_count}")
                return False
        else:
            logger.error(f"文件 {image_path} 不在数据库中")
            conn.close()
            return False
            
    except Exception as e:
        logger.error(f"检查文件处理状态失败: {e}")
        import traceback
        logger.error(f"错误堆栈: {traceback.format_exc()}")
        return False

def main():
    """主函数"""
    logger.info("开始测试自动向量化流程...")
    
    # 下载随机图片
    image_path = download_random_image()
    if not image_path:
        logger.error("下载图片失败，测试无法继续")
        return False
    
    # 检查文件是否被自动处理
    if check_file_processed(image_path):
        logger.info("✅ 自动向量化测试成功！")
        return True
    else:
        logger.error("❌ 自动向量化测试失败！")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
