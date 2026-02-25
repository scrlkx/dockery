from typing import Any

from gi.repository import Adw, GObject, Gtk


@Gtk.Template(resource_path="/com/scrlkx/dockery/dialogs/connection_dialog.ui")
class ConnectionDialog(Adw.Dialog):
    __gtype_name__ = "ConnectionDialog"

    __gsignals__ = {
        "connect-requested": (GObject.SignalFlags.RUN_FIRST, None, (str,)),
    }

    add_button = Gtk.Template.Child()
    uri_entry = Gtk.Template.Child()

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        self.add_button.connect("clicked", self.on_add_clicked)
        self.uri_entry.connect("notify::text", self.on_uri_changed)

        self.add_button.set_sensitive(bool(self.uri_entry.get_text().strip()))
        self.uri_entry.grab_focus()

    def on_uri_changed(
        self,
        entry: Adw.EntryRow,
        _pspec: GObject.ParamSpec,
    ) -> None:
        self.add_button.set_sensitive(bool(entry.get_text().strip()))

    def on_add_clicked(self, _: Gtk.Button) -> None:
        uri = self.uri_entry.get_text().strip()

        if not uri:
            return

        self.emit("connect-requested", uri)
        self.force_close()
