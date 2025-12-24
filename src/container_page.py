from collections.abc import Callable

from docker.models.containers import Container
from gi.repository import Adw, Gtk

from .events import on_container_change
from .utils.docker import (
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
from .utils.ui import (
    get_container_action_icon,
    get_container_action_label,
    get_container_status_label,
    humanize_mount_mode,
    iso_to_local,
)


@Gtk.Template(resource_path="/com/scrlkx/dockery/container_page.ui")
class ContainerPage(Adw.NavigationPage):
    __gtype_name__ = "ContainerPage"

    name_label = Gtk.Template.Child()
    details_group = Gtk.Template.Child()
    quick_actions_group = Gtk.Template.Child()
    environment_group = Gtk.Template.Child()
    volumes_group = Gtk.Template.Child()
    networks_group = Gtk.Template.Child()
    ports_group = Gtk.Template.Child()

    detail_rows: list[Adw.ActionRow] = []
    quick_action_rows: list[Gtk.Button] = []
    environment_rows: list[Adw.ActionRow] = []
    volumes_rows: list[Adw.ActionRow] = []
    networks_rows: list[Adw.ActionRow] = []
    ports_rows: list[Adw.ActionRow] = []

    container: Container

    def __init__(self, container: Container):
        super().__init__()

        self.container = get_container(container.name)

        self.register_events()
        self.build_ui()

    def register_events(self) -> None:
        on_container_change(self.reload_ui, self.container)

    def build_ui(self) -> None:
        self.load_details()
        self.load_quick_actions()
        self.load_environment_variables()
        self.load_volumes()
        self.load_networks()
        self.load_ports()

    def reload_ui(self) -> None:
        self.container = get_container(self.container.name)
        self.build_ui()

    def load_details(self) -> None:
        self.detail_rows = []

        self.set_title(self.container.name)
        self.name_label.set_text(self.container.name)

        details = {
            "ID": self.container.id,
            "Name": self.container.name,
            "Image": get_container_image(self.container) or "-",
            "Status": get_container_status_label(self.container) or "-",
            "Created at": iso_to_local(get_container_created_at(self.container)),
        }

        started_at = get_container_started_at(self.container)

        if started_at:
            details["Started at"] = iso_to_local(started_at)

        cmd = get_container_cmd(self.container)

        if cmd:
            details["CMD"] = cmd

        entrypoint = get_container_entrypoint(self.container)

        if entrypoint:
            details["Entrypoint"] = entrypoint

        details["Restart Policy"] = get_container_restart_policy(self.container)

        for row in self.detail_rows:
            self.details_group.remove(row)

        self.detail_rows.clear()

        for key, value in details.items():
            label = Gtk.Label(label=value)
            label.set_valign(Gtk.Align.CENTER)

            row = Adw.ActionRow()
            row.set_title(key)
            row.add_suffix(label)

            self.details_group.add(row)
            self.detail_rows.append(row)

    def load_quick_actions(self) -> None:
        self.quick_action_rows = []

        callbacks = {
            "start": self.on_start_clicked,
            "stop": self.on_stop_clicked,
            "pause": self.on_pause_clicked,
            "resume": self.on_resume_clicked,
            "restart": self.on_restart_clicked,
            "kill": self.on_kill_clicked,
            "remove": self.on_remove_clicked,
        }

        for row in self.quick_action_rows:
            self.quick_actions_group.remove(row)

        self.quick_action_rows.clear()

        actions = get_container_actions(self.container)

        for action in actions:
            label = get_container_action_label(action)
            icon = get_container_action_icon(action)
            callback = callbacks.get(action)

            if label and icon and callback:
                button = self.build_quick_action_button(
                    label,
                    icon,
                    callback,
                )

                self.quick_actions_group.append(button)
                self.quick_action_rows.append(button)

    def load_environment_variables(self) -> None:
        self.environment_rows = []

        variables = get_container_environment_variables(self.container)

        for row in self.environment_rows:
            self.environment_group.remove(row)

        self.environment_rows.clear()

        for key, value in variables.items():
            label = Gtk.Label(label=value)
            label.set_valign(Gtk.Align.CENTER)

            row = Adw.ActionRow()
            row.set_title(key)
            row.add_suffix(label)

            self.environment_group.add(row)
            self.environment_rows.append(row)

    def load_volumes(self) -> None:
        self.volumes_rows = []

        volumes = get_container_volumes(self.container)

        for row in self.volumes_rows:
            self.volumes_group.remove(row)

        self.volumes_rows.clear()

        for key, value in volumes.items():
            label = Gtk.Label(label=humanize_mount_mode(value))
            label.set_valign(Gtk.Align.CENTER)

            row = Adw.ActionRow()
            row.set_title(key)
            row.add_suffix(label)

            self.volumes_group.add(row)
            self.volumes_rows.append(row)

    def load_networks(self) -> None:
        self.networks_rows = []

        networks = get_container_networks(self.container)

        for row in self.networks_rows:
            self.networks_group.remove(row)

        self.networks_rows.clear()

        for key, value in networks.items():
            label = Gtk.Label(label=value)
            label.set_valign(Gtk.Align.CENTER)

            row = Adw.ActionRow()
            row.set_title(key)
            row.add_suffix(label)

            self.networks_group.add(row)
            self.networks_rows.append(row)

    def load_ports(self) -> None:
        self.ports_rows = []

        ports = get_container_ports(self.container)

        for row in self.ports_rows:
            self.ports_group.remove(row)

        self.ports_rows.clear()

        for key, value in ports.items():
            label = Gtk.Label(label=value)
            label.set_valign(Gtk.Align.CENTER)

            row = Adw.ActionRow()
            row.set_title(key)
            row.add_suffix(label)

            self.ports_group.add(row)
            self.ports_rows.append(row)

    def build_quick_action_button(
        self, label_text: str, icon_name: str, callback: Callable[[Gtk.Button], None]
    ) -> Gtk.Button:
        box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=6,
            halign=Gtk.Align.CENTER,
            valign=Gtk.Align.CENTER,
        )

        image = Gtk.Image.new_from_resource(f"/com/scrlkx/dockery/icons/{icon_name}")
        box.append(image)

        label = Gtk.Label(label=label_text)
        box.append(label)

        button = Gtk.Button(hexpand=True)
        button.set_child(box)
        button.connect("clicked", callback)

        return button

    def on_start_clicked(self, _: Gtk.Button) -> None:
        start_container(self.container.name)
        self.reload_ui()

    def on_pause_clicked(self, _: Gtk.Button) -> None:
        pause_container(self.container.name)
        self.reload_ui()

    def on_resume_clicked(self, _: Gtk.Button) -> None:
        unpause_container(self.container.name)
        self.reload_ui()

    def on_stop_clicked(self, _: Gtk.Button) -> None:
        stop_container(self.container.name)
        self.reload_ui()

    def on_restart_clicked(self, _: Gtk.Button) -> None:
        restart_container(self.container.name)
        self.reload_ui()

    def on_kill_clicked(self, _: Gtk.Button) -> None:
        kill_container(self.container.name)
        self.reload_ui()

    def on_remove_clicked(self, _: Gtk.Button) -> None:
        remove_container(self.container.name)
        self.reload_ui()
