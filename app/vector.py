# vector.py
import cn_clip.clip as clip
import torch
from PIL import Image
from cn_clip.clip import load_from_name, available_models
from milvus_utils import connect_milvus, insert_vectors  # 导入封装好的 Milvus 操作
from app.ulity import *
import os
import logging
import threading
import queue
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


total_task_num = get_total_tasks()

#从任务数据库中读取任务，将不是本地的文件下载到本地tmp目录，返回队列
def get_unvectorized_tasks(vectorized=0):
    tasks_queue = {}
    tmp= confing.get('tmp_dir')
    task_ids = get_task_list(vectorized=0)
    for task_id in task_ids:
        task = get_task_by_id(task_id)
        if task.type == 'remote' :
            download_remote_file(task.file_path, tmp)
            file_tmp_path = os.path.join(tmp, os.path.basename(task.file_name))
            update_task(task_id, cache_path='file_tmp_path'，cache_complete='now()')
            tasks_queue.append(task.id, file_tmp_path，task.task_type)
        else:
            tasks_queue.append(task.id, task.file_path,task.task_type)
        return tasks_queue

def emding_task(tasks_queue):
    for id in range(len(tasks_queue)):
        task_id, file_path, task_type = tasks_queue.get()
        if task_type == '1':
            img = Image.open(file_path)
            img_emb = clip.encode_image(model, img)
            img_emb = img_emb.detach().numpy().tolist()
            insert_vectors(collection_name, [id], [file_path], [task_id], [img_emb])
        elif task_type == '2':
            img_list = convert_video2gif(file_path)
            img_embs = []
            for img in img_list:
                img_emb = clip.encode_image(model, img)
                img_emb = img_emb.detach().numpy().tolist()
                img_embs.append(img_emb)
            insert_vectors(collection_name, [id], [file_path], [task_id], img_embs)
        elif task_type == '0':
            text = file_path
            text_emb = clip.encode_text(model, text)
            text_emb = text_emb.detach().numpy().tolist()    
            insert_vectors(collection_name, [id], [file_path], [task_id], [text_emb])
        update_task(task_id, vectorized=1)

def main():
    # 连接 Milvus 数据库
    connect_milvus()
    # 加载 CLIP 模型
    model_name = config.get('clip', 'name')
    model, preprocess = load_from_name(model_name)
    # 读取未向量化的任务
    tasks_queue = get_unvectorized_tasks()
    # 向量化任务
    emding_task(tasks_queue)
    # 关闭 Milvus 数据库
    close_milvus()

if __name__ == '__main__':
        main()
