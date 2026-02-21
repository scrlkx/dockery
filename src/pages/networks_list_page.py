from typing import Any

from docker.models.networks import Network
from gi.repository import Adw, GObject, Gtk

from ..components.async_list import AsyncList
from ..components.badge import Badge
from ..components.row_next import RowNext
from ..utils.docker import get_network_driver, get_networks
from ..utils.i18n import _


class NetworkRow(Adw.ActionRow):
    __gtype_name__ = "NetworkRow"

    id = GObject.Property(type=str)
    name = GObject.Property(type=str)
    driver = GObject.Property(type=str)


@Gtk.Template(resource_path="/com/scrlkx/dockery/pages/networks_list_page.ui")
class NetworksListPage(Adw.NavigationPage):
    __gtype_name__ = "NetworksListPage"

    __gsignals__ = {
        "network-activated": (GObject.SignalFlags.RUN_FIRST, None, (object,))
    }

    content_box = Gtk.Template.Child()

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        self.build_ui()

    def build_ui(self) -> None:
        self.list_widget = AsyncList(
            provider=get_networks,
            row_factory=self.render_row,
            search_placeholder=_("Search by ID or name"),
            search_callback=self.search,
            title=_("Networks"),
        )

        self.content_box.append(self.list_widget)

    def render_row(self, network: Network) -> NetworkRow:
        row = NetworkRow(title=network.name or network.short_id)
        row.id = network.id
        row.name = network.name or network.short_id
        row.driver = get_network_driver(network)
        row.set_activatable(True)
        row.connect("activated", self.on_row_clicked, network)

        driver = Badge(
            text=row.driver,
            margin_end=12,
        )

        row.add_suffix(driver)
        row.add_suffix(RowNext())

        return row

    def search(self, network: Network, text: str) -> bool:
        return text.lower() in (network.name or network.short_id).lower()

    def on_row_clicked(self, _: AsyncList, network: Network) -> None:
        self.emit("network-activated", network)
