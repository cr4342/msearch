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

class DatabaseMaintainer:
    def __init__(self, database_path: Path):
        self.database_path = database_path
        self.connection = None
        self.cursor = None
        
        # 确保备份目录存在
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    
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
        
        # 如果没有指定任何任务，显示帮助
        if not any([args.backup, args.vacuum, args.reindex, args.analyze, 
                   args.check, args.clean_tasks > 0, args.clean_vectors > 0, 
                   args.clean_all, args.info]):
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