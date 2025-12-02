#!/usr/bin/env python3
# MSearch Qdrant向量数据库备份脚本
# 功能：备份和恢复Qdrant向量数据库

import argparse
import os
import sys
import logging
import datetime
import shutil
import requests
import json
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/qdrant_backup.log')
    ]
)
logger = logging.getLogger(__name__)

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
QDRANT_DATA_DIR = PROJECT_ROOT / 'data' / 'qdrant'
BACKUP_DIR = PROJECT_ROOT / 'data' / 'backups' / 'qdrant'

# Qdrant API配置
QDRANT_HOST = 'localhost'
QDRANT_PORT = 6333
QDRANT_API_BASE = f'http://{QDRANT_HOST}:{QDRANT_PORT}'

class QdrantBackupManager:
    def __init__(self, qdrant_data_dir: Path, backup_dir: Path):
        self.qdrant_data_dir = qdrant_data_dir
        self.backup_dir = backup_dir
        
        # 确保备份目录存在
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def is_qdrant_running(self):
        """检查Qdrant服务是否正在运行"""
        try:
            response = requests.get(f'{QDRANT_API_BASE}/health', timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def get_collections(self):
        """获取所有集合信息"""
        try:
            response = requests.get(f'{QDRANT_API_BASE}/collections')
            if response.status_code == 200:
                data = response.json()
                return data.get('result', {}).get('collections', [])
            else:
                logger.error(f"获取集合信息失败: {response.status_code} {response.text}")
                return []
        except requests.exceptions.RequestException as e:
            logger.error(f"获取集合信息失败: {e}")
            return []
    
    def backup_qdrant(self, backup_name: str = None):
        """备份Qdrant向量数据库"""
        if not backup_name:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"qdrant_backup_{timestamp}"
        
        backup_path = self.backup_dir / backup_name
        
        try:
            logger.info(f"开始备份Qdrant向量数据库...")
            logger.info(f"Qdrant数据目录: {self.qdrant_data_dir}")
            logger.info(f"备份目标目录: {backup_path}")
            
            # 检查Qdrant是否正在运行
            if self.is_qdrant_running():
                logger.warning("Qdrant服务正在运行，建议停止服务后再备份")
                logger.info("正在获取集合信息...")
                collections = self.get_collections()
                if collections:
                    logger.info(f"当前集合: {[col['name'] for col in collections]}")
            
            # 创建备份目录
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # 复制Qdrant数据文件
            if self.qdrant_data_dir.exists():
                # 复制所有文件和目录
                for item in self.qdrant_data_dir.iterdir():
                    dest = backup_path / item.name
                    if item.is_dir():
                        shutil.copytree(str(item), str(dest), dirs_exist_ok=True)
                    else:
                        shutil.copy2(str(item), str(dest))
                
                logger.info(f"Qdrant数据备份完成: {backup_path}")
                
                # 创建备份元数据
                metadata = {
                    'backup_time': datetime.datetime.now().isoformat(),
                    'qdrant_version': self._get_qdrant_version(),
                    'collections': [col['name'] for col in collections] if collections else [],
                    'backup_size': self._get_dir_size(backup_path),
                    'source_path': str(self.qdrant_data_dir)
                }
                
                with open(backup_path / 'backup_metadata.json', 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                logger.info(f"备份元数据创建完成")
                return backup_path
            else:
                logger.error(f"Qdrant数据目录不存在: {self.qdrant_data_dir}")
                return None
        except Exception as e:
            logger.error(f"Qdrant备份失败: {e}")
            # 清理失败的备份
            if backup_path.exists():
                shutil.rmtree(str(backup_path))
            return None
    
    def restore_qdrant(self, backup_name: str, force: bool = False):
        """恢复Qdrant向量数据库"""
        backup_path = self.backup_dir / backup_name
        
        try:
            logger.info(f"开始恢复Qdrant向量数据库...")
            logger.info(f"备份目录: {backup_path}")
            logger.info(f"恢复目标: {self.qdrant_data_dir}")
            
            # 检查备份目录是否存在
            if not backup_path.exists():
                logger.error(f"备份目录不存在: {backup_path}")
                return False
            
            # 检查Qdrant是否正在运行
            if self.is_qdrant_running():
                if not force:
                    logger.error("Qdrant服务正在运行，请停止服务后再恢复")
                    logger.info("使用 --force 参数强制恢复")
                    return False
                else:
                    logger.warning("强制恢复，Qdrant服务正在运行")
            
            # 检查元数据文件
            metadata_file = backup_path / 'backup_metadata.json'
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                logger.info(f"备份元数据:")
                logger.info(f"  备份时间: {metadata.get('backup_time')}")
                logger.info(f"  Qdrant版本: {metadata.get('qdrant_version')}")
                logger.info(f"  集合数量: {len(metadata.get('collections', []))}")
                logger.info(f"  备份大小: {self._format_size(metadata.get('backup_size', 0))}")
            
            # 清理目标目录
            if self.qdrant_data_dir.exists():
                logger.info(f"清理目标目录: {self.qdrant_data_dir}")
                for item in self.qdrant_data_dir.iterdir():
                    if item.is_dir():
                        shutil.rmtree(str(item))
                    else:
                        item.unlink()
            else:
                self.qdrant_data_dir.mkdir(parents=True, exist_ok=True)
            
            # 复制备份文件到目标目录
            for item in backup_path.iterdir():
                if item.name == 'backup_metadata.json':
                    continue  # 跳过元数据文件
                
                dest = self.qdrant_data_dir / item.name
                if item.is_dir():
                    shutil.copytree(str(item), str(dest), dirs_exist_ok=True)
                else:
                    shutil.copy2(str(item), str(dest))
            
            logger.info(f"Qdrant数据恢复完成")
            return True
        except Exception as e:
            logger.error(f"Qdrant恢复失败: {e}")
            return False
    
    def list_backups(self):
        """列出所有备份"""
        try:
            logger.info(f"列出所有Qdrant备份...")
            logger.info(f"备份目录: {self.backup_dir}")
            
            if not self.backup_dir.exists():
                logger.info("备份目录不存在")
                return []
            
            backups = []
            for item in self.backup_dir.iterdir():
                if item.is_dir():
                    backup_info = {
                        'name': item.name,
                        'path': str(item),
                        'size': self._get_dir_size(item),
                        'created_at': datetime.datetime.fromtimestamp(item.stat().st_ctime).isoformat()
                    }
                    
                    # 检查元数据文件
                    metadata_file = item / 'backup_metadata.json'
                    if metadata_file.exists():
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)
                        backup_info.update(metadata)
                    
                    backups.append(backup_info)
            
            # 按创建时间排序
            backups.sort(key=lambda x: x.get('backup_time', x['created_at']), reverse=True)
            
            # 显示备份列表
            if backups:
                logger.info(f"找到 {len(backups)} 个备份:")
                for i, backup in enumerate(backups, 1):
                    size_str = self._format_size(backup['size'])
                    logger.info(f"  {i}. {backup['name']} ({size_str}) - {backup.get('backup_time', backup['created_at'])}")
                    if 'collections' in backup:
                        logger.info(f"     集合: {', '.join(backup['collections'])}")
            else:
                logger.info("没有找到备份")
            
            return backups
        except Exception as e:
            logger.error(f"列出备份失败: {e}")
            return []
    
    def delete_backup(self, backup_name: str):
        """删除指定备份"""
        backup_path = self.backup_dir / backup_name
        
        try:
            if backup_path.exists():
                logger.info(f"删除备份: {backup_path}")
                shutil.rmtree(str(backup_path))
                logger.info(f"备份删除成功")
                return True
            else:
                logger.error(f"备份不存在: {backup_path}")
                return False
        except Exception as e:
            logger.error(f"删除备份失败: {e}")
            return False
    
    def _get_qdrant_version(self):
        """获取Qdrant版本"""
        try:
            response = requests.get(f'{QDRANT_API_BASE}/')
            if response.status_code == 200:
                data = response.json()
                return data.get('version', 'unknown')
            else:
                return 'unknown'
        except requests.exceptions.RequestException:
            return 'unknown'
    
    def _get_dir_size(self, dir_path: Path):
        """获取目录大小"""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(str(dir_path)):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total_size += os.path.getsize(fp)
        return total_size
    
    def _format_size(self, size_bytes: int):
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"

def main():
    parser = argparse.ArgumentParser(description="MSearch Qdrant向量数据库备份脚本")
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 备份命令
    backup_parser = subparsers.add_parser('backup', help='备份Qdrant数据库')
    backup_parser.add_argument('--name', type=str, help='备份名称')
    
    # 恢复命令
    restore_parser = subparsers.add_parser('restore', help='恢复Qdrant数据库')
    restore_parser.add_argument('backup_name', type=str, help='备份名称')
    restore_parser.add_argument('--force', action='store_true', help='强制恢复（即使服务正在运行）')
    
    # 列出命令
    list_parser = subparsers.add_parser('list', help='列出所有备份')
    
    # 删除命令
    delete_parser = subparsers.add_parser('delete', help='删除指定备份')
    delete_parser.add_argument('backup_name', type=str, help='备份名称')
    
    # 解析参数
    args = parser.parse_args()
    
    # 创建备份管理器实例
    backup_manager = QdrantBackupManager(QDRANT_DATA_DIR, BACKUP_DIR)
    
    try:
        if args.command == 'backup':
            backup_manager.backup_qdrant(args.name)
        elif args.command == 'restore':
            backup_manager.restore_qdrant(args.backup_name, args.force)
        elif args.command == 'list':
            backup_manager.list_backups()
        elif args.command == 'delete':
            backup_manager.delete_backup(args.backup_name)
        else:
            parser.print_help()
            sys.exit(0)
    except KeyboardInterrupt:
        logger.info("用户中断操作")
    except Exception as e:
        logger.error(f"执行命令失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()