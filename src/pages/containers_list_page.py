from typing import Any

from docker.models.containers import Container
from gi.repository import Adw, GObject, Gtk

from ..components.async_list import AsyncList
from ..components.badge import Badge
from ..components.row_button import RowButton
from ..components.row_next import RowNext
from ..utils.docker import (
    get_containers,
    get_container_image,
    get_container_next_action,
    start_container,
    stop_container,
)
from ..utils.events import on_containers_change
from ..utils.i18n import _
from ..utils.ui import (
    get_container_status_label,
    get_container_status_class,
)


class ContainerRow(Adw.ActionRow):
    __gtype_name__ = "ContainerRow"

    id = GObject.Property(type=str)
    name = GObject.Property(type=str)
    image = GObject.Property(type=str)
    status_label = GObject.Property(type=str)
    status_class = GObject.Property(type=str)


@Gtk.Template(resource_path="/com/scrlkx/dockery/pages/containers_list_page.ui")
class ContainersListPage(Adw.NavigationPage):
    __gtype_name__ = "ContainersListPage"

    __gsignals__ = {
        "container-activated": (GObject.SignalFlags.RUN_FIRST, None, (object,))
    }

    content_group: Gtk.Box = Gtk.Template.Child()

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        self.build_ui()
        self.register_events()

    def build_ui(self) -> None:
        self.list_widget = AsyncList(
            provider=get_containers,
            row_factory=self.render_row,
            search_placeholder=_("Search by ID, name or image"),
            search_callback=self.search,
        )

        self.content_group.append(self.list_widget)

    def register_events(self) -> None:
        on_containers_change(self.on_containers_change)

    def render_row(self, container: Container) -> Gtk.Widget:
        row = ContainerRow(title=container.name)
        row.id = container.id
        row.name = container.name.lower()
        row.image = get_container_image(container)
        row.status_label = get_container_status_label(container)
        row.status_class = get_container_status_class(container)

        row.set_activatable(True)
        row.connect("activated", self.on_row_clicked, container)

        if row.status_label and row.status_class:
            status = Badge(row.status_label)
            status.add_css_class(row.status_class)
            status.set_margin_end(6)

            row.add_suffix(status)

        next_action = get_container_next_action(container)

        if next_action == "start":
            button = RowButton(
                icon_name="media-playback-start-symbolic",
                callback=lambda: start_container(container.name),
            )
            button.set_margin_end(6)

            row.add_suffix(button)
        elif next_action == "stop":
            button = RowButton(
                icon_name="media-playback-stop-symbolic",
                callback=lambda: stop_container(container.name),
            )
            button.set_margin_end(6)

            row.add_suffix(button)

        row.add_suffix(RowNext())

        return row

    def search(self, row: ContainerRow, text: str) -> bool:
        return (
            text in row.id
            or text in row.name
            or (row.image is not None and text in row.image)
        )

    def on_row_clicked(self, _: Gtk.ListBoxRow, container: Container) -> None:
        self.emit("container-activated", container)

    def on_containers_change(self) -> None:
        self.list_widget.reload_content()
