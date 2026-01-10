#!/usr/bin/env python3
"""
修复设计文档中的预览命名策略
"""

import os

# 读取设计文档
file_path = "/data/project/msearch/docs/design.md"
with open(file_path, 'r') as f:
    content = f.read()

# 要替换的内容
old_content = '''**基于文件哈希的预览命名策略**：
```python
def get_preview_filename(self, file_hash: str, preview_type: str = "thumbnail") -> str:
    """
    生成基于文件哈希的预览文件名
    
    使用文件SHA256哈希作为文件名，避免因路径/文件名变更导致重复生成
    
    Args:
        file_hash: 文件SHA256哈希
        preview_type: 预览类型
    
    Returns:
        预览文件名
    """
    # 使用文件哈希的前16位作为文件名
    hash_prefix = file_hash[:16]
    
    # 根据预览类型选择扩展名
    ext_map = {
        'thumbnail': '.jpg',
        'small': '.jpg',
        'medium': '.jpg',
        'large': '.jpg',
        'gif': '.gif',
        'video': '.mp4',
        'waveform': '.png'
    }
    
    ext = ext_map.get(preview_type, '.jpg')
    return f"{{hash_prefix}}{{ext}}"


def get_preview_path_by_hash(self, file_hash: str, preview_type: str = "thumbnail") -> str:
    """
    获取基于文件哈希的预览文件路径
    
    Args:
        file_hash: 文件SHA256哈希
        preview_type: 预览类型
    
    Returns:
        预览文件完整路径
    """
    filename = self.get_preview_filename(file_hash, preview_type)
    return os.path.join(self.config['cache_dir'], preview_type, filename)


def has_preview_by_hash(self, file_hash: str, preview_type: str = "thumbnail") -> bool:
    """
    检查是否存在基于文件哈希的预览
    
    Args:
        file_hash: 文件SHA256哈希
        preview_type: 预览类型
    
    Returns:
        是否存在预览
    """
    preview_path = self.get_preview_path_by_hash(file_hash, preview_type)
    return os.path.exists(preview_path)
```

**预览命名优势**：
- **避免重复生成**：相同内容的文件共享同一个预览文件
- **路径无关性**：文件移动或重命名不影响预览文件'''

new_content = '''**基于UUID的预览命名策略**：
```python
def get_preview_filename(self, file_id: str, preview_type: str = "thumbnail") -> str:
    """
    生成基于UUID的预览文件名
    
    使用文件ID（UUID v4）作为文件名，确保唯一性
    
    Args:
        file_id: 文件ID（UUID v4）
        preview_type: 预览类型
    
    Returns:
        预览文件名
    """
    # 根据预览类型选择扩展名
    ext_map = {
        'thumbnail': '.jpg',
        'small': '.jpg',
        'medium': '.jpg',
        'large': '.jpg',
        'gif': '.gif',
        'video': '.mp4',
        'waveform': '.png'
    }
    
    ext = ext_map.get(preview_type, '.jpg')
    return f"{{file_id}}{{ext}}"


def get_preview_path(self, file_id: str, preview_type: str = "thumbnail") -> str:
    """
    获取基于UUID的预览文件路径
    
    Args:
        file_id: 文件ID（UUID v4）
        preview_type: 预览类型
    
    Returns:
        预览文件完整路径
    """
    filename = self.get_preview_filename(file_id, preview_type)
    return os.path.join(self.config['cache_dir'], preview_type, filename)


def has_preview(self, file_id: str, preview_type: str = "thumbnail") -> bool:
    """
    检查是否存在基于UUID的预览
    
    Args:
        file_id: 文件ID（UUID v4）
        preview_type: 预览类型
    
    Returns:
        是否存在预览
    """
    preview_path = self.get_preview_path(file_id, preview_type)
    return os.path.exists(preview_path)


def get_preview_path_by_file_path(self, file_path: str, preview_type: str = "thumbnail") -> Optional[str]:
    """
    根据文件路径获取预览路径
    
    Args:
        file_path: 文件路径
        preview_type: 预览类型
    
    Returns:
        预览文件路径
    """
    # 通过文件路径获取文件ID
    file_info = self.database_manager.get_file_by_path(file_path)
    if file_info:
        return self.get_preview_path(file_info['id'], preview_type)
    return None
```

**预览命名优势**：
- **唯一性**：使用UUID确保文件名唯一
- **一致性**：与系统其他文件ID生成机制保持一致
- **可追溯性**：通过文件名可直接关联到原始文件
- **安全性**：避免因文件哈希泄露导致的安全问题
- **扩展性**：便于未来扩展缓存管理功能

**预览缓存管理**：
- 缓存目录：`{cache_dir}/{preview_type}/`
- 缓存格式：根据预览类型自动选择
- 缓存大小：根据预览类型自动调整
- 缓存清理：支持按时间（30天）和大小自动清理
- 缓存验证：定期验证缓存文件与原始文件的关联性'''

# 替换内容
new_content = content.replace(old_content, new_content)

# 保存修改后的文件
with open(file_path, 'w') as f:
    f.write(new_content)

print("预览命名策略已修复")
