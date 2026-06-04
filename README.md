# PingBro 🌌

A modern, sleek, dark-themed Windows desktop notification client and companion Android app designed to keep you on track. PingBro helps you schedule custom alarms, periodic intervals (e.g. repeat every N minutes), track hydration goals (optional), and features emergency keyboard-safe instant shutdowns.

---

## Key Desktop Features

1. **✏️ Click-to-Edit Reminders**:
   - Tap/click any active reminder card inside the **Active Reminders** tab to instantly load its values back into the editor. 
   - A bright orange editing layout visually distinguishes the edit state from the normal creation form.
2. **⏰ Unified Reminder System**:
   - Create generic reminders for any activity (stretching, posture check, water intake, eye rest, etc.).
   - Support for **Time of Day** triggers (specific daily alarm times, e.g. 2:00 PM).
   - Support for **Interval** triggers (periodic timers repeating every N minutes).
3. **📺 Alert Display Modes**:
   - **Notification Mode**: Displays a native Windows toast notification in the corner of the screen.
   - **Fullscreen Popup Mode**: Displays a prominent, beautifully centered warning card covering the entire screen with dismissal/snooze controls (DPI-scaling safe).
4. **💧 Optional Hydration Tracking Mode**:
   - Toggleable from the settings tab.
   - Embeds a progress bar tracking daily targets (calculated using weight-based guidelines or custom values).
   - Features a custom 7-day Weekly History Bar Chart built with native frames for zero-dependency execution.
   - Fast cup logging via a segmented size selector (200ml glass, 250ml mug, 500ml bottle).
5. **⚠️ Emergency Exam Mode**:
   - Immediately terminates the GUI window, kills background scheduler and hotkey listener threads, deletes the system tray icon, and shuts down the Python process instantly.
   - **Global Keyboard Shortcut**: Press `CTRL + SHIFT + X` system-wide at any time to instantly kill the app with no prompts or confirmation dialogs.
6. **🛡️ Fullscreen Safety**:
   - Dynamically checks if a fullscreen application (browser, presentation, game, or VirtualBox VM) is in focus using Windows APIs.
   - Suppresses disruptive popups and optionally converts them into silent notifications (can be toggled in settings).
7. **⚙️ System Tray & Windows Startup**:
   - Minimizing or closing the window withdraws the app to the Windows taskbar system tray.
   - Toggle "Start application on Windows startup" from the settings tab to run automatically on system boot.

---

## 📱 Companion Android App

Located in the [aura_reminder_android](file:///c:/Users/uvave/Documents/auto_flasher/aura_reminder_android) sub-directory, a Flutter companion mobile application delivers the same premium dark theme experience on Android:
- **Immersive Alarm Popups**: Rings alarm-clock alerts and displays full-screen wake-lock views over your device lock screen.
- **Ignore Battery Optimizations**: Requests special background permissions to guarantee exact firing schedules even during Android Doze mode.
- **Snooze Support**: Delayed rescheduling logic syncing directly with standard notifications.

---

## Installation & Running (Windows Desktop)

### 🚀 Standard Setup (Quick & User-Friendly — Bypasses Smart App Control)
For normal users who want a standard, clean installation:

1. **Download and Extract the App:**
   - Click the green **Code** button at the top of this GitHub page and select **Download ZIP**.
   - Right-click the downloaded ZIP file, select **Extract All...**, and extract it.

2. **Run the Installer:**
   - Open the extracted folder and double-click **`install.bat`**.
   - Click **Install** in the wizard. This runs the installer using the system Python interpreter (which is digitally signed and trusted by Windows), bypassing all Smart App Control blocks and warnings! It will automatically install PingBro to your local apps directory (`%LOCALAPPDATA%\PingBro`), register it in Windows, create a Start Menu shortcut, and launch the application!

3. **❌ Uninstall cleanly at any time:**
   - You can uninstall PingBro like any other app: Go to **Windows Settings > Apps > Installed apps**, search for **PingBro**, and click **Uninstall**.
   - Alternatively, search for **PingBro** in your Start Menu, right-click, and select **Uninstall**!

---

### 💻 Developer Setup (Running from Source Code)
If you want to run the app using Python and modify the code:

#### Prerequisites
- Windows 10 or 11
- Python 3.8+ installed

#### Steps:
1. Open Command Prompt/PowerShell in the folder and run:
   ```bash
   pip install -r requirements.txt
   ```
2. Launch the application:
   ```bash
   python main.py
   ```
3. (Optional) Recompile the standalone executable:
   ```bash
   pyinstaller --clean PingBro.spec
   ```
   The compiled binary will be generated inside the `dist` directory.

---

## Installation & Running (Linux / Kali Linux / Bazzite)

PingBro is fully cross-platform and supports running on Linux (including Kali Linux, Bazzite, Ubuntu, etc.) by automatically bypassing Windows-specific hooks and falling back to native Linux commands for audio playback.

### Automated 1-Click Installation
Open your terminal in the root project folder and run:
```bash
chmod +x install.sh
./install.sh
```
This script will automatically:
1. Detect your package manager and install required dependencies (like `tkinter` and `venv`).
2. Create and configure your Python virtual environment.
3. Install all required Python packages.
4. Register the **PingBro** shortcut in your Applications Menu so you can launch it natively.

*Note for GNOME Desktop: GNOME doesn't display tray icons by default. GNOME users (like on Bazzite OS) should install the GNOME extension [AppIndicator and KStatusNotifierItem Support](https://extensions.gnome.org/extension/615/appindicator-support/) to see the system tray icon in their status bar.*

---

## Project Structure

```text
PingBro/
│
├── main.py                     # Application launcher & background task setup
├── requirements.txt            # PIP dependencies
├── README.md                   # Setup and guides
├── .gitignore                  # Git commit exclusions
├── PingBro.spec                # PyInstaller compilation specification
├── create_launcher.sh          # Linux desktop menu installer script
├── install.sh                  # Automated 1-click Linux installation script
│
├── config/
│   ├── settings.py             # JSON Configuration Service (persists user states)
│   ├── settings.json           # Autogenerated user settings file
│   └── logs.json               # Autogenerated log history
│
├── ui/
│   ├── main_window.py          # App UI container (Navigation Sidebar & Header)
│   ├── dashboard.py            # Dashboard View (streak, progress tracker)
│   ├── active_reminders.py     # Unified reminders list management (click-to-edit)
│   ├── add_reminder.py         # Scheduling/Editing form for reminders
│   ├── settings_page.py        # Startup, sound, safety & theme switches
│   ├── logs_page.py            # Scrollable events history viewer
│   └── overlays.py             # Fullscreen popup card overlay
│
├── reminders/
│   └── models.py               # AppReminder model definitions
│
├── services/
│   ├── scheduler.py            # Time-keeper checker thread
│   └── tray.py                 # pystray System Tray menu loop thread
│
├── utils/
│   ├── fullscreen.py           # OS fullscreen state checker (fallback safe)
│   ├── hotkey.py               # Hotkey listener thread (Windows only, fallback safe)
│   ├── logger.py               # App logging engine (config/logs.json)
│   └── sound.py                # Sound player engine (winsound / Linux players)
│
└── aura_reminder_android/      # Flutter companion app source code
```
