import threading
from typing import Any, Callable

from gi.repository import GLib, Gtk

from ..utils import ui


class RowButton(Gtk.Button):
    def __init__(
        self,
        icon_name: str,
        callback: Callable[[], None] | None = None,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)

        self.callback = callback

        self.add_css_class("flat")
        self.set_valign(Gtk.Align.CENTER)

        image = Gtk.Image.new_from_icon_name(icon_name)

        box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=6,
            halign=Gtk.Align.CENTER,
            valign=Gtk.Align.CENTER,
        )

        box.append(image)

        self.set_child(box)

        if self.callback:
            self.connect("clicked", self.on_clicked)

    def on_clicked(self, _: Gtk.Button) -> None:
        self.set_sensitive(False)

        def task() -> None:
            try:
                if self.callback:
                    self.callback()
            except Exception as exception:
                GLib.idle_add(ui.show_error_dialog, str(exception))
                GLib.idle_add(self.set_sensitive, True)

        threading.Thread(target=task, daemon=True).start()
