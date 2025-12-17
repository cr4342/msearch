#!/usr/bin/env python3
"""
硬件分析脚本
用于检测系统硬件配置，为模型选择和优化提供依据
"""

import platform
import psutil
import sys
import json
from pathlib import Path
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class HardwareAnalyzer:
    """硬件分析器类"""
    
    def __init__(self):
        self.hardware_info = {}
    
    def analyze(self):
        """执行完整的硬件分析"""
        logger.info("开始硬件分析...")
        
        # 基本系统信息
        self._analyze_os()
        
        # CPU信息
        self._analyze_cpu()
        
        # 内存信息
        self._analyze_memory()
        
        # GPU信息（如果可用）
        self._analyze_gpu()
        
        # 磁盘信息
        self._analyze_disk()
        
        # 网络信息
        self._analyze_network()
        
        # 推荐配置
        self._generate_recommendations()
        
        logger.info("硬件分析完成")
        return self.hardware_info
    
    def _analyze_os(self):
        """分析操作系统"""
        logger.info("分析操作系统...")
        self.hardware_info['os'] = {
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'architecture': platform.machine(),
            'processor': platform.processor(),
            'python_version': platform.python_version()
        }
    
    def _analyze_cpu(self):
        """分析CPU"""
        logger.info("分析CPU...")
        cpu_info = {
            'physical_cores': psutil.cpu_count(logical=False),
            'total_cores': psutil.cpu_count(logical=True),
            'cpu_frequency': psutil.cpu_freq().max if psutil.cpu_freq() else None,
            'cpu_percent': psutil.cpu_percent(interval=1),
            'cpu_info': {
                'brand': platform.processor()
            }
        }
        
        # 尝试获取更详细的CPU信息
        if platform.system() == "Linux":
            try:
                with open('/proc/cpuinfo', 'r') as f:
                    cpuinfo = f.read()
                    for line in cpuinfo.split('\n'):
                        if line.startswith('model name'):
                            cpu_info['cpu_info']['model_name'] = line.split(':')[1].strip()
                            break
            except Exception as e:
                logger.warning(f"无法获取详细CPU信息: {e}")
        
        self.hardware_info['cpu'] = cpu_info
    
    def _analyze_memory(self):
        """分析内存"""
        logger.info("分析内存...")
        memory = psutil.virtual_memory()
        self.hardware_info['memory'] = {
            'total_gb': round(memory.total / (1024 ** 3), 2),
            'available_gb': round(memory.available / (1024 ** 3), 2),
            'used_percent': memory.percent
        }
    
    def _analyze_gpu(self):
        """分析GPU"""
        logger.info("分析GPU...")
        gpus = []
        
        # 尝试使用torch检测GPU（如果可用）
        try:
            import torch
            has_cuda = torch.cuda.is_available()
            gpu_count = torch.cuda.device_count()
            
            if has_cuda:
                for i in range(gpu_count):
                    gpu = {
                        'name': torch.cuda.get_device_name(i),
                        'memory_gb': round(torch.cuda.get_device_properties(i).total_memory / (1024 ** 3), 2),
                        'compute_capability': torch.cuda.get_device_capability(i)
                    }
                    gpus.append(gpu)
            
            self.hardware_info['cuda_available'] = has_cuda
            self.hardware_info['gpu_count'] = gpu_count
            self.hardware_info['gpus'] = gpus
            
        except ImportError:
            logger.warning("PyTorch未安装，无法检测CUDA GPU")
            self.hardware_info['cuda_available'] = False
            self.hardware_info['gpu_count'] = 0
            self.hardware_info['gpus'] = []
        except Exception as e:
            logger.error(f"GPU检测失败: {e}")
            self.hardware_info['cuda_available'] = False
            self.hardware_info['gpu_count'] = 0
            self.hardware_info['gpus'] = []
    
    def _analyze_disk(self):
        """分析磁盘"""
        logger.info("分析磁盘...")
        disks = []
        
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disk_info = {
                    'device': partition.device,
                    'mountpoint': partition.mountpoint,
                    'file_system_type': partition.fstype,
                    'total_gb': round(usage.total / (1024 ** 3), 2),
                    'used_gb': round(usage.used / (1024 ** 3), 2),
                    'free_gb': round(usage.free / (1024 ** 3), 2),
                    'used_percent': usage.percent
                }
                disks.append(disk_info)
            except PermissionError:
                continue
        
        self.hardware_info['disks'] = disks
        
        # 获取系统根目录的磁盘信息
        try:
            root_usage = psutil.disk_usage('/')
            self.hardware_info['root_disk'] = {
                'total_gb': round(root_usage.total / (1024 ** 3), 2),
                'used_gb': round(root_usage.used / (1024 ** 3), 2),
                'free_gb': round(root_usage.free / (1024 ** 3), 2),
                'used_percent': root_usage.percent
            }
        except Exception as e:
            logger.warning(f"无法获取根目录磁盘信息: {e}")
    
    def _analyze_network(self):
        """分析网络"""
        logger.info("分析网络...")
        try:
            net_if_addrs = psutil.net_if_addrs()
            net_info = {}
            for interface, addresses in net_if_addrs.items():
                net_info[interface] = []
                for addr in addresses:
                    net_info[interface].append({
                        'family': addr.family.name,
                        'address': addr.address,
                        'netmask': addr.netmask,
                        'broadcast': addr.broadcast
                    })
            self.hardware_info['network'] = net_info
        except Exception as e:
            logger.warning(f"无法获取网络信息: {e}")
            self.hardware_info['network'] = {}
    
    def _generate_recommendations(self):
        """根据硬件分析生成推荐配置"""
        logger.info("生成推荐配置...")
        
        recommendations = {
            'model_selection': {},
            'optimization': {},
            'configuration': {}
        }
        
        # 模型选择推荐
        cuda_available = self.hardware_info.get('cuda_available', False)
        gpu_count = self.hardware_info.get('gpu_count', 0)
        memory_gb = self.hardware_info['memory']['total_gb']
        
        # 推荐模型类型
        if cuda_available and gpu_count >= 1:
            gpu_memory = self.hardware_info['gpus'][0]['memory_gb'] if self.hardware_info['gpus'] else 0
            
            if gpu_memory >= 12:
                # 高性能GPU
                recommendations['model_selection'] = {
                    'clip': 'ViT-L/14',
                    'clap': 'htsat-large',
                    'whisper': 'large',
                    'backend': 'cuda'
                }
            elif gpu_memory >= 8:
                # 中等性能GPU
                recommendations['model_selection'] = {
                    'clip': 'ViT-B/32',
                    'clap': 'htsat-fused',
                    'whisper': 'medium',
                    'backend': 'cuda'
                }
            else:
                # 入门级GPU
                recommendations['model_selection'] = {
                    'clip': 'ViT-B/32',
                    'clap': 'htsat-fused',
                    'whisper': 'base',
                    'backend': 'cuda'
                }
        else:
            # CPU模式
            recommendations['model_selection'] = {
                'clip': 'ViT-B/32',
                'clap': 'htsat-fused',
                'whisper': 'base',
                'backend': 'cpu'
            }
        
        # 推荐优化设置
        recommendations['optimization'] = {
            'batch_size': 32 if cuda_available else 8,
            'num_workers': min(self.hardware_info['cpu']['total_cores'], 16),
            'use_half_precision': cuda_available,
            'enable_parallel': cuda_available and gpu_count > 1,
            'cache_strategy': 'disk' if memory_gb > 16 else 'memory'
        }
        
        # 推荐配置设置
        recommendations['configuration'] = {
            'qdrant_memory_limit': min(int(memory_gb * 0.4), 32),
            'embedding_cache_size': min(int(memory_gb * 0.2), 16),
            'max_concurrent_tasks': min(self.hardware_info['cpu']['total_cores'], 8),
            'check_interval': 5
        }
        
        self.hardware_info['recommendations'] = recommendations
    
    def save_to_file(self, output_path: Path):
        """将硬件信息保存到文件"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.hardware_info, f, indent=2, ensure_ascii=False, default=str)
            logger.info(f"硬件信息已保存到: {output_path}")
            return True
        except Exception as e:
            logger.error(f"保存硬件信息失败: {e}")
            return False
    
    def print_summary(self):
        """打印硬件信息摘要"""
        print("=" * 50)
        print("硬件分析摘要")
        print("=" * 50)
        
        # 操作系统
        os_info = self.hardware_info['os']
        print(f"操作系统: {os_info['system']} {os_info['release']} ({os_info['architecture']})")
        print(f"Python版本: {os_info['python_version']}")
        
        # CPU
        cpu_info = self.hardware_info['cpu']
        print(f"CPU: {cpu_info['cpu_info']['brand'] if 'brand' in cpu_info['cpu_info'] else cpu_info['cpu_info']['model_name'] if 'model_name' in cpu_info['cpu_info'] else 'Unknown'}")
        print(f"核心数: {cpu_info['physical_cores']} 物理核心, {cpu_info['total_cores']} 逻辑核心")
        if cpu_info['cpu_frequency']:
            print(f"CPU频率: {round(cpu_info['cpu_frequency'] / 1000, 2)} GHz")
        
        # 内存
        mem_info = self.hardware_info['memory']
        print(f"内存: {mem_info['total_gb']} GB 总内存, {mem_info['used_percent']}% 已使用")
        
        # GPU
        if self.hardware_info['cuda_available']:
            print(f"GPU: {self.hardware_info['gpu_count']} 个CUDA设备")
            for i, gpu in enumerate(self.hardware_info['gpus']):
                print(f"  GPU {i}: {gpu['name']}, {gpu['memory_gb']} GB 显存")
        else:
            print("GPU: 无CUDA设备，使用CPU模式")
        
        # 磁盘
        if 'root_disk' in self.hardware_info:
            root_disk = self.hardware_info['root_disk']
            print(f"磁盘: {root_disk['total_gb']} GB 总空间, {root_disk['used_percent']}% 已使用")
        
        # 推荐配置
        print("\n推荐配置:")
        recs = self.hardware_info['recommendations']
        print(f"  模型选择: CLIP={recs['model_selection']['clip']}, CLAP={recs['model_selection']['clap']}, Whisper={recs['model_selection']['whisper']}")
        print(f"  后端: {recs['model_selection']['backend']}")
        print(f"  批处理大小: {recs['optimization']['batch_size']}")
        print(f"  工作线程数: {recs['optimization']['num_workers']}")
        print(f"  半精度计算: {'启用' if recs['optimization']['use_half_precision'] else '禁用'}")
        
        print("=" * 50)

def main():
    """主函数"""
    # 获取输出路径（可选）
    output_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("./hardware_info.json")
    
    # 执行硬件分析
    analyzer = HardwareAnalyzer()
    hardware_info = analyzer.analyze()
    
    # 打印摘要
    analyzer.print_summary()
    
    # 保存结果
    analyzer.save_to_file(output_path)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())