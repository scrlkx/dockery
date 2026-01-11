from typing import Any, List

from docker.models.images import Image
from gi.repository import Adw, GObject, Gtk

from ..components.badge import Badge
from ..utils.docker import (
    get_image_last_tag,
    get_image_size,
    get_images,
)
from ..utils.ui import humanize_size


class ImageRow(Adw.ActionRow):
    __gtype_name__ = "ImageRow"

    short_id = GObject.Property(type=str)
    tags = GObject.Property(type=str)
    last_tag = GObject.Property(type=str)
    size = GObject.Property(type=str)


@Gtk.Template(resource_path="/com/scrlkx/dockery/pages/images_list_page.ui")
class ImagesListPage(Adw.NavigationPage):
    __gtype_name__ = "ImagesListPage"

    __gsignals__ = {"image-activated": (GObject.SignalFlags.RUN_FIRST, None, (object,))}

    search_entry = Gtk.Template.Child()
    images_group = Gtk.Template.Child()

    image_rows: List[ImageRow] = []

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        self.register_events()
        self.build_ui()

    def register_events(self) -> None:
        self.search_entry.connect("search-changed", self.on_search_changed)

    def build_ui(self) -> None:
        images = get_images()

        for image in images:
            row = ImageRow(title=image.short_id)
            row.short_id = image.short_id
            row.tags = "".join(image.tags)
            row.last_tag = get_image_last_tag(image)
            row.size = humanize_size(get_image_size(image))

            row.set_activatable(True)
            row.connect("activated", self.on_image_row_clicked, image)

            self.image_rows.append(row)

            if row.last_tag:
                last_tag = Badge(
                    text=row.last_tag,
                    style_class="tag-blue",
                    margin_end=0,
                )

                row.add_suffix(last_tag)

            size = Badge(
                text=row.size,
                margin_end=12,
            )

            row.add_suffix(size)

            info = Gtk.Image.new_from_resource(
                "/com/scrlkx/dockery/icons/chevron-right.svg"
            )
            info.add_css_class("flat")

            row.add_suffix(info)

            self.images_group.add(row)

    def on_search_changed(self, entry: Gtk.SearchEntry) -> None:
        text = entry.get_text().lower()

        for row in self.image_rows:
            visible = (row.short_id is not None and text in row.short_id) or (
                row.tags is not None and text in row.tags
            )

            row.set_visible(visible)

    def on_image_row_clicked(self, _: Gtk.ListBoxRow, image: Image) -> None:
        self.emit("image-activated", image)
