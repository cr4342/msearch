"""
Infinity服务管理器单元测试
测试InfinityServiceManager的核心功能
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import subprocess
import torch

from src.core.infinity_manager import (
    InfinityService, 
    InfinityServiceManager, 
    get_infinity_service_manager
)


class TestInfinityService:
    """单个Infinity服务测试"""
    
    def test_init_success(self):
        """测试初始化成功"""
        # 创建配置
        config = {
            "port": 7997,
            "model_id": "test/model",
            "device": "cpu",
            "max_batch_size": 32
        }
        
        # 执行测试
        service = InfinityService("test_service", config)
        
        # 验证结果
        assert service.name == "test_service"
        assert service.config == config
        assert service.port == 7997
        assert service.model_id == "test/model"
        assert service.device == "cpu"
        assert service.max_batch_size == 32
        assert service.status == "stopped"
        assert service.process is None


class TestInfinityServiceManager:
    """Infinity服务管理器核心功能测试"""
    
    @pytest.fixture
    def mock_config_manager(self):
        """模拟配置管理器"""
        mock_config = {
            'infinity': {
                'services': {
                    'clip': {
                        "port": 7997,
                        "model_id": "openai/clip-vit-base-patch32",
                        "device": "cpu",
                        "max_batch_size": 32
                    },
                    'clap': {
                        "port": 7998,
                        "model_id": "laion/clap-htsat-fused",
                        "device": "cpu",
                        "max_batch_size": 16
                    }
                },
                'health_check': {
                    "interval": 30,
                    "failure_threshold": 3,
                    "timeout": 5
                },
                'resource_monitor': {
                    "interval": 60,
                    "gpu_threshold": 0.9,
                    "memory_threshold": 0.85,
                    "auto_cleanup": True
                }
            }
        }
        
        mock_config_manager = Mock()
        mock_config_manager.config = mock_config
        mock_config_manager.get = Mock(side_effect=lambda key, default=None: {
            'infinity.services': mock_config['infinity']['services'],
            'infinity.services.clip': mock_config['infinity']['services']['clip'],
            'infinity.services.clap': mock_config['infinity']['services']['clap'],
            'infinity.health_check': mock_config['infinity']['health_check'],
            'infinity.resource_monitor': mock_config['infinity']['resource_monitor']
        }.get(key, default))
        mock_config_manager.watch = Mock()
        
        return mock_config_manager
    
    @pytest.fixture
    def service_manager(self, mock_config_manager):
        """服务管理器实例"""
        with patch('src.core.infinity_manager.get_config_manager', return_value=mock_config_manager):
            manager = InfinityServiceManager()
            return manager
    
    def test_init_success(self, mock_config_manager):
        """测试初始化成功"""
        with patch('src.core.infinity_manager.get_config_manager', return_value=mock_config_manager):
            manager = InfinityServiceManager()
            
            # 验证组件是否正确初始化
            assert len(manager.services) == 2
            assert 'clip' in manager.services
            assert 'clap' in manager.services
            assert manager.health_check_config == mock_config_manager.get('infinity.health_check')
            assert manager.resource_monitor_config == mock_config_manager.get('infinity.resource_monitor')
            assert len(manager.failure_counts) == 2
            mock_config_manager.watch.assert_called()
    
    def test_reload_config_services(self, service_manager, mock_config_manager):
        """测试重新加载服务配置"""
        # 为测试添加新服务，我们需要模拟配置管理器在被调用时返回包含新服务的完整配置
        complete_services_config = {
            'clip': {
                "port": 7997,
                "model_id": "openai/clip-vit-base-patch32",
                "device": "cpu",
                "max_batch_size": 32
            },
            'clap': {
                "port": 7998,
                "model_id": "laion/clap-htsat-fused",
                "device": "cpu",
                "max_batch_size": 16
            },
            'whisper': {  # 新添加的服务
                "port": 7999,
                "model_id": "openai/whisper-base",
                "device": "cpu",
                "max_batch_size": 8
            }
        }
        
        # 模拟配置管理器的get方法，当请求'infinity.services'时返回完整配置
        def mock_get(key, default=None):
            if key == 'infinity.services':
                return complete_services_config
            return default
        
        mock_config_manager.get.side_effect = mock_get
        
        # 执行测试 - 传入触发更新的键，但配置管理器会返回完整的配置
        service_manager._reload_config('infinity.services.whisper', complete_services_config['whisper'])
        
        # 验证新服务被添加
        assert 'whisper' in service_manager.services
        assert service_manager.services['whisper'].port == 7999
        assert service_manager.services['whisper'].model_id == "openai/whisper-base"
    
    def test_reload_config_health_check(self, service_manager, mock_config_manager):
        """测试重新加载健康检查配置"""
        new_health_config = {
            "interval": 60,
            "failure_threshold": 5,
            "timeout": 10
        }
        
        # 模拟配置管理器的get方法，当请求'infinity.health_check'时返回新配置
        def mock_get(key, default=None):
            if key == 'infinity.health_check':
                return new_health_config
            return default
        
        mock_config_manager.get.side_effect = mock_get
        
        # 执行测试
        service_manager._reload_config('infinity.health_check', new_health_config)
        
        # 验证配置已更新
        assert service_manager.health_check_config["interval"] == 60
        assert service_manager.health_check_config["failure_threshold"] == 5
        assert service_manager.health_check_config["timeout"] == 10
    
    def test_reload_config_resource_monitor(self, service_manager, mock_config_manager):
        """测试重新加载资源监控配置"""
        new_resource_config = {
            "interval": 120,
            "gpu_threshold": 0.8,
            "memory_threshold": 0.8,
            "auto_cleanup": False
        }
        
        # 模拟配置管理器的get方法，当请求'infinity.resource_monitor'时返回新配置
        def mock_get(key, default=None):
            if key == 'infinity.resource_monitor':
                return new_resource_config
            return default
        
        mock_config_manager.get.side_effect = mock_get
        
        # 执行测试
        service_manager._reload_config('infinity.resource_monitor', new_resource_config)
        
        # 验证配置已更新
        assert service_manager.resource_monitor_config["interval"] == 120
        assert service_manager.resource_monitor_config["gpu_threshold"] == 0.8
        assert service_manager.resource_monitor_config["memory_threshold"] == 0.8
        assert service_manager.resource_monitor_config["auto_cleanup"] is False
    
    def test_build_command_cpu(self, service_manager):
        """测试构建CPU命令"""
        # 创建服务
        config = {
            "port": 7997,
            "model_id": "test/model",
            "device": "cpu",
            "max_batch_size": 32
        }
        service = InfinityService("test_service", config)
        
        # 执行测试
        result = service_manager._build_command(service)
        
        # 验证结果
        assert "infinity_emb v2" in result
        assert "--model-id test/model" in result
        assert "--port 7997" in result
        assert "--device cpu" in result
        assert "--batch-size 32" in result
        assert "--engine torch" in result
        assert "--dtype float16" not in result  # CPU不使用FP16
    
    def test_build_command_gpu(self, service_manager):
        """测试构建GPU命令"""
        # 创建服务
        config = {
            "port": 7997,
            "model_id": "test/model",
            "device": "cuda",
            "max_batch_size": 32
        }
        service = InfinityService("test_service", config)
        
        # 执行测试
        result = service_manager._build_command(service)
        
        # 验证结果
        assert "infinity_emb v2" in result
        assert "--model-id test/model" in result
        assert "--port 7997" in result
        assert "--device cuda" in result
        assert "--batch-size 32" in result
        assert "--engine torch" in result
        assert "--dtype float16" in result  # GPU使用FP16
    
    @pytest.mark.asyncio
    async def test_start_service_success(self, service_manager):
        """测试成功启动服务"""
        with patch('subprocess.Popen') as mock_popen, \
             patch.object(service_manager, '_wait_for_ready', return_value=True):
            
            # 模拟进程
            mock_process = Mock()
            mock_process.poll.return_value = None
            mock_popen.return_value = mock_process
            
            # 执行测试
            await service_manager.start_service('clip')
            
            # 验证结果
            service = service_manager.services['clip']
            assert service.status == "running"
            assert service.process == mock_process
            mock_popen.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_start_service_not_exists(self, service_manager):
        """测试启动不存在的服务"""
        # 执行测试
        await service_manager.start_service('nonexistent_service')
        
        # 验证没有异常抛出
    
    @pytest.mark.asyncio
    async def test_stop_service_success(self, service_manager):
        """测试成功停止服务"""
        with patch('subprocess.Popen') as mock_popen:
            # 模拟进程
            mock_process = Mock()
            mock_process.poll.return_value = None
            mock_process.wait = Mock()
            mock_popen.return_value = mock_process
            
            # 先启动服务
            await service_manager.start_service('clip')
            
            # 执行测试
            await service_manager.stop_service('clip')
            
            # 验证结果
            service = service_manager.services['clip']
            assert service.status == "stopped"
            mock_process.terminate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_stop_service_not_exists(self, service_manager):
        """测试停止不存在的服务"""
        # 执行测试
        await service_manager.stop_service('nonexistent_service')
        
        # 验证没有异常抛出
    
    @pytest.mark.asyncio
    async def test_check_service_healthy(self, service_manager):
        """测试检查健康服务"""
        with patch('aiohttp.ClientSession') as mock_session:
            # 模拟健康检查响应
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_session_instance = AsyncMock()
            mock_session_instance.__aenter__.return_value = mock_session_instance
            mock_session_instance.get.return_value.__aenter__.return_value = mock_response
            mock_session.return_value = mock_session_instance
            
            # 创建模拟服务
            config = {
                "port": 7997,
                "model_id": "test/model",
                "device": "cpu",
                "max_batch_size": 32
            }
            service = InfinityService("test_service", config)
            service.process = Mock()
            service.process.poll.return_value = None  # 进程正在运行
            
            # 执行测试
            result = await service_manager._check_service(service)
            
            # 验证结果
            assert result is True
    
    @pytest.mark.asyncio
    async def test_check_service_unhealthy_process_stopped(self, service_manager):
        """测试检查不健康服务（进程已停止）"""
        # 创建模拟服务
        config = {
            "port": 7997,
            "model_id": "test/model",
            "device": "cpu",
            "max_batch_size": 32
        }
        service = InfinityService("test_service", config)
        service.process = Mock()
        service.process.poll.return_value = 1  # 进程已停止
        
        # 执行测试
        result = await service_manager._check_service(service)
        
        # 验证结果
        assert result is False
    
    @pytest.mark.asyncio
    async def test_restart_service(self, service_manager):
        """测试重启服务"""
        with patch.object(service_manager, 'stop_service', return_value=None) as mock_stop, \
             patch.object(service_manager, 'start_service', return_value=None) as mock_start:
            
            # 执行测试
            await service_manager.restart_service('clip')
            
            # 验证结果
            mock_stop.assert_called_once_with('clip')
            mock_start.assert_called_once_with('clip')
    
    def test_get_gpu_memory(self, service_manager):
        """测试获取GPU内存使用率"""
        with patch('torch.cuda.is_available', return_value=True), \
             patch('torch.cuda.device_count', return_value=1), \
             patch('torch.cuda.memory_allocated', return_value=512*1024*1024), \
             patch('torch.cuda.get_device_properties') as mock_get_props:
            
            # 模拟GPU属性
            mock_props = Mock()
            mock_props.total_memory = 1024*1024*1024  # 1GB
            mock_get_props.return_value = mock_props
            
            # 执行测试
            result = service_manager._get_gpu_memory(0)
            
            # 验证结果
            assert result == 0.5  # 512MB / 1024MB = 0.5
    
    def test_get_gpu_memory_no_gpu(self, service_manager):
        """测试获取GPU内存使用率（无GPU）"""
        # 当CUDA不可用时，应该返回0
        with patch('torch.cuda.is_available', return_value=False):
            result = service_manager._get_gpu_memory(0)
            # 验证结果
            assert result == 0


class TestInfinityServiceManagerSingleton:
    """Infinity服务管理器单例模式测试"""
    
    def test_get_infinity_service_manager_singleton(self):
        """测试获取全局Infinity服务管理器实例"""
        with patch('src.core.infinity_manager.get_config_manager'):
            # 重置全局实例
            import src.core.infinity_manager as im
            im._infinity_service_manager = None
            
            # 获取第一个实例
            manager1 = get_infinity_service_manager()
            assert manager1 is not None
            
            # 获取第二个实例，应该与第一个相同
            manager2 = get_infinity_service_manager()
            assert manager1 is manager2


if __name__ == '__main__':
    pytest.main([__file__])
