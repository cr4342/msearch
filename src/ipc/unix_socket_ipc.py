"""
Unix Socket IPC 实现 - 用于进程间低延迟通信
"""
import socket
import os
import json
import time
import threading
from typing import Dict, Any, Optional


class UnixSocketIPC:
    """
    基于 Unix Socket 的进程间通信实现
    适用于低延迟的控制命令和状态查询
    """
    
    def __init__(self, socket_path: str = "/tmp/msearch_ipc.sock"):
        self.socket_path = socket_path
        self.server_socket = None
        self.client_socket = None
        self.running = False
        self.thread = None
        self.message_handlers = []
        self.lock = threading.Lock()
    
    def start_server(self) -> bool:
        """启动 Unix Socket 服务器"""
        try:
            # 清理旧的 socket 文件
            if os.path.exists(self.socket_path):
                os.unlink(self.socket_path)
            
            # 创建 Unix Domain Socket
            self.server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.server_socket.bind(self.socket_path)
            self.server_socket.listen(5)
            self.running = True
            
            # 启动接收线程
            self.thread = threading.Thread(target=self._server_loop, daemon=True)
            self.thread.start()
            
            print(f"Unix Socket 服务器已启动: {self.socket_path}")
            return True
        except Exception as e:
            print(f"启动 Unix Socket 服务器失败: {e}")
            return False
    
    def _server_loop(self):
        """服务器主循环"""
        while self.running:
            try:
                # 设置超时以允许优雅退出
                self.server_socket.settimeout(1.0)
                client, address = self.server_socket.accept()
                
                # 处理客户端连接
                self._handle_client(client)
            except socket.timeout:
                continue
            except Exception as e:
                if not self.running:
                    break
                print(f"服务器循环错误: {e}")
                time.sleep(0.1)
    
    def _handle_client(self, client: socket.socket):
        """处理客户端连接"""
        try:
            # 接收数据
            data = b''
            while True:
                chunk = client.recv(4096)
                if not chunk:
                    break
                data += chunk
                # 检查是否接收到完整消息
                if b'\n\n' in data:
                    break
            
            if data:
                # 解析消息
                message = json.loads(data.decode('utf-8'))
                
                # 调用消息处理器
                for handler in self.message_handlers:
                    try:
                        handler(message)
                    except Exception as e:
                        print(f"消息处理器错误: {e}")
                
                # 发送响应
                response = {
                    "status": "success",
                    "timestamp": time.time()
                }
                client.sendall(json.dumps(response).encode('utf-8') + b'\n\n')
        except Exception as e:
            print(f"处理客户端错误: {e}")
        finally:
            try:
                client.close()
            except:
                pass
    
    def connect(self) -> bool:
        """连接到 Unix Socket 服务器"""
        try:
            self.client_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.client_socket.connect(self.socket_path)
            print(f"已连接到 Unix Socket 服务器: {self.socket_path}")
            return True
        except Exception as e:
            print(f"连接 Unix Socket 服务器失败: {e}")
            self.client_socket = None
            return False
    
    def send_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """发送消息到服务器并返回响应"""
        if not self.client_socket:
            if not self.connect():
                return None
        
        try:
            # 发送消息
            message_data = json.dumps(message).encode('utf-8') + b'\n\n'
            self.client_socket.sendall(message_data)
            
            # 接收响应
            response_data = b''
            while True:
                chunk = self.client_socket.recv(4096)
                if not chunk:
                    break
                response_data += chunk
                if b'\n\n' in response_data:
                    break
            
            if response_data:
                return json.loads(response_data.decode('utf-8'))
            return None
        except Exception as e:
            print(f"发送消息失败: {e}")
            self.client_socket = None
            return None
    
    def register_message_handler(self, handler: callable):
        """注册消息处理器"""
        with self.lock:
            if handler not in self.message_handlers:
                self.message_handlers.append(handler)
    
    def unregister_message_handler(self, handler: callable):
        """注销消息处理器"""
        with self.lock:
            if handler in self.message_handlers:
                self.message_handlers.remove(handler)
    
    def stop(self):
        """停止服务器"""
        self.running = False
        
        # 关闭服务器 socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        # 关闭客户端 socket
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
        
        # 等待线程退出
        if self.thread:
            self.thread.join(timeout=2.0)
        
        # 清理 socket 文件
        if os.path.exists(self.socket_path):
            try:
                os.unlink(self.socket_path)
            except:
                pass
        
        print("Unix Socket 服务器已停止")
    
    def __enter__(self):
        """上下文管理器入口"""
        self.start_server()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.stop()


class LocalCommandClient:
    """
    本地命令客户端
    用于发送控制命令到其他进程
    """
    
    def __init__(self, socket_path: str = "/tmp/msearch_ipc.sock"):
        self.socket_path = socket_path
        self.ipc = UnixSocketIPC(socket_path)
    
    def send_command(self, command: str, data: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """发送命令"""
        message = {
            "type": "command",
            "command": command,
            "data": data or {},
            "timestamp": time.time()
        }
        
        if self.ipc.connect():
            response = self.ipc.send_message(message)
            self.ipc.stop()
            return response
        return None
    
    def get_status(self) -> Optional[Dict[str, Any]]:
        """获取状态"""
        return self.send_command("get_status")
    
    def pause_process(self, process_name: str) -> Optional[Dict[str, Any]]:
        """暂停进程"""
        return self.send_command("pause_process", {"process_name": process_name})
    
    def resume_process(self, process_name: str) -> Optional[Dict[str, Any]]:
        """恢复进程"""
        return self.send_command("resume_process", {"process_name": process_name})
    
    def shutdown_process(self, process_name: str) -> Optional[Dict[str, Any]]:
        """关闭进程"""
        return self.send_command("shutdown_process", {"process_name": process_name})


# 使用示例
if __name__ == "__main__":
    # 服务器示例
    def message_handler(message):
        print(f"接收到消息: {message}")
    
    server = UnixSocketIPC("/tmp/test_ipc.sock")
    server.register_message_handler(message_handler)
    server.start_server()
    
    try:
        # 客户端示例
        time.sleep(1)
        client = LocalCommandClient("/tmp/test_ipc.sock")
        response = client.send_command("test_command", {"key": "value"})
        print(f"客户端响应: {response}")
        
        # 等待
        time.sleep(5)
    finally:
        server.stop()
