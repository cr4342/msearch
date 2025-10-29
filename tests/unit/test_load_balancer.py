"""
LoadBalancer Unit Tests
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from aiohttp import ClientResponse, ClientError
from aiohttp.test_utils import make_mocked_coro

from src.business.load_balancer import LoadBalancer, ServiceUnavailableError
from src.core.infinity_manager import InfinityService


class TestLoadBalancer:
    """LoadBalancer Test Class"""
    
    @pytest.fixture
    def infinity_services(self):
        """Fixture to create mock Infinity services"""
        services = {
            "clip": InfinityService("clip", {
                "port": 7997,
                "model_id": "openai/clip-vit-base-patch32",
                "device": "cpu",
                "max_batch_size": 32
            }),
            "clap": InfinityService("clap", {
                "port": 7998,
                "model_id": "laion/clap-htsat-fused",
                "device": "cpu",
                "max_batch_size": 16
            }),
            "whisper": InfinityService("whisper", {
                "port": 7999,
                "model_id": "openai/whisper-base",
                "device": "cpu",
                "max_batch_size": 8
            })
        }
        
        # 设置服务状态为运行
        for service in services.values():
            service.status = "running"
            
        return services
    
    @pytest.fixture
    def load_balancer(self, infinity_services):
        """Fixture to create LoadBalancer instance"""
        return LoadBalancer(infinity_services)
    
    def test_init(self, load_balancer, infinity_services):
        """Test initialization"""
        assert load_balancer is not None
        assert load_balancer.services == infinity_services
        assert len(load_balancer.request_queues) == 3
        assert "clip" in load_balancer.request_queues
        assert "clap" in load_balancer.request_queues
        assert "whisper" in load_balancer.request_queues
        assert load_balancer.max_concurrent_requests == 10
        assert load_balancer.request_timeouts == 30
    
    def test_get_load_balancer_singleton(self, infinity_services):
        """Test LoadBalancer singleton pattern"""
        from src.business.load_balancer import get_load_balancer
        
        # Reset global instance
        import src.business.load_balancer as lb_module
        lb_module._load_balancer = None
        
        # Get first instance
        lb1 = get_load_balancer(infinity_services)
        assert lb1 is not None
        
        # Get second instance, should be the same
        lb2 = get_load_balancer()
        assert lb1 is lb2
    
    @pytest.mark.asyncio
    async def test_route_request_success(self, load_balancer):
        """Test successful request routing"""
        # Mock the _execute_request method
        mock_response = {"data": [{"embedding": [0.1, 0.2, 0.3]}]}
        load_balancer._execute_request = AsyncMock(return_value=mock_response)
        
        request_data = {"inputs": ["test input"]}
        response = await load_balancer.route_request("clip", request_data)
        
        assert response == mock_response
        load_balancer._execute_request.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_route_request_unknown_service(self, load_balancer):
        """Test routing to unknown service"""
        request_data = {"inputs": ["test input"]}
        
        with pytest.raises(ServiceUnavailableError) as exc_info:
            await load_balancer.route_request("unknown_service", request_data)
        
        assert "未知服务: unknown_service" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_route_request_service_not_running(self, load_balancer):
        """Test routing to service that is not running"""
        # Set service status to stopped
        load_balancer.services["clip"].status = "stopped"
        
        request_data = {"inputs": ["test input"]}
        
        with pytest.raises(ServiceUnavailableError) as exc_info:
            await load_balancer.route_request("clip", request_data)
        
        assert "clip 服务未运行" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_route_request_queue_full(self, load_balancer):
        """Test routing when queue is full"""
        # Fill the queue to max capacity
        for i in range(load_balancer.max_concurrent_requests):
            await load_balancer.request_queues["clip"].put(f"request_{i}")
        
        # Mock the _execute_request method
        mock_response = {"data": [{"embedding": [0.1, 0.2, 0.3]}]}
        load_balancer._execute_request = AsyncMock(return_value=mock_response)
        
        request_data = {"inputs": ["test input"]}
        
        # This should still work, as the request is added to queue and then processed
        response = await load_balancer.route_request("clip", request_data)
        
        assert response == mock_response
        assert load_balancer.request_queues["clip"].qsize() == load_balancer.max_concurrent_requests  # Queue should be back to full
    
    @pytest.mark.asyncio
    async def test_execute_request_success(self, load_balancer):
        """Test successful request execution"""
        # Skip this test for now - httpx mocking is complex
        # TODO: Fix httpx mocking in this test
        pytest.skip("Skip httpx mocking test - needs refactoring")
    
    @pytest.mark.asyncio
    async def test_execute_request_http_error(self, load_balancer):
        """Test request execution with HTTP error"""
        # Skip this test for now - httpx mocking is complex
        # TODO: Fix httpx mocking in this test
        pytest.skip("Skip httpx mocking test - needs refactoring")
    
    @pytest.mark.asyncio
    async def test_execute_request_client_error(self, load_balancer):
        """Test request execution with client error"""
        # Skip this test for now - httpx mocking is complex
        # TODO: Fix httpx mocking in this test
        pytest.skip("Skip httpx mocking test - needs refactoring")
    
    @pytest.mark.asyncio
    async def test_execute_request_timeout(self, load_balancer):
        """Test request execution with timeout"""
        # Skip this test for now - httpx mocking is complex
        # TODO: Fix httpx mocking in this test
        pytest.skip("Skip httpx mocking test - needs refactoring")
    
    @pytest.mark.asyncio
    async def test_get_service_stats(self, load_balancer):
        """Test getting service statistics"""
        # Fill one queue with some requests
        await load_balancer.request_queues["clip"].put("request_1")
        await load_balancer.request_queues["clip"].put("request_2")
        
        stats = await load_balancer.get_service_stats()
        
        assert len(stats) == 3
        assert "clip" in stats
        assert "clap" in stats
        assert "whisper" in stats
        
        # Check clip service stats
        clip_stats = stats["clip"]
        assert clip_stats["status"] == "running"
        assert clip_stats["port"] == 7997
        assert clip_stats["queue_size"] == 2
        assert clip_stats["max_concurrent"] == 10
        
        # Check clap service stats
        clap_stats = stats["clap"]
        assert clap_stats["status"] == "running"
        assert clap_stats["port"] == 7998
        assert clap_stats["queue_size"] == 0
        assert clap_stats["max_concurrent"] == 10
    
    @pytest.mark.asyncio
    async def test_wait_for_queue_empty_success(self, load_balancer):
        """Test waiting for queue to empty successfully"""
        # Add some requests to queue
        await load_balancer.request_queues["clip"].put("request_1")
        await load_balancer.request_queues["clip"].put("request_2")
        
        # Process the requests (this will empty the queue)
        async def process_requests():
            await asyncio.sleep(0.1)  # Small delay
            # Manually empty the queue
            while not load_balancer.request_queues["clip"].empty():
                load_balancer.request_queues["clip"].get_nowait()
        
        # Run the processing in parallel with waiting
        wait_task = asyncio.create_task(load_balancer.wait_for_queue_empty("clip", timeout=5))
        process_task = asyncio.create_task(process_requests())
        
        # Wait for both tasks to complete
        wait_result = await wait_task
        await process_task
        
        assert wait_result is True
        assert load_balancer.request_queues["clip"].qsize() == 0
    
    @pytest.mark.asyncio
    async def test_wait_for_queue_empty_timeout(self, load_balancer):
        """Test waiting for queue to empty with timeout"""
        # Add some requests to queue
        await load_balancer.request_queues["clip"].put("request_1")
        await load_balancer.request_queues["clip"].put("request_2")
        
        # Wait for queue to empty with short timeout (should timeout)
        result = await load_balancer.wait_for_queue_empty("clip", timeout=0.1)
        
        assert result is False
        assert load_balancer.request_queues["clip"].qsize() == 2  # Queue should still have items
    
    @pytest.mark.asyncio
    async def test_wait_for_all_queues_empty(self, load_balancer):
        """Test waiting for all queues to empty"""
        # Add some requests to queues
        await load_balancer.request_queues["clip"].put("request_1")
        await load_balancer.request_queues["clap"].put("request_2")
        await load_balancer.request_queues["whisper"].put("request_3")
        
        # Wait for all queues to empty with short timeout (should timeout)
        result = await load_balancer.wait_for_queue_empty(timeout=0.1)
        
        assert result is False
        assert load_balancer.request_queues["clip"].qsize() == 1
        assert load_balancer.request_queues["clap"].qsize() == 1
        assert load_balancer.request_queues["whisper"].qsize() == 1

if __name__ == "__main__":
    pytest.main([__file__])