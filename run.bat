@echo off
echo 机器码管理器 - 运行脚本
echo =============================================

echo 正在检查Python环境...
python --version
if %ERRORLEVEL% neq 0 (
    echo 错误: 未找到Python，请安装Python 3.6或更高版本。
    pause
    exit /b 1
)

echo.
echo 正在安装依赖...
pip install pillow
if %ERRORLEVEL% neq 0 (
    echo 警告: 安装依赖失败，程序可能无法正常运行。
)

echo.
echo 正在启动机器码管理器...
python machine_code_manager.py
if %ERRORLEVEL% neq 0 (
    echo 错误: 程序运行失败。
    pause
    exit /b 1
)

exit /b 0 