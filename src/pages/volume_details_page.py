from docker.models.volumes import Volume
from gi.repository import Adw, Gtk

from ..components.key_value_row import KeyValueRow
from ..utils.docker import (
    get_volume_created_at,
    get_volume_driver,
    get_volume_mount_path,
    get_volume_short_name,
)
from ..utils.i18n import _
from ..utils.ui import iso_to_local


@Gtk.Template(resource_path="/com/scrlkx/dockery/pages/volume_details_page.ui")
class VolumeDetailsPage(Adw.NavigationPage):
    __gtype_name__ = "VolumeDetailsPage"

    name_label = Gtk.Template.Child()
    details_group = Gtk.Template.Child()

    detail_rows: list[Adw.ActionRow] = []

    volume: Volume

    def __init__(self, volume: Volume):
        super().__init__()

        self.detail_rows = []
        self.tag_rows = []

        self.volume = volume

        self.build_ui()

    def build_ui(self) -> None:
        self.load_details()

    def load_details(self) -> None:
        self.set_title(get_volume_short_name(self.volume))
        self.name_label.set_text(get_volume_short_name(self.volume))

        details = {
            _("Name"): self.volume.name,
            _("Driver"): get_volume_driver(self.volume),
            _("Mount path"): get_volume_mount_path(self.volume),
            _("Created at"): iso_to_local(get_volume_created_at(self.volume)),
        }

        for row in self.detail_rows:
            self.details_group.remove(row)

        self.detail_rows.clear()

        for key, value in details.items():
            row = KeyValueRow(key, value)

            self.details_group.add(row)
            self.detail_rows.append(row)
