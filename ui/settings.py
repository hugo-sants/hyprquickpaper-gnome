from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gdk, Gtk


class SettingsView(Gtk.Box):
    def __init__(self, settings, on_close, on_reset):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)

        self.add_css_class("settings-view")
        self.on_close = on_close
        self.on_reset = on_reset
        self.settings = dict(settings)
        self.value_labels = {}
        self.color_buttons = {}
        self.tab_buttons = {}
        self._changing_tab = False

        self.build_header()
        self.build_pages()
        self.show_page("appearance")
        self.install_input_controllers()
        self.install_css()

    def set_settings(self, settings):
        self.settings = dict(settings)

        for key, (label, digits) in self.value_labels.items():
            label.set_text(self.format_value(self.settings[key], digits))

        for key, button in self.color_buttons.items():
            rgba = Gdk.RGBA()

            if rgba.parse(self.settings[key]):
                button.set_rgba(rgba)

    def install_css(self):
        provider = Gtk.CssProvider()
        css_path = Path(__file__).resolve().parent / "settings.css"
        provider.load_from_path(str(css_path))
        Gtk.StyleContext.add_provider_for_display(self.get_display(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    def install_input_controllers(self):
        key = Gtk.EventControllerKey()
        key.connect("key-pressed", self.on_key_pressed)
        self.add_controller(key)

    def on_key_pressed(self, _controller, keyval, _keycode, _state):
        if (Gdk.keyval_name(keyval) or "").lower() == "escape":
            self.on_close(dict(self.settings))
            return True

        return False

    def build_header(self):
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        header.add_css_class("settings-header")
        header.set_margin_top(12)
        header.set_margin_start(12)
        header.set_margin_end(12)

        tabs = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        tabs.add_css_class("settings-tabs")
        tabs.set_halign(Gtk.Align.CENTER)
        tabs.set_hexpand(True)

        self.add_tab(tabs, "general", "settings-symbolic", "General")
        self.add_tab(tabs, "appearance", "applications-graphics-symbolic", "Appearance")

        close_button = Gtk.Button()
        close_button.add_css_class("settings-close-button")
        close_button.set_focusable(False)
        close_button.set_valign(Gtk.Align.CENTER)
        close_button.set_tooltip_text("Close settings")
        close_button.set_child(Gtk.Image.new_from_icon_name("window-close-symbolic"))
        close_button.connect("clicked", self.on_close_clicked)

        header.append(tabs)
        header.append(close_button)
        self.append(header)

    def add_tab(self, parent, name, icon_name, label):
        button = Gtk.ToggleButton()
        button.add_css_class("settings-tab")
        button.set_focusable(False)
        button.set_child(self.create_tab_content(icon_name, label))
        button.connect("toggled", self.on_tab_toggled, name)
        parent.append(button)
        self.tab_buttons[name] = button

    @staticmethod
    def create_tab_content(icon_name, label):
        content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        icon = Gtk.Image.new_from_icon_name(icon_name)
        text = Gtk.Label(label=label)
        content.append(icon)
        content.append(text)
        return content

    def build_pages(self):
        stack = Gtk.Stack()
        stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        stack.set_transition_duration(140)
        stack.set_hexpand(True)
        stack.set_vexpand(True)
        stack.add_css_class("settings-stack")
        stack.add_named(self.build_general_page(), "general")
        stack.add_named(self.build_appearance_page(), "appearance")
        self.stack = stack
        self.append(stack)

    def build_appearance_page(self):
        content = self.create_scrolled_content()
        self.add_section_title(content, "Layout")
        layout = self.create_group()

        self.add_numeric_row(layout, "number_of_pictures", "Visible wallpapers", "Number of wallpaper positions shown in the carousel.", self.settings["number_of_pictures"], 3, 15, 1, digits=0)
        
        self.add_numeric_row(layout, "spacing", "Spacing", "Distance between wallpaper previews.", self.settings["spacing"], 0, 50, 1, digits=0)
        self.add_numeric_row(layout, "shear", "Shear", "Diagonal perspective applied to the previews.", self.settings["shear"], 0.0, 1.0, 0.05, digits=2)

        content.append(layout)
        self.add_section_title(content, "Carousel scaling")
        scaling = self.create_group()

        self.add_numeric_row(scaling, "horizontal_scale", "Horizontal expansion", "Additional width applied to the selected wallpaper.", self.settings["horizontal_scale"], 1.0, 3.0, 0.05, digits=2)
        self.add_numeric_row(scaling, "vertical_scale", "Vertical expansion", "Additional height applied to the selected wallpaper.", self.settings["vertical_scale"], 1.0, 3.0, 0.05, digits=2)
        content.append(scaling)
        
        self.add_section_title(content, "Selected wallpaper")
        selected = self.create_group()
        self.add_color_row(selected, "border_color", "Border color", "Color of the selected wallpaper border.", self.settings["border_color"])
        content.append(selected)

        self.add_section_title(content, "Transparency")
        transparency = self.create_group()
        self.add_numeric_row(transparency, "filter_opacity", "Filter", "Controls the opacity of the wallpaper filter.", self.settings["filter_opacity"], 0, 100, 5, digits=0)
        self.add_numeric_row(transparency, "settings_opacity", "Settings panel", "Controls the opacity of the settings panel.", self.settings["settings_opacity"], 0, 100, 5, digits=0)
        content.append(transparency)

        return self.wrap_scrolled_content(content)

    def build_general_page(self):
        content = self.create_scrolled_content()
        self.add_section_title(content, "Wallpaper")
        wallpaper = self.create_group()

        self.add_info_row(wallpaper, "Wallpaper directory", "Directory used as the wallpaper source.", self.settings["wallpaper_path"])
        content.append(wallpaper)
        self.add_section_title(content, "Keyboard")
        keyboard = self.create_group()
        self.add_info_row(keyboard, "Open picker", "Keyboard shortcut used to open the wallpaper picker.", "Super+W")
        content.append(keyboard)
        self.add_section_title(content, "Settings")
        settings = self.create_group()

        reset_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        reset_row.add_css_class("settings-row")

        labels = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
        labels.set_hexpand(True)

        title_label = Gtk.Label(label="Reset settings", xalign=0)
        title_label.add_css_class("settings-row-title")

        subtitle_label = Gtk.Label(label="Restore all appearance settings to their default values.", xalign=0)
        subtitle_label.add_css_class("settings-row-subtitle")
        subtitle_label.set_wrap(True)

        labels.append(title_label)
        labels.append(subtitle_label)

        reset_button = Gtk.Button(label="Reset")
        reset_button.add_css_class("settings-reset-button")
        reset_button.set_valign(Gtk.Align.CENTER)
        reset_button.set_focusable(False)
        reset_button.connect("clicked", self.on_reset_clicked)

        reset_row.append(labels)
        reset_row.append(reset_button)

        settings.append(reset_row)
        content.append(settings)

        return self.wrap_scrolled_content(content)

    def create_scrolled_content(self):
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        content.add_css_class("settings-content")
        content.set_margin_top(22)
        content.set_margin_start(52)
        content.set_margin_end(52)
        content.set_margin_bottom(28)

        return content

    @staticmethod
    def wrap_scrolled_content(content):
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_hexpand(True)
        scrolled.set_vexpand(True)
        scrolled.add_css_class("settings-scroll")
        scrolled.set_child(content)

        return scrolled

    @staticmethod
    def add_section_title(parent, title):
        label = Gtk.Label(label=title)
        label.add_css_class("settings-section-title")
        label.set_halign(Gtk.Align.START)
        label.set_margin_top(4)
        parent.append(label)

    @staticmethod
    def create_group():
        group = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        group.add_css_class("settings-group")
        return group

    @staticmethod
    def format_value(value, digits):
        return f"{value:.{digits}f}" if digits else str(int(value))
    
    def add_numeric_row(self, parent, key, title, subtitle, value, minimum, maximum, step, digits=1):
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        row.add_css_class("settings-row")

        labels = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
        labels.set_hexpand(True)

        title_label = Gtk.Label(label=title, xalign=0)
        title_label.add_css_class("settings-row-title")

        subtitle_label = Gtk.Label(label=subtitle, xalign=0)
        subtitle_label.add_css_class("settings-row-subtitle")
        subtitle_label.set_wrap(True)

        labels.append(title_label)
        labels.append(subtitle_label)

        control = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        control.add_css_class("settings-number-control")
        control.set_valign(Gtk.Align.CENTER)

        value_label = Gtk.Label()
        value_label.add_css_class("settings-value")
        value_label.set_width_chars(6)
        value_label.set_xalign(1)
        value_label.set_text(self.format_value(value, digits))

        self.value_labels[key] = (value_label, digits)

        minus = Gtk.Button(label="−")
        minus.add_css_class("settings-step-button")
        minus.set_focusable(False)
        minus.set_valign(Gtk.Align.CENTER)

        plus = Gtk.Button(label="+")
        plus.add_css_class("settings-step-button")
        plus.set_focusable(False)
        plus.set_valign(Gtk.Align.CENTER)

        def update(delta):
            current = float(self.settings[key])
            new_value = max(minimum, min(maximum, current + delta))
            self.settings[key] = new_value
            value_label.set_text(self.format_value(new_value, digits))

        minus.connect("clicked", lambda _button: update(-step))
        plus.connect("clicked", lambda _button: update(step))

        control.append(value_label)
        control.append(minus)
        control.append(plus)

        row.append(labels)
        row.append(control)
        parent.append(row)

    def on_color_changed(self, button, _pspec, key):
        rgba = button.get_rgba()
        self.settings[key] = rgba.to_string()

    def add_color_row(self, parent, key, title, subtitle, value):
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        row.add_css_class("settings-row")

        labels = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
        labels.set_hexpand(True)

        title_label = Gtk.Label(label=title, xalign=0)
        title_label.add_css_class("settings-row-title")

        subtitle_label = Gtk.Label(label=subtitle, xalign=0)
        subtitle_label.add_css_class("settings-row-subtitle")
        subtitle_label.set_wrap(True)

        labels.append(title_label)
        labels.append(subtitle_label)

        dialog = Gtk.ColorDialog()
        dialog.set_title("Border color")

        color_button = Gtk.ColorDialogButton()
        color_button.set_dialog(dialog)
        color_button.set_valign(Gtk.Align.CENTER)
        color_button.add_css_class("settings-color-button")

        rgba = Gdk.RGBA()
        rgba.parse(value)
        color_button.set_rgba(rgba)

        self.color_buttons[key] = color_button

        color_button.connect("notify::rgba", self.on_color_changed, key)

        row.append(labels)
        row.append(color_button)
        parent.append(row)

    @staticmethod
    def add_info_row(parent, title, subtitle, value):
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        row.add_css_class("settings-row")

        labels = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
        labels.set_hexpand(True)
        title_label = Gtk.Label(label=title, xalign=0)
        title_label.add_css_class("settings-row-title")
        subtitle_label = Gtk.Label(label=subtitle, xalign=0)
        subtitle_label.add_css_class("settings-row-subtitle")
        subtitle_label.set_wrap(True)
        labels.append(title_label)
        labels.append(subtitle_label)

        value_label = Gtk.Label(label=value)
        value_label.add_css_class("settings-value")
        row.append(labels)
        row.append(value_label)
        parent.append(row)

    @staticmethod
    def draw_color_swatch(_area, cr, width, height, color):
        rgba = Gdk.RGBA()
        rgba.parse(color)
        radius = min(width, height) / 2.0 - 1.0
        cr.arc(width / 2.0, height / 2.0, radius, 0, 6.283185307179586)
        cr.set_source_rgba(rgba.red, rgba.green, rgba.blue, rgba.alpha)
        cr.fill()

    def on_tab_toggled(self, button, name):
        if self._changing_tab or not button.get_active():
            return

        self._changing_tab = True
        for tab_name, tab_button in self.tab_buttons.items():
            tab_button.set_active(tab_name == name)
        self.stack.set_visible_child_name(name)
        self._changing_tab = False

    def show_page(self, name):
        self._changing_tab = True
        self.stack.set_visible_child_name(name)
        for tab_name, button in self.tab_buttons.items():
            button.set_active(tab_name == name)
        self._changing_tab = False

    def on_close_clicked(self, _button):
        self.on_close(dict(self.settings))

    def on_reset_clicked(self, _button):
        self.on_reset()
