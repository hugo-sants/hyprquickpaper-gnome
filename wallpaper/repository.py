from pathlib import Path


class WallpaperRepository:
    EXTENSIONS = {".jpg", ".jpeg", ".png"}

    def __init__(self, wallpaper_dir):
        self.wallpaper_dir = Path(wallpaper_dir).expanduser()
        self.wallpapers = []
        self.metadata = {}

    def refresh(self):
        try:
            self.wallpapers = sorted(
                (
                    path
                    for path in self.wallpaper_dir.iterdir()
                    if path.is_file()
                    and path.suffix.lower() in self.EXTENSIONS
                ),
                key=lambda path: path.name.lower(),
            )
        except OSError:
            self.wallpapers = []

    def set_metadata(self, metadata):
        self.metadata = metadata

    def get_all(self):
        return list(self.wallpapers)

    def filter_by_color(self, color_group):
        if color_group is None:
            return self.get_all()

        return [
            path
            for path in self.wallpapers
            if self.metadata.get(path.name, {}).get("color_group")
            == color_group
        ]

    def filter_by_name(self, query):
        query = query.casefold().strip()

        if not query:
            return self.get_all()

        return [
            path
            for path in self.wallpapers
            if query in path.name.casefold()
        ]

    def get_available_colors(self):
        colors = []
        seen = set()

        for path in self.wallpapers:
            color_group = self.metadata.get(path.name, {}).get(
                "color_group"
            )

            if color_group is None or color_group in seen:
                continue

            seen.add(color_group)
            colors.append(color_group)

        return colors