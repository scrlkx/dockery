from docker.models.images import Image
from gi.repository import Adw, Gtk

from ..components.key_value_row import KeyValueRow
from ..utils.docker import (
    get_image,
    get_image_architecture,
    get_image_created_at,
    get_image_os,
    get_image_size,
)
from ..utils.i18n import _
from ..utils.ui import humanize_size, iso_to_local


@Gtk.Template(resource_path="/com/scrlkx/dockery/pages/image_details_page.ui")
class ImageDetailsPage(Adw.NavigationPage):
    __gtype_name__ = "ImageDetailsPage"

    name_label = Gtk.Template.Child()
    details_group = Gtk.Template.Child()
    tags_group = Gtk.Template.Child()

    detail_rows: list[Adw.ActionRow] = []
    tag_rows: list[Adw.ActionRow] = []

    image: Image

    def __init__(self, image: Image):
        super().__init__()

        self.detail_rows = []
        self.tag_rows = []

        self.image = get_image(image.id or image.short_id)

        self.build_ui()

    def build_ui(self) -> None:
        self.load_details()
        self.load_tags()

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

    def load_tags(self) -> None:
        for row in self.tag_rows:
            self.tags_group.remove(row)

        self.tag_rows.clear()

        tags = self.image.tags

        for tag in tags:
            row = KeyValueRow(tag, "")

            self.tags_group.add(row)
            self.tag_rows.append(row)
