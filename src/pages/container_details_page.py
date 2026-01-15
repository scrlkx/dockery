import threading
from typing import cast

from docker.errors import NotFound
from docker.models.containers import Container
from gi.repository import Adw, GLib, Gtk

from ..components.confirmation_dialog import ConfirmationDialog
from ..components.key_value_row import KeyValueRow
from ..components.quick_action_button import QuickActionButton
from ..utils.docker import (
    get_container,
    get_container_actions,
    get_container_cmd,
    get_container_created_at,
    get_container_entrypoint,
    get_container_environment_variables,
    get_container_image,
    get_container_networks,
    get_container_ports,
    get_container_restart_policy,
    get_container_started_at,
    get_container_volumes,
    kill_container,
    pause_container,
    remove_container,
    restart_container,
    start_container,
    stop_container,
    unpause_container,
)
from ..utils.events import on_container_change
from ..utils.i18n import _
from ..utils.ui import (
    get_container_action_icon,
    get_container_action_label,
    get_container_status_label,
    humanize_mount_mode,
    iso_to_local,
)


@Gtk.Template(resource_path="/com/scrlkx/dockery/pages/container_details_page.ui")
class ContainerDetailsPage(Adw.NavigationPage):
    __gtype_name__ = "ContainerDetailsPage"

    name_label = Gtk.Template.Child()
    details_group = Gtk.Template.Child()
    quick_actions_group = Gtk.Template.Child()
    volumes_group = Gtk.Template.Child()
    networks_group = Gtk.Template.Child()
    ports_group = Gtk.Template.Child()
    environment_group = Gtk.Template.Child()

    detail_rows: list[Adw.ActionRow] = []
    quick_action_rows: list[Gtk.Button] = []
    volumes_rows: list[Adw.ActionRow] = []
    networks_rows: list[Adw.ActionRow] = []
    ports_rows: list[Adw.ActionRow] = []
    environment_rows: list[Adw.ActionRow] = []

    container: Container

    def __init__(self, container: Container):
        super().__init__()

        self.detail_rows = []
        self.quick_action_rows = []
        self.volumes_rows = []
        self.networks_rows = []
        self.ports_rows = []
        self.environment_rows = []

        self.container = container

        self.register_events()
        self.build_ui()

    def register_events(self) -> None:
        on_container_change(self.reload_ui, self.container)

    def build_ui(self) -> None:
        self.load_details()
        self.load_quick_actions()
        self.load_volumes()
        self.load_networks()
        self.load_ports()
        self.load_environment_variables()

    def reload_ui(self) -> None:
        try:
            self.container = get_container(self.container.name)
        except NotFound:
            if self.get_sensitive():
                self.navigate_back()

            return

        self.build_ui()

    def load_details(self) -> None:
        self.set_title(self.container.name)
        self.name_label.set_text(self.container.name)

        details = {
            _("ID"): self.container.id,
            _("Name"): self.container.name,
            _("Image"): get_container_image(self.container) or "-",
            _("Status"): get_container_status_label(self.container),
            _("Created at"): iso_to_local(get_container_created_at(self.container)),
        }

        started_at = get_container_started_at(self.container)

        if started_at:
            details[_("Started at")] = iso_to_local(started_at)

        cmd = get_container_cmd(self.container)

        if cmd:
            details[_("CMD")] = cmd

        entrypoint = get_container_entrypoint(self.container)

        if entrypoint:
            details[_("Entrypoint")] = entrypoint

        details[_("Restart Policy")] = get_container_restart_policy(self.container)

        for row in self.detail_rows:
            self.details_group.remove(row)

        self.detail_rows.clear()

        for key, value in details.items():
            row = KeyValueRow(key, value)

            self.details_group.add(row)
            self.detail_rows.append(row)

    def load_quick_actions(self) -> None:
        actions_callback = {
            "start": start_container,
            "stop": stop_container,
            "pause": pause_container,
            "resume": unpause_container,
            "restart": restart_container,
            "kill": kill_container,
        }

        for row in self.quick_action_rows:
            self.quick_actions_group.remove(row)

        self.quick_action_rows.clear()

        actions = get_container_actions(self.container)

        for action in actions:
            label = get_container_action_label(action)
            icon = get_container_action_icon(action)

            if not label or not icon:
                continue

            if action == "remove":
                button = QuickActionButton(
                    label=label,
                    icon_name=icon,
                    callback=self.on_remove_clicked,
                    threaded=False,
                )
            elif callback := actions_callback.get(action):
                button = QuickActionButton(
                    label=label,
                    icon_name=icon,
                    callback=lambda f=callback: f(self.container.name),
                    on_finish=self.reload_ui,
                )
            else:
                continue

            self.quick_actions_group.append(button)
            self.quick_action_rows.append(button)

    def load_volumes(self) -> None:
        volumes = get_container_volumes(self.container)

        for row in self.volumes_rows:
            self.volumes_group.remove(row)

        self.volumes_rows.clear()

        for key, value in volumes.items():
            row = KeyValueRow(key, humanize_mount_mode(value))

            self.volumes_group.add(row)
            self.volumes_rows.append(row)

    def load_networks(self) -> None:
        networks = get_container_networks(self.container)

        for row in self.networks_rows:
            self.networks_group.remove(row)

        self.networks_rows.clear()

        for key, value in networks.items():
            row = KeyValueRow(key, value)

            self.networks_group.add(row)
            self.networks_rows.append(row)

    def load_ports(self) -> None:
        ports = get_container_ports(self.container)

        for row in self.ports_rows:
            self.ports_group.remove(row)

        self.ports_rows.clear()

        for key, value in ports.items():
            row = KeyValueRow(key, value)

            self.ports_group.add(row)
            self.ports_rows.append(row)

    def load_environment_variables(self) -> None:
        variables = get_container_environment_variables(self.container)

        for row in self.environment_rows:
            self.environment_group.remove(row)

        self.environment_rows.clear()

        for key, value in variables.items():
            row = KeyValueRow(key, value)

            self.environment_group.add(row)
            self.environment_rows.append(row)

    def on_remove_clicked(self) -> None:
        dialog = ConfirmationDialog(
            heading=_("Remove Container?"),
            body=_("Are you sure you want to remove this container?"),
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
            remove_container(self.container.name)

            def finish() -> None:
                self.navigate_back()

            GLib.idle_add(finish)

        threading.Thread(target=task).start()

    def navigate_back(self) -> None:
        navigation_view = cast(
            Adw.NavigationView, self.get_ancestor(Adw.NavigationView)
        )

        if navigation_view:
            navigation_view.pop()
