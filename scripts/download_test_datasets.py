#!/usr/bin/env python3
"""
下载标准测试数据集用于检索相似度评估
使用网上已标注的AI训练数据集作为参考标准
"""

import os
import sys
import tarfile
import zipfile
from pathlib import Path
from typing import List, Dict, Any
import requests
from tqdm import tqdm

sys.path.insert(0, 'src')


class DatasetDownloader:
    """数据集下载器"""
    
    def __init__(self, base_dir: str = "testdata"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        self.datasets = {
            'cifar10': {
                'name': 'CIFAR-10',
                'description': '60,000张32x32彩色图像，10个类别',
                'download_url': 'https://www.cs.toronto.edu/~kriz/cifar-10-python.tar.gz',
                'extract_dir': 'cifar10',
                'expected_files': ['cifar-10-batches-py/data_batch_1', 'cifar-10-batches-py/batches.meta'],
                'size': '163MB'
            },
            'lfw': {
                'name': 'LFW Faces',
                'description': '标记人脸数据库，用于人脸识别测试',
                'download_url': 'http://vis-www.cs.umass.edu/lfw/lfw.tgz',
                'extract_dir': 'lfw',
                'expected_files': ['lfw'],
                'size': '172MB'
            },
            'orl_faces': {
                'name': 'ORL Faces',
                'description': '400张人脸图像，40人，每人10张',
                'download_url': 'https://github.com/dingzhiping1/ORL-Dataset-Face-Recognition/raw/master/ORL.npz',
                'extract_dir': 'orl_faces',
                'expected_files': ['ORL.npz'],
                'size': '4MB'
            }
        }
    
    def download_file(self, url: str, destination: str, chunk_size: int = 8192) -> bool:
        """
        下载文件
        
        Args:
            url: 下载URL
            destination: 目标路径
            chunk_size: 块大小
            
        Returns:
            是否成功
        """
        try:
            print(f"正在下载: {url}")
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            with open(destination, 'wb') as f:
                with tqdm(total=total_size, unit='B', unit_scale=True, desc="下载中") as pbar:
                    for chunk in response.iter_content(chunk_size=chunk_size):
                        if chunk:
                            f.write(chunk)
                            pbar.update(len(chunk))
            
            print(f"✓ 下载完成: {destination}")
            return True
            
        except Exception as e:
            print(f"✗ 下载失败: {e}")
            return False
    
    def extract_tar_gz(self, archive_path: str, extract_to: str) -> bool:
        """
        解压tar.gz文件
        
        Args:
            archive_path: 压缩文件路径
            extract_to: 解压目标目录
            
        Returns:
            是否成功
        """
        try:
            print(f"正在解压: {archive_path}")
            with tarfile.open(archive_path, 'r:gz') as tar:
                tar.extractall(path=extract_to)
            print(f"✓ 解压完成: {extract_to}")
            return True
        except Exception as e:
            print(f"✗ 解压失败: {e}")
            return False
    
    def extract_tgz(self, archive_path: str, extract_to: str) -> bool:
        """
        解压tgz文件
        
        Args:
            archive_path: 压缩文件路径
            extract_to: 解压目标目录
            
        Returns:
            是否成功
        """
        return self.extract_tar_gz(archive_path, extract_to)
    
    def download_dataset(self, dataset_key: str) -> bool:
        """
        下载数据集
        
        Args:
            dataset_key: 数据集键名
            
        Returns:
            是否成功
        """
        if dataset_key not in self.datasets:
            print(f"✗ 未知数据集: {dataset_key}")
            return False
        
        dataset = self.datasets[dataset_key]
        print("\n" + "=" * 80)
        print(f"数据集: {dataset['name']}")
        print(f"描述: {dataset['description']}")
        print(f"大小: {dataset['size']}")
        print("=" * 80)
        
        # 创建临时目录
        temp_dir = self.base_dir / 'temp'
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # 下载文件
        filename = os.path.basename(dataset['download_url'])
        archive_path = temp_dir / filename
        
        if not self.download_file(dataset['download_url'], str(archive_path)):
            return False
        
        # 解压文件
        extract_dir = self.base_dir / dataset['extract_dir']
        extract_dir.mkdir(parents=True, exist_ok=True)
        
        if filename.endswith('.tar.gz') or filename.endswith('.tgz'):
            if not self.extract_tar_gz(str(archive_path), str(extract_dir)):
                return False
        elif filename.endswith('.zip'):
            try:
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
                print(f"✓ 解压完成: {extract_dir}")
            except Exception as e:
                print(f"✗ 解压失败: {e}")
                return False
        else:
            # 直接移动文件
            import shutil
            shutil.move(str(archive_path), str(extract_dir / filename))
            print(f"✓ 文件已保存: {extract_dir / filename}")
        
        # 验证下载
        print(f"\n验证数据集...")
        all_exist = True
        for expected_file in dataset['expected_files']:
            expected_path = extract_dir / expected_file
            if expected_path.exists():
                print(f"  ✓ {expected_file}")
            else:
                print(f"  ✗ {expected_file} (未找到)")
                all_exist = False
        
        # 清理临时文件
        try:
            archive_path.unlink()
            print(f"✓ 清理临时文件")
        except:
            pass
        
        return all_exist
    
    def download_all_datasets(self, datasets: List[str] = None) -> Dict[str, bool]:
        """
        下载所有数据集
        
        Args:
            datasets: 数据集键名列表，None表示全部
            
        Returns:
            下载结果字典
        """
        if datasets is None:
            datasets = list(self.datasets.keys())
        
        results = {}
        for dataset_key in datasets:
            results[dataset_key] = self.download_dataset(dataset_key)
        
        return results


def create_ground_truth_labels(dataset_dir: Path, dataset_name: str) -> bool:
    """
    创建标注文件
    
    Args:
        dataset_dir: 数据集目录
        dataset_name: 数据集名称
        
    Returns:
        是否成功
    """
    try:
        print(f"\n创建标注文件: {dataset_name}")
        
        if dataset_name == 'cifar10':
            # CIFAR-10标签
            labels_file = dataset_dir / 'ground_truth.txt'
            cifar_labels = [
                'airplane', 'automobile', 'bird', 'cat', 'deer',
                'dog', 'frog', 'horse', 'ship', 'truck'
            ]
            
            with open(labels_file, 'w', encoding='utf-8') as f:
                f.write("# CIFAR-10 类别标签\n")
                f.write("# 格式: image_id,label\n")
                f.write("# 用于文本检索相似度测试\n\n")
                
                # 假设数据集已经解压，这里创建示例标注
                # 实际使用时需要根据实际的图像文件创建
                f.write("# 示例标注（需要根据实际图像文件更新）:\n")
                for i, label in enumerate(cifar_labels):
                    f.write(f"example_{i}.jpg,{label}\n")
            
            print(f"✓ 标注文件已创建: {labels_file}")
            
        elif dataset_name == 'lfw':
            # LFW人脸标签
            labels_file = dataset_dir / 'ground_truth.txt'
            
            with open(labels_file, 'w', encoding='utf-8') as f:
                f.write("# LFW 人脸标签\n")
                f.write("# 格式: image_id,person_id\n")
                f.write("# 用于人脸检索相似度测试\n\n")
                f.write("# 示例标注（需要根据实际图像文件更新）:\n")
                f.write("lfw_person_1.jpg,person_1\n")
                f.write("lfw_person_1_2.jpg,person_1\n")
            
            print(f"✓ 标注文件已创建: {labels_file}")
            
        elif dataset_name == 'orl_faces':
            # ORL人脸标签
            labels_file = dataset_dir / 'ground_truth.txt'
            
            with open(labels_file, 'w', encoding='utf-8') as f:
                f.write("# ORL Faces 人脸标签\n")
                f.write("# 格式: image_id,person_id\n")
                f.write("# 用于人脸检索相似度测试\n\n")
                f.write("# 示例标注（需要根据实际图像文件更新）:\n")
                for i in range(40):
                    for j in range(10):
                        f.write(f"orl_s{i+1}_{j+1}.jpg,s{i+1}\n")
            
            print(f"✓ 标注文件已创建: {labels_file}")
        
        return True
        
    except Exception as e:
        print(f"✗ 创建标注文件失败: {e}")
        return False


def main():
    """主函数"""
    print("=" * 80)
    print("msearch 标准测试数据集下载工具")
    print("=" * 80)
    print("使用网上已标注的AI训练数据集作为参考标准")
    print("用于检索相似度可靠性评估")
    print("=" * 80)
    
    downloader = DatasetDownloader()
    
    # 显示可用数据集
    print("\n可用数据集:")
    for key, dataset in downloader.datasets.items():
        print(f"  [{key}] {dataset['name']} - {dataset['description']} ({dataset['size']})")
    
    # 下载数据集
    print("\n" + "=" * 80)
    print("开始下载数据集")
    print("=" * 80)
    
    # 下载CIFAR-10（推荐，小型且标准）
    print("\n推荐下载CIFAR-10数据集...")
    results = downloader.download_all_datasets(['cifar10'])
    
    # 如果CIFAR-10下载成功，创建标注文件
    if results.get('cifar10', False):
        cifar10_dir = downloader.base_dir / 'cifar10'
        create_ground_truth_labels(cifar10_dir, 'cifar10')
    
    # 可选：下载其他数据集
    print("\n可选数据集（需要较大存储空间）:")
    print("  - LFW: 人脸识别数据集（172MB）")
    print("  - ORL Faces: 小型人脸数据集（4MB）")
    
    # 总结
    print("\n" + "=" * 80)
    print("下载总结")
    print("=" * 80)
    
    success_count = sum(1 for result in results.values() if result)
    total_count = len(results)
    
    print(f"成功: {success_count}/{total_count}")
    
    for dataset_key, success in results.items():
        dataset = downloader.datasets[dataset_key]
        status = "✓ 成功" if success else "✗ 失败"
        print(f"  {status}: {dataset['name']}")
    
    if success_count > 0:
        print("\n下一步:")
        print("  1. 检查已下载的数据集在 testdata/ 目录中")
        print("  2. 根据实际的图像文件更新 ground_truth.txt 标注文件")
        print("  3. 运行检索准确率测试，使用标注文件作为参考标准")
        print("  4. 验证检索系统在不同数据集上的表现")
    else:
        print("\n所有数据集下载失败，请检查网络连接或手动下载")
    
    print("=" * 80)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n用户取消下载")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
