#!/usr/bin/env python3
"""
简化版基础文件扫描流程验证测试
直接测试文件监控 → SQLite存储的核心逻辑
"""

import asyncio
import hashlib
import os
import tempfile
import time
import uuid
from pathlib import Path
from typing import Dict, Any, List

from src.core.config_manager import ConfigManager
from src.common.storage.database_adapter import DatabaseAdapter


class SimpleFileScanningTester:
    """简化版文件扫描流程测试器"""
    
    def __init__(self):
        # 测试目录
        self.test_dir = tempfile.mkdtemp(prefix="msearch_test_simple_")
        
        # 初始化组件
        self.db_path = f"{self.test_dir}/test_database.db"
        self.config_manager = ConfigManager()
        
        # 设置配置
        self.config_manager.set("database.sqlite.path", self.db_path)
        self.config_manager.set("system.supported_extensions", ['.jpg', '.jpeg', '.png', '.mp3', '.wav', '.mp4'])
        
        self.db_adapter = DatabaseAdapter(self.config_manager)
        
        # 测试结果统计
        self.results = {
            'files_added': 0,
            'files_modified': 0,
            'files_deleted': 0,
            'errors': []
        }
        
        print(f"✅ 简化版测试环境初始化完成")
        print(f"📁 测试目录: {self.test_dir}")
        print(f"🗄️  数据库路径: {self.db_path}")
    
    async def create_test_file(self, file_path: str, file_type: str):
        """创建测试文件"""
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        if file_type == "image":
            # JPEG文件头 + 内容 + 文件尾
            content = f"Test JPEG image created at {time.time()}".encode('utf-8')
            with open(file_path, 'wb') as f:
                f.write(b'\xFF\xD8\xFF')  # JPEG文件头
                f.write(content)
                f.write(b'\xFF\xD9')  # JPEG文件尾
        elif file_type == "audio":
            # MP3文件头 + 内容
            content = f"Test MP3 audio created at {time.time()}".encode('utf-8')
            with open(file_path, 'wb') as f:
                f.write(b'ID3')  # MP3文件头标识
                f.write(content)
        elif file_type == "video":
            # MP4文件头 + 内容
            content = f"Test MP4 video created at {time.time()}".encode('utf-8')
            with open(file_path, 'wb') as f:
                f.write(b'ftypmp4')  # MP4文件头标识
                f.write(content)
        else:
            # 通用文本文件
            content = f"Test {file_type} file created at {time.time()}"
            with open(file_path, 'w') as f:
                f.write(content)
    
    async def _calculate_file_hash(self, file_path: str) -> str:
        """计算文件hash"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            self.results['errors'].append(f"计算文件hash失败: {e}")
            return ""
    
    async def _extract_file_metadata(self, file_path: str) -> Dict[str, Any]:
        """提取文件基础元数据"""
        file_path_obj = Path(file_path)
        
        # 计算文件hash
        file_hash = await self._calculate_file_hash(file_path)
        
        # 获取文件信息
        stat = file_path_obj.stat()
        
        # 确定文件类型
        file_ext = file_path_obj.suffix.lower()
        if file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.webp']:
            file_type = 'image'
        elif file_ext in ['.mp3', '.wav', '.flac', '.m4a']:
            file_type = 'audio'
        elif file_ext in ['.mp4', '.avi', '.mov', '.mkv']:
            file_type = 'video'
        else:
            file_type = 'unknown'
        
        # 生成唯一文件ID
        file_id = str(uuid.uuid4())
        
        return {
            'id': file_id,
            'file_path': str(file_path),
            'file_name': file_path_obj.name,
            'file_type': file_type,
            'file_size': stat.st_size,
            'created_at': stat.st_ctime,
            'modified_at': stat.st_mtime,
            'file_hash': file_hash,
            'status': 'pending'
        }
    
    async def _process_file(self, file_path: str) -> bool:
        """处理单个文件"""
        try:
            # 提取基础元数据
            file_info = await self._extract_file_metadata(file_path)
            
            # 检查文件是否已存在
            existing_files = await self.db_adapter.get_files_by_path(file_path)
            
            if existing_files:
                # 更新现有文件
                existing_file = existing_files[0]
                await self.db_adapter.update_file(existing_file['id'], file_info)
                print(f"    ✅ 更新文件记录: {os.path.basename(file_path)}")
                return True
            else:
                # 插入新文件
                await self.db_adapter.insert_file(file_info)
                print(f"    ✅ 新增文件记录: {os.path.basename(file_path)}")
                return True
                
        except Exception as e:
            print(f"    ❌ 处理文件失败: {os.path.basename(file_path)} - {e}")
            self.results['errors'].append(f"处理文件失败: {e}")
            return False
    
    async def test_file_addition(self):
        """测试场景 1: 文件添加"""
        print(f"\n🧪 测试场景 1: 文件添加")
        
        test_files = []
        
        # 创建测试文件
        file_configs = [
            ("image1.jpg", "image"),
            ("image2.png", "image"), 
            ("audio1.mp3", "audio"),
            ("audio2.wav", "audio"),
            ("video1.mp4", "video"),
            ("video2.avi", "video"),
        ]
        
        print(f"  📁 创建测试文件...")
        for filename, file_type in file_configs:
            file_path = os.path.join(self.test_dir, filename)
            await self.create_test_file(file_path, file_type)
            test_files.append(file_path)
            print(f"    ✅ 创建: {filename}")
        
        print(f"  🔄 处理文件...")
        success_count = 0
        for file_path in test_files:
            if await self._process_file(file_path):
                success_count += 1
        
        if success_count == len(test_files):
            print(f"  ✅ 文件添加测试成功: {success_count}/{len(test_files)}")
            self.results['files_added'] = success_count
            return True
        else:
            print(f"  ❌ 文件添加测试失败: {success_count}/{len(test_files)}")
            return False
    
    async def test_file_modification(self):
        """测试场景 2: 文件修改"""
        print(f"\n🧪 测试场景 2: 文件修改")
        
        # 获取第一个测试文件
        test_files = list(Path(self.test_dir).glob("*"))
        if not test_files:
            print(f"  ⚠️  没有文件可供修改测试")
            return False
        
        test_file = str(test_files[0])
        print(f"  📝 选择文件进行修改测试: {os.path.basename(test_file)}")
        
        try:
            # 获取修改前的记录
            files_before = await self.db_adapter.get_files_by_path(test_file)
            if not files_before:
                print(f"  ❌ 修改前找不到文件记录")
                return False
            
            old_hash = files_before[0]['file_hash']
            old_modified_time = files_before[0]['modified_at']
            
            print(f"  📝 修改前hash: {old_hash[:16]}...")
            
            # 等待确保修改时间不同
            await asyncio.sleep(1)
            
            # 修改文件内容
            with open(test_file, 'a') as f:
                f.write(f"\nModified content at {time.time()}")
            
            # 重新处理文件
            await asyncio.sleep(0.1)  # 短暂等待
            
            if await self._process_file(test_file):
                # 验证修改后的记录
                files_after = await self.db_adapter.get_files_by_path(test_file)
                if files_after:
                    new_hash = files_after[0]['file_hash']
                    new_modified_time = files_after[0]['modified_at']
                    
                    if new_hash != old_hash and new_modified_time > old_modified_time:
                        print(f"  ✅ 文件修改测试成功: hash和修改时间都已更新")
                        self.results['files_modified'] += 1
                        return True
                    else:
                        print(f"  ❌ 文件修改后记录未正确更新")
                        return False
                else:
                    print(f"  ❌ 修改后找不到文件记录")
                    return False
            else:
                print(f"  ❌ 处理修改后的文件失败")
                return False
                
        except Exception as e:
            print(f"  ❌ 文件修改测试失败: {e}")
            self.results['errors'].append(f"文件修改测试失败: {e}")
            return False
    
    async def test_file_deletion(self):
        """测试场景 3: 文件删除"""
        print(f"\n🧪 测试场景 3: 文件删除")
        
        # 获取测试文件
        test_files = list(Path(self.test_dir).glob("*"))
        if len(test_files) < 2:
            print(f"  ⚠️  文件数量不足，无法进行删除测试")
            return False
        
        test_file = str(test_files[1])
        print(f"  🗑️  选择文件进行删除测试: {os.path.basename(test_file)}")
        
        try:
            # 检查删除前的记录
            files_before = await self.db_adapter.get_files_by_path(test_file)
            if not files_before:
                print(f"  ❌ 删除前找不到文件记录")
                return False
            
            file_id = files_before[0]['id']
            print(f"  🗑️  删除前文件ID: {file_id}")
            
            # 删除文件
            os.remove(test_file)
            print(f"  ✅ 文件已删除: {os.path.basename(test_file)}")
            
            # 从数据库删除记录
            await self.db_adapter.delete_file(file_id)
            print(f"  ✅ 数据库记录已删除: {file_id}")
            
            # 验证记录已删除
            files_after = await self.db_adapter.get_files_by_path(test_file)
            if not files_after:
                print(f"  ✅ 文件删除测试成功: 记录已完全清理")
                self.results['files_deleted'] += 1
                return True
            else:
                print(f"  ❌ 数据库记录仍然存在")
                return False
                
        except Exception as e:
            print(f"  ❌ 文件删除测试失败: {e}")
            self.results['errors'].append(f"文件删除测试失败: {e}")
            return False
    
    async def run_all_tests(self):
        """运行所有测试"""
        print(f"\n🔍 多模态检索系统 - 简化版文件扫描流程验证测试")
        print("=" * 60)
        
        try:
            # 测试文件添加
            addition_success = await self.test_file_addition()
            
            # 测试文件修改
            if addition_success:
                modification_success = await self.test_file_modification()
            else:
                modification_success = False
            
            # 测试文件删除
            if addition_success:
                deletion_success = await self.test_file_deletion()
            else:
                deletion_success = False
            
            # 生成测试报告
            await self._generate_test_report(addition_success, modification_success, deletion_success)
            
        except Exception as e:
            print(f"❌ 测试执行失败: {e}")
            self.results['errors'].append(f"测试执行失败: {e}")
        finally:
            await self.cleanup()
    
    async def _generate_test_report(self, addition_success: bool, modification_success: bool, deletion_success: bool):
        """生成测试报告"""
        print(f"\n📊 测试结果报告")
        print("=" * 60)
        
        total_tests = 3
        passed_tests = sum([addition_success, modification_success, deletion_success])
        
        print(f"总测试数: {total_tests}")
        print(f"通过测试: {passed_tests}")
        print(f"失败测试: {total_tests - passed_tests}")
        print(f"通过率: {passed_tests/total_tests*100:.1f}%")
        
        print(f"\n详细结果:")
        print(f"------------------------------------------------------------")
        print(f"{'✓' if addition_success else '✗'} 文件添加: {'PASS' if addition_success else 'FAIL'}")
        print(f"{'✓' if modification_success else '✗'} 文件修改: {'PASS' if modification_success else 'FAIL'}")
        print(f"{'✓' if deletion_success else '✗'} 文件删除: {'PASS' if deletion_success else 'FAIL'}")
        
        if self.results['errors']:
            print(f"\n错误详情:")
            for i, error in enumerate(self.results['errors'], 1):
                print(f"  {i}. {error}")
        
        print(f"\n✅ 简化版文件扫描流程验证测试完成!")
    
    async def cleanup(self):
        """清理测试环境"""
        print(f"\n🧹 清理测试环境...")
        
        try:
            import shutil
            shutil.rmtree(self.test_dir)
            print(f"  ✅ 测试目录已清理: {self.test_dir}")
        except Exception as e:
            print(f"  ⚠️  清理测试目录失败: {e}")


async def main():
    """主函数"""
    tester = SimpleFileScanningTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())