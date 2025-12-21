from typing import List

from gi.repository import Adw, GObject, Gtk

from .ui import Badge
from .utils import (
    get_container_actions,
    get_container_image,
    get_container_status_class,
    get_container_status_label,
    get_containers,
    start_container,
    stop_container,
)


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

    def _start_container(self, _, container):
        start_container(container.name)
        self._reload_list()

    def _stop_container(self, _, container):
        stop_container(container.name)
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
        containers = get_containers()

        for container in containers:
            row = Adw.ActionRow(title=container.name)
            row.container_name = container.name.lower()
            row.container_image = get_container_image(container)

            row.set_activatable(True)
            row.connect("activated", self._on_row_activated, container)

            self._rows.append(row)

            if row.container_image:
                image = Badge(
                    text=get_container_image(container),
                    margin_end=12,
                )

                row.add_suffix(image)

            status = Badge(
                text=get_container_status_label(container),
                style_class=get_container_status_class(container),
                margin_end=12,
            )

            row.add_suffix(status)

            action = get_container_actions(container)[0]

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

            info = Gtk.Image.new_from_resource(
                "/com/scrlkx/dockery/icons/chevron-right.svg"
            )

            info.add_css_class("flat")

            row.add_suffix(info)

            self.containers_group.add(row)

    def _reload_list(self):
        for row in self._rows:
            self.containers_group.remove(row)

        self._rows.clear()
        self._load_containers()
