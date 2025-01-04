# vector.py
import cn_clip.clip as clip
import torch
from PIL import Image
from cn_clip.clip import load_from_name, available_models
from milvus_utils import connect_milvus, insert_vectors  # 导入封装好的 Milvus 操作
from src.ulity import pumping
import os
import logging
import threading
import queue
import configparser
from src.task import TaskManager  # 添加: 导入 TaskManager 类

# 读取配置文件
config = configparser.ConfigParser()
config.read('config/config.ini')

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

print("Available models:", available_models())
# Available models: ['ViT-B-16', 'ViT-L-14', 'ViT-L-14-336', 'ViT-H-14', 'RN50']

device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = load_from_name("ViT-B-16", device=device, download_root='./')

def vector_text(text):
    """将文本转换为向量"""
    try:
        text = clip.tokenize([text]).to(device)
        with torch.no_grad():
            text_features = model.encode_text(text)
        return text_features
    except Exception as e:
        logging.error(f"Error encoding text: {e}")
        return None

def combine_vectors(image_features, text_features):
    """统一文件名向量和文件向量的比例"""
    try:
        text_features /= text_features.norm(dim=-1, keepdim=True)
        logits_per_image, _ = model.get_similarity(image_features, text_features)
        probs = logits_per_image.softmax(dim=-1).cpu().numpy()
        return probs
    except Exception as e:
        logging.error(f"Error combining vectors: {e}")
        return None

def vector_image(path, file_name):
    """处理单张图片并返回其向量特征"""
    try:
        image = preprocess(Image.open(path)).unsqueeze(0).to(device)
        text = clip.tokenize([file_name]).to(device)

        with torch.no_grad():
            image_features = model.encode_image(image)
            image_features /= image_features.norm(dim=-1, keepdim=True)
            probs = combine_vectors(image_features, text)

        return probs
    except Exception as e:
        logging.error(f"Error processing image {path}: {e}")
        return None

# 创建一个队列来存储任务
task_queue = queue.Queue()

# 定义一个线程函数来处理任务
def process_task_thread(collection_name, vector_func, task_type):
    while True:
        task_id = task_queue.get()
        if task_id is None:
            break
        try:
            task_info = task.get_task_by_id(task_id)
            if not task_info:
                continue

            file_name = task_info['file_name']
            source = task_info['source']  # 获取任务的来源
            id = task_info['id']

            file_path = task_info['file_path'] if source == 'local' else task_info['cache_path']
            if source not in ['local', 'remote']:
                continue  # 跳过未知来源的任务

            vector_result = vector_func(file_path, file_name)
            if vector_result is not None:
                if task_type == '1':  # 图片任务
                    insert_vectors(collection_name, id, file_name, [vector_result], file_path)
                elif task_type == '2':  # 视频任务
                    insert_vectors(collection_name, vector_result['filename'], vector_result['filepath'], vector_result['vectors'], vector_result['timestamps'])

                task.update_task(task_id, 'vectorized', 1)

                # 如果是远程任务，删除缓存文件
                if source == 'remote':
                    os.remove(file_path)
        except Exception as e:
            logging.error(f"Error processing task {task_id}: {e}")
        finally:
            task_queue.task_done()

# 创建多个线程来处理任务
num_threads = config.getint('General', 'num_threads')
threads = []
for i in range(num_threads):
    thread = threading.Thread(target=process_task_thread, args=(collection_name, vector_func))
    thread.start()
    threads.append(thread)

def process_task(task_type, collection_name, vector_func):
    """通用任务处理函数，用于处理图片或视频任务"""
    task_ids = task.get_task_ids(task_type=task_type, vectorized=0)
    for task_id in task_ids:
        task_queue.put(task_id)

    # 等待所有任务完成
    task_queue.join()

    # 停止工作线程
    for i in range(num_threads):
        task_queue.put(None)
    for thread in threads:
        thread.join()

def vector_video(path, file_name):
    """利用file_processor.py中的pumping函数，将视频切分为图片帧"""
    try:
        result = pumping(path)
        frames = result['frames']
        vectors = []
        timestamps = []
        fps = result['frame_count'] / result['duration']  # 计算帧率
        for frame in frames:
            frame_path = frame['frame_path']
            frame_no = frame['no']
            vector_features = vector_image(frame_path, file_name)
            if vector_features is not None:
                vectors.append(vector_features)
                timestamps.append(frame_no / fps)  # 将帧编号转换为秒数

        # 返回向量结果和时间戳
        return {
            'filename': result['filename'],
            'filepath': result['filepath'],
            'vectors': vectors,
            'timestamps': timestamps
        }
    except Exception as e:
        logging.error(f"Error processing video {path}: {e}")
        return None
def process_images_in_task():
    """从任务队列中获取任务并处理图片向量化"""
    process_task('1', 'image_collection', vector_image)

def process_video():
    """从任务队列中获取任务并处理视频向量化"""
    process_task('2', 'video_collection', vector_video)
