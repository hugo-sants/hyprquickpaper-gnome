# HyprQuickPaper GNOME

![HyprQuickPaper GNOME](assets/demo.png)

A lightweight wallpaper selector for GNOME/GTK4, focused on a fast, visual, and keyboard-optimized workflow. The project offers a standalone implementation for GNOME.

The selected wallpaper is visually highlighted while the others remain visible, allowing for quick navigation through a large collection without the need to open a traditional file picker.

It also provides color-based filtering and name search, allowing wallpapers to be found visually or directly by filename.

Inspired by the visual approach of [ilyamiro's dotfiles](https://github.com/ilyamiro), particularly the Hyprland-oriented workflow and interface style. This is an independent GNOME/GTK4 implementation rather than a dependency or direct port of that repository.

## Features

### Animated wallpaper carousel

Wallpapers are displayed in a horizontal carousel with:

* A prominent selected wallpaper.
* Smooth transitions between selections.
* Equal-sized unselected wallpapers.
* Horizontal and vertical expansion of the selected wallpaper.
* Shear/perspective styling without distorting the actual image content.
* Mouse, keyboard and wheel navigation.
* Circular navigation through the wallpaper collection.

### Search

![Wallpaper search](assets/search.png)

A search button at the end of the color filter opens a compact search field.

Search is designed to remain lightweight and responsive:

* Searches by wallpaper filename.
* Case-insensitive.
* Updates while typing.
* No image processing is performed during the search.
* The existing wallpaper metadata and thumbnail cache are reused.
* The search can be navigated using the same carousel controls.

The back button closes the search and restores the normal filter interface.

### Color filtering

![Color filter](assets/color-filter.png)

The color filter provides a visual way to narrow the wallpaper collection.

Only color groups that actually exist in the current wallpaper collection are displayed. For example, a collection containing only blue and gray wallpapers will only display those available groups.

Selecting a color immediately updates the carousel to show wallpapers belonging to that group.

The first button restores the default unfiltered order.

### Fast thumbnail loading

Wallpapers are displayed using cached thumbnails instead of repeatedly loading the original images.

The cache is generated automatically and updated when wallpapers change, reducing the amount of work required while browsing the collection.

### GNOME integration

The installer creates a GNOME custom keyboard shortcut for opening the selector while preserving existing custom shortcuts.

The selected wallpaper is applied through GNOME's desktop background settings.

## Dependencies

The project is designed for GNOME and supports both Wayland and X11 sessions. It requires Python 3, GTK 4, PyGObject, Pycairo, `jq`, ImageMagick, and the GNOME `gsettings` command.

### Fedora

```bash
sudo dnf install \
    gtk4 \
    python3-gobject \
    python3-cairo \
    glib2 \
    jq \
    ImageMagick
```

### Ubuntu / Debian

The package names differ from Fedora. On Ubuntu or Debian systems with GTK 4 available:

```bash
sudo apt update
sudo apt install \
    python3 \
    python3-gi \
    python3-cairo \
    python3-gi-cairo \
    gir1.2-gtk-4.0 \
    libglib2.0-bin \
    jq \
    imagemagick
```

`libglib2.0-bin` provides `gsettings`, which is used by the installer to create the GNOME keyboard shortcut.

### Arch Linux

```bash
sudo pacman -S \
    gtk4 \
    python-gobject \
    python-cairo \
    glib2 \
    jq \
    imagemagick
```

### Other distributions

Other GNOME-based distributions can also run the project when they provide the equivalent packages for:

* Python 3
* GTK 4
* PyGObject
* Pycairo
* GdkPixbuf / GTK 4 introspection data
* GLib and `gsettings`
* `jq`
* ImageMagick

Package names vary between distributions, so install the corresponding packages from your distribution's repositories.

## Project structure

```text
hyprquickpaper-gnome/
├── app.py
├── config.example.json
├── Makefile
├── install.sh
├── uninstall.sh
├── cache/
│   ├── metadata.py
│   └── ...
├── wallpaper/
│   ├── color.py
│   └── repository.py
├── ui/
│   ├── color_filter.py
│   ├── color_filter.css
│   └── window.css
├── scripts/
│   ├── cache.sh
│   └── commands.sh
├── assets/
│   ├── demo.png
│   ├── color-filter.png
│   └── search.png
├── README.md
├── .gitignore
└── .gitattributes
```

## Installation

Clone the repository and enter it:

```bash
git clone https://github.com/hugo-sants/hyprquickpaper-gnome.git
cd hyprquickpaper-gnome
```

The project uses the provided `Makefile` as the main entry point for installation.

```bash
make install
```

The installer asks where your wallpapers are stored and which GNOME keyboard shortcut should open the picker.

The default shortcut is:

```text
Super+W
```

GNOME accelerator syntax can also be used, for example:

```text
<Super>w
<Super><Alt>w
```

The installer preserves existing GNOME custom shortcuts and creates a new shortcut for HyprQuickPaper GNOME.

### Wallpaper directory

The installer automatically chooses a default wallpaper directory in this order:

1. `~/Pictures/Wallpapers`
2. `~/Imagens/Wallpapers`
3. `~/Pictures/Wallpapers` when `~/Pictures` exists
4. `~/Imagens/Wallpapers` when `~/Imagens` exists
5. `~/Pictures/Wallpapers` as the fallback

The selected directory is created automatically when necessary.

You can also enter another directory when prompted by the installer.

### Installation locations

The installed application is stored in:

```text
~/.local/share/hyprquickpaper-gnome
```

Thumbnail and metadata cache:

```text
~/.cache/hyprquickpaper/thumbs
```

The generated configuration is stored at:

```text
~/.local/share/hyprquickpaper-gnome/config.json
```

The installer copies the application, UI, cache, wallpaper and script modules into the installation directory so the installed application can run independently from the original repository.

After installation, use the configured GNOME shortcut to open the selector.

## Run

The recommended way to run the application from the repository is:

```bash
make run
```

This uses the renderer configuration intended for the selector and is preferable to invoking `python3 app.py` directly.

The application can also be started manually with:

```bash
GSK_RENDERER=ngl python3 app.py
```

When running the installed application directly:

```bash
GSK_RENDERER=ngl ~/.local/share/hyprquickpaper-gnome/app.py
```

On Wayland, the backend can be specified explicitly:

```bash
GDK_BACKEND=wayland \
GSK_RENDERER=ngl \
~/.local/share/hyprquickpaper-gnome/app.py
```

The GNOME shortcut created by the installer launches the installed application using the configured renderer.

## Cache

Thumbnail generation is handled separately from the browsing interface.

To generate or update the thumbnail cache manually:

```bash
make cache
```

The cache process:

* Reads the wallpaper and cache locations from `config.json`.
* Generates thumbnails using ImageMagick.
* Reuses existing thumbnails whenever possible.
* Limits the number of concurrent thumbnail jobs.
* Updates the wallpaper metadata used by the application.
* Calculates the information required by the color filter.

The cache is stored in:

```text
~/.cache/hyprquickpaper/thumbs
```

The directory contains the generated thumbnails and:

```text
metadata.json
```

The cache is normally generated automatically by the application, but `make cache` is useful when rebuilding it manually or after changing a large wallpaper collection.

The number of simultaneous thumbnail jobs can be controlled through `cache_batch_size` in `config.json`.

Example:

```json
{
    "cache_batch_size": 20
}
```

Higher values can make cache generation faster, but may increase CPU and memory usage during the process.

## Keyboard and mouse controls

| Action                   | Default             |
| ------------------------ | ------------------- |
| Next wallpaper           | `J` / `Right Arrow` |
| Previous wallpaper       | `K` / `Left Arrow`  |
| Jump forward             | `D`                 |
| Jump backward            | `U`                 |
| Apply selected wallpaper | `Enter` / `Space`   |
| Exit selector            | `Esc`               |
| Select with mouse        | Click a wallpaper   |
| Horizontal navigation    | Mouse wheel         |
| Horizontal scrolling     | Left-drag           |

### Search controls

When the name search is active:

| Action              | Behavior                                         |
| ------------------- | ------------------------------------------------ |
| `J` / `Right Arrow` | Next result                                      |
| `K` / `Left Arrow`  | Previous result                                  |
| `D`                 | Jump forward                                     |
| `U`                 | Jump backward                                    |
| `Enter` / `Space`   | Apply result                                     |
| `Esc`               | Leave the search field while keeping the results |
| Back button         | Close search and restore the filter interface    |

The search result remains active until the back button is used.

## GNOME shortcut

`make install` configures a GNOME custom shortcut automatically.

Existing custom shortcuts are preserved.

To change the shortcut later, open:

**Settings → Keyboard → View and Customize Shortcuts → Custom Shortcuts**

Find **HyprQuickPaper GNOME** and edit its shortcut.

The shortcut created by the installer points to the installed application rather than the source directory.

## Customization

### `config.json`

**Location:** generated by `make install` in `~/.local/share/hyprquickpaper-gnome/`.

| Attribute            | Description                                                                                                                   |
| -------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| `wallpaper_path`     | Directory containing wallpapers.                                                                                              |
| `cache_path`         | Thumbnail and metadata cache location.                                                                                        |
| `number_of_pictures` | Number of visible wallpaper positions in the carousel. Odd values such as `5`, `7` or `9` work best for a centered selection. |
| `border_color`       | Color of the selected wallpaper border.                                                                                       |
| `cache_batch_size`   | Number of thumbnails generated concurrently during cache creation.                                                            |

Example:

```json
{
    "wallpaper_path": "/home/user/Pictures/Wallpapers",
    "cache_path": "/home/user/.cache/hyprquickpaper/thumbs",
    "number_of_pictures": 7,
    "border_color": "#1D70F9",
    "cache_batch_size": 20
}
```

### Carousel appearance

**Location:** `WallpaperPicker.__init__()` in `app.py`

```python
self.panel_height = 500
self.shear = -0.3
self.spacing = 4.0
```

* `panel_height` controls the base height of wallpaper previews.
* `shear` controls the diagonal perspective effect. Values closer to `0` make the previews straighter.
* `spacing` controls the distance between previews.

### Carousel scaling

```python
self.max_carousel_scale = 1.2
self.min_carousel_scale = 1.0
self.carousel_power = 1.0
```

* `max_carousel_scale` controls the maximum carousel scale.
* `min_carousel_scale` controls the scale of wallpapers away from the center.
* `carousel_power` controls how quickly the scale changes with distance.

Using:

```python
self.min_carousel_scale = 1.0
```

keeps unselected wallpapers at the same base size.

### Selected wallpaper expansion

```python
self.horizontal_scale = 1.6
self.vertical_scale = 1.1
```

These values control the additional width and height applied to the selected wallpaper.

For example:

```python
self.horizontal_scale = 1.8
self.vertical_scale = 1.15
```

makes the selected wallpaper wider and slightly taller.

### Filter and window spacing

The filter occupies its own area above the carousel.

```python
self.filter_height = 64
self.filter_gap = 32
```

* `filter_height` reserves vertical space for the filter.
* `filter_gap` controls the space between the filter and carousel.

### Animation

Selection and scrolling are animated continuously while a transition is active.

The animation speed can be adjusted in `animate()`:

```python
self.content_x += scroll_delta * 0.15
self.visual_selection += selection_delta * 0.22
```

Higher values make the selector react faster. Lower values produce a slower and softer transition.

### Keyboard customization

Keyboard mappings are defined near the top of `app.py`:

```python
KEY_NEXT = {"j", "right"}
KEY_PREVIOUS = {"k", "left"}
KEY_JUMP_FORWARD = {"d"}
KEY_JUMP_BACKWARD = {"u"}
KEY_APPLY = {"return", "kp_enter", "space"}
KEY_QUIT = {"escape"}
```

The values can be changed to customize the controls.

For example:

```python
KEY_NEXT = {"l", "right"}
```

adds `L` as another next-wallpaper shortcut.

## Filter customization

The visual appearance of the color filter is controlled by:

```text
ui/color_filter.css
```

This includes:

* Filter background.
* Border and shadow.
* Rounded corners.
* Color button appearance.
* Selected-state border.
* Search button.
* Search field appearance.

The actual set of available color groups is generated from the wallpaper metadata, so unavailable colors are not displayed.

## Uninstallation

To remove the installed application and its local cache:

```bash
make uninstall
```

This removes the installed application from:

```text
~/.local/share/hyprquickpaper-gnome
```

and the local HyprQuickPaper cache from:

```text
~/.cache/hyprquickpaper
```

The wallpaper files themselves are not removed.

The GNOME custom shortcut is stored separately in GSettings. After uninstalling, remove the **HyprQuickPaper GNOME** shortcut from:

**Settings → Keyboard → View and Customize Shortcuts → Custom Shortcuts**

Then remove the corresponding **HyprQuickPaper GNOME** entry.