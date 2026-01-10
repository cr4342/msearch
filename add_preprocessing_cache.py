#!/usr/bin/env python3
"""
在设计文档中添加预处理缓存和中间文件的设计说明
"""

import os

# 读取设计文档
file_path = "/data/project/msearch/docs/design.md"
with open(file_path, 'r') as f:
    content = f.read()

# 要添加的预处理缓存设计说明
preprocessing_cache_content = '''
## 预处理缓存与中间文件设计

系统在处理媒体文件过程中会产生大量中间文件和预处理结果，为了提高性能和避免重复处理，设计了完整的缓存管理机制。

### 1. 缓存目录结构

```
data/
├── cache/                  # 主缓存目录
│   ├── models/             # 模型缓存
│   ├── thumbnails/         # 缩略图缓存
│   ├── previews/           # 预览文件缓存
│   └── preprocessing/      # 预处理中间结果缓存
│       ├── frame_extraction/  # 视频帧提取结果
│       ├── audio_segments/    # 音频分段结果
│       ├── video_slices/      # 视频切片结果
│       └── text_embeddings/   # 文本向量化结果
```

### 2. 缓存管理组件

#### 2.1 PreprocessingCache 类

```python
class PreprocessingCache:
    """
    预处理缓存管理器
    
    负责管理预处理过程中产生的中间文件和缓存
    """
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.cache_dir = os.path.join(config['cache_dir'], 'preprocessing')
        self.max_cache_size = config.get('preprocessing', {}).get('max_cache_size', 5 * 1024 * 1024 * 1024)  # 5GB
        self.cache_ttl = config.get('preprocessing', {}).get('cache_ttl', 7 * 24 * 3600)  # 7天
    
    def get_cache_path(self, file_id: str, cache_type: str) -> str:
        """
        获取缓存文件路径
        
        Args:
            file_id: 文件ID（UUID v4）
            cache_type: 缓存类型（frame_extraction, audio_segments, etc.）
        
        Returns:
            缓存文件路径
        """
        cache_subdir = os.path.join(self.cache_dir, cache_type)
        os.makedirs(cache_subdir, exist_ok=True)
        return os.path.join(cache_subdir, f"{file_id}.json")
    
    def save_cache(self, file_id: str, cache_type: str, data: Any) -> bool:
        """
        保存缓存数据
        
        Args:
            file_id: 文件ID（UUID v4）
            cache_type: 缓存类型
            data: 缓存数据
        
        Returns:
            是否保存成功
        """
        try:
            cache_path = self.get_cache_path(file_id, cache_type)
            with open(cache_path, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
            return False
    
    def load_cache(self, file_id: str, cache_type: str) -> Optional[Any]:
        """
        加载缓存数据
        
        Args:
            file_id: 文件ID（UUID v4）
            cache_type: 缓存类型
        
        Returns:
            缓存数据
        """
        try:
            cache_path = self.get_cache_path(file_id, cache_type)
            if os.path.exists(cache_path):
                # 检查缓存是否过期
                if time.time() - os.path.getmtime(cache_path) > self.cache_ttl:
                    self.delete_cache(file_id, cache_type)
                    return None
                
                with open(cache_path, 'r') as f:
                    return json.load(f)
            return None
        except Exception as e:
            logger.error(f"Failed to load cache: {e}")
            return None
    
    def delete_cache(self, file_id: str, cache_type: Optional[str] = None) -> bool:
        """
        删除缓存数据
        
        Args:
            file_id: 文件ID（UUID v4）
            cache_type: 缓存类型（None表示删除所有类型）
        
        Returns:
            是否删除成功
        """
        try:
            if cache_type:
                # 删除特定类型的缓存
                cache_path = self.get_cache_path(file_id, cache_type)
                if os.path.exists(cache_path):
                    os.remove(cache_path)
            else:
                # 删除所有类型的缓存
                for cache_type in ['frame_extraction', 'audio_segments', 'video_slices', 'text_embeddings']:
                    cache_path = self.get_cache_path(file_id, cache_type)
                    if os.path.exists(cache_path):
                        os.remove(cache_path)
            return True
        except Exception as e:
            logger.error(f"Failed to delete cache: {e}")
            return False
    
    def cleanup_expired_cache(self) -> int:
        """
        清理过期缓存
        
        Returns:
            清理的缓存文件数量
        """
        try:
            count = 0
            current_time = time.time()
            
            for root, dirs, files in os.walk(self.cache_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    if current_time - os.path.getmtime(file_path) > self.cache_ttl:
                        os.remove(file_path)
                        count += 1
            
            return count
        except Exception as e:
            logger.error(f"Failed to cleanup expired cache: {e}")
            return 0
    
    def cleanup_by_size(self) -> int:
        """
        按大小清理缓存
        
        Returns:
            清理的缓存文件数量
        """
        try:
            # 计算当前缓存大小
            total_size = 0
            cache_files = []
            
            for root, dirs, files in os.walk(self.cache_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    file_size = os.path.getsize(file_path)
                    total_size += file_size
                    cache_files.append((file_path, file_size, os.path.getmtime(file_path)))
            
            # 如果缓存大小超过限制，按时间排序并删除最旧的文件
            count = 0
            if total_size > self.max_cache_size:
                # 按修改时间排序（最旧的先删除）
                cache_files.sort(key=lambda x: x[2])
                
                while total_size > self.max_cache_size and cache_files:
                    file_path, file_size, mtime = cache_files.pop(0)
                    os.remove(file_path)
                    total_size -= file_size
                    count += 1
            
            return count
        except Exception as e:
            logger.error(f"Failed to cleanup cache by size: {e}")
            return 0
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            缓存统计信息
        """
        try:
            total_size = 0
            file_count = 0
            type_counts = {}
            
            for root, dirs, files in os.walk(self.cache_dir):
                cache_type = os.path.basename(root)
                if cache_type == 'preprocessing':
                    continue
                
                type_counts[cache_type] = len(files)
                file_count += len(files)
                
                for file in files:
                    file_path = os.path.join(root, file)
                    total_size += os.path.getsize(file_path)
            
            return {
                'total_size': total_size,
                'file_count': file_count,
                'type_counts': type_counts,
                'max_cache_size': self.max_cache_size,
                'cache_ttl': self.cache_ttl
            }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {}
```

### 3. 缓存使用流程

#### 3.1 视频处理缓存流程

```python
def process_video(self, video_path: str) -> List[Dict[str, Any]]:
    """
    处理视频文件
    
    Args:
        video_path: 视频文件路径
    
    Returns:
        处理结果
    """
    # 1. 获取文件ID
    file_info = self.database_manager.get_or_create_file(video_path)
    file_id = file_info['id']
    
    # 2. 检查缓存
    cached_result = self.preprocessing_cache.load_cache(file_id, 'frame_extraction')
    if cached_result:
        logger.info(f"Using cached result for video {video_path}")
        return cached_result
    
    # 3. 执行实际处理
    # ... 视频处理逻辑 ...
    result = processed_segments
    
    # 4. 保存缓存
    self.preprocessing_cache.save_cache(file_id, 'frame_extraction', result)
    
    return result
```

### 4. 缓存清理策略

系统采用两种缓存清理策略：

1. **按时间清理**：
   - 默认缓存有效期为7天
   - 定期（每天）清理过期缓存
   - 支持手动触发清理

2. **按大小清理**：
   - 默认最大缓存大小为5GB
   - 当缓存大小超过限制时，按时间顺序删除最旧的文件
   - 支持配置最大缓存大小

3. **关联性清理**：
   - 当原始文件被删除时，自动清理相关缓存
   - 当原始文件被修改时，自动清理旧缓存
   - 定期验证缓存文件与原始文件的关联性

### 5. 中间文件管理

除了缓存文件外，系统还会产生一些临时中间文件，这些文件会被自动管理：

1. **临时文件目录**：`{cache_dir}/tmp/`
2. **自动清理**：程序退出时自动清理临时文件
3. **定期清理**：每小时清理一次临时文件
4. **最大生命周期**：临时文件最大生命周期为24小时

### 6. 缓存配置参数

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `cache_dir` | `data/cache` | 主缓存目录 |
| `preprocessing.max_cache_size` | `5GB` | 预处理缓存最大大小 |
| `preprocessing.cache_ttl` | `7天` | 预处理缓存有效期 |
| `preprocessing.cleanup_interval` | `3600` | 缓存清理间隔（秒） |
| `preprocessing.enable_cache` | `true` | 是否启用预处理缓存 |

### 7. 开发测试指南

1. **测试缓存功能**：
   - 测试缓存的保存和加载功能
   - 测试缓存过期清理功能
   - 测试缓存大小限制功能

2. **测试中间文件管理**：
   - 测试临时文件的自动清理
   - 测试程序异常退出时的临时文件清理

3. **性能测试**：
   - 测试缓存对处理性能的提升
   - 测试缓存清理对系统性能的影响

4. **边界测试**：
   - 测试空文件的缓存处理
   - 测试超大文件的缓存处理
   - 测试频繁修改文件的缓存处理

通过以上设计，系统实现了高效、可靠的预处理缓存和中间文件管理机制，能够显著提高系统性能，减少重复处理，同时保持系统的稳定性和可靠性。
'''

# 在合适的位置插入预处理缓存设计说明
# 我们在"4. 架构设计"之后插入
insert_position = content.find("## 4. 架构设计")
if insert_position != -1:
    # 找到"## 4. 架构设计"的结束位置
    architecture_end = content.find("## 5. ", insert_position)
    if architecture_end == -1:
        architecture_end = content.find("## 5", insert_position)
    if architecture_end == -1:
        # 如果找不到第5节，就在文件末尾插入
        new_content = content + preprocessing_cache_content
    else:
        # 在第5节之前插入
        new_content = content[:architecture_end] + preprocessing_cache_content + content[architecture_end:]
    
    # 保存修改后的文件
    with open(file_path, 'w') as f:
        f.write(new_content)
    
    print("预处理缓存设计说明已添加到设计文档中")
else:
    # 如果找不到"## 4. 架构设计"，就在文件末尾插入
    new_content = content + preprocessing_cache_content
    with open(file_path, 'w') as f:
        f.write(new_content)
    print("预处理缓存设计说明已添加到设计文档末尾")
