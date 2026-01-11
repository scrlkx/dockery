from typing import Any, List

from gi.repository import Adw, GObject, Gtk

from ..utils.docker import get_volumes


class VolumeRow(Adw.ActionRow):
    __gtype_name__ = "VolumeRow"

    name = GObject.Property(type=str)


@Gtk.Template(resource_path="/com/scrlkx/dockery/pages/volumes_list_page.ui")
class VolumesPage(Adw.NavigationPage):
    __gtype_name__ = "VolumesPage"

    search_entry = Gtk.Template.Child()
    volumes_group = Gtk.Template.Child()

    volume_rows: List[VolumeRow] = []

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        self.register_events()
        self.build_ui()

    def register_events(self) -> None:
        self.search_entry.connect("search-changed", self.on_search_changed)

    def build_ui(self) -> None:
        volumes = get_volumes()

        for volume in volumes:
            row = VolumeRow(title=volume.name)
            row.name = volume.name

            row.set_activatable(True)

            self.volume_rows.append(row)

            info = Gtk.Image.new_from_resource(
                "/com/scrlkx/dockery/icons/chevron-right.svg"
            )
            info.add_css_class("flat")

            row.add_suffix(info)

            self.volumes_group.add(row)

    def on_search_changed(self, entry: Gtk.SearchEntry) -> None:
        text = entry.get_text().lower()

        for row in self.volume_rows:
            visible = text in row.name
            row.set_visible(visible)
