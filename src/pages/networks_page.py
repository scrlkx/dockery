from typing import Any, List

from gi.repository import Adw, GObject, Gtk

from ..components.badge import Badge
from ..utils.docker import get_network_driver, get_networks


class NetworkRow(Adw.ActionRow):
    __gtype_name__ = "NetworkRow"

    name = GObject.Property(type=str)
    driver = GObject.Property(type=str)


@Gtk.Template(resource_path="/com/scrlkx/dockery/pages/networks_page.ui")
class NetworksPage(Adw.NavigationPage):
    __gtype_name__ = "NetworksPage"

    search_entry = Gtk.Template.Child()
    networks_group = Gtk.Template.Child()

    network_rows: List[NetworkRow] = []

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        self.register_events()
        self.build_ui()

    def register_events(self) -> None:
        self.search_entry.connect("search-changed", self.on_search_changed)

    def build_ui(self) -> None:
        networks = get_networks()

        for network in networks:
            row = NetworkRow(title=network.name or network.short_id)
            row.name = network.name or network.short_id
            row.driver = get_network_driver(network)

            row.set_activatable(True)

            self.network_rows.append(row)

            driver = Badge(
                text=row.driver,
                margin_end=12,
            )

            row.add_suffix(driver)

            info = Gtk.Image.new_from_resource(
                "/com/scrlkx/dockery/icons/chevron-right.svg"
            )
            info.add_css_class("flat")

            row.add_suffix(info)

            self.networks_group.add(row)

    def on_search_changed(self, entry: Gtk.SearchEntry) -> None:
        text = entry.get_text().lower()

        for row in self.network_rows:
            visible = text in row.name
            row.set_visible(visible)
