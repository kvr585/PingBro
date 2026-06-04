import os
import json
from datetime import datetime
from utils.paths import get_data_path

SETTINGS_FILE = get_data_path(os.path.join("config", "settings.json"))

DEFAULT_SETTINGS = {
    "theme": "Dark",
    "hydration_mode_enabled": True,  # Enabled by default, can be toggled in settings
    "hydration_target": 2000,          # ml
    "hydration_weight": 70,            # kg
    
    # Generic Reminders
    "reminders": [
        {
            "id": "r1",
            "title": "Drink Water",
            "message": "It's time to drink a glass of water and stay hydrated.",
            "trigger_type": "Interval",
            "time": "12:00",
            "interval_mins": 45,
            "mode_type": "Notification",
            "priority": "medium",
            "enabled": True,
            "last_triggered_time": 0.0,
            "last_triggered_date": ""
        },
        {
            "id": "r2",
            "title": "Stretch Break",
            "message": "Stand up, stretch your arms, and take a deep breath.",
            "trigger_type": "Time of Day",  # Time of Day, Interval
            "time": "14:00",               # 24h format
            "interval_mins": 30,           # used if trigger_type is Interval
            "mode_type": "Notification",   # Notification, Fullscreen Popup
            "priority": "low",
            "enabled": True,
            "last_triggered_time": 0.0,
            "last_triggered_date": ""
        },
        {
            "id": "r3",
            "title": "Eye Rest (20-20-20 Rule)",
            "message": "Look at something 20 feet away for 20 seconds to reduce eye strain.",
            "trigger_type": "Interval",
            "time": "12:00",
            "interval_mins": 20,
            "mode_type": "Fullscreen Popup",
            "priority": "medium",
            "enabled": True,
            "last_triggered_time": 0.0,
            "last_triggered_date": ""
        }
    ],
    
    "active_pause_end": None,  # Epoch timestamp (float) or None
    "startup_enabled": True,
    "silent_mode": False,
    "custom_sound_file": "",
    "fullscreen_safety_enabled": True,
    "fullscreen_convert_to_notif": True,
    
    # Statistics (for Hydration Mode)
    "stats_streak": 0,
    "stats_cups_logged": 0,
    "stats_total_reminders_triggered": 0,
    "stats_last_water_log_date": "",
    "stats_history": {}  # date (YYYY-MM-DD) -> cups_count
}

class SettingsManager:
    def __init__(self):
        self.settings = {}
        self.load_settings()

    def load_settings(self):
        """Loads settings from the settings.json file. If it doesn't exist, initializes with default settings."""
        if not os.path.exists(SETTINGS_FILE):
            self.settings = DEFAULT_SETTINGS.copy()
            self.save_settings()
        else:
            try:
                with open(SETTINGS_FILE, "r") as f:
                    file_data = json.load(f)
                
                # Merge loaded settings with default settings to ensure missing keys are added
                self.settings = DEFAULT_SETTINGS.copy()
                self.settings.update(file_data)
            except Exception as e:
                print(f"Error loading settings: {e}. Falling back to default settings.")
                self.settings = DEFAULT_SETTINGS.copy()

    def save_settings(self):
        """Saves current settings to the settings.json file."""
        try:
            os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
            with open(SETTINGS_FILE, "w") as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def get(self, key, default=None):
        """Gets a setting value."""
        return self.settings.get(key, default)

    def set(self, key, value):
        """Sets a setting value and saves immediately."""
        self.settings[key] = value
        self.save_settings()

    def log_water_intake(self, amount_ml=250):
        """Increments water intake count and updates streak statistics based on custom amount in ml."""
        today = datetime.now().strftime("%Y-%m-%d")
        last_log = self.get("stats_last_water_log_date", "")
        streak = self.get("stats_streak", 0)
        
        # Calculate streak logic
        if last_log:
            try:
                last_date = datetime.strptime(last_log, "%Y-%m-%d").date()
                today_date = datetime.now().date()
                delta = (today_date - last_date).days
                if delta == 1:
                    # Consecutive day
                    streak += 1
                elif delta > 1:
                    # Streak broken
                    streak = 1
                # If delta == 0, same day, streak doesn't change
            except Exception:
                streak = 1
        else:
            # First time logging
            streak = 1
            
        self.set("stats_streak", streak)
        self.set("stats_last_water_log_date", today)
        
        # Calculate how many equivalent 250ml cups this amount represents, or log direct ml
        # To keep it simple, we store ml in history but represent cups in stats_cups_logged
        cups_diff = amount_ml / 250.0
        cups = self.get("stats_cups_logged", 0) + cups_diff
        self.set("stats_cups_logged", round(cups, 2))
        
        # Log volume in ml to history
        history = self.get("stats_history", {})
        # History stores total ml drank today
        history[today] = history.get(today, 0) + amount_ml
        self.set("stats_history", history)

    def reset_daily_stats_if_new_day(self):
        """Resets the daily cups logged if today is a different day, but preserves history and streaks."""
        today = datetime.now().strftime("%Y-%m-%d")
        last_log = self.get("stats_last_water_log_date", "")
        
        # If it's a new day
        if last_log and last_log != today:
            # Check if streak was broken (last log was older than yesterday)
            try:
                last_date = datetime.strptime(last_log, "%Y-%m-%d").date()
                today_date = datetime.now().date()
                delta = (today_date - last_date).days
                if delta > 1:
                    self.set("stats_streak", 0)
            except Exception:
                pass
            
            # Reset daily cups count for visual display on dashboard
            self.set("stats_cups_logged", 0.0)
