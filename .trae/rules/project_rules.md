测试目录规范：
1. 所有测试代码统一放在 `tests/` 目录下  
2. 单元测试文件以 `test_*.py` 命名  
3. 测试数据与 fixtures 放在 `tests/data/` 子目录，按模块再分二级目录  
4. 性能基准测试放在 `tests/benchmark/` 目录，输出报告统一为 `.benchmark.json`  
5. 任何测试不得污染项目根目录，临时文件统一输出到 `tests/.tmp/`，并在 `.gitignore` 中忽略  
6. 运行入口统一使用 `pytest`，配置文件 `pytest.ini` 置于 `tests/` 下，`conftest.py` 也放在 `tests/` 目录  
7. 目录结构示例：  
   ├── tests/                   # 测试目录  
   │   ├── __init__.py  
   │   ├── conftest.py  
   │   ├── test_msearch_core.py  
   │   ├── test_timestamp_accuracy.py  
   │   ├── test_multimodal_fusion.py  
   │   ├── test_config_manager.py  
   │   ├── test_database_architecture.py  
   │   └── test_api_endpoints.py
