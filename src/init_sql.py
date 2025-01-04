import configparser  # 引入配置解析器
from sqlalchemy import create_engine, Column, String, Integer, TIMESTAMP, Enum, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import SQLAlchemyError  # 引入 SQLAlchemy 异常处理

# 创建 SQLAlchemy 基类
Base = declarative_base()


# 定义任务表的数据模型
class Task(Base):
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(String(255), index=True, nullable=False)  # 文件ID
    file_name = Column(String(255), nullable=False)  # 文件名
    source = Column(String(100), nullable=False)  # 任务来源
    file_path = Column(String(255), nullable=False)  # 原文件路径
    md5 = Column(String(32), nullable=False)  # MD5
    created_at = Column(TIMESTAMP, server_default=func.now())  # 创建时间
    cache_path = Column(String(255), nullable=True)  # 缓存文件路径
    cache_completed_at = Column(TIMESTAMP, nullable=True)  # 缓存完成时间
    type = Column(Enum('0', '1', '2', '3', '4'), nullable=False)  # 任务类型
    type_update_time = Column(TIMESTAMP, nullable=True)  # 任务类型最后更新时间
    vectorized = Column(Integer, default=0)  # 向量化状态，0表示未向量化
    first_vectorized = Column(TIMESTAMP, nullable=True)  # 初次向量化时间
    last_vectorized = Column(TIMESTAMP, nullable=True)  # 最后一次向量化时间


def create_database(db_url):
    try:
        with create_engine(db_url) as engine:
            Base.metadata.create_all(bind=engine)
            logging.info("Database and tables created successfully.")
    except SQLAlchemyError as e:
        logging.error(f"An error occurred while creating the database: {e}")
        raise  # 重新抛出异常以便外部处理


def get_db_url(db_type, db_user, db_password, db_host, db_name):
    # 根据数据库类型生成数据库 URL
    db_urls = {
        'mariadb': f"mariadb+mariadbconnector://{db_user}:{db_password}@{db_host}/{db_name}",
        'postgresql': f"postgresql://{db_user}:{db_password}@{db_host}/{db_name}",
        'sqlite': f"sqlite:///{db_name}.db"  # SQLite 使用文件名作为数据库
    }
    if db_type not in db_urls:
        raise ValueError("Unsupported database type. Please use 'mariadb', 'postgresql', or 'sqlite'.")
    return db_urls[db_type]


def validate_config(config):
    required_keys = ['type', 'user', 'password', 'host', 'dbname']
    for key in required_keys:
        if key not in config:
            raise KeyError(f"Missing required configuration: {key}")


if __name__ == "__main__":
    try:
        # 从配置文件读取数据库类型
        config = configparser.ConfigParser()
        config.read('config/config.ini')  # 可以通过命令行参数或环境变量传递

        # 获取数据库配置
        db_config = config['DATABASE']
        validate_config(db_config)

        db_type = db_config['type']
        db_user = db_config['user']
        db_password = db_config['password']
        db_host = db_config['host']
        db_name = db_config['dbname']

        # 生成数据库 URL
        db_url = get_db_url(db_type, db_user, db_password, db_host, db_name)

        # 初始化数据库
        create_database(db_url)
    except KeyError as e:
        logging.error(f"Missing required configuration: {e}")
    except ValueError as e:
        logging.error(f"Configuration error: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

import configparser
import logging
from sqlalchemy import create_engine, Column, String, Integer, TIMESTAMP, Enum, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import SQLAlchemyError

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 创建 SQLAlchemy 基类
Base = declarative_base()


# 定义任务表的数据模型
class Task(Base):
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(String(255), index=True, nullable=False)  # 文件ID
    file_name = Column(String(255), nullable=False)  # 文件名
    source = Column(String(100), nullable=False)  # 任务来源
    file_path = Column(String(255), nullable=False)  # 原文件路径
    md5 = Column(String(32), nullable=False)  # MD5
    created_at = Column(TIMESTAMP, server_default=func.now())  # 创建时间
    cache_path = Column(String(255), nullable=True)  # 缓存文件路径
    cache_completed_at = Column(TIMESTAMP, nullable=True)  # 缓存完成时间
    type = Column(Enum('0', '1', '2', '3', '4'), nullable=False)  # 任务类型
    type_update_time = Column(TIMESTAMP, nullable=True)  # 任务类型最后更新时间
    vectorized = Column(Integer, default=0)  # 向量化状态，0表示未向量化
    first_vectorized = Column(TIMESTAMP, nullable=True)  # 初次向量化时间
    last_vectorized = Column(TIMESTAMP, nullable=True)  # 最后一次向量化时间


def create_database(db_url):
    try:
        with create_engine(db_url) as engine:
            Base.metadata.create_all(bind=engine)
            logging.info("Database and tables created successfully.")
    except SQLAlchemyError as e:
        logging.error(f"An error occurred while creating the database: {e}")
        raise  # 重新抛出异常以便外部处理


def get_db_url(db_type, db_user, db_password, db_host, db_name):
    # 根据数据库类型生成数据库 URL
    db_urls = {
        'mariadb': f"mariadb+mariadbconnector://{db_user}:{db_password}@{db_host}/{db_name}",
        'postgresql': f"postgresql://{db_user}:{db_password}@{db_host}/{db_name}",
        'sqlite': f"sqlite:///{db_name}.db"  # SQLite 使用文件名作为数据库
    }
    if db_type not in db_urls:
        raise ValueError("Unsupported database type. Please use 'mariadb', 'postgresql', or 'sqlite'.")
    return db_urls[db_type]


def validate_config(config):
    required_keys = ['type', 'user', 'password', 'host', 'dbname']
    for key in required_keys:
        if key not in config:
            raise KeyError(f"Missing required configuration: {key}")


if __name__ == "__main__":
    try:
        # 获取配置文件路径（可以使用环境变量或其他方式）
        config_path = 'config/config.ini'  # 可以通过命令行参数或环境变量传递

        # 从配置文件读取数据库类型
        config = configparser.ConfigParser()
        config.read(config_path)

        # 获取数据库配置
        db_config = config['DATABASE']
        validate_config(db_config)

        db_type = db_config['type']
        db_user = db_config['user']
        db_password = db_config['password']
        db_host = db_config['host']
        db_name = db_config['dbname']

        # 生成数据库 URL
        db_url = get_db_url(db_type, db_user, db_password, db_host, db_name)

        # 初始化数据库
        create_database(db_url)
    except KeyError as e:
        logging.error(f"Missing required configuration: {e}")
    except ValueError as e:
        logging.error(f"Configuration error: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")