#!/usr/bin/env bash

set -euo pipefail

INSTALL_DIR="$HOME/.local/share/hyprquickpaper-gnome"
CACHE_DIR="$HOME/.cache/hyprquickpaper"

echo "HyprQuickPaper GNOME uninstallation"
echo

if [[ -d "$INSTALL_DIR" ]]; then
rm -rf "$INSTALL_DIR"
echo "Removed: $INSTALL_DIR"
else
echo "Installation directory not found: $INSTALL_DIR"
fi

if [[ -d "$CACHE_DIR" ]]; then
rm -rf "$CACHE_DIR"
echo "Removed: $CACHE_DIR"
else
echo "Cache directory not found: $CACHE_DIR"
fi

echo
echo "The GNOME custom shortcut is managed separately through GSettings."
echo "Remove 'HyprQuickPaper GNOME' from:"
echo "Settings → Keyboard → View and Customize Shortcuts → Custom Shortcuts"
echo
echo "Uninstallation complete."