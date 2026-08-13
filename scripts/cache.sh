#!/usr/bin/env bash
set -u

APP_DIR="${1:-}"

if [[ -z "$APP_DIR" || ! -f "$APP_DIR/config.json" ]]; then
    echo "Usage: $0 /path/to/hyprquickpaper-gnome" >&2
    exit 1
fi

CONFIG="$APP_DIR/config.json"

wallpaper_path=$(jq -r '.wallpaper_path' "$CONFIG")
cache_path=$(jq -r '.cache_path' "$CONFIG")
cache_batch_size=$(jq -r '.cache_batch_size' "$CONFIG")

mkdir -p "$cache_path"

if command -v magick >/dev/null 2>&1; then
    IM_BIN="magick"
elif command -v convert >/dev/null 2>&1; then
    IM_BIN="convert"
else
    echo "ImageMagick was not found (expected 'magick' or 'convert')." >&2
    exit 1
fi

find "$wallpaper_path" -type f \(     -iname "*.jpg" -o     -iname "*.jpeg" -o     -iname "*.png" \) | while read -r img; do

    filename=$(basename "$img")
    out="$cache_path/$filename"

    if [[ -f "$out" ]]; then
        continue
    fi

    "$IM_BIN" "$img" -thumbnail x500 -strip -quality 85 "$out" &

    if (( cache_batch_size > 0 )); then
        while (( $(jobs -rp | wc -l) >= cache_batch_size )); do
            wait -n
        done
    fi

done

wait
