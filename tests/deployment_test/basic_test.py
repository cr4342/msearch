import os
import sys
from pathlib import Path

# 设置项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

print("=== MSearch 基本测试 ===")
print(f"项目根目录: {PROJECT_ROOT}")
print(f"Python版本: {sys.version}")
print(f"Python路径: {sys.path[:3]}")

# 测试基本导入
try:
    from src.core.config import load_config
    print("✓ 配置模块导入成功")
except Exception as e:
    print(f"✗ 配置模块导入失败: {e}")

try:
    from src.core.logging_config import setup_logging
    print("✓ 日志配置模块导入成功")
except Exception as e:
    print(f"✗ 日志配置模块导入失败: {e}")

# 测试API模块
try:
    from src.api.main import app
    print("✓ API模块导入成功")
    print(f"API标题: {app.title}")
except Exception as e:
    print(f"✗ API模块导入失败: {e}")

# 测试模型加载
try:
    os.environ["HF_HOME"] = str(PROJECT_ROOT / "offline" / "models")
    os.environ["TRANSFORMERS_CACHE"] = str(PROJECT_ROOT / "offline" / "models")
    
    from transformers import CLIPModel, CLIPProcessor
    clip_path = PROJECT_ROOT / "offline" / "models" / "clip-vit-base-patch32"
    
    if clip_path.exists():
        print("✓ 发现CLIP模型路径")
        try:
            clip_model = CLIPModel.from_pretrained(str(clip_path), local_files_only=True)
            print("✓ CLIP模型加载成功")
        except Exception as e:
            print(f"✗ CLIP模型加载失败: {e}")
    else:
        print("✗ CLIP模型路径不存在")
except Exception as e:
    print(f"✗ 模型测试失败: {e}")

print("=== 测试完成 ===")