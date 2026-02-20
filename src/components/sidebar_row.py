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

        box = Gtk.Box(
            spacing=12,
            margin_top=10,
            margin_bottom=10,
            margin_start=12,
            margin_end=12,
        )

        box.append(Gtk.Image.new_from_icon_name(icon_name))

        box.append(Gtk.Label(label=title))

        self.set_child(box)
