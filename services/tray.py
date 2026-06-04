import os
import threading
import pystray
from pystray import MenuItem as item, Menu
from PIL import Image, ImageDraw

class TrayIconService:
    def __init__(self, on_open, on_pause, on_resume, on_exam_mode, on_exit):
        self.on_open = on_open
        self.on_pause = on_pause
        self.on_resume = on_resume
        self.on_exam_mode = on_exam_mode
        self.on_exit = on_exit
        
        self.icon = None
        self.thread = None

    def start(self):
        """Loads the icon and starts the system tray loop in a background thread."""
        image = self._load_icon_image()
        
        # Build tray menu with nested submenus
        menu = Menu(
            item('Open App', lambda icon, item: self.on_open()),
            item('Pause Reminders', Menu(
                item('30 Minutes', lambda icon, item: self.on_pause(30)),
                item('1 Hour', lambda icon, item: self.on_pause(60)),
                item('2 Hours', lambda icon, item: self.on_pause(120)),
                item('Custom...', lambda icon, item: self.on_open())  # Restores window to enter custom duration
            )),
            item('Resume', lambda icon, item: self.on_resume()),
            item('Exam Mode', lambda icon, item: self.on_exam_mode()),
            item('Exit', lambda icon, item: self.on_exit())
        )
        
        self.icon = pystray.Icon("PingBro", image, "PingBro", menu)
        
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self):
        """Stops the tray icon loop and removes it from the taskbar."""
        if self.icon:
            self.icon.stop()
            self.icon = None

    def _run(self):
        try:
            self.icon.run()
        except Exception as e:
            print(f"[Tray] Error running tray icon: {e}")

    def _load_icon_image(self):
        """Loads the app icon image from assets or creates a fallback image if unavailable."""
        from utils.paths import get_asset_path
        icon_path = get_asset_path(os.path.join("assets", "icon.png"))
        if os.path.exists(icon_path):
            try:
                return Image.open(icon_path)
            except Exception as e:
                print(f"[Tray] Failed to load icon image: {e}")
                
        # Generate a beautiful fallback icon: a purple-cyan aura gradient circle
        img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        # Draw a glossy purple/cyan circle representing Aura
        draw.ellipse([8, 8, 56, 56], fill=(138, 43, 226, 255), outline=(0, 173, 181, 255), width=2)
        # Highlight reflection
        draw.ellipse([18, 14, 30, 26], fill=(255, 255, 255, 180))
        return img
