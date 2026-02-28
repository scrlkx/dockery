import threading
from typing import Any, Dict, List, Tuple, cast

from gi.repository import Adw, GLib, Gtk

from ..components.key_value_row import KeyValueRow
from ..utils.docker import get_system_info
from ..utils.i18n import _


@Gtk.Template(resource_path="/com/scrlkx/dockery/pages/system_page.ui")
class SystemPage(Adw.NavigationPage):
    __gtype_name__ = "SystemPage"

    content_box = Gtk.Template.Child()

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        self.build_ui()

    def build_ui(self) -> None:
        self.host_group = Adw.PreferencesGroup()
        self.host_group.set_title(_("Host"))

        self.engine_group = Adw.PreferencesGroup()
        self.engine_group.set_title(_("Engine"))

        self.plugins_group = Adw.PreferencesGroup()
        self.plugins_group.set_title(_("Plugins"))

        spinner = Gtk.Spinner()
        spinner.set_spinning(True)
        spinner.set_halign(Gtk.Align.CENTER)
        spinner.set_size_request(48, 48)

        spinner_box = Gtk.Box()
        spinner_box.set_orientation(Gtk.Orientation.VERTICAL)
        spinner_box.set_vexpand(True)
        spinner_box.set_valign(Gtk.Align.CENTER)
        spinner_box.append(spinner)

        self.stack = Gtk.Stack()
        self.stack.set_vexpand(True)
        self.stack.add_named(spinner_box, "loading")

        content = Gtk.Box()
        content.set_orientation(Gtk.Orientation.VERTICAL)
        content.set_spacing(12)
        content.append(self.host_group)
        content.append(self.engine_group)
        content.append(self.plugins_group)

        self.stack.add_named(content, "content")
        self.content_box.append(self.stack)

        self.stack.set_visible_child_name("loading")
        self.load_info()

    def load_info(self) -> None:
        def task() -> None:
            info = get_system_info()
            GLib.idle_add(self.on_info_loaded, info)

        threading.Thread(target=task, daemon=True).start()

    def on_info_loaded(self, info: Dict[str, Any]) -> None:
        for key, value in self.get_host_items(info):
            self.host_group.add(KeyValueRow(key, value))

        for key, value in self.get_engine_items(info):
            self.engine_group.add(KeyValueRow(key, value))

        for key, value in self.get_plugins_items(info):
            self.plugins_group.add(KeyValueRow(key, value))

        self.stack.set_visible_child_name("content")

    def get_host_items(self, info: Dict[str, Any]) -> List[Tuple[str, str]]:
        return [
            (k, v)
            for k, v in {
                _("Name"): info.get("Name"),
                _("Type"): info.get("OSType"),
                _("OS"): info.get("OperatingSystem"),
                _("Kernel"): info.get("KernelVersion"),
                _("Architecture"): info.get("Architecture"),
                _("Time"): info.get("SystemTime"),
            }.items()
            if v
        ]

    def get_engine_items(self, info: Dict[str, Any]) -> List[Tuple[str, str]]:
        return [
            (k, v)
            for k, v in {
                _("Version"): info.get("ServerVersion"),
                _("Root directory"): info.get("DockerRootDir"),
                _("Storage driver"): info.get("Driver"),
            }.items()
            if v
        ]

    def get_plugins_items(self, info: Dict[str, Any]) -> List[Tuple[str, str]]:
        plugins = info.get("Plugins", {})

        items: List[Tuple[str, str]] = []

        for key, name in [
            (_("Authorization"), "Authorization"),
            (_("Log"), "Log"),
            (_("Network"), "Network"),
            (_("Volume"), "Volume"),
        ]:
            value = plugins.get(name)

            if not value:
                continue

            if isinstance(value, list):
                value = ", ".join(cast(list[str], value))

            items.append((key, value))

        return items
