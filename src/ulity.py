import json
import os
import cv2
from PIL import Image
import towhee
import re
import logging
import tempfile
from pathlib import Path
def scan_files(folder_path, start_from=None, last_scanned=None):
    file_list = []
    try:
        for root, _, files in os.walk(os.path.normpath(folder_path)):
            files.sort()  # Ensure files are processed in a consistent order
            for file in files:
                file_path = os.path.join(root, file)
                if start_from and os.path.normpath(file_path) < os.path.normpath(start_from):
                    continue
                if last_scanned and os.path.normpath(file_path) <= os.path.normpath(last_scanned):
                    continue  # Skip files that were already scanned
                if os.access(file_path, os.R_OK):  # Check file readability
                    file_list.append(file_path)
                else:
                    print(f"Warning: No read permission for {file_path}")
    except Exception as e:
        print(f"Error scanning files: {e}")
        return None  # Return None to indicate failure
    return file_list

def file_type(file_path):
    file_suffix = re.search(r'\.([^.]+)$', file_path, re.IGNORECASE)
    if not file_suffix:
        return 'other'
    file_suffix = file_suffix.group(1).lower()
    
    file_types = {
        'document': ['doc', 'docx', 'txt', 'pdf', 'ppt', 'pptx', 'xls', 'xlsx'],
        'video': ['mp4', 'avi', 'flv', 'rmvb', 'wmv', 'mkv', 'mov', '3gp'],
        'audio': ['mp3', 'wav', 'flac', 'ape', 'aac', 'm4a'],
        'picture': ['jpg', 'jpeg', 'png', 'gif', 'svg', 'psd', 'bmp']
    }
    
    for file_type, extensions in file_types.items():
        if file_suffix in extensions:
            return file_type
    return 'other'


logging.basicConfig(level=logging.INFO)

def pumping(file_path):
    video_name = os.path.splitext(os.path.basename(file_path))[0]  # 获取视频文件名（不带扩展名）
    cache_dir = tempfile.mkdtemp(prefix=f"{video_name}_")  # 创建临时缓存目录
    
    cap = cv2.VideoCapture(file_path)
    if not cap.isOpened():
        logging.error(f"Failed to open video file: {file_path}")
        return None

    fps = cap.get(cv2.CAP_PROP_FPS)  # 获取视频的帧率
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))  # 获取总帧数
    duration = total_frames / fps  # 计算视频时长（秒）

    frame_paths = []  # 用于存储每帧的路径

    # 每秒提取一帧
    for frame_count in range(int(duration)):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(frame_count * fps))  # 设置当前帧位置
        ret, frame = cap.read()
        if not ret:
            logging.warning(f"Failed to read frame {frame_count + 1} from {file_path}")
            continue
        
        frame_file_name = f"{video_name}{frame_count + 1}.jpg"  # 生成文件名
        frame_path = os.path.join(cache_dir, frame_file_name)  # 完整路径
        cv2.imwrite(frame_path, frame)  # 保存帧
        frame_paths.append({
            "no": frame_count,  # 帧的序号
            "frame": frame_file_name,  # 帧的文件名
            "frame_path": frame_path  # 帧的完整路径
        })  # 添加到路径列表

    cap.release()  # 释放视频对象

    # 清理临时目录
    def cleanup_cache():
        for p in Path(cache_dir).glob('*'):
            p.unlink()
        Path(cache_dir).rmdir()

    result = {
        "filename": video_name,
        "filepath": file_path,
        "frame_count": total_frames,
        "frames": frame_paths  # 使用更新的帧路径列表
    }

    cleanup_cache()  # 清理临时文件
    return result  # 返回字典

def convert_video2gif(video_path, num_samples=16):
    output_gif_path = os.path.splitext(os.path.normpath(video_path))[0] + '.gif'
    
    try:
        frames = (
            towhee.glob(video_path)
                  .video_decode.ffmpeg(sample_type='uniform_temporal_subsample', args={'num_samples': num_samples})
                  .to_list()[0]
        )
        imgs = [Image.fromarray(frame) for frame in frames]
        imgs[0].save(fp=output_gif_path, format='GIF', append_images=imgs[1:], save_all=True, loop=0)
    except Exception as e:
        logging.error(f"Error converting video to GIF: {e}")
        return None

    return output_gif_path
