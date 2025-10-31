#!/bin/bash
# 激活测试环境
source /data/project/msearch/venv_test/bin/activate
export PYTHONPATH="/data/project/msearch:$PYTHONPATH"
export PYTHONWARNINGS=ignore
echo "测试环境已激活"
echo "Python路径: $(which python)"
echo "项目路径: /data/project/msearch"
