"""
共享内存管理器 - 用于进程间大文件数据传输
"""
import mmap
import os
import struct
import tempfile
from typing import Optional


class SharedMemoryManager:
    """共享内存管理器"""
    
    def __init__(self, name: str, size: int = 100 * 1024 * 1024):  # 100MB 默认大小
        self.name = name
        self.size = size
        self.mm = None
        self.temp_file = None
        
        # 在Linux/macOS上使用 /dev/shm，否则使用临时文件
        if os.name == 'posix' and os.path.exists('/dev/shm'):
            self._shm_path = f'/dev/shm/{name}'
        else:
            # 使用临时文件
            self.temp_file = tempfile.NamedTemporaryFile(delete=False)
            self._shm_path = self.temp_file.name
    
    def create(self):
        """创建共享内存"""
        try:
            # 如果是临时文件，先创建文件
            if self.temp_file:
                with open(self._shm_path, 'wb') as f:
                    f.write(b'\x00' * self.size)
            
            # 打开文件用于内存映射
            fd = os.open(self._shm_path, os.O_CREAT | os.O_RDWR)
            os.ftruncate(fd, self.size)
            
            # 创建内存映射
            self.mm = mmap.mmap(fd, self.size)
            os.close(fd)
            
            return True
        except Exception as e:
            print(f"创建共享内存失败: {e}")
            return False
    
    def write(self, data: bytes, offset: int = 0) -> int:
        """写入数据，返回实际写入字节数"""
        if self.mm is None:
            raise RuntimeError("共享内存未初始化，请先调用create()")
        
        if offset + len(data) > self.size:
            raise ValueError(f"写入数据超出共享内存范围: {offset + len(data)} > {self.size}")
        
        try:
            # 将数据写入内存映射
            self.mm[offset:offset + len(data)] = data
            return len(data)
        except Exception as e:
            print(f"写入共享内存失败: {e}")
            return 0
    
    def read(self, offset: int, size: int) -> bytes:
        """读取数据"""
        if self.mm is None:
            raise RuntimeError("共享内存未初始化，请先调用create()")
        
        if offset + size > self.size:
            raise ValueError(f"读取数据超出共享内存范围: {offset + size} > {self.size}")
        
        if offset < 0 or size < 0:
            raise ValueError("偏移量和大小必须为非负数")
        
        try:
            # 从内存映射中读取数据
            return self.mm[offset:offset + size]
        except Exception as e:
            print(f"读取共享内存失败: {e}")
            return b''
    
    def close(self):
        """关闭共享内存"""
        if self.mm is not None:
            try:
                self.mm.close()
            except:
                pass
            self.mm = None
        
        # 如果使用了临时文件，删除它
        if self.temp_file and os.path.exists(self._shm_path):
            os.unlink(self._shm_path)
            self.temp_file = None
    
    def __enter__(self):
        """上下文管理器入口"""
        self.create()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()


class SharedMemoryBuffer:
    """共享内存缓冲区，支持数据分块传输"""
    
    def __init__(self, shared_memory: SharedMemoryManager):
        self.shared_memory = shared_memory
        self.header_size = 16  # 包含数据大小、类型等信息
    
    def write_data(self, data: bytes, data_type: str = "default") -> bool:
        """写入数据，包含头部信息"""
        try:
            # 头部格式: [数据大小(8字节) | 数据类型长度(4字节) | 类型字符串(最多4字节)]
            data_size = len(data)
            type_bytes = data_type.encode('utf-8')[:4]
            type_len = len(type_bytes)
            
            # 写入头部
            header = struct.pack('QI4s', data_size, type_len, type_bytes)
            self.shared_memory.write(header, 0)
            
            # 写入实际数据
            self.shared_memory.write(data, self.header_size)
            
            return True
        except Exception as e:
            print(f"写入数据失败: {e}")
            return False
    
    def read_data(self) -> Optional[tuple]:
        """读取数据，返回(数据, 数据类型)元组"""
        try:
            # 读取头部
            header = self.shared_memory.read(0, self.header_size)
            if len(header) < self.header_size:
                return None
            
            # 解析头部
            data_size, type_len, type_bytes = struct.unpack('QI4s', header)
            
            # 读取数据
            if data_size > 0:
                data = self.shared_memory.read(self.header_size, data_size)
            else:
                data = b''
            
            # 解析类型
            data_type = type_bytes.decode('utf-8', errors='ignore').rstrip('\x00')
            
            return data, data_type
        except Exception as e:
            print(f"读取数据失败: {e}")
            return None


# 使用示例
if __name__ == "__main__":
    # 创建共享内存
    with SharedMemoryManager("test_shm", 1024*1024) as shm:  # 1MB
        buffer = SharedMemoryBuffer(shm)
        
        # 写入数据
        test_data = b"Hello, Shared Memory!"
        success = buffer.write_data(test_data, "test")
        print(f"写入成功: {success}")
        
        # 读取数据
        result = buffer.read_data()
        if result:
            data, data_type = result
            print(f"读取数据: {data.decode()}, 类型: {data_type}")
        else:
            print("读取失败")