"""
进程间通信基类定义（优化版）
采用SQLite队列 + 本地IPC + 共享内存的组合方案，移除Redis依赖
"""

import json
import time
import uuid
import sqlite3
import threading
from typing import Any, Dict, Optional, List
from abc import ABC, abstractmethod
import socket
import os
from collections import OrderedDict

import persistqueue


class IPCBase(ABC):
    """进程间通信基类（优化版）"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.process_id = str(uuid.uuid4())
        self.process_type = "unknown"
        self.db_path = config.get("db_path", "data/ipc.db")
        self.queue_path = config.get("queue_path", "data/task_queue")
        self.socket_path = config.get("socket_path", "/tmp/msearch.sock")
    
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


class SQLiteIPC(IPCBase):
    """基于SQLite的进程间通信实现（替代Redis）"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config or {
            "db_path": "data/ipc.db",
            "queue_path": "data/task_queue",
            "memory_capacity": 1000
        })
        
        # 初始化SQLite数据库
        self.init_database()
        
        # 初始化持久化队列
        self.task_queue = persistqueue.SQLiteQueue(
            path=self.queue_path,
            multithreading=True,
            auto_commit=True
        )
        
        # 初始化内存LRU缓存
        self.memory_cache = LRUCache(capacity=self.config.get("memory_capacity", 1000))
        
        # 心跳间隔
        self.heartbeat_interval = 30
    
    def init_database(self):
        """初始化SQLite数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建任务表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                priority INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                created_at REAL NOT NULL,
                started_at REAL,
                completed_at REAL,
                worker_id TEXT,
                result TEXT,
                error TEXT,
                sender TEXT,
                sender_type TEXT
            )
        ''')
        
        # 创建进程状态表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS process_states (
                process_id TEXT PRIMARY KEY,
                process_type TEXT NOT NULL,
                status TEXT DEFAULT 'running',
                pid INTEGER,
                heartbeat REAL,
                created_at REAL NOT NULL,
                last_updated REAL NOT NULL
            )
        ''')
        
        # 创建任务状态缓存表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS task_states (
                task_id TEXT PRIMARY KEY,
                state_data TEXT NOT NULL,
                last_updated REAL NOT NULL,
                accessed_count INTEGER DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def connect(self) -> bool:
        """建立连接"""
        try:
            # 注册进程
            self.register_process()
            return True
        except Exception as e:
            print(f"SQLite IPC连接失败: {e}")
            return False
    
    def disconnect(self) -> None:
        """断开连接"""
        # 取消进程注册
        self.unregister_process()
    
    def register_process(self) -> None:
        """注册进程信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        process_info = {
            "process_id": self.process_id,
            "process_type": self.get_process_type(),
            "status": "running",
            "pid": os.getpid(),
            "heartbeat": time.time(),
            "created_at": time.time(),
            "last_updated": time.time()
        }
        
        cursor.execute('''
            INSERT OR REPLACE INTO process_states 
            (process_id, process_type, status, pid, heartbeat, created_at, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            process_info["process_id"], process_info["process_type"], process_info["status"],
            process_info["pid"], process_info["heartbeat"], process_info["created_at"],
            process_info["last_updated"]
        ))
        
        conn.commit()
        conn.close()
    
    def unregister_process(self) -> None:
        """取消进程注册"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            'DELETE FROM process_states WHERE process_id = ?',
            (self.process_id,)
        )
        
        conn.commit()
        conn.close()
    
    def update_heartbeat(self) -> None:
        """更新心跳"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE process_states 
            SET heartbeat = ?, last_updated = ?
            WHERE process_id = ?
        ''', (time.time(), time.time(), self.process_id))
        
        conn.commit()
        conn.close()
    
    def get_process_type(self) -> str:
        """获取进程类型，子类需要重写"""
        return self.process_type
    
    def send_message(self, message: Dict[str, Any], destination: str) -> bool:
        """发送消息到指定目的地"""
        try:
            # 添加时间戳和发送者信息
            message["timestamp"] = time.time()
            message["sender"] = self.process_id
            message["sender_type"] = self.get_process_type()
            message["destination"] = destination
            
            # 序列化消息
            serialized_message = json.dumps(message, ensure_ascii=False)
            
            # 存储到SQLite队列（使用persistqueue）
            queue_path = f"{self.queue_path}_{destination}"
            queue = persistqueue.SQLiteQueue(path=queue_path, multithreading=True)
            queue.put(serialized_message)
            
            return True
        except Exception as e:
            print(f"发送消息失败: {e}")
            return False
    
    def receive_message(self, source: str, timeout: int = 1) -> Optional[Dict[str, Any]]:
        """从指定源接收消息"""
        try:
            # 尝试从自己的队列获取消息
            queue_path = f"{self.queue_path}_{self.get_process_type()}"
            queue = persistqueue.SQLiteQueue(path=queue_path, multithreading=True)
            
            # 尝试获取消息（使用轮询方式模拟超时）
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    serialized_message = queue.get(timeout=0.1)
                    message = json.loads(serialized_message)
                    
                    # 检查消息来源（可选）
                    if source and message.get("sender_type") != source:
                        # 如果指定来源但不匹配，重新放回队列
                        queue.put(serialized_message)
                        continue
                    
                    return message
                except persistqueue.exceptions.Empty:
                    continue  # 队列为空，继续等待
            
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
        priority_map = {
            "high": 10,
            "normal": 5,
            "low": 1
        }
        priority_value = priority_map.get(priority, 5)
        
        # 存储到任务表
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO tasks 
            (id, data, priority, status, created_at, sender, sender_type)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            task_id, json.dumps(task_data), priority_value, 
            "pending", time.time(), self.process_id, self.get_process_type()
        ))
        
        conn.commit()
        conn.close()
        
        # 同时放到队列中
        task_queue = persistqueue.SQLiteQueue(
            path=f"{self.queue_path}_priority_{priority}",
            multithreading=True
        )
        task_queue.put(task)
        
        return task_id
    
    def get_task(self, timeout: int = 1) -> Optional[Dict[str, Any]]:
        """从任务队列获取任务"""
        # 按优先级顺序尝试获取任务
        priority_queues = ["high", "normal", "low"]
        
        for priority in priority_queues:
            queue_path = f"{self.queue_path}_priority_{priority}"
            queue = persistqueue.SQLiteQueue(path=queue_path, multithreading=True)
            
            try:
                # 尝试获取任务
                task = queue.get(timeout=0.1)  # 短超时，避免长时间阻塞
                
                # 更新任务状态为处理中
                if isinstance(task, str):
                    task = json.loads(task)
                
                task["status"] = "processing"
                task["started_at"] = time.time()
                task["worker"] = self.process_id
                self.set_task_status(task["task_id"], task)
                
                return task
            except persistqueue.exceptions.Empty:
                continue  # 当前优先级队列为空，尝试下一个
        
        # 如果所有队列都为空，使用轮询方式等待
        start_time = time.time()
        while time.time() - start_time < timeout:
            for priority in priority_queues:
                queue_path = f"{self.queue_path}_priority_{priority}"
                queue = persistqueue.SQLiteQueue(path=queue_path, multithreading=True)
                
                try:
                    task = queue.get(timeout=0.1)
                    
                    if isinstance(task, str):
                        task = json.loads(task)
                    
                    task["status"] = "processing"
                    task["started_at"] = time.time()
                    task["worker"] = self.process_id
                    self.set_task_status(task["task_id"], task)
                    
                    return task
                except persistqueue.exceptions.Empty:
                    continue
        
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
            
            # 更新数据库中的任务状态
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE tasks 
                SET status = 'completed', completed_at = ?, result = ?
                WHERE id = ?
            ''', (time.time(), json.dumps(result), task_id))
            
            conn.commit()
            conn.close()
    
    def fail_task(self, task_id: str, error: str) -> None:
        """标记任务失败"""
        task = self.get_task_status(task_id)
        if task:
            task["status"] = "failed"
            task["error"] = error
            task["failed_at"] = time.time()
            self.set_task_status(task_id, task)
            
            # 更新数据库中的任务状态
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE tasks 
                SET status = 'failed', error = ?, failed_at = ?
                WHERE id = ?
            ''', (error, time.time(), task_id))
            
            conn.commit()
            conn.close()
    
    def set_task_status(self, task_id: str, task_data: Dict[str, Any]) -> None:
        """设置任务状态"""
        # 更新内存缓存
        self.memory_cache.put(task_id, task_data)
        
        # 更新数据库
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO task_states 
            (task_id, state_data, last_updated, accessed_count)
            VALUES (?, ?, ?, COALESCE((SELECT accessed_count FROM task_states WHERE task_id = ?), 0) + 1)
        ''', (task_id, json.dumps(task_data), time.time(), task_id))
        
        conn.commit()
        conn.close()
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        # 先查内存缓存
        cached = self.memory_cache.get(task_id)
        if cached:
            return cached
        
        # 内存中未找到，查数据库
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT state_data FROM task_states WHERE task_id = ?',
            (task_id,)
        )
        result = cursor.fetchone()
        
        conn.close()
        
        if result:
            state_data = json.loads(result[0])
            # 加入内存缓存
            self.memory_cache.put(task_id, state_data)
            return state_data
        
        return None
    
    def get_all_processes(self) -> Dict[str, Any]:
        """获取所有进程状态"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM process_states')
        rows = cursor.fetchall()
        
        processes = {}
        for row in rows:
            process_id, process_type, status, pid, heartbeat, created_at, last_updated = row
            processes[process_type] = {
                "process_id": process_id,
                "status": status,
                "pid": pid,
                "heartbeat": heartbeat,
                "created_at": created_at,
                "last_updated": last_updated
            }
        
        conn.close()
        return processes


class LRUCache:
    """内存LRU缓存"""
    def __init__(self, capacity: int = 1000):
        self.capacity = capacity
        self.cache = OrderedDict()
        self.lock = threading.Lock()

    def get(self, key: str):
        with self.lock:
            if key in self.cache:
                # 移动到末尾，表示最近使用
                self.cache.move_to_end(key)
                return self.cache[key]
            return None

    def put(self, key: str, value):
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
            elif len(self.cache) >= self.capacity:
                # 删除最久未使用的项
                self.cache.popitem(last=False)
            self.cache[key] = value


class LocalIPC:
    """本地进程间通信（Unix Socket/Named Pipe）"""
    
    def __init__(self, socket_path: str = '/tmp/msearch.sock'):
        self.socket_path = socket_path
        self.socket = None
        self.is_server = False
        self.lock = threading.Lock()
    
    def start_server(self):
        """启动服务器（主进程）"""
        if os.path.exists(self.socket_path):
            os.unlink(self.socket_path)
        
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.socket.bind(self.socket_path)
        self.socket.listen(5)
        self.is_server = True
        
        # 设置权限，只允许当前用户访问
        os.chmod(self.socket_path, 0o600)
    
    def connect_client(self):
        """连接服务器（子进程）"""
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.socket.connect(self.socket_path)
    
    def send_message(self, message: Dict[str, Any]) -> bool:
        """发送消息"""
        try:
            serialized = json.dumps(message) + '\n'
            self.socket.send(serialized.encode('utf-8'))
            return True
        except Exception as e:
            print(f"发送消息失败: {e}")
            return False
    
    def receive_message(self, timeout: int = 1) -> Optional[Dict[str, Any]]:
        """接收消息"""
        try:
            self.socket.settimeout(timeout)
            data = self.socket.recv(4096).decode('utf-8').strip()
            if data:
                return json.loads(data)
        except socket.timeout:
            return None
        except Exception as e:
            print(f"接收消息失败: {e}")
            return None
        return None
    
    def close(self):
        """关闭连接"""
        if self.socket:
            self.socket.close()
            if self.is_server and os.path.exists(self.socket_path):
                os.unlink(self.socket_path)


class MainProcessIPC(SQLiteIPC):
    """主进程IPC"""
    
    def get_process_type(self) -> str:
        return "main"


class FileMonitorIPC(SQLiteIPC):
    """文件监控进程IPC"""
    
    def get_process_type(self) -> str:
        return "file_monitor"


class EmbeddingWorkerIPC(SQLiteIPC):
    """向量化工作进程IPC"""
    
    def get_process_type(self) -> str:
        return "embedding_worker"


class TaskWorkerIPC(SQLiteIPC):
    """任务工作进程IPC"""
    
    def get_process_type(self) -> str:
        return "task_worker"
