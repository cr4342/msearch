#!/usr/bin/env python3
import sys
import asyncio
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.config.config_manager import ConfigManager
from src.core.embedding.embedding_engine import EmbeddingEngine
from src.core.vector.vector_store import VectorStore

def test_text_to_audio_embedding():
    print("=" * 60)
    print("测试1: 文本到音频的跨模态向量转换")
    print("=" * 60)

    config_manager = ConfigManager()
    config = config_manager.config
    embedding_engine = EmbeddingEngine(config)

    test_queries = ["舒缓的背景音乐", "激烈的摇滚乐", "古典钢琴曲"]

    for query in test_queries:
        try:
            print(f"\n测试查询: '{query}'")
            vector = embedding_engine.embed_audio(query, model_type="audio_model", is_text_query=True)
            print(f"  向量维度: {len(vector)}")
            print(f"  前5个值: {vector[:5]}")
        except Exception as e:
            print(f"  错误: {e}")

async def test_audio_search():
    print("\n" + "=" * 60)
    print("测试2: 使用文本搜索音频")
    print("=" * 60)

    config_manager = ConfigManager()
    config = config_manager.config
    embedding_engine = EmbeddingEngine(config)
    vector_store = VectorStore(config)

    test_query = "舒缓的背景音乐"
    print(f"\n查询: '{test_query}'")

    try:
        vector = await embedding_engine.embed_audio(test_query, model_type="audio_model", is_text_query=True)
        print(f"向量生成成功: 维度={len(vector)}")

        results = vector_store.search(vector, limit=10, filter={"modality": "audio"})
        print(f"搜索到 {len(results)} 个音频结果")
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("开始测试...\n")
    test_text_to_audio_embedding()
    asyncio.run(test_audio_search())
