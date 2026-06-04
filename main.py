import os
import sys
import time
import threading
import socket

class SingleInstanceLock:
    def __init__(self, port=58585):
        self.port = port
        self.socket = None
        self.window = None
        self.thread = None
        self.running = False
        self.mutex = None
        self.lock_file = None

    def acquire(self):
        # 1. Platform-specific singleton check (Mutex on Windows, fcntl lock file on Linux)
        if sys.platform.startswith('win'):
            try:
                import ctypes
                self.mutex = ctypes.windll.kernel32.CreateMutexW(None, False, "PingBro_Singleton_Mutex")
                last_error = ctypes.windll.kernel32.GetLastError()
                if last_error == 183:  # ERROR_ALREADY_EXISTS
                    self.notify_and_restore_existing()
                    return False
            except Exception as e:
                print(f"[Lock] Failed to acquire Win32 mutex: {e}. Falling back to socket lock.")
        else:
            # Linux fallback using fcntl lock file
            try:
                import fcntl
                lock_path = os.path.join(os.path.expanduser("~"), ".pingbro.lock")
                self.lock_file = open(lock_path, 'w')
                try:
                    fcntl.lockf(self.lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except (IOError, OSError):
                    # Lock is already held by another instance
                    self.notify_and_restore_existing()
                    return False
            except Exception as e:
                print(f"[Lock] Failed to acquire fcntl lock file: {e}. Falling back to socket lock.")

        # 2. Both Windows (first instance) and Linux should start the socket listener for restoration signals
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(('127.0.0.1', self.port))
            self.socket.listen(5)
            self.running = True
            
            self.thread = threading.Thread(target=self._listen, daemon=True)
            self.thread.start()
            return True
        except OSError:
            # Fallback if binding fails (e.g. port is already in use by another program)
            if sys.platform.startswith('win') and self.mutex:
                # On Windows, if we successfully hold the mutex, we are the first instance.
                # So we can safely ignore the socket bind failure and run anyway!
                print("[Lock] Socket port in use. Running anyway as we hold the system mutex.")
                return True
            self.notify_and_restore_existing()
            return False

    def register_window(self, window):
        self.window = window

    def notify_and_restore_existing(self):
        """Attempts to notify the running instance to restore, and on Windows falls back to Win32 restoration."""
        # Try clean socket notification first
        socket_notified = False
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.5)
            s.connect(('127.0.0.1', self.port))
            s.sendall(b"restore")
            s.close()
            socket_notified = True
        except Exception:
            pass
        
        # On Windows, if socket fails/is blocked, force restore using FindWindowW API
        if not socket_notified and sys.platform.startswith('win'):
            self.restore_existing_window_win32()

    def restore_existing_window_win32(self):
        try:
            import ctypes
            hwnd = ctypes.windll.user32.FindWindowW(None, "PingBro")
            if hwnd:
                # SW_RESTORE = 9
                ctypes.windll.user32.ShowWindow(hwnd, 9)
                ctypes.windll.user32.SetForegroundWindow(hwnd)
        except Exception as e:
            print(f"[Lock] Failed to restore window via Win32: {e}")

    def _listen(self):
        while self.running:
            try:
                conn, addr = self.socket.accept()
                data = conn.recv(1024)
                if data == b"restore":
                    if self.window:
                        self.window.after(0, self.window.restore_from_tray)
                conn.close()
            except Exception:
                break

# Ensure working directory is the project root folder
project_root = os.path.dirname(os.path.abspath(__file__))
os.chdir(project_root)
sys.path.insert(0, project_root)

# If running via system python, inject local virtual environment site-packages
venv_site_packages = os.path.join(project_root, ".venv", "Lib", "site-packages")
if os.path.exists(venv_site_packages):
    sys.path.insert(0, venv_site_packages)

import traceback

try:
    import customtkinter as ctk
    from config.settings import SettingsManager
    from services.scheduler import ReminderScheduler
    from services.tray import TrayIconService
    from utils.hotkey import GlobalHotkeyListener
    from utils.logger import log_event
    from ui.main_window import MainWindow
except Exception as e:
    crash_log_path = os.path.join(project_root, "crash_log.txt")
    try:
        with open(crash_log_path, "w") as f:
            f.write("PingBro Crash Log (Import stage)\n")
            f.write("===============================\n\n")
            traceback.print_exc(file=f)
    except Exception:
        pass
    sys.exit(1)

# Global references
settings = None
scheduler = None
hotkey = None
tray = None
window = None
lock = None

def trigger_exam_mode():
    """Emergency shutdown: instantly terminates app, threads, and tray icon."""
    print("[Exam Mode] Activating emergency shutdown...")
    # Log the activation of Exam Mode
    log_event("exam_mode_activated", "Emergency Exam Mode activated! Hard process shutdown triggered.")
    
    # Attempt tray cleanup to remove taskbar icon
    try:
        if tray:
            tray.stop()
    except Exception:
        pass
        
    # Attempt hotkey listener thread cleanup
    try:
        if hotkey:
            hotkey.stop()
    except Exception:
        pass
        
    # Terminate process instantly (kills GUI, scheduler thread, hotkey thread, pystray)
    os._exit(0)

def trigger_safe_exit():
    """Performs a clean shutdown and exits the application."""
    print("[Shutdown] Cleaning up services and exiting...")
    log_event("app_exited", "Application exited cleanly by user.")
    
    try:
        if tray:
            tray.stop()
    except Exception:
        pass
        
    try:
        if hotkey:
            hotkey.stop()
    except Exception:
        pass
        
    try:
        if scheduler:
            scheduler.stop()
    except Exception:
        pass
        
    os._exit(0)

def tray_pause_reminders(minutes):
    """Sets a pause duration for reminders via the system tray menu."""
    now = time.time()
    pause_end = now + (minutes * 60)
    settings.set("active_pause_end", pause_end)
    log_event("pause_activated", f"Reminders paused for {minutes} minutes via system tray.")

def tray_resume_reminders():
    """Resumes reminders via the system tray menu."""
    settings.set("active_pause_end", None)
    log_event("resume_activated", "Reminders resumed manually via system tray.")

def run_uninstaller():
    """Removes all installed assets, registry keys, and shortcuts for PingBro."""
    if not sys.platform.startswith('win'):
        print("[Uninstall] Uninstall option is only supported on Windows.")
        return

    print("[Uninstall] Running uninstaller...")
    import winreg
    import subprocess
    import tempfile


    # 2. Delete Startup registry value and Startup folder shortcut
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_ALL_ACCESS)
        winreg.DeleteValue(key, "PingBro")
        winreg.CloseKey(key)
        print("[Uninstall] Removed startup registry key.")
    except Exception:
        pass
    try:
        startup_shortcut_path = os.path.join(
            os.environ["APPDATA"], "Microsoft", "Windows", "Start Menu", "Programs", "Startup", "PingBro.lnk"
        )
        if os.path.exists(startup_shortcut_path):
            os.remove(startup_shortcut_path)
            print("[Uninstall] Removed startup folder shortcut.")
    except Exception:
        pass

    # 3. Delete Uninstall registry key
    try:
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall\PingBro")
        print("[Uninstall] Removed uninstall entry from Windows Settings.")
    except Exception:
        pass

    # 4. Delete Start Menu shortcut
    try:
        shortcut_path = os.path.join(os.environ["APPDATA"], "Microsoft", "Windows", "Start Menu", "Programs", "PingBro.lnk")
        if os.path.exists(shortcut_path):
            os.remove(shortcut_path)
            print("[Uninstall] Removed Start Menu shortcut.")
    except Exception as e:
        print(f"[Uninstall] Failed to remove shortcut: {e}")

    # 5. Show uninstallation success dialog
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(
            None, 
            "PingBro has been successfully uninstalled from your computer.", 
            "PingBro Uninstallation", 
            0x40 | 0x0  # MB_ICONINFORMATION | MB_OK
        )
    except Exception:
        pass

    # 6. Spawn self-deletion batch script in the temp directory and exit
    try:
        exe_path = sys.executable
        if getattr(sys, 'frozen', False):
            install_dir = os.path.dirname(exe_path)
            exe_to_check = exe_path
        else:
            install_dir = os.path.dirname(os.path.abspath(__file__))
            exe_to_check = os.path.join(install_dir, "main.py")
        
        temp_dir = tempfile.gettempdir()
        bat_path = os.path.join(temp_dir, "pingbro_cleanup.bat")
        
        # Only delete directory if folder name is exactly "PingBro" to prevent accidental deletion
        is_safe_dir = os.path.basename(install_dir).lower() == "pingbro"
        
        with open(bat_path, "w") as f:
            f.write(f"""@echo off
:loop
taskkill /F /IM PingBro.exe >nul 2>&1
powershell -Command "Get-CimInstance Win32_Process -Filter 'CommandLine LIKE ''%%%%main.py%%%%'' AND Name <> ''powershell.exe''' | Invoke-CimMethod -MethodName Terminate" >nul 2>&1
del /F /Q "{exe_to_check}" >nul 2>&1
if exist "{exe_to_check}" (
    timeout /t 1 /nobreak >nul
    goto loop
)
""")
            if is_safe_dir:
                f.write(f'rmdir /S /Q "{install_dir}" >nul 2>&1\n')
            f.write('del "%~f0"\n')
        creationflags = 0
        if sys.platform.startswith('win'):
            creationflags = 0x08000000  # CREATE_NO_WINDOW
            subprocess.Popen(['cmd.exe', '/c', bat_path], creationflags=creationflags)
        else:
            subprocess.Popen(['/bin/sh', bat_path])
    except Exception as e:
        print(f"[Uninstall] Failed to spawn cleanup script: {e}")

def main():
    try:
        _main_impl()
    except Exception as e:
        project_root = os.path.dirname(os.path.abspath(__file__))
        crash_log_path = os.path.join(project_root, "crash_log.txt")
        try:
            with open(crash_log_path, "w") as f:
                f.write("PingBro Crash Log (Runtime stage)\n")
                f.write("================================\n\n")
                traceback.print_exc(file=f)
        except Exception:
            pass
        sys.exit(1)

def _main_impl():
    global settings, scheduler, hotkey, tray, window, lock

    # Check for uninstall command line flag
    if "--uninstall" in sys.argv:
        run_uninstaller()
        sys.exit(0)

    # Enforce single instance lock
    lock = SingleInstanceLock()
    if not lock.acquire():
        print("[Startup] PingBro is already running. Restoring active window and exiting.")
        sys.exit(0)

    print("[Startup] Launching PingBro...")
    log_event("app_started", "PingBro application started.")

    # 1. Initialize Configuration
    settings = SettingsManager()

    # Enable start on boot automatically by default if running on Windows and enabled
    if sys.platform.startswith('win'):
        startup_shortcut_path = os.path.join(
            os.environ["APPDATA"], "Microsoft", "Windows", "Start Menu", "Programs", "Startup", "PingBro.lnk"
        )
        if settings.get("startup_enabled", True):
            try:
                def get_powershell_exe():
                    system_root = os.environ.get("SystemRoot", "C:\\Windows")
                    powershell_exe = os.path.join(system_root, "System32", "WindowsPowerShell", "v1.0", "powershell.exe")
                    if os.path.exists(powershell_exe):
                        return powershell_exe
                    return "powershell"
                
                if getattr(sys, 'frozen', False):
                    powershell_cmd = f"""
                    $w = New-Object -ComObject WScript.Shell
                    $s = $w.CreateShortcut("{startup_shortcut_path}")
                    $s.TargetPath = "{sys.executable}"
                    $s.Description = "PingBro Reminder App"
                    $s.WorkingDirectory = "{os.path.dirname(sys.executable)}"
                    $s.IconLocation = "{sys.executable},0"
                    $s.Save()
                    """
                else:
                    pythonw_exe = os.path.join(sys.base_prefix, "pythonw.exe")
                    if not os.path.exists(pythonw_exe):
                        pythonw_exe = sys.executable
                    main_py = os.path.abspath(sys.argv[0])
                    install_dir = os.path.dirname(main_py)
                    icon_ico = os.path.join(install_dir, "assets", "icon.ico")
                    powershell_cmd = f"""
                    $w = New-Object -ComObject WScript.Shell
                    $s = $w.CreateShortcut("{startup_shortcut_path}")
                    $s.TargetPath = "{pythonw_exe}"
                    $s.Arguments = '"{main_py}"'
                    $s.Description = "PingBro Reminder App"
                    $s.WorkingDirectory = "{install_dir}"
                    $s.IconLocation = "{icon_ico}"
                    $s.Save()
                    """
                subprocess.run([get_powershell_exe(), "-Command", powershell_cmd], capture_output=True, text=True, check=True)
            except Exception as e:
                print(f"[Startup] Failed to create startup shortcut: {e}")
        else:
            try:
                if os.path.exists(startup_shortcut_path):
                    os.remove(startup_shortcut_path)
            except Exception:
                pass

    # 2. Setup visual alert trigger callback for the scheduler
    def scheduler_ui_dispatcher(title, message, mode, priority, is_water):
        if window:
            # Dispatch to main Tkinter thread to show window overlay/popup safely
            window.trigger_visual_reminder(title, message, mode, priority, is_water)

    # 3. Initialize background services
    scheduler = ReminderScheduler(settings, ui_trigger_callback=scheduler_ui_dispatcher)
    scheduler.start()

    hotkey = GlobalHotkeyListener(trigger_callback=trigger_exam_mode)
    hotkey.start()

    # Late binding callbacks for tray icon menu actions
    tray = TrayIconService(
        on_open=lambda: window.after(0, window.restore_from_tray()) if window else None,
        on_pause=tray_pause_reminders,
        on_resume=tray_resume_reminders,
        on_exam_mode=trigger_exam_mode,
        on_exit=trigger_safe_exit
    )
    tray.start()

    # 4. Start CustomTkinter GUI
    # Initialize theme style
    ctk.set_appearance_mode(settings.get("theme", "Dark"))
    ctk.set_default_color_theme("blue")  # Modern color scheme

    # Create Main Application Window
    window = MainWindow(
        settings_manager=settings,
        scheduler_ref=scheduler,
        hotkey_ref=hotkey,
        tray_ref=tray,
        exam_mode_handler=trigger_exam_mode,
        exit_handler=trigger_safe_exit
    )
    lock.register_window(window)

    # Begin the GUI event loop
    try:
        window.mainloop()
    except KeyboardInterrupt:
        trigger_safe_exit()

if __name__ == "__main__":
    main()
