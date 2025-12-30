# MSearch 系统架构图

本文档使用Mermaid图表展示系统架构，便于理解系统设计。

---

## 1. 系统总体架构

```mermaid
graph TB
    subgraph "用户界面层"
        UI[PySide6 桌面应用]
    end
    
    subgraph "API层"
        API[FastAPI 服务]
    end
    
    subgraph "业务逻辑层"
        Search[检索服务]
        Process[处理服务]
        Monitor[文件监控]
    end
    
    subgraph "核心引擎层"
        Embed[Embedding引擎]
        Media[媒体处理器]
        Smart[智能检索引擎]
    end
    
    subgraph "存储层"
        DB[(SQLite<br/>元数据)]
        Vector[(Milvus Lite<br/>向量数据)]
        Files[文件系统]
    end
    
    subgraph "AI推理层"
        Infinity[Infinity引擎]
        Models[AI模型<br/>CLIP/CLAP/Whisper]
    end
    
    UI --> API
    API --> Search
    API --> Process
    Process --> Monitor
    
    Search --> Smart
    Search --> Embed
    Process --> Media
    Process --> Embed
    
    Smart --> Vector
    Smart --> DB
    Embed --> Infinity
    Media --> Files
    
    Infinity --> Models
    
    Process --> DB
    Process --> Vector
    Monitor --> Files
```

---

## 2. 文件处理流程

```mermaid
sequenceDiagram
    participant Monitor as 文件监控
    participant Queue as 任务队列
    participant Processor as 媒体处理器
    participant Embed as 向量化引擎
    participant DB as SQLite
    participant Vector as Milvus Lite
    
    Monitor->>Queue: 检测到新文件
    Queue->>Processor: 提取处理任务
    
    alt 图像文件
        Processor->>Processor: 降采样处理
        Processor->>Embed: 图像向量化
    else 视频文件
        Processor->>Processor: 场景切分
        Processor->>Processor: 提取关键帧
        Processor->>Processor: 分离音频
        Processor->>Embed: 帧向量化
        Processor->>Embed: 音频向量化
    else 音频文件
        Processor->>Processor: 格式转换
        Processor->>Embed: 音频向量化
        Processor->>Embed: 语音转文本
    end
    
    Embed->>Vector: 存储向量
    Processor->>DB: 存储元数据
    DB-->>Monitor: 更新文件状态
```

---

## 3. 多模态检索流程

```mermaid
flowchart TD
    Start[用户输入查询] --> Parse[查询解析]
    
    Parse --> Detect{查询类型识别}
    
    Detect -->|纯文本| TextQuery[文本查询]
    Detect -->|包含人名| PersonQuery[人名查询]
    Detect -->|图像文件| ImageQuery[图像查询]
    Detect -->|音频文件| AudioQuery[音频查询]
    Detect -->|复杂查询| MultiQuery[多模态查询]
    
    TextQuery --> TextEmbed[文本向量化]
    PersonQuery --> FaceSearch[人脸检索]
    ImageQuery --> ImageEmbed[图像向量化]
    AudioQuery --> AudioEmbed[音频向量化]
    MultiQuery --> MultiEmbed[多模态向量化]
    
    TextEmbed --> VectorSearch[向量检索]
    FaceSearch --> LayeredSearch[分层检索]
    ImageEmbed --> VectorSearch
    AudioEmbed --> VectorSearch
    MultiEmbed --> FusionSearch[融合检索]
    
    VectorSearch --> Rank[结果排序]
    LayeredSearch --> Rank
    FusionSearch --> Rank
    
    Rank --> Filter[结果过滤]
    Filter --> Return[返回结果]
```

---

## 4. 数据库ER图

```mermaid
erDiagram
    FILES ||--o{ VIDEO_SEGMENTS : contains
    FILES ||--o{ FILE_RELATIONSHIPS : source
    FILES ||--o{ FILE_RELATIONSHIPS : derived
    FILES ||--o{ TASKS : has
    FILES ||--o{ FILE_FACES : contains
    PERSONS ||--o{ FILE_FACES : identified_in
    
    FILES {
        text id PK
        text file_path UK
        text file_name
        text file_type
        text file_category
        text source_file_id FK
        integer file_size
        text file_hash
        datetime created_at
        datetime modified_at
        datetime indexed_at
        text status
        boolean can_delete
    }
    
    VIDEO_SEGMENTS {
        text segment_id PK
        text file_uuid FK
        integer segment_index
        real start_time
        real end_time
        real duration
        boolean scene_boundary
        boolean has_audio
        integer frame_count
    }
    
    FILE_RELATIONSHIPS {
        text id PK
        text source_file_id FK
        text derived_file_id FK
        text relationship_type
        text metadata
    }
    
    TASKS {
        text id PK
        text file_id FK
        text task_type
        text status
        real progress
        integer priority
        integer retry_count
    }
    
    PERSONS {
        text id PK
        text name UK
        text aliases
        text description
    }
    
    FILE_FACES {
        text id PK
        text file_id FK
        text person_id FK
        real timestamp
        real confidence
        text bbox
    }
```

---

## 5. 向量存储结构

```mermaid
graph LR
    subgraph "Milvus Lite Collections"
        IC[image_vectors<br/>维度:512<br/>索引:IVF_FLAT]
        VC[video_vectors<br/>维度:512<br/>索引:IVF_FLAT]
        AC[audio_vectors<br/>维度:512<br/>索引:IVF_FLAT]
        FC[face_vectors<br/>维度:512<br/>索引:IVF_FLAT]
    end
    
    subgraph "Payload字段"
        IC --> ICP[file_id<br/>file_path<br/>file_type<br/>created_at]
        VC --> VCP[file_uuid<br/>segment_id<br/>timestamp<br/>file_path]
        AC --> ACP[file_id<br/>audio_type<br/>start_time<br/>end_time]
        FC --> FCP[file_id<br/>person_id<br/>timestamp<br/>confidence]
    end
```

---

## 6. 任务状态机

```mermaid
stateDiagram-v2
    [*] --> Pending: 创建任务
    
    Pending --> Processing: 开始处理
    Pending --> Cancelled: 取消任务
    
    Processing --> Completed: 处理成功
    Processing --> Failed: 处理失败
    Processing --> Paused: 暂停处理
    
    Failed --> Pending: 重试
    Failed --> Cancelled: 放弃
    
    Paused --> Processing: 恢复处理
    Paused --> Cancelled: 取消
    
    Completed --> [*]
    Cancelled --> [*]
```

---

## 7. 部署架构（单机模式）

```mermaid
graph TB
    subgraph "用户机器"
        subgraph "应用进程"
            UI[PySide6 UI<br/>内存:512MB]
            API[FastAPI服务<br/>内存:1GB<br/>CPU:2核]
        end
        
        subgraph "AI推理"
            Infinity[Infinity引擎<br/>GPU:4GB或CPU:4核]
            Models[AI模型文件<br/>磁盘:5GB]
        end
        
        subgraph "数据存储"
            SQLite[SQLite数据库<br/>磁盘:100MB+]
            Milvus[Milvus Lite<br/>内存:2GB<br/>磁盘:根据数据量]
            Files[文件系统<br/>磁盘:50GB+]
        end
    end
    
    UI --> API
    API --> Infinity
    API --> SQLite
    API --> Milvus
    API --> Files
    Infinity --> Models
```

---

## 8. 时间戳精度设计

```mermaid
graph TD
    Video[原始视频<br/>30fps] --> Split[场景切分]
    
    Split --> Seg1[Segment 1<br/>0-10秒]
    Split --> Seg2[Segment 2<br/>10-20秒]
    Split --> Seg3[Segment 3<br/>20-30秒]
    
    Seg1 --> Frame1[帧1: 0.000s<br/>帧2: 0.033s<br/>帧3: 0.067s]
    Seg2 --> Frame2[帧1: 10.000s<br/>帧2: 10.033s<br/>帧3: 10.067s]
    Seg3 --> Frame3[帧1: 20.000s<br/>帧2: 20.033s<br/>帧3: 20.067s]
    
    Frame1 --> Vector1[向量存储<br/>segment_id + timestamp]
    Frame2 --> Vector2[向量存储<br/>segment_id + timestamp]
    Frame3 --> Vector3[向量存储<br/>segment_id + timestamp]
    
    Vector1 --> Search[检索时计算<br/>绝对时间戳]
    Vector2 --> Search
    Vector3 --> Search
    
    Search --> Result[返回结果<br/>精度: ±0.033s]
```

---

## 9. 智能检索权重分配

```mermaid
graph LR
    Query[用户查询:<br/>"张三在会议上讲话"] --> Parse[查询解析]
    
    Parse --> Detect{检测查询特征}
    
    Detect --> Person[人名:张三]
    Detect --> Scene[场景:会议]
    Detect --> Action[动作:讲话]
    
    Person --> Weight1[人脸检索<br/>权重:0.5]
    Scene --> Weight2[图像检索<br/>权重:0.3]
    Action --> Weight3[音频检索<br/>权重:0.2]
    
    Weight1 --> Fusion[结果融合<br/>加权平均]
    Weight2 --> Fusion
    Weight3 --> Fusion
    
    Fusion --> Final[最终结果]
```

---

## 10. 错误处理流程

```mermaid
flowchart TD
    Start[操作开始] --> Try{执行操作}
    
    Try -->|成功| Success[返回结果]
    Try -->|失败| Classify{错误分类}
    
    Classify -->|可重试| Retry{重试次数<br/>< 最大值?}
    Classify -->|不可重试| Log[记录错误日志]
    
    Retry -->|是| Wait[指数退避等待]
    Retry -->|否| Log
    
    Wait --> Try
    
    Log --> Degrade{是否需要降级?}
    
    Degrade -->|是| Fallback[启用降级方案]
    Degrade -->|否| Alert[触发告警]
    
    Fallback --> Return[返回降级结果]
    Alert --> Return[返回错误信息]
    
    Success --> End[结束]
    Return --> End
```

---

## 使用说明

这些图表可以：
1. 直接在支持Mermaid的Markdown查看器中渲染
2. 使用Mermaid Live Editor编辑：https://mermaid.live/
3. 导出为PNG/SVG图片用于文档
4. 集成到文档网站（如GitBook、Docusaurus）

**建议**: 将这些图表嵌入到design.md的相应章节中，提升可读性。
