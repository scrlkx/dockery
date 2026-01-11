from typing import Any, cast

from gi.repository import Adw, Gtk

from ..components.key_value_row import KeyValueRow
from ..utils.docker import get_system_info
from ..utils.i18n import _


@Gtk.Template(resource_path="/com/scrlkx/dockery/pages/system_page.ui")
class SystemPage(Adw.NavigationPage):
    __gtype_name__ = "SystemPage"

    host_group = Gtk.Template.Child()
    engine_group = Gtk.Template.Child()
    plugins_group = Gtk.Template.Child()

    host_rows: list[Adw.ActionRow] = []
    engine_rows: list[Adw.ActionRow] = []
    plugins_rows: list[Adw.ActionRow] = []

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        self.host_rows = []
        self.engine_rows = []
        self.plugins_rows = []

        self.build_ui()

    def build_ui(self) -> None:
        system_info = get_system_info()

        host = {
            _("Name"): system_info.get("Name"),
            _("Type"): system_info.get("OSType"),
            _("OS"): system_info.get("OperatingSystem"),
            _("Kernel"): system_info.get("KernelVersion"),
            _("Architecture"): system_info.get("Architecture"),
            _("Time"): system_info.get("SystemTime"),
        }

        for key, value in host.items():
            if not value:
                continue

            row = KeyValueRow(key, value)

            self.host_group.add(row)
            self.host_rows.append(row)

        engine = {
            _("Version"): system_info.get("ServerVersion"),
            _("Root directory"): system_info.get("DockerRootDir"),
            _("Storage driver"): system_info.get("Driver"),
        }

        for key, value in engine.items():
            if not value:
                continue

            row = KeyValueRow(key, value)

            self.engine_group.add(row)
            self.engine_rows.append(row)

        plugins = {
            _("Authorization"): system_info.get("Plugins", {}).get("Authorization"),
            _("Log"): system_info.get("Plugins", {}).get("Log"),
            _("Network"): system_info.get("Plugins", {}).get("Network"),
            _("Volume"): system_info.get("Plugins", {}).get("Volume"),
        }

        for key, value in plugins.items():
            if not value:
                continue

            if isinstance(value, list):
                value = ", ".join(cast(list[str], value))

            row = KeyValueRow(key, value)

            self.plugins_group.add(row)
            self.plugins_rows.append(row)
