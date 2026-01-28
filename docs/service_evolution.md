# msearch 服务化演进设计文档

**文档版本**：v1.0  
**最后更新**：2026-01-28  
**对应设计文档**：[design.md](./design.md)  

---

> **文档定位**：本文档是 [design.md](./design.md) 的补充文档，详细展开第 7 部分"服务化演进（参考）"的内容。本文档聚焦于**未来**向容器化、微服务集群演进的设计，当前阶段请参考主文档的多进程架构设计。

**相关文档**：
- [design.md](./design.md) - 主设计文档（当前架构：本地多进程）
- [deployment.md](./deployment.md) - 部署与运维文档（单机部署）

---

## 目录

1. [演进路线图](#1-演进路线图)
2. [容器化架构设计](#2-容器化架构设计)
3. [微服务集群设计](#3-微服务集群设计)
4. [服务拆分策略](#4-服务拆分策略)
5. [服务间通信设计](#5-服务间通信设计)
6. [部署与运维](#6-部署与运维)

---

## 1. 演进路线图

### 1.1 演进阶段规划

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         服务化演进时间线                                     │
└─────────────────────────────────────────────────────────────────────────────┘

当前 ────────► 阶段二 ────────► 阶段三 ────────► 阶段四
(MVP)         (本地多进程)     (容器化)        (微服务集群)
  │              │              │              │
  │              │              │              └─ Kubernetes + Service Mesh
  │              │              │                 企业级部署
  │              │              │
  │              │              └─ Docker Compose
  │              │                 中小规模部署
  │              │
  │              └─ 多进程架构
  │                 单机性能优化
  │
  └─ 单进程架构
     当前实现
```

### 1.2 各阶段详细规划

#### 阶段一：单机单进程（当前）

**目标**：功能完整，快速迭代

**架构特点**：
- 所有组件在同一个 Python 进程中运行
- 直接内存调用，无序列化开销
- SQLite + LanceDB 本地存储

**适用场景**：
- 个人用户
- 小型工作室
- 开发测试

**技术债务预留**：
- ✅ 抽象接口定义
- ✅ 依赖注入模式
- ✅ 配置驱动架构
- ⏳ 异步任务队列
- ⏳ 状态外置存储

#### 阶段二：本地多进程

**目标**：提升单机性能，解耦计算密集型任务

**架构变化**：
```
主进程 (API + WebUI)
    │
    ├── 子进程 1: Task Scheduler (任务调度)
    ├── 子进程 2: Embedding Worker (向量化)
    └── 子进程 3: File Monitor (文件监控)
```

**通信方式**：
- Unix Domain Socket (Linux/macOS)
- Named Pipe (Windows)
- 共享内存 (大数据传输)

**数据存储**：
- Redis (替代内存队列)
- SQLite → PostgreSQL (可选)

**迁移成本**：低
- 复用现有接口定义
- 只需实现进程间通信适配器

**详细设计**：参考主文档 [design.md](./design.md) 第 1.6 节

#### 阶段三：容器化服务

**目标**：支持分布式部署，水平扩展

**架构变化**：
```
┌─────────────────────────────────────────┐
│           Docker Compose                │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐   │
│  │   API   │ │  Task   │ │ Embed   │   │
│  │ Service │ │ Service │ │ Service │   │
│  └────┬────┘ └────┬────┘ └────┬────┘   │
│       └───────────┴───────────┘         │
│                   │                     │
│            ┌──────┴──────┐              │
│            │   Redis     │              │
│            │  (Queue)    │              │
│            └─────────────┘              │
└─────────────────────────────────────────┘
```

**技术栈**：
- Docker + Docker Compose
- gRPC (服务间通信)
- Redis (消息队列 + 缓存)
- MinIO (对象存储)

**迁移成本**：中
- 需要编写 Dockerfile
- 实现 gRPC 服务包装器
- 配置服务发现

**详细设计**：参考本文档第 2 节

#### 阶段四：微服务集群

**目标**：企业级部署，高可用，弹性伸缩

**架构变化**：
```
┌─────────────────────────────────────────┐
│         Kubernetes Cluster              │
│  ┌─────────────────────────────────┐    │
│  │     Ingress Controller          │    │
│  │    (Nginx / Traefik)            │    │
│  └─────────────┬───────────────────┘    │
│                │                        │
│  ┌─────────────┼─────────────┐          │
│  │             │             │          │
│  ▼             ▼             ▼          │
│ ┌────┐    ┌────────┐    ┌────────┐     │
│ │API │◄──►│ Search │◄──►│ Embed  │     │
│ │Pod │    │  Pod   │    │  Pod   │     │
│ └────┘    └────────┘    └────────┘     │
│              │    ▲         │    ▲      │
│              ▼    │         ▼    │      │
│         ┌────────┐│    ┌────────┐│      │
│         │Milvus  ││    │ GPU    ││      │
│         │Cluster ││    │ Nodes  ││      │
│         └────────┘│    └────────┘│      │
│                   │              │      │
│              ┌────┴──────────────┘      │
│              │    etcd (Config)         │
│              └───────────────────────────┘
└─────────────────────────────────────────┘
```

**技术栈**：
- Kubernetes
- Istio / Linkerd (Service Mesh)
- Milvus (分布式向量数据库)
- Kafka (消息队列)
- Prometheus + Grafana (监控)

**迁移成本**：高
- 需要 Kubernetes 运维能力
- 服务网格配置
- 分布式追踪集成

**详细设计**：参考本文档第 3 节

### 1.3 演进策略建议

**保持向后兼容**：
- 接口版本控制 (v1, v2)
- 配置格式兼容
- 数据迁移工具

**渐进式拆分**：
1. 先拆分 Embedding Service（资源隔离需求最强）
2. 再拆分 Task Service（需要高可用）
3. 最后拆分 Storage Service（数据迁移复杂）

**技术选型原则**：
- 优先使用云原生技术
- 避免供应商锁定
- 保持技术栈简洁

---

## 2. 容器化架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         msearch 容器化架构图                                 │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                              接入层 (Presentation)                           │
├──────────────────┬──────────────────┬──────────────────┬────────────────────┤
│      WebUI       │    Desktop UI    │       CLI        │   Python SDK       │
│     (React)      │    (PySide6)     │   (Click)        │   (gRPC Client)    │
└────────┬─────────┴────────┬─────────┴────────┬─────────┴────────┬───────────┘
         │                  │                  │                  │
         └──────────────────┴──────────────────┴──────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              API Gateway                                     │
│                    (Nginx / Kong / Traefik)                                  │
│     功能：认证、路由、限流、负载均衡、日志、监控                                  │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          │                       │                       │
          ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Search Service │    │   Task Service  │    │  File Service   │
│    (Python)     │    │    (Python)     │    │    (Python)     │
│                 │    │                 │    │                 │
│ - 向量检索       │    │ - 任务调度       │    │ - 文件扫描       │
│ - 结果排序       │    │ - 队列管理       │    │ - 元数据提取     │
│ - 搜索API        │    │ - 状态跟踪       │    │ - 文件监控       │
└────────┬────────┘    └────────┬────────┘    └────────┬────────┘
         │                      │                      │
         │              ┌───────┴───────┐              │
         │              │               │              │
         ▼              ▼               ▼              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      Embedding Service (Python + GPU)                        │
│                                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ Text Embed  │  │ Image Embed │  │ Video Embed │  │    Audio Embed      │ │
│  │  (CLIP)     │  │   (CLIP)    │  │   (CLIP)    │  │      (CLAP)         │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      Storage Service                                         │
│                                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  Vector DB  │  │  Metadata   │  │    Cache    │  │    Object Store     │ │
│  │ (Milvus)    │  │ (PostgreSQL)│  │   (Redis)   │  │    (MinIO)          │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 服务拆分

#### 2.2.1 API Gateway

**职责**：
- 请求路由
- 认证与授权
- 限流与熔断
- 日志记录
- 监控指标收集

**技术选型**：
- Kong
- Nginx + Lua
- Traefik

#### 2.2.2 Search Service

**职责**：
- 接收搜索请求
- 执行向量检索
- 结果排序与融合
- 返回搜索结果

**依赖**：
- Vector DB (Milvus)
- Metadata DB (PostgreSQL)
- Redis (缓存)

#### 2.2.3 Task Service

**职责**：
- 任务调度
- 队列管理
- 状态跟踪
- 任务重试

**依赖**：
- Redis (任务队列)
- PostgreSQL (任务状态)

#### 2.2.4 File Service

**职责**：
- 文件扫描
- 元数据提取
- 文件监控
- 文件上传/下载

**依赖**：
- Object Store (MinIO)
- PostgreSQL (文件元数据)

#### 2.2.5 Embedding Service

**职责**：
- 向量推理
- 模型管理
- 批处理优化

**依赖**：
- GPU 资源
- Model Cache

#### 2.2.6 Storage Service

**职责**：
- 向量存储
- 元数据存储
- 缓存管理
- 对象存储

**组件**：
- Milvus (向量数据库)
- PostgreSQL (关系数据库)
- Redis (缓存)
- MinIO (对象存储)

### 2.3 Docker Compose 配置

```yaml
# docker-compose.yml
version: '3.8'

services:
  # API Gateway
  gateway:
    image: kong:3.0
    ports:
      - "8000:8000"
      - "8443:8443"
      - "8001:8001"
      - "8444:8444"
    environment:
      KONG_DATABASE: "off"
      KONG_DECLARATIVE_CONFIG: /kong/declarative/kong.yml
    volumes:
      - ./config/kong:/kong/declarative
    depends_on:
      - search-service
      - task-service
      - file-service

  # Search Service
  search-service:
    build:
      context: .
      dockerfile: services/search/Dockerfile
    environment:
      - MILVUS_HOST=milvus
      - POSTGRES_HOST=postgres
      - REDIS_HOST=redis
    depends_on:
      - milvus
      - postgres
      - redis

  # Task Service
  task-service:
    build:
      context: .
      dockerfile: services/task/Dockerfile
    environment:
      - REDIS_HOST=redis
      - POSTGRES_HOST=postgres
    depends_on:
      - redis
      - postgres

  # File Service
  file-service:
    build:
      context: .
      dockerfile: services/file/Dockerfile
    environment:
      - MINIO_HOST=minio
      - POSTGRES_HOST=postgres
    volumes:
      - ./data/uploads:/uploads
    depends_on:
      - minio
      - postgres

  # Embedding Service
  embedding-service:
    build:
      context: .
      dockerfile: services/embedding/Dockerfile
    runtime: nvidia
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
      - MILVUS_HOST=milvus
      - REDIS_HOST=redis
    depends_on:
      - milvus
      - redis
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  # Vector Database
  milvus:
    image: milvusdb/milvus:v2.3.0
    ports:
      - "19530:19530"
    volumes:
      - milvus_data:/var/lib/milvus

  # Metadata Database
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: msearch
      POSTGRES_PASSWORD: msearch
      POSTGRES_DB: msearch
    volumes:
      - postgres_data:/var/lib/postgresql/data

  # Cache
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  # Object Storage
  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      MINIO_ROOT_USER: msearch
      MINIO_ROOT_PASSWORD: msearch123
    volumes:
      - minio_data:/data

volumes:
  milvus_data:
  postgres_data:
  redis_data:
  minio_data:
```

---

## 3. 微服务集群设计

### 3.1 整体架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         msearch 微服务集群架构图                              │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌─────────────────┐
                              │   Ingress       │
                              │  Controller     │
                              │ (Nginx/Traefik) │
                              └────────┬────────┘
                                       │
                              ┌────────┴────────┐
                              │   API Gateway   │
                              │   (Kong/Istio)  │
                              └────────┬────────┘
                                       │
          ┌────────────────────────────┼────────────────────────────┐
          │                            │                            │
          ▼                            ▼                            ▼
┌─────────────────┐          ┌─────────────────┐          ┌─────────────────┐
│  Search Service │          │   Task Service  │          │  File Service   │
│   (3 replicas)  │          │   (2 replicas)  │          │   (2 replicas)  │
└────────┬────────┘          └────────┬────────┘          └────────┬────────┘
         │                            │                            │
         └────────────────────────────┼────────────────────────────┘
                                      │
                                      ▼
                    ┌───────────────────────────────────┐
                    │      Service Mesh (Istio)         │
                    └───────────────────────────────────┘
                                      │
         ┌────────────────────────────┼────────────────────────────┐
         │                            │                            │
         ▼                            ▼                            ▼
┌─────────────────┐          ┌─────────────────┐          ┌─────────────────┐
│ Embedding       │          │   Milvus        │          │   PostgreSQL    │
│ Service         │          │   Cluster       │          │   Cluster       │
│ (GPU Nodes)     │          │                 │          │                 │
│                 │          │ - Query Node    │          │ - Primary       │
│ - Node 1 (GPU0) │          │ - Data Node     │          │ - Replica       │
│ - Node 2 (GPU1) │          │ - Index Node    │          │                 │
└─────────────────┘          └─────────────────┘          └─────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                         基础设施层                                           │
├─────────────────┬─────────────────┬─────────────────┬───────────────────────┤
│   Kubernetes    │   etcd          │   Prometheus    │     Grafana           │
│   Cluster       │   (Config)      │   (Metrics)     │     (Dashboard)       │
└─────────────────┴─────────────────┴─────────────────┴───────────────────────┘
```

### 3.2 Kubernetes 部署配置

#### 3.2.1 Search Service

```yaml
# k8s/search-service.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: search-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: search-service
  template:
    metadata:
      labels:
        app: search-service
    spec:
      containers:
        - name: search-service
          image: msearch/search-service:latest
          ports:
            - containerPort: 8080
          env:
            - name: MILVUS_HOST
              value: "milvus-cluster"
            - name: POSTGRES_HOST
              value: "postgres-cluster"
          resources:
            requests:
              memory: "512Mi"
              cpu: "500m"
            limits:
              memory: "1Gi"
              cpu: "1000m"
---
apiVersion: v1
kind: Service
metadata:
  name: search-service
spec:
  selector:
    app: search-service
  ports:
    - port: 8080
      targetPort: 8080
```

#### 3.2.2 Embedding Service (GPU)

```yaml
# k8s/embedding-service.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: embedding-service
spec:
  replicas: 2
  selector:
    matchLabels:
      app: embedding-service
  template:
    metadata:
      labels:
        app: embedding-service
    spec:
      nodeSelector:
        accelerator: nvidia-gpu
      containers:
        - name: embedding-service
          image: msearch/embedding-service:latest
          ports:
            - containerPort: 8080
          resources:
            limits:
              nvidia.com/gpu: 1
            requests:
              memory: "4Gi"
              cpu: "2000m"
```

### 3.3 服务网格配置 (Istio)

```yaml
# istio/destination-rules.yaml
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: search-service
spec:
  host: search-service
  trafficPolicy:
    loadBalancer:
      simple: LEAST_CONN
    connectionPool:
      tcp:
        maxConnections: 100
      http:
        http1MaxPendingRequests: 50
        maxRequestsPerConnection: 10
---
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: msearch-routes
spec:
  hosts:
    - "*"
  gateways:
    - msearch-gateway
  http:
    - match:
        - uri:
            prefix: /api/search
      route:
        - destination:
            host: search-service
            port:
              number: 8080
      timeout: 30s
      retries:
        attempts: 3
        perTryTimeout: 10s
```

---

## 4. 服务拆分策略

### 4.1 拆分原则

**按业务能力拆分**：
- Search Service：搜索能力
- Task Service：任务调度能力
- File Service：文件管理能力
- Embedding Service：向量化能力

**按资源需求拆分**：
- Embedding Service：GPU 密集型
- Task Service：CPU 密集型
- Search Service：IO 密集型

**按扩展性需求拆分**：
- Embedding Service：需要水平扩展
- Search Service：需要负载均衡
- File Service：需要数据一致性

### 4.2 拆分顺序建议

**第一阶段**：Embedding Service
- 资源隔离需求最强
- 独立部署 GPU 节点
- 不影响其他服务

**第二阶段**：Task Service
- 需要高可用
- 独立扩展任务处理能力
- 解耦任务调度

**第三阶段**：File Service
- 数据迁移复杂
- 需要对象存储
- 文件上传/下载独立

**第四阶段**：Search Service
- 需要负载均衡
- 独立优化检索性能
- 缓存策略独立

### 4.3 数据一致性

**分布式事务**：
- Saga 模式
- 最终一致性
- 补偿事务

**数据同步**：
- 事件驱动 (Event Sourcing)
- CQRS 模式
- 数据变更捕获 (CDC)

---

## 5. 服务间通信设计

### 5.1 同步通信

**gRPC**：
- 高性能二进制协议
- 强类型接口
- 流式支持
- 服务间通信首选

**REST API**：
- 客户端兼容性
- 简单调试
- 外部接口

### 5.2 异步通信

**消息队列**：
- Kafka：高吞吐量
- RabbitMQ：可靠消息
- NATS：轻量级

**事件总线**：
- 解耦服务
- 事件驱动架构
- 最终一致性

### 5.3 服务发现

**Consul**：
- 服务注册
- 健康检查
- 键值存储

**etcd**：
- Kubernetes 原生
- 高可用
- 强一致性

**Kubernetes DNS**：
- 原生支持
- 自动服务发现
- 无额外依赖

---

## 6. 部署与运维

### 6.1 CI/CD 流程

```
代码提交
    │
    ▼
┌─────────────┐
│   Build     │
│   镜像构建   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│    Test     │
│   单元测试   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Push      │
│   镜像推送   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Deploy    │
│   部署到 K8s │
└─────────────┘
```

### 6.2 监控与告警

**Prometheus**：
- 指标收集
- 时序数据库
- 查询语言 (PromQL)

**Grafana**：
- 可视化仪表盘
- 告警配置
- 多数据源支持

**Jaeger**：
- 分布式追踪
- 性能分析
- 依赖分析

### 6.3 日志管理

**ELK Stack**：
- Elasticsearch：日志存储
- Logstash：日志处理
- Kibana：日志可视化

**Fluentd**：
- 日志收集
- 统一日志格式
- 多目标输出

---

## 附录

### A. 服务接口定义

详细的服务接口定义参考主文档 [design.md](./design.md) 第六部分。

### B. 配置示例

完整的配置示例参考 `config/examples/` 目录。

### C. 迁移指南

从本地多进程迁移到容器化的详细步骤参考 `docs/migration.md`。

---

**文档结束**
