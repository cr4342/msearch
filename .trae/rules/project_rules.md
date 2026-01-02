测试目录规范：  
1. 所有测试代码统一放在 `tests/` 目录下  
2. 单元测试文件以 `test_*.py` 命名  
3. 测试数据与 fixtures 放在 `tests/data/` 子目录，按模块再分二级目录  
4. 性能基准测试放在 `tests/benchmark/` 目录，输出报告统一为 `.benchmark.json`  
5. 任何测试不得污染项目根目录，临时文件统一输出到 `tests/.tmp/`，并在 `.gitignore` 中忽略  
6. 运行入口统一使用 `pytest`，配置文件 `pytest.ini` 置于 `tests/` 下，`conftest.py` 也放在 `tests/` 目录  
7. 覆盖率报告统一输出到 `tests/.coverage/` 目录，HTML 与 XML 格式均需生成，供 CI 与本地查看  
8. 所有测试用例必须遵循 Arrange-Act-Assert（AAA）模式，函数名使用 `test_功能点_预期行为` 的蛇形命名  
9. 禁止在测试代码中硬编码绝对路径，统一通过 `pytest` 的 `tmp_path` 或自定义 `fixture` 获取临时路径  
10. 目录结构示例：  
   ├── tests/                   # 测试目录  
   │   ├── __init__.py  
   │   ├── conftest.py  
   │   ├── pytest.ini  
   │   ├── .coverage/           # 覆盖率报告  
   │   ├── .tmp/                # 临时文件（已 gitignore）  
   │   ├── data/                # 测试数据  
   │   │   ├── msearch/  
   │   │   └── api/  
   │   ├── benchmark/           # 性能基准  
   │   │   └── test_msearch_benchmark.py  
   │   ├── test_msearch_core.py  
   │   ├── test_timestamp_accuracy.py  
   │   ├── test_multimodal_fusion.py  
   │   ├── test_config_manager.py  
   │   ├── test_database_architecture.py  
   │   └── test_api_endpoints.py
