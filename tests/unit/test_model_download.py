#!/usr/bin/env python3
"""
测试模型下载和验证功能
"""

import os
import sys
import tempfile
import shutil
import pytest
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.install_windows import Installer

class TestModelDownload:
    """测试模型下载功能"""
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """设置和清理测试环境"""
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp(prefix="test_msearch_")
        self.test_data_dir = Path(self.temp_dir) / "data"
        self.test_models_dir = self.test_data_dir / "models"
        
        # 创建必要的目录
        self.test_models_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"\n测试环境设置完成: {self.temp_dir}")
        
        # 保存原始目录
        self.original_cwd = os.getcwd()
        
        yield
        
        # 清理测试环境
        print(f"\n清理测试环境: {self.temp_dir}")
        shutil.rmtree(self.temp_dir)
        
        # 恢复原始目录
        os.chdir(self.original_cwd)
    
    def test_check_python(self):
        """测试Python环境检查"""
        """测试Python环境检查"""
        installer = Installer()
        assert installer._check_python() is True, "Python环境检查失败"
    
    def test_read_config(self):
        """测试配置文件读取"""
        installer = Installer()
        assert installer.config is not None, "配置文件读取失败"
        assert "models" in installer.config, "配置文件中没有models配置"
    
    def test_model_mapping(self):
        """测试模型目录映射"""
        """测试模型目录映射"""
        # 模拟模型目录
        test_models = ["clip-vit-base-patch32", "clap-htsat-fused", "whisper-base"]
        
        for model_name in test_models:
            model_dir = self.test_models_dir / model_name
            model_dir.mkdir(parents=True, exist_ok=True)
            
            # 创建模拟配置文件
            (model_dir / "config.json").write_text('{"model_name": "test"}')
            
            # 创建模拟模型文件
            if "clip" in model_name or "clap" in model_name:
                (model_dir / "pytorch_model.bin").write_text('dummy_data')
            elif "whisper" in model_name:
                (model_dir / "model.bin").write_text('dummy_data')
        
        # 测试模型目录映射函数
        installer = Installer()
        
        # 修改installer的models_dir为测试目录
        installer.models_dir = self.test_models_dir
        
        # 调用创建符号链接的方法
        installer._create_model_symlinks()
        
        # 检查符号链接或复制目录是否创建成功
        assert (self.test_models_dir / "clip").exists(), "clip符号链接或复制目录创建失败"
        assert (self.test_models_dir / "clap").exists(), "clap符号链接或复制目录创建失败"
        assert (self.test_models_dir / "whisper").exists(), "whisper符号链接或复制目录创建失败"
    
    def test_model_verification(self):
        """测试模型完整性验证"""
        """测试模型完整性验证"""
        # 创建完整的模型目录
        complete_model_dir = self.test_models_dir / "complete_model"
        complete_model_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建必要的文件
        (complete_model_dir / "config.json").write_text('{"model_name": "test"}')
        (complete_model_dir / "pytorch_model.bin").write_text('dummy_data' * 1024 * 1024)  # 1MB
        
        # 创建不完整的模型目录
        incomplete_model_dir = self.test_models_dir / "incomplete_model"
        incomplete_model_dir.mkdir(parents=True, exist_ok=True)
        
        # 只创建config.json，不创建模型文件
        (incomplete_model_dir / "config.json").write_text('{"model_name": "test"}')
        
        # 测试模型验证
        installer = Installer()
        
        # 完整模型应该验证通过
        assert installer._verify_model(complete_model_dir) is True, "完整模型验证失败"
        
        # 不完整模型应该验证失败
        assert installer._verify_model(incomplete_model_dir) is False, "不完整模型验证失败"
    
    def test_model_config(self):
        """测试模型配置"""
        """测试模型配置"""
        installer = Installer()
        
        # 检查模型配置是否存在
        assert "models" in installer.config, "配置中没有models部分"
        
        # 检查必要的模型是否在配置中
        required_models = ["clip", "clap", "whisper", "facenet"]
        for model_name in required_models:
            assert model_name in installer.config["models"], f"配置中缺少{model_name}模型"
        
