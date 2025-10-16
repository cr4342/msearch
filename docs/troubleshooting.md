# 故障排除指南

> **文档导航**: [文档索引](README.md) | [需求文档](requirements.md) | [设计文档](design.md) | [开发计划](development_plan.md) | [API文档](api_documentation.md) | [开发环境搭建](development_environment.md) | [部署与运维指南](deployment_and_operations.md) | [技术实现指南](technical_implementation.md)

## 1. 问题分类与优先级

### 1.1 问题严重程度分级

| 级别 | 描述 | 响应时间 | 示例 |
|------|------|----------|------|
| **P0 - 紧急** | 系统完全不可用 | 立即处理 | 服务无法启动、数据库连接失败 |
| **P1 - 高优先级** | 核心功能异常 | 2小时内 | 搜索功能失效、文件处理失败 |
| **P2 - 中优先级** | 部分功能异常 | 24小时内 | 缩略图生成失败、统计数据错误 |
| **P3 - 低优先级** | 性能或体验问题 | 72小时内 | 响应速度慢、界面显示异常 |

## 2. 系统启动问题

### 2.1 服务无法启动

**问题现象**: 运行启动脚本后，服务没有正常启动，或启动后立即崩溃。

**解决方案**:
```bash
# 检查Python路径和环境
python --version  # 确认Python 3.9+
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
source venv/bin/activate  # 激活虚拟环境
pip install -r requirements.txt  # 重新安装依赖

# 检查端口占用
lsof -i :8000  # 查找占用端口的进程
kill -9 <PID>  # 终止占用进程
python -m uvicorn main:app --port 8001  # 或使用不同端口
```

**预防措施**:
- 使用虚拟环境隔离依赖
- 配置文件中设置可配置的端口
- 使用启动脚本自动设置环境

### 2.2 依赖服务连接失败

**问题现象**: 应用无法连接到Qdrant或Infinity服务。

**解决方案**:
```bash
# 检查Qdrant服务
curl http://localhost:6333/health
docker ps | grep qdrant
docker restart qdrant

# 检查Infinity服务
curl http://localhost:7997/health
curl http://localhost:7998/health
curl http://localhost:7999/health
python -m infinity_emb v2 --model-id openai/clip-vit-base-patch32 --port 7997 &
```

**预防措施**:
- 实现服务健康检查机制
- 配置服务自动重启
- 使用Docker Compose管理多服务

## 3. 模型相关问题

### 3.1 模型下载失败

**问题现象**: 运行模型下载脚本后，部分或全部模型下载失败。

**解决方案**:
```bash
# 使用国内镜像
export HF_ENDPOINT=https://hf-mirror.com

# 手动下载模型
huggingface-cli download openai/clip-vit-base-patch32 --local-dir ./models/clip

# 重新运行下载脚本
./scripts/download_model_resources.sh
```

**预防措施**:
- 预先下载模型到本地
- 配置多个下载源
- 实现下载重试机制

### 3.2 GPU内存不足

**问题现象**: 处理大型文件或批量请求时，出现GPU内存不足错误。

**解决方案**:
```bash
# 检查GPU内存使用
nvidia-smi

# 减少批处理大小
# 修改config.yml中的batch_size参数

# 使用CPU模式
export CUDA_VISIBLE_DEVICES=""

# 清理GPU缓存
python -c "import torch; torch.cuda.empty_cache()"

# 重启相关服务
pkill -f infinity_emb
```

**预防措施**:
- 监控GPU内存使用情况
- 实现动态批处理大小调整
- 配置内存使用限制

## 4. 文件处理问题

### 4.1 文件上传失败

**问题现象**: 通过API或Web界面上传文件时失败。

**解决方案**:
```bash
# 检查文件大小限制
curl http://localhost:8000/api/v1/system/config | jq '.data.processing_limits'

# 检查文件格式支持
curl http://localhost:8000/api/v1/system/config | jq '.data.supported_formats'

# 转换文件格式
ffmpeg -i input.xyz -c:v libx264 output.mp4
```

**预防措施**:
- 在上传前验证文件格式
- 设置合理的文件大小限制
- 提供格式转换工具

### 4.2 文件处理超时

**问题现象**: 文件处理过程中超时。

**解决方案**:
```bash
# 检查文件大小
ls -lh /path/to/large_file.mp4

# 增加超时时间
# 修改config.yml中的processing_timeout

# 检查系统资源
free -h  # 检查内存
df -h    # 检查磁盘空间
```

**预防措施**:
- 实现文件预处理和压缩
- 配置分布式处理
- 优化处理队列机制

## 5. 数据库问题

### 5.1 Qdrant连接问题

**问题现象**: 无法连接到Qdrant向量数据库。

**解决方案**:
```bash
# 检查Qdrant服务状态
docker ps | grep qdrant
telnet localhost 6333

# 重启Qdrant服务
docker restart qdrant

# 重新创建容器
docker rm -f qdrant
docker run -d --name qdrant -p 6333:6333 -v $(pwd)/data/qdrant:/qdrant/storage qdrant/qdrant:latest
```

**预防措施**:
- 配置Qdrant健康检查
- 实现自动重连机制
- 定期备份向量数据

### 5.2 SQLite数据库锁定

**问题现象**: SQLite数据库被锁定。

**解决方案**:
```bash
# 检查数据库文件权限
ls -la data/msearch.db

# 查找占用数据库的进程
lsof data/msearch.db
kill -9 <PID>

# 修复数据库
sqlite3 data/msearch.db "PRAGMA integrity_check;"

# 重建数据库（如果损坏）
mv data/msearch.db data/msearch.db.backup
python scripts/init_database.py
```

**预防措施**:
- 使用连接池管理数据库连接
- 实现事务超时机制
- 定期备份数据库

## 6. 搜索功能问题

### 6.1 搜索结果为空

**问题现象**: 执行搜索查询后，没有返回任何结果。

**解决方案**:
- 确认文件是否已成功索引
- 降低相似度阈值
- 检查Qdrant服务是否正常运行
- 验证向量数据是否正确存储

**预防措施**:
- 实现索引状态监控
- 配置合理的搜索参数
- 定期检查数据一致性

### 6.2 搜索结果不精准

**问题现象**: 搜索结果与查询意图不匹配或相关性不高。

**解决方案**:
- 提高相似度阈值
- 调整多模态融合权重
- 尝试使用不同的模型版本
- 检查索引过程是否有错误

**预防措施**:
- 根据数据特点选择合适的模型
- 优化搜索算法和索引结构
- 实现查询预加载和预热机制

## 7. 性能优化问题

### 7.1 系统响应缓慢

**问题现象**: 系统处理请求的时间过长，响应缓慢。

**诊断步骤**:
```bash
# 检查系统资源
top
htop
iotop

# 检查数据库性能
curl http://localhost:6333/metrics

# 性能分析
python -m cProfile -o profile.stats main.py
```

**解决方案**:
- 增加系统CPU、内存或GPU资源
- 实施请求限流策略
- 调整缓存大小和过期时间
- 优化搜索算法和索引结构

### 7.2 内存使用过高

**问题现象**: 系统运行过程中内存使用持续增长。

**解决方案**:
```bash
# 检查内存使用
free -h
ps aux --sort=-%mem | head

# 重启服务释放内存
systemctl restart msearch

# 启用内存监控
python scripts/memory_monitor.py
```

**预防措施**:
- 实现内存使用监控
- 配置内存使用限制
- 定期重启服务

## 8. 日志与监控

### 8.1 启用详细日志

```bash
# 设置日志级别
export LOG_LEVEL=DEBUG

# 启用文件日志
mkdir -p logs
export LOG_FILE=logs/msearch.log

# 查看实时日志
tail -f logs/msearch.log

# 分析错误日志
grep ERROR logs/msearch.log | tail -20
```

### 8.2 系统监控

```bash
# 系统资源监控
htop
iotop
nvidia-smi -l 1

# 服务状态监控
curl http://localhost:8000/api/v1/system/status

# 数据库监控
curl http://localhost:6333/metrics
```

## 9. 紧急恢复程序

### 9.1 系统完全重置

```bash
#!/bin/bash
# emergency_reset.sh

echo "开始紧急系统重置..."

# 停止所有服务
pkill -f uvicorn
pkill -f infinity_emb
docker stop qdrant

# 备份数据
mkdir -p backup/$(date +%Y%m%d_%H%M%S)
cp -r data/ backup/$(date +%Y%m%d_%H%M%S)/

# 清理临时文件
rm -rf temp/*
rm -rf cache/*

# 重置数据库
rm -f data/msearch.db
python scripts/init_database.py

# 重启服务
docker start qdrant
sleep 5
python scripts/start_infinity_services.py &
sleep 10
python -m uvicorn main:app --host 0.0.0.0 --port 8000 &

echo "系统重置完成"
```

### 9.2 数据恢复

```bash
#!/bin/bash
# data_recovery.sh

BACKUP_DIR=$1
if [ -z "$BACKUP_DIR" ]; then
    echo "使用方法: $0 <backup_directory>"
    exit 1
fi

echo "开始数据恢复..."

# 停止服务
pkill -f uvicorn
docker stop qdrant

# 恢复数据
cp -r $BACKUP_DIR/data/* data/

# 重启服务
docker start qdrant
sleep 5
python -m uvicorn main:app --host 0.0.0.0 --port 8000 &

echo "数据恢复完成"
```

## 10. 预防性维护

### 10.1 定期检查清单

**每日检查**：
- [ ] 系统服务状态
- [ ] 磁盘空间使用
- [ ] 错误日志审查
- [ ] 处理队列状态

**每周检查**：
- [ ] 数据库性能分析
- [ ] 系统资源使用趋势
- [ ] 备份数据完整性
- [ ] 安全更新检查

**每月检查**：
- [ ] 系统性能基准测试
- [ ] 配置文件审查
- [ ] 依赖包更新
- [ ] 容量规划评估

### 10.2 自动化监控脚本

```python
#!/usr/bin/env python3
# health_check.py

import requests
import psutil
import logging
from datetime import datetime

def check_system_health():
    """系统健康检查"""
    issues = []
    
    # 检查API服务
    try:
        response = requests.get('http://localhost:8000/health', timeout=5)
        if response.status_code != 200:
            issues.append("API服务异常")
    except:
        issues.append("API服务无响应")
    
    # 检查系统资源
    cpu_percent = psutil.cpu_percent(interval=1)
    memory_percent = psutil.virtual_memory().percent
    disk_percent = psutil.disk_usage('/').percent
    
    if cpu_percent > 80:
        issues.append(f"CPU使用率过高: {cpu_percent}%")
    if memory_percent > 85:
        issues.append(f"内存使用率过高: {memory_percent}%")
    if disk_percent > 90:
        issues.append(f"磁盘使用率过高: {disk_percent}%")
    
    # 检查依赖服务
    try:
        response = requests.get('http://localhost:6333/health', timeout=5)
        if response.status_code != 200:
            issues.append("Qdrant服务异常")
    except:
        issues.append("Qdrant服务无响应")
    
    return issues

if __name__ == "__main__":
    issues = check_system_health()
    if issues:
        print(f"发现问题: {', '.join(issues)}")
        # 发送告警通知
    else:
        print("系统状态正常")
```

## 11. 问题报告模板

当遇到无法解决的问题时，请按以下模板提供信息：

```
**问题描述**：
[详细描述问题现象]

**环境信息**：
- 操作系统：
- Python版本：
- msearch版本：
- 硬件配置：

**重现步骤**：
1. 
2. 
3. 

**错误日志**：
```
[粘贴相关错误日志]
```

**已尝试的解决方案**：
[列出已经尝试的解决方法]
```

## 12. 相关文档

- [开发环境搭建](development_environment.md) - 环境配置问题
- [部署与运维指南](deployment_and_operations.md) - 部署相关问题
- [API文档](api_documentation.md) - API使用问题
- [技术实现指南](technical_implementation.md) - 系统架构和技术细节

---

*最后更新时间: 2024-01-01*
*合并自 troubleshooting_guide.md 和 troubleshooting.md*