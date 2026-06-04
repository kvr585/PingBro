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

### Prerequisites
- Windows OS (Windows 10 or 11 recommended).
- Python 3.8 or higher.

### 1. Install Dependencies
Open a Command Prompt or PowerShell in the root project folder and run:
```bash
pip install -r requirements.txt
```

### 2. Run the Application
Start the client by running:
```bash
python main.py
```

### 3. Compile Standalone Executable
To package the app into a standalone `PingBro.exe` file, run:
```bash
pyinstaller --clean PingBro.spec
```
The compiled binary will be generated inside the `dist` directory.

---

## Installation & Running (Linux / Kali Linux / Bazzite)

PingBro is fully cross-platform and supports running on Linux (including Kali Linux, Bazzite, Ubuntu, etc.) by automatically bypassing Windows-specific hooks and falling back to native Linux commands for audio playback.

### 1. Install System Dependencies
Depending on your Linux distribution, you may need to install Python's virtual environment and `tkinter` graphical package:

- **On Kali Linux / Debian / Ubuntu:**
  ```bash
  sudo apt update
  sudo apt install -y python3-pip python3-tk python3-venv
  ```

- **On Bazzite OS / Fedora (Atomic System):**
  ```bash
  sudo rpm-ostree install python3-tkinter
  # Note: A system reboot is required on Bazzite after installing system RPM packages.
  ```

### 2. Setup and Run
Open your terminal in the root project folder:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 main.py
```

### 3. Register Application Launcher in Desktop Menu
To add PingBro to your applications menu (complete with icon and search indexing), run:
```bash
chmod +x create_launcher.sh
./create_launcher.sh
```
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
