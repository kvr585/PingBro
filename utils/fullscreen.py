import ctypes
from ctypes import wintypes

user32 = ctypes.windll.user32

# Configure the process to be DPI-aware so dimensions match physical pixels
try:
    user32.SetProcessDPIAware()
except Exception:
    pass

class MONITORINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcMonitor", wintypes.RECT),
        ("rcWork", wintypes.RECT),
        ("dwFlags", wintypes.DWORD)
    ]

def is_fullscreen_app_active():
    """
    Checks if a fullscreen application (game, media player, F11 browser, presentation) 
    is currently active on the system.
    Avoids false positives from desktop background and taskbar.
    """
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return False
        
    # Fetch window class name to check if it's the desktop or taskbar
    class_name = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, class_name, ctypes.sizeof(class_name))
    class_str = class_name.value
    
    # Common desktop and taskbar classes
    if class_str in ["Progman", "WorkerW", "Shell_TrayWnd", "Shell_SecondaryTrayWnd"]:
        return False
        
    # Get window dimensions
    rect = wintypes.RECT()
    if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        return False
        
    # Get monitor details relative to this window (handles multi-monitor setups)
    MONITOR_DEFAULTTONEAREST = 2
    monitor = user32.MonitorFromWindow(hwnd, MONITOR_DEFAULTTONEAREST)
    
    mi = MONITORINFO()
    mi.cbSize = ctypes.sizeof(MONITORINFO)
    
    if user32.GetMonitorInfoW(monitor, ctypes.byref(mi)):
        # Calculate monitor and window sizes
        monitor_w = mi.rcMonitor.right - mi.rcMonitor.left
        monitor_h = mi.rcMonitor.bottom - mi.rcMonitor.top
        
        window_w = rect.right - rect.left
        window_h = rect.bottom - rect.top
        
        # Window is fullscreen if it covers or exceeds the monitor screen size
        return (window_w >= monitor_w and window_h >= monitor_h)
        
    # Fallback: check against primary screen metrics
    screen_width = user32.GetSystemMetrics(0)
    screen_height = user32.GetSystemMetrics(1)
    
    window_w = rect.right - rect.left
    window_h = rect.bottom - rect.top
    
    return (window_w >= screen_width and window_h >= screen_height)


def get_foreground_monitor_rect():
    """
    Returns the monitor rectangle (left, top, width, height) that contains the
    current foreground window. Falls back to the primary monitor if detection fails.
    """
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        # Primary monitor
        sw = user32.GetSystemMetrics(0)
        sh = user32.GetSystemMetrics(1)
        return (0, 0, sw, sh)

    MONITOR_DEFAULTTONEAREST = 2
    monitor = user32.MonitorFromWindow(hwnd, MONITOR_DEFAULTTONEAREST)

    mi = MONITORINFO()
    mi.cbSize = ctypes.sizeof(MONITORINFO)

    if user32.GetMonitorInfoW(monitor, ctypes.byref(mi)):
        # Use the monitor work area (rcWork) to account for taskbar and docked bars
        left = mi.rcWork.left
        top = mi.rcWork.top
        width = mi.rcWork.right - mi.rcWork.left
        height = mi.rcWork.bottom - mi.rcWork.top
        return (left, top, width, height)

    # Fallback to primary
    sw = user32.GetSystemMetrics(0)
    sh = user32.GetSystemMetrics(1)
    return (0, 0, sw, sh)
