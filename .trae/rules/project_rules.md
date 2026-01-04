测试目录规范（v2.0）  
1. 所有测试代码统一放在 `tests/` 目录下，禁止在业务源码目录内嵌测试文件。  
2. 单元测试文件以 `test_*.py` 命名；集成测试文件以 `it_*.py` 命名；端到端测试文件以 `e2e_*.py` 命名。  
3. 测试数据与 fixtures 放在 `tests/data/` 子目录，按“业务域/版本”再分二级目录，例如 `data/msearch/v1/`。  
4. 性能基准测试放在 `tests/benchmark/` 目录，输出报告统一为 `{模块}.benchmark.json`，并同步生成 `*.benchmark.md` 摘要。  
5. 任何测试不得污染项目根目录；临时文件统一输出到 `tests/.tmp/` 并在 `.gitignore` 中忽略，CI 流水线每次自动清空。  
6. 运行入口统一使用 `pytest`，配置文件 `pytest.ini` 置于 `tests/` 下；`conftest.py` 可按业务域拆分，放在 `tests/conf.d/` 中，由 `pytest.ini` 自动加载。  
7. 覆盖率报告统一输出到 `tests/.coverage/` 目录，HTML、XML、CSV 三种格式均需生成；XML 供 SonarQube 解析，CSV 供数据仓库归档。  
8. 所有测试用例必须遵循 Arrange-Act-Assert（AAA）模式；函数名使用 `test_功能点_预期行为` 的蛇形命名；集成与 e2e 用例允许附加 `__` 双下划线后缀以支持参数化。  
9. 禁止在测试代码中硬编码绝对路径；统一通过 `pytest` 的 `tmp_path`、`monkeypatch` 或自定义 `fixture` 获取临时路径；路径生成器统一封装在 `tests/fixtures/path_factory.py`。  
10. 目录结构示例：  
   ├── tests/                          # 测试目录  
   │   ├── __init__.py  
   │   ├── pytest.ini  
   │   ├── conf.d/                     # 按域拆分的 conftest  
   │   │   ├── conftest_msearch.py  
   │   │   └── conftest_api.py  
   │   ├── .coverage/                  # 覆盖率报告（HTML/XML/CSV）  
   │   ├── .tmp/                       # 临时文件（已 gitignore）  
   │   ├── data/                       # 测试数据  
   │   │   ├── msearch/  
   │   │   │   └── v1/  
   │   │   └── api/  
   │   │       └── v2/  
   │   ├── benchmark/                  # 性能基准  
   │   │   ├── msearch.benchmark.json  
   │   │   ├── msearch.benchmark.md  
   │   │   └── test_msearch_benchmark.py  
   │   ├── fixtures/                   # 共享 fixture  
   │   │   ├── __init__.py  
   │   │   └── path_factory.py  
   │   ├── unit/                       # 单元测试  
   │   │   ├── test_msearch_core.py  
   │   │   └── test_timestamp_accuracy.py  
   │   ├── integration/                # 集成测试  
   │   │   ├── it_multimodal_fusion.py  
   │   │   └── it_config_manager.py  
   │   └── e2e/                        # 端到端测试  
   │       ├── e2e_database_architecture.py  
   │       └── e2e_api_endpoints.py
