from typing import Any, cast

from gi.repository import Adw, Gtk

from ..components.async_list import AsyncList
from ..components.key_value_row import KeyValueRow
from ..utils.docker import get_system_info
from ..utils.i18n import _


@Gtk.Template(resource_path="/com/scrlkx/dockery/pages/system_page.ui")
class SystemPage(Adw.NavigationPage):
    __gtype_name__ = "SystemPage"

    content_group = Gtk.Template.Child()

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        self.build_ui()

    def build_ui(self) -> None:
        self.content_group.set_orientation(Gtk.Orientation.VERTICAL)

        host_list = AsyncList(
            provider=self.get_host_info,
            row_factory=self.create_row,
            search_enabled=False,
            title=_("Host"),
        )

        host_list.set_margin_bottom(24)
        self.content_group.append(host_list)

        engine_list = AsyncList(
            provider=self.get_engine_info,
            row_factory=self.create_row,
            search_enabled=False,
            title=_("Engine"),
        )

        engine_list.set_margin_bottom(24)
        self.content_group.append(engine_list)

        plugins_list = AsyncList(
            provider=self.get_plugins_info,
            row_factory=self.create_row,
            search_enabled=False,
            title=_("Plugins"),
        )

        self.content_group.append(plugins_list)

    def get_host_info(self) -> list[tuple[str, str]]:
        system_info = get_system_info()

        host = {
            _("Name"): system_info.get("Name"),
            _("Type"): system_info.get("OSType"),
            _("OS"): system_info.get("OperatingSystem"),
            _("Kernel"): system_info.get("KernelVersion"),
            _("Architecture"): system_info.get("Architecture"),
            _("Time"): system_info.get("SystemTime"),
        }

        return [(key, value) for key, value in host.items() if value]

    def get_engine_info(self) -> list[tuple[str, str]]:
        system_info = get_system_info()

        engine = {
            _("Version"): system_info.get("ServerVersion"),
            _("Root directory"): system_info.get("DockerRootDir"),
            _("Storage driver"): system_info.get("Driver"),
        }

        return [(key, value) for key, value in engine.items() if value]

    def get_plugins_info(self) -> list[tuple[str, str]]:
        system_info = get_system_info()

        plugins = {
            _("Authorization"): system_info.get("Plugins", {}).get("Authorization"),
            _("Log"): system_info.get("Plugins", {}).get("Log"),
            _("Network"): system_info.get("Plugins", {}).get("Network"),
            _("Volume"): system_info.get("Plugins", {}).get("Volume"),
        }

        items: list[tuple[str, str]] = []

        for key, value in plugins.items():
            if not value:
                continue

            if isinstance(value, list):
                value = ", ".join(cast(list[str], value))

            items.append((key, str(value)))

        return items

    def create_row(self, item: tuple[str, str]) -> Gtk.Widget:
        return KeyValueRow(item[0], item[1])
