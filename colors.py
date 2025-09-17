"""Color-related functions for devicons"""

import subprocess
import time

import ranger.api
from ranger import RANGERDIR
from ranger.core.shared import SettingsAware

# Initial version 2025-09-06 deepseek/deepseek-chat-v3.1:free with prompt:
# Please create a compact python function `color_from_stat(file.stat.st_mtime)`
# that maps a file's age to the 256-Color terminal palette, walking smoothly
# along the edges of the color cube from corner to corner with this mapping:
#
# up to 1 hour: white > magenta
# up to 1 day: magenta > red
# up to 1 week: red > orange    (orange changed to yellow)
# up to 1 year: orange > green  (orange changed to yellow)
# up to 5 years: green > cyan
# up to 20 years: cyan > blue
# up to 50 years: blue > white

# Define time thresholds in seconds
_thresholds = [
    3600,        # 1 hour
    86400,       # 1 day
    604800,      # 1 week
    31536000,    # 1 year
    157680000,   # 5 years
    630720000,   # 20 years
    1576800000   # 50 years
]

# Color cube corners (RGB values in 0-5 range for 256-color palette)
_colors = [
    (5, 5, 5),   # white
    (5, 0, 5),   # magenta
    (5, 0, 0),   # red
    (5, 5, 0),   # yellow
    (0, 5, 0),   # green
    (0, 5, 5),   # cyan
    (0, 0, 5),   # blue
    (5, 5, 5)    # white
]


def use_color():
    """
    Check if in-line color is supported by ranger and switched on
    """
    settings = SettingsAware.settings

    try:
        # ANSI color handling fix in 3802f91a901a49d2c6dc8e65d45d4ba08a4fb29c
        has_3802f91a = subprocess.call(
            ["sed -n '/def split_ansi_from_text/,+1p' gui/ansi.py"
             + "| grep -q isinstance"],
            cwd=RANGERDIR, shell=True) == 0
    except subprocess.CalledProcessError:
        pass

    ranger_supports_color = has_3802f91a or \
        tuple(map(int, ranger.__version__.split('.'))) > (1, 9, 4)
    return ranger_supports_color and settings.devicons_color


def rgb_to_term_palette(r, g, b):
    """
    Convert RGB (0-5) to 256-color code
    """
    return 16 + 36 * r + 6 * g + b


def color_from_file(file):  # pylint: disable=too-many-locals
    """
    Map file age (mtime) to 256 color terminal palette
    """
    if file.stat is None:
        return rgb_to_term_palette(1, 0, 0)

    now = time.time()
    age = now - file.stat.st_mtime

    # Find which segment we're in
    for i, threshold in enumerate(_thresholds):
        if age <= threshold:
            segment = i
            break
    else:
        segment = len(_thresholds)  # Beyond 50 years

    # Calculate interpolation factor within segment
    prev_thresh = _thresholds[segment - 1] if segment > 0 else 0
    next_thresh = _thresholds[segment] if segment < len(_thresholds) else None

    # Files older than 50 years
    if next_thresh is None:
        return rgb_to_term_palette(*_colors[segment])

    factor = (age - prev_thresh) / (next_thresh - prev_thresh)
    factor = max(0, min(1, factor))  # Clamp to 0-1

    # Interpolate between color corners
    r1, g1, b1 = _colors[segment]
    r2, g2, b2 = _colors[segment + 1]
    r = int(r1 + factor * (r2 - r1))
    g = int(g1 + factor * (g2 - g1))
    b = int(b1 + factor * (b2 - b1))

    return rgb_to_term_palette(r, g, b)
