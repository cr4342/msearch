# 常见问题解答 (FAQ)

> **文档导航**: [需求文档](requirements.md) | [设计文档](design.md) | [开发计划](development_plan.md) | [API文档](api_documentation.md) | [测试策略](test_strategy.md) | [用户手册](user_manual.md) | [安装指南](INSTALL.md)

## 1. 系统功能相关

### 1.1 MSearch 支持哪些文件类型？

**支持的文件类型**：
- **图像**: JPG, PNG, BMP, WebP, HEIC
- **视频**: MP4, AVI, MKV, MOV, WMV, FLV
- **音频**: MP3, WAV, AAC, FLAC, OGG

**不支持的文件类型**：
- 压缩文件 (ZIP, RAR, 7Z等)
- 文档文件 (DOCX, PDF, TXT等)
- 可执行文件 (EXE, DLL, APP等)

### 1.2 如何提高搜索准确率？

**提高搜索准确率的方法**：
1. **使用更具体的描述**：例如"一只黑色的猫在沙发上睡觉"比"猫"更准确
2. **添加关键词限定**：例如"2023年夏天的海滩日落"包含时间和地点信息
3. **使用人名搜索**：先录入人物信息，再使用人名搜索
4. **调整相似度阈值**：在设置中调整搜索结果的相似度阈值
5. **确保文件质量**：清晰的图片和视频能获得更好的识别效果

### 1.3 为什么搜索结果为空？

**可能的原因**：
1. **文件未被索引**：检查文件是否在监控目录中，或等待索引完成
2. **描述过于具体**：尝试使用更通用的描述
3. **相似度阈值过高**：降低设置中的相似度阈值
4. **文件类型不支持**：检查文件是否为支持的类型
5. **服务未正常运行**：检查API服务是否正在运行

### 1.4 如何搜索视频中的特定片段？

**视频搜索方法**：
1. **使用文字描述**：输入"会议开始"或"有人敲门"等场景描述
2. **使用时间范围**：在搜索时指定时间范围（例如"2023-01-01 14:00-15:00"）
3. **使用人物名称**：输入"张三"找到包含该人物的视频片段
4. **使用事件关键词**：例如"生日派对"或"演讲"等

**结果展示**：
- 视频结果会显示精确的时间戳（±2.5秒）
- 点击结果可直接跳转到视频中的对应时间点
- 支持预览视频片段

### 1.5 如何管理监控目录？

**管理监控目录**：
1. **添加监控目录**：
   - 在UI界面点击"设置" → "监控目录"
   - 点击"添加目录"按钮
   - 选择要监控的文件夹
   - 点击"确定"，系统将开始扫描和索引

2. **删除监控目录**：
   - 在监控目录列表中选择要删除的目录
   - 点击"删除"按钮
   - 选择是否同时删除索引数据
   - 点击"确定"

3. **暂停/恢复监控**：
   - 点击目录右侧的开关按钮
   - 暂停后系统将不再监控该目录的变化

## 2. 性能与优化

### 2.1 为什么系统运行缓慢？

**可能的原因**：
1. **硬件配置不足**：检查CPU、内存使用情况
2. **同时处理大量文件**：系统正在索引大量文件时会占用较多资源
3. **GPU未启用**：如果有GPU，确保已启用GPU加速
4. **磁盘IO过高**：检查磁盘使用情况，避免使用机械硬盘
5. **后台服务过多**：关闭不必要的后台服务

**优化建议**：
- 增加系统内存到16GB以上
- 使用SSD存储
- 启用GPU加速
- 调整批处理大小（在设置中）
- 减少同时监控的目录数量

### 2.2 如何优化索引速度？

**索引速度优化**：
1. **调整批处理大小**：在设置中增加批处理大小
2. **启用GPU加速**：如果有NVIDIA GPU，启用GPU加速
3. **使用SSD存储**：SSD比机械硬盘索引速度快3-5倍
4. **减少文件过滤**：只监控必要的文件类型
5. **关闭实时监控**：使用手动扫描代替实时监控

### 2.3 系统占用多少磁盘空间？

**磁盘空间占用**：
- **模型文件**：约10-20GB（根据使用的模型数量）
- **索引数据**：约为源文件大小的5-10%
- **临时文件**：系统会自动清理，通常不超过1GB
- **日志文件**：每天约10-100MB（根据日志级别）

**节省空间建议**：
- 定期清理日志文件
- 删除不需要的模型
- 定期优化数据库
- 清理孤立的索引数据

## 3. 技术问题

### 3.1 如何查看系统日志？

**查看日志文件**：
- 日志文件位于 `logs/` 目录
- `msearch.log`：主日志文件
- `error.log`：错误日志
- `performance.log`：性能日志

**使用命令行查看**：
```bash
# 查看最新日志
tail -f logs/msearch.log

# 查看错误日志
grep -i error logs/error.log
```

### 3.2 服务无法启动怎么办？

**排查步骤**：
1. **检查端口是否被占用**：
   ```bash
   lsof -i :8000  # 检查API端口
   lsof -i :6333  # 检查Qdrant端口
   ```

2. **检查依赖是否安装**：
   ```bash
   pip list | grep -E "fastapi|uvicorn|qdrant-client|infinity"
   ```

3. **检查配置文件**：
   ```bash
   python -c "from src.core.config_manager import ConfigManager; ConfigManager().validate_config()"
   ```

4. **检查数据库连接**：
   ```bash
   sqlite3 data/database/msearch.db ".tables"
   ```

5. **查看启动日志**：
   ```bash
   python scripts/start_services.py --debug
   ```

### 3.3 如何备份和恢复数据？

**备份数据**：
1. **数据库备份**：
   ```bash
   python scripts/backup_database.py
   ```

2. **向量数据库备份**：
   ```bash
   python scripts/backup_qdrant.py
   ```

3. **完整备份**：
   ```bash
   # 备份整个data目录
   tar -czf msearch_backup_$(date +%Y%m%d).tar.gz data/
   ```

**恢复数据**：
1. **停止服务**：
   ```bash
   python scripts/stop_services.py
   ```

2. **恢复数据库**：
   ```bash
   python scripts/restore_database.py --backup-file <backup_file>
   ```

3. **恢复向量数据库**：
   ```bash
   python scripts/restore_qdrant.py --backup-file <backup_file>
   ```

4. **启动服务**：
   ```bash
   python scripts/start_services.py
   ```

### 3.4 如何更新模型？

**更新模型**：
1. **自动更新**：
   ```bash
   python scripts/update_models.py
   ```

2. **手动更新**：
   - 删除旧模型文件：`rm -rf data/models/*`
   - 重新下载模型：`./scripts/download_all_resources.sh`
   - 重启服务：`python scripts/restart_services.py`

**注意事项**：
- 更新模型可能需要重新索引文件
- 建议在低峰时段更新模型
- 更新前备份当前模型

## 4. 安全与隐私

### 4.1 我的文件数据安全吗？

**数据安全保障**：
1. **本地存储**：所有数据都存储在本地，不发送到云端
2. **加密存储**：敏感数据使用加密存储
3. **访问控制**：通过系统权限控制访问
4. **备份机制**：支持数据备份和恢复
5. **安全审计**：详细记录系统操作日志

### 4.2 如何保护我的隐私？

**隐私保护建议**：
1. **设置强密码**：如果启用了认证
2. **限制监控目录**：只监控必要的目录
3. **定期清理数据**：删除不需要的索引和日志
4. **关闭不必要的功能**：例如人脸识别
5. **使用防火墙**：限制外部访问

### 4.3 人脸识别数据如何处理？

**人脸识别数据处理**：
1. **本地存储**：人脸特征数据存储在本地数据库
2. **匿名化处理**：不存储原始人脸图像，只存储特征向量
3. **可控删除**：支持一键删除所有人脸数据
4. **可选功能**：可以在设置中关闭人脸识别功能
5. **加密传输**：内部传输使用加密

## 5. 高级功能

### 5.1 如何使用API？

**API使用方法**：
1. **查看API文档**：
   - 启动服务后访问：http://localhost:8000/docs
   - 或查看 `docs/API.md` 文件

2. **获取API密钥**：
   - 在UI界面点击"设置" → "API密钥"
   - 点击"生成新密钥"
   - 复制生成的API密钥

3. **调用API**：
   ```bash
   curl -X POST "http://localhost:8000/api/search" \
     -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"query": "猫", "top_k": 10}'
   ```

### 5.2 如何自定义模型？

**自定义模型方法**：
1. **准备模型文件**：
   - 确保模型格式兼容（ONNX或PyTorch）
   - 放置到 `data/models/custom/` 目录

2. **配置模型**：
   - 编辑 `config/models.yml` 文件
   - 添加自定义模型配置

3. **重启服务**：
   ```bash
   python scripts/restart_services.py
   ```

4. **验证模型**：
   ```bash
   python -c "from src.business.embedding_engine import EmbeddingEngine; ee = EmbeddingEngine(); print(ee.list_models())"
   ```

### 5.3 如何集成到其他系统？

**系统集成方法**：
1. **使用API集成**：
   - 通过REST API与其他系统交互
   - 支持JSON格式的数据交换

2. **使用Python SDK**：
   ```python
   from msearch.sdk import MSearchClient
   
   client = MSearchClient(api_key="YOUR_API_KEY")
   results = client.search(query="猫", top_k=10)
   ```

3. **使用Webhook**：
   - 配置Webhook接收索引完成通知
   - 在 `config/config.yml` 中设置webhook_url

4. **使用命令行工具**：
   ```bash
   python scripts/search_cli.py --query "猫" --output results.json
   ```

## 6. 其他问题

### 6.1 如何获取技术支持？

**获取技术支持**：
1. **查看文档**：首先查阅官方文档
2. **搜索GitHub Issues**：https://github.com/yourusername/msearch/issues
3. **提交Issue**：如果没有找到解决方案，提交新的Issue
4. **社区论坛**：https://forum.msearch.com
5. **邮件支持**：support@msearch.com
6. **商业支持**：联系sales@msearch.com获取商业支持

### 6.2 如何贡献代码？

**贡献代码方法**：
1. **Fork仓库**：在GitHub上Fork项目
2. **创建分支**：
   ```bash
   git checkout -b feature/your-feature
   ```

3. **编写代码**：
   - 遵循项目代码规范
   - 编写测试用例
   - 更新文档

4. **提交代码**：
   ```bash
   git add .
   git commit -m "Add your feature"
   git push origin feature/your-feature
   ```

5. **创建Pull Request**：在GitHub上创建Pull Request
6. **等待审核**：项目维护者会审核你的代码
7. **合并代码**：审核通过后，代码会被合并到主分支

### 6.3 如何获取最新版本？

**获取最新版本**：
1. **使用Git更新**：
   ```bash
   git pull origin main
   python scripts/update_models.py
   python scripts/restart_services.py
   ```

2. **下载安装包**：
   - 访问GitHub Releases页面：https://github.com/yourusername/msearch/releases
   - 下载最新的安装包
   - 按照安装指南安装

3. **启用自动更新**：
   - 在设置中开启"自动更新"选项
   - 系统会定期检查并安装更新

## 7. 故障排除流程图

```
┌─────────────────────────────────────────┐
│ 问题：搜索结果不准确                     │
└─────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│ 1. 检查搜索描述是否清晰具体               │
│    - 示例："一只黑色的猫" 比 "猫" 更准确   │
└─────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│ 2. 检查文件是否已被索引                   │
│    - 查看UI中的"已索引文件数"             │
│    - 检查文件是否在监控目录中             │
└─────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│ 3. 检查相似度阈值设置                     │
│    - 默认值：0.6                         │
│    - 降低阈值可获得更多结果               │
│    - 提高阈值可获得更准确结果             │
└─────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│ 4. 检查模型是否正常工作                   │
│    - 运行模型测试：pytest tests/unit/test_embedding.py │
│    - 检查模型文件是否完整                 │
└─────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│ 5. 重建索引                               │
│    - 在设置中点击"重建索引"按钮           │
│    - 或运行命令：python scripts/rebuild_index.py │
└─────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│ 6. 联系技术支持                           │
│    - 提供详细的问题描述和日志            │
└─────────────────────────────────────────┘
```

## 8. 联系我们

- **官方网站**: https://msearch.com
- **GitHub**: https://github.com/yourusername/msearch
- **文档中心**: https://docs.msearch.com
- **社区论坛**: https://forum.msearch.com
- **技术支持**: support@msearch.com
- **商务合作**: sales@msearch.com
- **反馈建议**: feedback@msearch.com

---

**更新时间**: 2024-01-01  
**版本**: v1.0.0  
**最后更新者**: MSearch Team