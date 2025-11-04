"""
媒体预处理系统集成测试
测试整个媒体预处理系统的端到端功能
"""
import os
import unittest
import asyncio
import tempfile
import shutil
import json
from pathlib import Path

from src.processors.media_preprocessing_system import get_media_preprocessing_system
from src.core.config_manager import get_config_manager


class TestMediaPreprocessingSystemIntegration(unittest.TestCase):
    """媒体预处理系统集成测试类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp()
        
        # 创建测试文件
        self.create_test_files()
        
        # 获取媒体预处理系统实例
        self.system = get_media_preprocessing_system()
    
    def tearDown(self):
        """测试后清理"""
        # 删除临时目录
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_files(self):
        """创建测试文件"""
        # 创建测试图像文件
        self.test_image = os.path.join(self.temp_dir, 'test_image.jpg')
        self.create_test_image(self.test_image)
        
        # 创建测试视频文件
        self.test_video = os.path.join(self.temp_dir, 'test_video.mp4')
        self.create_test_video(self.test_video)
        
        # 创建测试音频文件
        self.test_audio = os.path.join(self.temp_dir, 'test_audio.mp3')
        self.create_test_audio(self.test_audio)
        
        # 创建测试文本文件
        self.test_text = os.path.join(self.temp_dir, 'test_text.txt')
        self.create_test_text(self.test_text)
    
    def create_test_image(self, file_path):
        """创建测试图像文件"""
        try:
            from PIL import Image
            # 创建一个简单的RGB图像
            img = Image.new('RGB', (640, 480), color='red')
            img.save(file_path, 'JPEG')
        except ImportError:
            # 如果PIL不可用，创建一个假的图像文件
            with open(file_path, 'wb') as f:
                f.write(b'fake_image_data')
    
    def create_test_video(self, file_path):
        """创建测试视频文件"""
        # 创建一个假的视频文件
        with open(file_path, 'wb') as f:
            f.write(b'fake_video_data')
    
    def create_test_audio(self, file_path):
        """创建测试音频文件"""
        # 创建一个假的音频文件
        with open(file_path, 'wb') as f:
            f.write(b'fake_audio_data')
    
    def create_test_text(self, file_path):
        """创建测试文本文件"""
        # 创建一个测试文本文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("这是一个测试文本文件。\n")
            f.write("This is a test text file.\n")
            f.write("包含中文和英文内容。\n")
    
    async def test_process_image_integration(self):
        """测试图像处理集成"""
        # 处理图像文件
        result = await self.system.process_file(self.test_image)
        
        # 验证结果
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['file_path'], self.test_image)
        self.assertEqual(result['file_type'], 'image')
        
        # 验证元数据
        self.assertIn('metadata', result)
        metadata = result['metadata']
        self.assertEqual(metadata['file_path'], self.test_image)
        self.assertEqual(metadata['file_type'], 'image')
        self.assertIn('file_size', metadata)
        
        # 验证处理结果
        self.assertIn('data', result)
        data = result['data']
        self.assertEqual(data['status'], 'success')
        self.assertIn('image_data', data)
        self.assertIn('width', data)
        self.assertIn('height', data)
    
    async def test_process_video_integration(self):
        """测试视频处理集成"""
        # 处理视频文件
        result = await self.system.process_file(self.test_video)
        
        # 验证结果
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['file_path'], self.test_video)
        self.assertEqual(result['file_type'], 'video')
        
        # 验证元数据
        self.assertIn('metadata', result)
        metadata = result['metadata']
        self.assertEqual(metadata['file_path'], self.test_video)
        self.assertEqual(metadata['file_type'], 'video')
        self.assertIn('file_size', metadata)
        
        # 验证处理结果
        self.assertIn('data', result)
        data = result['data']
        self.assertEqual(data['status'], 'success')
        self.assertIn('video_data', data)
    
    async def test_process_audio_integration(self):
        """测试音频处理集成"""
        # 处理音频文件
        result = await self.system.process_file(self.test_audio)
        
        # 验证结果
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['file_path'], self.test_audio)
        self.assertEqual(result['file_type'], 'audio')
        
        # 验证元数据
        self.assertIn('metadata', result)
        metadata = result['metadata']
        self.assertEqual(metadata['file_path'], self.test_audio)
        self.assertEqual(metadata['file_type'], 'audio')
        self.assertIn('file_size', metadata)
        
        # 验证处理结果
        self.assertIn('data', result)
        data = result['data']
        self.assertEqual(data['status'], 'success')
        self.assertIn('audio_data', data)
    
    async def test_process_text_integration(self):
        """测试文本处理集成"""
        # 处理文本文件
        result = await self.system.process_file(self.test_text)
        
        # 验证结果
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['file_path'], self.test_text)
        self.assertEqual(result['file_type'], 'text')
        
        # 验证元数据
        self.assertIn('metadata', result)
        metadata = result['metadata']
        self.assertEqual(metadata['file_path'], self.test_text)
        self.assertEqual(metadata['file_type'], 'text')
        self.assertIn('file_size', metadata)
        
        # 验证处理结果
        self.assertIn('data', result)
        data = result['data']
        self.assertEqual(data['status'], 'success')
        self.assertIn('text_data', data)
        self.assertIn('content', data)
        self.assertIn('encoding', data)
    
    async def test_batch_process_files_integration(self):
        """测试批量处理文件集成"""
        # 准备文件列表
        file_paths = [self.test_image, self.test_video, self.test_audio, self.test_text]
        
        # 批量处理文件
        results = await self.system.batch_process_files(file_paths)
        
        # 验证结果
        self.assertEqual(len(results), 4)
        
        # 验证每个结果
        for i, result in enumerate(results):
            self.assertEqual(result['status'], 'success')
            self.assertEqual(result['file_path'], file_paths[i])
            self.assertIn('file_type', result)
            self.assertIn('metadata', result)
            self.assertIn('data', result)
    
    async def test_file_validation_integration(self):
        """测试文件验证集成"""
        # 验证图像文件
        result = self.system.validate_file(self.test_image)
        self.assertTrue(result['valid'])
        self.assertEqual(result['file_type'], 'image')
        
        # 验证视频文件
        result = self.system.validate_file(self.test_video)
        self.assertTrue(result['valid'])
        self.assertEqual(result['file_type'], 'video')
        
        # 验证音频文件
        result = self.system.validate_file(self.test_audio)
        self.assertTrue(result['valid'])
        self.assertEqual(result['file_type'], 'audio')
        
        # 验证文本文件
        result = self.system.validate_file(self.test_text)
        self.assertTrue(result['valid'])
        self.assertEqual(result['file_type'], 'text')
        
        # 验证不存在的文件
        non_existent_file = os.path.join(self.temp_dir, 'non_existent.jpg')
        result = self.system.validate_file(non_existent_file)
        self.assertFalse(result['valid'])
        self.assertIn("文件不存在", result['errors'][0])
    
    async def test_error_handling_integration(self):
        """测试错误处理集成"""
        # 测试处理不存在的文件
        non_existent_file = os.path.join(self.temp_dir, 'non_existent.jpg')
        result = await self.system.process_file(non_existent_file)
        
        # 验证错误处理
        self.assertEqual(result['status'], 'error')
        self.assertIn('error', result)
        self.assertEqual(result['file_path'], non_existent_file)
        
        # 测试处理不支持的文件类型
        unknown_file = os.path.join(self.temp_dir, 'test.xyz')
        with open(unknown_file, 'wb') as f:
            f.write(b'')
        
        result = await self.system.process_file(unknown_file)
        self.assertEqual(result['status'], 'error')
        self.assertIn('error', result)
        self.assertEqual(result['file_path'], unknown_file)
    
    async def test_configuration_integration(self):
        """测试配置集成"""
        # 获取配置管理器
        config_manager = get_config_manager()
        
        # 验证媒体处理配置
        media_processing_config = config_manager.get('media_processing', {})
        self.assertIn('max_file_size', media_processing_config)
        self.assertIn('temp_dir', media_processing_config)
        self.assertIn('max_workers', media_processing_config)
        
        # 验证图像处理配置
        image_processing_config = config_manager.get('image_processing', {})
        self.assertIn('target_size', image_processing_config)
        self.assertIn('max_resolution', image_processing_config)
        self.assertIn('quality_threshold', image_processing_config)
        
        # 验证视频处理配置
        video_processing_config = config_manager.get('video_processing', {})
        self.assertIn('target_size', video_processing_config)
        self.assertIn('max_resolution', video_processing_config)
        self.assertIn('target_fps', video_processing_config)
        
        # 验证音频处理配置
        audio_processing_config = config_manager.get('audio_processing', {})
        self.assertIn('target_sample_rate', audio_processing_config)
        self.assertIn('target_channels', audio_processing_config)
        self.assertIn('segment_duration', audio_processing_config)
        
        # 验证文本处理配置
        text_processing_config = config_manager.get('text_processing', {})
        self.assertIn('max_file_size', text_processing_config)
        self.assertIn('encoding_priority', text_processing_config)
    
    async def test_performance_integration(self):
        """测试性能集成"""
        import time
        
        # 测试单个文件处理性能
        start_time = time.time()
        result = await self.system.process_file(self.test_image)
        end_time = time.time()
        
        # 验证处理时间和结果
        self.assertEqual(result['status'], 'success')
        processing_time = end_time - start_time
        self.assertLess(processing_time, 10.0)  # 处理时间应小于10秒
        
        # 测试批量处理性能
        file_paths = [self.test_image, self.test_video, self.test_audio, self.test_text]
        start_time = time.time()
        results = await self.system.batch_process_files(file_paths)
        end_time = time.time()
        
        # 验证处理时间和结果
        self.assertEqual(len(results), 4)
        for result in results:
            self.assertEqual(result['status'], 'success')
        
        batch_processing_time = end_time - start_time
        self.assertLess(batch_processing_time, 30.0)  # 批量处理时间应小于30秒


class TestMediaPreprocessingSystemEndToEnd(unittest.TestCase):
    """媒体预处理系统端到端测试类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp()
        
        # 创建测试数据集
        self.create_test_dataset()
        
        # 获取媒体预处理系统实例
        self.system = get_media_preprocessing_system()
    
    def tearDown(self):
        """测试后清理"""
        # 删除临时目录
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_dataset(self):
        """创建测试数据集"""
        # 创建测试目录结构
        self.dataset_dir = os.path.join(self.temp_dir, 'test_dataset')
        os.makedirs(self.dataset_dir, exist_ok=True)
        
        # 创建子目录
        self.image_dir = os.path.join(self.dataset_dir, 'images')
        self.video_dir = os.path.join(self.dataset_dir, 'videos')
        self.audio_dir = os.path.join(self.dataset_dir, 'audio')
        self.text_dir = os.path.join(self.dataset_dir, 'texts')
        
        for dir_path in [self.image_dir, self.video_dir, self.audio_dir, self.text_dir]:
            os.makedirs(dir_path, exist_ok=True)
        
        # 创建测试文件
        self.test_files = []
        
        # 创建图像文件
        for i in range(3):
            file_path = os.path.join(self.image_dir, f'image_{i}.jpg')
            self.create_test_image(file_path)
            self.test_files.append(file_path)
        
        # 创建视频文件
        for i in range(2):
            file_path = os.path.join(self.video_dir, f'video_{i}.mp4')
            self.create_test_video(file_path)
            self.test_files.append(file_path)
        
        # 创建音频文件
        for i in range(2):
            file_path = os.path.join(self.audio_dir, f'audio_{i}.mp3')
            self.create_test_audio(file_path)
            self.test_files.append(file_path)
        
        # 创建文本文件
        for i in range(3):
            file_path = os.path.join(self.text_dir, f'text_{i}.txt')
            self.create_test_text(file_path)
            self.test_files.append(file_path)
    
    def create_test_image(self, file_path):
        """创建测试图像文件"""
        try:
            from PIL import Image
            # 创建一个简单的RGB图像
            img = Image.new('RGB', (640, 480), color='red')
            img.save(file_path, 'JPEG')
        except ImportError:
            # 如果PIL不可用，创建一个假的图像文件
            with open(file_path, 'wb') as f:
                f.write(b'fake_image_data')
    
    def create_test_video(self, file_path):
        """创建测试视频文件"""
        # 创建一个假的视频文件
        with open(file_path, 'wb') as f:
            f.write(b'fake_video_data')
    
    def create_test_audio(self, file_path):
        """创建测试音频文件"""
        # 创建一个假的音频文件
        with open(file_path, 'wb') as f:
            f.write(b'fake_audio_data')
    
    def create_test_text(self, file_path):
        """创建测试文本文件"""
        # 创建一个测试文本文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"这是测试文本文件 {Path(file_path).stem}。\n")
            f.write("This is a test text file.\n")
            f.write("包含中文和英文内容。\n")
    
    async def test_end_to_end_processing(self):
        """测试端到端处理"""
        # 批量处理所有文件
        results = await self.system.batch_process_files(self.test_files)
        
        # 验证处理结果
        self.assertEqual(len(results), len(self.test_files))
        
        # 统计各类型文件处理结果
        image_count = sum(1 for r in results if r.get('file_type') == 'image' and r.get('status') == 'success')
        video_count = sum(1 for r in results if r.get('file_type') == 'video' and r.get('status') == 'success')
        audio_count = sum(1 for r in results if r.get('file_type') == 'audio' and r.get('status') == 'success')
        text_count = sum(1 for r in results if r.get('file_type') == 'text' and r.get('status') == 'success')
        
        # 验证各类型文件处理数量
        self.assertEqual(image_count, 3)
        self.assertEqual(video_count, 2)
        self.assertEqual(audio_count, 2)
        self.assertEqual(text_count, 3)
        
        # 验证所有文件都处理成功
        success_count = sum(1 for r in results if r.get('status') == 'success')
        self.assertEqual(success_count, len(self.test_files))
        
        # 验证每个结果都包含必要的字段
        for result in results:
            self.assertIn('file_path', result)
            self.assertIn('file_type', result)
            self.assertIn('metadata', result)
            self.assertIn('data', result)
            self.assertIn('processing_timestamp', result)
    
    async def test_end_to_end_error_handling(self):
        """测试端到端错误处理"""
        # 添加一个不存在的文件到文件列表
        non_existent_file = os.path.join(self.temp_dir, 'non_existent.jpg')
        test_files_with_error = self.test_files + [non_existent_file]
        
        # 批量处理文件
        results = await self.system.batch_process_files(test_files_with_error)
        
        # 验证处理结果
        self.assertEqual(len(results), len(test_files_with_error))
        
        # 统计成功和失败的文件数量
        success_count = sum(1 for r in results if r.get('status') == 'success')
        error_count = sum(1 for r in results if r.get('status') == 'error')
        
        # 验证错误处理
        self.assertEqual(success_count, len(self.test_files))
        self.assertEqual(error_count, 1)
        
        # 验证错误信息
        error_result = next(r for r in results if r.get('status') == 'error')
        self.assertEqual(error_result['file_path'], non_existent_file)
        self.assertIn('error', error_result)
    
    async def test_end_to_end_performance(self):
        """测试端到端性能"""
        import time
        
        # 记录开始时间
        start_time = time.time()
        
        # 批量处理所有文件
        results = await self.system.batch_process_files(self.test_files)
        
        # 记录结束时间
        end_time = time.time()
        
        # 计算处理时间
        total_time = end_time - start_time
        
        # 验证处理结果
        self.assertEqual(len(results), len(self.test_files))
        success_count = sum(1 for r in results if r.get('status') == 'success')
        self.assertEqual(success_count, len(self.test_files))
        
        # 验证处理时间
        self.assertLess(total_time, 60.0)  # 总处理时间应小于60秒
        
        # 计算平均处理时间
        avg_time_per_file = total_time / len(self.test_files)
        self.assertLess(avg_time_per_file, 10.0)  # 平均每个文件处理时间应小于10秒


# 运行测试
if __name__ == '__main__':
    # 创建测试套件
    suite = unittest.TestSuite()
    
    # 添加测试用例
    suite.addTest(unittest.makeSuite(TestMediaPreprocessingSystemIntegration))
    suite.addTest(unittest.makeSuite(TestMediaPreprocessingSystemEndToEnd))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出测试结果
    if result.wasSuccessful():
        print("所有集成测试通过!")
    else:
        print(f"测试失败: {len(result.failures)} 个失败, {len(result.errors)} 个错误")
        for test, traceback in result.failures + result.errors:
            print(f"失败测试: {test}")
            print(traceback)