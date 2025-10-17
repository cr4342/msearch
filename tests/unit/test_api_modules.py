"""
测试API模块的导入功能
"""
import unittest
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

class TestAPIModules(unittest.TestCase):
    """测试API相关模块"""

    def test_api_routes_imports(self):
        """测试API路由模块导入"""
        try:
            from src.api.routes import search
            from src.api.routes import config
            from src.api.routes import tasks
            from src.api.routes import status
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"API路由模块导入失败: {e}")

    def test_api_models_imports(self):
        """测试API数据模型模块导入"""
        try:
            from src.api.models import search_models
            from src.api.models import config_models
            from src.api.models import common_models
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"API数据模型模块导入失败: {e}")

    def test_api_middleware_imports(self):
        """测试API中间件模块导入"""
        try:
            from src.api.middleware import cors
            from src.api.middleware import error_handler
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"API中间件模块导入失败: {e}")

    def test_search_route_functions(self):
        """测试搜索路由功能"""
        from src.api.routes import search
        self.assertTrue(hasattr(search, 'router'))
        self.assertIsNotNone(search.router)

    def test_config_route_functions(self):
        """测试配置路由功能"""
        from src.api.routes import config
        self.assertTrue(hasattr(config, 'router'))
        self.assertIsNotNone(config.router)

    def test_data_models_structure(self):
        """测试数据模型结构"""
        from src.api.models import search_models, config_models, common_models

        # 测试SearchRequest模型
        self.assertTrue(hasattr(search_models, 'SearchRequest'))
        self.assertTrue(hasattr(search_models, 'SearchResult'))
        self.assertTrue(hasattr(search_models, 'SearchResponse'))

        # 测试Config模型
        self.assertTrue(hasattr(config_models, 'ConfigRequest'))
        self.assertTrue(hasattr(config_models, 'ConfigResponse'))

        # 测试通用模型
        self.assertTrue(hasattr(common_models, 'CommonResponse'))
        self.assertTrue(hasattr(common_models, 'ErrorResponse'))


if __name__ == '__main__':
    unittest.main()