@echo off
echo 机器码管理器 - 构建脚本
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
pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo 错误: 安装依赖失败，请检查网络连接或手动安装依赖。
    pause
    exit /b 1
)

echo.
echo 正在创建请求管理员权限的启动器...
echo import ctypes, sys > admin_launcher.py
echo. >> admin_launcher.py
echo def is_admin(): >> admin_launcher.py
echo     try: >> admin_launcher.py
echo         return ctypes.windll.shell32.IsUserAnAdmin() >> admin_launcher.py
echo     except: >> admin_launcher.py
echo         return False >> admin_launcher.py
echo. >> admin_launcher.py
echo if not is_admin(): >> admin_launcher.py
echo     ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1) >> admin_launcher.py
echo     sys.exit() >> admin_launcher.py
echo. >> admin_launcher.py
echo import machine_code_manager >> admin_launcher.py
echo if __name__ == "__main__": >> admin_launcher.py
echo     root = machine_code_manager.tk.Tk() >> admin_launcher.py
echo     app = machine_code_manager.MachineCodeManager(root) >> admin_launcher.py
echo     root.mainloop() >> admin_launcher.py

echo.
echo 正在运行打包脚本...
python setup.py
if %ERRORLEVEL% neq 0 (
    echo 错误: 打包应用程序失败。
    pause
    exit /b 1
)

echo.
echo 构建完成！打包后的应用程序位于dist目录中。
echo.
echo 按任意键打开dist目录...
pause > nul
start dist 