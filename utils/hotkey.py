import sys
import ctypes

IS_WINDOWS = sys.platform.startswith('win')

if IS_WINDOWS:
    from ctypes import wintypes
    user32 = ctypes.windll.user32
else:
    wintypes = None
    user32 = None

import threading
import os

# Win32 API Constants
WM_HOTKEY = 0x0312
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
VK_X = 0x58  # Virtual key code for 'X'
HOTKEY_ID = 999  # Unique ID for our global hotkey

class GlobalHotkeyListener:
    def __init__(self, trigger_callback):
        self.trigger_callback = trigger_callback
        self.thread = None
        self.running = False

    def start(self):
        """Starts the global hotkey listener in a background daemon thread."""
        if not IS_WINDOWS:
            print("[Hotkey] Global hotkeys are not supported on Linux/non-Windows systems.")
            return
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self):
        """Unregisters the hotkey and stops the listener thread."""
        if not IS_WINDOWS:
            return
        self.running = False
        # Post a dummy WM_NULL message to unblock GetMessageW if it's waiting
        user32.PostThreadMessageW(self.thread.ident, 0x0000, 0, 0)

    def _run(self):
        # Register Hotkey: CTRL + SHIFT + X
        modifiers = MOD_CONTROL | MOD_SHIFT
        success = user32.RegisterHotKey(None, HOTKEY_ID, modifiers, VK_X)
        
        if not success:
            print("[Hotkey] Failed to register global hotkey CTRL + SHIFT + X. It may be in use by another app.")
            return

        print("[Hotkey] Registered global hotkey CTRL + SHIFT + X successfully.")
        
        msg = wintypes.MSG()
        try:
            # Message loop
            while self.running and user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
                if msg.message == WM_HOTKEY:
                    if msg.wParam == HOTKEY_ID:
                        print("[Hotkey] Global hotkey CTRL + SHIFT + X pressed! Triggering callback...")
                        # Run callback (typically triggers Exam Mode)
                        if self.trigger_callback:
                            self.trigger_callback()
                
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
        finally:
            # Unregister hotkey on thread exit
            user32.UnregisterHotKey(None, HOTKEY_ID)
            print("[Hotkey] Unregistered global hotkey.")
