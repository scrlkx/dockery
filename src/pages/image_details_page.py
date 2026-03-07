import threading
from typing import cast

from docker.models.images import Image
from gi.repository import Adw, Gio, GLib, Gtk

from ..components.confirmation_dialog import ConfirmationDialog
from ..components.key_value_row import KeyValueRow
from ..components.quick_action_button import QuickActionButton
from ..utils.docker import (
    get_image,
    get_image_architecture,
    get_image_created_at,
    get_image_export_filename,
    get_image_last_tag,
    get_image_os,
    get_image_size,
    pull_image,
    push_image,
    remove_image,
    save_image,
)
from ..utils.i18n import _
from ..utils.ui import humanize_size, iso_to_local, show_error_dialog


@Gtk.Template(resource_path="/com/scrlkx/dockery/pages/image_details_page.ui")
class ImageDetailsPage(Adw.NavigationPage):
    __gtype_name__ = "ImageDetailsPage"

    name_label = Gtk.Template.Child()
    quick_actions_group = Gtk.Template.Child()
    details_group = Gtk.Template.Child()
    tags_group = Gtk.Template.Child()

    quick_action_rows: list[Gtk.Button] = []
    detail_rows: list[Adw.ActionRow] = []
    tag_rows: list[Adw.ActionRow] = []

    image: Image

    def __init__(self, image: Image):
        super().__init__()

        self.quick_action_rows = []
        self.detail_rows = []
        self.tag_rows = []

        assert image.id is not None
        self.image = get_image(image.id)

        self.build_ui()

    def build_ui(self) -> None:
        self.load_details()
        self.load_quick_actions()
        self.load_tags()

    def reload_ui(self) -> None:
        assert self.image.id is not None

        self.image = get_image(self.image.id)
        self.build_ui()

    def load_details(self) -> None:
        self.set_title(self.image.short_id)
        self.name_label.set_text(self.image.short_id)

        details = {
            _("ID"): self.image.id or "-",
            _("Size"): humanize_size(get_image_size(self.image)),
            _("Architecture"): get_image_architecture(self.image),
            _("OS"): get_image_os(self.image),
            _("Created at"): iso_to_local(get_image_created_at(self.image)),
        }

        for row in self.detail_rows:
            self.details_group.remove(row)

        self.detail_rows.clear()

        for key, value in details.items():
            row = KeyValueRow(key, value)

            self.details_group.add(row)
            self.detail_rows.append(row)

    def load_quick_actions(self) -> None:
        image_tag = get_image_last_tag(self.image)
        actions = [
            (
                "pull",
                _("Pull"),
                "go-down-symbolic",
                self.on_pull_clicked,
                bool(image_tag),
            ),
            (
                "push",
                _("Push"),
                "go-up-symbolic",
                self.on_push_clicked,
                bool(image_tag),
            ),
            (
                "export",
                _("Export"),
                "package-x-generic-symbolic",
                self.on_export_clicked,
                True,
            ),
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

        for action, label, icon_name, callback, enabled in actions:
            button = QuickActionButton(
                label=label,
                icon_name=icon_name,
                callback=callback,
                on_finish=self.reload_ui if action in {"pull", "push"} else None,
                threaded=action in {"pull", "push"},
            )
            button.set_sensitive(enabled)

            self.quick_actions_group.append(button)
            self.quick_action_rows.append(button)

    def load_tags(self) -> None:
        for row in self.tag_rows:
            self.tags_group.remove(row)

        self.tag_rows.clear()

        tags = self.image.tags

        for tag in tags:
            row = KeyValueRow(tag, "")

            self.tags_group.add(row)
            self.tag_rows.append(row)

    def on_pull_clicked(self) -> None:
        image_tag = get_image_last_tag(self.image)

        if image_tag:
            pull_image(image_tag)

    def on_push_clicked(self) -> None:
        image_tag = get_image_last_tag(self.image)

        if image_tag:
            push_image(image_tag)

    def on_export_clicked(self) -> None:
        dialog = Gtk.FileDialog(title=_("Export image"))
        dialog.set_initial_name(get_image_export_filename(self.image))

        root = self.get_root()
        parent = root if isinstance(root, Gtk.Window) else None
        dialog.save(parent, None, self.on_export_file_chosen)

    def on_export_file_chosen(
        self,
        dialog: Gtk.FileDialog,
        result: Gio.AsyncResult,
    ) -> None:
        try:
            file = dialog.save_finish(result)
        except GLib.Error:
            return

        path = file.get_path()

        if path is None:
            show_error_dialog(_("The selected location is not available."))
            return

        self.set_sensitive(False)

        def task() -> None:
            try:
                assert self.image.id is not None
                save_image(self.image.id, path)
            except Exception as exception:
                GLib.idle_add(show_error_dialog, str(exception))
            finally:
                GLib.idle_add(self.set_sensitive, True)

        threading.Thread(target=task).start()

    def on_remove_clicked(self) -> None:
        dialog = ConfirmationDialog(
            heading=_("Remove image?"),
            body=_("Are you sure you want to remove this image?"),
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
                assert self.image.id is not None
                remove_image(self.image.id)
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
