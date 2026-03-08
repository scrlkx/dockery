from collections.abc import Callable
from typing import Any, cast

from gi.repository import GLib, Gtk, Vte


class TerminalWindow(Gtk.Window):
    __gtype_name__ = "TerminalWindow"

    def __init__(
        self,
        title: str,
        command: list[str],
        transient_for: Gtk.Window | None = None,
        on_close: Callable[[], None] | None = None,
    ):
        super().__init__()

        self._on_close = on_close

        self.set_title(title)
        self.set_default_size(800, 600)

        if transient_for is not None:
            self.set_transient_for(transient_for)

        self.terminal = Vte.Terminal()
        self.terminal.set_vexpand(True)
        self.terminal.set_hexpand(True)

        self.set_child(self.terminal)

        self.connect("close-request", self.on_close_request)
        self.terminal.connect("child-exited", self.on_child_exited)
        self.terminal.spawn_async(
            Vte.PtyFlags.DEFAULT,
            None,
            command,
            None,
            GLib.SpawnFlags.SEARCH_PATH,
            None,
            cast(int, None),
            cast(Any, -1),
            None,
            None,
        )

    def on_close_request(self, _window: Gtk.Window) -> bool:
        if self._on_close is not None:
            self._on_close()

        return False

    def on_child_exited(self, _terminal: Vte.Terminal, _status: int) -> None:
        self.close()

    def present(self) -> None:
        self.terminal.grab_focus()
        super().present()
