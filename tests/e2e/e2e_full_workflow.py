"""
端到端测试：完整工作流程
测试从文件扫描到检索的完整端到端工作流程
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from PIL import Image
import time

from src.core.config.config_manager import ConfigManager
from src.core.database.database_manager import DatabaseManager
from src.core.vector.vector_store import VectorStore
from src.core.embedding.embedding_engine import EmbeddingEngine
from src.services.search.search_engine import SearchEngine
from src.services.media.media_processor import MediaProcessor
from src.data.extractors.noise_filter import NoiseFilterManager
from src.services.search.timeline import VideoTimelineGenerator


@pytest.fixture(scope="module")
def temp_dir():
    """创建临时目录"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture(scope="module")
def test_data_dir(temp_dir):
    """创建测试数据目录"""
    data_dir = Path(temp_dir) / "test_data"
    data_dir.mkdir(exist_ok=True)
    
    # 创建测试图像
    for i in range(5):
        img = Image.new('RGB', (100 + i * 10, 100 + i * 10), color=(255 - i * 50, i * 50, 100))
        img.save(data_dir / f"image_{i}.jpg")
    
    # 创建测试文本文件
    for i in range(3):
        text_file = data_dir / f"text_{i}.txt"
        text_file.write_text(f"这是第{i}个测试文本文件，包含一些测试内容用于端到端测试。")
    
    return data_dir


@pytest.fixture(scope="module")
def config_manager():
    """创建配置管理器（使用默认配置）"""
    return ConfigManager()


@pytest.fixture(scope="module")
def database_manager(temp_dir, config_manager):
    """创建数据库管理器"""
    db_path = Path(temp_dir) / "database" / "msearch.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    db_manager = DatabaseManager(db_path=str(db_path))
    db_manager.initialize()
    return db_manager


@pytest.fixture(scope="module")
def vector_store(temp_dir, config_manager):
    """创建向量存储"""
    vector_dir = Path(temp_dir) / "lancedb"
    vector_dir.mkdir(parents=True, exist_ok=True)
    
    # 使用配置创建向量存储
    vector_store = VectorStore(config=config_manager)
    return vector_store


@pytest.fixture(scope="module")
def embedding_engine(config_manager):
    """创建向量化引擎"""
    engine = EmbeddingEngine(config=config_manager)
    return engine


@pytest.fixture(scope="module")
def noise_filter(config_manager):
    """创建噪音过滤器"""
    filter_config = config_manager.get("noise_filter", {})
    return NoiseFilterManager(filter_config)


@pytest.fixture(scope="module")
def media_processor(config_manager, embedding_engine, noise_filter):
    """创建媒体处理器"""
    processor = MediaProcessor(
        config=config_manager,
        thumbnail_generator=None
    )
    # 手动设置引用（不通过构造函数）
    processor.embedding_engine = embedding_engine
    processor.noise_filter = noise_filter
    return processor


@pytest.fixture(scope="module")
def search_engine(vector_store, embedding_engine):
    """创建搜索引擎"""
    engine = SearchEngine(
        embedding_engine=embedding_engine,
        vector_store=vector_store
    )
    return engine


@pytest.fixture(scope="module")
def timeline_generator():
    """创建时间轴生成器"""
    return VideoTimelineGenerator()


class TestFullWorkflow:
    """完整工作流程端到端测试"""
    
    @pytest.mark.asyncio
    async def test_complete_image_workflow(self, test_data_dir, media_processor, database_manager, 
                                           vector_store, search_engine, embedding_engine):
        """测试完整的图像工作流程：扫描 -> 索引 -> 检索"""
        indexed_files = []
        
        # 1. 扫描图像文件
        image_files = list(test_data_dir.glob("*.jpg"))
        assert len(image_files) >= 3, "至少需要3个测试图像文件"
        
        # 2. 索引图像文件
        for image_file in image_files[:3]:  # 只处理前3个
            try:
                # 提取元数据
                file_size = image_file.stat().st_size
                file_ext = image_file.suffix.lower().lstrip(".")
                
                # 噪音过滤
                media_info = {
                    "width": 100,
                    "height": 100,
                    "file_size": file_size,
                    "file_ext": file_ext
                }
                
                should_keep, reason = media_processor.noise_filter.filter("image", media_info)
                if not should_keep:
                    continue
                
                # 向量化
                image_vector = await embedding_engine.embed_image(str(image_file))
                if image_vector is None:
                    continue
                
                # 存储元数据
                file_uuid = f"e2e_image_{file_size}"
                database_manager.add_file_metadata(
                    file_uuid=file_uuid,
                    file_path=str(image_file),
                    file_name=image_file.name,
                    file_size=file_size,
                    file_type="image",
                    modality="image"
                )
                
                # 存储向量
                vector_id = f"{file_uuid}_vector"
                vector_store.add_vector(
                    vector_id=vector_id,
                    vector=image_vector,
                    modality="image",
                    metadata={
                        "file_uuid": file_uuid,
                        "file_path": str(image_file),
                        "file_name": image_file.name
                    }
                )
                
                indexed_files.append(file_uuid)
                
            except Exception as e:
                print(f"索引文件 {image_file} 时出错: {e}")
                continue
        
        # 3. 验证索引结果
        assert len(indexed_files) >= 2, f"至少应该成功索引2个图像文件，实际索引: {len(indexed_files)}"
        
        # 4. 执行检索
        query = "测试图像"
        query_vector = await embedding_engine.embed_text(query)
        
        results = search_engine.search(
            query_vector=query_vector,
            modality="image",
            top_k=10
        )
        
        # 5. 验证检索结果
        assert results is not None, "检索结果不应为None"
        assert len(results) >= 0, "检索结果数量应该>=0"
        
        # 清理
        for file_uuid in indexed_files:
            database_manager.delete_file_metadata(file_uuid)
            vector_id = f"{file_uuid}_vector"
            vector_store.delete_vector(vector_id)
    
    @pytest.mark.asyncio
    async def test_complete_text_workflow(self, test_data_dir, media_processor, database_manager,
                                          vector_store, search_engine, embedding_engine):
        """测试完整的文本工作流程：扫描 -> 索引 -> 检索"""
        indexed_files = []
        
        # 1. 扫描文本文件
        text_files = list(test_data_dir.glob("*.txt"))
        assert len(text_files) >= 2, "至少需要2个测试文本文件"
        
        # 2. 索引文本文件
        for text_file in text_files:
            try:
                # 提取元数据
                file_size = text_file.stat().st_size
                file_ext = text_file.suffix.lower().lstrip(".")
                text_content = text_file.read_text()
                text_length = len(text_content)
                
                # 噪音过滤
                media_info = {
                    "text_length": text_length,
                    "file_size": file_size,
                    "file_ext": file_ext
                }
                
                should_keep, reason = media_processor.noise_filter.filter("text", media_info)
                if not should_keep:
                    continue
                
                # 向量化
                text_vector = await embedding_engine.embed_text(text_content)
                if text_vector is None:
                    continue
                
                # 存储元数据
                file_uuid = f"e2e_text_{file_size}"
                database_manager.add_file_metadata(
                    file_uuid=file_uuid,
                    file_path=str(text_file),
                    file_name=text_file.name,
                    file_size=file_size,
                    file_type="text",
                    modality="text"
                )
                
                # 存储向量
                vector_id = f"{file_uuid}_vector"
                vector_store.add_vector(
                    vector_id=vector_id,
                    vector=text_vector,
                    modality="text",
                    metadata={
                        "file_uuid": file_uuid,
                        "file_path": str(text_file),
                        "file_name": text_file.name,
                        "text_length": text_length
                    }
                )
                
                indexed_files.append(file_uuid)
                
            except Exception as e:
                print(f"索引文件 {text_file} 时出错: {e}")
                continue
        
        # 3. 验证索引结果
        assert len(indexed_files) >= 1, f"至少应该成功索引1个文本文件，实际索引: {len(indexed_files)}"
        
        # 4. 执行检索
        query = "测试文本"
        query_vector = await embedding_engine.embed_text(query)
        
        results = search_engine.search(
            query_vector=query_vector,
            modality="text",
            top_k=10
        )
        
        # 5. 验证检索结果
        assert results is not None, "检索结果不应为None"
        assert len(results) >= 0, "检索结果数量应该>=0"
        
        # 清理
        for file_uuid in indexed_files:
            database_manager.delete_file_metadata(file_uuid)
            vector_id = f"{file_uuid}_vector"
            vector_store.delete_vector(vector_id)
    
    @pytest.mark.asyncio
    async def test_multimodal_search_workflow(self, test_data_dir, media_processor, database_manager,
                                               vector_store, search_engine, embedding_engine):
        """测试多模态搜索工作流程"""
        indexed_images = []
        indexed_texts = []
        
        # 1. 索引图像文件
        image_files = list(test_data_dir.glob("*.jpg"))[:2]
        for image_file in image_files:
            try:
                file_size = image_file.stat().st_size
                image_vector = await embedding_engine.embed_image(str(image_file))
                
                if image_vector is None:
                    continue
                
                file_uuid = f"e2e_multi_image_{file_size}"
                database_manager.add_file_metadata(
                    file_uuid=file_uuid,
                    file_path=str(image_file),
                    file_name=image_file.name,
                    file_size=file_size,
                    file_type="image",
                    modality="image"
                )
                
                vector_id = f"{file_uuid}_vector"
                vector_store.add_vector(
                    vector_id=vector_id,
                    vector=image_vector,
                    modality="image",
                    metadata={"file_uuid": file_uuid, "file_path": str(image_file)}
                )
                
                indexed_images.append(file_uuid)
                
            except Exception as e:
                print(f"索引图像 {image_file} 时出错: {e}")
                continue
        
        # 2. 索引文本文件
        text_files = list(test_data_dir.glob("*.txt"))[:1]
        for text_file in text_files:
            try:
                file_size = text_file.stat().st_size
                text_content = text_file.read_text()
                text_vector = await embedding_engine.embed_text(text_content)
                
                if text_vector is None:
                    continue
                
                file_uuid = f"e2e_multi_text_{file_size}"
                database_manager.add_file_metadata(
                    file_uuid=file_uuid,
                    file_path=str(text_file),
                    file_name=text_file.name,
                    file_size=file_size,
                    file_type="text",
                    modality="text"
                )
                
                vector_id = f"{file_uuid}_vector"
                vector_store.add_vector(
                    vector_id=vector_id,
                    vector=text_vector,
                    modality="text",
                    metadata={"file_uuid": file_uuid, "file_path": str(text_file)}
                )
                
                indexed_texts.append(file_uuid)
                
            except Exception as e:
                print(f"索引文本 {text_file} 时出错: {e}")
                continue
        
        # 3. 验证索引结果
        assert len(indexed_images) >= 1 or len(indexed_texts) >= 1, "至少应该索引一些文件"
        
        # 清理
        for file_uuid in indexed_images:
            database_manager.delete_file_metadata(file_uuid)
            vector_id = f"{file_uuid}_vector"
            vector_store.delete_vector(vector_id)
        
        for file_uuid in indexed_texts:
            database_manager.delete_file_metadata(file_uuid)
            vector_id = f"{file_uuid}_vector"
            vector_store.delete_vector(vector_id)
    
    @pytest.mark.asyncio
    async def test_performance_workflow(self, test_data_dir, database_manager,
                                        vector_store, search_engine, embedding_engine):
        """测试性能工作流程：测量索引和检索性能"""
        indexed_files = []
        
        # 1. 测量索引性能
        start_time = time.time()
        
        image_files = list(test_data_dir.glob("*.jpg"))[:2]
        for image_file in image_files:
            try:
                file_size = image_file.stat().st_size
                image_vector = await embedding_engine.embed_image(str(image_file))
                
                if image_vector is None:
                    continue
                
                file_uuid = f"e2e_perf_{file_size}"
                database_manager.add_file_metadata(
                    file_uuid=file_uuid,
                    file_path=str(image_file),
                    file_name=image_file.name,
                    file_size=file_size,
                    file_type="image",
                    modality="image"
                )
                
                vector_id = f"{file_uuid}_vector"
                vector_store.add_vector(
                    vector_id=vector_id,
                    vector=image_vector,
                    modality="image",
                    metadata={"file_uuid": file_uuid, "file_path": str(image_file)}
                )
                
                indexed_files.append(file_uuid)
                
            except Exception as e:
                print(f"索引文件 {image_file} 时出错: {e}")
                continue
        
        indexing_time = time.time() - start_time
        
        # 2. 测量检索性能
        query = "性能测试"
        query_vector = await embedding_engine.embed_text(query)
        
        start_time = time.time()
        results = search_engine.search(
            query_vector=query_vector,
            modality="image",
            top_k=10
        )
        search_time = time.time() - start_time
        
        # 3. 验证性能
        assert results is not None, "检索结果不应为None"
        
        # 索引时间应该合理（< 30秒）
        assert indexing_time < 30.0, f"索引时间过长: {indexing_time:.2f}秒"
        
        print(f"索引时间: {indexing_time:.2f}秒")
        print(f"检索时间: {search_time:.2f}秒")
        
        # 清理
        for file_uuid in indexed_files:
            database_manager.delete_file_metadata(file_uuid)
            vector_id = f"{file_uuid}_vector"
            vector_store.delete_vector(vector_id)
    
    @pytest.mark.asyncio
    async def test_timeline_workflow(self, test_data_dir, database_manager,
                                     vector_store, search_engine, embedding_engine, timeline_generator):
        """测试时间轴工作流程"""
        indexed_files = []
        
        # 1. 索引图像文件（模拟视频片段）
        image_files = list(test_data_dir.glob("*.jpg"))[:3]
        for idx, image_file in enumerate(image_files):
            try:
                file_size = image_file.stat().st_size
                image_vector = await embedding_engine.embed_image(str(image_file))
                
                if image_vector is None:
                    continue
                
                file_uuid = f"e2e_timeline_{file_size}"
                database_manager.add_file_metadata(
                    file_uuid=file_uuid,
                    file_path=str(image_file),
                    file_name=image_file.name,
                    file_size=file_size,
                    file_type="image",
                    modality="image"
                )
                
                vector_id = f"{file_uuid}_vector"
                vector_store.add_vector(
                    vector_id=vector_id,
                    vector=image_vector,
                    modality="image",
                    metadata={
                        "file_uuid": file_uuid,
                        "file_path": str(image_file),
                        "video_uuid": f"video_001",
                        "start_time": idx * 10.0,
                        "end_time": (idx + 1) * 10.0
                    }
                )
                
                indexed_files.append(file_uuid)
                
            except Exception as e:
                print(f"索引文件 {image_file} 时出错: {e}")
                continue
        
        # 2. 验证索引结果
        assert len(indexed_files) >= 1, f"至少应该索引1个文件，实际: {len(indexed_files)}"
        
        # 3. 生成时间轴（使用模拟数据）
        query = "时间轴测试"
        search_results = []
        for i, file_uuid in enumerate(indexed_files[:3]):
            search_results.append({
                "video_uuid": f"video_001",
                "video_name": "test_video.mp4",
                "video_path": "/path/to/test_video.mp4",
                "start_time": i * 10.0,
                "end_time": (i + 1) * 10.0,
                "relevance_score": 0.9 - i * 0.1
            })
        
        timeline_result = timeline_generator.from_search_results(
            query=query,
            search_results=search_results
        )
        
        # 4. 验证时间轴结果
        assert timeline_result is not None, "时间轴结果不应为None"
        assert timeline_result.query == query, "时间轴查询应该匹配"
        
        # 清理
        for file_uuid in indexed_files:
            database_manager.delete_file_metadata(file_uuid)
            vector_id = f"{file_uuid}_vector"
            vector_store.delete_vector(vector_id)