import time
import threading
from datetime import datetime, timedelta
from plyer import notification

from reminders.models import AppReminder
from utils.fullscreen import is_fullscreen_app_active
from utils.sound import play_alert_sound
from utils.logger import log_event
from utils.paths import get_asset_path

class ReminderScheduler:
    def __init__(self, settings_manager, ui_trigger_callback=None):
        self.settings = settings_manager
        self.ui_trigger_callback = ui_trigger_callback  # Callback to trigger UI overlays (Popup)
        self.running = False
        self.thread = None

    def start(self):
        """Starts the scheduler background thread."""
        self.running = True
        
        # Seed last_triggered_time for any unseeded interval reminders on startup
        now = time.time()
        reminders_list = self.settings.get("reminders", [])
        modified = False
        for r_dict in reminders_list:
            if r_dict.get("trigger_type") == "Interval" and r_dict.get("last_triggered_time", 0.0) == 0.0:
                r_dict["last_triggered_time"] = now
                modified = True
        if modified:
            self.settings.set("reminders", reminders_list)
            
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self):
        """Stops the scheduler loop."""
        self.running = False

    def get_water_countdown(self):
        """Returns the seconds left until the next active water reminder, or 0 if none exist."""
        if not self.settings.get("hydration_mode_enabled"):
            return 0
        if self.is_paused():
            return 0
            
        reminders_list = self.settings.get("reminders", [])
        now = time.time()
        min_time_left = float('inf')
        
        for r_dict in reminders_list:
            r = AppReminder.from_dict(r_dict)
            if r.enabled and ("water" in r.title.lower() or "water" in r.message.lower() or "hydrate" in r.title.lower()):
                if r.trigger_type == "Interval":
                    time_left = (r.last_triggered_time + r.interval_mins * 60) - now
                    if time_left > 0 and time_left < min_time_left:
                        min_time_left = time_left
                elif r.trigger_type == "Time of Day":
                    try:
                        dt = datetime.now()
                        r_hour, r_min = map(int, r.time_str.split(":"))
                        target_dt = dt.replace(hour=r_hour, minute=r_min, second=0, microsecond=0)
                        if target_dt < dt:
                            target_dt += timedelta(days=1)
                        time_left = (target_dt - dt).total_seconds()
                        if time_left > 0 and time_left < min_time_left:
                            min_time_left = time_left
                    except Exception:
                        pass
                        
        return int(min_time_left) if min_time_left != float('inf') else 0

    def is_paused(self):
        """Checks if reminders are currently paused."""
        pause_end = self.settings.get("active_pause_end")
        if pause_end:
            now = time.time()
            if now < pause_end:
                return True
            else:
                self.settings.set("active_pause_end", None)
                log_event("pause_expired", "Reminder pause duration ended. Reminders resumed.")
        return False

    def trigger_reminder(self, title, message, mode, priority, is_water_reminder=False):
        """
        Triggers a reminder. Handles silent mode, sound, fullscreen safety,
        and dispatches to standard notification or fullscreen popup.
        """
        is_fullscreen = is_fullscreen_app_active()
        safety_enabled = self.settings.get("fullscreen_safety_enabled", True)
        convert_to_notif = self.settings.get("fullscreen_convert_to_notif", True)
        silent_mode = self.settings.get("silent_mode", False)
        sound_enabled = self.settings.get("water_reminder_sound" if is_water_reminder else "sound_enabled", True)
        custom_sound = self.settings.get("custom_sound_file", "")
        
        log_event("reminder_triggered", f"{title}: {message} (Mode: {mode}, Fullscreen: {is_fullscreen})")
        
        # 1. Fullscreen Safety Checks
        if is_fullscreen and safety_enabled:
            if convert_to_notif:
                # Convert fullscreen popup into a silent Windows Notification
                self._show_desktop_notification(title, message)
                log_event("reminder_suppressed", f"Converted '{title}' to notification due to active fullscreen application.")
                self.settings.set("stats_total_reminders_triggered", self.settings.get("stats_total_reminders_triggered", 0) + 1)
            else:
                log_event("reminder_suppressed", f"Suppressed '{title}' completely due to active fullscreen application.")
            return

        # 2. Sound Management (if not silent)
        if not silent_mode and sound_enabled:
            play_alert_sound(custom_sound if custom_sound else None, silent=False)

        # Increment trigger count
        self.settings.set("stats_total_reminders_triggered", self.settings.get("stats_total_reminders_triggered", 0) + 1)

        # 3. Mode Dispatch (Notification vs Fullscreen Popup)
        if mode == "Notification":
            self._show_desktop_notification(title, message)
        elif mode == "Fullscreen Popup":
            if self.ui_trigger_callback:
                self.ui_trigger_callback(title, message, mode, priority, is_water_reminder)
            else:
                self._show_desktop_notification(title, message)

    def _show_desktop_notification(self, title, message):
        """Triggers a standard Windows toast notification."""
        try:
            icon_path = get_asset_path("assets/icon.png")
            if not os.path.exists(icon_path):
                icon_path = None
                
            notification.notify(
                title=title,
                message=message,
                app_name="PingBro",
                app_icon=icon_path,
                timeout=5
            )
        except Exception as e:
            print(f"Error displaying notification: {e}")

    def _run(self):
        """Main scheduler execution loop."""
        while self.running:
            if self.is_paused():
                time.sleep(1)
                continue
                
            now = time.time()
            now_dt = datetime.now()
            today_str = now_dt.strftime("%Y-%m-%d")
            current_time_str = now_dt.strftime("%H:%M")

            reminders_list = self.settings.get("reminders", [])
            modified = False

            for r_dict in reminders_list:
                r = AppReminder.from_dict(r_dict)
                if r.enabled:
                    triggered = False
                    
                    if r.trigger_type == "Time of Day":
                        if current_time_str == r.time_str:
                            if r.last_triggered_date != today_str:
                                triggered = True
                                r.last_triggered_date = today_str
                                
                    elif r.trigger_type == "Interval":
                        # Check elapsed time
                        if r.last_triggered_time == 0.0:
                            # Seed it so it triggers interval_mins later
                            r.last_triggered_time = now
                            for item in reminders_list:
                                if item["id"] == r.id:
                                    item["last_triggered_time"] = now
                            modified = True
                        elif now - r.last_triggered_time >= r.interval_mins * 60:
                            triggered = True
                            r.last_triggered_time = now
                            
                    if triggered:
                        # Determine if this contains water-related keys to sync with Hydration Mode
                        is_water = "water" in r.title.lower() or "water" in r.message.lower() or "hydrate" in r.title.lower()
                        
                        self.trigger_reminder(
                            title=r.title,
                            message=r.message,
                            mode=r.mode_type,
                            priority=r.priority,
                            is_water_reminder=is_water
                        )
                        # Sync states back to list
                        for item in reminders_list:
                            if item["id"] == r.id:
                                item["last_triggered_time"] = r.last_triggered_time
                                item["last_triggered_date"] = r.last_triggered_date
                        modified = True

            if modified:
                self.settings.set("reminders", reminders_list)

            self.settings.reset_daily_stats_if_new_day()
            time.sleep(1)
