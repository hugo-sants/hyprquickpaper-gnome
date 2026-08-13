#!/usr/bin/env bash
set -u

WALLPAPER="${1:-}"

if [[ ! -f "$WALLPAPER" ]]; then
    echo "Wallpaper not found: $WALLPAPER" >&2
    exit 1
fi

URI="file://$WALLPAPER"

gsettings set org.gnome.desktop.background picture-uri "$URI"
gsettings set org.gnome.desktop.background picture-uri-dark "$URI"
