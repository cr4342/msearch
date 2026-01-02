#!/usr/bin/env python3
# MSearch 数据库维护脚本
# 功能：数据库清理、优化、备份等维护任务

import argparse
import sqlite3
import os
import sys
import logging
import datetime
import shutil
from pathlib import Path
import faiss
import numpy as np

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# 添加项目根目录到Python路径
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.config_manager import get_config_manager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/database_maintenance.log')
    ]
)
logger = logging.getLogger(__name__)

class DatabaseMaintainer:
    def __init__(self, config_manager=None):
        self.config_manager = config_manager or get_config_manager()
        
        # 从配置文件读取配置
        self._load_config()
        
        # 连接状态
        self.connection = None
        self.cursor = None
        self.milvus_client = None
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("数据库维护工具初始化完成")
    
    def _load_config(self):
        """从配置文件加载配置"""
        # 数据库配置
        self.database_path = Path(self.config_manager.get("database.sqlite.path", "./data/msearch.db"))
        if not self.database_path.is_absolute():
            self.database_path = PROJECT_ROOT / self.database_path
        
        # 备份配置
        self.backup_dir = Path(self.config_manager.get("database.backup_dir", "./data/backups"))
        if not self.backup_dir.is_absolute():
            self.backup_dir = PROJECT_ROOT / self.backup_dir
        
        # 向量数据库配置
        self.vector_db_type = self.config_manager.get("database.vector_db.type", "milvus_lite")
        self.milvus_uri = self.config_manager.get("database.vector_db.uri", "./data/milvus/milvus.db")
        
        # 处理Milvus URI路径
        if self.vector_db_type == "milvus_lite":
            milvus_path = Path(self.milvus_uri)
            if not milvus_path.is_absolute():
                milvus_path = PROJECT_ROOT / milvus_path
            self.milvus_uri = str(milvus_path)
            self.milvus_dir = milvus_path.parent
            self.milvus_dir.mkdir(parents=True, exist_ok=True)
        
        # FAISS索引配置
        self.faiss_index_dir = Path(self.config_manager.get("database.faiss.index_dir", "./data/faiss_indices"))
        if not self.faiss_index_dir.is_absolute():
            self.faiss_index_dir = PROJECT_ROOT / self.faiss_index_dir
        
        # 维护配置
        self.default_clean_task_days = self.config_manager.get("database.maintenance.clean_task_days", 30)
        self.default_clean_vector_days = self.config_manager.get("database.maintenance.clean_vector_days", 90)
        
        # 确保目录存在
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.faiss_index_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"加载配置完成")
        self.logger.debug(f"数据库路径: {self.database_path}")
        self.logger.debug(f"备份目录: {self.backup_dir}")
        self.logger.debug(f"FAISS索引目录: {self.faiss_index_dir}")
        self.logger.debug(f"向量数据库类型: {self.vector_db_type}")
        self.logger.debug(f"Milvus URI: {self.milvus_uri}")
    
    def connect(self):
        """连接到数据库"""
        try:
            # 连接SQLite数据库
            self.connection = sqlite3.connect(str(self.database_path))
            self.cursor = self.connection.cursor()
            logger.info(f"成功连接到SQLite数据库: {self.database_path}")
            
            # 连接Milvus Lite数据库
            if self.vector_db_type == "milvus_lite":
                try:
                    from pymilvus import MilvusClient
                    self.milvus_client = MilvusClient(self.milvus_uri, db_name="default")
                    logger.info(f"成功连接到Milvus Lite数据库: {self.milvus_uri}")
                except Exception as e:
                    logger.warning(f"连接Milvus Lite数据库失败: {e}")
                    logger.warning("将只维护SQLite数据库")
            
            return True
        except sqlite3.Error as e:
            logger.error(f"连接SQLite数据库失败: {e}")
            return False
    
    def disconnect(self):
        """断开数据库连接"""
        if self.connection:
            self.connection.close()
            logger.info("SQLite数据库连接已关闭")
        
        if self.milvus_client:
            # Milvus Lite不需要显式断开连接，只需要将客户端设置为None
            self.milvus_client = None
            logger.info("Milvus Lite数据库连接已关闭")
    
    def backup_database(self, backup_file: Path = None):
        """备份数据库"""
        if not backup_file:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"msearch_backup_{timestamp}.db"
        
        try:
            # 确保备份目录存在
            backup_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 复制SQLite数据库文件
            shutil.copy2(str(self.database_path), str(backup_file))
            self.logger.info(f"SQLite数据库备份成功: {backup_file}")
            
            # 备份Milvus Lite数据库
            if self.vector_db_type == "milvus_lite":
                try:
                    # Milvus Lite备份：复制数据目录
                    milvus_backup_dir = backup_file.parent / f"milvus_backup_{timestamp}"
                    milvus_backup_dir.mkdir(parents=True, exist_ok=True)
                    
                    # 复制Milvus Lite的所有文件
                    for file in self.milvus_dir.glob("*"):
                        if file.is_file() and file.suffix in [".db", ".log"]:
                            milvus_backup_file = milvus_backup_dir / file.name
                            shutil.copy2(str(file), str(milvus_backup_file))
                            self.logger.info(f"Milvus Lite文件备份成功: {milvus_backup_file}")
                    
                    self.logger.info(f"Milvus Lite备份成功: {milvus_backup_dir}")
                except Exception as e:
                    self.logger.error(f"Milvus Lite备份失败: {e}")
            
            return backup_file
        except Exception as e:
            self.logger.error(f"数据库备份失败: {e}")
            return None
    
    def vacuum_database(self):
        """优化数据库（VACUUM命令）"""
        try:
            if not self.connection:
                if not self.connect():
                    return False
        
            self.logger.info("开始优化数据库...")
            self.cursor.execute("VACUUM")
            self.connection.commit()
            self.logger.info("数据库优化完成")
            return True
        except sqlite3.Error as e:
            self.logger.error(f"数据库优化失败: {e}")
            return False
    
    def reindex_database(self):
        """重建索引"""
        try:
            if not self.connection:
                if not self.connect():
                    return False
        
            self.logger.info("开始重建索引...")
            
            # 获取所有表名
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = self.cursor.fetchall()
            
            for table in tables:
                table_name = table[0]
                if table_name.startswith('sqlite_'):
                    continue
                
                # 重建表的索引
                self.cursor.execute(f"REINDEX {table_name};")
                self.logger.info(f"重建表 {table_name} 的索引完成")
            
            # 重建所有索引
            self.cursor.execute("REINDEX;")
            self.connection.commit()
            
            self.logger.info("所有索引重建完成")
            return True
        except sqlite3.Error as e:
            self.logger.error(f"重建索引失败: {e}")
            return False
    
    def clean_old_tasks(self, days: int = None):
        """清理旧任务记录"""
        if days is None:
            days = self.default_clean_task_days
            
        try:
            if not self.connection:
                if not self.connect():
                    return False
        
            self.logger.info(f"开始清理 {days} 天前的旧任务...")
            
            # 计算截止时间
            cutoff_time = datetime.datetime.now().timestamp() - (days * 86400)
            
            # 清理旧任务
            self.cursor.execute("DELETE FROM tasks WHERE updated_at < ?", (cutoff_time,))
            deleted_count = self.cursor.rowcount
            self.connection.commit()
            
            self.logger.info(f"清理完成，共删除 {deleted_count} 条旧任务记录")
            return True
        except sqlite3.Error as e:
            self.logger.error(f"清理旧任务失败: {e}")
            return False
    
    def clean_old_vectors(self, days: int = None):
        """清理旧向量记录"""
        if days is None:
            days = self.default_clean_vector_days
            
        try:
            if not self.connection:
                if not self.connect():
                    return False
        
            self.logger.info(f"开始清理 {days} 天前的旧向量记录...")
            
            # 计算截止时间
            cutoff_time = datetime.datetime.now().timestamp() - (days * 86400)
            
            # 清理旧向量
            self.cursor.execute("DELETE FROM vectors WHERE created_at < ?", (cutoff_time,))
            deleted_count = self.cursor.rowcount
            self.connection.commit()
            
            self.logger.info(f"清理完成，共删除 {deleted_count} 条旧向量记录")
            return True
        except sqlite3.Error as e:
            self.logger.error(f"清理旧向量记录失败: {e}")
            return False
    
    def get_database_info(self):
        """获取数据库信息"""
        try:
            if not self.connection:
                if not self.connect():
                    return None
        
            info = {}
            
            # 获取数据库文件大小
            info['file_size'] = os.path.getsize(str(self.database_path))
            
            # 获取表信息
            self.cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table';")
            tables = self.cursor.fetchall()
            info['tables'] = [table[0] for table in tables if not table[0].startswith('sqlite_')]
            
            # 获取各表记录数
            info['table_counts'] = {}
            for table in info['tables']:
                self.cursor.execute(f"SELECT COUNT(*) FROM {table};")
                count = self.cursor.fetchone()[0]
                info['table_counts'][table] = count
            
            self.logger.info(f"数据库信息: {info}")
            return info
        except Exception as e:
            self.logger.error(f"获取数据库信息失败: {e}")
            return None
    
    def check_integrity(self):
        """检查数据库完整性"""
        try:
            if not self.connection:
                if not self.connect():
                    return False
        
            self.logger.info("开始检查数据库完整性...")
            self.cursor.execute("PRAGMA integrity_check;")
            result = self.cursor.fetchone()[0]
            
            if result == "ok":
                self.logger.info("数据库完整性检查通过")
                return True
            else:
                self.logger.error(f"数据库完整性检查失败: {result}")
                return False
        except sqlite3.Error as e:
            self.logger.error(f"数据库完整性检查失败: {e}")
            return False
    
    def analyze_database(self):
        """分析数据库（更新统计信息）"""
        try:
            if not self.connection:
                if not self.connect():
                    return False
        
            self.logger.info("开始分析数据库...")
            self.cursor.execute("ANALYZE")
            self.connection.commit()
            self.logger.info("数据库分析完成")
            return True
        except sqlite3.Error as e:
            self.logger.error(f"数据库分析失败: {e}")
            return False
    
    def clean_all_old_data(self, task_days: int = None, vector_days: int = None):
        """清理所有旧数据"""
        if task_days is None:
            task_days = self.default_clean_task_days
        if vector_days is None:
            vector_days = self.default_clean_vector_days
            
        self.logger.info("开始清理所有旧数据...")
        
        # 先备份数据库
        backup_file = self.backup_database()
        if not backup_file:
            self.logger.warning("备份失败，但仍继续清理")
        
        # 清理旧任务
        self.clean_old_tasks(task_days)
        
        # 清理旧向量
        self.clean_old_vectors(vector_days)
        
        # 优化数据库
        self.vacuum_database()
        
        self.logger.info("所有旧数据清理完成")
        return True
    
    def get_faiss_indices(self):
        """获取所有FAISS索引文件"""
        try:
            indices = []
            for file in self.faiss_index_dir.iterdir():
                if file.suffix in ['.index', '.faiss']:
                    indices.append(file)
            return indices
        except Exception as e:
            self.logger.error(f"获取FAISS索引文件失败: {e}")
            return []
    
    def check_faiss_index(self, index_path: Path):
        """检查FAISS索引完整性"""
        try:
            self.logger.info(f"开始检查FAISS索引: {index_path}")
            
            # 尝试加载索引
            index = faiss.read_index(str(index_path))
            
            # 获取索引信息
            info = {
                'dimension': index.d,
                'ntotal': index.ntotal,
                'metric_type': index.metric_type
            }
            
            self.logger.info(f"FAISS索引检查通过: {info}")
            return True, info
        except Exception as e:
            self.logger.error(f"FAISS索引检查失败: {e}")
            return False, None
    
    def optimize_faiss_index(self, index_path: Path):
        """优化FAISS索引"""
        try:
            self.logger.info(f"开始优化FAISS索引: {index_path}")
            
            # 加载索引
            index = faiss.read_index(str(index_path))
            
            # 优化索引（根据索引类型执行不同的优化操作）
            if isinstance(index, faiss.IndexIVF):
                # IVF索引需要训练，但如果已经训练过，就执行重构
                if not index.is_trained:
                    self.logger.warning(f"FAISS索引 {index_path} 未训练，跳过优化")
                    return False
                else:
                    # 重构索引以提高搜索性能
                    index.reconstruct_n(0, index.ntotal)
            elif isinstance(index, faiss.IndexHNSW):
                # HNSW索引不需要特殊优化，只需要确保它是最新的
                pass
            
            # 保存优化后的索引
            faiss.write_index(index, str(index_path))
            self.logger.info(f"FAISS索引优化完成: {index_path}")
            return True
        except Exception as e:
            self.logger.error(f"FAISS索引优化失败: {e}")
            return False
    
    def backup_faiss_indices(self, backup_dir: Path = None):
        """备份所有FAISS索引"""
        if not backup_dir:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = self.backup_dir / f"faiss_backup_{timestamp}"
        
        try:
            # 确保备份目录存在
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # 获取所有FAISS索引
            indices = self.get_faiss_indices()
            
            for index_path in indices:
                # 复制索引文件
                backup_path = backup_dir / index_path.name
                shutil.copy2(str(index_path), str(backup_path))
                self.logger.info(f"FAISS索引备份成功: {backup_path}")
            
            self.logger.info(f"所有FAISS索引备份完成，共备份 {len(indices)} 个索引")
            return backup_dir
        except Exception as e:
            self.logger.error(f"FAISS索引备份失败: {e}")
            return None
    
    def optimize_all_faiss_indices(self):
        """优化所有FAISS索引"""
        try:
            # 获取所有FAISS索引
            indices = self.get_faiss_indices()
            
            for index_path in indices:
                self.optimize_faiss_index(index_path)
            
            self.logger.info(f"所有FAISS索引优化完成，共优化 {len(indices)} 个索引")
            return True
        except Exception as e:
            self.logger.error(f"优化所有FAISS索引失败: {e}")
            return False
    
    def check_all_faiss_indices(self):
        """检查所有FAISS索引"""
        try:
            # 获取所有FAISS索引
            indices = self.get_faiss_indices()
            
            results = []
            for index_path in indices:
                is_valid, info = self.check_faiss_index(index_path)
                results.append((index_path, is_valid, info))
            
            # 统计结果
            valid_count = sum(1 for _, is_valid, _ in results if is_valid)
            total_count = len(results)
            
            self.logger.info(f"FAISS索引检查完成: {valid_count}/{total_count} 个索引有效")
            return results
        except Exception as e:
            self.logger.error(f"检查所有FAISS索引失败: {e}")
            return []
    
    def maintain_faiss_indices(self):
        """维护所有FAISS索引：备份、检查、优化"""
        self.logger.info("开始FAISS索引维护...")
        
        # 备份所有FAISS索引
        backup_dir = self.backup_faiss_indices()
        if not backup_dir:
            self.logger.warning("FAISS索引备份失败，但仍继续维护")
        
        # 检查所有FAISS索引
        self.check_all_faiss_indices()
        
        # 优化所有FAISS索引
        self.optimize_all_faiss_indices()
        
        self.logger.info("FAISS索引维护完成")
        return True
    
    def maintain_milvus_database(self):
        """维护Milvus Lite数据库：检查、优化"""
        if self.vector_db_type != "milvus_lite":
            self.logger.info(f"跳过Milvus Lite维护，当前向量数据库类型为: {self.vector_db_type}")
            return True
        
        if not self.milvus_client:
            self.logger.warning("Milvus Lite客户端未连接，跳过维护")
            return True
        
        self.logger.info("开始Milvus Lite数据库维护...")
        
        try:
            # 获取所有集合
            collections = self.milvus_client.list_collections()
            self.logger.info(f"Milvus Lite包含 {len(collections)} 个集合: {collections}")
            
            # 检查每个集合
            for collection_name in collections:
                # 获取集合统计信息
                stats = self.milvus_client.get_collection_stats(collection_name)
                row_count = stats.get("row_count", 0)
                self.logger.info(f"集合 {collection_name} 包含 {row_count} 个向量")
                
                # 检查索引
                index_info = self.milvus_client.describe_index(collection_name, "vector")
                self.logger.info(f"集合 {collection_name} 索引信息: {index_info}")
            
            self.logger.info("Milvus Lite数据库维护完成")
            return True
        except Exception as e:
            self.logger.error(f"Milvus Lite数据库维护失败: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description="MSearch数据库维护脚本")
    
    parser.add_argument("--backup", action="store_true", help="备份数据库")
    parser.add_argument("--vacuum", action="store_true", help="优化数据库")
    parser.add_argument("--reindex", action="store_true", help="重建索引")
    parser.add_argument("--analyze", action="store_true", help="分析数据库")
    parser.add_argument("--check", action="store_true", help="检查数据库完整性")
    parser.add_argument("--clean-tasks", type=int, default=30, help="清理指定天数前的任务记录")
    parser.add_argument("--clean-vectors", type=int, default=90, help="清理指定天数前的向量记录")
    parser.add_argument("--clean-all", action="store_true", help="清理所有旧数据")
    parser.add_argument("--info", action="store_true", help="获取数据库信息")
    
    # FAISS索引维护参数
    parser.add_argument("--faiss-check", action="store_true", help="检查FAISS索引完整性")
    parser.add_argument("--faiss-optimize", action="store_true", help="优化FAISS索引")
    parser.add_argument("--faiss-backup", action="store_true", help="备份FAISS索引")
    parser.add_argument("--faiss-maintain", action="store_true", help="完整维护FAISS索引（备份、检查、优化）")
    
    # Milvus Lite维护参数
    parser.add_argument("--milvus-maintain", action="store_true", help="维护Milvus Lite数据库（检查、优化）")
    
    args = parser.parse_args()
    
    # 创建数据库维护实例
    maintainer = DatabaseMaintainer()
    
    try:
        # 连接数据库
        if not maintainer.connect():
            sys.exit(1)
        
        # 执行相应的维护任务
        if args.backup:
            maintainer.backup_database()
        
        if args.vacuum:
            maintainer.vacuum_database()
        
        if args.reindex:
            maintainer.reindex_database()
        
        if args.analyze:
            maintainer.analyze_database()
        
        if args.check:
            maintainer.check_integrity()
        
        if args.clean_tasks:
            maintainer.clean_old_tasks(args.clean_tasks)
        
        if args.clean_vectors:
            maintainer.clean_old_vectors(args.clean_vectors)
        
        if args.clean_all:
            maintainer.clean_all_old_data()
        
        if args.info:
            maintainer.get_database_info()
        
        # FAISS索引维护任务
        if args.faiss_check:
            maintainer.check_all_faiss_indices()
        
        if args.faiss_optimize:
            maintainer.optimize_all_faiss_indices()
        
        if args.faiss_backup:
            maintainer.backup_faiss_indices()
        
        if args.faiss_maintain:
            maintainer.maintain_faiss_indices()
        
        # Milvus Lite维护任务
        if args.milvus_maintain:
            maintainer.maintain_milvus_database()
        
        # 如果没有指定任何任务，显示帮助
        if not any([args.backup, args.vacuum, args.reindex, args.analyze, 
                   args.check, args.clean_tasks > 0, args.clean_vectors > 0, 
                   args.clean_all, args.info, args.faiss_check, 
                   args.faiss_optimize, args.faiss_backup, args.faiss_maintain,
                   args.milvus_maintain]):
            parser.print_help()
            sys.exit(0)
            
    except KeyboardInterrupt:
        maintainer.logger.info("用户中断操作")
    except Exception as e:
        maintainer.logger.error(f"执行维护任务失败: {e}")
        sys.exit(1)
    finally:
        # 断开连接
        maintainer.disconnect()

if __name__ == "__main__":
    main()