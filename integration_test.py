#!/usr/bin/env python3
"""
msearch 集成测试脚本
按照设计文档要求测试各功能模块
"""

import os
import sys
import asyncio
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
src_root = project_root / "src"
sys.path.insert(0, str(src_root))
sys.path.insert(0, str(project_root))

# 设置离线环境变量
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['HF_DATASETS_OFFLINE'] = '1'
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'

import lancedb
import numpy as np
from core.config.config_manager import ConfigManager
from core.vector.vector_store import VectorStore
from core.embedding.embedding_engine import EmbeddingEngine
from core.task.central_task_manager import CentralTaskManager
from services.media.media_processor import MediaProcessor


class IntegrationTest:
    """集成测试类"""
    
    def __init__(self):
        self.config = None
        self.config_manager = None
        self.vector_store = None
        self.embedding_engine = None
        self.task_manager = None
        self.media_processor = None
        self.test_results = []
        
    def log(self, message, success=True):
        """记录测试结果"""
        status = "✓" if success else "✗"
        print(f"{status} {message}")
        self.test_results.append((status, message))
        
    async def test_config_loading(self):
        """测试配置加载"""
        print("\n" + "="*60)
        print("测试1: 配置加载")
        print("="*60)
        
        try:
            self.config_manager = ConfigManager()
            self.config = self.config_manager.get_all()
            
            self.log(f"配置文件加载成功")
            self.log(f"  - 监控目录: {self.config.get('file_monitor', {}).get('watch_directories', [])}")
            self.log(f"  - 设备类型: {self.config.get('models', {}).get('device', 'cpu')}")
            self.log(f"  - 向量维度: {self.config.get('models', {}).get('image_video_model', {}).get('embedding_dim', 'N/A')}")
            
            return True
        except Exception as e:
            self.log(f"配置加载失败: {e}", success=False)
            return False
            
    async def test_vector_store(self):
        """测试向量存储"""
        print("\n" + "="*60)
        print("测试2: 向量存储")
        print("="*60)
        
        try:
            vector_db_path = self.config.get('database', {}).get('vector_db_path', 'data/database/lancedb')
            vector_store_config = {
                'data_dir': vector_db_path,
                'collection_name': 'unified_vectors',
                'index_type': 'ivf_pq',
                'num_partitions': 128,
                'vector_dimension': 512
            }
            
            self.vector_store = VectorStore(vector_store_config)
            self.vector_store.initialize()
            
            # 测试向量搜索
            query_vector = np.random.randn(512).astype(np.float32)
            results = self.vector_store.search(query_vector, limit=5)
            
            self.log(f"向量存储初始化成功")
            self.log(f"  - 数据库路径: {vector_db_path}")
            self.log(f"  - 搜索结果数: {len(results)}")
            
            return True
        except Exception as e:
            self.log(f"向量存储测试失败: {e}", success=False)
            return False
            
    async def test_embedding_engine(self):
        """测试向量化引擎"""
        print("\n" + "="*60)
        print("测试3: 向量化引擎")
        print("="*60)
        
        try:
            self.embedding_engine = EmbeddingEngine(self.config)
            await self.embedding_engine.initialize()
            
            self.log(f"向量化引擎初始化成功")
            self.log(f"  - 默认图像模型: {self.embedding_engine._default_image_model}")
            self.log(f"  - 默认文本模型: {self.embedding_engine._default_text_model}")
            self.log(f"  - 默认音频模型: {self.embedding_engine._default_audio_model}")
            
            return True
        except Exception as e:
            self.log(f"向量化引擎测试失败: {e}", success=False)
            return False
            
    async def test_task_manager(self):
        """测试任务管理器"""
        print("\n" + "="*60)
        print("测试4: 任务管理器")
        print("="*60)
        
        try:
            device = self.config.get('models', {}).get('device', 'cpu')
            self.task_manager = CentralTaskManager(self.config, device)
            
            if self.task_manager.initialize():
                stats = self.task_manager.get_statistics()
                
                self.log(f"任务管理器初始化成功")
                self.log(f"  - 队列大小: {stats.get('queue_size', 0)}")
                self.log(f"  - 运行中任务: {stats.get('running_count', 0)}")
                self.log(f"  - 资源状态: {stats.get('resource_state', 'unknown')}")
                
                return True
            else:
                self.log(f"任务管理器初始化失败", success=False)
                return False
        except Exception as e:
            self.log(f"任务管理器测试失败: {e}", success=False)
            return False
            
    async def test_media_processor(self):
        """测试媒体处理器"""
        print("\n" + "="*60)
        print("测试5: 媒体处理器")
        print("="*60)
        
        try:
            self.media_processor = MediaProcessor(self.config)
            
            self.log(f"媒体处理器初始化成功")
            
            return True
        except Exception as e:
            self.log(f"媒体处理器测试失败: {e}", success=False)
            return False
            
    async def test_text_search(self):
        """测试文本搜索"""
        print("\n" + "="*60)
        print("测试6: 文本搜索")
        print("="*60)
        
        try:
            # 使用文本查询进行搜索
            test_queries = ["人物", "风景", "建筑"]
            
            for query in test_queries:
                # 生成查询向量
                query_embedding = await self.embedding_engine.embed_text(query)
                
                # 执行搜索
                results = self.vector_store.search(query_embedding, limit=3)
                
                self.log(f"查询 '{query}': 找到 {len(results)} 个结果")
                
                # 显示前3个结果
                for i, result in enumerate(results[:3]):
                    file_path = result.get('file_path', 'N/A')
                    similarity = result.get('similarity', 0)
                    self.log(f"  {i+1}. {file_path} (相似度: {similarity:.4f})")
            
            return True
        except Exception as e:
            self.log(f"文本搜索测试失败: {e}", success=False)
            import traceback
            traceback.print_exc()
            return False
            
    async def test_image_search(self):
        """测试图像搜索"""
        print("\n" + "="*60)
        print("测试7: 图像搜索")
        print("="*60)
        
        try:
            # 查找测试图像
            testdata_dir = Path("testdata")
            image_files = list(testdata_dir.glob("*.jpg")) + list(testdata_dir.glob("*.png"))
            
            if not image_files:
                self.log(f"未找到测试图像", success=False)
                return False
            
            # 使用第一个图像进行搜索
            test_image = image_files[0]
            self.log(f"使用测试图像: {test_image}")
            
            # 生成图像向量
            query_embedding = await self.embedding_engine.embed_image(str(test_image))
            
            # 执行搜索
            results = self.vector_store.search(query_embedding, limit=3)
            
            self.log(f"图像搜索: 找到 {len(results)} 个结果")
            
            # 显示结果
            for i, result in enumerate(results[:3]):
                file_path = result.get('file_path', 'N/A')
                similarity = result.get('similarity', 0)
                self.log(f"  {i+1}. {file_path} (相似度: {similarity:.4f})")
            
            return True
        except Exception as e:
            self.log(f"图像搜索测试失败: {e}", success=False)
            import traceback
            traceback.print_exc()
            return False
            
    async def test_task_management(self):
        """测试任务管理功能"""
        print("\n" + "="*60)
        print("测试8: 任务管理")
        print("="*60)
        
        try:
            # 创建测试任务
            task_id = self.task_manager.create_task(
                task_type='test_task',
                task_data={'test': 'data'},
                priority=5
            )
            
            self.log(f"创建测试任务: {task_id}")
            
            # 获取任务列表
            tasks = self.task_manager.get_all_tasks()
            self.log(f"任务列表: {len(tasks)} 个任务")
            
            # 获取任务统计
            stats = self.task_manager.get_statistics()
            self.log(f"队列大小: {stats.get('queue_size', 0)}")
            self.log(f"运行中任务: {stats.get('running_count', 0)}")
            
            return True
        except Exception as e:
            self.log(f"任务管理测试失败: {e}", success=False)
            return False
            
    def cleanup(self):
        """清理资源"""
        print("\n" + "="*60)
        print("清理资源")
        print("="*60)
        
        try:
            if self.task_manager:
                self.task_manager.shutdown()
                self.log("任务管理器已关闭")
                
            if self.vector_store:
                self.vector_store.close()
                self.log("向量存储已关闭")
                
            self.log("资源清理完成")
        except Exception as e:
            self.log(f"资源清理失败: {e}", success=False)
            
    async def run_all_tests(self):
        """运行所有测试"""
        print("\n")
        print("╔" + "="*58 + "╗")
        print("║" + " "*15 + "msearch 集成测试" + " "*25 + "║")
        print("╚" + "="*58 + "╝")
        print()
        
        tests = [
            ("配置加载", self.test_config_loading),
            ("向量存储", self.test_vector_store),
            ("向量化引擎", self.test_embedding_engine),
            ("任务管理器", self.test_task_manager),
            ("媒体处理器", self.test_media_processor),
            ("文本搜索", self.test_text_search),
            ("图像搜索", self.test_image_search),
            ("任务管理", self.test_task_management),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            try:
                if await test_func():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                self.log(f"测试 {test_name} 异常: {e}", success=False)
                failed += 1
                
        # 清理资源
        self.cleanup()
        
        # 打印测试总结
        print("\n" + "="*60)
        print("测试总结")
        print("="*60)
        print(f"总测试数: {len(tests)}")
        print(f"通过: {passed}")
        print(f"失败: {failed}")
        print(f"通过率: {passed/len(tests)*100:.1f}%")
        
        if failed == 0:
            print("\n✓ 所有测试通过！")
        else:
            print(f"\n✗ {failed} 个测试失败")
            
        return failed == 0


async def main():
    """主函数"""
    test = IntegrationTest()
    success = await test.run_all_tests()
    return 0 if success else 1


if __name__ == '__main__':
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
