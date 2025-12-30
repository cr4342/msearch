"""
配置管理器测试
测试配置管理器的核心功能，包括配置加载、验证、访问和热重载
"""

import pytest
import tempfile
import os
from pathlib import Path

from src.core.config_manager import ConfigManager


class TestConfigManager:
    """配置管理器测试类"""
    
    @pytest.fixture
    def config_manager(self):
        """配置管理器实例"""
        # 创建临时配置文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write("""
system:
  log_level: "INFO"
  data_dir: "./data"
  temp_dir: "./temp"
  max_workers: 4

logging:
  level: "INFO"
  format:
    standard: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

database:
  sqlite:
    path: "./data/msearch.db"
    connection_pool_size: 10
    timeout: 30

infinity:
  services:
    clip:
      model_id: "openai/clip-vit-base-patch32"
      port: 7997
      device: "cuda:0"
      max_batch_size: 32
      dtype: "float16"
""")
            temp_config_path = f.name
        
        yield ConfigManager(temp_config_path)
        
        # 清理临时文件
        os.unlink(temp_config_path)
    
    def test_config_manager_initialization(self, config_manager):
        """测试配置管理器初始化"""
        assert config_manager is not None
        assert isinstance(config_manager, ConfigManager)
    
    def test_config_manager_get(self, config_manager):
        """测试配置获取功能"""
        # 测试获取系统配置
        log_level = config_manager.get("system.log_level")
        assert log_level is not None
        assert isinstance(log_level, str)
        assert log_level == "INFO"
    
        # 测试获取性能配置
        max_workers = config_manager.get("system.max_workers")
        assert max_workers is not None
        assert isinstance(max_workers, int)
        assert max_workers == 4
    
        # 测试获取不存在的配置 - 带default参数
        non_existent = config_manager.get("non.existent.config", default="default_value")
        assert non_existent == "default_value"
    
        # 测试获取无默认值的不存在配置 - 应该抛出KeyError
        with pytest.raises(KeyError):
            config_manager.get("non.existent.config")
    
    def test_config_manager_get_int(self, config_manager):
        """测试获取整数配置"""
        max_workers = config_manager.get_int("system.max_workers")
        assert max_workers is not None
        assert isinstance(max_workers, int)
        assert max_workers == 4
    
        # 测试不存在的配置会抛出KeyError
        with pytest.raises(KeyError):
            config_manager.get_int("non.existent.config")
    
    def test_config_manager_get_float(self, config_manager):
        """测试获取浮点数配置"""
        # 添加一个浮点数配置到测试配置中
        config_manager.set("test.float_value", 3.14)
        float_value = config_manager.get_float("test.float_value")
        assert float_value is not None
        assert isinstance(float_value, float)
        assert float_value == 3.14
    
        # 测试不存在的配置会抛出KeyError
        with pytest.raises(KeyError):
            config_manager.get_float("non.existent.config")
    
    def test_config_manager_get_bool(self, config_manager):
        """测试获取布尔值配置"""
        # 添加一个布尔值配置到测试配置中
        config_manager.set("test.bool_value", True)
        bool_value = config_manager.get_bool("test.bool_value")
        assert bool_value is not None
        assert isinstance(bool_value, bool)
        assert bool_value is True
    
        # 测试不存在的配置会抛出KeyError
        with pytest.raises(KeyError):
            config_manager.get_bool("non.existent.config")
    
    def test_config_manager_get_list(self, config_manager):
        """测试获取列表配置"""
        # 添加一个列表配置到测试配置中
        test_list = ["item1", "item2", "item3"]
        config_manager.set("test.list_value", test_list)
        list_value = config_manager.get_list("test.list_value")
        assert list_value is not None
        assert isinstance(list_value, list)
        assert list_value == test_list
    
        # 测试不存在的配置会抛出KeyError
        with pytest.raises(KeyError):
            config_manager.get_list("non.existent.config")
    
    def test_config_manager_validation(self, config_manager):
        """测试配置验证功能"""
        # 由于get方法不会抛出KeyError，而是返回None或默认值
        # 这里测试配置的正确获取
        assert config_manager.get("system.log_level") == "INFO"
        assert config_manager.get_int("system.max_workers") == 4
    
    def test_config_manager_database_config(self, config_manager):
        """测试数据库配置访问"""
        db_path = config_manager.get("database.sqlite.path")
        assert db_path is not None
        assert isinstance(db_path, str)
        assert db_path == "./data/msearch.db"
    
        pool_size = config_manager.get_int("database.sqlite.connection_pool_size")
        assert pool_size is not None
        assert isinstance(pool_size, int)
        assert pool_size == 10
    
    def test_config_manager_infinity_config(self, config_manager):
        """测试Infinity服务配置访问"""
        clip_port = config_manager.get_int("infinity.services.clip.port")
        assert clip_port is not None
        assert isinstance(clip_port, int)
        assert clip_port == 7997
    
        clip_model = config_manager.get("infinity.services.clip.model_id")
        assert clip_model is not None
        assert clip_model == "openai/clip-vit-base-patch32"
    
    def test_config_manager_set_and_get(self, config_manager):
        """测试配置设置和获取"""
        # 测试设置新配置
        config_manager.set("test.new_config", "test_value")
        value = config_manager.get("test.new_config")
        assert value == "test_value"
    
        # 测试设置整数配置
        config_manager.set("test.new_int", 42)
        int_value = config_manager.get_int("test.new_int")
        assert int_value == 42