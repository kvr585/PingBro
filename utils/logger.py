import os
import json
import threading
from datetime import datetime
from utils.paths import get_data_path

LOGS_FILE = get_data_path(os.path.join("config", "logs.json"))
MAX_LOG_ENTRIES = 200

# Use a lock to ensure thread safety when writing to logs from multiple threads
log_lock = threading.Lock()

def log_event(event_type, details=""):
    """
    Logs an application event with a timestamp.
    Event types: "reminder_triggered", "reminder_dismissed", "pause_activated", "resume_activated", "exam_mode_activated", "settings_changed"
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = {
        "timestamp": timestamp,
        "event": event_type,
        "details": details
    }
    
    with log_lock:
        logs = []
        if os.path.exists(LOGS_FILE):
            try:
                with open(LOGS_FILE, "r") as f:
                    logs = json.load(f)
                    if not isinstance(logs, list):
                        logs = []
            except Exception:
                logs = []
        
        # Insert at the beginning of the list (most recent first)
        logs.insert(0, entry)
        
        # Cap the log entries
        if len(logs) > MAX_LOG_ENTRIES:
            logs = logs[:MAX_LOG_ENTRIES]
            
        try:
            os.makedirs(os.path.dirname(LOGS_FILE), exist_ok=True)
            with open(LOGS_FILE, "w") as f:
                json.dump(logs, f, indent=4)
        except Exception as e:
            print(f"Error saving log: {e}")

def get_logs():
    """Retrieves all logged entries."""
    with log_lock:
        if not os.path.exists(LOGS_FILE):
            return []
        try:
            with open(LOGS_FILE, "r") as f:
                logs = json.load(f)
                return logs if isinstance(logs, list) else []
        except Exception:
            return []

def clear_logs():
    """Clears all logged entries."""
    with log_lock:
        try:
            if os.path.exists(LOGS_FILE):
                os.remove(LOGS_FILE)
            log_event("logs_cleared", "System log history was cleared by user.")
        except Exception as e:
            print(f"Error clearing logs: {e}")
