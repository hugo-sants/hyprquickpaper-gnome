#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"

INSTALL_DIR="$HOME/.local/share/hyprquickpaper-gnome"
CONFIG_EXAMPLE="$PROJECT_DIR/config.example.json"
CONFIG_FILE="$INSTALL_DIR/config.json"
CACHE_DIR="$HOME/.cache/hyprquickpaper/thumbs"

if [[ ! -f "$CONFIG_EXAMPLE" ]]; then
    echo "Missing config.example.json." >&2
    exit 1
fi

detect_default_wallpaper_dir() {
    if [[ -d "$HOME/Pictures/Wallpapers" ]]; then
        printf '%s\n' "$HOME/Pictures/Wallpapers"
    elif [[ -d "$HOME/Imagens/Wallpapers" ]]; then
        printf '%s\n' "$HOME/Imagens/Wallpapers"
    elif [[ -d "$HOME/Pictures" ]]; then
        printf '%s\n' "$HOME/Pictures/Wallpapers"
    elif [[ -d "$HOME/Imagens" ]]; then
        printf '%s\n' "$HOME/Imagens/Wallpapers"
    else
        printf '%s\n' "$HOME/Pictures/Wallpapers"
    fi
}

default_wallpaper_dir="$(detect_default_wallpaper_dir)"

echo "HyprQuickPaper GNOME installation"
echo
echo "Enter the directory that contains your wallpapers."
echo "Press Enter to use the default: $default_wallpaper_dir"
echo

read -r -p "Wallpaper directory [$default_wallpaper_dir]: " wallpaper_dir

wallpaper_dir="${wallpaper_dir:-$default_wallpaper_dir}"

if [[ "$wallpaper_dir" == "~/"* ]]; then
    wallpaper_dir="$HOME/${wallpaper_dir#~/}"
elif [[ "$wallpaper_dir" != /* ]]; then
    wallpaper_dir="$PROJECT_DIR/$wallpaper_dir"
fi

wallpaper_dir="$(realpath -m "$wallpaper_dir")"

mkdir -p "$INSTALL_DIR"
mkdir -p "$wallpaper_dir" "$CACHE_DIR"

cp "$PROJECT_DIR/app.py" "$INSTALL_DIR/"
cp "$PROJECT_DIR/config.example.json" "$INSTALL_DIR/"
cp -r "$PROJECT_DIR/scripts" "$INSTALL_DIR/"
cp -r "$PROJECT_DIR/cache" "$INSTALL_DIR/"
cp -r "$PROJECT_DIR/wallpaper" "$INSTALL_DIR/"
cp -r "$PROJECT_DIR/ui" "$INSTALL_DIR/"

CONFIG_EXAMPLE="$INSTALL_DIR/config.example.json"

python3 - "$CONFIG_EXAMPLE" "$CONFIG_FILE" "$wallpaper_dir" "$CACHE_DIR" <<'PY'
import json
import sys
from pathlib import Path

example, output, wallpaper_dir, cache_dir = sys.argv[1:]

config = json.loads(
    Path(example).read_text(
        encoding="utf-8"
    )
)

config["wallpaper_path"] = str(
    Path(wallpaper_dir).expanduser().resolve()
)

config["cache_path"] = str(
    Path(cache_dir).expanduser().resolve()
)

Path(output).write_text(
    json.dumps(config, indent=4) + "\n",
    encoding="utf-8",
)
PY

chmod +x "$INSTALL_DIR/app.py"

# Configure a GNOME custom shortcut without replacing existing custom shortcuts.

default_shortcut="<Super>w"

echo
echo "Choose the GNOME shortcut that should open HyprQuickPaper GNOME."
echo "Use GNOME accelerator syntax, for example: <Super>w or <Super><Alt>w"

read -r -p "Shortcut [$default_shortcut]: " wallpaper_shortcut

wallpaper_shortcut="${wallpaper_shortcut:-$default_shortcut}"

script_path="$INSTALL_DIR/app.py"
command="env GSK_RENDERER=gl $script_path"
base="/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/"

existing="$(gsettings get org.gnome.settings-daemon.plugins.media-keys custom-keybindings)"

index=0

while [[ "$existing" == *"${base}custom${index}/"* ]]; do
    index=$((index + 1))
done

shortcut_path="${base}custom${index}/"

if [[ "$existing" == "@as []" ]]; then
    new_keybindings="['$shortcut_path']"
else
    new_keybindings="${existing%]}"
    new_keybindings+=", '$shortcut_path']"
fi

gsettings set org.gnome.settings-daemon.plugins.media-keys custom-keybindings "$new_keybindings"

gsettings set \
    "org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:${shortcut_path}" \
    name \
    "HyprQuickPaper GNOME"

gsettings set \
    "org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:${shortcut_path}" \
    command \
    "$command"

gsettings set \
    "org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:${shortcut_path}" \
    binding \
    "$wallpaper_shortcut"

echo "GNOME shortcut configured: $wallpaper_shortcut"
echo
echo "Installation complete."
echo "Installation directory: $INSTALL_DIR"
echo "Wallpaper directory:    $wallpaper_dir"
echo "Cache directory:        $CACHE_DIR"
echo "GNOME shortcut:         $wallpaper_shortcut"
echo
echo "Test the selector using the configured shortcut:"
echo "  $wallpaper_shortcut"
echo
echo "Or run it directly:"
echo "  GSK_RENDERER=gl $INSTALL_DIR/app.py"
echo
echo "Or, explicitly on Wayland:"
echo "  GDK_BACKEND=wayland GSK_RENDERER=gl $INSTALL_DIR/app.py"