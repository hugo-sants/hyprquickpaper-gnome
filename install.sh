#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_EXAMPLE="$SCRIPT_DIR/config.example.json"
CONFIG_FILE="$SCRIPT_DIR/config.json"
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
    wallpaper_dir="$SCRIPT_DIR/$wallpaper_dir"
fi

wallpaper_dir="$(realpath -m "$wallpaper_dir")"

mkdir -p "$wallpaper_dir" "$CACHE_DIR"

python3 - "$CONFIG_EXAMPLE" "$CONFIG_FILE" "$wallpaper_dir" "$CACHE_DIR" <<'PY'
import json
import sys
from pathlib import Path

example, output, wallpaper_dir, cache_dir = sys.argv[1:]

config = json.loads(Path(example).read_text(encoding="utf-8"))
config["wallpaper_path"] = str(Path(wallpaper_dir).expanduser().resolve())
config["cache_path"] = str(Path(cache_dir).expanduser().resolve())

Path(output).write_text(
    json.dumps(config, indent=4) + "\n",
    encoding="utf-8",
)
PY

chmod +x "$SCRIPT_DIR/app.py"
chmod +x "$SCRIPT_DIR/scripts/cache.sh"
chmod +x "$SCRIPT_DIR/scripts/commands.sh"

# Configure a GNOME custom shortcut without replacing existing custom shortcuts.
default_shortcut="<Super>w"

echo
echo "Choose the GNOME shortcut that should open HyprQuickPaper GNOME."
echo "Use GNOME accelerator syntax, for example: <Super>w or <Super><Alt>w"
read -r -p "Shortcut [$default_shortcut]: " wallpaper_shortcut
wallpaper_shortcut="${wallpaper_shortcut:-$default_shortcut}"

python3 - "$SCRIPT_DIR" "$wallpaper_shortcut" <<'PY'
import sys
from pathlib import Path

script_dir = Path(sys.argv[1]).resolve()
shortcut = sys.argv[2]
command = f"env GDK_BACKEND=wayland python3 {script_dir / 'app.py'}"

try:
    from gi.repository import Gio
except Exception as exc:
    print(f"Could not load GSettings bindings: {exc}", file=sys.stderr)
    raise SystemExit(1)

settings = Gio.Settings.new("org.gnome.settings-daemon.plugins.media-keys")
existing = list(settings.get_strv("custom-keybindings"))

base = "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/"
used = set(existing)

index = 0
while f"{base}custom{index}/" in used:
    index += 1

path = f"{base}custom{index}/"

existing.append(path)
settings.set_strv("custom-keybindings", existing)

custom = Gio.Settings.new_with_path(
    "org.gnome.settings-daemon.plugins.media-keys.custom-keybinding",
    path,
)
custom.set_string("name", "HyprQuickPaper GNOME")
custom.set_string("command", command)
custom.set_string("binding", shortcut)

print(f"GNOME shortcut configured: {shortcut}")
PY

echo
echo "Installation complete."
echo "Wallpaper directory: $wallpaper_dir"
echo "Cache directory:     $CACHE_DIR"
echo "GNOME shortcut:      $wallpaper_shortcut"
echo
echo "Test the selector using the configured shortcut:"
echo "  $wallpaper_shortcut"
echo
echo "Or run it directly:"
echo "  ./app.py"
echo
echo "Or, explicitly on Wayland:"
echo "  GDK_BACKEND=wayland ./app.py"