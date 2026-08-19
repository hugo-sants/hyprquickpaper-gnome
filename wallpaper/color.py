from dataclasses import dataclass
from math import sqrt


@dataclass(frozen=True)
class ColorGroup:
    name: str
    color: str

COLOR_GROUPS = {
    "red": ColorGroup("red", "#E53935"),
    "orange": ColorGroup("orange", "#FB8C00"),
    "yellow": ColorGroup("yellow", "#FDD835"),
    "green": ColorGroup("green", "#43A047"),
    "cyan": ColorGroup("cyan", "#00ACC1"),
    "blue": ColorGroup("blue", "#1E88E5"),
    "purple": ColorGroup("purple", "#8E24AA"),
    "pink": ColorGroup("pink", "#D81B60"),
    "gray": ColorGroup("gray", "#9E9E9E"),
}

def rgb_to_hex(red, green, blue):
    return f"#{red:02X}{green:02X}{blue:02X}"

def _srgb_to_linear(value):
    value /= 255.0

    if value <= 0.04045:
        return value / 12.92

    return ((value + 0.055) / 1.055) ** 2.4


def _rgb_to_xyz(red, green, blue):
    red = _srgb_to_linear(red)
    green = _srgb_to_linear(green)
    blue = _srgb_to_linear(blue)

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

    return x, y, z


def _lab_f(value):
    delta = 6 / 29

    if value > delta ** 3:
        return value ** (1 / 3)

    return value / (3 * delta ** 2) + 4 / 29


def _rgb_to_lab(red, green, blue):
    x, y, z = _rgb_to_xyz(red, green, blue)

    x /= 0.95047
    y /= 1.00000
    z /= 1.08883

    fx = _lab_f(x)
    fy = _lab_f(y)
    fz = _lab_f(z)

    lightness = 116 * fy - 16
    a = 500 * (fx - fy)
    b = 200 * (fy - fz)

    return lightness, a, b

def _lab_distance(color_a, color_b):
    dl = color_a[0] - color_b[0]
    da = color_a[1] - color_b[1]
    db = color_a[2] - color_b[2]

    return sqrt(
        dl * dl
        + da * da
        + db * db
    )


def _hex_to_rgb(value):
    value = value.lstrip("#")

    return (
        int(value[0:2], 16),
        int(value[2:4], 16),
        int(value[4:6], 16),
    )

_GROUP_LAB = {
    name: _rgb_to_lab(
        *_hex_to_rgb(group.color)
    )
    for name, group in COLOR_GROUPS.items()
}

def classify_rgb(red, green, blue):
    lab = _rgb_to_lab(
        red,
        green,
        blue,
    )

    lightness, a, b = lab

    chroma = (
        a * a
        + b * b
    ) ** 0.5

    if lightness < 15:
        if chroma < 4:
            return "gray"

    elif lightness < 30:
        if chroma < 6:
            return "gray"

    elif lightness < 70:
        if chroma < 9:
            return "gray"

    else:
        if chroma < 11:
            return "gray"

    best_group = None
    best_distance = float("inf")

    for name, group_lab in _GROUP_LAB.items():
        if name == "gray":
            continue

        distance = _lab_distance(
            lab,
            group_lab,
        )

        if distance < best_distance:
            best_distance = distance
            best_group = name

    return best_group


def get_group(name):
    return COLOR_GROUPS[name]


def get_group_color(name):
    return COLOR_GROUPS[name].color