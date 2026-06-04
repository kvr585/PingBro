import customtkinter as ctk
from datetime import datetime
from utils.logger import log_event

class ActiveRemindersView(ctk.CTkFrame):
    def __init__(self, parent, settings_manager, edit_callback=None):
        super().__init__(parent, fg_color="transparent")
        self.settings = settings_manager
        self.edit_callback = edit_callback
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # 1. Reminders List Container
        self.create_reminders_list()

    def create_reminders_list(self):
        # Daily Reminders frame
        self.daily_frame = ctk.CTkFrame(self, fg_color="#1e1e1e", corner_radius=15, border_width=1, border_color="#2e2e2e")
        self.daily_frame.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")
        
        header_lbl = ctk.CTkLabel(
            self.daily_frame, 
            text="⏰ ACTIVE SCHEDULED REMINDERS", 
            font=("Helvetica", 14, "bold"), 
            text_color="#ffffff"
        )
        header_lbl.pack(anchor="w", padx=20, pady=(15, 10))
        
        # Scrollable container for the reminders
        self.scroll_frame = ctk.CTkScrollableFrame(
            self.daily_frame, 
            fg_color="transparent",
            scrollbar_button_color="#2c2c2c",
            scrollbar_button_hover_color="#3a3a3a"
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        self.populate_daily_reminders()

    def populate_daily_reminders(self):
        # Clear existing items in scroll frame
        for child in self.scroll_frame.winfo_children():
            child.destroy()
            
        reminders = self.settings.get("reminders", [])
        if not reminders:
            empty_lbl = ctk.CTkLabel(
                self.scroll_frame, 
                text="No reminders configured.\nGo to 'Add Reminder' to schedule a new one.", 
                font=("Helvetica", 12, "italic"), 
                text_color="#666666"
            )
            empty_lbl.pack(pady=40)
            return

        for r in reminders:
            # Create a card for each reminder
            item_card = ctk.CTkFrame(self.scroll_frame, fg_color="#252525", corner_radius=10, border_width=1, border_color="#333333")
            item_card.pack(fill="x", pady=5, padx=2)
            
            # Left part: text details
            text_frame = ctk.CTkFrame(item_card, fg_color="transparent")
            text_frame.pack(side="left", fill="both", expand=True, padx=15, pady=10)
            
            # Formatted priority badge color
            priority = r.get("priority", "low")
            p_colors = {"low": "#30d158", "medium": "#ff9f0a", "high": "#ff453a"}
            p_color = p_colors.get(priority, "#30d158")
            
            # Convert trigger type description nicely for user view
            trigger_type = r.get("trigger_type", "Time of Day")
            if trigger_type == "Time of Day":
                time_str = r.get("time", "12:00")
                try:
                    dt = datetime.strptime(time_str, "%H:%M")
                    display_trigger = f"⏰ Daily at {dt.strftime('%I:%M %p')}"
                except Exception:
                    display_trigger = f"⏰ Daily at {time_str}"
            else:
                interval_mins = r.get("interval_mins", 30)
                display_trigger = f"🔁 Every {interval_mins} minutes"
                
            title_lbl = ctk.CTkLabel(
                text_frame, 
                text=f"{r.get('title')}  ({display_trigger})", 
                font=("Helvetica", 13, "bold"), 
                text_color="#ffffff"
            )
            title_lbl.pack(anchor="w")
            
            desc_lbl = ctk.CTkLabel(
                text_frame, 
                text=r.get("message", ""), 
                font=("Helvetica", 11), 
                text_color="#888888",
                wraplength=450,
                justify="left"
            )
            desc_lbl.pack(anchor="w", pady=(2, 0))
            
            tags_lbl = ctk.CTkLabel(
                text_frame, 
                text=f"Mode: {r.get('mode_type')}  |  Priority: {priority.upper()}", 
                font=("Helvetica", 10, "bold"), 
                text_color=p_color
            )
            tags_lbl.pack(anchor="w", pady=(4, 0))
            
            # Bind card click to edit callback if present
            if self.edit_callback:
                click_handler = lambda event, reminder=r: self.edit_callback(reminder)
                item_card.bind("<Button-1>", click_handler)
                text_frame.bind("<Button-1>", click_handler)
                title_lbl.bind("<Button-1>", click_handler)
                desc_lbl.bind("<Button-1>", click_handler)
                tags_lbl.bind("<Button-1>", click_handler)
                
                # Apply pointer cursor to signal interactivity
                item_card.configure(cursor="hand2")
                text_frame.configure(cursor="hand2")
                title_lbl.configure(cursor="hand2")
                desc_lbl.configure(cursor="hand2")
                tags_lbl.configure(cursor="hand2")
            
            # Right part: controls (Toggle and Delete button)
            ctrls_frame = ctk.CTkFrame(item_card, fg_color="transparent")
            ctrls_frame.pack(side="right", fill="y", padx=15, pady=10)
            
            # Switch
            # We capture the reminder ID inside the lambda using default arg binding
            enabled_switch = ctk.CTkSwitch(
                ctrls_frame,
                text="",
                progress_color="#00adb5",
                command=lambda rid=r.get("id"): self.toggle_daily_reminder(rid)
            )
            enabled_switch.pack(side="left", padx=10)
            enabled_switch.select() if r.get("enabled") else enabled_switch.deselect()
            
            # Delete button
            del_btn = ctk.CTkButton(
                ctrls_frame,
                text="🗑️",
                font=("Segoe UI", 12),
                fg_color="transparent",
                text_color="#ff453a",
                hover_color="#3a2525",
                width=30,
                height=30,
                corner_radius=5,
                command=lambda rid=r.get("id"): self.delete_daily_reminder(rid)
            )
            del_btn.pack(side="left")

    def toggle_daily_reminder(self, reminder_id):
        reminders = self.settings.get("reminders", [])
        for r in reminders:
            if r.get("id") == reminder_id:
                r["enabled"] = not r.get("enabled", True)
                break
        self.settings.set("reminders", reminders)
        log_event("settings_changed", f"Reminder ID {reminder_id} toggle changed.")

    def delete_daily_reminder(self, reminder_id):
        reminders = self.settings.get("reminders", [])
        updated = [r for r in reminders if r.get("id") != reminder_id]
        
        # Clean from trigger map
        trig_map = self.settings.get("daily_last_triggered", {})
        if reminder_id in trig_map:
            del trig_map[reminder_id]
            self.settings.set("daily_last_triggered", trig_map)
            
        self.settings.set("reminders", updated)
        log_event("settings_changed", f"Deleted reminder ID {reminder_id}")
        self.populate_daily_reminders()
