#!/usr/bin/env python3
"""
数据库Schema升级验证测试（修正版）
基于实际数据库结构进行测试
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database_adapter_upgraded import DatabaseAdapterUpgraded
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DatabaseUpgradeTestCorrected:
    """数据库升级测试类（修正版）"""
    
    def __init__(self):
        self.db = DatabaseAdapterUpgraded()
        self.test_results = []
    
    def log_test_result(self, test_name: str, success: bool, message: str = ""):
        """记录测试结果"""
        status = "✅ 通过" if success else "❌ 失败"
        result = {
            'test_name': test_name,
            'success': success,
            'message': message,
            'status': status
        }
        self.test_results.append(result)
        print(f"{status} {test_name} - {message}")
    
    def create_test_file_data(self, file_path: str, category: str = None) -> dict:
        """创建测试文件数据"""
        now = datetime.now().timestamp()
        
        file_data = {
            'file_path': file_path,
            'file_name': os.path.basename(file_path),
            'file_type': 'text',
            'file_size': 1024,
            'file_hash': f"hash_{hash(file_path)}",
            'created_at': now,
            'modified_at': now,
            'status': 'pending',
            'can_delete': False
        }
        
        if category:
            file_data['file_category'] = category
            
        return file_data
    
    def test_new_fields_in_files_table(self) -> bool:
        """测试files表的新字段"""
        try:
            # 插入包含新字段的测试文件
            test_file = self.create_test_file_data('/test/upgraded_file_corrected.txt')
            test_file.update({
                'file_category': 'document',
                'can_delete': True
            })
            
            file_id = self.db.insert_file(test_file)
            
            # 测试根据分类查询
            documents = self.db.get_file_by_category('document')
            found_file = any(f['id'] == file_id for f in documents)
            
            if found_file:
                self.log_test_result("files表新字段插入和查询", True, "成功插入和查询file_category字段")
                return True
            else:
                self.log_test_result("files表新字段插入和查询", False, "未找到插入的文件")
                return False
                
        except Exception as e:
            self.log_test_result("files表新字段插入和查询", False, f"错误: {str(e)}")
            return False
    
    def test_file_relationships_table(self) -> bool:
        """测试文件关系表"""
        try:
            # 创建测试文件
            file1_data = self.create_test_file_data('/test/source_file_relationship.txt')
            file2_data = self.create_test_file_data('/test/related_file_relationship.txt')
            
            file1_id = self.db.insert_file(file1_data)
            file2_id = self.db.insert_file(file2_data)
            
            # 创建文件关系
            success = self.db.create_file_relationship(
                source_file_id=file1_id,
                related_file_id=file2_id,
                relationship_type='similar',
                confidence_score=0.85,
                metadata={'similarity_algorithm': 'text_hash'}
            )
            
            if success:
                # 测试查询文件关系
                relationships = self.db.get_file_relationships(file1_id)
                found_relationship = any(
                    r['related_file_id'] == file2_id and r['relationship_type'] == 'similar' 
                    for r in relationships
                )
                
                if found_relationship:
                    self.log_test_result("file_relationships表功能", True, "成功创建和查询文件关系")
                    return True
                else:
                    self.log_test_result("file_relationships表功能", False, "未找到创建的文件关系")
                    return False
            else:
                self.log_test_result("file_relationships表功能", False, "创建文件关系失败")
                return False
                
        except Exception as e:
            self.log_test_result("file_relationships表功能", False, f"错误: {str(e)}")
            return False
    
    def test_video_segments_table(self) -> bool:
        """测试视频片段表"""
        try:
            # 创建测试文件
            test_video = self.create_test_file_data('/test/video_segments_test.mp4')
            test_video.update({
                'file_type': 'video',
                'file_category': 'media'
            })
            
            video_id = self.db.insert_file(test_video)
            
            # 创建视频片段
            segment_data = {
                'file_uuid': video_id,
                'segment_index': 1,
                'start_time': 0.0,
                'end_time': 10.0,
                'duration': 10.0,
                'scene_boundary': True
            }
            
            segment_id = self.db.insert_video_segment(segment_data)
            
            # 测试查询视频片段
            segments = self.db.get_video_segments_by_file(video_id)
            found_segment = any(s['segment_id'] == segment_id for s in segments)
            
            if found_segment:
                self.log_test_result("video_segments表功能", True, "成功插入和查询视频片段")
                return True
            else:
                self.log_test_result("video_segments表功能", False, "未找到插入的视频片段")
                return False
                
        except Exception as e:
            self.log_test_result("video_segments表功能", False, f"错误: {str(e)}")
            return False
    
    def test_deletable_files_functionality(self) -> bool:
        """测试可删除文件功能"""
        try:
            # 创建一个可删除的测试文件
            deletable_file = self.create_test_file_data('/test/deletable_file_corrected.txt')
            deletable_file.update({
                'file_category': 'temp',
                'can_delete': True
            })
            
            file_id = self.db.insert_file(deletable_file)
            
            # 测试获取可删除文件列表
            deletable_files = self.db.get_deletable_files()
            found_deletable = any(f['id'] == file_id for f in deletable_files)
            
            if found_deletable:
                self.log_test_result("可删除文件功能", True, "成功查询可删除文件列表")
                return True
            else:
                self.log_test_result("可删除文件功能", False, "未找到可删除文件")
                return False
                
        except Exception as e:
            self.log_test_result("可删除文件功能", False, f"错误: {str(e)}")
            return False
    
    def test_database_statistics(self) -> bool:
        """测试数据库统计功能"""
        try:
            stats = self.db.get_database_stats()
            
            # 检查是否返回了统计信息
            if isinstance(stats, dict) and len(stats) > 0:
                self.log_test_result("数据库统计功能", True, f"成功获取统计信息: {len(stats)}项")
                return True
            else:
                self.log_test_result("数据库统计功能", False, "未获取到统计信息")
                return False
                
        except Exception as e:
            self.log_test_result("数据库统计功能", False, f"错误: {str(e)}")
            return False
    
    def test_schema_version(self) -> bool:
        """测试Schema版本功能"""
        try:
            version_info = self.db.get_schema_version()
            
            if version_info and 'version' in version_info:
                self.log_test_result("Schema版本功能", True, f"当前版本: {version_info['version']}")
                return True
            else:
                self.log_test_result("Schema版本功能", False, "未获取到版本信息")
                return False
                
        except Exception as e:
            self.log_test_result("Schema版本功能", False, f"错误: {str(e)}")
            return False
    
    def test_source_file_relationship(self) -> bool:
        """测试源文件关系功能"""
        try:
            # 创建源文件
            source_file = self.create_test_file_data('/test/source_file_main.txt')
            source_file.update({
                'file_category': 'original',
                'can_delete': False
            })
            
            source_id = self.db.insert_file(source_file)
            
            # 创建派生文件
            derived_file = self.create_test_file_data('/test/derived_file_copy.txt')
            derived_file.update({
                'file_category': 'derived',
                'source_file_id': source_id,
                'can_delete': True
            })
            
            derived_id = self.db.insert_file(derived_file)
            
            # 测试根据源文件ID查询派生文件
            derived_files = self.db.get_file_by_source(source_id)
            found_derived = any(f['id'] == derived_id for f in derived_files)
            
            if found_derived:
                self.log_test_result("源文件关系功能", True, "成功查询源文件的派生文件")
                return True
            else:
                self.log_test_result("源文件关系功能", False, "未找到派生文件")
                return False
                
        except Exception as e:
            self.log_test_result("源文件关系功能", False, f"错误: {str(e)}")
            return False
    
    def run_all_tests(self) -> bool:
        """运行所有测试"""
        print("🚀 开始运行数据库Schema升级验证测试（修正版）...\n")
        
        tests = [
            ("files表新字段测试", self.test_new_fields_in_files_table),
            ("文件关系表测试", self.test_file_relationships_table),
            ("视频片段表测试", self.test_video_segments_table),
            ("可删除文件功能测试", self.test_deletable_files_functionality),
            ("数据库统计功能测试", self.test_database_statistics),
            ("Schema版本功能测试", self.test_schema_version),
            ("源文件关系功能测试", self.test_source_file_relationship)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"🔍 运行测试: {test_name}")
            if test_func():
                passed += 1
            print()
        
        # 总结测试结果
        print("=" * 60)
        print("📊 测试结果总结")
        print("=" * 60)
        
        for result in self.test_results:
            print(f"{result['status']} {result['test_name']} - {result['message']}")
        
        print(f"\n🎯 总计: {total} 个测试")
        print(f"✅ 通过: {passed} 个测试")
        print(f"❌ 失败: {total - passed} 个测试")
        print(f"📈 通过率: {passed/total*100:.1f}%")
        
        success = passed == total
        if success:
            print("\n🎉 所有测试通过！数据库Schema升级验证成功！")
        else:
            print(f"\n⚠️  有 {total-passed} 个测试失败，请检查相关功能")
        
        return success


def main():
    """主函数"""
    print("=" * 60)
    print("🔧 数据库Schema升级验证测试（修正版）")
    print("=" * 60)
    
    # 创建测试实例
    tester = DatabaseUpgradeTestCorrected()
    
    # 运行所有测试
    success = tester.run_all_tests()
    
    # 退出码
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()