#!/usr/bin/env python3
"""
MSearch 模型下载工具
仅用于下载模型，不包含其他安装步骤
"""

import os
import sys
import time
import hashlib
import shutil
from pathlib import Path
from huggingface_hub import snapshot_download, hf_hub_url, hf_hub_download

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 设置日志函数
def log(message, level="INFO"):
    """打印日志消息"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] [{level}] {message}"
    print(log_message)
    
    # 写入日志文件
    logs_dir = Path(__file__).parent.parent / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_file = logs_dir / f"download_models_{time.strftime('%Y%m%d_%H%M%S')}.log"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(log_message + "\n")

def log_info(message):
    """打印信息日志"""
    log(message, "INFO")

def log_success(message):
    """打印成功日志"""
    log(message, "SUCCESS")

def log_warning(message):
    """打印警告日志"""
    log(message, "WARNING")

def log_error(message):
    """打印错误日志"""
    log(message, "ERROR")

def calculate_file_hash(file_path, block_size=65536):
    """计算文件哈希值用于验证完整性"""
    hash_algo = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for block in iter(lambda: f.read(block_size), b''):
            hash_algo.update(block)
    return hash_algo.hexdigest()

def verify_model_integrity(model_path):
    """验证模型完整性"""
    log_info(f"验证模型完整性: {model_path}")
    required_files = [
        "config.json",
        "pytorch_model.bin"  # CLIP和CLAP模型
    ]
    
    # 检查Whisper模型的特殊情况
    if "whisper" in str(model_path).lower():
        required_files = [
            "config.json",
            "model.bin"  # Whisper模型使用不同的文件名
        ]
    
    # 检查必要文件是否存在
    for file_name in required_files:
        file_path = os.path.join(model_path, file_name)
        if not os.path.exists(file_path):
            log_error(f"缺少必要文件: {file_name}")
            return False
        
        # 检查文件大小
        file_size = os.path.getsize(file_path)
        if file_size < 1024 * 1024:  # 至少1MB
            log_error(f"文件过小: {file_name} ({file_size} bytes)")
            return False
    
    log_success(f"模型完整性验证通过: {model_path}")
    return True

def install_dependencies():
    """安装必要的依赖，根据GPU可用性选择PyTorch版本"""
    log_info("\n安装必要的依赖...")
    
    import subprocess
    
    # 检测GPU可用性
    gpu_available = False
    try:
        # 先安装一个轻量级的torch版本来检测GPU
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "torch", "--index-url", "https://download.pytorch.org/whl/cpu", "--no-cache-dir"],
            capture_output=True, 
            text=True
        )
        
        # 检测GPU
        import torch
        gpu_available = torch.cuda.is_available()
        if gpu_available:
            log_info(f"检测到GPU: {torch.cuda.get_device_name(0)}")
        else:
            log_info("未检测到GPU，将使用CPU版本的PyTorch")
        
        # 卸载临时PyTorch
        subprocess.run(
            [sys.executable, "-m", "pip", "uninstall", "-y", "torch"],
            capture_output=True, 
            text=True
        )
    except Exception as e:
        log_warning(f"GPU检测失败: {e}，将使用CPU版本的PyTorch")
    
    # 构建安装命令
    commands = [
        # 首先卸载可能存在的PyTorch，避免版本冲突
        [sys.executable, "-m", "pip", "uninstall", "-y", "torch", "torchvision"]
    ]
    
    # 根据GPU可用性选择PyTorch版本
    if gpu_available:
        commands.append([
            sys.executable, "-m", "pip", "install", "torch", "torchvision", 
            "-i", "https://pypi.tuna.tsinghua.edu.cn/simple", 
            "--extra-index-url", "https://download.pytorch.org/whl/cu121"
        ])
        log_info("将安装GPU版本的PyTorch和torchvision")
    else:
        commands.append([
            sys.executable, "-m", "pip", "install", "torch", "torchvision", 
            "-i", "https://pypi.tuna.tsinghua.edu.cn/simple", 
            "--extra-index-url", "https://download.pytorch.org/whl/cpu"
        ])
        log_info("将安装CPU版本的PyTorch和torchvision")
    
    # 添加其他依赖安装命令
    commands.extend([
        # 安装其他必要依赖
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "-i", "https://pypi.tuna.tsinghua.edu.cn/simple"],
        # 安装缺失的依赖
        [sys.executable, "-m", "pip", "install", "opencv-python", "watchdog", "-i", "https://pypi.tuna.tsinghua.edu.cn/simple"]
    ])
    
    for cmd in commands:
        try:
            log_info(f"执行命令: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path(__file__).parent.parent)
            if result.returncode == 0:
                log_success(f"命令执行成功: {' '.join(cmd)}")
                if result.stdout:
                    log_info(f"输出: {result.stdout[:200]}...")
            else:
                log_error(f"命令执行失败: {' '.join(cmd)}")
                log_error(f"错误信息: {result.stderr}")
                
                # 如果是GPU版本安装失败，尝试安装CPU版本
                if "cu121" in ' '.join(cmd):
                    log_info("GPU版本安装失败，尝试安装CPU版本...")
                    cpu_cmd = cmd.copy()
                    cpu_cmd[-1] = "https://download.pytorch.org/whl/cpu"
                    cpu_result = subprocess.run(cpu_cmd, capture_output=True, text=True, cwd=Path(__file__).parent.parent)
                    if cpu_result.returncode == 0:
                        log_success(f"CPU版本安装成功: {' '.join(cpu_cmd)}")
                    else:
                        log_error(f"CPU版本安装也失败: {' '.join(cpu_cmd)}")
        except Exception as e:
            log_error(f"执行命令时发生异常: {e}")

def download_model(repo_id, local_path, max_retries=3):
    """下载单个模型"""
    log_info(f"\n开始下载模型: {repo_id} 到 {local_path}")
    
    # 确保目录存在
    os.makedirs(local_path, exist_ok=True)
    
    # 设置环境变量
    os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
    os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
    
    # 跳过SSL证书验证（解决企业环境问题）
    import ssl
    ssl._create_default_https_context = ssl._create_unverified_context
    
    # 直接使用requests库下载模型文件
    import requests
    
    # 初始化下载成功的文件计数
    successful_files = 0
    total_files = 0
    
    # 模型文件列表
    model_files = [
        "config.json",
        "pytorch_model.bin",  # CLIP和CLAP模型
        "model.bin",  # Whisper模型
        "preprocessor_config.json",
        "tokenizer_config.json",
        "vocab.json",
        "merges.txt",
        "special_tokens_map.json"
    ]
    
    # 根据模型类型调整文件列表
    if "whisper" in str(local_path).lower():
        model_files.remove("pytorch_model.bin")
    else:
        model_files.remove("model.bin")
    
    total_files = len(model_files)
    log_info(f"模型需要下载 {total_files} 个文件")
    
    success = False
    for attempt in range(max_retries):
        log_info(f"下载尝试 {attempt + 1}/{max_retries}")
        successful_files = 0
        
        # 逐个文件下载
        for file_name in model_files:
            try:
                # 构建下载URL
                base_url = os.environ.get("HF_ENDPOINT", "https://hf-mirror.com")
                file_url = f"{base_url}/{repo_id}/resolve/main/{file_name}"
                
                log_info(f"下载文件: {file_name} 从 {file_url}")
                
                # 设置超时
                timeout = 120  # 增加超时时间到120秒
                
                # 发送GET请求
                log_info(f"发送GET请求，超时时间: {timeout}秒")
                response = requests.get(file_url, verify=False, timeout=timeout, stream=True)
                response.raise_for_status()
                
                # 获取文件大小
                file_size = int(response.headers.get("Content-Length", 0))
                log_info(f"文件大小: {file_size / (1024 * 1024):.2f} MB")
                
                # 保存文件
                file_path = os.path.join(local_path, file_name)
                downloaded_size = 0
                
                log_info(f"开始保存文件到: {file_path}")
                with open(file_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        # 打印进度
                        if file_size > 0:
                            progress = (downloaded_size / file_size) * 100
                            if int(progress) % 20 == 0:  # 每20%打印一次进度
                                log_info(f"下载进度: {progress:.1f}%")
                
                # 检查文件大小
                saved_size = os.path.getsize(file_path)
                if saved_size == file_size:
                    log_success(f"文件 {file_name} 下载成功，大小: {saved_size / (1024 * 1024):.2f} MB")
                    successful_files += 1
                else:
                    log_error(f"文件 {file_name} 下载不完整，预期大小: {file_size}字节，实际大小: {saved_size}字节")
                
            except requests.exceptions.Timeout as e:
                log_error(f"文件 {file_name} 下载超时: {e}")
                # 超时错误，不继续下载其他文件，直接重试
                break
            except requests.exceptions.RequestException as e:
                log_error(f"文件 {file_name} 下载请求失败: {e}")
                # 跳过当前文件，继续下载其他文件
                continue
            except Exception as e:
                log_error(f"处理文件 {file_name} 时出错: {e}")
                import traceback
                log_error(f"错误堆栈: {traceback.format_exc()}")
                continue
        
        log_info(f"本轮下载完成，成功下载 {successful_files}/{total_files} 个文件")
        
        # 验证模型完整性
        if verify_model_integrity(local_path):
            log_success(f"模型 {repo_id} 下载成功")
            success = True
            break
        else:
            log_warning(f"模型 {repo_id} 完整性验证失败，{10}秒后重试...")
            time.sleep(10)
    
    if not success:
        log_error(f"模型 {repo_id} 多次尝试后仍然失败")
    
    return success

def create_model_symlinks(models_dir):
    """创建模型符号链接或复制目录"""
    log_info("\n创建模型目录映射...")
    
    # 模型目录映射（简化名称 -> 完整名称）
    model_dir_mapping = { 
        "clip": "clip-vit-base-patch32", 
        "clap": "clap-htsat-fused", 
        "whisper": "whisper-base", 
        "facenet": "facenet-pytorch" 
    }
    
    # 确保模型目录结构正确
    for simple_name, full_name in model_dir_mapping.items():
        source_dir = os.path.join(models_dir, full_name)
        target_dir = os.path.join(models_dir, simple_name)
        
        if os.path.exists(source_dir):
            file_count = len([f for f in os.listdir(source_dir) if os.path.isfile(os.path.join(source_dir, f))])
            log_info(f"模型目录 {source_dir} 包含 {file_count} 个文件")
            
            # 如果目标目录不存在，创建符号链接或复制
            if not os.path.exists(target_dir):
                log_info(f"创建从 {source_dir} 到 {target_dir} 的目录...")
                try:
                    # 尝试创建符号链接
                    os.symlink(source_dir, target_dir, target_is_directory=True)
                    log_success(f"成功创建符号链接: {target_dir} -> {source_dir}")
                except Exception as e:
                    log_warning(f"创建符号链接失败: {e}")
                    log_info(f"尝试复制目录...")
                    try:
                        shutil.copytree(source_dir, target_dir)
                        log_success(f"成功复制目录: {target_dir}")
                    except Exception as e2:
                        log_error(f"复制目录失败: {e2}")
        else:
            log_warning(f"模型目录 {source_dir} 不存在，可能下载不完整")

def main():
    """主函数"""
    # 获取项目根目录
    project_root = Path(__file__).parent.parent
    models_dir = project_root / "data" / "models"
    
    log_info("===============================================")
    log_info("        MSearch 模型下载工具")
    log_info("===============================================")
    log_info(f"项目根目录: {project_root}")
    log_info(f"模型存储目录: {models_dir}")
    log_info("使用镜像源: https://hf-mirror.com")
    log_info("===============================================")
    
    # 确保模型目录存在
    models_dir.mkdir(parents=True, exist_ok=True)
    
    # 安装依赖
    install_dependencies()
    
    # 模型列表
    models = [
        {
            "name": "clap",
            "repo_id": "laion/clap-htsat-fused",
            "local_path": models_dir / "clap-htsat-fused",
            "model_type": "clap"
        }
    ]
    
    # 下载每个模型
    success_count = 0
    total_count = len(models)
    
    for i, model_info in enumerate(models, 1):
        log_info(f"\n[{i}/{total_count}] 处理模型: {model_info['name']}")
        
        # 检查模型是否已存在且完整
        if model_info['local_path'].exists():
            if verify_model_integrity(model_info['local_path']):
                log_success(f"模型已存在且完整，跳过下载")
                success_count += 1
                continue
            else:
                log_warning(f"模型存在但不完整，重新下载")
                # 删除不完整的模型
                shutil.rmtree(model_info['local_path'])
                model_info['local_path'].mkdir(parents=True, exist_ok=True)
        
        # 下载模型
        if download_model(
            model_info['repo_id'],
            model_info['local_path']
        ):
            success_count += 1
    
    # 创建模型符号链接
    create_model_symlinks(models_dir)
    
    # 下载完成
    log_info("\n===============================================")
    log_info(f"模型下载完成: {success_count}/{total_count} 成功")
    log_info("===============================================")
    
    if success_count > 0:
        log_success("至少有部分模型下载成功")
        return 0
    else:
        log_error("所有模型下载失败")
        log_info("建议:")
        log_info("   1. 检查网络连接")
        log_info("   2. 确保有足够的磁盘空间")
        log_info("   3. 手动下载模型并放到指定目录")
        log_info(f"   4. 模型目录: {models_dir}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
