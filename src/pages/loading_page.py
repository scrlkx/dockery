from gi.repository import GLib, GObject, Gtk


@Gtk.Template(resource_path="/com/scrlkx/dockery/pages/loading_page.ui")
class LoadingPage(Gtk.Box):
    __gtype_name__ = "LoadingPage"

    __gsignals__ = {
        "loading-done": (GObject.SignalFlags.RUN_FIRST, None, ()),
        "setup-required": (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    spinner = Gtk.Template.Child()

    def __init__(self):
        super().__init__()

        self.check_docker()

    def check_docker(self) -> None:
        GLib.idle_add(self.emit, "setup-required")
