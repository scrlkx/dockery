from gi.repository import Adw, Gtk

from .container_page import ContainerPage
from .containers_page import ContainersPage


@Gtk.Template(resource_path="/com/scrlkx/dockery/window.ui")
class DockeryWindow(Adw.ApplicationWindow):
    __gtype_name__ = "DockeryWindow"

    header_bar = Gtk.Template.Child()
    back_button = Gtk.Template.Child()
    nav_view = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.back_button.connect("clicked", self._on_back_clicked)

        containers_page = ContainersPage()
        containers_page.connect(
            "container-activated",
            self._on_container_activated,
        )

        self.nav_view.push(containers_page)

    def _on_back_clicked(self, _):
        self.nav_view.pop()

        if self.nav_view.get_visible_page() is not None:
            self.back_button.set_visible(False)

    def _on_container_activated(self, _, container):
        self.back_button.set_visible(True)

        details_page = ContainerPage(container)
        self.nav_view.push(details_page)
