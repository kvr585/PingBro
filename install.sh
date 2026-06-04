#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "🚀 Starting PingBro installation for Linux..."

# Get absolute path of this project folder
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

# 1. Detect and install system package dependencies
echo "📦 Installing system dependencies (requires sudo)..."
if command -v apt-get &> /dev/null; then
    sudo apt-get update
    sudo apt-get install -y python3-pip python3-tk python3-venv
elif command -v dnf &> /dev/null; then
    sudo dnf install -y python3-pip python3-tkinter
    # Check if atomic system like Bazzite
    if command -v rpm-ostree &> /dev/null; then
        echo "⚠️ Note: Bazzite/Fedora Silverblue detected. If python3-tkinter is not installed,"
        echo "you will need to run 'sudo rpm-ostree install python3-tkinter' and reboot your system."
    fi
else
    echo "⚠️ Unknown package manager. Please ensure python3-venv and python3-tkinter are installed."
fi

# 2. Setup python virtual environment
echo "🐍 Creating virtual environment..."
python3 -m venv .venv

# 3. Install PIP requirements
echo "📥 Installing python packages..."
.venv/bin/pip install -r requirements.txt

# 4. Run launcher script to register menu entry
echo "🖥️ Registering application shortcut in system menu..."
chmod +x create_launcher.sh
./create_launcher.sh

echo ""
echo "🎉 Installation completed successfully!"
echo "You can now find and launch 'PingBro' directly from your Applications Menu!"
