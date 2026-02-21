from typing import Any, List, Tuple, cast

from gi.repository import Adw, Gtk

from ..components.async_list import AsyncList
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
        self.host_list = AsyncList(
            provider=self.get_host_items,
            row_factory=self.render_row,
            search_enabled=False,
            title=_("Host"),
        )

        self.engine_list = AsyncList(
            provider=self.get_engine_items,
            row_factory=self.render_row,
            search_enabled=False,
            title=_("Engine"),
        )

        self.plugins_list = AsyncList(
            provider=self.get_plugins_items,
            row_factory=self.render_row,
            search_enabled=False,
            title=_("Plugins"),
        )

        self.content_box.append(self.host_list)
        self.content_box.append(self.engine_list)
        self.content_box.append(self.plugins_list)

    def get_host_items(self) -> List[Tuple[str, str]]:
        info = get_system_info()

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

    def get_engine_items(self) -> List[Tuple[str, str]]:
        info = get_system_info()

        return [
            (k, v)
            for k, v in {
                _("Version"): info.get("ServerVersion"),
                _("Root directory"): info.get("DockerRootDir"),
                _("Storage driver"): info.get("Driver"),
            }.items()
            if v
        ]

    def get_plugins_items(self) -> List[Tuple[str, str]]:
        info = get_system_info()
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

    def render_row(self, item: Tuple[str, str]) -> KeyValueRow:
        key, value = item
        return KeyValueRow(key, value)
