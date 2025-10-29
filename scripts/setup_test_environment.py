#!/usr/bin/env python3
"""
测试环境设置脚本
将模型从offline/models复制到data/models，并安装所有依赖
"""

import os
import sys
import shutil
import subprocess
import logging
from pathlib import Path

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('setup_test_environment.log')
    ]
)
logger = logging.getLogger(__name__)

class TestEnvironmentSetup:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.offline_models_dir = self.project_root / 'offline' / 'models'
        self.data_models_dir = self.project_root / 'data' / 'models'
        self.config_file = self.project_root / 'config' / 'config.yml'
        
    def check_directories(self):
        """检查必要的目录是否存在"""
        logger.info("检查目录结构...")
        
        if not self.offline_models_dir.exists():
            logger.error(f"离线模型目录不存在: {self.offline_models_dir}")
            return False
            
        # 创建data/models目录
        self.data_models_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"创建运行时模型目录: {self.data_models_dir}")
        
        return True
    
    def copy_models(self):
        """复制模型文件"""
        logger.info("开始复制模型文件...")
        
        model_mapping = {
            'clip-vit-base-patch32': 'clip',
            'clap-htsat-fused': 'clap', 
            'whisper-base': 'whisper'
        }
        
        for source_dir, target_dir in model_mapping.items():
            source_path = self.offline_models_dir / source_dir
            target_path = self.data_models_dir / target_dir
            
            if not source_path.exists():
                logger.warning(f"源模型目录不存在: {source_path}")
                continue
                
            if target_path.exists():
                logger.info(f"目标目录已存在，删除后重新复制: {target_path}")
                shutil.rmtree(target_path)
            
            try:
                shutil.copytree(source_path, target_path)
                logger.info(f"成功复制 {source_dir} -> {target_dir}")
            except Exception as e:
                logger.error(f"复制 {source_dir} 失败: {e}")
                return False
                
        logger.info("模型文件复制完成")
        return True
    
    def install_dependencies(self):
        """安装Python依赖"""
        logger.info("安装Python依赖...")
        
        requirements_file = self.project_root / 'requirements.txt'
        
        if not requirements_file.exists():
            logger.error(f"依赖文件不存在: {requirements_file}")
            return False
        
        try:
            # 使用pip安装依赖
            result = subprocess.run([
                sys.executable, '-m', 'pip', 'install', '-r', str(requirements_file)
            ], capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode == 0:
                logger.info("依赖安装成功")
                return True
            else:
                logger.error(f"依赖安装失败: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"安装依赖时出错: {e}")
            return False
    
    def setup_database(self):
        """设置数据库"""
        logger.info("设置数据库...")
        
        # 创建数据库目录
        db_dir = self.project_root / 'data' / 'database'
        db_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建日志目录
        logs_dir = self.project_root / 'logs'
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("数据库目录设置完成")
        return True
    
    def update_config(self):
        """更新配置文件中的模型路径"""
        logger.info("更新配置文件...")
        
        if not self.config_file.exists():
            logger.error(f"配置文件不存在: {self.config_file}")
            return False
        
        try:
            # 读取配置文件
            with open(self.config_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 更新模型路径配置
            updated_content = content.replace(
                'models_dir: "./data/models"',
                'models_dir: "./data/models"'
            )
            
            # 确保模型路径正确
            updated_content = updated_content.replace(
                'model_name: "./data/models/clip-vit-base-patch32"',
                'model_name: "./data/models/clip"'
            )
            updated_content = updated_content.replace(
                'local_path: "./data/models/clip-vit-base-patch32"',
                'local_path: "./data/models/clip"'
            )
            
            updated_content = updated_content.replace(
                'model_name: "./data/models/clap-htsat-fused"',
                'model_name: "./data/models/clap"'
            )
            updated_content = updated_content.replace(
                'local_path: "./data/models/clap-htsat-fused"',
                'local_path: "./data/models/clap"'
            )
            
            updated_content = updated_content.replace(
                'model_name: "./data/models/whisper-base"',
                'model_name: "./data/models/whisper"'
            )
            updated_content = updated_content.replace(
                'local_path: "./data/models/whisper-base"',
                'local_path: "./data/models/whisper"'
            )
            
            # 写回配置文件
            with open(self.config_file, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            logger.info("配置文件更新完成")
            return True
            
        except Exception as e:
            logger.error(f"更新配置文件失败: {e}")
            return False
    
    def run_tests(self):
        """运行测试验证环境"""
        logger.info("运行测试验证环境...")
        
        test_files = [
            'tests/unit/test_config_manager.py',
            'tests/unit/test_vector_store.py',
            'tests/unit/test_embedding_engine.py'
        ]
        
        all_passed = True
        
        for test_file in test_files:
            test_path = self.project_root / test_file
            if not test_path.exists():
                logger.warning(f"测试文件不存在: {test_file}")
                continue
                
            logger.info(f"运行测试: {test_file}")
            
            try:
                result = subprocess.run([
                    sys.executable, '-m', 'pytest', str(test_path), '-v'
                ], capture_output=True, text=True, cwd=self.project_root)
                
                if result.returncode == 0:
                    logger.info(f"✓ {test_file} 测试通过")
                else:
                    logger.error(f"✗ {test_file} 测试失败")
                    logger.error(result.stderr)
                    all_passed = False
                    
            except Exception as e:
                logger.error(f"运行测试 {test_file} 时出错: {e}")
                all_passed = False
        
        return all_passed
    
    def setup(self):
        """执行完整的设置流程"""
        logger.info("开始设置测试环境...")
        
        steps = [
            ("检查目录结构", self.check_directories),
            ("设置数据库目录", self.setup_database),
            ("复制模型文件", self.copy_models),
            ("安装依赖", self.install_dependencies),
            ("更新配置文件", self.update_config),
            ("运行测试验证", self.run_tests)
        ]
        
        for step_name, step_func in steps:
            logger.info(f"执行步骤: {step_name}")
            if not step_func():
                logger.error(f"步骤失败: {step_name}")
                return False
        
        logger.info("测试环境设置完成!")
        return True

def main():
    """主函数"""
    setup = TestEnvironmentSetup()
    
    if setup.setup():
        print("\n✅ 测试环境设置成功!")
        print("✅ 模型文件已从 offline/models 复制到 data/models")
        print("✅ 依赖已安装")
        print("✅ 配置文件已更新")
        print("✅ 测试已运行")
        print("\n现在可以正常运行测试了!")
        return 0
    else:
        print("\n❌ 测试环境设置失败，请检查日志文件")
        return 1

if __name__ == "__main__":
    sys.exit(main())