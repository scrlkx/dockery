from collections.abc import Callable
from typing import Any

from gi.repository import Gtk


class RowAction(Gtk.Button):
    def __init__(
        self,
        icon_name: str,
        callback: Callable[[], None] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)

        self._callback = callback

        self.set_icon_name(icon_name)
        self.add_css_class("flat")
        self.set_valign(Gtk.Align.CENTER)

        if self._callback:
            self.connect("clicked", self._on_clicked)

    def _on_clicked(self, _button: Gtk.Button) -> None:
        if self._callback:
            self._callback()
