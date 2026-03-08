from typing import Any

from docker.models.volumes import Volume
from gi.repository import Adw, GObject, Gtk

from ..components.async_list import AsyncList
from ..components.row_next import RowNext
from ..utils.docker import get_volume_short_name, get_volumes
from ..utils.events import on_volumes_change, unsubscribe
from ..utils.i18n import _


class VolumeRow(Adw.ActionRow):
    __gtype_name__ = "VolumeRow"

    name = GObject.Property(type=str)


@Gtk.Template(resource_path="/com/scrlkx/dockery/pages/volumes_list_page.ui")
class VolumesPage(Adw.NavigationPage):
    __gtype_name__ = "VolumesPage"

    __gsignals__ = {
        "volume-activated": (GObject.SignalFlags.RUN_FIRST, None, (object,))
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
        on_volumes_change(self.list_widget.reload_content)

    def build_ui(self) -> None:
        self.list_widget = AsyncList(
            provider=get_volumes,
            row_factory=self.render_row,
            search_placeholder=_("Search by name"),
            search_callback=self.search,
            title=_("Volumes"),
        )

        self.content_box.append(self.list_widget)

    def render_row(self, volume: Volume) -> VolumeRow:
        row = VolumeRow(title=get_volume_short_name(volume))
        row.name = volume.name
        row.set_activatable(True)
        row.connect("activated", self.on_row_clicked, volume)

        row.add_suffix(RowNext())

        return row

    def search(self, volume: Volume, text: str) -> bool:
        return text.lower() in volume.name.lower()

    def on_row_clicked(self, _: AsyncList, volume: Volume) -> None:
        self.emit("volume-activated", volume)
