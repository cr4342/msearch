"""
简单测试脚本：测试单个图像处理（简化版）
"""
import sys
import os
import asyncio
from pathlib import Path

# 设置离线模式环境变量
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.config.config_manager import ConfigManager
from src.core.embedding.embedding_engine import EmbeddingEngine


async def test_single_image():
    """测试单个图像处理"""
    print("=" * 60)
    print("测试单个图像处理")
    print("=" * 60)
    
    # 1. 初始化配置管理器
    print("\n1. 初始化配置...")
    config_manager = ConfigManager()
    print(f"   配置加载成功")
    
    # 2. 初始化向量化引擎
    print("\n2. 初始化向量化引擎...")
    embedding_engine = EmbeddingEngine(config=config_manager.config)
    print(f"   向量化引擎初始化完成")
    
    # 3. 获取testdata目录中的第一个图像文件
    testdata_dir = Path('testdata')
    if not testdata_dir.exists():
        print(f"\n错误: testdata目录不存在")
        return False
    
    image_files = list(testdata_dir.glob('*.jpg')) + list(testdata_dir.glob('*.jpeg')) + list(testdata_dir.glob('*.png'))
    if len(image_files) == 0:
        print(f"\n错误: 没有找到图像文件")
        return False
    
    image_file = image_files[0]
    print(f"\n3. 测试文件: {image_file.name}")
    
    # 4. 生成向量
    print(f"\n4. 开始向量化...")
    import time
    start_time = time.time()
    
    try:
        vector = await embedding_engine.embed_image(str(image_file))
        
        elapsed_time = time.time() - start_time
        print(f"   向量化成功，耗时: {elapsed_time:.2f}秒")
        print(f"   向量维度: {len(vector)}")
        
        # 显示前5个向量值
        print(f"   向量前5个值: {[f'{v:.4f}' for v in vector[:5]]}")
        
        return True
    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"   向量化失败，耗时: {elapsed_time:.2f}秒")
        print(f"   错误: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(test_single_image())
        if success:
            print("\n测试成功!")
        else:
            print("\n测试失败")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
