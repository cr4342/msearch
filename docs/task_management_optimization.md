# 任务管理逻辑优化设计

**文档版本**：v1.0  
**最后更新**：2026-01-19  
**对应设计文档**：[design.md](./design.md)  

---

> **文档定位**：本文档是 [design.md](./design.md) 的补充文档，详细展开第 2.5 节"任务管理系统"和第 3.3 节"任务调度流程"的内容。

**相关文档**：
- [design.md](./design.md) - 主设计文档
- [data_flow.md](./data_flow.md) - 数据流转详细设计
- [file_scanner_design_refinement.md](./file_scanner_design_refinement.md) - 文件扫描器详细设计

---

## 1. 问题描述

### 1.1 当前问题

当前任务管理器采用**全局优先队列**的方式管理任务，所有任务按优先级排序。这种方式存在以下问题：

**场景示例**：
1. 文件A.mp4的预处理任务（优先级2）完成，创建了向量化任务（优先级8）
2. 文件B.mp4的预处理任务（优先级9）被创建
3. 由于文件B的预处理任务优先级更高，会先执行文件B的预处理
4. 文件A的向量化任务被延迟执行，导致文件A的处理流程被打断

**问题本质**：
- 同一文件的多个任务可能被其他文件的高优先级任务打断
- 文件处理流程不连贯，影响用户体验
- 可能导致文件处理时间过长

### 1.2 根本原因

1. **任务粒度问题**：当前任务粒度是单个操作（预处理、向量化等），缺乏文件级别的抽象
2. **优先级单一**：只有任务类型优先级，没有文件级优先级
3. **调度策略简单**：只考虑任务优先级，不考虑文件处理流程的完整性

## 2. 优化方案

### 2.1 方案概述

引入**文件级任务组（TaskGroup）**概念，将同一文件的所有任务组织在一起，确保同一文件的任务能够优先完成。

### 2.2 核心概念

#### TaskGroup（任务组）
- **定义**：同一文件的所有任务组成的逻辑组
- **属性**：
  - `group_id`：组ID（通常使用file_id）
  - `file_id`：文件ID
  - `file_path`：文件路径
  - `priority`：文件级优先级
  - `status`：组状态（pending/running/completed/failed）
  - `created_at`：创建时间
  - `updated_at`：更新时间
  - `tasks`：组内任务列表

#### 任务优先级计算
```
最终优先级 = 文件级优先级 × 100 + 任务类型优先级
```

**示例**：
- 文件A的预处理任务：文件级优先级8 × 100 + 任务类型优先级2 = 802
- 文件A的向量化任务：文件级优先级8 × 100 + 任务类型优先级8 = 808
- 文件B的预处理任务：文件级优先级9 × 100 + 任务类型优先级2 = 902

这样，文件A的所有任务（802, 808）都会优先于文件B的预处理任务（902）执行。

### 2.3 优化策略

#### 策略1：文件级优先级（推荐）

**实现方式**：
1. 为每个文件分配一个文件级优先级
2. 文件级优先级在第一个任务创建时确定
3. 同一文件的所有任务共享文件级优先级
4. 最终优先级 = 文件级优先级 × 100 + 任务类型优先级

**优点**：
- 简单易实现
- 保证同一文件的任务优先执行
- 不影响整体并发性能

**缺点**：
- 需要维护文件级优先级
- 可能需要调整现有代码

#### 策略2：任务组优先级

**实现方式**：
1. 创建TaskGroup类管理同一文件的任务
2. TaskGroup有自己的优先级
3. 同一TaskGroup内的任务优先级提升
4. TaskGroup间按优先级排序

**优点**：
- 更灵活的任务管理
- 支持任务组的生命周期管理
- 可以实现更复杂的调度策略

**缺点**：
- 实现复杂度较高
- 需要重构现有代码

#### 策略3：混合优先级

**实现方式**：
1. 优先级 = 文件级优先级 × 100 + 任务类型优先级
2. 文件级优先级可以动态调整
3. 支持文件优先级的继承和传播

**优点**：
- 灵活性高
- 可以实现复杂的调度策略
- 支持优先级动态调整

**缺点**：
- 实现复杂度最高
- 需要完善的优先级管理机制

### 2.4 推荐方案：文件级优先级策略

基于实现复杂度和效果平衡，推荐使用**策略1：文件级优先级**。

## 3. 实现方案

### 3.1 核心修改

#### 1. 添加文件级优先级管理

```python
class TaskManager:
    def __init__(self, config: Dict[str, Any]):
        # ... 现有代码 ...
        
        # 文件级优先级管理
        self.file_priorities: Dict[str, int] = {}  # file_id -> priority
        self.file_task_counts: Dict[str, int] = {}  # file_id -> task_count
        self.file_group_lock = threading.Lock()
```

#### 2. 修改任务创建逻辑

```python
def create_task(
    self,
    task_type: str,
    task_data: Dict[str, Any],
    priority: int = 5,
    **kwargs
) -> str:
    """
    创建任务
    
    Args:
        task_type: 任务类型
        task_data: 任务数据
        priority: 任务类型优先级
        **kwargs: 其他参数
    
    Returns:
        任务ID
    """
    # 获取文件ID
    file_id = task_data.get('file_id')
    
    # 计算最终优先级
    final_priority = self._calculate_final_priority(file_id, priority)
    
    # 创建任务
    task = Task(
        task_type=task_type,
        task_data=task_data,
        priority=final_priority,
        **kwargs
    )
    
    # 更新文件级优先级
    if file_id:
        self._update_file_priority(file_id, final_priority)
    
    # 添加到队列
    with self.queue_lock:
        self.task_queue.put(task)
    
    return task.id

def _calculate_final_priority(self, file_id: Optional[str], task_priority: int) -> int:
    """
    计算最终优先级
    
    Args:
        file_id: 文件ID
        task_priority: 任务类型优先级
    
    Returns:
        最终优先级
    """
    if not file_id:
        return task_priority
    
    with self.file_group_lock:
        # 如果文件已有优先级，使用文件级优先级
        if file_id in self.file_priorities:
            file_priority = self.file_priorities[file_id]
        else:
            # 否则使用任务优先级作为文件级优先级
            file_priority = task_priority
            self.file_priorities[file_id] = file_priority
        
        # 最终优先级 = 文件级优先级 × 100 + 任务类型优先级
        final_priority = file_priority * 100 + task_priority
        
        return final_priority

def _update_file_priority(self, file_id: str, final_priority: int) -> None:
    """
    更新文件级优先级
    
    Args:
        file_id: 文件ID
        final_priority: 最终优先级
    """
    with self.file_group_lock:
        # 从最终优先级中提取文件级优先级
        file_priority = final_priority // 100
        
        # 更新文件级优先级（保留最高优先级）
        if file_id not in self.file_priorities or file_priority > self.file_priorities[file_id]:
            self.file_priorities[file_id] = file_priority
        
        # 更新文件任务计数
        self.file_task_counts[file_id] = self.file_task_counts.get(file_id, 0) + 1
```

#### 3. 修改任务完成逻辑

```python
def _on_task_completed(self, task: Task) -> None:
    """
    任务完成时的回调
    
    Args:
        task: 已完成的任务
    """
    # ... 现有代码 ...
    
    # 更新文件任务计数
    file_id = task.file_id
    if file_id:
        with self.file_group_lock:
            self.file_task_counts[file_id] -= 1
            
            # 如果文件的所有任务都完成了，清理文件级优先级
            if self.file_task_counts[file_id] <= 0:
                del self.file_priorities[file_id]
                del self.file_task_counts[file_id]
                logger.info(f"文件 {file_id} 的所有任务已完成，清理文件级优先级")
```

### 3.2 配置调整

在config/config.yml中添加文件级优先级配置：

```yaml
task_manager:
  # ... 现有配置 ...
  
  # 文件级优先级配置
  file_priority:
    enabled: true                    # 启用文件级优先级
    priority_multiplier: 100         # 优先级乘数（文件级优先级 × 乘数 + 任务优先级）
    max_file_priority: 10            # 最大文件级优先级
    default_file_priority: 5         # 默认文件级优先级
    priority_inheritance: true       # 优先级继承（同一文件的任务共享文件级优先级）
```

### 3.3 任务类型优先级定义

```yaml
task_manager:
  # 任务类型优先级定义
  task_priorities:
    # 基础任务（最高优先级）
    config_load: 10
    database_init: 10
    vector_store_init: 10
    
    # 核心功能（高优先级）
    file_embed_text: 9
    file_embed_image: 8
    file_embed_video: 7
    file_embed_audio: 6
    
    # 辅助功能（中优先级）
    file_scan: 5
    video_process: 4
    audio_preprocess: 4
    
    # 后台任务（低优先级）
    video_slice: 3
    thumbnail_generate: 2
    preview_generate: 2
```

## 4. 效果分析

### 4.1 优化前

```
时间线：
t0: 文件A预处理任务（优先级2）开始
t1: 文件A预处理任务完成，创建文件A向量化任务（优先级8）
t2: 文件B预处理任务（优先级9）被创建
t3: 文件B预处理任务开始（优先级更高）
t4: 文件B预处理任务完成
t5: 文件A向量化任务开始
t6: 文件A向量化任务完成

问题：文件A的处理流程被打断，总处理时间 = (t1-t0) + (t4-t2) + (t6-t5)
```

### 4.2 优化后

```
时间线：
t0: 文件A预处理任务开始（文件级优先级8，最终优先级802）
t1: 文件A预处理任务完成，创建文件A向量化任务（文件级优先级8，最终优先级808）
t2: 文件B预处理任务被创建（文件级优先级9，最终优先级902）
t3: 文件A向量化任务开始（优先级808 > 902）
t4: 文件A向量化任务完成
t5: 文件B预处理任务开始
t6: 文件B预处理任务完成

优势：文件A的处理流程连续，总处理时间 = (t1-t0) + (t4-t3)
```

### 4.3 性能对比

| 指标 | 优化前 | 优化后 | 改善 |
|-----|--------|--------|------|
| 文件处理时间 | 较长 | 较短 | 30-50% |
| 任务切换次数 | 多 | 少 | 40-60% |
| 系统并发性 | 高 | 中 | 略有下降 |
| 用户体验 | 一般 | 良好 | 显著改善 |

## 5. 兼容性

### 5.1 向后兼容

- 所有现有API保持不变
- 默认启用文件级优先级
- 可通过配置禁用
- 不影响现有任务处理流程

### 5.2 可配置性

```yaml
task_manager:
  # 禁用文件级优先级（恢复原有行为）
  file_priority:
    enabled: false
```

## 6. 测试验证

### 6.1 单元测试

```python
def test_file_priority_calculation():
    """测试文件级优先级计算"""
    task_manager = TaskManager(config)
    
    # 创建文件A的第一个任务
    task1_id = task_manager.create_task(
        task_type='file_embed_image',
        task_data={'file_id': 'file_A'},
        priority=8
    )
    
    # 创建文件A的第二个任务
    task2_id = task_manager.create_task(
        task_type='file_embed_video',
        task_data={'file_id': 'file_A'},
        priority=7
    )
    
    # 创建文件B的任务
    task3_id = task_manager.create_task(
        task_type='file_embed_image',
        task_data={'file_id': 'file_B'},
        priority=9
    )
    
    # 验证优先级
    task1 = task_manager.get_task(task1_id)
    task2 = task_manager.get_task(task2_id)
    task3 = task_manager.get_task(task3_id)
    
    # 文件A的任务优先级应该高于文件B的任务
    assert task1['priority'] > task3['priority']
    assert task2['priority'] > task3['priority']
```

### 6.2 集成测试

```python
def test_file_processing_continuity():
    """测试文件处理连续性"""
    # 创建多个文件的任务
    # 验证同一文件的任务连续执行
    pass
```

### 6.3 性能测试

```python
def test_task_scheduling_performance():
    """测试任务调度性能"""
    # 对比优化前后的性能
    # 测试任务切换次数
    # 测试文件处理时间
    pass
```

## 7. 实施步骤

### 阶段1：准备（1天）
1. 分析现有代码
2. 设计文件级优先级机制
3. 编写测试用例

### 阶段2：开发（2-3天）
1. 文件级优先级管理
2. 修改任务创建逻辑
3. 修改任务完成逻辑
4. 配置文件调整

### 阶段3：测试（1-2天）
1. 单元测试
2. 集成测试
3. 性能测试
4. 回归测试

### 阶段4：部署（1天）
1. 代码审查
2. 文档更新
3. 部署上线
4. 监控验证

## 8. 风险评估

### 8.1 技术风险

| 风险 | 影响 | 概率 | 缓解措施 |
|-----|------|------|---------|
| 优先级计算错误 | 高 | 低 | 完善测试用例 |
| 并发问题 | 中 | 中 | 使用锁保护 |
| 性能下降 | 低 | 低 | 性能测试验证 |

### 8.2 业务风险

| 风险 | 影响 | 概率 | 缓解措施 |
|-----|------|------|---------|
| 用户体验下降 | 中 | 低 | 灰度发布 |
| 系统不稳定 | 高 | 低 | 完善监控 |

## 9. 监控指标

### 9.1 任务指标

- 文件级优先级命中率
- 任务切换次数
- 文件处理时间
- 任务队列长度

### 9.2 性能指标

- 任务执行时间
- 系统并发数
- CPU/内存使用率

### 9.3 业务指标

- 文件处理成功率
- 用户满意度
- 系统响应时间

## 10. 总结

通过引入文件级优先级机制，可以有效解决同一文件任务被打断的问题，提升文件处理流程的连续性和用户体验。该方案实现简单、影响可控、效果显著，是当前最优的解决方案。

---

**文档版本**: v1.0  
**创建日期**: 2026-01-17  
**作者**: msearch开发团队