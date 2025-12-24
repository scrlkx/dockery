from gi.repository import Adw, Gtk

from .events import on_container_chage
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

    detail_rows: list[Adw.ActionRow]
    quick_action_rows: list[Adw.ActionRow]
    environment_rows: list[Adw.ActionRow]
    volumes_rows: list[Adw.ActionRow]
    networks_rows: list[Adw.ActionRow]
    ports_rows: list[Adw.ActionRow]

    def __init__(self, container):
        super().__init__()

        self.detail_rows = []
        self.quick_action_rows = []
        self.environment_rows = []
        self.volumes_rows = []
        self.networks_rows = []
        self.ports_rows = []

        self.container = get_container(container.name)

        on_container_chage(self._load, self.container.id)

        self._load()

    def _load(self):
        self._load_details()
        self._load_quick_actions()
        self._load_environment_variables()
        self._load_volumes()
        self._load_networks()
        self._load_ports()

    def _load_details(self):
        if self.container:
            self.container = get_container(self.container.name)

        self.set_title(self.container.name)
        self.name_label.set_text(self.container.name)

        created_at = get_container_created_at(self.container)

        if created_at:
            created_at = iso_to_local(created_at)

        started_at = get_container_started_at(self.container)

        if started_at:
            started_at = iso_to_local(started_at)

        details = {
            "ID": self.container.id,
            "Name": self.container.name,
            "Image": get_container_image(self.container),
            "Status": get_container_status_label(self.container),
            "Created at": created_at,
            "Started at": started_at,
            "CMD": get_container_cmd(self.container),
            "Entrypoint": get_container_entrypoint(self.container),
            "Restart Policy": get_container_restart_policy(self.container),
        }

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

    def _load_quick_actions(self):
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
            button = self._create_quick_action_button(
                get_container_action_label(action),
                get_container_action_icon(action),
                callbacks.get(action),
            )

            self.quick_actions_group.append(button)
            self.quick_action_rows.append(button)

    def _load_environment_variables(self):
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

    def _load_volumes(self):
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

    def _load_networks(self):
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

    def _load_ports(self):
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

    def _create_quick_action_button(self, label_text, icon_name, callback):
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

    def on_start_clicked(self, _):
        start_container(self.container.name)

        self._load_details()
        self._load_quick_actions()

    def on_pause_clicked(self, _):
        pause_container(self.container.name)

        self._load_details()
        self._load_quick_actions()

    def on_resume_clicked(self, _):
        unpause_container(self.container.name)

        self._load_details()
        self._load_quick_actions()

    def on_stop_clicked(self, _):
        stop_container(self.container.name)

        self._load_details()
        self._load_quick_actions()

    def on_restart_clicked(self, _):
        restart_container(self.container.name)

        self._load_details()
        self._load_quick_actions()

    def on_kill_clicked(self, _):
        kill_container(self.container.name)

        self._load_details()
        self._load_quick_actions()

    def on_remove_clicked(self, _):
        remove_container(self.container.name)

        self._load_details()
        self._load_quick_actions()
