"""
硬件检测器
检测系统硬件配置并推荐合适的模型
"""

import platform
import os
import subprocess
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class HardwareDetector:
    """硬件检测器"""
    
    def __init__(self):
        """初始化硬件检测器"""
        self.system_info = {}
        self.cpu_info = {}
        self.gpu_info = {}
        self.memory_info = {}
        self.disk_info = {}
        
        # 检测硬件
        self._detect_all()
    
    def _detect_all(self) -> None:
        """检测所有硬件信息"""
        try:
            self._detect_system()
            self._detect_cpu()
            self._detect_memory()
            self._detect_gpu()
            self._detect_disk()
            logger.info("硬件检测完成")
        except Exception as e:
            logger.error(f"硬件检测失败: {e}")
    
    def _detect_system(self) -> None:
        """检测系统信息"""
        self.system_info = {
            'platform': platform.system(),
            'platform_release': platform.release(),
            'platform_version': platform.version(),
            'architecture': platform.machine(),
            'hostname': platform.node(),
            'processor': platform.processor()
        }
    
    def _detect_cpu(self) -> None:
        """检测CPU信息"""
        try:
            # CPU核心数
            self.cpu_info = {
                'physical_cores': os.cpu_count() or 0,
                'total_cores': os.cpu_count() or 0,
                'max_frequency': 0.0,
                'min_frequency': 0.0,
                'model': ''
            }
            
            # 获取CPU频率
            if platform.system() == 'Linux':
                try:
                    with open('/proc/cpuinfo', 'r') as f:
                        cpuinfo = f.read()
                        for line in cpuinfo.split('\n'):
                            if 'model name' in line:
                                self.cpu_info['model'] = line.split(':')[1].strip()
                                break
                            elif 'cpu MHz' in line:
                                self.cpu_info['max_frequency'] = float(line.split(':')[1].strip()) / 1000.0
                except Exception as e:
                    logger.warning(f"获取CPU信息失败: {e}")
            
            elif platform.system() == 'Darwin':  # macOS
                try:
                    result = subprocess.run(['sysctl', '-n', 'hw.cpufrequency'], capture_output=True, text=True)
                    if result.returncode == 0:
                        self.cpu_info['max_frequency'] = float(result.stdout.strip()) / 1000000000.0
                    
                    result = subprocess.run(['sysctl', '-n', 'machdep.cpu.brand_string'], capture_output=True, text=True)
                    if result.returncode == 0:
                        self.cpu_info['model'] = result.stdout.strip()
                except Exception as e:
                    logger.warning(f"获取macOS CPU信息失败: {e}")
            
            elif platform.system() == 'Windows':
                try:
                    import wmi
                    c = wmi.WMI()
                    for cpu in c.Win32_Processor():
                        self.cpu_info['physical_cores'] = cpu.NumberOfCores
                        self.cpu_info['model'] = cpu.Name
                        if cpu.MaxClockSpeed:
                            self.cpu_info['max_frequency'] = cpu.MaxClockSpeed / 1000.0
                        break
                except Exception as e:
                    logger.warning(f"获取Windows CPU信息失败: {e}")
            
        except Exception as e:
            logger.error(f"检测CPU失败: {e}")
    
    def _detect_memory(self) -> None:
        """检测内存信息"""
        try:
            self.memory_info = {
                'total': 0,
                'available': 0,
                'used': 0,
                'percent': 0.0
            }
            
            if platform.system() == 'Linux':
                try:
                    with open('/proc/meminfo', 'r') as f:
                        meminfo = {}
                        for line in f:
                            key, value = line.split(':')
                            meminfo[key.strip()] = int(value.split()[0])
                    
                    total = meminfo.get('MemTotal', 0) / 1024  # MB
                    available = meminfo.get('MemAvailable', meminfo.get('MemFree', 0)) / 1024  # MB
                    used = total - available
                    
                    self.memory_info = {
                        'total': int(total),
                        'available': int(available),
                        'used': int(used),
                        'percent': round(used / total * 100, 2) if total > 0 else 0.0
                    }
                except Exception as e:
                    logger.warning(f"获取Linux内存信息失败: {e}")
            
            elif platform.system() == 'Darwin':
                try:
                    result = subprocess.run(['sysctl', '-n', 'hw.memsize'], capture_output=True, text=True)
                    if result.returncode == 0:
                        total_gb = float(result.stdout.strip()) / (1024**3)
                        self.memory_info['total'] = int(total_gb * 1024)
                        self.memory_info['available'] = int(total_gb * 1024 * 0.7)
                        self.memory_info['used'] = int(total_gb * 1024 * 0.3)
                        self.memory_info['percent'] = 30.0
                except Exception as e:
                    logger.warning(f"获取macOS内存信息失败: {e}")
            
            elif platform.system() == 'Windows':
                try:
                    import psutil
                    mem = psutil.virtual_memory()
                    self.memory_info = {
                        'total': int(mem.total / (1024**2)),
                        'available': int(mem.available / (1024**2)),
                        'used': int(mem.used / (1024**2)),
                        'percent': round(mem.percent, 2)
                    }
                except Exception as e:
                    logger.warning(f"获取Windows内存信息失败: {e}")
            
            # 使用psutil作为后备
            if self.memory_info['total'] == 0:
                try:
                    import psutil
                    mem = psutil.virtual_memory()
                    self.memory_info = {
                        'total': int(mem.total / (1024**2)),
                        'available': int(mem.available / (1024**2)),
                        'used': int(mem.used / (1024**2)),
                        'percent': round(mem.percent, 2)
                    }
                except ImportError:
                    pass
                except Exception as e:
                    logger.warning(f"使用psutil获取内存信息失败: {e}")
        
        except Exception as e:
            logger.error(f"检测内存失败: {e}")
    
    def _detect_gpu(self) -> None:
        """检测GPU信息"""
        try:
            self.gpu_info = {
                'has_gpu': False,
                'gpu_count': 0,
                'gpus': [],
                'cuda_available': False,
                'cuda_version': '',
                'rocm_available': False,
                'mps_available': False,
                'recommended_backend': 'cpu'
            }
            
            # 检测CUDA
            try:
                import torch
                self.gpu_info['cuda_available'] = torch.cuda.is_available()
                if self.gpu_info['cuda_available']:
                    self.gpu_info['cuda_version'] = torch.version.cuda
                    self.gpu_info['gpu_count'] = torch.cuda.device_count()
                    self.gpu_info['has_gpu'] = True
                    
                    for i in range(self.gpu_info['gpu_count']):
                        props = torch.cuda.get_device_properties(i)
                        self.gpu_info['gpus'].append({
                            'id': i,
                            'name': props.name,
                            'total_memory': props.total_memory / (1024**3),  # GB
                            'compute_capability': f"{props.major}.{props.minor}"
                        })
                    
                    self.gpu_info['recommended_backend'] = 'cuda'
                    logger.info(f"检测到CUDA GPU: {self.gpu_info['gpu_count']}个")
            except ImportError:
                pass
            except Exception as e:
                logger.warning(f"检测CUDA失败: {e}")
            
            # 检测ROCm
            if not self.gpu_info['cuda_available']:
                try:
                    import torch
                    self.gpu_info['rocm_available'] = torch.version.hip is not None
                    if self.gpu_info['rocm_available']:
                        self.gpu_info['has_gpu'] = True
                        self.gpu_info['gpu_count'] = torch.cuda.device_count()
                        for i in range(self.gpu_info['gpu_count']):
                            props = torch.cuda.get_device_properties(i)
                            self.gpu_info['gpus'].append({
                                'id': i,
                                'name': props.name,
                                'total_memory': props.total_memory / (1024**3),
                                'compute_capability': f"{props.major}.{props.minor}"
                            })
                        self.gpu_info['recommended_backend'] = 'rocm'
                        logger.info(f"检测到ROCm GPU: {self.gpu_info['gpu_count']}个")
                except Exception as e:
                    logger.warning(f"检测ROCm失败: {e}")
            
            # 检测MPS (Apple Silicon)
            if not self.gpu_info['has_gpu'] and platform.system() == 'Darwin':
                try:
                    import torch
                    self.gpu_info['mps_available'] = torch.backends.mps.is_available()
                    if self.gpu_info['mps_available']:
                        self.gpu_info['has_gpu'] = True
                        self.gpu_info['gpu_count'] = 1
                        self.gpu_info['gpus'].append({
                            'id': 0,
                            'name': 'Apple Silicon GPU',
                            'total_memory': self.memory_info.get('total', 0) / 1024,  # GB
                            'compute_capability': 'N/A'
                        })
                        self.gpu_info['recommended_backend'] = 'mps'
                        logger.info("检测到MPS (Apple Silicon)")
                except ImportError:
                    pass
                except Exception as e:
                    logger.warning(f"检测MPS失败: {e}")
            
            # 使用nvidia-smi作为后备
            if not self.gpu_info['has_gpu']:
                try:
                    result = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader'], 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        lines = result.stdout.strip().split('\n')
                        self.gpu_info['has_gpu'] = True
                        self.gpu_info['gpu_count'] = len(lines)
                        self.gpu_info['recommended_backend'] = 'cuda'
                        
                        for i, line in enumerate(lines):
                            parts = line.split(',')
                            name = parts[0].strip()
                            memory = float(parts[1].split()[0])  # GB
                            self.gpu_info['gpus'].append({
                                'id': i,
                                'name': name,
                                'total_memory': memory,
                                'compute_capability': 'N/A'
                            })
                        logger.info(f"通过nvidia-smi检测到GPU: {self.gpu_info['gpu_count']}个")
                except FileNotFoundError:
                    pass
                except Exception as e:
                    logger.warning(f"使用nvidia-smi检测GPU失败: {e}")
        
        except Exception as e:
            logger.error(f"检测GPU失败: {e}")
    
    def _detect_disk(self) -> None:
        """检测磁盘信息"""
        try:
            self.disk_info = {
                'total': 0,
                'used': 0,
                'free': 0,
                'percent': 0.0
            }
            
            try:
                import psutil
                disk = psutil.disk_usage('/')
                self.disk_info = {
                    'total': int(disk.total / (1024**3)),  # GB
                    'used': int(disk.used / (1024**3)),
                    'free': int(disk.free / (1024**3)),
                    'percent': round(disk.percent, 2)
                }
            except ImportError:
                pass
            except Exception as e:
                logger.warning(f"使用psutil获取磁盘信息失败: {e}")
        
        except Exception as e:
            logger.error(f"检测磁盘失败: {e}")
    
    def get_hardware_info(self) -> Dict[str, Any]:
        """
        获取硬件信息
        
        Returns:
            硬件信息字典
        """
        return {
            'system': self.system_info,
            'cpu': self.cpu_info,
            'memory': self.memory_info,
            'gpu': self.gpu_info,
            'disk': self.disk_info
        }
    
    def get_hardware_profile(self) -> str:
        """
        获取硬件配置级别
        
        Returns:
            配置级别: 'low', 'mid', 'high'
        """
        # GPU优先
        if self.gpu_info['has_gpu']:
            total_gpu_memory = sum(gpu['total_memory'] for gpu in self.gpu_info['gpus'])
            
            if total_gpu_memory >= 16:
                return 'high'
            elif total_gpu_memory >= 8:
                return 'mid'
            else:
                return 'low'
        
        # CPU和内存
        memory_gb = self.memory_info.get('total', 0) / 1024
        cpu_cores = self.cpu_info.get('physical_cores', 0)
        
        if memory_gb >= 32 and cpu_cores >= 8:
            return 'mid'
        elif memory_gb >= 16 and cpu_cores >= 4:
            return 'low'
        else:
            return 'low'
    
    def get_recommended_model(self, task_type: str = 'multimodal') -> str:
        """
        获取推荐的模型
        
        Args:
            task_type: 任务类型
        
        Returns:
            推荐的模型名称
        """
        profile = self.get_hardware_profile()
        backend = self.gpu_info.get('recommended_backend', 'cpu')
        
        # Apple Silicon优先使用mobileclip
        if backend == 'mps':
            return 'apple/mobileclip-vit-large-patch14-336'
        
        # 根据配置级别推荐模型
        if profile == 'high':
            if task_type == 'multimodal':
                return 'vidore/colqwen2.5-v0.2'
            elif task_type == 'text_image':
                return 'vidore/colqwen2.5-v0.2'
            elif task_type == 'text_video':
                return 'vidore/colqwen2.5-v0.2'
            elif task_type == 'text_audio':
                return 'laion/clap-htsat-unfused'
        
        elif profile == 'mid':
            if task_type == 'multimodal':
                return 'vidore/colSmol-500M'
            elif task_type == 'text_image':
                return 'vidore/colSmol-500M'
            elif task_type == 'text_video':
                return 'vidore/colSmol-500M'
            elif task_type == 'text_audio':
                return 'laion/clap-htsat-unfused'
        
        else:  # low
            if task_type == 'multimodal':
                return 'apple/mobileclip-vit-large-patch14-336'
            elif task_type == 'text_image':
                return 'apple/mobileclip-vit-large-patch14-336'
            elif task_type == 'text_video':
                return 'apple/mobileclip-vit-large-patch14-336'
            elif task_type == 'text_audio':
                return 'laion/clap-htsat-unfused'
        
        return 'apple/mobileclip-vit-large-patch14-336'
    
    def get_batch_size(self, model_name: str) -> int:
        """
        获取推荐的批大小
        
        Args:
            model_name: 模型名称
        
        Returns:
            批大小
        """
        profile = self.get_hardware_profile()
        backend = self.gpu_info.get('recommended_backend', 'cpu')
        
        if backend == 'cpu':
            return 1
        
        if profile == 'high':
            if 'colqwen2.5' in model_name:
                return 8
            elif 'colSmol' in model_name:
                return 16
            else:
                return 32
        
        elif profile == 'mid':
            if 'colqwen2.5' in model_name:
                return 4
            elif 'colSmol' in model_name:
                return 8
            else:
                return 16
        
        else:  # low
            if 'colqwen2.5' in model_name:
                return 2
            elif 'colSmol' in model_name:
                return 4
            else:
                return 8
        
        return 4
    
    def get_max_concurrent_embeddings(self) -> int:
        """
        获取最大并发向量化数
        
        Returns:
            最大并发数
        """
        profile = self.get_hardware_profile()
        backend = self.gpu_info.get('recommended_backend', 'cpu')
        
        if backend == 'cpu':
            return 1
        
        if profile == 'high':
            return 4
        elif profile == 'mid':
            return 2
        else:
            return 1
    
    def can_use_model(self, model_name: str) -> bool:
        """
        检查是否可以使用指定模型
        
        Args:
            model_name: 模型名称
        
        Returns:
            是否可以使用
        """
        profile = self.get_hardware_profile()
        
        # 检查模型要求
        if 'colqwen2.5' in model_name:
            # 需要至少16GB GPU内存
            if self.gpu_info['has_gpu']:
                total_gpu_memory = sum(gpu['total_memory'] for gpu in self.gpu_info['gpus'])
                return total_gpu_memory >= 16 or profile == 'high'
            return profile == 'high'
        
        elif 'colSmol' in model_name:
            # 需要至少8GB GPU内存
            if self.gpu_info['has_gpu']:
                total_gpu_memory = sum(gpu['total_memory'] for gpu in self.gpu_info['gpus'])
                return total_gpu_memory >= 8 or profile in ['mid', 'high']
            return profile in ['mid', 'high']
        
        else:
            # mobileclip可以在任何配置上运行
            return True
    
    def get_optimization_suggestions(self) -> List[str]:
        """
        获取优化建议
        
        Returns:
            优化建议列表
        """
        suggestions = []
        
        # 内存建议
        memory_gb = self.memory_info.get('total', 0) / 1024
        if memory_gb < 16:
            suggestions.append("建议增加系统内存到至少16GB以获得更好的性能")
        
        # GPU建议
        if not self.gpu_info['has_gpu']:
            suggestions.append("建议使用支持CUDA的GPU以加速AI推理")
        elif self.gpu_info['recommended_backend'] == 'cuda':
            gpu_memory = sum(gpu['total_memory'] for gpu in self.gpu_info['gpus'])
            if gpu_memory < 8:
                suggestions.append("建议使用显存至少8GB的GPU以支持更大的模型")
        
        # 磁盘建议
        disk_free = self.disk_info.get('free', 0)
        if disk_free < 50:
            suggestions.append("建议确保至少50GB的可用磁盘空间用于存储模型和数据")
        
        return suggestions


def detect_hardware() -> HardwareDetector:
    """
    检测硬件
    
    Returns:
        硬件检测器实例
    """
    return HardwareDetector()


def get_hardware_info() -> Dict[str, Any]:
    """
    获取硬件信息
    
    Returns:
        硬件信息字典
    """
    detector = detect_hardware()
    return detector.get_hardware_info()


def get_hardware_profile() -> str:
    """
    获取硬件配置级别
    
    Returns:
        配置级别
    """
    detector = detect_hardware()
    return detector.get_hardware_profile()


def get_recommended_model(task_type: str = 'multimodal') -> str:
    """
    获取推荐的模型
    
    Args:
        task_type: 任务类型
    
    Returns:
        推荐的模型名称
    """
    detector = detect_hardware()
    return detector.get_recommended_model(task_type)