import ctypes, sys

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
