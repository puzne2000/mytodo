#!/bin/zsh
# Creates MyTodo.app in the current folder.
# Run this once, then drag MyTodo.app to /Applications.
# If you move the project folder, run this again.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_NAME="MyTodo"
APP_DIR="$SCRIPT_DIR/$APP_NAME.app/Contents"

echo "Building $APP_NAME.app..."

mkdir -p "$APP_DIR/MacOS"

# Info.plist
cat > "$APP_DIR/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>$APP_NAME</string>
    <key>CFBundleExecutable</key>
    <string>$APP_NAME</string>
    <key>CFBundleIdentifier</key>
    <string>com.personal.mytodo</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>LSMinimumSystemVersion</key>
    <string>11.0</string>
</dict>
</plist>
EOF

# Launcher script
cat > "$APP_DIR/MacOS/$APP_NAME" << EOF
#!/bin/zsh
cd "$SCRIPT_DIR"
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    .venv/bin/pip install PySide6 tomli_w
fi
source .venv/bin/activate
python3 main.py
EOF

chmod +x "$APP_DIR/MacOS/$APP_NAME"

echo "Done. MyTodo.app is in $SCRIPT_DIR"
echo "Drag it to /Applications to install."
