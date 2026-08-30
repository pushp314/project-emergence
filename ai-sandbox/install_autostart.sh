#!/bin/bash

# Setup paths
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLIST_FILE="$HOME/Library/LaunchAgents/com.aisandbox.desktop.plist"

echo "Installing AI Sandbox Autostart Service..."

# Create LaunchAgent plist
cat <<EOF > "$PLIST_FILE"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.aisandbox.desktop</string>
    <key>ProgramArguments</key>
    <array>
        <string>$PROJECT_DIR/run_desktop.sh</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>WorkingDirectory</key>
    <string>$PROJECT_DIR</string>
    <key>StandardOutPath</key>
    <string>$PROJECT_DIR/autostart.log</string>
    <key>StandardErrorPath</key>
    <string>$PROJECT_DIR/autostart.err</string>
</dict>
</plist>
EOF

# Load the agent
launchctl unload "$PLIST_FILE" 2>/dev/null
launchctl load "$PLIST_FILE"

echo "Autostart Service Installed!"
echo "The Native AI Sandbox will now launch automatically in the background when you log into your Mac."
