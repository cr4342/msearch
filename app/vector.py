import cn_clip.clip as clip
import torch
from PIL import Image
from cn_clip.clip import load_from_name, available_models
from milvus_utils import connect_milvus, insert_vectors  # 导入封装好的 Milvus 操作
from app.ulity import *
import os
import logging
import configparser
from app.task import TaskManager  

# 读取配置文件
def read_config(config_path='config/config.ini'):
    config = configparser.ConfigParser()
    config.read(config_path)
    return config

config = read_config()

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 从任务数据库中读取任务，将不是本地的文件下载到本地cache目录，返回队列
def get_unvectorized_tasks(vectorized=0):
    tasks_queue = queue.Queue()
    cache = config.get('cache_dir', 'cache')
    task_ids = get_task_list(vectorized=vectorized)
    for task_id in task_ids:
        task = get_task_by_id(task_id)
        if task.type == 'remote':
            download_remote_file(task.file_path, cache)
            file_cache_path = os.path.join(cache, os.path.basename(task.file_name))
            update_task(task_id, cache_path=file_cache_path, cache_complete='now()')
            tasks_queue.put((task.id, file_cache_path, task.task_type))
        else:
            tasks_queue.put((task.id, task.file_path, task.task_type))
    return tasks_queue

def embedding_task(tasks_queue):
    while not tasks_queue.empty():
        task_id, file_path, task_type = tasks_queue.get()
        try:
            if task_type == '1':  # 图片
                probs = vector_image(file_path)
                insert_vectors(collection_name, [task_id], [file_path], [probs.tolist()])
            elif task_type == '2':  # 视频
                result = vector_video(file_path)
                frame_vectors = result['frame_vectors']
                for frame_no, frame_data in frame_vectors.items():
                    vector = frame_data['vector']
                    timestamp = frame_data['timestamp']
                    insert_vectors(collection_name, [task_id], [file_path], [vector.tolist()], [timestamp])
            elif task_type == '0':  # 文本
                text_features = vector_text(file_path)
                insert_vectors(collection_name, [task_id], [file_path], [text_features.tolist()])
            update_task(task_id, vectorized=1)
        except Exception as e:
            logging.error(f"Error processing task {task_id}: {e}")
            update_task(task_id, vectorized=-1, error_message=str(e))

def main():
    # 连接 Milvus 数据库
    connect_milvus()
    # 加载 CLIP 模型
    model_name = config.get('clip', 'name', fallback='ViT-B-16')
    device = "cuda" if torch.cuda.is_available() else "cpu"
    global model, preprocess
    model, preprocess = load_from_name(model_name, device=device, download_root='./')
    model.eval()
    # 读取未向量化的任务
    tasks_queue = get_unvectorized_tasks()
    # 向量化任务
    embedding_task(tasks_queue)
    # 关闭 Milvus 数据库
    close_milvus()

if __name__ == '__main__':
    main()