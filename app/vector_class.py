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

print("Available models:", available_models())
# Available models: ['ViT-B-16', 'ViT-L-14', 'ViT-L-14-336', 'ViT-H-14', 'RN50']

device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = load_from_name("ViT-B-16", device=device, download_root='./')
model.eval()

class Vectorization():
    
def vector_text(text):
    """将文本转换为向量"""
    try:
        text = clip.tokenize([text]).to(device)
        with torch.no_grad():
            text_features = model.encode_text(text)
        return text_features
    except Exception as e:
        logging.error(f"Error encoding text: {e}")
        raise VectorizationError(f"Error encoding text: {e}")

def combine_vectors(image_features, text_features):
    """统一文件名向量和文件向量的比例"""
    try:
        text_features /= text_features.norm(dim=-1, keepdim=True)
        logits_per_image, _ = model.get_similarity(image_features, text_features)
        probs = logits_per_image.softmax(dim=-1).cpu().numpy()
        return probs
    except Exception as e:
        logging.error(f"Error combining vectors: {e}")
        raise VectorizationError(f"Error combining vectors: {e}")

def vector_image(path):
    """处理单张图片并返回其向量特征"""
    file_name = os.path.basename(path)
    try:
        image = preprocess(Image.open(path)).unsqueeze(0).to(device)
        text = clip.tokenize([file_name]).to(device)

        with torch.no_grad():
            image_features = model.encode_image(image)
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            probs = combine_vectors(image_features, text) 

        return probs
    except Exception as e:
        logging.error(f"Error processing image {path}: {e}")
        raise VectorizationError(f"Error processing image {path}: {e}")

def vector_video(path):
    """利用ulity.py中的pumping函数，将视频切分为图片帧"""
    try:
        result = pumping(path)
        if not all(key in result for key in ['frames', 'frame_count', 'duration']):
            raise ValueError("Invalid video processing result")

        frames = result['frames']
        frame_vectors = {} 
        fps = 1  

        for frame in frames:
            frame_path = frame['frame_path']
            frame_no = frame['no']
            vector_features = vector_image(frame_path)
            if vector_features is not None:
                frame_vectors[frame_no] = {
                    'vector': vector_features,
                    'timestamp': frame_no / fps  # 直接使用 frame_no 作为秒数
                }

        # 删除 pumping 产生的视频帧缓存
        for frame in frames:
            frame_path = frame['frame_path']
            if os.path.exists(frame_path):
                os.remove(frame_path)

        # 返回向量结果和时间戳
        return {
            'filename': result['filename'],
            'filepath': result['filepath'],
            'frame_vectors': frame_vectors
        }
    except Exception as e:
        logging.error(f"Error processing video {path}: {e}")
        raise VectorizationError(f"Error processing video {path}: {e}")