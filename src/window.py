from typing import Any

from docker.models.containers import Container
from docker.models.images import Image
from docker.models.networks import Network
from docker.models.volumes import Volume
from gi.repository import Adw, Gtk

from .pages.container_details_page import ContainerDetailsPage
from .pages.containers_list_page import ContainersListPage
from .pages.image_details_page import ImageDetailsPage
from .pages.images_list_page import ImagesListPage
from .pages.network_details_page import NetworkDetailsPage
from .pages.networks_list_page import NetworksListPage
from .pages.volume_details_page import VolumeDetailsPage
from .pages.volumes_list_page import VolumesPage
from .utils.i18n import _


@Gtk.Template(resource_path="/com/scrlkx/dockery/window.ui")
class DockeryWindow(Adw.ApplicationWindow):
    __gtype_name__ = "DockeryWindow"

    header_bar = Gtk.Template.Child()
    back_button = Gtk.Template.Child()
    nav_view = Gtk.Template.Child()
    sidebar_list = Gtk.Template.Child()
    containers_row = Gtk.Template.Child()
    images_row = Gtk.Template.Child()
    content_page = Gtk.Template.Child()

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        self.register_events()
        self.build_ui()

    def register_events(self) -> None:
        self.sidebar_list.connect("row-activated", self.on_sidebar_row_activated)

        self.back_button.connect("clicked", self.on_back_button_clicked)

    def build_ui(self):
        self.sidebar_list.set_activate_on_single_click(True)
        self.sidebar_list.select_row(self.containers_row)

        containers_list_page = ContainersListPage()
        containers_list_page.connect(
            "container-activated",
            self.on_container_activated,
        )

        self.nav_view.push(containers_list_page)

    def on_back_button_clicked(self, __: Gtk.Button) -> None:
        self.nav_view.pop()

        if self.nav_view.get_visible_page() is not None:
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

    def on_sidebar_row_activated(self, __: Gtk.ListBox, row: Gtk.ListBoxRow) -> None:
        index = row.get_index()

        if index == 0:
            self.content_page.set_title(_("Containers"))

            containers_list_page = ContainersListPage()
            containers_list_page.connect(
                "container-activated",
                self.on_container_activated,
            )

            self.nav_view.replace([containers_list_page])
            self.back_button.set_visible(False)
        elif index == 1:
            self.content_page.set_title(_("Images"))

            images_list_page = ImagesListPage()
            images_list_page.connect(
                "image-activated",
                self.on_image_activated,
            )

            self.nav_view.replace([images_list_page])
            self.back_button.set_visible(False)
        elif index == 2:
            self.content_page.set_title(_("Volumes"))

            volumes_list_page = VolumesPage()
            volumes_list_page.connect(
                "volume-activated",
                self.on_volume_activated,
            )

            self.nav_view.replace([volumes_list_page])
            self.back_button.set_visible(False)
        elif index == 3:
            self.content_page.set_title(_("Networks"))

            networks_list_page = NetworksListPage()
            networks_list_page.connect(
                "network-activated",
                self.on_network_activated,
            )

            self.nav_view.replace([networks_list_page])
            self.back_button.set_visible(False)
