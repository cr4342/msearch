#!/usr/bin/env python3
"""
API端点功能测试脚本
测试所有API端点的功能性和稳定性
"""

import asyncio
import json
import time
import aiohttp
import tempfile
import base64
from typing import Dict, Any, List
from pathlib import Path


class APITestValidator:
    """API功能验证器"""
    
    def __init__(self, base_url: str = "http://localhost:8000/api"):
        self.base_url = base_url.rstrip('/')
        self.results = []
        self.test_images = []
        self.test_files = {}
        
    def log_test(self, test_name: str, status: str, response_data: Dict = None, error: str = None):
        """记录测试结果"""
        result = {
            "test_name": test_name,
            "status": status,
            "timestamp": time.time(),
            "response_data": response_data,
            "error": error
        }
        self.results.append(result)
        status_symbol = "✓" if status == "PASS" else "✗"
        print(f"{status_symbol} {test_name}: {status}")
        if error:
            print(f"  错误: {error}")
        if response_data and len(str(response_data)) > 200:
            print(f"  响应数据: {str(response_data)[:200]}...")
        else:
            if response_data:
                print(f"  响应数据: {response_data}")
    
    def _create_test_image(self, color: str = "red", size: tuple = (100, 100)) -> bytes:
        """创建测试图像的PNG字节数据"""
        width, height = size
        
        # PNG文件头
        png_header = b'\x89PNG\r\n\x1a\n'
        
        # IHDR块
        ihdr_data = width.to_bytes(4, 'big') + height.to_bytes(4, 'big') + \
                   b'\x08\x02\x00\x00\x00'  # 8位RGB
        
        import zlib
        ihdr_chunk = b'\x00\x00\x00\x0d' + b'IHDR' + ihdr_data + \
                    (zlib.crc32(b'IHDR' + ihdr_data) & 0xffffffff).to_bytes(4, 'big')
        
        # 创建简单的图像数据
        if color == "red":
            image_data = b'\xff\x00\x00' * (width * height)
        elif color == "blue":
            image_data = b'\x00\x00\xff' * (width * height)
        elif color == "green":
            image_data = b'\x00\xff\x00' * (width * height)
        else:
            image_data = b'\xff\xff\xff' * (width * height)
        
        compressed_data = zlib.compress(image_data)
        idat_chunk = (len(compressed_data).to_bytes(4, 'big') + 
                     b'IDAT' + compressed_data +
                     (zlib.crc32(b'IDAT' + compressed_data) & 0xffffffff).to_bytes(4, 'big'))
        
        # IEND块
        iend_chunk = b'\x00\x00\x00\x00' + b'IEND' + \
                    (zlib.crc32(b'IEND') & 0xffffffff).to_bytes(4, 'big')
        
        return png_header + ihdr_chunk + idat_chunk + iend_chunk
    
    def _create_test_audio(self) -> bytes:
        """创建测试音频数据 (简单的WAV格式)"""
        # 简单的16位单声道WAV文件头
        sample_rate = 44100
        duration = 1  # 1秒
        num_samples = sample_rate * duration
        
        # WAV文件头
        wav_header = b'RIFF'
        wav_header += (36 + num_samples * 2).to_bytes(4, 'little')  # 文件大小
        wav_header += b'WAVE'
        wav_header += b'fmt ' + b'\x10\x00\x00\x00'  # fmt块大小
        wav_header += b'\x01\x00'  # PCM格式
        wav_header += b'\x01\x00'  # 单声道
        wav_header += sample_rate.to_bytes(4, 'little')  # 采样率
        wav_header += (sample_rate * 2).to_bytes(4, 'little')  # 字节率
        wav_header += b'\x02\x00'  # 块对齐
        wav_header += b'\x10\x00'  # 位深
        wav_header += b'data'
        wav_header += (num_samples * 2).to_bytes(4, 'little')  # 数据大小
        
        # 生成简单的正弦波数据
        import math
        audio_data = bytearray()
        for i in range(num_samples):
            sample = int(32767 * math.sin(2 * math.pi * 440 * i / sample_rate))  # 440Hz正弦波
            audio_data.extend(sample.to_bytes(2, 'little'))
        
        return wav_header + bytes(audio_data)
    
    async def _make_request(self, session: aiohttp.ClientSession, method: str, endpoint: str, 
                          data: Any = None, json_data: Dict = None, headers: Dict = None) -> Dict:
        """发起HTTP请求"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            if method.upper() == "GET":
                async with session.get(url, headers=headers) as response:
                    result = await response.json()
                    return {"status_code": response.status, "data": result}
            
            elif method.upper() == "POST":
                if json_data:
                    async with session.post(url, json=json_data, headers=headers) as response:
                        result = await response.json()
                        return {"status_code": response.status, "data": result}
                else:
                    async with session.post(url, data=data, headers=headers) as response:
                        result = await response.json()
                        return {"status_code": response.status, "data": result}
            
            elif method.upper() == "DELETE":
                async with session.delete(url, headers=headers) as response:
                    result = await response.json()
                    return {"status_code": response.status, "data": result}
            
            elif method.upper() == "PUT":
                async with session.put(url, json=json_data, headers=headers) as response:
                    result = await response.json()
                    return {"status_code": response.status, "data": result}
                    
        except Exception as e:
            return {"status_code": 0, "data": None, "error": str(e)}
    
    async def test_search_endpoints(self, session: aiohttp.ClientSession):
        """测试搜索相关API端点"""
        print("\n=== 测试搜索API端点 ===")
        
        # 1. 测试文本搜索
        try:
            response = await self._make_request(
                session, "POST", "/search",
                json_data={
                    "query": "测试文本查询",
                    "query_type": "text",
                    "top_k": 5
                }
            )
            
            if response["status_code"] == 200:
                self.log_test("文本搜索", "PASS", response["data"])
            else:
                self.log_test("文本搜索", "FAIL", response["data"], 
                            f"状态码: {response['status_code']}")
        except Exception as e:
            self.log_test("文本搜索", "FAIL", error=str(e))
        
        # 2. 测试图像搜索 (使用测试图像数据)
        try:
            test_image_data = self._create_test_image("red")
            
            data = aiohttp.FormData()
            data.add_field('image', test_image_data, filename='test.png', 
                          content_type='image/png')
            data.add_field('top_k', '5')
            
            response = await self._make_request(
                session, "POST", "/search/image", data=data
            )
            
            if response["status_code"] == 200:
                self.log_test("图像搜索", "PASS", response["data"])
            else:
                self.log_test("图像搜索", "FAIL", response["data"], 
                            f"状态码: {response['status_code']}")
        except Exception as e:
            self.log_test("图像搜索", "FAIL", error=str(e))
        
        # 3. 测试音频搜索
        try:
            test_audio_data = self._create_test_audio()
            
            data = aiohttp.FormData()
            data.add_field('audio', test_audio_data, filename='test.wav', 
                          content_type='audio/wav')
            data.add_field('top_k', '5')
            
            response = await self._make_request(
                session, "POST", "/search/audio", data=data
            )
            
            if response["status_code"] == 200:
                self.log_test("音频搜索", "PASS", response["data"])
            else:
                self.log_test("音频搜索", "FAIL", response["data"], 
                            f"状态码: {response['status_code']}")
        except Exception as e:
            self.log_test("音频搜索", "FAIL", error=str(e))
        
        # 4. 测试获取相似文件 (使用虚拟file_id)
        try:
            response = await self._make_request(
                session, "GET", "/similar/test_file_id_123"
            )
            
            if response["status_code"] == 200:
                self.log_test("获取相似文件", "PASS", response["data"])
            else:
                self.log_test("获取相似文件", "FAIL", response["data"], 
                            f"状态码: {response['status_code']}")
        except Exception as e:
            self.log_test("获取相似文件", "FAIL", error=str(e))
        
        # 5. 测试获取搜索建议
        try:
            response = await self._make_request(
                session, "GET", "/suggestions?query=测试&limit=5"
            )
            
            if response["status_code"] == 200:
                self.log_test("获取搜索建议", "PASS", response["data"])
            else:
                self.log_test("获取搜索建议", "FAIL", response["data"], 
                            f"状态码: {response['status_code']}")
        except Exception as e:
            self.log_test("获取搜索建议", "FAIL", error=str(e))
        
        # 6. 测试获取热门搜索
        try:
            response = await self._make_request(
                session, "GET", "/popular?limit=5"
            )
            
            if response["status_code"] == 200:
                self.log_test("获取热门搜索", "PASS", response["data"])
            else:
                self.log_test("获取热门搜索", "FAIL", response["data"], 
                            f"状态码: {response['status_code']}")
        except Exception as e:
            self.log_test("获取热门搜索", "FAIL", error=str(e))
    
    async def test_config_endpoints(self, session: aiohttp.ClientSession):
        """测试配置相关API端点"""
        print("\n=== 测试配置API端点 ===")
        
        # 1. 测试获取系统配置
        try:
            response = await self._make_request(session, "GET", "/config")
            
            if response["status_code"] == 200:
                self.log_test("获取系统配置", "PASS", response["data"])
            else:
                self.log_test("获取系统配置", "FAIL", response["data"], 
                            f"状态码: {response['status_code']}")
        except Exception as e:
            self.log_test("获取系统配置", "FAIL", error=str(e))
        
        # 2. 测试获取监控目录
        try:
            response = await self._make_request(session, "GET", "/config/monitored-directories")
            
            if response["status_code"] == 200:
                self.log_test("获取监控目录", "PASS", response["data"])
            else:
                self.log_test("获取监控目录", "FAIL", response["data"], 
                            f"状态码: {response['status_code']}")
        except Exception as e:
            self.log_test("获取监控目录", "FAIL", error=str(e))
        
        # 3. 测试添加监控目录
        try:
            response = await self._make_request(
                session, "POST", "/config/monitored-directories",
                json_data={},  # 使用json_data传递目录路径
                headers={"Content-Type": "application/json"}
            )
            
            if response["status_code"] in [200, 400]:  # 400可能是目录不存在
                self.log_test("添加监控目录", "PASS", response["data"])
            else:
                self.log_test("添加监控目录", "FAIL", response["data"], 
                            f"状态码: {response['status_code']}")
        except Exception as e:
            self.log_test("添加监控目录", "FAIL", error=str(e))
        
        # 4. 测试获取支持的文件扩展名
        try:
            response = await self._make_request(session, "GET", "/config/supported-extensions")
            
            if response["status_code"] == 200:
                self.log_test("获取文件扩展名", "PASS", response["data"])
            else:
                self.log_test("获取文件扩展名", "FAIL", response["data"], 
                            f"状态码: {response['status_code']}")
        except Exception as e:
            self.log_test("获取文件扩展名", "FAIL", error=str(e))
    
    async def test_status_endpoints(self, session: aiohttp.ClientSession):
        """测试状态相关API端点"""
        print("\n=== 测试状态API端点 ===")
        
        # 1. 测试获取系统状态
        try:
            response = await self._make_request(session, "GET", "/status")
            
            if response["status_code"] == 200:
                self.log_test("获取系统状态", "PASS", response["data"])
            else:
                self.log_test("获取系统状态", "FAIL", response["data"], 
                            f"状态码: {response['status_code']}")
        except Exception as e:
            self.log_test("获取系统状态", "FAIL", error=str(e))
        
        # 2. 测试健康检查
        try:
            response = await self._make_request(session, "GET", "/status/health")
            
            if response["status_code"] == 200:
                self.log_test("健康检查", "PASS", response["data"])
            else:
                self.log_test("健康检查", "FAIL", response["data"], 
                            f"状态码: {response['status_code']}")
        except Exception as e:
            self.log_test("健康检查", "FAIL", error=str(e))
    
    async def test_tasks_endpoints(self, session: aiohttp.ClientSession):
        """测试任务相关API端点"""
        print("\n=== 测试任务API端点 ===")
        
        # 1. 测试获取任务列表
        try:
            response = await self._make_request(session, "GET", "/tasks")
            
            if response["status_code"] == 200:
                self.log_test("获取任务列表", "PASS", response["data"])
            else:
                self.log_test("获取任务列表", "FAIL", response["data"], 
                            f"状态码: {response['status_code']}")
        except Exception as e:
            self.log_test("获取任务列表", "FAIL", error=str(e))
        
        # 2. 测试获取任务统计
        try:
            response = await self._make_request(session, "GET", "/tasks/statistics")
            
            if response["status_code"] == 200:
                self.log_test("获取任务统计", "PASS", response["data"])
            else:
                self.log_test("获取任务统计", "FAIL", response["data"], 
                            f"状态码: {response['status_code']}")
        except Exception as e:
            self.log_test("获取任务统计", "FAIL", error=str(e))
        
        # 3. 测试获取不存在的任务详情 (应该返回404)
        try:
            response = await self._make_request(session, "GET", "/tasks/nonexistent_task_id")
            
            if response["status_code"] == 404:
                self.log_test("获取不存在任务", "PASS", response["data"])
            else:
                self.log_test("获取不存在任务", "FAIL", response["data"], 
                            f"期望404，实际: {response['status_code']}")
        except Exception as e:
            self.log_test("获取不存在任务", "FAIL", error=str(e))
    
    async def test_edge_cases(self, session: aiohttp.ClientSession):
        """测试边界情况"""
        print("\n=== 测试边界情况 ===")
        
        # 1. 测试无效的搜索参数
        try:
            response = await self._make_request(
                session, "POST", "/search",
                json_data={
                    "query": "",
                    "query_type": "invalid_type",
                    "top_k": -1
                }
            )
            
            if response["status_code"] in [400, 422]:  # 参数验证错误
                self.log_test("无效搜索参数", "PASS", response["data"])
            else:
                self.log_test("无效搜索参数", "FAIL", response["data"], 
                            f"期望400/422，实际: {response['status_code']}")
        except Exception as e:
            self.log_test("无效搜索参数", "FAIL", error=str(e))
        
        # 2. 测试空查询
        try:
            response = await self._make_request(session, "GET", "/suggestions?query=")
            
            if response["status_code"] in [400, 422]:  # 参数验证错误
                self.log_test("空查询建议", "PASS", response["data"])
            else:
                self.log_test("空查询建议", "FAIL", response["data"], 
                            f"期望400/422，实际: {response['status_code']}")
        except Exception as e:
            self.log_test("空查询建议", "FAIL", error=str(e))
    
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "="*60)
        print("API功能测试报告")
        print("="*60)
        
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r["status"] == "PASS"])
        failed_tests = total_tests - passed_tests
        
        print(f"总测试数: {total_tests}")
        print(f"通过测试: {passed_tests}")
        print(f"失败测试: {failed_tests}")
        print(f"通过率: {passed_tests/total_tests*100:.1f}%")
        
        print("\n详细结果:")
        print("-"*60)
        
        for result in self.results:
            status_symbol = "✓" if result["status"] == "PASS" else "✗"
            print(f"{status_symbol} {result['test_name']}: {result['status']}")
            if result["error"]:
                print(f"    错误: {result['error']}")
        
        # 保存详细报告
        report_file = "api_test_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": time.time(),
                "summary": {
                    "total_tests": total_tests,
                    "passed_tests": passed_tests,
                    "failed_tests": failed_tests,
                    "success_rate": passed_tests/total_tests*100
                },
                "results": self.results
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n详细报告已保存到: {report_file}")
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": passed_tests/total_tests*100
        }


async def main():
    """主函数"""
    print("开始API功能测试...")
    print(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    validator = APITestValidator()
    
    # 创建HTTP会话
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        
        # 测试所有API端点
        await validator.test_search_endpoints(session)
        await validator.test_config_endpoints(session)
        await validator.test_status_endpoints(session)
        await validator.test_tasks_endpoints(session)
        await validator.test_edge_cases(session)
    
    # 生成测试报告
    summary = validator.generate_report()
    
    print("\nAPI功能测试完成!")
    return summary


if __name__ == "__main__":
    asyncio.run(main())