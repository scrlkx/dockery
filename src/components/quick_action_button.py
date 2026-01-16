import threading
from collections.abc import Callable
from typing import Any

from gi.repository import Adw, GLib, Gtk

from ..utils import ui


class QuickActionButton(Gtk.Button):
    def __init__(
        self,
        label: str,
        icon_name: str,
        callback: Callable[[], None],
        on_finish: Callable[[], None] | None = None,
        threaded: bool = True,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)

        self.callback = callback
        self.on_finish = on_finish
        self.threaded = threaded

        self.set_hexpand(True)

        content = Adw.ButtonContent(
            icon_name=icon_name,
            label=label,
        )

        self.set_child(content)
        self.connect("clicked", self.on_clicked)

    def on_clicked(self, _: Gtk.Button) -> None:
        if not self.threaded:
            self.callback()
            return

        self.set_sensitive(False)

        def task() -> None:
            try:
                self.callback()
            except Exception as exception:
                GLib.idle_add(ui.show_error_dialog, str(exception))
            finally:
                if self.on_finish:
                    GLib.idle_add(self.on_finish)
                else:
                    GLib.idle_add(self.set_sensitive, True)

        threading.Thread(target=task).start()
