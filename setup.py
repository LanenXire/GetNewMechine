import os
import sys
from PIL import Image
import subprocess

def convert_png_to_ico(png_path, ico_path):
    """将PNG图像转换为ICO格式"""
    try:
        img = Image.open(png_path)
        img.save(ico_path)
        print(f"成功将 {png_path} 转换为 {ico_path}")
        return True
    except Exception as e:
        print(f"转换图标失败: {str(e)}")
        return False

def create_admin_launcher():
    """创建请求管理员权限的启动器"""
    with open("admin_launcher.py", "w") as f:
        f.write("""import ctypes, sys

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()

import machine_code_manager
if __name__ == "__main__":
    root = machine_code_manager.tk.Tk()
    app = machine_code_manager.MachineCodeManager(root)
    root.mainloop()
""")
    return os.path.abspath("admin_launcher.py")

def main():
    # 检查是否安装了所需的库
    required_packages = ["pyinstaller", "pillow"]
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            print(f"正在安装 {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    
    # 定义输入和输出路径
    png_icon = "ComfyUI_temp_ieyiv_00007_.png"
    ico_icon = "icon.ico"
    
    # 检查PNG图标是否存在
    if not os.path.exists(png_icon):
        print(f"错误: 找不到图标文件 {png_icon}")
        return
    
    # 转换图标
    if not convert_png_to_ico(png_icon, ico_icon):
        return
    
    # 创建管理员权限启动器
    launcher = create_admin_launcher()
    
    # 构建PyInstaller命令
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--uac-admin",  # 请求管理员权限
        f"--icon={ico_icon}",
        "--name=机器码管理器",
        "--add-data", f"{ico_icon};.",
        launcher  # 使用管理员权限启动器
    ]
    
    # 执行PyInstaller命令
    print("开始打包应用程序...")
    subprocess.call(cmd)
    
    print("\n打包完成！")
    print("打包后的可执行文件位于 dist 目录中。")

if __name__ == "__main__":
    main() 