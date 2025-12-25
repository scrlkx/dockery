from typing import Any, Callable, List

from docker.models.containers import Container
from gi.repository import Adw, GObject, Gtk

from ..components.badge import Badge
from ..utils.docker import (
    get_container_image,
    get_container_next_action,
    get_containers,
    start_container,
    stop_container,
)
from ..utils.events import on_containers_change
from ..utils.ui import (
    get_container_status_class,
    get_container_status_label,
)


class ContainerRow(Adw.ActionRow):
    __gtype_name__ = "ContainerRow"

    name = GObject.Property(type=str)
    image = GObject.Property(type=str)
    status_label = GObject.Property(type=str)
    status_class = GObject.Property(type=str)


@Gtk.Template(resource_path="/com/scrlkx/dockery/pages/containers_page.ui")
class ContainersPage(Adw.NavigationPage):
    __gtype_name__ = "ContainersPage"

    __gsignals__ = {
        "container-activated": (GObject.SignalFlags.RUN_FIRST, None, (object,))
    }

    search_entry = Gtk.Template.Child()
    containers_group = Gtk.Template.Child()

    container_rows: List[ContainerRow] = []

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        self.register_events()
        self.build_ui()

    def register_events(self) -> None:
        self.search_entry.connect("search-changed", self.on_search_changed)

        on_containers_change(self.reload_ui)

    def build_ui(self) -> None:
        containers = get_containers()

        for container in containers:
            row = ContainerRow(title=container.name)
            row.name = container.name.lower()
            row.image = get_container_image(container)
            row.status_label = get_container_status_label(container)
            row.status_class = get_container_status_class(container)

            row.set_activatable(True)
            row.connect("activated", self.on_container_row_clicked, container)

            self.container_rows.append(row)

            if row.image:
                image = Badge(
                    text=row.image,
                    margin_end=12,
                )

                row.add_suffix(image)

            if row.status_label and row.status_class:
                status = Badge(
                    text=row.status_label,
                    style_class=row.status_class,
                    margin_end=12,
                )

                row.add_suffix(status)

            next_action = get_container_next_action(container)

            if next_action == "start":
                button = self.build_next_action_button(
                    container,
                    self.row_start_container,
                    "play.svg",
                )

                row.add_suffix(button)
            elif next_action == "stop":
                button = self.build_next_action_button(
                    container,
                    self.row_stop_container,
                    "circle-crossed.svg",
                )

                row.add_suffix(button)

            info = Gtk.Image.new_from_resource(
                "/com/scrlkx/dockery/icons/chevron-right.svg"
            )
            info.add_css_class("flat")

            row.add_suffix(info)

            self.containers_group.add(row)

    def reload_ui(self) -> None:
        for row in self.container_rows:
            self.containers_group.remove(row)

        self.container_rows.clear()
        self.build_ui()

    def build_next_action_button(
        self,
        container: Container,
        callback: Callable[[Gtk.Button, Container], None],
        icon_name: str,
    ) -> Gtk.Button:
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

    def on_search_changed(self, entry: Gtk.SearchEntry) -> None:
        text = entry.get_text().lower()

        for row in self.container_rows:
            visible = text in row.name
            row.set_visible(visible)

    def on_container_row_clicked(self, _: Gtk.ListBoxRow, container: Container) -> None:
        self.emit("container-activated", container)

    def row_start_container(self, _: Any, container: Container) -> None:
        start_container(container.name)
        self.reload_ui()

    def row_stop_container(self, _: Any, container: Container) -> None:
        stop_container(container.name)
        self.reload_ui()
