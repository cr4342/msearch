# 扩展性设计文档

## 1. 概述

MSearch 系统采用插件化架构，支持模型、存储和功能的灵活扩展。系统设计充分考虑了未来功能扩展的需求，提供了清晰的扩展点和标准化的扩展接口。

### 1.1 设计目标

- **模型扩展**: 支持新增 AI 模型，无需修改核心代码
- **存储扩展**: 支持多种向量数据库和存储后端
- **功能扩展**: 支持插件式功能扩展，自定义处理流程
- **向后兼容**: 新增扩展不影响现有功能

### 1.2 扩展原则

- **开闭原则**: 对扩展开放，对修改关闭
- **接口隔离**: 扩展接口职责单一，易于实现
- **依赖倒置**: 依赖抽象接口，不依赖具体实现
- **最小侵入**: 扩展实现不修改核心代码

## 2. 模型扩展

### 2.1 模型管理架构

**统一模型接口**:
```python
class ModelInterface(ABC):
    """模型统一接口"""
    
    @abstractmethod
    def load(self, model_path: str) -> None:
        """加载模型"""
        pass
    
    @abstractmethod
    def embed(self, data: Any) -> np.ndarray:
        """生成向量"""
        pass
    
    @abstractmethod
    def unload(self) -> None:
        """卸载模型"""
        pass
```

**模型注册机制**:
```python
class ModelRegistry:
    """模型注册表"""
    
    def __init__(self):
        self._models: Dict[str, ModelInterface] = {}
    
    def register(self, name: str, model: ModelInterface) -> None:
        """注册模型"""
        self._models[name] = model
    
    def get(self, name: str) -> ModelInterface:
        """获取模型"""
        return self._models.get(name)
    
    def list_models(self) -> List[str]:
        """列出所有模型"""
        return list(self._models.keys())
```

### 2.2 内置模型

**CLIP 模型**:
- 用途: 文本-图像/视频检索
- 模型类型: OpenAI CLIP
- 向量维度: 512/768
- 支持模态: 文本、图像

**CLAP 模型**:
- 用途: 文本-音乐检索
- 模型类型: LAION CLAP
- 向量维度: 512
- 支持模态: 文本、音频（音乐）

**Whisper 模型**:
- 用途: 语音转文本
- 模型类型: OpenAI Whisper
- 向量维度: N/A（生成文本）
- 支持模态: 音频（语音）

**CLIP4Clip 模型**:
- 用途: 视频片段向量化和检索
- 模型类型: CLIP4Clip
- 向量维度: 512
- 支持模态: 文本、视频（片段）

### 2.3 自定义模型

**模型实现示例**:
```python
class CustomModel(ModelInterface):
    """自定义模型示例"""
    
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.model = None
    
    def load(self, model_path: str) -> None:
        """加载模型"""
        import torch
        self.model = torch.load(model_path)
    
    def embed(self, data: Any) -> np.ndarray:
        """生成向量"""
        # 实现向量生成逻辑
        result = self.model.encode(data)
        return result.cpu().numpy()
    
    def unload(self) -> None:
        """卸载模型"""
        del self.model
        self.model = None
```

**模型注册**:
```python
# 在系统启动时注册自定义模型
registry = ModelRegistry()
custom_model = CustomModel("my_custom_model")
registry.register("custom", custom_model)

# 使用自定义模型
model = registry.get("custom")
vector = model.embed(data)
```

### 2.4 模型热加载

**热加载机制**:
- 支持运行时加载新模型
- 支持运行时卸载模型
- 支持模型版本管理

**热加载示例**:
```python
class EmbeddingEngine:
    """向量化引擎"""
    
    def load_model(self, model_name: str, model_path: str) -> None:
        """加载模型"""
        model = self.model_registry.get(model_name)
        if model:
            model.load(model_path)
    
    def unload_model(self, model_name: str) -> None:
        """卸载模型"""
        model = self.model_registry.get(model_name)
        if model:
            model.unload()
```

### 2.5 模型配置

**配置文件**:
```yaml
models:
  clip:
    name: "openai/clip-vit-base-patch32"
    path: "/models/clip"
    enabled: true
    device: "cuda"
  
  clap:
    name: "laion/clap"
    path: "/models/clap"
    enabled: true
    device: "cuda"
  
  whisper:
    name: "openai/whisper-base"
    path: "/models/whisper"
    enabled: true
    device: "cuda"
  
  clip4clip:
    name: "clip4clip"
    path: "/models/clip4clip"
    enabled: true
    device: "cuda"
  
  custom:
    name: "my_custom_model"
    path: "/models/custom"
    enabled: false
    device: "cuda"
```

## 3. 存储扩展

### 3.1 存储抽象层

**统一存储接口**:
```python
class StorageInterface(ABC):
    """存储统一接口"""
    
    @abstractmethod
    def insert(self, collection: str, data: List[Dict]) -> bool:
        """插入数据"""
        pass
    
    @abstractmethod
    def search(self, collection: str, vector: np.ndarray, top_k: int) -> List[Dict]:
        """搜索数据"""
        pass
    
    @abstractmethod
    def delete(self, collection: str, ids: List[str]) -> bool:
        """删除数据"""
        pass
    
    @abstractmethod
    def update(self, collection: str, data: List[Dict]) -> bool:
        """更新数据"""
        pass
```

**存储注册机制**:
```python
class StorageRegistry:
    """存储注册表"""
    
    def __init__(self):
        self._storages: Dict[str, StorageInterface] = {}
    
    def register(self, name: str, storage: StorageInterface) -> None:
        """注册存储"""
        self._storages[name] = storage
    
    def get(self, name: str) -> StorageInterface:
        """获取存储"""
        return self._storages.get(name)
```

### 3.2 内置存储

**Milvus Lite**:
- 类型: 向量数据库
- 用途: 存储和检索向量数据
- 特性: 高性能、低延迟、支持多种索引类型

**SQLite**:
- 类型: 关系数据库
- 用途: 存储元数据和配置
- 特性: 轻量级、无需额外服务、事务支持

### 3.3 自定义存储

**存储实现示例**:
```python
class CustomStorage(StorageInterface):
    """自定义存储示例"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.client = None
    
    def connect(self) -> None:
        """连接存储"""
        # 实现连接逻辑
        pass
    
    def insert(self, collection: str, data: List[Dict]) -> bool:
        """插入数据"""
        # 实现插入逻辑
        return True
    
    def search(self, collection: str, vector: np.ndarray, top_k: int) -> List[Dict]:
        """搜索数据"""
        # 实现搜索逻辑
        return []
    
    def delete(self, collection: str, ids: List[str]) -> bool:
        """删除数据"""
        # 实现删除逻辑
        return True
    
    def update(self, collection: str, data: List[Dict]) -> bool:
        """更新数据"""
        # 实现更新逻辑
        return True
```

### 3.4 存储配置

**配置文件**:
```yaml
storage:
  vector_db:
    type: "milvus_lite"
    config:
      path: "/data/milvus"
      index_type: "IVF_FLAT"
      metric_type: "IP"
  
  metadata_db:
    type: "sqlite"
    config:
      path: "/data/metadata.db"
  
  custom:
    type: "custom"
    config:
      host: "localhost"
      port: 6379
      password: "password"
```

## 4. 功能扩展

### 4.1 插件系统

**插件接口**:
```python
class PluginInterface(ABC):
    """插件统一接口"""
    
    @abstractmethod
    def initialize(self, context: PluginContext) -> None:
        """初始化插件"""
        pass
    
    @abstractmethod
    def execute(self, input_data: Any) -> Any:
        """执行插件功能"""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """清理插件"""
        pass
```

**插件管理器**:
```python
class PluginManager:
    """插件管理器"""
    
    def __init__(self):
        self._plugins: Dict[str, PluginInterface] = {}
    
    def load_plugin(self, plugin_path: str) -> None:
        """加载插件"""
        import importlib.util
        spec = importlib.util.spec_from_file_location("plugin", plugin_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        plugin_class = getattr(module, "Plugin")
        plugin = plugin_class()
        plugin.initialize(self._create_context())
        self._plugins[plugin.name] = plugin
    
    def unload_plugin(self, plugin_name: str) -> None:
        """卸载插件"""
        plugin = self._plugins.get(plugin_name)
        if plugin:
            plugin.cleanup()
            del self._plugins[plugin_name]
    
    def execute_plugin(self, plugin_name: str, input_data: Any) -> Any:
        """执行插件"""
        plugin = self._plugins.get(plugin_name)
        if plugin:
            return plugin.execute(input_data)
        return None
```

### 4.2 预处理插件

**预处理插件示例**:
```python
class PreprocessPlugin(PluginInterface):
    """预处理插件示例"""
    
    name = "custom_preprocess"
    
    def initialize(self, context: PluginContext) -> None:
        """初始化插件"""
        self.context = context
    
    def execute(self, input_data: Dict) -> Dict:
        """执行预处理"""
        file_path = input_data["file_path"]
        
        # 实现自定义预处理逻辑
        processed_data = self._process_file(file_path)
        
        return {
            "file_path": file_path,
            "processed_data": processed_data
        }
    
    def cleanup(self) -> None:
        """清理插件"""
        pass
    
    def _process_file(self, file_path: str) -> Any:
        """处理文件"""
        # 实现具体的文件处理逻辑
        pass
```

### 4.3 向量化插件

**向量化插件示例**:
```python
class EmbeddingPlugin(PluginInterface):
    """向量化插件示例"""
    
    name = "custom_embedding"
    
    def initialize(self, context: PluginContext) -> None:
        """初始化插件"""
        self.context = context
        self.model = self._load_model()
    
    def execute(self, input_data: Dict) -> Dict:
        """执行向量化"""
        file_path = input_data["file_path"]
        data = input_data["data"]
        
        # 生成向量
        vector = self.model.embed(data)
        
        return {
            "file_path": file_path,
            "vector": vector,
            "model": self.name
        }
    
    def cleanup(self) -> None:
        """清理插件"""
        del self.model
    
    def _load_model(self) -> ModelInterface:
        """加载模型"""
        # 实现模型加载逻辑
        pass
```

### 4.4 插件配置

**配置文件**:
```yaml
plugins:
  preprocess:
    - name: "video_slicer"
      enabled: true
      config:
        slice_duration: 5
    
    - name: "audio_segmenter"
      enabled: true
      config:
        segment_duration: 10
  
  embedding:
    - name: "custom_embedding"
      enabled: false
      config:
        model_path: "/models/custom"
  
  postprocess:
    - name: "result_filter"
      enabled: true
      config:
        threshold: 0.7
```

## 5. 任务扩展

### 5.1 任务类型扩展

**任务接口**:
```python
class TaskInterface(ABC):
    """任务统一接口"""
    
    @abstractmethod
    def execute(self) -> TaskResult:
        """执行任务"""
        pass
    
    @abstractmethod
    def cancel(self) -> None:
        """取消任务"""
        pass
```

**任务类型**:
- SCAN: 文件扫描任务
- PREPROCESS: 文件预处理任务
- EMBED: 向量化任务
- STORAGE: 存储任务
- INDEX: 索引任务

**自定义任务**:
```python
class CustomTask(TaskInterface):
    """自定义任务示例"""
    
    def __init__(self, task_data: Dict):
        self.task_data = task_data
        self.cancelled = False
    
    def execute(self) -> TaskResult:
        """执行任务"""
        # 实现任务逻辑
        result = self._do_work()
        
        return TaskResult(
            success=True,
            data=result,
            message="Task completed"
        )
    
    def cancel(self) -> None:
        """取消任务"""
        self.cancelled = True
    
    def _do_work(self) -> Any:
        """执行工作"""
        # 实现具体的工作逻辑
        pass
```

### 5.2 任务队列扩展

**任务队列接口**:
```python
class TaskQueueInterface(ABC):
    """任务队列统一接口"""
    
    @abstractmethod
    def enqueue(self, task: TaskInterface) -> None:
        """入队任务"""
        pass
    
    @abstractmethod
    def dequeue(self) -> TaskInterface:
        """出队任务"""
        pass
    
    @abstractmethod
    def size(self) -> int:
        """队列大小"""
        pass
```

**自定义任务队列**:
```python
class CustomTaskQueue(TaskQueueInterface):
    """自定义任务队列示例"""
    
    def __init__(self):
        self._queue = queue.Queue()
    
    def enqueue(self, task: TaskInterface) -> None:
        """入队任务"""
        self._queue.put(task)
    
    def dequeue(self) -> TaskInterface:
        """出队任务"""
        return self._queue.get()
    
    def size(self) -> int:
        """队列大小"""
        return self._queue.qsize()
```

## 6. API 扩展

### 6.1 API 路由扩展

**路由注册**:
```python
class APIRouter:
    """API 路由器"""
    
    def __init__(self):
        self._routes: Dict[str, Callable] = {}
    
    def register(self, path: str, handler: Callable) -> None:
        """注册路由"""
        self._routes[path] = handler
    
    def get_handler(self, path: str) -> Callable:
        """获取处理器"""
        return self._routes.get(path)
```

**自定义 API**:
```python
# 注册自定义 API 路由
router = APIRouter()

@router.register("/api/v1/custom/search")
def custom_search(request: Request) -> Response:
    """自定义搜索 API"""
    # 实现搜索逻辑
    return Response(results)
```

### 6.2 中间件扩展

**中间件接口**:
```python
class MiddlewareInterface(ABC):
    """中间件统一接口"""
    
    @abstractmethod
    def process_request(self, request: Request) -> Request:
        """处理请求"""
        pass
    
    @abstractmethod
    def process_response(self, response: Response) -> Response:
        """处理响应"""
        pass
```

**自定义中间件**:
```python
class AuthMiddleware(MiddlewareInterface):
    """认证中间件"""
    
    def process_request(self, request: Request) -> Request:
        """处理请求"""
        # 验证认证信息
        token = request.headers.get("Authorization")
        if not self._validate_token(token):
            raise UnauthorizedError()
        
        return request
    
    def process_response(self, response: Response) -> Response:
        """处理响应"""
        # 添加认证头
        response.headers["X-Auth-Status"] = "valid"
        return response
    
    def _validate_token(self, token: str) -> bool:
        """验证令牌"""
        # 实现令牌验证逻辑
        pass
```

## 7. 配置扩展

### 7.1 配置加载器

**配置加载器接口**:
```python
class ConfigLoaderInterface(ABC):
    """配置加载器统一接口"""
    
    @abstractmethod
    def load(self, config_path: str) -> Dict:
        """加载配置"""
        pass
    
    @abstractmethod
    def save(self, config_path: str, config: Dict) -> None:
        """保存配置"""
        pass
```

**自定义配置加载器**:
```python
class JSONConfigLoader(ConfigLoaderInterface):
    """JSON 配置加载器"""
    
    def load(self, config_path: str) -> Dict:
        """加载配置"""
        import json
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def save(self, config_path: str, config: Dict) -> None:
        """保存配置"""
        import json
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
```

### 7.2 配置验证

**配置验证器**:
```python
class ConfigValidator:
    """配置验证器"""
    
    def __init__(self, schema: Dict):
        self.schema = schema
    
    def validate(self, config: Dict) -> bool:
        """验证配置"""
        # 实现配置验证逻辑
        return True
```

## 8. 扩展最佳实践

### 8.1 模型扩展建议

**模型选择**:
- 选择与系统兼容的模型
- 考虑模型性能和资源消耗
- 评估模型准确率和适用场景

**模型优化**:
- 使用量化技术减少模型大小
- 使用蒸馏技术提高模型速度
- 使用剪枝技术减少模型参数

### 8.2 存储扩展建议

**存储选择**:
- 根据数据量选择合适的存储
- 考虑存储性能和扩展性
- 评估存储成本和维护复杂度

**存储优化**:
- 使用合适的索引类型
- 定期清理过期数据
- 实现数据分片和分区

### 8.3 功能扩展建议

**插件开发**:
- 遵循插件接口规范
- 实现完善的错误处理
- 提供清晰的文档和示例

**插件测试**:
- 编写单元测试
- 进行集成测试
- 进行性能测试

### 8.4 API 扩展建议

**API 设计**:
- 遵循 RESTful 设计原则
- 使用统一的响应格式
- 提供完善的错误处理

**API 文档**:
- 使用 OpenAPI 规范
- 提供详细的接口说明
- 提供使用示例

## 9. 扩展示例

### 9.1 添加新的 AI 模型

**步骤**:
1. 实现 `ModelInterface` 接口
2. 在 `ModelRegistry` 中注册模型
3. 在配置文件中添加模型配置
4. 测试模型功能

**示例代码**:
```python
# 1. 实现模型接口
class BERTModel(ModelInterface):
    def load(self, model_path: str) -> None:
        from transformers import BertModel, BertTokenizer
        self.model = BertModel.from_pretrained(model_path)
        self.tokenizer = BertTokenizer.from_pretrained(model_path)
    
    def embed(self, data: str) -> np.ndarray:
        inputs = self.tokenizer(data, return_tensors="pt")
        outputs = self.model(**inputs)
        return outputs.last_hidden_state.mean(dim=1).detach().numpy()

# 2. 注册模型
registry = ModelRegistry()
bert_model = BERTModel()
registry.register("bert", bert_model)

# 3. 配置文件
# models:
#   bert:
#     name: "bert-base-uncased"
#     path: "/models/bert"
#     enabled: true

# 4. 使用模型
model = registry.get("bert")
vector = model.embed("Hello, world!")
```

### 9.2 添加新的存储后端

**步骤**:
1. 实现 `StorageInterface` 接口
2. 在 `StorageRegistry` 中注册存储
3. 在配置文件中添加存储配置
4. 测试存储功能

**示例代码**:
```python
# 1. 实现存储接口
class RedisStorage(StorageInterface):
    def __init__(self, config: Dict):
        import redis
        self.client = redis.Redis(
            host=config["host"],
            port=config["port"],
            password=config["password"]
        )
    
    def insert(self, collection: str, data: List[Dict]) -> bool:
        for item in data:
            key = f"{collection}:{item['id']}"
            self.client.set(key, json.dumps(item))
        return True
    
    def search(self, collection: str, vector: np.ndarray, top_k: int) -> List[Dict]:
        # 实现搜索逻辑
        return []

# 2. 注册存储
registry = StorageRegistry()
redis_storage = RedisStorage(config)
registry.register("redis", redis_storage)

# 3. 配置文件
# storage:
#   redis:
#     type: "redis"
#     config:
#       host: "localhost"
#       port: 6379
#       password: "password"

# 4. 使用存储
storage = registry.get("redis")
storage.insert("documents", data)
```

### 9.3 添加新的预处理插件

**步骤**:
1. 实现 `PluginInterface` 接口
2. 在插件目录中创建插件文件
3. 在配置文件中启用插件
4. 测试插件功能

**示例代码**:
```python
# 1. 实现插件接口
class ImageResizePlugin(PluginInterface):
    name = "image_resize"
    
    def initialize(self, context: PluginContext) -> None:
        self.context = context
        self.target_size = (224, 224)
    
    def execute(self, input_data: Dict) -> Dict:
        from PIL import Image
        file_path = input_data["file_path"]
        
        # 调整图像大小
        image = Image.open(file_path)
        image = image.resize(self.target_size)
        
        # 保存处理后的图像
        output_path = self._get_output_path(file_path)
        image.save(output_path)
        
        return {
            "file_path": file_path,
            "output_path": output_path
        }
    
    def cleanup(self) -> None:
        pass
    
    def _get_output_path(self, file_path: str) -> str:
        # 生成输出路径
        pass

# 2. 保存为 plugins/preprocess/image_resize.py

# 3. 配置文件
# plugins:
#   preprocess:
#     - name: "image_resize"
#       enabled: true
#       config:
#         target_size: [224, 224]

# 4. 使用插件
manager = PluginManager()
manager.load_plugin("plugins/preprocess/image_resize.py")
result = manager.execute_plugin("image_resize", {"file_path": "image.jpg"})
```

## 10. 扩展检查清单

### 10.1 模型扩展

- [ ] 实现了 `ModelInterface` 接口
- [ ] 在 `ModelRegistry` 中注册了模型
- [ ] 在配置文件中添加了模型配置
- [ ] 编写了模型测试用例
- [ ] 提供了模型使用文档

### 10.2 存储扩展

- [ ] 实现了 `StorageInterface` 接口
- [ ] 在 `StorageRegistry` 中注册了存储
- [ ] 在配置文件中添加了存储配置
- [ ] 编写了存储测试用例
- [ ] 提供了存储使用文档

### 10.3 功能扩展

- [ ] 实现了 `PluginInterface` 接口
- [ ] 在插件目录中创建了插件文件
- [ ] 在配置文件中启用了插件
- [ ] 编写了插件测试用例
- [ ] 提供了插件使用文档

### 10.4 API 扩展

- [ ] 实现了 API 路由处理器
- [ ] 在 `APIRouter` 中注册了路由
- [ ] 编写了 API 测试用例
- [ ] 提供了 API 文档
- [ ] 提供了 API 使用示例

## 11. 附录

### 11.1 扩展术语

- **插件**: 可独立加载和卸载的功能模块
- **模型**: 用于向量化的 AI 模型
- **存储**: 数据存储后端
- **路由**: API 路由处理器
- **中间件**: 请求/响应处理器

### 11.2 参考资料

- 插件开发指南
- 模型集成指南
- 存储集成指南
- API 开发指南

### 11.3 扩展模板

- 模型扩展模板
- 存储扩展模板
- 插件扩展模板
- API 扩展模板
