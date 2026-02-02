from typing import Any

from gi.repository import Gtk

from ..utils.i18n import _


class HelpOverlay(Gtk.ShortcutsWindow):
    __gtype_name__ = "HelpOverlay"

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)

        self.set_modal(True)

        section = Gtk.ShortcutsSection(title=_("General"))
        self.set_child(section)

        group = Gtk.ShortcutsGroup(title=_("Application"))
        section.append(group)

        quit_shortcut = Gtk.ShortcutsShortcut(title=_("Quit"), accelerator="<Ctrl>q")
        group.append(quit_shortcut)

        shortcuts_shortcut = Gtk.ShortcutsShortcut(
            title=_("Keyboard Shortcuts"), accelerator="<Ctrl>question"
        )

        group.append(shortcuts_shortcut)
