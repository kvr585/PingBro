import os
import sys

IS_WINDOWS = sys.platform.startswith('win')
if IS_WINDOWS:
    import winreg
else:
    winreg = None

import customtkinter as ctk
from tkinter import filedialog, messagebox
from utils.logger import log_event
from utils.sound import play_alert_sound

class SettingsView(ctk.CTkFrame):
    def __init__(self, parent, settings_manager):
        super().__init__(parent, fg_color="transparent")
        self.settings = settings_manager
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Scrollable Settings Container
        self.scroll_container = ctk.CTkScrollableFrame(
            self, 
            fg_color="transparent",
            scrollbar_button_color="#2c2c2c",
            scrollbar_button_hover_color="#3a3a3a"
        )
        self.scroll_container.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")
        
        # 1. Theme and Appearance Card
        self.create_appearance_card()
        
        # 2. Startup and System Settings Card
        if IS_WINDOWS:
            self.create_system_card()
        
        # 3. Sound Settings Card
        self.create_sound_card()
        
        # 4. Fullscreen Safety Card
        self.create_safety_card()
        
        # 5. Hydration Settings Card
        self.create_hydration_card()

    def create_appearance_card(self):
        card = ctk.CTkFrame(self.scroll_container, fg_color="#1e1e1e", corner_radius=12, border_width=1, border_color="#2e2e2e")
        card.pack(fill="x", pady=10, padx=2)
        
        title = ctk.CTkLabel(card, text="🎨 APPEARANCE AND THEMING", font=("Helvetica", 13, "bold"), text_color="#00adb5")
        title.pack(anchor="w", padx=20, pady=(15, 10))
        
        # Appearance mode selection
        lbl_frame = ctk.CTkFrame(card, fg_color="transparent")
        lbl_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(lbl_frame, text="Theme Mode:", font=("Helvetica", 12), text_color="#aaaaaa").pack(side="left")
        
        self.theme_cb = ctk.CTkComboBox(
            lbl_frame, 
            values=["System", "Dark", "Light"],
            fg_color="#2b2b2b",
            border_color="#3a3a3a",
            button_color="#3a3a3a",
            state="readonly",
            command=self.change_theme,
            width=150
        )
        self.theme_cb.pack(side="right")
        self.theme_cb.set(self.settings.get("theme", "Dark"))

    def create_system_card(self):
        card = ctk.CTkFrame(self.scroll_container, fg_color="#1e1e1e", corner_radius=12, border_width=1, border_color="#2e2e2e")
        card.pack(fill="x", pady=10, padx=2)
        
        title = ctk.CTkLabel(card, text="⚙️ SYSTEM INTEGRATION", font=("Helvetica", 13, "bold"), text_color="#00adb5")
        title.pack(anchor="w", padx=20, pady=(15, 10))
        
        # Startup toggle
        self.startup_switch = ctk.CTkSwitch(
            card, 
            text="Start application on Windows startup", 
            font=("Helvetica", 12, "bold"),
            progress_color="#00adb5",
            command=self.toggle_startup
        )
        self.startup_switch.pack(anchor="w", padx=20, pady=15)
        
        # Load startup switch state
        if self.settings.get("startup_enabled", False):
            self.startup_switch.select()
        else:
            self.startup_switch.deselect()

    def create_sound_card(self):
        card = ctk.CTkFrame(self.scroll_container, fg_color="#1e1e1e", corner_radius=12, border_width=1, border_color="#2e2e2e")
        card.pack(fill="x", pady=10, padx=2)
        
        title = ctk.CTkLabel(card, text="🔊 AUDIO PREFERENCES", font=("Helvetica", 13, "bold"), text_color="#00adb5")
        title.pack(anchor="w", padx=20, pady=(15, 10))
        
        # Silent Mode
        self.silent_switch = ctk.CTkSwitch(
            card,
            text="Silent Mode (Mute all sounds)",
            font=("Helvetica", 12, "bold"),
            progress_color="#ff9f0a",
            command=self.toggle_silent_mode
        )
        self.silent_switch.pack(anchor="w", padx=20, pady=8)
        if self.settings.get("silent_mode", False):
            self.silent_switch.select()
            
        # Custom sound file select
        sound_lbl = ctk.CTkLabel(card, text="Custom Reminder Sound (.wav):", font=("Helvetica", 12), text_color="#aaaaaa")
        sound_lbl.pack(anchor="w", padx=20, pady=(10, 2))
        
        file_frame = ctk.CTkFrame(card, fg_color="transparent")
        file_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        self.sound_file_lbl = ctk.CTkLabel(
            file_frame,
            text=self._get_sound_display_name(),
            font=("Helvetica", 11, "italic"),
            text_color="#888888",
            anchor="w"
        )
        self.sound_file_lbl.pack(side="left", fill="x", expand=True)
        
        # Action Buttons
        self.clear_sound_btn = ctk.CTkButton(
            file_frame,
            text="CLEAR",
            font=("Helvetica", 11, "bold"),
            fg_color="#333333",
            hover_color="#444444",
            text_color="#888888",
            width=65,
            height=30,
            corner_radius=15,
            command=self.clear_custom_sound
        )
        self.clear_sound_btn.pack(side="right", padx=(5, 0))
        
        self.browse_sound_btn = ctk.CTkButton(
            file_frame,
            text="BROWSE",
            font=("Helvetica", 11, "bold"),
            fg_color="#00adb5",
            hover_color="#008c92",
            width=75,
            height=30,
            corner_radius=15,
            command=self.browse_custom_sound
        )
        self.browse_sound_btn.pack(side="right", padx=(5, 0))

        self.test_sound_btn = ctk.CTkButton(
            file_frame,
            text="TEST",
            font=("Helvetica", 11, "bold"),
            fg_color="#ff9f0a",
            hover_color="#e08b08",
            text_color="#ffffff",
            width=65,
            height=30,
            corner_radius=15,
            command=self.test_custom_sound
        )
        self.test_sound_btn.pack(side="right")

    def create_safety_card(self):
        card = ctk.CTkFrame(self.scroll_container, fg_color="#1e1e1e", corner_radius=12, border_width=1, border_color="#2e2e2e")
        card.pack(fill="x", pady=10, padx=2)
        
        title = ctk.CTkLabel(card, text="🛡️ FULLSCREEN SAFETY", font=("Helvetica", 13, "bold"), text_color="#00adb5")
        title.pack(anchor="w", padx=20, pady=(15, 10))
        
        # Suppress fullscreen popups
        self.fs_safety_switch = ctk.CTkSwitch(
            card,
            text="Enable Fullscreen Safety (Suppress alerts in games/movies)",
            font=("Helvetica", 12, "bold"),
            progress_color="#00adb5",
            command=self.toggle_fullscreen_safety
        )
        self.fs_safety_switch.pack(anchor="w", padx=20, pady=8)
        if self.settings.get("fullscreen_safety_enabled", True):
            self.fs_safety_switch.select()
            
        # Convert suppressed alerts to notifications
        self.fs_convert_switch = ctk.CTkSwitch(
            card,
            text="Convert suppressed alerts to silent notifications",
            font=("Helvetica", 12, "bold"),
            progress_color="#00adb5",
            command=self.toggle_fullscreen_convert
        )
        self.fs_convert_switch.pack(anchor="w", padx=20, pady=8)
        if self.settings.get("fullscreen_convert_to_notif", True):
            self.fs_convert_switch.select()

    def create_hydration_card(self):
        card = ctk.CTkFrame(self.scroll_container, fg_color="#1e1e1e", corner_radius=12, border_width=1, border_color="#2e2e2e")
        card.pack(fill="x", pady=10, padx=2)
        
        title = ctk.CTkLabel(card, text="💧 HYDRATION TRACKING", font=("Helvetica", 13, "bold"), text_color="#00adb5")
        title.pack(anchor="w", padx=20, pady=(15, 10))
        
        # Hydration Mode switch
        self.hyd_switch = ctk.CTkSwitch(
            card,
            text="Enable Hydration Tracking Features",
            font=("Helvetica", 12, "bold"),
            progress_color="#00adb5",
            command=self.toggle_hydration_mode
        )
        self.hyd_switch.pack(anchor="w", padx=20, pady=8)
        if self.settings.get("hydration_mode_enabled", False):
            self.hyd_switch.select()
        else:
            self.hyd_switch.deselect()

        # Target Calculator Inputs (Weight & Daily Target)
        inputs_frame = ctk.CTkFrame(card, fg_color="transparent")
        inputs_frame.pack(fill="x", padx=20, pady=10)
        
        # Weight entry
        ctk.CTkLabel(inputs_frame, text="Body Weight (kg):", font=("Helvetica", 11), text_color="#aaaaaa").grid(row=0, column=0, padx=(0, 5), pady=5, sticky="w")
        self.weight_entry = ctk.CTkEntry(inputs_frame, width=70, fg_color="#2b2b2b", border_color="#3a3a3a")
        self.weight_entry.grid(row=0, column=1, padx=(0, 15), pady=5, sticky="w")
        self.weight_entry.insert(0, str(self.settings.get("hydration_weight", 70)))
        
        # Target entry
        ctk.CTkLabel(inputs_frame, text="Daily Target (ml):", font=("Helvetica", 11), text_color="#aaaaaa").grid(row=0, column=2, padx=(0, 5), pady=5, sticky="w")
        self.target_entry = ctk.CTkEntry(inputs_frame, width=80, fg_color="#2b2b2b", border_color="#3a3a3a")
        self.target_entry.grid(row=0, column=3, padx=(0, 15), pady=5, sticky="w")
        self.target_entry.insert(0, str(self.settings.get("hydration_target", 2000)))
        
        # Save button
        self.save_hyd_btn = ctk.CTkButton(
            inputs_frame,
            text="SAVE SETUP",
            font=("Helvetica", 11, "bold"),
            fg_color="#00adb5",
            hover_color="#008c92",
            width=90,
            height=30,
            corner_radius=15,
            command=self.save_hydration_settings
        )
        self.save_hyd_btn.grid(row=0, column=4, padx=(5, 0), pady=5, sticky="w")

        # Auto calc button
        self.calc_target_btn = ctk.CTkButton(
            inputs_frame,
            text="CALC TARGET",
            font=("Helvetica", 11, "bold"),
            fg_color="#ff9f0a",
            hover_color="#e08b08",
            width=90,
            height=30,
            corner_radius=15,
            command=self.auto_calculate_target
        )
        self.calc_target_btn.grid(row=0, column=5, padx=5, pady=5, sticky="w")

    def _get_sound_display_name(self):
        path = self.settings.get("custom_sound_file", "")
        if path:
            return os.path.basename(path)
        return "Default Windows System Alert"

    def change_theme(self, choice):
        self.settings.set("theme", choice)
        ctk.set_appearance_mode(choice)
        log_event("settings_changed", f"Appearance mode updated to {choice}")

    def toggle_startup(self):
        val = self.startup_switch.get() == 1
        success = self._set_windows_registry_startup(val)
        
        if success:
            self.settings.set("startup_enabled", val)
            log_event("settings_changed", f"Startup setting updated to {val}")
        else:
            # Revert switch on failure
            if val:
                self.startup_switch.deselect()
            else:
                self.startup_switch.select()
            messagebox.showerror("Registry Error", "Failed to update Windows registry startup entry.")

    def _set_windows_registry_startup(self, enabled=True):
        """Creates or removes a shortcut in the Windows Startup folder."""
        startup_shortcut_path = os.path.join(
            os.environ["APPDATA"], "Microsoft", "Windows", "Start Menu", "Programs", "Startup", "PingBro.lnk"
        )
        if not enabled:
            try:
                if os.path.exists(startup_shortcut_path):
                    os.remove(startup_shortcut_path)
                return True
            except Exception as e:
                print(f"[Startup] Error removing startup shortcut: {e}")
                return False
                
        system_root = os.environ.get("SystemRoot", "C:\\Windows")
        powershell_exe = os.path.join(system_root, "System32", "WindowsPowerShell", "v1.0", "powershell.exe")
        if not os.path.exists(powershell_exe):
            powershell_exe = "powershell"
            
        try:
            if getattr(sys, 'frozen', False):
                powershell_cmd = f"""
                $w = New-Object -ComObject WScript.Shell
                $s = $w.CreateShortcut("{startup_shortcut_path}")
                $s.TargetPath = "{sys.executable}"
                $s.Description = "PingBro Reminder App"
                $s.WorkingDirectory = "{os.path.dirname(sys.executable)}"
                $s.IconLocation = "{sys.executable},0"
                $s.Save()
                """
            else:
                pythonw_exe = os.path.join(sys.base_prefix, "pythonw.exe")
                if not os.path.exists(pythonw_exe):
                    pythonw_exe = sys.executable
                main_py = os.path.abspath(sys.argv[0])
                install_dir = os.path.dirname(main_py)
                icon_ico = os.path.join(install_dir, "assets", "icon.ico")
                powershell_cmd = f"""
                $w = New-Object -ComObject WScript.Shell
                $s = $w.CreateShortcut("{startup_shortcut_path}")
                $s.TargetPath = "{pythonw_exe}"
                $s.Arguments = '"{main_py}"'
                $s.Description = "PingBro Reminder App"
                $s.WorkingDirectory = "{install_dir}"
                $s.IconLocation = "{icon_ico}"
                $s.Save()
                """
            subprocess.run([powershell_exe, "-Command", powershell_cmd], capture_output=True, text=True, check=True)
            return True
        except Exception as e:
            print(f"[Startup] Error creating startup shortcut: {e}")
            return False

    def toggle_silent_mode(self):
        val = self.silent_switch.get() == 1
        self.settings.set("silent_mode", val)
        log_event("settings_changed", f"Silent mode set to {val}")

    def browse_custom_sound(self):
        file_path = filedialog.askopenfilename(
            title="Select Custom WAV Alert Sound",
            filetypes=[("WAV Audio Files", "*.wav")]
        )
        if file_path:
            self.settings.set("custom_sound_file", file_path)
            self.sound_file_lbl.configure(text=os.path.basename(file_path))
            log_event("settings_changed", f"Custom sound file updated to: {file_path}")
            messagebox.showinfo("Sound Configured", f"Custom alert sound '{os.path.basename(file_path)}' loaded.")

    def clear_custom_sound(self):
        self.settings.set("custom_sound_file", "")
        self.sound_file_lbl.configure(text="Default Windows System Alert")
        log_event("settings_changed", "Custom alert sound cleared. Reverted to default.")
        messagebox.showinfo("Sound Reverted", "Alert sound reverted to default Windows alert.")

    def test_custom_sound(self):
        path = self.settings.get("custom_sound_file", "")
        play_alert_sound(path if path else None, silent=False)
        log_event("sound_previewed", "User manually previewed alert sound.")

    def toggle_fullscreen_safety(self):
        val = self.fs_safety_switch.get() == 1
        self.settings.set("fullscreen_safety_enabled", val)
        log_event("settings_changed", f"Fullscreen safety mode set to {val}")

    def toggle_fullscreen_convert(self):
        val = self.fs_convert_switch.get() == 1
        self.settings.set("fullscreen_convert_to_notif", val)
        log_event("settings_changed", f"Fullscreen notification conversion set to {val}")

    def toggle_hydration_mode(self):
        val = self.hyd_switch.get() == 1
        self.settings.set("hydration_mode_enabled", val)
        log_event("settings_changed", f"Hydration mode tracking enabled set to {val}")

    def save_hydration_settings(self):
        try:
            w_val = int(self.weight_entry.get().strip())
            t_val = int(self.target_entry.get().strip())
            if w_val <= 0 or t_val <= 0:
                raise ValueError()
            self.settings.set("hydration_weight", w_val)
            self.settings.set("hydration_target", t_val)
            log_event("settings_changed", f"Hydration settings updated: Weight={w_val}kg, Target={t_val}ml")
            messagebox.showinfo("Success", "Hydration settings updated successfully!")
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter positive integer values for weight and target.")

    def auto_calculate_target(self):
        try:
            w_val = int(self.weight_entry.get().strip())
            if w_val <= 0:
                raise ValueError()
            t_val = w_val * 35
            self.target_entry.delete(0, "end")
            self.target_entry.insert(0, str(t_val))
            messagebox.showinfo("Target Calculated", f"Water target calculated as {t_val} ml (35ml per kg). Make sure to click SAVE SETUP.")
        except ValueError:
            messagebox.showerror("Invalid Weight", "Please enter a valid weight in kg first.")
