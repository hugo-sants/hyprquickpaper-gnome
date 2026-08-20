#!/usr/bin/env python3

import json
import math
import os
import signal
import subprocess
import sys
from pathlib import Path

import cairo
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
gi.require_version("GdkPixbuf", "2.0")

from gi.repository import Gdk, GdkPixbuf, Gio, GLib, Gtk
from cache.metadata import MetadataStore
from wallpaper.repository import WallpaperRepository
from ui.color_filter import ColorFilter


APP_DIR = Path(__file__).resolve().parent
CONFIG_FILE = APP_DIR / "config.json"
CACHE_SCRIPT = APP_DIR / "scripts" / "cache.sh"
COMMANDS_SCRIPT = APP_DIR / "scripts" / "commands.sh"


# Keyboard customization: change these sets to adjust the picker shortcuts.
KEY_NEXT = {"j", "right"}
KEY_PREVIOUS = {"k", "left"}
KEY_JUMP_FORWARD = {"d"}
KEY_JUMP_BACKWARD = {"u"}
KEY_APPLY = {"return", "kp_enter", "space"}
KEY_QUIT = {"escape"}


class WallpaperPicker:
    def __init__(self, app: Gtk.Application):
        self.app = app

        self.window = Gtk.ApplicationWindow(application=app)
        self.window.set_title("HyprQuickPaper GNOME")
        self.window.set_decorated(False)
        self.window.set_resizable(False)
        self.window.set_focus_visible(False)

        self.config = self.load_config()

        self.wallpaper_dir = Path(
            self.config["wallpaper_path"]
        ).expanduser()

        self.cache_dir = Path(
            self.config["cache_path"]
        ).expanduser()

        self.repository = WallpaperRepository(self.wallpaper_dir)

        self.metadata_store = MetadataStore(
            self.cache_dir / "metadata.json"
        )

        self.metadata_store.load()
        self.repository.set_metadata(self.metadata_store.data)

        self.active_color = None

        # Appearance customization: odd values (5, 7, 9) keep a single
        # wallpaper visually centered in the carousel.
        self.count_visible = max(
            1,
            int(self.config.get("number_of_pictures", 7))
        )

        # Appearance customization: change the selected border color.
        self.border_color = self.parse_color(
            self.config.get("border_color", "#C27B63")
        )

        self.panel_height = 500

        self.filter_height = 64
        self.filter_gap = 32

        self.shear = -0.3
        self.spacing = 4.0

        self.selected_index = 0

        self.visual_selection = 0.0
        self.target_selection = 0.0

        # Carousel customization: selected size, distant size, scale falloff and horizontal/vertical expansion of the previews.
        self.max_carousel_scale = 1.2
        self.min_carousel_scale = 1.0
        self.carousel_power = 1.0
        self.horizontal_scale = 1.6
        self.vertical_scale = 1.1

        self.content_x = 0.0
        self.target_x = 0.0

        self.animation_source = None

        self.drag_start_x = None
        self.drag_start_content_x = 0.0
        self.last_pointer_x = None

        self.pointer_down = False
        self.press_x = None
        self.press_y = None

        self.images = {}
        self.wallpapers = []

        self.cache_process = None

        self.wallpaper_monitor = None
        self.cache_monitor = None

        self.area = Gtk.DrawingArea()
        self.area.set_focusable(True)
        self.area.set_hexpand(True)
        self.area.set_vexpand(True)
        self.area.set_draw_func(self.draw)

        self.color_filter = ColorFilter(
            self.apply_color_filter,
            self.apply_search_filter,
            self.on_search_key,
        )

        self.color_filter.set_halign(Gtk.Align.CENTER)
        self.color_filter.set_valign(Gtk.Align.START)
        self.color_filter.set_margin_top(16)

        self.overlay = Gtk.Overlay()
        self.overlay.set_child(self.area)
        self.overlay.add_overlay(self.color_filter)

        self.window.set_child(self.overlay)

        self.install_input_controllers()
        self.install_css()

        self.area.connect("resize", self.on_resize)
        self.window.connect("close-request", self.on_close_request)

    @staticmethod
    def load_config():
        with CONFIG_FILE.open("r", encoding="utf-8") as fh:
            return json.load(fh)

    @staticmethod
    def parse_color(value):
        rgba = Gdk.RGBA()

        if not rgba.parse(value):
            rgba.parse("#C27B63")

        return rgba

    def update_metadata(self):
        self.metadata_store.load()
        self.repository.set_metadata(self.metadata_store.data)

    def update_color_filter(self):
        if not hasattr(self, "color_filter"):
            return

        colors = self.repository.get_available_colors()
        self.color_filter.set_colors(colors)

    def apply_color_filter(self, color_group):
        self.active_color = color_group

        self.wallpapers = self.repository.filter_by_color(
            color_group
        )

        self.selected_index = 0
        self.visual_selection = 0.0
        self.target_selection = 0.0

        if self.wallpapers:
            self.selected_index = 0
            self.visual_selection = 0.0
            self.target_selection = 0.0
            self.ensure_visible(0)

        self.area.queue_draw()

    def on_search_key(self, key):
        if key in KEY_NEXT:
            self.move_selection(1)

        elif key in KEY_PREVIOUS:
            self.move_selection(-1)

        elif key in KEY_JUMP_FORWARD:
            self.move_selection(self.count_visible)

        elif key in KEY_JUMP_BACKWARD:
            self.move_selection(-self.count_visible)

        elif key in KEY_APPLY:
            self.activate_current()

        elif key in KEY_QUIT:
            self.area.grab_focus()

    def apply_search_filter(self, query):
        if query:
            self.wallpapers = self.repository.filter_by_name(
                query
            )
        else:
            self.wallpapers = self.repository.filter_by_color(
                self.active_color
            )

        self.selected_index = 0
        self.visual_selection = 0.0
        self.target_selection = 0.0

        if self.wallpapers:
            self.ensure_visible(0)

        self.area.queue_draw()

    def install_css(self):
        provider = Gtk.CssProvider()

        provider.load_from_data(
            b"""
            window.background {
                background: rgba(0, 0, 0, 0.0);
            }
            """
        )

        Gtk.StyleContext.add_provider_for_display(
            self.window.get_display(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

    def install_input_controllers(self):
        click = Gtk.GestureClick()
        click.set_button(0)
        click.connect("pressed", self.on_click_pressed)
        click.connect("released", self.on_click_released)
        self.area.add_controller(click)

        drag = Gtk.GestureDrag()
        drag.set_button(1)
        drag.connect("drag-begin", self.on_drag_begin)
        drag.connect("drag-update", self.on_drag_update)
        drag.connect("drag-end", self.on_drag_end)
        self.area.add_controller(drag)

        scroll = Gtk.EventControllerScroll.new(
            Gtk.EventControllerScrollFlags.VERTICAL
            | Gtk.EventControllerScrollFlags.HORIZONTAL
        )
        scroll.connect("scroll", self.on_scroll)
        self.area.add_controller(scroll)

        key = Gtk.EventControllerKey()
        key.connect("key-pressed", self.on_key_pressed)
        self.area.add_controller(key)

    def show(self):
        self.refresh_wallpapers()

        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self.load_cached_images()
        except OSError:
            pass

        self.update_metadata()
        self.repository.set_metadata(self.metadata_store.data)
        self.update_color_filter()

        self.install_file_monitors()

        display = self.window.get_display()
        monitors = display.get_monitors()

        monitor = (
            monitors.get_item(0)
            if monitors.get_n_items()
            else None
        )

        window_height = math.ceil(
            self.filter_height
            + self.panel_height * self.vertical_scale
            + self.filter_gap * 2
        )

        if monitor is not None:
            geometry = monitor.get_geometry()
            self.window.set_default_size(
                geometry.width,
                window_height,
            )
        else:
            self.window.set_default_size(1920, window_height)

        self.window.present()

        if self.wallpapers:
            self.ensure_visible(self.selected_index)

        self.area.grab_focus()

        self.start_cache_generation()

    def install_file_monitors(self):
        if self.wallpaper_monitor is None:
            try:
                wallpaper_file = Gio.File.new_for_path(
                    str(self.wallpaper_dir)
                )

                self.wallpaper_monitor = (
                    wallpaper_file.monitor_directory(
                        Gio.FileMonitorFlags.NONE,
                        None,
                    )
                )

                self.wallpaper_monitor.connect(
                    "changed",
                    self.on_wallpaper_directory_changed,
                )

            except GLib.Error as exc:
                print(
                    f"Failed to monitor wallpaper directory: {exc}",
                    file=sys.stderr,
                )

        if self.cache_monitor is None:
            try:
                cache_file = Gio.File.new_for_path(
                    str(self.cache_dir)
                )

                self.cache_monitor = (
                    cache_file.monitor_directory(
                        Gio.FileMonitorFlags.NONE,
                        None,
                    )
                )

                self.cache_monitor.connect(
                    "changed",
                    self.on_cache_directory_changed,
                )

            except GLib.Error as exc:
                print(
                    f"Failed to monitor cache directory: {exc}",
                    file=sys.stderr,
                )

    def on_wallpaper_directory_changed(
        self,
        _monitor,
        _file,
        _other_file,
        event_type,
    ):
        if event_type not in {
            Gio.FileMonitorEvent.CREATED,
            Gio.FileMonitorEvent.DELETED,
            Gio.FileMonitorEvent.MOVED_IN,
            Gio.FileMonitorEvent.MOVED_OUT,
            Gio.FileMonitorEvent.CHANGED,
        }:
            return

        self.refresh_wallpapers()

    def on_cache_directory_changed(
        self,
        _monitor,
        _file,
        _other_file,
        event_type,
    ):
        if event_type not in {
            Gio.FileMonitorEvent.CREATED,
            Gio.FileMonitorEvent.DELETED,
            Gio.FileMonitorEvent.MOVED_IN,
            Gio.FileMonitorEvent.MOVED_OUT,
            Gio.FileMonitorEvent.CHANGED,
        }:
            return

        self.load_cached_images()
        self.update_metadata()
        self.repository.set_metadata(self.metadata_store.data)
        self.update_color_filter()

    def on_resize(self, _area, width, height):
        self.area.queue_draw()

    def get_panel_geometry(self, width, height):
        available_height = height - self.filter_height

        panel_h = min(
            self.panel_height,
            available_height
        )

        panel_y = (
            self.filter_height
            + self.filter_gap
            + (
                available_height
                - self.filter_gap * 2
                - panel_h
            ) / 2.0
        )

        return panel_y, panel_h

    def refresh_wallpapers(self):
        self.repository.refresh()
        self.repository.set_metadata(self.metadata_store.data)

        previous_count = len(self.wallpapers)
        self.wallpapers = self.repository.get_all()

        if not self.wallpapers:
            self.selected_index = 0
            self.visual_selection = 0.0
            self.target_selection = 0.0

        elif previous_count == 0:
            self.selected_index = self.count_visible // 2
            self.visual_selection = float(self.selected_index)
            self.target_selection = float(self.selected_index)

        self.area.queue_draw()

    def load_cached_images(self):
        for wall in self.wallpapers:
            cache_path = self.cache_dir / wall.name

            if not cache_path.is_file():
                continue

            try:
                mtime = cache_path.stat().st_mtime
            except OSError:
                continue

            old = self.images.get(wall.name)

            if old and old[0] == mtime:
                continue

            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file(
                    str(cache_path)
                )

                self.images[wall.name] = (mtime, pixbuf)

            except Exception as exc:
                print(
                    f"Failed to load thumbnail "
                    f"{cache_path}: {exc}",
                    file=sys.stderr
                )

        self.area.queue_draw()

    def start_cache_generation(self):
        if not CACHE_SCRIPT.is_file():
            print(f"Missing {CACHE_SCRIPT}", file=sys.stderr)
            return

        if not os.access(CACHE_SCRIPT, os.X_OK):
            print(
                f"{CACHE_SCRIPT} is not executable",
                file=sys.stderr
            )
            return

        try:
            self.cache_process = subprocess.Popen(
                [
                    str(CACHE_SCRIPT),
                    str(APP_DIR)
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )

        except OSError as exc:
            print(
                f"Failed to start cache script: {exc}",
                file=sys.stderr
            )

    def panel_metrics(self, width):
        tile_width = width / self.count_visible - 10.0
        tile_width = max(1.0, tile_width)
        step = tile_width + self.spacing

        return tile_width, step

    def start_animation(self):
        if self.animation_source is None:
            self.animation_source = GLib.timeout_add(
                16,
                self.animate,
            )

    def set_target_scroll(self, value, animate=True):
        self.target_x = float(value)

        if not animate:
            self.content_x = self.target_x
            self.area.queue_draw()
            return

        self.start_animation()

    def animate(self):
        scroll_delta = self.target_x - self.content_x
        selection_delta = self.target_selection - self.visual_selection

        scroll_done = abs(scroll_delta) < 0.5
        selection_done = abs(selection_delta) < 0.01

        if scroll_done:
            self.content_x = self.target_x
        else:
            self.content_x += scroll_delta * 0.09

        if selection_done:
            self.visual_selection = self.target_selection
        else:
            self.visual_selection += selection_delta * 0.15

        self.area.queue_draw()

        if scroll_done and selection_done:
            self.animation_source = None
            return False

        return True

    def set_selection(self, index):
        if not self.wallpapers:
            return

        self.selected_index = int(index)
        self.target_selection = float(self.selected_index)

        self.start_animation()

        self.ensure_visible(self.selected_index)
        self.area.queue_draw()

    def get_carousel_scale(self, index):
        distance = abs(index - self.visual_selection)

        scale = (self.min_carousel_scale + 
                (self.max_carousel_scale - self.min_carousel_scale) / 
                (1.0 + distance ** self.carousel_power))

        return scale

    def ensure_visible(self, index):
        width = self.area.get_width()
        tile_width, step = self.panel_metrics(width)

        item_center = index * step + tile_width / 2.0
        viewport_center = width / 2.0

        target = item_center - viewport_center

        self.set_target_scroll(target)

    def move_selection(self, amount):
        if not self.wallpapers:
            return

        new_index = self.selected_index + amount
        self.set_selection(new_index)

    def activate_current(self):
        if not self.wallpapers:
            return

        real_index = self.selected_index % len(self.wallpapers)
        path = self.wallpapers[real_index]

        if not COMMANDS_SCRIPT.is_file():
            print(f"Missing {COMMANDS_SCRIPT}", file=sys.stderr)
            return

        try:
            subprocess.Popen(
                [
                    str(COMMANDS_SCRIPT),
                    str(path)
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )

        except OSError as exc:
            print(
                f"Failed to apply wallpaper: {exc}",
                file=sys.stderr
            )
            return

        self.quit()

    def on_key_pressed(
        self,
        _controller,
        keyval,
        _keycode,
        state,
    ):
        name = Gdk.keyval_name(keyval) or ""
        key = name.lower()

        if key in KEY_NEXT:
            self.move_selection(1)

        elif key in KEY_PREVIOUS:
            self.move_selection(-1)

        elif key in KEY_JUMP_FORWARD:
            self.move_selection(self.count_visible)

        elif key in KEY_JUMP_BACKWARD:
            self.move_selection(-self.count_visible)

        elif key in KEY_APPLY:
            self.activate_current()

        elif key in KEY_QUIT:
            self.quit()

        else:
            return False

        return True

    def point_to_index(self, x, y):
        width = self.area.get_width()
        height = self.area.get_height()

        panel_y, panel_h = self.get_panel_geometry(width, height)

        if y < panel_y or y > panel_y + panel_h:
            return None

        tile_width, step = self.panel_metrics(width)

        local_x = x + self.content_x
        index = math.floor(local_x / step)

        inside_x = local_x - index * step

        if inside_x > tile_width:
            return None

        return index

    def on_click_pressed(
        self,
        gesture,
        n_press,
        x,
        y
    ):
        self.pointer_down = True
        self.press_x = x
        self.press_y = y
        self.last_pointer_x = x

        gesture.set_state(Gtk.EventSequenceState.CLAIMED)

    def on_click_released(
        self,
        _gesture,
        _n_press,
        x,
        y
    ):
        if not self.pointer_down:
            return

        self.pointer_down = False

        if (
            self.press_x is not None
            and math.hypot(x - self.press_x, y - self.press_y) > 8
        ):
            self.press_x = None
            self.press_y = None
            return

        self.press_x = None
        self.press_y = None

        index = self.point_to_index(x, y)

        if index is None:
            return

        self.set_selection(index)
        self.activate_current()

    def on_drag_begin(
        self,
        _gesture,
        x,
        y
    ):
        self.drag_start_x = x
        self.drag_start_content_x = self.content_x

    def on_drag_update(
        self,
        _gesture,
        offset_x,
        _offset_y
    ):
        if self.drag_start_x is None:
            return

        self.set_target_scroll(
            self.drag_start_content_x - offset_x,
            animate=False,
        )

    def on_drag_end(
        self,
        gesture,
        offset_x,
        _offset_y
    ):
        if abs(offset_x) > 8:
            self.drag_start_x = None
            return

        self.drag_start_x = None

    def on_scroll(
        self,
        _controller,
        dx,
        dy
    ):
        delta = dy if abs(dy) >= abs(dx) else dx

        self.set_target_scroll(
            self.content_x - delta * 80.0
        )

        return True

    @staticmethod
    def draw_cover_pixbuf(
        cr,
        pixbuf,
        x,
        y,
        width,
        height
    ):
        pw = pixbuf.get_width()
        ph = pixbuf.get_height()

        if pw <= 0 or ph <= 0 or width <= 0 or height <= 0:
            return

        scale = max(width / pw, height / ph)

        dw = pw * scale
        dh = ph * scale

        ox = x + (width - dw) / 2.0
        oy = y + (height - dh) / 2.0

        cr.save()

        cr.rectangle(x, y, width, height)
        cr.clip()

        cr.translate(ox, oy)
        cr.scale(scale, scale)

        Gdk.cairo_set_source_pixbuf(cr, pixbuf, 0, 0)
        cr.paint()

        cr.restore()

    def draw_tile(
        self,
        cr,
        path,
        x,
        y,
        tile_width,
        tile_height,
        scale,
        index,
        selected
    ):
        cr.save()

        center_x = tile_width / 2.0
        center_y = tile_height / 2.0

        selection_progress = max(0.0, 1.0 - abs(self.visual_selection - index))

        scaled_width = (tile_width * (1.0 + (self.horizontal_scale - 1.0) * selection_progress))

        scaled_height = (tile_height * (1.0 + (self.vertical_scale - 1.0) * selection_progress))

        left = x + center_x - scaled_width / 2.0
        top = y + center_y - scaled_height / 2.0

        right = left + scaled_width
        bottom = top + scaled_height

        shear_offset = abs(self.shear) * scaled_height

        left -= shear_offset / 2.0
        right -= shear_offset / 2.0

        cr.new_path()

        cr.move_to(left + shear_offset, top)
        cr.line_to(right + shear_offset, top)
        cr.line_to(right, bottom)
        cr.line_to(left, bottom)

        cr.close_path()

        cr.clip()

        pix_info = self.images.get(path.name)

        if pix_info:
            self.draw_cover_pixbuf(
                cr,
                pix_info[1],
                left,
                top,
                scaled_width + shear_offset,
                scaled_height
            )

        if selected and pix_info:
            cr.reset_clip()

            cr.set_source_rgba(
                self.border_color.red,
                self.border_color.green,
                self.border_color.blue,
                1.0
            )

            cr.set_line_width(4.0)

            cr.new_path()

            cr.move_to(left + shear_offset, top)
            cr.line_to(right + shear_offset, top)
            cr.line_to(right, bottom)
            cr.line_to(left, bottom)

            cr.close_path()

            cr.stroke()

        cr.restore()

    def draw(
        self,
        _area,
        cr,
        width,
        height
    ):
        if not self.wallpapers:
            return

        panel_y, panel_h = self.get_panel_geometry(width, height)
        tile_width, step = self.panel_metrics(width)

        visible = []

        visible_range = max(self.count_visible + 2, 6)

        center = int(math.floor(self.visual_selection))
        start = center - visible_range
        end = center + visible_range + 1

        for index in range(start, end):
            real_index = index % len(self.wallpapers)
            path = self.wallpapers[real_index]

            x = index * step - self.content_x

            extra_width = tile_width * (self.horizontal_scale - 1.0)

            if index < self.selected_index:
                x -= extra_width / 2.0
            elif index > self.selected_index:
                x += extra_width / 2.0

            margin = tile_width * 0.25

            if x > width + margin:
                continue

            if x + tile_width < -margin:
                continue

            distance = abs(index - self.visual_selection)

            visible.append((distance, index, path, x))

        visible.sort(key=lambda item: item[0], reverse=True)

        for distance, index, path, x in visible:
            scale = self.get_carousel_scale(index)

            self.draw_tile(
                cr,
                path,
                x,
                panel_y,
                tile_width,
                panel_h,
                scale,
                index,
                index == self.selected_index
            )

    def quit(self):
        if self.animation_source:
            GLib.source_remove(self.animation_source)
            self.animation_source = None

        if self.wallpaper_monitor:
            self.wallpaper_monitor.cancel()
            self.wallpaper_monitor = None

        if self.cache_monitor:
            self.cache_monitor.cancel()
            self.cache_monitor = None

        self.app.quit()

    def on_close_request(self, _window):
        self.quit()
        return False


class Application(Gtk.Application):

    def __init__(self):
        super().__init__(
            application_id="wallpaper.picker",
            flags=0,
        )

        self.picker = None

    def do_activate(self):
        if self.picker is None:
            self.picker = WallpaperPicker(self)

        self.picker.show()


def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = Application()

    raise SystemExit(app.run(sys.argv))


if __name__ == "__main__":
    main()