from typing import List

import docker
from gi.repository import Adw, GObject, Gtk


class ContainerItem(GObject.Object):
    name = GObject.Property(type=str)
    status = GObject.Property(type=str)


@Gtk.Template(resource_path="/com/scrlkx/dockery/containers_page.ui")
class ContainersPage(Adw.NavigationPage):
    __gtype_name__ = "ContainersPage"

    __gsignals__ = {
        "container-activated": (GObject.SignalFlags.RUN_FIRST, None, (object,))
    }

    _rows: List[Adw.ActionRow] = []

    search_entry = Gtk.Template.Child()
    containers_group = Gtk.Template.Child()

    CONTAINER_STATUS_ORDER = {
        "running": 0,
        "paused": 1,
        "restarting": 2,
        "created": 3,
        "exited": 4,
        "dead": 5,
    }

    CONTAINER_STATUS_LABEL = {
        "running": "Running",
        "paused": "Paused",
        "restarting": "Restarting",
        "created": "Created",
        "exited": "Exited",
        "dead": "Dead",
    }

    CONTAINER_STATUS_STYLE = {
        "running": "tag-green",
        "paused": "tag-blue",
        "restarting": "tag-red",
        "created": "tag-gray",
        "exited": "tag-orange",
        "dead": "tag-black",
    }

    CONTAINER_STATUS_ACTIONS = {
        "running": "stop",
        "paused": "start",
        "restarting": "stop",
        "created": "start",
        "exited": "start",
        "dead": None,
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._rows = []

        self.search_entry.connect("search-changed", self._on_search_changed)

        self._load_containers()

    def _on_search_changed(self, entry):
        text = entry.get_text().lower()

        for row in self._rows:
            visible = text in row.container_name
            row.set_visible(visible)

    def _get_container_list(self):
        client = docker.from_env()

        containers = client.containers.list(all=True)
        containers.sort(
            key=lambda item: self.CONTAINER_STATUS_ORDER.get(item.status, 99)
        )

        return containers

    def _start_container(self, _, container):
        client = docker.from_env()

        container = client.containers.get(container.name)
        container.start()

        self._reload_list()

    def _stop_container(self, _, container):
        client = docker.from_env()

        container = client.containers.get(container.name)
        container.stop()

        self._reload_list()

    def _on_row_activated(self, _, container):
        self.emit("container-activated", container)

    def _action_button(self, icon_name, callback, container):
        button = Gtk.Button()
        button.add_css_class("flat")
        button.set_valign(Gtk.Align.CENTER)
        button.set_margin_end(12)

        image = Gtk.Image.new_from_resource(f"/com/scrlkx/dockery/icons/{icon_name}")

        box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=6,
            halign=Gtk.Align.CENTER,
            valign=Gtk.Align.CENTER,
        )

        box.append(image)

        button.set_child(box)

        button.connect("clicked", callback, container)

        return button

    def _load_containers(self):
        containers = self._get_container_list()

        for container in containers:
            row = Adw.ActionRow(title=container.name)
            row.container_name = container.name.lower()
            row.container_image = (
                container.image.tags[0] if len(container.image.tags) > 0 else ""
            )

            row.set_activatable(True)
            row.connect("activated", self._on_row_activated, container)

            self._rows.append(row)

            if row.container_image:
                image = Gtk.Label(label=row.container_image)
                image.set_valign(Gtk.Align.CENTER)
                image.add_css_class("tag")
                image.add_css_class("caption")
                image.set_margin_end(12)

                row.add_suffix(image)

            status = Gtk.Label(label=self.CONTAINER_STATUS_LABEL[container.status])
            status.set_valign(Gtk.Align.CENTER)
            status.add_css_class("tag")
            status.add_css_class("caption")
            status.add_css_class(self.CONTAINER_STATUS_STYLE[container.status])
            status.set_margin_end(12)

            row.add_suffix(status)

            action = self.CONTAINER_STATUS_ACTIONS[container.status]

            if action == "start":
                button = self._action_button(
                    "play.svg",
                    self._start_container,
                    container,
                )

                row.add_suffix(button)
            elif action == "stop":
                button = self._action_button(
                    "circle-crossed.svg",
                    self._stop_container,
                    container,
                )

                row.add_suffix(button)

            info = Gtk.Image.new_from_icon_name("go-next-symbolic")
            info.add_css_class("flat")

            row.add_suffix(info)

            self.containers_group.add(row)

    def _reload_list(self):
        for row in self._rows:
            self.containers_group.remove(row)

        self._rows.clear()
        self._load_containers()
