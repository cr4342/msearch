"""
进程间通信基类定义
"""
import json
import redis
import time
import uuid
from typing import Any, Dict, Optional, List
from abc import ABC, abstractmethod


class IPCBase(ABC):
    """进程间通信基类"""
    
    def __init__(self, connection_params: Dict[str, Any]):
        self.connection_params = connection_params
        self.connection = None
        self.process_id = str(uuid.uuid4())
    
    @abstractmethod
    def connect(self) -> bool:
        """建立连接"""
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """断开连接"""
        pass
    
    @abstractmethod
    def send_message(self, message: Dict[str, Any], destination: str) -> bool:
        """发送消息到指定目的地"""
        pass
    
    @abstractmethod
    def receive_message(self, source: str, timeout: int = 1) -> Optional[Dict[str, Any]]:
        """从指定源接收消息"""
        pass


class RedisIPC(IPCBase):
    """基于Redis的进程间通信实现"""
    
    def __init__(self, connection_params: Dict[str, Any] = None):
        super().__init__(connection_params or {"host": "localhost", "port": 6379, "db": 0})
        self.connection = None
        self.heartbeat_interval = 30  # 心跳间隔30秒
    
    def connect(self) -> bool:
        """建立Redis连接"""
        try:
            self.connection = redis.Redis(
                host=self.connection_params.get("host", "localhost"),
                port=self.connection_params.get("port", 6379),
                db=self.connection_params.get("db", 0),
                decode_responses=False  # 保持字节格式
            )
            
            # 测试连接
            self.connection.ping()
            
            # 注册进程
            self.register_process()
            
            return True
        except Exception as e:
            print(f"Redis连接失败: {e}")
            return False
    
    def disconnect(self) -> None:
        """断开Redis连接"""
        if self.connection:
            # 取消进程注册
            process_key = f"process:{self.get_process_type()}:status"
            self.connection.delete(process_key)
            
            heartbeat_key = f"heartbeat:{self.get_process_type()}"
            self.connection.delete(heartbeat_key)
            
            self.connection = None
    
    def register_process(self) -> None:
        """注册进程信息"""
        process_key = f"process:{self.get_process_type()}:status"
        heartbeat_key = f"heartbeat:{self.get_process_type()}"
        
        process_info = {
            "pid": self.process_id,
            "timestamp": time.time(),
            "status": "running"
        }
        
        self.connection.hset(process_key, mapping=process_info)
        self.connection.setex(heartbeat_key, self.heartbeat_interval * 2, time.time())
    
    def update_heartbeat(self) -> None:
        """更新心跳"""
        heartbeat_key = f"heartbeat:{self.get_process_type()}"
        self.connection.setex(heartbeat_key, self.heartbeat_interval * 2, time.time())
    
    def get_process_type(self) -> str:
        """获取进程类型，子类需要重写"""
        return "unknown"
    
    def send_message(self, message: Dict[str, Any], destination: str) -> bool:
        """发送消息到指定目的地"""
        try:
            # 添加时间戳和发送者信息
            message["timestamp"] = time.time()
            message["sender"] = self.process_id
            message["sender_type"] = self.get_process_type()
            
            # 序列化消息
            serialized_message = json.dumps(message, ensure_ascii=False).encode('utf-8')
            
            # 发送到Redis队列
            queue_key = f"queue:messages:{destination}"
            self.connection.lpush(queue_key, serialized_message)
            
            return True
        except Exception as e:
            print(f"发送消息失败: {e}")
            return False
    
    def receive_message(self, source: str, timeout: int = 1) -> Optional[Dict[str, Any]]:
        """从指定源接收消息"""
        try:
            queue_key = f"queue:messages:{self.get_process_type()}"
            
            # 阻塞式弹出消息，超时返回None
            result = self.connection.blpop([queue_key], timeout=timeout)
            
            if result:
                _, serialized_message = result
                message = json.loads(serialized_message.decode('utf-8'))
                
                # 检查消息来源（可选）
                if source and message.get("sender_type") != source:
                    # 如果指定来源但不匹配，重新放回队列
                    self.connection.lpush(queue_key, serialized_message)
                    return None
                
                return message
            
            return None
        except Exception as e:
            print(f"接收消息失败: {e}")
            return None
    
    def send_task(self, task_data: Dict[str, Any], priority: str = "normal") -> str:
        """发送任务到任务队列"""
        task_id = str(uuid.uuid4())
        
        # 创建任务对象
        task = {
            "task_id": task_id,
            "data": task_data,
            "priority": priority,
            "status": "pending",
            "created_at": time.time(),
            "sender": self.process_id,
            "sender_type": self.get_process_type()
        }
        
        # 设置任务状态
        self.set_task_status(task_id, task)
        
        # 根据优先级发送到不同队列
        queue_key = f"queue:tasks:priority:{priority}"
        self.connection.lpush(queue_key, json.dumps(task, ensure_ascii=False).encode('utf-8'))
        
        return task_id
    
    def get_task(self, timeout: int = 1) -> Optional[Dict[str, Any]]:
        """从任务队列获取任务"""
        priority_queues = [
            "queue:tasks:priority:high",
            "queue:tasks:priority:normal", 
            "queue:tasks:priority:low"
        ]
        
        result = self.connection.blpop(priority_queues, timeout=timeout)
        
        if result:
            _, serialized_task = result
            task = json.loads(serialized_task.decode('utf-8'))
            
            # 更新任务状态为处理中
            task["status"] = "processing"
            task["started_at"] = time.time()
            task["worker"] = self.process_id
            self.set_task_status(task["task_id"], task)
            
            return task
        
        return None
    
    def complete_task(self, task_id: str, result: Any) -> None:
        """完成任务"""
        # 更新任务状态
        task = self.get_task_status(task_id)
        if task:
            task["status"] = "completed"
            task["result"] = result
            task["completed_at"] = time.time()
            self.set_task_status(task_id, task)
            
            # 移动到完成队列
            completed_queue = f"queue:tasks:completed"
            self.connection.lpush(completed_queue, json.dumps(task, ensure_ascii=False).encode('utf-8'))
    
    def fail_task(self, task_id: str, error: str) -> None:
        """标记任务失败"""
        task = self.get_task_status(task_id)
        if task:
            task["status"] = "failed"
            task["error"] = error
            task["failed_at"] = time.time()
            self.set_task_status(task_id, task)
            
            # 移动到失败队列
            failed_queue = f"queue:tasks:failed"
            self.connection.lpush(failed_queue, json.dumps(task, ensure_ascii=False).encode('utf-8'))
    
    def set_task_status(self, task_id: str, task_data: Dict[str, Any]) -> None:
        """设置任务状态"""
        self.connection.hset(f"task:{task_id}:status", mapping=task_data)
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        task_data = self.connection.hgetall(f"task:{task_id}:status")
        if task_data:
            # Redis返回的键值对是字节格式，需要转换
            result = {}
            for key, value in task_data.items():
                key_str = key.decode('utf-8') if isinstance(key, bytes) else key
                value_str = value.decode('utf-8') if isinstance(value, bytes) else value
                try:
                    # 尝试解析JSON格式的值
                    result[key_str] = json.loads(value_str)
                except (json.JSONDecodeError, TypeError):
                    result[key_str] = value_str
            return result
        return None
    
    def get_all_processes(self) -> Dict[str, Any]:
        """获取所有进程状态"""
        process_keys = self.connection.keys("process:*:status")
        processes = {}
        
        for key in process_keys:
            key_str = key.decode('utf-8') if isinstance(key, bytes) else key
            process_info = self.connection.hgetall(key)
            
            # 转换字节为字符串
            clean_info = {}
            for k, v in process_info.items():
                k_str = k.decode('utf-8') if isinstance(k, bytes) else k
                v_str = v.decode('utf-8') if isinstance(v, bytes) else v
                clean_info[k_str] = v_str
            
            process_type = key_str.replace("process:", "").replace(":status", "")
            processes[process_type] = clean_info
        
        return processes


class MainProcessIPC(RedisIPC):
    """主进程IPC"""
    
    def get_process_type(self) -> str:
        return "main"


class FileMonitorIPC(RedisIPC):
    """文件监控进程IPC"""
    
    def get_process_type(self) -> str:
        return "file_monitor"


class EmbeddingWorkerIPC(RedisIPC):
    """向量化工作进程IPC"""
    
    def get_process_type(self) -> str:
        return "embedding_worker"


class TaskWorkerIPC(RedisIPC):
    """任务工作进程IPC"""
    
    def get_process_type(self) -> str:
        return "task_worker"