# 数据库 Schema 文档

> **文档导航**: [需求文档](requirements.md) | [设计文档](design.md) | [开发计划](development_plan.md) | [API文档](api_documentation.md) | [测试策略](test_strategy.md) | [用户手册](user_manual.md) | [安装指南](INSTALL.md)

## 1. 数据库概述

MSearch 使用 SQLite 作为主要数据库，用于存储文件元数据、处理任务、媒体片段和向量索引信息。SQLite 数据库文件位于 `data/database/msearch.db`。

### 1.1 设计原则

- **轻量级**: 使用 SQLite 避免复杂的数据库部署
- **高性能**: 合理设计索引，优化查询性能
- **数据完整性**: 使用外键约束维护数据关系
- **可扩展性**: 模块化设计，支持未来扩展
- **事务支持**: 确保数据操作的原子性

### 1.2 核心表结构

| 表名 | 主要功能 | 关联表 |
|------|----------|--------|
| files | 存储文件基本信息 | tasks, media_segments, vectors |
| tasks | 存储处理任务信息 | files |
| media_segments | 存储媒体片段信息 | files |
| vectors | 存储向量数据 | files, tasks |
| video_segments | 存储视频片段信息 | - |

## 2. 表结构详细说明

### 2.1 files 表

**功能**: 存储文件的基本信息和处理状态

| 字段名 | 数据类型 | 约束 | 默认值 | 描述 |
|--------|----------|------|--------|------|
| id | TEXT | PRIMARY KEY | - | 文件唯一标识符（UUID） |
| file_path | TEXT | UNIQUE NOT NULL | - | 文件完整路径 |
| file_name | TEXT | NOT NULL | - | 文件名（不含路径） |
| file_type | TEXT | NOT NULL | - | 文件类型（image/video/audio） |
| file_size | INTEGER | NOT NULL | - | 文件大小（字节） |
| file_hash | TEXT | NOT NULL | - | 文件哈希值（用于检测文件变化） |
| created_at | REAL | NOT NULL | - | 文件创建时间（Unix时间戳） |
| modified_at | REAL | NOT NULL | - | 文件修改时间（Unix时间戳） |
| processed_at | REAL | - | - | 文件处理完成时间（Unix时间戳） |
| status | TEXT | - | 'pending' | 文件处理状态（pending/processing/completed/failed） |
| can_delete | BOOLEAN | - | 0 | 是否可以删除（0=不可删除, 1=可删除） |

**索引**: 
- idx_files_path (file_path)
- idx_files_status (status)

### 2.2 tasks 表

**功能**: 存储文件处理任务的详细信息

| 字段名 | 数据类型 | 约束 | 默认值 | 描述 |
|--------|----------|------|--------|------|
| id | TEXT | PRIMARY KEY | - | 任务唯一标识符（UUID） |
| file_id | TEXT | NOT NULL, FOREIGN KEY | - | 关联的文件ID |
| task_type | TEXT | NOT NULL | - | 任务类型（preprocess/embedding/indexing） |
| status | TEXT | - | 'pending' | 任务状态（pending/processing/completed/failed/retry） |
| progress | INTEGER | - | 0 | 任务进度（0-100） |
| error_message | TEXT | - | - | 错误信息（如果任务失败） |
| created_at | REAL | NOT NULL | - | 任务创建时间（Unix时间戳） |
| updated_at | REAL | NOT NULL | - | 任务更新时间（Unix时间戳） |
| retry_count | INTEGER | - | 0 | 当前重试次数 |
| max_retry_attempts | INTEGER | - | 3 | 最大重试次数 |
| retry_at | REAL | - | - | 下次重试时间（Unix时间戳） |

**索引**: 
- idx_tasks_status (status)
- idx_tasks_file_id (file_id)

### 2.3 media_segments 表

**功能**: 存储媒体文件的片段信息（如视频关键帧、音频片段）

| 字段名 | 数据类型 | 约束 | 默认值 | 描述 |
|--------|----------|------|--------|------|
| id | TEXT | PRIMARY KEY | - | 片段唯一标识符（UUID） |
| file_id | TEXT | NOT NULL, FOREIGN KEY | - | 关联的文件ID |
| segment_type | TEXT | NOT NULL | - | 片段类型（frame/audio/unknown） |
| segment_index | INTEGER | NOT NULL | - | 片段索引（从0开始） |
| start_time_ms | REAL | - | - | 片段开始时间（毫秒，仅视频/音频） |
| end_time_ms | REAL | - | - | 片段结束时间（毫秒，仅视频/音频） |
| duration_ms | REAL | - | - | 片段持续时间（毫秒，仅视频/音频） |
| data_path | TEXT | - | - | 片段数据文件路径 |
| metadata | TEXT | - | - | 片段元数据（JSON格式） |
| created_at | REAL | NOT NULL | - | 片段创建时间（Unix时间戳） |

**索引**: 
- idx_media_segments_file_id (file_id)

### 2.4 vectors 表

**功能**: 存储文件和片段的向量表示

| 字段名 | 数据类型 | 约束 | 默认值 | 描述 |
|--------|----------|------|--------|------|
| id | TEXT | PRIMARY KEY | - | 向量唯一标识符（UUID） |
| file_id | TEXT | NOT NULL, FOREIGN KEY | - | 关联的文件ID |
| task_id | TEXT | FOREIGN KEY | - | 关联的任务ID |
| segment_id | TEXT | FOREIGN KEY | - | 关联的片段ID（如果是片段向量） |
| vector_data | BLOB | NOT NULL | - | 序列化的向量数据（pickle格式） |
| model_name | TEXT | NOT NULL | - | 生成向量的模型名称 |
| vector_type | TEXT | NOT NULL | - | 向量类型（image/audio/text） |
| qdrant_point_id | TEXT | - | - | 对应Qdrant向量数据库中的点ID |
| created_at | REAL | NOT NULL | - | 向量创建时间（Unix时间戳） |

**索引**: 
- idx_vectors_file_id (file_id)

### 2.5 video_segments 表

**功能**: 存储视频片段信息，用于精确时间戳定位

| 字段名 | 数据类型 | 约束 | 默认值 | 描述 |
|--------|----------|------|--------|------|
| segment_id | TEXT | PRIMARY KEY | - | 片段唯一标识符（UUID） |
| file_uuid | TEXT | NOT NULL | - | 关联的文件UUID |
| segment_index | INTEGER | NOT NULL | - | 片段索引（从0开始） |
| start_time | REAL | NOT NULL | - | 片段开始时间（秒） |
| end_time | REAL | NOT NULL | - | 片段结束时间（秒） |
| duration | REAL | NOT NULL | - | 片段持续时间（秒） |
| scene_boundary | BOOLEAN | - | 0 | 是否为场景边界（0=否, 1=是） |
| created_at | REAL | NOT NULL | - | 片段创建时间（Unix时间戳） |

**索引**: 
- idx_video_segments_file_uuid (file_uuid)

## 3. 数据关系图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              files                                      │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ id (PK)                                                          │  │
│  │ file_path (UNIQUE)                                               │  │
│  │ file_name                                                        │  │
│  │ file_type                                                        │  │
│  │ file_size                                                        │  │
│  │ file_hash                                                        │  │
│  │ created_at                                                       │  │
│  │ modified_at                                                      │  │
│  │ processed_at                                                     │  │
│  │ status                                                           │  │
│  │ can_delete                                                       │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────┬───────────────────────────────────┘
                                      │
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                              tasks                                      │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ id (PK)                                                          │  │
│  │ file_id (FK -> files.id)                                         │  │
│  │ task_type                                                        │  │
│  │ status                                                           │  │
│  │ progress                                                         │  │
│  │ error_message                                                    │  │
│  │ created_at                                                       │  │
│  │ updated_at                                                       │  │
│  │ retry_count                                                      │  │
│  │ max_retry_attempts                                               │  │
│  │ retry_at                                                         │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────┬───────────────────────────────────┘
                                      │
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                            media_segments                              │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ id (PK)                                                          │  │
│  │ file_id (FK -> files.id)                                         │  │
│  │ segment_type                                                     │  │
│  │ segment_index                                                    │  │
│  │ start_time_ms                                                    │  │
│  │ end_time_ms                                                      │  │
│  │ duration_ms                                                      │  │
│  │ data_path                                                        │  │
│  │ metadata                                                         │  │
│  │ created_at                                                       │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────┬───────────────────────────────────┘
                                      │
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                              vectors                                    │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ id (PK)                                                          │  │
│  │ file_id (FK -> files.id)                                         │  │
│  │ task_id (FK -> tasks.id)                                         │  │
│  │ segment_id (FK -> media_segments.id)                             │  │
│  │ vector_data                                                      │  │
│  │ model_name                                                       │  │
│  │ vector_type                                                      │  │
│  │ qdrant_point_id                                                  │  │
│  │ created_at                                                       │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                           video_segments                              │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ segment_id (PK)                                                  │  │
│  │ file_uuid                                                        │  │
│  │ segment_index                                                    │  │
│  │ start_time                                                       │  │
│  │ end_time                                                         │  │
│  │ duration                                                         │  │
│  │ scene_boundary                                                   │  │
│  │ created_at                                                       │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

## 4. 数据流程

### 4.1 文件处理流程

1. **文件添加**: 
   - 当新文件被监控到或手动添加时
   - 在 `files` 表中插入一条记录，状态为 `pending`
   - 同时在 `tasks` 表中创建一个预处理任务

2. **预处理阶段**: 
   - 任务状态变为 `processing`
   - 处理完成后，在 `media_segments` 表中插入片段记录
   - 任务状态变为 `completed`
   - 自动创建向量化任务

3. **向量化阶段**: 
   - 任务状态变为 `processing`
   - 生成向量后，在 `vectors` 表中插入向量记录
   - 同时将向量上传到Qdrant向量数据库
   - 任务状态变为 `completed`
   - 更新 `files` 表中的 `status` 为 `completed`

4. **文件更新**: 
   - 当文件内容变化时
   - 更新 `files` 表中的 `file_hash` 和 `modified_at`
   - 创建新的处理任务

5. **文件删除**: 
   - 当文件被删除时
   - 从 `files` 表中删除记录
   - 级联删除关联的 `tasks`、`media_segments` 和 `vectors` 记录
   - 同时从Qdrant向量数据库中删除对应的向量

### 4.2 搜索流程

1. **查询处理**: 
   - 接收用户查询（文本/图像/音频）
   - 生成查询向量

2. **向量检索**: 
   - 使用查询向量在Qdrant中检索相似向量
   - 获取 `qdrant_point_id` 列表

3. **数据关联**: 
   - 根据 `qdrant_point_id` 在 `vectors` 表中查找对应的记录
   - 关联 `files` 和 `media_segments` 表获取完整信息

4. **结果返回**: 
   - 组装搜索结果
   - 返回给用户

## 5. 数据库维护

### 5.1 定期维护任务

1. **清理旧任务**: 
   - 删除超过30天的已完成任务
   - 命令: `python scripts/maintain_database.py --clean-tasks`

2. **优化数据库**: 
   - 运行VACUUM命令优化数据库文件
   - 命令: `python scripts/maintain_database.py --vacuum`

3. **重建索引**: 
   - 定期重建索引以提高查询性能
   - 命令: `python scripts/maintain_database.py --reindex`

### 5.2 备份与恢复

1. **备份数据库**: 
   ```bash
   python scripts/backup_database.py
   ```

2. **恢复数据库**: 
   ```bash
   python scripts/restore_database.py --backup-file <backup_file>
   ```

3. **完整备份**: 
   ```bash
   # 备份整个data目录
   tar -czf msearch_backup_$(date +%Y%m%d).tar.gz data/
   ```

## 6. 性能优化

### 6.1 索引优化

- **查询频繁的字段**: 为 `status`、`file_id` 等字段创建索引
- **联合查询优化**: 为经常一起查询的字段创建复合索引
- **避免全表扫描**: 确保所有查询都使用索引

### 6.2 查询优化

- **分页查询**: 对大量数据使用分页
- **限制返回字段**: 只查询需要的字段
- **使用事务**: 批量操作时使用事务提高性能
- **避免复杂JOIN**: 尽量减少表连接数量

### 6.3 数据清理

- **定期清理**: 定期清理不再需要的数据
- **软删除**: 对重要数据使用软删除，避免频繁的物理删除
- **批量删除**: 批量处理删除操作，减少IO开销

## 7. 未来扩展

### 7.1 计划添加的表

1. **file_relationships**: 存储文件之间的关系
   ```sql
   CREATE TABLE file_relationships (
       id TEXT PRIMARY KEY,
       source_file_id TEXT NOT NULL,
       target_file_id TEXT NOT NULL,
       relationship_type TEXT NOT NULL,
       created_at REAL NOT NULL,
       FOREIGN KEY (source_file_id) REFERENCES files (id),
       FOREIGN KEY (target_file_id) REFERENCES files (id)
   );
   ```

2. **persons**: 存储人物信息（用于人脸识别）
   ```sql
   CREATE TABLE persons (
       id TEXT PRIMARY KEY,
       name TEXT NOT NULL,
       aliases TEXT,
       face_vector BLOB,
       created_at REAL NOT NULL,
       updated_at REAL NOT NULL
   );
   ```

3. **file_faces**: 存储文件中的人脸信息
   ```sql
   CREATE TABLE file_faces (
       id TEXT PRIMARY KEY,
       file_id TEXT NOT NULL,
       person_id TEXT,
       face_vector BLOB NOT NULL,
       bounding_box TEXT NOT NULL,
       confidence REAL NOT NULL,
       created_at REAL NOT NULL,
       FOREIGN KEY (file_id) REFERENCES files (id),
       FOREIGN KEY (person_id) REFERENCES persons (id)
   );
   ```

### 7.2 计划添加的字段

1. **files表**: 
   - `file_category`: 文件类别（source/processed/derived/thumbnail）
   - `source_file_id`: 关联源文件ID

2. **tasks表**: 
   - `priority`: 任务优先级（high/medium/low）
   - `estimated_time`: 估计处理时间

## 8. 数据库操作示例

### 8.1 插入文件记录

```python
async def insert_file_example():
    from src.common.storage.database_adapter import DatabaseAdapter
    
    db = DatabaseAdapter()
    file_info = {
        'id': 'uuid-1234-5678',
        'file_path': '/path/to/file.jpg',
        'file_name': 'file.jpg',
        'file_type': 'image',
        'file_size': 1024,
        'file_hash': 'abc123',
        'created_at': 1234567890.0,
        'modified_at': 1234567890.0,
        'status': 'pending'
    }
    await db.insert_file(file_info)
```

### 8.2 查询待处理文件

```python
async def get_pending_files_example():
    from src.common.storage.database_adapter import DatabaseAdapter
    
    db = DatabaseAdapter()
    pending_files = await db.get_pending_files(limit=10)
    for file in pending_files:
        print(f"待处理文件: {file['file_path']}")
```

### 8.3 更新任务状态

```python
async def update_task_status_example():
    from src.common.storage.database_adapter import DatabaseAdapter
    
    db = DatabaseAdapter()
    await db.update_task('task-1234', {
        'status': 'completed',
        'progress': 100,
        'updated_at': 1234567890.0
    })
```

## 9. 常见问题

### 9.1 数据库文件损坏

**问题**: SQLite数据库文件损坏
**解决**: 
1. 恢复最近的备份
2. 运行修复命令: 
   ```bash
   sqlite3 data/database/msearch.db ".recover" | sqlite3 data/database/msearch_fixed.db
   ```
3. 替换原数据库文件

### 9.2 数据库文件过大

**问题**: 数据库文件超过1GB
**解决**: 
1. 清理旧数据: `python scripts/maintain_database.py --clean-old-data`
2. 运行VACUUM命令: `python scripts/maintain_database.py --vacuum`
3. 考虑分区存储或迁移到其他数据库

### 9.3 查询性能下降

**问题**: 查询速度变慢
**解决**: 
1. 运行EXPLAIN QUERY PLAN分析查询
2. 优化索引
3. 清理旧数据
4. 重建索引: `python scripts/maintain_database.py --reindex`

## 10. 联系方式

如有数据库相关问题，请联系技术支持: support@msearch.com

---

**更新时间**: 2024-01-01  
**版本**: v1.0.0  
**最后更新者**: MSearch Team