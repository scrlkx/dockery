import threading
from typing import cast

from docker.models.networks import Network
from gi.repository import Adw, GLib, Gtk

from ..components.confirmation_dialog import ConfirmationDialog
from ..components.key_value_row import KeyValueRow
from ..components.quick_action_button import QuickActionButton
from ..utils.docker import (
    get_network_created_at,
    get_network_driver,
    remove_network,
)
from ..utils.i18n import _
from ..utils.ui import iso_to_local, show_error_dialog


@Gtk.Template(resource_path="/com/scrlkx/dockery/pages/network_details_page.ui")
class NetworkDetailsPage(Adw.NavigationPage):
    __gtype_name__ = "NetworkDetailsPage"

    name_label = Gtk.Template.Child()
    quick_actions_group = Gtk.Template.Child()
    details_group = Gtk.Template.Child()

    detail_rows: list[Adw.ActionRow] = []
    quick_action_rows: list[Gtk.Button] = []

    network: Network

    def __init__(self, network: Network):
        super().__init__()

        self.detail_rows = []
        self.quick_action_rows = []

        self.network = network

        self.build_ui()

    def build_ui(self) -> None:
        self.load_quick_actions()
        self.load_details()

    def load_quick_actions(self) -> None:
        actions = [
            (
                "remove",
                _("Remove"),
                "user-trash-symbolic",
                self.on_remove_clicked,
                True,
            ),
        ]

        for row in self.quick_action_rows:
            self.quick_actions_group.remove(row)

        self.quick_action_rows.clear()

        for _action, label, icon_name, callback, enabled in actions:
            button = QuickActionButton(
                label=label,
                icon_name=icon_name,
                callback=callback,
                threaded=False,
            )
            button.set_sensitive(enabled)

            self.quick_actions_group.append(button)
            self.quick_action_rows.append(button)

    def load_details(self) -> None:
        self.set_title(self.network.name or self.network.short_id)
        self.name_label.set_text(self.network.name or self.network.short_id)

        details = {
            _("ID"): self.network.id or self.network.short_id,
            _("Name"): self.network.name or "-",
            _("Driver"): get_network_driver(self.network),
            _("Created at"): iso_to_local(get_network_created_at(self.network)),
        }

        for row in self.detail_rows:
            self.details_group.remove(row)

        self.detail_rows.clear()

        for key, value in details.items():
            row = KeyValueRow(key, value)

            self.details_group.add(row)
            self.detail_rows.append(row)

    def on_remove_clicked(self) -> None:
        dialog = ConfirmationDialog(
            heading=_("Remove network?"),
            body=_("Are you sure you want to remove this network?"),
            action_label=_("Remove"),
        )

        dialog.connect("response", self.on_remove_response)
        dialog.set_transient_for(cast(Gtk.Window, self.get_root()))
        dialog.present()

    def on_remove_response(self, dialog: Adw.MessageDialog, response: str) -> None:
        dialog.close()

        if response != "continue":
            return

        self.set_sensitive(False)

        def task() -> None:
            try:
                identifier = self.network.id or self.network.name or ""

                if not identifier:
                    raise RuntimeError(_("Network identifier is missing."))

                remove_network(identifier)

                GLib.idle_add(self.navigate_back)
            except Exception as exception:
                GLib.idle_add(show_error_dialog, str(exception))
                GLib.idle_add(self.set_sensitive, True)

        threading.Thread(target=task).start()

    def navigate_back(self) -> None:
        root = self.get_root()
        navigate_back = getattr(root, "navigate_back", None)

        if callable(navigate_back):
            navigate_back()
            return

        navigation_view = cast(
            Adw.NavigationView, self.get_ancestor(Adw.NavigationView)
        )

        if navigation_view:
            navigation_view.pop()
