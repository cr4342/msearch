# WebUI文字搜索音频功能实现总结

## 功能概述

在WebUI中增加了文字搜索音频的入口，支持用户通过文本搜索查询音频文件。

## 已完成的修改

### 1. WebUI前端修改

#### HTML修改 (`src/webui/index.html`)
- 将搜索输入框改为div容器，包含文本输入和文件输入两种模式
- 支持根据搜索类型动态切换输入方式：
  - 文本搜索：显示文本输入框
  - 图像搜索：显示文件上传控件（accept="image/*"）
  - 音频搜索：显示文件上传控件（accept="audio/*"）

#### JavaScript修改 (`src/webui/app.js`)
- 添加了`updateSearchUI()`函数，根据搜索类型动态更新UI
- 添加了`getSearchInput()`辅助函数，获取搜索输入
- 修改了`performTextSearch()`函数，使用新的DOM结构
- 实现了`performImageSearch()`函数，支持图像文件上传和搜索
- 实现了`performAudioSearch()`函数，支持音频文件上传和搜索
- 添加了文件上传功能，通过`/api/v1/files/upload`端点上传文件

### 2. API服务端修改

#### 路由修改 (`src/api/v1/routes.py`)
- 添加了`/api/v1/files/upload`端点，支持文件上传
- 添加了`UploadFile`和`File`的导入

#### 处理器修改 (`src/api/v1/handlers.py`)
- 修复了`handle_text_search`中的modality映射，使用结果中的实际modality而不是固定为`TEXT`

### 3. 核心组件修改

#### 搜索引擎修改 (`src/services/search/search_engine.py`)
- 修复了`search`方法，根据`modalities`参数创建filter条件
- 将filter条件传递给向量存储的search方法

#### 向量存储修改 (`src/core/vector/vector_store.py`)
- 修复了`search_vectors`方法的filter实现
- 使用LanceDB的`where`子句进行过滤，支持列表和单个值

## 使用方法

### 文本搜索音频

1. 在WebUI中选择"文本搜索"
2. 在文本输入框中输入搜索查询（如"二泉映月"、"音乐"等）
3. 点击"搜索"按钮
4. 系统会搜索所有模态的文件，包括音频文件

### 音频文件搜索

1. 在WebUI中选择"音频搜索"
2. 点击文件选择按钮，上传一个音频文件
3. 点击"搜索"按钮
4. 系统会上传音频文件，然后使用该文件搜索相似的音频

## 技术实现细节

### 文件上传流程

1. 用户在前端选择文件
2. JavaScript将文件通过FormData发送到`/api/v1/files/upload`端点
3. 服务器保存文件到`data/uploads`目录
4. 服务器返回文件路径
5. 前端使用返回的文件路径调用相应的搜索API

### 搜索流程

1. 文本搜索：
   - 将文本向量化
   - 在向量数据库中搜索相似向量
   - 应用modality过滤（可选）
   - 返回搜索结果

2. 音频文件搜索：
   - 上传音频文件
   - 将音频文件向量化
   - 在向量数据库中搜索相似向量
   - 返回搜索结果

### 过滤机制

- 使用LanceDB的`where`子句进行过滤
- 支持单值过滤：`modality = 'audio'`
- 支持列表过滤：`modality in ('image', 'video', 'audio', 'text')`
- 在向量搜索前应用过滤，提高搜索效率

## 注意事项

1. **文件上传目录**：确保`data/uploads`目录存在且有写权限
2. **模态过滤**：文本搜索默认搜索所有模态，可以通过修改`modalities`参数限制搜索范围
3. **相似度计算**：使用余弦相似度，LanceDB返回余弦距离，需要转换为相似度（1 - distance）
4. **去重机制**：根据file_path去重，保留相似度最高的结果

## 测试验证

### 测试文本搜索音频

```bash
curl -X POST http://localhost:8000/api/v1/search/text \
  -H "Content-Type: application/json" \
  -d '{"query": "二泉映月", "top_k": 20, "threshold": 0.0}'
```

### 测试音频文件搜索

1. 在WebUI中选择"音频搜索"
2. 上传一个音频文件
3. 点击"搜索"按钮
4. 查看搜索结果

## 未来优化方向

1. **性能优化**：
   - 实现向量缓存，避免重复向量化
   - 优化批量搜索性能

2. **功能增强**：
   - 添加音频预览功能
   - 支持音频片段搜索
   - 添加搜索结果排序选项

3. **用户体验**：
   - 添加上传进度显示
   - 支持拖拽上传
   - 添加搜索历史记录

## 相关文件

- `src/webui/index.html` - WebUI HTML
- `src/webui/app.js` - WebUI JavaScript
- `src/api/v1/routes.py` - API路由
- `src/api/v1/handlers.py` - API处理器
- `src/services/search/search_engine.py` - 搜索引擎
- `src/core/vector/vector_store.py` - 向量存储

## 总结

WebUI中的文字搜索音频功能已经完成实现，包括：
- ✅ 前端UI修改，支持文本、图像、音频三种搜索方式
- ✅ 文件上传功能，支持图像和音频文件上传
- ✅ API端点实现，支持文件上传和搜索
- ✅ 核心组件优化，支持模态过滤
- ✅ 文档完善，提供使用说明和技术细节

用户现在可以通过WebUI使用文本搜索查询音频文件，也可以上传音频文件进行相似度搜索。