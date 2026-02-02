from typing import Any

from docker.models.volumes import Volume
from gi.repository import Adw, GObject, Gtk

from ..components.async_list import AsyncList
from ..components.row_next import RowNext
from ..utils.docker import get_volume_short_name, get_volumes
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

    content_group: Gtk.Box = Gtk.Template.Child()

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        self.build_ui()

    def build_ui(self) -> None:
        self.list_widget = AsyncList(
            provider=get_volumes,
            row_factory=self.render_row,
            search_placeholder=_("Search by name"),
            search_callback=self.search,
        )

        self.content_group.append(self.list_widget)

    def render_row(self, volume: Volume) -> Gtk.Widget:
        row = VolumeRow(title=get_volume_short_name(volume))
        row.name = volume.name

        row.set_activatable(True)
        row.connect("activated", self.on_row_clicked, volume)

        row.add_suffix(RowNext())

        return row

    def search(self, row: VolumeRow, text: str) -> bool:
        return text in row.name

    def on_row_clicked(self, _: Gtk.ListBoxRow, volume: Volume) -> None:
        self.emit("volume-activated", volume)
