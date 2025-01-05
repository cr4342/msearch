import os
import logging
from hashlib import md5
from nextcloud import NextcloudClient 

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskManager:
    def __init__(self, db_session):
        self.db_session = db_session
        self.nextcloud_client = None  # 这里初始化为空，稍后设置

    def set_nextcloud_client(self, nextcloud_url: str, username: str, password: str) -> None:
        """设置 Nextcloud 客户端实例"""
        self.nextcloud_client = NextcloudClient(nextcloud_url, username, password)
        if not self.nextcloud_client.login():
            logger.error("无法登录到 Nextcloud")
            raise Exception("无法登录到 Nextcloud")

    def add_remote_task(self, file_url: str) -> str:
        try:
            if not self.nextcloud_client:
                logger.error("Nextcloud 客户端未初始化或登录失败")
                raise Exception("Nextcloud 客户端未初始化或登录失败")

            local_cache_path = self._create_cache_directory(file_url)

            # 从 Nextcloud 下载文件到本地缓存路径
            download_result = self.nextcloud_client.download_file(file_url, local_cache_path)
            if download_result == "fail":
                logger.error(f"下载文件 {file_url} 失败")
                return "fail"

            file_md5 = self.calc_md5(download_result)
            existing_task = self.db_session.query(Task).filter_by(file_id=file_md5).first()

            if not existing_task:
                task_type = self.get_task_type(download_result)

                self.create_task(
                    file_id=file_md5,
                    file_name=os.path.basename(file_url),
                    source='remote',
                    file_path=file_url,  # 使用原始的 Nextcloud 文件路径
                    cache_path=download_result,
                    task_type=task_type
                )
                logger.info(f"为远程文件 {file_url} 创建了新任务")
            else:
                logger.info(f"文件 {file_url} 已经存在于数据库中")
        except Exception as e:
            logger.error(f"添加远程任务时发生错误: {e}")
            return "fail"

    def _create_cache_directory(self, file_url: str) -> str:
        """创建缓存目录并返回本地缓存路径"""
        cache_dir = "cache"  # 定义缓存目录
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        return os.path.join(cache_dir, os.path.basename(file_url))

    def calc_md5(self, cache_path: str) -> str:
        hasher = md5()
        with open(cache_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def get_task_type(self, cache_path: str) -> str:
        # 实现判断文件类型并返回任务类型的逻辑
        pass

    def create_task(self, **kwargs) -> None:
        # 实现创建新任务的逻辑
        pass

# 示例：如何从命令行获取信息并调用 add_remote_task 方法
if __name__ == '__main__':
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import create_engine

    # 初始化数据库会话（这里需要替换为实际的数据库连接字符串）
    engine = create_engine('sqlite:///tasks.db')
    Session = sessionmaker(bind=engine)
    session = Session()

    manager = TaskManager(session)
    
    # 获取Nextcloud的URL、用户名和密码
    nextcloud_url = input('Enter Nextcloud URL: ')
    username = input('Enter your username: ')
    password = getpass('Enter your password: ')

    # 设置 Nextcloud 客户端
    manager.set_nextcloud_client(nextcloud_url, username, password)

    # 添加远程任务示例
    file_url = input('Enter the Nextcloud file path you want to process: ')
    result = manager.add_remote_task(file_url)