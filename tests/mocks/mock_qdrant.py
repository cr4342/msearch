
import sys
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建基本的模拟类
class MockQdrantClient:
    def __init__(self, *args, **kwargs):
        logger.info("使用模拟的Qdrant客户端，跳过实际连接")
    
    def __getattr__(self, name):
        def mock_method(*args, **kwargs):
            logger.info(f"调用模拟方法: {name} with args={args}, kwargs={kwargs}")
            return None
        return mock_method

# 替换实际模块
sys.modules['qdrant_client'] = type('module', (), {'QdrantClient': MockQdrantClient})
sys.modules['qdrant_client.QdrantClient'] = MockQdrantClient
logger.info("Qdrant客户端已被模拟，测试可以在无实际服务的情况下运行")
