# MSearch - 多模态搜索系统

## 项目简介

MSearch是一个强大的多模态搜索系统，支持文本、图像、音频等多种数据类型的统一索引和检索。系统采用向量搜索引擎Milvus Lite作为底层存储，提供高效的相似度搜索能力。

## 核心功能

- **多模态支持**：支持文本、视觉（图像）、音频（音乐、语音）等多种数据类型
- **混合检索**：支持跨模态的混合检索，例如用文本搜索相关图像
- **高性能**：优化的向量存储和检索算法，支持大批量数据处理
- **可扩展性**：模块化设计，易于扩展新的向量类型和检索算法
- **错误处理**：完善的异常处理机制，提供详细的错误信息和重试策略

## 系统架构

### 主要组件

1. **VectorStorageManager**：向量存储管理器，负责向量的增删改查
2. **VectorAdapter**：向量存储适配器接口，支持不同的向量数据库后端
3. **MilvusAdapter**：Milvus Lite向量数据库适配器实现
4. **ConfigManager**：配置管理器，负责系统配置的加载和管理
5. **Exception Classes**：自定义异常类体系，提供丰富的错误处理

### 工作流程

1. **数据处理**：将原始数据（文本、图像、音频）转换为向量表示
2. **向量存储**：将向量及其元数据存储到向量数据库中
3. **向量检索**：根据查询向量查找相似的向量
4. **结果融合**：对于混合检索，融合不同模态的检索结果

## 安装指南

### 环境要求

- Python 3.8+
- Milvus Lite 2.3.0+
- NumPy, AsyncIO

### 安装步骤

1. 克隆项目：
```bash
git clone <repository-url>
cd msearch
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. Milvus Lite无需单独启动服务，直接集成在代码中使用

## 使用示例

### 初始化向量存储

```python
from msearch.common.storage.vector_storage_manager import VectorStorageManager
from msearch.utils.enums import VectorType

# 初始化向量存储管理器
storage_manager = VectorStorageManager()

# 确保集合存在
await storage_manager.initialize()
```

### 存储向量

```python
# 存储单个向量
await storage_manager.store_vector(
    vector_type=VectorType.VISUAL,
    vector=[0.1, 0.2, ..., 0.5],  # 512维向量
    metadata={
        "file_path": "/path/to/image.jpg",
        "file_name": "image.jpg",
        "file_type": "jpg"
    }
)

# 批量存储向量
await storage_manager.batch_store_vectors(
    vectors=[
        (VectorType.VISUAL, [0.1, 0.2, ..., 0.5], {"file_path": "/path/to/image1.jpg"}),
        (VectorType.VISUAL, [0.3, 0.4, ..., 0.7], {"file_path": "/path/to/image2.jpg"})
    ]
)
```

### 搜索向量

```python
# 搜索相似向量
results = await storage_manager.search_vectors(
    vector_type=VectorType.VISUAL,
    query_vector=[0.15, 0.25, ..., 0.55],
    limit=10,
    score_threshold=0.6
)

# 带过滤条件的搜索
results = await storage_manager.search_vectors(
    vector_type=VectorType.VISUAL,
    query_vector=[0.15, 0.25, ..., 0.55],
    limit=10,
    filter_conditions={"file_type": "jpg"}
)
```

### 删除向量

```python
# 删除文件相关的所有向量
deleted_count = await storage_manager.delete_file(
    file_path="/path/to/image.jpg"
)
```

## 配置说明

主要配置文件位于 `config/config.yml`，包含以下关键配置项：

- **vector_storage**：向量存储相关配置
  - dimensions：各类型向量的维度
  - batch_size：批量处理大小
  - collection_mapping：向量类型到集合名的映射

- **error_handling**：错误处理配置
  - max_retries：最大重试次数
  - retry_enabled：是否启用重试
  - dimension_adjustment_enabled：是否启用维度调整

## 性能优化

1. **批量处理**：使用 `batch_store_vectors` 方法批量存储向量
2. **并行处理**：系统内部实现了向量处理的并行化
3. **动态批处理**：根据向量数量自动调整批处理大小
4. **结果缓存**：对于频繁查询的结果可以考虑添加缓存层

## 错误处理

系统提供了完善的异常处理机制，主要异常类包括：

- **VectorStorageError**：向量存储相关错误
- **VectorDimensionError**：向量维度不匹配错误
- **CollectionNotFoundError**：集合未找到错误
- **ConnectionError**：连接错误
- **TimeoutError**：超时错误
- **ValidationError**：参数验证错误

## 开发指南

### 添加新的向量类型

1. 在 `VectorType` 枚举中添加新类型
2. 在配置文件中设置对应的维度和集合名
3. 更新 `VectorStorageManager` 中的相关方法

### 运行测试

```bash
cd tests
pytest
```

## 许可证

[MIT License](LICENSE)
