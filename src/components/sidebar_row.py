from typing import Any, Callable

from gi.repository import Gtk


class SidebarRow(Gtk.ListBoxRow):
    __gtype_name__ = "SidebarRow"

    def __init__(self, title: str, icon_name: str, **kwargs: Any):
        super().__init__(**kwargs)

        self.title = title
        self.page_class: Any = None
        self.signal: str | None = None
        self.callback: Callable[..., Any] | None = None

        box = Gtk.Box()
        box.set_spacing(12)
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        box.set_margin_start(12)
        box.set_margin_end(12)

        icon = Gtk.Image()
        icon.set_from_icon_name(icon_name)
        box.append(icon)

        label = Gtk.Label()
        label.set_label(title)
        box.append(label)

        self.set_child(box)
