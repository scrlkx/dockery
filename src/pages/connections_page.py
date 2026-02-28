import threading
from typing import Any

from gi.repository import Adw, GLib, GObject, Gtk

from ..components.confirmation_dialog import ConfirmationDialog
from ..components.row_action import RowAction
from ..components.row_next import RowNext
from ..dialogs.connection_dialog import ConnectionDialog
from ..utils.connection_profile import ConnectionProfile, get_profile_display_name
from ..utils.connections import (
    add_connection,
    get_connections,
    remove_connection,
    update_connection,
)
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

        add_button = Gtk.Button(label=_("Add connection"))
        add_button.add_css_class("suggested-action")
        add_button.add_css_class("pill")
        add_button.set_halign(Gtk.Align.CENTER)
        add_button.connect("clicked", self.on_add_connection_clicked)

        self.content_box.append(add_button)

        connections = get_connections()

        if connections:
            saved_group = Adw.PreferencesGroup()
            saved_group.set_title(_("Saved connections"))

            self.content_box.append(saved_group)

            for index, profile in enumerate(connections):
                name = profile.get("name", "")
                display_name = get_profile_display_name(profile)

                row = Adw.ActionRow()
                row.set_title(name or display_name)
                row.set_subtitle(
                    display_name if name else profile.get("kind", "unix").upper()
                )
                row.set_activatable(True)
                row.connect("activated", self.on_connection_clicked, profile)

                delete_button = RowAction(
                    icon_name="user-trash-symbolic",
                    callback=lambda i=index, p=profile: self.on_delete_connection_clicked(
                        i, p
                    ),
                )

                edit_button = RowAction(
                    icon_name="document-edit-symbolic",
                    callback=lambda i=index, p=profile: self.on_edit_connection_clicked(
                        i, p
                    ),
                )

                row.add_suffix(delete_button)
                row.add_suffix(edit_button)
                row.add_suffix(RowNext())

                saved_group.add(row)

    def on_connection_clicked(
        self, _row: Adw.ActionRow, profile: ConnectionProfile
    ) -> None:
        self.try_connect(profile)

    def on_add_connection_clicked(self, _button: Gtk.Button) -> None:
        dialog = ConnectionDialog()
        dialog.connect("connect-requested", self.on_connect_requested)

        root = self.get_root()
        dialog.present(root if isinstance(root, Gtk.Widget) else None)

    def on_edit_connection_clicked(
        self, index: int, profile: ConnectionProfile
    ) -> None:
        dialog = ConnectionDialog(profile=profile)
        dialog.connect("connect-requested", self.on_edit_saved, index)

        root = self.get_root()
        dialog.present(root if isinstance(root, Gtk.Widget) else None)

    def on_delete_connection_clicked(
        self,
        index: int,
        _profile: ConnectionProfile,
    ) -> None:
        dialog = ConfirmationDialog(
            heading=_("Remove saved connection?"),
            body=_("Are you sure you want to remove this connection?"),
            action_label=_("Remove"),
        )

        dialog.connect(
            "response",
            self.on_delete_connection_response,
            index,
        )

        root = self.get_root()

        if isinstance(root, Gtk.Window):
            dialog.set_transient_for(root)

        dialog.present()

    def on_delete_connection_response(
        self,
        dialog: Adw.MessageDialog,
        response: str,
        index: int,
    ) -> None:
        dialog.close()

        if response != "continue":
            return

        remove_connection(index)
        self.build_ui()

    def on_edit_saved(
        self, _dialog: ConnectionDialog, profile: ConnectionProfile, index: int
    ) -> None:
        update_connection(index, profile)
        self.build_ui()

    def on_connect_requested(
        self, _dialog: ConnectionDialog, profile: ConnectionProfile
    ) -> None:
        self.try_connect(profile)

    def try_connect(self, profile: ConnectionProfile) -> None:
        self.set_sensitive(False)
        self.status_page.set_description(_("Connecting..."))

        def task() -> None:
            try:
                connect(profile)
                GLib.idle_add(self.on_connect_success, profile)
            except Exception as exception:
                GLib.idle_add(self.on_connect_error, str(exception))

        threading.Thread(target=task, daemon=True).start()

    def on_connect_success(self, profile: ConnectionProfile) -> None:
        add_connection(profile)

        self.set_sensitive(True)
        self.status_page.set_description(self.PROJECT_SLOGAN)
        self.emit("connected", get_profile_display_name(profile))

    def on_connect_error(self, message: str) -> None:
        self.set_sensitive(True)
        self.status_page.set_description(self.PROJECT_SLOGAN)

        show_error_dialog(message)

    def refresh(self) -> None:
        self.build_ui()
