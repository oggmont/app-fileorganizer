#!/bin/sh
# Builds "Video File Organizer.app" in this folder. Double-click it in Finder to start the app,
# or drag it to the Dock or to Applications.
#
# The app runs the code in this folder, so code changes apply on the next launch without a
# rebuild. Run this script again only if you move or rename this folder.
set -e
cd "$(dirname "$0")"
PROJECT="$(pwd)"
APP="$PROJECT/Video File Organizer.app"

./scripts/setup_venv.sh
VERSION="$(.venv/bin/python -c 'import fileorganizer; print(fileorganizer.__version__)')"

rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"

cat > "$APP/Contents/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDevelopmentRegion</key><string>en</string>
    <key>CFBundleDisplayName</key><string>Video File Organizer</string>
    <key>CFBundleName</key><string>Video File Organizer</string>
    <key>CFBundleExecutable</key><string>launcher</string>
    <key>CFBundleIconFile</key><string>AppIcon</string>
    <key>CFBundleIdentifier</key><string>local.app-fileorganizer.video-file-organizer</string>
    <key>CFBundleInfoDictionaryVersion</key><string>6.0</string>
    <key>CFBundlePackageType</key><string>APPL</string>
    <key>CFBundleShortVersionString</key><string>$VERSION</string>
    <key>CFBundleVersion</key><string>$VERSION</string>
    <key>LSApplicationCategoryType</key><string>public.app-category.video</string>
    <key>LSMinimumSystemVersion</key><string>13.0</string>
    <key>NSHighResolutionCapable</key><true/>
</dict>
</plist>
EOF

# The launcher: the project path (quoted for sh), then the body from scripts/launcher.sh.
{
    echo '#!/bin/sh'
    echo '# Built by make_app.sh. Run it again if the project folder moves.'
    printf "PROJECT='%s'\n" "$(printf '%s' "$PROJECT" | sed "s/'/'\\\\''/g")"
    cat scripts/launcher.sh
} > "$APP/Contents/MacOS/launcher"
chmod +x "$APP/Contents/MacOS/launcher"

.venv/bin/python scripts/make_icon.py "$APP/Contents/Resources/AppIcon.icns"

# Let Finder and the Dock pick up the new app and its icon right away.
LSREGISTER=/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister
if [ -x "$LSREGISTER" ]; then "$LSREGISTER" -f "$APP" || true; fi
touch "$APP"

echo "Built: $APP"
echo "Double-click it in Finder, or drag it to the Dock or to Applications."
