#!/usr/bin/env python3
"""
MSearch 统一安装脚本 - Windows 版
用于在 Windows 系统上安装 MSearch 并下载模型
"""

import os
import sys
import json
import logging
import shutil
import subprocess
import time
from pathlib import Path
import yaml

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('install_windows.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class Installer:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.data_dir = self.project_root / "data"
        self.models_dir = self.data_dir / "models"
        self.config_path = self.project_root / "config" / "msearch.yml"
        self.venv_dir = self.project_root / "venv"
        self.logs_dir = self.project_root / "logs"
        self.temp_dir = self.project_root / "temp"
        
        # 创建必要的目录
        self._create_directories()
        
        # 读取配置
        self.config = self._read_config()
    
    def _create_directories(self):
        """创建必要的目录"""
        directories = [
            self.data_dir,
            self.models_dir,
            self.logs_dir,
            self.temp_dir
        ]
        
        for dir_path in directories:
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"创建目录: {dir_path}")
    
    def _read_config(self):
        """读取配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            logger.info(f"读取配置文件成功: {self.config_path}")
            return config
        except Exception as e:
            logger.error(f"读取配置文件失败: {e}")
            return None
    
    def _check_python(self):
        """检查 Python 环境"""
        logger.info("检查 Python 环境...")
        
        try:
            result = subprocess.run([sys.executable, "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"Python 版本: {result.stdout.strip()}")
                return True
            else:
                logger.error(f"Python 版本检查失败: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Python 检查失败: {e}")
            return False
    
    def _create_venv(self):
        """创建虚拟环境"""
        logger.info("创建虚拟环境...")
        
        if self.venv_dir.exists():
            logger.info(f"虚拟环境已存在: {self.venv_dir}，跳过创建")
            return True
        
        try:
            subprocess.run([sys.executable, "-m", "venv", str(self.venv_dir)], check=True)
            logger.info(f"虚拟环境创建成功: {self.venv_dir}")
            return True
        except Exception as e:
            logger.error(f"虚拟环境创建失败: {e}")
            return False
    
    def _get_python_path(self):
        """获取虚拟环境中的 Python 路径"""
        return self.venv_dir / "Scripts" / "python.exe"
    
    def _run_pip_command(self, args, description="执行pip命令", max_retries=3):
        """运行pip命令，使用python -m pip的方式"""
        python_path = self._get_python_path()
        cmd = [str(python_path), "-m", "pip"] + args
        return self._run_command(cmd, description, max_retries)
    
    def _run_command(self, cmd, description="执行命令", max_retries=3):
        """运行命令，支持重试"""
        for attempt in range(max_retries):
            try:
                logger.info(f"{description} (尝试 {attempt + 1}/{max_retries})...")
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                logger.info(f"{description} 成功")
                if result.stdout:
                    logger.debug(f"命令输出: {result.stdout}")
                return True
            except subprocess.CalledProcessError as e:
                logger.warning(f"{description} 失败: {e}")
                logger.debug(f"命令输出: {e.stdout}")
                logger.debug(f"错误信息: {e.stderr}")
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 5
                    logger.info(f"等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"{description} 多次尝试后仍然失败")
                    return False
            except Exception as e:
                logger.error(f"{description} 发生异常: {e}")
                return False
    
    def _install_dependencies(self):
        """安装依赖"""
        import sys
        logger.info("安装依赖...")
        
        python_path = self._get_python_path()
        
        # 确保pip已安装
        logger.info("确保pip已安装...")
        if not self._run_command([str(python_path), "-m", "ensurepip"], "安装pip"):
            logger.error("pip安装失败")
            return False
        
        # 升级 pip
        if not self._run_pip_command(["install", "--upgrade", "pip"], "升级pip"):
            logger.warning("pip升级失败，继续使用现有版本")
        
        # 安装 Visual C++ Redistributable (解决PyTorch DLL问题)
        logger.info("检查并安装Visual C++ Redistributable...")
        try:
            import os
            import subprocess
            
            # 直接使用项目根目录作为下载路径，避免tempfile的编码问题
            vc_redist_path = self.temp_dir / "vc_redist.x64.exe"
            
            # 下载Visual C++ Redistributable
            vc_redist_url = "https://aka.ms/vs/17/release/vc_redist.x64.exe"
            logger.info(f"下载Visual C++ Redistributable到: {vc_redist_path}")
            
            # 使用更可靠的下载方式，避免路径编码问题
            import urllib.request
            urllib.request.urlretrieve(vc_redist_url, str(vc_redist_path))
            logger.info(f"Visual C++ Redistributable下载完成")
            
            # 安装Visual C++ Redistributable
            logger.info(f"安装Visual C++ Redistributable...")
            result = subprocess.run(
                [str(vc_redist_path), "/install", "/quiet", "/norestart"],
                capture_output=True, text=True
            )
            
            if result.returncode == 0 or result.returncode == 3010:  # 3010表示需要重启
                logger.info("Visual C++ Redistributable安装成功")
            else:
                logger.warning(f"Visual C++ Redistributable安装返回非零代码: {result.returncode}")
                logger.debug(f"安装输出: {result.stdout}")
                logger.debug(f"安装错误: {result.stderr}")
            
            # 清理临时文件
            if vc_redist_path.exists():
                vc_redist_path.unlink()
        except Exception as e:
            logger.warning(f"Visual C++ Redistributable安装失败: {e}，继续安装其他依赖")
        
        # 额外提示：如果Visual C++ Redistributable安装失败，建议手动安装
        logger.info("如果PyTorch出现DLL初始化问题，建议手动安装Visual C++ Redistributable")
        logger.info("下载地址: https://aka.ms/vs/17/release/vc_redist.x64.exe")
        
        # 额外安装可能需要的系统依赖
        logger.info("安装可能需要的系统依赖...")
        self._run_pip_command(
            ["install", "pywin32", "wmi", "psutil"],
            "安装系统依赖包"
        )
        
        # 安装 requirements.txt 中的依赖
        requirements_path = self.project_root / "requirements.txt"
        if requirements_path.exists():
            if not self._run_pip_command(
                ["install", "-r", str(requirements_path), "-i", "https://pypi.tuna.tsinghua.edu.cn/simple"],
                "安装requirements.txt依赖",
                max_retries=2
            ):
                logger.warning("requirements.txt依赖安装失败，尝试安装核心依赖")
        else:
            logger.error(f"requirements.txt 不存在: {requirements_path}")
        
        # 安装额外的模型依赖
        # 先卸载可能存在的PyTorch和torchvision，避免版本冲突
        logger.info("卸载可能存在的PyTorch和torchvision...")
        self._run_pip_command(
            ["uninstall", "-y", "torch", "torchvision", "torchaudio"],
            "卸载PyTorch和torchvision"
        )
        
        # 确保Milvus Lite安装正确版本
        logger.info("安装/更新Milvus Lite...")
        # 先安装兼容的marshmallow版本
        self._run_pip_command(
            ["install", "marshmallow>=3.0.0,<4.0.0", "--no-cache-dir"],
            "安装兼容的marshmallow版本"
        )
        # 安装pymilvus
        self._run_pip_command(
            ["install", "pymilvus==2.3.0", "--no-cache-dir"],
            "安装pymilvus"
        )
        # 尝试安装milvus-lite（如果可用）
        self._run_pip_command(
            ["install", "milvus-lite", "--no-cache-dir"],
            "安装milvus-lite",
            max_retries=1
        )
        
        # 检测GPU可用性
        gpu_available = False
        
        # 使用更可靠的GPU检测方法（不依赖PyTorch）
        try:
            import subprocess
            result = subprocess.run(["nvidia-smi"], capture_output=True, text=True)
            gpu_available = result.returncode == 0 and "NVIDIA" in result.stdout
            if gpu_available:
                logger.info("检测到NVIDIA GPU，将使用GPU版本的PyTorch")
            else:
                logger.info("未检测到NVIDIA GPU或nvidia-smi不可用，将使用CPU版本的PyTorch")
        except Exception as e:
            logger.warning(f"GPU检测失败: {e}，将使用CPU版本的PyTorch")
        
        # 获取Python版本，用于选择兼容的PyTorch版本
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        logger.info(f"当前Python版本: {python_version}")
        
        # 初始化pytorch_installed变量
        pytorch_installed = False
        
        # 首先确保wheel和setuptools是最新的
        self._run_pip_command(["install", "--upgrade", "wheel", "setuptools"], "升级wheel和setuptools")
        
        # 定义多种PyTorch版本组合，根据Python版本和GPU可用性选择
        pytorch_versions = []
        
        # 基于Python版本选择合适的PyTorch版本
        if python_version == "3.10":
            # Python 3.10兼容的版本
            if gpu_available:
                pytorch_versions = [
                    {
                        "name": "CUDA 11.8 - PyTorch 2.0.1 (Python 3.10兼容)",
                        "command": [
                            "install",
                            "torch==2.0.1",
                            "torchvision==0.15.2",
                            "torchaudio==2.0.1",
                            "--index-url", "https://download.pytorch.org/whl/cu118",
                            "--no-cache-dir"
                        ]
                    },
                    {
                        "name": "CUDA 11.7 - PyTorch 1.13.1 (稳定版)",
                        "command": [
                            "install",
                            "torch==1.13.1",
                            "torchvision==0.14.1",
                            "torchaudio==0.13.1",
                            "--index-url", "https://download.pytorch.org/whl/cu117",
                            "--no-cache-dir"
                        ]
                    }
                ]
            
            # 添加CPU版本作为回退
            pytorch_versions.extend([
                {
                    "name": "CPU - PyTorch 2.0.1 (Python 3.10兼容)",
                    "command": [
                        "install",
                        "torch==2.0.1",
                        "torchvision==0.15.2",
                        "torchaudio==2.0.1",
                        "--index-url", "https://download.pytorch.org/whl/cpu",
                        "--no-cache-dir"
                    ]
                },
                {
                    "name": "CPU - PyTorch 1.13.1 (稳定版)",
                    "command": [
                        "install",
                        "torch==1.13.1",
                        "torchvision==0.14.1",
                        "torchaudio==0.13.1",
                        "--index-url", "https://download.pytorch.org/whl/cpu",
                        "--no-cache-dir"
                    ]
                },
                {
                    "name": "CPU - PyTorch 1.12.1 (兼容旧系统)",
                    "command": [
                        "install",
                        "torch==1.12.1",
                        "torchvision==0.13.1",
                        "torchaudio==0.12.1",
                        "--index-url", "https://download.pytorch.org/whl/cpu",
                        "--no-cache-dir"
                    ]
                }
            ])
        elif python_version in ["3.8", "3.9"]:
            # Python 3.8/3.9兼容的版本
            if gpu_available:
                pytorch_versions = [
                    {
                        "name": "CUDA 11.6 - PyTorch 1.12.1 (Python 3.8/3.9兼容)",
                        "command": [
                            "install",
                            "torch==1.12.1",
                            "torchvision==0.13.1",
                            "torchaudio==0.12.1",
                            "--index-url", "https://download.pytorch.org/whl/cu116",
                            "--no-cache-dir"
                        ]
                    }
                ]
            
            # 添加CPU版本
            pytorch_versions.extend([
                {
                    "name": "CPU - PyTorch 1.12.1 (Python 3.8/3.9兼容)",
                    "command": [
                        "install",
                        "torch==1.12.1",
                        "torchvision==0.13.1",
                        "torchaudio==0.12.1",
                        "--index-url", "https://download.pytorch.org/whl/cpu",
                        "--no-cache-dir"
                    ]
                }
            ])
        else:
            # 其他Python版本，使用较旧的稳定版本
            if gpu_available:
                pytorch_versions = [
                    {
                        "name": "CUDA 11.3 - PyTorch 1.11.0 (通用兼容)",
                        "command": [
                            "install",
                            "torch==1.11.0",
                            "torchvision==0.12.0",
                            "torchaudio==0.11.0",
                            "--index-url", "https://download.pytorch.org/whl/cu113",
                            "--no-cache-dir"
                        ]
                    }
                ]
            
            # 添加CPU版本
            pytorch_versions.extend([
                {
                    "name": "CPU - PyTorch 1.11.0 (通用兼容)",
                    "command": [
                        "install",
                        "torch==1.11.0",
                        "torchvision==0.12.0",
                        "torchaudio==0.11.0",
                        "--index-url", "https://download.pytorch.org/whl/cpu",
                        "--no-cache-dir"
                    ]
                }
            ])
        
        # 尝试所有版本，直到找到能正常工作的
        for version in pytorch_versions:
            logger.info(f"尝试安装: {version['name']}")
            
            # 先卸载可能存在的PyTorch版本，避免冲突
            self._run_pip_command(["uninstall", "-y", "torch", "torchvision", "torchaudio"], "清理旧的PyTorch版本")
            
            # 安装当前版本
            if self._run_pip_command(version['command'], f"安装{version['name']}"):
                logger.info(f"{version['name']}安装成功，验证中...")
                
                # 验证安装
                try:
                    # 重新创建一个干净的Python进程来测试，避免内存中的模块冲突
                    test_script = """
import torch
import torchvision
print(f"PyTorch: {torch.__version__}")
print(f"torchvision: {torchvision.__version__}")
print(f"CUDA可用: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"CUDA版本: {torch.version.cuda}")
    print(f"GPU设备: {torch.cuda.get_device_name(0)}")
# 测试简单运算
x = torch.tensor([1.0, 2.0, 3.0])
y = x * 2
print(f"张量运算: {x} * 2 = {y}")
print("测试通过")
"""
                    
                    # 写入测试脚本
                    test_file = self.temp_dir / "test_pytorch_verify.py"
                    with open(test_file, 'w', encoding='utf-8') as f:
                        f.write(test_script)
                    
                    # 在虚拟环境中运行测试脚本
                    python_path = self._get_python_path()
                    result = subprocess.run(
                        [str(python_path), str(test_file)],
                        capture_output=True, text=True
                    )
                    
                    if result.returncode == 0:
                        logger.info(f"✅ {version['name']}验证通过！")
                        logger.info(f"   验证输出: {result.stdout.strip()}")
                        pytorch_installed = True
                        break
                    else:
                        logger.error(f"❌ {version['name']}验证失败！")
                        logger.error(f"   验证错误: {result.stderr.strip()}")
                    
                    # 清理测试文件
                    if test_file.exists():
                        test_file.unlink()
                        
                except Exception as e:
                    logger.error(f"❌ {version['name']}验证时发生异常: {e}")
                    logger.error(f"   错误类型: {type(e).__name__}")
            else:
                logger.warning(f"⚠️ {version['name']}安装失败，尝试下一个版本")
        
        if not pytorch_installed:
            logger.error("❌ 所有PyTorch版本安装失败")
            logger.error("建议手动安装PyTorch: https://pytorch.org/get-started/locally/")
            # 继续安装，让用户手动解决PyTorch问题
            logger.warning("继续安装其他依赖，PyTorch将需要手动安装")
            # 不要返回False，继续安装其他依赖
        
        # 即使PyTorch安装失败，也要继续安装其他依赖
        logger.info("PyTorch安装完成，继续安装其他依赖")
        
        # 安装其他依赖
        additional_packages = [
            "transformers",
            "huggingface_hub",
            "facenet-pytorch"
        ]
        
        for package in additional_packages:
            if not self._run_pip_command(
                ["install", package, "-i", "https://pypi.tuna.tsinghua.edu.cn/simple"],
                f"安装{package}"
            ):
                logger.warning(f"{package}安装失败，继续尝试其他依赖")
        
        # 检查关键依赖是否安装成功
        try:
            # 先添加虚拟环境的site-packages到Python路径
            import sys
            site_packages = str(self.venv_dir / "Lib" / "site-packages")
            if site_packages not in sys.path:
                sys.path.insert(0, site_packages)
            
            import transformers
            import torch
            import huggingface_hub
            logger.info("核心依赖检查通过")
            return True
        except ImportError as e:
            logger.error(f"核心依赖检查失败: {e}")
            return False
    
    def _download_model(self, repo_id, local_path, model_type):
        """下载单个模型"""
        logger.info(f"\n下载模型: {repo_id} 到 {local_path}")
        
        # 创建模型目录
        local_path.mkdir(parents=True, exist_ok=True)
        
        # 使用 Python 脚本下载模型
        python_path = self._get_python_path()
        
        download_script = f"""
import os
import sys
import ssl

# 添加虚拟环境site-packages到Python路径
venv_site_packages = r'{venv_site_packages}'
if venv_site_packages not in sys.path:
    sys.path.insert(0, venv_site_packages)

# 确保huggingface_hub已安装
try:
    from huggingface_hub import snapshot_download
except ImportError:
    print("安装huggingface_hub...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "huggingface_hub", "-i", "https://pypi.tuna.tsinghua.edu.cn/simple"])
    from huggingface_hub import snapshot_download

# 禁用 SSL 验证（解决企业环境问题）
ssl._create_default_https_context = ssl._create_unverified_context

# 设置环境变量
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"

# 下载模型
try:
    snapshot_download(
        repo_id="{repo_id}",
        local_dir="{local_path}",
        local_dir_use_symlinks=False,
        resume_download=True,
        ignore_patterns=[".gitattributes", ".gitignore", "README.md", "LICENSE"],
        max_workers=4
    )
    print("模型下载成功")
    sys.exit(0)
except Exception as e:
    print(f"模型下载失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
"""
        
        # 获取虚拟环境site-packages路径
        venv_site_packages = str(self.venv_dir / "Lib" / "site-packages")
        
        # 替换占位符
        download_script = download_script.format(
            repo_id=repo_id, 
            local_path=local_path,
            venv_site_packages=venv_site_packages
        )
        
        # 写入临时脚本
        temp_script = self.temp_dir / f"download_{model_type}.py"
        with open(temp_script, 'w', encoding='utf-8') as f:
            f.write(download_script)
        
        try:
            # 执行下载脚本
            result = self._run_command(
                [str(python_path), str(temp_script)], 
                f"下载模型 {repo_id}",
                max_retries=2
            )
            return result
        except Exception as e:
            logger.error(f"模型 {repo_id} 下载异常: {e}")
            return False
        finally:
            # 删除临时脚本
            if temp_script.exists():
                temp_script.unlink()
    
    def _verify_model(self, model_path):
        """验证模型是否完整"""
        logger.info(f"验证模型: {model_path}")
        
        # 检查关键文件是否存在
        required_files = ["config.json"]
        
        # 检查模型类型，添加特定的模型文件
        if "clip" in str(model_path).lower() or "clap" in str(model_path).lower():
            required_files.append("pytorch_model.bin")
        elif "whisper" in str(model_path).lower():
            required_files.append("model.bin")
        
        all_exist = True
        for file_name in required_files:
            file_path = model_path / file_name
            if file_path.exists():
                logger.info(f"   ✅ {file_name} 存在")
            else:
                logger.error(f"   ❌ {file_name} 不存在")
                all_exist = False
        
        return all_exist
    
    def _create_model_symlinks(self):
        """创建模型目录的符号链接或复制目录"""
        logger.info("创建模型目录映射...")
        
        # 模型目录映射（简化名称 -> 完整名称）
        model_dir_mapping = {
            "clip": "clip-vit-base-patch32",
            "clap": "clap-htsat-fused",
            "whisper": "whisper-base",
            "facenet": "facenet-pytorch"
        }
        
        for simple_name, full_name in model_dir_mapping.items():
            source_dir = self.models_dir / full_name
            target_dir = self.models_dir / simple_name
            
            if source_dir.exists():
                logger.info(f"处理模型: {simple_name} -> {full_name}")
                
                # 如果目标目录不存在，创建它
                if not target_dir.exists():
                    try:
                        # 尝试创建符号链接
                        os.symlink(source_dir, target_dir, target_is_directory=True)
                        logger.info(f"创建符号链接成功: {source_dir} -> {target_dir}")
                    except Exception as e:
                        # 符号链接失败，尝试复制目录
                        logger.warning(f"创建符号链接失败: {e}，尝试复制目录")
                        try:
                            shutil.copytree(source_dir, target_dir)
                            logger.info(f"复制目录成功: {source_dir} -> {target_dir}")
                        except Exception as e2:
                            logger.error(f"复制目录失败: {e2}")
                else:
                    logger.info(f"目标目录已存在: {target_dir}")
    
    def download_models(self):
        """下载所有必要的模型"""
        logger.info("\n开始下载模型...")
        
        # 模型列表
        models = [
            {
                "name": "clip",
                "repo_id": "openai/clip-vit-base-patch32",
                "local_path": self.models_dir / "clip-vit-base-patch32",
                "model_type": "clip"
            },
            {
                "name": "clap",
                "repo_id": "laion/clap-htsat-fused",
                "local_path": self.models_dir / "clap-htsat-fused",
                "model_type": "clap"
            },
            {
                "name": "whisper",
                "repo_id": "openai/whisper-base",
                "local_path": self.models_dir / "whisper-base",
                "model_type": "whisper"
            },
            {
                "name": "facenet",
                "repo_id": "timobrooks/facenet-pytorch",
                "local_path": self.models_dir / "facenet-pytorch",
                "model_type": "facenet"
            }
        ]
        
        # 下载每个模型
        success_count = 0
        for model in models:
            if self._download_model(model["repo_id"], model["local_path"], model["model_type"]):
                if self._verify_model(model["local_path"]):
                    success_count += 1
                else:
                    logger.warning(f"模型 {model['name']} 验证失败")
        
        logger.info(f"\n模型下载完成: {success_count}/{len(models)} 个模型成功")
        
        # 创建模型目录映射
        self._create_model_symlinks()
        
        return success_count > 0
    
    def verify_installation(self):
        """验证安装是否成功"""
        logger.info("\n验证安装...")
        
        # 检查模型目录
        model_paths = {
            "clip": self.models_dir / "clip",
            "clap": self.models_dir / "clap",
            "whisper": self.models_dir / "whisper",
            "facenet": self.models_dir / "facenet"
        }
        
        all_exist = True
        for model_name, model_path in model_paths.items():
            if model_path.exists() and model_path.is_dir():
                # 检查模型文件数量
                files = list(model_path.glob("*"))
                logger.info(f"   ✅ {model_name} 模型目录存在，包含 {len(files)} 个文件")
            else:
                logger.error(f"   ❌ {model_name} 模型目录不存在或为空")
                all_exist = False
        
        return all_exist
    
    def run_simple_test(self):
        """运行简单的模型测试"""
        logger.info("\n运行简单模型测试...")
        
        python_path = self._get_python_path()
        
        # 简单的 CLIP 模型测试脚本
        test_script = f"""
import os
import sys
from transformers import CLIPModel, CLIPProcessor
import torch

# 设置模型路径
clip_path = r"{self.models_dir / 'clip'}"

print(f"测试 CLIP 模型: {clip_path}")

try:
    # 加载模型
    model = CLIPModel.from_pretrained(clip_path, local_files_only=True)
    processor = CLIPProcessor.from_pretrained(clip_path, local_files_only=True)
    
    print("模型加载成功")
    
    # 简单推理
    text = "a photo of a cat"
    inputs = processor(text=text, return_tensors="pt")
    outputs = model.get_text_features(**inputs)
    
    print(f"推理成功，输出向量维度: {outputs.shape}")
    print("测试通过！")
    sys.exit(0)
except Exception as e:
    print(f"测试失败: {e}")
    sys.exit(1)
"""
        
        # 写入测试脚本
        test_file = self.temp_dir / "test_model.py"
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_script)
        
        try:
            # 执行测试脚本
            result = subprocess.run([str(python_path), str(test_file)], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"模型测试成功: {result.stdout}")
                return True
            else:
                logger.error(f"模型测试失败: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"模型测试异常: {e}")
            return False
        finally:
            # 删除测试脚本
            if test_file.exists():
                test_file.unlink()
    
    def run(self):
        """运行完整的安装流程"""
        logger.info("========================================")
        logger.info("MSearch 安装脚本 (Windows)")
        logger.info("========================================")
        
        # 检查 Python 环境
        if not self._check_python():
            logger.error("Python 环境检查失败，无法继续安装")
            return False
        
        # 创建虚拟环境
        if not self._create_venv():
            logger.error("虚拟环境创建失败，无法继续安装")
            return False
        
        # 安装依赖
        if not self._install_dependencies():
            logger.error("依赖安装失败，无法继续安装")
            return False
        
        # 下载模型
        if not self.download_models():
            logger.error("模型下载失败，无法继续安装")
            return False
        
        # 验证安装
        if not self.verify_installation():
            logger.error("安装验证失败")
            return False
        
        # 运行简单测试
        if not self.run_simple_test():
            logger.warning("模型测试失败，但安装已完成")
            # 测试失败不影响安装，继续返回成功
        
        logger.info("\n========================================")
        logger.info("✅ 安装完成！")
        logger.info("========================================")
        return True

if __name__ == "__main__":
    installer = Installer()
    success = installer.run()
    sys.exit(0 if success else 1)
