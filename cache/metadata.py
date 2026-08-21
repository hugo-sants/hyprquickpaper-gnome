import json
import sys
from pathlib import Path

import gi

gi.require_version("GdkPixbuf", "2.0")

from gi.repository import GdkPixbuf

from wallpaper.color import classify_rgb, rgb_to_hex


class MetadataStore:
    def __init__(self, path):
        self.path = Path(path).expanduser()
        self.data = {}

    def load(self):
        if not self.path.is_file():
            self.data = {}
            return self.data

        try:
            with self.path.open("r", encoding="utf-8") as file:
                self.data = json.load(file)
        except (OSError, json.JSONDecodeError):
            self.data = {}

        return self.data

    def save(self):
        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temporary_path = self.path.with_suffix(
            f"{self.path.suffix}.tmp"
        )

        temporary_path.write_text(
            json.dumps(
                self.data,
                indent=4,
            ) + "\n",
            encoding="utf-8",
        )

        temporary_path.replace(self.path)

    def get(self, filename):
        return self.data.get(filename)

    def set(self, filename, mtime, dominant_color, color_group):
        self.data[filename] = {
            "mtime": mtime,
            "dominant_color": dominant_color,
            "color_group": color_group,
        }

    def is_current(self, filename, mtime):
        entry = self.get(filename)

        return (
            entry is not None
            and entry.get("mtime") == mtime
        )

    def update_from_thumbnail(
        self,
        wallpaper_path,
        thumbnail_path,
    ):
        wallpaper_path = Path(wallpaper_path).expanduser()
        thumbnail_path = Path(thumbnail_path).expanduser()

        filename = wallpaper_path.name

        try:
            mtime = wallpaper_path.stat().st_mtime
        except OSError:
            return False

        if self.is_current(filename, mtime):
            return False

        if not thumbnail_path.is_file():
            return False

        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(
                str(thumbnail_path)
            )
        except Exception:
            return False

        red, green, blue = self.get_dominant_color(pixbuf)

        dominant_color = rgb_to_hex(
            red,
            green,
            blue,
        )

        color_group = classify_rgb(
            red,
            green,
            blue,
        )

        self.set(
            filename,
            mtime,
            dominant_color,
            color_group,
        )

        return True

    @staticmethod
    def get_dominant_color(pixbuf):
        width = pixbuf.get_width()
        height = pixbuf.get_height()
        rowstride = pixbuf.get_rowstride()
        channels = pixbuf.get_n_channels()
        pixels = pixbuf.get_pixels()

        if width <= 0 or height <= 0:
            return 0, 0, 0

        max_dimension = 48

        step_x = max(
            1,
            width // max_dimension,
        )

        step_y = max(
            1,
            height // max_dimension,
        )

        samples = []

        for y in range(0, height, step_y):
            row = y * rowstride

            for x in range(0, width, step_x):
                offset = row + x * channels

                red = pixels[offset]
                green = pixels[offset + 1]
                blue = pixels[offset + 2]

                samples.append(
                    (red, green, blue)
                )

        if not samples:
            return 0, 0, 0

        def srgb_to_linear(value):
            value /= 255.0

            if value <= 0.04045:
                return value / 12.92

            return ((value + 0.055) / 1.055) ** 2.4

        def rgb_to_lab(red, green, blue):
            red = srgb_to_linear(red)
            green = srgb_to_linear(green)
            blue = srgb_to_linear(blue)

            x = (
                red * 0.4124564
                + green * 0.3575761
                + blue * 0.1804375
            )

            y = (
                red * 0.2126729
                + green * 0.7151522
                + blue * 0.0721750
            )

            z = (
                red * 0.0193339
                + green * 0.1191920
                + blue * 0.9503041
            )

            x /= 0.95047
            y /= 1.00000
            z /= 1.08883

            delta = 6 / 29

            def f(value):
                if value > delta ** 3:
                    return value ** (1 / 3)

                return value / (3 * delta ** 2) + 4 / 29

            fx = f(x)
            fy = f(y)
            fz = f(z)

            return (
                116 * fy - 16,
                500 * (fx - fy),
                200 * (fy - fz),
            )

        lab_samples = []

        for red, green, blue in samples:
            lightness, a, b = rgb_to_lab(
                red,
                green,
                blue,
            )

            chroma = (
                a * a
                + b * b
            ) ** 0.5

            if lightness < 10:
                neutral = True
            elif lightness < 25:
                neutral = chroma < 5
            elif lightness < 70:
                neutral = chroma < 8
            else:
                neutral = chroma < 10

            if neutral:
                chroma_weight = 0.08
            else:
                chroma_weight = min(
                    1.0,
                    0.35 + chroma / 30.0,
                )

            lab_samples.append(
                (
                    red,
                    green,
                    blue,
                    lightness,
                    a,
                    b,
                    chroma,
                    chroma_weight,
                    neutral,
                )
            )

        chromatic_samples = [
            sample
            for sample in lab_samples
            if not sample[8]
        ]

        chromatic_ratio = (
            len(chromatic_samples)
            / len(lab_samples)
        )

        if chromatic_ratio < 0.08:
            neutral_samples = [
                sample
                for sample in lab_samples
                if sample[8]
            ]

            if not neutral_samples:
                return 0, 0, 0

            total = len(neutral_samples)

            return (
                round(
                    sum(sample[0] for sample in neutral_samples)
                    / total
                ),
                round(
                    sum(sample[1] for sample in neutral_samples)
                    / total
                ),
                round(
                    sum(sample[2] for sample in neutral_samples)
                    / total
                ),
            )

        cluster_count = min(
            7,
            max(3, len(lab_samples) // 100),
        )

        centers = []

        first = max(
            chromatic_samples,
            key=lambda item: item[7],
        )

        centers.append(
            first[3:6]
        )

        while len(centers) < cluster_count:
            best_sample = None
            best_distance = -1

            for sample in lab_samples:
                lab = sample[3:6]

                distance = min(
                    (
                        (lab[0] - center[0]) ** 2
                        + (lab[1] - center[1]) ** 2
                        + (lab[2] - center[2]) ** 2
                    )
                    for center in centers
                )

                weighted_distance = (
                    distance
                    * sample[7]
                )

                if weighted_distance > best_distance:
                    best_distance = weighted_distance
                    best_sample = sample

            centers.append(
                best_sample[3:6]
            )

        groups = []

        for _ in range(10):
            groups = [
                []
                for _ in centers
            ]

            for sample in lab_samples:
                lab = sample[3:6]

                nearest_index = min(
                    range(len(centers)),
                    key=lambda index: (
                        (lab[0] - centers[index][0]) ** 2
                        + (lab[1] - centers[index][1]) ** 2
                        + (lab[2] - centers[index][2]) ** 2
                    ),
                )

                groups[nearest_index].append(
                    sample
                )

            new_centers = []

            for index, group in enumerate(groups):
                if not group:
                    new_centers.append(
                        centers[index]
                    )
                    continue

                total_weight = sum(
                    sample[7]
                    for sample in group
                )

                if total_weight <= 0:
                    new_centers.append(
                        centers[index]
                    )
                    continue

                center_l = sum(
                    sample[3] * sample[7]
                    for sample in group
                ) / total_weight

                center_a = sum(
                    sample[4] * sample[7]
                    for sample in group
                ) / total_weight

                center_b = sum(
                    sample[5] * sample[7]
                    for sample in group
                ) / total_weight

                new_centers.append(
                    (
                        center_l,
                        center_a,
                        center_b,
                    )
                )

            centers = new_centers

        best_cluster = None
        best_score = -1

        for index, group in enumerate(groups):
            if not group:
                continue

            chromatic_pixels = [
                sample
                for sample in group
                if not sample[8]
            ]

            if not chromatic_pixels:
                continue

            chromatic_area = len(
                chromatic_pixels
            )

            center = centers[index]

            chroma = (
                center[1] ** 2
                + center[2] ** 2
            ) ** 0.5

            chroma_factor = (
                0.75
                + min(
                    1.0,
                    chroma / 50.0,
                ) * 0.25
            )

            score = (
                chromatic_area
                * chroma_factor
            )

            if score > best_score:
                best_score = score
                best_cluster = chromatic_pixels

        if not best_cluster:
            total = len(lab_samples)

            return (
                round(
                    sum(sample[0] for sample in lab_samples)
                    / total
                ),
                round(
                    sum(sample[1] for sample in lab_samples)
                    / total
                ),
                round(
                    sum(sample[2] for sample in lab_samples)
                    / total
                ),
            )

        total_weight = sum(
            sample[7]
            for sample in best_cluster
        )

        red = round(
            sum(
                sample[0] * sample[7]
                for sample in best_cluster
            )
            / total_weight
        )

        green = round(
            sum(
                sample[1] * sample[7]
                for sample in best_cluster
            )
            / total_weight
        )

        blue = round(
            sum(
                sample[2] * sample[7]
                for sample in best_cluster
            )
            / total_weight
        )

        return (
            red,
            green,
            blue,
        )

    def remove_missing(self, filenames):
        filenames = set(filenames)

        self.data = {
            filename: entry
            for filename, entry in self.data.items()
            if filename in filenames
        }


def process_directory(wallpaper_path, cache_path):
    wallpaper_path = Path(wallpaper_path).expanduser()
    cache_path = Path(cache_path).expanduser()

    metadata_path = cache_path / "metadata.json"

    store = MetadataStore(metadata_path)
    store.load()

    filenames = []

    try:
        wallpapers = sorted(
            (
                path
                for path in wallpaper_path.iterdir()
                if path.is_file()
                and path.suffix.lower()
                in {".jpg", ".jpeg", ".png"}
            ),
            key=lambda path: path.name.lower(),
        )
    except OSError:
        return

    for wallpaper in wallpapers:
        filenames.append(wallpaper.name)

        thumbnail = cache_path / wallpaper.name

        store.update_from_thumbnail(
            wallpaper,
            thumbnail,
        )

    store.remove_missing(filenames)
    store.save()


def main():
    if len(sys.argv) != 3:
        print(
            "Usage: python3 -m cache.metadata "
            "/path/to/wallpapers /path/to/cache",
            file=sys.stderr,
        )
        return 1

    process_directory(
        sys.argv[1],
        sys.argv[2],
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())