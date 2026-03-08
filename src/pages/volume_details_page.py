import threading
from typing import cast

from docker.models.volumes import Volume
from gi.repository import Adw, GLib, GObject, Gtk

from ..components.confirmation_dialog import ConfirmationDialog
from ..components.key_value_row import KeyValueRow
from ..components.quick_action_button import QuickActionButton
from ..components.terminal_window import TerminalWindow
from ..utils.docker import (
    create_volume_inspect_container,
    get_container_console_command,
    get_volume,
    get_volume_created_at,
    get_volume_driver,
    get_volume_mount_path,
    get_volume_short_name,
    is_socket_connection,
    remove_container,
    remove_volume,
)
from ..utils.i18n import _
from ..utils.ui import iso_to_local, show_error_dialog


@Gtk.Template(resource_path="/com/scrlkx/dockery/pages/volume_details_page.ui")
class VolumeDetailsPage(Adw.NavigationPage):
    __gtype_name__ = "VolumeDetailsPage"

    name_label = Gtk.Template.Child()
    quick_actions_group = Gtk.Template.Child()
    details_group = Gtk.Template.Child()

    quick_action_rows: list[Gtk.Button] = []
    detail_rows: list[Adw.ActionRow] = []

    volume: Volume

    def __init__(self, volume: Volume):
        super().__init__()

        self.quick_action_rows = []
        self.detail_rows = []

        self.volume = get_volume(volume.name)

        self.build_ui()

    def build_ui(self) -> None:
        self.load_details()
        self.load_quick_actions()

    def reload_ui(self) -> None:
        self.volume = get_volume(self.volume.name)
        self.build_ui()

    def load_details(self) -> None:
        self.set_title(get_volume_short_name(self.volume))
        self.name_label.set_text(get_volume_short_name(self.volume))

        details = {
            _("Name"): self.volume.name,
            _("Driver"): get_volume_driver(self.volume),
            _("Mount path"): get_volume_mount_path(self.volume),
            _("Created at"): iso_to_local(get_volume_created_at(self.volume)),
        }

        for row in self.detail_rows:
            self.details_group.remove(row)

        self.detail_rows.clear()

        for key, value in details.items():
            row = KeyValueRow(key, value)

            self.details_group.add(row)
            self.detail_rows.append(row)

    def load_quick_actions(self) -> None:
        mount_path = get_volume_mount_path(self.volume)
        actions = [
            (
                "inspect-contents",
                _("Inspect contents"),
                "utilities-terminal-symbolic",
                self.on_inspect_contents_clicked,
                is_socket_connection(),
            ),
            (
                "copy-mount-path",
                _("Copy mount path"),
                "edit-copy-symbolic",
                self.on_copy_mount_path_clicked,
                bool(mount_path),
            ),
            (
                "remove",
                _("Remove"),
                "user-trash-symbolic",
                self.on_remove_clicked,
                True,
            ),
        ]

        for row in self.quick_action_rows:
            self.quick_actions_group.remove(row)

        self.quick_action_rows.clear()

        for _action, label, icon_name, callback, enabled in actions:
            button = QuickActionButton(
                label=label,
                icon_name=icon_name,
                callback=callback,
                threaded=False,
            )
            button.set_sensitive(enabled)

            self.quick_actions_group.append(button)
            self.quick_action_rows.append(button)

    def on_inspect_contents_clicked(self) -> None:
        self.set_sensitive(False)

        def task() -> None:
            try:
                container_id = create_volume_inspect_container(self.volume.name)
                GLib.idle_add(self.open_inspect_console, container_id)
            except Exception as exception:
                GLib.idle_add(show_error_dialog, str(exception))
                GLib.idle_add(self.set_sensitive, True)

        threading.Thread(target=task).start()

    def on_copy_mount_path_clicked(self) -> None:
        mount_path = get_volume_mount_path(self.volume)

        if not mount_path:
            return

        clipboard = self.get_display().get_clipboard()
        value = GObject.Value()
        value.init(str)
        value.set_string(mount_path)
        clipboard.set(value)

    def open_inspect_console(self, container_id: str) -> bool:
        self.set_sensitive(True)

        command = get_container_console_command(container_id, workdir="/volume")

        def cleanup() -> None:
            try:
                remove_container(container_id, force=True)
            except Exception:
                pass

        def on_close() -> None:
            threading.Thread(target=cleanup).start()

        window = TerminalWindow(
            title=get_volume_short_name(self.volume),
            command=command,
            transient_for=cast(Gtk.Window, self.get_root()),
            on_close=on_close,
        )

        window.present()

        return False

    def on_remove_clicked(self) -> None:
        dialog = ConfirmationDialog(
            heading=_("Remove volume?"),
            body=_("Are you sure you want to remove this volume?"),
            action_label=_("Remove"),
        )

        dialog.connect("response", self.on_remove_response)
        dialog.set_transient_for(cast(Gtk.Window, self.get_root()))
        dialog.present()

    def on_remove_response(self, dialog: Adw.MessageDialog, response: str) -> None:
        dialog.close()

        if response != "continue":
            return

        self.set_sensitive(False)

        def task() -> None:
            try:
                remove_volume(self.volume.name)
                GLib.idle_add(self.navigate_back)
            except Exception as exception:
                GLib.idle_add(show_error_dialog, str(exception))
                GLib.idle_add(self.set_sensitive, True)

        threading.Thread(target=task).start()

    def navigate_back(self) -> None:
        root = self.get_root()
        navigate_back = getattr(root, "navigate_back", None)

        if callable(navigate_back):
            navigate_back()
            return

        navigation_view = cast(
            Adw.NavigationView, self.get_ancestor(Adw.NavigationView)
        )

        if navigation_view:
            navigation_view.pop()
