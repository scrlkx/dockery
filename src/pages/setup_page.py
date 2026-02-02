import threading
import traceback
from typing import Any

from gi.repository import Adw, GLib, GObject, Gtk

from ..dialogs.connection_dialog import ConnectionDialog
from ..utils.docker import init_client, get_system_info
from ..utils import settings
from ..utils.i18n import _


@Gtk.Template(resource_path="/com/scrlkx/dockery/pages/setup_page.ui")
class SetupPage(Gtk.Box):
    __gtype_name__ = "SetupPage"

    __gsignals__ = {
        "recheck-connections": (GObject.SignalFlags.RUN_FIRST, None, ()),
        "connection-successful": (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    new_connection_button = Gtk.Template.Child()
    stack = Gtk.Template.Child()

    connections_group: Adw.PreferencesGroup
    connection_rows: list[Gtk.Widget]

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        self.connection_rows = []

        self.build_ui()

        # self.set_orientation(Gtk.Orientation.VERTICAL)
        #

        # self.connections_group = Adw.PreferencesGroup(title=_("Configured Connections"))
        # self.append(self.connections_group)
        # self.refresh_connections()

    def build_ui(self) -> None:
        status_page = Adw.StatusPage()
        status_page.set_icon_name("network-server-symbolic")
        status_page.set_title(_("Setup Connection"))
        status_page.set_description(_("Configure how to connect to the Docker"))
        status_page.set_vexpand(True)

        self.stack.append(status_page)

        connections = settings.get_connections()

        if len(connections) > 0:
            self.connections_group = Adw.PreferencesGroup()

            self.load_connections(connections)

            self.stack.append(self.connections_group)

        new_connection_button = Gtk.Button()
        new_connection_button.set_label(_("New Connection"))
        new_connection_button.set_halign(3)
        new_connection_button.set_vexpand(False)
        new_connection_button.add_css_class("suggested-action")
        new_connection_button.add_css_class("pill")
        new_connection_button.connect("clicked", self.on_new_connection_clicked)

        self.stack.append(new_connection_button)

    def load_connections(self, connections: list[tuple[str, str]]) -> None:
        for name, uri in connections:
            row = Adw.ActionRow(title=name, subtitle=uri)
            row.set_activatable(True)
            row.connect("activated", self.on_connection_row_activated, uri)

            edit_button = Gtk.Button.new_from_icon_name("document-edit-symbolic")
            edit_button.set_valign(Gtk.Align.CENTER)
            edit_button.add_css_class("flat")
            edit_button.set_tooltip_text(_("Edit Connection"))
            edit_button.connect("clicked", self.on_edit_connection_clicked, name, uri)
            row.add_suffix(edit_button)

            icon = Gtk.Image.new_from_icon_name("go-next-symbolic")
            row.add_suffix(icon)

            self.connections_group.add(row)
            self.connection_rows.append(row)

    def refresh_connections(self) -> None:
        # Clear existing rows
        for row in self.connection_rows:
            self.connections_group.remove(row)

        self.connection_rows.clear()

        connections = settings.get_connections()

        if len(connections) > 0:
            self.load_connections(connections)
        else:
            self.stack.remove(self.connections_group)

    def on_new_connection_clicked(self, _: Gtk.Button) -> None:
        dialog = ConnectionDialog()
        dialog.connect("connection-added", self.on_connection_added)

        if root := self.get_root():
            dialog.set_transient_for(root)  # type: ignore

        dialog.present()

    def on_connection_added(self, _: ConnectionDialog) -> None:
        self.emit("recheck-connections")

        self.refresh_connections()

    def on_edit_connection_clicked(self, _: Gtk.Button, name: str, uri: str) -> None:
        # This assumes the ConnectionDialog can be initialized with existing data
        # for editing.
        dialog = ConnectionDialog(name=name, uri=uri)
        dialog.connect("connection-added", self.on_connection_added)

        if root := self.get_root():
            dialog.set_transient_for(root)  # type: ignore

        dialog.present()

    def on_connection_row_activated(self, _: Adw.ActionRow, uri: str) -> None:
        self.set_sensitive(False)

        def task() -> None:
            try:
                init_client(uri)
                get_system_info()

                self.set_sensitive(True)

                GLib.idle_add(self.emit, "connection-successful")
            except Exception as exception:
                # Capture the full traceback for debugging
                tb_str = traceback.format_exc()
                print("--- CONNECTION FAILED ---")
                print(tb_str)
                print("-------------------------")

                # Format a more detailed error message for the dialog
                error_message = (
                    f"<b>{GLib.markup_escape_text(str(exception))}</b>\n\n"
                    "<small>Full error details have been printed to the console.</small>"
                )
                GLib.idle_add(self.on_connection_failed, error_message)

        threading.Thread(target=task).start()

    def on_connection_failed(self, error: str) -> None:
        self.set_sensitive(True)

        dialog = Adw.MessageDialog(
            heading=_("Connection Failed"),
            body=error,
            transient_for=self.get_root(),  # type: ignore
        )
        dialog.set_body_use_markup(True)

        dialog.add_response("ok", _("OK"))
        dialog.present()
