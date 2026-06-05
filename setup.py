import os
import sys
import shutil
import subprocess
import winreg

# Bootstrap dependencies first!
def bootstrap():
    project_root = os.path.dirname(os.path.abspath(__file__))
    venv_dir = os.path.join(project_root, ".venv")
    site_packages = os.path.join(venv_dir, "Lib", "site-packages")
    
    # Ensure site-packages directory exists
    os.makedirs(site_packages, exist_ok=True)
    
    # Add it to sys.path immediately
    sys.path.insert(0, site_packages)
    
    try:
        import customtkinter as ctk
        import pystray
        import PIL
        import plyer
    except ImportError:
        print("==========================================================")
        print("   PingBro Setup: Preparing installation dependencies... ")
        print("   Please wait, this will only take a moment.             ")
        print("==========================================================")
        print()
        
        req_file = os.path.join(project_root, "requirements.txt")
        if not os.path.exists(req_file):
            with open(req_file, "w") as f:
                f.write("customtkinter>=5.2.0\npystray>=0.19.5\nPillow>=10.0.0\nplyer>=2.1.0\n")
                
        try:
            cmd = [
                sys.executable, "-m", "pip", "install", 
                "--target", site_packages, 
                "-r", req_file
            ]
            subprocess.run(cmd, check=True)
            print()
            print("Dependencies successfully installed!")
            print("Launching Setup Wizard GUI...")
            print()
        except Exception as e:
            print()
            print(f"Error installing dependencies: {e}")
            print("Attempting to run Setup Wizard anyway...")
            print()

bootstrap()
import customtkinter as ctk

def get_powershell_exe():
    system_root = os.environ.get("SystemRoot", "C:\\Windows")
    powershell_exe = os.path.join(system_root, "System32", "WindowsPowerShell", "v1.0", "powershell.exe")
    if os.path.exists(powershell_exe):
        return powershell_exe
    return "powershell"

class SetupWizard(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("PingBro Setup Wizard")
        self.geometry("520x350")
        self.resizable(False, False)

        # Set appearance to dark mode matching PingBro
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        # Define standard directories
        self.install_dir = os.path.join(os.environ["LOCALAPPDATA"], "PingBro")
        self.target_exe = os.path.join(self.install_dir, "PingBro.exe")
        self.shortcut_path = os.path.join(
            os.environ["APPDATA"], "Microsoft", "Windows", "Start Menu", "Programs", "PingBro.lnk"
        )

        # Frame container
        self.main_frame = ctk.CTkFrame(self, fg_color="#141417", corner_radius=0)
        self.main_frame.pack(fill="both", expand=True)

        self.show_welcome_screen()

    def show_welcome_screen(self):
        self.clear_frame()

        # Header Title
        title_lbl = ctk.CTkLabel(
            self.main_frame, text="Install PingBro", font=("Helvetica", 24, "bold"), text_color="#00adb5"
        )
        title_lbl.pack(pady=(40, 10))

        # Description
        desc_lbl = ctk.CTkLabel(
            self.main_frame,
            text="PingBro will be installed to your computer.\nThis will place the application in your local apps folder,\ncreate a Start Menu shortcut, and enable Windows Settings integration.",
            font=("Helvetica", 13),
            text_color="#a0a0a5",
            justify="center"
        )
        desc_lbl.pack(pady=20)

        # Destination Info
        dest_lbl = ctk.CTkLabel(
            self.main_frame,
            text=f"Install location: {self.install_dir}",
            font=("Helvetica", 11, "italic"),
            text_color="#606065"
        )
        dest_lbl.pack(pady=(0, 20))

        # Action Buttons Frame
        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.pack(side="bottom", fill="x", padx=30, pady=25)

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Cancel",
            width=100,
            fg_color="#2b2b30",
            hover_color="#3e3e45",
            text_color="#ffffff",
            command=self.destroy
        )
        cancel_btn.pack(side="left")

        install_btn = ctk.CTkButton(
            btn_frame,
            text="Install",
            width=120,
            fg_color="#00adb5",
            hover_color="#008c95",
            text_color="#ffffff",
            font=("Helvetica", 12, "bold"),
            command=self.start_installation
        )
        install_btn.pack(side="right")

    def start_installation(self):
        self.clear_frame()

        # Title
        title_lbl = ctk.CTkLabel(
            self.main_frame, text="Installing PingBro...", font=("Helvetica", 20, "bold"), text_color="#00adb5"
        )
        title_lbl.pack(pady=(50, 20))

        # Progress Bar
        self.prog_bar = ctk.CTkProgressBar(self.main_frame, width=380, progress_color="#00adb5")
        self.prog_bar.pack(pady=10)
        self.prog_bar.set(0)

        # Status Label
        self.status_lbl = ctk.CTkLabel(
            self.main_frame, text="Preparing installation...", font=("Helvetica", 12), text_color="#a0a0a5"
        )
        self.status_lbl.pack(pady=10)

        # Run installation in after() calls to keep UI responsive
        self.after(500, lambda: self.step_copy_exe())

    def step_copy_exe(self):
        try:
            self.status_lbl.configure(text="Creating directory and copying application binary...")
            self.prog_bar.set(0.2)

            os.makedirs(self.install_dir, exist_ok=True)

            if getattr(sys, 'frozen', False):
                # Determine where PingBro.exe is packaged in temp folder
                source_exe = os.path.join(getattr(sys, '_MEIPASS', '.'), 'PingBro.exe')

                if not os.path.exists(source_exe):
                    # Fallback to current folder if setup runs uncompiled
                    source_exe = "PingBro.exe"

                if not os.path.exists(source_exe):
                    raise FileNotFoundError("Could not find packaged PingBro.exe resource.")

                # Stop any running processes to prevent file locking
                try:
                    subprocess.run(["taskkill", "/F", "/IM", "PingBro.exe"], capture_output=True)
                except Exception:
                    pass

                shutil.copy2(source_exe, self.target_exe)
            else:
                # source mode: copy folders and files
                source_dir = os.path.dirname(os.path.abspath(__file__))
                
                # Stop any running processes to prevent file locking
                try:
                    subprocess.run(["taskkill", "/F", "/IM", "PingBro.exe"], capture_output=True)
                except Exception:
                    pass
                try:
                    powershell_cmd = f"Get-CimInstance Win32_Process -Filter 'CommandLine LIKE ''%%main.py%%%%'' AND ProcessId <> {os.getpid()}' | Invoke-CimMethod -MethodName Terminate"
                    subprocess.run([get_powershell_exe(), "-Command", powershell_cmd], capture_output=True)
                except Exception:
                    pass

                # Delete old compiled PingBro.exe if it exists in install_dir
                old_exe = os.path.join(self.install_dir, "PingBro.exe")
                if os.path.exists(old_exe):
                    try:
                        os.remove(old_exe)
                    except Exception as e:
                        print(f"[Setup] Warning: Could not remove old PingBro.exe: {e}")

                # Clean up old Registry Run key if it exists
                try:
                    import winreg
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_ALL_ACCESS)
                    winreg.DeleteValue(key, "PingBro")
                    winreg.CloseKey(key)
                except Exception:
                    pass

                folders_to_copy = ["config", "services", "ui", "utils", "reminders", "assets", ".venv"]
                files_to_copy = ["main.py"]
                
                # Copy directories
                for i, folder in enumerate(folders_to_copy):
                    src_folder = os.path.join(source_dir, folder)
                    if os.path.exists(src_folder):
                        dst_folder = os.path.join(self.install_dir, folder)
                        self.status_lbl.configure(text=f"Copying {folder} folder ({i+1}/{len(folders_to_copy)})...")
                        self.prog_bar.set(0.2 + (i / len(folders_to_copy)) * 0.25)
                        self.update_idletasks()
                        if os.path.exists(dst_folder):
                            try:
                                shutil.rmtree(dst_folder)
                            except Exception:
                                pass
                        shutil.copytree(src_folder, dst_folder)
                
                # Copy files
                for file in files_to_copy:
                    src_file = os.path.join(source_dir, file)
                    if os.path.exists(src_file):
                        self.status_lbl.configure(text=f"Copying {file}...")
                        self.update_idletasks()
                        shutil.copy2(src_file, os.path.join(self.install_dir, file))

            self.after(500, lambda: self.step_create_shortcut())
        except Exception as e:
            self.show_error_screen(f"Failed to copy application files: {e}")

    def step_create_shortcut(self):
        try:
            self.status_lbl.configure(text="Creating Start Menu shortcut...")
            self.prog_bar.set(0.5)

            if getattr(sys, 'frozen', False):
                powershell_cmd = f"""
                $w = New-Object -ComObject WScript.Shell
                $s = $w.CreateShortcut("{self.shortcut_path}")
                $s.TargetPath = "{self.target_exe}"
                $s.Description = "PingBro Reminder App"
                $s.WorkingDirectory = "{self.install_dir}"
                $s.IconLocation = "{self.target_exe},0"
                $s.Save()
                """
            else:
                pythonw_exe = os.path.join(sys.base_prefix, "pythonw.exe")
                main_py = os.path.join(self.install_dir, "main.py")
                icon_ico = os.path.join(self.install_dir, "assets", "icon.ico")
                powershell_cmd = f"""
                $w = New-Object -ComObject WScript.Shell
                $s = $w.CreateShortcut("{self.shortcut_path}")
                $s.TargetPath = "{pythonw_exe}"
                $s.Arguments = '"{main_py}"'
                $s.Description = "PingBro Reminder App"
                $s.WorkingDirectory = "{self.install_dir}"
                $s.IconLocation = "{icon_ico}"
                $s.Save()
                """
            subprocess.run([get_powershell_exe(), "-Command", powershell_cmd], capture_output=True, text=True, check=True)

            self.after(500, lambda: self.step_register_uninstall())
        except Exception as e:
            self.show_error_screen(f"Failed to create shortcut: {e}")

    def step_register_uninstall(self):
        try:
            self.status_lbl.configure(text="Registering app in Windows Settings...")
            self.prog_bar.set(0.8)

            if getattr(sys, 'frozen', False):
                uninstall_string = f'"{self.target_exe}" --uninstall'
                startup_cmd = f'"{self.target_exe}"'
                display_icon = f'"{self.target_exe}",0'
                launch_cmd = [self.target_exe]
            else:
                python_exe = os.path.join(sys.base_prefix, "python.exe")
                pythonw_exe = os.path.join(sys.base_prefix, "pythonw.exe")
                main_py = os.path.join(self.install_dir, "main.py")
                icon_ico = os.path.join(self.install_dir, "assets", "icon.ico")
                uninstall_string = f'"{python_exe}" "{main_py}" --uninstall'
                startup_cmd = f'"{pythonw_exe}" "{main_py}"'
                display_icon = icon_ico
                launch_cmd = [pythonw_exe, main_py]

            # 1. Register in HKEY_CURRENT_USER for Uninstall (Installed apps list)
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\PingBro"
            key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS)
            
            winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, "PingBro")
            winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, "1.0.23")
            winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, "PingBro")
            winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, display_icon)
            winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, uninstall_string)
            winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, self.install_dir)
            winreg.CloseKey(key)

            # 2. Register in Windows Startup (autostart by default)
            startup_shortcut_path = os.path.join(
                os.environ["APPDATA"], "Microsoft", "Windows", "Start Menu", "Programs", "Startup", "PingBro.lnk"
            )
            try:
                if getattr(sys, 'frozen', False):
                    powershell_cmd = f"""
                    $w = New-Object -ComObject WScript.Shell
                    $s = $w.CreateShortcut("{startup_shortcut_path}")
                    $s.TargetPath = "{self.target_exe}"
                    $s.Description = "PingBro Reminder App"
                    $s.WorkingDirectory = "{self.install_dir}"
                    $s.IconLocation = "{self.target_exe},0"
                    $s.Save()
                    """
                else:
                    pythonw_exe = os.path.join(sys.base_prefix, "pythonw.exe")
                    main_py = os.path.join(self.install_dir, "main.py")
                    icon_ico = os.path.join(self.install_dir, "assets", "icon.ico")
                    powershell_cmd = f"""
                    $w = New-Object -ComObject WScript.Shell
                    $s = $w.CreateShortcut("{startup_shortcut_path}")
                    $s.TargetPath = "{pythonw_exe}"
                    $s.Arguments = '"{main_py}"'
                    $s.Description = "PingBro Reminder App"
                    $s.WorkingDirectory = "{self.install_dir}"
                    $s.IconLocation = "{icon_ico}"
                    $s.Save()
                    """
                subprocess.run([get_powershell_exe(), "-Command", powershell_cmd], capture_output=True, text=True, check=True)
            except Exception as e:
                print(f"[Startup] Failed to create startup shortcut: {e}")

            self.prog_bar.set(1.0)

            # Start the application immediately in the background
            try:
                subprocess.Popen(
                    launch_cmd,
                    cwd=self.install_dir,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL,
                    creationflags=0x00000008
                )
            except Exception:
                pass

            self.after(500, lambda: self.show_success_screen())
        except Exception as e:
            self.show_error_screen(f"Failed to register registry entries: {e}")

    def show_success_screen(self):
        self.clear_frame()

        # Icon or Checkmark representation
        success_lbl = ctk.CTkLabel(
            self.main_frame, text="🎉", font=("Helvetica", 40)
        )
        success_lbl.pack(pady=(35, 10))

        # Title
        title_lbl = ctk.CTkLabel(
            self.main_frame, text="Installation Complete!", font=("Helvetica", 22, "bold"), text_color="#30d158"
        )
        title_lbl.pack(pady=5)

        # Details
        details_lbl = ctk.CTkLabel(
            self.main_frame,
            text="PingBro has been successfully installed, registered, and launched!\nYou can now find it running in your system tray.\nManage or uninstall it directly from your Windows Settings Apps list.",
            font=("Helvetica", 12),
            text_color="#a0a0a5",
            justify="center"
        )
        details_lbl.pack(pady=20)

        # Action Buttons
        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.pack(side="bottom", fill="x", padx=30, pady=25)

        finish_btn = ctk.CTkButton(
            btn_frame,
            text="Finish",
            width=120,
            fg_color="#00adb5",
            hover_color="#008c95",
            text_color="#ffffff",
            font=("Helvetica", 12, "bold"),
            command=self.finish_installation
        )
        finish_btn.pack(side="right")

    def finish_installation(self):
        self.destroy()

    def show_error_screen(self, err_message):
        self.clear_frame()

        title_lbl = ctk.CTkLabel(
            self.main_frame, text="Installation Failed", font=("Helvetica", 20, "bold"), text_color="#ff453a"
        )
        title_lbl.pack(pady=(45, 10))

        err_lbl = ctk.CTkLabel(
            self.main_frame,
            text=err_message,
            font=("Helvetica", 12),
            text_color="#ff8c82",
            wraplength=440
        )
        err_lbl.pack(pady=20)

        # Action Buttons
        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.pack(side="bottom", fill="x", padx=30, pady=25)

        close_btn = ctk.CTkButton(
            btn_frame,
            text="Close",
            width=120,
            fg_color="#ff453a",
            hover_color="#c9362e",
            text_color="#ffffff",
            command=self.destroy
        )
        close_btn.pack(side="right")

    def clear_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

if __name__ == "__main__":
    app = SetupWizard()
    app.mainloop()
