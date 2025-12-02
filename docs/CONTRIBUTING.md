# 贡献指南

> **文档导航**: [需求文档](requirements.md) | [设计文档](design.md) | [开发计划](development_plan.md) | [API文档](api_documentation.md) | [测试策略](test_strategy.md) | [用户手册](user_manual.md) | [安装指南](INSTALL.md)

## 1. 贡献者行为准则

我们欢迎所有形式的贡献，包括但不限于：
- 代码提交
- 文档改进
- 测试用例编写
- 问题报告
- 功能建议
- 社区支持

为了保持良好的社区氛围，我们期望所有贡献者遵守以下准则：

1. **尊重他人**: 尊重每一位社区成员，避免使用攻击性语言或行为
2. **建设性反馈**: 提供建设性的反馈，避免人身攻击
3. **协作精神**: 积极协作，共同解决问题
4. **质量优先**: 确保贡献的代码和文档质量
5. **遵守许可证**: 确保所有贡献都符合项目许可证
6. **透明沟通**: 保持沟通透明，及时更新进展

## 2. 开发环境搭建

### 2.1 克隆仓库

```bash
git clone https://github.com/yourusername/msearch.git
cd msearch
```

### 2.2 创建虚拟环境

```bash
# Linux/macOS
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 2.3 安装依赖

```bash
pip install -r requirements.txt
```

### 2.4 安装开发依赖

```bash
pip install -r requirements-dev.txt
```

### 2.5 初始化开发环境

```bash
python scripts/init_dev_env.py
```

## 3. 代码规范

### 3.1 Python代码规范

- 遵循 [PEP 8](https://www.python.org/dev/peps/pep-0008/) 代码风格
- 使用 4 个空格缩进
- 每行不超过 100 个字符
- 使用类型注解
- 函数和方法使用文档字符串（Google风格）
- 类和模块使用文档字符串

### 3.2 命名规范

| 类型 | 命名规则 | 示例 |
|------|----------|------|
| 类 | 大驼峰命名法 | `DatabaseAdapter` |
| 函数/方法 | 小驼峰命名法 | `insert_file` |
| 变量 | 下划线命名法 | `file_path` |
| 常量 | 全大写+下划线 | `MAX_RETRY_ATTEMPTS` |
| 模块 | 小写+下划线 | `database_adapter.py` |
| 包 | 小写 | `storage` |

### 3.3 文档字符串规范

使用 Google 风格的文档字符串：

```python
def insert_file(self, file_info: Dict[str, Any]) -> str:
    """插入文件记录
    
    Args:
        file_info: 文件信息字典，包含id、file_path、file_name等字段
        
    Returns:
        str: 插入的文件ID
        
    Raises:
        Exception: 插入失败时抛出异常
    """
    pass
```

## 4. 开发流程

### 4.1 分支管理

- **main**: 主分支，包含稳定版本
- **develop**: 开发分支，包含最新开发代码
- **feature/xxx**: 功能分支，用于开发新功能
- **bugfix/xxx**: Bug修复分支，用于修复bug
- **hotfix/xxx**: 热修复分支，用于紧急修复生产环境问题

### 4.2 开发步骤

1. **创建分支**: 
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/your-feature
   ```

2. **编写代码**: 
   - 实现功能
   - 编写测试用例
   - 更新文档

3. **运行测试**: 
   ```bash
   # 运行单元测试
   pytest tests/unit/
   
   # 运行集成测试
   pytest tests/integration/
   
   # 运行所有测试
   pytest
   ```

4. **代码检查**: 
   ```bash
   # 运行代码风格检查
   flake8 src/
   
   # 运行类型检查
   mypy src/
   
   # 运行代码格式化
   black src/
   ```

5. **提交代码**: 
   ```bash
   git add .
   git commit -m "Add your feature description"
   git push origin feature/your-feature
   ```

6. **创建Pull Request**: 
   - 在GitHub上创建Pull Request
   - 描述功能或修复内容
   - 关联相关Issue
   - 等待代码审查

7. **代码审查**: 
   - 回应审查意见
   - 进行必要的修改
   - 再次运行测试

8. **合并代码**: 
   - 审查通过后，代码将被合并到develop分支
   - 定期从develop分支合并到main分支发布新版本

## 5. 测试规范

### 5.1 测试类型

- **单元测试**: 测试单个函数或类
- **集成测试**: 测试多个模块之间的交互
- **端到端测试**: 测试完整的功能流程
- **性能测试**: 测试系统性能
- **精度测试**: 测试模型精度

### 5.2 测试目录结构

```
tests/
├── unit/             # 单元测试
├── integration/      # 集成测试
├── e2e/              # 端到端测试
├── performance/      # 性能测试
├── accuracy/         # 精度测试
├── data/             # 测试数据
├── conftest.py       # 测试配置
└── pytest.ini        # pytest配置
```

### 5.3 编写测试用例

- 每个测试用例应该测试一个特定的功能点
- 使用 descriptive 测试名称
- 使用 fixtures 管理测试资源
- 测试边界情况
- 测试异常情况
- 保持测试用例的独立性

**示例测试用例**:

```python
def test_insert_file(database_adapter):
    """测试插入文件记录"""
    file_info = {
        'id': 'test-uuid-123',
        'file_path': '/test/path/file.jpg',
        'file_name': 'file.jpg',
        'file_type': 'image',
        'file_size': 1024,
        'file_hash': 'test-hash',
        'created_at': 1234567890.0,
        'modified_at': 1234567890.0
    }
    
    file_id = asyncio.run(database_adapter.insert_file(file_info))
    assert file_id == 'test-uuid-123'
    
    # 验证文件已插入
    inserted_file = asyncio.run(database_adapter.get_file(file_id))
    assert inserted_file is not None
    assert inserted_file['file_path'] == '/test/path/file.jpg'
```

## 6. 文档贡献

### 6.1 文档类型

- **用户文档**: 面向最终用户，包括安装指南、使用手册、FAQ等
- **开发者文档**: 面向开发者，包括API文档、架构文档、贡献指南等
- **技术文档**: 包括设计文档、测试策略、数据库schema等

### 6.2 文档编写规范

- 使用 Markdown 格式
- 保持文档结构清晰
- 使用适当的标题层级
- 包含代码示例和截图
- 保持文档与代码同步
- 使用一致的术语

### 6.3 文档更新流程

1. **修改文档**: 
   - 更新相关文档文件
   - 确保文档内容准确
   - 添加必要的示例和截图

2. **预览文档**: 
   ```bash
   # 使用Markdown预览工具预览文档
   python -m http.server 8000 --directory docs/
   ```

3. **提交文档**: 
   - 提交文档修改
   - 创建Pull Request
   - 等待审查

## 7. 问题报告

### 7.1 报告问题前的准备

1. **搜索现有问题**: 先搜索GitHub Issues，确认问题是否已被报告
2. **更新到最新版本**: 确认问题是否在最新版本中仍然存在
3. **收集信息**: 
   - 操作系统版本
   - Python版本
   - 项目版本
   - 完整的错误信息
   - 重现步骤
   - 预期行为和实际行为

### 7.2 提交问题

在GitHub Issues中提交问题，使用以下模板：

```markdown
## 问题描述

[清晰描述问题]

## 环境信息

- 操作系统: [e.g. Ubuntu 20.04]
- Python版本: [e.g. 3.10.0]
- 项目版本: [e.g. v1.0.0]
- 安装方式: [e.g. 在线安装/离线安装/手动安装]

## 重现步骤

1. [步骤1]
2. [步骤2]
3. [步骤3]

## 预期行为

[描述预期的行为]

## 实际行为

[描述实际发生的行为]

## 错误信息

```
[完整的错误信息]
```

## 附加信息

[任何其他相关信息，如截图、日志文件等]
```

## 8. 功能建议

### 8.1 提交功能建议

在GitHub Issues中提交功能建议，使用以下模板：

```markdown
## 功能描述

[清晰描述建议的功能]

## 功能背景

[描述为什么需要这个功能]

## 功能需求

1. [需求1]
2. [需求2]
3. [需求3]

## 实现建议

[描述可能的实现方式]

## 预期效果

[描述预期的效果]

## 附加信息

[任何其他相关信息]
```

## 9. 代码审查指南

### 9.1 审查内容

- **功能完整性**: 功能是否完整实现
- **代码质量**: 代码是否符合规范
- **测试覆盖**: 是否有足够的测试用例
- **文档更新**: 是否更新了相关文档
- **性能影响**: 是否影响系统性能
- **安全性**: 是否存在安全隐患
- **可维护性**: 代码是否易于维护

### 9.2 审查反馈

- **明确具体**: 反馈要明确具体，指出问题所在
- **提供建议**: 提供改进建议
- **鼓励为主**: 鼓励开发者，肯定好的部分
- **保持尊重**: 保持尊重，避免攻击性语言

### 9.3 审查流程

1. **分配审查者**: 代码提交后，自动或手动分配审查者
2. **审查代码**: 审查者审查代码，提出反馈
3. **修改代码**: 开发者根据反馈修改代码
4. **再次审查**: 审查者再次审查修改后的代码
5. **批准合并**: 审查通过后，批准合并

## 10. 发布流程

### 10.1 版本号规范

使用语义化版本号（Semantic Versioning）：
- **MAJOR.MINOR.PATCH**
- **MAJOR**: 不兼容的API变更
- **MINOR**: 向下兼容的功能新增
- **PATCH**: 向下兼容的bug修复

### 10.2 发布步骤

1. **更新版本号**: 
   - 更新 `__version__` 变量
   - 更新 CHANGELOG.md

2. **运行测试**: 
   ```bash
   pytest
   ```

3. **构建发布包**: 
   ```bash
   python scripts/build_release.py
   ```

4. **创建发布分支**: 
   ```bash
   git checkout -b release/v1.0.0
   git push origin release/v1.0.0
   ```

5. **创建发布标签**: 
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

6. **合并到main分支**: 
   ```bash
   git checkout main
   git merge release/v1.0.0
   git push origin main
   ```

7. **合并回develop分支**: 
   ```bash
   git checkout develop
   git merge release/v1.0.0
   git push origin develop
   ```

8. **删除发布分支**: 
   ```bash
   git branch -d release/v1.0.0
   git push origin --delete release/v1.0.0
   ```

9. **发布到GitHub Releases**: 
   - 创建Release
   - 上传发布包
   - 编写发布说明

## 11. 常见问题

### 11.1 如何处理合并冲突

1. **查看冲突文件**: 
   ```bash
   git status
   ```

2. **解决冲突**: 
   - 打开冲突文件
   - 解决冲突标记
   - 保存文件

3. **提交解决结果**: 
   ```bash
   git add .
   git commit -m "Resolve merge conflicts"
   ```

### 11.2 如何回滚提交

1. **查看提交历史**: 
   ```bash
   git log --oneline
   ```

2. **回滚到指定提交**: 
   ```bash
   # 软回滚（保留修改）
   git reset --soft commit-hash
   
   # 硬回滚（丢弃修改）
   git reset --hard commit-hash
   ```

3. **强制推送**: 
   ```bash
   git push -f origin branch-name
   ```

### 11.3 如何处理测试失败

1. **查看测试失败信息**: 
   ```bash
   pytest tests/path/to/test_file.py -v
   ```

2. **分析失败原因**: 
   - 检查测试用例
   - 检查代码实现
   - 检查环境配置

3. **修复问题**: 
   - 修改代码
   - 修改测试用例
   - 调整环境配置

4. **再次运行测试**: 
   ```bash
   pytest tests/path/to/test_file.py
   ```

## 12. 联系方式

- **GitHub Issues**: https://github.com/yourusername/msearch/issues
- **社区论坛**: https://forum.msearch.com
- **Slack**: https://msearch.slack.com
- **邮件列表**: dev@msearch.com

## 13. 致谢

感谢所有为MSearch项目做出贡献的开发者和社区成员！

---

**更新时间**: 2024-01-01  
**版本**: v1.0.0  
**最后更新者**: MSearch Team