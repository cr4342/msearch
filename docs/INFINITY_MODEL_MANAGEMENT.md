# Infinity 模型管理完整指南

## 概述

本文档整合了Infinity框架的多模型管理、ColPali集成、离线模式配置和Merged版本使用的完整指南。

**版本**: v2.0  
**更新日期**: 2026-01-21

---

## 目录

1. [Infinity框架概述](#1-infinity框架概述)
2. [多模型管理架构](#2-多模型管理架构)
3. [配置驱动的模型管理](#3-配置驱动的模型管理)
4. [ColPali模型集成](#4-colpali模型集成)
5. [完全离线模式配置](#5-完全离线模式配置)
6. [Merged版本模型使用](#6-merged版本模型使用)
7. [常见问题与解决方案](#7-常见问题与解决方案)
8. [最佳实践](#8-最佳实践)

---

## 1. Infinity框架概述

### 1.1 什么是Infinity

Infinity是一个高吞吐量、低延迟的服务引擎，支持：
- **多种模型类型**: text-embeddings, reranking models, CLIP, CLAP, ColPali
- **多种推理后端**: PyTorch, Optimum (ONNX/TensorRT), CTranslate2
- **多模态支持**: 文本、图像、音频、视频
- **多模型部署**: 同时部署多个模型

### 1.2 核心特性

- **统一接口**: 所有模型使用相同的API
- **配置驱动**: 通过配置文件管理模型
- **高性能**: 动态批处理和FlashAttention加速
- **易用性**: 基于FastAPI，支持OpenAI兼容API

### 1.3 支持的模型类型

| 模型类型 | 说明 | 示例模型 |
|---------|------|---------|
| TextEmbedding | 文本嵌入 | BAAI/bge-small-en-v1.5 |
| Rerank | 重排序 | mixedbread-ai/mxbai-rerank-xsmall-v1 |
| Clip | CLIP模型 | OFA-Sys/chinese-clip-vit-base-patch16 |
| Clap | CLAP模型 | laion/clap-htsat-unfused |
| ColPali | ColPali模型 | VAGOsolutions/SauerkrautLM-ColQwen3-1.7b-Turbo-v0.1 |

---

## 2. 多模型管理架构

### 2.1 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                    ModelManager (统一管理)                   │
└─────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
    ┌─────▼─────┐      ┌─────▼─────┐      ┌─────▼─────┐
    │ TextModel │      │ImageModel│      │AudioModel │
    │  (Infinity)│      │ (Infinity)│      │ (Infinity)│
    └─────┬─────┘      └─────┬─────┘      └─────┬─────┘
          │                   │                   │
    ┌─────▼─────┐      ┌─────▼─────┐      ┌─────▼─────┐
    │ 模型配置   │      │ 模型配置   │      │ 模型配置   │
    │ config.yml│      │ config.yml│      │ config.yml│
    └───────────┘      └───────────┘      └───────────┘
```

### 2.2 核心组件

#### ModelManager
- 统一管理所有模型
- 支持模型热切换
- 自动处理LoRA模型

#### EmbeddingService
- 统一向量化接口
- 支持文本、图像、音频向量化
- 自动批处理优化

---

## 3. 配置驱动的模型管理

### 3.1 配置文件结构

```yaml
models:
  # 可用模型列表
  available_models:
    image_video_model:
      model_id: "image_video"
      model_name: "VAGOsolutions/SauerkrautLM-ColQwen3-1.7b-Turbo-v0.1"
      local_path: "data/models/SauerkrautLM-ColQwen3-1.7b-Turbo-v0.1"
      engine: "torch"
      device: "cpu"
      dtype: "float32"
      embedding_dim: 512
      trust_remote_code: true
      pooling_method: "mean"
      compile: false
      batch_size: 8
    
    audio_model:
      model_id: "audio"
      model_name: "laion/clap-htsat-unfused"
      local_path: "data/models/clap-htsat-unfused"
      engine: "torch"
      device: "cpu"
      dtype: "float32"
      embedding_dim: 512
      trust_remote_code: true
      pooling_method: "mean"
      compile: false
      batch_size: 8
  
  # 活跃模型列表
  active_models:
    - image_video_model
    - audio_model
  
  # 离线模式配置
  offline_mode:
    enabled: true
    model_cache_dir: data/models
    local_files_only: true
```

### 3.2 模型切换

**无需修改代码，只需修改配置文件**：

```yaml
# 切换到新模型
models:
  available_models:
    image_video_model:
      model_name: "VAGOsolutions/SauerkrautLM-ColQwen3-1.7b-Turbo-v0.1"  # 更换模型
      local_path: "data/models/SauerkrautLM-ColQwen3-1.7b-Turbo-v0.1"  # 更新路径
```

---

## 4. ColPali模型集成

### 4.1 ColPali模型特点

ColPali系列模型是视觉检索模型，基于ColBERT late interaction机制：
- **多向量输出**: 每个文档/查询输出多个向量
- **Late Interaction**: 查询和文档向量的交互在检索时进行
- **高精度**: 在ViDoRe基准测试中表现优异

### 4.2 支持的ColPali模型

| 模型 | ViDoRe得分 | 模型大小 | 向量维度 | Infinity支持 |
|------|-----------|---------|---------|--------------|
| VAGOsolutions/SauerkrautLM-ColQwen3-1.7b-Turbo-v0.1 | 89.3 | ~4GB | 512 | ✅ 支持 |
| OFA-Sys/chinese-clip-vit-base-patch16 | 82.3 | 70MB | 512 | ✅ 支持 |
| OFA-Sys/chinese-clip-vit-large-patch14-336px | 85.1 | 150MB | 768 | ✅ 支持 |

### 4.3 LoRA vs Merged版本

**LoRA版本**：
- 文件小（adapter权重）
- 需要基础模型
- Infinity不支持
- 需要colpali-engine

**Merged版本**：
- 文件大（完整模型）
- 无需基础模型
- Infinity支持
- 推荐使用

---

## 5. 完全离线模式配置

### 5.1 环境变量设置

```bash
# Transformers离线模式
export TRANSFORMERS_OFFLINE=1
export HF_DATASETS_OFFLINE=1
export HF_HUB_OFFLINE=1

# 禁用HuggingFace遥测
export HF_HUB_DISABLE_TELEMETRY=1
export HF_HUB_DISABLE_EXPERIMENTAL_WARNING=1
export HF_HUB_ENABLE_HF_TRANSFER=0

# 设置HuggingFace缓存目录
export HF_HOME=data/models
export HUGGINGFACE_HUB_CACHE=data/models

# Infinity离线模式
export INFINITY_ANONYMOUS_USAGE_STATS=0

# 禁用所有网络请求
export NO_PROXY='*'
export no_proxy='*'
```

### 5.2 代码配置

```python
import os
from pathlib import Path

def setup_offline_mode(model_cache_dir: str):
    """设置完全离线模式"""
    logger.info(f"设置完全离线模式，模型缓存目录: {model_cache_dir}")

    # 创建模型缓存目录
    Path(model_cache_dir).mkdir(parents=True, exist_ok=True)

    # 设置环境变量
    os.environ['TRANSFORMERS_OFFLINE'] = '1'
    os.environ['HF_DATASETS_OFFLINE'] = '1'
    os.environ['HF_HUB_OFFLINE'] = '1'
    os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
    os.environ['HF_HUB_DISABLE_EXPERIMENTAL_WARNING'] = '1'
    os.environ['HF_HUB_ENABLE_HF_TRANSFER'] = '0'
    os.environ['HF_HOME'] = model_cache_dir
    os.environ['HUGGINGFACE_HUB_CACHE'] = model_cache_dir
    os.environ['INFINITY_ANONYMOUS_USAGE_STATS'] = '0'
    os.environ['NO_PROXY'] = '*'
    os.environ['no_proxy'] = '*'

    logger.info("离线模式环境变量已设置")
```

### 5.3 Infinity离线模式限制

**重要**: Infinity框架**不支持**`local_files_only`参数

离线模式通过以下方式实现：
1. 设置完整的环境变量
2. 使用本地模型路径
3. 确保模型文件完整

---

## 6. Merged版本模型使用

### 6.1 为什么使用Merged版本

**问题**: LoRA版本无法在离线模式下使用Infinity

**原因**:
1. Infinity不支持ColIdefics3架构的LoRA adapter
2. adapter_config.json的base_model_name_or_path指向HuggingFace模型名称
3. target_modules正则表达式不匹配基础模型结构
4. 需要特殊处理（切换工作目录、使用colpali-engine）

**解决方案**: 使用Merged版本

**优点**:
- ✅ 完全支持Infinity
- ✅ 无需特殊处理
- ✅ 配置驱动
- ✅ 统一接口
- ✅ 性能相当
- ✅ 完全离线

**缺点**:
- 模型文件较大（~4GB）
- 需要更多内存

### 6.2 已下载的Merged版本

**VAGOsolutions/SauerkrautLM-ColQwen3-1.7b-Turbo-v0.1**
- ViDoRe得分：89.3
- 模型大小：~4GB
- 向量维度：512
- 基础模型：Qwen2.5-1.5B-Instruct
- 状态：✅ 已下载

**文件列表**:
```
data/models/SauerkrautLM-ColQwen3-1.7b-Turbo-v0.1/
├── config.json
├── adapter_config.json
├── adapter_model.safetensors
├── tokenizer.json
├── tokenizer_config.json
└── ...
```

**注意**: 包含adapter_config.json，这是LoRA版本的merged

### 6.3 使用方法

#### Python API

```python
import os
import asyncio

# 设置离线模式
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['HF_HOME'] = 'data/models'
os.environ['INFINITY_ANONYMOUS_USAGE_STATS'] = '0'

from infinity_emb import AsyncEmbeddingEngine, EngineArgs

async def use_merged_model():
    engine_args = EngineArgs(
        model_name_or_path="data/models/colqwen3_turbo",
        engine="torch",
        device="cpu",
        dtype="float32",
        trust_remote_code=True,
        model_warmup=False,
        batch_size=8
    )
    
    client = AsyncEmbeddingEngine.from_args(engine_args)
    await client.astart()
    
    # 使用模型
    texts = ["这是一个测试"]
    embeddings = await client.embed(texts, input_type="text")
    
    print(f"嵌入维度: {len(embeddings[0])}")
    
    await client.astop()

asyncio.run(use_merged_model())
```

#### 使用ModelManager

```python
from src.core.models.model_manager import ModelManager, ModelConfig

config = ModelConfig(
    name="VAGOsolutions/SauerkrautLM-ColQwen3-1.7b-Turbo-v0.1",
    engine="torch",
    device="cpu",
    dtype="float32",
    embedding_dim=512,
    trust_remote_code=True,
    pooling_method="mean",
    compile=False,
    batch_size=8,
    local_path="data/models/SauerkrautLM-ColQwen3-1.7b-Turbo-v0.1"
)

model_manager = ModelManager()
await model_manager.initialize({'image_video': config})
```

### 6.4 内存要求

**最低配置**:
- RAM：16GB
- 可用内存：8GB（用于加载模型）

**推荐配置**:
- RAM：32GB
- 可用内存：12GB

**优化建议**:
- 使用较小的batch_size（4-8）
- 使用float32而不是float16（CPU）
- 关闭其他占用内存的程序

---

## 9. 离线使用建议

### 9.1 国内镜像站配置

#### 9.1.1 HuggingFace镜像站（推荐）

使用国内镜像站 `hf-mirror.com` 下载模型，显著提升下载速度：

```bash
# 方法1：设置环境变量
export HF_ENDPOINT=https://hf-mirror.com

# 下载模型（支持断点续传）
huggingface-cli download --resume-download --local-dir-use-symlinks False \
    OFA-Sys/chinese-clip-vit-base-patch16 \
    --local-dir data/models/chinese-clip-vit-base-patch16

# 对于需要登录的模型，添加token参数
huggingface-cli download --resume-download --local-dir-use-symlinks False \
    VAGOsolutions/SauerkrautLM-ColQwen3-1.7b-Turbo-v0.1 \
    --token hf_xxxxxxxxxxxxxxxxxxxx \
    --local-dir data/models/SauerkrautLM-ColQwen3-1.7b-Turbo-v0.1
```

#### 9.1.2 配置自动使用镜像站

在 `config/config.yml` 中设置：

```yaml
models:
  download:
    # 使用国内镜像站
    use_mirror: true
    mirror_url: "https://hf-mirror.com"
    
    # 下载配置
    resume_download: true
    local_dir_use_symlinks: false
    
    # 认证（对于需要登录的模型）
    token: null  # 或设置 HuggingFace token
```

### 9.2 手动模型导入

#### 9.2.1 支持的导入方式

1. **本地目录导入**：
   ```python
   from src.core.models.model_manager import ModelManager
   
   model_manager = ModelManager()
   
   # 导入本地模型
   model_manager.import_local_model(
       model_id="custom_model",
       model_path="/path/to/local/model",
       model_type="text_embedding"
   )
   ```

2. **压缩包导入**：
   ```bash
   # 导入模型压缩包
   python scripts/import_model.py --archive model.tar.gz --output data/models/
   ```

3. **配置文件导入**：
   ```yaml
   # config/config.yml
   models:
     available_models:
       custom_model:
         model_id: "custom_model"
         model_name: "/path/to/local/model"  # 本地路径
         local_path: "/path/to/local/model"
         engine: "torch"
         device: "cpu"
         dtype: "float32"
         embedding_dim: 512
   ```

#### 9.2.2 模型导入验证

导入模型时自动验证：

```python
def validate_model_files(model_path: str) -> bool:
    """验证模型文件完整性"""
    required_files = [
        "config.json",
        "tokenizer.json",
        "tokenizer_config.json",
        "pytorch_model.bin"  # 或 model.safetensors
    ]
    
    for file in required_files:
        file_path = os.path.join(model_path, file)
        if not os.path.exists(file_path):
            logger.error(f"模型文件缺失: {file_path}")
            return False
    
    return True
```

### 9.3 模型验证机制

#### 9.3.1 完整性验证

```python
import hashlib
import json

class ModelValidator:
    """模型验证器"""
    
    @staticmethod
    def validate_model_integrity(model_path: str) -> Dict[str, Any]:
        """
        验证模型完整性
        
        Returns:
            {
                "valid": bool,
                "missing_files": List[str],
                "file_count": int,
                "total_size": int,
                "message": str
            }
        """
        result = {
            "valid": False,
            "missing_files": [],
            "file_count": 0,
            "total_size": 0,
            "message": ""
        }
        
        # 必需文件列表
        required_files = [
            "config.json",
            "tokenizer.json", 
            "tokenizer_config.json",
            "special_tokens_map.json"
        ]
        
        # 可选但重要的文件
        important_files = [
            "pytorch_model.bin",
            "model.safetensors",
            "preprocessor_config.json"
        ]
        
        # 检查必需文件
        for file in required_files:
            file_path = os.path.join(model_path, file)
            if not os.path.exists(file_path):
                result["missing_files"].append(file)
        
        if result["missing_files"]:
            result["message"] = f"模型文件缺失: {result['missing_files']}"
            return result
        
        # 检查重要文件
        has_weight = any(
            os.path.exists(os.path.join(model_path, wf)) 
            for wf in important_files
        )
        
        if not has_weight:
            result["message"] = "模型权重文件缺失"
            return result
        
        # 计算文件统计
        for root, dirs, files in os.walk(model_path):
            for file in files:
                file_path = os.path.join(root, file)
                result["file_count"] += 1
                result["total_size"] += os.path.getsize(file_path)
        
        result["valid"] = True
        result["message"] = "模型完整性验证通过"
        
        return result
    
    @staticmethod
    def compute_model_checksum(model_path: str) -> str:
        """计算模型目录校验和"""
        checksum = hashlib.md5()
        
        for root, dirs, files in os.walk(model_path):
            for file in sorted(files):
                file_path = os.path.join(root, file)
                with open(file_path, 'rb') as f:
                    checksum.update(f.read())
        
        return checksum.hexdigest()
```

### 9.4 离线包支持

#### 9.4.1 预下载模型包

提供预下载的模型包，支持离线安装：

```bash
# 下载完整模型包（含所有推荐模型）
bash scripts/download_models.sh --all --output data/models/

# 下载指定模型
bash scripts/download_models.sh --model chinese-clip-vit-base-patch16 --output data/models/

# 验证模型包完整性
bash scripts/download_models.sh --verify --model chinese-clip-vit-base-patch16
```

#### 9.4.2 离线安装脚本

```bash
#!/bin/bash
# run_offline.sh - 完全离线模式启动脚本

# 设置离线模式环境变量
export TRANSFORMERS_OFFLINE=1
export HF_DATASETS_OFFLINE=1
export HF_HUB_OFFLINE=1
export HF_HOME="data/models"

# 禁用网络请求
export HF_HUB_DISABLE_TELEMETRY=1
export HF_HUB_DISABLE_EXPERIMENTAL_WARNING=1
export HF_HUB_ENABLE_HF_TRANSFER=0

# Infinity离线模式
export INFINITY_LOCAL_MODE=1
export INFINITY_ANONYMOUS_USAGE_STATS=0

# 禁用所有网络请求
export NO_PROXY='*'
export no_proxy='*'

# 启动应用
python3 src/main.py --offline
```

#### 9.4.3 离线安装验证

```python
# verify_offline_mode.py - 验证离线模式配置

import os
import sys

def verify_offline_mode():
    """验证离线模式配置"""
    checks = []
    
    # 检查环境变量
    offline_vars = [
        'TRANSFORMERS_OFFLINE',
        'HF_DATASETS_OFFLINE', 
        'HF_HUB_OFFLINE'
    ]
    
    for var in offline_vars:
        value = os.environ.get(var, '0')
        checks.append({
            'name': f"环境变量 {var}",
            'passed': value == '1',
            'current': value
        })
    
    # 检查模型文件
    model_dirs = [
        'data/models/chinese-clip-vit-base-patch16',
        'data/models/clap-htsat-unfused'
    ]
    
    for model_dir in model_dirs:
        exists = os.path.exists(model_dir)
        checks.append({
            'name': f"模型目录 {model_dir}",
            'passed': exists,
            'current': '存在' if exists else '不存在'
        })
    
    # 检查配置文件
    config_exists = os.path.exists('config/config.yml')
    checks.append({
        'name': '配置文件 config/config.yml',
        'passed': config_exists,
        'current': '存在' if config_exists else '不存在'
    })
    
    return checks

if __name__ == "__main__":
    results = verify_offline_mode()
    
    all_passed = all(r['passed'] for r in results)
    
    print("=" * 60)
    print("离线模式验证结果")
    print("=" * 60)
    
    for result in results:
        status = "✅ 通过" if result['passed'] else "❌ 失败"
        print(f"{status} | {result['name']}: {result['current']}")
    
    print("=" * 60)
    
    if all_passed:
        print("✅ 离线模式配置正确")
        sys.exit(0)
    else:
        print("❌ 离线模式配置有误")
        sys.exit(1)
```

---

## 10. 性能优化建议

### 10.1 启动速度优化

#### 10.1.1 模型懒加载

默认情况下，模型在首次使用时加载，而不是启动时加载：

```python
class EmbeddingEngine:
    """向量化引擎 - 支持懒加载"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._model_manager: Optional[ModelManager] = None
        self._embedding_service: Optional[EmbeddingService] = None
        self._models_loaded = False
        
        # 模型配置
        self._model_configs = {}
        self._init_model_configs()
    
    async def _ensure_models_loaded(self):
        """确保模型已加载（懒加载机制）"""
        if not self._models_loaded:
            await self._load_models()
            self._models_loaded = True
    
    async def _load_models(self):
        """加载模型"""
        self._model_manager = ModelManager()
        await self._model_manager.initialize(self._model_configs)
        self._embedding_service = EmbeddingService(self._model_manager)
    
    async def embed_text(self, text: str) -> List[float]:
        """文本向量化（自动触发模型加载）"""
        await self._ensure_models_loaded()
        return await self._embedding_service.embed_text(text)
```

#### 10.1.2 增量索引

启动时只扫描变化的文件，不扫描全量：

```python
class FileScanner:
    """文件扫描器 - 支持增量扫描"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._last_scan_time = {}
    
    async def scan_incremental(self, directory: str) -> List[Path]:
        """
        增量扫描目录
        
        只扫描自上次扫描以来修改的文件
        """
        current_time = time.time()
        
        # 获取所有文件
        all_files = await self.scan_directory(directory)
        
        # 筛选新增或修改的文件
        changed_files = []
        for file_path in all_files:
            mtime = os.path.getmtime(file_path)
            
            last_mtime = self._last_scan_time.get(str(file_path), 0)
            
            # 文件是新增的或已修改
            if mtime > last_mtime:
                changed_files.append(file_path)
            
            # 更新最后修改时间
            self._last_scan_time[str(file_path)] = mtime
        
        return changed_files
    
    async def scan_full(self, directory: str) -> List[Path]:
        """全量扫描"""
        self._last_scan_time.clear()
        return await self.scan_directory(directory)
```

#### 10.1.3 后台线程加载

模型加载在后台线程执行，避免UI阻塞：

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

class EmbeddingEngine:
    """向量化引擎 - 后台线程加载"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="model_loader")
        self._load_future = None
    
    async def start_background_load(self):
        """后台开始加载模型"""
        if self._load_future is None or self._load_future.done():
            loop = asyncio.get_event_loop()
            self._load_future = loop.run_in_executor(
                self._executor, 
                self._sync_load_models
            )
    
    def _sync_load_models(self):
        """同步加载模型（在后台线程执行）"""
        # 同步加载模型
        self._model_manager = ModelManager()
        self._sync_initialize_models()
    
    async def ensure_loaded(self):
        """确保模型已加载（等待后台加载完成）"""
        if self._load_future:
            await self._load_future
        else:
            await self._ensure_models_loaded()
```

### 10.2 内存优化

#### 10.2.1 内存限制

限制最大内存使用：

```python
import resource
import psutil

class MemoryManager:
    """内存管理器"""
    
    def __init__(self, max_memory_mb: int = 4096):
        self.max_memory_mb = max_memory_mb
        self.process = psutil.Process()
    
    def get_memory_usage(self) -> float:
        """获取当前内存使用（MB）"""
        return self.process.memory_info().rss / (1024 * 1024)
    
    def check_memory_limit(self) -> bool:
        """检查是否超过内存限制"""
        return self.get_memory_usage() < self.max_memory_mb
    
    def get_memory_limit_reached(self) -> bool:
        """是否达到内存限制"""
        return self.get_memory_usage() >= self.max_memory_mb * 0.9
    
    @staticmethod
    def set_memory_limit(soft_limit_mb: int, hard_limit_mb: int = None):
        """
        设置系统内存限制（Linux）
        
        Args:
            soft_limit_mb: 软限制（MB）
            hard_limit_mb: 硬限制（MB），默认为软限制的1.2倍
        """
        if hard_limit_mb is None:
            hard_limit_mb = int(soft_limit_mb * 1.2)
        
        # 设置RLIMIT_AS
        resource.setrlimit(
            resource.RLIMIT_AS,
            (soft_limit_mb * 1024 * 1024, hard_limit_mb * 1024 * 1024)
        )
```

#### 10.2.2 模型自动卸载

长时间不使用时自动卸载模型：

```python
import time
from typing import Dict, Optional
from dataclasses import dataclass, field

@dataclass
class ModelState:
    """模型状态"""
    model_id: str
    loaded: bool = False
    last_used: float = field(default_factory=time.time)
    memory_usage: int = 0

class ModelManager:
    """模型管理器 - 支持自动卸载"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._models: Dict[str, ModelState] = {}
        self._loaded_models: Dict[str, Any] = {}
        
        # 自动卸载配置
        self.auto_unload_enabled = config.get('models', {}).get('auto_unload_enabled', True)
        self.unload_after_seconds = config.get('models', {}).get('unload_after_seconds', 300)  # 5分钟
        self.check_interval = config.get('models', {}).get('unload_check_interval', 60)  # 1分钟
    
    def _check_and_unload_idle_models(self):
        """检查并卸载空闲模型"""
        if not self.auto_unload_enabled:
            return
        
        current_time = time.time()
        models_to_unload = []
        
        for model_id, state in self._models.items():
            if state.loaded:
                idle_time = current_time - state.last_used
                
                # 超过空闲时间则卸载
                if idle_time > self.unload_after_seconds:
                    models_to_unload.append(model_id)
        
        for model_id in models_to_unload:
            self.unload_model(model_id)
            logger.info(f"自动卸载空闲模型: {model_id}")
    
    def mark_model_used(self, model_id: str):
        """标记模型已被使用"""
        if model_id in self._models:
            self._models[model_id].last_used = time.time()
    
    async def start_unload_monitor(self):
        """启动卸载监控任务"""
        while True:
            await asyncio.sleep(self.check_interval)
            self._check_and_unload_idle_models()
```

#### 10.2.3 动态批处理

根据可用内存动态调整批处理大小：

```python
class BatchOptimizer:
    """批处理器 - 动态调整"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_batch_size = config.get('models', {}).get('batch_size', 8)
        self.current_batch_size = self.base_batch_size
        self.memory_manager = MemoryManager()
    
    def get_optimal_batch_size(self) -> int:
        """
        获取最优批处理大小
        
        根据当前内存使用动态调整
        """
        memory_usage = self.memory_manager.get_memory_usage()
        max_memory = self.memory_manager.max_memory_mb
        
        # 内存使用率
        memory_ratio = memory_usage / max_memory
        
        # 根据内存使用率调整批处理大小
        if memory_ratio > 0.8:
            # 内存紧张，减小批处理大小
            self.current_batch_size = max(1, int(self.base_batch_size * 0.5))
        elif memory_ratio > 0.6:
            # 内存较紧张，略微减小批处理大小
            self.current_batch_size = max(2, int(self.base_batch_size * 0.75))
        elif memory_ratio < 0.4:
            # 内存充裕，可以增大批处理大小
            self.current_batch_size = min(16, int(self.base_batch_size * 1.25))
        else:
            # 内存正常，使用基础批处理大小
            self.current_batch_size = self.base_batch_size
        
        return self.current_batch_size
    
    async def process_batch(self, items: List[Any], process_func: callable) -> List[Any]:
        """处理批次"""
        batch_size = self.get_optimal_batch_size()
        results = []
        
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_results = await process_func(batch)
            results.extend(batch_results)
        
        return results
```

### 10.3 GPU资源管理

#### 10.3.1 GPU内存监控

```python
try:
    import torch
    
    class GPUMemoryManager:
        """GPU内存管理器"""
        
        @staticmethod
        def get_gpu_memory_info(device: int = 0) -> Dict[str, float]:
            """
            获取GPU内存信息
            
            Returns:
                {
                    "allocated": GB,
                    "cached": GB,
                    "total": GB,
                    "free": GB,
                    "utilization": %
                }
            """
            if not torch.cuda.is_available():
                return None
            
            torch.cuda.synchronize(device)
            
            memory_info = {
                "allocated": torch.cuda.memory_allocated(device) / (1024**3),
                "cached": torch.cuda.memory_reserved(device) / (1024**3),
                "total": torch.cuda.get_device_properties(device).total_memory / (1024**3),
                "free": (torch.cuda.get_device_properties(device).total_memory - 
                        torch.cuda.memory_allocated(device)) / (1024**3),
                "utilization": torch.cuda.memory_allocated(device) / 
                             torch.cuda.get_device_properties(device).total_memory * 100
            }
            
            return memory_info
        
        @staticmethod
        def get_gpu_utilization(device: int = 0) -> float:
            """获取GPU利用率"""
            if not torch.cuda.is_available():
                return 0.0
            
            # 使用nvidia-smi获取利用率
            import subprocess
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=utilization.gpu', 
                 '--format=csv,noheader,nounits'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return float(result.stdout.strip())
            return 0.0
        
        @staticmethod
        def clear_gpu_cache(device: int = 0):
            """清理GPU缓存"""
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.synchronize(device)
        
        @staticmethod
        def is_gpu_memory_sufficient(required_gb: float, device: int = 0) -> bool:
            """检查GPU内存是否充足"""
            if not torch.cuda.is_available():
                return False
            
            info = GPUMemoryManager.get_gpu_memory_info(device)
            return info["free"] > required_gb
    
except ImportError:
    GPUMemoryManager = None
```

#### 10.3.2 CPU回退机制

GPU不足时自动回退到CPU：

```python
class DeviceManager:
    """设备管理器 - 支持CPU/GPU自动切换"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._preferred_device = config.get('models', {}).get('device', 'auto')
        self._current_device = 'cpu'
        self._gpu_available = False
        self._check_gpu_availability()
    
    def _check_gpu_availability(self):
        """检查GPU是否可用"""
        try:
            import torch
            self._gpu_available = torch.cuda.is_available()
            
            if self._gpu_available:
                # 检查GPU内存
                gpu_memory = GPUMemoryManager.get_gpu_memory_info()
                if gpu_memory and gpu_memory["free"] < 1.0:  # 小于1GB
                    logger.warning("GPU内存不足，自动切换到CPU")
                    self._gpu_available = False
                else:
                    self._current_device = 'cuda'
            
            if not self._gpu_available:
                self._current_device = 'cpu'
            
            logger.info(f"设备选择: {self._current_device}")
            
        except ImportError:
            self._gpu_available = False
            self._current_device = 'cpu'
    
    def get_optimal_device(self, required_memory_gb: float = 2.0) -> str:
        """
        获取最优设备
        
        Args:
            required_memory_gb: 所需GPU内存（GB）
            
        Returns:
            设备类型 ('cuda' 或 'cpu')
        """
        if self._preferred_device == 'cpu':
            return 'cpu'
        
        if self._preferred_device == 'auto':
            if self._gpu_available:
                # 检查内存是否充足
                if GPUMemoryManager and GPUMemoryManager.is_gpu_memory_sufficient(required_memory_gb):
                    return 'cuda'
                else:
                    logger.warning(f"GPU内存不足（需要{required_memory_gb}GB），自动切换到CPU")
                    return 'cpu'
            else:
                return 'cpu'
        
        return self._preferred_device
    
    def get_device_for_model(self, model_id: str) -> str:
        """
        根据模型获取最优设备
        
        不同模型有不同的内存需求
        """
        model_memory_requirements = {
            'chinese_clip_base': 2.0,  # 2GB
            'chinese_clip_large': 4.0,  # 4GB
            'colqwen3_turbo': 8.0,  # 8GB
            'tomoro_colqwen3': 16.0,  # 16GB
            'audio_model': 2.0,  # 2GB
        }
        
        required_memory = model_memory_requirements.get(model_id, 2.0)
        return self.get_optimal_device(required_memory)
```

### 10.4 性能监控

#### 10.4.1 性能指标收集

```python
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from contextlib import contextmanager

@dataclass
class PerformanceMetrics:
    """性能指标"""
    operation: str
    duration_ms: float
    timestamp: float = field(default_factory=time.time)
    memory_used_mb: float = 0.0
    success: bool = True
    error_message: str = ""

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.metrics: List[PerformanceMetrics] = []
        self.memory_manager = MemoryManager()
    
    @contextmanager
    def measure_operation(self, operation: str):
        """测量操作耗时"""
        start_time = time.time()
        memory_before = self.memory_manager.get_memory_usage()
        
        try:
            yield
            success = True
            error_msg = ""
        except Exception as e:
            success = False
            error_msg = str(e)
            raise
        finally:
            duration = (time.time() - start_time) * 1000  # 转换为毫秒
            memory_after = self.memory_manager.get_memory_usage()
            
            metric = PerformanceMetrics(
                operation=operation,
                duration_ms=duration,
                memory_used_mb=memory_after - memory_before,
                success=success,
                error_message=error_msg
            )
            self.metrics.append(metric)
    
    def get_operation_stats(self, operation: str) -> Dict[str, float]:
        """获取操作统计"""
        operations = [m for m in self.metrics if m.operation == operation]
        
        if not operations:
            return {}
        
        durations = [m.duration_ms for m in operations]
        
        return {
            "count": len(operations),
            "avg_duration_ms": sum(durations) / len(durations),
            "min_duration_ms": min(durations),
            "max_duration_ms": max(durations),
            "success_rate": len([m for m in operations if m.success]) / len(operations) * 100
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        summary = {
            "total_operations": len(self.metrics),
            "operations": {},
            "memory_peak_mb": 0
        }
        
        # 按操作分组统计
        operations_dict = {}
        for metric in self.metrics:
            if metric.operation not in operations_dict:
                operations_dict[metric.operation] = []
            operations_dict[metric.operation].append(metric)
        
        for op, metrics_list in operations_dict.items():
            durations = [m.duration_ms for m in metrics_list]
            summary["operations"][op] = {
                "count": len(durations),
                "avg_ms": sum(durations) / len(durations),
                "min_ms": min(durations),
                "max_ms": max(durations)
            }
            
            # 记录内存峰值
            for m in metrics_list:
                if m.memory_used_mb > summary["memory_peak_mb"]:
                    summary["memory_peak_mb"] = m.memory_used_mb
        
        return summary
```

---

## 11. 最佳实践总结

### 11.1 离线使用最佳实践

1. **镜像站配置**
   - 使用 `hf-mirror.com` 镜像站
   - 设置 `HF_ENDPOINT` 环境变量
   - 使用 `huggingface-cli` 下载模型

2. **模型管理**
   - 使用 `scripts/setup_models.py` 管理模型
   - 定期验证模型完整性
   - 使用 `scripts/verify_offline_mode.py` 验证离线配置

3. **离线部署**
   - 使用 `scripts/run_offline.sh` 启动
   - 预下载所有必要模型
   - 配置本地pip源

### 11.2 性能优化最佳实践

1. **启动优化**
   - 使用模型懒加载
   - 使用增量索引
   - 后台线程加载模型

2. **内存优化**
   - 设置内存限制
   - 自动卸载空闲模型
   - 动态调整批处理大小

3. **GPU优化**
   - 监控GPU内存
   - 使用CPU回退
   - 清理GPU缓存

### 11.3 监控和维护

1. **性能监控**
   - 使用 `PerformanceMonitor` 收集指标
   - 定期检查性能摘要
   - 优化慢操作

2. **内存管理**
   - 定期检查内存使用
   - 及时释放资源
   - 监控内存泄漏

3. **模型管理**
   - 定期验证模型完整性
   - 清理不需要的模型
   - 监控模型加载时间

### 7.1 Infinity不支持local_files_only参数

**症状**: `TypeError: EngineArgs.__init__() got an unexpected keyword argument 'local_files_only'`

**原因**: Infinity当前版本不支持`local_files_only`参数

**解决方案**: 
- 设置完整的环境变量
- 使用本地模型路径
- 确保模型文件完整

### 7.2 LoRA模型无法加载

**症状**: `OSError: We couldn't connect to 'https://huggingface.co'`

**原因**: 
- adapter_config.json的base_model_name_or_path指向HuggingFace模型名称
- PEFT在离线模式下无法解析相对路径
- target_modules正则表达式不匹配

**解决方案**:
- 使用Merged版本（推荐）
- 或使用colpali-engine

### 7.3 模型路径问题

**症状**: `OSError: ... is not the path to a directory containing a file named config.json`

**原因**: 相对路径无法正确解析

**解决方案**:
- 使用绝对路径
- 或切换工作目录到模型目录

### 7.4 内存不足

**症状**: 进程被杀死（Killed）

**原因**: 模型太大，内存不足

**解决方案**:
- 减小batch_size（从8降到4或2）
- 关闭其他程序
- 使用更小的模型
- 或使用GPU

---

## 8. 最佳实践

### 8.1 模型选择建议

| 场景 | 推荐模型 | 使用方法 |
|------|---------|---------|
| 生产环境 | VAGOsolutions/SauerkrautLM-ColQwen3-1.7b-Turbo-v0.1 | Infinity |
| 最高精度 | VAGOsolutions/SauerkrautLM-ColQwen3-1.7b-Turbo-v0.1 | Infinity |
| 内存受限 | OFA-Sys/chinese-clip-vit-base-patch16 | Infinity |
| 开发环境 | OFA-Sys/chinese-clip-vit-base-patch16 | Infinity |

### 8.2 配置文件管理

**建议**:
- 使用版本控制管理配置文件
- 为不同环境创建不同配置
- 定期备份配置

**示例**:
```
config/
├── config.yml            # 默认配置
├── config.dev.yml        # 开发环境配置
├── config.prod.yml       # 生产环境配置
└── config.offline.yml    # 离线环境配置
```

### 8.3 模型下载

**使用国内镜像站**:
```bash
export HF_ENDPOINT=https://hf-mirror.com
hf download VAGOsolutions/SauerkrautLM-ColQwen3-1.7b-Turbo-v0.1 \
  --local-dir data/models/SauerkrautLM-ColQwen3-1.7b-Turbo-v0.1
```

**验证模型完整性**:
```bash
# 检查必需文件
ls data/models/SauerkrautLM-ColQwen3-1.7b-Turbo-v0.1/{config.json,tokenizer.json,adapter_model.safetensors}

# 检查文件大小
du -sh data/models/SauerkrautLM-ColQwen3-1.7b-Turbo-v0.1/
```

### 8.4 性能优化

**批处理优化**:
```yaml
models:
  available_models:
    image_video_model:
      batch_size: 8  # 根据内存调整
```

**数据类型优化**:
```yaml
models:
  available_models:
    image_video_model:
      dtype: float32  # CPU使用float32
      engine: torch
```

**设备选择**:
```yaml
models:
  available_models:
    image_video_model:
      device: cpu  # 或 cuda/mps
```

---

## 附录

### A. 依赖安装

```bash
# 基础依赖
pip install infinity-emb[all]

# ColPali支持
pip install colpali-engine

# Flash Attention（可选）
pip install flash-attn --no-build-isolation
```

### B. 参考文档

- [Infinity GitHub](https://github.com/michaelfeil/infinity)
- [ColPali GitHub](https://github.com/illuin-tech/colpali)
- [Infinity 文档](https://michaelfeil.github.io/infinity/)
- [ColQwen3 模型卡](https://huggingface.co/VAGOsolutions/SauerkrautLM-ColQwen3-1.7b-Turbo-v0.1)
- [ViDoRe Leaderboard](https://huggingface.co/spaces/vidore/vidore-leaderboard)

### C. 验证脚本

```bash
# 验证离线模式
python3 scripts/verify_offline_mode.py

# 验证模型文件
python3 -c "
import os
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['HF_HUB_OFFLINE'] = '1'
from transformers import AutoConfig
config = AutoConfig.from_pretrained('data/models/colqwen3_turbo', local_files_only=True)
print(f'✓ 模型类型: {config.model_type}')
print(f'✓ 架构: {config.architectures}')
"
```

---

**版本**: v2.0  
**更新日期**: 2026-01-21  
**作者**: MSearch Team
