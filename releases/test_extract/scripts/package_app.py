#!/usr/bin/env python3
"""
MSearch 应用程序打包脚本
将应用程序打包到 releases 目录
"""

import os
import sys
import shutil
import zipfile
import tarfile
import json
from datetime import datetime
from pathlib import Path


def create_package():
    """创建应用程序包"""
    # 获取项目根目录
    project_root = Path(__file__).parent.parent
    releases_dir = project_root / "releases"
    temp_dir = project_root / "temp_package"
    
    # 创建 releases 目录
    releases_dir.mkdir(exist_ok=True)
    
    # 创建临时目录用于打包
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir()
    
    try:
        # 要复制的目录和文件
        items_to_copy = [
            "src",
            "config",
            "scripts",
            "docs",
            "examples",
            "requirements.txt",
            "requirements-dev.txt",
            "requirements-test.txt",
            "README.md",
            "IFLOW.md",
            ".gitignore"
        ]
        
        # 复制项目文件到临时目录
        for item in items_to_copy:
            source = project_root / item
            destination = temp_dir / item
            
            if source.exists():
                if source.is_dir():
                    shutil.copytree(source, destination)
                else:
                    shutil.copy2(source, destination)
                print(f"已复制: {item}")
            else:
                print(f"警告: {item} 不存在，跳过")
        
        # 创建版本信息文件
        version_info = {
            "version": "1.0.0",
            "build_date": datetime.now().isoformat(),
            "package_type": "source",
            "description": "MSearch 多模态检索系统源码包"
        }
        
        version_file = temp_dir / "VERSION.json"
        with open(version_file, 'w', encoding='utf-8') as f:
            json.dump(version_info, f, indent=2, ensure_ascii=False)
        
        print(f"已创建版本信息文件: {version_file}")
        
        # 创建打包日期戳
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 创建ZIP包
        zip_filename = releases_dir / f"msearch_{timestamp}.zip"
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(temp_dir)
                    zipf.write(file_path, arcname)
        
        print(f"已创建ZIP包: {zip_filename}")
        
        # 创建TAR.GZ包
        tar_filename = releases_dir / f"msearch_{timestamp}.tar.gz"
        with tarfile.open(tar_filename, "w:gz") as tar:
            for item in temp_dir.iterdir():
                tar.add(item, arcname=item.name)
        
        print(f"已创建TAR.GZ包: {tar_filename}")
        
        # 创建最新版本符号链接
        latest_zip = releases_dir / "msearch_latest.zip"
        latest_tar = releases_dir / "msearch_latest.tar.gz"
        
        if latest_zip.exists():
            latest_zip.unlink()
        if latest_tar.exists():
            latest_tar.unlink()
            
        # 在Windows上需要复制文件而不是创建符号链接
        shutil.copy2(zip_filename, latest_zip)
        shutil.copy2(tar_filename, latest_tar)
        
        print(f"已创建最新版本链接")
        
        # 获取包大小信息
        zip_size = zip_filename.stat().st_size
        tar_size = tar_filename.stat().st_size
        
        print(f"ZIP包大小: {zip_size / (1024*1024):.2f} MB")
        print(f"TAR.GZ包大小: {tar_size / (1024*1024):.2f} MB")
        
        # 复制安装脚本和README到临时目录
        install_sh = project_root / "releases" / "install.sh"
        install_bat = project_root / "releases" / "install.bat"
        readme_md = project_root / "releases" / "README.md"
        release_notes = project_root / "releases" / "RELEASE_NOTES.md"
        
        additional_files = [
            (install_sh, "install.sh"),
            (install_bat, "install.bat"),
            (readme_md, "README.md"),
            (release_notes, "RELEASE_NOTES.md")
        ]
        
        for source_file, dest_name in additional_files:
            if source_file.exists():
                shutil.copy2(source_file, temp_dir / dest_name)
                print(f"已复制: {dest_name}")
        
        # 创建打包信息文件
        package_info = {
            "timestamp": timestamp,
            "zip_filename": zip_filename.name,
            "tar_filename": tar_filename.name,
            "zip_size_mb": round(zip_size / (1024*1024), 2),
            "tar_size_mb": round(tar_size / (1024*1024), 2),
            "version": "1.0.0"
        }
        
        info_file = releases_dir / "package_info.json"
        with open(info_file, 'w', encoding='utf-8') as f:
            json.dump(package_info, f, indent=2, ensure_ascii=False)
        
        print(f"已创建打包信息文件: {info_file}")
        
        print(f"\n打包完成! 文件已保存到: {releases_dir}")
        print(f"ZIP包: {zip_filename.name}")
        print(f"TAR.GZ包: {tar_filename.name}")
        
    finally:
        # 清理临时目录
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
            print(f"已清理临时目录: {temp_dir}")


def main():
    """主函数"""
    print("MSearch 应用程序打包工具")
    print("=" * 40)
    
    try:
        create_package()
        print("\n✓ 打包成功完成!")
        return 0
    except Exception as e:
        print(f"\n✗ 打包失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())