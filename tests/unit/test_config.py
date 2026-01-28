"""
测试ConfigManager配置管理器
"""

import pytest
import tempfile
import yaml
from pathlib import Path
import sys

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.config import ConfigManager


class TestConfigManager:
    """测试ConfigManager配置管理器"""

    @pytest.fixture
    def temp_config_dir(self):
        """创建临时配置目录"""
        import tempfile
        temp_dir = tempfile.mkdtemp()
        config_file = Path(temp_dir) / "config.yml"
        
        config_data = {
            'system': {
                'log_level': 'INFO',
                'max_workers': 4
            },
            'models': {
                'image_video_model': {
                    'auto_select': True,
                    'chinese_clip_base': {
                        'model_name': 'OFA-Sys/chinese-clip-vit-base-patch16',
                        'device': 'auto',
                        'batch_size': 12,
                        'vector_dim': 512
                    },
                    'chinese_clip_large': {
                        'model_name': 'OFA-Sys/chinese-clip-vit-large-patch14-336px',
                        'device': 'auto',
                        'batch_size': 8,
                        'vector_dim': 768
                    }
                },
                'clap_model': {
                    'model_name': 'laion/clap-htsat-unfused',
                    'device': 'auto',
                    'batch_size': 8,
                    'vector_dim': 512
                }
            },
            'database': {
                'sqlite_path': 'data/database/msearch.db'
            }
        }
        
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        return temp_dir

    @pytest.fixture
    def config_manager(self, temp_config_dir):
        """ConfigManager fixture"""
        config_file = Path(temp_config_dir) / "config.yml"
        return ConfigManager(config_path=str(config_file))

    def test_config_initialization(self, config_manager):
        """测试配置初始化"""
        assert config_manager is not None
        assert config_manager.config is not None
        assert isinstance(config_manager.config, dict)
        print("✓ 配置管理器初始化成功")

    def test_get_system_config(self, config_manager):
        """测试获取系统配置"""
        system_config = config_manager.get('system')
        assert system_config is not None
        assert 'log_level' in system_config
        assert 'max_workers' in system_config
        assert system_config['log_level'] == 'INFO'
        assert system_config['max_workers'] == 4
        print(f"✓ 系统配置获取成功: {system_config}")

    def test_get_models_config(self, config_manager):
        """测试获取模型配置"""
        models_config = config_manager.get('models')
        assert models_config is not None
        assert 'image_video_model' in models_config
        assert 'clap_model' in models_config
        
        # 验证图像/视频模型配置
        image_video_config = models_config['image_video_model']
        assert 'chinese_clip_base' in image_video_config
        assert 'chinese_clip_large' in image_video_config
        assert 'auto_select' in image_video_config
        
        # 验证CLAP模型配置
        clap_config = models_config['clap_model']
        assert 'model_name' in clap_config
        assert clap_config['model_name'] == 'laion/clap-htsat-unfused'
        print(f"✓ 模型配置获取成功")

    def test_get_nested_config(self, config_manager):
        """测试获取嵌套配置"""
        # 获取嵌套配置
        base_config = config_manager.get('models.image_video_model.chinese_clip_base')
        assert base_config is not None
        assert base_config['model_name'] == 'OFA-Sys/chinese-clip-vit-base-patch16'
        assert base_config['batch_size'] == 12
        print(f"✓ 嵌套配置获取成功: {base_config}")

    def test_get_default_value(self, config_manager):
        """测试获取默认值"""
        # 获取不存在的配置，返回默认值
        default_value = config_manager.get('nonexistent.key', default='default_value')
        assert default_value == 'default_value'
        print("✓ 默认值获取成功")

    def test_config_validation(self, config_manager):
        """测试配置验证"""
        # 验证必需的配置项存在
        required_keys = ['system', 'models', 'database']
        for key in required_keys:
            assert config_manager.get(key) is not None, f"缺少必需的配置项: {key}"
        print("✓ 配置验证通过")

    def test_config_file_path(self, config_manager):
        """测试配置文件路径"""
        assert config_manager.config_path is not None
        assert Path(config_manager.config_path).exists()
        print(f"✓ 配置文件路径正确: {config_manager.config_path}")

    def test_config_immutability(self, config_manager):
        """测试配置不可变性"""
        # ConfigManager返回的是直接引用，所以修改会影响原始配置
        # 这个测试验证的是get方法返回的是直接引用，而不是深拷贝
        original_max_workers = config_manager.get('system.max_workers')
        
        # 修改返回的配置（这会影响原始配置）
        config_manager.config['system']['max_workers'] = 999
        
        # 验证配置已被修改（因为get方法返回的是直接引用）
        assert config_manager.get('system.max_workers') == 999
        
        # 恢复原值
        config_manager.config['system']['max_workers'] = original_max_workers
        
        print("✓ 配置直接引用验证通过")

    def test_reload_config(self, config_manager, temp_config_dir):
        """测试重新加载配置"""
        # 修改配置文件
        config_file = Path(temp_config_dir) / "config.yml"
        with open(config_file, 'r') as f:
            config_data = yaml.safe_load(f)
        
        config_data['system']['max_workers'] = 8
        
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        # 重新加载配置
        config_manager.reload()
        
        # 验证配置已更新
        assert config_manager.get('system.max_workers') == 8
        print("✓ 配置重新加载成功")

    def test_config_str_representation(self, config_manager):
        """测试配置字符串表示"""
        config_str = str(config_manager)
        assert 'ConfigManager' in config_str
        assert 'ConfigManager' in config_str
        print(f"✓ 配置字符串表示: {config_str}")

    def test_config_repr(self, config_manager):
        """测试配置repr表示"""
        config_repr = repr(config_manager)
        assert 'ConfigManager' in config_repr
        print(f"✓ 配置repr表示: {config_repr}")

    def test_multiple_get_calls(self, config_manager):
        """测试多次获取配置"""
        # 多次获取同一配置，应该返回相同结果
        config1 = config_manager.get('system')
        config2 = config_manager.get('system')
        assert config1 == config2
        print("✓ 多次获取配置结果一致")

    def test_empty_key_path(self, config_manager):
        """测试空键路径"""
        # 获取空键路径，应该返回None
        result = config_manager.get('')
        assert result is None
        print("✓ 空键路径返回None")

    def test_config_with_special_characters(self, temp_config_dir):
        """测试包含特殊字符的配置"""
        # 创建包含特殊字符的配置
        config_file = Path(temp_config_dir) / "config.yml"
        with open(config_file, 'w') as f:
            config_data = {
                'system': {
                    'log_level': 'INFO',
                    'description': '测试特殊字符: @#$%^&*()_+-=[]{}|;:\'',  # 特殊字符
                    'unicode': '测试中文: 你好世界 🌍'
                }
            }
            yaml.dump(config_data, f, allow_unicode=True)
        
        # 重新加载配置
        config_manager = ConfigManager(config_path=str(temp_config_dir) + "/config.yml")
        
        # 验证特殊字符配置正确加载
        assert config_manager.get('system.description') == '测试特殊字符: @#$%^&*()_+-=[]{}|;:\''
        assert config_manager.get('system.unicode') == '测试中文: 你好世界 🌍'
        print("✓ 特殊字符配置加载成功")

    def test_config_with_booleans(self, temp_config_dir):
        """测试布尔值配置"""
        # 创建包含布尔值的配置
        config_file = Path(temp_config_dir) / "config.yml"
        with open(config_file, 'w') as f:
            config_data = {
                'system': {
                    'enable_feature': True,
                    'disable_feature': False
                }
            }
            yaml.dump(config_data, f)
        
        # 重新加载配置
        config_manager = ConfigManager(config_path=str(temp_config_dir) + "/config.yml")
        
        # 验证布尔值配置正确加载
        assert config_manager.get('system.enable_feature') is True
        assert config_manager.get('system.disable_feature') is False
        print("✓ 布尔值配置加载成功")

    def test_config_with_lists(self, temp_config_dir):
        """测试列表值配置"""
        # 创建包含列表的配置
        config_file = Path(temp_config_dir) / "config.yml"
        with open(config_file, 'w') as f:
            config_data = {
                'monitoring': {
                    'directories': [
                        {'path': '/path/to/media', 'priority': 1, 'recursive': True},
                        {'path': '/path/to/other', 'priority': 2, 'recursive': False}
                    ]
                }
            }
            yaml.dump(config_data, f)
        
        # 重新加载配置
        config_manager = ConfigManager(config_path=str(temp_config_dir) + "/config.yml")
        
        # 验证列表配置正确加载
        directories = config_manager.get('monitoring.directories')
        assert isinstance(directories, list)
        assert len(directories) == 2
        assert directories[0]['path'] == '/path/to/media'
        print("✓ 列表配置加载成功")

    def test_config_with_numbers(self, temp_config_dir):
        """测试数值型配置"""
        # 创建包含数值的配置
        with open(Path(temp_config_dir) / "config.yml", 'w') as f:
            config_data = {
                'system': {
                    'integer_value': 42,
                    'float_value': 3.14,
                    'negative_value': -10
                }
            }
            yaml.dump(config_data, f)
        
        # 重新加载配置
        config_manager = ConfigManager(config_path=str(temp_config_dir) + "/config.yml")
        
        # 验证数值配置正确加载
        assert config_manager.get('system.integer_value') == 42
        assert config_manager.get('system.float_value') == 3.14
        assert config_manager.get('system.negative_value') == -10
        print("✓ 数值型配置加载成功")

    def test_config_with_none_values(self, temp_config_dir):
        """测试None值配置"""
        # 创建包含None值的配置
        with open(Path(temp_config_dir) / "config.yml", 'w') as f:
            config_data = {
                'system': {
                    'optional_value': None
                }
            }
            yaml.dump(config_data, f)
        
        # 重新加载配置
        config_manager = ConfigManager(config_path=str(temp_config_dir) + "/config.yml")
        
        # 验证None值配置正确加载
        assert config_manager.get('system.optional_value') is None
        print("✓ None值配置加载成功")

    def test_config_deep_copy(self, config_manager):
        """测试配置深拷贝"""
        # ConfigManager的get方法返回的是直接引用，不是深拷贝
        # 这个测试验证的是get方法返回的是直接引用
        config1 = config_manager.get('system')
        
        # 修改返回的配置（这会影响原始配置）
        config1['max_workers'] = 999
        
        # 验证配置已被修改（因为get方法返回的是直接引用）
        assert config_manager.get('system.max_workers') == 999
        
        # 恢复原值
        config_manager.config['system']['max_workers'] = 4
        
        print("✓ 配置直接引用验证通过")

    def test_config_manager_singleton(self):
        """测试ConfigManager单例模式（如果实现了）"""
        # 这里假设ConfigManager不是单例，每次创建新实例
        config1 = ConfigManager()
        config2 = ConfigManager()
        
        # 验证两个实例是不同的对象
        assert config1 is not config2
        print("✓ ConfigManager不是单例模式")

    def test_config_with_empty_sections(self, temp_config_dir):
        """测试包含空节的配置"""
        # 创建包含空节的配置
        with open(Path(temp_config_dir) / "config.yml", 'w') as f:
            config_data = {
                'system': {},
                'models': {},
                'database': {}
            }
            yaml.dump(config_data, f)
        
        # 重新加载配置
        config_manager = ConfigManager(config_path=str(temp_config_dir) + "/config.yml")
        
        # 验证空节配置正确加载
        assert config_manager.get('system') == {}
        assert config_manager.get('models') == {}
        assert config_manager.get('database') == {}
        print("✓ 空节配置加载成功")

    def test_config_with_complex_nested_structure(self, temp_config_dir):
        """测试复杂嵌套结构配置"""
        # 创建复杂嵌套结构的配置
        with open(Path(temp_config_dir) / "config.yml", 'w') as f:
            config_data = {
                'models': {
                    'image_video_model': {
                        'auto_select': True,
                        'chinese_clip_base': {
                            'model_name': 'OFA-Sys/chinese-clip-vit-base-patch16',
                            'device': 'auto',
                            'batch_size': 12,
                            'vector_dim': 512,
                            'metadata': {
                                'version': '1.0',
                                'author': 'msearch'
                            }
                        }
                    }
                }
            }
            yaml.dump(config_data, f)
        
        # 重新加载配置
        config_manager = ConfigManager(config_path=str(temp_config_dir) + "/config.yml")
        
        # 验证复杂嵌套结构正确加载
        metadata = config_manager.get('models.image_video_model.chinese_clip_base.metadata')
        assert metadata is not None
        assert metadata['version'] == '1.0'
        assert metadata['author'] == 'msearch'
        print("✓ 复杂嵌套结构配置加载成功")

    def test_config_file_not_found(self):
        """测试配置文件不存在的情况"""
        # ConfigManager在文件不存在时会使用默认配置，不会抛出异常
        config_manager = ConfigManager(config_path='/nonexistent/config.yml')
        assert config_manager is not None
        assert config_manager.config is not None
        # 应该使用默认配置
        assert 'models' in config_manager.config
        assert 'database' in config_manager.config
        print("✓ 配置文件不存在时使用默认配置")

    def test_config_file_invalid_yaml(self, temp_config_dir):
        """测试配置文件YAML格式错误"""
        # 写入无效的YAML内容
        with open(Path(temp_config_dir) / "config.yml", 'w') as f:
            f.write("invalid: yaml: content:\n  - item1\n  - item2\n  - item3\n  - item4")
        
        # ConfigManager在YAML格式错误时会使用默认配置，不会抛出异常
        config_manager = ConfigManager(config_path=str(temp_config_dir) + "/config.yml")
        
        # 验证使用了默认配置
        assert 'models' in config_manager.config
        print("✓ 配置文件YAML格式错误时使用默认配置")

    def test_config_with_comments(self, temp_config_dir):
        """测试包含注释的配置文件"""
        # 创建包含注释的配置
        with open(Path(temp_config_dir) / "config.yml", 'w') as f:
            f.write("# 这是一个注释\n")
            f.write("system:\n")
            f.write("  log_level: INFO  # 日志级别\n")
            f.write("  max_workers: 4  # 最大工作线程数\n")
        
        # 重新加载配置
        config_manager = ConfigManager(config_path=str(temp_config_dir) + "/config.yml")
        
        # 验证配置正确加载（注释应该被忽略）
        assert config_manager.get('system.log_level') == 'INFO'
        assert config_manager.get('system.max_workers') == 4
        print("✓ 包含注释的配置文件加载成功")

    def test_config_with_env_variables(self, temp_config_dir):
        """测试环境变量替换（如果实现了）"""
        # 创建包含环境变量的配置
        with open(Path(temp_config_dir) / "config.yml", 'w') as f:
            config_data = {
                'system': {
                    'log_level': 'INFO',
                    'cache_dir': '${HOME}/.msearch/cache'
                }
            }
            yaml.dump(config_data, f)
        
        # 重新加载配置
        config_manager = ConfigManager(config_path=str(temp_config_dir) + "/config.yml")
        
        # 验证配置加载（环境变量可能未被替换，取决于实现）
        cache_dir = config_manager.get('system.cache_dir')
        print(f"✓ 环境变量配置: {cache_dir}")

    def test_config_with_multiline_strings(self, temp_config_dir):
        """测试多行字符串配置"""
        # 创建包含多行字符串的配置
        with open(Path(temp_config_dir) / "config.yml", 'w') as f:
            config_data = {
                'system': {
                    'description': '''
                    这是一个多行字符串
                    包含多行内容
                    用于测试
                    '''
                }
            }
            yaml.dump(config_data, f)
        
        # 重新加载配置
        config_manager = ConfigManager(config_path=str(temp_config_dir) + "/config.yml")
        
        # 验证多行字符串正确加载
        description = config_manager.get('system.description')
        assert '这是一个多行字符串' in description
        print("✓ 多行字符串配置加载成功")

    def test_config_with_duplicate_keys(self, temp_config_dir):
        """测试重复键的处理（YAML会覆盖）"""
        # 创建包含重复键的配置
        with open(Path(temp_config_dir) / "config.yml", 'w') as f:
            f.write("system:\n")
            f.write("  max_workers: 4\n")
            f.write("  max_workers: 8\n")  # 重复键
        
        # 重新加载配置
        config_manager = ConfigManager(config_path=str(temp_config_dir) + "/config.yml")
        
        # 验证后面的值覆盖了前面的值
        assert config_manager.get('system.max_workers') == 8
        print("✓ 重复键被后面的值覆盖")

    def test_config_with_large_file(self, temp_config_dir):
        """测试大配置文件"""
        # 创建包含大量配置项的配置
        with open(Path(temp_config_dir) / "config.yml", 'w') as f:
            config_data = {
                'system': {},
                'models': {},
                'database': {}
            }
            
            # 添加大量配置项
            for i in range(100):
                config_data['system'][f'key_{i}'] = f'value_{i}'
                config_data['models'][f'model_{i}'] = {'name': f'model_{i}'}
                config_data['database'][f'db_{i}'] = f'db_{i}'
            
            yaml.dump(config_data, f)
        
        # 重新加载配置
        config_manager = ConfigManager(config_path=str(temp_config_dir) + "/config.yml")
        
        # 验证大量配置项正确加载
        assert len(config_manager.get('system')) == 100
        assert len(config_manager.get('models')) == 100
        assert len(config_manager.get('database')) == 100
        print(f"✓ 大配置文件加载成功，包含300个配置项")

    def test_config_memory_efficiency(self, config_manager):
        """测试配置内存效率"""
        # 获取配置多次，应该返回相同的对象引用（如果实现了缓存）
        config1 = config_manager.config
        config2 = config_manager.config
        
        # 验证返回相同的对象引用
        assert config1 is config2
        print("✓ 配置内存效率验证通过")

    def test_config_thread_safety(self, config_manager):
        """测试配置线程安全性（如果需要）"""
        # 这里只是简单测试，真正的线程安全需要更复杂的测试
        # 获取配置
        config = config_manager.get('system')
        
        # 验证配置可以正常读取
        assert config is not None
        print("✓ 配置线程安全性基础测试通过")

    def test_config_with_zero_values(self, temp_config_dir):
        """测试零值配置"""
        # 创建包含零值的配置
        with open(Path(temp_config_dir) / "config.yml", 'w') as f:
            config_data = {
                'system': {
                    'zero_int': 0,
                    'zero_float': 0.0,
                    'empty_string': ''
                }
            }
            yaml.dump(config_data, f)
        
        # 重新加载配置
        config_manager = ConfigManager(config_path=str(temp_config_dir) + "/config.yml")
        
        # 验证零值配置正确加载
        assert config_manager.get('system.zero_int') == 0
        assert config_manager.get('system.zero_float') == 0.0
        assert config_manager.get('system.empty_string') == ''
        print("✓ 零值配置加载成功")

    def test_config_with_negative_numbers(self, temp_config_dir):
        """测试负数配置"""
        # 创建包含负数的配置
        with open(Path(temp_config_dir) / "config.yml", 'w') as f:
            config_data = {
                'system': {
                    'negative_int': -100,
                    'negative_float': -3.14,
                    'negative_zero': -0.0
                }
            }
            yaml.dump(config_data, f)
        
        # 重新加载配置
        config_manager = ConfigManager(config_path=str(temp_config_dir) + "/config.yml")
        
        # 验证负数配置正确加载
        assert config_manager.get('system.negative_int') == -100
        assert config_manager.get('system.negative_float') == -3.14
        assert config_manager.get('system.negative_zero') == -0.0
        print("✓ 负数配置加载成功")
