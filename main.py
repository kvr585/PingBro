import os
import sys
import time
import threading
import customtkinter as ctk

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
    global settings, scheduler, hotkey, tray, window

    print("[Startup] Launching PingBro...")
    log_event("app_started", "PingBro application started.")

    # 1. Initialize Configuration
    settings = SettingsManager()

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

    # Begin the GUI event loop
    try:
        window.mainloop()
    except KeyboardInterrupt:
        trigger_safe_exit()

if __name__ == "__main__":
    main()
