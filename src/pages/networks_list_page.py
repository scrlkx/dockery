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

    content_group: Gtk.Box = Gtk.Template.Child()

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        self.build_ui()

    def build_ui(self) -> None:
        self.list_widget = AsyncList(
            provider=get_networks,
            row_factory=self.render_row,
            search_placeholder=_("Search by name or ID"),
            search_callback=self.search,
        )

        self.content_group.append(self.list_widget)

    def render_row(self, network: Network) -> Gtk.Widget:
        row = NetworkRow(title=network.name or network.short_id)
        row.id = network.id
        row.name = network.name or network.short_id
        row.driver = get_network_driver(network)

        row.set_activatable(True)
        row.connect("activated", self.on_row_clicked, network)

        driver = Badge(row.driver)
        driver.set_margin_end(6)

        row.add_suffix(driver)

        row.add_suffix(RowNext())

        return row

    def search(self, row: NetworkRow, text: str) -> bool:
        return text in row.id or text in row.name

    def on_row_clicked(self, _: Gtk.ListBoxRow, network: Network) -> None:
        self.emit("network-activated", network)
