import cn_clip.clip as clip
import torch
from PIL import Image
from cn_clip.clip import load_from_name, available_models
from milvus_utils import connect_milvus, insert_vectors  
from app.ulity import download_file  
import os
import logging
import threading
import queue
import configparser
from app.task import TaskManager  


def read_config(config_path='config/config.ini'):
    config = configparser.ConfigParser()
    config.read(config_path)
    return config

config = read_config()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 从任务数据库中读取任务
def embedding_task(task_manager):
    max_memory = task_manager.config.get_max_memory()
    max_threads = task_manager.config.get_max_threads()
    threads = []

    while True:
        tasks = task_manager.get_unvectorized_tasks()
        if not tasks:
            break

        for task_id, file_path, task_type in tasks:
            if threading.active_count() >= max_threads:
                time.sleep(1)  # 等待线程空闲
                continue

            # 处理远程文件
            if task_type == 'remote':
                local_path = os.path.join('cache', os.path.basename(file_path))
                if not os.path.exists(local_path):
                    download_file(file_path, local_path)
                file_path = local_path

            task = EmbeddingTask((task_id, file_path, task_type))
            thread = threading.Thread(target=task.process)
            threads.append(thread)
            thread.start()

            # 模拟内存限制
            if sum(thread.is_alive() for thread in threads) * 100 > max_memory:
                time.sleep(1)  # 等待内存释放

        for thread in threads:
            thread.join()

        task_manager.mark_task_as_vectorized(task_id)

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
    task_manager = TaskManager()
    # 向量化任务
    embedding_task(task_manager)
    # 关闭 Milvus 数据库
    close_milvus()

if __name__ == '__main__':
    main()