from typing import Any, Callable

from gi.repository import GObject, Gtk


class SidebarRow(Gtk.ListBoxRow):
    __gtype_name__ = "SidebarRow"

    title = GObject.Property(type=str, default="")
    icon_name = GObject.Property(type=str, default="")

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)

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

        self.icon_image = Gtk.Image()
        box.append(self.icon_image)

        self.title_label = Gtk.Label()
        box.append(self.title_label)

        self.set_child(box)

        self.bind_property(
            "title",
            self.title_label,
            "label",
            GObject.BindingFlags.SYNC_CREATE,
        )

        self.bind_property(
            "icon_name",
            self.icon_image,
            "icon-name",
            GObject.BindingFlags.SYNC_CREATE,
        )
