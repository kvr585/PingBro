import os
import sys
import time
import threading
import socket
import customtkinter as ctk

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
sys.path.insert(0, project_root)

from config.settings import SettingsManager
from services.scheduler import ReminderScheduler
from services.tray import TrayIconService
from utils.hotkey import GlobalHotkeyListener
from utils.logger import log_event
from ui.main_window import MainWindow

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

def main():
    global settings, scheduler, hotkey, tray, window, lock

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
        if settings.get("startup_enabled", True):
            try:
                import winreg
                key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
                app_name = "PingBro"
                if getattr(sys, 'frozen', False):
                    cmd = f'"{sys.executable}"'
                else:
                    cmd = f'"{sys.executable}" "{os.path.abspath(sys.argv[0])}"'
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS)
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, cmd)
                winreg.CloseKey(key)
            except Exception as e:
                print(f"[Registry] Failed to auto-set registry startup key: {e}")

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
