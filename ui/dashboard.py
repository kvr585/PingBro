import time
import customtkinter as ctk
from datetime import datetime, timedelta
from utils.logger import log_event

class DashboardView(ctk.CTkFrame):
    def __init__(self, parent, settings_manager, scheduler):
        super().__init__(parent, fg_color="transparent")
        self.settings = settings_manager
        self.scheduler = scheduler
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self.active_hydration_mode = None
        self.rebuild_layout()

    def rebuild_layout(self):
        """Clears current layout and builds widgets according to the active hydration mode setting."""
        # Clean current children
        for child in self.winfo_children():
            child.destroy()
            
        self.active_hydration_mode = self.settings.get("hydration_mode_enabled", False)
        
        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        # 1. Header welcome card
        self.create_header_card()
        
        if self.active_hydration_mode:
            # Hydration mode is ON
            # Left Panel - Hydration Progress Card
            self.create_hydration_card()
            # Right Panel - Controls Card
            self.create_control_card()
            # Bottom Panel - Weekly history chart
            self.create_weekly_chart_card()
        else:
            # Hydration mode is OFF
            # Left Panel - General Statistics Card
            self.create_general_stats_card()
            # Right Panel - Controls Card
            self.create_control_card()
            # Bottom Panel - Upcoming Reminders Timeline
            self.create_upcoming_timeline_card()

    def create_header_card(self):
        header_card = ctk.CTkFrame(self, fg_color="#1e1e1e", corner_radius=15, border_width=1, border_color="#2e2e2e")
        header_card.grid(row=0, column=0, columnspan=2, padx=15, pady=(15, 10), sticky="ew")
        
        title_text = "💧 PINGBRO HYDRATION DASHBOARD" if self.active_hydration_mode else "📊 PINGBRO REMINDER DASHBOARD"
        welcome_lbl = ctk.CTkLabel(
            header_card, 
            text=title_text, 
            font=("Helvetica", 18, "bold"), 
            text_color="#00adb5"
        )
        welcome_lbl.pack(anchor="w", padx=20, pady=(15, 5))
        
        quote_text = "Stay hydrated, stay focused. Health is wealth." if self.active_hydration_mode else "Organize your day, stay on track, and achieve your goals."
        self.quote_lbl = ctk.CTkLabel(
            header_card, 
            text=quote_text, 
            font=("Helvetica", 12, "italic"), 
            text_color="#888888"
        )
        self.quote_lbl.pack(anchor="w", padx=20, pady=(0, 15))

    def create_hydration_card(self):
        self.hyd_card = ctk.CTkFrame(self, fg_color="#1e1e1e", corner_radius=15, border_width=1, border_color="#2e2e2e")
        self.hyd_card.grid(row=1, column=0, padx=15, pady=5, sticky="nsew")
        
        title_lbl = ctk.CTkLabel(
            self.hyd_card, 
            text="HYDRATION PROGRESS", 
            font=("Helvetica", 13, "bold"), 
            text_color="#ffffff"
        )
        title_lbl.pack(anchor="w", padx=20, pady=(15, 5))
        
        # Streak info
        self.streak_frame = ctk.CTkFrame(self.hyd_card, fg_color="transparent")
        self.streak_frame.pack(anchor="w", padx=20, pady=2)
        
        self.streak_icon = ctk.CTkLabel(self.streak_frame, text="🔥", font=("Segoe UI", 20))
        self.streak_icon.pack(side="left")
        
        self.streak_lbl = ctk.CTkLabel(
            self.streak_frame, 
            text="Streak: 0 Days", 
            font=("Helvetica", 14, "bold"), 
            text_color="#ff9f0a"
        )
        self.streak_lbl.pack(side="left", padx=5)
        
        # Progress bar
        self.progress_lbl = ctk.CTkLabel(
            self.hyd_card, 
            text="0 ml / 2000 ml (0%)", 
            font=("Helvetica", 12, "bold"), 
            text_color="#aaaaaa"
        )
        self.progress_lbl.pack(anchor="w", padx=20, pady=(10, 2))
        
        self.progress_bar = ctk.CTkProgressBar(
            self.hyd_card, 
            progress_color="#00adb5", 
            fg_color="#333333", 
            height=10
        )
        self.progress_bar.pack(fill="x", padx=20, pady=(0, 10))
        self.progress_bar.set(0)
        
        # Drink Size Selector
        self.drink_size_selector = ctk.CTkSegmentedButton(
            self.hyd_card,
            values=["200ml", "250ml", "500ml"],
            command=self.on_drink_size_changed,
            selected_color="#00adb5",
            selected_hover_color="#008c92",
            height=28
        )
        self.drink_size_selector.pack(fill="x", padx=20, pady=5)
        self.drink_size_selector.set("250ml")
        
        # Log Water Button
        self.log_btn = ctk.CTkButton(
            self.hyd_card, 
            text="💧 RECORD DRINK (+250ml)", 
            font=("Helvetica", 12, "bold"), 
            fg_color="#00adb5", 
            hover_color="#008c92", 
            text_color="#ffffff",
            height=35,
            corner_radius=18,
            command=self.log_water
        )
        self.log_btn.pack(fill="x", padx=20, pady=(5, 15))

    def create_general_stats_card(self):
        self.stats_card = ctk.CTkFrame(self, fg_color="#1e1e1e", corner_radius=15, border_width=1, border_color="#2e2e2e")
        self.stats_card.grid(row=1, column=0, padx=15, pady=5, sticky="nsew")
        
        title_lbl = ctk.CTkLabel(
            self.stats_card, 
            text="REMINDER METRICS", 
            font=("Helvetica", 13, "bold"), 
            text_color="#ffffff"
        )
        title_lbl.pack(anchor="w", padx=20, pady=(15, 10))
        
        # Total Reminders Panel
        self.total_rem_lbl = ctk.CTkLabel(
            self.stats_card, 
            text="Total Reminders Scheduled: --", 
            font=("Helvetica", 12, "bold"), 
            text_color="#aaaaaa"
        )
        self.total_rem_lbl.pack(anchor="w", padx=20, pady=5)
        
        # Active Reminders Panel
        self.active_rem_lbl = ctk.CTkLabel(
            self.stats_card, 
            text="Active (Enabled) Reminders: --", 
            font=("Helvetica", 12, "bold"), 
            text_color="#30d158"
        )
        self.active_rem_lbl.pack(anchor="w", padx=20, pady=5)
        
        # Triggered count
        self.triggered_count_lbl = ctk.CTkLabel(
            self.stats_card, 
            text="Total Triggered Alerts: --", 
            font=("Helvetica", 12, "bold"), 
            text_color="#ff9f0a"
        )
        self.triggered_count_lbl.pack(anchor="w", padx=20, pady=5)

    def create_control_card(self):
        self.ctrl_card = ctk.CTkFrame(self, fg_color="#1e1e1e", corner_radius=15, border_width=1, border_color="#2e2e2e")
        self.ctrl_card.grid(row=1, column=1, padx=15, pady=5, sticky="nsew")
        
        title_lbl = ctk.CTkLabel(
            self.ctrl_card, 
            text="PAUSE & CONTROL", 
            font=("Helvetica", 13, "bold"), 
            text_color="#ffffff"
        )
        title_lbl.pack(anchor="w", padx=20, pady=(15, 5))
        
        # Status Label
        self.status_lbl = ctk.CTkLabel(
            self.ctrl_card, 
            text="STATUS: Active", 
            font=("Helvetica", 13, "bold"), 
            text_color="#30d158"
        )
        self.status_lbl.pack(anchor="w", padx=20, pady=2)
        
        # Next water countdown / info
        self.countdown_lbl = ctk.CTkLabel(
            self.ctrl_card, 
            text="Next water reminder: Loading...", 
            font=("Helvetica", 11), 
            text_color="#aaaaaa"
        )
        self.countdown_lbl.pack(anchor="w", padx=20, pady=(0, 10))
        
        # Pause Duration selection
        select_lbl = ctk.CTkLabel(self.ctrl_card, text="Quick Pause Reminders:", font=("Helvetica", 11), text_color="#888888")
        select_lbl.pack(anchor="w", padx=20, pady=(5, 2))
        
        self.pause_combobox = ctk.CTkComboBox(
            self.ctrl_card, 
            values=["30 Minutes", "1 Hour", "2 Hours", "Custom..."],
            fg_color="#2b2b2b",
            border_color="#3a3a3a",
            button_color="#3a3a3a",
            button_hover_color="#4a4a4a",
            dropdown_fg_color="#2b2b2b",
            state="readonly",
            height=30
        )
        self.pause_combobox.pack(fill="x", padx=20, pady=(0, 8))
        self.pause_combobox.set("30 Minutes")
        
        # Apply Pause / Resume buttons
        btn_frame = ctk.CTkFrame(self.ctrl_card, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(5, 15))
        
        self.pause_btn = ctk.CTkButton(
            btn_frame, 
            text="PAUSE", 
            font=("Helvetica", 11, "bold"), 
            fg_color="#ff9f0a", 
            hover_color="#e08b08",
            text_color="#ffffff",
            height=32,
            width=80,
            corner_radius=16,
            command=self.apply_pause
        )
        self.pause_btn.pack(side="left", fill="x", expand=True, padx=(0, 3))
        
        self.resume_btn = ctk.CTkButton(
            btn_frame, 
            text="RESUME", 
            font=("Helvetica", 11, "bold"), 
            fg_color="#333333", 
            hover_color="#444444",
            text_color="#888888",
            height=32,
            width=80,
            corner_radius=16,
            command=self.apply_resume
        )
        self.resume_btn.pack(side="left", fill="x", expand=True, padx=(3, 0))

    def create_weekly_chart_card(self):
        self.chart_card = ctk.CTkFrame(self, fg_color="#1e1e1e", corner_radius=15, border_width=1, border_color="#2e2e2e")
        self.chart_card.grid(row=2, column=0, columnspan=2, padx=15, pady=10, sticky="ew")
        
        lbl = ctk.CTkLabel(self.chart_card, text="📊 WEEKLY HYDRATION HISTORY (Last 7 Days)", font=("Helvetica", 13, "bold"), text_color="#ffffff")
        lbl.pack(anchor="w", padx=20, pady=(15, 5))
        
        self.bars_frame = ctk.CTkFrame(self.chart_card, fg_color="transparent")
        self.bars_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        self.draw_weekly_chart()

    def create_upcoming_timeline_card(self):
        self.timeline_card = ctk.CTkFrame(self, fg_color="#1e1e1e", corner_radius=15, border_width=1, border_color="#2e2e2e")
        self.timeline_card.grid(row=2, column=0, columnspan=2, padx=15, pady=10, sticky="nsew")
        
        lbl = ctk.CTkLabel(self.timeline_card, text="⏰ UPCOMING REMINDERS TIMELINE (Next 24h)", font=("Helvetica", 13, "bold"), text_color="#ffffff")
        lbl.pack(anchor="w", padx=20, pady=(15, 5))
        
        self.timeline_frame = ctk.CTkFrame(self.timeline_card, fg_color="transparent")
        self.timeline_frame.pack(fill="both", expand=True, padx=20, pady=(0, 15))

    def draw_weekly_chart(self):
        # Clear frame
        for child in self.bars_frame.winfo_children():
            child.destroy()
            
        today = datetime.now().date()
        days = []
        for i in range(6, -1, -1):
            d = today - timedelta(days=i)
            days.append(d)
            
        history = self.settings.get("stats_history", {})
        target = self.settings.get("hydration_target", 2000)
        
        for idx, d in enumerate(days):
            day_frame = ctk.CTkFrame(self.bars_frame, fg_color="transparent")
            day_frame.grid(row=0, column=idx, padx=5, sticky="nsew")
            self.bars_frame.grid_columnconfigure(idx, weight=1)
            
            # ml label
            date_str = d.strftime("%Y-%m-%d")
            ml = history.get(date_str, 0)
            
            ml_lbl = ctk.CTkLabel(day_frame, text=f"{ml}ml", font=("Helvetica", 9), text_color="#aaaaaa")
            ml_lbl.pack()
            
            # bar container
            bar_container = ctk.CTkFrame(day_frame, width=28, height=75, fg_color="#2c2c2c", corner_radius=4)
            bar_container.pack(pady=3)
            bar_container.pack_propagate(False)
            
            # fill
            pct = min(1.0, ml / target) if target > 0 else 0
            fill_height = max(1, int(pct * 75))
            bar_fill = ctk.CTkFrame(bar_container, fg_color="#00adb5", height=fill_height, corner_radius=3)
            bar_fill.pack(side="bottom", fill="x")
            
            # day label
            day_lbl = ctk.CTkLabel(day_frame, text=d.strftime("%a"), font=("Helvetica", 10, "bold"), text_color="#ffffff")
            day_lbl.pack()

    def update_upcoming_timeline(self):
        # Clear frame
        for child in self.timeline_frame.winfo_children():
            child.destroy()
            
        upcoming = self.get_upcoming_reminders()
        if not upcoming:
            empty_lbl = ctk.CTkLabel(
                self.timeline_frame, 
                text="No active reminders are scheduled.", 
                font=("Helvetica", 11, "italic"), 
                text_color="#666666"
            )
            empty_lbl.pack(pady=15)
            return
            
        now = time.time()
        # Display top 4 upcoming reminders
        for item in upcoming[:4]:
            r_frame = ctk.CTkFrame(self.timeline_frame, fg_color="#252525", corner_radius=8, height=35)
            r_frame.pack(fill="x", pady=3)
            r_frame.pack_propagate(False)
            
            # Info text
            time_left = max(0, int(item["epoch"] - now))
            m, s = divmod(time_left, 60)
            h, m = divmod(m, 60)
            
            if h > 0:
                cd_str = f"{h}h {m}m"
            else:
                cd_str = f"{m}m {s}s"
                
            trigger_type = item["trigger_type"]
            if trigger_type == "Time of Day":
                # convert 24h
                try:
                    dt = datetime.strptime(item["time_str"], "%H:%M")
                    trigger_desc = f"at {dt.strftime('%I:%M %p')}"
                except Exception:
                    trigger_desc = f"at {item['time_str']}"
            else:
                trigger_desc = f"every {item['interval_mins']}m"
                
            info_lbl = ctk.CTkLabel(
                r_frame, 
                text=f"🔔  {item['title']} ({trigger_desc})", 
                font=("Helvetica", 12, "bold"),
                text_color="#ffffff"
            )
            info_lbl.pack(side="left", padx=15)
            
            cd_lbl = ctk.CTkLabel(
                r_frame, 
                text=f"in {cd_str}", 
                font=("Helvetica", 11, "bold"), 
                text_color="#00adb5"
            )
            cd_lbl.pack(side="right", padx=15)

    def get_upcoming_reminders(self):
        reminders = self.settings.get("reminders", [])
        active_list = []
        now = time.time()
        
        for r_dict in reminders:
            if not r_dict.get("enabled", True):
                continue
            
            trigger_type = r_dict.get("trigger_type", "Time of Day")
            title = r_dict.get("title", "Reminder")
            
            if trigger_type == "Time of Day":
                time_str = r_dict.get("time", "12:00")
                try:
                    r_hour, r_min = map(int, time_str.split(":"))
                    dt = datetime.now()
                    target_dt = dt.replace(hour=r_hour, minute=r_min, second=0, microsecond=0)
                    if target_dt.timestamp() < now:
                        target_dt += timedelta(days=1)
                    epoch = target_dt.timestamp()
                except Exception:
                    continue
            else:
                interval_mins = r_dict.get("interval_mins", 30)
                last_trig = r_dict.get("last_triggered_time", 0.0)
                if last_trig == 0.0:
                    epoch = now + interval_mins * 60
                else:
                    epoch = last_trig + interval_mins * 60
                    
            active_list.append({
                "title": title,
                "epoch": epoch,
                "trigger_type": trigger_type,
                "time_str": r_dict.get("time", "12:00"),
                "interval_mins": r_dict.get("interval_mins", 30)
            })
            
        # Sort by epoch ascending
        active_list.sort(key=lambda x: x["epoch"])
        return active_list

    def update_stats(self):
        """Updates the dashboard interface elements with the latest values from settings."""
        # Auto rebuild layout if setting was toggled in the background
        current_setting = self.settings.get("hydration_mode_enabled", False)
        if self.active_hydration_mode != current_setting:
            self.rebuild_layout()
            return
            
        # 1. Update status and toggle controls
        if self.scheduler.is_paused():
            pause_end = self.settings.get("active_pause_end", 0)
            time_left = max(0, int(pause_end - time.time()))
            m, s = divmod(time_left, 60)
            h, m = divmod(m, 60)
            
            time_str = f"{m}m {s}s" if h == 0 else f"{h}h {m}m"
            self.status_lbl.configure(text=f"PAUSED (Ends in {time_str})", text_color="#ff9f0a")
            self.countdown_lbl.configure(text="Reminders suspended.")
            self.pause_btn.configure(state="disabled", fg_color="#555555")
            self.resume_btn.configure(state="normal", fg_color="#30d158", text_color="#ffffff")
        else:
            self.status_lbl.configure(text="STATUS: ACTIVE", text_color="#30d158")
            self.pause_btn.configure(state="normal", fg_color="#ff9f0a")
            self.resume_btn.configure(state="disabled", fg_color="#2c2c2c", text_color="#666666")
            
            # Update next reminder text in Control card
            if self.active_hydration_mode:
                seconds = self.scheduler.get_water_countdown()
                if seconds > 0:
                    m, s = divmod(seconds, 60)
                    self.countdown_lbl.configure(text=f"Next water reminder: {m}m {s}s")
                else:
                    self.countdown_lbl.configure(text="No water-related reminders active.")
            else:
                upcoming = self.get_upcoming_reminders()
                if upcoming:
                    seconds = max(0, int(upcoming[0]["epoch"] - time.time()))
                    m, s = divmod(seconds, 60)
                    h, m = divmod(m, 60)
                    cd_str = f"{h}h {m}m" if h > 0 else f"{m}m {s}s"
                    self.countdown_lbl.configure(text=f"Next reminder: '{upcoming[0]['title']}' in {cd_str}")
                else:
                    self.countdown_lbl.configure(text="No active reminders.")

        # 2. Update stats based on mode
        if self.active_hydration_mode:
            intake_target = self.settings.get("hydration_target", 2000)
            cups_drank = self.settings.get("stats_cups_logged", 0.0)
            ml_drank = int(cups_drank * 250)
            
            progress = min(1.0, ml_drank / intake_target) if intake_target > 0 else 0
            self.progress_bar.set(progress)
            self.progress_lbl.configure(text=f"{ml_drank} ml / {intake_target} ml ({int(progress*100)}%)")
            
            # Streak
            streak = self.settings.get("stats_streak", 0)
            self.streak_lbl.configure(text=f"Streak: {streak} Day{'s' if streak != 1 else ''}")
            
            self.draw_weekly_chart()
        else:
            reminders = self.settings.get("reminders", [])
            total_count = len(reminders)
            active_count = sum(1 for r in reminders if r.get("enabled", True))
            triggered_count = self.settings.get("stats_total_reminders_triggered", 0)
            
            self.total_rem_lbl.configure(text=f"Total Reminders Scheduled: {total_count}")
            self.active_rem_lbl.configure(text=f"Active (Enabled) Reminders: {active_count}")
            self.triggered_count_lbl.configure(text=f"Total Triggered Alerts: {triggered_count}")
            
            self.update_upcoming_timeline()

    def on_drink_size_changed(self, val):
        self.log_btn.configure(text=f"💧 RECORD DRINK (+{val})")

    def log_water(self):
        """Action when 'Record Drink' button is pressed."""
        val_str = self.drink_size_selector.get()
        try:
            # e.g., "250ml" -> 250
            amount_ml = int(val_str.replace("ml", ""))
        except Exception:
            amount_ml = 250
            
        self.settings.log_water_intake(amount_ml)
        log_event("water_logged", f"User logged {amount_ml}ml of water via dashboard.")
        
        # Play a sound asynchronously if configured
        if not self.settings.get("silent_mode", False) and self.settings.get("sound_enabled", True):
            from utils.sound import play_alert_sound
            custom_sound = self.settings.get("custom_sound_file", "")
            play_alert_sound(custom_sound if custom_sound else None, silent=False)
            
        self.update_stats()

    def apply_pause(self):
        """Action when 'Pause' button is pressed."""
        sel = self.pause_combobox.get()
        minutes = 30
        
        if sel == "30 Minutes":
            minutes = 30
        elif sel == "1 Hour":
            minutes = 60
        elif sel == "2 Hours":
            minutes = 120
        elif sel == "Custom...":
            # Ask for custom minutes using a dialog
            dialog = ctk.CTkInputDialog(text="Enter pause duration (minutes):", title="Custom Pause")
            try:
                res = dialog.get_input()
                if res:
                    minutes = int(res)
                    if minutes <= 0:
                        raise ValueError()
                else:
                    return  # Cancelled
            except ValueError:
                # Show error dialog
                from tkinter import messagebox
                messagebox.showerror("Invalid Input", "Please enter a valid positive integer of minutes.")
                return
                
        now = time.time()
        pause_end = now + (minutes * 60)
        self.settings.set("active_pause_end", pause_end)
        log_event("pause_activated", f"Reminders paused for {minutes} minutes.")
        self.update_stats()

    def apply_resume(self):
        """Action when 'Resume' button is pressed."""
        self.settings.set("active_pause_end", None)
        log_event("resume_activated", "Reminders resumed manually by user.")
        self.update_stats()
