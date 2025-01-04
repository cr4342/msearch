import hashlib
import os
from datetime import datetime
from sqlalchemy.orm import Session
import requests

from ulity import scan_files, file_type  # 导入文件处理模块
from init_sql import Task

class TaskManager:
    def __init__(self, db_session: Session):
        self.db_session = db_session

    async def create_task(self, file_id: str, file_name: str, source: str, file_path: str, cache_path: str, task_type: int):
        try:
            new_task = Task(
                file_id=file_id,
                file_name=file_name,
                source=source,
                file_path=file_path,
                cache_path=cache_path,
                type=task_type,
                vectorized=0,
                created_at=datetime.now()
            )
            self.db_session.add(new_task)
            await self.db_session.commit()
            return new_task
        except Exception as e:
            self.db_session.rollback()
            raise Exception(f"创建任务失败: {e}")

    def get_task_type(self, file_path):
        """根据文件类型返回任务类型"""
        file_category = file_type(file_path)
        task_type_mapping = {
            'document': 0,
            'picture': 1,
            'video': 2,
            'audio': 3
        }
        return task_type_mapping.get(file_category, 4)

    def calc_md5(self, file_path):
        """计算文件的MD5值"""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            print(f"计算文件 {file_path} 的MD5值失败: {e}")
            return "fail"

    def create_local_tasks(self, folder_path):
        """扫描本地文件夹并创建新任务"""
        try:
            file_paths = scan_files(folder_path)  # 使用 file_processor 中的 scan_files 方法
            for file_path in file_paths:
                file_md5 = self.calc_md5(file_path)
                if file_md5 == "fail":
                    print(f"文件 {file_path} 的MD5计算失败，跳过该文件")
                    continue

                # 检查数据库中是否已存在相同MD5的文件
                existing_task = self.db_session.query(Task).filter_by(file_id=file_md5).first()
                if not existing_task:
                    # 判断文件类型并定义任务类型
                    task_type = self.get_task_type(file_path)
                    self.create_task(file_id=file_md5, file_name=os.path.basename(file_path), source='local',
                                    file_path=file_path, cache_path=None, task_type=task_type)
                    print(f"为文件 {file_path} 创建了新任务")
                else:
                    print(f"文件 {file_path} 已经存在于数据库中")
        except Exception as e:
            print(f"创建本地任务时发生错误: {e}")
            return "fail"

    def download_file(self, file_url):
        """
        从url下载文件到配置文件指定的缓存路径，返回缓存的文件路径
        """
        cache_path = config.get('cache_path', 'default_cache_path')
        if not os.path.exists(cache_path):
            os.makedirs(cache_path)

        file_name = os.path.basename(file_url)
        cache_file_path = os.path.join(cache_path, file_name)

        try:
            response = requests.get(file_url, stream=True)
            response.raise_for_status()
            with open(cache_file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return cache_file_path
        except requests.RequestException as e:
            print(f"下载文件失败：{e}")
            return "fail"

    def add_remote_task(self, file_url):
        try:
            cache_path = self.download_file(file_url)
            if cache_path == "fail":
                print(f"下载文件 {file_url} 失败")
                return "fail"

            file_md5 = self.calc_md5(cache_path)
            if file_md5 == "fail":
                print(f"文件 {cache_path} 的MD5计算失败，跳过该文件")
                return "fail"

            existing_task = self.db_session.query(Task).filter_by(file_id=file_md5).first()
            if not existing_task:
                # 判断文件类型并定义任务类型
                task_type = self.get_task_type(cache_path)
                self.create_task(file_id=file_md5, file_name=os.path.basename(file_url), source='remote',
                                file_path=file_url, cache_path=cache_path, task_type=task_type)
                print(f"为远程文件 {file_url} 创建了新任务")
            else:
                print(f"文件 {file_url} 已经存在于数据库中")
        except Exception as e:
            print(f"添加远程任务时发生错误: {e}")
            return "fail"

    def get_task_ids(self, task_type, vectorized=0):
        """
        根据任务类型和向量化状态获取所有匹配的任务ID列表
        :param task_type: 任务类型
        :param vectorized: 向量化状态，默认为0
        :return: 所有匹配的任务ID列表，如果不存在返回空列表
        """
        tasks = self.db_session.query(Task.id).filter_by(type=task_type, vectorized=vectorized).all()
        return [task.id for task in tasks]  # 返回所有匹配的任务ID列表

    def get_task_by_id(self, task_id):
        """
        根据任务ID获取任务对象的字典表示
        :param task_id: 任务ID
        :return: 任务对象的字典表示，如果不存在返回None
        """
        task = self.db_session.query(Task).filter_by(id=task_id).first()
        return task.__dict__ if task else None  # 返回任务对象的字典表示

    def update_task(self, task_id, key, value):
        """
        更新任务列表中的任务
        :param task_id: 要更新的任务ID
        :param key: 要更新的任务键
        :param value: 要更新的任务值
        :return: None
        """
        try:
            task = self.db_session.query(Task).filter_by(id=task_id).first()
            if task:
                setattr(task, key, value)
                self.db_session.commit()
                print(f"任务 {task_id} 更新成功")
            else:
                print(f"任务 {task_id} 未找到")
        except Exception as e:
            print(f"更新任务 {task_id} 时发生错误: {e}")
            self.db_session.rollback()
