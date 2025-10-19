#!/usr/bin/env python3
"""
增强版Qdrant Mock
提供更稳定的向量数据库模拟功能，解决连接问题
"""

import sys
import os
import json
import threading
import time
from typing import Dict, List, Any, Optional

# 确保Windows编码正确
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

class EnhancedQdrantMock:
    """增强版Qdrant向量数据库模拟类"""
    
    def __init__(self):
        """初始化模拟数据库"""
        # 存储集合数据
        self.collections: Dict[str, Dict] = {}
        # 存储向量数据
        self.vectors: Dict[str, List[Dict]] = {}
        # 线程锁，确保线程安全
        self.lock = threading.RLock()
        # 连接状态
        self.connected = True
        # 操作计数器
        self.operation_count = 0
        # 模拟延迟配置
        self.delay_ms = 10  # 默认10ms延迟
        # 日志配置
        self.log_level = 'INFO'
        
        print("✅ EnhancedQdrantMock 初始化完成")
    
    def set_delay(self, delay_ms: int):
        """设置模拟延迟时间（毫秒）"""
        self.delay_ms = delay_ms
        print(f"⏱️ 设置模拟延迟: {delay_ms}ms")
    
    def set_log_level(self, level: str):
        """设置日志级别"""
        self.log_level = level.upper()
        print(f"📝 设置日志级别: {self.log_level}")
    
    def _log(self, level: str, message: str):
        """日志记录"""
        levels = {'DEBUG': 1, 'INFO': 2, 'WARNING': 3, 'ERROR': 4}
        if levels.get(level.upper(), 999) >= levels.get(self.log_level, 2):
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            print(f"[{timestamp}] [{level}] {message}")
    
    def _simulate_delay(self):
        """模拟网络延迟"""
        if self.delay_ms > 0:
            time.sleep(self.delay_ms / 1000)
    
    def connect(self, url: str, **kwargs) -> bool:
        """模拟连接"""
        with self.lock:
            self._log('INFO', f"🔌 模拟连接到 Qdrant 服务: {url}")
            self.connected = True
            self._simulate_delay()
            return True
    
    def disconnect(self):
        """模拟断开连接"""
        with self.lock:
            self._log('INFO', "🔌 断开Qdrant连接")
            self.connected = False
    
    def is_connected(self) -> bool:
        """检查连接状态"""
        return self.connected
    
    def create_collection(self, collection_name: str, vectors_config: Dict, **kwargs) -> Dict:
        """创建集合"""
        with self.lock:
            self._log('INFO', f"📚 创建集合: {collection_name}")
            if collection_name in self.collections:
                self._log('WARNING', f"集合 '{collection_name}' 已存在")
                return {'status': 'warning', 'message': f'Collection {collection_name} already exists'}
            
            self.collections[collection_name] = {
                'name': collection_name,
                'vectors_config': vectors_config,
                'created_at': time.time(),
                'kwargs': kwargs
            }
            self.vectors[collection_name] = []
            self.operation_count += 1
            self._simulate_delay()
            
            return {
                'status': 'ok',
                'result': {
                    'collection_name': collection_name
                }
            }
    
    def delete_collection(self, collection_name: str) -> Dict:
        """删除集合"""
        with self.lock:
            self._log('INFO', f"🗑️ 删除集合: {collection_name}")
            if collection_name not in self.collections:
                self._log('ERROR', f"集合 '{collection_name}' 不存在")
                return {'status': 'error', 'message': f'Collection {collection_name} does not exist'}
            
            del self.collections[collection_name]
            del self.vectors[collection_name]
            self.operation_count += 1
            self._simulate_delay()
            
            return {'status': 'ok'}
    
    def upsert(self, collection_name: str, points: List[Dict], **kwargs) -> Dict:
        """插入或更新向量点"""
        with self.lock:
            self._log('DEBUG', f"📥 向集合 '{collection_name}' 插入 {len(points)} 个点")
            
            if collection_name not in self.collections:
                self._log('ERROR', f"集合 '{collection_name}' 不存在")
                return {'status': 'error', 'message': f'Collection {collection_name} does not exist'}
            
            # 确保点列表有效
            if not isinstance(points, list):
                self._log('ERROR', "points参数必须是列表类型")
                return {'status': 'error', 'message': 'Points must be a list'}
            
            # 处理每个点
            for point in points:
                if not isinstance(point, dict):
                    self._log('WARNING', "跳过无效点数据")
                    continue
                    
                # 检查必要字段
                point_id = point.get('id', self._generate_id())
                vector = point.get('vector', [])
                
                # 查找并更新现有点或添加新点
                updated = False
                for i, existing_point in enumerate(self.vectors[collection_name]):
                    if existing_point.get('id') == point_id:
                        self.vectors[collection_name][i] = point
                        updated = True
                        break
                
                if not updated:
                    self.vectors[collection_name].append(point)
            
            self.operation_count += 1
            self._simulate_delay()
            
            return {
                'status': 'ok',
                'result': {
                    'operation_id': str(self.operation_count),
                    'status': 'completed'
                }
            }
    
    def search(self, collection_name: str, vector: List[float], limit: int = 10, **kwargs) -> List[Dict]:
        """搜索相似向量"""
        with self.lock:
            self._log('DEBUG', f"🔍 在集合 '{collection_name}' 中搜索相似向量，限制结果数: {limit}")
            
            if collection_name not in self.collections:
                self._log('ERROR', f"集合 '{collection_name}' 不存在")
                return []
            
            if not vector or not isinstance(vector, list):
                self._log('ERROR', "无效的搜索向量")
                return []
            
            results = []
            # 简单的模拟搜索 - 随机生成相似度分数
            for point in self.vectors[collection_name]:
                if 'vector' in point:
                    # 计算简单的相似度分数（实际应用中应使用真正的向量相似度算法）
                    similarity = 0.5 + (hash(str(point)) % 50) / 100
                    results.append({
                        'id': point.get('id'),
                        'score': similarity,
                        'payload': point.get('payload', {})
                    })
            
            # 按相似度排序并限制结果数量
            results.sort(key=lambda x: x['score'], reverse=True)
            results = results[:limit]
            
            self._simulate_delay()
            self._log('DEBUG', f"✅ 搜索完成，返回 {len(results)} 个结果")
            
            return results
    
    def scroll(self, collection_name: str, limit: int = 100, **kwargs) -> Dict:
        """滚动遍历集合中的点"""
        with self.lock:
            self._log('INFO', f"📜 滚动遍历集合 '{collection_name}'，限制: {limit}")
            
            if collection_name not in self.collections:
                self._log('ERROR', f"集合 '{collection_name}' 不存在")
                return {'status': 'error', 'message': f'Collection {collection_name} does not exist'}
            
            offset = kwargs.get('offset', 0)
            limit = min(limit, 1000)  # 最大限制
            
            points = self.vectors[collection_name][offset:offset + limit]
            has_more = offset + limit < len(self.vectors[collection_name])
            
            self._simulate_delay()
            
            return {
                'status': 'ok',
                'result': {
                    'points': points,
                    'next_page_offset': offset + limit if has_more else None
                }
            }
    
    def count(self, collection_name: str, **kwargs) -> Dict:
        """计数集合中的点数量"""
        with self.lock:
            self._log('INFO', f"🔢 计数集合 '{collection_name}' 中的点数量")
            
            if collection_name not in self.collections:
                self._log('ERROR', f"集合 '{collection_name}' 不存在")
                return {'status': 'error', 'message': f'Collection {collection_name} does not exist'}
            
            count = len(self.vectors[collection_name])
            self._simulate_delay()
            
            return {
                'status': 'ok',
                'result': {
                    'count': count
                }
            }
    
    def update_collection(self, collection_name: str, **kwargs) -> Dict:
        """更新集合配置"""
        with self.lock:
            self._log('INFO', f"🔄 更新集合 '{collection_name}' 配置")
            
            if collection_name not in self.collections:
                self._log('ERROR', f"集合 '{collection_name}' 不存在")
                return {'status': 'error', 'message': f'Collection {collection_name} does not exist'}
            
            self.collections[collection_name].update(kwargs)
            self.operation_count += 1
            self._simulate_delay()
            
            return {'status': 'ok'}
    
    def get_collection(self, collection_name: str) -> Dict:
        """获取集合信息"""
        with self.lock:
            self._log('INFO', f"ℹ️ 获取集合 '{collection_name}' 信息")
            
            if collection_name not in self.collections:
                self._log('ERROR', f"集合 '{collection_name}' 不存在")
                return {'status': 'error', 'message': f'Collection {collection_name} does not exist'}
            
            self._simulate_delay()
            
            return {
                'status': 'ok',
                'result': self.collections[collection_name]
            }
    
    def _generate_id(self) -> int:
        """生成唯一ID"""
        return hash(str(time.time())) % 1000000
    
    def clear_all(self):
        """清空所有数据"""
        with self.lock:
            self._log('WARNING', "🧹 清空所有集合和向量数据")
            self.collections.clear()
            self.vectors.clear()
            self.operation_count = 0
    
    def export_state(self, file_path: str) -> bool:
        """导出当前状态到文件"""
        try:
            with self.lock:
                state = {
                    'collections': self.collections,
                    'vectors': self.vectors,
                    'operation_count': self.operation_count,
                    'timestamp': time.time()
                }
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(state, f, ensure_ascii=False, indent=2)
                
                self._log('INFO', f"💾 状态已导出到: {file_path}")
                return True
        except Exception as e:
            self._log('ERROR', f"导出状态失败: {str(e)}")
            return False
    
    def import_state(self, file_path: str) -> bool:
        """从文件导入状态"""
        try:
            with self.lock:
                with open(file_path, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                
                self.collections = state.get('collections', {})
                self.vectors = state.get('vectors', {})
                self.operation_count = state.get('operation_count', 0)
                
                self._log('INFO', f"📥 从 {file_path} 导入状态成功")
                return True
        except Exception as e:
            self._log('ERROR', f"导入状态失败: {str(e)}")
            return False

# 创建单例实例
_qdrant_mock_instance = None
_instance_lock = threading.Lock()

def get_qdrant_mock() -> EnhancedQdrantMock:
    """获取Qdrant mock的单例实例"""
    global _qdrant_mock_instance
    with _instance_lock:
        if _qdrant_mock_instance is None:
            _qdrant_mock_instance = EnhancedQdrantMock()
    return _qdrant_mock_instance

# 兼容层，模拟QdrantClient的主要接口
class MockQdrantClient:
    """QdrantClient兼容层"""
    
    def __init__(self, url: str = None, api_key: str = None, **kwargs):
        """初始化兼容客户端"""
        self.mock = get_qdrant_mock()
        self.mock.connect(url or "http://localhost:6333")
        self._log('INFO', "MockQdrantClient初始化完成")
    
    def _log(self, level: str, message: str):
        """调用mock的日志方法"""
        self.mock._log(level, message)
    
    # 以下是兼容QdrantClient API的方法
    def get_collection(self, collection_name: str):
        """获取集合信息"""
        return self.mock.get_collection(collection_name)
    
    def create_collection(self, collection_name: str, vectors_config: Dict, **kwargs):
        """创建集合"""
        return self.mock.create_collection(collection_name, vectors_config, **kwargs)
    
    def delete_collection(self, collection_name: str):
        """删除集合"""
        return self.mock.delete_collection(collection_name)
    
    def upsert(self, collection_name: str, points: List[Dict], **kwargs):
        """插入或更新向量点"""
        return self.mock.upsert(collection_name, points, **kwargs)
    
    def search(self, collection_name: str, query_vector: List[float], limit: int = 10, **kwargs):
        """搜索相似向量"""
        return self.mock.search(collection_name, query_vector, limit, **kwargs)
    
    def scroll(self, collection_name: str, limit: int = 100, **kwargs):
        """滚动遍历集合中的点"""
        return self.mock.scroll(collection_name, limit, **kwargs)
    
    def count(self, collection_name: str, **kwargs):
        """计数集合中的点数量"""
        return self.mock.count(collection_name, **kwargs)
    
    def close(self):
        """关闭连接"""
        self.mock.disconnect()

if __name__ == "__main__":
    # 简单的测试
    print("🔬 测试EnhancedQdrantMock功能")
    mock = EnhancedQdrantMock()
    mock.set_log_level('DEBUG')
    
    # 创建集合
    mock.create_collection('test_collection', {'size': 768, 'distance': 'Cosine'})
    
    # 插入向量
    mock.upsert('test_collection', [
        {'id': 1, 'vector': [0.1] * 10, 'payload': {'text': '测试向量1'}},
        {'id': 2, 'vector': [0.2] * 10, 'payload': {'text': '测试向量2'}}
    ])
    
    # 搜索
    results = mock.search('test_collection', [0.15] * 10, limit=2)
    print(f"搜索结果: {results}")
    
    # 计数
    count = mock.count('test_collection')
    print(f"集合点数: {count}")
    
    print("✅ 测试完成")
