#!/bin/bash
# msearch CLI 工具快速测试脚本

echo "============================================================"
echo "msearch CLI 工具快速测试"
echo "============================================================"
echo ""

# 检查 API 服务器是否运行
echo "1. 检查 API 服务器状态..."
python3 src/cli.py health
echo ""

# 显示系统信息
echo "2. 显示系统信息..."
python3 src/cli.py info
echo ""

# 显示向量统计
echo "3. 显示向量统计..."
python3 src/cli.py vector-stats
echo ""

# 显示任务统计
echo "4. 显示任务统计..."
python3 src/cli.py task stats
echo ""

# 列出所有任务
echo "5. 列出所有任务..."
python3 src/cli.py task list
echo ""

# 测试文本搜索
echo "6. 测试文本搜索..."
python3 src/cli.py search text "测试"
echo ""

# 测试取消所有任务
echo "7. 测试取消所有任务..."
python3 src/cli.py task cancel-all
echo ""

# 测试按类型取消任务
echo "8. 测试按类型取消任务..."
python3 src/cli.py task cancel-by-type image_preprocess
echo ""

echo "============================================================"
echo "测试完成！"
echo "============================================================"
echo ""
echo "更多用法请参考: python3 src/cli.py --help"
echo "详细文档请查看: docs/cli_usage.md"