# -*- coding: utf-8 -*-
"""
负载均衡器
用于管理多个模型服务的负载均衡
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
import random
from collections import defaultdict
from src.core.config import get_config


class ModelService:
    """模型服务实例"""
    
    def __init__(self, name: str, service_config: Dict[str, Any]):
        self.name = name
        self.port = service_config.get("port", 7997)
        self.model_id = service_config.get("model_id", "")
        self.device = service_config.get("device", "cpu")
        self.max_batch_size = service_config.get("max_batch_size", 32)
        self.current_load = 0
        self.status = "running"


class LoadBalancer:
    """负载均衡器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.services: Dict[str, List[ModelService]] = defaultdict(list)
        self.service_weights = {}
        
        self.logger.info("负载均衡器初始化完成")
    
    def add_service(self, service_type: str, service: ModelService):
        """添加服务"""
        self.services[service_type].append(service)
        self.logger.info(f"添加服务: {service_type} -> {service.name}:{service.port}")
    
    def set_service_weights(self, service_type: str, weights: Dict[str, float]):
        """设置服务权重"""
        self.service_weights[service_type] = weights
        self.logger.info(f"设置服务权重: {service_type} = {weights}")
    
    def get_best_service(self, service_type: str) -> Optional[ModelService]:
        """获取最优服务"""
        if service_type not in self.services:
            return None
        
        available_services = [s for s in self.services[service_type] if s.status == "running"]
        
        if not available_services:
            return None
        
        # 选择负载最轻的服务
        available_services.sort(key=lambda s: s.current_load)
        return available_services[0]
    
    async def route_request(self, service_type: str, request_data: Any) -> Optional[ModelService]:
        """路由请求"""
        service = self.get_best_service(service_type)
        
        if service:
            service.current_load += 1
            self.logger.debug(f"路由请求到 {service.name}:{service.port}")
        
        return service
    
    def release_service(self, service_type: str, service: ModelService):
        """释放服务"""
        if service.current_load > 0:
            service.current_load -= 1
        self.logger.debug(f"释放服务 {service.name}:{service.port}")
    
    def get_service_stats(self, service_type: str) -> Dict[str, Any]:
        """获取服务统计"""
        services = self.services.get(service_type, [])
        
        return {
            "total_services": len(services),
            "running_services": len([s for s in services if s.status == "running"]),
            "total_load": sum(s.current_load for s in services),
            "average_load": sum(s.current_load for s in services) / len(services) if services else 0
        }


# 全局负载均衡器实例
_load_balancer = None


def get_load_balancer() -> LoadBalancer:
    """获取全局负载均衡器实例"""
    global _load_balancer
    
    if _load_balancer is None:
        _load_balancer = LoadBalancer()
        
        # 从配置文件加载服务配置
        config = get_config()
        services_dict = config.models
        
        # 注册服务
        for service_name, service_config in services_dict.items():
            # 推断服务类型
            service_type = service_name
            
            service = ModelService(service_name, {
                "port": service_config.port,
                "model_id": service_config.model_name,
                "device": service_config.device,
                "max_batch_size": service_config.max_batch_size
            })
            _load_balancer.add_service(service_type, service)
    
    return _load_balancer


async def route_request_to_model(service_type: str, request_data: Any) -> Optional[ModelService]:
    """路由请求到模型服务"""
    load_balancer = get_load_balancer()
    return await load_balancer.route_request(service_type, request_data)


def release_model_service(service_type: str, service: ModelService):
    """释放模型服务"""
    load_balancer = get_load_balancer()
    load_balancer.release_service(service_type, service)
