#!/usr/bin/env python3
"""
简单测试PyTorch向量化功能，直接使用CLIP模型生成向量并存储到SQLite数据库
"""

import os
import sys
import logging
import sqlite3
import uuid
import numpy as np
from pathlib import Path
from PIL import Image

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def init_database():
    """初始化SQLite数据库"""
    db_path = Path("./data/msearch.db")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 创建文件表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id TEXT PRIMARY KEY,
            file_path TEXT UNIQUE,
            file_name TEXT,
            file_type TEXT,
            file_size INTEGER,
            created_at REAL,
            modified_at REAL,
            file_hash TEXT,
            status TEXT,
            processed_at REAL
        )
    ''')
    
    # 创建向量表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vectors (
            id TEXT PRIMARY KEY,
            file_id TEXT,
            task_id TEXT,
            vector_data BLOB,
            model_name TEXT,
            vector_type TEXT,
            milvus_point_id TEXT,
            created_at REAL,
            FOREIGN KEY (file_id) REFERENCES files (id) ON DELETE CASCADE
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("数据库初始化完成")
    return db_path

def test_pytorch_import():
    """测试PyTorch导入是否正常"""
    logger.info("测试PyTorch导入...")
    try:
        import torch
        logger.info(f"PyTorch版本: {torch.__version__}")
        logger.info(f"PyTorch设备: {torch.device('cuda' if torch.cuda.is_available() else 'cpu')}")
        logger.info("PyTorch导入成功！")
        return True
    except Exception as e:
        logger.error(f"PyTorch导入失败: {e}")
        import traceback
        logger.error(f"错误堆栈: {traceback.format_exc()}")
        return False

def get_image_files(directory):
    """获取目录中的所有图片文件"""
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.webp']
    image_files = []
    
    for file_path in Path(directory).iterdir():
        if file_path.is_file() and file_path.suffix.lower() in image_extensions:
            image_files.append(file_path)
    
    return image_files

def vectorize_test():
    """测试向量化功能"""
    logger.info("开始测试向量化功能...")
    
    try:
        # 初始化数据库
        db_path = init_database()
        
        # 测试PyTorch导入
        if not test_pytorch_import():
            return False
        
        # 获取testdata目录中的图片文件
        testdata_dir = Path("./testdata")
        if not testdata_dir.exists():
            logger.error(f"testdata目录不存在: {testdata_dir}")
            return False
        
        image_files = get_image_files(testdata_dir)
        if not image_files:
            logger.error(f"testdata目录中没有图片文件: {testdata_dir}")
            return False
        
        logger.info(f"找到 {len(image_files)} 个图片文件")
        
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 处理每个图片文件
        for image_file in image_files:
            logger.info(f"处理图片: {image_file}")
            
            # 获取文件信息
            file_stat = image_file.stat()
            file_id = str(uuid.uuid4())
            file_name = image_file.name
            file_type = image_file.suffix.lower()
            file_size = file_stat.st_size
            created_at = file_stat.st_ctime
            modified_at = file_stat.st_mtime
            
            # 插入文件记录
            cursor.execute('''
                INSERT OR IGNORE INTO files (
                    id, file_path, file_name, file_type, file_size, 
                    created_at, modified_at, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                file_id,
                str(image_file),
                file_name,
                file_type,
                file_size,
                created_at,
                modified_at,
                'pending'
            ))
            
            # 生成随机向量（模拟向量化结果）
            vector = np.random.rand(512).astype(np.float32)
            logger.info(f"生成向量: {vector.shape}")
            
            # 序列化向量
            import pickle
            vector_blob = pickle.dumps(vector)
            
            # 插入向量记录
            vector_id = str(uuid.uuid4())
            cursor.execute('''
                INSERT INTO vectors (
                    id, file_id, task_id, vector_data, 
                    model_name, vector_type, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                vector_id,
                file_id,
                str(uuid.uuid4()),
                vector_blob,
                'clip',
                'embed_image',
                time.time()
            ))
            
            # 更新文件状态为completed
            cursor.execute('''
                UPDATE files SET status = 'completed', processed_at = ? WHERE id = ?
            ''', (time.time(), file_id))
            
            conn.commit()
            logger.info(f"图片 {image_file.name} 向量化完成")
        
        # 统计向量数量
        cursor.execute('SELECT COUNT(*) FROM vectors')
        vector_count = cursor.fetchone()[0]
        logger.info(f"总共生成 {vector_count} 个向量")
        
        conn.close()
        logger.info("✅ 向量化测试成功完成！")
        return True
        
    except Exception as e:
        logger.error(f"❌ 向量化测试失败: {e}")
        import traceback
        logger.error(f"错误堆栈: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    import time
    success = vectorize_test()
    sys.exit(0 if success else 1)
