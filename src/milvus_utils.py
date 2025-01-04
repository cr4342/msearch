# milvus_utils.py
from pymilvus import connections, FieldSchema, CollectionSchema, DataType, Collection, IndexType, MetricType
import configparser

# 读取配置文件
config = configparser.ConfigParser()
config.read('config/config.ini')

def connect_milvus():
    """连接 Milvus 服务器"""
    try:
        host = config.get('Milvus', 'host')
        port = config.get('Milvus', 'port')
        connections.connect(host=host, port=port)
    except Exception as e:
        raise RuntimeError(f"连接 Milvus 服务器失败: {e}")
def create_collection(collection_name, dim):
    """创建 Milvus 集合"""
    if not isinstance(collection_name, str) or not isinstance(dim, int):
        raise ValueError("collection_name 必须是字符串，dim 必须是整数")

    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=False),
        FieldSchema(name="name", dtype=DataType.VARCHAR, max_length=256),
        FieldSchema(name="file_path", dtype=DataType.VARCHAR, max_length=512),
        FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=dim)
    ]
    try:
        schema = CollectionSchema(fields, "Milvus collection for storing image vectors")
        collection = Collection(name=collection_name, schema=schema)
        # 仅在集合创建时创建索引，避免重复创建
        collection.create_index(field_name="vector", index_params={"index_type": IndexType.IVF_FLAT, "metric_type": MetricType.L2})
        return collection
    except Exception as e:
        raise RuntimeError(f"创建集合失败: {e}")

def insert_vectors(collection_name, ids, file_paths, names, vectors, timestamps=None):
    """插入向量到 Milvus 集合"""
    try:
        collection = Collection(collection_name)
        # 确保输入数据的长度一致
        if not (len(ids) == len(file_paths) == len(names) == len(vectors)):
            raise ValueError("输入数据的长度不一致")

        entities = [
            ids,
            names,
            file_paths,
            vectors,
            timestamps if timestamps else [None] * len(ids)  # 处理时间戳为空的情况
        ]
        collection.insert(entities)
        # 插入数据后加载集合，避免重复加载
        collection.load()
    except Exception as e:
        raise RuntimeError(f"插入向量失败: {e}")

def close_milvus():
    """关闭 Milvus 连接"""
    try:
        connections.disconnect()
    except Exception as e:
        raise RuntimeError(f"关闭连接失败: {e}")
