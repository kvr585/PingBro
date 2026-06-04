import time
import customtkinter as ctk
from ui.dashboard import DashboardView
from ui.active_reminders import ActiveRemindersView
from ui.add_reminder import AddReminderView
from ui.settings_page import SettingsView
from ui.logs_page import LogsView
from ui.overlays import FullscreenPopup
from utils.logger import log_event

class MainWindow(ctk.CTk):
    def __init__(self, settings_manager, scheduler_ref, hotkey_ref, tray_ref, exam_mode_handler, exit_handler):
        super().__init__()
        
        self.settings = settings_manager
        self.scheduler = scheduler_ref
        self.hotkey = hotkey_ref
        self.tray = tray_ref
        self.exam_mode_handler = exam_mode_handler
        self.exit_handler = exit_handler
        
        # Configure Window
        self.title("PingBro")
        self.geometry("850x550")
        self.resizable(True, True)  # Make window resizable
        
        # Bind F11 key to toggle fullscreen
        self.bind("<F11>", self.toggle_window_fullscreen)
        self.is_fullscreen = False
        
        # Override Close Window Protocol (Minimize to tray instead of close)
        self.protocol("WM_DELETE_WINDOW", self.minimize_to_tray)
        
        # Configure Layout Grid (Sidebar on left, Main content on right)
        self.grid_columnconfigure(0, weight=0)  # Sidebar fixed
        self.grid_columnconfigure(1, weight=1)  # Content flexible
        self.grid_rowconfigure(0, weight=1)
        
        # Current active tab tracking
        self.current_tab = None
        self.views = {}
        
        # 1. Create Sidebar GUI
        self.create_sidebar()
        
        # 2. Create Content Area & Load Views
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(1, weight=1)
        
        # Top Header Bar (Status, theme switcher, fullscreen)
        self.create_header()
        
        # Load View Panels
        self.views["dashboard"] = DashboardView(self.content_frame, self.settings, self.scheduler)
        self.views["active"] = ActiveRemindersView(self.content_frame, self.settings, edit_callback=self.trigger_edit)
        self.views["add"] = AddReminderView(self.content_frame, self.settings, self.show_tab)
        self.views["settings"] = SettingsView(self.content_frame, self.settings)
        self.views["logs"] = LogsView(self.content_frame)
        
        # Set default tab
        self.show_tab("dashboard")
        
        # Configure global theme styling
        theme = self.settings.get("theme", "Dark")
        ctk.set_appearance_mode(theme)
        
        # Start periodic UI status updates (like countdown timer)
        self.update_ui_loop()

    def create_sidebar(self):
        sidebar = ctk.CTkFrame(self, width=200, fg_color="#141417", corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_rowconfigure(7, weight=1)  # Push exam mode to bottom
        
        # Brand Header
        logo_lbl = ctk.CTkLabel(sidebar, text="PINGBRO", font=("Helvetica", 16, "bold"), text_color="#00adb5")
        logo_lbl.grid(row=0, column=0, padx=20, pady=(25, 20), sticky="w")
        
        # Navigation Buttons
        self.nav_btns = {}
        tabs = [
            ("dashboard", "📊 Dashboard"),
            ("active", "🔔 Active Reminders"),
            ("add", "➕ Add Reminder"),
            ("settings", "⚙️ Settings"),
            ("logs", "📜 Logs/History")
        ]
        
        for idx, (tab_id, name) in enumerate(tabs, start=1):
            btn = ctk.CTkButton(
                sidebar,
                text=name,
                font=("Helvetica", 12, "bold"),
                anchor="w",
                fg_color="transparent",
                text_color="#888888",
                hover_color="#2b2b2b",
                height=40,
                corner_radius=8,
                command=lambda tid=tab_id: self.show_tab(tid)
            )
            btn.grid(row=idx, column=0, padx=12, pady=5, sticky="ew")
            self.nav_btns[tab_id] = btn

        # Exam Mode Button (Emergency Shutdown)
        self.exam_btn = ctk.CTkButton(
            sidebar,
            text="⚠️ EXAM MODE",
            font=("Helvetica", 12, "bold"),
            fg_color="#ff453a",
            hover_color="#c9362e",
            text_color="#ffffff",
            height=45,
            corner_radius=8,
            command=self.exam_mode_handler
        )
        self.exam_btn.grid(row=8, column=0, padx=12, pady=25, sticky="ew")

    def create_header(self):
        header_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=(5, 5))
        
        # Title/Quick Info
        self.header_title = ctk.CTkLabel(header_frame, text="Active Status", font=("Helvetica", 14, "bold"), text_color="#ffffff")
        self.header_title.pack(side="left")
        
        # Quick Theme Switcher Toggle on header
        self.theme_toggle = ctk.CTkSwitch(
            header_frame,
            text="Light Mode",
            font=("Helvetica", 11, "bold"),
            progress_color="#00adb5",
            command=self.toggle_theme_quick
        )
        self.theme_toggle.pack(side="right", padx=10)
        
        # Quick Fullscreen Switcher Toggle on header
        self.fullscreen_toggle = ctk.CTkSwitch(
            header_frame,
            text="Fullscreen",
            font=("Helvetica", 11, "bold"),
            progress_color="#00adb5",
            command=self.toggle_fullscreen_quick
        )
        self.fullscreen_toggle.pack(side="right", padx=10)
        
        # Synchronize toggle switch state
        if self.settings.get("theme") == "Light":
            self.theme_toggle.select()
        else:
            self.theme_toggle.deselect()

    def show_tab(self, tab_id, reset_add=True):
        """Switches the right hand layout content frame to display the selected tab_id."""
        if tab_id == "add" and reset_add:
            self.views["add"].reset_form()

        if self.current_tab == tab_id:
            return
            
        # Hide current view
        if self.current_tab and self.current_tab in self.views:
            self.views[self.current_tab].grid_forget()
            self.nav_btns[self.current_tab].configure(fg_color="transparent", text_color="#888888")
            
        # Show new view
        self.current_tab = tab_id
        view = self.views[tab_id]
        view.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        # Highlight active sidebar button
        self.nav_btns[tab_id].configure(fg_color="#1f2d2e", text_color="#00adb5")
        
        # Refresh target views on switch
        if tab_id == "dashboard":
            view.update_stats()
        elif tab_id == "active":
            view.populate_daily_reminders()
        elif tab_id == "logs":
            view.refresh_history()

    def trigger_edit(self, reminder_dict):
        """Switches to the Add/Edit Reminder tab and populates values for editing."""
        self.views["add"].set_edit_mode(reminder_dict)
        self.show_tab("add", reset_add=False)

    def toggle_theme_quick(self):
        val = self.theme_toggle.get() == 1
        choice = "Light" if val else "Dark"
        self.settings.set("theme", choice)
        ctk.set_appearance_mode(choice)
        log_event("settings_changed", f"Appearance theme toggled quickly to {choice}")
        
        # Sync Settings view combobox if loaded
        if "settings" in self.views:
            self.views["settings"].theme_cb.set(choice)

    def toggle_fullscreen_quick(self):
        val = self.fullscreen_toggle.get() == 1
        self.is_fullscreen = val
        self.attributes("-fullscreen", val)
        log_event("window_resized", f"Fullscreen toggled to {val}")

    def toggle_window_fullscreen(self, event=None):
        self.is_fullscreen = not self.is_fullscreen
        self.attributes("-fullscreen", self.is_fullscreen)
        if self.is_fullscreen:
            self.fullscreen_toggle.select()
        else:
            self.fullscreen_toggle.deselect()
        log_event("window_resized", f"Fullscreen toggled via F11 to {self.is_fullscreen}")

    def minimize_to_tray(self):
        """Hides the application window, keeping it running in the background."""
        self.withdraw()
        log_event("window_minimized", "App window minimized to system tray.")

    def restore_from_tray(self):
        """Restores the application window to screen focus."""
        self.deiconify()
        self.focus_force()
        self.attributes("-topmost", True)
        self.after(100, lambda: self.attributes("-topmost", False))
        log_event("window_restored", "App window restored from system tray.")

    def update_ui_loop(self):
        """Ticks once a second to refresh dynamic values like timers and headers."""
        try:
            # Update header text showing quick state
            if self.scheduler.is_paused():
                pause_end = self.settings.get("active_pause_end", 0)
                left = max(0, int(pause_end - time.time()))
                m, s = divmod(left, 60)
                self.header_title.configure(text=f"Reminders paused ({m}m {s}s remaining)", text_color="#ff9f0a")
            else:
                self.header_title.configure(text="System Active & Running", text_color="#30d158")
                
            # If current view is dashboard, keep it ticking
            if self.current_tab == "dashboard":
                self.views["dashboard"].update_stats()
                
        except Exception as e:
            print(f"[UI Loop] Error ticking UI: {e}")
            
        self.after(1000, self.update_ui_loop)

    def trigger_visual_reminder(self, title, message, mode, priority, is_water):
        """
        Thread-safe callback executed on main thread via root.after().
        Instantiates overlays (Popups) on screen.
        """
        self.after(0, lambda: self._execute_visual_reminder(title, message, mode, priority, is_water))

    def _execute_visual_reminder(self, title, message, mode, priority, is_water):
        if mode == "Fullscreen Popup":
            # Show large modal centered popup alert
            FullscreenPopup(
                title=title, 
                message=message, 
                priority=priority, 
                is_water=is_water,
                on_dismiss=lambda choice: self.handle_reminder_dismissal(choice, is_water)
            )

    def handle_reminder_dismissal(self, choice, is_water):
        """Handles actions when alerts are dismissed or snooze/drink is logged."""
        if is_water:
            if choice == "drank":
                # Increment hydration statistics (logs standard cup size: 250ml)
                self.settings.log_water_intake(250)
                # Update dashboard stats immediately if open
                if self.current_tab == "dashboard":
                    self.views["dashboard"].update_stats()
            elif choice == "snooze":
                # Postpone all water-related reminders by 5 minutes
                # Rather than settings water trigger, we postpone custom reminders by setting their last_triggered_time forward!
                # Wait, this is a clean way to snooze: we can add 5 minutes (offset) by finding the water reminder in config and updating its last_triggered_time!
                reminders_list = self.settings.get("reminders", [])
                now = time.time()
                for r in reminders_list:
                    if "water" in r.get("title", "").lower() or "water" in r.get("message", "").lower() or "hydrate" in r.get("title", "").lower():
                        # We push its last triggered time forward so it triggers 5 minutes later relative to now
                        # e.g., target_time = now + 5 min => last_triggered_time = now - (interval - 5) min
                        interval_mins = r.get("interval_mins", 30)
                        r["last_triggered_time"] = now - (interval_mins - 5) * 60
                self.settings.set("reminders", reminders_list)
