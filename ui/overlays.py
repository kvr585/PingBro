import ctypes
import customtkinter as ctk
from utils.logger import log_event

class FlashOverlay(ctk.CTkToplevel):
    def __init__(self, color="#ff453a", alpha=0.3, duration_ms=800):
        super().__init__()
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(fg_color=color)
        
        # Expand across the whole screen width and height
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        self.geometry(f"{screen_width}x{screen_height}+0+0")
        
        # Force initial rendering to capture the valid HWND window handle
        self.update()
        
        # Apply Windows specific click-through flags using ctypes
        try:
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            if hwnd == 0:
                hwnd = self.winfo_id()
            
            GWL_EXSTYLE = -20
            WS_EX_LAYERED = 0x00080000
            WS_EX_TRANSPARENT = 0x00000020
            
            style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style | WS_EX_LAYERED | WS_EX_TRANSPARENT)
            self.attributes("-alpha", alpha)
        except Exception as e:
            print(f"[Overlay] Failed to apply click-through attributes: {e}")
            
        # Automatically close this overlay after a brief duration
        self.after(duration_ms, self.destroy)


class FullscreenPopup(ctk.CTkToplevel):
    def __init__(self, title, message, priority="high", is_water=False, on_dismiss=None):
        super().__init__()
        self.attributes("-fullscreen", True)  # Robust native OS fullscreen
        self.attributes("-topmost", True)
        self.focus_force()
        
        # Center grid configurations
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self.on_dismiss_callback = on_dismiss
        self.is_water = is_water
        
        # Determine theme coloring based on priority
        self.accent_color = "#00adb5"  # Sleek cyan for water hydration
        if not is_water:
            if priority == "low":
                self.accent_color = "#30d158"  # Green
            elif priority == "medium":
                self.accent_color = "#ff9f0a"  # Orange
            else:
                self.accent_color = "#ff453a"  # Red
                
        # Dark overlay background
        self.configure(fg_color="#0c0c0c")
        
        # Centered card layout frame
        card_width = 500
        card_height = 380
        
        main_frame = ctk.CTkFrame(
            self, 
            fg_color="#181818", 
            corner_radius=24, 
            border_width=1, 
            border_color="#2e2e2e",
            width=card_width,
            height=card_height
        )
        main_frame.grid(row=0, column=0, sticky="")
        main_frame.pack_propagate(False)  # Ensure frame dimensions are locked
        
        # Icon / Header Section
        emoji = "💧" if is_water else ("🔔" if priority == "low" else "⚠️")
        icon_label = ctk.CTkLabel(main_frame, text=emoji, font=("Segoe UI", 48))
        icon_label.pack(pady=(35, 5))
        
        header = ctk.CTkLabel(main_frame, text=title.upper(), font=("Helvetica", 14, "bold"), text_color=self.accent_color)
        header.pack(pady=0)
        
        # Text Body Section
        msg_label = ctk.CTkLabel(
            main_frame, 
            text=message, 
            font=("Helvetica", 16, "normal"), 
            text_color="#ffffff", 
            wraplength=420, 
            justify="center"
        )
        msg_label.pack(expand=True, padx=30, pady=15)
        
        # Action Buttons Section
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(side="bottom", pady=30)
        
        if is_water:
            drank_btn = ctk.CTkButton(
                btn_frame, 
                text="💧 I DRANK!", 
                font=("Helvetica", 13, "bold"), 
                fg_color="#00adb5", 
                hover_color="#008c92", 
                text_color="#ffffff",
                height=42, 
                width=160, 
                corner_radius=21, 
                command=self._on_drank
            )
            drank_btn.pack(side="left", padx=10)
            
            snooze_btn = ctk.CTkButton(
                btn_frame, 
                text="Snooze (5m)", 
                font=("Helvetica", 13, "normal"), 
                fg_color="#2c2c2c", 
                hover_color="#3c3c3c", 
                text_color="#aaaaaa",
                height=42, 
                width=110, 
                corner_radius=21, 
                command=self._on_snooze
            )
            snooze_btn.pack(side="left", padx=10)
        else:
            dismiss_btn = ctk.CTkButton(
                btn_frame, 
                text="DISMISS", 
                font=("Helvetica", 13, "bold"), 
                fg_color=self.accent_color, 
                hover_color=self._adjust_color_brightness(self.accent_color, -0.2), 
                text_color="#ffffff",
                height=42, 
                width=180, 
                corner_radius=21, 
                command=self._on_dismiss
            )
            dismiss_btn.pack()

    def _on_drank(self):
        log_event("reminder_dismissed", "User logged water consumption from popup alert.")
        if self.on_dismiss_callback:
            self.on_dismiss_callback("drank")
        self.destroy()

    def _on_snooze(self):
        log_event("reminder_dismissed", "User selected snooze from popup alert.")
        if self.on_dismiss_callback:
            self.on_dismiss_callback("snooze")
        self.destroy()

    def _on_dismiss(self):
        log_event("reminder_dismissed", "User dismissed custom reminder from popup alert.")
        if self.on_dismiss_callback:
            self.on_dismiss_callback("dismiss")
        self.destroy()

    def _adjust_color_brightness(self, hex_color, factor):
        hex_color = hex_color.lstrip('#')
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        r = max(0, min(255, int(r * (1 + factor))))
        g = max(0, min(255, int(g * (1 + factor))))
        b = max(0, min(255, int(b * (1 + factor))))
        return f"#{r:02x}{g:02x}{b:02x}"
