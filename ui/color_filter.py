from pathlib import Path

import cairo
import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gdk, GLib, Gtk


COLOR_VALUES = {
    "red": "#E53935",
    "orange": "#FB8C00",
    "yellow": "#FDD835",
    "green": "#43A047",
    "cyan": "#00ACC1",
    "blue": "#1E88E5",
    "purple": "#8E24AA",
    "pink": "#D81B60",
    "gray": "#9E9E9E",
}


class ColorSwatch(Gtk.DrawingArea):
    def __init__(self, color_group):
        super().__init__()

        self.color_group = color_group
        self.selected = False

        self.set_content_width(32)
        self.set_content_height(32)
        self.set_hexpand(True)
        self.set_vexpand(True)
        self.set_halign(Gtk.Align.FILL)
        self.set_valign(Gtk.Align.FILL)

        self.set_draw_func(self.draw)

    def set_selected(self, selected):
        if self.selected == selected:
            return

        self.selected = selected
        self.queue_draw()

    def draw(self, _area, cr, width, height):
        color = Gdk.RGBA()

        if not color.parse(
            COLOR_VALUES.get(
                self.color_group,
                "#9E9E9E",
            )
        ):
            color.parse("#9E9E9E")

        radius = 8.0
        inset = 2.0

        x = inset
        y = inset
        w = width - inset * 2.0
        h = height - inset * 2.0

        cr.new_path()
        cr.arc(
            x + radius,
            y + radius,
            radius,
            3.141592653589793,
            4.71238898038469,
        )
        cr.arc(
            x + w - radius,
            y + radius,
            radius,
            4.71238898038469,
            0.0,
        )
        cr.arc(
            x + w - radius,
            y + h - radius,
            radius,
            0.0,
            1.5707963267948966,
        )
        cr.arc(
            x + radius,
            y + h - radius,
            radius,
            1.5707963267948966,
            3.141592653589793,
        )
        cr.close_path()

        cr.set_source_rgba(
            color.red,
            color.green,
            color.blue,
            color.alpha,
        )
        cr.fill()

        if self.selected:
            cr.new_path()
            cr.arc(
                x + radius,
                y + radius,
                radius,
                3.141592653589793,
                4.71238898038469,
            )
            cr.arc(
                x + w - radius,
                y + radius,
                radius,
                4.71238898038469,
                0.0,
            )
            cr.arc(
                x + w - radius,
                y + h - radius,
                radius,
                0.0,
                1.5707963267948966,
            )
            cr.arc(
                x + radius,
                y + h - radius,
                radius,
                1.5707963267948966,
                3.141592653589793,
            )
            cr.close_path()

            cr.set_source_rgba(
                1.0,
                1.0,
                1.0,
                0.95,
            )
            cr.set_line_width(1.9)
            cr.stroke()


class ColorFilter(Gtk.Box):
    def __init__(
        self,
        on_filter_changed,
        on_search_changed,
        on_search_key,
    ):
        super().__init__(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=12,
        )

        self.add_css_class("color-filter")
        self.set_focusable(False)

        self.on_filter_changed = on_filter_changed
        self.on_search_changed = on_search_changed
        self.on_search_key = on_search_key

        self.active_color = None
        self.buttons = {}
        self.swatches = {}
        self.current_colors = []
        self.search_entry = None
        self.search_source = None
        self.search_mode = False

        self.install_css()

    def install_css(self):
        provider = Gtk.CssProvider()

        css_path = (
            Path(__file__).resolve().parent
            / "color_filter.css"
        )

        provider.load_from_path(str(css_path))

        Gtk.StyleContext.add_provider_for_display(
            self.get_display(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

    def set_colors(self, colors):
        self.current_colors = list(colors)

        if self.search_mode:
            return

        while child := self.get_first_child():
            self.remove(child)

        self.buttons.clear()
        self.swatches.clear()

        self.add_all_button()

        for color in self.current_colors:
            self.add_color_button(color)

        self.add_search_button()
        self.set_active(self.active_color)

    def add_all_button(self):
        container = Gtk.Box()
        container.set_size_request(32, 32)
        container.set_halign(Gtk.Align.CENTER)
        container.set_valign(Gtk.Align.CENTER)

        button = Gtk.Button()
        button.add_css_class("all-button")
        button.set_focusable(False)
        button.set_hexpand(True)
        button.set_vexpand(True)
        button.set_halign(Gtk.Align.FILL)
        button.set_valign(Gtk.Align.FILL)

        icon = Gtk.Image.new_from_icon_name(
            "view-grid-symbolic"
        )

        icon.add_css_class("all-icon")

        button.set_child(icon)

        button.connect(
            "clicked",
            self.on_button_clicked,
            None,
        )

        container.append(button)
        self.append(container)

        self.buttons[None] = button

    def add_color_button(self, color_group):
        container = Gtk.Box()
        container.set_size_request(32, 32)
        container.set_halign(Gtk.Align.CENTER)
        container.set_valign(Gtk.Align.CENTER)

        button = Gtk.Button()
        button.add_css_class("color-button")
        button.set_focusable(False)
        button.set_hexpand(True)
        button.set_vexpand(True)
        button.set_halign(Gtk.Align.FILL)
        button.set_valign(Gtk.Align.FILL)

        button.set_tooltip_text(
            color_group.capitalize()
        )

        swatch = ColorSwatch(color_group)

        button.set_child(swatch)

        button.connect(
            "clicked",
            self.on_button_clicked,
            color_group,
        )

        container.append(button)
        self.append(container)

        self.buttons[color_group] = button
        self.swatches[color_group] = swatch

    def add_search_button(self):
        container = Gtk.Box()
        container.set_size_request(32, 32)
        container.set_halign(Gtk.Align.CENTER)
        container.set_valign(Gtk.Align.CENTER)

        button = Gtk.Button()
        button.add_css_class("search-button")
        button.set_focusable(False)
        button.set_hexpand(True)
        button.set_vexpand(True)
        button.set_halign(Gtk.Align.FILL)
        button.set_valign(Gtk.Align.FILL)

        icon = Gtk.Image.new_from_icon_name(
            "system-search-symbolic"
        )

        icon.add_css_class("search-icon")

        button.set_child(icon)

        button.connect(
            "clicked",
            self.open_search,
        )

        container.append(button)
        self.append(container)

    def open_search(self, _button):
        if self.search_mode:
            return

        self.search_mode = True

        while child := self.get_first_child():
            self.remove(child)

        self.buttons.clear()
        self.swatches.clear()

        back_container = Gtk.Box()
        back_container.set_size_request(32, 32)
        back_container.set_halign(Gtk.Align.CENTER)
        back_container.set_valign(Gtk.Align.CENTER)

        back_button = Gtk.Button()
        back_button.add_css_class("search-back-button")
        back_button.set_focusable(False)
        back_button.set_hexpand(True)
        back_button.set_vexpand(True)
        back_button.set_halign(Gtk.Align.FILL)
        back_button.set_valign(Gtk.Align.FILL)

        icon = Gtk.Image.new_from_icon_name(
            "go-previous-symbolic"
        )

        back_button.set_child(icon)

        back_button.connect(
            "clicked",
            self.close_search,
        )

        back_container.append(back_button)
        self.append(back_container)

        self.search_entry = Gtk.SearchEntry()
        self.search_entry.add_css_class("search-entry")
        self.search_entry.set_hexpand(True)
        self.search_entry.set_placeholder_text(
            "Search wallpapers"
        )

        key = Gtk.EventControllerKey()

        key.connect(
            "key-pressed",
            self.on_search_key_pressed,
        )

        self.search_entry.add_controller(key)

        self.search_entry.connect(
            "changed",
            self.on_search_entry_changed,
        )

        self.search_entry.connect(
            "activate",
            self.on_search_activate,
        )

        self.append(self.search_entry)
        self.search_entry.grab_focus()

    def close_search(self, _button=None):
        if not self.search_mode:
            return

        if self.search_source is not None:
            GLib.source_remove(
                self.search_source
            )
            self.search_source = None

        self.search_mode = False
        self.search_entry = None

        self.set_colors(self.current_colors)

        self.on_search_changed("")
        self.set_active(self.active_color)

    def on_search_entry_changed(self, entry):
        if self.search_source is not None:
            GLib.source_remove(
                self.search_source
            )

        query = entry.get_text()

        self.search_source = GLib.timeout_add(
            150,
            self.run_search,
            query,
        )

    def run_search(self, query):
        self.search_source = None
        self.on_search_changed(query)
        return False

    def on_search_activate(self, entry):
        self.on_search_changed(
            entry.get_text()
        )

    def on_search_key_pressed(
        self,
        _controller,
        keyval,
        _keycode,
        state,
    ):
        name = Gdk.keyval_name(keyval) or ""
        key = name.lower()

        if key in {
            "j",
            "k",
            "right",
            "left",
            "d",
            "u",
            "return",
            "kp_enter",
            "space",
            "escape",
        }:
            self.on_search_key(key)

        return True

    def on_button_clicked(
        self,
        _button,
        color_group,
    ):
        self.set_active(color_group)
        self.on_filter_changed(color_group)

    def set_active(self, color_group):
        self.active_color = color_group

        for group, button in self.buttons.items():
            if group == color_group:
                button.add_css_class("selected")
            else:
                button.remove_css_class("selected")

        for group, swatch in self.swatches.items():
            swatch.set_selected(
                group == color_group
            )