import threading
from typing import Any

from gi.repository import Adw, GLib, GObject, Gtk

from ..components.row_next import RowNext
from ..dialogs.connection_dialog import ConnectionDialog
from ..utils.connections import add_connection, get_connections
from ..utils.docker import connect
from ..utils.i18n import _
from ..utils.ui import show_error_dialog


@Gtk.Template(resource_path="/com/scrlkx/dockery/pages/connections_page.ui")
class ConnectionsPage(Gtk.Box):
    __gtype_name__ = "ConnectionsPage"
    PROJECT_SLOGAN = _("Adwaita-based Docker management UI")

    __gsignals__ = {"connected": (GObject.SignalFlags.RUN_FIRST, None, (str,))}

    header_bar = Gtk.Template.Child()
    status_page = Gtk.Template.Child()
    content_box = Gtk.Template.Child()

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        self.build_ui()

    def build_ui(self) -> None:
        while child := self.content_box.get_first_child():
            self.content_box.remove(child)

        add_button = Gtk.Button(label=_("Add Connection"))
        add_button.add_css_class("suggested-action")
        add_button.add_css_class("pill")
        add_button.set_halign(Gtk.Align.CENTER)
        add_button.connect("clicked", self.on_add_connection_clicked)
        self.content_box.append(add_button)

        connections = get_connections()

        if connections:
            saved_group = Adw.PreferencesGroup()
            saved_group.set_title(_("Saved Connections"))
            self.content_box.append(saved_group)

            for uri in connections:
                row = Adw.ActionRow()
                row.set_title(uri)
                row.set_activatable(True)
                row.add_suffix(RowNext())
                row.connect("activated", self.on_connection_clicked, uri)

                saved_group.add(row)

    def on_connection_clicked(self, _row: Adw.ActionRow, uri: str) -> None:
        self.try_connect(uri)

    def on_add_connection_clicked(self, _button: Gtk.Button) -> None:
        dialog = ConnectionDialog()
        dialog.connect("connect-requested", self.on_connect_requested)
        root = self.get_root()
        dialog.present(root if isinstance(root, Gtk.Widget) else None)

    def on_connect_requested(self, _dialog: ConnectionDialog, uri: str) -> None:
        self.try_connect(uri)

    def try_connect(self, uri: str) -> None:
        self.set_sensitive(False)
        self.status_page.set_description(_("Connecting…"))

        def task() -> None:
            try:
                connect(uri)
                GLib.idle_add(self.on_connect_success, uri)
            except Exception as exception:
                GLib.idle_add(self.on_connect_error, str(exception))

        threading.Thread(target=task, daemon=True).start()

    def on_connect_success(self, uri: str) -> None:
        add_connection(uri)

        self.set_sensitive(True)
        self.status_page.set_description(self.PROJECT_SLOGAN)
        self.emit("connected", uri)

    def on_connect_error(self, message: str) -> None:
        self.set_sensitive(True)
        self.status_page.set_description(self.PROJECT_SLOGAN)

        show_error_dialog(message)

    def refresh(self) -> None:
        self.build_ui()
