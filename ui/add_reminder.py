import uuid
import time
import customtkinter as ctk
from datetime import datetime
from utils.logger import log_event

class AddReminderView(ctk.CTkFrame):
    def __init__(self, parent, settings_manager, navigate_callback):
        super().__init__(parent, fg_color="transparent")
        self.settings = settings_manager
        self.navigate_callback = navigate_callback  # Callback to switch tabs after adding
        self.edit_id = None
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Form Container
        self.form_card = ctk.CTkFrame(self, fg_color="#1e1e1e", corner_radius=15, border_width=1, border_color="#2e2e2e")
        self.form_card.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")
        self.form_card.grid_columnconfigure(1, weight=1)
        
        # Title
        self.title_lbl = ctk.CTkLabel(self.form_card, text="📅 CREATE NEW REMINDER", font=("Helvetica", 16, "bold"), text_color="#00adb5")
        self.title_lbl.grid(row=0, column=0, columnspan=2, padx=25, pady=(20, 15), sticky="w")
        
        # Reminder Title Input
        row = 1
        ctk.CTkLabel(self.form_card, text="Title:", font=("Helvetica", 12, "bold"), text_color="#aaaaaa").grid(row=row, column=0, padx=(25, 10), pady=10, sticky="w")
        self.title_entry = ctk.CTkEntry(self.form_card, placeholder_text="e.g. Stretch Break, Drink Water", fg_color="#2b2b2b", border_color="#3a3a3a")
        self.title_entry.grid(row=row, column=1, padx=(10, 25), pady=10, sticky="ew")
        
        # Message Input
        row = 2
        ctk.CTkLabel(self.form_card, text="Message:", font=("Helvetica", 12, "bold"), text_color="#aaaaaa").grid(row=row, column=0, padx=(25, 10), pady=10, sticky="w")
        self.msg_entry = ctk.CTkEntry(self.form_card, placeholder_text="Enter reminder details...", fg_color="#2b2b2b", border_color="#3a3a3a")
        self.msg_entry.grid(row=row, column=1, padx=(10, 25), pady=10, sticky="ew")
        
        # Trigger Type Selection (Time of Day vs Interval)
        row = 3
        ctk.CTkLabel(self.form_card, text="Trigger Type:", font=("Helvetica", 12, "bold"), text_color="#aaaaaa").grid(row=row, column=0, padx=(25, 10), pady=10, sticky="w")
        
        self.trigger_type_var = ctk.StringVar(value="Time of Day")
        self.trigger_type_btn = ctk.CTkSegmentedButton(
            self.form_card,
            values=["Time of Day", "Interval"],
            variable=self.trigger_type_var,
            command=self.on_trigger_type_changed,
            selected_color="#00adb5",
            selected_hover_color="#008c92",
            height=32
        )
        self.trigger_type_btn.grid(row=row, column=1, padx=(10, 25), pady=10, sticky="w")
        
        # Trigger Values input container
        row = 4
        self.trigger_value_lbl = ctk.CTkLabel(self.form_card, text="Time:", font=("Helvetica", 12, "bold"), text_color="#aaaaaa")
        self.trigger_value_lbl.grid(row=row, column=0, padx=(25, 10), pady=10, sticky="w")
        
        self.trigger_inputs_container = ctk.CTkFrame(self.form_card, fg_color="transparent")
        self.trigger_inputs_container.grid(row=row, column=1, padx=(10, 25), pady=10, sticky="w")
        self.trigger_inputs_container.grid_columnconfigure(0, weight=1)
        self.trigger_inputs_container.grid_rowconfigure(0, weight=1)
        
        # Panel 1: Time of Day picker
        self.time_picker_frame = ctk.CTkFrame(self.trigger_inputs_container, fg_color="transparent")
        self.time_picker_frame.grid(row=0, column=0, sticky="w")
        
        # Hour dropdown
        self.hour_cb = ctk.CTkComboBox(
            self.time_picker_frame, 
            values=[f"{i:02d}" for i in range(1, 13)], 
            width=65, 
            fg_color="#2b2b2b", 
            border_color="#3a3a3a", 
            button_color="#3a3a3a",
            state="readonly"
        )
        self.hour_cb.pack(side="left", padx=(0, 5))
        self.hour_cb.set("12")
        
        # Colon label
        ctk.CTkLabel(self.time_picker_frame, text=":", font=("Helvetica", 12, "bold")).pack(side="left", padx=2)
        
        # Minute dropdown
        self.minute_cb = ctk.CTkComboBox(
            self.time_picker_frame, 
            values=[f"{i:02d}" for i in range(60)], 
            width=65, 
            fg_color="#2b2b2b", 
            border_color="#3a3a3a", 
            button_color="#3a3a3a",
            state="readonly"
        )
        self.minute_cb.pack(side="left", padx=5)
        self.minute_cb.set("00")
        
        # AM/PM dropdown
        self.ampm_cb = ctk.CTkComboBox(
            self.time_picker_frame, 
            values=["AM", "PM"], 
            width=65, 
            fg_color="#2b2b2b", 
            border_color="#3a3a3a", 
            button_color="#3a3a3a",
            state="readonly"
        )
        self.ampm_cb.pack(side="left", padx=5)
        self.ampm_cb.set("PM")
        
        # Panel 2: Interval entry
        self.interval_picker_frame = ctk.CTkFrame(self.trigger_inputs_container, fg_color="transparent")
        
        self.interval_entry = ctk.CTkEntry(
            self.interval_picker_frame, 
            placeholder_text="e.g. 20", 
            width=80, 
            fg_color="#2b2b2b", 
            border_color="#3a3a3a"
        )
        self.interval_entry.pack(side="left", padx=(0, 5))
        self.interval_entry.insert(0, "20")
        
        ctk.CTkLabel(self.interval_picker_frame, text="minutes", font=("Helvetica", 12), text_color="#aaaaaa").pack(side="left")

        # Mode Selection (Only 2 options: Notification, Fullscreen Popup)
        row = 5
        ctk.CTkLabel(self.form_card, text="Alert Mode:", font=("Helvetica", 12, "bold"), text_color="#aaaaaa").grid(row=row, column=0, padx=(25, 10), pady=10, sticky="w")
        self.mode_cb = ctk.CTkComboBox(
            self.form_card, 
            values=["Notification", "Fullscreen Popup"], 
            fg_color="#2b2b2b", 
            border_color="#3a3a3a", 
            button_color="#3a3a3a",
            state="readonly"
        )
        self.mode_cb.grid(row=row, column=1, padx=(10, 25), pady=10, sticky="w")
        self.mode_cb.set("Notification")
        
        # Priority Selection
        row = 6
        ctk.CTkLabel(self.form_card, text="Priority:", font=("Helvetica", 12, "bold"), text_color="#aaaaaa").grid(row=row, column=0, padx=(25, 10), pady=10, sticky="w")
        self.priority_cb = ctk.CTkComboBox(
            self.form_card, 
            values=["low", "medium", "high"], 
            fg_color="#2b2b2b", 
            border_color="#3a3a3a", 
            button_color="#3a3a3a",
            state="readonly"
        )
        self.priority_cb.grid(row=row, column=1, padx=(10, 25), pady=10, sticky="w")
        self.priority_cb.set("low")

        # Submit Button
        row = 7
        self.submit_btn = ctk.CTkButton(
            self.form_card,
            text="💾 ADD NEW REMINDER",
            font=("Helvetica", 13, "bold"),
            fg_color="#00adb5",
            hover_color="#008c92",
            height=40,
            corner_radius=20,
            command=self.save_reminder
        )
        self.submit_btn.grid(row=row, column=0, columnspan=2, padx=25, pady=25, sticky="ew")

    def on_trigger_type_changed(self, choice):
        if choice == "Time of Day":
            self.trigger_value_lbl.configure(text="Time:")
            self.interval_picker_frame.grid_forget()
            self.time_picker_frame.grid(row=0, column=0, sticky="w")
        else:
            self.trigger_value_lbl.configure(text="Repeat Every:")
            self.time_picker_frame.grid_forget()
            self.interval_picker_frame.grid(row=0, column=0, sticky="w")

    def save_reminder(self):
        title = self.title_entry.get().strip()
        msg = self.msg_entry.get().strip()
        trigger_type = self.trigger_type_var.get()
        
        if not title:
            from tkinter import messagebox
            messagebox.showerror("Validation Error", "Title cannot be empty.")
            return
            
        if not msg:
            from tkinter import messagebox
            messagebox.showerror("Validation Error", "Message cannot be empty.")
            return
            
        time_24h = "12:00"
        interval_mins = 30
        
        if trigger_type == "Time of Day":
            # Parse time to 24h HH:MM format
            hour = self.hour_cb.get()
            minute = self.minute_cb.get()
            ampm = self.ampm_cb.get()
            
            try:
                time_input = f"{hour}:{minute} {ampm}"
                parsed_dt = datetime.strptime(time_input, "%I:%M %p")
                time_24h = parsed_dt.strftime("%H:%M")
            except Exception as e:
                from tkinter import messagebox
                messagebox.showerror("Time Parsing Error", f"Could not parse the selected time: {e}")
                return
        else:
            # Parse interval minutes
            val_str = self.interval_entry.get().strip()
            try:
                interval_mins = int(val_str)
                if interval_mins <= 0:
                    raise ValueError()
            except ValueError:
                from tkinter import messagebox
                messagebox.showerror("Validation Error", "Please enter a valid positive integer for interval minutes.")
                return
            
        # Formulate general reminder dict
        reminder_id = str(uuid.uuid4().hex[:8])
        new_reminder = {
            "id": reminder_id,
            "title": title,
            "message": msg,
            "trigger_type": trigger_type,
            "time": time_24h,
            "interval_mins": interval_mins,
            "mode_type": self.mode_cb.get(),
            "priority": self.priority_cb.get(),
            "enabled": True,
            "last_triggered_time": time.time() if trigger_type == "Interval" else 0.0,
            "last_triggered_date": ""
        }
        
        reminders = self.settings.get("reminders", [])
        
        if self.edit_id:
            # Edit mode: Find the existing reminder and update it
            success_msg = f"Reminder '{title}' updated successfully!"
            reminder_found = False
            for r in reminders:
                if r.get("id") == self.edit_id:
                    r["title"] = title
                    r["message"] = msg
                    r["trigger_type"] = trigger_type
                    r["time"] = time_24h
                    r["interval_mins"] = interval_mins
                    r["mode_type"] = self.mode_cb.get()
                    r["priority"] = self.priority_cb.get()
                    # Preserve enabled status and last triggered info, but reset if trigger type changed
                    if trigger_type == "Interval":
                        if "last_triggered_time" not in r or r.get("trigger_type") != trigger_type:
                            r["last_triggered_time"] = time.time()
                    else:
                        r["last_triggered_time"] = 0.0
                        r["last_triggered_date"] = ""
                    reminder_found = True
                    break
            
            if not reminder_found:
                # Fallback to create if not found
                new_reminder = {
                    "id": self.edit_id,
                    "title": title,
                    "message": msg,
                    "trigger_type": trigger_type,
                    "time": time_24h,
                    "interval_mins": interval_mins,
                    "mode_type": self.mode_cb.get(),
                    "priority": self.priority_cb.get(),
                    "enabled": True,
                    "last_triggered_time": time.time() if trigger_type == "Interval" else 0.0,
                    "last_triggered_date": ""
                }
                reminders.append(new_reminder)
                
            self.settings.set("reminders", reminders)
            log_event("reminder_updated", f"Updated reminder: '{title}' ({trigger_type}, Mode: {self.mode_cb.get()})")
        else:
            # Create mode: Generate a new ID and append
            reminder_id = str(uuid.uuid4().hex[:8])
            new_reminder = {
                "id": reminder_id,
                "title": title,
                "message": msg,
                "trigger_type": trigger_type,
                "time": time_24h,
                "interval_mins": interval_mins,
                "mode_type": self.mode_cb.get(),
                "priority": self.priority_cb.get(),
                "enabled": True,
                "last_triggered_time": time.time() if trigger_type == "Interval" else 0.0,
                "last_triggered_date": ""
            }
            reminders.append(new_reminder)
            self.settings.set("reminders", reminders)
            log_event("reminder_added", f"Added reminder: '{title}' ({trigger_type}, Mode: {self.mode_cb.get()})")
            success_msg = f"Reminder '{title}' added successfully!"
            
        # Reset form fields
        self.reset_form()
        
        from tkinter import messagebox
        messagebox.showinfo("Success", success_msg)
        
        # Switch tab back to Active Reminders list
        if self.navigate_callback:
            self.navigate_callback("active")

    def set_edit_mode(self, reminder_dict):
        self.edit_id = reminder_dict.get("id")
        
        self.title_entry.delete(0, "end")
        self.title_entry.insert(0, reminder_dict.get("title", ""))
        
        self.msg_entry.delete(0, "end")
        self.msg_entry.insert(0, reminder_dict.get("message", ""))
        
        trigger_type = reminder_dict.get("trigger_type", "Time of Day")
        self.trigger_type_var.set(trigger_type)
        self.on_trigger_type_changed(trigger_type)
        
        if trigger_type == "Time of Day":
            time_str = reminder_dict.get("time", "12:00")
            try:
                dt = datetime.strptime(time_str, "%H:%M")
                self.hour_cb.set(dt.strftime("%I"))
                self.minute_cb.set(dt.strftime("%M"))
                self.ampm_cb.set(dt.strftime("%p"))
            except Exception:
                self.hour_cb.set("12")
                self.minute_cb.set("00")
                self.ampm_cb.set("PM")
        else:
            interval_mins = reminder_dict.get("interval_mins", 20)
            self.interval_entry.delete(0, "end")
            self.interval_entry.insert(0, str(interval_mins))
            
        self.mode_cb.set(reminder_dict.get("mode_type", "Notification"))
        self.priority_cb.set(reminder_dict.get("priority", "low"))
        
        self.title_lbl.configure(text="📅 EDIT REMINDER", text_color="#ff9f0a")
        self.submit_btn.configure(text="💾 SAVE CHANGES", fg_color="#ff9f0a", hover_color="#e08b08")

    def reset_form(self):
        self.edit_id = None
        self.title_entry.delete(0, "end")
        self.msg_entry.delete(0, "end")
        self.hour_cb.set("12")
        self.minute_cb.set("00")
        self.ampm_cb.set("PM")
        self.interval_entry.delete(0, "end")
        self.interval_entry.insert(0, "20")
        self.mode_cb.set("Notification")
        self.priority_cb.set("low")
        self.trigger_type_var.set("Time of Day")
        self.on_trigger_type_changed("Time of Day")
        
        self.title_lbl.configure(text="📅 CREATE NEW REMINDER", text_color="#00adb5")
        self.submit_btn.configure(text="💾 ADD NEW REMINDER", fg_color="#00adb5", hover_color="#008c92")
