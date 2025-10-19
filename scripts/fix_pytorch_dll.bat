@echo off
setlocal enabledelayedexpansion

REM =====================================
REM PyTorch DLL 问题修复脚本 - Windows专用
REM 更新时间: 2025-10-21
REM =====================================

echo ====================================================
echo 🛠️  PyTorch DLL 问题修复工具 v1.0
set "script_dir=%~dp0"
set "project_root=%script_dir%.."
set "project_root=%project_root:\=/%"

REM 设置输出编码为UTF-8
chcp 65001 > nul

REM 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误: 未检测到Python，请先安装Python 3.9或更高版本
    pause
    exit /b 1
)

echo ✅ 检测到Python环境

REM 创建Python修复脚本
set "py_fix_script=%TEMP%\fix_pytorch_dll_temp.py"

echo 创建临时修复脚本...
( 
  echo import sys
  echo import os
  echo import subprocess
  echo import site
  echo import importlib
  echo 
  echo def check_pytorch_installation():
  echo     try:
  echo         import torch
  echo         print(f'✅ 已安装PyTorch版本: {torch.__version__}')
  echo         return True
  echo     except ImportError as e:
  echo         print(f'❌ 未安装PyTorch或导入错误: {e}')
  echo         return False
  echo     except Exception as e:
  echo         print(f'⚠️ PyTorch导入异常: {e}')
  echo         return False
  echo 
  echo def fix_pytorch_installation():
  echo     print('🔄 开始修复PyTorch安装...')
  echo     
  echo     # 先卸载现有PyTorch
  echo     try:
  echo         print('📦 清理现有PyTorch安装...')
  echo         subprocess.check_call([sys.executable, '-m', 'pip', 'uninstall', '-y', 'torch', 'torchvision', 'torchaudio'])
  echo     except Exception as e:
  echo         print(f'⚠️ 卸载PyTorch时出现警告: {e}')
  echo     
  echo     # 安装兼容的CPU版本PyTorch（稳定性优先）
  echo     print('📥 安装兼容的CPU版本PyTorch...')
  echo     try:
  echo         # 使用清华大学镜像加速下载
  echo         subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'torch', 'torchvision', '--index-url', 'https://download.pytorch.org/whl/cpu'])
  echo         print('✅ PyTorch安装成功')
  echo         return True
  echo     except Exception as e:
  echo         print(f'❌ PyTorch安装失败: {e}')
  echo         print('🔄 尝试备用安装方式...')
  echo         try:
  echo             # 尝试使用国内镜像
  echo             subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'torch', 'torchvision', '-i', 'https://pypi.tuna.tsinghua.edu.cn/simple'])
  echo             print('✅ PyTorch备用安装成功')
  echo             return True
  echo         except Exception as e2:
  echo             print(f'❌ PyTorch备用安装也失败: {e2}')
  echo             return False
  echo 
  echo def fix_dll_issues():
  echo     print('🔍 修复Windows DLL加载问题...')
  echo     
  echo     # 获取site-packages路径
  echo     site_packages_path = site.getsitepackages()[0]
  echo     print(f'📁 Python包路径: {site_packages_path}')
  echo     
  echo     # 添加环境变量配置文件
  echo     print('📝 生成环境变量配置文件...')
  echo     env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pytorch_fix_env.bat')
  echo     
  echo     with open(env_file, 'w', encoding='utf-8') as f:
  echo         f.write(f'@echo off\n')
  echo         f.write(f'REM PyTorch环境变量修复配置\n')
  echo         f.write(f'REM 请在运行程序前执行此文件\n')
  echo         f.write(f'set "PYTHONPATH={site_packages_path};%PYTHONPATH%"\n')
  echo         f.write(f'set "KMP_DUPLICATE_LIB_OK=TRUE"\n')
  echo         f.write(f'set "CUDA_LAUNCH_BLOCKING=1"\n')
  echo         f.write(f'set "PATH={site_packages_path}\torch\lib;%PATH%"\n')
  echo     
  echo     print(f'✅ 环境变量配置文件已生成: {env_file}')
  echo     return env_file
  echo 
  echo def create_registry_fix():
  echo     print('🔧 创建注册表修复脚本...')
  echo     reg_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fix_pytorch_dll.reg')
  echo     
  echo     with open(reg_file, 'w', encoding='utf-8') as f:
  echo         f.write('Windows Registry Editor Version 5.00\n\n')
  echo         f.write('[HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Environment]\n')
  echo         f.write('"KMP_DUPLICATE_LIB_OK"="TRUE"\n')
  echo     
  echo     print(f'✅ 注册表修复脚本已生成: {reg_file}')
  echo     print('📌 提示: 您可以根据需要手动运行此注册表文件')
  echo     return reg_file
  echo 
  echo def main():
  echo     print('🚀 PyTorch DLL问题修复程序启动')
  echo     print('=' * 50)
  echo     
  echo     # 首先升级pip
  echo     print('🔄 升级pip...')
  echo     try:
  echo         subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'])
  echo     except Exception as e:
  echo         print(f'⚠️ pip升级警告: {e}')
  echo     
  echo     # 检查并修复PyTorch安装
  echo     pytorch_installed = check_pytorch_installation()
  echo     if not pytorch_installed:
  echo         fix_pytorch_installation()
  echo     
  echo     # 修复DLL问题
  echo     env_file = fix_dll_issues()
  echo     reg_file = create_registry_fix()
  echo     
  echo     print('=' * 50)
  echo     print('✅ 修复完成!')
  echo     print('📋 后续步骤:')
  echo     print(f'1. 运行生成的环境配置文件: {env_file}')
  echo     print('2. 如果仍然遇到DLL问题，可以尝试运行注册表修复文件')
  echo     print('3. 重启终端或IDE以应用环境变量更改')
  echo     print('4. 重新运行您的程序或测试')
  echo     print('=' * 50)
  echo 
  echo if __name__ == '__main__':
  echo     main()
) > "%py_fix_script%"

REM 运行Python修复脚本
echo 🔄 执行修复程序...
python "%py_fix_script%"

REM 创建永久环境变量设置脚本
set "perm_fix_script=%script_dir%\set_pytorch_env_permanently.bat"
(
  echo @echo off
  echo REM =====================================
  echo REM PyTorch永久环境变量设置脚本
  echo REM 更新时间: 2025-10-21
  echo REM =====================================
  echo 
  echo setlocal enabledelayedexpansion
  echo echo 🛠️ 设置PyTorch永久环境变量
  echo echo =====================================
  echo 
  echo REM 创建PowerShell脚本来永久设置环境变量
  echo set "ps_script=%TEMP%\set_pytorch_env.ps1"
  echo 
  echo ^( 
  echo   echo Write-Host "正在设置永久环境变量..."
  echo   echo 
  echo   echo # 设置KMP_DUPLICATE_LIB_OK环境变量
  echo   echo [System.Environment]::SetEnvironmentVariable^('KMP_DUPLICATE_LIB_OK', 'TRUE', [System.EnvironmentVariableTarget]::Machine^)
  echo   echo Write-Host "✅ KMP_DUPLICATE_LIB_OK = TRUE"
  echo   echo 
  echo   echo # 设置CUDA_LAUNCH_BLOCKING环境变量
  echo   echo [System.Environment]::SetEnvironmentVariable^('CUDA_LAUNCH_BLOCKING', '1', [System.EnvironmentVariableTarget]::Machine^)
  echo   echo Write-Host "✅ CUDA_LAUNCH_BLOCKING = 1"
  echo   echo 
  echo   echo Write-Host "=" * 50
  echo   echo Write-Host "✅ 永久环境变量设置完成!"
  echo   echo Write-Host "📋 请重启计算机以应用这些更改"
  echo ^) ^> "!ps_script!"
  echo 
  echo REM 使用管理员权限运行PowerShell脚本
  echo echo 📢 请以管理员身份运行此脚本以设置永久环境变量
  echo echo 📢 即将启动PowerShell配置窗口...
  echo echo =====================================
  echo pause
  echo powershell -Command "Start-Process powershell -ArgumentList '-ExecutionPolicy Bypass -File !ps_script!' -Verb RunAs"
) > "%perm_fix_script%"

echo 📋 其他可用工具:
echo - 永久环境变量设置脚本: %perm_fix_script%
echo - 运行方式: 右键点击并选择"以管理员身份运行"

echo ====================================================
echo 🎉 PyTorch DLL修复工具执行完成
echo 📌 重要提示: 建议重新启动计算机以确保所有更改生效
pause
endlocal
