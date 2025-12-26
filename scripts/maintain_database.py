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

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
DATABASE_PATH = PROJECT_ROOT / 'data' / 'database' / 'msearch.db'
BACKUP_DIR = PROJECT_ROOT / 'data' / 'backups'
FAISS_INDEX_DIR = PROJECT_ROOT / 'data' / 'database' / 'faiss_indices'

class DatabaseMaintainer:
    def __init__(self, database_path: Path):
        self.database_path = database_path
        self.connection = None
        self.cursor = None
        
        # 确保备份目录存在
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        
        # 确保FAISS索引目录存在
        FAISS_INDEX_DIR.mkdir(parents=True, exist_ok=True)
    
    def connect(self):
        """连接到数据库"""
        try:
            self.connection = sqlite3.connect(str(self.database_path))
            self.cursor = self.connection.cursor()
            logger.info(f"成功连接到数据库: {self.database_path}")
            return True
        except sqlite3.Error as e:
            logger.error(f"连接数据库失败: {e}")
            return False
    
    def disconnect(self):
        """断开数据库连接"""
        if self.connection:
            self.connection.close()
            logger.info("数据库连接已关闭")
    
    def backup_database(self, backup_file: Path = None):
        """备份数据库"""
        if not backup_file:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = BACKUP_DIR / f"msearch_backup_{timestamp}.db"
        
        try:
            # 确保备份目录存在
            backup_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 复制数据库文件
            shutil.copy2(str(self.database_path), str(backup_file))
            logger.info(f"数据库备份成功: {backup_file}")
            return backup_file
        except Exception as e:
            logger.error(f"数据库备份失败: {e}")
            return None
    
    def vacuum_database(self):
        """优化数据库（VACUUM命令）"""
        try:
            if not self.connection:
                if not self.connect():
                    return False
        
            logger.info("开始优化数据库...")
            self.cursor.execute("VACUUM")
            self.connection.commit()
            logger.info("数据库优化完成")
            return True
        except sqlite3.Error as e:
            logger.error(f"数据库优化失败: {e}")
            return False
    
    def reindex_database(self):
        """重建索引"""
        try:
            if not self.connection:
                if not self.connect():
                    return False
        
            logger.info("开始重建索引...")
            
            # 获取所有表名
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = self.cursor.fetchall()
            
            for table in tables:
                table_name = table[0]
                if table_name.startswith('sqlite_'):
                    continue
                
                # 重建表的索引
                self.cursor.execute(f"REINDEX {table_name};")
                logger.info(f"重建表 {table_name} 的索引完成")
            
            # 重建所有索引
            self.cursor.execute("REINDEX;")
            self.connection.commit()
            
            logger.info("所有索引重建完成")
            return True
        except sqlite3.Error as e:
            logger.error(f"重建索引失败: {e}")
            return False
    
    def clean_old_tasks(self, days: int = 30):
        """清理旧任务记录"""
        try:
            if not self.connection:
                if not self.connect():
                    return False
        
            logger.info(f"开始清理 {days} 天前的旧任务...")
            
            # 计算截止时间
            cutoff_time = datetime.datetime.now().timestamp() - (days * 86400)
            
            # 清理旧任务
            self.cursor.execute("DELETE FROM tasks WHERE updated_at < ?", (cutoff_time,))
            deleted_count = self.cursor.rowcount
            self.connection.commit()
            
            logger.info(f"清理完成，共删除 {deleted_count} 条旧任务记录")
            return True
        except sqlite3.Error as e:
            logger.error(f"清理旧任务失败: {e}")
            return False
    
    def clean_old_vectors(self, days: int = 90):
        """清理旧向量记录"""
        try:
            if not self.connection:
                if not self.connect():
                    return False
        
            logger.info(f"开始清理 {days} 天前的旧向量记录...")
            
            # 计算截止时间
            cutoff_time = datetime.datetime.now().timestamp() - (days * 86400)
            
            # 清理旧向量
            self.cursor.execute("DELETE FROM vectors WHERE created_at < ?", (cutoff_time,))
            deleted_count = self.cursor.rowcount
            self.connection.commit()
            
            logger.info(f"清理完成，共删除 {deleted_count} 条旧向量记录")
            return True
        except sqlite3.Error as e:
            logger.error(f"清理旧向量记录失败: {e}")
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
            
            logger.info(f"数据库信息: {info}")
            return info
        except Exception as e:
            logger.error(f"获取数据库信息失败: {e}")
            return None
    
    def check_integrity(self):
        """检查数据库完整性"""
        try:
            if not self.connection:
                if not self.connect():
                    return False
        
            logger.info("开始检查数据库完整性...")
            self.cursor.execute("PRAGMA integrity_check;")
            result = self.cursor.fetchone()[0]
            
            if result == "ok":
                logger.info("数据库完整性检查通过")
                return True
            else:
                logger.error(f"数据库完整性检查失败: {result}")
                return False
        except sqlite3.Error as e:
            logger.error(f"数据库完整性检查失败: {e}")
            return False
    
    def analyze_database(self):
        """分析数据库（更新统计信息）"""
        try:
            if not self.connection:
                if not self.connect():
                    return False
        
            logger.info("开始分析数据库...")
            self.cursor.execute("ANALYZE")
            self.connection.commit()
            logger.info("数据库分析完成")
            return True
        except sqlite3.Error as e:
            logger.error(f"数据库分析失败: {e}")
            return False
    
    def clean_all_old_data(self, task_days: int = 30, vector_days: int = 90):
        """清理所有旧数据"""
        logger.info("开始清理所有旧数据...")
        
        # 先备份数据库
        backup_file = self.backup_database()
        if not backup_file:
            logger.warning("备份失败，但仍继续清理")
        
        # 清理旧任务
        self.clean_old_tasks(task_days)
        
        # 清理旧向量
        self.clean_old_vectors(vector_days)
        
        # 优化数据库
        self.vacuum_database()
        
        logger.info("所有旧数据清理完成")
        return True
    
    def get_faiss_indices(self):
        """获取所有FAISS索引文件"""
        try:
            indices = []
            for file in FAISS_INDEX_DIR.iterdir():
                if file.suffix in ['.index', '.faiss']:
                    indices.append(file)
            return indices
        except Exception as e:
            logger.error(f"获取FAISS索引文件失败: {e}")
            return []
    
    def check_faiss_index(self, index_path: Path):
        """检查FAISS索引完整性"""
        try:
            logger.info(f"开始检查FAISS索引: {index_path}")
            
            # 尝试加载索引
            index = faiss.read_index(str(index_path))
            
            # 获取索引信息
            info = {
                'dimension': index.d,
                'ntotal': index.ntotal,
                'metric_type': index.metric_type
            }
            
            logger.info(f"FAISS索引检查通过: {info}")
            return True, info
        except Exception as e:
            logger.error(f"FAISS索引检查失败: {e}")
            return False, None
    
    def optimize_faiss_index(self, index_path: Path):
        """优化FAISS索引"""
        try:
            logger.info(f"开始优化FAISS索引: {index_path}")
            
            # 加载索引
            index = faiss.read_index(str(index_path))
            
            # 优化索引（根据索引类型执行不同的优化操作）
            if isinstance(index, faiss.IndexIVF):
                # IVF索引需要训练，但如果已经训练过，就执行重构
                if not index.is_trained:
                    logger.warning(f"FAISS索引 {index_path} 未训练，跳过优化")
                    return False
                else:
                    # 重构索引以提高搜索性能
                    index.reconstruct_n(0, index.ntotal)
            elif isinstance(index, faiss.IndexHNSW):
                # HNSW索引不需要特殊优化，只需要确保它是最新的
                pass
            
            # 保存优化后的索引
            faiss.write_index(index, str(index_path))
            logger.info(f"FAISS索引优化完成: {index_path}")
            return True
        except Exception as e:
            logger.error(f"FAISS索引优化失败: {e}")
            return False
    
    def backup_faiss_indices(self, backup_dir: Path = None):
        """备份所有FAISS索引"""
        if not backup_dir:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = BACKUP_DIR / f"faiss_backup_{timestamp}"
        
        try:
            # 确保备份目录存在
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # 获取所有FAISS索引
            indices = self.get_faiss_indices()
            
            for index_path in indices:
                # 复制索引文件
                backup_path = backup_dir / index_path.name
                shutil.copy2(str(index_path), str(backup_path))
                logger.info(f"FAISS索引备份成功: {backup_path}")
            
            logger.info(f"所有FAISS索引备份完成，共备份 {len(indices)} 个索引")
            return backup_dir
        except Exception as e:
            logger.error(f"FAISS索引备份失败: {e}")
            return None
    
    def optimize_all_faiss_indices(self):
        """优化所有FAISS索引"""
        try:
            # 获取所有FAISS索引
            indices = self.get_faiss_indices()
            
            for index_path in indices:
                self.optimize_faiss_index(index_path)
            
            logger.info(f"所有FAISS索引优化完成，共优化 {len(indices)} 个索引")
            return True
        except Exception as e:
            logger.error(f"优化所有FAISS索引失败: {e}")
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
            
            logger.info(f"FAISS索引检查完成: {valid_count}/{total_count} 个索引有效")
            return results
        except Exception as e:
            logger.error(f"检查所有FAISS索引失败: {e}")
            return []
    
    def maintain_faiss_indices(self):
        """维护所有FAISS索引：备份、检查、优化"""
        logger.info("开始FAISS索引维护...")
        
        # 备份所有FAISS索引
        backup_dir = self.backup_faiss_indices()
        if not backup_dir:
            logger.warning("FAISS索引备份失败，但仍继续维护")
        
        # 检查所有FAISS索引
        self.check_all_faiss_indices()
        
        # 优化所有FAISS索引
        self.optimize_all_faiss_indices()
        
        logger.info("FAISS索引维护完成")
        return True

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
    parser.add_argument("--database", type=Path, default=DATABASE_PATH, help="数据库文件路径")
    
    # FAISS索引维护参数
    parser.add_argument("--faiss-check", action="store_true", help="检查FAISS索引完整性")
    parser.add_argument("--faiss-optimize", action="store_true", help="优化FAISS索引")
    parser.add_argument("--faiss-backup", action="store_true", help="备份FAISS索引")
    parser.add_argument("--faiss-maintain", action="store_true", help="完整维护FAISS索引（备份、检查、优化）")
    
    args = parser.parse_args()
    
    # 创建数据库维护实例
    maintainer = DatabaseMaintainer(args.database)
    
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
        
        # 如果没有指定任何任务，显示帮助
        if not any([args.backup, args.vacuum, args.reindex, args.analyze, 
                   args.check, args.clean_tasks > 0, args.clean_vectors > 0, 
                   args.clean_all, args.info, args.faiss_check, 
                   args.faiss_optimize, args.faiss_backup, args.faiss_maintain]):
            parser.print_help()
            sys.exit(0)
            
    except KeyboardInterrupt:
        logger.info("用户中断操作")
    except Exception as e:
        logger.error(f"执行维护任务失败: {e}")
        sys.exit(1)
    finally:
        # 断开连接
        maintainer.disconnect()

if __name__ == "__main__":
    main()