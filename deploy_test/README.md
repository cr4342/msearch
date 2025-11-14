# 部署测试说明

本目录包含文件监控与处理状态查询功能的部署测试脚本。

## 测试内容

1. **API健康检查** - 验证API服务是否正常运行
2. **文件监控状态查询** - 验证文件监控服务状态
3. **启动/停止文件监控** - 验证文件监控服务的启动和停止功能
4. **添加/移除监控目录** - 验证监控目录的管理功能
5. **文件处理状态查询** - 验证单个文件处理状态查询功能
6. **处理状态统计** - 验证所有文件处理状态统计功能
7. **完整工作流程测试** - 验证从文件创建到处理完成的完整流程

## 如何运行测试

### 前提条件

1. 确保API服务已启动并运行在 `http://localhost:8000`
2. 确保Python环境已安装必要的依赖：
   ```bash
   pip install requests
   ```

### 运行测试

1. 使用默认参数运行测试：
   ```bash
   python test_file_monitoring.py
   ```

2. 指定测试目录：
   ```bash
   python test_file_monitoring.py --test-dir /path/to/test/dir
   ```

3. 指定API地址：
   ```bash
   python test_file_monitoring.py --api-url http://localhost:8080/api/v1
   ```

### 测试结果

测试结果将输出到控制台，并记录在 `deploy_test.log` 文件中。

## 测试脚本说明

`test_file_monitoring.py` 是一个Python脚本，使用requests库调用API接口进行测试。脚本包含以下主要函数：

- `test_api_health()` - 测试API健康状态
- `test_monitoring_status()` - 测试监控状态
- `test_start_monitoring()` - 测试启动监控
- `test_stop_monitoring()` - 测试停止监控
- `test_add_monitoring_directory()` - 测试添加监控目录
- `test_remove_monitoring_directory()` - 测试移除监控目录
- `test_file_processing_status()` - 测试文件处理状态查询
- `test_all_processing_status()` - 测试所有处理状态统计
- `test_file_monitoring_workflow()` - 测试完整文件监控工作流程

## 注意事项

1. 测试过程中会在指定测试目录中创建临时文件，测试完成后不会自动删除
2. 测试脚本会尝试等待文件处理完成，最长等待时间为60秒
3. 如果API服务未启动或无法访问，测试将失败并终止
4. 测试日志会追加到 `deploy_test.log` 文件中，不会覆盖之前的内容
