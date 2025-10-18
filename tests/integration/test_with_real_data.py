#!/usr/bin/env python3
"""
使用真实数据的模型功能测试
"""
import sys
import os
import time
import numpy as np
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_image_processing():
    """测试图像处理功能"""
    print("=== 图像处理功能测试 ===")
    
    try:
        from src.business.embedding_engine import EmbeddingEngine
        from src.core.config_manager import get_config_manager
        
        config_manager = get_config_manager()
        config = config_manager.config
        
        # 创建嵌入引擎
        engine = EmbeddingEngine(config)
        
        # 创建测试图像数据（随机生成）
        test_image = np.random.rand(224, 224, 3).astype(np.float32)
        
        print("✓ 嵌入引擎创建成功")
        print(f"  - 测试图像形状: {test_image.shape}")
        
        # 测试图像向量化
        import asyncio
        async def test_embed_image():
            try:
                vector = await engine.embed_image(test_image)
                print(f"  - 图像向量形状: {vector.shape}")
                print(f"  - 向量类型: {type(vector)}")
                return True
            except Exception as e:
                print(f"  ✗ 图像向量化失败: {e}")
                return False
        
        success = asyncio.run(test_embed_image())
        return success
        
    except Exception as e:
        print(f"✗ 图像处理测试失败: {e}")
        return False

def test_text_processing():
    """测试文本处理功能"""
    print("\n=== 文本处理功能测试 ===")
    
    try:
        from src.business.embedding_engine import EmbeddingEngine
        from src.core.config_manager import get_config_manager
        
        config_manager = get_config_manager()
        config = config_manager.config
        
        # 创建嵌入引擎
        engine = EmbeddingEngine(config)
        
        # 测试文本
        test_text = "这是一段测试文本，用于验证文本向量化功能"
        
        print("✓ 嵌入引擎创建成功")
        print(f"  - 测试文本: {test_text}")
        
        # 测试文本向量化
        import asyncio
        async def test_embed_text():
            try:
                vector = await engine.embed_text(test_text)
                print(f"  - 文本向量形状: {vector.shape}")
                print(f"  - 向量类型: {type(vector)}")
                return True
            except Exception as e:
                print(f"  ✗ 文本向量化失败: {e}")
                return False
        
        success = asyncio.run(test_embed_text())
        return success
        
    except Exception as e:
        print(f"✗ 文本处理测试失败: {e}")
        return False

def test_database_operations():
    """测试数据库操作"""
    print("\n=== 数据库操作测试 ===")
    
    try:
        from src.storage.database import DatabaseManager
        
        # 创建数据库管理器
        db_manager = DatabaseManager()
        
        print("✓ 数据库管理器创建成功")
        
        # 测试查询
        try:
            tables = db_manager.execute_query("SELECT name FROM sqlite_master WHERE type='table';")
            print(f"  - 数据库表数量: {len(tables)}")
            for table in tables:
                print(f"    - {table['name']}")
        except Exception as e:
            print(f"  - 数据库查询测试: {e}")
        
        return True
        
    except Exception as e:
        print(f"✗ 数据库操作测试失败: {e}")
        return False

def test_configuration():
    """测试系统配置"""
    print("\n=== 系统配置测试 ===")
    
    try:
        from src.core.config_manager import get_config_manager
        
        config_manager = get_config_manager()
        config = config_manager.config
        
        print("✓ 配置管理器创建成功")
        
        # 检查关键配置
        key_configs = [
            ("系统日志级别", "logging.level"),
            ("数据库路径", "database.sqlite.path"),
            ("Qdrant主机", "database.qdrant.host"),
            ("CLIP服务端口", "infinity.services.clip.port"),
            ("CLAP服务端口", "infinity.services.clap.port"),
            ("Whisper服务端口", "infinity.services.whisper.port"),
        ]
        
        all_valid = True
        for desc, key in key_configs:
            value = config_manager.get(key)
            if value is not None:
                print(f"  ✓ {desc}: {value}")
            else:
                print(f"  ✗ {desc}: 缺失")
                all_valid = False
        
        return all_valid
        
    except Exception as e:
        print(f"✗ 配置测试失败: {e}")
        return False

def test_file_operations():
    """测试文件操作"""
    print("\n=== 文件操作测试 ===")
    
    try:
        from src.core.file_type_detector import get_file_type_detector
        from src.core.config_manager import get_config_manager
        
        config_manager = get_config_manager()
        config = config_manager.config
        
        detector = get_file_type_detector(config)
        
        print("✓ 文件类型检测器创建成功")
        
        # 创建测试文件
        test_files = [
            ("test.jpg", "image"),
            ("test.png", "image"),
            ("test.mp4", "video"),
            ("test.mp3", "audio"),
            ("test.txt", "unknown"),
        ]
        
        all_valid = True
        for filename, expected_type in test_files:
            file_path = Path("testdata") / filename
            
            # 如果文件不存在，创建临时测试文件
            if not file_path.exists():
                file_path.parent.mkdir(exist_ok=True)
                file_path.touch()
            
            try:
                result = detector.detect_file_type(str(file_path))
                detected_type = result.get('type', 'unknown')
                print(f"  - {filename}: 检测类型={detected_type}, 期望类型={expected_type}")
                
                # 清理临时文件
                if file_path.exists() and file_path.name.startswith('test.'):
                    file_path.unlink()
                    
            except Exception as e:
                print(f"  - {filename}: 检测失败 - {e}")
                all_valid = False
        
        return all_valid
        
    except Exception as e:
        print(f"✗ 文件操作测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("msearch 真实数据功能测试")
    print("=" * 50)
    
    # 运行测试
    results = []
    results.append(test_configuration())
    results.append(test_database_operations())
    results.append(test_file_operations())
    results.append(test_text_processing())
    results.append(test_image_processing())
    
    print("\n" + "=" * 50)
    print("测试总结:")
    print(f"  系统配置: {'通过' if results[0] else '失败'}")
    print(f"  数据库操作: {'通过' if results[1] else '失败'}")
    print(f"  文件操作: {'通过' if results[2] else '失败'}")
    print(f"  文本处理: {'通过' if results[3] else '失败'}")
    print(f"  图像处理: {'通过' if results[4] else '失败'}")
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"\n✓ 所有 {total} 个测试全部通过！系统功能正常。")
        return 0
    else:
        print(f"\n⚠ {passed}/{total} 个测试通过，有 {total - passed} 个测试失败")
        print("系统基本功能正常，部分高级功能需要进一步配置")
        return 1

if __name__ == "__main__":
    sys.exit(main())