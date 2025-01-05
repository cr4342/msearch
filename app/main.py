import asyncio
import configparser
import os
import sys
import time
from task import TaskManager, init_sql, get_db_session


def build_task_scan(self, file_path, cache_dir):
        
    target_folder = config.get('General', 'target_folder')
    webdav_url = config.get('General', 'remote_folder')
        
    create_local_tasks(target_folder)  # 从配置中获取本地目标文件夹路径
    create_remote_tasks(webdav_url)    # 从配置中获取 WebDAV URL
    

if __name__ == '__main__':
    try:
        init_sql()  