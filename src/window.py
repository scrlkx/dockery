from typing import Any

from docker.models.containers import Container
from docker.models.images import Image
from docker.models.networks import Network
from docker.models.volumes import Volume
from gi.repository import Adw, Gio, Gtk

from .components.help_overlay import HelpOverlay
from .components.sidebar_row import SidebarRow
from .pages.container_details_page import ContainerDetailsPage
from .pages.containers_list_page import ContainersListPage
from .pages.image_details_page import ImageDetailsPage
from .pages.images_list_page import ImagesListPage
from .pages.network_details_page import NetworkDetailsPage
from .pages.networks_list_page import NetworksListPage
from .pages.system_page import SystemPage
from .pages.volume_details_page import VolumeDetailsPage
from .pages.volumes_list_page import VolumesPage
from .utils import ui
from .utils.i18n import _


@Gtk.Template(resource_path="/com/scrlkx/dockery/window.ui")
class DockeryWindow(Adw.ApplicationWindow):
    __gtype_name__ = "DockeryWindow"

    header_bar = Gtk.Template.Child()
    back_button = Gtk.Template.Child()
    nav_view = Gtk.Template.Child()
    sidebar_list = Gtk.Template.Child()
    content_page = Gtk.Template.Child()

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        self.register_events()
        self.build_ui()

        ui.set_main_window(self)

    def register_events(self) -> None:
        self.sidebar_list.connect("row-activated", self.on_sidebar_row_activated)

        self.back_button.connect("clicked", self.on_back_button_clicked)

    def build_ui(self) -> None:
        self.build_primary_menu()
        self.build_help_overlay()

        self.build_sidebar()

        containers_list_page = ContainersListPage()
        containers_list_page.connect(
            "container-activated",
            self.on_container_activated,
        )

        self.nav_view.push(containers_list_page)

    def build_primary_menu(self) -> None:
        menu = Gio.Menu()

        # menu.append(_("Preferences"), "app.preferences")
        menu.append(_("Keyboard Shortcuts"), "win.show-help-overlay")
        menu.append(_("Help"), "app.help")
        menu.append(_("About"), "app.about")

        menu_button = Gtk.MenuButton()
        menu_button.set_icon_name("open-menu-symbolic")
        menu_button.set_menu_model(menu)
        menu_button.set_tooltip_text(_("Main Menu"))

        self.header_bar.pack_end(menu_button)

    def build_help_overlay(self) -> None:
        self.set_help_overlay(HelpOverlay())

    def build_sidebar(self) -> None:
        self.sidebar_list.set_activate_on_single_click(True)

        rows = [
            (
                _("Containers"),
                "container-symbolic",
                ContainersListPage,
                "container-activated",
                self.on_container_activated,
            ),
            (
                _("Images"),
                "image-symbolic",
                ImagesListPage,
                "image-activated",
                self.on_image_activated,
            ),
            (
                _("Volumes"),
                "volume-symbolic",
                VolumesPage,
                "volume-activated",
                self.on_volume_activated,
            ),
            (
                _("Networks"),
                "network-symbolic",
                NetworksListPage,
                "network-activated",
                self.on_network_activated,
            ),
            (
                _("System"),
                "system-symbolic",
                SystemPage,
                None,
                None,
            ),
        ]

        for title, icon, page_class, signal, callback in rows:
            row = SidebarRow(title, icon)
            row.page_class = page_class
            row.signal = signal
            row.callback = callback

            self.sidebar_list.append(row)

        self.sidebar_list.select_row(self.sidebar_list.get_row_at_index(0))

    def on_back_button_clicked(self, __: Gtk.Button) -> None:
        self.nav_view.pop()

        if self.nav_view.get_visible_page() is not None:
            self.back_button.set_visible(False)

    def on_sidebar_row_activated(self, __: Gtk.ListBox, row: SidebarRow) -> None:
        self.content_page.set_title(row.title)

        page = row.page_class()

        if row.signal and row.callback:
            page.connect(row.signal, row.callback)

        self.nav_view.replace([page])
        self.back_button.set_visible(False)

    def on_container_activated(self, __: Gtk.Widget, container: Container) -> None:
        self.back_button.set_visible(True)

        container_details_page = ContainerDetailsPage(container)
        self.nav_view.push(container_details_page)

    def on_image_activated(self, __: Gtk.Widget, image: Image) -> None:
        self.back_button.set_visible(True)

        image_details_page = ImageDetailsPage(image)
        self.nav_view.push(image_details_page)

    def on_volume_activated(self, __: Gtk.Widget, volume: Volume) -> None:
        self.back_button.set_visible(True)

        volume_details_page = VolumeDetailsPage(volume)
        self.nav_view.push(volume_details_page)

    def on_network_activated(self, __: Gtk.Widget, network: Network) -> None:
        self.back_button.set_visible(True)

        network_details_page = NetworkDetailsPage(network)
        self.nav_view.push(network_details_page)
