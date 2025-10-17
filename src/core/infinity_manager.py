"""
Infinity服务管理器
负责管理多个模型服务的启动、停止和监控
"""

import asyncio
import aiohttp
import subprocess
import time
import logging
from typing import Dict, Any, Optional
import torch
import psutil

from src.core.config_manager import get_config_manager
from src.core.logging_config import get_logger

logger = get_logger(__name__)


class InfinityService:
    """单个Infinity服务"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.process: Optional[subprocess.Popen] = None
        self.status = "stopped"  # stopped, starting, running, failed
        self.port = config.get("port", 7997)
        self.model_id = config.get("model_id", "")
        self.device = config.get("device", "cpu")
        self.max_batch_size = config.get("max_batch_size", 32)


class InfinityServiceManager:
    """Infinity服务管理器 - 统一管理多个模型服务"""
    
    def __init__(self):
        self.config_manager = get_config_manager()
        self.config = self.config_manager.config
        self.services: Dict[str, InfinityService] = {}
        
        # 从配置加载服务
        services_config = self.config_manager.get('infinity.services', {})
        for service_name, service_config in services_config.items():
            self.services[service_name] = InfinityService(service_name, service_config)
        
        # 健康检查配置
        self.health_check_config = self.config_manager.get('infinity.health_check', {
            "interval": 30,
            "failure_threshold": 3,
            "timeout": 5
        })
        
        # 资源监控配置
        self.resource_monitor_config = self.config_manager.get('infinity.resource_monitor', {
            "interval": 60,
            "gpu_threshold": 0.9,
            "memory_threshold": 0.85,
            "auto_cleanup": True
        })
        
        # 失败计数器
        self.failure_counts = {name: 0 for name in self.services.keys()}
        
        # 监听配置变更
        self.config_manager.watch('infinity', self._reload_config)
    
    def _reload_config(self, key: str, value: Any) -> None:
        """重新加载配置"""
        if 'infinity.services' in key:
            services_config = self.config_manager.get('infinity.services', {})
            for service_name, service_config in services_config.items():
                if service_name in self.services:
                    # 更新现有服务配置
                    self.services[service_name].config = service_config
                    self.services[service_name].port = service_config.get("port", 7997)
                    self.services[service_name].model_id = service_config.get("model_id", "")
                    self.services[service_name].device = service_config.get("device", "cpu")
                    self.services[service_name].max_batch_size = service_config.get("max_batch_size", 32)
                else:
                    # 添加新服务
                    self.services[service_name] = InfinityService(service_name, service_config)
        
        if 'infinity.health_check' in key:
            self.health_check_config = self.config_manager.get('infinity.health_check', {
                "interval": 30,
                "failure_threshold": 3,
                "timeout": 5
            })
        
        if 'infinity.resource_monitor' in key:
            self.resource_monitor_config = self.config_manager.get('infinity.resource_monitor', {
                "interval": 60,
                "gpu_threshold": 0.9,
                "memory_threshold": 0.85,
                "auto_cleanup": True
            })
        
        logger.info(f"Infinity服务管理器配置已更新: {key}")
    
    async def start_all(self) -> None:
        """启动所有服务"""
        logger.info("开始启动所有Infinity服务")
        
        # 按优先级启动服务
        service_order = ["clip", "clap", "whisper"]
        
        for service_name in service_order:
            if service_name in self.services:
                await self.start_service(service_name)
                await asyncio.sleep(5)  # 等待服务就绪
        
        # 启动健康检查
        asyncio.create_task(self._health_check_loop())
        
        # 启动资源监控
        asyncio.create_task(self._resource_monitor_loop())
        
        # 初始化负载均衡器
        from src.core.load_balancer import get_load_balancer
        get_load_balancer(self.services)
        
        logger.info("所有Infinity服务启动完成")
    
    async def start_service(self, service_name: str) -> None:
        """启动单个服务"""
        if service_name not in self.services:
            logger.error(f"服务 {service_name} 不存在")
            return
        
        service = self.services[service_name]
        logger.info(f"开始启动服务: {service_name}")
        
        try:
            # 构建启动命令
            cmd = self._build_command(service)
            logger.info(f"启动命令: {cmd}")
            
            # 启动进程
            process = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            service.process = process
            service.status = "starting"
            
            # 等待服务就绪
            await self._wait_for_ready(service)
            
            service.status = "running"
            logger.info(f"{service_name} 服务启动成功，端口: {service.port}")
            
        except Exception as e:
            logger.error(f"启动服务 {service_name} 失败: {e}")
            service.status = "failed"
    
    def _build_command(self, service: InfinityService) -> str:
        """构建Infinity启动命令"""
        cmd = f"infinity_emb v2 "
        cmd += f"--model-id {service.model_id} "
        cmd += f"--port {service.port} "
        cmd += f"--device {service.device} "
        cmd += f"--batch-size {service.max_batch_size} "
        cmd += "--engine torch"
        
        # GPU优化参数
        if "cuda" in service.device:
            cmd += " --dtype float16"  # 使用FP16加速
        
        logger.info(f"构建启动命令: {cmd}")
        return cmd
    
    async def _wait_for_ready(self, service: InfinityService, timeout: int = 60) -> bool:
        """等待服务就绪"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"http://localhost:{service.port}/health", timeout=5) as resp:
                        if resp.status == 200:
                            return True
            except Exception as e:
                logger.debug(f"服务 {service.name} 尚未就绪: {e}")
            
            await asyncio.sleep(2)
        
        raise TimeoutError(f"服务 {service.name} 在 {timeout} 秒内未就绪")
    
    async def stop_all(self) -> None:
        """停止所有服务"""
        logger.info("开始停止所有Infinity服务")
        
        for service_name, service in self.services.items():
            await self.stop_service(service_name)
        
        logger.info("所有Infinity服务停止完成")
    
    async def stop_service(self, service_name: str) -> None:
        """停止单个服务"""
        if service_name not in self.services:
            logger.error(f"服务 {service_name} 不存在")
            return
        
        service = self.services[service_name]
        logger.info(f"开始停止服务: {service_name}")
        
        if service.process and service.process.poll() is None:
            # 优雅停止
            service.process.terminate()
            try:
                service.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                # 强制杀死
                service.process.kill()
                service.process.wait()
        
        service.status = "stopped"
        logger.info(f"服务 {service_name} 停止完成")
    
    async def _health_check_loop(self) -> None:
        """健康检查循环"""
        interval = self.health_check_config.get("interval", 30)
        failure_threshold = self.health_check_config.get("failure_threshold", 3)
        
        while True:
            await asyncio.sleep(interval)
            await self._check_all_services(failure_threshold)
    
    async def _check_all_services(self, failure_threshold: int) -> None:
        """检查所有服务"""
        for service_name, service in self.services.items():
            is_healthy = await self._check_service(service)
            
            if not is_healthy:
                self.failure_counts[service_name] += 1
                logger.warning(f"{service_name} 健康检查失败 ({self.failure_counts[service_name]}/{failure_threshold})")
                
                if self.failure_counts[service_name] >= failure_threshold:
                    logger.error(f"{service_name} 超过失败阈值，正在重启...")
                    await self.restart_service(service_name)
                    self.failure_counts[service_name] = 0
            else:
                self.failure_counts[service_name] = 0
    
    async def _check_service(self, service: InfinityService) -> bool:
        """检查单个服务"""
        try:
            # 1. 检查进程是否存活
            if service.process and service.process.poll() is not None:
                return False
            
            # 2. 检查HTTP健康端点
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"http://localhost:{service.port}/health",
                    timeout=aiohttp.ClientTimeout(total=self.health_check_config.get("timeout", 5))
                ) as resp:
                    if resp.status != 200:
                        return False
            
            # 3. 测试推理功能
            test_result = await self._test_inference(service)
            return test_result
            
        except Exception as e:
            logger.error(f"健康检查错误: {e}")
            return False
    
    async def _test_inference(self, service: InfinityService) -> bool:
        """测试推理功能"""
        try:
            async with aiohttp.ClientSession() as session:
                # 发送测试请求
                test_data = {"inputs": ["test"]}
                async with session.post(
                    f"http://localhost:{service.port}/embeddings",
                    json=test_data,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    return resp.status == 200
        except Exception as e:
            logger.error(f"推理测试失败: {e}")
            return False
    
    async def restart_service(self, service_name: str) -> None:
        """重启服务"""
        await self.stop_service(service_name)
        await self.start_service(service_name)
    
    async def _resource_monitor_loop(self) -> None:
        """资源监控循环"""
        interval = self.resource_monitor_config.get("interval", 60)
        gpu_threshold = self.resource_monitor_config.get("gpu_threshold", 0.9)
        memory_threshold = self.resource_monitor_config.get("memory_threshold", 0.85)
        auto_cleanup = self.resource_monitor_config.get("auto_cleanup", True)
        
        while True:
            await asyncio.sleep(interval)
            
            if auto_cleanup:
                await self._check_resources(gpu_threshold, memory_threshold)
    
    async def _check_resources(self, gpu_threshold: float, memory_threshold: float) -> None:
        """检查资源使用情况"""
        # 1. GPU监控
        if torch.cuda.is_available():
            for i in range(torch.cuda.device_count()):
                gpu_memory = self._get_gpu_memory(i)
                
                if gpu_memory > gpu_threshold:
                    logger.warning(f"GPU {i} 内存使用率过高: {gpu_memory:.1%}")
                    await self._cleanup_gpu_memory(i)
        
        # 2. 系统内存监控
        memory = psutil.virtual_memory()
        memory_usage = memory.percent / 100
        
        if memory_usage > memory_threshold:
            logger.warning(f"系统内存使用率过高: {memory_usage:.1%}")
            await self._cleanup_system_memory()
    
    def _get_gpu_memory(self, device_id: int) -> float:
        """获取GPU显存使用率"""
        memory_allocated = torch.cuda.memory_allocated(device_id)
        memory_total = torch.cuda.get_device_properties(device_id).total_memory
        return memory_allocated / memory_total if memory_total > 0 else 0
    
    async def _cleanup_gpu_memory(self, device_id: int) -> None:
        """清理GPU内存"""
        torch.cuda.empty_cache()
        torch.cuda.synchronize(device_id)
        logger.info(f"GPU {device_id} 内存清理完成")
    
    async def _cleanup_system_memory(self) -> None:
        """清理系统内存"""
        import gc
        gc.collect()
        logger.info("系统内存清理完成")


# 全局Infinity服务管理器实例
_infinity_service_manager = None


def get_infinity_service_manager() -> InfinityServiceManager:
    """获取全局Infinity服务管理器实例"""
    global _infinity_service_manager
    if _infinity_service_manager is None:
        _infinity_service_manager = InfinityServiceManager()
    return _infinity_service_manager


def initialize_load_balancer():
    """初始化负载均衡器"""
    from src.core.load_balancer import get_load_balancer
    service_manager = get_infinity_service_manager()
    get_load_balancer(service_manager.services)