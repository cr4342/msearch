#!/usr/bin/env python3
"""
部署测试脚本 - 文件监控与处理状态查询功能
测试文件监控和处理状态查询功能在真实环境中的表现
"""

import os
import sys
import time
import json
import logging
import requests
import argparse
from pathlib import Path

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# API基础URL
BASE_URL = "http://localhost:8000/api/v1"

def test_api_health():
    """测试API健康状态"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            logger.info("API健康检查通过")
            return True
        else:
            logger.error(f"API健康检查失败，状态码: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"API健康检查异常: {str(e)}")
        return False

def test_monitoring_status():
    """测试监控状态"""
    try:
        response = requests.get(f"{BASE_URL}/monitoring/status")
        if response.status_code == 200:
            data = response.json()
            logger.info(f"监控状态: {json.dumps(data, indent=2, ensure_ascii=False)}")
            return data
        else:
            logger.error(f"获取监控状态失败，状态码: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"获取监控状态异常: {str(e)}")
        return None

def test_start_monitoring(directories=None):
    """测试启动监控"""
    try:
        url = f"{BASE_URL}/monitoring/start"
        payload = {"directories": directories} if directories else None
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"启动监控成功: {json.dumps(data, indent=2, ensure_ascii=False)}")
            return True
        else:
            logger.error(f"启动监控失败，状态码: {response.status_code}")
            logger.error(f"响应内容: {response.text}")
            return False
    except Exception as e:
        logger.error(f"启动监控异常: {str(e)}")
        return False

def test_stop_monitoring():
    """测试停止监控"""
    try:
        response = requests.post(f"{BASE_URL}/monitoring/stop")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"停止监控成功: {json.dumps(data, indent=2, ensure_ascii=False)}")
            return True
        else:
            logger.error(f"停止监控失败，状态码: {response.status_code}")
            logger.error(f"响应内容: {response.text}")
            return False
    except Exception as e:
        logger.error(f"停止监控异常: {str(e)}")
        return False

def test_add_monitoring_directory(directory):
    """测试添加监控目录"""
    try:
        url = f"{BASE_URL}/monitoring/directories/add"
        response = requests.post(url, params={"directory": directory})
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"添加监控目录成功: {json.dumps(data, indent=2, ensure_ascii=False)}")
            return True
        else:
            logger.error(f"添加监控目录失败，状态码: {response.status_code}")
            logger.error(f"响应内容: {response.text}")
            return False
    except Exception as e:
        logger.error(f"添加监控目录异常: {str(e)}")
        return False

def test_remove_monitoring_directory(directory):
    """测试移除监控目录"""
    try:
        url = f"{BASE_URL}/monitoring/directories/{directory}"
        response = requests.delete(url)
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"移除监控目录成功: {json.dumps(data, indent=2, ensure_ascii=False)}")
            return True
        else:
            logger.error(f"移除监控目录失败，状态码: {response.status_code}")
            logger.error(f"响应内容: {response.text}")
            return False
    except Exception as e:
        logger.error(f"移除监控目录异常: {str(e)}")
        return False

def test_file_processing_status(file_path):
    """测试文件处理状态查询"""
    try:
        url = f"{BASE_URL}/monitoring/file-status"
        response = requests.get(url, params={"file_path": file_path})
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"文件处理状态: {json.dumps(data, indent=2, ensure_ascii=False)}")
            return data
        else:
            logger.error(f"获取文件处理状态失败，状态码: {response.status_code}")
            logger.error(f"响应内容: {response.text}")
            return None
    except Exception as e:
        logger.error(f"获取文件处理状态异常: {str(e)}")
        return None

def test_all_processing_status():
    """测试所有处理状态统计"""
    try:
        url = f"{BASE_URL}/monitoring/processing-status"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"所有处理状态统计: {json.dumps(data, indent=2, ensure_ascii=False)}")
            return data
        else:
            logger.error(f"获取所有处理状态统计失败，状态码: {response.status_code}")
            logger.error(f"响应内容: {response.text}")
            return None
    except Exception as e:
        logger.error(f"获取所有处理状态统计异常: {str(e)}")
        return None

def create_test_file(directory, filename, content=b"test file content"):
    """创建测试文件"""
    try:
        file_path = os.path.join(directory, filename)
        with open(file_path, 'wb') as f:
            f.write(content)
        logger.info(f"创建测试文件: {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"创建测试文件失败: {str(e)}")
        return None

def wait_for_file_processing(file_path, max_wait_time=60):
    """等待文件处理完成"""
    start_time = time.time()
    while time.time() - start_time < max_wait_time:
        status_data = test_file_processing_status(file_path)
        if status_data and status_data.get("success"):
            processing_status = status_data.get("data", {}).get("processing_status")
            if processing_status == "completed":
                logger.info(f"文件处理完成: {file_path}")
                return True
            elif processing_status == "failed":
                logger.error(f"文件处理失败: {file_path}")
                return False
            else:
                logger.info(f"文件处理中: {file_path}, 状态: {processing_status}")
        time.sleep(5)
    
    logger.warning(f"等待文件处理超时: {file_path}")
    return False

def test_file_monitoring_workflow(test_dir):
    """测试文件监控工作流程"""
    logger.info("开始测试文件监控工作流程")
    
    # 1. 添加监控目录
    if not test_add_monitoring_directory(test_dir):
        logger.error("添加监控目录失败")
        return False
    
    # 2. 启动监控
    if not test_start_monitoring([test_dir]):
        logger.error("启动监控失败")
        return False
    
    # 3. 创建测试文件
    test_files = [
        ("test_image.jpg", b"fake image content"),
        ("test_video.mp4", b"fake video content"),
        ("test_audio.mp3", b"fake audio content"),
        ("test_text.txt", b"fake text content")
    ]
    
    created_files = []
    for filename, content in test_files:
        file_path = create_test_file(test_dir, filename, content)
        if file_path:
            created_files.append(file_path)
    
    # 4. 等待文件处理
    for file_path in created_files:
        wait_for_file_processing(file_path)
    
    # 5. 查询所有处理状态
    test_all_processing_status()
    
    # 6. 停止监控
    if not test_stop_monitoring():
        logger.error("停止监控失败")
        return False
    
    logger.info("文件监控工作流程测试完成")
    return True

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="文件监控与处理状态查询功能部署测试")
    parser.add_argument("--test-dir", default="/tmp/msearch_test", help="测试目录路径")
    parser.add_argument("--api-url", default="http://localhost:8000/api/v1", help="API基础URL")
    args = parser.parse_args()
    
    # 更新API基础URL
    global BASE_URL
    BASE_URL = args.api_url
    
    # 创建测试目录
    test_dir = args.test_dir
    os.makedirs(test_dir, exist_ok=True)
    
    # 记录测试开始时间
    start_time = time.time()
    logger.info(f"开始部署测试，测试目录: {test_dir}")
    
    # 1. 测试API健康状态
    if not test_api_health():
        logger.error("API健康检查失败，终止测试")
        return 1
    
    # 2. 测试监控状态
    test_monitoring_status()
    
    # 3. 测试文件监控工作流程
    if not test_file_monitoring_workflow(test_dir):
        logger.error("文件监控工作流程测试失败")
        return 1
    
    # 4. 记录测试结束时间
    end_time = time.time()
    duration = end_time - start_time
    logger.info(f"部署测试完成，耗时: {duration:.2f}秒")
    
    # 5. 记录测试结果
    test_result = {
        "start_time": start_time,
        "end_time": end_time,
        "duration": duration,
        "test_dir": test_dir,
        "api_url": BASE_URL,
        "status": "success"
    }
    
    # 写入测试日志
    log_file = os.path.join(os.path.dirname(__file__), "deploy_test.log")
    with open(log_file, "a") as f:
        f.write(f"{json.dumps(test_result, ensure_ascii=False)}\n")
    
    logger.info(f"测试结果已记录到: {log_file}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
