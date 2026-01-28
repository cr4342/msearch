#!/usr/bin/env python3
"""
模型设置脚本
用于下载和配置AI模型
使用 Infinity 框架统一管理模型
"""

import os
import sys
import argparse
import asyncio
from pathlib import Path
import logging

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

try:
    from src.core.config.config_manager import ConfigManager
    from src.core.embedding.embedding_engine import EmbeddingEngine
except ImportError as e:
    logger.error(f"导入模块失败: {e}")
    logger.error("请确保已安装所有依赖: pip install -r requirements.txt")
    sys.exit(1)


def print_info(message):
    """打印信息"""
    logger.info(message)


def print_success(message):
    """打印成功信息"""
    logger.info(f"✓ {message}")


def print_warning(message):
    """打印警告信息"""
    logger.warning(f"⚠️  {message}")


def print_error(message):
    """打印错误信息"""
    logger.error(f"✗ {message}")


async def setup_models(config_dir="config", config_file="config.yml", model_types=None, force=False):
    """
    设置AI模型
    
    Args:
        config_dir: 配置目录
        config_file: 配置文件名
        model_types: 要设置的模型类型列表，None表示设置所有模型
                      支持的类型: image_video, audio
        force: 是否强制重新下载（即使模型已存在）
    """
    print_info("开始设置AI模型...")
    
    # 检查模型是否已完整下载（如果不需要强制下载）
    if not force:
        print_info("检查模型完整性...")
        all_complete = check_models()
        if all_complete:
            print_success("所有模型已完整下载，跳过下载")
            return
        else:
            print_info("部分模型不完整或未下载，继续下载...")
    
    # 加载配置
    print_info("加载配置...")
    config_path = Path(config_dir) / config_file
    config = ConfigManager(config_path=str(config_path))
    
    # 获取模型配置
    models_config = config.get("models", {})
    model_cache_dir = models_config.get("model_cache_dir", "data/models")
    available_models = models_config.get("available_models", {})
    active_models = models_config.get("active_models", [])
    
    # 确定要设置的模型
    if model_types is None:
        # 获取所有活跃模型类型
        model_types = []
        for model_id in active_models:
            model_config = available_models.get(model_id, {})
            model_name = model_config.get("model_name", "")
            if "clip" in model_name.lower():
                model_types.append("image_video")
            elif "clap" in model_name.lower() or "audio" in model_id.lower():
                model_types.append("audio")
    
    # 创建向量化引擎
    print_info("初始化向量化引擎...")
    embedding_engine = EmbeddingEngine(config=config)
    
    # 设置图像/视频模型
    if "image_video" in model_types:
        await setup_image_video_model(embedding_engine, available_models, active_models, force)
    
    # 设置音频模型
    if "audio" in model_types:
        await setup_audio_model(embedding_engine, available_models, active_models, force)
    
    print_success("所有模型设置完成！")


async def setup_image_video_model(embedding_engine, available_models, active_models, force=False):
    """设置图像/视频模型"""
    print_info("设置图像/视频模型...")
    
    try:
        # 获取活跃的图像/视频模型
        for model_id in active_models:
            model_config = available_models.get(model_id, {})
            model_name = model_config.get("model_name", "")
            
            if "clip" in model_name.lower():
                # 检查模型是否已存在且完整
                if not force and is_model_complete(model_id, model_name, available_models):
                    print_success(f"图像/视频模型 {model_id} 已完整下载，跳过")
                    break
                
                print_info(f"加载图像/视频模型: {model_name}")
                print_info("这可能需要几分钟...")
                
                # 加载模型（这将触发模型下载）
                await embedding_engine._ensure_models_loaded()
                
                print_success(f"图像/视频模型 {model_id} 设置完成")
                break
    except Exception as e:
        print_error(f"设置图像/视频模型失败: {e}")


async def setup_audio_model(embedding_engine, available_models, active_models, force=False):
    """设置音频模型"""
    print_info("设置音频模型...")
    
    try:
        # 获取活跃的音频模型
        for model_id in active_models:
            model_config = available_models.get(model_id, {})
            model_name = model_config.get("model_name", "")
            
            if "clap" in model_name.lower() or "audio" in model_id.lower():
                # 检查模型是否已存在且完整
                if not force and is_model_complete(model_id, model_name, available_models):
                    print_success(f"音频模型 {model_id} 已完整下载，跳过")
                    break
                
                print_info(f"加载音频模型: {model_name}")
                print_info("这可能需要几分钟...")
                
                # 加载模型（这将触发模型下载）
                await embedding_engine._ensure_models_loaded()
                
                print_success(f"音频模型 {model_id} 设置完成")
                break
    except Exception as e:
        print_error(f"设置音频模型失败: {e}")


def is_model_complete(model_id: str, model_name: str, available_models: dict) -> bool:
    """
    检查模型是否完整
    
    Args:
        model_id: 模型ID
        model_name: 模型名称
        available_models: 可用模型配置
    
    Returns:
        模型是否完整
    """
    # 加载配置
    config = ConfigManager()
    models_config = config.get("models", {})
    model_cache_dir = models_config.get("model_cache_dir", "data/models")
    
    # 使用绝对路径
    cache_path = Path(model_cache_dir).resolve()
    project_root = Path(__file__).parent.parent.resolve()
    
    if not cache_path.exists():
        return False
    
    # 获取模型路径
    model_config = available_models.get(model_id, {})
    local_path = model_config.get("local_path", "")
    
    if local_path:
        # 如果是相对路径，相对于项目根目录
        if Path(local_path).is_absolute():
            model_path = Path(local_path)
        else:
            model_path = project_root / local_path
    else:
        model_name_clean = model_name.replace("/", "_").replace("\\", "_")
        model_path = cache_path / model_name_clean
    
    if not model_path.exists():
        return False
    
    # 检查必需文件
    if not (model_path / "config.json").exists():
        return False
    
    # 检查权重文件
    has_weights = False
    for f in model_path.rglob("*.safetensors"):
        has_weights = True
        break
    if not has_weights:
        for f in model_path.rglob("pytorch_model.bin"):
            has_weights = True
            break
    
    if not has_weights:
        return False
    
    # 检查词汇表（如果是文本模型）
    if not (model_path / "vocab.txt").exists() and not (model_path / "tokenizer.json").exists():
        return False
    
    return True


def check_models():
    """检查模型是否已下载"""
    print_info("检查模型状态...")
    
    # 加载配置
    config = ConfigManager()
    
    # 获取模型配置
    models_config = config.get("models", {})
    available_models = models_config.get("available_models", {})
    active_models = models_config.get("active_models", [])
    model_cache_dir = models_config.get("model_cache_dir", "data/models")
    
    # 使用绝对路径
    cache_path = Path(model_cache_dir).resolve()
    project_root = Path(__file__).parent.parent.resolve()
    
    if not cache_path.exists():
        print_warning("模型缓存目录不存在")
        return False
    
    # 检查活跃模型
    print_info(f"检查 {len(active_models)} 个活跃模型...")
    
    checked_count = 0
    for model_id in active_models:
        model_config = available_models.get(model_id, {})
        model_name = model_config.get("model_name", "")
        local_path = model_config.get("local_path", "")
        
        # 处理本地路径
        if local_path:
            # 如果是相对路径，相对于项目根目录
            if Path(local_path).is_absolute():
                model_path = Path(local_path)
            else:
                model_path = project_root / local_path
        else:
            # 如果没有指定本地路径，使用模型名称创建路径
            model_name_clean = model_name.replace("/", "_").replace("\\", "_")
            model_path = cache_path / model_name_clean
        
        if model_path.exists():
            # 检查模型文件完整性
            required_files = ["config.json"]
            has_weights = False
            missing_files = []
            
            # 检查必需文件
            for req_file in required_files:
                if (model_path / req_file).exists():
                    continue
                else:
                    missing_files.append(req_file)
            
            # 检查权重文件（safetensors或pytorch_model.bin）
            for f in model_path.rglob("*.safetensors"):
                has_weights = True
                break
            if not has_weights:
                for f in model_path.rglob("pytorch_model.bin"):
                    has_weights = True
                    break
            if not has_weights:
                missing_files.append("权重文件(safetensors/pytorch_model.bin)")
            
            # 检查词汇表（如果是文本模型）
            if not (model_path / "vocab.txt").exists() and not (model_path / "tokenizer.json").exists():
                missing_files.append("词汇表文件")
            
            if not missing_files:
                size = sum(f.stat().st_size for f in model_path.rglob('*') if f.is_file())
                size_mb = size / (1024 * 1024)
                print_success(f"{model_id} ({model_name}): 已完整下载 ({size_mb:.2f} MB)")
                checked_count += 1
            else:
                print_warning(f"{model_id} ({model_name}): 下载不完整，缺少文件: {', '.join(missing_files)}")
        else:
            print_warning(f"{model_id} ({model_name}): 未下载")
    
    print_info(f"共检查 {len(active_models)} 个模型，已完整下载 {checked_count} 个")
    
    return checked_count == len(active_models)


def clear_models():
    """清除已下载的模型（chinese-clip-vit-huge-patch14和CLAP）"""
    print_warning("此操作将删除所有已下载的模型文件（chinese-clip-vit-huge-patch14和CLAP）")
    response = input("确定要继续吗？(yes/no): ")
    
    if response.lower() != "yes":
        print_info("操作已取消")
        return
    
    # 加载配置
    config = ConfigManager()
    
    # 获取模型缓存目录
    models_config = config.get("models", {})
    model_cache_dir = models_config.get("model_cache_dir", "data/models")
    cache_path = Path(model_cache_dir)
    
    if not cache_path.exists():
        print_warning("模型缓存目录不存在")
        return
    
    # 删除模型文件
    import shutil
    try:
        shutil.rmtree(cache_path)
        print_success("所有模型文件已删除")
    except Exception as e:
        print_error(f"删除模型文件失败: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="msearch模型设置脚本")
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # setup命令
    setup_parser = subparsers.add_parser("setup", help="设置AI模型")
    setup_parser.add_argument(
        "--config-dir",
        default="config",
        help="配置目录（默认: config）"
    )
    setup_parser.add_argument(
        "--config-file",
        default="config.yml",
        help="配置文件名（默认: config.yml）"
    )
    setup_parser.add_argument(
        "--models",
        nargs="+",
        choices=["image_video", "audio"],
        help="要设置的模型类型（默认: 所有模型）"
    )
    setup_parser.add_argument(
        "--force",
        action="store_true",
        help="强制重新下载（即使模型已存在）"
    )
    
    # check命令
    subparsers.add_parser("check", help="检查模型状态")
    
    # clear命令
    subparsers.add_parser("clear", help="清除已下载的模型")
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(1)
    
    if args.command == "setup":
        asyncio.run(setup_models(
            config_dir=args.config_dir,
            config_file=args.config_file,
            model_types=args.models,
            force=args.force
        ))
    elif args.command == "check":
        check_models()
    elif args.command == "clear":
        clear_models()


if __name__ == "__main__":
    main()