# MSearch 项目结构

根据测试策略文档规范整理的项目结构

## 目录结构

```
msearch/
├── .github/                    # GitHub Actions 工作流
│   └── workflows/
│       ├── incremental_checks.yml
│       ├── multimodal_processor_checks.yml
│       ├── quick_error_detection.yml
│       └── smart_error_notification.yml
├── config/                     # 配置文件
│   ├── config.yml             # 主配置文件
│   ├── config_cpu.yml         # CPU模式配置
│   └── qdrant.yml             # Qdrant配置
├── data/                      # 数据目录（不提交到Git）
│   ├── database/              # 数据库文件
│   ├── databases/             # 数据库目录
│   ├── logs/                  # 日志文件
│   └── models/                # 模型数据
├── docs/                      # 文档
│   ├── api_documentation.md
│   ├── design.md
│   ├── development_plan.md
│   ├── requirements.md
│   ├── technical_implementation.md
│   ├── test_strategy.md
│   └── user_manual.md
├── offline/                   # 离线资源（不提交到Git）
│   ├── bin/                   # 二进制文件
│   ├── models/                # 离线模型
│   └── packages/              # Python包
├── releases/                  # 发布文件
├── scripts/                   # 脚本文件
│   ├── diagnose_clap_model.py # CLAP模型诊断
│   ├── diagnose_models.py     # 模型诊断
│   ├── download_all_resources.sh # 下载所有资源
│   ├── install_auto.bat       # Windows自动安装
│   ├── install_auto.sh        # Linux自动安装
│   ├── integration_test_with_infinity.sh # Infinity集成测试
│   ├── package_app.py         # 应用打包
│   ├── run_integration_test_with_infinity.sh # 运行集成测试
│   ├── setup_models.py        # 模型设置
│   ├── setup_test_environment.py # 测试环境设置
│   ├── start_infinity_services.sh # 启动Infinity服务
│   ├── start_qdrant_optimized.sh # 优化启动Qdrant
│   ├── start_qdrant.sh        # 启动Qdrant
│   ├── stop_infinity_services.sh # 停止Infinity服务
│   └── stop_qdrant.sh         # 停止Qdrant
├── src/                       # 源代码
│   ├── api/                   # API层
│   ├── business/              # 业务逻辑层
│   ├── core/                  # 核心组件
│   ├── gui/                   # 图形界面
│   ├── processors/            # 处理器
│   ├── storage/               # 存储层
│   └── utils/                 # 工具函数
├── tests/                     # 测试文件
│   ├── unit/                  # 单元测试
│   ├── conftest.py            # 测试配置
│   ├── mock_models.py         # Mock模型
│   ├── test_config.py         # 配置测试
│   └── test_model_loading.py  # 模型加载测试
├── temp/                      # 临时文件（不提交到Git）
├── .coveragerc                # 测试覆盖率配置
├── .gitignore                 # Git忽略规则
├── IFLOW.md                   # iFlow CLI上下文文档
├── project_progress_report.md # 项目进度报告
├── README.md                  # 项目说明文档
└── requirements.txt           # Python依赖
```

## 文件分类说明

### 根目录文件
- **.coveragerc**: 测试覆盖率配置
- **.gitignore**: Git忽略文件规则
- **IFLOW.md**: 项目上下文文档
- **project_progress_report.md**: 项目进度报告
- **README.md**: 项目说明文档
- **requirements.txt**: Python依赖列表

### 脚本文件 (scripts/)
- **诊断脚本**: diagnose_clap_model.py, diagnose_models.py
- **安装脚本**: install_auto.sh, install_auto.bat
- **测试脚本**: integration_test_with_infinity.sh, run_integration_test_with_infinity.sh
- **服务管理**: start/stop_infinity_services.sh, start/stop_qdrant.sh
- **资源管理**: download_all_resources.sh, setup_models.py

### 测试文件 (tests/)
- **单元测试**: tests/unit/ 目录
- **测试配置**: conftest.py, test_config.py
- **Mock数据**: mock_models.py
- **模型测试**: test_model_loading.py

### 不提交到Git的目录
- **data/**: 数据文件、数据库、日志
- **offline/**: 离线资源、模型、二进制文件
- **temp/**: 临时文件
- **venv/**: Python虚拟环境
- **__pycache__/**: Python缓存

## 符合测试策略规范的改进

1. **文件分类清晰**: 脚本文件统一放在scripts/目录
2. **测试文件集中**: 测试相关文件统一放在tests/目录
3. **临时数据隔离**: 临时文件和数据文件不提交到Git
4. **配置管理**: 配置文件集中在config/目录
5. **文档完整**: 所有文档集中在docs/目录

这种结构符合测试策略文档中关于项目组织和文件管理的规范。