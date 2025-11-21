"""
配置管理模块 - 兼容层
负责加载和管理应用程序配置，使用新的ConfigManager
"""

from typing import Dict, Any
from src.core.config_manager import get_config_manager, get_config as get_new_config


def load_config(config_path: str = None) -> Dict[str, Any]:
    """
    加载配置文件(兼容旧接口)
    
    Args:
        config_path: 配置文件路径(为保持兼容性而保留，但不再使用)
        
    Returns:
        配置字典
    """
    # 使用新的配置管理器
    return get_new_config()


def get_model_config(config: Dict[str, Any], model_type: str) -> str:
    """
    根据硬件模式获取模型配置(兼容旧接口)
    
    Args:
        config: 配置字典
        model_type: 模型类型 (clip, clap, whisper)
        
    Returns:
        模型名称
    """
    config_manager = get_config_manager()
    
    # 获取硬件模式
    hardware_mode = config_manager.get("hardware_mode", "cpu")
    
    # 获取模型配置
    if model_type == "clip":
        return config_manager.get(f"infinity.services.clip.model_id", "openai/clip-vit-base-patch32")
    elif model_type == "clap":
        return config_manager.get(f"infinity.services.clap.model_id", "laion/clap-htsat-fused")
    elif model_type == "whisper":
        return config_manager.get(f"infinity.services.whisper.model_id", "openai/whisper-base")
    
    # 默认返回CPU模型
    defaults = {
        "clip": "openai/clip-vit-base-patch32",
        "clap": "laion/clap-htsat-fused",
        "whisper": "openai/whisper-base"
    }
    
    return defaults.get(model_type, "")


def get_config() -> Dict[str, Any]:
    """
    获取全局配置实例
    
    Returns:
        配置字典
    """
    return get_new_config()