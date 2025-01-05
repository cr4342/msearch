import configparser
from milvus_utils import connect_milvus, Collection
from vector import vector_text, vector_image
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 读取配置文件
try:
    config = configparser.ConfigParser()
    config.read('config/config.ini')
except FileNotFoundError:
    logging.error("Config file not found.")
    raise
except configparser.Error as e:
    logging.error(f"Error reading config file: {e}")
    raise

# 连接 Milvus
def init_milvus():
    try:
        connect_milvus()
    except Exception as e:
        logging.error(f"Failed to connect to Milvus: {e}")
        raise

init_milvus()

def get_top_k(default_key):
    try:
        return config.getint('General', default_key)
    except (configparser.NoOptionError, ValueError) as e:
        logging.warning(f"Failed to read top_k from config: {e}")
        return 10  # 默认值

def search_vectors(collection_name, query_vector, top_k=None, anns_field="vector_field"):
    """
    从 Milvus 中检索相似的向量。
    
    :param collection_name: Milvus 集合的名称
    :param query_vector: 查询向量
    :param top_k: 返回的最相似向量的数量
    :param anns_field: 向量字段名
    :return: 最相似的向量及其距离
    """
    try:
        if top_k is None:
            top_k = get_top_k('top_k')

        if top_k <= 0:
            raise ValueError("top_k must be a positive integer")

        # 获取集合
        collection = Collection(collection_name)

        # 设置搜索参数
        search_params = {
            "metric_type": "L2",
            "params": {"nprobe": 10}
        }

        # 执行搜索
        results = collection.search(
            data=[query_vector],
            anns_field=anns_field,
            param=search_params,
            limit=top_k
        )

        # 返回结果
        return results
    except Exception as e:
        logging.error(f"Error searching vectors in collection {collection_name}: {e}")
        return None

def search_with_query_vector(collection_name, query_vector, top_k=None, anns_field="vector_field"):
    """
    使用查询向量从 Milvus 中检索相似的向量。
    
    :param collection_name: Milvus 集合的名称
    :param query_vector: 查询向量
    :param top_k: 返回的最相似向量的数量
    :param anns_field: 向量字段名
    :return: 最相似的向量及其距离
    """
    if query_vector is None:
        return None
    return search_vectors(collection_name, query_vector, top_k, anns_field)

def search_text2img(text, top_k=None):
    """
    从 Milvus 中检索与文本相似的图片。
    
    :param text: 查询文本
    :param top_k: 返回的最相似向量的数量
    :return: 最相似的图片及其距离
    """
    try:
        query_vector = vector_text(text)
        return search_with_query_vector('image_collection', query_vector, top_k, "vector_field")
    except Exception as e:
        logging.error(f"Error searching text to image: {e}")
        return None

def search_text2video(collection_name, text, top_k=None):
    """
    从 Milvus 中检索与文本相似的视频。
    
    :param collection_name: Milvus 集合的名称
    :param text: 查询文本
    :param top_k: 返回的最相似向量的数量
    :return: 最相似的视频及其距离
    """
    try:
        query_vector = vector_text(text)
        return search_with_query_vector(collection_name:“video_collection”, query_vector, top_k, "vector_field")
    except Exception as e:
        logging.error(f"Error searching text to video: {e}")
        return None

def search_image2image(collection_name, image_path, file_name, top_k=None):
    """
    从 Milvus 中检索与图片相似的图片。
    
    :param collection_name: Milvus 集合的名称
    :param image_path: 图片路径
    :param file_name: 图片文件名
    :param top_k: 返回的最相似向量的数量
    :return: 最相似的图片及其距离
    """
    try:
        query_vector = vector_image(image_path, file_name)
        return search_with_query_vector('image_collection', query_vector, top_k, "vector_field")
    except Exception as e:
        logging.error(f"Error searching image to image: {e}")
        return None

def search_image2video(collection_name, image_path, file_name, top_k=None):
    """
    从 Milvus 中检索与图片相似的视频。
    
    :param collection_name: Milvus 集合的名称
    :param image_path: 图片路径
    :param file_name: 图片文件名
    :param top_k: 返回的最相似向量的数量
    :return: 最相似的视频及其距离
    """
    try:
        query_vector = vector_image(image_path, file_name)
        return search_with_query_vector('video_collection', query_vector, top_k, "vector_field")
    except Exception as e:
        logging.error(f"Error searching image to video: {e}")
        return None

def search_by_text(text, top_k=None):
    """
    从 Milvus 中检索与文本相似的图片和视频。
    
    :param text: 查询文本
    :param top_k: 返回的最相似向量的数量
    :return: 最相似的图片和视频及其距离
    """
    results = {
        "images": None,
        "videos": None
    }
    
    try:
        # 获取文本的查询向量
        query_vector = vector_text(text)

        # 检索图片
        results["images"] = search_with_query_vector('image_collection', query_vector, top_k, "vector_field")

        # 检索视频
        results["videos"] = search_with_query_vector('video_collection', query_vector, top_k, "vector_field")

        return results
    except Exception as e:
        logging.error(f"Error searching by text: {e}")
        return None

def search_by_image(image_path, file_name, top_k=None):
    """
    从 Milvus 中检索与图片相似的图片和视频。
    
    :param image_path: 图片路径
    :param file_name: 图片文件名
    :param top_k: 返回的最相似向量的数量
    :return: 最相似的图片和视频及其距离
    """
    results = {
        "images": None,
        "videos": None
    }
    
    try:
        # 获取图片的查询向量
        query_vector = vector_image(image_path, file_name)

        # 检索与图片相似的图片
        results["images"] = search_with_query_vector('image_collection', query_vector, top_k, "vector_field")

        # 检索与图片相似的视频
        results["videos"] = search_with_query_vector('video_collection', query_vector, top_k, "vector_field")

        return results
    except Exception as e:
        logging.error(f"Error searching by image: {e}")
        return None