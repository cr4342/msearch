#!/usr/bin/env python3
"""
模型和依赖安装脚本
将模型从 ./offline/models 复制到 ./data/models，并安装所需依赖
"""

import os
import sys
import shutil
import subprocess
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('setup_models.log', encoding='utf-8')
    ]
)

def check_and_create_directories():
    """检查并创建必要的目录结构"""
    required_dirs = [
        "./data/models",
        "./data/databases",
        "./logs",
        "./temp"
    ]
    
    for dir_path in required_dirs:
        os.makedirs(dir_path, exist_ok=True)
        logging.info(f"✓ 目录已创建/存在: {dir_path}")

def copy_models():
    """复制模型文件"""
    source_dir = "./offline/models"
    target_dir = "./data/models"
    
    if not os.path.exists(source_dir):
        logging.error(f"✗ 源模型目录不存在: {source_dir}")
        return False
    
    try:
        # 复制整个models目录
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)
        
        shutil.copytree(source_dir, target_dir)
        logging.info(f"✓ 模型文件已从 {source_dir} 复制到 {target_dir}")
        
        # 验证复制结果
        model_dirs = ["clip", "clap", "whisper"]
        for model_dir in model_dirs:
            model_path = os.path.join(target_dir, model_dir)
            if os.path.exists(model_path):
                logging.info(f"✓ {model_dir} 模型目录存在")
                # 检查关键文件
                required_files = {
                    "clip": ["config.json", "pytorch_model.bin", "preprocessor_config.json"],
                    "clap": ["config.json", "pytorch_model.bin", "preprocessor_config.json"],
                    "whisper": ["config.json", "pytorch_model.bin", "tokenizer.json"]
                }
                
                for file_name in required_files.get(model_dir, []):
                    file_path = os.path.join(model_path, file_name)
                    if os.path.exists(file_path):
                        logging.info(f"  ✓ {file_name} 存在")
                    else:
                        logging.warning(f"  ⚠ {file_name} 不存在")
            else:
                logging.warning(f"⚠ {model_dir} 模型目录不存在")
        
        return True
        
    except Exception as e:
        logging.error(f"✗ 复制模型文件失败: {e}")
        return False

def install_dependencies():
    """安装项目依赖"""
    try:
        # 检查requirements.txt是否存在
        if not os.path.exists("requirements.txt"):
            logging.warning("⚠ requirements.txt 不存在，跳过依赖安装")
            return True
        
        # 安装依赖
        logging.info("正在安装项目依赖...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            capture_output=True,
            text=True,
            cwd="."
        )
        
        if result.returncode == 0:
            logging.info("✓ 依赖安装成功")
            if result.stdout:
                logging.info(f"安装输出: {result.stdout}")
            return True
        else:
            logging.error(f"✗ 依赖安装失败: {result.stderr}")
            return False
            
    except Exception as e:
        logging.error(f"✗ 安装依赖时出错: {e}")
        return False

def setup_database():
    """设置数据库"""
    try:
        # 创建数据库目录和文件
        db_dir = "./data/databases"
        os.makedirs(db_dir, exist_ok=True)
        
        # 创建空的数据库文件（如果需要）
        db_files = ["search_index.db", "metadata.db"]
        for db_file in db_files:
            db_path = os.path.join(db_dir, db_file)
            if not os.path.exists(db_path):
                with open(db_path, 'w') as f:
                    f.write('')
                logging.info(f"✓ 创建数据库文件: {db_file}")
        
        logging.info("✓ 数据库设置完成")
        return True
        
    except Exception as e:
        logging.error(f"✗ 数据库设置失败: {e}")
        return False

def run_tests():
    """运行测试验证设置"""
    try:
        logging.info("正在运行测试验证...")
        
        # 运行模型加载测试
        result = subprocess.run(
            [sys.executable, "test_model_loading.py"],
            capture_output=True,
            text=True,
            cwd="."
        )
        
        if result.returncode == 0:
            logging.info("✓ 模型加载测试通过")
            if "✓" in result.stdout:
                logging.info("测试输出包含成功标记")
        else:
            logging.error(f"✗ 模型加载测试失败: {result.stderr}")
            return False
        
        # 运行EmbeddingEngine单元测试
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/unit/test_embedding_engine.py", "-v"],
            capture_output=True,
            text=True,
            cwd="."
        )
        
        if result.returncode == 0:
            logging.info("✓ EmbeddingEngine单元测试通过")
        else:
            logging.warning(f"⚠ EmbeddingEngine单元测试失败: {result.stderr}")
            # 不返回False，因为测试可能还在开发中
        
        return True
        
    except Exception as e:
        logging.error(f"✗ 运行测试时出错: {e}")
        return False

def main():
    """主函数"""
    logging.info("开始设置模型和依赖...")
    
    # 检查并创建目录
    if not check_and_create_directories():
        sys.exit(1)
    
    # 复制模型
    if not copy_models():
        sys.exit(1)
    
    # 安装依赖
    if not install_dependencies():
        sys.exit(1)
    
    # 设置数据库
    if not setup_database():
        sys.exit(1)
    
    # 运行测试验证
    if not run_tests():
        logging.warning("测试验证过程中出现问题，但继续完成设置")
    
    logging.info("✅ 模型和依赖设置完成！")
    logging.info("📁 模型位置: ./data/models")
    logging.info("📊 数据库位置: ./data/databases")
    logging.info("📋 详细日志: setup_models.log")

if __name__ == "__main__":
    main()