"""
负载均衡器模块
负责智能分发请求到Infinity服务实例
"""

import asyncio
import httpx
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from src.core.logging_config import get_logger
from src.core.infinity_manager import InfinityService

logger = get_logger(__name__)


@dataclass
class ServiceUnavailableError(Exception):
    """服务不可用异常"""
    message: str


class LoadBalancer:
    """负载均衡器 - 智能分发请求"""
    
    def __init__(self, services: Dict[str, InfinityService]):
        self.services = services
        self.request_queues = {name: asyncio.Queue() for name in services.keys()}
        self.max_concurrent_requests = 10
        self.request_timeouts = 30  # 请求超时时间(秒)
        
        logger.info("负载均衡器初始化完成")
    
    async def route_request(self, service_name: str, request_data: Dict) -> Dict:
        """
        路由请求到最优服务实例
        
        Args:
            service_name: 服务名称 (clip, clap, whisper)
            request_data: 请求数据
            
        Returns:
            服务响应数据
            
        Raises:
            ServiceUnavailableError: 服务不可用时抛出异常
        """
        if service_name not in self.services:
            raise ServiceUnavailableError(f"未知服务: {service_name}")
        
        service = self.services[service_name]
        
        # 1. 检查服务状态
        if service.status != "running":
            raise ServiceUnavailableError(f"{service_name} 服务未运行")
        
        # 2. 检查队列长度
        queue_size = self.request_queues[service_name].qsize()
        if queue_size > self.max_concurrent_requests:
            logger.warning(f"{service_name} 队列已满 ({queue_size}/{self.max_concurrent_requests})，等待中...")
        
        # 3. 添加到队列
        await self.request_queues[service_name].put(request_data)
        
        # 4. 执行请求
        try:
            response = await self._execute_request(service, request_data)
            return response
        finally:
            self.request_queues[service_name].get_nowait()
    
    async def _execute_request(self, service: InfinityService, data: Dict) -> Dict:
        """
        执行实际请求
        
        Args:
            service: Infinity服务实例
            data: 请求数据
            
        Returns:
            服务响应数据
            
        Raises:
            ServiceUnavailableError: 请求失败时抛出异常
        """
        try:
            async with httpx.AsyncClient(timeout=self.request_timeouts) as client:
                resp = await client.post(
                    f"http://localhost:{service.port}/embeddings",
                    json=data
                )
                if resp.status_code == 200:
                    return resp.json()
                else:
                    raise ServiceUnavailableError(f"服务返回错误状态码: {resp.status_code}")
        except httpx.RequestError as e:
            logger.error(f"请求执行失败: {e}")
            raise ServiceUnavailableError(f"请求执行失败: {str(e)}")
        except asyncio.TimeoutError:
            logger.error(f"请求超时: {service.name}")
            raise ServiceUnavailableError(f"请求超时: {service.name}")
    
    async def get_service_stats(self) -> Dict[str, Any]:
        """
        获取服务统计信息
        
        Returns:
            服务统计信息字典
        """
        stats = {}
        for service_name, service in self.services.items():
            stats[service_name] = {
                "status": service.status,
                "port": service.port,
                "queue_size": self.request_queues[service_name].qsize(),
                "max_concurrent": self.max_concurrent_requests
            }
        return stats
    
    async def wait_for_queue_empty(self, service_name: str = None, timeout: int = 30) -> bool:
        """
        等待队列清空
        
        Args:
            service_name: 服务名称，如果为None则等待所有服务队列清空
            timeout: 超时时间(秒)
            
        Returns:
            是否在超时前清空队列
        """
        services_to_check = [service_name] if service_name else list(self.services.keys())
        
        try:
            async with asyncio.timeout(timeout):
                while True:
                    all_empty = True
                    for svc_name in services_to_check:
                        if self.request_queues[svc_name].qsize() > 0:
                            all_empty = False
                            break
                    
                    if all_empty:
                        return True
                    
                    await asyncio.sleep(0.1)
                    
        except asyncio.TimeoutError:
            logger.warning(f"等待队列清空超时 ({timeout}秒)")
            return False


# 全局负载均衡器实例
_load_balancer = None


def get_load_balancer(services: Dict[str, InfinityService] = None) -> LoadBalancer:
    """
    获取全局负载均衡器实例
    
    Args:
        services: Infinity服务字典(首次初始化时需要提供)
        
    Returns:
        负载均衡器实例
    """
    global _load_balancer
    if _load_balancer is None:
        if services is None:
            raise ValueError("首次初始化负载均衡器时必须提供services参数")
        _load_balancer = LoadBalancer(services)
    return _load_balancer