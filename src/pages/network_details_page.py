from docker.models.networks import Network
from gi.repository import Adw, Gtk

from ..components.key_value_row import KeyValueRow
from ..utils.docker import (
    get_network,
    get_network_created_at,
    get_network_driver,
)
from ..utils.i18n import _
from ..utils.ui import iso_to_local


@Gtk.Template(resource_path="/com/scrlkx/dockery/pages/network_details_page.ui")
class NetworkDetailsPage(Adw.NavigationPage):
    __gtype_name__ = "NetworkDetailsPage"

    name_label = Gtk.Template.Child()
    details_group = Gtk.Template.Child()

    detail_rows: list[Adw.ActionRow] = []

    network: Network

    def __init__(self, network: Network):
        super().__init__()

        self.detail_rows = []
        self.tag_rows = []

        self.network = get_network(network.short_id)

        self.build_ui()

    def build_ui(self) -> None:
        self.load_details()

    def load_details(self) -> None:
        self.set_title(self.network.name or self.network.short_id)
        self.name_label.set_text(self.network.name or self.network.short_id)

        details = {
            _("ID"): self.network.id or self.network.short_id,
            _("Name"): self.network.name or "-",
            _("Driver"): get_network_driver(self.network),
            _("Created at"): iso_to_local(get_network_created_at(self.network)),
        }

        for row in self.detail_rows:
            self.details_group.remove(row)

        self.detail_rows.clear()

        for key, value in details.items():
            row = KeyValueRow(key, value)

            self.details_group.add(row)
            self.detail_rows.append(row)
