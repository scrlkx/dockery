from typing import Any

from docker.models.containers import Container
from gi.repository import Adw, Gtk

from .pages.container_page import ContainerPage
from .pages.containers_page import ContainersPage
from .pages.images_page import ImagesPage
from .pages.networks_page import NetworksPage
from .pages.volumes_page import VolumesPage


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

        containers_page = ContainersPage()
        containers_page.connect(
            "container-activated",
            self._on_container_activated,
        )

        self.nav_view.push(containers_page)

    def _on_back_clicked(self, _: Gtk.Button) -> None:
        self.nav_view.pop()

        if self.nav_view.get_visible_page() is not None:
            self.back_button.set_visible(False)

    def _on_container_activated(self, _: Gtk.Widget, container: Container) -> None:
        self.back_button.set_visible(True)

        details_page = ContainerPage(container)
        self.nav_view.push(details_page)

    def _on_sidebar_row_activated(self, _: Gtk.ListBox, row: Gtk.ListBoxRow) -> None:
        index = row.get_index()

        if index == 0:
            self.content_page.set_title("Containers")

            containers_page = ContainersPage()
            containers_page.connect(
                "container-activated",
                self._on_container_activated,
            )

            self.nav_view.replace([containers_page])
            self.back_button.set_visible(False)
        elif index == 1:
            self.content_page.set_title("Images")

            images_page = ImagesPage()
            self.nav_view.replace([images_page])
            self.back_button.set_visible(False)
        elif index == 2:
            self.content_page.set_title("Volumes")

            volumes_page = VolumesPage()
            self.nav_view.replace([volumes_page])
            self.back_button.set_visible(False)
        elif index == 3:
            self.content_page.set_title("Volumes")

            networks_page = NetworksPage()
            self.nav_view.replace([networks_page])
            self.back_button.set_visible(False)
