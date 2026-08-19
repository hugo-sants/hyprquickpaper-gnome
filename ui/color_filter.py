from pathlib import Path

import cairo
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gtk


class ColorFilter(Gtk.Box):
    def __init__(self, on_filter_changed):
        super().__init__(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=12,
        )

        self.add_css_class("color-filter")
        self.set_focusable(False)

        self.on_filter_changed = on_filter_changed
        self.active_color = None
        self.buttons = {}

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
        while child := self.get_first_child():
            self.remove(child)

        self.buttons.clear()

        self.add_all_button()

        self.add_separator()

        for color in colors:
            self.add_color_button(color)

        self.set_active(None)

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
        button.set_tooltip_text("All")

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

    def add_separator(self):
        triangle = Gtk.DrawingArea()

        triangle.set_content_width(12)
        triangle.set_content_height(32)

        triangle.set_halign(Gtk.Align.CENTER)
        triangle.set_valign(Gtk.Align.CENTER)

        def draw_triangle(_area, cr, width, height):
            center_y = height / 2

            cr.move_to(0, center_y - 6)
            cr.line_to(0, center_y + 6)
            cr.line_to(12, center_y)
            cr.close_path()

            cr.set_source_rgba(
                1.0,
                1.0,
                1.0,
                0.65,
            )

            cr.fill()

        triangle.set_draw_func(draw_triangle)

        self.append(triangle)

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
        button.set_tooltip_text(
            color_group.capitalize()
        )

        button.connect(
            "clicked",
            self.on_button_clicked,
            color_group,
        )

        container.append(button)

        self.append(container)
        self.buttons[color_group] = button

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