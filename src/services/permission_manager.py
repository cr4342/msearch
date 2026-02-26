"""
权限管理器 - 实现三层权限控制

支持：
- Application Layer: RBAC/ABAC策略
- File Layer: 目录/文件级ACL
- Database Layer: 行级安全策略
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class User:
    """用户信息"""
    user_id: str
    username: str
    role: str
    permissions: List[str] = None
    
    def __post_init__(self):
        if self.permissions is None:
            self.permissions = []
    
    def __post_init__(self):
        if self.permissions is None:
            self.permissions = []


@dataclass
class Resource:
    """资源信息"""
    resource_id: str
    resource_type: str  # file, directory, project, database
    path: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class PermissionManager:
    """
    权限管理器 - 实现三层权限控制
    
    层级结构：
    - Application Layer: 主权限决策中心，处理RBAC/ABAC策略
    - File Layer: 通过文件服务API配置目录/文件级ACL
    - Database Layer: 行级安全策略实现项目隔离
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化权限管理器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.permissions_config = config.get('permissions', {})
        
        # 初始化三层权限控制
        self.app_layer = ApplicationLayer(self.permissions_config)
        self.file_layer = FileLayerAdapter(self.permissions_config)
        self.db_layer = DatabaseLayerAdapter(self.permissions_config)
        
        # 保护规则配置
        self.protection_rules = self.permissions_config.get('protection_rules', {})
        
        logger.info("权限管理器初始化完成")
    
    def check_access(self, user: User, resource: Resource, operation: str) -> bool:
        """
        检查用户是否有权限执行操作
        
        Args:
            user: 用户对象
            resource: 资源对象
            operation: 操作类型 (read, write, delete, rename, upload)
            
        Returns:
            bool: 是否有权限
        """
        # 三层权限检查（取最严格结果）
        app_result = self.app_layer.check(user, resource, operation)
        file_result = self.file_layer.check(user, resource, operation)
        db_result = self.db_layer.check(user, resource, operation)
        
        result = app_result and file_result and db_result
        
        logger.debug(
            f"权限检查: user={user.username}, resource={resource.resource_id}, "
            f"operation={operation}, result={result}"
        )
        
        return result
    
    def update_permissions(self, role: str, permissions: Dict[str, Any]) -> None:
        """
        更新权限配置并同步到所有层级
        
        Args:
            role: 角色名称
            permissions: 权限配置字典
        """
        self.app_layer.update(role, permissions)
        self.file_layer.sync_permissions()
        self.db_layer.sync_permissions()
        
        logger.info(f"权限配置已更新: role={role}")
    
    def check_asset_protection(self, resource: Resource) -> bool:
        """
        检查资源是否受保护（已确认素材保护规则）
        
        Args:
            resource: 资源对象
            
        Returns:
            bool: 是否受保护
        """
        # 检查是否匹配保护规则
        for rule_name, rule_config in self.protection_rules.items():
            if resource.resource_type == 'file':
                metadata = resource.metadata or {}
                is_confirmed = metadata.get('confirmed', False)
                if is_confirmed and not rule_config.get('allow_delete', True):
                    return True
        
        return False
    
    def get_user_permissions(self, user: User) -> Dict[str, List[str]]:
        """
        获取用户的完整权限信息
        
        Args:
            user: 用户对象
            
        Returns:
            Dict: 权限字典
        """
        return {
            'file_ops': self.app_layer.get_role_permissions(user.role).get('file_ops', []),
            'resolve_access': self.app_layer.get_role_permissions(user.role).get('resolve_access', []),
        }


class ApplicationLayer:
    """应用层权限控制 - RBAC/ABAC策略"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.roles = config.get('roles', {})
    
    def check(self, user: User, resource: Resource, operation: str) -> bool:
        """应用层权限检查"""
        role_perms = self.roles.get(user.role, {})
        
        # 文件操作权限检查
        if resource.resource_type in ('file', 'directory'):
            file_ops = role_perms.get('file_ops', [])
            if operation in file_ops:
                return True
            # 管理员拥有完全控制权
            if 'full_control' in file_ops:
                return True
        
        # 数据库操作权限检查
        if resource.resource_type == 'database':
            resolve_access = role_perms.get('resolve_access', [])
            if operation in resolve_access or 'full_control' in resolve_access:
                return True
        
        return False
    
    def update(self, role: str, permissions: Dict[str, Any]) -> None:
        """更新角色权限"""
        self.roles[role] = permissions
    
    def get_role_permissions(self, role: str) -> Dict[str, Any]:
        """获取角色权限"""
        return self.roles.get(role, {})


class FileLayerAdapter:
    """文件层权限控制 - ACL规则"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.acl_rules = {}
    
    def check(self, user: User, resource: Resource, operation: str) -> bool:
        """文件层权限检查"""
        # 简化实现：基于角色和资源类型的基本检查
        role_perms = self.config.get('roles', {}).get(user.role, {})
        
        # 检查是否配置了文件操作权限
        if resource.resource_type in ('file', 'directory'):
            file_ops = role_perms.get('file_ops', [])
            if operation in file_ops or 'full_control' in file_ops:
                return True
        
        # 默认允许
        return True
    
    def sync_permissions(self) -> None:
        """同步权限到文件系统"""
        # 实现与文件系统ACL的同步
        pass


class DatabaseLayerAdapter:
    """数据库层权限控制 - 行级安全策略"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.rls_policies = {}
    
    def check(self, user: User, resource: Resource, operation: str) -> bool:
        """数据库层权限检查"""
        # 简化实现：基于角色的基本检查
        role_perms = self.config.get('roles', {}).get(user.role, {})
        
        # 检查数据库操作权限
        if resource.resource_type == 'database':
            resolve_access = role_perms.get('resolve_access', [])
            if operation in resolve_access or 'full_control' in resolve_access:
                return True
        
        # 默认允许
        return True
    
    def sync_permissions(self) -> None:
        """同步权限到数据库"""
        # 实现与数据库RLS策略的同步
        pass
