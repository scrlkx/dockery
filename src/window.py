from typing import Any

from docker.models.containers import Container
from gi.repository import Adw, Gtk

from .pages.container_details_page import ContainerDetailsPage
from .pages.containers_list_page import ContainersListPage
from .pages.images_list_page import ImagesListPage
from .pages.networks_list_page import NetworksListPage
from .pages.volumes_list_page import VolumesPage


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
        self.sidebar_list.connect("row-activated", self._on_sidebar_row_activated)

        self.back_button.connect("clicked", self._on_back_clicked)

    def build_ui(self):
        self.sidebar_list.set_activate_on_single_click(True)
        self.sidebar_list.select_row(self.containers_row)

        containers_list_page = ContainersListPage()
        containers_list_page.connect(
            "container-activated",
            self._on_container_activated,
        )

        self.nav_view.push(containers_list_page)

    def _on_back_clicked(self, _: Gtk.Button) -> None:
        self.nav_view.pop()

        if self.nav_view.get_visible_page() is not None:
            self.back_button.set_visible(False)

    def _on_container_activated(self, _: Gtk.Widget, container: Container) -> None:
        self.back_button.set_visible(True)

        container_details_page = ContainerDetailsPage(container)
        self.nav_view.push(container_details_page)

    def _on_sidebar_row_activated(self, _: Gtk.ListBox, row: Gtk.ListBoxRow) -> None:
        index = row.get_index()

        if index == 0:
            self.content_page.set_title("Containers")

            containers_list_page = ContainersListPage()
            containers_list_page.connect(
                "container-activated",
                self._on_container_activated,
            )

            self.nav_view.replace([containers_list_page])
            self.back_button.set_visible(False)
        elif index == 1:
            self.content_page.set_title("Images")

            images_list_page = ImagesListPage()
            self.nav_view.replace([images_list_page])
            self.back_button.set_visible(False)
        elif index == 2:
            self.content_page.set_title("Volumes")

            volumes_list_page = VolumesPage()
            self.nav_view.replace([volumes_list_page])
            self.back_button.set_visible(False)
        elif index == 3:
            self.content_page.set_title("Networks")

            networks_list_page = NetworksListPage()
            self.nav_view.replace([networks_list_page])
            self.back_button.set_visible(False)
