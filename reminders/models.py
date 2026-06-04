class AppReminder:
    def __init__(self, reminder_id, title, message, trigger_type="Time of Day", time_str="12:00", interval_mins=30, mode_type="Notification", priority="low", enabled=True, last_triggered_time=0.0, last_triggered_date=""):
        self.id = reminder_id
        self.title = title
        self.message = message
        self.trigger_type = trigger_type  # "Time of Day", "Interval"
        self.time_str = time_str          # "HH:MM" in 24h format
        self.interval_mins = interval_mins  # integer minutes
        self.mode_type = mode_type        # "Notification", "Fullscreen Popup"
        self.priority = priority          # "low", "medium", "high"
        self.enabled = enabled
        self.last_triggered_time = last_triggered_time  # epoch float (for interval timers)
        self.last_triggered_date = last_triggered_date  # YYYY-MM-DD string (for daily alarms)

    @classmethod
    def from_dict(cls, data):
        """Creates an AppReminder object from a dictionary."""
        return cls(
            reminder_id=data.get("id"),
            title=data.get("title", "Reminder"),
            message=data.get("message", ""),
            trigger_type=data.get("trigger_type", "Time of Day"),
            time_str=data.get("time", "12:00"),
            interval_mins=data.get("interval_mins", 30),
            mode_type=data.get("mode_type", "Notification"),
            priority=data.get("priority", "low"),
            enabled=data.get("enabled", True),
            last_triggered_time=data.get("last_triggered_time", 0.0),
            last_triggered_date=data.get("last_triggered_date", "")
        )

    def to_dict(self):
        """Converts the AppReminder object to a dictionary for JSON serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "message": self.message,
            "trigger_type": self.trigger_type,
            "time": self.time_str,
            "interval_mins": self.interval_mins,
            "mode_type": self.mode_type,
            "priority": self.priority,
            "enabled": self.enabled,
            "last_triggered_time": self.last_triggered_time,
            "last_triggered_date": self.last_triggered_date
        }
