"""Ranger plugin expanding any linemode with devicons."""

import os
import ranger.api
from .devicons import *

SEPARATOR = os.getenv('RANGER_DEVICONS_SEPARATOR', ' ')

HOOK_INIT_OLD = ranger.api.hook_init
HOOK_FILETITLE = {}


# pylint: disable=invalid-name,protected-access
def hook_init(fm):
    """
    Hook into ranger startup so browser column has been set up.
    """

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
        return devicon(file) + SEPARATOR + HOOK_FILETITLE[file.linemode](file, metadata)

    return HOOK_INIT_OLD(fm)


ranger.api.hook_init = hook_init
