"""
UI配置管理器
处理UI配置的持久化和加载，支持用户自定义配置
"""

import logging
from typing import Dict, Any, Optional, List
import json
import os
from pathlib import Path
import sqlite3
from contextlib import contextmanager
from datetime import datetime

from src.core.config_manager import get_config_manager


logger = logging.getLogger(__name__)


class UIConfigManager:
    """UI配置管理器"""
    
    def __init__(self, db_path: str = None, config_manager=None):
        self.config_manager = config_manager or get_config_manager()
        
        # 使用配置中的数据库路径，或使用默认路径
        if db_path:
            self.db_path = db_path
        else:
            data_dir = self.config_manager.get("system.data_dir", "./data")
            self.db_path = os.path.join(data_dir, "ui_config.db")
        
        # 确保目录存在
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # 初始化数据库
        self._init_database()
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"UI配置管理器初始化完成，数据库路径: {self.db_path}")
    
    def _init_database(self):
        """初始化数据库表"""
        with self._get_db_connection() as conn:
            # 创建UI配置表
            conn.execute('''
                CREATE TABLE IF NOT EXISTS ui_config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    config_key TEXT UNIQUE NOT NULL,
                    config_value TEXT NOT NULL,
                    config_type TEXT DEFAULT 'string',
                    user_id TEXT DEFAULT 'default',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    description TEXT
                )
            ''')
            
            # 创建监控目录配置表
            conn.execute('''
                CREATE TABLE IF NOT EXISTS monitored_directories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    directory_path TEXT UNIQUE NOT NULL,
                    priority INTEGER DEFAULT 0,
                    enabled INTEGER DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            ''')
            
            # 创建UI布局配置表
            conn.execute('''
                CREATE TABLE IF NOT EXISTS ui_layout (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    layout_type TEXT NOT NULL,
                    layout_config TEXT NOT NULL,
                    user_id TEXT DEFAULT 'default',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            ''')
            
            # 创建索引
            conn.execute('CREATE INDEX IF NOT EXISTS idx_config_key ON ui_config(config_key)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON ui_config(user_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_directory_path ON monitored_directories(directory_path)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_layout_type ON ui_layout(layout_type)')
            
            conn.commit()
    
    @contextmanager
    def _get_db_connection(self):
        """获取数据库连接的上下文管理器"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 使结果可以通过列名访问
        try:
            yield conn
        finally:
            conn.close()
    
    def set_config(self, key: str, value: Any, config_type: str = 'string', 
                   user_id: str = 'default', description: str = None) -> bool:
        """
        设置UI配置项
        
        Args:
            key: 配置键
            value: 配置值
            config_type: 配置类型（string, integer, float, boolean, json）
            user_id: 用户ID
            description: 描述
            
        Returns:
            是否设置成功
        """
        try:
            # 根据类型序列化值
            if config_type == 'json':
                config_value = json.dumps(value, ensure_ascii=False)
            else:
                config_value = str(value)
            
            with self._get_db_connection() as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO ui_config 
                    (config_key, config_value, config_type, user_id, created_at, updated_at, description)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    key, config_value, config_type, user_id,
                    datetime.now().isoformat(), datetime.now().isoformat(), description
                ))
                conn.commit()
                
                self.logger.debug(f"设置UI配置: {key} = {value} (用户: {user_id})")
                return True
                
        except Exception as e:
            self.logger.error(f"设置UI配置失败 {key}: {e}")
            return False
    
    def get_config(self, key: str, default: Any = None, user_id: str = 'default') -> Any:
        """
        获取UI配置项
        
        Args:
            key: 配置键
            default: 默认值
            user_id: 用户ID
            
        Returns:
            配置值，如果不存在则返回默认值
        """
        try:
            with self._get_db_connection() as conn:
                row = conn.execute('''
                    SELECT config_value, config_type FROM ui_config 
                    WHERE config_key = ? AND user_id = ?
                ''', (key, user_id)).fetchone()
                
                if row:
                    config_value = row['config_value']
                    config_type = row['config_type']
                    
                    # 根据类型反序列化值
                    if config_type == 'integer':
                        return int(config_value)
                    elif config_type == 'float':
                        return float(config_value)
                    elif config_type == 'boolean':
                        return config_value.lower() == 'true'
                    elif config_type == 'json':
                        return json.loads(config_value)
                    else:
                        return config_value
                else:
                    return default
                    
        except Exception as e:
            self.logger.error(f"获取UI配置失败 {key}: {e}")
            return default
    
    def get_all_configs(self, user_id: str = 'default') -> Dict[str, Any]:
        """
        获取用户的所有UI配置
        
        Args:
            user_id: 用户ID
            
        Returns:
            配置字典
        """
        try:
            with self._get_db_connection() as conn:
                rows = conn.execute('''
                    SELECT config_key, config_value, config_type FROM ui_config 
                    WHERE user_id = ? ORDER BY config_key
                ''', (user_id,)).fetchall()
                
                configs = {}
                for row in rows:
                    key = row['config_key']
                    value = row['config_value']
                    config_type = row['config_type']
                    
                    # 根据类型反序列化值
                    if config_type == 'integer':
                        configs[key] = int(value)
                    elif config_type == 'float':
                        configs[key] = float(value)
                    elif config_type == 'boolean':
                        configs[key] = value.lower() == 'true'
                    elif config_type == 'json':
                        configs[key] = json.loads(value)
                    else:
                        configs[key] = value
                
                return configs
                
        except Exception as e:
            self.logger.error(f"获取所有UI配置失败: {e}")
            return {}
    
    def delete_config(self, key: str, user_id: str = 'default') -> bool:
        """
        删除UI配置项
        
        Args:
            key: 配置键
            user_id: 用户ID
            
        Returns:
            是否删除成功
        """
        try:
            with self._get_db_connection() as conn:
                conn.execute('DELETE FROM ui_config WHERE config_key = ? AND user_id = ?', (key, user_id))
                conn.commit()
                
                if conn.total_changes > 0:
                    self.logger.debug(f"删除UI配置: {key} (用户: {user_id})")
                    return True
                else:
                    self.logger.warning(f"未找到UI配置: {key} (用户: {user_id})")
                    return False
                    
        except Exception as e:
            self.logger.error(f"删除UI配置失败 {key}: {e}")
            return False
    
    def add_monitored_directory(self, directory_path: str, priority: int = 0, enabled: bool = True) -> bool:
        """
        添加监控目录
        
        Args:
            directory_path: 目录路径
            priority: 优先级
            enabled: 是否启用
            
        Returns:
            是否添加成功
        """
        try:
            with self._get_db_connection() as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO monitored_directories 
                    (directory_path, priority, enabled, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    directory_path, priority, int(enabled),
                    datetime.now().isoformat(), datetime.now().isoformat()
                ))
                conn.commit()
                
                self.logger.info(f"添加监控目录: {directory_path}")
                return True
                
        except Exception as e:
            self.logger.error(f"添加监控目录失败 {directory_path}: {e}")
            return False
    
    def get_monitored_directories(self) -> List[Dict[str, Any]]:
        """
        获取所有监控目录
        
        Returns:
            监控目录列表
        """
        try:
            with self._get_db_connection() as conn:
                rows = conn.execute('''
                    SELECT directory_path, priority, enabled, created_at, updated_at 
                    FROM monitored_directories 
                    ORDER BY priority ASC, directory_path
                ''').fetchall()
                
                directories = []
                for row in rows:
                    directories.append({
                        'directory_path': row['directory_path'],
                        'priority': row['priority'],
                        'enabled': bool(row['enabled']),
                        'created_at': row['created_at'],
                        'updated_at': row['updated_at']
                    })
                
                return directories
                
        except Exception as e:
            self.logger.error(f"获取监控目录失败: {e}")
            return []
    
    def update_monitored_directory(self, directory_path: str, priority: int = None, enabled: bool = None) -> bool:
        """
        更新监控目录
        
        Args:
            directory_path: 目录路径
            priority: 优先级
            enabled: 是否启用
            
        Returns:
            是否更新成功
        """
        try:
            with self._get_db_connection() as conn:
                update_fields = []
                update_values = []
                
                if priority is not None:
                    update_fields.append("priority = ?")
                    update_values.append(priority)
                
                if enabled is not None:
                    update_fields.append("enabled = ?")
                    update_values.append(int(enabled))
                
                update_fields.append("updated_at = ?")
                update_values.append(datetime.now().isoformat())
                
                if update_fields:
                    query = f"UPDATE monitored_directories SET {', '.join(update_fields)} WHERE directory_path = ?"
                    update_values.append(directory_path)
                    
                    conn.execute(query, update_values)
                    conn.commit()
                    
                    if conn.total_changes > 0:
                        self.logger.debug(f"更新监控目录: {directory_path}")
                        return True
                    else:
                        self.logger.warning(f"未找到监控目录: {directory_path}")
                        return False
                else:
                    return True  # 没有需要更新的字段
                    
        except Exception as e:
            self.logger.error(f"更新监控目录失败 {directory_path}: {e}")
            return False
    
    def remove_monitored_directory(self, directory_path: str) -> bool:
        """
        移除监控目录
        
        Args:
            directory_path: 目录路径
            
        Returns:
            是否移除成功
        """
        try:
            with self._get_db_connection() as conn:
                conn.execute('DELETE FROM monitored_directories WHERE directory_path = ?', (directory_path,))
                conn.commit()
                
                if conn.total_changes > 0:
                    self.logger.info(f"移除监控目录: {directory_path}")
                    return True
                else:
                    self.logger.warning(f"未找到监控目录: {directory_path}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"移除监控目录失败 {directory_path}: {e}")
            return False
    
    def set_ui_layout(self, layout_type: str, layout_config: Dict[str, Any], user_id: str = 'default') -> bool:
        """
        设置UI布局配置
        
        Args:
            layout_type: 布局类型
            layout_config: 布局配置
            user_id: 用户ID
            
        Returns:
            是否设置成功
        """
        try:
            config_json = json.dumps(layout_config, ensure_ascii=False)
            
            with self._get_db_connection() as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO ui_layout 
                    (layout_type, layout_config, user_id, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    layout_type, config_json, user_id,
                    datetime.now().isoformat(), datetime.now().isoformat()
                ))
                conn.commit()
                
                self.logger.debug(f"设置UI布局: {layout_type} (用户: {user_id})")
                return True
                
        except Exception as e:
            self.logger.error(f"设置UI布局失败 {layout_type}: {e}")
            return False
    
    def get_ui_layout(self, layout_type: str, user_id: str = 'default') -> Optional[Dict[str, Any]]:
        """
        获取UI布局配置
        
        Args:
            layout_type: 布局类型
            user_id: 用户ID
            
        Returns:
            布局配置，如果不存在则返回None
        """
        try:
            with self._get_db_connection() as conn:
                row = conn.execute('''
                    SELECT layout_config FROM ui_layout 
                    WHERE layout_type = ? AND user_id = ?
                ''', (layout_type, user_id)).fetchone()
                
                if row:
                    return json.loads(row['layout_config'])
                else:
                    return None
                    
        except Exception as e:
            self.logger.error(f"获取UI布局失败 {layout_type}: {e}")
            return None
    
    def validate_config(self, key: str, value: Any) -> tuple[bool, str]:
        """
        验证配置值的有效性
        
        Args:
            key: 配置键
            value: 配置值
            
        Returns:
            (是否有效, 错误信息)
        """
        # 验证监控目录路径
        if key.startswith('monitoring.directory.'):
            if isinstance(value, str):
                path = Path(value)
                if not path.exists():
                    return False, f"目录不存在: {value}"
                if not path.is_dir():
                    return False, f"路径不是目录: {value}"
                return True, ""
        
        # 验证数值范围
        if key in ['ui.thumbnail_size', 'ui.grid_spacing', 'ui.max_results']:
            if isinstance(value, (int, float)):
                if value < 1:
                    return False, f"数值不能小于1: {key} = {value}"
                if value > 10000:
                    return False, f"数值不能大于10000: {key} = {value}"
                return True, ""
        
        # 验证布尔值
        if key in ['ui.show_thumbnails', 'ui.auto_refresh', 'ui.enable_notifications']:
            if not isinstance(value, bool):
                return False, f"配置项 {key} 必须是布尔值"
            return True, ""
        
        # 默认验证通过
        return True, ""
    
    def import_configs(self, configs: Dict[str, Any], user_id: str = 'default') -> bool:
        """
        导入配置
        
        Args:
            configs: 配置字典
            user_id: 用户ID
            
        Returns:
            是否导入成功
        """
        try:
            for key, value in configs.items():
                # 验证配置
                is_valid, error_msg = self.validate_config(key, value)
                if not is_valid:
                    self.logger.warning(f"配置验证失败 {key}: {error_msg}")
                    continue
                
                # 确定配置类型
                if isinstance(value, bool):
                    config_type = 'boolean'
                elif isinstance(value, int):
                    config_type = 'integer'
                elif isinstance(value, float):
                    config_type = 'float'
                elif isinstance(value, (dict, list)):
                    config_type = 'json'
                else:
                    config_type = 'string'
                
                # 保存配置
                self.set_config(key, value, config_type, user_id)
            
            self.logger.info(f"导入配置完成 (用户: {user_id})")
            return True
            
        except Exception as e:
            self.logger.error(f"导入配置失败: {e}")
            return False
    
    def export_configs(self, user_id: str = 'default') -> Dict[str, Any]:
        """
        导出配置
        
        Args:
            user_id: 用户ID
            
        Returns:
            配置字典
        """
        return self.get_all_configs(user_id)
    
    def reset_user_configs(self, user_id: str = 'default') -> bool:
        """
        重置用户配置
        
        Args:
            user_id: 用户ID
            
        Returns:
            是否重置成功
        """
        try:
            with self._get_db_connection() as conn:
                conn.execute('DELETE FROM ui_config WHERE user_id = ?', (user_id,))
                conn.execute('DELETE FROM ui_layout WHERE user_id = ?', (user_id,))
                conn.commit()
                
                self.logger.info(f"重置用户配置: {user_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"重置用户配置失败: {e}")
            return False
    
    def get_config_history(self, key: str, user_id: str = 'default', limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取配置历史（此功能需要额外的日志表，这里简化实现）
        注意：当前实现没有配置历史表，返回当前值作为示例
        
        Args:
            key: 配置键
            user_id: 用户ID
            limit: 限制数量
            
        Returns:
            配置历史列表
        """
        # 简化实现：返回当前配置值
        current_value = self.get_config(key, user_id=user_id)
        if current_value is not None:
            return [{
                'timestamp': datetime.now().isoformat(),
                'value': current_value,
                'action': 'current'
            }]
        return []


# 全局UI配置管理器实例
_ui_config_manager = None


def get_ui_config_manager() -> UIConfigManager:
    """获取全局UI配置管理器实例"""
    global _ui_config_manager
    
    if _ui_config_manager is None:
        _ui_config_manager = UIConfigManager()
    
    return _ui_config_manager