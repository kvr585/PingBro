#!/bin/bash

# Get the absolute path of the directory containing the script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# Desktop entry path
DESKTOP_DIR="$HOME/.local/share/applications"
DESKTOP_FILE="$DESKTOP_DIR/pingbro.desktop"

# Create applications directory if it doesn't exist
mkdir -p "$DESKTOP_DIR"

# Write desktop entry file
cat <<EOF > "$DESKTOP_FILE"
[Desktop Entry]
Name=PingBro
Comment=A modern dark-themed notification and reminder client
Exec=$DIR/.venv/bin/python3 $DIR/main.py
Path=$DIR
Icon=$DIR/assets/icon.png
Terminal=false
Type=Application
Categories=Utility;
EOF

# Make the desktop entry executable
chmod +x "$DESKTOP_FILE"

# Update desktop database to force menu refresh
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database "$DESKTOP_DIR"
fi

echo "PingBro application launcher successfully registered in your Applications Menu!"
