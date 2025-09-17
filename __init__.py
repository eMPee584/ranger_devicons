"""Ranger plugin expanding any linemode with devicons."""

import os
import ranger.api
from ranger.core.shared import FileManagerAware
from ranger.container.settings import (
    ALLOWED_SETTINGS, SIGNAL_PRIORITY_SANITIZE,
    SIGNAL_PRIORITY_SYNC, SIGNAL_PRIORITY_AFTER_SYNC)
from .colors import *
from .devicons import *

ALLOWED_SETTINGS['devicons_color'] = bool
USE_COLOR = True
SEPARATOR = os.getenv('RANGER_DEVICONS_SEPARATOR', ' ')

HOOK_INIT_OLD = ranger.api.hook_init
HOOK_FILETITLE = {}


# pylint: disable=global-statement
def check_use_color():
    """
    callback handler to check whether color mode can and should be active and
    reset display when it changes
    """
    global USE_COLOR
    fm = FileManagerAware.fm

    prev_val = USE_COLOR
    USE_COLOR = use_color()

    if prev_val != USE_COLOR:
        fm.garbage_collect(-1)
        fm.reload_cwd()


# pylint: disable=invalid-name,protected-access,fixme
def hook_init(fm):
    """
    Hook into ranger startup so browser column has been set up.
    """

    check_use_color()
    fm.execute_console("map zC toggle_option devicons_color")
    fm.settings.signal_bind("setopt.devicons_color",
                            fm.settings._sanitize,
                            priority=SIGNAL_PRIORITY_SANITIZE)
    fm.settings.signal_bind("setopt.devicons_color",
                            fm.settings._raw_set_with_signal,
                            priority=SIGNAL_PRIORITY_SYNC)
    fm.settings.signal_bind("setopt.devicons_color",
                            check_use_color,
                            priority=SIGNAL_PRIORITY_AFTER_SYNC)

    # FIXME: workaround required because we can't set these signal handlers
    # before the settings files are read.. needs ranger.api.hook_loading
    fm.source("/etc/ranger/rc.conf")

    HOOK_DRAW_DIR = \
        ranger.gui.widgets.browsercolumn.BrowserColumn._draw_directory

    def _draw_directory_override(self):
        if self.target.files is not None and len(self.target.files) > 0:
            fobj = self.target.files[0]
            current_linemode = fobj.linemode_dict[fobj.linemode]
            if id(current_linemode.filetitle) != id(filetitle_override):
                # Store pointer to active linemode's filetitle() function
                HOOK_FILETITLE[fobj.linemode] = current_linemode.filetitle
                # and hook in our override function instead.
                current_linemode.filetitle = filetitle_override
        HOOK_DRAW_DIR(self)

    ranger.gui.widgets.browsercolumn.BrowserColumn._draw_directory = \
        _draw_directory_override

    def filetitle_override(file, metadata):
        """Return the file's title with the appropriate devicon."""
        icon = devicon(file)
        filetitle = HOOK_FILETITLE[file.linemode](file, metadata)

        if not USE_COLOR:
            return icon + SEPARATOR + filetitle

        color = str(color_from_file(file))
        return '\x1b[38;5;' + color + 'm' + icon + '\x1b[0m' \
            + SEPARATOR + filetitle

    return HOOK_INIT_OLD(fm)


ranger.api.hook_init = hook_init
