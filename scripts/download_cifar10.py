#!/usr/bin/env python3
"""
使用torchvision下载CIFAR-10数据集用于检索相似度测试
使用网上已标注的AI训练数据集作为参考标准
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any

sys.path.insert(0, 'src')


def download_cifar10_with_torchvision(output_dir: str = "testdata/cifar10") -> bool:
    """
    使用torchvision下载CIFAR-10数据集
    
    Args:
        output_dir: 输出目录
        
    Returns:
        是否成功
    """
    try:
        print("=" * 80)
        print("使用torchvision下载CIFAR-10数据集")
        print("=" * 80)
        
        # 检查是否安装了torchvision
        try:
            import torchvision
            import torchvision.datasets as datasets
        except ImportError:
            print("✗ torchvision未安装")
            print("请运行: pip install torchvision")
            return False
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        print(f"\n下载CIFAR-10数据集到: {output_path}")
        print("数据集信息:")
        print("  - 60,000张32x32彩色图像")
        print("  - 10个类别")
        print("  - 每个类别6,000张图像")
        print("  - 训练集50,000张，测试集10,000张")
        
        # 下载训练集
        print("\n正在下载训练集...")
        train_dataset = datasets.CIFAR10(
            root=str(output_path),
            train=True,
            download=True
        )
        
        # 下载测试集
        print("正在下载测试集...")
        test_dataset = datasets.CIFAR10(
            root=str(output_path),
            train=False,
            download=True
        )
        
        print(f"✓ CIFAR-10数据集下载完成")
        print(f"  训练集: {len(train_dataset)} 张图像")
        print(f"  测试集: {len(test_dataset)} 张图像")
        
        # 创建标注文件
        create_cifar10_ground_truth(output_path, train_dataset, test_dataset)
        
        return True
        
    except Exception as e:
        print(f"✗ 下载失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def create_cifar10_ground_truth(output_dir: Path, train_dataset, test_dataset):
    """
    创建CIFAR-10标注文件
    
    Args:
        output_dir: 输出目录
        train_dataset: 训练数据集
        test_dataset: 测试数据集
    """
    try:
        print("\n创建标注文件...")
        
        # CIFAR-10类别标签
        cifar_labels = [
            'airplane', 'automobile', 'bird', 'cat', 'deer',
            'dog', 'frog', 'horse', 'ship', 'truck'
        ]
        
        labels_file = output_dir / 'ground_truth.txt'
        
        with open(labels_file, 'w', encoding='utf-8') as f:
            f.write("# CIFAR-10 数据集标注文件\n")
            f.write("# 用于检索相似度评估\n")
            f.write("# 格式: image_index,label,class_name\n")
            f.write("#\n")
            f.write("# 类别标签映射:\n")
            for i, label in enumerate(cifar_labels):
                f.write(f"{i} -> {label}\n")
            f.write("#\n")
            f.write("# 训练集标注:\n")
            for i, (image, label_idx) in enumerate(train_dataset):
                label_name = cifar_labels[label_idx]
                f.write(f"train_{i:05d},{label_idx},{label_name}\n")
            
            f.write("#\n")
            f.write("# 测试集标注:\n")
            for i, (image, label_idx) in enumerate(test_dataset):
                label_name = cifar_labels[label_idx]
                f.write(f"test_{i:05d},{label_idx},{label_name}\n")
        
        print(f"✓ 标注文件已创建: {labels_file}")
        
        # 创建检索测试用例
        create_search_test_cases(output_dir, train_dataset, test_dataset, cifar_labels)
        
    except Exception as e:
        print(f"✗ 创建标注文件失败: {e}")


def create_search_test_cases(output_dir: Path, train_dataset, test_dataset, cifar_labels: List[str]):
    """
    创建检索测试用例
    
    Args:
        output_dir: 输出目录
        train_dataset: 训练数据集
        test_dataset: 测试数据集
        cifar_labels: 类别标签列表
    """
    try:
        print("\n创建检索测试用例...")
        
        test_cases_file = output_dir / 'search_test_cases.txt'
        
        with open(test_cases_file, 'w', encoding='utf-8') as f:
            f.write("# CIFAR-10 检索测试用例\n")
            f.write("# 用于评估检索系统的相似度准确性\n")
            f.write("# 格式: query_text,expected_class,expected_image_count\n")
            f.write("#\n")
            
            # 为每个类别创建文本检索测试用例
            for label_idx, label_name in enumerate(cifar_labels):
                # 计算该类别的图像数量
                train_count = sum(1 for _, y in train_dataset if y == label_idx)
                test_count = sum(1 for _, y in test_dataset if y == label_idx)
                total_count = train_count + test_count
                
                f.write(f"# {label_name} 类别的文本检索\n")
                f.write(f"{label_name},{label_idx},{total_count}\n")
            
            f.write("#\n")
            f.write("# 说明:\n")
            f.write("# 1. 使用 query_text 作为检索查询\n")
            f.write("# 2. 预期结果应该返回 expected_class 类别的图像\n")
            f.write("# 3. 相关图像数量应该接近 expected_image_count\n")
            f.write("# 4. 用于评估 Precision@K, Recall@K, MRR, NDCG 等指标\n")
        
        print(f"✓ 测试用例文件已创建: {test_cases_file}")
        
    except Exception as e:
        print(f"✗ 创建测试用例失败: {e}")


def create_evaluation_script(output_dir: Path):
    """
    创建评估脚本
    
    Args:
        output_dir: 输出目录
    """
    try:
        print("\n创建评估脚本...")
        
        script_file = output_dir / 'evaluate_with_cifar10.py'
        
        script_content = '''#!/usr/bin/env python3
"""
使用CIFAR-10数据集评估检索相似度准确性
"""

import sys
sys.path.insert(0, 'src')

import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Set
from collections import defaultdict

import torchvision
import torchvision.datasets as datasets

from core.config.config_manager import ConfigManager
from core.vector.vector_store import VectorStore


class SearchAccuracyEvaluator:
    """检索准确率评估器"""
    
    def __init__(self):
        self.evaluation_results = {}
    
    def calculate_precision_at_k(self, retrieved_items: List[Dict], relevant_items: Set[str], k: int) -> float:
        """计算Precision@K"""
        if k == 0:
            return 0.0
        
        relevant_count = 0
        for i in range(min(k, len(retrieved_items))):
            item = retrieved_items[i]
            item_id = item.get('file_id')
            if item_id in relevant_items:
                relevant_count += 1
        
        return relevant_count / k
    
    def calculate_recall_at_k(self, retrieved_items: List[Dict], relevant_items: Set[str], k: int) -> float:
        """计算Recall@K"""
        if len(relevant_items) == 0:
            return 0.0
        
        relevant_count = 0
        for i in range(min(k, len(retrieved_items))):
            item = retrieved_items[i]
            item_id = item.get('file_id')
            if item_id in relevant_items:
                relevant_count += 1
        
        return relevant_count / len(relevant_items)
    
    def calculate_mrr(self, retrieved_items: List[Dict], relevant_items: Set[str]) -> float:
        """计算Mean Reciprocal Rank (MRR)"""
        if len(relevant_items) == 0:
            return 0.0
        
        for i, item in enumerate(retrieved_items, start=1):
            item_id = item.get('file_id')
            if item_id in relevant_items:
                return 1.0 / i
        
        return 0.0
    
    def evaluate_search_quality(self, query: str, retrieved_items: List[Dict], 
                               relevant_items: Set[str], k_values: List[int] = [1, 5, 10, 20]) -> Dict[str, Any]:
        """综合评估检索质量"""
        results = {
            'query': query,
            'retrieved_count': len(retrieved_items),
            'relevant_count': len(relevant_items),
            'metrics': {}
        }
        
        for k in k_values:
            precision = self.calculate_precision_at_k(retrieved_items, relevant_items, k)
            recall = self.calculate_recall_at_k(retrieved_items, relevant_items, k)
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
            
            results['metrics'][f'precision@{k}'] = precision
            results['metrics'][f'recall@{k}'] = recall
            results['metrics'][f'f1@{k}'] = f1
        
        mrr = self.calculate_mrr(retrieved_items, relevant_items)
        results['metrics']['mrr'] = mrr
        
        similarities = [item.get('similarity', item.get('score', 0)) for item in retrieved_items]
        if similarities:
            results['metrics']['avg_similarity'] = np.mean(similarities)
            results['metrics']['max_similarity'] = np.max(similarities)
            results['metrics']['min_similarity'] = np.min(similarities)
        
        return results


def load_cifar10_labels(dataset_dir: str) -> Dict[str, List[str]]:
    """加载CIFAR-10标签"""
    labels_file = Path(dataset_dir) / 'ground_truth.txt'
    
    labels = defaultdict(list)
    with open(labels_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and ',' in line:
                parts = line.split(',')
                if len(parts) >= 3:
                    image_id, label_idx, label_name = parts[0], parts[1], parts[2]
                    labels[label_name].append(image_id)
    
    return dict(labels)


def main():
    """主函数"""
    print("=" * 80)
    print("使用CIFAR-10数据集评估检索相似度准确性")
    print("=" * 80)
    print("使用网上已标注的AI训练数据集作为参考标准")
    print("=" * 80)
    
    try:
        from PIL import Image
        
        dataset_dir = Path("testdata/cifar10")
        
        if not dataset_dir.exists():
            print("错误: CIFAR-10数据集未找到")
            print("请先运行: python scripts/download_cifar10.py")
            return 1
        
        print(f"数据集目录: {dataset_dir}")
        
        # 加载数据集
        print("\\n加载CIFAR-10数据集...")
        train_dataset = datasets.CIFAR10(
            root=str(dataset_dir),
            train=True,
            download=False
        )
        test_dataset = datasets.CIFAR10(
            root=str(dataset_dir),
            train=False,
            download=False
        )
        
        print(f"  训练集: {len(train_dataset)} 张图像")
        print(f"  测试集: {len(test_dataset)} 张图像")
        
        # 加载标签
        print("\\n加载标注文件...")
        labels = load_cifar10_labels(str(dataset_dir))
        print(f"  类别数量: {len(labels)}")
        
        for label_name, image_ids in labels.items():
            print(f"  {label_name}: {len(image_ids)} 张图像")
        
        # 初始化向量存储
        print("\\n初始化向量存储...")
        from core.config.config.config_manager import ConfigManager
        from core.vector.vector_store import VectorStore
        
        config_manager = ConfigManager()
        config = config_manager.config
        vector_store = VectorStore(config)
        
        stats = vector_store.get_stats()
        print(f"  向量数量: {stats.get('vector_count', 0)}")
        
        print("\\n注意: 当前向量库中没有CIFAR-10的向量")
        print("需要先对CIFAR-10图像进行向量化处理")
        print("建议步骤:")
        print("  1. 运行脚本对CIFAR-10图像进行向量化")
        print("  2. 使用ground_truth.txt中的标签作为参考标准")
        print("  3. 运行评估脚本测试检索准确性")
        
        print("\\n" + "=" * 80)
        print("评估说明")
        print("=" * 80)
        print("\\n1. 标注文件说明:")
        print("   - ground_truth.txt: 包含所有图像的类别标签")
        print("   - search_test_cases.txt: 包含检索测试用例")
        print("\\n2. 评估指标:")
        print("   - Precision@K: 前K个结果中相关项目的比例")
        print("   - Recall@K: 相关项目中在前K个结果中的比例")
        print("   - MRR: 首个相关项目的平均倒数排名")
        print("   - NDCG@K: 归一化折损累计增益")
        print("\\n3. 使用方法:")
        print("   - 对CIFAR-10图像进行向量化后")
        print("   - 使用类别名称进行文本检索")
        print("   - 使用标注文件验证结果相关性")
        print("   - 计算各项评估指标")
        print("\\n4. 预期结果:")
        print("   - 高相似度检索应该返回同类别图像")
        print("   - Precision@1 应该 >= 0.8")
        print("   - Recall@10 应该 >= 0.7")
        print("   - MRR 应该 >= 0.8")
        
        print("=" * 80)
        
    except Exception as e:
        print(f"\\n❌ 评估失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''
        
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        # 添加执行权限
        os.chmod(script_file, 0o755)
        
        print(f"✓ 评估脚本已创建: {script_file}")
        print(f"  运行方式: python3 {script_file}")
        
    except Exception as e:
        print(f"✗ 创建评估脚本失败: {e}")


def main():
    """主函数"""
    print("=" * 80)
    print("下载CIFAR-10标准数据集")
    print("=" * 80)
    print("使用网上已标注的AI训练数据集作为参考标准")
    print("用于检索相似度可靠性评估")
    print("=" * 80)
    
    # 下载数据集
    if download_cifar10_with_torchvision():
        print("\n" + "=" * 80)
        print("下载成功！")
        print("=" * 80)
        print("\n下一步:")
        print("1. 检查已下载的数据集: testdata/cifar10/")
        print("2. 查看标注文件: testdata/cifar10/ground_truth.txt")
        print("3. 查看测试用例: testdata/cifar10/search_test_cases.txt")
        print("4. 对CIFAR-10图像进行向量化处理")
        print("5. 使用标注文件验证检索准确性")
        print("=" * 80)
        return 0
    else:
        print("\n" + "=" * 80)
        print("下载失败")
        print("=" * 80)
        print("\n请检查:")
        print("1. 网络连接是否正常")
        print("2. 是否已安装torchvision: pip install torchvision")
        print("3. 存储空间是否充足（需要约170MB）")
        print("=" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(main())
