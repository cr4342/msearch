#!/bin/bash
# 简化版CIFAR-10数据集下载脚本
# 使用网上已标注的AI训练数据集作为参考标准

set -e

echo "=============================================================================="
echo "msearch 标准数据集下载工具（简化版）"
echo "=============================================================================="
echo "使用网上已标注的AI训练数据集作为参考标准"
echo "用于检索相似度可靠性评估"
echo "=============================================================================="

# 检查依赖
echo "检查依赖..."
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到python3"
    exit 1
fi

# 创建目录
echo "创建目录..."
mkdir -p testdata/cifar10
mkdir -p testdata/temp

echo ""
echo "=============================================================================="
echo "数据集选项"
echo "=============================================================================="
echo "推荐: CIFAR-10（小型、标准、易于使用）"
echo "  - 60,000张32x32彩色图像"
echo "  - 10个类别，每类6,000张图像"
echo "  - 大小约170MB"
echo ""
echo "其他可选数据集:"
echo "  - Flickr8k: 8,000张图像，带文本描述（~1GB）"
echo "  - LFW: 人脸识别数据集（~172MB）"
echo "  - ORL Faces: 小型人脸数据集（~4MB）"
echo ""
echo "=============================================================================="

# 尝试使用torchvision下载CIFAR-10
echo ""
echo "尝试使用torchvision下载CIFAR-10..."
echo ""

# 创建Python下载脚本
cat > testdata/temp/download_cifar10.py << 'EOF'
import sys
sys.path.insert(0, 'src')

try:
    import torchvision
    import torchvision.datasets as datasets
    from pathlib import Path
    
    print("正在下载CIFAR10数据集...")
    
    dataset_dir = Path("testdata/cifar10")
    dataset_dir.mkdir(parents=True, exist_ok=True)
    
    # 下载训练集
    print("下载训练集...")
    train_dataset = datasets.CIFAR10(root=str(dataset_dir), train=True, download=True)
    print(f"训练集: {len(train_dataset)} 张图像")
    
    # 下载测试集
    print("下载测试集...")
    test_dataset = datasets.CIFAR10(root=str(dataset_dir), train=False, download=True)
    print(f"测试集: {len(test_dataset)} 张图像")
    
    # 创建标注文件
    print("创建标注文件...")
    cifar_labels = [
        'airplane', 'automobile', 'bird', 'cat', 'deer',
        'dog', 'frog', 'horse', 'ship', 'truck'
    ]
    
    labels_file = dataset_dir / 'ground_truth.txt'
    with open(labels_file, 'w', encoding='utf-8') as f:
        f.write("# CIFAR-10 数据集标注文件\n")
        f.write("# 用于检索相似度评估\n")
        f.write("# 格式: image_index,label,label_name\n")
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
    test_cases_file = dataset_dir / 'search_test_cases.txt'
    with open(test_cases_file, 'w', encoding='utf-8') as f:
        f.write("# CIFAR-10 检索测试用例\n")
        f.write("# 用于评估检索系统的相似度准确性\n")
        f.write("# 格式: query_text,expected_class,expected_image_count\n")
        f.write("#\n")
        
        for label_idx, label_name in enumerate(cifar_labels):
            train_count = sum(1 for _, y in train_dataset if y == label_idx)
            test_count = sum(1 for _, y in test_dataset if y == label_idx)
            total_count = train_count + test_count
            
            f.write(f"# {label_name} 类别的文本检索\n")
            f.write(f"{label_name},{label_idx},{total_count}\n")
    
    print(f"✓ 测试用例文件已创建: {test_cases_file}")
    
    print("\n✓ CIFAR-10数据集下载完成!")
    print(f"  训练集: {len(train_dataset)} 张图像")
    print(f"  测试集: {len(test_dataset)} 张图像")
    print(f"  总计: {len(train_dataset) + len(test_dataset)} 张图像")
    
except ImportError as e:
    print("✗ torchvision未安装")
    print("请运行: pip install torchvision")
    sys.exit(1)
except Exception as e:
    print(f"✗ 下载失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
EOF

# 运行下载脚本
cd testdata/temp
python3 download_cifar10.py

# 检查下载结果
echo ""
echo "=============================================================================="
echo "下载结果检查"
echo "=============================================================================="

if [ -f "../cifar10/ground_truth.txt" ]; then
    echo "✓ 数据集下载成功!"
    echo ""
    echo "文件列表:"
    ls -lh ../cifar10/
    echo ""
    echo "下一步:"
    echo "  1. 查看标注文件: testdata/cifar10/ground_truth.txt"
    echo "  2. 查看测试用例: testdata/cifar10/search_test_cases.txt"
    echo "  3. 对CIFAR-10图像进行向量化处理"
    echo "  4. 使用标注文件验证检索准确性"
    echo ""
    echo "预期评估结果:"
    echo "  - 文本检索（使用类别名称）: Precision@1 ≥ 0.8, Recall@10 ≥ 0.7"
    echo "  - 图像检索: 同类相似度 > 0.8, 不同类相似度 < 0.5"
    echo "  - 自己检索自己: 相似度 = 1.0"
    echo "  - 综合评估: 良好或优秀"
else
    echo "✗ 数据集下载失败"
    echo ""
    echo "请检查:"
    echo "  1. 网络连接是否正常"
    echo "  2. 是否已安装torchvision: pip install torchvision"
    echo "  3. 存储空间是否充足（需要约170MB）"
fi

echo "=============================================================================="

# 清理临时文件
rm -rf testdata/temp

echo "完成!"