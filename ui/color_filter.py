from pathlib import Path

import cairo
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gdk, GLib, Gtk


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
        button.add_css_class(
            f"color-{color_group}"
        )

        button.set_focusable(False)
        button.set_hexpand(True)
        button.set_vexpand(True)
        button.set_halign(Gtk.Align.FILL)
        button.set_valign(Gtk.Align.FILL)

        button.connect(
            "clicked",
            self.on_button_clicked,
            color_group,
        )

        container.append(button)

        self.append(container)
        self.buttons[color_group] = button

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
            GLib.source_remove(self.search_source)
            self.search_source = None

        self.search_mode = False
        self.search_entry = None

        self.set_colors(self.current_colors)

        self.on_search_changed("")

        self.set_active(self.active_color)

    def on_search_entry_changed(self, entry):
        if self.search_source is not None:
            GLib.source_remove(self.search_source)

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

        return False

    def on_button_clicked(self, _button, color_group):
        self.set_active(color_group)
        self.on_filter_changed(color_group)

    def set_active(self, color_group):
        self.active_color = color_group

        for group, button in self.buttons.items():
            if group == color_group:
                button.add_css_class("selected")
            else:
                button.remove_css_class("selected")