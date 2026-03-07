from typing import Any

from docker.models.containers import Container
from gi.repository import Adw, GObject, Gtk

from ..components.async_list import AsyncList
from ..components.badge import Badge
from ..components.row_button import RowButton
from ..components.row_next import RowNext
from ..utils.docker import (
    get_container_next_action,
    get_containers,
    start_container,
    stop_container,
)
from ..utils.events import on_containers_change, unsubscribe
from ..utils.i18n import _
from ..utils.ui import (
    get_container_status_class,
    get_container_status_label,
)


class ContainerRow(Adw.ActionRow):
    __gtype_name__ = "ContainerRow"

    id = GObject.Property(type=str)
    name = GObject.Property(type=str)
    status_label = GObject.Property(type=str)
    status_class = GObject.Property(type=str)


@Gtk.Template(resource_path="/com/scrlkx/dockery/pages/containers_list_page.ui")
class ContainersListPage(Adw.NavigationPage):
    __gtype_name__ = "ContainersListPage"

    __gsignals__ = {
        "container-activated": (GObject.SignalFlags.RUN_FIRST, None, (object,))
    }

    content_box = Gtk.Template.Child()

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        self.connect("unrealize", self.on_unrealize)

        self.build_ui()
        self.register_events()

    def on_unrealize(self, _widget: Gtk.Widget) -> None:
        unsubscribe(self.list_widget.reload_content)

    def register_events(self) -> None:
        on_containers_change(self.list_widget.reload_content)

    def build_ui(self) -> None:
        self.list_widget = AsyncList(
            provider=get_containers,
            row_factory=self.render_row,
            search_placeholder=_("Search by ID or name"),
            search_callback=self.search,
            title=_("Containers"),
        )

        self.content_box.append(self.list_widget)

    def render_row(self, container: Container) -> ContainerRow:
        row = ContainerRow()
        row.set_title(container.name)
        row.id = container.id
        row.name = container.name.lower()
        row.status_label = get_container_status_label(container)
        row.status_class = get_container_status_class(container)
        row.set_activatable(True)
        row.connect("activated", self.on_row_clicked, container)

        if row.status_label and row.status_class:
            status = Badge(
                text=row.status_label,
                style_class=row.status_class,
                margin_end=12,
            )

            row.add_suffix(status)

        next_action = get_container_next_action(container)

        if next_action == "start":
            button = RowButton(
                icon_name="media-playback-start-symbolic",
                callback=lambda c=container: start_container(c.name),
            )
            button.set_margin_end(6)

            row.add_suffix(button)
        elif next_action == "stop":
            button = RowButton(
                icon_name="media-playback-stop-symbolic",
                callback=lambda c=container: stop_container(c.name),
            )
            button.set_margin_end(6)

            row.add_suffix(button)

        row.add_suffix(RowNext())

        return row

    def search(self, container: ContainerRow, text: str) -> bool:
        return text in container.id or text in container.name

    def on_row_clicked(self, _: AsyncList, container: Container) -> None:
        self.emit("container-activated", container)
