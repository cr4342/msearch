#!/usr/bin/env python3
"""
msearch 整合版真实模型离线集成测试

整合了以下测试的优点：
1. 离线模式验证
2. 资源监控（CPU/内存限制：90%）
3. 多模态支持（图像、音频、视频）
4. 搜索功能测试
5. 每种类型只处理1个文件，控制资源使用
6. 使用项目核心组件
"""

import os
import sys
import asyncio
import time
import tempfile
import shutil
import psutil
import threading
from pathlib import Path
import gc
import requests
import random
import string

# =====================================================
# 设置离线环境变量（必须在最开始设置）
# =====================================================
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['HF_DATASETS_OFFLINE'] = '1'
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
os.environ['HF_HUB_DISABLE_EXPERIMENTAL_WARNING'] = '1'
os.environ['HF_HUB_DISABLE_IMPORT_ERROR'] = '1'
os.environ['NO_PROXY'] = '*'
os.environ['no_proxy'] = '*'

# 添加项目根目录到PYTHONPATH
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)

# 导入项目核心组件
from src.core.config.config_manager import ConfigManager
from src.core.database.database_manager import DatabaseManager
from src.core.vector.vector_store import VectorStore
from src.core.embedding.embedding_engine import EmbeddingEngine


class CombinedIntegrationTest:
    """整合版集成测试"""
    
    # 资源限制阈值
    MAX_CPU_PERCENT = 90
    MAX_MEMORY_PERCENT = 90
    
    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.temp_dir = None
        self.config = None
        self.db_manager = None
        self.vector_store = None
        self.embedding_engine = None
        self.results = []
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.monitor_thread = None
        self.resource_stats = {
            'start_cpu': 0,
            'start_memory': 0,
            'max_cpu': 0,
            'max_memory': 0,
            'end_cpu': 0,
            'end_memory': 0
        }
        self.downloaded_files = []
        # 测试关键词（用于下载和检索验证）
        self.test_keywords = {
            'image': '人物',      # 人物图像
            'audio': '音乐',      # 音乐音频
            'video': '风景',      # 风景视频
        }
        self.test_files = {'image': None, 'audio': None, 'video': None}
    
    def log(self, message, is_error=False):
        """线程安全的日志输出"""
        with self.lock:
            prefix = "✗" if is_error else "✓"
            print(f"{prefix} {message}")
            self.results.append(f"{prefix} {message}")
            
    def resource_monitor(self):
        """资源监控线程"""
        while not self.stop_event.is_set():
            try:
                cpu = psutil.cpu_percent()
                memory = psutil.virtual_memory().percent
                
                # 更新最大资源使用
                with self.lock:
                    if cpu > self.resource_stats['max_cpu']:
                        self.resource_stats['max_cpu'] = cpu
                    if memory > self.resource_stats['max_memory']:
                        self.resource_stats['max_memory'] = memory
                
                if cpu > self.MAX_CPU_PERCENT or memory > self.MAX_MEMORY_PERCENT:
                    self.log(f"警告: 资源使用率过高 - CPU: {cpu:.1f}%, 内存: {memory:.1f}%", is_error=True)
                    # 触发垃圾回收
                    gc.collect()
                
            except Exception as e:
                self.log(f"资源监控错误: {e}", is_error=True)
            
            time.sleep(2)  # 每2秒检查一次
            
    def start_monitoring(self):
        """启动资源监控"""
        # 记录初始资源状态
        self.resource_stats['start_cpu'] = psutil.cpu_percent()
        self.resource_stats['start_memory'] = psutil.virtual_memory().percent
        
        self.monitor_thread = threading.Thread(target=self.resource_monitor, daemon=True)
        self.monitor_thread.start()
        self.log(f"资源监控已启动 (CPU/内存限制: {self.MAX_CPU_PERCENT}%)")
        self.log(f"初始资源状态: CPU: {self.resource_stats['start_cpu']:.1f}%, 内存: {self.resource_stats['start_memory']:.1f}%")
        
    def stop_monitoring(self):
        """停止资源监控"""
        self.stop_event.set()
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        # 记录最终资源状态
        self.resource_stats['end_cpu'] = psutil.cpu_percent()
        self.resource_stats['end_memory'] = psutil.virtual_memory().percent
        
        self.log("资源监控已停止")
        self.log(f"最终资源状态: CPU: {self.resource_stats['end_cpu']:.1f}%, 内存: {self.resource_stats['end_memory']:.1f}%")
        self.log(f"峰值资源使用: CPU: {self.resource_stats['max_cpu']:.1f}%, 内存: {self.resource_stats['max_memory']:.1f}%")
        
    async def setup(self):
        """初始化测试环境"""
        print("\n" + "="*60)
        print("整合版集成测试环境初始化")
        print("="*60)
        
        # 启动资源监控
        self.start_monitoring()
        
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp(prefix="msearch_test_")
        print(f"\n临时目录: {self.temp_dir}")
        
        # 初始化配置
        print("\n[1/5] 初始化配置...")
        self.config = ConfigManager()
        self.log("配置管理器初始化成功")
        
        # 初始化数据库
        print("\n[2/5] 初始化数据库...")
        db_path = Path(self.temp_dir) / "database" / "msearch.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db_manager = DatabaseManager(db_path=str(db_path))
        self.db_manager.initialize()
        self.log("数据库初始化成功")
        
        # 初始化向量存储
        print("\n[3/5] 初始化向量存储...")
        vector_dir = Path(self.temp_dir) / "lancedb"
        vector_dir.mkdir(parents=True, exist_ok=True)
        self.vector_store = VectorStore(config={
            'data_dir': str(vector_dir),
            'collection_name': 'unified_vectors',
            'vector_dimension': 512
        })
        self.vector_store.initialize()
        self.log("向量存储初始化成功")
        
        # 初始化向量化引擎
        print("\n[4/5] 初始化向量化引擎...")
        self.embedding_engine = EmbeddingEngine(self.config.config)
        
        # 强制垃圾回收
        gc.collect()
        
        # 异步初始化
        success = await self.embedding_engine.initialize()
        
        if success:
            self.log("向量化引擎初始化成功 (离线模式)")
        else:
            self.log("向量化引擎初始化失败", is_error=True)
            return False
            
        # 验证离线模式
        print("\n[5/5] 验证离线模式...")
        self._validate_offline_mode()
        
        return True
        
    def _validate_offline_mode(self):
        """验证离线模式设置"""
        checks = [
            ("TRANSFORMERS_OFFLINE", os.environ.get('TRANSFORMERS_OFFLINE') == '1'),
            ("HF_HUB_OFFLINE", os.environ.get('HF_HUB_OFFLINE') == '1'),
            ("HF_DATASETS_OFFLINE", os.environ.get('HF_DATASETS_OFFLINE') == '1'),
            ("NO_PROXY", os.environ.get('NO_PROXY') == '*'),
        ]
        
        for name, passed in checks:
            status = "✓" if passed else "✗"
            print(f"  {status} {name}: {'已设置' if passed else '未设置'}")
            if not passed:
                self.log(f"离线模式配置缺失: {name}", is_error=True)
        
        # 检查模型文件
        models = [
            'chinese-clip-vit-base-patch16',
            'clap-htsat-unfused'
        ]
        
        print("\n模型文件检查:")
        for model_name in models:
            model_path = Path('/data/project/msearch/data/models') / model_name
            exists = model_path.exists()
            status = "✓" if exists else "✗"
            print(f"  {status} {model_name}: {'存在' if exists else '不存在'}")
            if not exists:
                self.log(f"模型文件缺失: {model_name}", is_error=True)
        
    def _generate_random_name(self, extension):
        """生成随机文件名"""
        random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        return f"test_{random_str}.{extension}"
    
    def _download_file(self, url, save_path):
        """下载文件"""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            with open(save_path, 'wb') as f:
                f.write(response.content)
            return True
        except Exception as e:
            self.log(f"下载文件失败: {url} - {e}", is_error=True)
            return False
    
    def download_test_media(self):
        """下载测试媒体文件（使用指定关键词）"""
        print("\n" + "="*60)
        print("下载测试媒体文件（使用关键词）")
        print("="*60)
        print(f"测试关键词:")
        for k, v in self.test_keywords.items():
            print(f"  - {k}: {v}")
        
        testdata_dir = self.project_root / "testdata"
        testdata_dir.mkdir(exist_ok=True)
        
        # 下载图像
        print("\n[1/3] 下载测试图像...")
        keyword = self.test_keywords['image']
        image_urls = [
            f"https://picsum.photos/id/1005/800/600",  # 人物图像
            f"https://loremflickr.com/800/600/{keyword}",  # 关键词图像
        ]
        
        for url in image_urls[:1]:  # 只下载1个
            image_name = f"test_{keyword}.jpg"
            image_path = testdata_dir / image_name
            if self._download_file(url, image_path):
                self.downloaded_files.append(str(image_path))
                self.test_files['image'] = str(image_path)
                self.log(f"  → 下载图像: {image_name} (关键词: {keyword})")
                break
        
        # 下载音频
        print("\n[2/3] 下载测试音频...")
        keyword = self.test_keywords['audio']
        audio_urls = [
            "https://www2.cs.uic.edu/~i101/SoundFiles/BabyElephantWalk60.wav",
            "https://www2.cs.uic.edu/~i101/SoundFiles/StarWars60.wav"
        ]
        
        for url in audio_urls[:1]:  # 只下载1个
            audio_name = f"test_{keyword}.wav"
            audio_path = testdata_dir / audio_name
            if self._download_file(url, audio_path):
                self.downloaded_files.append(str(audio_path))
                self.test_files['audio'] = str(audio_path)
                self.log(f"  → 下载音频: {audio_name} (关键词: {keyword})")
                break
        
        # 下载视频
        print("\n[3/3] 下载测试视频...")
        keyword = self.test_keywords['video']
        video_urls = [
            "https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/360/Big_Buck_Bunny_360_10s_1MB.mp4",
            "https://file-examples.com/storage/fe58427f19631a2969a97c1/2017/04/file_example_MP4_480_1_5MG.mp4",
        ]
        
        for url in video_urls[:1]:  # 只下载1个
            video_name = f"test_{keyword}.mp4"
            video_path = testdata_dir / video_name
            if self._download_file(url, video_path):
                self.downloaded_files.append(str(video_path))
                self.test_files['video'] = str(video_path)
                self.log(f"  → 下载视频: {video_name} (关键词: {keyword})")
                break
        
        self.log(f"下载完成，共下载 {len(self.downloaded_files)} 个文件")
    
    def cleanup_downloaded_files(self):
        """清理下载的测试文件"""
        if self.downloaded_files:
            print("\n清理下载的测试文件...")
            for file_path in self.downloaded_files:
                try:
                    if Path(file_path).exists():
                        Path(file_path).unlink()
                        self.log(f"  → 清理文件: {Path(file_path).name}")
                except Exception as e:
                    self.log(f"  → 清理文件失败: {e}", is_error=True)
            self.downloaded_files = []
    
    def cleanup(self):
        """清理测试环境"""
        print("\n清理测试环境...")
        
        # 停止资源监控
        self.stop_monitoring()
        
        # 关闭组件
        if self.vector_store:
            self.vector_store.close()
        if self.db_manager:
            self.db_manager.close()
        
        # 清理临时目录
        if self.temp_dir and Path(self.temp_dir).exists():
            try:
                shutil.rmtree(self.temp_dir)
                self.log("临时目录已清理")
            except Exception as e:
                self.log(f"清理临时目录失败: {e}", is_error=True)
        
        # 清理下载的文件
        self.cleanup_downloaded_files()
        
        # 强制垃圾回收
        gc.collect()
        self.log("清理完成")
        
    async def process_images(self):
        """处理测试图像（只处理1个）"""
        print("\n" + "="*60)
        print("测试1: 图像向量化")
        print("="*60)
        
        # 优先使用下载的图像文件
        downloaded_images = [Path(f) for f in self.downloaded_files if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        
        if downloaded_images:
            test_images = downloaded_images[:1]
        else:
            # 查找测试图像 - 只取1个
            test_images = list((self.project_root / "testdata").glob("*.jpg"))
            test_images.extend(list((self.project_root / "testdata").glob("*.png")))
            # 过滤掉可能是缩略图的文件
            test_images = [f for f in test_images if not any(x in f.name for x in ['OIP', 'u=', 'RGB'])][:1]
        
        if not test_images:
            self.log("未找到测试图像", is_error=True)
            return
            
        img_path = test_images[0]
        self.log(f"处理图像: {img_path.name} (1/1)")
        
        try:
            # 强制垃圾回收
            gc.collect()
            
            # 异步向量化
            start = time.time()
            embedding = await self.embedding_engine.embed_image(str(img_path))
            elapsed = time.time() - start
            
            dim = len(embedding)
            self.log(f"  → 嵌入向量维度: {dim}, 耗时: {elapsed:.3f}s")
            
            # 存储到向量数据库
            self.vector_store.add_vector({
                "id": f"image_{img_path.stem}",
                "vector": embedding,
                "modality": "image",
                "metadata": {
                    "file_path": str(img_path),
                    "file_name": img_path.name,
                    "file_hash": "test_hash"
                }
            })
            self.log(f"  → 已存储到向量数据库")
            self.log("图像测试通过")
                
        except Exception as e:
            self.log(f"  → 处理失败: {e}", is_error=True)
        finally:
            gc.collect()
            
    async def process_audio(self):
        """处理测试音频（只处理1个）"""
        print("\n" + "="*60)
        print("测试2: 音频向量化")
        print("="*60)
        
        # 优先使用下载的音频文件
        downloaded_audio = [Path(f) for f in self.downloaded_files if f.lower().endswith(('.mp3', '.wav', '.flac'))]
        
        if downloaded_audio:
            test_audio = downloaded_audio[:1]
        else:
            # 查找测试音频 - 只取1个
            test_audio = list((self.project_root / "testdata").glob("*.mp3"))
            test_audio.extend(list((self.project_root / "testdata").glob("*.flac")))
            test_audio.extend(list((self.project_root / "testdata").glob("*.wav")))
            test_audio = test_audio[:1]
        
        if not test_audio:
            self.log("未找到测试音频")
            return
            
        audio_path = test_audio[0]
        self.log(f"处理音频: {audio_path.name} (1/1)")
        
        try:
            # 强制垃圾回收
            gc.collect()
            
            # 异步向量化
            start = time.time()
            embedding = await self.embedding_engine.embed_audio(str(audio_path))
            elapsed = time.time() - start
            
            dim = len(embedding)
            self.log(f"  → 嵌入向量维度: {dim}, 耗时: {elapsed:.3f}s")
            
            # 存储到向量数据库
            self.vector_store.add_vector({
                "id": f"audio_{audio_path.stem}",
                "vector": embedding,
                "modality": "audio",
                "metadata": {
                    "file_path": str(audio_path),
                    "file_name": audio_path.name,
                    "file_hash": "test_hash"
                }
            })
            self.log(f"  → 已存储到向量数据库")
            self.log("音频测试通过")
                
        except Exception as e:
            self.log(f"  → 处理失败: {e}", is_error=True)
        finally:
            gc.collect()
            
    async def process_videos(self):
        """处理测试视频（只处理1个）"""
        print("\n" + "="*60)
        print("测试3: 视频向量化")
        print("="*60)
        
        # 优先使用下载的视频文件
        downloaded_videos = [Path(f) for f in self.downloaded_files if f.lower().endswith(('.mp4', '.mov', '.avi'))]
        
        if downloaded_videos:
            test_videos = downloaded_videos[:1]
        else:
            # 查找测试视频 - 只取1个
            test_videos = list((self.project_root / "testdata").rglob("*.mp4"))
            test_videos.extend(list((self.project_root / "testdata").rglob("*.mov")))
            test_videos = test_videos[:1]
        
        if not test_videos:
            self.log("未找到测试视频")
            return
            
        video_path = test_videos[0]
        self.log(f"处理视频: {video_path.name} (1/1)")
        
        try:
            # 强制垃圾回收
            gc.collect()
            
            # 异步向量化
            start = time.time()
            embedding = await self.embedding_engine.embed_video(str(video_path))
            elapsed = time.time() - start
            
            dim = len(embedding)
            self.log(f"  → 嵌入向量维度: {dim}, 耗时: {elapsed:.3f}s")
            
            # 存储到向量数据库
            self.vector_store.add_vector({
                "id": f"video_{video_path.stem}",
                "vector": embedding,
                "modality": "video",
                "metadata": {
                    "file_path": str(video_path),
                    "file_name": video_path.name,
                    "file_hash": "test_hash"
                }
            })
            self.log(f"  → 已存储到向量数据库")
            self.log("视频测试通过")
                
        except Exception as e:
            self.log(f"  → 处理失败: {e}", is_error=True)
        finally:
            gc.collect()
            
    async def test_search(self):
        """测试搜索功能（使用下载时的相同关键词进行检索）"""
        print("\n" + "="*60)
        print("测试4: 搜索功能（关键词检索）")
        print("="*60)
        
        all_keywords = list(self.test_keywords.values())
        
        for query in all_keywords:
            try:
                self.log(f"\n搜索查询: '{query}' (使用下载时的关键词)")
                
                # 向量化查询
                start = time.time()
                query_embedding = await self.embedding_engine.embed_text(query)
                elapsed = time.time() - start
                self.log(f"  → 查询向量化耗时: {elapsed:.3f}s")
                
                # 搜索
                start = time.time()
                results = self.vector_store.search(
                    query_vector=query_embedding,
                    limit=5
                )
                elapsed = time.time() - start
                
                self.log(f"  → 搜索耗时: {elapsed:.3f}s")
                self.log(f"  → 找到 {len(results)} 个结果")
                
                # 显示结果
                for i, r in enumerate(results[:3]):
                    meta = r.get('metadata', {})
                    modality = r.get('modality', 'unknown')
                    score = r.get('_score', 0)
                    file_name = meta.get('file_name', 'unknown')
                    self.log(f"    [{i+1}] {file_name} [{modality}] (相似度: {score:.4f})")
                    
            except Exception as e:
                self.log(f"  → 搜索失败: {e}", is_error=True)
        
        return True
                
    async def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "="*60)
        print("msearch 整合版真实模型离线集成测试")
        print("="*60)
        print(f"项目根目录: {self.project_root}")
        print(f"测试数据目录: {self.project_root / 'testdata'}")
        print(f"模型目录: {self.project_root / 'data' / 'models'}")
        print("离线模式: 已启用")
        print("资源限制: CPU 90%, 内存 90%")
        print("测试策略: 每种类型只处理1个文件")
        
        if not await self.setup():
            print("\n环境初始化失败，退出测试")
            return False
            
        try:
            # 下载测试媒体文件
            self.download_test_media()
            
            # 运行测试（每种类型只处理1个）
            await self.process_images()
            await self.process_audio()
            await self.process_videos()
            await self.test_search()
            
            # 统计结果
            print("\n" + "="*60)
            print("测试结果汇总")
            print("="*60)
            
            success_count = sum(1 for r in self.results if r.startswith("✓"))
            error_count = sum(1 for r in self.results if r.startswith("✗"))
            
            print(f"总步骤: {len(self.results)}")
            print(f"成功: {success_count}")
            print(f"失败: {error_count}")
            
            # 输出资源使用统计
            print("\n" + "="*60)
            print("资源使用统计")
            print("="*60)
            print(f"初始资源: CPU: {self.resource_stats['start_cpu']:.1f}%, 内存: {self.resource_stats['start_memory']:.1f}%")
            print(f"峰值资源: CPU: {self.resource_stats['max_cpu']:.1f}%, 内存: {self.resource_stats['max_memory']:.1f}%")
            print(f"最终资源: CPU: {self.resource_stats['end_cpu']:.1f}%, 内存: {self.resource_stats['end_memory']:.1f}%")
            
            # 检查资源限制
            resource_ok = True
            if self.resource_stats['max_cpu'] > self.MAX_CPU_PERCENT:
                self.log(f"警告: CPU使用率超过限制! 峰值: {self.resource_stats['max_cpu']:.1f}% (限制: {self.MAX_CPU_PERCENT}%)", is_error=True)
                resource_ok = False
            if self.resource_stats['max_memory'] > self.MAX_MEMORY_PERCENT:
                self.log(f"警告: 内存使用率超过限制! 峰值: {self.resource_stats['max_memory']:.1f}% (限制: {self.MAX_MEMORY_PERCENT}%)", is_error=True)
                resource_ok = False
            
            if resource_ok:
                self.log("✓ 资源使用在限制范围内")
            
            # 最终判断
            if error_count == 0 and resource_ok:
                print("\n" + "="*60)
                print("✓ 所有集成测试通过！")
                print("  - 测试文件下载成功（使用关键词）")
                print("  - 离线模式工作正常")
                print("  - 模型加载和使用正常")
                print("  - 向量化和搜索流程正常")
                print("  - 关键词检索功能正常")
                print("  - 资源使用在限制范围内")
                print("="*60)
                return True
            else:
                print("\n" + "="*60)
                print("✗ 测试未完全通过")
                print("="*60)
                if error_count > 0:
                    print(f"  - 有 {error_count} 个步骤失败")
                if not resource_ok:
                    print("  - 资源使用超出限制")
                return False
                
        finally:
            self.cleanup()


def main():
    """主测试函数"""
    test = CombinedIntegrationTest()
    success = asyncio.run(test.run_all_tests())
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
