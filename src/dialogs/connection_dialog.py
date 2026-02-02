import threading
from typing import Any, Optional

from gi.repository import Adw, GLib, GObject, Gtk

from ..utils import docker, settings
from ..utils.i18n import _


@Gtk.Template(resource_path="/com/scrlkx/dockery/dialogs/connection_dialog.ui")
class ConnectionDialog(Adw.Window):
    __gtype_name__ = "ConnectionDialog"

    __gsignals__ = {
        "connection-added": (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    add_button = Gtk.Template.Child()
    name_entry = Gtk.Template.Child()
    uri_entry = Gtk.Template.Child()

    original_name: Optional[str] = None
    original_uri: Optional[str] = None

    def __init__(
        self, name: Optional[str] = None, uri: Optional[str] = None, **kwargs: Any
    ) -> None:
        super().__init__(**kwargs)
        self.add_button.connect("clicked", self.on_add_clicked)

        self.original_name = name
        self.original_uri = uri

        if name:
            self.name_entry.set_text(name)
            self.add_button.set_label(_("Save"))
            self.set_title(_("Edit Connection"))

        if uri:
            self.uri_entry.set_text(uri)

    def on_add_clicked(self, _: Gtk.Button) -> None:
        name = self.name_entry.get_text()
        uri = self.uri_entry.get_text()

        if not name or not uri:
            return

        self.set_sensitive(False)

        def task() -> None:
            success = docker.validate_connection(uri)
            GLib.idle_add(self.on_validation_finished, success, name, uri)

        threading.Thread(target=task).start()

    def on_validation_finished(self, success: bool, name: str, uri: str) -> None:
        if success:
            if self.original_name and self.original_uri:
                settings.remove_connection(self.original_name, self.original_uri)

            settings.add_connection(name, uri)
            self.emit("connection-added")
            self.close()
        else:
            self.set_sensitive(True)
            dialog = Adw.MessageDialog(
                heading=_("Connection Failed"),
                body=_("Could not connect to Docker daemon at '{}'.").format(uri),
                transient_for=self,
            )
            dialog.add_response("ok", _("OK"))
            dialog.present()
