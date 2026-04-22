#!/usr/bin/env bash
# Job Search Assistant — Installer
# Supports macOS. Requires Python 3.9+.

set -euo pipefail

INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_NAME="Job Search"
APP_BUNDLE="$HOME/Desktop/${APP_NAME}.app"
MIN_PYTHON="3.9"

# ── Helpers ────────────────────────────────────────────────────────────────────

bold()  { printf '\033[1m%s\033[0m'  "$*"; }
green() { printf '\033[32m%s\033[0m' "$*"; }
dim()   { printf '\033[2m%s\033[0m'  "$*"; }
err()   { printf '\033[31mError:\033[0m %s\n' "$*" >&2; exit 1; }
step()  { printf '\n  %s\n' "$(bold "$*")"; }
ok()    { printf '  %s %s\n' "$(green '✓')" "$*"; }

version_gte() {
    python3 -c "import sys; exit(0 if sys.version_info >= tuple(int(x) for x in '${MIN_PYTHON}'.split('.')) else 1)"
}

# ── Banner ─────────────────────────────────────────────────────────────────────

clear
printf '\n'
printf '  ╔══════════════════════════════════════╗\n'
printf '  ║       Job Search Assistant           ║\n'
printf '  ║       Installation Wizard            ║\n'
printf '  ╚══════════════════════════════════════╝\n'
printf '\n'
printf '  This installer will:\n'
printf '    • Create a Python virtual environment\n'
printf '    • Install all dependencies\n'
printf "    • Add \033[1mJob Search.app\033[0m to your Desktop\n"
printf '\n'
printf '  Install location: %s\n' "$(dim "$INSTALL_DIR")"
printf '\n'
read -rp "  Press Enter to continue, or Ctrl+C to cancel… "

# ── Python check ───────────────────────────────────────────────────────────────

step "Checking Python…"
if ! command -v python3 &>/dev/null; then
    err "python3 not found. Install it from https://python.org (version ${MIN_PYTHON}+)"
fi
if ! version_gte; then
    FOUND="$(python3 --version 2>&1)"
    err "Python ${MIN_PYTHON}+ required. Found: ${FOUND}. Download from https://python.org"
fi
ok "$(python3 --version)"

# ── Virtual environment ────────────────────────────────────────────────────────

step "Setting up virtual environment…"
if [ -d "$INSTALL_DIR/venv" ]; then
    ok "Existing venv found — reusing"
else
    python3 -m venv "$INSTALL_DIR/venv"
    ok "Virtual environment created"
fi

# ── Dependencies ───────────────────────────────────────────────────────────────

step "Installing dependencies…"
"$INSTALL_DIR/venv/bin/pip" install --quiet --upgrade pip
"$INSTALL_DIR/venv/bin/pip" install --quiet -r "$INSTALL_DIR/requirements.txt"
ok "All packages installed"

# ── macOS app bundle ───────────────────────────────────────────────────────────

step "Creating app shortcut…"
mkdir -p "$APP_BUNDLE/Contents/MacOS"
mkdir -p "$APP_BUNDLE/Contents/Resources"

cat > "$APP_BUNDLE/Contents/Info.plist" << PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>            <string>Job Search</string>
    <key>CFBundleDisplayName</key>     <string>Job Search</string>
    <key>CFBundleIdentifier</key>      <string>com.jobsearch.assistant</string>
    <key>CFBundleVersion</key>         <string>1.0</string>
    <key>CFBundleExecutable</key>      <string>launch</string>
    <key>CFBundleIconFile</key>        <string>AppIcon</string>
    <key>LSUIElement</key>             <true/>
</dict>
</plist>
PLIST

# Write the launch script — bakes in the install path at creation time
cat > "$APP_BUNDLE/Contents/MacOS/launch" << LAUNCH
#!/usr/bin/env bash
INSTALL_DIR="${INSTALL_DIR}"

if lsof -i :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    open "http://localhost:8000"
    exit 0
fi

cd "\$INSTALL_DIR"
nohup "\$INSTALL_DIR/venv/bin/uvicorn" main:app > /tmp/jsa-server.log 2>&1 &
disown \$!
sleep 2
open "http://localhost:8000"
LAUNCH
chmod +x "$APP_BUNDLE/Contents/MacOS/launch"
ok "App bundle created at ~/Desktop/Job Search.app"

# ── App icon ───────────────────────────────────────────────────────────────────

if command -v sips &>/dev/null && command -v iconutil &>/dev/null; then
    ICON_DEST="$APP_BUNDLE/Contents/Resources/AppIcon.icns"
    python3 "$INSTALL_DIR/scripts/make_icon.py" "$ICON_DEST" 2>/dev/null \
        && ok "App icon generated" \
        || printf '  Icon generation skipped (non-fatal)\n'
fi

# ── Remove macOS quarantine so the app opens without a warning ─────────────────

xattr -rd com.apple.quarantine "$APP_BUNDLE" 2>/dev/null || true

# ── Done ───────────────────────────────────────────────────────────────────────

printf '\n'
printf '  ╔══════════════════════════════════════╗\n'
printf '  ║   %s  All done!                   ║\n' "$(green '✓')"
printf '  ╚══════════════════════════════════════╝\n'
printf '\n'
printf '  %s on your Desktop to launch the app.\n' "$(bold 'Double-click Job Search.app')"
printf '  The server starts automatically and opens in your browser.\n'
printf '\n'
printf '  To start manually:\n'
printf '    %s\n' "$(dim "cd $INSTALL_DIR && source venv/bin/activate && uvicorn main:app")"
printf '\n'
printf '  Logs: %s\n' "$(dim '/tmp/jsa-server.log')"
printf '\n'
